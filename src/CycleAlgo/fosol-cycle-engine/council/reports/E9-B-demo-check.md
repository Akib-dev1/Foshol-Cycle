# E9 Stream B - demo check

`python scripts/demo_check.py` (offline; no network/live SMAP/POWER) exits 0:

```text
profiles: 8
initial: status=partial branches=0 candidate=0 conditional=295 exclusions=56 options=8
initial waits: 6 conditional <=180; Aman/Mung unsupported
selected: boro_brri_dhan28=42 lentil_binamasur9=55 maize_rabi_bari_hybrid13=42 mustard_binasarisha9=54 potato_bari_alu41=54 wheat_bari_gom33=48
preferences: fastest/diversity ranked; cost/net/irrigation/upfront unranked/no_winner
water: rainfed/irrigation_available/unknown -> partial
smap: status/branch IDs/status/ranking identical; context available/unavailable
offline: unavailable/expired SMAP -> partial with warning; no moisture zero-fill
determinism: identical
PASS
```

Checks: 8 options (Aman/Mung unsupported; 6 conditional); all 6 selected crops return partial 3-crop/2-transition branches with shown messages; `lowest_upfront_cash` is rejected by request validation, while direct ranking is unranked/no_winner; every response passes `validate_response`, source coverage, finite/unique/3-2/range invariants; SMAP changes only context metadata, never status/branches/ranking.
Full suite: `Ran 307 tests in 8.116s`, `OK`. No Data changes; no commits.
