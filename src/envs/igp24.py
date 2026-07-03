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

    def __init__(self, N=DEGREE, init=False, coeffs=None):
        super().__init__()
        if int(N) != DEGREE:
            raise ValueError(f"IGP24 uses fixed degree {DEGREE}; got N={N}")
        self.N = DEGREE
        self.coefficients = tuple(validate_coefficients(coeffs)) if coeffs is not None else tuple([0] * DEGREE)
        self.analysis = None
        if init:
            self.coefficients = self._random_coefficients()
            self.calc_features()
            self.calc_score()

    @classmethod
    def _random_coefficients(cls):
        coeffs = np.random.randint(-cls.COEFF_BOUND, cls.COEFF_BOUND + 1, size=DEGREE).astype(int).tolist()
        if coeffs[0] == 0:
            coeffs[0] = 1 if np.random.randint(2) == 0 else -1
        return tuple(coeffs)

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
        record = analysis_to_record(
            self.analysis,
            self.score,
            target_r=self.TARGET_R,
            target_t=self.TARGET_T,
            experiment_name=self.EXPERIMENT_NAME,
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
        return tuple(out)

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
        return tuple(out)

    @classmethod
    def _translation_mutation(cls, coeffs, rng):
        for _ in range(4):
            k = rng.choice([-2, -1, 1, 2])
            try:
                translated = translate_coefficients(coeffs, k)
            except Exception:
                continue
            if cls._bounded(translated):
                return translated
        return coeffs

    @classmethod
    def _canonical_mutation(cls, coeffs):
        try:
            canonical, _ = canonicalize_under_translations(
                coeffs,
                radius=cls.TRANSLATION_RADIUS,
                coeff_bound=cls.COEFF_BOUND,
            )
            if cls._bounded(canonical):
                return canonical
        except Exception:
            pass
        return coeffs

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

    def local_search(self, improve_with_local_search):
        if not improve_with_local_search and self.score >= 0:
            return
        seed = self._stable_local_seed(self.coefficients, self.SEED)
        rng = random.Random(seed)

        best_coeffs = tuple(self.coefficients)
        best_score, best_analysis = self._score_coefficients(best_coeffs)
        preserve_target = self.TARGET_R is not None and best_analysis.valid and best_analysis.real_root_count == self.TARGET_R

        for _ in range(max(0, int(self.MAX_LOCAL_SEARCH_STEPS))):
            candidate = self._mutate(best_coeffs, rng)
            if candidate == best_coeffs or not self._bounded(candidate):
                continue
            candidate_score, candidate_analysis = self._score_coefficients(candidate)
            if preserve_target and candidate_analysis.valid and candidate_analysis.real_root_count != self.TARGET_R:
                continue
            if candidate_score > best_score:
                best_coeffs = candidate
                best_score = candidate_score
                best_analysis = candidate_analysis
                if not improve_with_local_search and best_score >= 0:
                    break

        self.coefficients = tuple(best_coeffs)
        self.score = best_score
        self.analysis = best_analysis
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
        self.data_class.TRANSLATION_RADIUS = int(params.igp24_translation_radius)
        self.data_class.KNOWN_HASHES = CandidateLedger(params.igp24_ledger_path).hashes if params.igp24_ledger_path else set()
        self.data_class.ALWAYS_SEARCH = bool(getattr(params, "always_search", False))
        self.data_class.REDEEM_ONLY = bool(getattr(params, "redeem_only", False))

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
