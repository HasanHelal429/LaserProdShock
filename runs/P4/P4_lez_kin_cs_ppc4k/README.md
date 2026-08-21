# P4_lez_kin_cs_ppc4k — is WarpX under-sampled where the laser deposits?

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** WarpX's fixed-ppc loading thins out as the corona expands; PSC's fixed-weight
loading keeps particles where the density is. Measured at τ_own 5.39, macroparticles per
simulation cell:

| `n_e` band | WarpX (500 ppc) | PSC (`NNpart` = 1000) |
|---|---|---|
| 0.01–0.03 `n_cr` (front) | **42** | 17 |
| 0.03–0.1 | 62 | 55 |
| 0.1–0.3 | **71** | 173 |
| **0.3–1.0 `n_cr`** | **184** | **548** |

At the front WarpX has 2.5× *more*; at **0.3–1.0 `n_cr` it has 3× fewer** — and that band is
exactly where the laser deposits (median deposition density **0.5–0.7 `n_cr`**, measured
2026-08-20). **Does under-sampling the absorption region suppress the electron heating?**

**Why the earlier ppc test does not settle this.** `P4_lez_kin_ic6_ppc2k` ran on the
**broken-floor** configuration (`f_abs` 0.13–0.27, `Tlocalfrac` = 0). With the floor fixed the
coefficient responds to the measured `T_e`, so per-cell sampling now feeds back into
absorption in a way it could not before — `K ∝ T^(-3/2)` is convex, so sampling noise biases
`K` **high** (gate G5).

**Setup.** `P4_lez_kin_ic6_coldsolid` with **ppc 500 → 4000** and nothing else changed. That
puts ~1470 macroparticles per cell at 0.3–1.0 `n_cr`, comfortably above PSC's 548. Deck diff
against the control is the two `num_particles_per_cell_each_dim` lines.

**Control.** `P4_lez_kin_ic6_coldsolid`, identical dump times.

**Expected.**
1. **Sampling was suppressing it**: plume `T_e` rises toward PSC/FLASH.
2. **It was not**: `T_e` unchanged, and particle sampling is cleared on the *fixed*
   configuration rather than only on the broken one.

**Falsified by.** Outcome 2.

**Prior evidence.** `ppc2k` (4×, broken floor) moved `T_e` by <2 %, and `studies/ppc_ladder`
found ppc was not the lever for the `T_e` shape either (RISE 0.945 vs 0.944 at 500 vs 2000).
So outcome 2 is the more likely, but neither test had a working local temperature.

**Cost.** 8× particles ⇒ ~45 min.

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
  grid              : 5000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 110592 steps = 10.93 ps
```

## Result
**A modest, MARGINAL effect — not a resolution of the gap.** 36 min, `reached max_step`,
`--verify` OK, ppc = 4000 confirmed in `warpx_used_inputs`. Sampling goal met: **2003**
e-macroparticles per cell at 0.3–1.0 `n_cr` against the control's 184 and PSC's 548.

| τ_own | | `T_e` | `/FLASH` | `T_i/T_e` | `f_abs` |
|---|---|---|---|---|---|
| 1.35 | ppc 500 | 180.3 | 0.382 | 1.054 | 0.352 |
| | ppc 4000 | 182.4 | 0.386 | 1.000 | 0.308 |
| 2.70 | ppc 500 | 146.4 | 0.262 | 1.210 | 0.295 |
| | **ppc 4000** | **167.9** | **0.300** | **0.906** | 0.402 |
| 5.39 | ppc 500 | 148.6 | 0.230 | 1.339 | 0.379 |
| | **ppc 4000** | **181.8** | **0.281** | **1.022** | 0.263 |

`T_e` rises 15–22 % at the two later times and `T_i/T_e` falls from 1.34 to 1.02 — both in the
right direction, and the `T_i/T_e` move is the cleaner signal.

**But it is marginal, and the honest reason is measured here.** The control run reads
`T_e` = 148.6 eV at τ 5.39, where **the same configuration measured 166.6 eV** in its earlier
incarnation (it was re-run with a finer `phase_intervals` for the movie; physics identical).
That is **12 % run-to-run scatter**, consistent with `CLAUDE.md`'s *"the CUDA build is not
run-to-run reproducible AT ALL"*. A +22 % effect against 12 % scatter is roughly 2σ on a
sample of one.

**And it does not close the gap regardless.** 0.281 × FLASH against PSC's 0.87–0.96. Eleven
times the particle count at the absorption region, and 72 % of the discrepancy remains.

**What to do with it.** The direction and the `T_i/T_e` improvement are worth keeping, but the
claim needs a repeat of both legs before it is quotable. **Any `T_e` difference below ~15 %
measured from single CUDA runs in this project should be treated as noise** — that applies
retrospectively to several small differences reported today.

## Retracted
Nothing from this run.

## Retracted
Nothing yet.
