# P4_lez_kin_mr25_dzhalf — is the µ-sweep's step-0 absorption resolution-limited?

**Phase.** 4, `TEST_PLAN.md` §12
**Question.** Step-1 `τ_abs` across the µ-sweep scales as `µ^0.664`, where pure geometry (path
`L ∝ d_i0 ∝ µ^(1/2)` at an identical ζ-profile) predicts `µ^0.500`. `dz` is fixed at 0.5 `d_e`
while `d_i0/d_e ∝ µ^(1/2)`, so the legs differ **8.6×** in cells per `d_i0` — `mr25` resolves
the corona with 10 cells per `d_i0` where `mrreal` has 85.7. **Is the excess a ray-march
resolution artifact?**
**Expected.** If resolution is irrelevant, halving `dz` leaves step-1 `f_abs` at 0.07032. If
the coarse grid was *under*-integrating `K`, `f_abs` rises and the sweep's true exponent is
closer to 0.500.
**Falsified by.** Nothing — this is a null test on the worst-resolved leg, and either answer
bounds the artifact.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ##~                                                               
      ^                                                                ^
      reflecting                                                    open
      z = -25                                                  z = +1223

  #  target flat top : 10 n_cr, 22.5 d_e thick, centred at -11.25 d_e
  ~  coronal ramp   : exponential, L_n = 3.4775 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 4992 cells, dz = 0.25 d_e, dt = 0.04943 fs, 27648 steps = 1.367 ps
```

## Setup
Parent: **`P4_lez_kin_mr25_drift`**. `dz_over_de` 0.5 → **0.25** (cells 2496 → 4992), with
`max_grid_size` doubled to match so the one-box GPU rule still holds. Nothing else moves.

Only step 1 is needed: at that point the plasma is exactly the config IC, so the comparison
isolates the ray march from every dynamical effect.

## Cost
~2 min to the first dump; the leg is not run to completion.

## Gates
Unchanged from the parent except G2, which improves 2× by construction (`dz/λ_D` 58.1 → 29.1).

## Result
**Not a null. The coarse grid was under-integrating `K`.**

| `mr25` | cells | `f_abs(0)` | `τ(0)` |
|---|---|---|---|
| `dz` = 0.5 `d_e` (as the sweep runs it) | 2496 | 0.07032 | 0.03646 |
| **`dz` = 0.25 `d_e`** | 4992 | **0.08493** | **0.04438** |

**+21 % in `τ(0)` from halving `dz` alone.** Refitting the step-1 exponent across the sweep
with the better-resolved `mr25`:

```
tau(0) ~ mu^+0.664   with mr25 as the sweep runs it
tau(0) ~ mu^+0.623   with mr25 dz-halved
```

The µ-sweep holds `dz` at 0.5 `d_e` while `d_i0/d_e ∝ µ^(1/2)`, so the legs span **8.6×** in
cells per `d_i0` — 10 at `mr25` against 85.7 at `mrreal`. The low-µ legs are the least
resolved *in units of the structure being integrated*, they under-absorb, and that steepens
the fitted exponent. `mrreal` at 85.7 cells per `d_i0` is presumably converged, so the true
exponent is **shallower than measured, by an amount this pair bounds at ~0.04 and does not
fully determine.**

**This does not touch the operator.** It is a grid-resolution property of how the sweep was
*specified* — `dz_over_de` held fixed, per the project convention (gate G7) — and it applies
equally to any code integrating the same profiles on the same grid.

## Retracted
nothing
