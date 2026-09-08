# near_critical_stats — put a real error bar under the near-critical verdict

**The question.** Does the near-critical fix (`laser_deposition.near_critical_fix`) help,
hurt, or do nothing to `ray_cfl` convergence? The 2026-09-04 attempt could not say: with one
run per rung and a measured run-to-run 1σ of **1.32 %** on `E_abs`, both fine increments of
the OFF ladder were 0.3–0.7σ and both ON increments were 2.4σ. Two verdicts were issued and
both had to be retracted.

**The design.** 4 rungs × 2 modes × **5 repeats** = 40 runs.

| | |
|---|---|
| rungs | `ray_cfl` = 0.25, 0.10, 0.05, 0.025 |
| modes | `near_critical_fix` = 0 (previous behaviour) and 1 (corrected) |
| repeats | 5, each with a different `warpx.random_seed` |
| base leg | `P5_raycfl_*`, the lifted-FLASH ladder — the one that diverged |
| march | **straight rays** (`refraction = 0`) |

**Why straight rays.** Decided 2026-09-08: the specifics of the refraction are not important
to the questions these studies ask, every P5 leg is plane-stratified (`shape: planar`, 1D),
the operator's own documentation calls the straight-ray mode *exact* for such a target, and
it is cheaper. It also removes the RK4 approach to the turning surface as an independent
error source — measured drift was +0.95 % straight-ray against +3.27 % refracting on the
identical IC. Both modes share the analytic near-critical layer, so this is still a valid
test of the fix, run in the configuration the project will actually use.

**Why the seed varies across repeats.** A production run picks a seed, so the uncertainty on
a production number has to include that choice. The 1.32 % measured at *fixed* seed is a
lower bound on it; varying the seed is the honest — and larger — estimate.

**What it buys.** The standard error on each rung's mean is σ/√5 ≈ 0.6 %, so an increment
(a difference of two means) carries ≈0.8 %. That resolves a 2.5 % increment at ~3σ, which is
enough to separate the ON ladder's apparent +3.2 % from converged (<1 %). It does **not**
resolve a 1 % increment, and the analysis says so rather than pretending otherwise.

**Falsifiable outcomes.**
* ON increments shrink into the floor → the fix helps; adopt it and re-open the spine.
* ON increments stay flat and > OFF → the fix hurts convergence; keep it anyway for the
  evanescent-deposition correction, and pursue the layer-extent fix (Fix 2).
* Both ladders' fine increments land inside the floor → the ladder is converged at
  `ray_cfl` ≥ 0.10 and the original +18.3 % was entirely a coarse-end effect.

Run: `sbatch -A <proj> -q shared -t 02:00:00 --array=0-7 studies/near_critical_stats/run.sbatch`
Analyse: `python studies/near_critical_stats/analyse.py`
