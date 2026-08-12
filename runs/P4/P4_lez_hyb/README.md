# P4_lez_hyb — hybrid leg of the Phase-4 cross-code benchmark

**Phase.** 4, `TEST_PLAN.md` §12, esp. §12.4
**Question.** With kinetic electrons replaced by an Ohm's-law fluid and *nothing else*
changed, does the answer survive — and if it does not, does the failure localise to the
electron closure, which is the only thing that differs?

**Status: config written, NOT LAUNCHED.** Blocked on the §12.3 tooling work (`deck.py`
emits no hybrid solver block).

Spec: `TEST_PLAN.md` §12, esp. §12.4. Decisions: `runs/P4/README.md` (**D2**).

---

## Why this run exists

The paper compares two models: FLASH (fluid, conducting electrons) and PSC (kinetic
electrons). **The hybrid sits exactly between them** — kinetic ions, fluid electrons closed
by Ohm's law — and the paper has no such leg.

That position is what makes the run worth the compute. `P4_lez_hyb` is configured to be
identical to `P4_lez_kin` in *every* physical respect — same target, laser, box, grid,
mass ratio, charge state (checked: the two configs agree on all 15 shared physics keys) —
and to differ in exactly one: the electron closure. So if FLASH and full PIC agree and the
hybrid does not, the disagreement **localises to the closure**. There is nowhere else for
it to come from.

This is a sharper test of `feature/hybrid-laser` than anything we could design from
scratch, because the answer is already published for the two bracketing models.

## The prediction, stated in advance

`hybrid_pic_model.electron_energy_mode = advected` integrates

```
dTe/dt + u_e . grad Te = -(2/3) Te div u_e + (2/3) S/n_e
```

— advection, compression, and the laser source. **There is no `div q_e`.** The
`conducting` mode aborts as unimplemented; the abort message says so outright.

FLASH's ablation front is *set* by Spitzer conduction with a Larsen flux limiter
(`α_ele` = 0.06), and the paper's §III.C is entirely about heat flux. So:

| | Prediction |
|---|---|
| A1 `n_e`, A4 `V_z`, A8 rarefaction | **PASS** — advection-dominated, which is what `advected` does model |
| A2 `T_e` near the ablation front | **FAIL** — conduction-dominated, and there is no conduction |

**If it passes A2 anyway**, then thermal conduction is not what sets the front at these
parameters, §12.4's premise is wrong, and the case for writing a conduction solver
weakens. That is a result worth having either way — which is exactly why this control runs
**before** any conduction solver is written (decision **D2c**).

## Geometry

Identical to `P4_lez_kin` — same target, same box, same grid. That is the point of the run,
and it is checked mechanically: the two configs agree on all 15 shared physics keys.

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1693 um

                                                               <== laser
      ####~~~~~~                                                        
      ^                                                                ^
      open                                                          open
      z = -50                                                  z = +950

  #  target flat top : 10 n_cr, 45 d_e thick, centred at -22.5 d_e
  ~  coronal ramp   : Gaussian, L_n = 27 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 2000 cells, dz = 0.5 d_e, dt = 0.09885 fs, 552960 steps = 54.66 ps
```

The one thing the diagram does **not** show is the difference that matters: in this run the
`#` and `~` regions contain **no electron macroparticles at all**. Ions are still particles;
electrons are a fluid living on the grid. The laser's absorbed power `P_abs` becomes a source
term `S` in that fluid's energy equation instead of a momentum kick on electron
macroparticles.

`dt` differs too, and by a lot. With no electron macroparticles and `B0` = 0, neither the
`ω_pe` nor the whistler constraint applies, so `dt` is set by the ion CFL — 10 `d_e/c`
against the kinetic run's 0.175, i.e. **57× larger**, giving 10 240 steps against 552 960
for the *same physical duration* (54.66 ps, which is the paper's 1 ns — see the kinetic
run's README for the two rescalings).

## Setup

Identical to `P4_lez_kin` except:

```
no electron macroparticles       -> no omega_pe dt gate, no Debye gate, no f(v_e) diagnostic
algo.maxwell_solver = hybrid     electron_energy_mode = advected, elec_temp = 100 eV
laser density_source = hybrid_rho    temperature_mode = hybrid_fluid    deposit_to = fluid
B0 = 0                           -> Ohm's law reduces to E = eta*J - grad(Pe)/(e n_e)
dt = 10 d_e/c (57x the kinetic step)  -> 10240 steps for the SAME physical duration
```

`B0 = 0` is not a degenerate case here: it is the `grad(Pe)` term that drives ambipolar
expansion, i.e. the ablation physics this benchmark is about. Dropping `B` removes the
whistler CFL and is why this leg is so much cheaper than the kinetic one.

`gamma` is deliberately **absent** from the config. Under `advected` WarpX solves
`eps = (3/2) n kB Te`, which fixes `gamma = 5/3`, and it aborts on a conflicting value —
applying the polytropic closure on top would count compression heating twice.

## Traps specific to this run

1. **Never baseline on the step-0 dump.** Hybrid WarpX writes step-0 diagnostics *before*
   `rho` is deposited. This is a standing project rule and it bites hardest in a run whose
   whole point is a temperature field.
2. **The `T_e` comparison is against a fluid field, not a particle moment.** In
   `P4_lez_kin`, `T_e` is a measured moment of the electron distribution; here it is a
   solved field. They are the same symbol and not the same object, and the difference is
   the entire subject of the run — label figures accordingly.
3. **The paper's Fig. 8 result is structurally unavailable.** Non-Maxwellian `f(v_z)` near
   the critical surface cannot be diagnosed without kinetic electrons. That absence is part
   of what this leg demonstrates about the closure, so it is not a gap to be apologised for
   — but no claim about electron distributions can come from this run.
4. **Normalised units only** — see `TEST_PLAN.md` §12.2. Same trap as the kinetic leg.

## What follows from the result

Under **D2**, this control is step one of two. If it fails A2 as predicted, the case for
implementing `electron_energy_mode = conducting` (Spitzer `κ_e` + Larsen flux limiter) is
made *quantitatively* rather than by assertion, and the re-run becomes the measurement of
whether the implementation worked. That is the single highest-value code item this phase
could produce: the difference between "our hybrid can drive shocks" and "our hybrid can
model ablation".

## Result

**Not yet run.** Blocked on the §12.3 tooling — `config.py` rejects
`temperature_mode: hybrid_fluid` today, which is the gap made concrete:

```
ValueError: laser.temperature_mode must be 'local' or 'fixed'
```

The operator supports the three hybrid swaps; only the config path is missing.

Expected, recorded now so it can be falsified: **passes A1, A4, A8; fails A2 near the
ablation front.**

## Retracted

Nothing yet — this run has not produced a number.
