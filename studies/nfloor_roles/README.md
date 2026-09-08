# nfloor_roles — Stage A: which of n_floor's three jobs actually sets the answer?

**Why this exists.** `n_floor` is one constant doing three unrelated jobs in
`LaserDeposition.cpp`:

| # | line | role |
|---|---|---|
| 1 | 1434 | `n_ref = sqrt(max(1-r, n_floor^2))` — the refractive index the RK4 **integrates**, so the ray trajectory and (via `1/(2 n_cr n_ref)`) the bending force |
| 2 | 1656 | `den_of` — the **denominator of K** in the discrete deposit, capping absorption at `1/n_floor` |
| 3 | 1724 | `turning = (den_end <= n_floor)` — the **switch-over** to the analytic near-critical layer, so that layer's extent `w = 1 - r_prev` |

Moving `n_floor` moves all three at once. Measured effect on `E_abs`: **-30 %/+11 % per
decade**. The fix (Stage B) is to separate them — but which one to fix first depends on
which dominates, and inferring that from the code has already been wrong twice in this
campaign.

**The design separates the roles without touching the code.** In straight-ray mode
(`refraction = 0`) the `n_ref` gradient is never computed — line 1435 guards it on
`do_refr` — so **role 1 is inactive**. Therefore:

* sweep in straight-ray mode → sensitivity from roles **2 + 3**
* sweep in refracting mode → sensitivity from roles **1 + 2 + 3**
* the difference between the two → **role 1**
* `layerfrac` inside each sweep → separates **role 3** (the analytic layer's share of
  absorbed power) from **role 2** (the cap on the marched steps)

`layerfrac` and `overfrac` are the diagnostics added 2026-09-02; this is the first study
built to use them rather than to check them.

**Grid.** `n_floor` = 1e-1, 1e-2 (the historical hardcoded value), 1e-3, 1e-4 — four clean
decades, so the reported slope is literally "per decade". 3 repeats each with different
seeds, because run-to-run 1σ on `E_abs` is 1.32 % and the effect being measured is ~30 %.
Base leg `P5_raycfl_025`, the lifted-FLASH rung that diverged.

**What each outcome implies for Stage B.**
* `layerfrac` tracks `E_abs` across the sweep → **role 3 dominates**; fix the switch-over
  (locate the critical surface from the profile).
* `layerfrac` flat while `E_abs` moves → **role 2 dominates**; the cap is doing the work and
  should become an explicit `tau_max` per step.
* straight-ray and refracting sensitivities differ materially → **role 1 matters** and the
  refractive-index regularisation needs its own constant before trajectories can be trusted.

Run: `sbatch -A <proj> -q shared -t 02:00:00 --array=0-7 studies/nfloor_roles/run.sbatch`
Analyse: `python studies/nfloor_roles/analyse.py`
