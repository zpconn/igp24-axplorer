# IGP24 GAP Group-Index Workflow

- Created: `2026-07-09T22:42:39.892838+00:00`
- Source commit: `beae117d08f4289a71e5b68efd255ba62e42a03f`
- Status: `blocked_missing_gap_outputs`
- GAP path: `None`
- Manifest: `data/igp24/remediation_20260709/group_index_offline_export_phase3/top25_uncovered_r24_gap_programs/gap_export_manifest.json`
- Programs: `3`
- Programs loaded from captured output: `0`
- Programs run with GAP: `0`
- Programs blocked: `3`
- Rows available: `0`
- Rows imported: `0`
- Group count: `0`
- Readiness output: `None`
- Readiness blockers: `None`
- No approximation written: `True`
- Safety: Exact GAP group-index workflow. It runs GAP only when available, reuses captured GAP JSON outputs when present, calls no SAIR/network APIs, does not generate candidates, and does not submit anything.

## Missing GAP Outputs

- `data/igp24/remediation_20260709/group_index_workflow_phase3/top25_uncovered_r24_blocked_no_gap/gap_outputs/degree24_group_cycle_export_0001_19906_15069.json`
- `data/igp24/remediation_20260709/group_index_workflow_phase3/top25_uncovered_r24_blocked_no_gap/gap_outputs/degree24_group_cycle_export_0002_15083_23719.json`
- `data/igp24/remediation_20260709/group_index_workflow_phase3/top25_uncovered_r24_blocked_no_gap/gap_outputs/degree24_group_cycle_export_0003_23722_24189.json`

## Program Results

| program | status | rows | output |
| --- | --- | ---: | --- |
| `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/group_index_offline_export_phase3/top25_uncovered_r24_gap_programs/degree24_group_cycle_export_0001_19906_15069.g` | `blocked_missing_gap_output` | 0 | `data/igp24/remediation_20260709/group_index_workflow_phase3/top25_uncovered_r24_blocked_no_gap/gap_outputs/degree24_group_cycle_export_0001_19906_15069.json` |
| `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/group_index_offline_export_phase3/top25_uncovered_r24_gap_programs/degree24_group_cycle_export_0002_15083_23719.g` | `blocked_missing_gap_output` | 0 | `data/igp24/remediation_20260709/group_index_workflow_phase3/top25_uncovered_r24_blocked_no_gap/gap_outputs/degree24_group_cycle_export_0002_15083_23719.json` |
| `/home/zpconn/code/igp24-axplorer/data/igp24/remediation_20260709/group_index_offline_export_phase3/top25_uncovered_r24_gap_programs/degree24_group_cycle_export_0003_23722_24189.g` | `blocked_missing_gap_output` | 0 | `data/igp24/remediation_20260709/group_index_workflow_phase3/top25_uncovered_r24_blocked_no_gap/gap_outputs/degree24_group_cycle_export_0003_23722_24189.json` |
