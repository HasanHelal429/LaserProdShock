#!/usr/bin/env bash
# Time the ray march itself, on the real P1_vac_2d_spot geometry.
#
#   studies/ray_march_perf/bench.sh <out_dir> [label=threads:parmparse...] ...
#
# The number that matters is WarpX's own TinyProfiler line for
# `LaserDeposition::applyDeposition`, not the wall time: it isolates the march from
# the particle push, which is what changes when ppc is lowered to make the benchmark
# affordable. The march cost does not depend on ppc at all -- it reads a gathered
# density field -- so `num_particles_per_cell_each_dim = 1 1` keeps the geometry, the
# grid, the vacuum gap and the ray count of the real run while making each step cheap.
#
# `laser_deposition.intervals=1` fires the operator every step so a short run still
# gives many applications; the plotfile diagnostics are pushed past the end for the
# same reason.
#
# e.g. bench.sh scratch/bench "serial:1:" "o2off:1:laser_deposition.vacuum_skip=0" \
#                             "t8:8:"
set -euo pipefail

OUT=${1:?usage: bench.sh <out_dir> [label:threads:overrides] ...}
shift
DECK=/home/hhelal/LaserProdShock/runs/P1/P1_vac_2d_spot/inputs_P1_vac_2d_spot
BIN=${BIN:-/home/hhelal/warpx-cda/build/bin/warpx.2d}
STEPS=${STEPS:-6}

mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)

printf "%-12s %8s %10s %12s %12s %10s\n" label threads calls "march[s]" "per-app[s]" "share"
for spec in "$@"; do
    label=${spec%%:*}; rest=${spec#*:}
    thr=${rest%%:*}; extra=${rest#*:}
    d="$OUT/$label"; rm -rf "$d"; mkdir -p "$d"
    # shellcheck disable=SC2086
    ( cd "$d" && OMP_NUM_THREADS="$thr" OMP_PROC_BIND=spread OMP_PLACES=cores \
        nice -n 19 "$BIN" "$DECK" \
        max_step=$STEPS \
        laser_deposition.intervals=1 \
        targ_electrons.num_particles_per_cell_each_dim="1 1" \
        targ_ions.num_particles_per_cell_each_dim="1 1" \
        diag1.intervals=1000000 diag_fields.intervals=1000000 \
        diag_phase.intervals=1000000 laser_deposition.profile_intervals=1000000 \
        $extra > run.log 2>&1 ) || { echo "!! $label FAILED"; tail -20 "$d/run.log"; exit 1; }
    python3 - "$d/run.log" "$label" "$thr" <<'PY'
import re, sys
log, label, thr = sys.argv[1], sys.argv[2], sys.argv[3]
txt = open(log).read()
# TinyProfiler's inclusive table: "name  ncalls  min  avg  max  max%"
m = re.search(r"LaserDeposition::applyDeposition\s+(\d+)\s+"
              r"([0-9.e+-]+)\s+([0-9.e+-]+)\s+([0-9.e+-]+)\s+([0-9.]+)%", txt)
tot = re.search(r"Total Timers covered\s*=\s*([0-9.e+-]+)", txt)
run = re.search(r"Total GPU global memory|Total Time\s*:\s*([0-9.e+-]+)", txt)
if not m:
    print(f"{label:<12} {thr:>8}   no applyDeposition timer in {log}"); sys.exit(0)
calls, mx, pct = int(m.group(1)), float(m.group(4)), float(m.group(5))
print(f"{label:<12} {thr:>8} {calls:>10} {mx:>12.3f} {mx/max(calls,1):>12.4f} {pct:>9.1f}%")
PY
done
