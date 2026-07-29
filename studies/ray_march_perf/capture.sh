#!/usr/bin/env bash
# Run the five upstream laser_deposition CI decks with a given WarpX build and capture
# everything Tier 1 compares: the per-cell profile dump at every step, the reduced
# LASERDEP history, and the run log.
#
# The decks do NOT dump laser_deposition profiles by default -- they are analytic tests
# that reduce the operator to one number, which is exactly why the clamp bug survived
# them all (TEST_PLAN §2.8). `profile_intervals=1` is appended on the command line so the
# deck files stay untouched and the comparison is SPATIAL.
#
#   studies/ray_march_perf/capture.sh <bin_dir> <out_dir>
#
# e.g.  capture.sh studies/ray_march_perf/baseline_bin  .../scratch/base
#       capture.sh /home/hhelal/warpx-cda/build/bin     .../scratch/o3
set -euo pipefail

BIN_DIR=${1:?usage: capture.sh <bin_dir> <out_dir>}
OUT=${2:?usage: capture.sh <bin_dir> <out_dir>}
DECKS=/home/hhelal/warpx-cda/Examples/Tests/laser_deposition

# name:dims -- the five decks the plan's Tier 1 names
CASES=(
  "1d_laser_deposition:1d"
  "1d_laser_deposition_ramp:1d"
  "2d_laser_deposition_oblique:2d"
  "2d_laser_deposition_gaussian:2d"
  "2d_laser_deposition_focus:2d"
)

mkdir -p "$OUT"
BIN_DIR=$(cd "$BIN_DIR" && pwd)
OUT=$(cd "$OUT" && pwd)

for case in "${CASES[@]}"; do
    name=${case%%:*}; dims=${case##*:}
    bin="$BIN_DIR/warpx.$dims"
    [ -x "$bin" ] || { echo "!! no $bin"; exit 1; }
    d="$OUT/$name"
    rm -rf "$d"; mkdir -p "$d"
    cp "$DECKS/inputs_test_$name" "$d/inputs"
    echo "=== $name ($dims) with $(basename "$(readlink -f "$bin")")"
    # OMP_NUM_THREADS=1 deliberately: the baseline must be the SERIAL march, so that
    # Tier 4's thread-invariance test has an unambiguous reference. nice'd because a
    # physics run may be latency-bound on the same host.
    ( cd "$d" && OMP_NUM_THREADS=1 nice -n 19 "$bin" inputs \
        laser_deposition.profile_intervals=1 > run.log 2>&1 ) \
      || { echo "!! $name FAILED -- see $d/run.log"; tail -20 "$d/run.log"; exit 1; }
done

echo
echo "captured to $OUT"
find "$OUT" -name 'laserdep_profile_*.txt' | wc -l | xargs echo "  profile dumps:"
