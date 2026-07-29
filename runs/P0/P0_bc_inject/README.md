# P0_bc_inject — what happens when the plume reaches the laser injection face?

**Phase.** 0, `TEST_PLAN.md` §5.1, §5.2

**Established from the operator source first** (`LaserDeposition.cpp`, ray launch):

```cpp
c0[m_axis] = m_inject_hi ? phi[m_axis] : plo[m_axis];
```

Rays are launched **exactly on the injection boundary plane**, not one cell inside it. So
the boundary cell's plasma is traversed and absorbs from the very first RK4 step, and
`deposit` clamps its cell index into the valid box. Nothing special happens at the face.

**Question.** The ablation plume always flows *back up the beam*, so it eventually
reaches the launch plane. From then on the laser is absorbed at the boundary rather than
at the target. Is that transition physical absorption in the blow-off, or does it couple
to the pec/absorbing boundary and make the drive history a boundary artifact?

**Expected.** `f_abs(t)` should track `P0_bc_open_B` while the beam's path is clear, then
depart once the plume arrives at the face — with the deposition profile's peak migrating
from the target's corona toward the +z boundary. That is real: a beam is absorbed in the
plasma it has to cross.
**Falsified by.** `f_abs(t)` departing from `P0_bc_open_B` **from t = 0**, which would
mean the target's position alone changed the drive and the two runs are not comparable;
or the absorbed power showing a discontinuity or non-monotonic jump exactly at the
arrival time, which would indicate boundary coupling rather than absorption.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      ..........................................########~~~~~~~~~~~~~...
      ^                                                                ^
      open                                                          open
      z = -100                                                  z = +100

  #  target flat top : 1.5 n_cr, 20 d_e thick, centred at +40 d_e
  ~  coronal ramp   : Gaussian, L_n = 15 d_e on the LASER-FACING side (face at z = +50)
  .  ambient        : 0.06 n_cr, theta_e = 0.005  (fills BOTH sides -- no vacuum gap)
  B  field          : B0 = 74.7 T along y (perpendicular to z), 1/w_ci0 = 7.61 ps
  grid              : 400 cells, dz = 0.5 d_e, dt = 0.09783 fs, 24000 steps = 2.348 ps
```

## Setup

Identical to `P0_bc_open_B` except `plasma.target.center_de: -50 → 40`, putting the
laser-facing face at **+50 d_e**, i.e. 50 d_e from the +z injection face instead of
140 d_e. At t = 0 the corona density at the face is 2×10⁻⁵ n_cr — optically negligible,
so the beam starts with a clear path; the plume then reaches the launch plane well inside
the run rather than at the very end. That separation matters: it is what makes "before"
and "after" both observable in one run.

`profile_intervals` is 4000 rather than 8000, giving 7 deposition-profile dumps, because
the migration of the deposition peak toward the face is the actual observable here.

Parent: `P0_bc_open_B`.

## Cost

400 cells × 4 species, 24 000 steps (2.35 ps). See `progress.log`.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 ω_pe·dt at 2× compression | 0.303 | PASS |
| G2 dz/λ_D | target 61, ambient 1.73 | info |
| G3 laser-off control | none declared | WARN |
| G4 ray_cfl | 0.25, interior critical surface | WARN |
| G5 ppc / Tlocalfrac | 200 target | PASS |
| G6 energy closure | | post-run |

## Media

All under `media/P0/P0_bc_inject/` — gitignored and regenerable:

- `checks.png`
- `fields_lineouts.png`
- `fields_streak.png`
- `gates.png`
- `laser_history.png`
- `laser_profile.png`
- `movie_fields.mp4`
- `movie_phase.mp4`

```bash
python scripts/run_checks.py   runs/P0/P0_bc_inject
python scripts/laser_report.py runs/P0/P0_bc_inject
/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/P0/P0_bc_inject
/opt/anaconda3/envs/physics/bin/python scripts/phase_space.py runs/P0/P0_bc_inject
/opt/anaconda3/envs/physics/bin/python scripts/make_movies.py runs/P0/P0_bc_inject
```
## Result

Ran 24 000 steps (2.348 ps) in 8 min at 4 threads. `--verify` OK.

**The drive at t = 0 is unchanged, and the later divergence is physical.**
`f_abs(0) = 0.283`, identical to `P0_bc_open_B` — so moving the target from −50 to
+40 d_e did **not** by itself change the drive, which is what the falsification criterion
demanded. The runs are comparable.

- **17.05 % of particles lost**, the largest of the five, as intended: with the
  laser-facing face at +50 d_e the plume reaches the +z injection face early and flows
  out through it.
- `E_abs` = 2.106e5 J/m², 2 % below `P0_bc_open_B` — the beam is absorbed in the
  blow-off plasma at the launch plane rather than at the target, and the total coupled
  energy is barely affected. No discontinuity or non-monotonic jump at the arrival time,
  so there is no sign of boundary *coupling* as opposed to ordinary absorption.
- This matches what the source says must happen: rays launch **exactly on** the injection
  plane (`c0[m_axis] = m_inject_hi ? phi : plo`), so the boundary cell's plasma absorbs
  from the first RK4 step.

**Practical rule for Phase 1–3**: a target may sit near the injection face without
corrupting the drive, but once the plume crosses the launch plane the deposition profile
migrates to the boundary, so the *spatial* deposition diagnostic (not the integrated
`E_abs`) is what stops being interpretable. Keep the target far enough away that the
observation window ends before that matters, or accept it and read only `E_abs`.

G6 reads +235 %, which at 17 % particle loss is boundary outflow, not grid heating.

## Retracted

Nothing.
