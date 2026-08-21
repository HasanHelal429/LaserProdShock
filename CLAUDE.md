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

## Non-negotiables (full reasoning in `GOTCHAS.md`)
`GOTCHAS.md` holds 63 hard-won conventions — **read it before** adding or launching a test,
changing `cfl`/`dz`/`ppc`/box size, benchmarking, switching CPU↔GPU, rebuilding WarpX,
comparing runs or dimensionalities, or quoting absorption/piston/transverse numbers. The
handful below are here because getting them wrong is destructive or silently wrong:

- **Launch with `scripts/launch.sh runs/<phase>/<ID>`, never by hand.** Decks set no
  `diag*.file_prefix`, so a hand launch writes `diags/` relative to the launch CWD and two runs
  clobber each other. `launch.sh` cd's in, picks the binary from `geometry.dims`, requires a
  `README.md`, and refuses to start over existing output. `-b` detaches, `-L` adds the progress
  logger (always use it).
- **Run `--verify` seconds after launch, not at the end.** A binary that predates a deck's flag
  **ignores it silently** — WarpX never queries the key and says nothing. `warpx_used_inputs` is
  written at initialisation, so the answer is cheap immediately; this cost 4.6 h once.
- **The `warpx-cda` build trees are SHARED and get rebuilt under you by other projects.**
  A finished run's binary provenance can be invalidated after the fact without touching this
  repo. `strings <binary> | grep -x <key>` at launch; record branch + commit in the run README.
- **Kill runs BY PID.** `pkill -f` matches the shell you type it in — it has killed the invoking
  shell mid-chain and orphaned a progress logger onto the same `progress.log`. Use
  `ps -eo pid,lstart,args | grep <thing>` then `kill <pid>`, and check what survived.
- **`ω_pe·dt < 2` is the binding stability limit and the grid CFL cannot see it.** Check it at
  the **peak compressed density the run will reach**, not at t=0 (gate G1). `cfl ≈ 0.35` in 1D /
  `0.5` in 2D is tested. Violating it grew total particle energy 21× while the laser supplied
  1/1400 of it.
- **Size every box from `v_th,e`, NEVER from `c_s`** — `v_th,e/c_s ≈ 10` here. This has cost
  three separate mistakes.
- **No mesh refinement.** The operator asserts `finestLevel() == 0`. The scale separation is a
  central difficulty of the project, not something to engineer away.
- **GPU: `launch.sh --gpu [N]`; the CUDA build is ONE TREE PER DIMENSIONALITY** (`build_cuda/`
  is 2D only, 1D needs `build_cuda1d/`). Two RTX 4070s, `-g 0` / `-g 1`.
- **Quote `E_abs`, never `f_abs(0)`, when comparing runs.** `f_abs(0)` carries 10.4 % 1σ across
  RNG seed alone; `E_abs` agreed to 0.6 % between geometries whose `f_abs(0)` differed by 10 %.
- **Pass an explicit prefix to `lpio.plotfiles(rd)`.** The default `"diag"` prefixes `diag1*`,
  `diag_fields*` AND `diag_phase*`, silently keeping whichever came last. Never wrap a
  particle-field read in `except: continue` — a missing field then contributes zero.
- **Watch for stray `.old.NNNN` plotfiles.** WarpX renames rather than overwrites and the suffix
  parses as a step number, interleaving two runs at fabricated times.

- **Env.** conda env at `/opt/anaconda3/envs/physics`; WarpX binaries
  `/home/hhelal/warpx-cda/build/bin/warpx.{1d,2d,3d}` (OMP/CPU, double precision) and
  `build_cuda1d/bin/warpx.1d` + `build_cuda/bin/warpx.2d` (CUDA, double precision).

## Keeping this file cheap
`CLAUDE.md` is re-read on **every** API call in a session; `GOTCHAS.md`, `TEST_PLAN.md` and
`RESULTS.md` are not. New hard-won findings go in `GOTCHAS.md` (or `RESULTS.md` if they are
results), not here. Only add to this file something that prevents a destructive or silently
wrong action.

## Working preferences
- Work in the **regular repo folders** (not git worktrees). Commit to `main`.
- Keep `RESULTS.md` updated with a dated entry per substantive run/finding — that is how
  context survives between sessions. Anything worth keeping goes in the repo (scratch under
  a job's tmp does not persist).
- A negative result, stated quantitatively, is a result. If the laser-driven-shock regime
  turns out not to exist at affordable cost, the deliverable is the impossibility argument
  with numbers — that is the physics justification for why PSC and Fox 2018 prescribe a
  heater instead. Write it up as a finding, not a failure.
