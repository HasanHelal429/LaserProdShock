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
#   studies/ray_march_perf/capture.sh <bin_dir> <out_dir> [parmparse overrides...]
#
# e.g.  capture.sh studies/ray_march_perf/baseline_bin  .../scratch/base
#       capture.sh /home/hhelal/warpx-cda/build/bin     .../scratch/o3
#       # the EXACT configuration: one accumulator (serial summation order), no vacuum skip
#       capture.sh .../build/bin .../scratch/o1_exact \
#           laser_deposition.n_accumulators=1 laser_deposition.vacuum_skip_density=0
#
# `THREADS=<n>` overrides OMP_NUM_THREADS (default 1) -- Tier 4 compares captures taken at
# 1/2/4/8/12 threads, which must be bit-identical to each other because ray i always lands
# in accumulator i % n_accumulators regardless of who runs it.
set -euo pipefail

BIN_DIR=${1:?usage: capture.sh <bin_dir> <out_dir> [parmparse overrides...]}
OUT=${2:?usage: capture.sh <bin_dir> <out_dir> [parmparse overrides...]}
shift 2
EXTRA=("$@")
THREADS=${THREADS:-1}
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
    # OMP_NUM_THREADS=1 by default, deliberately: the baseline must be the SERIAL march, so
    # that Tier 4's thread-invariance test has an unambiguous reference. nice'd because a
    # physics run may be latency-bound on the same host.
    ( cd "$d" && OMP_NUM_THREADS="$THREADS" nice -n 19 "$bin" inputs \
        laser_deposition.profile_intervals=1 "${EXTRA[@]}" > run.log 2>&1 ) \
      || { echo "!! $name FAILED -- see $d/run.log"; tail -20 "$d/run.log"; exit 1; }
done

echo
echo "captured to $OUT"
find "$OUT" -name 'laserdep_profile_*.txt' | wc -l | xargs echo "  profile dumps:"
