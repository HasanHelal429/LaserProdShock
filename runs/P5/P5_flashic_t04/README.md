# P5_flashic_t04 — handoff-time ladder, rung `t₀ = 0.4 ns`

**Phase.** 5, `TEST_PLAN.md` §13. **Read with `P5_flashic` (t₀ = 0.1) and the other rung.**
**Question.** Does the WarpX evolution remember where it started?
**Expected.** Over the shared window 0.4 → 1.0 ns the rungs are the same physical problem
handed over at different points. If their trajectories collapse onto one another, the
evolution has forgotten the handoff.
**Falsified by.** Rungs that stay separated — then the FLASH↔WarpX comparison is
substantially a comparison of *initial conditions*, and running longer does not fix it.

---

## Why this is the sensitivity test worth running

FLASH ran the entire 1 ns, so it can seed a PIC leg at **any** time. That makes the
handoff a controllable variable rather than a fixed assumption, and it is the only test
that separates "our IC is imperfect" from "the IC does not matter".

There is prior evidence for the optimistic outcome, and it is narrow:
`d(ln T_plume)/d(ln T_IC)` = **0.156** measured on `P4_lez_kin_mr100_sim`
(`HANDOFF.md` §7.4) — the plume temperature is set by the *laser*, not by the handoff. But
that was **one knob**, on a **reduced-mass** leg, with an **analytic** IC. This ladder tests
the whole initial condition at real mass with the profile lifted.

Note the two effects run opposite ways and the ladder measures the net: a later handoff
gives a **better-conditioned** start (less of the profile is clipped by the 10 `n_cr` cap —
46.6 % of cells at 0.1 ns, 33.8 % at 0.2, 25.1 % at 0.4) but a **shorter** window in which
to forget it.

**What is different from `P5_flashic`:** `ic_flash.yaml` is fitted to FLASH's 0.4 ns
plotfile, and `max_step` = 6093000 so the run still ends at `t_FLASH` = 1.0 ns
(602.3 ps of WarpX time). Nothing else.

**Cost.** Strictly cheaper than the spine — this rung is 602.3 ps against 903.4.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 6093000 steps = 602.3 ps
```

## Result
*(to be filled in after the run)*

## Retracted
nothing yet — the run has not been launched.
