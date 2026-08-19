# P4_lez_kin_ic6 — six decades of resolved density **with the FLASH-fitted corona**

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** `L_ppc500` showed that widening the resolved density range from four decades
to six takes the `T_e` outward rise from **1.504 to 1.133**, against FLASH's own **1.148** —
the single largest step toward FLASH all campaign. But it inherited `P4_lez_kin`'s
**analytic Gaussian corona**, which is the initial condition that **fails the paper's own
Fig.-2 acceptance test**: peak laser deposition at ζ = **4.13** against FLASH's **0.27**, and
critical surface at 4.08 against 0.27. So the best shape result to date was measured on the
wrong IC. Does it survive the right one?

**Expected.** The shape result holds or improves, and the absorption and critical-surface
placement improve markedly, because the deposition now happens where FLASH puts it.

**Falsified by.** The `T_e` rise returning toward 1.5, which would mean the six-decade
result was an accident of the Gaussian corona rather than a property of the density floor.

**Parents.** `L_ppc500` (geometry, six decades) + `P4_lez_kin_flashic` (the corona).

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ##~                                                               
      ^                                                                ^
      reflecting                                                    open
      z = -50                                                  z = +2450

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 5000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 552960 steps = 54.66 ps
```

## Setup — what this combines

| | `P4_lez_kin` / `L_ppc500` | `P4_lez_kin_flashic` | **this run** |
|---|---|---|---|
| corona | Gaussian, `L_n` = 27 `d_e` | **exponential, 6.955** | **exponential, 6.955** |
| corona `T_e` / `T_i` | 100 / 10 eV | **378.3 / 115.6 eV** | **378.3 / 115.6 eV** |
| initial flow | at rest | **ramp to 4–5 `C_S0`** | **ramp to 4–5 `C_S0`** |
| `n_max` | **10 `n_cr`** (paper) | 40 | **10 (paper)** |
| thickness | **4.5 `d_i0`** (paper) | 20 | **4.5 (paper)** |
| `density_min_frac` | 1e-4 / **1e-6** | 1e-4 | **1e-6 (six decades)** |
| Fig.-2 peak deposition | ζ = 4.13 ✗ | **ζ = 0.28 ✓** | expected ✓ |

The paper-faithful target (10 `n_cr`, 4.5 `d_i0`) is used rather than `flashic`'s 40 and 20:
those were motivated by the reservoir, which was **falsified on 2026-08-18**, and the
paper's own `n_max` scan finds `T_e` matches for `n_max` ≳ 5 `n_cr`.

## Cost
5000 cells × 500 ppc × 552 960 steps. `L_ppc500` took **20 min** on one RTX 4070; the lower
solid temperature and the drift add a little.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | **0.783** | PASS |
| G2 `dz/lambda_D` | **58.1** (against 116 on the 100 eV corona) | INFO |
| G3 laser-off control | not run | deferred |
| G4 `ray_cfl` | 0.25 | PASS |
| G5 ppc | 500 | PASS |
| G6 energy closure | | post-run |

**All four pre-run gates pass for the first time in this phase** — the earlier decks carried
two warnings. The hotter corona doubles the Debye resolution.

## Result
_Pending._

## Retracted
Nothing yet.
