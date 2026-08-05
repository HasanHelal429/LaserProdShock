# `runs/` — one directory per simulation, grouped by phase

**Layout is `runs/<phase>/<run_id>/`** — `runs/P0/P0_bc_open/`, `runs/P1/P1_vac_1d/`, and so
on. A flat directory stopped being readable at ~10 runs; the phase prefix already encoded the
grouping, so this just makes it a directory. `media/` mirrors it: `media/<phase>/<run_id>/`,
derived automatically from the run-ID prefix by `laserprod.plotting.media_dir`, so no script
has to be told the phase.

Nothing else changes: every script still takes a path to a run directory, `launch.sh` still
cd's into it, and `config.yaml` still carries `meta.run_id` (the directory name is not the
source of truth for the ID).

Each run directory holds:

| File | Tracked? | What |
|---|---|---|
| `config.yaml` | **yes** | the single source of truth (`CLAUDE.md`) |
| `README.md` | **yes** | what this run is — **required**, see below |
| `inputs_<id>` | yes | the generated deck. A build artifact; never hand-edit it |
| `warpx_used_inputs` | yes | what WarpX actually parsed; `make_inputs.py --verify` diffs it |
| `shock_fit.yaml` | yes | by-eye `v_sh` + front fit, for shock runs only |
| `diags/`, `*.log`, `logger.out` | no | gitignored, regenerable |
| `progress.log` | yes | wall-clock cost record from the progress logger |

## `README.md` is required

`scripts/launch.sh` **refuses to start a run that has no `README.md`.** The reason is
concrete: upstream, a laser-driven "marginally supercritical shock" was reported and later
retracted, because the run's density and B streaks looked shock-like and nothing recorded
what had and had not been checked. A run that cannot say what it was for cannot be trusted
later, and cannot be retracted cleanly either.

Write the top half **before** launching (it is the hypothesis), the bottom half after.

### Template

```markdown
# <RUN_ID> — <one-line what-it-is>

**Phase.** <0 | 1 | 2 | 3>, `TEST_PLAN.md` §<n>
**Question.** <the single question this run answers>
**Expected.** <what should happen if the hypothesis holds, with numbers>
**Falsified by.** <what observation would say the hypothesis is wrong>

## Geometry
<paste the GENERATED diagram -- never hand-draw it:

    python scripts/make_inputs.py runs/<phase>/<ID> --diagram

It is built from config.yaml (target slab, coronal ramp, ambient fill, boundary condition
per face, which face the laser enters, transverse extent in 2D, B0 axis, grid and
duration), so it cannot drift away from what the deck actually builds.

A 1D run renders as an axial strip. A 2D or 3D run renders as a real map of the x-z plane:
all four boundaries labelled, the target drawn per transverse row (so `shape: curved` shows
its displaced face and `shape: finite_width` shows its edges), and the beam drawn on the
injection side with bar length proportional to the LOCAL intensity. That last part is the
point for a finite-spot run -- the target is uniform in x while the beam is not, so an axial
strip draws the one thing a spot run is not about and omits the one thing it is. Re-render
every 2D README after touching the generator; the block under `## Geometry` is the only
thing that changes.>

## Setup
<what differs from its parent run, and why. Link the parent by ID. Densities in n_cr,
lengths in d_e,ref (say which), speeds in c or v_A (say which).>

## Cost
<cells x ppc x steps, wall time at 8 threads, from progress.log>

## Gates
| Gate | Value | Pass? |
|---|---|---|
| G1 `omega_pe dt` at peak density | | |
| G2 `dz/lambda_D` (target / ambient) | | |
| G3 laser-off control | | |
| G4 `ray_cfl` check | | |
| G5 ppc / `Tlocalfrac` | | |
| G6 energy closure | | |

## Result
<what happened. Numbers, not adjectives.>

## Retracted
<anything previously claimed from this run that is now known to be wrong, and why.
"nothing" is a valid entry. Never silently delete a wrong claim -- move it here.>
```

## Run-ID scheme

`<phase><letter?>_<what>` — phase first so `ls` sorts the campaign in order.

| Prefix | Phase | Examples |
|---|---|---|
| `P0_` | boundaries and geometry | `P0_bc_periodic`, `P0_bc_open`, `P0_bc_open_B`, `P0_bc_inject`, `P0_bc_2d` |
| `P1_` | ablation into vacuum | `P1_vac_1d`, `P1_vac_1d_off`, `P1_vac_2d`, `P1_vac_2d_spot` |
| `P2_` | piston into ambient | `P2_unmag`, `P2_mag`, `P2_mag_2d` |
| `P3_` | one-off sweep points kept for the record | `P3_I1e19` |

Suffix conventions:

- `_off` — **the laser-off control** (gate G3): an otherwise identical deck with the laser
  disabled, run for the same duration, so grid heating can be subtracted from laser
  heating. Mandatory alongside every headline Phase-1/Phase-2 run.
- `_1d` / `_2d` — dimensionality, when a run exists in both.
- `_fine` — a higher-resolution or higher-ppc variant of the same physics.

Systematic sweeps live in `studies/`, not here — only sweep points worth keeping as
standalone references get promoted to a `runs/P3/P3_*` directory.

### `_long` — an extended-duration variant

`P1_vac_1d_long` is `P1_vac_1d` run 10× longer. Two rules learned the hard way when making
one:

- **The domain must grow with the duration.** `P1_vac_1d`'s rear expansion reached its wall at
  t ≈ 7.5 ps of a 10 ps run, so simply raising `max_step` would have bled the plume into the
  boundary for 90 % of a 100 ps run and voided gate G6. Size the new domain from the
  **measured** ion-weight quantile drift of the short run, not from a guess.
- **Scale the `diagnostics:` intervals by the same factor**, so you get the same number of
  dumps rather than 10× the data. But **`laser.intervals` is NOT a diagnostic** — it is the
  deposition cadence, and the kick amplitude goes as `√(H·Δt)` with `Δt = intervals·dt`, so
  changing it changes the physics. Leave it alone.

A `_long` run needs its **own** `_long_off` control: grid heating accumulates with step count,
so a shorter control cannot bound a longer run.
