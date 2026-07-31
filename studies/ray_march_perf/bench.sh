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
# gives many applications.
#
# Diagnostics are disabled with `intervals=0`, which is the ONLY value that disables
# them: `SliceParser::contains` is `(n - start) % period == 0` and returns false only
# for `period <= 0`, so a large period like 1000000 still CONTAINS STEP 0. Setting the
# diagnostics to 1000000 to "turn them off" instead wrote a 74 MB laserdep_profile at
# step 0 -- from inside applyDeposition, so the write landed in the operator's own timer
# and was charged to every application as 0.118 s of amortised "floor".
#
# e.g. bench.sh scratch/bench "serial:1:" "o2off:1:laser_deposition.vacuum_skip=0" \
#                             "t8:8:"
set -euo pipefail

OUT=${1:?usage: bench.sh <out_dir> [label:threads:overrides] ...}
shift
DECK=/home/hhelal/LaserProdShock/runs/P1/P1_vac_2d_spot/inputs_P1_vac_2d_spot
BIN=${BIN:-/home/hhelal/warpx-cda/build/bin/warpx.2d}
STEPS=${STEPS:-6}
# ppc does not affect the ray march at all -- it reads a gathered field -- so 1 keeps the
# benchmark cheap. But it DOES set the cost of the density deposit and the kicks, so use
# `PPC="6 6"` (the real spot run) when the question is what the operator costs, not what
# the march costs.
PPC=${PPC:-1 1}

mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)

printf "%-12s %7s %6s %10s %9s %9s %9s %9s %9s %9s %9s\n" \
       label threads calls "app[s]" "rayTrace" "gather" "coeff" "tlocal" "density" "kick" "other"
for spec in "$@"; do
    label=${spec%%:*}; rest=${spec#*:}
    thr=${rest%%:*}; extra=${rest#*:}
    d="$OUT/$label"; rm -rf "$d"; mkdir -p "$d"
    # shellcheck disable=SC2086
    ( cd "$d" && OMP_NUM_THREADS="$thr" OMP_PROC_BIND=spread OMP_PLACES=cores \
        nice -n 19 "$BIN" "$DECK" \
        max_step=$STEPS \
        laser_deposition.intervals=1 \
        targ_electrons.num_particles_per_cell_each_dim="$PPC" \
        targ_ions.num_particles_per_cell_each_dim="$PPC" \
        diag1.intervals=0 diag_fields.intervals=0 \
        diag_phase.intervals=0 laser_deposition.profile_intervals=0 \
        $extra > run.log 2>&1 ) || { echo "!! $label FAILED"; tail -20 "$d/run.log"; exit 1; }
    python3 - "$d/run.log" "$label" "$thr" <<'PY'
import re, sys
log, label, thr = sys.argv[1], sys.argv[2], sys.argv[3]
txt = open(log).read()

# TinyProfiler prints TWO tables, exclusive first. Read the INCLUSIVE one: with the
# sub-regions in place, applyDeposition's exclusive time is what is left over after
# them, which is not the cost of an application. Reading the first match in the file
# silently gave the exclusive number and reported an application as 0.0002 s.
incl = txt.split("Incl. Min", 1)
if len(incl) < 2:
    print(f"{label:<12} {thr:>7}   no inclusive profiler table in {log}"); sys.exit(0)
incl = incl[1]

def region(name):
    m = re.search(rf"{re.escape(name)}\s+(\d+)\s+"
                  rf"([0-9.e+-]+)\s+([0-9.e+-]+)\s+([0-9.e+-]+)\s+([0-9.]+)%", incl)
    return (int(m.group(1)), float(m.group(4))) if m else (0, 0.0)

calls, app = region("LaserDeposition::applyDeposition")
if not calls:
    print(f"{label:<12} {thr:>7}   no applyDeposition timer in {log}"); sys.exit(0)
parts = {n: region(f"LaserDeposition::{n}")[1] for n in
         ("rayTrace", "gather", "density", "kick", "coeff", "tlocal", "scatter")}
other = app - sum(parts.values())
n = float(calls)
print(f"{label:<12} {thr:>7} {calls:>6} {app/n:>10.4f} "
      + " ".join(f"{parts[k]/n:>9.4f}" for k in
                 ("rayTrace", "gather", "coeff", "tlocal", "density", "kick"))
      + f" {other/n:>9.4f}")
PY
done
