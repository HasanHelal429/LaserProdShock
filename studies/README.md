# `studies/` — experiments that launch WarpX themselves

`runs/` holds one directory per simulation, launched by hand through `scripts/launch.sh`.
`studies/` holds the heavier experiments that **launch a family of runs** and reduce them to
a single answer: the Phase-3 parameter sweeps, and any convergence study that needs a
variant ladder.

Each study is a directory:

```
studies/<name>/
  README.md          what it varies, what it tests, which hypothesis (TEST_PLAN.md §2.3)
  config.base.yaml   the base run config; the runner overrides one key per variant
  run_variants.sh    launches the ladder (via scripts/launch.sh, one run dir per variant)
  analyze.py         reduces the ladder to fitted exponents + a figure
  scratch/           the variant run dirs (gitignored)
```

Everything tracked except `scratch/`: the runner and the analysis are the study; the WarpX
output is regenerable.

Rules that carry over from `runs/`:

- **`README.md` is required**, and states the hypothesis being tested *before* the sweep
  runs — a sweep without a written prediction is a fishing trip.
- Variants go in `scratch/<variant>/`, each a real run dir with its own `config.yaml` and a
  generated `README.md` naming its parent study. `launch.sh` is still the launcher, so
  `diags/` cannot be shared.
- **Log what was dropped.** If a study bounds coverage (a truncated range, a failed variant
  excluded, a lower ppc than the headline runs), say so in the README. A silently truncated
  sweep reads as "we covered the space" when it did not.

## Planned studies

| Study | Varies | Tests |
|---|---|---|
| `sweep_intensity/` | `I₀` (10¹⁷…10²¹ W/m²), `Z_eff·lnΛ`, λ₀, target thickness, coronal `L_n`, pulse duration via `intervals` | H1–H4: the shutoff picture, whether coupled energy is intensity-independent, and whether there is an **optimum intensity** for shock formation |
| `sweep_geometry/` | dimensionality, `beam_waist`, `beam_profile`, `incidence_angle`, `beam_focus`, target shape, `inject_side` | H5: planarity (`w₀ ≳ 0.8 ρ_i0`), and the cost of the 1D approximation |
| `numerics_gates/` | `ray_cfl`, ppc, `cfl`, `dz` | Gates G1, G4, G5, G7 as ladders rather than single checks |

Reference implementations to follow: `../KinShock2020/studies/bfield_convergence/` (the
structure) and `warpx-cda/laser_deposition/scripts/run_{convergence,scaling,te_error}.sh`
(sweep runners for this same operator).
