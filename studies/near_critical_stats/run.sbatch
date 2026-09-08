#!/bin/bash -l
# One array task = one (rung, mode) pair, all 5 repeats run sequentially.
#
# Eight tasks rather than forty: gpu_shared has been running several hundred deep, and a
# 40-task array churns the queue for no benefit when each run is ~6 min. Each task is
# ~30-45 min, comfortably inside a 2 h wall.
#SBATCH -C gpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32
#SBATCH -G 1
#SBATCH -J lp5_ncstats
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%A_%a.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%A_%a.err
set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"
export MPICH_OFI_NIC_POLICY=GPU OMP_NUM_THREADS=16

BIN=${WARPX_BIN:-/pscratch/sd/h/hhelal/warpx-fix/build_fix/bin/warpx.1d}
R=/pscratch/sd/h/hhelal/LaserProdShock/runs/P5
OUT=${STATS_OUT:-/pscratch/sd/h/hhelal/tier_fixes/ncstats}
NREP=${NREP:-5}
mkdir -p "$OUT"

# task index -> (rung, mode)
RUNGS=(0025 005 010 025)
IDX=${SLURM_ARRAY_TASK_ID:-0}
RUNG=${RUNGS[$(( IDX % 4 ))]}
FIX=$(( IDX / 4 ))            # 0..3 -> fix 0 ; 4..7 -> fix 1
LEG="P5_raycfl_${RUNG}"

echo "=== task $IDX : $LEG, near_critical_fix=$FIX, $NREP repeats, straight rays ==="
echo "    binary $BIN"

for ((k = 1; k <= NREP; ++k)); do
    tag="${LEG}_fix${FIX}_r${k}"
    d="$OUT/$tag"
    if [[ -f "$d/run.log" ]] && tail -1 "$d/run.log" | grep -q finalized; then
        echo "  $tag already complete, skipping"; continue
    fi
    rm -rf "$d"; mkdir -p "$d"; cd "$d"
    cp "$R/$LEG/inputs_$LEG" deck
    cp "$R/$LEG/ic_flash.yaml" . 2>/dev/null || true
    # refraction = 0 is the point of this study; the seed varies per repeat so the error
    # bar includes seed choice, which a production number is subject to.
    srun -n 1 --cpu-bind=cores "$BIN" deck \
        laser_deposition.refraction=0 \
        laser_deposition.near_critical_fix="$FIX" \
        warpx.random_seed=$(( 20260908 + k )) \
        > run.log 2>&1
    rc=$?
    printf '  %-26s exit=%s Eabs=%s overfrac=%s\n' "$tag" "$rc" \
      "$(grep -oE 'Eabs [0-9.e+-]+' run.log | tail -1 | awk '{print $2}')" \
      "$(grep -oE 'overfrac [0-9.e+-]+' run.log | awk '{print $2}' | sort -g | tail -1)"
    # fail loudly rather than leaving a silent gap in the statistics
    [[ $rc -eq 0 ]] || { echo "    FAILED -- last 5 lines:"; tail -5 run.log | sed 's/^/      /'; }
done
echo "=== task $IDX done ==="
