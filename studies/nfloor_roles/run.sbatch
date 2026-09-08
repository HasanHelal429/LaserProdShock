#!/bin/bash -l
# One array task = one (march mode, n_floor) pair, 3 repeats run sequentially.
#SBATCH -C gpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32
#SBATCH -G 1
#SBATCH -J lp5_nfloor
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%A_%a.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%A_%a.err
set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"
export MPICH_OFI_NIC_POLICY=GPU OMP_NUM_THREADS=16

BIN=${WARPX_BIN:-/pscratch/sd/h/hhelal/warpx-fix/build_fix/bin/warpx.1d}
LEG=P5_raycfl_025
R=/pscratch/sd/h/hhelal/LaserProdShock/runs/P5
OUT=${NFLOOR_OUT:-/pscratch/sd/h/hhelal/tier_fixes/nfloor}
NREP=${NREP:-3}
mkdir -p "$OUT"

FLOORS=(1.e-1 1.e-2 1.e-3 1.e-4)
IDX=${SLURM_ARRAY_TASK_ID:-0}
NF=${FLOORS[$(( IDX % 4 ))]}
REFR=$(( IDX < 4 ? 0 : 1 ))       # tasks 0-3 straight-ray, 4-7 refracting

echo "=== task $IDX : n_floor=$NF  refraction=$REFR  ($NREP repeats) ==="
for ((k = 1; k <= NREP; ++k)); do
    tag="nf${NF}_refr${REFR}_r${k}"
    d="$OUT/$tag"
    if [[ -f "$d/run.log" ]] && tail -1 "$d/run.log" | grep -q finalized; then
        echo "  $tag complete, skipping"; continue
    fi
    rm -rf "$d"; mkdir -p "$d"; cd "$d"
    cp "$R/$LEG/inputs_$LEG" deck
    cp "$R/$LEG/ic_flash.yaml" . 2>/dev/null || true
    srun -n 1 --cpu-bind=cores "$BIN" deck \
        laser_deposition.n_floor="$NF" \
        laser_deposition.refraction="$REFR" \
        laser_deposition.near_critical_fix=1 \
        warpx.random_seed=$(( 20260908 + k )) > run.log 2>&1
    rc=$?
    printf '  %-24s exit=%s Eabs=%s layerfrac=%s overfrac=%s rmax=%s\n' "$tag" "$rc" \
      "$(grep -oE 'Eabs [0-9.e+-]+' run.log | tail -1 | awk '{print $2}')" \
      "$(grep -oE 'layerfrac [0-9.e+-]+' run.log | awk '{print $2}' | sort -g | tail -1)" \
      "$(grep -oE 'overfrac [0-9.e+-]+' run.log | awk '{print $2}' | sort -g | tail -1)" \
      "$(grep -oE 'rmax [0-9.e+-]+' run.log | awk '{print $2}' | sort -g | tail -1)"
    [[ $rc -eq 0 ]] || { echo "    FAILED:"; tail -5 run.log | sed 's/^/      /'; }
done
echo "=== task $IDX done ==="
