# r8 Score-Followup Lane

- Source signal pair: `24T9993|r=8`
- Target r: `8`
- Input rows: `34`
- Accepted lane rows: `32`
- Rejected rows: `2`
- Template families: `{"r8_score_followup:four_positive_fibers_e:odd_pair_off_core": 17, "r8_score_followup:four_positive_fibers_f:odd_pair_off_core": 15}`
- Basin fingerprints: `32`
- Perturbation modes: `{"odd_pair_off_core": 32}`
- Mod-p signatures: `{"p2:11-13;p3:6-18;p5:6-18;p7:1-6-17": 1, "p2:11-13;p3:9-15;p5:6-18;p7:1-23": 1, "p2:2-22;p3:6-18;p5:1-1-6-6-10;p7:2-3-4-7-8": 1, "p2:2-3-6-13;p5:1-1-8-14;p7:2-2-3-3-4-10": 2, "p2:2-4-18;p3:11-13;p5:1-1-22;p7:2-5-8-9": 1, "p2:2-4-18;p3:3-4-17;p5:24;p7:3-5-16": 2, "p2:24;p3:3-21;p5:2-3-3-5-11;p7:1-23": 2, "p2:24;p3:7-17;p7:1-2-3-4-4-4-6": 1, "p2:3-4-17;p3:11-13;p5:1-1-9-13;p7:1-2-7-14": 3, "p2:3-6-15;p3:3-3-5-13;p7:1-2-3-6-6-6": 2, "p2:3-7-14;p3:7-17;p5:12-12;p7:5-7-12": 1, "p2:3-8-13;p3:7-17;p5:3-6-15": 2, "p2:4-20;p3:2-22;p5:1-1-3-4-4-11": 1, "p2:4-5-15;p3:10-14;p5:4-20;p7:1-2-8-13": 2, "p2:4-5-15;p3:6-18;p5:4-4-7-9;p7:6-18": 2, "p2:5-19;p3:9-15;p5:2-3-9-10;p7:1-4-4-15": 1, "p2:5-6-13;p3:2-3-3-4-6-6;p5:1-1-3-5-5-9;p7:1-2-2-7-12": 3, "p2:6-8-10;p3:5-19;p5:5-19;p7:2-7-15": 1, "p2:7-17;p3:11-13;p5:1-1-3-9-10;p7:1-2-5-8-8": 1, "p2:8-16;p3:2-22;p5:1-1-5-17;p7:1-2-5-6-10": 1, "p2:9-15;p3:11-13;p5:24;p7:1-3-20": 1}`
- Rejection reasons: `{"duplicate_canonical_hash": 2, "duplicate_coefficient_line": 2}`

## Outputs
- candidate_jsonl: `data/igp24/r8_score_followup_20260708/lane_combined/r8_score_followup_candidates.jsonl`
- rejected_jsonl: `data/igp24/r8_score_followup_20260708/lane_combined/r8_score_followup_rejected.jsonl`
- summary_json: `data/igp24/r8_score_followup_20260708/lane_combined/r8_score_followup_lane_summary.json`
- report_md: `data/igp24/r8_score_followup_20260708/lane_combined/r8_score_followup_lane_report.md`

This lane-prep step does not call SAIR and does not claim exact labels.
