# P4_lez_kin_off_dz125 — is the electron energy drain a Debye-resolution artifact?

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** Every kinetic WarpX run drains electron energy into the ions. PSC (same mass
ratio, same laser kernel, cross-validated to 8e-9) and WarpX's **own hybrid** (fluid electrons)
do not. Is the drain a numerical artifact of **Debye under-resolution**?

**Why this run is the clean reproducer.** The laser-off runs show the drain with **no
absorption, no temperature floor and no collisional heating** in play.
`P4_lez_kin_ic6_off` falls to `E_e/E_e0` = **0.795 at τ 1.35** and **0.647 by τ 27**, with the
loss appearing in the ions (×2.67).

**The one first-order numerical difference left.**
`dz/λ_D = (dz/d_e)·√(m_e c²/kT)` — **density-independent**, since `λ_D/d_e = v_th/c`.

| | `dz/d_e` | `m_e c²` | at 120 eV | at 400 eV |
|---|---|---|---|---|
| WarpX kinetic (control) | 0.5 | 511 keV | **32.6** | **17.9** |
| **this run** | **0.125** | 511 keV | **8.2** | **4.5** |
| PSC (paper) | 0.2 | 60 keV | 4.5 | 2.4 |

Gate G2's budget is **8**. WarpX's plume runs 2–4× over it; PSC sits inside it because its
**reduced speed of light** makes `λ_D/d_e = v_th/c` larger by √(511/60) = 2.92 at the same
temperature. This run puts WarpX in PSC's regime.

**Controls.** `P4_lez_kin_ic6_off` — identical but for `dz_over_de` (0.5 → 0.125) and the
step count needed to reach the same physical time.

**Expected.**
1. **Numerical**: the dip shrinks materially — `E_e/E_e0` at τ 5.39 rises from 0.706 toward 1.
2. **Physical**: the dip is unchanged, the drain is real ambipolar transfer, and PSC/the hybrid
   differ for some other reason.

**Falsified by.** Outcome 2, which would move the search to the current deposition/field
solve itself rather than to resolution.

**Prior evidence, and it points at outcome 2.** The 511 keV PSC run degraded PSC's own
`dz/λ_D` by 2.92× (2.4 → 7.1 in its plume) and its energy partition barely moved
(0.68 → 0.62–0.67). That is weak sensitivity, so I do **not** expect resolution alone to
account for 0.68 → −0.08. Recorded before running.

**Cost.** 4× cells and 4× steps for the same physical time ≈ 16× the control's short run.
`ic6_off` ran 552 960 steps in 17 min; this is 442 368 steps at 20 000 cells, so expect
**~40–60 min**.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                    x  LASER OFF (I = 0)
      ##~                                                               
      ^                                                                ^
      reflecting                                                    open
      z = -50                                                  z = +2450

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 20000 cells, dz = 0.125 d_e, dt = 0.02471 fs, 442368 steps = 10.93 ps
```

## Result
_Pending._

## Retracted
Nothing yet.
