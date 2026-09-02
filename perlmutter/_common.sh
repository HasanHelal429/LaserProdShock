#!/bin/bash -l
# Shared environment + the one function that launches WarpX on Perlmutter.
# Sourced by job.sbatch (inside the allocation) and by submit.sh (outside it).
#
# Ported from KinShock2020/perlmutter/_common.sh, which was verified against the real
# machine on 2026-08-11. The invariants it protects are identical here.

set -euo pipefail
LP_PM="${LP_PM:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
export LP_PM

[[ -f "$LP_PM/site.conf" ]] || {
    echo "perlmutter: create $LP_PM/site.conf from site.conf.example" >&2; exit 1; }
# site.conf is user-authored config, not code. Source it with `set -u` OFF: it legitimately
# refers to $PSCRATCH, which does not exist off Perlmutter, and an unbound-variable abort
# there makes every script in this directory impossible to dry-run anywhere else.
set +u
# shellcheck disable=SC1090
source "$LP_PM/site.conf"
set -u

: "${NERSC_ACCOUNT:?set NERSC_ACCOUNT in site.conf (must end in _g for GPU)}"
: "${LASERPROD_ROOT:?set LASERPROD_ROOT in site.conf}"
[[ "$NERSC_ACCOUNT" == *_g ]] || echo "perlmutter: WARNING NERSC_ACCOUNT '$NERSC_ACCOUNT' does not end in _g; GPU jobs will be rejected" >&2

pm_profile() {
    [[ -n "${MY_PROFILE:-}" ]] && return 0
    # shellcheck disable=SC1090
    source "$HOME/perlmutter_gpu_warpx.profile"
}

pm_binary() {
    local bin
    bin="$(ls "$WARPX_BUILD"/bin/warpx.1d 2>/dev/null || ls "$WARPX_BUILD"/bin/warpx.1d.* 2>/dev/null | head -1)"
    [[ -x "$bin" ]] || { echo "pm_binary: no binary in $WARPX_BUILD/bin -- run perlmutter/build_warpx.sh" >&2; return 1; }
    echo "$bin"
}

# run_warpx <run_dir_relative_to_repo> [label]
#
# THE INVARIANT THIS EXISTS TO PRESERVE: the generated deck sets no diag*.file_prefix, so
# WarpX writes plotfiles to diags/ RELATIVE TO THE LAUNCH CWD. Two runs started from a
# shared directory clobber each other -- the reason scripts/launch.sh exists on chablis.
# Same rule here: always cd first.
run_warpx() {
    local run_rel="$1" label="${2:-}"
    local run_dir="$LASERPROD_ROOT/$run_rel"
    local bin; bin="$(pm_binary)"
    local deck; deck="$(ls "$run_dir"/inputs_* 2>/dev/null | head -1)"
    [[ -f "$deck" ]] || { echo "run_warpx: no deck in $run_dir" >&2; return 1; }
    # The project's second rule, enforced here as it is by scripts/launch.sh on chablis.
    [[ -f "$run_dir/README.md" ]] || {
        echo "run_warpx: $run_rel has no README.md -- refusing (see runs/README.md)" >&2
        return 1; }

    local work="$run_dir"
    if [[ -n "$label" ]]; then
        work="${WORKROOT:?WORKROOT must be set when using a label}/$label"
        mkdir -p "$work"
        cp "$deck" "$work/"
        cp "$run_dir/config.yaml" "$work/"
        # A lifted-IC run's table is part of its initial condition, so a labelled
        # replicate is not a replicate without it.
        [[ -f "$run_dir/ic_flash.yaml" ]] && cp "$run_dir/ic_flash.yaml" "$work/"
    fi

    # RESTART, or refuse. The refusal is a safety property -- two runs sharing a diags/
    # clobber each other, which has already cost this group a rerun -- so it is kept for
    # every case EXCEPT the one where resuming is well defined: a checkpoint written by
    # this same run. A leg whose deck asks for checkpoints is meant to be chained; a leg
    # whose deck does not is still protected exactly as before.
    local restart=""
    if compgen -G "$work/diags/chk*" > /dev/null; then
        # highest step wins; the names are zero-padded so a lexical sort is numeric
        restart="$(ls -d "$work"/diags/chk* 2>/dev/null | sort | tail -1)"
        echo "run_warpx: RESTARTING from $(basename "$restart")"
    elif compgen -G "$work/diags/*" > /dev/null; then
        echo "run_warpx: $work/diags already has output and no checkpoint to resume from" >&2
        echo "           -- refusing to overwrite in place. Move it aside or delete it," >&2
        echo "           then resubmit. (Add diagnostics.checkpoint_intervals to the" >&2
        echo "           config if this leg should be resumable.)" >&2
        return 1
    fi

    pm_profile
    export MPICH_OFI_NIC_POLICY=GPU
    export OMP_NUM_THREADS=16          # 16 physical cores per GPU; avoids hyperthreading

    cd "$work"                          # THE POINT: diags/ lands here
    echo "run_warpx: $(basename "$work")  bin=$bin"
    echo "run_warpx: cwd=$PWD"

    # Every run leaves a progress.log (project convention, and the memory note about it).
    # Started before srun so it sees run.log from the first poll; it exits when WarpX does.
    local logger_pid=""
    if [[ -f "$LASERPROD_ROOT/scripts/run_progress_logger.py" ]]; then
        python3 "$LASERPROD_ROOT/scripts/run_progress_logger.py" "$work" \
            > "$work/logger.out" 2>&1 &
        logger_pid=$!
    fi

    # `set -e` off across the run: a WarpX failure must NOT abort this function, or the
    # array task dies before the logger is reaped and before --verify reports why.
    local rc=0
    set +e
    # A restart APPENDS to run.log rather than truncating it: the LASERDEP history and
    # the step trace from the earlier segments are the run's only record of what it did
    # before the wall, and every analysis tool reads them out of this one file.
    if [[ -n "$restart" ]]; then
        srun --cpu-bind=cores "$bin" "$(basename "$deck")" \
             amr.restart="$restart" >> run.log 2>&1
    else
        srun --cpu-bind=cores "$bin" "$(basename "$deck")" > run.log 2>&1
    fi
    rc=$?
    set -e
    if [[ -n "$logger_pid" ]]; then
        sleep 35
        kill "$logger_pid" 2>/dev/null || true
    fi

    echo "run_warpx: exit $rc"
    if [[ $rc -ne 0 ]]; then
        echo "run_warpx: FAILED — last 15 lines of run.log:" >&2
        tail -15 run.log >&2 || true
    fi
    # Closes the "config = what was simulated" loop, including the unused-input scan. On
    # chablis this is meant to be run SECONDS after launch, not at the end (a binary that
    # predates a deck's flag ignores it silently); in a batch job the earliest it can run
    # is here, so read it and do not assume it passed.
    if [[ -z "$label" ]]; then
        python3 "$LASERPROD_ROOT/scripts/make_inputs.py" "$run_dir" --verify || true
    fi
    return $rc
}
