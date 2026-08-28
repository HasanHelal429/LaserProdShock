# P4_lez_kin_mrreal_drift — the real mass ratio, with the IC corona drift corrected

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Same as `P4_lez_kin_mrreal`: what does the reduced ion mass ratio cost? That leg
answered it with a starting corona 4.29× too fast in its own `C_S0`. This one repeats it with
the drift rescaled.
**Expected.** Plume `T_e` **below** the parent's 464.3 eV — the parent's extra initial flow
inflated the plume extent (`L_n` 4.05× FLASH, `zeta_front` 2.81× FLASH, both anomalous against
`mr100` *and* FLASH). If `µ^(1/3)` still holds, ~416 eV.
**Falsified by.** `T_e` unchanged from 464.3 eV, which would mean the drift is not what drove
the parent's extended plume and something else is.

## Setup
Parent: **`P4_lez_kin_mrreal`**. One key moves:

| key | parent | here | why |
|---|---|---|---|
| `plasma.target.drift_uz_de` | `[1.5271e-3, 1.5593e-4]` | **`[3.5638e-4, 8.4922e-6]`** | `uza` is a velocity in `c`, so it scales as `1/s`; `uzb`'s ramp is *per `d_e`* while the flow is per `d_i0`, so it scales as `1/s²` |

**The defect this fixes.** The mass-ratio recipe (`mr25/mr100/mr400` READMEs) lists
`drift_uz_de` under *held fixed by design*, and `mrreal` followed it. But the recipe's two
families are `s¹` for `d_e`-quoted lengths and `s²` for times and step counts — a **velocity**
belongs to neither, and holding it fixed while `C_S0` falls by `s` leaves the corona `s` times
too fast in normalised units. Measured at the handoff (`tau` 2.7), `v` at `n_e = 0.1 n_cr`:

| | FLASH | `mr100` | `mrreal` |
|---|---|---|---|
| `v/C_S0` at 0.1 `n_cr` | 1.722 | 1.748 ✓ | **21.060** ✗ |
| `uza/C_S0` | 0.548 | 0.548 ✓ | **2.349** ✗ |

`mr100` matches FLASH because `1.5271e-3` was chosen against *its* `C_S0`; every other leg of
the sweep inherits the same error in proportion to `s`. `mr25` and `mr400` are affected too
(by `0.5` and `2.0`), which is worth re-checking before their numbers are quoted again.

## Cost
Identical to the parent: 21424 cells × 500 ppc × 2030600 steps, **~3 h 35 m** measured.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.783 | PASS |
| G2 `dz/lambda_D` (target / ambient) | 58.1 / n.a. | INFO |
| G3 laser-off control | none at this mass ratio | **NOT VALID** — as the parent |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

## Result
**Interim, at 20 % — the notch is gone.** Checked at the first post-IC dump, the earliest one
that can show it:

| | `tau_own` | max `v/C_S0` over ζ 0.3–6 | notch recovery |
|---|---|---|---|
| `mrreal` (parent) | 0.00 | **63.51** | — |
| `mrreal` | 1.35 | 4.30 | **25.6×** ✗ |
| **this leg** | 0.00 | **3.88** | — |
| **this leg** | 1.35 | 2.95 | **1.0× — clean** ✓ |

The starting corona is 16.4× slower, against `s²` = 18.4 — `uzb` was the dominant term and it
carried the `1/s²`, so that is the expected factor. The profile at `tau_own` 1.35 is monotonic
where the parent's had already opened a 25.6× notch at ζ 1.73.

Full result pending; the run is at 20 % with ETA ~4 h (the machine picked up other load, so
this is slower than the parent's 3 h 35 m at the same step count).

<pending: plume T_e, f_abs, the raw-eV comparison>

## Retracted
nothing
