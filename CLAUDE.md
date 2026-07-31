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
`runs/<phase>/<ID>/config.yaml` holds the intuitive primaries (densities in `n_cr`, θ = kT/mₑc²,
lengths in `d_e,ref`, speeds/c, intensity in W/m²). `scripts/make_inputs.py` renders the
WarpX deck from it. **Never hand-edit a deck** (`inputs_*`) — edit `config.yaml` and
regenerate; `--verify` checks `warpx_used_inputs` against the config after a run.

## The second rule: every run has a `README.md`
`runs/<phase>/<ID>/README.md` describes what the run is, the question it answers, what was expected,
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
- `runs/<phase>/<ID>/` — `config.yaml` + `README.md` + deck + `warpx_used_inputs` (tracked);
  `diags/`, `*.log` gitignored.
- `media/<phase>/<ID>/` — figures/movies (gitignored, regenerable).

## Typical workflow
```bash
python scripts/make_inputs.py runs/<phase>/<ID>                 # config.yaml -> deck
scripts/launch.sh -b -L runs/<phase>/<ID>                       # launch WarpX (+ progress logger)
python scripts/make_inputs.py runs/<phase>/<ID> --verify        # deck == config?
python scripts/run_checks.py   runs/<phase>/<ID>                # derived scales + gates G1-G7
python scripts/laser_report.py runs/<phase>/<ID>                # f_abs(t), E_abs, t_s, Tlocalfrac
python scripts/spot_report.py  runs/<phase>/<ID>                # FINITE SPOT only: f_ax, w_eff/w0, leak, wall/in
python scripts/g3_spot.py      runs/<phase>/<ID> --control ..._off   # FINITE SPOT only: G3 on the LIT columns
python scripts/plot_fields.py  runs/<phase>/<ID>                # streaks + lineouts (needs yt: physics env)
python scripts/plot_rays.py    runs/<phase>/<ID>                # 2D ONLY: ray paths, turning point -- geometry, NOT f_abs
python scripts/phase_space.py  runs/<phase>/<ID>                # THE ARBITER -- before any shock claim
python scripts/make_movies.py  runs/<phase>/<ID>                # movies (needs yt + ffmpeg)
python scripts/tune_shock.py   runs/<phase>/<ID>                # fit v_sh + front BY EYE -> shock_fit.yaml
python scripts/make_figures.py runs/<phase>/<ID>                # Schaeffer criteria (reads shock_fit.yaml)
```
Built: `launch.sh`, `run_progress_logger.py`, `make_inputs.py`, `run_checks.py`,
`laser_report.py`, `spot_report.py`, `g3_spot.py`, `compare_runs.py`, `compare_frontside.py`,
`plot_fields.py`, `plot_rays.py`, `phase_space.py`, `make_movies.py`,
and `src/laserprod/{units,config,deck,io,plotting}`. Still to build: `tune_shock.py`,
`make_figures.py`, `plot_ablation.py`, `sweep.py` and `laserprod.metrics` (Phase 1-3).

**The plotfile tools need the `physics` env** (yt is not in base anaconda):
`/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py runs/<phase>/<ID>`. The
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
  so a cold target absorbs strongly and weakens as its corona heats and rarefies — captured
  only because `temperature_mode = local` (the default) measures `T_e` per cell.
  **But the "shuts off at a heat-capacity ceiling, coupled energy independent of intensity"
  story is FALSIFIED — see the next bullet.** It is the inherited H2 picture and it does not
  describe what the operator does.
- **`Z_eff·lnΛ` is a very strong knob — change it in small steps.** 5/5 → 13/7 coupled
  **16×** more energy (92 keV per slab ion), giving a 0.06 c piston that crossed the domain
  in a fraction of a gyroperiod.
- **`lnΛ` no longer has to be a guess: `laser.coulomb_log_mode`** (added 2026-08-02, after
  reading PSC's ray-trace module, which does it per cell and ours did not). `constant` (the
  default, and bit-identical to before) keeps `laser.coulomb_log`; `nrl` / `flash` / `ib`
  evaluate lnΛ **per cell** from the local `(n_e, T_e)` — the same values, and the same
  sparse-cell fall-back, that set `T_e` in the coefficient. **`ib` is the physical one**:
  it cuts off at `b_max = v_th/max(ω_pe, ω_laser)`, so below critical lnΛ *saturates* at its
  critical-surface value instead of growing logarithmically out into the corona, which is
  right because an encounter lasting longer than `1/ω` is adiabatic and absorbs nothing.
  `flash` is Eqs. (11)–(13) of Lezhnin 2025 (Debye `b_max`), `nrl` is the **transport**
  logarithm and exists only to cross-validate against PSC, which uses it for IB — and that
  cross-validation is now **done and exact**: PSC's compiled `get_lnlambda` and our `nrl`
  differ by **0.000e+00** over 1681 points, covering both NRL branches and the floor
  (2026-08-03; `warpx-cda/laser_deposition/psc_reference/`). So `nrl` is the mode to pick
  when the question is "what would PSC have done here", and never for physics.
  Measured on the `run_profile_ramp` deck: **lnΛ 2 → ~7.3, absorbed power ×1.6**. The
  effective value is reported as `lnLmean` on every `LASERDEP` line and per cell in the
  `profile_intervals` dump. Keep using `constant` when you need collisionality *pinned*
  (e.g. holding it fixed while something else varies) — that is a real use, not a fallback.
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
  `media/<phase>/<ID>/_frames_<name>/` and deletes the directory once ffmpeg succeeds; leftovers
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
- **Launch with `scripts/launch.sh runs/<phase>/<ID>`, never by hand.** The generated deck sets no
  `diag*.file_prefix`, so WarpX writes plotfiles to `diags/` *relative to the launch CWD* —
  two runs launched from the repo root share `./diags/` and clobber each other (`.old.NNNN`
  rename files are the tell; cost a rerun in `KinShock2020`). `launch.sh` cd's into the run
  dir, **picks `warpx.1d`/`warpx.2d` from `geometry.dims`**, applies the benchmarked OMP
  settings, requires a `README.md`, and refuses to start when `diags/` already holds output
  (`--force` to override). `-b` detaches, `-L` also starts the progress logger, `-n`
  dry-runs, and anything after `--` becomes ParmParse overrides (smoke tests only — they
  will trip `--verify`).
- **Kill runs BY PID. `pkill -f` matches the shell you type it in.** Its own command line
  contains the pattern, so `pkill -f "warpx.2d inputs_P1_vac_2d_spot_omp"` killed the invoking
  shell (exit 144) and **everything chained after it never ran** — including the second `pkill`
  that was supposed to stop the progress logger. The orphaned logger then kept appending to the
  same `progress.log` as the relaunched run's logger, and because each logger times the run from
  *its own* start, the file grew two "10.1 %" lines one second apart reporting 0h18m vs 0h26m
  elapsed and ETA 2h43m vs 3h51m. Only `warpx_rate` agreed — it is read from WarpX's output
  rather than timed by the logger. **`ps -eo pid,lstart,args | grep <thing>` then `kill <pid>`**,
  and check what is left afterwards rather than trusting the kill. The logger now refuses to
  start when another holds the run (`.logger.pid`), but that only helps the next time.
- **Shock kinematics come from `runs/<phase>/<ID>/shock_fit.yaml`, fit BY EYE** — the convention
  `KinShock2020` arrived at after automatic `v_sh` drifted between scripts. One speed and
  front per run, shared by every diagnostic.
- **No mesh refinement.** The operator asserts `finestLevel() == 0`. One uniform grid must
  resolve both the near-critical target and the tenuous ambient; that scale separation is a
  central difficulty of the project, not something to engineer away.
- **Performance.** `OMP_NUM_THREADS=8 OMP_PROC_BIND=spread OMP_PLACES=cores` — near-linear
  to 8 cores (~1.8× vs 4), memory-bandwidth-bound beyond. `max_grid_size`, tiling and
  `sort_intervals` were benchmarked as neutral-to-negative in `KinShock2020` — don't bother.
- **The GPU is worth 12.7× even in 1D — use it, and BENCHMARK rather than scale.** On the
  `P1_vac_1d` deck (2000 cells, 420 k macroparticles): **7.9 min on one RTX 4070 vs 100.6 min
  on 8 CPU threads**. Estimating that run by scaling from `P0_thick_open` (particles ×3.15 ×
  steps ×4.27) predicted ~25 min on CPU and was **wrong by 4×** — cell count dominates far
  more than a particle×step scaling allows for, so measure a 2000-step slice when the grid
  changes size. CPU and GPU agree on `P_abs(0)` to 2×10⁻⁶ but on integrated `E_abs` only to
  ~2.5 %, because the kicks use `ParallelForRNG` and the backends draw different random
  streams: the two are different *realizations*, well inside the 10.4 % seed noise on
  `f_abs(0)`. **Run a physics run and its `_off` control on the SAME backend**, or that
  difference lands inside the G3 subtraction.
- **GPU: `launch.sh --gpu [N]`, and the CUDA build is ONE TREE PER DIMENSIONALITY.**
  `WarpX_DIMS` is compile-time, so `build_cuda/` is **2D only** and 1D needs its own
  `build_cuda1d/`. Two RTX 4070s (12 GB, arch 8.9) — `-g 0` and `-g 1` carry two runs at
  once. `--gpu` forces `OMP_NUM_THREADS=1` (the push is on the device; host threads only
  contend) and pins with `CUDA_VISIBLE_DEVICES` — that is still right for the push, but the ray
  march is host code and now threads, so a **driven** run wants `laser_deposition.ray_threads`
  in the deck instead (see the ray-march bullet below).
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
- **Absorption FLOORS onto a plateau, then decays HYDRODYNAMICALLY when the target goes
  underdense. A half-peak `t_s` is meaningless here.** `f_abs` 1.000 → plateau ≈ 0.24 → 0.042
  at 100 ps (`P1_vac_1d_long`). The decay is caused by the rarefaction taking peak `n_e` below
  `n_cr` — measured at **28.8 ps**, with `f_abs` at half its plateau by **41.6 ps** — so the
  beam punches through with no turning point. **Not** H1's shutoff temperature, and **not**
  never (which is all 10 ps could show). **H2 stays falsified**: `E_abs = ∫f_abs(t)·I₀ dt`
  with `f_abs` set by the target's hydrodynamic state (`TEST_PLAN.md` §2.4–2.5). Quote the
  **plateau level, the `n_cr`-crossing time and `dE/dt`** — never a half-peak shutoff time.
- **The transverse-boundary clamp is FIXED** (`warpx-cda` c817b63, 2026-07-29) — but **the two 2D
  runs on disk predate it and are invalid.** `P1_vac_2d` / `P1_vac_2d_off` must be re-run before any
  2D claim; `build_cuda/bin/warpx.2d` is already rebuilt with the fix. What the bug was: rays
  drifting past a periodic transverse face were neither wrapped nor terminated (`deposit()` clamped
  the index in *every* dimension, the exit test checked *only* the axis), so each dumped its
  remaining power into column 0 or N−1 — the 2 edge columns' share went **3.2 % at t = 0 (= 2/64,
  correct) → 98.8 % at 26.9 ps** and absorption ran **+12 %** above matched 1D. Now index mapping
  and termination are keyed off one `wrap[]` flag: periodic transverse faces wrap, everything else
  terminates, and **the axis always terminates even if periodic** — which is what keeps the 1D
  tests (periodic in z!) bit-identical. Verified on the CI oblique deck: one column's share
  **99.53 % → 12.50 %** (= 1/8 exactly) with the step-0 total unchanged to 7 digits.
  `TEST_PLAN.md` §2.7–2.8.
- **A conserved total is not a working operator.** All five `laser_deposition` CI tests passed
  *throughout* the bug above, because each reduces the operator to one number (a `dKE/dt` slope) and
  the clamp **relocated** energy without creating or destroying it — step-0 total `P_abs` agreed to
  7 digits before and after the fix. `ACCURACY.md` predicted exactly this class. When touching the
  operator, **check a spatial field, not just an energy budget.**
- **Diagnose non-uniformity from the PATTERN, not the variance.** rms/mean = 4.17 was equally
  consistent with smooth refractive channelling and with an edge pile-up, and I first asserted the
  former — which would have wasted GPU time on a convergence study of a deterministic bug. Printing
  the per-column profile showed two hot edge columns and 62 flat ones, which is a boundary
  signature and pointed straight at the index clamp. **Always look at the spatial profile.**
- **Compare energy-integrated `E_abs` or the mean across dimensionalities — NEVER the median.**
  The 5–25 ps median `f_abs` differed 1D vs 2D by **48 %** where the energy-integrated figure
  differed by **12 %**: 2D sums 64 rays so its distribution is smooth and median ≈ mean, while
  1D's single ray is spiky and median ≪ mean. The median difference was an estimator artifact.
- **A `_off` control is worth more than its energy budget.** `P1_vac_2d_off` is what proved the 2D
  transverse structure was shot noise rather than laser-driven filamentation — a question that
  would otherwise have been unresolvable speculation. Also: at 36 ppc its excursion is **−3.09 %**
  of the driven gain against **−0.066 %** at 400 ppc (47× larger), so quote it beside any
  few-percent 2D number.
- **Target thickness is a DRIVE-DURATION knob, and it trades against piston speed.** A 5×
  thicker target keeps the peak above `n_cr` for the whole run (it even *compresses*, to 1.92
  `n_cr`) where the 80 d_e target crossed at 28.8 ps and lost its plateau — so thickness extends
  the drive past the ~38 ps formation needs. But it costs speed: `E_abs` rises only ~46 % for 5×
  the mass (a colder target absorbs *better*, `K ∝ n_e²T_e^{−3/2}`, so the plateau is +23 % —
  coupled energy is **not** thickness-independent), hence `v_p ∝ √(E_abs/w_t)` **falls** (0.63×
  measured, 0.54× predicted). **H3's "thickness leaves `v_p` unchanged" is FALSIFIED**; α ≈ 1–2
  survives. There is an optimum thickness, as consequential as the optimum `I₀` (`TEST_PLAN.md`
  §2.6).
- **Validate a rear truncation by CORE DECOUPLING, never by boundary-density invariance.** The
  truncated boundary sits on a **free surface**, which must rarefy — asking it to stay put is an
  ill-posed test (`P1_vac_1d_thick`'s rear density fell 37 % while the truncation was sound).
  The right measure is the width of slab still at its initial density between the two
  disturbance fronts: 269 of 400 d_e (67 %) undisturbed there. Also, **truncating costs the
  energy budget** — 6.13 % weight loss at 30 ps vs 1.14 % at 100 ps untruncated — so **G6 cannot
  be closed tightly on a truncated run**; take strict closure from untruncated ones.
- **The laser operator is FIXED (Phase 1.5, 2026-07-30): a driven 2D step went 0.1453 → 0.0743 s,
  and the laser is now 6 % of a step instead of 52 %.** It *was* ~65 % of the step and plain
  serial host code — the driven run's GPU oscillated **0 % → 61 % → 0 %** while its control held
  82 %. One patch (`studies/ray_march_perf/patches/o123-ray-march.patch`): **O3** reuses the
  end-of-step sample as RK4 stage 1 (1.27×), **O2** drops the field samples of steps lying wholly
  in empty field (1.92×), **O1** threads the ray loop over `n_accumulators` buckets (6.2×) —
  10.9× on the march — and **O4** forms the IB coefficient on the device instead of in a serial
  host `pow` loop, gathering 3 components instead of 6 (−18 % of the whole operator). All
  bit-identical: Tier 1 is 285/285 byte-equal at `n_accumulators=1`, `Tlocalfrac` included, and
  every `LASERDEP` line is byte-equal across 1/2/4/8/12 threads. **Do not re-derive the old cost
  model.** What is left, per application at 36 ppc on GPU: march 79 ms, density deposit 12,
  kicks 3.4, gather 2.4.
- **`laser_deposition.ray_threads` exists because `--gpu` still wants `OMP_NUM_THREADS=1`.** The
  push belongs on the device; the march is host code and now threads. Set `laser.ray_threads` in
  `config.yaml` rather than raising `OMP_NUM_THREADS`, and note that O1 is **inert unless the
  binary was compiled with `-fopenmp`**: `build_cuda` is `AMReX_OMP=OFF`, so that binary gets
  O2 + O3 + O4 only. **Use `build_cuda_omp/bin/warpx.2d`** — the same tree configured
  `-DAMReX_OMP=ON`, which puts `-Xcompiler=-fopenmp` in the CUDA flags. `launch.sh --gpu` warns
  when a driven deck sets no `ray_threads`. The best value is **machine state, not a constant**:
  8 beat 16 at load 18 and lost to it on a quiet box.
- **Two benchmarking traps, both of which produced confident wrong numbers here.**
  (1) `profile_intervals = 1000000` does **not** disable the per-cell dump — an
  `IntervalsParser` period contains step 0 — so a "diagnostics off" benchmark wrote a 74 MB
  table from *inside* `applyDeposition` and inflated the operator's cost by 0.118 s per
  application. **Only `intervals = 0` disables a diagnostic** (`m_period <= 0`). (2) TinyProfiler
  prints the **exclusive** table first; reading the first match of a region name gives
  time-minus-children, which for an instrumented `applyDeposition` is nearly zero. Read the
  table after `Incl. Min`.
- **The P1 decks are NOT reproducible run-to-run under OMP threading.** Same binary, same deck,
  `OMP_NUM_THREADS=4`, 36 ppc: `Tlocalfrac` 0.43034 vs 0.430789, and 365 k of 704 k cells differ
  in `n_e` — the thermal momenta are drawn through `ParallelForRNG` and the draws follow the
  thread scheduling. At `OMP_NUM_THREADS=1` it is exact. Production is unaffected (`--gpu` forces
  1), but **pin the thread count for any bit-level comparison**, including a run against its
  `_off` control.
- **A forward vacuum gap is now cheap for the ray trace too, but only because it is EMPTY.** The
  march costs `path/(ray_cfl·dz)` RK4 steps *per ray*, and rays = transverse cells ×
  `rays_per_cell`: in `P1_vac_2d` that is 9 168 steps × 64 rays = 5.9×10⁵ steps per application,
  **89 % of them through vacuum**. O2 now costs those steps ~1/4 of a full one (they keep their
  arithmetic, they drop their five interpolations), so a gap is ~4× cheaper than it was but not
  free — still size the forward gap to what the plume needs.
- **A skip threshold near a discrete trigger is not bounded by its own smallness.** O2 was
  specified as "treat `n_e < 3×10⁻² n_cr` as vacuum and jump" — the value chosen by sweeping the
  *discarded optical depth* to 3.5×10⁻⁴. It moved the 1D ramp CI deck by **+6.13 %**, because
  sub-threshold plasma still refracts: the discrete march lags the straight line by 1.6×10⁻³ `h`
  over 16 steps, the jump lands the ray ahead of it, and that flips the near-critical trigger
  `n_ref ≤ n_floor && drds > 0` — which pre-change **never fires** on that deck. Skipping one
  cell and skipping four gave the identical error, the signature of a discrete flip. **Ask what
  an approximation does to the branches downstream of it, not only to the quantity it bounds.**
- **ppc in 2D: 36 (6×6), not 400.** 400 is unaffordable once a transverse dimension multiplies
  both grid and particles. G5's absorption-bias bound rises 0.31 % → 3.5 %, but `Tlocalfrac`
  stayed at 0.90–0.99 (and 0.975–0.987 in the Phase-0 2D runs at only **16** ppc), so `T_e` is
  still measured rather than floored. **Match the ppc in any 1D baseline** used for a 1D↔2D
  comparison, or ppc bias confounds dimensionality.
- **Matching a 1D run to a 2D run means matching `t_end`, not `max_step`.** `dt` is `cfl·dz/c`
  in 1D but `cfl·dz/(c√2)` in 2D, so 2D needs √2 more steps for the same physical time.
- **`c_s` must come from the MEASURED electron energy, not `laser_report`'s implied `T_e,ab`.**
  That number assumes all coupled energy is electron thermal, but **66 % of it is in ions** by
  100 ps, so it overstates `c_s` by 2.3× and understates α to 0.84. Use `<KE_e>` from the `EP`
  reduced diag: `T_e = (2/3)<KE_e>` ⇒ 548 eV ⇒ `c_s` = 0.00327 c ⇒ **α = 1.5–2.4, so H3 is
  CONFIRMED** (predicted 1–3). Ion energy is 62 % of `E_abs` — the drive efficiency Phase 2 spends.
- **A non-monotonic ion front means particles LEFT, not that the piston decelerated.** The
  driven percentile front read 0.0536 c at 30 ps but 0.0245 c at 100 ps purely because the fast
  tail was absorbed at the wall. Another reason fronts are the wrong `v_p` measure.
- **In a driven vacuum run the plume edge advances at ~50 d_e/ps once `T_e` ≈ 600 eV** — far
  faster than the ~20 d_e/ps a 10 ps run extrapolates, because the target keeps heating. Sizing
  `P1_vac_1d_long`'s domain from 10 ps drift rates left the plume pinned against both walls for
  the last 45 % of the run (1.14 % weight loss, G6 −9.56 %). **A 100 ps vacuum run needs
  ≥ ±5000 d_e**, and the requirement is set by the **drive**, not the geometry — the laser-off
  control on the same domain lost only 0.0014 %.
- **GPU benchmarks assume an IDLE host.** A CUDA run is latency-bound on one host thread issuing
  kernel launches, so a loaded box starves it: at 2882 % CPU demand on 32 cores the 100 ps runs
  took 1.8× their benchmark, GPU utilisation fell 71 % → 53 % and power sat at 47–56 W of 200 W.
  Separately, cost grows *during* a vacuum run as the plume spreads (occupied cells 526 → 10 800
  at flat particle count ⇒ deposition scatters over 20× the memory footprint); the laser-off
  control slows too, which is how to tell the two apart. **`warpx.sort_intervals` is worth
  benchmarking on GPU** — the "sorting is neutral-to-negative" note below is an inherited *CPU*
  result and should not be assumed to hold on the device.
- **The coronal scale length sets the absorption REGIME, not just the amount.** `L_n/w_t`
  0.19 → 0.75 (`L_n` 15 → 60 d_e at `w_t` = 80) took τ-to-the-turning-point from 0.14 to 5.60,
  i.e. optically thin → thick, and `f_abs(0)` from 0.248 to **1.000**. At `L_n` = 60 the ray is
  extinguished ~15 d_e *before* the critical surface: **0.000 % of `P_abs` lands at or below
  it**, so the turning point plays no role and G4's `ray_cfl` sensitivity should weaken. Predict
  this before running by integrating τ to the turning point at the **group** `T_e` — it got
  +53.8 d_e for the deposition peak against a +53.6 d_e prediction.
- **Piston speed from a weight-weighted bulk, never a percentile front.** The laser-off
  control's own ion front reaches 0.0091 c against the driven run's 0.0267 c — a percentile
  front is ~1/3 undriven thermal expansion. By mass the split is clean (0.00089 vs 0.00144 c).
  Also beware averaging in target mass the rarefaction has not reached yet: at 10 ps it had
  crossed only ~70 % of an 80 d_e slab, which drags the bulk mean down and makes α a **lower
  bound** (H3 is untested, not falsified).
- **Quote the WEIGHT lost at the boundaries, not the macroparticle count** — they differ by
  65×. `P1_vac_1d` lost 0.68 % of macroparticles but only **0.0104 % of the weight**, because
  the escapers are the tenuous corona tail. That is why G6 finally closed (**−0.74 %**) where
  Phase 0 could only report +218 %/+235 %.
- **Size every box from `v_th,e`, NEVER from `c_s`. This has now cost three separate
  mistakes.** Electrons carry the energy and `v_th,e/c_s` ≈ 10 here (37.7 vs 4.0 `d_e`/ps at a
  227 eV corona). `P1_vac_2d_spot` sized its ±80 `d_e` transverse box from `c_s` — predicting the
  lateral flow would reach the wall at 14 ps, beyond its 9.96 ps — and **lost its transverse
  contrast after 1.99 ps**, against the 2.1 ps `v_th,e` predicts. The same error appeared in
  Phase 0 (confining the ambient electron excursion needs ~2 400 `d_e` per open direction) and in
  O2's vacuum estimate (a forward gap is consumed at `v_th,e`, so it lasts ~1/10 as long as a
  `c_s` estimate says). **Ask it of every dimension:** `L/2 ≳ v_th,e·t_end + (initial extent)`.
- **A periodic transverse box turns a finite spot into an infinite ARRAY of spots.** Once heat
  crosses half the pitch they merge and the run is planar with extra steps — silently, with every
  gate passing and energy conserved. Run `scripts/spot_isolation.py <run> --control <run>_off`:
  it measures the transverse profile of the NET absorbed energy (driven minus the control's drain)
  and reports `dark/lit` — **< 0.2 isolated, 0.2–0.5 marginal, > 0.5 effectively planar**. On
  `P1_vac_2d_spot` it goes 0.135 at 1 ps to **0.946 at 10 ps**, i.e. the deposited energy ends
  **flat to 7 % across a box the beam illuminates at 1.1×10⁻⁷ of peak**.
- **`w_eff` is not the heated radius, and `T_e` needs its weighting stated.** `w_eff` is the
  second moment of the ABSORBED POWER, so the shot-noise leak inflates it (2.39 `w₀` at a 16 %
  leak). And on-axis `T_e` at `t_end` is **243 eV absorption-weighted** (the tenuous corona the
  rays cross) against **81 eV density-weighted** (the bulk mass) — a factor 3, so √3 in `c_s` and
  in every timescale built on it.
- **A finite spot heats a profile ~1.5× WIDER than it is illuminated with, and that is real.**
  `w_eff/w₀` is 1.000 at `t` = 0 and 1.5–1.6 by 1 ps, at *both* 36 and 144 ppc, while the
  transverse `n_e` stays flat to 0.6 % (and 0.75 ps of `c_s` is 4 % of a waist, so density could
  not have responded). What changed is `T_e` — 248 eV on axis against 126 eV at 2 `w₀` — and
  inverse bremsstrahlung goes as `T_e^{−3/2}`, so **the spot suppresses its own coupling where it
  is brightest**. Consequences: `t_cross = w₀/c_s` *understates* the crossing time, and
  **`f_ax` is not `f_abs`** (0.39 vs 0.63) — a whole-beam absorbed fraction overstates what the
  axis receives by 60 %. Do not "fix" this broadening; it shares a profile with the shot-noise
  leak below but scales differently.
- **The transverse leak in a spot run is shot noise, and it scales as a POWER not an amplitude.**
  ×4 ppc halved the ripple at `n_cr` (9.32 → 4.56 %) but cut the far-wing leak **×0.25** at 0.25
  and 0.5 ps — because weakly scattered power goes as `δn²`. The tell that it is transported
  rather than absorbed light: the wings take in **4.1–4.3× the power incident on them**. It also
  costs a number you might quote — 36 ppc under-reports `f_ax` by **16 %** — and the *sign*
  identifies the mechanism, since the 36 ppc axis is *cooler* and so should absorb *more*. By
  0.75 ps the `δn²` law fails (the 36 ppc leak turns over while 144 ppc rises), so **two ppc
  points bound the requirement and cannot claim convergence**.
- **The step-0 spot profile is the one transverse check with NO shot-noise floor.** `w_eff/w₀`
  1.0000, `f_ax` 0.9999, `f(1w₀)` 0.9973, `f(2w₀)` 1.0009, leak 0.00041 — *identical* at 36 and
  144 ppc, so it is geometry and the tolerance is the print precision. Use it, not a driven
  total, to regression-test anything that touches the ray march.
- **A faster ray march does not buy ppc.** 144 ppc at the spot geometry does not fit in 12 GB;
  that is a memory bound the march has no bearing on. Cost decomposes as
  `T = M + P·ppc` — from 1103 s (36 ppc) and 2331 s (144 ppc), `M` = 694 s, so the march is
  **62.9 % at 36 ppc but only 29.8 % at 144** (and 694 s bounds it from above, since `M` also
  holds the field solve). Optimising the march buys transverse extent and sweep points.
- **`lpio.plotfiles(rd)` without a prefix silently mixes three diagnostic families.** The
  default prefix `"diag"` is a prefix of `diag1*`, `diag_fields*` AND `diag_phase*`, so a
  `{step: path}` dict built from it keeps whichever came last and quietly reads the wrong dumps.
  Only `diag1*` carries the full particle record (`particle_momentum_{x,y,z}`,
  `particle_weight`); `diag_phase*` carries **none** of `targ_electrons`' fields. Every other
  script passes an explicit prefix — do the same. And never wrap a particle-field read in
  `except: continue`: a missing field then contributes **zero**, which turns a wrong-family
  mistake into a confident fabricated number (it produced a *positive* G3 control ratio, i.e.
  apparent grid heating, before the cross-check caught it).
- **Cross-check any new whole-domain measurement against `ParticleEnergy` before restricting
  it.** `scripts/g3_spot.py` computes G3 from plotfiles so it can be restricted to the
  illuminated columns; its whole-box column reproduces the reduced diagnostic to **0.000 %**,
  and that agreement — not the plausibility of the restricted number — is what makes the
  restricted number quotable.
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
