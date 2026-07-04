import hashlib
import json
import logging
import random

import numpy as np

from src.envs.environment import BaseEnvironment, DataPoint
from src.envs.tokenizers import Tokenizer
from src.igp24.ledger import CandidateLedger
from src.igp24.polynomial import (
    DEGREE,
    analysis_to_record,
    canonicalize_under_translations,
    coefficient_height,
    score_candidate,
    stable_canonical_hash,
    translate_coefficients,
    validate_coefficients,
)
from src.utils import bool_flag

logger = logging.getLogger(__name__)

IGP24_GENERATION_STRATEGIES = [
    "uniform",
    "low_height",
    "sparse",
    "lower_degree",
    "structured",
    "four_real_seed",
    "quartic_lift",
]
DEFAULT_MIXED_STRATEGY_WEIGHTS = {
    "uniform": 0.10,
    "low_height": 0.20,
    "sparse": 0.25,
    "lower_degree": 0.20,
    "structured": 0.25,
    "four_real_seed": 0.0,
    "quartic_lift": 0.0,
}
IGP24_GENERATION_PRESETS = {
    "none": {
        "target_r": None,
        "strategy": None,
        "mixed_strategy_weights": None,
    },
    "r0": {
        "target_r": 0,
        "strategy": "structured",
        "mixed_strategy_weights": None,
    },
    "r2": {
        "target_r": 2,
        "strategy": "mixed",
        "mixed_strategy_weights": {"sparse": 0.55, "structured": 0.45},
    },
    "r4": {
        "target_r": 4,
        "strategy": "mixed",
        "mixed_strategy_weights": {"four_real_seed": 0.80, "sparse": 0.20},
    },
}


def parse_mixed_strategy_weights(value):
    if isinstance(value, dict):
        weights = {str(key): float(weight) for key, weight in value.items()}
    else:
        weights = {}
        for item in str(value).split(","):
            item = item.strip()
            if not item:
                continue
            if ":" not in item:
                raise ValueError("mixed strategy weights must use name:weight entries")
            name, weight = item.split(":", 1)
            weights[name.strip()] = float(weight)

    unknown = set(weights) - set(IGP24_GENERATION_STRATEGIES)
    if unknown:
        raise ValueError(f"unknown mixed strategy weight keys: {sorted(unknown)}")
    if not weights:
        raise ValueError("at least one mixed strategy weight is required")
    if any(weight < 0 for weight in weights.values()):
        raise ValueError("mixed strategy weights must be nonnegative")
    total = sum(weights.values())
    if total <= 0:
        raise ValueError("mixed strategy weights must have positive total weight")

    normalized = {name: weights.get(name, 0.0) / total for name in IGP24_GENERATION_STRATEGIES}
    return normalized


def format_mixed_strategy_weights(weights):
    return ",".join(f"{name}:{weights[name]:.4f}" for name in IGP24_GENERATION_STRATEGIES)


def resolve_generation_preset(preset, generation_strategy, mixed_strategy_weights):
    preset_name = str(preset or "none").strip().lower()
    if preset_name not in IGP24_GENERATION_PRESETS:
        raise ValueError(f"unknown IGP24 generation preset: {preset_name}")

    resolved_strategy = str(generation_strategy)
    resolved_weights = parse_mixed_strategy_weights(mixed_strategy_weights)
    target_r_intent = None
    if preset_name != "none":
        spec = IGP24_GENERATION_PRESETS[preset_name]
        resolved_strategy = spec["strategy"] or resolved_strategy
        target_r_intent = spec["target_r"]
        if spec["mixed_strategy_weights"] is not None:
            resolved_weights = parse_mixed_strategy_weights(spec["mixed_strategy_weights"])

    return {
        "preset_name": preset_name,
        "target_r_intent": target_r_intent,
        "resolved_strategy": resolved_strategy,
        "resolved_mixed_strategy_weights": resolved_weights,
    }


class IGP24CoefficientTokenizer(Tokenizer):
    """Fixed-length signed coefficient tokenizer using coeff + coeff_bound."""

    def __init__(self, dataclass, coeff_bound, extra_symbols):
        super().__init__()
        self.dataclass = dataclass
        self.N = DEGREE
        self.coeff_bound = int(coeff_bound)
        self.extra_symbols = extra_symbols
        self.stoi = {}
        self.itos = {}

        for token_id, coeff in enumerate(range(-self.coeff_bound, self.coeff_bound + 1)):
            self.stoi[coeff] = token_id
            self.itos[token_id] = coeff

        offset = len(self.stoi)
        for idx, symbol in enumerate(extra_symbols):
            token_id = offset + idx
            self.stoi[symbol] = token_id
            self.itos[token_id] = symbol

    def encode(self, datapoint_to_encode):
        coeffs = validate_coefficients(datapoint_to_encode.coefficients)
        tokens = [self.stoi["BOS"]]
        for coeff in coeffs:
            if coeff < -self.coeff_bound or coeff > self.coeff_bound:
                raise ValueError(f"coefficient outside tokenizer bound: {coeff}")
            tokens.append(self.stoi[coeff])
        tokens.append(self.stoi["EOS"])
        return np.array(tokens, dtype=np.int32)

    def decode(self, token_seq_to_decode):
        if len(token_seq_to_decode) == 0:
            return None
        token_seq_to_decode = token_seq_to_decode[1:]
        coeffs = []
        try:
            for token in token_seq_to_decode:
                value = self.itos[int(token)]
                if value in self.extra_symbols:
                    break
                coeffs.append(value)
                if len(coeffs) == DEGREE:
                    break
        except Exception:
            return None
        if len(coeffs) != DEGREE:
            return None
        return self.dataclass(N=DEGREE, coeffs=coeffs)


class IGP24DataPoint(DataPoint):
    COEFF_BOUND = 10
    TARGET_R = None
    TARGET_T = None
    PRIME_LIMIT = 31
    MAX_LOCAL_SEARCH_STEPS = 50
    DISCRIMINANT_WEIGHT = 1.0
    HEIGHT_WEIGHT = 1.0
    CYCLE_DIVERSITY_WEIGHT = 5.0
    EXACT_SCORE_TIMEOUT = 0.0
    LEDGER_PATH = "data/igp24/candidates.jsonl"
    WRITE_LEDGER = True
    EXPERIMENT_NAME = "igp24"
    SEED = 0
    TRANSLATION_RADIUS = 2
    KNOWN_HASHES = set()
    ALWAYS_SEARCH = False
    REDEEM_ONLY = False
    GENERATION_STRATEGY = "mixed"
    SPARSE_TERMS = 4
    LOW_HEIGHT_BOUND = 3
    MIXED_STRATEGY_WEIGHTS = DEFAULT_MIXED_STRATEGY_WEIGHTS.copy()
    GENERATION_PRESET = "none"
    GENERATION_PRESET_TARGET_R = None

    def __init__(self, N=DEGREE, init=False, coeffs=None, generation_strategy=None):
        super().__init__()
        if int(N) != DEGREE:
            raise ValueError(f"IGP24 uses fixed degree {DEGREE}; got N={N}")
        self.N = DEGREE
        self.coefficients = tuple(validate_coefficients(coeffs)) if coeffs is not None else tuple([0] * DEGREE)
        self.analysis = None
        self.generation_strategy = generation_strategy or "manual"
        self.local_search_stats = {}
        if init:
            self.coefficients, self.generation_strategy = self._generate_coefficients()
            self.calc_features()
            self.calc_score()

    @classmethod
    def _nonzero_random_int(cls, bound):
        bound = max(1, int(bound))
        value = 0
        while value == 0:
            value = int(np.random.randint(-bound, bound + 1))
        return value

    @classmethod
    def _uniform_coefficients(cls):
        coeffs = np.random.randint(-cls.COEFF_BOUND, cls.COEFF_BOUND + 1, size=DEGREE).astype(int).tolist()
        if coeffs[0] == 0:
            coeffs[0] = 1 if np.random.randint(2) == 0 else -1
        return tuple(coeffs)

    @classmethod
    def _low_height_coefficients(cls):
        inner_bound = max(1, min(cls.COEFF_BOUND, int(cls.LOW_HEIGHT_BOUND)))
        coeffs = np.random.randint(-inner_bound, inner_bound + 1, size=DEGREE).astype(int).tolist()
        if coeffs[0] == 0:
            coeffs[0] = cls._nonzero_random_int(inner_bound)
        return tuple(coeffs)

    @classmethod
    def _sparse_coefficients(cls):
        coeffs = [0] * DEGREE
        coeffs[0] = cls._nonzero_random_int(cls.COEFF_BOUND)
        n_terms = max(1, min(DEGREE, int(cls.SPARSE_TERMS)))
        if n_terms > 1:
            indices = np.random.choice(np.arange(1, DEGREE), size=min(n_terms - 1, DEGREE - 1), replace=False)
            for index in indices:
                coeffs[int(index)] = cls._nonzero_random_int(cls.COEFF_BOUND)
        return tuple(coeffs)

    @classmethod
    def _lower_degree_coefficients(cls):
        coeffs = []
        for index in range(DEGREE):
            scale = ((DEGREE - index) / DEGREE) ** 1.5
            local_bound = max(1, int(round(cls.COEFF_BOUND * scale)))
            zero_probability = min(0.85, 0.15 + 0.65 * (index / (DEGREE - 1)))
            if index > 0 and np.random.random() < zero_probability:
                coeffs.append(0)
            else:
                coeffs.append(int(np.random.randint(-local_bound, local_bound + 1)))
        if coeffs[0] == 0:
            coeffs[0] = cls._nonzero_random_int(cls.COEFF_BOUND)
        return tuple(coeffs)

    @classmethod
    def _structured_coefficients(cls):
        coeffs = [0] * DEGREE
        coeffs[0] = cls._nonzero_random_int(cls.COEFF_BOUND)
        possible_exponents = [1, 2, 3, 4, 6, 8, 12, 16, 18]
        n_extra = int(np.random.choice([1, 2, 3], p=[0.5, 0.35, 0.15]))
        exponents = np.random.choice(possible_exponents, size=n_extra, replace=False)
        inner_bound = max(1, min(cls.COEFF_BOUND, int(cls.LOW_HEIGHT_BOUND)))
        for exponent in exponents:
            coeffs[int(exponent)] = cls._nonzero_random_int(inner_bound)
        return tuple(coeffs)

    @classmethod
    def _four_real_factor_pairs(cls):
        bound = max(1, int(cls.COEFF_BOUND))
        pairs = []
        for a in range(1, bound + 1):
            for b in range(a + 1, bound + 1):
                if a + b <= bound and a * b <= bound:
                    pairs.append((a, b))
        return pairs

    @classmethod
    def _four_real_seed_coefficients(cls):
        pairs = cls._four_real_factor_pairs()
        if not pairs:
            return cls._sparse_coefficients()

        a, b = pairs[int(np.random.randint(len(pairs)))]
        coeffs = [0] * DEGREE
        coeffs[0] = a * b
        coeffs[2] = -(a + b)
        coeffs[4] = 1
        coeffs[20] = a * b
        coeffs[22] = -(a + b)

        odd_indices = list(range(1, DEGREE, 2))
        perturb_count = int(np.random.choice([1, 2, 3], p=[0.5, 0.35, 0.15]))
        perturb_count = min(perturb_count, len(odd_indices))
        for index in np.random.choice(odd_indices, size=perturb_count, replace=False):
            coeffs[int(index)] = cls._nonzero_random_int(1)
        return tuple(coeffs)

    @classmethod
    def _quartic_lift_templates(cls):
        bound = max(1, int(cls.COEFF_BOUND))
        templates = []
        for a in range(1, bound + 1):
            for b in range(a + 1, bound + 1):
                for c in range(1, bound + 1):
                    for d in range(c, bound + 1):
                        y3 = c + d - a - b
                        y2 = (a * b) + (c * d) - ((a + b) * (c + d))
                        y1 = (a * b * (c + d)) - (c * d * (a + b))
                        y0 = a * b * c * d
                        y_coefficients = (y0, y1, y2, y3)
                        if y0 != 0 and all(abs(value) <= bound for value in y_coefficients):
                            templates.append((a, b, c, d, y_coefficients))
        return templates

    @staticmethod
    def _quartic_lift_core_support():
        return (0, 6, 12, 18)

    @classmethod
    def _quartic_lift_coefficients(cls):
        templates = cls._quartic_lift_templates()
        if not templates:
            return cls._sparse_coefficients()

        _, _, _, _, y_coefficients = templates[int(np.random.randint(len(templates)))]
        coeffs = [0] * DEGREE
        for exponent, coefficient in zip(cls._quartic_lift_core_support(), y_coefficients):
            coeffs[exponent] = int(coefficient)

        perturbable = [index for index in range(DEGREE) if index not in cls._quartic_lift_core_support()]
        perturb_count = int(np.random.choice([1, 2, 3], p=[0.5, 0.35, 0.15]))
        perturb_count = min(perturb_count, len(perturbable))
        for index in np.random.choice(perturbable, size=perturb_count, replace=False):
            coeffs[int(index)] = cls._nonzero_random_int(1)
        return tuple(coeffs)

    @classmethod
    def _select_generation_strategy(cls):
        strategy = cls.GENERATION_STRATEGY
        if strategy != "mixed":
            return strategy
        weights = parse_mixed_strategy_weights(cls.MIXED_STRATEGY_WEIGHTS)
        probabilities = [weights[name] for name in IGP24_GENERATION_STRATEGIES]
        return str(np.random.choice(IGP24_GENERATION_STRATEGIES, p=probabilities))

    @classmethod
    def _generate_coefficients(cls):
        strategy = cls._select_generation_strategy()
        if strategy == "uniform":
            return cls._uniform_coefficients(), strategy
        if strategy == "low_height":
            return cls._low_height_coefficients(), strategy
        if strategy == "sparse":
            return cls._sparse_coefficients(), strategy
        if strategy == "lower_degree":
            return cls._lower_degree_coefficients(), strategy
        if strategy == "structured":
            return cls._structured_coefficients(), strategy
        if strategy == "four_real_seed":
            return cls._four_real_seed_coefficients(), strategy
        if strategy == "quartic_lift":
            return cls._quartic_lift_coefficients(), strategy
        raise ValueError(f"Unknown IGP24 generation strategy: {strategy}")

    @classmethod
    def _batch_generate_and_score(cls, batch_size, N, pars=None):
        out = []
        if pars is not None:
            cls._update_class_params(pars)
        for _ in range(batch_size):
            datapoint = cls(N=N, init=True)
            invalid = datapoint.score < 0
            if cls.ALWAYS_SEARCH:
                datapoint.local_search(improve_with_local_search=True)
            elif invalid and cls.REDEEM_ONLY:
                datapoint.local_search(improve_with_local_search=False)
            if datapoint.score >= 0:
                out.append(datapoint)
        return out

    @classmethod
    def _score_coefficients(cls, coeffs):
        return score_candidate(
            coeffs,
            coeff_bound=cls.COEFF_BOUND,
            target_r=cls.TARGET_R,
            target_t=cls.TARGET_T,
            prime_limit=cls.PRIME_LIMIT,
            discriminant_weight=cls.DISCRIMINANT_WEIGHT,
            height_weight=cls.HEIGHT_WEIGHT,
            cycle_diversity_weight=cls.CYCLE_DIVERSITY_WEIGHT,
            exact_score_timeout=cls.EXACT_SCORE_TIMEOUT,
            seen_hashes=cls.KNOWN_HASHES,
            translation_radius=cls.TRANSLATION_RADIUS,
        )

    def calc_score(self):
        self.score, self.analysis = self._score_coefficients(self.coefficients)
        self.calc_features()
        self._append_to_ledger_if_valid()

    def calc_features(self):
        if self.analysis is not None and self.analysis.canonical_hash:
            self.features = self.analysis.canonical_hash
            return
        try:
            self.features = stable_canonical_hash(
                self.coefficients,
                radius=self.TRANSLATION_RADIUS,
                coeff_bound=self.COEFF_BOUND,
            )
        except Exception:
            payload = json.dumps(list(self.coefficients), separators=(",", ":"))
            self.features = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _append_to_ledger_if_valid(self):
        if not self.WRITE_LEDGER or not self.LEDGER_PATH or self.analysis is None or not self.analysis.valid:
            return
        generation_metadata = {
            "strategy": self.generation_strategy,
            "generation_preset": self.GENERATION_PRESET,
            "preset_target_r": self.GENERATION_PRESET_TARGET_R,
            "resolved_generation_strategy": self.GENERATION_STRATEGY,
            "resolved_mixed_strategy_weights": dict(self.MIXED_STRATEGY_WEIGHTS),
            "coeff_bound": self.COEFF_BOUND,
            "sparse_terms": self.SPARSE_TERMS,
            "low_height_bound": self.LOW_HEIGHT_BOUND,
            "mixed_strategy_weights": dict(self.MIXED_STRATEGY_WEIGHTS),
        }
        if self.generation_strategy == "four_real_seed":
            generation_metadata.update(
                {
                    "target_r_heuristic": 4,
                    "seed_template": "perturbed_(x^2-a)(x^2-b)(x^20+1)",
                    "perturbation": "one_to_three_odd_coefficients",
                }
            )
        if self.generation_strategy == "quartic_lift":
            core_support = self._quartic_lift_core_support()
            perturbations = {
                str(index): int(self.coefficients[index])
                for index in range(DEGREE)
                if index not in core_support and self.coefficients[index] != 0
            }
            generation_metadata.update(
                {
                    "target_r_heuristic": 4,
                    "seed_template": "perturbed_(y-a)(y-b)(y+c)(y+d)_with_y=x^6",
                    "quartic_lift_core_support": list(core_support),
                    "quartic_lift_coefficients_y": [
                        int(self.coefficients[0]),
                        int(self.coefficients[6]),
                        int(self.coefficients[12]),
                        int(self.coefficients[18]),
                        1,
                    ],
                    "perturbation": "one_to_three_non_core_coefficients",
                    "perturbation_coefficients": perturbations,
                }
            )
        record = analysis_to_record(
            self.analysis,
            self.score,
            target_r=self.TARGET_R,
            target_t=self.TARGET_T,
            experiment_name=self.EXPERIMENT_NAME,
            generation_metadata=generation_metadata,
            local_search_metadata=self.local_search_stats,
        )
        try:
            ledger = CandidateLedger(self.LEDGER_PATH)
            if ledger.append(record):
                self.KNOWN_HASHES.add(self.analysis.canonical_hash)
        except Exception as exc:
            logger.warning("Could not append IGP24 candidate ledger record: %s", exc)

    @staticmethod
    def _stable_local_seed(coeffs, seed):
        payload = json.dumps({"seed": int(seed), "coefficients": list(coeffs)}, separators=(",", ":"))
        return int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")

    @classmethod
    def _bounded(cls, coeffs):
        try:
            return coefficient_height(coeffs) <= cls.COEFF_BOUND
        except Exception:
            return False

    @classmethod
    def _single_mutation(cls, coeffs, rng):
        out = list(coeffs)
        index = min(DEGREE - 1, int((rng.random() ** 1.8) * DEGREE))
        delta = rng.choice([-3, -2, -1, 1, 2, 3])
        out[index] = max(-cls.COEFF_BOUND, min(cls.COEFF_BOUND, out[index] + delta))
        if index == 0 and out[index] == 0:
            out[index] = 1 if delta > 0 else -1
        return tuple(out), "single"

    @classmethod
    def _few_mutation(cls, coeffs, rng):
        out = list(coeffs)
        count = rng.randint(2, 4)
        for _ in range(count):
            index = min(DEGREE - 1, int((rng.random() ** 1.8) * DEGREE))
            delta = rng.choice([-2, -1, 1, 2])
            out[index] = max(-cls.COEFF_BOUND, min(cls.COEFF_BOUND, out[index] + delta))
        if out[0] == 0:
            out[0] = rng.choice([-1, 1])
        return tuple(out), "few"

    @classmethod
    def _translation_mutation(cls, coeffs, rng):
        for _ in range(4):
            k = rng.choice([-2, -1, 1, 2])
            try:
                translated = translate_coefficients(coeffs, k)
            except Exception:
                continue
            if cls._bounded(translated):
                return translated, f"translate_{k}"
        return coeffs, "translate_failed"

    @classmethod
    def _canonical_mutation(cls, coeffs):
        try:
            canonical, _ = canonicalize_under_translations(
                coeffs,
                radius=cls.TRANSLATION_RADIUS,
                coeff_bound=cls.COEFF_BOUND,
            )
            if cls._bounded(canonical):
                return canonical, "canonicalize"
        except Exception:
            pass
        return coeffs, "canonicalize_failed"

    @classmethod
    def _mutate(cls, coeffs, rng):
        move = rng.random()
        if move < 0.55:
            return cls._single_mutation(coeffs, rng)
        if move < 0.82:
            return cls._few_mutation(coeffs, rng)
        if move < 0.95:
            return cls._translation_mutation(coeffs, rng)
        return cls._canonical_mutation(coeffs)

    @classmethod
    def _analysis_metrics(cls, analysis, score):
        if analysis is None or not analysis.valid:
            return {
                "score": score,
                "height": None,
                "log_abs_discriminant": None,
                "target_r_distance": None,
                "cycle_diversity_count": 0,
            }
        target_r_distance = None
        if cls.TARGET_R is not None and analysis.real_root_count is not None:
            target_r_distance = abs(int(cls.TARGET_R) - int(analysis.real_root_count))
        return {
            "score": score,
            "height": analysis.coefficient_height,
            "log_abs_discriminant": analysis.log_abs_discriminant,
            "target_r_distance": target_r_distance,
            "cycle_diversity_count": len({pattern.degrees for pattern in analysis.mod_p_factorization_degree_patterns}),
        }

    @staticmethod
    def _improvement_flags(before, after):
        flags = {"score": after["score"] > before["score"]}
        for key in ["height", "log_abs_discriminant", "target_r_distance"]:
            flags[key] = before[key] is not None and after[key] is not None and after[key] < before[key]
        flags["cycle_diversity_count"] = after["cycle_diversity_count"] > before["cycle_diversity_count"]
        return flags

    def local_search(self, improve_with_local_search):
        if not improve_with_local_search and self.score >= 0:
            return
        seed = self._stable_local_seed(self.coefficients, self.SEED)
        rng = random.Random(seed)

        best_coeffs = tuple(self.coefficients)
        best_score, best_analysis = self._score_coefficients(best_coeffs)
        preserve_target = self.TARGET_R is not None and best_analysis.valid and best_analysis.real_root_count == self.TARGET_R
        start_metrics = self._analysis_metrics(best_analysis, best_score)
        accepted_moves = {}
        rejected_reasons = {}
        attempted = 0
        accepted = 0
        last_improvements = {}

        for _ in range(max(0, int(self.MAX_LOCAL_SEARCH_STEPS))):
            candidate, move_type = self._mutate(best_coeffs, rng)
            attempted += 1
            if candidate == best_coeffs:
                rejected_reasons["unchanged"] = rejected_reasons.get("unchanged", 0) + 1
                continue
            if not self._bounded(candidate):
                rejected_reasons["out_of_bounds"] = rejected_reasons.get("out_of_bounds", 0) + 1
                continue
            candidate_score, candidate_analysis = self._score_coefficients(candidate)
            if preserve_target and candidate_analysis.valid and candidate_analysis.real_root_count != self.TARGET_R:
                rejected_reasons["target_r_changed"] = rejected_reasons.get("target_r_changed", 0) + 1
                continue
            if candidate_score > best_score:
                before_metrics = self._analysis_metrics(best_analysis, best_score)
                best_coeffs = candidate
                best_score = candidate_score
                best_analysis = candidate_analysis
                after_metrics = self._analysis_metrics(best_analysis, best_score)
                accepted += 1
                accepted_moves[move_type] = accepted_moves.get(move_type, 0) + 1
                last_improvements = self._improvement_flags(before_metrics, after_metrics)
                if not improve_with_local_search and best_score >= 0:
                    break
            else:
                rejected_reasons["not_improved"] = rejected_reasons.get("not_improved", 0) + 1

        self.coefficients = tuple(best_coeffs)
        self.score = best_score
        self.analysis = best_analysis
        end_metrics = self._analysis_metrics(best_analysis, best_score)
        self.local_search_stats = {
            "attempted": attempted,
            "accepted": accepted,
            "rejected": attempted - accepted,
            "accepted_moves": accepted_moves,
            "rejected_reasons": rejected_reasons,
            "start": start_metrics,
            "end": end_metrics,
            "improved_from_start": self._improvement_flags(start_metrics, end_metrics),
            "last_accepted_improvements": last_improvements,
            "max_steps": int(self.MAX_LOCAL_SEARCH_STEPS),
            "seed": int(self.SEED),
        }
        self.calc_features()
        self._append_to_ledger_if_valid()

    @classmethod
    def _update_class_params(cls, pars):
        for key, value in pars.items():
            setattr(cls, key, value)
        cls.KNOWN_HASHES = set(cls.KNOWN_HASHES)

    @classmethod
    def _save_class_params(cls):
        return {
            "COEFF_BOUND": cls.COEFF_BOUND,
            "TARGET_R": cls.TARGET_R,
            "TARGET_T": cls.TARGET_T,
            "PRIME_LIMIT": cls.PRIME_LIMIT,
            "MAX_LOCAL_SEARCH_STEPS": cls.MAX_LOCAL_SEARCH_STEPS,
            "DISCRIMINANT_WEIGHT": cls.DISCRIMINANT_WEIGHT,
            "HEIGHT_WEIGHT": cls.HEIGHT_WEIGHT,
            "CYCLE_DIVERSITY_WEIGHT": cls.CYCLE_DIVERSITY_WEIGHT,
            "EXACT_SCORE_TIMEOUT": cls.EXACT_SCORE_TIMEOUT,
            "LEDGER_PATH": cls.LEDGER_PATH,
            "WRITE_LEDGER": cls.WRITE_LEDGER,
            "EXPERIMENT_NAME": cls.EXPERIMENT_NAME,
            "SEED": cls.SEED,
            "TRANSLATION_RADIUS": cls.TRANSLATION_RADIUS,
            "KNOWN_HASHES": set(cls.KNOWN_HASHES),
            "ALWAYS_SEARCH": cls.ALWAYS_SEARCH,
            "REDEEM_ONLY": cls.REDEEM_ONLY,
            "GENERATION_STRATEGY": cls.GENERATION_STRATEGY,
            "SPARSE_TERMS": cls.SPARSE_TERMS,
            "LOW_HEIGHT_BOUND": cls.LOW_HEIGHT_BOUND,
            "MIXED_STRATEGY_WEIGHTS": dict(cls.MIXED_STRATEGY_WEIGHTS),
            "GENERATION_PRESET": cls.GENERATION_PRESET,
            "GENERATION_PRESET_TARGET_R": cls.GENERATION_PRESET_TARGET_R,
        }


class IGP24Environment(BaseEnvironment):
    data_class = IGP24DataPoint

    def __init__(self, params):
        super().__init__(params)
        if int(params.N) != DEGREE:
            raise ValueError(f"IGP24 uses fixed degree {DEGREE}; got --N {params.N}")
        if params.encoding_tokens != "coefficients":
            raise ValueError("IGP24 currently supports --encoding_tokens coefficients")

        self.data_class.COEFF_BOUND = int(params.coeff_bound)
        self.data_class.TARGET_R = params.target_r
        self.data_class.TARGET_T = params.target_t
        self.data_class.PRIME_LIMIT = int(params.prime_limit)
        self.data_class.MAX_LOCAL_SEARCH_STEPS = int(params.max_local_search_steps)
        self.data_class.DISCRIMINANT_WEIGHT = float(params.discriminant_weight)
        self.data_class.HEIGHT_WEIGHT = float(params.height_weight)
        self.data_class.CYCLE_DIVERSITY_WEIGHT = float(params.cycle_diversity_weight)
        self.data_class.EXACT_SCORE_TIMEOUT = float(params.exact_score_timeout)
        self.data_class.LEDGER_PATH = params.igp24_ledger_path
        self.data_class.WRITE_LEDGER = bool(params.igp24_write_ledger)
        self.data_class.EXPERIMENT_NAME = params.exp_name
        self.data_class.SEED = int(params.seed)
        if int(params.seed) >= 0:
            np.random.seed(int(params.seed))
        self.data_class.TRANSLATION_RADIUS = int(params.igp24_translation_radius)
        self.data_class.KNOWN_HASHES = CandidateLedger(params.igp24_ledger_path).hashes if params.igp24_ledger_path else set()
        self.data_class.ALWAYS_SEARCH = bool(getattr(params, "always_search", False))
        self.data_class.REDEEM_ONLY = bool(getattr(params, "redeem_only", False))
        generation_resolution = resolve_generation_preset(
            getattr(params, "igp24_generation_preset", "none"),
            params.igp24_generation_strategy,
            params.igp24_mixed_strategy_weights,
        )
        self.data_class.GENERATION_STRATEGY = generation_resolution["resolved_strategy"]
        self.data_class.SPARSE_TERMS = int(params.igp24_sparse_terms)
        self.data_class.LOW_HEIGHT_BOUND = int(params.igp24_low_height_bound)
        self.data_class.MIXED_STRATEGY_WEIGHTS = generation_resolution["resolved_mixed_strategy_weights"]
        self.data_class.GENERATION_PRESET = generation_resolution["preset_name"]
        self.data_class.GENERATION_PRESET_TARGET_R = generation_resolution["target_r_intent"]

        self.tokenizer = IGP24CoefficientTokenizer(self.data_class, params.coeff_bound, self.SPECIAL_SYMBOLS)

    @staticmethod
    def register_args(parser):
        parser.add_argument("--N", type=int, default=DEGREE, help="Fixed IGP24 degree; must remain 24")
        parser.add_argument("--encoding_tokens", type=str, default="coefficients", help="IGP24 fixed signed coefficient vector tokenizer")
        parser.add_argument("--coeff_bound", type=int, default=10, help="Search bound for coefficients a0..a23")
        parser.add_argument("--target_r", type=int, default=None, help="Optional target real-root count")
        parser.add_argument("--target_t", type=str, default=None, help="Optional target 24Tt metadata; not exact-scored in stage 0")
        parser.add_argument("--prime_limit", type=int, default=31, help="Largest small prime for modular factorization proxy data")
        parser.add_argument("--max_local_search_steps", type=int, default=50, help="Bounded local-search mutation steps")
        parser.add_argument("--discriminant_weight", type=float, default=1.0, help="Penalty weight for log(abs(discriminant))")
        parser.add_argument("--height_weight", type=float, default=1.0, help="Penalty weight for coefficient height")
        parser.add_argument("--cycle_diversity_weight", type=float, default=5.0, help="Bonus weight for mod-p factorization diversity")
        parser.add_argument("--exact_score_timeout", type=float, default=0.0, help="Optional per-candidate exact scoring timeout in seconds")
        parser.add_argument("--igp24_ledger_path", type=str, default="data/igp24/candidates.jsonl", help="JSONL candidate ledger path")
        parser.add_argument("--igp24_write_ledger", type=bool_flag, default="true", help="Write valid proxy-scored candidates to the JSONL ledger")
        parser.add_argument("--igp24_translation_radius", type=int, default=2, help="Small translation radius for canonical hashes")
        parser.add_argument(
            "--igp24_generation_strategy",
            type=str,
            default="mixed",
            choices=["mixed"] + IGP24_GENERATION_STRATEGIES,
            help="Initial IGP24 coefficient generation strategy",
        )
        parser.add_argument(
            "--igp24_generation_preset",
            type=str,
            default="none",
            choices=sorted(IGP24_GENERATION_PRESETS),
            help="Optional target-specific generation preset; none preserves explicit strategy settings",
        )
        parser.add_argument("--igp24_sparse_terms", type=int, default=4, help="Number of nonzero free coefficients for sparse generation")
        parser.add_argument("--igp24_low_height_bound", type=int, default=3, help="Inner coefficient bound for low-height and structured generation")
        parser.add_argument(
            "--igp24_mixed_strategy_weights",
            type=str,
            default=format_mixed_strategy_weights(DEFAULT_MIXED_STRATEGY_WEIGHTS),
            help="Comma-separated name:weight entries used when --igp24_generation_strategy mixed",
        )
