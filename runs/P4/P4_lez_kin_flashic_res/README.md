# P4_lez_kin_flashic_res — the same leg with a SEMI-INFINITE RESERVOIR

**Phase.** 4, `TEST_PLAN.md` §12; decision **D5** (`n_max` / target mass).

**Question.** How much of the FLASH↔WarpX profile-shape gap is simply that **FLASH's
target is effectively infinite and ours is a foil**? FLASH ablates **0.275 %** of a
795 `n_cr` × 295 `d_e` solid over 27 τ; `P4_lez_kin_flashic_ct` loses 5–15 % of a
40 × 200 slab. The measured signature is a **plateau-and-cliff** profile — zero
macroparticles beyond ζ = 70 — against FLASH's smooth exponential still at
7.5e-3 `n_cr` at ζ = 100 (`studies/plume_structure/`, 2026-08-18).

**Expected.** The plateau-and-cliff becomes an **exponential tail**, the plume front moves
out from 0.46× toward FLASH's value, and the log-slope becomes closer to constant. If the
reservoir is the dominant cause, `d2_shape.py`'s raw slope std should fall toward FLASH's
0.33.

**Falsified by.** The profile shape not changing — which would mean the finite reservoir is
*not* what produces the cliff, and the remaining causes (no electron conduction; the
unrelaxed corona) carry it.

**Parent.** `P4_lez_kin_flashic_ct`. **The deck differs in the injector block and nothing
else** — verified by diff — so this is a genuine single-variable test, which the parent
itself was not.

## Geometry
```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
       #####~                                                           
      ^                                                                ^
      reflecting                                                    open
      z = -224                                                  z = +2464

  #  target flat top : 40 n_cr, 200 d_e thick, centred at -100 d_e
  ~  coronal ramp   : exponential, L_n = 6.955 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 5376 cells, dz = 0.5 d_e, dt = 0.07061 fs, 149184 steps = 10.53 ps
```

## Setup — the one change

```
target_injector.species              = targ_electrons
target_injector.neutralizing_species = targ_ions      # exact charge balance, zero net rho
target_injector.intervals            = 20
target_injector.tau                  = 400./wpe       # 0.226 ps = 2.1 % of the run
target_injector.lo                   = -200.*de       # the REAR HALF of the slab
target_injector.hi                   = -100.*de
target_injector.density              = 40.*ncr        # the slab's OWN initial density
target_injector.ppc_reference        = 500
```

**Why the rear half and not the whole slab.** The slab spans −200 → 0 `d_e` with its
laser-facing face at `z` = 0. Replenishing the cells the laser is currently ablating would
suppress the very dynamics being measured; the box stops **100 `d_e` short of the face**,
so the front half ablates freely while the rear half stands for the semi-infinite solid
behind it.

**Why pin at 40 `n_cr` and not higher.** The operator replenishes a *deficit*. Pinning
above the slab's own density would make it a particle **source**, breaking the mass and
energy closure instead of modelling a reservoir — `config.validate` now refuses it.

## Cost
Identical to the parent: 5376 cells × 500 ppc × 149 184 steps, **~15 min** on one RTX 4070
at 0.0061 s/step, plus whatever the injector adds. `max_step` is deliberately left at the
parent's value so the A/B is exact — note that means it spans **τ = 140**, with τ = 27
(the FLASH-matched window) at step 28 695.

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 1.199 at 2.3× compression | PASS |
| G2 `dz/lambda_D` | 326.9 | INFO |
| G3 laser-off control | not run — see the parent's README | deferred |
| G4 `ray_cfl` check | 0.25, interior critical surface | WARN, as parent |
| G5 ppc / `Tlocalfrac` | 500 | PASS |
| G6 energy closure | **watch this one** | post-run |

**G6 matters more here than in any earlier run.** The injector *adds macroparticles and
energy by construction*, so the usual "weight is conserved" check no longer applies. The
right check is that injected weight ≈ the deficit implied by what left the box, and that
the injected population is cold (`u_std` = `sqrt(th_ts)`, the solid temperature) rather
than silently heating the reservoir.

## Result
_Pending._

## Retracted
Nothing yet.
