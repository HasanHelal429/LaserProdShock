# P5_raycfl_005 — G4 ray_cfl ladder, rung `ray_cfl = 0.05`

**Phase.** 5, `TEST_PLAN.md` §13. **Read the four rungs as a set, never one alone.**
**Question.** Has the eikonal ray march converged on *this* target — 10 `n_cr`, with the
turning point inside the plasma?
**Expected.** `E_abs` and the deposition profile stop moving between 0.10 and 0.05. If they
do, 0.25 is safe and every P5 leg stands. **Convergence here is documented as
non-monotonic**, so a small 0.25→0.10 change is *not* evidence of convergence on its own —
that is why the ladder has four rungs and not two.
**Falsified by.** `E_abs` still moving by more than 1 % between 0.10 and 0.05, or the
deposition peak moving by more than one cell. Either would mean every P5 leg needs a finer
march, and the phase's absorption numbers are resolution-limited rather than physical.

---

## Why this ladder is a gate and not bookkeeping

Two inherited defects sit exactly here (RESULTS 2026-07-28):

* **`ray_cfl = 0.25` is not asymptotic for turning-point problems.** Convergence is
  non-monotonic and the default sits near a **2.5 %** excursion.
* **The exit-boundary overshoot**: a ray takes a partial extra arc-length step past the far
  boundary and *creates* energy in the final cell — **+24.9 %** at the default.

Uniform slabs are exact at any `ray_cfl`, which is why this has never bitten: the existing
`studies/exit_overshoot` ladder ran a **1.5 `n_cr`** target with **no interior critical
surface**, so no ray ever turned inside the plasma.

Every P5 leg is **10 `n_cr`**. The ray turns inside the target, and the 2026-08-29 optical
depth audit put **41 % of the initial condition's entire optical depth in
`0.9 < n/n_cr < 1`** — within a few tenths of a micron of the turning point, which is
precisely the region a coarse march integrates badly. The deposition profile is acceptance
criterion A5.

## What it involves

Four runs, identical to `P5_flashic` except for `ray_cfl` and `max_step`. **20 300 steps
= 2.0 ps = 0.054 `τ_own`** — the ray march is tested against a nearly *static* profile,
which is the right test: what is being measured is the integration of a given profile, not
the evolution. That yields ~2030 `LASERDEP` samples and ~10 deposition-profile dumps.

**Cost: minutes each.** 20 300 of 9 139 500 steps is 0.22 % of the spine, and even the
0.05 rung — 5× the march work of the default — stays in that range. They fit `--qos debug`
(30-minute cap, 5-job limit) exactly, which starts hours sooner than `shared`.

## How it is read

```bash
for r in 050 025 010 005; do python3 scripts/laser_report.py runs/P5/P5_raycfl_$r; done
```

Compare across rungs: `E_abs` (**not** `f_abs(0)`, which carries 10.4 % 1σ on RNG seed
alone — retraction ledger 1), and the deposition profile's peak position and width from
`plot_fields.py`. Pass criterion: **< 1 % in `E_abs` and < 1 cell in the peak, between
0.10 and 0.05.**

## Geometry

Identical to `P5_flashic`: 22040 cells, FLASH's lifted profile capped at 10 `n_cr`,
reflecting rear / open front. `ic_flash.yaml` is copied from the spine so all four rungs
and the spine share one initial condition byte for byte.

## Result
*(to be filled in after the run)*

## Retracted
nothing yet -- the run has not been launched.
