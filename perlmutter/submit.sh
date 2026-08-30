#!/bin/bash -l
# Submit a LaserProdShock P5 job array on Perlmutter.
#
#   perlmutter/submit.sh raycfl --qos debug --time 00:30:00   # RUN THIS FIRST (D4 gate)
#   perlmutter/submit.sh spine                                 # the headline + its control
#   perlmutter/submit.sh ladder                                # handoff-time sensitivity
#   perlmutter/submit.sh cap                                   # the 10 -> 20 n_cr A/B
#   perlmutter/submit.sh all                                   # every long leg at once
#   perlmutter/submit.sh spine --dry                           # print sbatch, submit nothing
#
# Site-specific values come from perlmutter/site.conf. sbatch #SBATCH directives cannot
# read shell variables, which is why -A/-q/-t/--array are passed here rather than baked
# into job.sbatch.

set -euo pipefail
LP_PM="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export LP_PM
# shellcheck disable=SC1090
source "$LP_PM/_common.sh"

WHAT="${1:-}"; shift || true
DRY=0; QOS_OVERRIDE=""; TIME_OVERRIDE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry)  DRY=1; shift ;;
        --qos)  QOS_OVERRIDE="$2"; shift 2 ;;
        --time) TIME_OVERRIDE="$2"; shift 2 ;;
        *) echo "unknown option '$1'" >&2; exit 2 ;;
    esac
done

QOS="${DEFAULT_QOS:-shared}"
TIME="${SPINE_TIME:-24:00:00}"
JOBNAME="lp5"

case "$WHAT" in
  raycfl)
    # THE G4 GATE. Four 2-ps rungs, minutes each -- they fit debug's 30-minute cap and
    # 5-job limit exactly, and debug starts hours sooner than shared. Ordered coarse-first
    # so the cheap rung surfaces a setup mistake before the 5x-finer one runs.
    RUNS=(runs/P5/P5_raycfl_050 runs/P5/P5_raycfl_025
          runs/P5/P5_raycfl_010 runs/P5/P5_raycfl_005)
    TIME="00:30:00"; QOS="debug"; JOBNAME="lp5_raycfl"
    ;;
  spine)
    # The headline leg, its own G3 control, and the analytic-IC arm that measures what
    # lifting the initial condition was worth. All three are the same duration, so on
    # three GPUs the wall clock is one run.
    RUNS=(runs/P5/P5_seed          # 0.3 ns -- finishes first, surfaces mistakes cheaply
          runs/P5/P5_flashic       # THE SPINE
          runs/P5/P5_flashic_off   # its G3 control
          runs/P5/P5_full)         # analytic IC: the A/B for the lift itself
    JOBNAME="lp5_spine"
    ;;
  ladder)
    # Handoff-time sensitivity. Later rungs are strictly cheaper.
    RUNS=(runs/P5/P5_flashic_t04 runs/P5/P5_flashic_t02)
    JOBNAME="lp5_ladder"
    ;;
  cap)
    RUNS=(runs/P5/P5_flashic_n20)
    JOBNAME="lp5_cap"
    ;;
  all)
    RUNS=(runs/P5/P5_seed runs/P5/P5_flashic runs/P5/P5_flashic_off runs/P5/P5_full
          runs/P5/P5_flashic_t04 runs/P5/P5_flashic_t02 runs/P5/P5_flashic_n20)
    JOBNAME="lp5_all"
    ;;
  *)
    echo "usage: $0 {raycfl|spine|ladder|cap|all} [--dry] [--qos Q] [--time HH:MM:SS]" >&2
    exit 2 ;;
esac

[[ -n "$QOS_OVERRIDE"  ]] && QOS="$QOS_OVERRIDE"
[[ -n "$TIME_OVERRIDE" ]] && TIME="$TIME_OVERRIDE"

# debug's caps are hard. Refuse here rather than let the user find out after the wait.
if [[ "$QOS" == "debug" ]]; then
    secs=$(awk -F: '{print ($1*3600)+($2*60)+$3}' <<<"$TIME")
    (( secs <= 1800 )) || { echo "submit: --qos debug caps walltime at 00:30:00 (asked $TIME)" >&2; exit 2; }
    (( ${#RUNS[@]} <= 5 )) || { echo "submit: --qos debug caps a job array at 5 tasks (asked ${#RUNS[@]})" >&2; exit 2; }
fi

# Pre-flight: every leg must have a deck, a README, and -- if it is a lifted-IC run --
# its node table. Catching a missing ic_flash.yaml here costs a second; catching it
# inside an array task costs a queue wait.
fail=0
for r in "${RUNS[@]}"; do
    d="$LASERPROD_ROOT/${r%%:*}"
    [[ -f "$d/config.yaml" ]] || { echo "missing $d/config.yaml" >&2; fail=1; }
    [[ -f "$d/README.md"   ]] || { echo "missing $d/README.md (runs/README.md: required)" >&2; fail=1; }
    compgen -G "$d/inputs_*" > /dev/null || { echo "no deck in $d -- run scripts/make_inputs.py" >&2; fail=1; }
    if grep -q "corona_profile: flash_table" "$d/config.yaml" 2>/dev/null; then
        [[ -f "$d/ic_flash.yaml" ]] || {
            echo "$d uses a lifted IC but has no ic_flash.yaml" >&2
            echo "   generate it: scripts/flash_ic_fit.py ${r%%:*} --time <ns>" >&2; fail=1; }
    fi
done
(( fail == 0 )) || exit 1

# A file rather than an exported variable: sbatch --export is comma-separated and mangles
# anything containing spaces.
RUNLIST="$(mktemp "${TMPDIR:-/tmp}/lp5_runlist.XXXXXX")"
printf '%s\n' "${RUNS[@]}" > "$RUNLIST"
WORKROOT="${WORKROOT:-${PSCRATCH:-$HOME}/laserprod_work}"

CMD=(sbatch -A "$NERSC_ACCOUNT" -q "$QOS" -t "$TIME"
     --array="0-$((${#RUNS[@]} - 1))" -J "$JOBNAME"
     --export=ALL,LP_PM="$LP_PM",RUNLIST="$RUNLIST",WORKROOT="$WORKROOT"
     "$LP_PM/job.sbatch")

echo "runs (${#RUNS[@]}):"; printf '  %s\n' "${RUNS[@]}"
echo
echo "${CMD[@]}"
if (( DRY )); then
    echo "(--dry: nothing submitted; runlist left at $RUNLIST)"
    exit 0
fi
"${CMD[@]}"
