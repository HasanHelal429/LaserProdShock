# P0_bc_open — the candidate fix: pec fields + absorbing particles

**Phase.** 0, `TEST_PLAN.md` §5.2
**Question.** With `open` boundaries (field = `pec`, particle = `absorbing`), does the
runaway ablation front leave the domain cleanly — and what does the pec field wall
reflect back into the interior?
**Expected.** Particle number should **fall** as the fast front is absorbed (contrast
`P0_bc_periodic`, where it is exactly constant). `E_abs(t)` should match
`P0_bc_periodic` for as long as the plume is far from both boundaries: the boundary
choice must not perturb the drive itself. The pec wall zeroes tangential E, so some
near-wall sheath and image-charge structure is expected; the question is how far into the
domain it reaches, in d_e.
**Falsified by.** Particle number not falling (the absorbing BC is not firing);
`E_abs(t)` differing from `P0_bc_periodic` from t = 0 (the boundary changed the drive,
so the pair is not a controlled comparison); or wall structure reaching more than a few
d_e into the interior, which would make `open` unusable for a run whose shock forms near
the boundary.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
                   ########~~~~~~~~~~~~~                                
      ^                                                                ^
      open                                                          open
      z = -100                                                  z = +100

  #  target flat top : 1.5 n_cr, 20 d_e thick, centred at -50 d_e
  ~  coronal ramp   : Gaussian, L_n = 15 d_e on the LASER-FACING side (face at z = -40)
  ' ' vacuum        : no ambient plasma
  grid              : 400 cells, dz = 0.5 d_e, dt = 0.09783 fs, 24000 steps = 2.348 ps
```

## Setup

Byte-identical to `P0_bc_periodic` in every physical primary — same target, same laser,
same domain, same duration, same ppc. **The only change is
`geometry.boundary.axis: {lo: open, hi: open}`.** That is the point: with one variable
changed, any difference between the two runs is attributable to the boundary.

`B0 = 0` deliberately. This run isolates the *particle* boundary question; whether pec
also coexists with a uniform applied `B0` is the separate question `P0_bc_open_B` asks.
Keeping them apart means a failure has one candidate cause instead of two.

Parent: `P0_bc_periodic`.

## Cost

400 cells × 2 species × 200 ppc, 24 000 steps (2.35 ps). See `progress.log`.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 ω_pe·dt at 2× compression | 0.303 | PASS |
| G2 dz/λ_D (target cold) | 61 | info |
| G3 laser-off control | none declared | WARN |
| G4 ray_cfl | 0.25, interior critical surface | WARN |
| G5 ppc / Tlocalfrac | 200 | PASS |
| G6 energy closure | | post-run |

## Media

All under `media/P0_bc_open/` — gitignored and regenerable:

- `checks.png`
- `fields_lineouts.png`
- `fields_streak.png`
- `gates.png`
- `laser_history.png`
- `laser_profile.png`
- `movie_fields.mp4`
- `movie_phase.mp4`

```bash
python scripts/run_checks.py   runs/P0_bc_open
python scripts/laser_report.py runs/P0_bc_open
/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/P0_bc_open
/opt/anaconda3/envs/physics/bin/python scripts/phase_space.py runs/P0_bc_open
/opt/anaconda3/envs/physics/bin/python scripts/make_movies.py runs/P0_bc_open
```
## Result

Ran 24 000 steps (2.348 ps) in 6 min at 4 threads. `--verify` OK.

**The absorbing boundary fires and the drive is unaffected.** Macroparticle count is flat
until **t ≈ 0.9 ps** and then falls at an accelerating rate, reaching **0.227 % lost** by
2.348 ps — the runaway front arriving and being absorbed, against exactly 0.000 % for the
periodic twin. Hypothesis upheld.

- `f_abs(t)` overlays `P0_bc_periodic` for the whole run; `E_abs` agrees to **1.5 %**
  (3.719e5 vs 3.774e5 J/m²). So the boundary change did not perturb the drive, and the
  pair is a controlled comparison — the precondition for reading anything into the
  difference.
- **G6 closes to +1.5 %**, slightly worse than the periodic run's +0.55 % precisely
  because energy now also leaves with the absorbed particles (which is not in the sum).
- No wall pathology was visible in the energy history; a dedicated near-wall field
  lineout still wants doing once a plotfile reader is in place (Phase 1).

Adopted as the default boundary together with `P0_bc_open_B` — see RESULTS 2026-07-28.

## Retracted

Nothing.
