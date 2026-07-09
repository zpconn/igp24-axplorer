# AXG-1.10 Training Summary

Status: bounded CUDA hash-exclusion runs completed; sparse-submode replay submitted later and resolved as negative feedback.

- Hash memory: `data/igp24/active_learning/axg20_hash_exclusions_20260709.jsonl` with 1,515 known hashes.
- r8 CUDA: runtime 266.228s, max/avg GPU 88.0% / 42.19%, skipped 11,360 excluded hashes, decoded 12 rows, scored 12 rows, target survivors 1.
- r12 CUDA: runtime 401.508s, max/avg GPU 88.0% / 29.13%, skipped 10,313 excluded hashes, decoded 3 rows, scored 3 rows, target survivors 0.
- Sparse-submode planner replay made the combined spillover packet locally ready after a fresh full SAIR sync.
- Live submission `sub_e558f7c55b3d45a0a926c5a9c6d05d75` accepted and scored all 4 rows, but all collapsed to crowded `24T25000`: r4 x3 and r8 x1.
- Interpretation: no score-improvement completion; ingest as hard negative feedback for model:sparse r8/r4 sparse-template basins.
