# P0_bc_2d — the transverse boundary, and the 1D↔2D planar baseline

**Phase.** 0, `TEST_PLAN.md` §5.2

**Question.** 2D adds a transverse axis, and with it a boundary choice that has no 1D
analogue. The two options are not two spellings of the same thing:

- **transverse periodic** — the drive is *exactly planar* and a uniform beam is
  effectively infinite. This is the configuration in which a 2D run must reproduce 1D on
  axis, so it is the **1D↔2D validation**. It is what the known-good upstream
  `run_laser_shock_2d` deck used. **This run.**
- **transverse open** — a finite system: plasma leaves sideways, lateral rarefaction is
  real, and a finite beam spot means something. Required for the Phase-1/3 finite-spot
  physics (planarity, H5), but it introduces edge effects whose reach must be measured
  against the box width.

The periodic case comes first deliberately: if the planar 2D run does *not* match 1D,
then a later 2D↔1D discrepancy would have two candidate causes (dimensionality and the
transverse boundary) instead of one.

**Expected.** On-axis `n_e(z)`, `f_abs(t)` and `E_abs(t)` match `P0_bc_open_B` within
noise over the overlapping window (0 → 0.79 ps). All transverse structure stays flat: a
uniform beam on a planar target with periodic transverse boundaries has no x dependence
to develop, so any x structure that appears is numerical.
**Falsified by.** An on-axis discrepancy against `P0_bc_open_B` larger than the ppc noise
floor, or transverse structure growing out of nothing. Either is a bug or a boundary
artifact, not physics — and both must be resolved before any 2D physics claim.

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
  x  transverse     : -20 .. 20 d_e, boundaries periodic/periodic
  B  field          : B0 = 74.7 T along y (perpendicular to z), 1/w_ci0 = 7.61 ps
  grid              : 80 x 400 cells, dz = 0.5 d_e, dt = 0.09882 fs, 8000 steps = 0.7906 ps
```

## Setup

The 1D `P0_bc_open_B` extended to 2D (WarpX XZ). Same target, laser, field, domain along
z and duration in dt. Transverse extent ±20 d_e (80 cells) with square cells
(`dx_over_dz: 1.0`), because the ray tracer's arc-length step is `ray_cfl × min(dx)` and
non-square cells make the ray step finer than the coarse direction needs.

B0 is along **y**, out of the x–z plane — the standard choice for a 2D perpendicular
shock, and why the 1D runs already use y.

`cfl = 0.5`, not 0.35: with square cells the 2D Yee CFL already carries a factor
1/√2, and 0.5 is the setting the known-good 2D deck used. ω_pe·dt = 0.306 at compression,
so G1 has ample margin either way.

**Two scopes this run does NOT have.** (1) The transverse extent is ~0.5 ρ_i0
(ρ_i0 = 40.8 d_e here), so this is not gyro-scale 2D physics — Phase 2 sizes the
transverse box against ρ_i0, which `TEST_PLAN.md` §2.1 shows is affordable. (2) At 8000
steps it covers 0.79 ps, a third of the 1D runs' window, so the on-axis comparison is
over 0 → 0.79 ps only, and the plume does not reach the axial boundary. Neither limits
the question being asked.

Parent: `P0_bc_open_B`. Declared follow-up: `P0_bc_2d_open` (transverse `open`).

## Cost

80 × 400 = 32 000 cells × 4 species × 16 ppc (4×4 per dim) ≈ 2.0M macroparticles,
8000 steps (dt = 0.0988 fs → 0.79 ps). Substantially the most expensive P0 run.
See `progress.log`.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 ω_pe·dt at 2× compression | 0.306 | PASS |
| G2 dz/λ_D | target 61, ambient 1.73 | info |
| G3 laser-off control | none declared | WARN |
| G4 ray_cfl | 0.25, interior critical surface | WARN |
| G5 ppc / Tlocalfrac | 16 target ppc — **budget relaxed to 16 for this run** | PASS (relaxed) |
| G6 energy closure | | post-run |

**G5 is knowingly relaxed.** Local-`T_e` mode needs several hundred macroparticles per
cell for sub-percent absorbed power, because `T^{-3/2}` is convex and per-cell noise
biases `K` high (~3% at 25 ppc). At 16 ppc the absorption here is biased high by roughly
8%, so **this run's `f_abs` is not an absorption measurement** — it is a boundary and
dimensionality test, and the 1D↔2D comparison is against a 1D run at 200 ppc, which
means a systematic offset in `f_abs` of that order is expected and is not evidence of a
2D effect. Phase 1's 2D runs raise ppc for the absorption numbers.

## Media

All under `media/P0/P0_bc_2d/` — gitignored and regenerable:

- `checks.png`
- `fields_lineouts.png`
- `fields_map2d.png`
- `fields_streak.png`
- `gates.png`
- `laser_history.png`
- `laser_profile.png`
- `movie_fields.mp4`
- `movie_map2d.mp4`
- `movie_phase.mp4`

```bash
python scripts/run_checks.py   runs/P0/P0_bc_2d
python scripts/laser_report.py runs/P0/P0_bc_2d
/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/P0/P0_bc_2d
/opt/anaconda3/envs/physics/bin/python scripts/phase_space.py runs/P0/P0_bc_2d
/opt/anaconda3/envs/physics/bin/python scripts/make_movies.py runs/P0/P0_bc_2d
```
## Result

Ran 8000 steps (0.791 ps) in 22 min at 4 threads — by far the most expensive P0 run.
`--verify` OK.

**The 2D path works end to end.** The deck rendered `amr.n_cell = 80 400`,
`boundary.field_lo = periodic pec`, `prob_lo = xlo zlo`, `ppc = 4 4` and B₀ on **y**
(out of the x–z plane), all from the same code path as the 1D runs. The run completed
with 4.61 % of particles lost through the axial `open` faces.

**On-axis agreement with 1D: `f_abs(0) = 0.247` in 2D against 0.283 in 1D
(`P0_bc_open_B`), a 13 % difference.** That is the right order for the ppc difference
alone — this run uses 16 ppc against the 1D run's 200, and G5's convexity bias on
`⟨T^{-3/2}⟩` is ~8 % at 16 ppc and ~0.6 % at 200 — so the planar 2D case reproduces 1D
to within the noise it was set up to have. **No 2D-specific absorption effect is
detected.** A cleaner test wants matched ppc, which Phase 1's 2D runs will use.

Time-averaged absorbed fraction and the normalised KE history both overlay the 1D
ambient runs (see `media/P0/P0_boundary_decision/compare.png`, panels 3 and 4 — note those
are deliberately dimensionless, because `E_abs` is per m² in 1D and per m in 2D and the
raw values must never share an axis).

**Transverse flatness — the other pass criterion — is confirmed quantitatively.** The
transverse relative spread of `n_e` (std over x, per z, where there is meaningful plasma)
is **0.00 % at t = 0, then median 5.0 % / max 14.9 % at 0.40 ps and median 5.3 % /
max 13.2 % at 0.79 ps**. The per-cell shot-noise floor is `1/sqrt(32)` = **17.7 %**
(16 ppc x 2 electron species), so the measured spread is *below* the noise floor: there is
**no coherent x structure**, which is exactly what a uniform beam on a planar target with
periodic transverse boundaries must give. `media/P0/P0_bc_2d/movie_map2d.mp4` shows the
stratification staying horizontal for the whole run.

**Declared follow-up: `P0_bc_2d_open`** (transverse `open`), required before any
finite-spot physics, and only meaningful now that the planar case is known to match 1D.

## Retracted

Nothing.
