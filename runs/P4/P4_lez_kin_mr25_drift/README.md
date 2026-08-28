# P4_lez_kin_mr25_drift — the m_p/m_e = 25 leg with the IC corona drift corrected

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Does the µ-sweep's `µ^(1/3)` result survive once every leg starts from the same
*normalised* corona flow? The scan held `drift_uz_de` fixed, so each leg's starting
`uza/C_S0` scales as `1/s` — only `mr100` came out at FLASH's 0.548.
**Expected.** `µ^(1/3)` to hold at least as well as before. The real-mass leg moved 464.3 →
440.2 eV (1.055×) when this was fixed, so a few-percent shift here, in the direction that
brings each leg toward `mr100`'s convention.
**Falsified by.** A shift large enough to change the fitted exponent outside 1/3 ± the 13.5 %
noise floor, which would mean the scan's headline was an artifact of the IC rather than physics.

## Setup
Parent: **`P4_lez_kin_mr25`**. One key moves, `plasma.target.drift_uz_de`, rescaled by
`1/s` on `uza` and `1/s²` on `uzb` with `s` = 0.5:

| leg | `uza/C_S0` before | after |
|---|---|---|
| `mr25` | 0.274 (2× too slow) | **0.548** |
| `mr100` | 0.548 ✓ (untouched) | 0.548 |
| `mr400` | 1.096 (2× too fast) | **0.548** |
| `mrreal` | 2.349 | 0.548 (as `mrreal_drift`) |

`uza` is a velocity in units of `c` and `uzb` is its ramp *per `d_e`*, so they form a third
scaling family the run READMEs never listed — see GOTCHAS, "Cross-code comparison".

## Cost
Identical to the parent: measured 58.4 s (`mr25`) and 2009 s (`mr400`) on one RTX 4070.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.783 | PASS — µ-invariant |
| G2 `dz/lambda_D` (target / ambient) | 58.1 / n.a. | INFO — µ-invariant |
| G3 laser-off control | `P4_lez_kin_ic6_off` (mr100 basis) | see parent |
| G4 `ray_cfl` check | 0.25 | PASS |
| G5 ppc / `Tlocalfrac` | 500, mode local | PASS |
| G6 energy closure | | post-run |

## Result
<pending>

## Retracted
nothing
