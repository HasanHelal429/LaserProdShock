# P4_lez_kin_bg5 — the clean 2698 leg: FLASH-matched IC, background at the PIC floor

> ## [DEFECTIVE] — diagnostics deleted 2026-08-28
> **Killed at 30.1 %; RESULTS records it was testing the wrong axis. Its declared laser-off control never existed.**
> 
> Superseded by: **the table at RESULTS.md:3970+**. `diags/` and `run.log` were removed to reclaim disk; the
> config, deck, `warpx_used_inputs` and this README are kept as the provenance record.
> Re-run from the config if the raw output is ever needed again.
> See `runs/P4/SUPERSEDED.md` for the full ledger.

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** `P4_lez_kin_bg` is the best-agreeing leg (`f_abs` 0.769 vs FLASH's 0.870,
plume `T_e` 1.11× its own Manheimer value, front 0.71×) — but it carries **two** things
that should disqualify it, and they may be cancelling:

1. Its background is **1e-3 `n_cr`**, which is **33 940×** denser than the 1e-10 g/cm³
   chamber gas it stands for (2.95e-8 `n_cr`), and bg3 → bg4 moved the plume front **1.8×**.
2. Its **initial condition fails the paper's own acceptance test.** In the Fig.-2
   replication (`scripts/fig2_ic.py`) its Gaussian corona puts the peak laser deposition at
   ζ = **4.13** against FLASH's **0.27**, and its critical surface at 4.08 against 0.27.

Meanwhile `P4_lez_kin_flashic` — whose IC **passes** that test (peak deposition ζ = 0.28,
critical surface 0.23, `T_e` plateau 419 eV against FLASH's 379) — agrees *worse*
(`f_abs` 0.358). **The leg with the correct initial condition performs worse than the leg
with the wrong one.** This run asks whether that is because the background is doing the
work as a tamper.

**Expected.** If `kin_bg`'s agreement is physics, it survives thinning the background 100×.
If it was tamping, this run falls back toward `P4_lez_kin_flashic`'s behaviour.

**Falsified by.** Either outcome is informative; the run is a discriminator, not a fix.

**Parent.** `P4_lez_kin_flashic` (its IC), with the background of `P4_lez_kin_bg` thinned
100× to the paper's stated PIC floor.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      .#####~...........................................................
      ^                                                                ^
      reflecting                                                    open
      z = -224                                                  z = +2464

  #  target flat top : 40 n_cr, 200 d_e thick, centred at -100 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  .  ambient        : 1e-05 n_cr, theta_e = 1.957e-06  (fills BOTH sides -- no vacuum gap)
  grid              : 5376 cells, dz = 0.5 d_e, dt = 0.07061 fs, 774144 steps = 54.66 ps
```

## Setup
| | `kin_bg` | `flashic` | **this run** |
|---|---|---|---|
| corona | Gaussian, `L_n` = 27 `d_e` | **exponential, 6.955** | **exponential, 6.955** |
| corona `T_e` | 100 eV | **378.3 eV** | **378.3 eV** |
| ambient | 1e-3 `n_cr` | none | **1e-5 `n_cr`** |
| collision pairs | target only | target only | **all 10, incl. target↔ambient** |
| Fig.-2 peak deposition | ζ = 4.13 | **ζ = 0.28** | **ζ = 0.28** (same IC) |

**1e-5 `n_cr` is the paper's own PIC floor** — *"the minimum density in PIC being limited
to `n_cr/N_PPC` ≈ 1e-5 `n_cr`"*. It is **not** a physical chamber; FLASH's is 2.95e-8
`n_cr`, which PIC cannot resolve, and the paper says so outright.

**The collision pairs are complete for the first time.** `kin_bg`'s covered only the target
species, so its background was collisionless and there was **no target↔ambient coupling at
all** — a background that tamps hydrodynamically but cannot exchange heat is not a
physical chamber under any reading.

## Cost
5376 cells × 500 ppc × 774 144 steps, ~1 h 30 m on one RTX 4070 by the parent's
0.0068 s/step, plus the ambient's ppc and the larger collision set.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 1.199 | PASS |
| G2 `dz/lambda_D` target / ambient | 116.2 / **1.13** | INFO |
| G3 laser-off control | not run | deferred |
| G4 `ray_cfl` | 0.25 | WARN, as parent |
| G5 ppc | 500 target / 1 ambient | PASS |
| G6 energy closure | | post-run |

## Result
_Pending._

## Retracted
Nothing yet.
