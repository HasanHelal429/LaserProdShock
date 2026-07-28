# `fabs_noise` — the PIC noise floor on `f_abs(0)`

**What it varies.** Only `numerics.random_seed`, over one otherwise identical config
(`runs/P0_bc_open_B` truncated to `max_step = 2`, since `f_abs(0)` needs only the step-0
application). Six seeds, seconds each.

**Hypothesis it tests.** That `f_abs(0)` is reproducible enough for a small difference
between two runs to mean something.

**Result — it is not.** Across six statistically identical runs:

```
seed 1  0.2925    seed 4  0.2938
seed 2  0.3140    seed 5  0.2837
seed 3  0.2740    seed 6  0.2279

mean 0.2810   std 0.0292   relative std 10.39%   full spread 30.64%
```

**Why.** `K ∝ 1/√(1 − n_e/n_cr)` diverges at the critical surface, and the operator
integrates that layer analytically over the *locally interpolated* density and its gradient.
Both are noisy at finite ppc, so a near-critical target turns per-cell density noise into
large swings in the deposited power. The step-0 profile dumps localise it: essentially the
entire difference between two runs sits in the single cell containing the critical surface
(P_abs there varied 1.18e24 → 1.51e24 W/m³ between two runs whose densities agreed to
0.0004 n_cr).

**Consequence, and it is a working rule.** **Any single-shot `f_abs` number for an overdense
target carries a ~10 % 1σ uncertainty, and differences below ~30 % are not evidence of
anything.** Time-averaged quantities (`E_abs`, which integrates hundreds of applications) are
far tighter — `E_abs` agreed to 0.6 % between geometries whose `f_abs(0)` differed by 10 %.
So: **quote `E_abs`, not `f_abs(0)`, when comparing runs.** This also sharpens gate G4: the
`ray_cfl` non-asymptoticity at turning points is not just a discretisation issue, it is a
noise-amplification one.

This study caused a retraction — see RESULTS 2026-07-28.
