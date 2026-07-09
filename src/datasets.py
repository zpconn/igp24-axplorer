import os
import pickle
import random
import json
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
    }

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
                datapoint.source_metadata = {
                    "source_path": str(path),
                    "source_index": line_index,
                    "dataset_row_id": record.get("dataset_row_id"),
                    "source_role": record.get("source_role"),
                    "derived_class_label": record.get("derived_class_label"),
                    "score_aware_supervision": record.get("score_aware_supervision"),
                    "train_eval_split": record.get("train_eval_split"),
                    "conditioning_target_r": r_value,
                }
                if record.get("train_eval_split") == "eval":
                    test_set.append(datapoint)
                else:
                    train_set.append(datapoint)
        if max_rows > 0 and len(train_set) + len(test_set) >= max_rows:
            break

    if not train_set and test_set:
        train_set, test_set = make_train_test(test_set, min(len(test_set) // 2, int(args.ntest)))
    if not test_set and len(train_set) > max(1, int(args.ntest)):
        train_set, test_set = make_train_test(train_set, min(int(args.ntest), max(1, len(train_set) // 5)))

    logger.info(
        "Loaded IGP24 JSONL training data: train=%s test=%s paths=%s target_rs=%s skipped=%s",
        len(train_set),
        len(test_set),
        [str(path) for path in paths],
        sorted(target_rs),
        skipped,
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
    def __init__(self, encoded_data, max_len, stoi, block_size=None):
        self.encoded_data = encoded_data
        self.max_len = max_len
        self.block_size = int(block_size or (max_len + 2))
        self.pad_token_id = stoi["PAD"]

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

    def __init__(self, dataset, **kwargs):
        train_sampler = torch.utils.data.RandomSampler(dataset, replacement=True, num_samples=int(1e10))
        self.train_loader = DataLoader(dataset, sampler=train_sampler, collate_fn=dataset.collate_fn, **kwargs)
        self.data_iter = iter(self.train_loader)
        self._closed = False

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
