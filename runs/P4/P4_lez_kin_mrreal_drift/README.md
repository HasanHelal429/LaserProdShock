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
<pending>

## Retracted
nothing
