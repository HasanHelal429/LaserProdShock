# P4_lez_kin_mr400_drift — the m_p/m_e = 400 leg with the IC corona drift corrected

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Does the µ-sweep's `µ^(1/3)` result survive once every leg starts from the same
*normalised* corona flow? The scan held `drift_uz_de` fixed, so each leg's starting
`uza/C_S0` scales as `1/s` — only `mr100` came out at FLASH's 0.548.
**Expected.** `µ^(1/3)` to hold at least as well as before. The real-mass leg moved 464.3 →
440.2 eV (1.055×) when this was fixed, so a few-percent shift here, in the direction that
brings each leg toward `mr100`'s convention.
**Falsified by.** A shift large enough to change the fitted exponent outside 1/3 ± the 13.5 %
noise floor, which would mean the scan's headline was an artifact of the IC rather than physics.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ##~                                                               
      ^                                                                ^
      reflecting                                                    open
      z = -100                                                  z = +4900

  #  target flat top : 10 n_cr, 90 d_e thick, centred at -45 d_e
  ~  coronal ramp   : exponential, L_n = 13.91 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 10000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 442368 steps = 43.73 ps
```

## Setup
Parent: **`P4_lez_kin_mr400`**. One key moves, `plasma.target.drift_uz_de`, rescaled by
`1/s` on `uza` and `1/s²` on `uzb` with `s` = 2.0:

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
Completed, **2265 s** (one RTX 4070, sharing the machine with the other rerun).

| | parent `mr400` | **this leg** | change |
|---|---|---|---|
| `uza/C_S0` | 2x too fast (1.096) | **0.548** ✓ | — |
| `⟨f_abs⟩` | 0.5145 | **0.6244** | — |
| plume `T_e` | 244.6 eV | **271.0 eV** | 1.108× |
| `T_e/T_ss(own µ)` | — | **0.547** | — |

### What it does to the sweep
With all four legs on the same normalised corona flow, the fits tighten and both move toward
their theories:

| | before the drift fix | **after** | theory |
|---|---|---|---|
| plume `T_e` | `µ^0.293` | **`µ^0.322`** | `µ^(1/3)` = 0.333 |
| optical depth `−ln(1−f)/2` | `µ^0.454` | **`µ^0.490`** | `µ^(1/2)` = 0.500 on a raw-eV handoff |
| scatter | 8.3 % | **4.5 %** | — |

`T_e/T_ss(own µ)` across the corrected sweep: 0.580 / 0.506 / 0.547 / 0.535 — a 1.15× spread,
inside the 13.5 % noise floor. **`µ^(1/3)` is now confirmed to 3.3 %**, and the optical-depth
exponent sits 2 % from the `µ^(1/2)` that a raw-eV handoff predicts — so that failure is fully
explained by the handoff convention, not by anything in the code.

## Retracted
nothing
