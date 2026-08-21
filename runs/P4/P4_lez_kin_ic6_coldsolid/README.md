# P4_lez_kin_ic6_coldsolid — is the 20 eV solid where the absorbed energy goes?

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** WarpX's plume runs 3× colder than PSC's and FLASH's (165–187 eV vs 455–563 and
472–646) even with PSC-equivalent heating and matched `f_abs`. Corrected for baseline, WarpX
puts **comparable or more** absorbed energy into its electrons than PSC does. So where does it
go? The **solid** holds ~97 % of the electrons and WarpX starts it **16× hotter** than PSC.

| | solid `T_e` at t = 0 |
|---|---|
| WarpX `theta_e_solid` | **20.0 eV** |
| PSC, from the FLASH IC | **1.26 eV** (areal-weighted) |

**Setup.** `P4_lez_kin_ic6_pscheat` — already PSC-equivalent in heating — with
**`theta_e_solid` 3.914e-5 → 2.466e-6** (20 → 1.26 eV) and nothing else changed. Deck diff
against the control is the single `th_ts` line.

**Control.** `P4_lez_kin_ic6_pscheat`, identical dump times.

**Why 20 eV was there.** A **deliberate, documented** departure (`CLAUDE.md`: *"NOT FLASH's
0.1377 eV: the cold solid is Debye-unresolvable"*), chosen for numerics rather than physics.

**Expected.**
1. **The solid was the sink**: the plume `T_e` rises toward PSC/FLASH, and the electron share
   of the energy gain rises from 0.26–0.31 toward 0.65–0.69.
2. **It was not**: plume `T_e` is unchanged, and the 20 eV solid is cleared as a candidate.

**Falsified by.** Outcome 2.

**Stated risk, in advance.** `dz/λ_D` in the solid rises from **80 to ~318** — that is exactly
why the departure was made. This run may grid-heat or go unstable. **If it does, that is
itself the answer**: it would mean the 20 eV solid is not a free choice but a numerical
necessity, and the resulting energy budget cannot be compared with PSC's on this grid. Watch
the electron energy for anomalous *growth* as well as the plume temperature.

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
**Outcome 2 — FALSIFIED. The 20 eV solid is cleared.** 6 min, `reached max_step`, `--verify`
OK, **no NaN and no instability** despite `dz/λ_D` ≈ 318 in the solid. Deck diff is the single
`th_ts` line.

| τ_own | | plume `T_e` | `/FLASH` | e share | `E_e/E_e0` |
|---|---|---|---|---|---|
| 1.35 | pscheat (20 eV) | 165.2 | 0.350 | −0.738 | 0.916 |
| | **coldsolid (1.26 eV)** | **179.3** | **0.380** | 0.003 | 1.001 |
| 2.70 | pscheat | 171.3 | 0.306 | −0.100 | 0.974 |
| | **coldsolid** | **147.0** | **0.263** | 0.203 | 1.150 |
| 5.39 | pscheat | 186.6 | 0.289 | 0.312 | 1.215 |
| | **coldsolid** | **166.6** | **0.258** | 0.450 | 1.825 |

`E_e0` drops 5.077e5 → 1.704e5 J (×0.34) as intended. The electron share and `E_e/E_e0` both
rise — **but those are the baseline-sensitive measures**, and they rise for the same arithmetic
reason flagged in RESULTS 2026-08-20 (kick): a smaller denominator. The **un-normalised** plume
temperature is *better at τ 1.35 and worse at τ 2.70 and 5.39*, ending at **0.258× FLASH
against the control's 0.289×**.

**The solid is not where the absorbed energy is going.** Emptying it of 66 % of its initial
energy did not warm the plume.

**Incidental**: the run was stable at `dz/λ_D` ≈ 318 over 110 592 steps with no NaN and no
anomalous electron-energy growth, so the documented reason for the 20 eV departure did not
bite on this timescale. That does not license changing it — grid heating accumulates with step
count, and this is 1/5 of a production run.

## Retracted
The "energy is going into the solid" hypothesis from RESULTS 2026-08-20 (kick).

## Retracted
Nothing yet.
