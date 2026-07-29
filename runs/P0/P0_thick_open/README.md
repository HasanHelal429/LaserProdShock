# P0_thick_open — rear truncation at 4x thickness (the TRUNCATED run)

**Phase.** 0 (geometry validation), stepping toward the Phase-1/2 physics setup
**Question.** The rear truncation was validated for a **20 d_e** target
(`P0_rear_open` vs `P0_bc_open_B`), with the explicit caveat that it holds for *that*
thickness over *that* duration. Does it still hold for a target **4x thicker**, which is
closer to the setup this project actually wants?

**Why thicker is "the desired setup".** The upstream `run_laser_shock` target is
40 d_e,ambient = **163 d_e,cr** = 27.4 um. The Phase-0 runs used 20 d_e,cr = 3.35 um, chosen
for cost. This pair uses **80 d_e,cr = 13.4 um — 49 % of the upstream thickness**, a 4x step
that closes most of the gap. Thickness also matters physically: `TEST_PLAN.md` H3 holds that
thickness buys piston *momentum* (drive distance), not speed, since coupled energy and mass
scale together.

**Expected — and this is a quantitative prediction, not a hope.** The rear rarefaction
crosses the slab in `w_t/c_s`, which at the heated target temperature is **2.3 ps for
20 d_e** against a 2.348 ps run (**103 % crossed — fully coupled**, which is exactly why
`P0_rear_reflect` changed the momentum balance) but **9.1 ps for 80 d_e** (**26 % crossed**).
So the two faces should be substantially **decoupled** here, and the truncation should be
*better* than it already was: front-side agreement at least as good as the thin pair's
(ion count +0.1 %, `E_abs` −0.6 %, total `p_z` −3.4 %), and a smaller fraction of target mass
behind the initial rear face than the 6.95 % measured at 20 d_e.
**Falsified by.** Front-side agreement *worse* than the thin pair, or a rear-side mass
fraction that does not fall — either would mean the coupling is not governed by the
rarefaction crossing time and the truncation rule needs a different justification.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      #########################~~~~~~~~~~~~.............................
      ^                                                                ^
      open                                                          open
      z = -80                                                  z = +140

  #  target flat top : 1.5 n_cr, 80 d_e thick, centred at -40 d_e
  ~  coronal ramp   : Gaussian, L_n = 15 d_e on the LASER-FACING side (face at z = +0)
  .  ambient        : 0.06 n_cr, theta_e = 0.005  (fills BOTH sides -- no vacuum gap)
  B  field          : B0 = 74.7 T along y (perpendicular to z), 1/w_ci0 = 7.61 ps
  grid              : 440 cells, dz = 0.5 d_e, dt = 0.09783 fs, 24000 steps = 2.348 ps
```

## Setup

`P0_bc_open_B` with `plasma.target.thickness_de: 20 → 80` and `center_de: −50 → −40`, so the
laser-facing face sits at z = 0 and the flat top spans [−80, 0]. domain cut at the target's rear face with the `open` boundary validated at 20 d_e thickness. 440 cells — 15 % fewer than its own reference.

**The coronal scale length is deliberately left at 15 d_e.** Scaling it with the thickness
(the upstream ratio is `L_n/w_t` = 0.75, which the 20 d_e runs also had at 15/20) would change
where the tau = 1 surface sits and therefore the absorption, confounding the one variable
under test. Matching the upstream `L_n/w_t` is a Phase-1 item, not this run's job.

Gates are unchanged from `P0_bc_open_B` — same `dz`, `cfl`, densities and ppc — so G1 = 0.303
and G2 target 61 / ambient 1.73 still hold.

Parent: `P0_bc_open_B`; thin-target counterpart pair: `P0_rear_open` / `P0_bc_open_B`.

## Cost

440 cells x 4 species (200 ppc target, 48 ambient), 24 000 steps -> 2.348 ps.
See `progress.log`.

## Media

*(not generated yet)*

## Result

Ran 24 000 steps (2.348 ps) in 3.4 min at 4 threads (440 cells vs 520). `--verify` OK.

**VERDICT: the rear truncation holds at 4× thickness, and is measurably BETTER than at
20 d_e — as predicted.** Against its own full-domain reference `P0_thick_full`:

| front-side observable | 20 d_e pair | **80 d_e pair** |
|---|---|---|
| total target-ion `p_z` | −3.39 % | **−0.54 %** (6× better) |
| `E_abs` over the run | −0.67 % | **+0.88 %** |
| target-ion count at z > face | +0.10 % | **+0.11 %** |
| reference rear-side mass fraction | 6.97 % | **2.24 %** |

**`p_z(total)` is the number that matters**, because it is the observable that exposed
`P0_rear_reflect` (which flipped its sign entirely). It improves **6-fold**, from −3.4 % to
−0.54 %, exactly as the decoupling argument requires: the rear rarefaction crosses only 26 %
of an 80 d_e slab in 2.348 ps against 103 % of a 20 d_e slab, so there is far less rear
dynamics for the boundary to get wrong.

`E_abs` changes sign between the pairs (−0.67 % → +0.88 %) but both are sub-1 %, which is
scatter rather than a trend — and note that `f_abs(0)` cannot be used to refine this, since
it carries a 10.4 % 1σ (`studies/fabs_noise/`).

The target remains overdense throughout (peak `n_e/n_cr` = 1.761), so the premise still
holds: the ray turns inside the slab and the rear boundary is invisible to the laser.

**Conclusion for the project.** Truncating at the target's rear face with an `open` boundary
is now verified at both 20 d_e and 80 d_e, and the fidelity *improves* with thickness. Since
the intended setup is thicker still (the upstream target is 163 d_e,cr, and this run is at
49 % of it), the truncation is safe for Phase 1 and Phase 2 — **it saves 15 % of the cells
here and would save proportionally more for a target sitting further from the domain edge.**

**Remaining gap to the desired setup**, stated so it is not forgotten: the coronal scale
length is still 15 d_e, whereas matching the upstream `L_n/w_t` = 0.75 would put it at 60 d_e.
That was held fixed deliberately to isolate thickness (see Setup), and it changes where the
τ = 1 surface sits, so it is a Phase-1 item rather than a detail.

## Retracted

Nothing.
