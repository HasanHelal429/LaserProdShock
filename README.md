# LaserProdShock

Testing the WarpX **ray-tracing laser-deposition module** as a **shock driver**.

`../KinShock2020/` replicated Schaeffer et al. 2020 (piston-driven perpendicular magnetized
collisionless shock) with a *prescribed* piston — a `ParticleHeater` + `TargetInjector`
surrogate for laser ablation. This project replaces the surrogate with an **actual
ray-traced laser** (`warpx-cda/Source/Particles/LaserDeposition/`, a port of Hyder et al.,
Comput. Phys. Commun. 318, 109419) and asks what it takes to drive a real shock that way.

**The question.** *Can a ray-traced laser drive a piston that produces a verifiable
collisionless shock in WarpX, and what does the laser have to be for that to happen?*

**Status.** Phase-0 tooling built and the five boundary/geometry runs are executing. The
config schema, deck renderer, gates G1–G7 and the laser diagnostics all work in 1D and 2D;
71 tests pass. See `TEST_PLAN.md` §11 for the checklist and `RESULTS.md` for current state.

## The campaign

| Phase | Question |
|---|---|
| **0** | What boundary conditions and geometry are admissible at all? (periodic fields force periodic particles; a runaway ablation front then wraps) |
| **1** | Does the laser ablate a target correctly into vacuum — in 1D, and does 1D describe the 2D reality? |
| **2** | Does the piston couple to an ambient plasma, unmagnetized (negative control) and magnetized (the shock)? |
| **3** | How do absorbed fraction, coupled energy, piston speed and `M_ms` depend on laser power and geometry? |

The one prior attempt at a laser-driven shock produced a **freely-propagating fast
magnetosonic pulse, not a shock**, and an earlier "marginally supercritical shock" reading
from it was retracted. That retraction is why this is a structured campaign with a
mandatory phase-space check rather than a single run. See `OVERVIEW.md` §5.

## Documents

| File | What it is |
|---|---|
| `TEST_PLAN.md` | **The plan** — phases, runs, numerical gates, scaling hypotheses. Start here. |
| `OVERVIEW.md` | Physics reference: the eikonal/IB model, the deposition kernel, the shock physics. |
| `RESULTS.md` | The running lab notebook — dated entry per run/finding. |
| `CLAUDE.md` | Enforced project rules and the accumulated gotchas. |
| `runs/README.md` | Run-ID scheme and the per-run `README.md` template. |
| `scripts/README.md` | Tool docs and build status. |

## Layout

```
src/laserprod/     the package: units, config, deck, io, metrics, plotting
scripts/           driver + analysis CLIs; launch.sh is the only way to start a run
runs/<ID>/         config.yaml + README.md + deck (tracked); diags/, *.log (ignored)
studies/           heavier experiments that launch WarpX (the Phase-3 sweeps)
tests/             fast pytest checks
media/<ID>/        figures and movies (ignored, regenerable)
```

## Rules that are actually enforced

1. **`runs/<ID>/config.yaml` is the single source of truth.** `scripts/make_inputs.py`
   renders the deck; never hand-edit a deck. `--verify` diffs `warpx_used_inputs` against
   the config after a run.
2. **Every run directory has a `README.md`.** `launch.sh` refuses to start without one.
3. **Phase space decides what is a shock.** No shock claim without `phase_space.py`.
4. **`scripts/launch.sh` is the only way to start a run** — it cd's into the run dir so
   `diags/` cannot be clobbered, and picks `warpx.1d`/`warpx.2d` from `geometry.dims`.

## Quickstart

```bash
python scripts/make_inputs.py runs/<ID>          # config.yaml -> deck
scripts/launch.sh -b -L      runs/<ID>          # detach + progress logger
python scripts/run_checks.py runs/<ID>          # derived scales + gates G1-G7
```

Built: the whole Phase-0 chain above, plus `laser_report.py`. Phase 1–3 analysis
(`phase_space.py`, `tune_shock.py`, `make_figures.py`, `sweep.py`) is still to come —
`scripts/README.md` carries the status table.

**Environment.** conda env `/opt/anaconda3/envs/physics`; WarpX at
`/home/hhelal/warpx-cda/build/bin/warpx.{1d,2d,3d}` (OMP/CPU, double precision).
Override with `$LPS_WARPX` (a binary) or `$LPS_WARPX_DIR` (the directory).
