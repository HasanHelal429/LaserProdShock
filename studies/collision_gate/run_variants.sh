#!/usr/bin/env bash
# D3 collision gate -- launch the 18 variants.
#
#   ./run_variants.sh            # all 18, sequentially, on GPU 0
#   ./run_variants.sh -g 1       # ... on GPU 1
#   ./run_variants.sh D3_n1_Ti12_c10 D3_n1_Ti12_coll_off    # just these
#
# Every variant goes through scripts/launch.sh, so each has its own diags/ and cannot
# clobber another's (see CLAUDE.md: two runs launched from the repo root share ./diags/).
set -euo pipefail
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
PY=/opt/anaconda3/envs/physics/bin/python
GPU=0
while getopts "g:" o; do case $o in g) GPU=$OPTARG;; esac; done
shift $((OPTIND-1))

VARIANTS=("$@")
if [ ${#VARIANTS[@]} -eq 0 ]; then
  mapfile -t VARIANTS < <(ls -d scratch/D3_* | xargs -n1 basename | sort)
fi

echo "== D3 collision gate: ${#VARIANTS[@]} variants on GPU $GPU =="
for v in "${VARIANTS[@]}"; do
  d="scratch/$v"
  [ -d "$d" ] || { echo "!! no such variant: $v"; exit 1; }
  echo "-- $v"
  "$PY" "$ROOT/scripts/make_inputs.py" "$d" >/dev/null
  # --force: re-running a variant is normal here (the ladder is cheap and gets rebuilt),
  # and each variant owns its own diags/ so there is nothing to clobber but itself.
  "$ROOT/scripts/launch.sh" --gpu "$GPU" --force "$d"
  # --verify IMMEDIATELY, not at the end: warpx_used_inputs is written at initialisation,
  # and a binary predating a deck flag ignores it SILENTLY (CLAUDE.md). ndt_supercycle and
  # laser_deposition.intervals are exactly the kind of key that would vanish unnoticed.
  "$PY" "$ROOT/scripts/make_inputs.py" "$d" --verify
done
echo "== done. now: $PY analyze.py =="
