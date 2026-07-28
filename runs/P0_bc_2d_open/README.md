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

- *(not generated yet)*

```bash
python scripts/run_checks.py   runs/P0_bc_2d_open
python scripts/laser_report.py runs/P0_bc_2d_open
/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/P0_bc_2d_open
/opt/anaconda3/envs/physics/bin/python scripts/phase_space.py runs/P0_bc_2d_open
/opt/anaconda3/envs/physics/bin/python scripts/make_movies.py runs/P0_bc_2d_open
```
## Result

*(not yet run)*

## Retracted

Nothing.
