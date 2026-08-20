# P4_lez_kin_ic6_tfloor

**Phase.** 4, `TEST_PLAN.md` §12.

**Question.** Is WarpX's 3-6x absorption deficit caused by the laser temperature FLOOR?
`LaserDeposition.cpp:703` sets `m_theta_floor = m_theta_e`, so the floor DEFAULTS to
`electron_temperature` (378.3 eV here), and the gate at :1017 accepts a measured per-cell
`T_e` only if `kT > kT_floor`. Against a ~120 eV plume the measurement is never accepted,
`Tlocalfrac` reads 0, and `K` is evaluated at 378.3 eV for the whole run. `K` goes as
`T^(-3/2)`, so that suppresses absorption. This run lowers the floor to 20 eV.
 See `config.yaml` `meta.description` for the full
statement of the check and its prediction, and RESULTS.md 2026-08-19 (root cause) for the
finding these two runs test.

**The finding under test.** WarpX absorbs `f_abs` = 0.15–0.32 where PSC absorbs 0.47–0.56 and
FLASH 0.870, on the same IC and with a kernel cross-validated to 8e-9. Traced in the source to
`LaserDeposition.cpp:703`, `m_theta_floor = m_theta_e` — the temperature floor **defaults to
`electron_temperature`** (here `th_t` = 378.3 eV) — and the gate at :1017 accepts a measured
per-cell temperature **only if `kT > kT_floor`**. The plume sits at ~120 eV, so the
measurement is never accepted, `Tlocalfrac` reads 0, and `K` is evaluated at 378.3 eV
everywhere. `K ∝ T^(-3/2)` makes that a **5.6×** under-estimate.

**Controls.** `P4_lez_kin_ic6` (the production configuration) on identical dump times, and
each other — A changes the floor, B changes ppc, neither changes anything else.

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
**CONFIRMED — the temperature floor was suppressing absorption by ~2×.** 5 min,
`reached max_step`, `--verify` OK, `laser_deposition.temperature_floor = 3.914e-05` in
`warpx_used_inputs`.

| τ_own | control `f_abs` / `Tlocalfrac` | **floor 20 eV** |
|---|---|---|
| 0.50 | 0.142 / 0.000 | **0.308 / 0.233** |
| 2.70 | 0.217 / 0.000 | **0.545 / 0.394** |
| 5.39 | 0.319 / 0.000 | **0.634 / 0.667** |

`Tlocalfrac` activates immediately (0.001 → 0.43 at step 0) and `f_abs` roughly **doubles**,
landing at 0.31–0.63 — squarely on PSC's 0.47–0.56. `E_abs` to τ 5.39 rises
**2.3805e5 → 5.2571e5 J (2.2×)**.

**But it does not close the temperature gap.** `T_e` goes 119.3 → 184.6 eV at τ 2.70
(0.213 → **0.330** of FLASH) and 123.4 → 199.0 at τ 5.39 (0.191 → **0.308**). Doubling the
absorbed energy bought ~+55 % of `T_e`, leaving WarpX still **3× below** FLASH and PSC.
`T_i/T_e` stays ≈1.09, so the collisional inversion is untouched by this (as expected).

**Status: a real, confirmed misconfiguration — not the whole story.**

## Retracted
Nothing yet.
