# AXG-1.10 Training Summary

Status: bounded CUDA hash-exclusion runs completed; no SAIR submission.

- Hash memory: `data/igp24/active_learning/axg20_hash_exclusions_20260709.jsonl` with 1,515 known hashes.
- r8 CUDA: runtime 266.228s, max/avg GPU 88.0% / 42.19230769230769%, skipped 11360 excluded hashes, decoded 12 rows, scored 12 rows, target survivors 1.
- r12 CUDA: runtime 401.508s, max/avg GPU 88.0% / 29.126903553299492%, skipped 10313 excluded hashes, decoded 3 rows, scored 3 rows, target survivors 0.
- Gate result: r8 singleton held; r12 target gate selected 0; combined spillover gate selected 4 but held because all selected rows shared `sparse_mixed_support_gcd1` perturbation mode.
- Next: add a materially different sparse submode/support generator or mode discriminator before another submission attempt.
