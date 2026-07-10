# IGP24 Exact Structural Pretraining Corpus

- Created: `2026-07-10T12:01:38.006912+00:00`
- Source commit: `d003ca0a27cbc8183f7065dd4f1544d37fcef2a1`
- Status: `ready_for_post_loader_readiness_audit`
- Unique train rows: `1000000`
- Unique evaluation rows: `100000`
- Target-r counts: `{"eval|r=12": 20000, "eval|r=16": 20000, "eval|r=20": 20000, "eval|r=24": 20000, "eval|r=8": 20000, "train|r=12": 200000, "train|r=16": 200000, "train|r=20": 200000, "train|r=24": 200000, "train|r=8": 200000}`
- Construction families: `8`
- Canonical collisions rejected: `0`
- Known hashes rejected: `0`
- Corpus bytes: `1479898407`
- Runtime seconds: `537.402`
- Network/SAIR/submission calls: `none`

## Mathematical Contract

Every row is monic degree 24 and exactly irreducible by an Eisenstein certificate. Its real-root count is certified by disjoint midpoint/IVT intervals in the outer polynomial, and its `h(x^m)` form preserves an imprimitive block system. These facts do not establish an exact degree-24 transitive-group label. Quartic-in-x6 rows additionally prove outer group S4.

## Training Contract

Counts refer to unique post-generation canonical hashes. Evaluation families and parameter ranges are disjoint from training families. Repeated sampler draws and epochs do not count as additional examples. Rows are pretraining-only and packet-ineligible.
