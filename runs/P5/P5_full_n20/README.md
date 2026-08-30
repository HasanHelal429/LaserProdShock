# P5_full_n20 — the density-cap A/B, at real mass

**Phase.** 5, `TEST_PLAN.md` §13
**Question.** Is the 10 `n_cr` cap on the target — the largest surviving structural
departure from FLASH — a live lever on plume `T_e` at real ion mass?
**Expected.** If the cap is binding, doubling it to 20 `n_cr` moves plume `T_e` materially
(≫ the `P5_seed` band) and part of the 0.69 × gap is a cap artifact rather than a code
difference.
**Falsified by.** A `T_e` difference inside the seed band, which eliminates the cap and
moves the question to electron thermal transport (D3 Appendix C, never run).

---

## Why this is the next structural test

Everything cheaper has already been eliminated, and the retraction ledger says so:

| candidate | verdict | where |
|---|---|---|
| the deposition operator | **cleared** — at matched `f_abs`, `T_e` does not move | ledger 21 |
| `f_abs` mismatch | **not in play** — 0.840 vs 0.870, 3.4 % | `mrreal_drift` |
| the density floor | **< 4 %** on the FLASH-fitted exponential | ledger 20 |
| electron heat conduction as the `T_e` *shape* | **it was the floor** | ledger 19 |
| the corona fit | `ζ_cr` 1.03 ×, `L_n` 0.81 × — already close | `mrreal_drift` |

What is left is the concession that is *structural* rather than numerical: FLASH's target is
solid Al at **795 `n_cr`** and ours is capped at **10**.

The paper's own Appendix-A scan (2 / 5 / 10 / 20 `n_cr`) found `T_e` matches FLASH only for
`n_max` ≥ 5 — evidence the cap is a live lever near our operating point rather than a settled
one. **But that scan ran at a reduced mass ratio**, where `HANDOFF.md` §7.4 shows absorption
is broken by construction (`τ_abs ∝ µ^0.490`). It does not transfer to µ = 1, and nobody has
run the cap ladder at real mass.

Read as a two-point derivative, not as a convergence: 20 `n_cr` is still 40 × below FLASH's
solid.

## What is different from `P5_full`

`plasma.target.density_over_ncr: 10.0 → 20.0`. Nothing else.

## Two consequences to watch

**1. G1 becomes the binding gate.** `ω_pe·dt` = √20 × 0.175 = **0.783** at `t` = 0, and at the
gate's `compression_factor` 2.0 it reaches **1.107** against the 1.2 limit — an **8 % margin,
not a comfortable one**. `run_checks.py` G1 must be read *before* launch and again at the peak
compressed density the run actually reaches. If compression exceeds ~2.35 ×, drop `cfl` to
0.25 and accept the 1.4 × cost rather than trusting the margin. A G1 violation once grew total
particle energy **21 ×** while the laser supplied 1/1400 of it.

**2. This leg is not a single-variable test of the *reservoir*.** Doubling the density doubles
the areal mass too, so the 0.9 ns ablation draw falls 15.2 % → 7.6 %. Cap and reservoir move
together here. The reservoir arm is separately controlled by `P5_full` against its 4.5 `d_i0`
parent, so **the pair separates them** — neither run does it alone.

## Geometry

Identical to `P5_full` except the target flat top is 20 `n_cr`; 22040 cells, 9139500 steps
= 903.4 ps. `dz/λ_D` in the solid rises 58.1 → **82.2**.

## Cost

≈ 19.8 h, as `P5_full`. **Tier 3 — run it only after `P5_full` has reported**, since if the
ratio curve comes back flat the cap question changes shape.

## Result
*(to be filled in after the run)*
