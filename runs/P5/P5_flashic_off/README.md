# P5_flashic_off — G3 laser-off control for the spine

**Phase.** 5, `TEST_PLAN.md` §13
**Question.** How much of `P5_flashic`'s plume `T_e` is the laser, and how much is the grid?
**Expected.** `dz/λ_D` = 58 in the solid, so it is a standing numerical heat source; the
plume band (0.05–1 `n_cr`), where every benchmark number is actually measured, sits near 1.8
and should heat far less. Expect a slow rise in the solid and a small one in the plume.
**Falsified by.** A plume-band rise that is a significant fraction of the spine's — the
headline could then not be quoted without subtraction.

**Why not `P5_full_off`.** A G3 subtraction is only meaningful against a run differing in
the laser and **nothing else**, so the spine's control must carry the spine's initial
condition. `P5_full_off` holds the analytic exponential, which is a different plasma —
1.80× the optical depth — and therefore a different grid-heating problem.

**What is different from `P5_flashic`:** `laser.intensity: 1.0e17 → 0.0`. That is the whole
diff. No ray march runs, so this comes in under the spine's ~19.8 h (4070) / 8–13 h (A100).

**How it is used.** `scripts/xcode_trajectory.py --g3 runs/P5/P5_flashic_off` removes this
leg's plume-band `T_e` *rise* (not its level) before any ratio against FLASH is formed. Both
curves are reported; if they differ by more than the `P5_seed` band, the subtraction is
load-bearing and must be stated with every quoted number.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                    x  LASER OFF (I = 0)
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 9139500 steps = 903.4 ps
```

## Result
*(to be filled in after the run)*

## Retracted
nothing yet — the run has not been launched.
