#!/usr/bin/env bash
# Wait for other work to clear, then launch a run. A queue of one.
#
# Usage:  scripts/queue_run.sh [options] <run_dir> [-- <launch.sh args>]
#
#   -a, --after DIR        wait until DIR is no longer running (repeatable). DIR is any
#                          run directory, in this repo or another (KinShock2020, ...).
#   -G, --gpus-free LIST   wait until each comma-listed device is idle
#   -p, --poll N           seconds between checks (default 60)
#   -c, --confirm N        consecutive clean checks required before launching (default 3)
#   -o, --orphan-timeout N seconds to keep waiting for an --after run that has never
#                          STARTED, once everything else is clear (default 7200)
#   -m, --max-wait N       give up entirely after N seconds (default 172800 = 48 h)
#   -n, --dry-run          evaluate the conditions once, print them, launch nothing
#
# Everything after `--` is handed to launch.sh verbatim, so the run is started exactly
# the way it would have been by hand:
#
#   scripts/queue_run.sh -a ../KinShock2020/runs/implicit_phase/i0_implicit_cfl075 \
#                        -G 0,1 runs/P1/P1_vac_2d_spot_abl -- -b -L --gpu 0,1
#
# WHY THE CONDITIONS ARE WHAT THEY ARE
#
# "No longer running" is decided by whether any live process has that directory as its
# cwd -- NOT by looking for DONE in progress.log. A run that was killed, or that never
# started, never writes DONE, and a queue that waits for a string that will never appear
# hangs forever. Absence of a process plus an idle GPU is the honest test, and it is the
# same test for a run that finished, was killed, or was abandoned.
#
# The GPU check is separate on purpose. A run directory can be idle while its card is
# still held by somebody else's job -- this is a shared machine -- and starting into that
# gets the new run OOM-killed or starved.
#
# --confirm exists because both tests are instantaneous samples. A process that is
# between MPI ranks, or a card mid-teardown, can read clear for one poll. Three
# consecutive clean polls a minute apart is cheap insurance against launching into a gap.
#
# --orphan-timeout is the one judgement call. If you queue behind a run that is never
# launched, strict waiting means your run never starts either. So: once every other
# condition is clear, a never-started --after directory is waited on for this long and
# then given up on, loudly, in the log. A run that HAS started and is still going is
# never given up on, however long it takes.
#
# Kill this queue by PID (`ps -eo pid,lstart,args | grep queue_run`), never with
# `pkill -f queue_run` -- pkill's own command line contains the pattern, which is how a
# previous session killed the shell it was typing in and left an orphaned logger
# appending to a live run's progress.log.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AFTER=()
GPUS=""
POLL=60
CONFIRM=3
ORPHAN=7200
MAXWAIT=172800
DRYRUN=0
RUN_DIR=""
LAUNCH_ARGS=()

die() { echo "queue: $*" >&2; exit 1; }
say() { echo "$(date -Is) queue: $*"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --)                    shift; LAUNCH_ARGS=("$@"); break ;;
        -a|--after)            AFTER+=("${2:-}"); shift 2 ;;
        -G|--gpus-free)        GPUS="${2:-}"; shift 2 ;;
        -p|--poll)             POLL="${2:-}"; shift 2 ;;
        -c|--confirm)          CONFIRM="${2:-}"; shift 2 ;;
        -o|--orphan-timeout)   ORPHAN="${2:-}"; shift 2 ;;
        -m|--max-wait)         MAXWAIT="${2:-}"; shift 2 ;;
        -n|--dry-run)          DRYRUN=1; shift ;;
        -h|--help)             sed -n '2,48p' "${BASH_SOURCE[0]}"; exit 0 ;;
        -*)                    die "unknown option '$1' (try --help)" ;;
        *)                     [[ -n "$RUN_DIR" ]] && die "one run_dir at a time"
                               RUN_DIR="$1"; shift ;;
    esac
done

[[ -n "$RUN_DIR" ]] || die "usage: scripts/queue_run.sh [options] <run_dir> [-- <launch args>]"
[[ -d "$RUN_DIR" ]] || die "no such run dir: $RUN_DIR"
[[ -f "$RUN_DIR/README.md" ]] || die "$RUN_DIR has no README.md -- launch.sh would refuse it \
anyway, and the point of the rule is that it is written BEFORE the run, not after"

# --- the two tests ---------------------------------------------------------------

# Live process with this directory as cwd? Reads /proc rather than matching command
# lines, so it cannot match itself the way `pgrep -f` does.
dir_busy() {
    local target pid cwd
    target="$(cd "$1" 2>/dev/null && pwd)" || return 1
    for pid in $(ls /proc 2>/dev/null | grep -E '^[0-9]+$'); do
        [[ "$pid" == "$$" ]] && continue
        cwd="$(readlink "/proc/$pid/cwd" 2>/dev/null)" || continue
        [[ "$cwd" == "$target" ]] && return 0
    done
    return 1
}

dir_started() { [[ -f "$1/run.log" ]] || [[ -d "$1/diags" ]]; }

# Idle means: no compute process on it, and its memory is essentially unused. Both,
# because a process that has just exited can leave memory reported for a moment, and a
# card can hold memory with no compute app while a display is attached.
GPU_IDLE_MIB=${GPU_IDLE_MIB:-600}
gpu_busy() {
    local dev used napps
    for dev in ${1//,/ }; do
        used="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits \
                -i "$dev" 2>/dev/null | tr -d ' ')"
        [[ -z "$used" ]] && { echo "  gpu $dev: cannot read"; return 0; }
        napps="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader \
                 -i "$dev" 2>/dev/null | grep -c . || true)"
        if [[ "$used" -gt "$GPU_IDLE_MIB" || "$napps" -gt 0 ]]; then
            echo "  gpu $dev: ${used} MiB, ${napps} compute app(s) -- BUSY"
            return 0
        fi
    done
    return 1
}

# --- the wait --------------------------------------------------------------------

say "queued $(basename "$RUN_DIR")"
say "  launch args : ${LAUNCH_ARGS[*]:-<none>}"
say "  after       : ${AFTER[*]:-<none>}"
say "  gpus free   : ${GPUS:-<not checked>}"
say "  poll ${POLL}s, confirm ${CONFIRM}, orphan-timeout ${ORPHAN}s, max-wait ${MAXWAIT}s"

T0=$SECONDS
CLEAN=0
READY_SINCE=-1

while : ; do
    blockers=()
    orphans=()
    for d in ${AFTER[@]+"${AFTER[@]}"}; do
        if [[ ! -d "$d" ]]; then
            blockers+=("$d (no such directory)"); continue
        fi
        if dir_busy "$d"; then
            blockers+=("$(basename "$d") running")
        elif ! dir_started "$d"; then
            orphans+=("$(basename "$d") never started")
        fi
    done
    gpu_note=""
    if [[ -n "$GPUS" ]]; then
        if gpu_note="$(gpu_busy "$GPUS")"; then
            blockers+=("gpu busy")
        fi
    fi

    # Everything except never-started runs is clear -> start the orphan clock.
    if [[ ${#blockers[@]} -eq 0 ]]; then
        [[ $READY_SINCE -lt 0 ]] && READY_SINCE=$SECONDS
        if [[ ${#orphans[@]} -gt 0 ]]; then
            waited=$((SECONDS - READY_SINCE))
            if [[ $waited -ge $ORPHAN ]]; then
                say "GIVING UP waiting for: ${orphans[*]} -- ${waited}s with everything \
else clear, past --orphan-timeout ${ORPHAN}s. Launching anyway; if that run is still \
intended, it will now contend with this one."
                orphans=()
            else
                blockers+=("${orphans[*]} (waiting ${waited}/${ORPHAN}s)")
            fi
        fi
    else
        READY_SINCE=-1
    fi

    if [[ ${#blockers[@]} -eq 0 ]]; then
        CLEAN=$((CLEAN + 1))
        say "clear ($CLEAN/$CONFIRM)"
        [[ $CLEAN -ge $CONFIRM ]] && break
    else
        [[ $CLEAN -gt 0 ]] && say "no longer clear, resetting confirmation"
        CLEAN=0
        # Orphans are reported even when something else is blocking, so the log always
        # says which of the --after runs have not started -- otherwise a run that is
        # never launched looks identical to one that is merely slow.
        pending=""
        [[ ${#orphans[@]} -gt 0 ]] && pending=" | not started yet: ${orphans[*]}"
        say "waiting: ${blockers[*]}${pending}${gpu_note:+$'\n'$gpu_note}"
    fi

    if [[ $DRYRUN -eq 1 ]]; then
        say "--dry-run: evaluated once, launching nothing."; exit 0
    fi
    if [[ $((SECONDS - T0)) -ge $MAXWAIT ]]; then
        say "GAVE UP after $((SECONDS - T0))s (--max-wait). Nothing launched."; exit 1
    fi
    sleep "$POLL"
done

say "conditions met after $((SECONDS - T0))s -- launching"
say "exec: $ROOT/scripts/launch.sh ${LAUNCH_ARGS[*]:-} $RUN_DIR"
"$ROOT/scripts/launch.sh" ${LAUNCH_ARGS[@]+"${LAUNCH_ARGS[@]}"} "$RUN_DIR"
rc=$?
say "launch.sh exited $rc"
exit $rc
