# `tests/` — fast pytest checks

Fast, no-WarpX-required checks on the package and the configs. These run in seconds and are
the guard against the config/deck drift that the "config is the single source of truth" rule
exists to prevent.

```bash
pytest tests/ -q
```

## Planned

`test_units.py`
- `d_e,cr == λ₀/2π` exactly, and `n_cr(1.053 µm) == 1.005×10²⁷ m⁻³`.
- The three length scales (`critical`, `target`, `ambient`) are mutually consistent, and
  `reference.length_scale` selects the one the config claims. *This is the project's most
  confusable quantity — `TEST_PLAN.md` §2.1.*
- The IB coefficient `K` reproduces its known exponents on `n_e`, `Z_eff`, `lnΛ`, `T_e`
  (2, 1, 1, −3/2) — cross-checked against
  `warpx-cda/laser_deposition/scripts/ibtheory.py`, which derives them independently of the
  operator.

`test_gates.py`
- `run_checks` computes `ω_pe dt` at the **peak compressed** density, not the initial one
  (gate G1 — the check whose absence invalidated a whole deck upstream).
- `dz/λ_D` is reported per region, and the cold-target value is flagged rather than silently
  passed (G2).
- Each gate fires on a config constructed to violate it.

`test_structures.py`
- Every `runs/*/config.yaml` loads, validates, and renders a deck.
- Every `runs/*/` has a `README.md` (the rule `launch.sh` enforces at launch time — this
  catches it at commit time).
- Boundary-token map: no config produces exactly one periodic face (WarpX requires both or
  neither), and no config combines `absorbing` (Silver–Mueller) fields with a background `B`
  — the div-B-cleaner incompatibility inherited from `KinShock2020`.
- Round-trip: `render(cfg)` then `key_params()` recovers the config's primaries.

Reference: `../KinShock2020/tests/test_structures.py`.
