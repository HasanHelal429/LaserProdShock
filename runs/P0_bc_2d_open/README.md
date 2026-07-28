# P0_bc_2d_open — the transverse boundary as a finite system

**Phase.** 0, `TEST_PLAN.md` §5.2 — the declared follow-up to `P0_bc_2d`.
**Question.** With transverse **`open`** boundaries instead of periodic, plasma can leave
sideways: lateral rarefaction becomes real and a finite beam spot means something. How
fast does the plasma drain sideways, and how far does the transverse wall reach into the
domain?
**Expected.** On-axis `n_e(z)`, `f_abs(t)` and `E_abs(t)` should match `P0_bc_2d` (the
exactly-planar baseline) while the transverse wall is far from the axis; the difference
between the two runs *is* the edge effect. A sideways thermal drain is expected — the
ambient runs already lose 15.7 % of their ambient through the *axial* open faces in
2.35 ps, and the transverse extent here (±20 d_e) is 5× smaller than the axial half-width,
so the sideways drain should be correspondingly faster.
**Falsified by.** An on-axis discrepancy that appears from t = 0 (the boundary changed the
drive, not just the edges), or a transverse wall artifact reaching the axis — either would
mean ±20 d_e is too narrow to host finite-spot physics at all.

**Why the periodic case came first.** `P0_bc_2d` had to establish that the planar 2D run
reproduces 1D *before* this run introduces edge effects; otherwise a 2D↔1D discrepancy
would have two candidate causes instead of one.

## Geometry

```
2D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      .............########~~~~~~~~~~~~~................................
      ^                                                                ^
      open                                                          open
      z = -100                                                  z = +100

  #  target flat top : 1.5 n_cr, 20 d_e thick, centred at -50 d_e
  ~  coronal ramp   : Gaussian, L_n = 15 d_e on the LASER-FACING side (face at z = -40)
  .  ambient        : 0.06 n_cr, theta_e = 0.005  (fills BOTH sides -- no vacuum gap)
  x  transverse     : -20 .. 20 d_e, boundaries open/open
  B  field          : B0 = 74.7 T along y (perpendicular to z), 1/w_ci0 = 7.61 ps
  grid              : 80 x 400 cells, dz = 0.5 d_e, dt = 0.09882 fs, 8000 steps = 0.7906 ps
```

## Setup

Byte-identical to `P0_bc_2d` in every physical primary — same target, laser, field, domain,
duration, ppc, square cells, B₀ out-of-plane on y. **The only change is
`geometry.boundary.transverse: periodic → open`**, so any difference is attributable to
the transverse boundary alone.

Note this makes *all four* faces `pec`/`absorbing`: the pec wall artifact measured in the
1D runs (|B_y/B₀ − 1| growing to 2.4 and penetrating 6–9 d_e by 2.35 ps) now applies to the
transverse faces too, and the transverse half-width is only 20 d_e. That is the central
risk this run exists to quantify.

Parent: `P0_bc_2d` (declared as `controls.planar_baseline`).

## Cost

80 × 400 = 32 000 cells × 4 species × 16 ppc (4×4 per dim), 8000 steps → 0.791 ps.
Comparable to `P0_bc_2d` (~22 min at 4 threads). See `progress.log`.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 ω_pe·dt at 2× compression | 0.306 | PASS |
| G2 dz/λ_D | target 61, ambient 1.73 | info |
| G3 laser-off control | none declared | WARN |
| G4 ray_cfl | 0.25, interior critical surface | WARN |
| G5 ppc / Tlocalfrac | 16 target ppc — budget relaxed as in `P0_bc_2d` | PASS (relaxed) |
| G6 energy closure | — must be read WITH the loss fraction (now large on four faces) | post-run |

## Media

All under `media/P0_bc_2d_open/` — gitignored and regenerable:

- `checks.png`
- `fields_lineouts.png`
- `fields_map2d.png`
- `fields_streak.png`
- `gates.png`
- `laser_history.png`
- `laser_profile.png`
- `phase_space.png`
- `movie_fields.mp4`
- `movie_map2d.mp4`
- `movie_phase.mp4`

```bash
python scripts/run_checks.py   runs/P0_bc_2d_open
python scripts/laser_report.py runs/P0_bc_2d_open
/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/P0_bc_2d_open
/opt/anaconda3/envs/physics/bin/python scripts/phase_space.py runs/P0_bc_2d_open
/opt/anaconda3/envs/physics/bin/python scripts/make_movies.py runs/P0_bc_2d_open
```
## Result

Ran 8000 steps (0.791 ps) in 20 min at 4 threads. `--verify` OK.

**The comparison is controlled at t = 0 — bit-identical in the interior.** The transverse
`n_e` difference against `P0_bc_2d` at t = 0 has an interior median of **0.000 %** and is
confined to **exactly two columns per side**. Those two columns sit at **0.365×** and
**0.861×** the interior density, which is the `particle_shape = 2` deposition losing its
periodic wrap: a quadratic shape spans three cells, so the outermost two are under-counted.

**That edge artifact is not cosmetic for a near-critical target.** At 0.365× the interior
value the target peak in the outermost column is 1.5 × 0.365 = **0.55 n_cr — underdense**,
so the ray does *not* turn there: it transits instead of reflecting, and the edge columns do
different ray physics from the rest of the beam. `f_abs(0)` is 0.2594 against 0.2466 for the
planar run, a **5.2 %** offset from four columns of eighty. My falsification criterion above
("`f_abs` diverging from t = 0 means the boundary changed the drive") is therefore
*technically triggered but wrongly framed* — the criterion did not anticipate that a
transverse boundary changes the density *deposition* in edge columns and hence their
absorption, even at t = 0. The interior being bit-identical is the check that matters.

**The axis stays usable.** The transverse `n_e` deficit (>5 % from the centre value) reaches
**1.0 d_e (2 cells) at t = 0, 2.0 d_e at 0.40 ps and 3.5 d_e at 0.79 ps** — growing, but
still only 3.5 of the 20 d_e half-width, leaving **±16.5 d_e clean**. The centre density
falls just 3 % (0.3035 → 0.2947 n_cr). The transverse `pec` walls do build a `B_y`
excursion reaching **1.9**, comparable to the axial walls measured in 1D.

**But the energy drain is severe, and this is the headline.** Against the planar run:

| | `P0_bc_2d` (periodic ⊥) | `P0_bc_2d_open` (open ⊥) |
|---|---|---|
| particles lost | 4.61 % | **30.83 %** |
| ambient electrons / ions | 6.51 % / 6.45 % | **47.74 % / 30.00 %** |
| target electrons / ions | 0.00 % / 0.00 % | 14.11 % / 7.82 % |
| total particle KE | −4.3 % | **−42.9 %** |

In 0.791 ps — **0.10 gyroperiods** — nearly half the ambient electrons and 43 % of the total
kinetic energy have left. The scale that explains it: the ambient electron thermal speed at
θ_e = 5×10⁻³ is 0.0707 c, so in 0.79 ps an electron travels ~100 d_e, against a transverse
extent of only 40 d_e. The hot electron population is simply not confined by a box this
small, and it carries the thermal energy out with it. Even the *target* now loses mass
sideways (14 % of its electrons), which the periodic run does not do at all.

**Verdict.** Transverse `open` is *usable* for finite-spot physics — the axis stays clean to
±16.5 d_e — **provided the beam profile is negligible at the transverse walls** (which
finite-spot work wants anyway, and which also makes the edge-column ray artifact
irrelevant). But at this box size it is **not usable for anything needing a gyroperiod**:
the ambient's thermal energy is gone long before t*₁. See RESULTS 2026-07-28 — this
sharpens the Phase-2 drain blocker from "must be resolved" to a quantitative requirement on
the transverse box size.

## Retracted

Nothing.
