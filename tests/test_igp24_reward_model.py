import json

from scripts.igp24_score_reward_model import load_model, score_rows
from scripts.igp24_train_reward_model import main as train_reward_model_main
from src.igp24.reward_model import (
    AdvisoryRewardModel,
    OUTCOME_ACCEPTED_DUPLICATE,
    DEFAULT_FEATURE_KEYS,
    OUTCOME_CROWDED_COLLAPSE,
    OUTCOME_NO_VALUABLE_TARGET_SURVIVAL,
    OUTCOME_SCORE_POSITIVE,
    OUTCOME_UNKNOWN,
    build_training_artifacts,
    group_key_from_record,
    outcome_from_record,
    positive_vs_crowded_diagnostic,
    ranked_family_risk,
    train_reward_model,
    write_jsonl,
)


def _record(
    *,
    outcome: str,
    family: str,
    r: int = 8,
    coefficient: int = 1,
    label: str = "",
    team_count: int = 0,
) -> dict:
    score_label = {
        "score_positive": "score_positive",
        "low_team_scoreable": "low_team_scoreable",
        "crowded_accepted_collapse": "accepted_but_crowded_collapse",
        "accepted_duplicate": "accepted_duplicate",
        "wrong_r": "wrong_r",
        "invalid": "invalid",
        "unknown": "pending_or_unknown",
    }[outcome]
    role = {
        "score_positive": "score_positive",
        "low_team_scoreable": "low_team_scoreable",
        "crowded_accepted_collapse": "crowded_collapse",
        "accepted_duplicate": "accepted_duplicate",
        "wrong_r": "wrong_r",
        "invalid": "invalid",
        "unknown": "exact_local_exploration",
    }[outcome]
    return {
        "canonical_hash": f"hash-{outcome}-{family}-{coefficient}",
        "dataset_row_id": f"row-{outcome}-{family}-{coefficient}",
        "coefficients": [coefficient] + [0] * 23 + [1],
        "r": r,
        "derived_class_label": "exact_local_valid",
        "features": {
            "r": r,
            "coefficient_height": abs(coefficient),
            "construction_family": family,
            "template_family_id": f"{family}:template",
            "family_key": f"{family}:key",
            "basin_fingerprint": f"{family}:basin",
            "decomposition_pattern": f"{family}:pattern",
            "perturbation_mode": f"{family}:mode",
            "sparse_support_submode": f"{family}:sparse",
            "support_gcd": 1,
            "even_support": False,
            "odd_support_exponents": [1, 3],
            "mod_p_pattern_signature": f"{family}:modsig",
            "label": label,
        },
        "generator_training": {
            "eligible": outcome in {"score_positive", "low_team_scoreable", "unknown"},
            "weight": 12.0 if outcome == "score_positive" else 1.0,
            "role": role,
            "split_group_key": f"construction_family:{family}",
            "construction_family": family,
            "basin_fingerprint": f"{family}:basin",
        },
        "score_aware_supervision": {
            "label": score_label,
            "signature_team_count": team_count,
            "label_team_count": team_count,
        },
        "sair_feedback": {
            "status": "accepted" if outcome in {"score_positive", "crowded_accepted_collapse"} else None,
            "scoreable": outcome in {"score_positive", "crowded_accepted_collapse"},
            "label": label,
            "pair_key": f"{label}|r={r}" if label else None,
        },
        "progress_context": {
            "signature_team_count": team_count,
            "label_team_count": team_count,
        },
    }


def _training_rows() -> list[dict]:
    rows = []
    for i in range(6):
        rows.append(_record(outcome="score_positive", family="rare_good_family", coefficient=i + 1, label="24T9993"))
    for i in range(8):
        rows.append(
            _record(
                outcome="crowded_accepted_collapse",
                family="crowded_24T25000_family",
                coefficient=20 + i,
                label="24T25000",
                team_count=50,
            )
        )
    for i in range(3):
        rows.append(_record(outcome="wrong_r", family="wrong_r_family", r=6, coefficient=40 + i))
    for i in range(3):
        rows.append(_record(outcome="invalid", family="invalid_family", coefficient=50 + i))
    for i in range(4):
        rows.append(_record(outcome="unknown", family="unknown_family", coefficient=60 + i))
    return rows


def test_reward_model_outcome_mapping_does_not_treat_unknown_as_negative():
    assert outcome_from_record(_record(outcome="score_positive", family="good")) == OUTCOME_SCORE_POSITIVE
    assert outcome_from_record(_record(outcome="crowded_accepted_collapse", family="bad")) == OUTCOME_CROWDED_COLLAPSE
    assert outcome_from_record(_record(outcome="unknown", family="mystery")) == OUTCOME_UNKNOWN

    model = train_reward_model([_record(outcome="unknown", family="mystery")])
    assert model.class_counts == {}


def test_non_improving_exact_pair_role_overrides_pair_level_score_positive_label():
    row = _record(outcome="score_positive", family="known_pair_duplicate", label="24T9993")
    row["generator_training"]["role"] = "non_improving_exact_pair"

    assert outcome_from_record(row) == OUTCOME_ACCEPTED_DUPLICATE


def test_no_valuable_target_survival_is_supervised_collapse_risk():
    row = _record(outcome="unknown", family="no_value_family")
    row["generator_training"]["role"] = "no_valuable_target_survival"

    assert outcome_from_record(row) == OUTCOME_NO_VALUABLE_TARGET_SURVIVAL

    model = train_reward_model([row])
    prediction = model.predict(row)

    assert model.class_counts == {OUTCOME_NO_VALUABLE_TARGET_SURVIVAL: 1}
    assert prediction.collapse_risk_probability > prediction.reward_probability


def test_no_valuable_target_survival_role_overrides_crowded_score_label():
    row = _record(outcome="crowded_accepted_collapse", family="adaptive_no_value_family")
    row["generator_training"]["role"] = "no_valuable_target_survival"

    assert outcome_from_record(row) == OUTCOME_NO_VALUABLE_TARGET_SURVIVAL


def test_reward_model_features_exclude_verified_label_and_team_count_leaks():
    assert "label" not in DEFAULT_FEATURE_KEYS
    assert "signature_team_bucket" not in DEFAULT_FEATURE_KEYS
    assert "label_team_bucket" not in DEFAULT_FEATURE_KEYS


def test_reward_model_ranks_positive_above_crowded_and_reports_family_risk():
    rows = _training_rows()
    model = train_reward_model(rows)
    positive_prediction = model.predict(_record(outcome="unknown", family="rare_good_family", label="24T9993"))
    crowded_prediction = model.predict(
        _record(outcome="unknown", family="crowded_24T25000_family", label="24T25000", team_count=50)
    )

    assert positive_prediction.reward_probability > crowded_prediction.reward_probability
    assert crowded_prediction.collapse_risk_probability > positive_prediction.collapse_risk_probability

    family_risk = ranked_family_risk(model, rows)
    assert family_risk[0]["family"] == "crowded_24T25000_family"
    assert family_risk[0]["mean_collapse_risk_probability"] > 0.80

    diagnostic = positive_vs_crowded_diagnostic(model, rows)
    assert diagnostic["positive_ranks_above_crowded_mean"] is True


def test_reward_model_blocks_known_exact_negative_hash_and_basin_after_round_trip():
    exact_negative = _record(
        outcome="crowded_accepted_collapse",
        family="known_negative_family",
        coefficient=71,
        label="24T23883",
        team_count=47,
    )
    model = train_reward_model([exact_negative])
    restored = AdvisoryRewardModel.from_json(model.to_json())

    exact_prediction = restored.predict(exact_negative)
    assert exact_prediction.decision == "avoid_known_exact_negative_hash"
    assert exact_prediction.evidence_source == "known_exact_hash_outcome"
    assert exact_prediction.collapse_risk_probability == 1.0

    same_basin = _record(outcome="unknown", family="known_negative_family", coefficient=72)
    basin_prediction = restored.predict(same_basin)
    assert basin_prediction.decision == "avoid_known_exact_negative_basin"
    assert basin_prediction.evidence_source == "known_exact_negative_basin"
    assert basin_prediction.collapse_risk_probability == 0.95


def test_reward_training_artifacts_use_grouped_split_and_metrics():
    rows = _training_rows()
    artifacts = build_training_artifacts(rows, source_path="fixture.jsonl")
    split = artifacts["manifest"]["split"]
    assert split["group_overlap"] == []
    assert set(split["train_groups"]).isdisjoint(split["eval_groups"])

    eval_matrix = artifacts["metrics"]["eval"]["confusion_matrix"]
    assert OUTCOME_SCORE_POSITIVE in eval_matrix
    assert "per_class_metrics" in artifacts["metrics"]["eval"]
    assert artifacts["metrics"]["leave_one_family_out"]["families_evaluated"] >= 1
    assert artifacts["manifest"]["advisory_status"] == "advisory_insufficient_positive_data"

    assert all("indices" not in key for key in artifacts["manifest"]["split"])


def test_reward_model_train_and_score_scripts_write_reproducible_artifacts(tmp_path):
    dataset = tmp_path / "dataset.jsonl"
    output = tmp_path / "reward_model"
    write_jsonl(dataset, _training_rows())

    assert train_reward_model_main(["--input_jsonl", str(dataset), "--output_dir", str(output)]) == 0
    assert (output / "reward_model.json").exists()
    assert (output / "training_manifest.json").exists()
    assert (output / "training_metrics.json").exists()
    assert (output / "training_report.md").exists()

    manifest = json.loads((output / "training_manifest.json").read_text(encoding="utf-8"))
    assert manifest["split"]["group_overlap"] == []

    model = load_model(output / "reward_model.json")
    scored, summary = score_rows(model, _training_rows())
    assert len(scored) == len(_training_rows())
    assert summary["decision_counts"]
    top_crowded = [
        row for row in summary["top_collapse_risk_rows"] if row["observed_outcome"] == OUTCOME_CROWDED_COLLAPSE
    ]
    assert top_crowded
    assert top_crowded[0]["family"] == "crowded_24T25000_family"


def test_reward_scoring_normalizes_nested_candidate_generation_metadata():
    model = train_reward_model(_training_rows())
    candidate = {
        "canonical_hash": "nested-candidate-hash",
        "real_root_count": 8,
        "exported_coefficients": [1] + [0] * 23 + [1],
        "generation_metadata": {
            "construction_family": "rare_good_family",
            "template_family_id": "rare_good_family:template",
            "perturbation_mode": "rare_good_family:mode",
            "basin_fingerprint": "rare_good_family:basin",
            "family_key": "rare_good_family:key",
            "even_support_like": True,
            "odd_support_exponents": [],
            "support_gcd": 2,
            "support_pattern": "even_support_like",
        },
    }

    scored, summary = score_rows(model, [candidate])

    assert summary["top_families"] == {"rare_good_family": 1}
    assert scored[0]["features"]["construction_family"] == "rare_good_family"
    assert scored[0]["features"]["template_family_id"] == "rare_good_family:template"
    assert scored[0]["features"]["even_support"] is True
    assert scored[0]["features"]["odd_support_exponents"] == []
    assert scored[0]["features"]["support_gcd"] == 2
    assert scored[0]["reward_model"]["reward_probability"] > scored[0]["reward_model"]["collapse_risk_probability"]
