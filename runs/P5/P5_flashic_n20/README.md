# P5_flashic_n20 — the density-cap A/B against the spine

**Phase.** 5, `TEST_PLAN.md` §13
**Question.** Is the 10 `n_cr` cap — the largest surviving structural departure from FLASH —
a live lever on absorption and plume `T_e` at real mass?
**Expected.** **Less** absorption, moving toward FLASH's. The 2026-08-29 audit gives the
mechanism: FLASH's critical surface sits inside a near-vertical front to 795 `n_cr`, ours on
a 10 `n_cr` plateau, and a higher cap steepens the gradient at the turning point where the
IB kernel diverges as `(1−n̂)^(−1/2)`.
**Falsified by.** A change inside the `P5_seed` band, which eliminates the cap and moves the
question to electron thermal transport (D3 Appendix C, never run).

---

**What is different from `P5_flashic`:** `density_over_ncr: 10.0 → 20.0`. Nothing else.

**How the cap acts on a lifted IC.** With `corona_profile: flash_table` the density comes
entirely from the node table, and `density_over_ncr` is the **clip applied at fit time** by
`flash_ic_fit.py`. So `ic_flash.yaml` here is a genuinely different table, not the same one
read differently, and it must be regenerated whenever the cap changes.

A telling detail from the fit: the clip binds on **46.6 % of cells at both 10 and 20 `n_cr`**
— the *same* cells. FLASH's front is so steep that nothing sits between them, which is the
same fact that put **no FLASH cells at all** in `0.9 < n/n_cr < 1`. The cap therefore changes
the *value* on the overdense side, not its extent: exactly the gradient test intended.

**G1 is the binding gate.** `ω_pe·dt` = √20 × 0.175 = **0.783** at `t` = 0 and **1.107** at
the gate's 2.0× compression, against a **1.2** limit — an **8 % margin, not a comfortable
one**. Read `run_checks.py` G1 before launch *and* at the peak compressed density the run
reaches. If compression exceeds ~2.35×, drop `cfl` to 0.25 and accept the 1.4× cost rather
than trusting the margin: a G1 violation once grew total particle energy **21×** while the
laser supplied 1/1400 of it. `dz/λ_D` in the solid also rises 58.1 → **82.2**.

**Order.** Hold until `P5_flashic` reports. If the ratio curve comes back flat, the cap
question changes shape.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 20 n_cr, 500 d_e thick, centred at -250 d_e
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 9139500 steps = 903.4 ps
```

## Result
*(to be filled in after the run)*

## Retracted
nothing yet — the run has not been launched.
