# LaserProdShock — hard-won conventions & gotchas

Every entry here was paid for by a wrong number, a lost run, or a retracted claim. This file
was split out of `CLAUDE.md` so it is read **on demand** rather than loaded into every session.

**Read this file before**: adding or launching a test, changing `cfl`/`dz`/`ppc`/box size,
benchmarking, switching CPU↔GPU, rebuilding WarpX, comparing runs or dimensionalities,
quoting absorption/piston/transverse numbers, or touching a finite-spot run.

`CLAUDE.md` keeps only the non-negotiables that prevent a destructive or silently-wrong
action. Everything else — the reasoning, the numbers, the failure histories — is below.

---

## Grid, resolution and stability

Everything that decides whether the run is numerically trustworthy before it is physically interesting.

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
- **`local` temperature mode needs ppc.** `T^{−3/2}` is convex, so per-cell noise biases
  absorption **high**: ~3 % at 25 ppc, < 0.1 % at 800. High ppc in the target, not the
  ambient. Watch `Tlocalfrac`.
- **ppc in 2D: 36 (6×6), not 400.** 400 is unaffordable once a transverse dimension multiplies
  both grid and particles. G5's absorption-bias bound rises 0.31 % → 3.5 %, but `Tlocalfrac`
  stayed at 0.90–0.99 (and 0.975–0.987 in the Phase-0 2D runs at only **16** ppc), so `T_e` is
  still measured rather than floored. **Match the ppc in any 1D baseline** used for a 1D↔2D
  comparison, or ppc bias confounds dimensionality.
- **Size every box from `v_th,e`, NEVER from `c_s`. This has now cost three separate
  mistakes.** Electrons carry the energy and `v_th,e/c_s` ≈ 10 here (37.7 vs 4.0 `d_e`/ps at a
  227 eV corona). `P1_vac_2d_spot` sized its ±80 `d_e` transverse box from `c_s` — predicting the
  lateral flow would reach the wall at 14 ps, beyond its 9.96 ps — and **lost its transverse
  contrast after 1.99 ps**, against the 2.1 ps `v_th,e` predicts. The same error appeared in
  Phase 0 (confining the ambient electron excursion needs ~2 400 `d_e` per open direction) and in
  O2's vacuum estimate (a forward gap is consumed at `v_th,e`, so it lasts ~1/10 as long as a
  `c_s` estimate says). **Ask it of every dimension:** `L/2 ≳ v_th,e·t_end + (initial extent)`.
- **No mesh refinement.** The operator asserts `finestLevel() == 0`. One uniform grid must
  resolve both the near-critical target and the tenuous ambient; that scale separation is a
  central difficulty of the project, not something to engineer away.
- **Boundaries: periodic fields force periodic particles.** WarpX ties them
  (`Source/Particles/ParticleBoundaries.cpp`), and a free expansion has a runaway ion front
  (measured at 0.20 c) that then wraps and pollutes the upstream — **no vacuum gap is large
  enough** (two deck versions died this way). `open` = `pec` fields + `absorbing` particles
  is the combination that coexists with a uniform applied `B₀`; `absorbing`
  (Silver–Mueller) is **incompatible** with the div-B cleaner that runs when a background B
  is set. Also: **there is no vacuum gap behind the target** in an ambient run — the ambient
  fills both sides. This is Phase 0's subject; the finding lands here when it exists.
- **Truncate the domain at the target's rear face, with an `open` boundary.** Verified at
  both 20 d_e and 80 d_e thickness (front-side ion count within 0.11 %, `E_abs` within 0.9 %,
  total target `p_z` within 0.54 % at 80 d_e), and the fidelity *improves* with thickness
  because the rear rarefaction crosses less of a thicker slab. Saves 15-20 % of the cells.
  A `reflecting` rear is **different physics** — it flips the sign of the target's net
  momentum (a tamped target), and front-side density alone will not reveal that.
- **Validate a rear truncation by CORE DECOUPLING, never by boundary-density invariance.** The
  truncated boundary sits on a **free surface**, which must rarefy — asking it to stay put is an
  ill-posed test (`P1_vac_1d_thick`'s rear density fell 37 % while the truncation was sound).
  The right measure is the width of slab still at its initial density between the two
  disturbance fronts: 269 of 400 d_e (67 %) undisturbed there. Also, **truncating costs the
  energy budget** — 6.13 % weight loss at 30 ps vs 1.14 % at 100 ps untruncated — so **G6 cannot
  be closed tightly on a truncated run**; take strict closure from untruncated ones.
- **In a VACUUM run extra domain is nearly free — do not truncate to save cells.**
  `density_min = 1e-4·n_t` means WarpX creates no macroparticles below that density, so in
  `P1_vac_1d` only **525 of 2000 cells** carry particles and the other 1475 are empty field
  cells (a rounding error next to the particle push in 1D). Rear-face truncation pays off
  when an *ambient* fills the cushion at 48 ppc; with no ambient, spend the cells on genuine
  free surfaces at both faces instead. It is also why a 10 ps vacuum run is affordable.
- **A forward vacuum gap is now cheap for the ray trace too, but only because it is EMPTY.** The
  march costs `path/(ray_cfl·dz)` RK4 steps *per ray*, and rays = transverse cells ×
  `rays_per_cell`: in `P1_vac_2d` that is 9 168 steps × 64 rays = 5.9×10⁵ steps per application,
  **89 % of them through vacuum**. O2 now costs those steps ~1/4 of a full one (they keep their
  arithmetic, they drop their five interpolations), so a gap is ~4× cheaper than it was but not
  free — still size the forward gap to what the plume needs.

## The laser operator

How `LaserDeposition` behaves, what it fixes, and the two bugs that are still live.

- **The laser pins the absolute density scale.** IB absorption is measured against
  `n_cr = ε₀mₑω²/e²`, so λ₀ fixes densities in m⁻³ — a scale-free heater run cannot be
  re-labelled as a laser run. `KinShock2020`'s `n0 = 10¹⁸ m⁻³` target would be
  `2.5×10⁻⁸ n_cr` and perfectly transparent. **Quote every density in `n_cr`.** Note
  `d_e,cr = c/ω₀ = λ₀/2π` exactly, and that Schaeffer's Table I densities are 0.6 `n_cr`
  (ablation) and 0.0048 `n_cr` (upstream) at 1.053 µm.
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
- **A finite pulse is expressed through `intervals`.** `laser_deposition.intervals` is an
  `IntervalsParser`, so `start:stop:period` gates the drive on and off — there is no
  pulse-shape parameter. Verified in the source, 2026-07-28.
- **Rays launch EXACTLY ON the injection face** (`c0[axis] = inject_hi ? phi : plo`), not one
  cell inside it. So the boundary cell's plasma absorbs from the first RK4 step, and once the
  ablation plume reaches the launch plane **the beam is absorbed in the plume rather than at
  the target**. That is physically right, but it makes the drive a boundary quantity — keep
  the target far enough from the injection face that the transition is observable rather than
  present from t = 0. `make_inputs.py` warns when a corona exceeds 1e-3 n_cr at the face.
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
- **A skip threshold near a discrete trigger is not bounded by its own smallness.** O2 was
  specified as "treat `n_e < 3×10⁻² n_cr` as vacuum and jump" — the value chosen by sweeping the
  *discarded optical depth* to 3.5×10⁻⁴. It moved the 1D ramp CI deck by **+6.13 %**, because
  sub-threshold plasma still refracts: the discrete march lags the straight line by 1.6×10⁻³ `h`
  over 16 steps, the jump lands the ray ahead of it, and that flips the near-critical trigger
  `n_ref ≤ n_floor && drds > 0` — which pre-change **never fires** on that deck. Skipping one
  cell and skipping four gave the identical error, the signature of a discrete flip. **Ask what
  an approximation does to the branches downstream of it, not only to the quantity it bounds.**
- **Absorption FLOORS onto a plateau, then decays HYDRODYNAMICALLY when the target goes
  underdense. A half-peak `t_s` is meaningless here.** `f_abs` 1.000 → plateau ≈ 0.24 → 0.042
  at 100 ps (`P1_vac_1d_long`). The decay is caused by the rarefaction taking peak `n_e` below
  `n_cr` — measured at **28.8 ps**, with `f_abs` at half its plateau by **41.6 ps** — so the
  beam punches through with no turning point. **Not** H1's shutoff temperature, and **not**
  never (which is all 10 ps could show). **H2 stays falsified**: `E_abs = ∫f_abs(t)·I₀ dt`
  with `f_abs` set by the target's hydrodynamic state (`TEST_PLAN.md` §2.4–2.5). Quote the
  **plateau level, the `n_cr`-crossing time and `dE/dt`** — never a half-peak shutoff time.
- **The coronal scale length sets the absorption REGIME, not just the amount.** `L_n/w_t`
  0.19 → 0.75 (`L_n` 15 → 60 d_e at `w_t` = 80) took τ-to-the-turning-point from 0.14 to 5.60,
  i.e. optically thin → thick, and `f_abs(0)` from 0.248 to **1.000**. At `L_n` = 60 the ray is
  extinguished ~15 d_e *before* the critical surface: **0.000 % of `P_abs` lands at or below
  it**, so the turning point plays no role and G4's `ray_cfl` sensitivity should weaken. Predict
  this before running by integrating τ to the turning point at the **group** `T_e` — it got
  +53.8 d_e for the deposition peak against a +53.6 d_e prediction.
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

## Running: launch, build, kill, performance

Read before starting anything. Several of these are destructive if ignored.

- **Launch with `scripts/launch.sh runs/<phase>/<ID>`, never by hand.** The generated deck sets no
  `diag*.file_prefix`, so WarpX writes plotfiles to `diags/` *relative to the launch CWD* —
  two runs launched from the repo root share `./diags/` and clobber each other (`.old.NNNN`
  rename files are the tell; cost a rerun in `KinShock2020`). `launch.sh` cd's into the run
  dir, **picks `warpx.1d`/`warpx.2d` from `geometry.dims`**, applies the benchmarked OMP
  settings, requires a `README.md`, and refuses to start when `diags/` already holds output
  (`--force` to override). `-b` detaches, `-L` also starts the progress logger, `-n`
  dry-runs, and anything after `--` becomes ParmParse overrides (smoke tests only — they
  will trip `--verify`).
- **A binary that predates a deck's flag IGNORES IT SILENTLY — so run `--verify` right after
  launch, not at the end.** `P1_vac_2d_spot_abl` was launched with
  `laser_deposition.refraction = 0` onto `build_cuda_omp` as built on **2026-07-31**;
  `refraction` was added to the operator on **2026-08-04**. `amrex.abort_on_unused_inputs`
  defaults to 0, so WarpX parsed the deck, never queried the key, said nothing, and marched
  with **full refraction** while the run's README claimed straight rays. Nothing in the run's
  own output looks wrong — `f_abs`, `Tlocalfrac`, the gates and both GPUs were all healthy.
  The single tell is that the key is **absent from `warpx_used_inputs`**, which is exactly what
  `make_inputs.py --verify` reports (`laser_deposition.refraction: missing from
  warpx_used_inputs`). `warpx_used_inputs` is written at initialisation, so **`--verify` is
  answerable seconds after launch** — that is when the answer is cheap, and it cost 7 minutes
  here instead of 4.6 h. Settle it in one line with
  `strings <binary> | grep -x <key>`, and treat **the binary's build date as part of a run's
  provenance**: check it against the commit that introduced whatever the deck newly relies on.
  Corollary: `build/` (CPU) and `build_cuda*/` drift apart independently — on 2026-08-05 the
  CPU build had `refraction` and the CUDA one did not. The step-0 dumps the aborted run left
  behind are kept as a free refracting reference in `studies/refraction_xcheck/`.
- **The build trees are SHARED with the other projects in `warpx-cda`, and they get rebuilt
  under you from other branches.** The bullet above is a binary that is too *old*; this is the
  same failure from the opposite direction. `build_cuda_omp/bin/warpx.2d` was rebuilt on
  **2026-08-07 19:04** by the hybrid/particle-heater work — `warpx-cda` is now checked out on
  `feature/hybrid-laser`, not `feature/laser-deposition` — and that binary contains
  `electron_energy_mode` and **zero occurrences of `refraction`**. So the binary in the tree
  today **cannot reproduce `P1_vac_2d_spot_abl`**: re-running that deck with it would silently
  march with full refraction, which is precisely the 2026-08-05 bug. The completed run is not in
  doubt — its `warpx_used_inputs` records `laser_deposition.refraction = 0` and is committed,
  which is *why* that file is tracked — but **a finished run's binary provenance can be
  invalidated after the fact, by another project, without touching this repo at all**. So:
  `strings <binary> | grep -x <key>` **at launch**, never assuming yesterday's build survived;
  and when a result must be reproducible, record the branch and commit
  (`git -C ~/warpx-cda log -1 --format=%h` into the run README) and rebuild from it rather than
  trusting whatever the tree currently holds.
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
- **`laser_deposition.ray_threads` exists because `--gpu` still wants `OMP_NUM_THREADS=1`.** The
  push belongs on the device; the march is host code and now threads. Set `laser.ray_threads` in
  `config.yaml` rather than raising `OMP_NUM_THREADS`, and note that O1 is **inert unless the
  binary was compiled with `-fopenmp`**: `build_cuda` is `AMReX_OMP=OFF`, so that binary gets
  O2 + O3 + O4 only. **Use `build_cuda_omp/bin/warpx.2d`** — the same tree configured
  `-DAMReX_OMP=ON`, which puts `-Xcompiler=-fopenmp` in the CUDA flags. `launch.sh --gpu` warns
  when a driven deck sets no `ray_threads`. The best value is **machine state, not a constant**:
  8 beat 16 at load 18 and lost to it on a quiet box.
- **GPU benchmarks assume an IDLE host.** A CUDA run is latency-bound on one host thread issuing
  kernel launches, so a loaded box starves it: at 2882 % CPU demand on 32 cores the 100 ps runs
  took 1.8× their benchmark, GPU utilisation fell 71 % → 53 % and power sat at 47–56 W of 200 W.
  Separately, cost grows *during* a vacuum run as the plume spreads (occupied cells 526 → 10 800
  at flat particle count ⇒ deposition scatters over 20× the memory footprint); the laser-off
  control slows too, which is how to tell the two apart. **`warpx.sort_intervals` is worth
  benchmarking on GPU** — the "sorting is neutral-to-negative" note below is an inherited *CPU*
  result and should not be assumed to hold on the device.
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
- **The CUDA build is not run-to-run reproducible AT ALL, so no bit-level check may be run on
  it.** The bullet above is a CPU statement. On `build_cuda_omp`, two runs of one
  configuration — same binary, same deck, `OMP_NUM_THREADS=1` — differ by up to **1e-3
  relative in `Pabs`**, and that holds even on the static-plasma `laser_deposition` CI decks,
  which evolve no particles at all. The cause is atomic ordering in the GPU density deposit,
  amplified by `K ∝ n_e²/√(1−n_e/n_cr)` near critical. This produced a wrong conclusion once
  already: an old-vs-new binary comparison "failed", and the control — the old binary against
  *itself* — failed identically, so the test had no power. **Always run that control.** Take
  bit-identity acceptance from `build/` (OMP/CPU), where the same three CI decks are
  byte-identical run to run and to the pre-change binary. Whatever produced the "Tier 1
  285/285 byte-equal" figure, it was not the CUDA build.
- **Movie frames clean themselves up.** `make_movies.py` writes PNGs to
  `media/<phase>/<ID>/_frames_<name>/` and deletes the directory once ffmpeg succeeds; leftovers
  from an interrupted encode are swept at startup (so stale frames cannot be globbed into a
  new, shorter movie). `--keep-frames` retains them, and a failed encode keeps them
  automatically. Never leave frame directories behind by hand -- they are several times the
  size of the movie they produced.

## Diagnostics and reading output

How to get a number out of a run without it being silently the wrong number.

- **`diag1` has only the total `rho`; per-species densities are on `diag_fields`.** And yt
  refuses a `covering_grid` flush against a non-periodic domain edge on some domain sizes —
  call `ds.force_periodicity()` first (the analysis scripts do).
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
- **The step-0 spot profile is the one transverse check with NO shot-noise floor.** `w_eff/w₀`
  1.0000, `f_ax` 0.9999, `f(1w₀)` 0.9973, `f(2w₀)` 1.0009, leak 0.00041 — *identical* at 36 and
  144 ppc, so it is geometry and the tolerance is the print precision. Use it, not a driven
  total, to regression-test anything that touches the ray march.

## Controls and comparing runs

What is comparable to what, and what a control has to hold fixed to be one.

- **Quote `E_abs`, never `f_abs(0)`, when comparing runs.** `f_abs(0)` carries a **10.4 %
  1σ and a 30.6 % full spread** across runs differing only in RNG seed
  (`studies/fabs_noise/`): `K ∝ 1/√(1−n_e/n_cr)` diverges at the critical surface and the
  operator integrates that layer over a locally interpolated, noisy density and gradient, so
  essentially the whole run-to-run difference sits in the single cell containing the critical
  surface. `E_abs` integrates hundreds of applications and agreed to 0.6 % between geometries
  whose `f_abs(0)` differed by 10 %. This also makes gate G4 a **noise-amplification** issue,
  not only a discretisation one.
- **Compare energy-integrated `E_abs` or the mean across dimensionalities — NEVER the median.**
  The 5–25 ps median `f_abs` differed 1D vs 2D by **48 %** where the energy-integrated figure
  differed by **12 %**: 2D sums 64 rays so its distribution is smooth and median ≈ mean, while
  1D's single ray is spiky and median ≪ mean. The median difference was an estimator artifact.
- **A `_off` control is worth more than its energy budget.** `P1_vac_2d_off` is what proved the 2D
  transverse structure was shot noise rather than laser-driven filamentation — a question that
  would otherwise have been unresolvable speculation. Also: at 36 ppc its excursion is **−3.09 %**
  of the driven gain against **−0.066 %** at 400 ppc (47× larger), so quote it beside any
  few-percent 2D number.
- **A `_off` control must differ ONLY in `laser.intensity`.** Grid heating accumulates with
  step count and depends on the grid, the ppc and the species, so any other difference makes
  the G3 subtraction meaningless. `tests/test_structures.py` renders both decks and diffs
  them, rather than trusting that two hand-edited configs stayed in step.
- **Matching a 1D run to a 2D run means matching `t_end`, not `max_step`.** `dt` is `cfl·dz/c`
  in 1D but `cfl·dz/(c√2)` in 2D, so 2D needs √2 more steps for the same physical time.
- **`c_s` must come from the MEASURED electron energy, not `laser_report`'s implied `T_e,ab`.**
  That number assumes all coupled energy is electron thermal, but **66 % of it is in ions** by
  100 ps, so it overstates `c_s` by 2.3× and understates α to 0.84. Use `<KE_e>` from the `EP`
  reduced diag: `T_e = (2/3)<KE_e>` ⇒ 548 eV ⇒ `c_s` = 0.00327 c ⇒ **α = 1.5–2.4, so H3 is
  CONFIRMED** (predicted 1–3). Ion energy is 62 % of `E_abs` — the drive efficiency Phase 2 spends.

## Shock and piston claims

The arbiters. Nothing here is optional before the word 'shock' is used.

- **Shock kinematics come from `runs/<phase>/<ID>/shock_fit.yaml`, fit BY EYE** — the convention
  `KinShock2020` arrived at after automatic `v_sh` drifted between scripts. One speed and
  front per run, shared by every diagnostic.
- **Target thickness is a DRIVE-DURATION knob, and it trades against piston speed.** A 5×
  thicker target keeps the peak above `n_cr` for the whole run (it even *compresses*, to 1.92
  `n_cr`) where the 80 d_e target crossed at 28.8 ps and lost its plateau — so thickness extends
  the drive past the ~38 ps formation needs. But it costs speed: `E_abs` rises only ~46 % for 5×
  the mass (a colder target absorbs *better*, `K ∝ n_e²T_e^{−3/2}`, so the plateau is +23 % —
  coupled energy is **not** thickness-independent), hence `v_p ∝ √(E_abs/w_t)` **falls** (0.63×
  measured, 0.54× predicted). **H3's "thickness leaves `v_p` unchanged" is FALSIFIED**; α ≈ 1–2
  survives. There is an optimum thickness, as consequential as the optimum `I₀` (`TEST_PLAN.md`
  §2.6).
- **Thickening the target does not raise the Mach number.** Coupled energy and mass both
  scale with thickness, so `v = √(2E/m)` is unchanged. Thickness buys piston *momentum*
  (drive distance).
- **A non-monotonic ion front means particles LEFT, not that the piston decelerated.** The
  driven percentile front read 0.0536 c at 30 ps but 0.0245 c at 100 ps purely because the fast
  tail was absorbed at the wall. Another reason fronts are the wrong `v_p` measure.
- **In a driven vacuum run the plume edge advances at ~50 d_e/ps once `T_e` ≈ 600 eV** — far
  faster than the ~20 d_e/ps a 10 ps run extrapolates, because the target keeps heating. Sizing
  `P1_vac_1d_long`'s domain from 10 ps drift rates left the plume pinned against both walls for
  the last 45 % of the run (1.14 % weight loss, G6 −9.56 %). **A 100 ps vacuum run needs
  ≥ ±5000 d_e**, and the requirement is set by the **drive**, not the geometry — the laser-off
  control on the same domain lost only 0.0014 %.
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

## Finite spot (2D)

Only relevant to finite-spot runs, but non-negotiable within them.

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
- **A faster ray march does not buy ppc.** 144 ppc at the spot geometry does not fit in 12 GB;
  that is a memory bound the march has no bearing on. Cost decomposes as
  `T = M + P·ppc` — from 1103 s (36 ppc) and 2331 s (144 ppc), `M` = 694 s, so the march is
  **62.9 % at 36 ppc but only 29.8 % at 144** (and 694 s bounds it from above, since `M` also
  holds the field solve). Optimising the march buys transverse extent and sweep points.

## Cross-code comparison (FLASH / PSC / WarpX)

Added 2026-08-27. Every one of these has already produced a wrong number in `RESULTS.md`.

- **PSC has TWO normalisation knobs, and the second one is easy to miss.** `ReducedMassRatio`
  = 100 sets `d_i0` and the mass unit; `ReducedSoL` = 3000 eV / `m_e c^2` sets the temperature
  unit, the clock and the collision rate. `K_length` (`INIT_param.f:156`) and `K_mass` (`:164`)
  carry **no** `ReducedSoL`, so the 60 keV and 511 keV legs share every length and every
  physical mass. What moves is `K_temperature` (8.52×), `K_time` (2.92×) and `nudt0` (72.5×).
- **The PSC leg to compare against is `~/psc-raytrace/run_ourflash_511keV`, not the paper's
  `run_ourflash`.** At 511 keV, `c` = `K_length/K_time` = 0.2333 `c` = 1/√18.36 exactly — for
  an 18.36× electron that is precisely the `c` that keeps `m_e c²` real, so the leg sits **on**
  the similarity transform. The 60 keV leg cuts `c` a further 2.92× beyond it and is **72.5×
  over-collisional** (`nudt0 *= (511000/K_temperature)²`, `:594`). It also crashed at 18 % of
  its planned length; the 511 keV leg finished clean.
- **Never hardcode PSC's units — call `xcode_compare.psc_norm(data_dir)`.** It reads
  `K_temperature`, `K_time` and `dt` from the run's own `run.log`. The old hardcoded 60 keV
  constants (`K_TEMP_ = 60000`, `DT_PSC = 4.544 fs`, `ReducedSoL = 0.05`) read the 511 keV
  dumps **8.52× too cold on a clock 2.92× too slow, silently and with no error.**
- **PSC's ion is REAL aluminium at every `ReducedMassRatio`** — `MMi1·K_mass` =
  `26.9815·hydr_mass_phys`, the ratio cancels (`:212`, `:164`). So a PSC "µ-sweep" is an
  **electron**-mass sweep at fixed real ion, and PSC's plume `T_e` is *expected* to be
  RMR-invariant. That is why PSC "shows no `µ^(1/3)`" — not a code difference, a different knob.
- **PSC's COLLISION lnΛ is a global 8.275, not the per-cell NRL.** The per-cell NRL formula
  (`get_lnlambda`, `PIC_part_heating.F90:882`) belongs to the **laser** operator only;
  `INIT_param.f:584` sets `lnlambda = 23 − ln(√n_cr·Z_eff/T^1.5)` once at `n_cr` and 3000 eV,
  floored at 1, entering only through `nudt0`. WarpX's is 6.3 global — same kind, 1.31× apart.
- **Say which `f_abs` you mean.** The `RESULTS.md` cross-code tables all use `f_end`, the final
  *instantaneous* value from the LASERDEP lines. `xcode_compare.absorbed()` returns `f_mean`,
  the **time-integrated** fraction, and its own docstring says that is the one setting the
  energy budget. They differ materially (WarpX mr100 0.350 vs 0.364; PSC 0.475 vs 0.583) and
  `T_ss ∝ f_abs^(2/3)` amplifies the choice. `f_abs` is also violently spiky per-step, so a
  single endpoint carries large noise — never mix conventions inside one table.
- **`µ^(1/3)` rescales `T_ss`, but the transform is NOT collisionality-preserving.**
  `λ_ei ∝ T²/(n lnΛ)` is **mass-independent**, while `L ∝ d_i0 ∝ µ^(1/2)`, so
  `λ_ei/L ∝ µ^(1/6)` — at WarpX's `µ` = 0.0545 that is 0.616, i.e. **1.62× more collisional
  relative to scale** than the real system. Optical depth `∫K dz` *is* preserved (`µ⁰`).
  PSC's heavy-electron convention keeps `m_i` real, so its `λ_ei/L` is exactly real.
- **`LaserDeposition.cpp` hardcodes `PhysConst::m_e` in 17 places, so a non-real electron mass
  silently corrupts the operator under test.** Two are fatal: `:1014` measures
  `kT = PhysConst::m_e·⅓·(u²−drift²)`, so in `temperature_mode: local` an 18.36× electron reads
  `T_e` **18.36× too cold** and `K ∝ T^(−3/2)` **78.7× too large**; and `:1135` builds `H` with
  `1/m_e,real` while the kick at `:2088` delivers `⟨dE⟩ = m_actual·H·dt`, so particles absorb
  **18.36× more energy than the rays gave up**. Only G6 would catch the second. **Any
  `electron_mass_scale` work needs the C++ fixed first** (`:936/:1014`, `:1135`, `:357/:359`).
- **Cost of a WarpX mass-ratio leg scales as `s^2.55`, not `s³`** (`s = √(mr/2698)`). Measured:
  mr25 58.35 s, mr100 345.1 s, mr400 2009 s, all one RTX 4070, all completed. The shortfall
  from `s³` is GPU underutilisation at 2.5k–10k cells and should trend back toward 3 as cells
  grow — so treat `s^2.55` as a floor, not a central estimate, when extrapolating.
- **A new PSC run directory needs `data/{chk,etracking,itracking}` pre-created, not just
  `data/`.** PSC takes its first checkpoint at 3 minutes of wall time
  (`checkpoint_next = 0.05*60*60`, `INIT_param.f:386`) and `SERV_openby_p` opens
  `data/chk/...` without creating the directory, so the run aborts there — far enough in to
  look like a physics failure and to have written five moment dumps first.
- **The `s` rescaling of a mass-ratio leg is 100 % MANUAL.** Nothing in `units.py`/`deck.py`
  applies it. Two families: **s¹** on `d_e`-quoted lengths (`thickness_de`, `center_de`,
  `scale_length_de`, `corona_offset_de`, `axis.lo_de`, `hi_de`, `max_grid_size`) and **s²** on
  `mass_ratio`, `laser.profile_intervals`, `max_step` and the four `diagnostics.*_intervals`.
  `dz`, `dt`, `cfl`, `ppc` and every `theta_*` stay fixed — `dt` is bit-identical across the
  whole existing scan. `n_cell` must stay divisible by `blocking_factor` 8 (AMReX aborts, so
  this one is loud) and `max_grid_size` must be reset to match it or the one-box GPU rule costs
  7.9×.

## Environment

- **Env.** conda env at `/opt/anaconda3/envs/physics`; WarpX binaries
  `/home/hhelal/warpx-cda/build/bin/warpx.{1d,2d,3d}` (OMP/CPU, double precision) and
  `build_cuda1d/bin/warpx.1d` + `build_cuda/bin/warpx.2d` (CUDA, double precision).
