# Running LaserProdShock Phase 5 on Perlmutter (NERSC)

> **Status 2026-08-29. Ported, not yet executed.** The structure here is
> `KinShock2020/perlmutter/`, which *was* verified against the real machine on 2026-08-11
> (account `m5032_g`, `$PSCRATCH=/pscratch/sd/h/hhelal`, QOS table via `sbatch --test-only`).
> What is unverified for *this* project is the build and the first submission — treat the
> `raycfl` array as the shakeout, which is what it is for anyway.

## Why P5 moves off chablis

Not per-GPU speed. An A100 is maybe 1.5–2.5× an RTX 4070 on these decks. **The win is
concurrency.** P5 is seven long legs of 6–20 h each plus a four-rung ladder. On chablis's
two 4070s that is roughly 60 h of serial wall clock; on Perlmutter every leg is its own
single-GPU array task and the wall clock is **the longest single run**, ~8–13 h.

Single-GPU is not a compromise: every P5 config sets `numerics.max_grid_size = n_cell`,
i.e. **one box**, and one box cannot be split across ranks. It is also the *fastest* 1D
configuration — 7.9× over the default decomposition (project memory). More GPUs would idle.

## `warpx-cda` provenance — resolved 2026-08-29

The chablis clone had sat 7 commits ahead of `origin/feature/hybrid-laser` (all
`HybridPICModel` and docs; none touching `LaserDeposition` or `Initialization`). They are
**pushed**: `fcb48c9fe..534f3b170`. The two clones now agree, and `site.conf.example` pins
`WARPX_COMMIT=534f3b170`, so a fresh Perlmutter clone builds exactly the code P4 was
measured on.

## One-time setup

```bash
# 1. profile (upstream's; edit line 2 -- proj must end in _g)
cp $PSCRATCH/warpx-cda/Tools/machines/perlmutter-nersc/perlmutter_gpu_warpx.profile.example \
   $HOME/perlmutter_gpu_warpx.profile
vi $HOME/perlmutter_gpu_warpx.profile
source $HOME/perlmutter_gpu_warpx.profile

# 2. dependencies (boost, c-blosc, adios2, blaspp, lapackpp). Slow, idempotent, once.
bash $PSCRATCH/warpx-cda/Tools/machines/perlmutter-nersc/install_gpu_dependencies.sh

# 3. both repos on $PSCRATCH -- NOT $HOME (quota'd, not for parallel I/O)
cd $PSCRATCH
git clone git@github.com:Schaeffer-Lab/warpx-cda.git
git clone <this repo's remote> LaserProdShock

# 4. site config
cd $PSCRATCH/LaserProdShock
cp perlmutter/site.conf.example perlmutter/site.conf
vi perlmutter/site.conf                    # NERSC_ACCOUNT and paths; WARPX_COMMIT is already right
```

⚠ Lustre striping: WarpX plotfiles are many small files, and P5 writes **45 per long leg**
against P4's 5. If write time shows up in `progress.log`, `stripe_medium
$PSCRATCH/LaserProdShock/runs` before the first run.

## The FLASH delivery is a dependency, and it is on chablis

`scripts/flash_ic_fit.py`, `flash_absorption.py`, `ic_optical_depth.py` and
`xcode_trajectory.py` all read `~/shared/simulations/FLASH_LaserAblation-Ploegstra_2026-08/`.
**The decks do not** — that is the whole point of `ic_flash.yaml` being a tracked node table
rather than a live read. So:

* **running** P5 on Perlmutter needs no FLASH data at all;
* **re-fitting an IC** or **running the trajectory comparison** needs either the delivery
  copied over (36 MB, `lez1d_hdf5_plt_cnt_*` and `lez1d_LaserEnergyProfile.dat`) or those
  steps done on chablis.

Copying is easier and the minimal set is **7.6 MB**, not the delivery's 36. From chablis:

```bash
D=~/shared/simulations/FLASH_LaserAblation-Ploegstra_2026-08/Ablation_prod_08-17
rsync -av $D/lez1d_hdf5_plt_cnt_* $D/lez1d_LaserEnergyProfile.dat \
      perlmutter.nersc.gov:$PSCRATCH/flash_lez1d/
```

Then on Perlmutter, **no source edit** — the path is an env var:

```bash
export LP_FLASH_DIR=$PSCRATCH/flash_lez1d
```

`xcode_compare.py`, `flash_absorption.py`, `ic_optical_depth.py`, `flash_ic_fit.py` and
`xcode_trajectory.py` all read it. Editing a hardcoded path on a second machine is how two
clones start disagreeing about what they measured.

## Build

```bash
perlmutter/build_warpx.sh
```

Detached HEAD at `WARPX_COMMIT`, so the binary's provenance is a SHA. The script then
**greps the binary for every input key P5 depends on** — including
`maxwellian_u_std_distribution_type` and `maxwellian_u_mean_distribution_type`, which the
lifted-IC legs need for their temperature and drift profiles. A binary predating a deck's
flag **ignores it silently**; that cost 4.6 h once on chablis, and here it would cost a
20-hour array task.

## Submit

```bash
perlmutter/submit.sh raycfl --qos debug --time 00:30:00   # FIRST -- the G4 gate
perlmutter/submit.sh spine                                 # the headline + control + A/B
perlmutter/submit.sh ladder                                # handoff-time sensitivity
perlmutter/submit.sh cap                                   # hold until the spine reports
perlmutter/submit.sh spine --dry                           # print sbatch, submit nothing
```

**QOS — from KinShock2020's `--test-only` measurement, 2026-08-11:**

| QOS | resources | max wall | max jobs | would start |
|---|---|---|---|---|
| `shared` | 1 GPU / 32 cores | 2 d | 5000 | **+11 h** |
| `debug` | whole node | **30 min** | **5** | **+5 h** |
| `regular` | whole node | 2 d | 5000 | **+6 days** |

`shared` is right for every long leg: it bills per-GPU, and these runs are single-GPU by
construction. `regular` is six days deep *and* wastes three of four GPUs per task.

**Put the `raycfl` ladder in `debug`.** Four ~2-minute runs fits its 5-job and 30-minute
caps exactly and starts hours sooner. `submit.sh` refuses `--qos debug` past either cap
rather than letting you discover it after the wait.

`submit.sh` also pre-flights every leg for a config, a **README** (the project's second
rule, enforced here as `scripts/launch.sh` enforces it on chablis), a deck, and — for a
lifted-IC run — its `ic_flash.yaml`. Catching a missing table costs a second here and a
queue wait inside an array task.

## Recommended order

1. **`raycfl`**, in `debug`. It gates the phase: `ray_cfl = 0.25` is documented
   non-monotonic for turning-point problems, and 41 % of the IC's optical depth sits at the
   turning point. Minutes.
2. **`spine`** — `P5_seed` (0.3 ns, finishes first and surfaces mistakes cheaply),
   `P5_flashic`, `P5_flashic_off`, `P5_full`. Four tasks, one wall clock.
3. **`ladder`** — the two handoff rungs, both cheaper than the spine.
4. **`cap`** — after the spine reports.

In parallel and off-machine: the two **FLASH collaborator reruns** (`lrefine_max` 5/6 and
`diff_eleFlCoef` 0.03/0.12), which cost *seconds* each and can move the benchmark's anchor.
See `runs/P5/README.md` F1/F2.

## Reading the results

```bash
python3 scripts/make_inputs.py runs/P5/<ID> --verify        # config == what ran
python3 scripts/run_checks.py  runs/P5/<ID>                 # gates G1-G7
python3 scripts/laser_report.py runs/P5/<ID>                # E_abs, f_abs -- the ladder
/opt/anaconda3/envs/physics/bin/python scripts/xcode_trajectory.py \
    runs/P5/P5_flashic --g3 runs/P5/P5_flashic_off --band runs/P5/P5_seed
```

The last one needs the FLASH delivery present (see above) and is the phase's headline
output: the ratio-versus-τ curve with a fitted `dlnR/dτ`, so "flat" is measured.

## Two things to keep straight

**WarpX on GPU is not reproducible**, fixed seed or not — `ablastr/math/RandomSeed.H` says
so outright, and two runs of one deck confirmed it on chablis. `P5_seed` sets a *different*
seed deliberately so the replicate measures the seed and not nondeterminism; do not read a
single-run difference below the band it returns.

**`diags/` lands in the launch CWD.** The decks set no `diag*.file_prefix`, so `run_warpx`
cd's into the run directory first and refuses to start over existing output. Never `srun`
the binary by hand from a shared directory — two runs will clobber each other, which has
already cost this group a rerun.
