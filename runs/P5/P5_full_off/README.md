# P5_full_off — G3 laser-off control for `P5_full`

**Phase.** 5, `TEST_PLAN.md` §13
**Question.** How much of `P5_full`'s plume `T_e` is the laser, and how much is the grid?
**Expected.** The cold solid is Debye-under-resolved by ~58× (`dz/λ_D` = 58.1), so it is a
standing numerical heat source. Over `τ_own` 5.39 its contribution was tolerable. Over
24.26 nobody has measured it. Expect a slow, roughly linear rise in solid `T_e` and a much
smaller one in the plume band (0.05–1 `n_cr`), where `dz/λ_D` ≈ 1.8.
**Falsified by.** A plume-band `T_e` rise that is a significant fraction of `P5_full`'s —
that would say the headline number is partly grid heating and the leg cannot be quoted
without subtraction.

---

## Why a new control rather than the inherited one

`P4_lez_kin_ic6_off` is the existing G3 control and it **cannot do this job**: it is a
*reduced-mass* deck with a 4.5 `d_i0` target running 5.39 `τ_own`. A G3 subtraction is only
meaningful against a run that differs in the laser **and nothing else** — that is the whole
content of the gate. This run is `P5_full` with `intensity: 0.0` and no other change.

The combination that makes it mandatory here is specific: **absorption and grid heating both
look like energy arriving.** The energy budget alone cannot separate them, so a run whose
headline observable is plume `T_e` and whose duration has just been multiplied by 4.5 needs
the heating *rate* measured, not assumed.

## What is different from `P5_full`

`laser.intensity: 1.0e17 → 0.0`. That is the entire diff. `config.py` detects a control by
`intensity == 0` and the deck generator keys off it, so no ray march runs at all — this leg
should come in well under `P5_full`'s ~19.8 h.

## Geometry

Identical to `P5_full` (22040 cells, 500 `d_e` target at 10 `n_cr`, reflecting rear / open
front), with no beam:

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                    x  LASER OFF (I = 0)
      ####~                                                             
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ~  coronal ramp   : exponential, L_n = 29.8024 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 9139500 steps = 903.4 ps
```

## How it is used

`scripts/xcode_trajectory.py --g3 runs/P5/P5_full_off` subtracts this leg's plume-band
`T_e(τ)` from `P5_full`'s before any ratio against FLASH is formed. The subtracted and
unsubtracted curves are both reported; if they differ by more than the seed band from
`P5_seed`, the subtraction is load-bearing and must be stated with every quoted number.

## Result
*(to be filled in after the run)*

## Retracted
nothing yet — the run has not been launched.
