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
| `queue_run.sh` | Wait for other work / GPUs to clear, then hand off to `launch.sh` | the `--after` run dirs, `nvidia-smi` | stdout (redirect it) | **built** |
| `run_progress_logger.py` | Sidecar wall-clock progress/ETA + live absorption-shutoff readout | `run.log`, deck | `<run_dir>/progress.log` | **built** |
| `make_inputs.py` | `config.yaml` → deck (`--verify`, `--check`) | `config.yaml` | `inputs_<id>` | **built** |
| `run_checks.py` | Derived scales + numerical gates G1–G7 + a pre-run figure | `config.yaml`, `run.log`, reduced diags | `media/<ID>/checks.png`, `gates.png` | **built** |
| `laser_report.py` | `LASERDEP` history + per-cell profile dumps → `f_abs(t)`, `E_abs`, `t_s`, `Tlocalfrac` | `run.log`, `diags/laserdep_profile_*.txt` | `media/<ID>/laser_*.png` | **built** |
| `spot_report.py` | **Finite-spot transverse diagnostics** -- deposition vs the analytic `I(x)`, `w_eff(t)`, on-axis `f_ax(t)`, edge-column regression | `config.yaml`, `diags/laserdep_profile_*.txt`, `run.log` | `media/<ID>/spot_*.png` | **built** |
| `g3_spot.py` | works; validated | G3 restricted to the illuminated columns, from plotfiles. Whole-box column reproduces `ParticleEnergy` to 0.000 % |
| `spot_isolation.py` | works; **should become a gate** | is a finite-spot run still a finite spot? `dark/lit` of the net absorbed energy, plus the box a valid run would need |
| `plot_fields.py` | (z,t) streaks of `n_e`/`B_y`/`E_z`, lineouts, 2D x–z map | `config.yaml`, plotfiles | `media/<ID>/fields_*.png` | **built** |
| `plot_rays.py` | **Ray paths** — refraction, the turning point, the outbound leg. Offline reconstruction, geometry only | `config.yaml`, plotfiles | `media/<ID>/rays.png` | **built** |
| `phase_space.py` | **The arbiter** — ion (z, u_z), reflected-ion population | `config.yaml`, plotfiles | `media/<ID>/phase_space.png` | **built** |
| `make_movies.py` | Movies: evolving lineouts + laser cursor, phase space, 2D map | `config.yaml`, plotfiles | `media/<ID>/movie_*.mp4` | **built** |
| `compare_runs.py` | Cross-run overlay — the controlled-comparison evidence | several run dirs | `media/<name>/compare.png` | **built** |
| `xcode_compare.py` | **Three-way FLASH / kinetic / hybrid comparison** on the normalised axes, plus the A1-A8 table | FLASH delivery + two run dirs | `media/xcode/{profiles,history}.png` | **built** |
| `talk_xcode.py` | The same series, two or three large panels for a slide. Imports `xcode_compare`, so it cannot drift from it | same | `media/xcode/talk_ablation.png` | **built** |
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
scripts/launch.sh runs/P1/P1_vac_1d              # foreground, logs to the run dir
scripts/launch.sh -b -L runs/P1/P1_vac_1d        # detach + start the progress logger
scripts/launch.sh -n runs/P1/P1_vac_1d           # dry run: print the command, change nothing
scripts/launch.sh -f runs/P1/P1_vac_1d           # overwrite a populated diags/ (mean it)
scripts/launch.sh runs/P1/P1_vac_1d -- max_step=20   # ParmParse overrides: smoke tests only
```

Overrides after `--` are not reflected in `config.yaml`, so `make_inputs.py --verify` will
flag them afterwards. Use them for smoke tests, not physics.

## `queue_run.sh`

A queue of one: wait until named runs are finished and named GPUs are idle, then run
`launch.sh` with whatever arguments you give it after `--`.

```bash
scripts/queue_run.sh -a ../KinShock2020/runs/implicit_phase/i0_implicit_cfl075 \
                     -a ../KinShock2020/runs/implicit_phase/i1_explicit_villasenor \
                     -G 0,1 runs/P1/P1_vac_2d_spot_abl -- -b -L --gpu 0,1
```

Three decisions in it are worth knowing, because each replaces something that fails:

- **"Finished" is the absence of a process with that cwd, not `DONE` in `progress.log`.**
  A run that was killed, or never launched, never writes `DONE`, and a queue waiting for a
  string that will never appear waits forever. Reading `/proc/<pid>/cwd` also cannot match
  the queue's own command line, which is the trap `pkill -f` falls into.
- **The GPU test is separate from the run test.** This is a shared machine: a run
  directory can be idle while its card is still held by somebody else, and launching into
  that gets the new run starved or OOM-killed. Idle means under `$GPU_IDLE_MIB` (600) and
  no compute apps.
- **`--orphan-timeout` (default 2 h) is the one judgement call.** Queue behind a run that
  is never launched and strict waiting means yours never starts. So once everything else
  is clear, a *never-started* `--after` directory is waited on for that long and then
  given up on, loudly, in the log. A run that has started is never given up on.

Redirect the output and detach it (`nohup ... > queue.out 2>&1 &`); the log is the only
record of why it did or did not fire. **Kill it by PID**, never `pkill -f queue_run`.

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
python scripts/run_progress_logger.py runs/P1/P1_vac_1d --every-pct 5 --poll 20
```


---

## `plot_rays.py`

**The only view of where the beam goes**, as opposed to where its energy landed. Both
operator bugs found so far were ray-path bugs — the transverse index clamp and the
exit-boundary overshoot — and both had to be inferred from spatial deposition profiles
because nothing drew the paths.

```bash
/opt/anaconda3/envs/physics/bin/python scripts/plot_rays.py runs/P1/P1_vac_2d_spot
... scripts/plot_rays.py runs/P1/P1_vac_2d_spot --time 5.0 --rays 40
```

2D only (in 1D the path is the z axis). Inbound legs are green, outbound dashed blue,
turning points marked on the critical contour, cropped to the interaction region.

Two things to hold onto when reading it:

1. **It is a reconstruction, not the operator's output.** It re-integrates the same eikonal
   equation with the same RK4 marcher, multilinear sampling, `n_floor` threshold and
   wrap/clamp index mapping as `LaserDeposition.cpp`, on the `n_e` a plotfile dumped. That
   makes agreement with the operator's own ray dump a real cross-check, and a disagreement a
   bug in one of the two — not automatically this one.
2. **No absorption is carried**, because the IB coefficient needs the per-cell `T_e` the
   operator builds from the momentum moments and that is not in the plotfiles. So no ray is
   extinguished, and the outbound leg is *the path a ray would fly*, not evidence that power
   came back out. At `tau` = 1411 through the flat top of the P1 target, essentially none
   does. **Never read an absorbed fraction off this figure.**

A detail worth knowing, because it produced a wrong figure first time round: the operator's
explicit specular branch fires only at `n_ref <= n_floor`, i.e. within 1e-4 of critical, and
at normal incidence a ray is turned by ordinary refraction *before* it gets that close. In
`P1_vac_2d_spot_omp` exactly 1 ray of 25 enters that branch while all 25 turn around.
Counting the branch as "the turning point" reports 1/25 for a bundle in which every ray
turns; the script marks the axial sign change instead and reports the branch separately.

## `spot_report.py`

**The only script that keeps the transverse direction.** Every other analysis here reduces `x`
away, which is right for a planar run -- there, transverse structure is noise or a bug -- and
useless for a finite spot, where it is the subject.

```bash
python scripts/spot_report.py runs/P1/P1_vac_2d_spot
python scripts/spot_report.py runs/P1/P1_vac_2d_spot --baseline runs/P1/P1_vac_1d_thick
```

Three things it measures, in order of how much trouble they save:

1. **`f_ax`, the on-axis local absorbed fraction** (absorption inside `|x| < w0/4` divided by the
   incident power in those same columns). Quote **this**, not the whole-beam `f_abs`, against a 1D
   run. The whole-beam figure mixes two opposite finite-spot effects: lateral rarefaction lowers
   coupling, while the cooler wings (lower `I`, so less heating, so higher `K` proportional to
   `T_e^-3/2`) raise it -- and at early times the second one wins, so a Gaussian reads *above* a
   flat-top of the same peak intensity. That is not the drive being better.
2. **`w_eff(t)`**, the second-moment width of the absorbed-power profile, normalised so a
   `exp(-(x/w)^2)` beam returns `w`. This is the lateral-spreading rate H5 is about.
3. **The edge-column share, as a standing regression test** for the transverse-wrap fix
   (`warpx-cda` c817b63). An unilluminated wall must carry `exp(-(x_wall/w0)^2)` and nothing more;
   the script prints that prediction next to the measurement. The bug the fix removed only switched
   on *after* structure developed (3.2 % of absorption in the edge columns at `t` = 0 -> 98.8 % at
   26.9 ps), so a step-0 check cannot catch a regression -- which is why the whole dump series is
   tracked, and why a finite-spot run doubles as the regression test for free.

Two implementation notes that were bugs first:

- **The dumps are written box by box, not row-major.** The operator gathers the field to one rank
  and walks its `MFIter`, so the row order is the AMReX box decomposition. Reshaping to `(nx, nz)`
  silently transposes patches of the domain; the reader scatters by rounded cell index instead, and
  refuses to continue if the cell count does not match the grid.
- **A column integral of `P_abs` is W per metre**, matching `laserprod.io.incident_power`'s 2D
  convention, so only the dimensionless ratio is comparable to 1D. `incident_power` already
  integrates the Gaussian profile over the face, so `f_abs` is correct for a spot deck with no
  special-casing.

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


## `g3_spot.py` — G3 where the light actually went

The standard G3 subtraction uses the `ParticleEnergy` reduced diagnostic, which is a
whole-domain total. For a **finite spot** that is structurally unfair: `P1_vac_2d_spot` drives
a `w₀` = 20 `d_e` beam inside a ±80 `d_e` box, so ~78 % of the transverse extent is never lit.
The driven gain is diluted by the dark region while grid heating — a property of the grid and
the ppc, not of the beam — fills the whole box, so the whole-box ratio overstates the control.

This script re-computes the same quantity from the plotfiles, which have positions, and reports
three regions: **illuminated** (`|x−x_c| < waists·w₀`), **dark** (`> 2.5 w₀`, where the beam
puts 0.04 % of its power at `t` = 0 — so it is a control-free grid-heating measure), and
**whole box** (so the effect of restricting is visible rather than asserted).

```bash
python scripts/g3_spot.py runs/P1/P1_vac_2d_spot --control runs/P1/P1_vac_2d_spot_off
```

**Two self-tests run every time, and both must be read before quoting the restricted number:**

1. **the whole-box column must reproduce `ParticleEnergy`.** It does, to **0.000 %**
   (+60.258 and −1.8615 J/m on the `P1_vac_2d` pair). An independent code path measuring the
   same thing is the only reason to believe the restricted column.
2. **a `profile: uniform` run must give the same G3 in every region.** On `P1_vac_2d` the three
   regions spread **0.02 percentage points**. Run it on the planar pair after any change here.

### Two traps this script exists downstream of

* `lpio.plotfiles(rd)` **with no prefix** matches `diag1*`, `diag_fields*` and `diag_phase*`
  alike, so a `{step: path}` dict keeps whichever sorted last. Pass `--prefix` (default
  `diag1`, the only family with the full particle record).
* a particle-field read wrapped in `except: continue` contributes **zero** when the field is
  absent. That is how the family mix-up first presented: a confident, smooth, *positive*
  control ratio of +17.16 %, i.e. apparent grid heating, instead of −3.09 %. Missing species
  and missing fields are now hard errors naming the fix.


## `spot_isolation.py` — is the finite spot still finite?

With periodic transverse faces a localized-heating run is really an infinite **array** of spots at
pitch `L_t`. Once heat has crossed `L_t/2` the array merges and the result is planar physics with
extra steps — and nothing announces it: every gate passes and energy is conserved.

```bash
python scripts/spot_isolation.py runs/P1/P1_vac_2d_spot --control runs/P1/P1_vac_2d_spot_off
```

It bands the transverse axis and reports the **net** absorbed energy per band — the driven
particle-KE gain minus the laser-off control's boundary drain, so the boundary drain cannot
masquerade as structure — then `dark/lit`: **< 0.2 isolated, 0.2–0.5 marginal (quote it), > 0.5
effectively planar**. It also prints the box a valid run of that duration would need.

**The timescale is `v_th,e`, not `c_s`** — a factor ~10. On `P1_vac_2d_spot`: `c_s` said the box
would last 45 ps, `v_th,e` said 2.1 ps, and the measurement lost contrast after **1.99 ps**. Sizing
rule: `L_t/2 ≳ v_th,e(T_e,corona)·t_end + w₀`.
