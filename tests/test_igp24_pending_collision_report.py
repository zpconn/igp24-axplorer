import json

from scripts.igp24_pending_collision_report import build_summary
from src.igp24.polynomial import stable_canonical_hash


LINE_A = "2,0,-3,0,1,0,0,0,0,0,0,0,-1,0,0,0,0,0,0,0,2,0,-3,0,1"
LINE_B = "3,0,0,0,0,0,2,0,0,0,0,0,-4,0,0,0,0,0,-2,0,0,0,0,-1,1"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_pending_collision_report_detects_pending_pressure_without_hash_overlap(tmp_path):
    selected_hash = stable_canonical_hash([int(value) for value in LINE_A.split(",")[:-1]])
    pending_hash = stable_canonical_hash([int(value) for value in LINE_B.split(",")[:-1]])
    selected_jsonl = tmp_path / "selected.jsonl"
    _write_jsonl(
        selected_jsonl,
        [
            {
                "canonical_hash": selected_hash,
                "candidate": {"exported_coefficients": [int(value) for value in LINE_A.split(",")]},
                "features": {
                    "r": 20,
                    "template_family_id": "model:mixed:r20:dense",
                    "basin_fingerprint": "basin-a",
                    "perturbation_mode": "dense_mixed_support_gcd1",
                    "mod_p_pattern_signature": "p3:1-23",
                },
            }
        ],
    )
    sync_dir = tmp_path / "sync"
    _write_json(
        sync_dir / "sair_sync_summary.json",
        {
            "sync_status": {
                "partial_sync": True,
                "submission_state_complete": False,
                "full_submission_state_complete": False,
                "degraded_mode_summary": "1/2 details recovered",
            }
        },
    )
    _write_jsonl(
        sync_dir / "sair_submission_rows.jsonl",
        [
            {
                "canonical_hash": pending_hash,
                "short_hash": pending_hash[:12],
                "polynomial": LINE_B,
                "pair_key": "24T25000|r=20",
                "label": "24T25000",
                "r": 20,
                "status_class": "pending",
                "scoring_status": "pending",
            }
        ],
    )

    summary = build_summary(
        selected_jsonl=selected_jsonl,
        sync_dir=sync_dir,
        focus_pair="24T25000|r=20",
        output_dir=tmp_path / "out",
        command=["pytest"],
    )

    assert summary["comparison"]["selected_count"] == 1
    assert summary["comparison"]["focus_pending_count"] == 1
    assert summary["comparison"]["exact_hash_overlap_count"] == 0
    assert summary["pending_pair_counts"] == {"24T25000|r=20": 1}
    assert summary["conclusion"]["live_submission_allowed"] is False
