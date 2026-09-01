# P5_ncr_200 — Tier 3 regime map

**Phase.** 5, `TEST_PLAN.md` §13. **Read each Tier 3 family as a set, never one run alone.**
**Question.** How does the module behave across the peak densities anyone has actually validated it at (1.5–3 `n_cr`) versus the 10 `n_cr` every P5 leg uses?
**Expected.** Absorption rises with the reservoir behind critical. G1 (`ω_pe·Δt` at peak compression) becomes the binding constraint at the top of the range.
**Falsified by.** Nothing — it is a map. But a G1 **failure** at 20 `n_cr` is a real result: it is the regime boundary, and should be recorded as one rather than worked around.

---

## What this run is

TIER 3a REGIME MAP -- target peak density 20.0 n_cr, everything else held.
    NOT a test of critical-layer resolution: with an exponential corona anchored at n_cr the
    crossing gradient is the scale length regardless of how dense the solid behind it is (that
    is 3c's job). What this varies is how much plasma sits BEHIND critical -- the reservoir the
    laser never reaches directly, which sets the ablation supply and the compression the target
    can reach.
    It also spans the regime upstream actually validated. ACCURACY.md's exit-overshoot ladder
    ran a 1.5 n_cr target and Finding 4's shock decks ran 1.5-2.5 n_cr; every P5 leg is 10.
    G1 (omega_pe*dt at the peak compressed density) is the binding limit here and will bite at
    20 n_cr -- if the gate refuses this rung, that refusal IS the regime boundary and should be
    recorded as one rather than worked around.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####~                                                             
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 20 n_cr, 500 d_e thick, centred at -250 d_e
  ~  coronal ramp   : exponential, L_n = 29.8024 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 20300 steps = 2.007 ps
```

## Result

*(pending — submitted 2026-08-31)*

## Retracted

Nothing.
