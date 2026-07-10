import os
import pickle
import random
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from logging import getLogger
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset
from torch.utils.data.dataloader import DataLoader

from src.envs.environment import do_stats
from src.utils import MAX_WORKERS

logger = getLogger()


def _csv_ints(value):
    if not value:
        return set()
    return {int(part.strip()) for part in str(value).split(",") if part.strip()}


def _jsonl_paths(value):
    if not value:
        return []
    if isinstance(value, (list, tuple)):
        return [Path(path) for path in value if str(path).strip()]
    return [Path(part.strip()) for part in str(value).split(",") if part.strip()]


def _coefficient_vector_from_record(record):
    for key in ("coefficients", "exported_coefficients", "decoded_coefficients"):
        value = record.get(key)
        if isinstance(value, list):
            try:
                coeffs = [int(item) for item in value]
            except (TypeError, ValueError):
                return None
            if len(coeffs) == 25 and coeffs[-1] == 1:
                return coeffs[:-1]
            if len(coeffs) == 24:
                return coeffs
    polynomial = record.get("polynomial")
    if isinstance(polynomial, str):
        parts = [part.strip() for part in polynomial.split(",") if part.strip()]
        if len(parts) == 25:
            try:
                coeffs = [int(part) for part in parts]
            except ValueError:
                return None
            if coeffs[-1] == 1:
                return coeffs[:-1]
    return None


def _r_from_record(record):
    for key in ("r", "real_root_count", "target_r"):
        value = record.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    features = record.get("features")
    if isinstance(features, dict) and features.get("r") is not None:
        try:
            return int(features["r"])
        except (TypeError, ValueError):
            return None
    feedback = record.get("sair_feedback")
    if isinstance(feedback, dict):
        pair_key = feedback.get("pair_key")
        if isinstance(pair_key, str) and "|r=" in pair_key:
            try:
                return int(pair_key.rsplit("|r=", 1)[-1])
            except ValueError:
                return None
    return None


def _score_from_active_learning_class(class_label):
    score_map = {
        "accepted_useful_score_positive": 4.0,
        "accepted_useful_or_unknown": 3.0,
        "accepted_globally_covered_high_team_basin": 2.0,
        "accepted_duplicate_collapsed_basin": 1.0,
        "pending_score": 0.5,
        "wrong_real_root_count": 0.25,
        "exact_local_valid": 0.25,
        "locally_invalid": -1.0,
    }
    return score_map.get(str(class_label), 0.0)


def _score_from_score_aware_supervision(record):
    supervision = record.get("score_aware_supervision")
    if not isinstance(supervision, dict):
        return None
    reward = supervision.get("reward")
    weight = supervision.get("weight")
    try:
        reward_value = float(reward)
    except (TypeError, ValueError):
        return None
    try:
        weight_value = float(weight) if weight is not None else 1.0
    except (TypeError, ValueError):
        weight_value = 1.0
    # Keep the magnitude modest for compatibility with existing stats/logging,
    # but preserve the AXG-1.7 distinction between weak and strong supervision.
    return reward_value * min(max(weight_value, 0.25), 5.0)


def _generator_training_contract(record):
    contract = record.get("generator_training")
    if isinstance(contract, dict):
        try:
            weight = float(contract.get("weight", 0.0))
        except (TypeError, ValueError):
            weight = 0.0
        eligible = bool(contract.get("eligible")) and weight > 0.0
        return {
            "eligible": eligible,
            "weight": weight if eligible else 0.0,
            "role": str(contract.get("role") or "unknown"),
            "reason": str(contract.get("reason") or ""),
            "label": contract.get("label"),
            "pair_key": contract.get("pair_key"),
            "construction_family": contract.get("construction_family"),
            "basin_fingerprint": contract.get("basin_fingerprint"),
            "split_group_key": contract.get("split_group_key"),
        }

    class_label = str(record.get("derived_class_label") or "")
    score_aware = record.get("score_aware_supervision") if isinstance(record.get("score_aware_supervision"), dict) else {}
    score_label = str(score_aware.get("label") or "")
    label = (record.get("sair_feedback") or {}).get("label") if isinstance(record.get("sair_feedback"), dict) else record.get("label")
    pair = (record.get("sair_feedback") or {}).get("pair_key") if isinstance(record.get("sair_feedback"), dict) else record.get("pair_key")
    features = record.get("features") if isinstance(record.get("features"), dict) else {}
    family = features.get("construction_family") or features.get("template_family") or features.get("family_key") or "unknown"

    if score_label == "score_positive" or class_label == "accepted_useful_score_positive":
        role, eligible, weight = "score_positive", True, 12.0
    elif score_label == "low_team_scoreable":
        role, eligible, weight = "low_team_scoreable", True, 8.0
    elif class_label == "accepted_useful_or_unknown":
        role, eligible, weight = "accepted_useful_unknown", True, 3.0
    elif class_label == "exact_local_valid" or score_label == "pending_or_unknown":
        role, eligible, weight = "exact_local_exploration", True, 1.0
    elif score_label == "accepted_but_crowded_collapse" or class_label in {
        "accepted_duplicate_collapsed_basin",
        "accepted_globally_covered_high_team_basin",
    }:
        role, eligible, weight = "crowded_collapse", False, 0.0
    elif score_label == "accepted_duplicate":
        role, eligible, weight = "accepted_duplicate", False, 0.0
    elif score_label == "wrong_r" or class_label == "wrong_real_root_count":
        role, eligible, weight = "wrong_r", False, 0.0
    elif score_label == "invalid" or class_label == "locally_invalid":
        role, eligible, weight = "invalid", False, 0.0
    else:
        role, eligible, weight = "exact_local_exploration", True, 1.0
    return {
        "eligible": eligible,
        "weight": weight,
        "role": role,
        "reason": "derived from legacy active-learning labels",
        "label": label,
        "pair_key": pair,
        "construction_family": family,
        "basin_fingerprint": features.get("basin_fingerprint"),
        "split_group_key": _split_group_key(record),
    }


def _split_group_key(record):
    contract = record.get("generator_training") if isinstance(record.get("generator_training"), dict) else {}
    if contract.get("split_group_key"):
        return str(contract["split_group_key"])
    features = record.get("features") if isinstance(record.get("features"), dict) else {}
    for key in ("construction_family", "template_family", "family_key", "basin_fingerprint"):
        value = features.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    canonical_hash = record.get("canonical_hash")
    if canonical_hash:
        return f"canonical_hash:{canonical_hash}"
    return None


def _cap_key(record, contract, key):
    if key == "hash":
        return str(record.get("canonical_hash") or "")
    if key == "pair":
        return str(contract.get("pair_key") or (record.get("sair_feedback") or {}).get("pair_key") or "")
    if key == "label":
        return str(contract.get("label") or (record.get("sair_feedback") or {}).get("label") or "")
    if key == "family":
        features = record.get("features") if isinstance(record.get("features"), dict) else {}
        return str(contract.get("construction_family") or features.get("construction_family") or features.get("template_family") or features.get("family_key") or "")
    if key == "basin":
        features = record.get("features") if isinstance(record.get("features"), dict) else {}
        return str(contract.get("basin_fingerprint") or features.get("basin_fingerprint") or "")
    raise ValueError(key)


def _load_igp24_training_jsonl(args, classname):
    paths = _jsonl_paths(getattr(args, "igp24_training_jsonl", []))
    if not paths:
        return None

    target_rs = _csv_ints(getattr(args, "igp24_training_jsonl_target_rs", ""))
    max_rows = int(getattr(args, "igp24_training_jsonl_max_rows", 0) or 0)
    max_abs_coeff = int(getattr(args, "igp24_training_jsonl_max_abs_coeff", 0) or 0)
    train_set = []
    test_set = []
    skipped = {
        "missing_coefficients": 0,
        "target_r_filtered": 0,
        "missing_r": 0,
        "coefficient_bound_filtered": 0,
        "invalid_datapoint": 0,
        "generator_ineligible": 0,
        "duplicate_canonical_hash": 0,
        "cap_per_pair": 0,
        "cap_per_label": 0,
        "cap_per_family": 0,
        "cap_per_basin_fingerprint": 0,
    }
    seen_hashes = set()
    cap_counts = {
        "pair": Counter(),
        "label": Counter(),
        "family": Counter(),
        "basin": Counter(),
    }
    cap_limits = {
        "pair": int(getattr(args, "igp24_generator_cap_per_pair", 16) or 0),
        "label": int(getattr(args, "igp24_generator_cap_per_label", 64) or 0),
        "family": int(getattr(args, "igp24_generator_cap_per_family", 128) or 0),
        "basin": int(getattr(args, "igp24_generator_cap_per_basin_fingerprint", 8) or 0),
    }
    role_counts = Counter()
    role_weight = Counter()
    label_weight = Counter()
    family_weight = Counter()
    split_groups = {"train": set(), "eval": set()}

    for path in paths:
        with path.open("r", encoding="utf-8") as handle:
            for line_index, line in enumerate(handle):
                if max_rows > 0 and len(train_set) + len(test_set) >= max_rows:
                    break
                if not line.strip():
                    continue
                record = json.loads(line)
                coeffs = _coefficient_vector_from_record(record)
                if coeffs is None:
                    skipped["missing_coefficients"] += 1
                    continue
                r_value = _r_from_record(record)
                if r_value is None:
                    skipped["missing_r"] += 1
                    if target_rs:
                        continue
                if target_rs and r_value not in target_rs:
                    skipped["target_r_filtered"] += 1
                    continue
                if max_abs_coeff > 0 and max(abs(value) for value in coeffs) > max_abs_coeff:
                    skipped["coefficient_bound_filtered"] += 1
                    continue
                canonical_hash = str(record.get("canonical_hash") or f"{path}:{line_index}")
                if canonical_hash in seen_hashes:
                    skipped["duplicate_canonical_hash"] += 1
                    continue
                contract = _generator_training_contract(record)
                if not contract["eligible"] or float(contract["weight"]) <= 0.0:
                    skipped["generator_ineligible"] += 1
                    continue
                capped = False
                for cap_name, limit in cap_limits.items():
                    if limit <= 0:
                        continue
                    key = _cap_key(record, contract, cap_name)
                    if key and cap_counts[cap_name][key] >= limit:
                        skipped_key = "cap_per_basin_fingerprint" if cap_name == "basin" else f"cap_per_{cap_name}"
                        skipped[skipped_key] += 1
                        capped = True
                        break
                if capped:
                    continue
                try:
                    datapoint = classname(N=args.N, coeffs=coeffs, conditioning_target_r=r_value)
                except Exception:
                    skipped["invalid_datapoint"] += 1
                    continue
                score_aware = _score_from_score_aware_supervision(record)
                datapoint.score = (
                    score_aware
                    if score_aware is not None
                    else _score_from_active_learning_class(record.get("derived_class_label"))
                )
                datapoint.features = record.get("canonical_hash") or f"{path}:{line_index}"
                datapoint.generator_training_weight = float(contract["weight"])
                datapoint.generator_training_role = str(contract["role"])
                datapoint.generator_training_split_group = contract.get("split_group_key") or _split_group_key(record) or canonical_hash
                datapoint.source_metadata = {
                    "source_path": str(path),
                    "source_index": line_index,
                    "canonical_hash": record.get("canonical_hash"),
                    "dataset_row_id": record.get("dataset_row_id"),
                    "source_role": record.get("source_role"),
                    "derived_class_label": record.get("derived_class_label"),
                    "score_aware_supervision": record.get("score_aware_supervision"),
                    "generator_training": contract,
                    "construction_family": contract.get("construction_family"),
                    "train_eval_split": record.get("train_eval_split"),
                    "conditioning_target_r": r_value,
                }
                seen_hashes.add(canonical_hash)
                for cap_name in cap_counts:
                    key = _cap_key(record, contract, cap_name)
                    if key:
                        cap_counts[cap_name][key] += 1
                role_counts[str(contract["role"])] += 1
                role_weight[str(contract["role"])] += float(contract["weight"])
                if contract.get("label"):
                    label_weight[str(contract["label"])] += float(contract["weight"])
                if contract.get("construction_family"):
                    family_weight[str(contract["construction_family"])] += float(contract["weight"])
                split_group = datapoint.generator_training_split_group
                if record.get("train_eval_split") == "eval":
                    test_set.append(datapoint)
                    split_groups["eval"].add(split_group)
                else:
                    train_set.append(datapoint)
                    split_groups["train"].add(split_group)
        if max_rows > 0 and len(train_set) + len(test_set) >= max_rows:
            break

    if not train_set and test_set:
        train_set, test_set = make_grouped_train_test(test_set, min(len(test_set) // 2, int(args.ntest)))
    if not test_set and len(train_set) > 1:
        train_set, test_set = make_grouped_train_test(train_set, min(int(args.ntest), max(1, len(train_set) // 5)))

    train_groups = {getattr(row, "generator_training_split_group", None) for row in train_set}
    test_groups = {getattr(row, "generator_training_split_group", None) for row in test_set}
    overlap = {group for group in train_groups & test_groups if group is not None}
    if overlap:
        raise ValueError(f"IGP24 grouped train/eval split leakage detected for {len(overlap)} groups")

    logger.info(
        "Loaded IGP24 JSONL training data: train=%s test=%s paths=%s target_rs=%s skipped=%s generator_roles=%s generator_weight_by_role=%s",
        len(train_set),
        len(test_set),
        [str(path) for path in paths],
        sorted(target_rs),
        skipped,
        dict(role_counts),
        {key: round(value, 3) for key, value in sorted(role_weight.items())},
    )
    logger.info(
        "IGP24 generator sampling mass: labels=%s families=%s cap_limits=%s family_split_overlap=%s",
        label_weight.most_common(20),
        family_weight.most_common(20),
        cap_limits,
        sorted(split_groups["train"] & split_groups["eval"])[:20],
    )
    return train_set, test_set, skipped


def detokenize(data, args, env, executor=None):
    res = []
    pars = env.tokenizer.dataclass._save_class_params()
    if args.process_pool:
        BATCH = args.gen_batch_size
        data_slices = [data[i : i + BATCH] for i in range(0, len(data), BATCH)]

        if executor is not None:
            for chunk in executor.map(env.tokenizer.decode_batch, data_slices, repeat(pars, len(data_slices))):
                if chunk:
                    res.extend(chunk)
        else:
            with ProcessPoolExecutor(max_workers=min(MAX_WORKERS, args.num_workers)) as ex:
                for chunk in ex.map(env.tokenizer.decode_batch, data_slices, repeat(pars, len(data_slices))):
                    if chunk:
                        res.extend(chunk)
    else:
        res = env.tokenizer.decode_batch(data, pars)
    return res


# helper functions for creating the training and test Datasets


def generate_and_score(args, classname):
    """
    Generation method if no data
    """
    data = []
    BATCH = args.gen_batch_size
    batch_counts = [BATCH] * (args.gensize // BATCH)
    rem = args.gensize % BATCH
    if rem:
        batch_counts.append(rem)
    if args.process_pool:
        pars = classname._save_class_params()
        with ProcessPoolExecutor(max_workers=min(MAX_WORKERS, args.num_workers)) as executor:
            # map returns lists; stream them to avoid a giant materialization
            for chunk in executor.map(
                classname._batch_generate_and_score, batch_counts, repeat(args.N, len(batch_counts)), repeat(pars, len(batch_counts))
            ):
                if chunk:  # extend incrementally to manage memory
                    data.extend(chunk)
    else:
        for t in batch_counts:
            d = classname._batch_generate_and_score(t, args.N)
            if d is not None:
                data.extend(d)
    return data


def select_best(n, data):
    if len(data) <= n:
        random.shuffle(data)
        return data
    sorted_data = sorted(data, key=lambda x: x.score, reverse=True)[:n]
    random.shuffle(sorted_data)
    return sorted_data


def make_train_test(data, ntest):
    """
    Create a train and test dataset from a dataset.
    """
    indices = np.random.permutation(len(data))
    rp = [data[i] for i in indices]
    return rp[:-ntest], rp[-ntest:]


def make_grouped_train_test(data, ntest):
    groups = {}
    for row in data:
        key = getattr(row, "generator_training_split_group", None) or getattr(row, "features", None) or id(row)
        groups.setdefault(str(key), []).append(row)
    if len(groups) <= 1:
        if int(ntest) > 0:
            logger.warning(
                "Grouped train/eval split has only %s family group; keeping all %s rows in train to avoid family leakage",
                len(groups),
                len(data),
            )
        return list(data), []
    group_items = []
    for key, rows in groups.items():
        roles = Counter(getattr(row, "generator_training_role", "unknown") for row in rows)
        role = roles.most_common(1)[0][0] if roles else "unknown"
        group_items.append({"key": key, "rows": rows, "role": role, "size": len(rows)})
    reserved_train_keys = set()
    for role in {item["role"] for item in group_items}:
        role_groups = [item for item in group_items if item["role"] == role]
        reserved = sorted(role_groups, key=lambda item: (-item["size"], item["key"]))[0]
        reserved_train_keys.add(reserved["key"])

    desired_test = max(1, min(int(ntest), max(1, len(data) // 5)))
    test_set = []
    train_set = []
    eval_candidates = sorted(
        [item for item in group_items if item["key"] not in reserved_train_keys],
        key=lambda item: (item["size"], item["role"], item["key"]),
    )
    for item in eval_candidates:
        if len(test_set) < desired_test:
            test_set.extend(item["rows"])
        else:
            train_set.extend(item["rows"])
    for item in group_items:
        if item["key"] in reserved_train_keys:
            train_set.extend(item["rows"])
    if not train_set:
        return make_train_test(data, ntest)
    if not test_set and eval_candidates:
        moved = eval_candidates[0]
        train_set = [row for row in train_set if row not in moved["rows"]]
        test_set.extend(moved["rows"])
    return train_set, test_set


def compute_unique_data(old_data, new_data=None):
    def add_unique(src, unique_hashes):
        des = []
        for d in src:
            if d.features not in unique_hashes:
                unique_hashes.add(d.features)
                des.append(d)
        return des, unique_hashes

    unique_hashes = set()
    unique_old_data, unique_hashes = add_unique(old_data, unique_hashes)
    if new_data is not None:
        unique_new_data, unique_hashes = add_unique(new_data, unique_hashes)
    else:
        unique_new_data = None
    return unique_old_data, unique_new_data


def update_datasets(args, data, train_set, test_set, train_path, test_path):
    inc_temp = False
    if args.keep_only_unique:
        bef = len(data)
        data, _ = compute_unique_data(data)
        aft = len(data)
        logger.info(f"Unique processing: {aft} examples left, {bef-aft} duplicates")
        do_stats(-1, data)
        if aft / (bef + 1) < 0.9:
            inc_temp = True
    if args.new_proportion > 0.0:
        new_data = select_best(int(args.new_proportion * args.pop_size), data)
    else:
        new_data = select_best(args.pop_size, data)

    if len(new_data) >= 2 * args.ntest or test_set is None:
        new_train, test_set = make_train_test(new_data, args.ntest)
    else:
        new_train = new_data
    logger.info(f"New train and test generated. Size are train: {len(new_train)}, test {len(test_set)}")
    # Get all examples of previous train and current train and then select best.
    if args.keep_only_unique:
        train_set, new_train = compute_unique_data(train_set, new_train)
        logger.info(f"Unique data computed for original train set: {len(train_set)}, generated train set: {len(new_train)}")
    if args.new_proportion > 0.0:
        train_set = select_best(int((1.0 - args.new_proportion) * args.pop_size), train_set) + new_train
    else:
        train_set = select_best(args.pop_size, train_set + new_train)
    logger.info(f"Final train and test generated. Size are train: {len(train_set)}, test {len(test_set)}")

    pickle.dump(test_set, open(test_path, "wb"))
    pickle.dump(train_set, open(train_path, "wb"))
    return train_set, test_set, inc_temp


def load_initial_data(args, classname):
    train_data_path = os.path.join(args.dump_path, "train_data.pkl")
    test_data_path = os.path.join(args.dump_path, "test_data.pkl")
    if os.path.isfile(train_data_path):
        logger.info("resuming from existing data")
        train_set = pickle.load(open(train_data_path, "rb"))
        test_set = pickle.load(open(test_data_path, "rb"))
    else:
        loaded = _load_igp24_training_jsonl(args, classname)
        if loaded is not None:
            train_set, test_set, skipped = loaded
            if not train_set:
                raise ValueError("IGP24 JSONL training data produced no train rows")
            os.makedirs(args.dump_path, exist_ok=True)
            pickle.dump(test_set, open(test_data_path, "wb"))
            pickle.dump(train_set, open(train_data_path, "wb"))
            args.igp24_training_jsonl_loaded_rows = len(train_set) + len(test_set)
            args.igp24_training_jsonl_train_rows = len(train_set)
            args.igp24_training_jsonl_eval_rows = len(test_set)
            args.igp24_training_jsonl_skipped = skipped
        else:
            data = generate_and_score(args, classname=classname)
            test_set = []
            train_set = []
            train_set, test_set, _ = update_datasets(args, data, train_set, test_set, train_data_path, test_data_path)
    return train_set, test_set


class CharDataset(Dataset):
    def __init__(self, encoded_data, max_len, stoi, block_size=None, sample_weights=None, sample_metadata=None):
        self.encoded_data = encoded_data
        self.max_len = max_len
        self.block_size = int(block_size or (max_len + 2))
        self.pad_token_id = stoi["PAD"]
        self.sample_weights = list(sample_weights or [])
        self.sample_metadata = list(sample_metadata or [])
        if self.sample_weights and len(self.sample_weights) != len(self.encoded_data):
            raise ValueError("sample_weights must match encoded_data length")
        if self.sample_metadata and len(self.sample_metadata) != len(self.encoded_data):
            raise ValueError("sample_metadata must match encoded_data length")

    def __len__(self):
        return len(self.encoded_data)

    def __getitem__(self, idx):
        return self.encoded_data[idx]

    def collate_fn(self, batch):
        x = np.full((len(batch), self.block_size), self.pad_token_id, dtype=np.int32)

        for i, el in enumerate(batch):
            if el.shape[0] > self.block_size:
                raise ValueError(f"encoded sequence length {el.shape[0]} exceeds block size {self.block_size}")
            x[i, : el.shape[0]] = el
        valid_col = (x != self.pad_token_id).any(axis=0)
        last_col = np.nonzero(valid_col)[0][-1] + 1
        x = x[:, :last_col]
        y = np.concatenate([x[:, 1:], np.full((len(batch), 1), self.pad_token_id, dtype=x.dtype)], axis=1)
        return torch.LongTensor(x), torch.LongTensor(y)


class InfiniteDataLoader:
    """
    Create a infinite datalaoder in PyTorch
    """

    def __init__(self, dataset, seed=None, **kwargs):
        self.sampled_role_counts = Counter()
        self.sampled_label_counts = Counter()
        self.sampled_family_counts = Counter()
        weights = getattr(dataset, "sample_weights", None)
        if weights:
            generator = torch.Generator()
            if seed is not None and int(seed) >= 0:
                generator.manual_seed(int(seed))
            train_sampler = TrackingWeightedReplacementSampler(
                dataset,
                weights=weights,
                num_samples=int(1e10),
                generator=generator,
                on_sample=self._record_sample,
            )
        else:
            train_sampler = torch.utils.data.RandomSampler(dataset, replacement=True, num_samples=int(1e10))
        self.train_loader = DataLoader(dataset, sampler=train_sampler, collate_fn=dataset.collate_fn, **kwargs)
        self.data_iter = iter(self.train_loader)
        self._closed = False

    def _record_sample(self, index):
        metadata = getattr(self.train_loader.dataset, "sample_metadata", None)
        if not metadata or index >= len(metadata):
            return
        row = metadata[index] or {}
        role = str(row.get("role") or "unknown")
        self.sampled_role_counts[role] += 1
        label = row.get("label")
        if label:
            self.sampled_label_counts[str(label)] += 1
        family = row.get("construction_family")
        if family:
            self.sampled_family_counts[str(family)] += 1

    def sampled_counts(self):
        return {
            "role": dict(self.sampled_role_counts),
            "label": dict(self.sampled_label_counts),
            "construction_family": dict(self.sampled_family_counts),
        }

    def next(self):
        try:
            batch = next(self.data_iter)
        except StopIteration:  # this will technically only happen after 1e10 samples... (i.e. basically never)
            self.data_iter = iter(self.train_loader)
            batch = next(self.data_iter)
        return batch

    def close(self):
        if self._closed:
            return
        shutdown_workers = getattr(self.data_iter, "_shutdown_workers", None)
        if shutdown_workers is not None:
            shutdown_workers()
        self.data_iter = None
        self.train_loader = None
        self._closed = True

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


class TrackingWeightedReplacementSampler(torch.utils.data.Sampler):
    def __init__(self, dataset, *, weights, num_samples, generator=None, on_sample=None):
        self.dataset = dataset
        self.weights = torch.as_tensor([float(weight) for weight in weights], dtype=torch.double)
        if self.weights.numel() != len(dataset):
            raise ValueError("weights length must match dataset length")
        if not torch.all(self.weights >= 0):
            raise ValueError("weights must be non-negative")
        if float(self.weights.sum().item()) <= 0.0:
            raise ValueError("at least one sampler weight must be positive")
        self.num_samples = int(num_samples)
        self.generator = generator
        self.on_sample = on_sample

    def __iter__(self):
        produced = 0
        chunk_size = 8192
        while produced < self.num_samples:
            take = min(chunk_size, self.num_samples - produced)
            indices = torch.multinomial(self.weights, take, replacement=True, generator=self.generator).tolist()
            for index in indices:
                if self.on_sample is not None:
                    self.on_sample(int(index))
                yield int(index)
            produced += take

    def __len__(self):
        return self.num_samples
