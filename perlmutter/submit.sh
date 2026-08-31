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
  raycfl2)
    # FIFTH rung, added after the first four did NOT converge: E_abs still moved 1.18%
    # between 0.10 and 0.05, above this ladder's own 1% threshold. Minutes, so it runs in
    # debug alongside whatever the spine is doing in shared.
    RUNS=(runs/P5/P5_raycfl_0025)
    TIME="00:30:00"; QOS="debug"; JOBNAME="lp5_raycfl2"
    ;;
  dzladder)
    # TIER 1a -- THE decisive test of the 2026-08-30 diagnosis. ray_cfl held at 0.25; the
    # GRID is the variable. The dz = 0.5 rung is P5_raycfl_025, ALREADY RUN -- do not
    # repeat it. Cost is 4x and 16x that rung (2x/4x cells AND 2x/4x steps, since dt
    # scales with dz at fixed cfl), so ~25 min and ~95 min.
    RUNS=(runs/P5/P5_dz_025 runs/P5/P5_dz_0125)
    TIME="06:00:00"; JOBNAME="lp5_dzladder"
    ;;
  rampcfl)
    # TIER 1b + 1c -- the analytic-ramp ray_cfl ladder (the control for the lifted-IC
    # ladder that diverged) plus the laser-off control at the ladder's OWN duration, which
    # is what makes the ladder's energy closure readable. All six are 20300 steps, minutes
    # each; six tasks exceed debug's 5-task cap, so they go to shared.
    RUNS=(runs/P5/P5_ramp_050 runs/P5/P5_ramp_025 runs/P5/P5_ramp_010
          runs/P5/P5_ramp_005 runs/P5/P5_ramp_0025 runs/P5/P5_raycfl_off)
    TIME="01:00:00"; JOBNAME="lp5_rampcfl"
    ;;
  controls)
    # The two G3 laser-off controls. Both have intensity = 0, so NO ray is traced and
    # ray_cfl is inert in them -- which makes them the only long legs that the G4 outcome
    # cannot invalidate, and therefore the only ones safe to start before it is settled.
    # P5_full_off had no launcher path at all before 2026-08-29.
    RUNS=(runs/P5/P5_flashic_off runs/P5/P5_full_off)
    JOBNAME="lp5_controls"
    ;;
  spine)
    # The headline leg, its own G3 control, and the analytic-IC arm that measures what
    # lifting the initial condition was worth. All three are the same duration, so on
    # three GPUs the wall clock is one run.
    # P5_flashic_off is NOT here: it is in the `controls` target, which can start before
    # the G4 gate settles. Running it from both would put two tasks in one run dir.
    RUNS=(runs/P5/P5_seed          # 0.3 ns -- finishes first, surfaces mistakes cheaply
          runs/P5/P5_flashic       # THE SPINE
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
    echo "usage: $0 {raycfl|raycfl2|dzladder|rampcfl|controls|spine|ladder|cap|all} [--dry] [--qos Q] [--time HH:MM:SS]" >&2
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
#
# It MUST live on $PSCRATCH, not $TMPDIR. On Perlmutter /tmp is a per-node tmpfs, so a
# runlist written here on a login node is invisible to the compute node that runs the
# array task: job.sbatch would sed an absent file, get an empty SPEC and exit 2 on every
# task -- after the full queue wait. KinShock2020 got this right and the port lost it.
# Timestamped rather than mktemp'd so a submission's run list is also its provenance.
mkdir -p "$LP_PM/.runlists"
RUNLIST="$LP_PM/.runlists/${WHAT}-$(date +%Y%m%dT%H%M%S).txt"
printf '%s\n' "${RUNS[@]}" > "$RUNLIST"
echo "run list -> $RUNLIST"
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
