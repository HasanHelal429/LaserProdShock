# P1_vac_1d_long — the reference ablation run 10× longer (1D, vacuum, 100 ps)

**Phase.** 1, `TEST_PLAN.md` §7.1 and §2.4
**Question.** `P1_vac_1d` showed absorption **floors** at `f_abs` ≈ 0.23 instead of shutting
off, with `E_abs` still rising linearly at the final step. That established the drive does not
shut off *within 10 ps*. **Does it ever?**

**Why 10 ps was not enough, and why 100 ps is the right number.** 99 % of `P1_vac_1d`'s
`E_abs` arrived by 9.90 ps of a 10.02 ps run — the measurement was truncated by the run, not
by the physics. Three independent clocks say 100 ps:

- **13 gyroperiods** at the Phase-2 reference `ω_ci0⁻¹` = 7.61 ps. Schaeffer needs
  `t*` ≈ 1, 2.5, 5 `ω_ci0⁻¹` (7.6 / 19 / 38 ps) for shock formation, so **Phase 2 needs the
  piston to still be driven at ~38 ps.** Whether the drive survives that long is the single
  most consequential thing Phase 1 can hand to Phase 2.
- **~7 rear-rarefaction slab crossings** (`w_t/c_s` = 14.3 ps at the measured
  `T_e,ab` = 0.507 keV). At 10 ps only ~70 % of one crossing had happened, so ~30 % of the
  slab was still cold — which is exactly why **H3 could not be fairly tested**. With the whole
  target processed, the bulk *is* the ablated population.
- **The rarefaction must eventually take the peak below `n_cr`**, at which point the beam
  punches straight through, there is no turning point at all, and absorption should collapse.
  100 ps is long enough to look for that.

**Expected.**
1. **The plateau persists far beyond 10 ps, and `E_abs` reaches ~2×10⁷ J/m².** If `f_abs`
   held at 0.23 for the whole run, `E_abs` = 0.23 × 10¹⁸ × 100.2 ps = **2.3×10⁷ J/m²**, ~9.4×
   the 10 ps value. Anything much *below* that means the plateau does close, and **the fall-off
   time is then the most important number in Phase 1** — it is the drive duration Phase 2 gets.
2. **The target rarefies below `n_cr` at some point**, and `f_abs` should drop sharply when it
   does — a qualitatively different event from the initial 1.000 → 0.23 fall (which was the
   corona thinning, not the peak going underdense). Watch peak `n_e` and `f_abs` together.
3. **H3 becomes testable.** With ≥ 1 slab crossing complete, the weight-weighted bulk is the
   ablated population, so α = `v_p/c_s` is a fair number rather than the α ≥ 0.46 lower bound
   the 10 ps run could offer.
4. **G6 still closes**, because the domain was sized from measured drift rates (below). Weight
   loss should stay ≲ 1 %; the 10 ps run lost 0.0104 %.

**Falsified by.** `E_abs` rolling over *without* the peak density going underdense (that would
mean a mechanism neither the shutoff picture nor the plateau picture describes); or a weight
loss large enough to void G6, which would mean the domain scaling below is wrong.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
                                         ##~~                           
      ^                                                                ^
      open                                                          open
      z = -3000                                                  z = +2400

  #  target flat top : 1.5 n_cr, 80 d_e thick, centred at -40 d_e
  ~  coronal ramp   : Gaussian, L_n = 60 d_e on the LASER-FACING side (face at z = +0)
  ' ' vacuum        : no ambient plasma
  grid              : 10800 cells, dz = 0.5 d_e, dt = 0.09783 fs, 1024000 steps = 100.2 ps
```

## Setup

Parent: **`P1_vac_1d`**. The target, laser, `dz`, `cfl`, ppc and boundaries are **identical**;
only the duration and the domain change, so this is a clean extension rather than a new run.

**1. Duration ×10: 102 400 → 1 024 000 steps = 10.018 → 100.18 ps.**

**2. Domain 2.7× larger: [−300, +700] → [−3000, +2400] d_e** (2000 → 10 800 cells).
**Sized from measured drift, not guessed.** `P1_vac_1d`'s ion-weight quantiles were tracked
across all 21 phase dumps; over the last few ps they move at:

| ion-weight quantile | drift rate | extrapolated to 100 ps |
|---|---|---|
| 1 % (rear of the bulk) | −14.3 d_e/ps | −1 510 |
| 99 % (front of the bulk) | +9.7 d_e/ps | +1 060 |
| 0.1 % / 99.9 % (tails) | −20 / +13 d_e/ps | −2 100 / +1 450 |
| 0.01 % (extreme rear) | −28 d_e/ps | −2 880 |

So [−3000, +2400] holds **99.9 % of the ion weight for the full 100 ps** with margin. The
0.01 % extreme tail will still leave — that is expected and cheap, and the weight-loss
fraction is the number to quote beside G6. **This is why the domain had to grow with the
duration**: `P1_vac_1d`'s rear expansion already reached its wall at t ≈ 7.5 ps, so simply
raising `max_step` on the old domain would have bled the plume into the boundary for 90 % of
the run and voided the energy budget.

Extra cells are affordable for the reason recorded in `CLAUDE.md`: `density_min = 1e-4·n_t`
still confines particles to z ∈ [−80, +182] at t = 0, so the macroparticle count is
**unchanged at 420 000** and the added 8 800 cells are empty field cells.

**3. Diagnostics scaled by 10× so the figure count is unchanged**, not the data volume:
`plotfile` 102 400, `field` 12 800 (80 frames), `phase` 51 200 (21 dumps), `reduced` 2 560.

**`laser.intervals` stays at 10 — it is NOT a diagnostic.** It is the deposition cadence, and
the kick amplitude goes as `√(H·Δt)` with `Δt = intervals·dt`, so changing it would change the
physics. The consequence is 102 400 `LASERDEP` lines in `run.log` (10× more), which is only a
parsing cost.

## Hazards specific to this run

- **The vacuum + `open` charge-imbalance concern from `P1_vac_1d` now has 10× longer to
  develop.** Electrons are absorbed at the wall while their ions remain, charging the box
  positive against a `pec` field boundary. It was benign at 10 ps (G6 closed to −0.74 %); it is
  the first thing to check if the late-time plume misbehaves. The larger domain helps.
- **Grid heating gets 1.024 million steps to accumulate**, which is why this run has its **own**
  10× control (`P1_vac_1d_long_off`) — the 10 ps control cannot bound a 100 ps run.

## Cost

10 800 cells, 420 000 macroparticles (unchanged), 1 024 000 steps → 100.18 ps.

**Measured** on this deck: 4 000 steps in 28.7 s on one RTX 4070 ⇒ **~123 min projected**.
Per step that is 7.19 ms against 4.70 ms at 2 000 cells, so the 5.4× cell increase costs only
**1.53×** — field work in 1D is real but sub-linear against the particle push. Run concurrently
with the control on the second GPU, so ~2 h wall for the pair. (Benchmarked rather than scaled,
per the rule the 10 ps run's 4× estimate error established.)

## Gates

`make_inputs.py --check`: **4 pass, 0 warn, 0 fail**, 2 info, 1 post-run — identical to
`P1_vac_1d`, since none of the gate inputs (`dz`, `cfl`, densities, ppc) changed.

| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | 0.303 at 2× compression (0.214 initial; hits 2 at 130.6 n_cr) | **pass** |
| G2 `dz/lambda_D` (target / ambient) | 61 target, cold / no ambient | info — bounded by G3 |
| G3 laser-off control | `P1_vac_1d_long_off`, same 100.18 ps | **pass** |
| G4 `ray_cfl` check | 0.25, ladder declared | **pass** |
| G5 ppc / `Tlocalfrac` | 400 ppc; bias bound ≤ 0.31 % | **pass** |
| G6 energy closure | — | post-run; **quote the weight-loss fraction with it** |
| G7 `dz` unchanged | 0.5 d_e,cr = 0.0838 µm, as every run in this project | info |

## Media

*(not generated yet)*

## Result

*(running)*

## Retracted

Nothing.
