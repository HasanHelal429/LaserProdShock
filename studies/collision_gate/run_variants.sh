#!/usr/bin/env bash
# D3 collision gate -- launch the 18 variants.
#
#   ./run_variants.sh            # all 18, sequentially, on CPU (8 OMP threads)
#   ./run_variants.sh -g 0       # ... on GPU 0 instead (see the warning below)
#   ./run_variants.sh D3_n1_Ti12_c10 D3_n1_Ti12_coll_off    # just these
#
# CPU IS THE DEFAULT, DELIBERATELY, and the opposite of the production run's choice.
# This box is 40 cells, so a GPU run is kernel-launch-latency bound: 0.133 s/step on a
# 4070 against 0.011 s/step on 8 OMP threads. Worse, AMReX sizes its device Arena from the
# free GPU memory at startup and asks for ~8.9 GiB, so a SECOND concurrent run on the same
# device dies with "Arena out of memory" (622 MiB free) -- which is exactly what killed the
# first attempt at this ladder when three streams were launched with the old GPU default.
# Parallelism here comes from running several streams on the CPU, not from the GPU.
#
# Every variant goes through scripts/launch.sh, so each has its own diags/ and cannot
# clobber another's (see CLAUDE.md: two runs launched from the repo root share ./diags/).
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
PY=/opt/anaconda3/envs/physics/bin/python
GPU=""
while getopts "g:" o; do case $o in g) GPU=$OPTARG;; esac; done
shift $((OPTIND-1))
DEV=()
[ -n "$GPU" ] && DEV=(--gpu "$GPU")

VARIANTS=("$@")
if [ ${#VARIANTS[@]} -eq 0 ]; then
  mapfile -t VARIANTS < <(ls -d scratch/D3_* | xargs -n1 basename | sort)
fi

echo "== D3 collision gate: ${#VARIANTS[@]} variants on ${GPU:+GPU $GPU}${GPU:-CPU} =="
for v in "${VARIANTS[@]}"; do
  d="scratch/$v"
  [ -d "$d" ] || { echo "!! no such variant: $v"; exit 1; }
  echo "-- $v"
  "$PY" "$ROOT/scripts/make_inputs.py" "$d" >/dev/null
  # --force: re-running a variant is normal here (the ladder is cheap and gets rebuilt),
  # and each variant owns its own diags/ so there is nothing to clobber but itself.
  "$ROOT/scripts/launch.sh" "${DEV[@]}" --force "$d"
  # --verify IMMEDIATELY, not at the end: warpx_used_inputs is written at initialisation,
  # and a binary predating a deck flag ignores it SILENTLY (CLAUDE.md). ndt_supercycle and
  # laser_deposition.intervals are exactly the kind of key that would vanish unnoticed.
  "$PY" "$ROOT/scripts/make_inputs.py" "$d" --verify
done
echo "== done. now: $PY analyze.py =="
