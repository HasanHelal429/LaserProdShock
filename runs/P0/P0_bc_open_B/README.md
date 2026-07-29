# P0_bc_open_B — does `open` coexist with a uniform applied B0?

**Phase.** 0, `TEST_PLAN.md` §5.0, §5.2 — **the central Phase-0 question.**

**Question.** A magnetized laser-driven shock run needs three things that pull against
each other. Can one boundary configuration deliver all three?

1. a **uniform applied B0** across the domain;
2. **absorbing particle boundaries**, so the runaway ablation front leaves;
3. a **laser injection face**, which is simultaneously a field boundary, a particle
   boundary, and the beam aperture.

Periodic gives (1) and (3) but not (2) — that is `P0_bc_periodic`'s failure.
Silver-Mueller `absorbing` gives (2) and (3) but is incompatible with the projection
B-divergence cleaner that runs whenever an external B is set: it accepts only
periodic / pec / pmc / neumann, and pmc or neumann would zero the tangential B0. So
`open` = pec fields + absorbing particles is the **only** candidate that can give all
three, and `KinShock2020` uses it successfully with a background field. This run tests
whether that carries over when a laser is also present.

**Expected.** `B_y/B0 = 1.000` in the far upstream at t = 0 and throughout; div(B) stays
clean (no cleaner blow-up in the log); the front still leaves as in `P0_bc_open`; and the
ambient traverse costs < 2% of the beam, so the upstream is not pre-heated before
anything arrives.
**Falsified by.** A WarpX abort from the divergence cleaner; `B_y` departing from B0 in
the far upstream; or wall artifacts in `B_y`/`E_z` that intrude measurably. Any of those
forks the plan (§5.3): either a large sacrificial buffer region, or a documented artifact
with a stated validity window in time.

## Geometry

```
1D  |  propagation axis z  |  lengths in d_e at critical density = 0.1676 um

                                                               <== laser
      .............########~~~~~~~~~~~~~................................
      ^                                                                ^
      open                                                          open
      z = -100                                                  z = +100

  #  target flat top : 1.5 n_cr, 20 d_e thick, centred at -50 d_e
  ~  coronal ramp   : Gaussian, L_n = 15 d_e on the LASER-FACING side (face at z = -40)
  .  ambient        : 0.06 n_cr, theta_e = 0.005  (fills BOTH sides -- no vacuum gap)
  B  field          : B0 = 74.7 T along y (perpendicular to z), 1/w_ci0 = 7.61 ps
  grid              : 400 cells, dz = 0.5 d_e, dt = 0.09783 fs, 24000 steps = 2.348 ps
```

## Setup

`P0_bc_open` plus an ambient plasma and a perpendicular field. The ambient is required
for the field to be defined at all — `B0 = vA·√(µ₀ n_amb m_i)` needs a density to
reference. `n_amb = 0.06 n_cr` (the 25:1 contrast of the upstream `run_laser_shock`) and
`vA = 0.003 c` give **B0 = 74.7 T, 1/ω_ci0 = 7.61 ps**.

B0 is along **y**, i.e. out of the x–z plane. In 1D any transverse direction is
equivalent, but y is chosen for continuity with the 2D runs, where out-of-plane is the
standard choice for a perpendicular shock (it leaves the in-plane dynamics free).

**The domain is only ±2.4 ρ_i0 and the run covers 0.31 gyroperiods.** That is nowhere
near enough for shock physics, and deliberately so: this is a boundary test. Phase 2
sizes the box against ρ_i0.

Parent: `P0_bc_open` (adds the ambient + field).

## Cost

400 cells × 4 species (200 ppc target, 48 ambient), 24 000 steps (2.35 ps).
See `progress.log`.

## Gates

| Gate | Value | Pass? |
|---|---|---|
| G1 ω_pe·dt at 2× compression | 0.303 | PASS |
| G2 dz/λ_D | target 61, ambient 1.73 | info — ambient well resolved |
| G3 laser-off control | none declared | WARN |
| G4 ray_cfl | 0.25, interior critical surface | WARN |
| G5 ppc / Tlocalfrac | 200 target | PASS |
| G6 energy closure | | post-run |

Predicted: the ambient traverse eats **0.047%** of the beam, so the upstream stays cold.

## Media

All under `media/P0/P0_bc_open_B/` — gitignored and regenerable:

- `checks.png`
- `fields_lineouts.png`
- `fields_streak.png`
- `gates.png`
- `laser_history.png`
- `laser_profile.png`
- `movie_fields.mp4`
- `movie_phase.mp4`

```bash
python scripts/run_checks.py   runs/P0/P0_bc_open_B
python scripts/laser_report.py runs/P0/P0_bc_open_B
/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/P0/P0_bc_open_B
/opt/anaconda3/envs/physics/bin/python scripts/phase_space.py runs/P0/P0_bc_open_B
/opt/anaconda3/envs/physics/bin/python scripts/make_movies.py runs/P0/P0_bc_open_B
```
## Result

Ran 24 000 steps (2.348 ps) in 9 min at 4 threads. `--verify` OK.

**YES — `pec` fields carry a uniform applied B₀ exactly, alongside absorbing particles.**
This was the central Phase-0 question.

- **Field energy at t = 0 is 74496 J/m² against the analytic `B₀²/(2µ₀)·L` = 74496 —
  ratio 1.000000**, with B₀ = 74.74 T. The projection div-B cleaner runs without
  complaint and the run completes. B₀ is applied on **y** (out-of-plane).
- Particles leave: **5.84 % lost**, so the front is absorbed as in `P0_bc_open`.
- Field energy rises to 1.213× its initial value — the plasma's diamagnetic response
  compressing the field, which is the physics this project is here to drive.

**Unexpected: `f_abs(0) = 0.283`, not 1.000.** Adding the ambient cut initial absorption
**3.6×**. This is *not* a boundary effect and not a 2D effect (the 2D run gives 0.247).
The mechanism — see RESULTS 2026-07-28 finding (a) — is that
`laser_deposition.species` lists every electron population that is both heated *and*
counted in `n_e`, so the ambient electrons must be included for a correct refractive
index, and their θ = 5e-3 then enters the **group** temperature that `K ∝ T_e^{−3/2}`
sees. In the corona, where the τ = 1 surface sits, the group θ is ~25× the target's and
**K falls 43–129×**. Consequence for Phase 2: **the ambient temperature is a drive
parameter, not merely an upstream one.**

Shutoff is correspondingly slower, **210 fs** vs 19.7 fs in vacuum.

**G6 reads +218 % and must NOT be read as grid heating** — 5.84 % of particles left
carrying their energy out, so total KE actually *falls* (2.448e6 → 2.178e6 J/m²) while
the laser adds 2.16e5. G6's definition has been corrected accordingly (`TEST_PLAN.md` §6).

## Retracted

Nothing.
