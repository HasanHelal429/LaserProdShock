# `scripts/` — driver and analysis CLIs

Each script is config-driven: it reads `runs/<ID>/config.yaml`, derives every physical scale
through `laserprod.units`, and either generates the WarpX deck or writes outputs under
`media/<ID>/`. **`config.yaml` is the single source of truth** — you author the intuitive
primaries there (densities in `n_cr`, θ = kT/mₑc², lengths in `d_e,ref`, speeds in `c`,
intensity in W/m²) and `make_inputs.py` generates the deck. The deck is a build artifact;
never hand-edit it.

Run from the repository root:

```bash
python scripts/<script>.py <run_dir> [options]
```

## Status

| Script | Purpose | Reads | Writes | Status |
|---|---|---|---|---|
| `launch.sh` | **The** way to start a run | `config.yaml`, `README.md`, deck | `<run_dir>/{run.log,diags/}` | **built** |
| `run_progress_logger.py` | Sidecar wall-clock progress/ETA + live absorption-shutoff readout | `run.log`, deck | `<run_dir>/progress.log` | **built** |
| `make_inputs.py` | `config.yaml` → deck (`--verify`, `--check`) | `config.yaml` | `inputs_<id>` | **built** |
| `run_checks.py` | Derived scales + numerical gates G1–G7 + a pre-run figure | `config.yaml`, `run.log`, reduced diags | `media/<ID>/checks.png`, `gates.png` | **built** |
| `laser_report.py` | `LASERDEP` history + per-cell profile dumps → `f_abs(t)`, `E_abs`, `t_s`, `Tlocalfrac` | `run.log`, `diags/laserdep_profile_*.txt` | `media/<ID>/laser_*.png` | **built** |
| `plot_fields.py` | (z,t) streaks of `n_e`/`B_y`/`E_z`, lineouts, 2D x–z map | `config.yaml`, plotfiles | `media/<ID>/fields_*.png` | **built** |
| `phase_space.py` | **The arbiter** — ion (z, u_z), reflected-ion population | `config.yaml`, plotfiles | `media/<ID>/phase_space.png` | **built** |
| `make_movies.py` | Movies: evolving lineouts + laser cursor, phase space, 2D map | `config.yaml`, plotfiles | `media/<ID>/movie_*.mp4` | **built** |
| `compare_runs.py` | Cross-run overlay — the controlled-comparison evidence | several run dirs | `media/<name>/compare.png` | **built** |
| `plot_ablation.py` | Vacuum ablation: plume profiles, `v_p`, `T_e(t)`, energy budget | `config.yaml`, plotfiles | `media/<ID>/ablation_*.png` | Phase 1 |
| `tune_shock.py` | Fit `v_sh` + front **by eye** → `shock_fit.yaml` | `config.yaml`, plotfiles | `<run_dir>/shock_fit.yaml` | Phase 2 |
| `make_figures.py` | Schaeffer criteria + `criteria.json` | `config.yaml`, plotfiles, `shock_fit.yaml` | `media/<ID>/*.png` | Phase 2 |
| `sweep.py` / `plot_sweep.py` | Launch + reduce a parameter sweep to fitted exponents | `studies/<name>/` | `media/<name>/*.png` | Phase 3 |

Ports available for reference when building the Phase-2 tools:
`../KinShock2020/scripts/{tune_shock,make_figures,make_movies}.py` and
`../KinShock2020/src/kinshock/metrics.py` (Schaeffer criteria, `F`/`G`, front tracking);
`warpx-cda/laser_deposition/scripts/{plot_laser_shock,plot_laser_shock_phase,ibtheory}.py`
(`LASERDEP` parsing, phase-space plots, independent analytic IB reference).

---

## `launch.sh`

**Use this rather than invoking WarpX yourself.** The generated deck sets no
`diag*.file_prefix`, so WarpX writes plotfiles to `diags/` *relative to the launch CWD* —
two runs launched from the repo root share `./diags/` and clobber each other (`.old.NNNN`
rename files are the tell; this cost a rerun of two control runs in `KinShock2020`).
`launch.sh` always cd's into the run dir first.

It additionally:

- **picks the WarpX binary from `geometry.dims`** (`warpx.1d` / `warpx.2d`) — this project
  runs both, unlike `KinShock2020`. Override with `--warpx`, `$LPS_WARPX`, or
  `$LPS_WARPX_DIR`;
- **refuses to start a run with no `README.md`** (`runs/README.md` explains why);
- applies the benchmarked thread settings (`OMP_NUM_THREADS=8 OMP_PROC_BIND=spread
  OMP_PLACES=cores` — near-linear to 8 cores, ~1.8× vs 4);
- resolves the run's single `inputs_*` deck and sends stdout/stderr to `<run_dir>/run.log`;
- **refuses to start when `diags/` already holds output**, since relaunching overwrites a
  finished run's plotfiles in place.

```bash
scripts/launch.sh runs/P1_vac_1d              # foreground, logs to the run dir
scripts/launch.sh -b -L runs/P1_vac_1d        # detach + start the progress logger
scripts/launch.sh -n runs/P1_vac_1d           # dry run: print the command, change nothing
scripts/launch.sh -f runs/P1_vac_1d           # overwrite a populated diags/ (mean it)
scripts/launch.sh runs/P1_vac_1d -- max_step=20   # ParmParse overrides: smoke tests only
```

Overrides after `--` are not reflected in `config.yaml`, so `make_inputs.py --verify` will
flag them afterwards. Use them for smoke tests, not physics.

## `run_progress_logger.py`

Watches `run.log` and appends a checkpoint to `<run_dir>/progress.log` every N percent of
`max_step`: wall-clock elapsed and ETA, the WarpX compute rate, a contention factor
(wall-rate / compute-rate, > 1 when the machine is shared), and the system load — so compute
cost is trackable after the fact and runs can be paced without babysitting.

`--total` is auto-detected from `warpx_used_inputs` / the deck (last `max_step` wins,
matching ParmParse). The logger stops at `max_step`, on WarpX's end marker, or when the run
goes stale.

**Laser addition over the `KinShock2020` original**: when the deck enables the ray-tracing
laser with `warpx.verbose = 1`, WarpX emits
`LASERDEP step <n> t <s> Pabs <W> Eabs <J>` per application. The logger reports `Pabs` as a
fraction of its running peak plus the cumulative `Eabs`, which is the cheapest live read on
the **self-limiting absorption shutoff** (`K ∝ n_e² T_e^{−3/2}`, so the drive switches itself
off as the corona heats and rarefies). A run whose `Pabs/Pmax` has collapsed to ~0 is no
longer being driven, however many steps remain — useful for killing a run early.

Normally started by `launch.sh -L`; standalone:

```bash
python scripts/run_progress_logger.py runs/P1_vac_1d --every-pct 5 --poll 20
```


---

## Figure conventions

Every analysis script writes into `media/<run_id>/` and prints the path. Two rules the
figures never break, both enforced in `laserprod.plotting`:

- **No dual axis.** Two measures of different scale go in stacked panels sharing an
  x-axis, never twin y-axes. Overlaying an absorbed *power* on a *density* is how a
  shutoff gets misread as a compression.
- **Status is never colour alone.** Gate rows carry a colour chip, a glyph and a word,
  so a red cell still means something in greyscale, in print, or to a reader who cannot
  see red.

The three categorical series colours (target / ambient / laser) were **validated, not
eyeballed** — checked with the `dataviz` skill's `validate_palette.js` in the order they
are assigned. All hard checks pass on the light surface (worst adjacent CVD ΔE 23.1
protan / 9.6 tritan; worst normal-vision ΔE 24.0). The one WARN is sub-3:1 contrast on
the aqua and yellow slots, whose required relief is *visible labels* — which is why every
series is directly labelled rather than identified by colour alone.

**Figure titles are descriptive, never assertive.** A panel states what the data shows,
computed from that run's own numbers — it does not restate the hypothesis the run is
testing. (`laser_report.py`'s coupled-energy panel computes the late/early `dE/dt` ratio
and says whether the run saturated, because the first run through it did **not**, and a
title claiming otherwise would have been wrong on the page.)


---

## The plotfile tools need the `physics` environment

`plot_fields.py`, `phase_space.py` and `make_movies.py` read WarpX plotfiles through **yt**,
which lives only in the project conda env — base anaconda has matplotlib and yaml but not
yt. Run them as:

```bash
/opt/anaconda3/envs/physics/bin/python scripts/plot_fields.py  runs/<ID>
/opt/anaconda3/envs/physics/bin/python scripts/phase_space.py  runs/<ID>
/opt/anaconda3/envs/physics/bin/python scripts/make_movies.py  runs/<ID> --fps 12
```

`make_inputs.py`, `run_checks.py`, `laser_report.py` and `compare_runs.py` need neither yt
nor plotfiles — they work from `config.yaml`, `run.log` and the plain-text reduced diags, so
they run under any interpreter and while a run is still going.

## `make_movies.py`

Three movies per run, into `media/<ID>/`:

| file | what |
|---|---|
| `movie_fields.mp4` | `n_e(z)` and `B_y/B_0(z)` lineouts, with the full `f_abs(t)` history below and a cursor marking the current frame |
| `movie_phase.mp4` | ion `(z, u_z)` phase space, target and ambient additively tinted |
| `movie_map2d.mp4` | `n_e(x, z)` map (2D runs only) |

**Axis limits are fixed across all frames**, computed from every frame before any is drawn.
Per-frame autoscaling is the easiest way to make a movie useless — a plume that grows by
two decades looks stationary if its axis grows with it.

**Frames are temporary and are deleted automatically.** They go to
`media/<ID>/_frames_<name>/` and the directory is removed as soon as the encode succeeds —
the PNGs are a build artifact of the mp4 and are several times larger than it (sweeping the
first batch reclaimed 43 MB against 13 MB of kept output). Leftovers from an interrupted
encode are swept at startup, which also prevents ffmpeg globbing stale frames into a new,
shorter movie. Frames are kept when ffmpeg *fails*, since then they are the only record of
what went wrong, and `--keep-frames` retains them deliberately for debugging.

Encoding is libx264 with `-pix_fmt yuv420p` and an even-dimension scale filter, both
required for the result to play in a browser.
