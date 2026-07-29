# LaserProdShock — testing the WarpX ray-tracing laser-deposition module as a shock driver

WarpX 1D3V/2D3V PIC tests of the **`LaserDeposition` ray-tracing operator**
(`warpx-cda/Source/Particles/LaserDeposition/`) used to **drive shocks**: an actual
ray-traced laser ablating a target, in place of the prescribed `ParticleHeater` +
`TargetInjector` piston surrogate that `../KinShock2020/` used to replicate Schaeffer et
al. 2020. Campaign: boundaries/geometry → ablation into vacuum (1D, 2D) → piston into
ambient plasma (unmagnetized, magnetized) → sweeps of laser power and geometry.

## Read these for context (don't duplicate them here)
- `TEST_PLAN.md` — **the plan**: phases, runs, gates, scaling hypotheses. Start here.
- `OVERVIEW.md` — the model (eikonal rays, inverse bremsstrahlung, the deposition kernel)
  and the shock physics being driven. The physics reference.
- `RESULTS.md` — **the running lab notebook.** Dated entry per run/finding. Read it first
  to learn current state.
- `runs/README.md`, `scripts/README.md`, `studies/README.md` — conventions and tool docs.
- Upstream, and **required reading before adding a test**:
  `warpx-cda/laser_deposition/LASER_DEPOSITION_PLAN.md` (development history, what is
  already validated) and `warpx-cda/laser_deposition/ACCURACY.md` (accuracy
  characterisation, the three known findings).

## The one rule: `config.yaml` is the single source of truth
`runs/<ID>/config.yaml` holds the intuitive primaries (densities in `n_cr`, θ = kT/mₑc²,
lengths in `d_e,ref`, speeds/c, intensity in W/m²). `scripts/make_inputs.py` renders the
WarpX deck from it. **Never hand-edit a deck** (`inputs_*`) — edit `config.yaml` and
regenerate; `--verify` checks `warpx_used_inputs` against the config after a run.

## The second rule: every run has a `README.md`
`runs/<ID>/README.md` describes what the run is, the question it answers, what was expected,
and — after it finishes — what happened, including **what is retracted**. `launch.sh`
**refuses to start a run that has no README.md.** This is not bureaucracy: a laser-driven
"marginally supercritical shock" was reported upstream and later retracted, and an
undocumented run is how that happens. See `runs/README.md` for the template.

## The third rule: phase space decides what is a shock
Density and B streaks of a *decaying magnetosonic pulse* look shock-like. Only phase space
distinguishes it from a driven shock. **Run `scripts/phase_space.py` before the word
"shock" appears in any run README, `RESULTS.md` entry, or figure caption.** Check: is there
ion reflection, and is the piston *faster* than the compression it launched?

## Layout
- `src/laserprod/` — the package: `units` (λ₀ → scales), `config`, `deck` (config→deck),
  `io`, `metrics`, `plotting`.
- `scripts/` — analysis/driver CLIs (see `scripts/README.md`). All take a `run_dir`.
- `studies/` — heavier experiments that *launch* WarpX (the Phase-3 sweeps).
- `tests/` — fast pytest checks.
- `runs/<ID>/` — `config.yaml` + `README.md` + deck + `warpx_used_inputs` (tracked);
  `diags/`, `*.log` gitignored.
- `media/<ID>/` — figures/movies (gitignored, regenerable).

## Typical workflow
```bash
python scripts/make_inputs.py runs/<ID>                 # config.yaml -> deck
scripts/launch.sh -b -L runs/<ID>                       # launch WarpX (+ progress logger)
python scripts/make_inputs.py runs/<ID> --verify        # deck == config?
python scripts/run_checks.py   runs/<ID>                # derived scales + gates G1-G7
python scripts/laser_report.py runs/<ID>                # f_abs(t), E_abs, t_s, Tlocalfrac
python scripts/plot_fields.py  runs/<ID>                # streaks + lineouts (needs yt: physics env)
python scripts/phase_space.py  runs/<ID>                # THE ARBITER -- before any shock claim
python scripts/make_movies.py  runs/<ID>                # movies (needs yt + ffmpeg)
python scripts/tune_shock.py   runs/<ID>                # fit v_sh + front BY EYE -> shock_fit.yaml
python scripts/make_figures.py runs/<ID>                # Schaeffer criteria (reads shock_fit.yaml)
```
Built: `launch.sh`, `run_progress_logger.py`, `make_inputs.py`, `run_checks.py`,
`laser_report.py`, `compare_runs.py`, `plot_fields.py`, `phase_space.py`, `make_movies.py`,
and `src/laserprod/{units,config,deck,io,plotting}`. Still to build: `tune_shock.py`,
`make_figures.py`, `plot_ablation.py`, `sweep.py` and `laserprod.metrics` (Phase 1-3).

**The plotfile tools need the `physics` env** (yt is not in base anaconda):
`/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/<ID>`. The
config/log-based tools (`make_inputs`, `run_checks`, `laser_report`, `compare_runs`) do
not, and work while a run is still going.

## Hard-won conventions & gotchas

- **The laser pins the absolute density scale.** IB absorption is measured against
  `n_cr = ε₀mₑω²/e²`, so λ₀ fixes densities in m⁻³ — a scale-free heater run cannot be
  re-labelled as a laser run. `KinShock2020`'s `n0 = 10¹⁸ m⁻³` target would be
  `2.5×10⁻⁸ n_cr` and perfectly transparent. **Quote every density in `n_cr`.** Note
  `d_e,cr = c/ω₀ = λ₀/2π` exactly, and that Schaeffer's Table I densities are 0.6 `n_cr`
  (ablation) and 0.0048 `n_cr` (upstream) at 1.053 µm.
- **`ω_pe·dt < 2` is the binding stability limit, and the grid CFL cannot see it.** The grid
  CFL is set by `dz/c` and knows nothing about how dense the plasma is. `cfl = 0.75` gave
  `ω_pe dt = 1.91` in a 1.5 `n_cr` target, which then **compressed under its own ablation**
  to 2.43 — total particle energy grew 21× while the laser supplied 1/1400 of it, and every
  number past `t ≈ 0.1 ω_ci0⁻¹` was a measurement of that instability. **Check `ω_pe dt` at
  the peak compressed density the run will reach, not at t = 0** (gate G1). `cfl ≈ 0.35` in
  1D / `0.5` in 2D is the tested setting.
- **`dz/λ_D`, not `dz/d_e`, is the free parameter.** Coarsening `dz` from 0.5 to 1.0 `d_e`
  (`dz/λ_D` 7 → 14) blew a run up: ambient heated to `u ~ 0.15 c`, `B_y/B₀` reached 82.
  Economise via ppc, domain and duration instead. Note the **cold near-critical target is
  Debye-under-resolved by ~250×**, unavoidably, at one uniform grid — hence the mandatory
  **laser-off control** (gate G3) to separate grid heating from laser heating.
- **Boundaries: periodic fields force periodic particles.** WarpX ties them
  (`Source/Particles/ParticleBoundaries.cpp`), and a free expansion has a runaway ion front
  (measured at 0.20 c) that then wraps and pollutes the upstream — **no vacuum gap is large
  enough** (two deck versions died this way). `open` = `pec` fields + `absorbing` particles
  is the combination that coexists with a uniform applied `B₀`; `absorbing`
  (Silver–Mueller) is **incompatible** with the div-B cleaner that runs when a background B
  is set. Also: **there is no vacuum gap behind the target** in an ambient run — the ambient
  fills both sides. This is Phase 0's subject; the finding lands here when it exists.
- **Absorption is self-limiting, and that is real physics.** `K ∝ Z_eff lnΛ n_e² T_e^{−3/2}`,
  so a cold target absorbs ~90 % and shuts off within ~0.05 gyroperiods as its corona heats
  and rarefies. Coupled energy is set by the target electrons' heat capacity at shutoff and
  is nearly **independent of intensity** — only captured because
  `temperature_mode = local` (the default) measures `T_e` per cell.
- **`Z_eff·lnΛ` is a very strong knob — change it in small steps.** 5/5 → 13/7 coupled
  **16×** more energy (92 keV per slab ion), giving a 0.06 c piston that crossed the domain
  in a fraction of a gyroperiod. `lnΛ` here is an honest mid-Z stand-in, and is a fixed
  input, so the model is not fully self-consistent (logarithmically, not as a power law).
- **Thickening the target does not raise the Mach number.** Coupled energy and mass both
  scale with thickness, so `v = √(2E/m)` is unchanged. Thickness buys piston *momentum*
  (drive distance).
- **A finite pulse is expressed through `intervals`.** `laser_deposition.intervals` is an
  `IntervalsParser`, so `start:stop:period` gates the drive on and off — there is no
  pulse-shape parameter. Verified in the source, 2026-07-28.
- **Rays launch EXACTLY ON the injection face** (`c0[axis] = inject_hi ? phi : plo`), not one
  cell inside it. So the boundary cell's plasma absorbs from the first RK4 step, and once the
  ablation plume reaches the launch plane **the beam is absorbed in the plume rather than at
  the target**. That is physically right, but it makes the drive a boundary quantity — keep
  the target far enough from the injection face that the transition is observable rather than
  present from t = 0. `make_inputs.py` warns when a corona exceeds 1e-3 n_cr at the face.
- **Movie frames clean themselves up.** `make_movies.py` writes PNGs to
  `media/<ID>/_frames_<name>/` and deletes the directory once ffmpeg succeeds; leftovers
  from an interrupted encode are swept at startup (so stale frames cannot be globbed into a
  new, shorter movie). `--keep-frames` retains them, and a failed encode keeps them
  automatically. Never leave frame directories behind by hand -- they are several times the
  size of the movie they produced.
- **Quote `E_abs`, never `f_abs(0)`, when comparing runs.** `f_abs(0)` carries a **10.4 %
  1σ and a 30.6 % full spread** across runs differing only in RNG seed
  (`studies/fabs_noise/`): `K ∝ 1/√(1−n_e/n_cr)` diverges at the critical surface and the
  operator integrates that layer over a locally interpolated, noisy density and gradient, so
  essentially the whole run-to-run difference sits in the single cell containing the critical
  surface. `E_abs` integrates hundreds of applications and agreed to 0.6 % between geometries
  whose `f_abs(0)` differed by 10 %. This also makes gate G4 a **noise-amplification** issue,
  not only a discretisation one.
- **Truncate the domain at the target's rear face, with an `open` boundary.** Verified at
  both 20 d_e and 80 d_e thickness (front-side ion count within 0.11 %, `E_abs` within 0.9 %,
  total target `p_z` within 0.54 % at 80 d_e), and the fidelity *improves* with thickness
  because the rear rarefaction crosses less of a thicker slab. Saves 15-20 % of the cells.
  A `reflecting` rear is **different physics** — it flips the sign of the target's net
  momentum (a tamped target), and front-side density alone will not reveal that.
- **`diag1` has only the total `rho`; per-species densities are on `diag_fields`.** And yt
  refuses a `covering_grid` flush against a non-periodic domain edge on some domain sizes —
  call `ds.force_periodicity()` first (the analysis scripts do).
- **Analyse the step-0 deposition profile.** Later `profile_intervals` dumps drift as the
  kicks move electrons.
- **`ray_cfl = 0.25` (default) is not asymptotic for turning-point problems** —
  convergence in the arc-length step is non-monotonic and the default sits near a 2.5 %
  excursion. Uniform slabs are exact at any `ray_cfl`. Check it whenever the target has an
  interior critical surface.
- **Known operator bug: exit-boundary overshoot.** The domain-exit test happens *after* the
  step's deposit, so the ray always takes one full RK4 arc-length step past the far boundary
  and deposits it into the clamped final cell — which reads **+24.9 %** high at default
  `ray_cfl`. The energy is *created*, not misplaced, and the affected cell is the last one at
  the **far** (non-injection) face. ≤ 0.04 % of total absorption
  upstream, but a vacuum-ablation target sits near that boundary. Quantify before trusting
  the last cell. Fixing it upstream is in scope — finding a bug is a valid outcome of a test
  campaign.
- **`local` temperature mode needs ppc.** `T^{−3/2}` is convex, so per-cell noise biases
  absorption **high**: ~3 % at 25 ppc, < 0.1 % at 800. High ppc in the target, not the
  ambient. Watch `Tlocalfrac`.
- **Launch with `scripts/launch.sh runs/<ID>`, never by hand.** The generated deck sets no
  `diag*.file_prefix`, so WarpX writes plotfiles to `diags/` *relative to the launch CWD* —
  two runs launched from the repo root share `./diags/` and clobber each other (`.old.NNNN`
  rename files are the tell; cost a rerun in `KinShock2020`). `launch.sh` cd's into the run
  dir, **picks `warpx.1d`/`warpx.2d` from `geometry.dims`**, applies the benchmarked OMP
  settings, requires a `README.md`, and refuses to start when `diags/` already holds output
  (`--force` to override). `-b` detaches, `-L` also starts the progress logger, `-n`
  dry-runs, and anything after `--` becomes ParmParse overrides (smoke tests only — they
  will trip `--verify`).
- **Shock kinematics come from `runs/<ID>/shock_fit.yaml`, fit BY EYE** — the convention
  `KinShock2020` arrived at after automatic `v_sh` drifted between scripts. One speed and
  front per run, shared by every diagnostic.
- **No mesh refinement.** The operator asserts `finestLevel() == 0`. One uniform grid must
  resolve both the near-critical target and the tenuous ambient; that scale separation is a
  central difficulty of the project, not something to engineer away.
- **Performance.** `OMP_NUM_THREADS=8 OMP_PROC_BIND=spread OMP_PLACES=cores` — near-linear
  to 8 cores (~1.8× vs 4), memory-bandwidth-bound beyond. `max_grid_size`, tiling and
  `sort_intervals` were benchmarked as neutral-to-negative in `KinShock2020` — don't bother.
- **GPU: `launch.sh --gpu [N]`, and the CUDA build is ONE TREE PER DIMENSIONALITY.**
  `WarpX_DIMS` is compile-time, so `build_cuda/` is **2D only** and 1D needs its own
  `build_cuda1d/`. Two RTX 4070s (12 GB, arch 8.9) — `-g 0` and `-g 1` carry two runs at
  once. `--gpu` forces `OMP_NUM_THREADS=1` (the push is on the device; host threads only
  contend) and pins with `CUDA_VISIBLE_DEVICES`.
  **The system `nvcc` is 12.0 and AMReX requires ≥ 12.2** — configure with the 12.9 toolkit
  at `/home/hhelal/opt/cuda-12.9`, which is what `build_cuda` used. CUDA and OMP builds are
  both double precision but **not bit-identical** (device reductions run in a different
  order), so a GPU-vs-CPU cross-check is a physics comparison, not a diff.
- **In a VACUUM run extra domain is nearly free — do not truncate to save cells.**
  `density_min = 1e-4·n_t` means WarpX creates no macroparticles below that density, so in
  `P1_vac_1d` only **525 of 2000 cells** carry particles and the other 1475 are empty field
  cells (a rounding error next to the particle push in 1D). Rear-face truncation pays off
  when an *ambient* fills the cushion at 48 ppc; with no ambient, spend the cells on genuine
  free surfaces at both faces instead. It is also why a 10 ps vacuum run is affordable.
- **A `_off` control must differ ONLY in `laser.intensity`.** Grid heating accumulates with
  step count and depends on the grid, the ppc and the species, so any other difference makes
  the G3 subtraction meaningless. `tests/test_structures.py` renders both decks and diffs
  them, rather than trusting that two hand-edited configs stayed in step.
- **Env.** conda env at `/opt/anaconda3/envs/physics`; WarpX binaries
  `/home/hhelal/warpx-cda/build/bin/warpx.{1d,2d,3d}` (OMP/CPU, double precision) and
  `build_cuda1d/bin/warpx.1d` + `build_cuda/bin/warpx.2d` (CUDA, double precision).

## Working preferences
- Work in the **regular repo folders** (not git worktrees). Commit to `main`.
- Keep `RESULTS.md` updated with a dated entry per substantive run/finding — that is how
  context survives between sessions. Anything worth keeping goes in the repo (scratch under
  a job's tmp does not persist).
- A negative result, stated quantitatively, is a result. If the laser-driven-shock regime
  turns out not to exist at affordable cost, the deliverable is the impossibility argument
  with numbers — that is the physics justification for why PSC and Fox 2018 prescribe a
  heater instead. Write it up as a finding, not a failure.
