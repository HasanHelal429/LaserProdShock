# P5_Ln_010_fine — Tier 3c fine rung (`ray_cfl` = 0.025)

**Phase.** 5, `TEST_PLAN.md` §13. Read with `P5_Ln_010`, never alone.
**Question.** How much does `E_abs` drift when **only** `ray_cfl` changes, at a corona whose
`1−r < 0.01` layer spans **0.20 cells**?
**Expected.** Drift falls as the layer resolves — at or near the 0.80 % seed floor by 1.20
cells, well above it at 0.20.
**Falsified by.** Drift independent of layer resolution. That would break the G8 threshold
and mean the Tier 1 correlation between layer cells and convergence was coincidence.

---

## Why this rung exists — a correction to Tier 3c

The first pass swept `L_n` at fixed `ray_cfl` and moved `E_abs` **2.5×** (6.99e4 → 1.78e5
across `L_n` = 10 → 60 `d_e`). That is **physics**: a longer corona holds more plasma at
absorbing densities, so optical depth rises with `L_n`. It swamps the numerical signal, so
absolute `E_abs` cannot distinguish "better-resolved layer" from "more plasma to absorb in".

The drift when *only* `ray_cfl` moves — physics held exactly fixed — is what isolates the
numerics. This rung supplies that at 0.20 cells, beside the two already measured:
**+4.3 %** at 0.60 cells and **+18.3 %** at 0.16–0.22 cells.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####                                                              
      ^                                                                ^
      reflecting                                                    open
      z = -521                                                  z = +10499

  #  target flat top : 10 n_cr, 500 d_e thick, centred at -250 d_e
  ~  coronal ramp   : exponential, L_n = 10 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 22040 cells, dz = 0.5 d_e, dt = 0.09885 fs, 20300 steps = 2.007 ps
```

## Result

*(pending — submitted 2026-08-31)*

## Retracted

Nothing. But see above: the first-pass reading of Tier 3c as a resolution test is
withdrawn — it measured an optical-depth scaling instead.
