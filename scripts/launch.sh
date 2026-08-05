#!/bin/bash
# scripts/launch.sh -- the ONE correct way to start a WarpX run in this repo.
#
# Ported from KinShock2020/scripts/launch.sh, with one addition: this project runs
# BOTH 1D and 2D, so the WarpX binary is chosen from the run's `geometry.dims`
# instead of being hard-coded to warpx.1d.
#
# WHY THIS SCRIPT EXISTS. The generated deck sets no `diag*.file_prefix`, so WarpX
# writes plotfiles to `diags/` RELATIVE TO THE LAUNCH CWD. Launching two runs from
# the repo root makes them share ./diags/ and clobber each other (WarpX leaves
# .old.NNNN rename files as the tell) -- that cost a rerun of two control runs in
# KinShock2020 (RESULTS 2026-07-26). This script always cd's into the run dir first,
# so diag1/diag_fields/reducedfiles/laserdep_profile_* land under runs/<ID>/diags/.
#
# Also applies the benchmarked thread settings (KinShock2020 RESULTS 2026-07-23:
# near-linear to 8 cores, ~1.8x vs 4, memory-bandwidth-bound beyond; max_grid_size,
# tiling and sort_intervals were neutral-to-negative -- don't bother).
#
# Usage:  scripts/launch.sh [options] <run_dir> [-- <warpx args>]
#
#   -j, --threads N    OMP_NUM_THREADS (default 8; forced to 1 with --gpu)
#   -w, --warpx PATH   WarpX binary (default: $LPS_WARPX, else picked from geometry.dims)
#   -g, --gpu [N|L]    run the CUDA build on GPU N (default 0), or on a comma list
#                      such as `-g 0,1` for ONE run spread over both cards via MPI
#   -b, --background   detach and return immediately (prints the PID)
#   -L, --logger       also start scripts/run_progress_logger.py in the background
#   -f, --force        launch even though diags/ already holds output (see below)
#   -n, --dry-run      print what would run, change nothing
#
# --gpu picks the binary out of the CUDA build tree instead of the OMP one, pins the run
# to a single device with CUDA_VISIBLE_DEVICES, and sets OMP_NUM_THREADS=1 (with the CUDA
# backend the particle push is on the device; host threads only add contention). There
# are two RTX 4070s on this machine, so `-g 0` and `-g 1` can carry two runs at once.
#
# `-g 0,1` instead puts ONE run across both, as one MPI rank per device. Two things to
# know before using it. (1) The laser operator gathers the whole density onto a single
# box and ray-traces on the rank that owns it (others get an empty MFIter), then scatters
# the heating rate back -- so it is CORRECT under MPI, but the ray march does not
# parallelise and stays on one rank. Since Phase 1.5 that is only ~6 % of a step, so
# little is lost. (2) AMReX balances CELLS, not particles. In an ablation deck the plasma
# is a slab at one end of a long vacuum domain, so a decomposition that cuts the
# propagation axis gives one rank nearly every macroparticle. Set
# `numerics.max_grid_size` to cut the TRANSVERSE axis only (a planar target is uniform
# in x, so that split is exactly balanced) -- and this script refuses to spread a run
# over several devices unless the deck pins the decomposition, because the default one
# silently wastes a card.
#
# WarpX_DIMS is a COMPILE-time setting, so the CUDA build is one tree PER DIMENSIONALITY:
#   build_cuda1d/bin/warpx.1d      build_cuda/bin/warpx.2d
# --gpu therefore searches $LPS_WARPX_DIR_CUDA, then build_cuda<D>d/bin, then
# build_cuda/bin, and names the missing tree if it finds nothing. The CUDA and OMP builds
# are both double precision but are NOT bit-identical: device reductions run in a
# different order, so cross-checking a GPU run against a CPU one is a physics comparison,
# not a diff.
#
# Anything after `--` is appended as ParmParse overrides, e.g.
#   scripts/launch.sh runs/P0_bc_1d -- max_step=20
# NOTE overrides are not reflected in config.yaml, so `make_inputs.py --verify` will
# flag them afterwards. Use them for smoke tests, not for physics.
#
# Stdout/stderr go to <run_dir>/run.log (gitignored; findings belong in RESULTS.md).
#
# Refuses to start when diags/ is already populated, because relaunching overwrites a
# finished run's plotfiles in place -- pass --force once you mean it, or move the old
# diags/ aside. Run `make_inputs.py <run_dir> --check` first if the deck may be stale.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WARPX_ROOT="${LPS_WARPX_ROOT:-/home/hhelal/warpx-cda}"
WARPX_DIR="${LPS_WARPX_DIR:-$WARPX_ROOT/build/bin}"
WARPX="${LPS_WARPX:-}"          # empty => resolve from geometry.dims below
THREADS=8
GPU=""                          # empty => CPU/OMP build; else the device index
BACKGROUND=0
LOGGER=0
FORCE=0
DRYRUN=0
RUN_DIR=""
EXTRA=()

die() { echo "launch: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --)              shift; EXTRA=("$@"); break ;;
        -j|--threads)    THREADS="${2:-}"; shift 2 ;;
        -w|--warpx)      WARPX="${2:-}";   shift 2 ;;
        -g|--gpu)        # optional argument: a device index, or a comma list of them
                         if [[ "${2:-}" =~ ^[0-9]+(,[0-9]+)*$ ]]; then GPU="$2"; shift 2
                         else GPU=0; shift; fi ;;
        -b|--background) BACKGROUND=1; shift ;;
        -L|--logger)     LOGGER=1;     shift ;;
        -f|--force)      FORCE=1;      shift ;;
        -n|--dry-run)    DRYRUN=1;     shift ;;
        -h|--help)       sed -n '2,56p' "${BASH_SOURCE[0]}"; exit 0 ;;
        -*)              die "unknown option '$1' (try --help)" ;;
        *)               [[ -n "$RUN_DIR" ]] && die "one run_dir at a time (got '$RUN_DIR' and '$1')"
                         RUN_DIR="$1"; shift ;;
    esac
done

[[ -n "$RUN_DIR" ]] || die "usage: scripts/launch.sh [options] <run_dir>"
[[ -d "$RUN_DIR" ]] || die "no such run dir: $RUN_DIR"
RUN_DIR="$(cd "$RUN_DIR" && pwd)"                       # absolute: we are about to cd
[[ -f "$RUN_DIR/config.yaml" ]] || die "$RUN_DIR has no config.yaml -- is it a run dir?"

# Every run dir must document itself (see CLAUDE.md / runs/README.md).
[[ -f "$RUN_DIR/README.md" ]] || die "$RUN_DIR has no README.md -- every run must describe
     itself before it is launched (see runs/README.md for the template)."

# --- WarpX binary: 1D and 2D are both first-class here, so pick by dimensionality ---
DIMS="$(sed -n 's/^[[:space:]]*dims:[[:space:]]*\([0-9]\).*/\1/p' "$RUN_DIR/config.yaml" | head -1)"
if [[ -z "$WARPX" ]]; then
    [[ -n "$DIMS" ]] || die "could not read geometry.dims from $RUN_DIR/config.yaml
     (add it, or pass --warpx / set \$LPS_WARPX)"
    if [[ -n "$GPU" ]]; then
        # WarpX_DIMS is compile-time, so the CUDA build is one tree per dimensionality.
        # `build_cuda_omp` comes FIRST for 2D: it is the same source configured
        # -DAMReX_OMP=ON, which is the only way `_OPENMP` is defined and therefore the
        # only way the threaded ray march (Phase 1.5) is anything but inert. It is a
        # separate tree so that build_cuda stays a valid fallback.
        for d in "${LPS_WARPX_DIR_CUDA:-}" \
                 "$WARPX_ROOT/build_cuda${DIMS}d_omp/bin" "$WARPX_ROOT/build_cuda_omp/bin" \
                 "$WARPX_ROOT/build_cuda${DIMS}d/bin" "$WARPX_ROOT/build_cuda/bin"; do
            [[ -n "$d" && -x "$d/warpx.${DIMS}d" ]] && { WARPX="$d/warpx.${DIMS}d"; break; }
        done
        [[ -n "$WARPX" ]] || die "no CUDA warpx.${DIMS}d found. The CUDA build is one tree
     per dimensionality (WarpX_DIMS is compile-time), so ${DIMS}D needs
     $WARPX_ROOT/build_cuda${DIMS}d. Build it with:
       PATH=/home/hhelal/opt/cuda-12.9/bin:\$PATH cmake -S $WARPX_ROOT \\
         -B $WARPX_ROOT/build_cuda${DIMS}d -DCMAKE_BUILD_TYPE=Release \\
         -DWarpX_DIMS=${DIMS} -DWarpX_COMPUTE=CUDA -DAMReX_CUDA_ARCH=8.9 \\
         -DWarpX_PRECISION=DOUBLE -DWarpX_PARTICLE_PRECISION=DOUBLE
     (the SYSTEM nvcc is 12.0 and AMReX requires >= 12.2 -- use the 12.9 toolkit in
     ~/opt, which is what build_cuda was built with), or pass --warpx / \$LPS_WARPX."
    else
        WARPX="$WARPX_DIR/warpx.${DIMS}d"
    fi
fi
[[ -x "$WARPX" ]] || die "WarpX binary not executable: $WARPX (set --warpx or \$LPS_WARPX)"

# A CUDA binary on a machine with no visible device fails deep inside AMReX init; catch it
# here where the message can say what to do.
NRANKS=1
if [[ -n "$GPU" ]]; then
    command -v nvidia-smi >/dev/null || die "--gpu but no nvidia-smi on PATH"
    NGPU="$(nvidia-smi --list-gpus 2>/dev/null | wc -l)"
    [[ "$NGPU" -gt 0 ]] || die "--gpu but nvidia-smi lists no devices"
    IFS=',' read -r -a GPULIST <<< "$GPU"
    NRANKS=${#GPULIST[@]}
    for g in "${GPULIST[@]}"; do
        [[ "$g" -lt "$NGPU" ]] || die "--gpu $GPU names device $g but only $NGPU \
device(s) present (0..$((NGPU-1)))"
    done
    # A repeated index would put two ranks on one card, which is a mistake every time.
    if [[ "$(printf '%s\n' "${GPULIST[@]}" | sort -u | wc -l)" -ne "$NRANKS" ]]; then
        die "--gpu $GPU repeats a device index"
    fi
fi

# Exactly one deck, so we never guess which input file was meant.
shopt -s nullglob
DECKS=("$RUN_DIR"/inputs_*)
shopt -u nullglob
case ${#DECKS[@]} in
    0) die "no deck in $RUN_DIR -- run: python scripts/make_inputs.py $RUN_DIR" ;;
    1) DECK="$(basename "${DECKS[0]}")" ;;
    *) die "$RUN_DIR has ${#DECKS[@]} decks (${DECKS[*]##*/}) -- keep one" ;;
esac

if [[ -d "$RUN_DIR/diags" ]] && compgen -G "$RUN_DIR/diags/*" >/dev/null; then
    if [[ $FORCE -eq 1 ]]; then
        echo "launch: --force, writing into the existing $RUN_DIR/diags"
    elif [[ $DRYRUN -eq 1 ]]; then
        echo "launch: WARNING $RUN_DIR/diags already has output -- a real launch would"
        echo "launch:         refuse this without --force."
    else
        die "$RUN_DIR/diags already has output -- relaunching overwrites it in place.
     Move it aside, or pass --force if that is what you want."
    fi
fi

MPIRUN=()
if [[ -n "$GPU" ]]; then
    THREADS=1                   # the push is on the device; host threads only contend
    if [[ $NRANKS -gt 1 ]]; then
        command -v mpirun >/dev/null || die "--gpu $GPU needs $NRANKS ranks but there is \
no mpirun on PATH"
        # Refuse the default decomposition on several devices: AMReX balances cells, and
        # an ablation deck's particles all sit in one end of the domain, so without a
        # pinned decomposition one card would idle. Better to stop than to waste it.
        if ! grep -qE "^amr\.max_grid_size(_[xyz])? *=" "${DECKS[0]}" 2>/dev/null; then
            die "--gpu $GPU spreads this run over $NRANKS devices, but the deck pins no
     decomposition (no amr.max_grid_size*). AMReX balances CELLS, not particles, so the
     default split would hand one rank nearly every macroparticle and leave a card idle.
     Set numerics.max_grid_size in config.yaml to cut the TRANSVERSE axis only, e.g.
       max_grid_size: [<half the transverse cells>, <all the axial cells>]
     then regenerate the deck. Or run on one device with -g <N>."
        fi
        MPIRUN=(mpirun -np "$NRANKS")
        echo "launch: GPU mode -- $NRANKS MPI ranks, one per device ($GPU), \
OMP_NUM_THREADS forced to 1"
        echo "launch:      decomposition: $(grep -hE '^amr\.max_grid_size' \
"${DECKS[0]}" | tr '\n' ' ')"
        echo "launch:      NOTE the ray march runs on ONE rank (it owns the gathered
launch:      full-domain box); only the push, deposit and field solve decompose."
    else
    echo "launch: GPU mode -- device $GPU ($(nvidia-smi --query-gpu=name \
        --format=csv,noheader -i "$GPU" 2>/dev/null)), OMP_NUM_THREADS forced to 1"
    fi
    # The push belongs on the device, but since Phase 1.5 the ray march is threaded HOST
    # code, and it is ~65 % of a driven 2D step. OMP_NUM_THREADS=1 leaves it serial unless
    # the deck asks for threads by itself, which is what laser_deposition.ray_threads is
    # for (config key `laser.ray_threads`). Say so rather than let a driven run quietly
    # give up the 6x -- and note it needs a binary built with OpenMP: build_cuda is not.
    # Read the value and compare it numerically -- a pattern like `= *[^0]` matches the
    # SPACE in `= 0.` (the ` *` happily matches zero spaces), which would fire this note
    # on every laser-off control.
    I0="$(awk -F= '/^laser_deposition\.intensity[[:space:]]*=/ {gsub(/[[:space:]]/,"",$2);
                                                                print $2; exit}' \
          "${DECKS[0]}" 2>/dev/null)"
    if awk -v v="${I0:-0}" 'BEGIN{exit !(v+0 > 0)}' \
       && ! grep -q "^laser_deposition\.ray_threads" "${DECKS[0]}" 2>/dev/null; then
        echo "launch: NOTE this is a DRIVEN run and the deck sets no laser_deposition.ray_threads,"
        echo "launch:      so the ray march stays single-threaded. Set laser.ray_threads in"
        echo "launch:      config.yaml (and use a CUDA build compiled with OpenMP)."
    fi
fi
# The build tree, not just the basename: build_cuda and build_cuda_omp both produce a
# file called warpx.2d, and which one ran is the difference between the threaded ray
# march and an inert one. This line is the run's provenance.
echo "launch: $(basename "$RUN_DIR")  deck=$DECK  threads=$THREADS"
echo "launch: warpx=$WARPX"
echo "launch: cwd=$RUN_DIR  (so diags/ lands here, not in the repo root)"
echo "launch: ${MPIRUN[*]:-}${MPIRUN:+ }$WARPX $DECK ${EXTRA[*]:-} > run.log 2>&1"
if [[ $DRYRUN -eq 1 ]]; then
    echo "launch: --dry-run, nothing started."
    exit 0
fi

cd "$RUN_DIR"                                           # THE POINT OF THIS SCRIPT
export OMP_NUM_THREADS="$THREADS" OMP_PROC_BIND=spread OMP_PLACES=cores
if [[ -n "$GPU" ]]; then
    export CUDA_VISIBLE_DEVICES="$GPU"
    unset OMP_PROC_BIND OMP_PLACES         # meaningless with one host thread
fi

start_logger() {   # after WarpX, so run.log exists (the logger waits for it anyway)
    [[ $LOGGER -eq 1 ]] || return 0
    nohup python "$ROOT/scripts/run_progress_logger.py" "$RUN_DIR" \
        > "$RUN_DIR/logger.out" 2>&1 &
    local lpid=$!
    # The logger refuses to start when another one already holds this run (they
    # would append to the same progress.log, each timing the run from its own
    # start). It exits immediately in that case, and its complaint goes to
    # logger.out where nobody looks -- so surface it here instead.
    sleep 1
    if ! kill -0 "$lpid" 2>/dev/null; then
        echo "launch: WARNING the progress logger exited immediately:"
        sed 's/^/launch:          /' "$RUN_DIR/logger.out"
        echo "launch:          WarpX itself is unaffected and still running."
        return 0
    fi
    echo "launch: progress logger pid $lpid -> $(basename "$RUN_DIR")/progress.log"
}

if [[ $BACKGROUND -eq 1 ]]; then
    nohup ${MPIRUN[@]+"${MPIRUN[@]}"} "$WARPX" "$DECK" \
         ${EXTRA[@]+"${EXTRA[@]}"} > run.log 2>&1 &
    if [[ ${#MPIRUN[@]} -gt 0 ]]; then
        echo "launch: mpirun pid $! -> $(basename "$RUN_DIR")/run.log"
        echo "launch:      (kill THAT pid, not the warpx children -- and kill BY PID)"
    else
        echo "launch: warpx pid $! -> $(basename "$RUN_DIR")/run.log"
    fi
    start_logger
    echo "launch: tail -f $RUN_DIR/run.log"
else
    start_logger
    echo "launch: running in the foreground; tail -f $RUN_DIR/run.log"
    exec ${MPIRUN[@]+"${MPIRUN[@]}"} "$WARPX" "$DECK" \
         ${EXTRA[@]+"${EXTRA[@]}"} > run.log 2>&1
fi
