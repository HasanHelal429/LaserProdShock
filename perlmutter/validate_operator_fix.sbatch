#!/bin/bash -l
# ACCEPTANCE for the instrumented operator (Group 1a/1b), built on branch
# fix/near-critical-layer in a separate worktree so the shared checkout stays at
# 534f3b170 and build_pm_1d's provenance is untouched.
#
# 1a added three self-check numbers to the LASERDEP line -- rmax (closest any ray came to
# critical), clampfrac (fraction of absorbed power bought from the n_floor clamp rather
# than from the plasma) and overfrac (fraction deposited into evanescent cells). 1b made
# n_floor an input.
#
# TWO THINGS MUST BE TRUE. The new numbers have to actually distinguish the cases the
# campaign found the hard way -- a sub-grid layer versus an underdense target -- and the
# instrumentation must not have changed any answer, since 1a/1b are diagnostics only.
# The four registered 1D/2D operator CI tests are the regression check.
#SBATCH -C gpu
#SBATCH -N 1 -n 1 -c 32 -G 1
#SBATCH -J lp5_valfix
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.err
set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"
export MPICH_OFI_NIC_POLICY=GPU OMP_NUM_THREADS=16 MPLBACKEND=Agg
NEW=/pscratch/sd/h/hhelal/warpx-fix
OLD=/pscratch/sd/h/hhelal/warpx-cda
OUT=/pscratch/sd/h/hhelal/tier_fixes/valfix
mkdir -p "$OUT"
w1() { srun -n 1 --cpu-bind=cores "$NEW/build_fix/bin/warpx.1d" "$@"; }
w2() { srun -n 1 --cpu-bind=cores "$NEW/build_fix/bin/warpx.2d" "$@"; }

echo "=== instrumented operator: $(cd $NEW && git rev-parse --short HEAD) on $(hostname) ==="

echo; echo "--- [A] does the self-check distinguish the cases the campaign found? ---"
for leg in P5_raycfl_025 P5_under_025 P5_ramp_025; do
    d="$OUT/$leg"; rm -rf "$d"; mkdir -p "$d"; cd "$d"
    cp /pscratch/sd/h/hhelal/LaserProdShock/runs/P5/$leg/inputs_$leg deck
    w1 deck max_step=200 > run.log 2>&1
    printf '  %-16s %s\n' "$leg" \
      "$(grep -m1 -oE 'rmax [^ ]+ clampfrac [^ ]+ overfrac [^ ]+' run.log || echo 'NO SELF-CHECK LINE')"
done

echo; echo "--- [B] n_floor is now an input (1b) ---"
d="$OUT/nfloor"; rm -rf "$d"; mkdir -p "$d"; cd "$d"
cp /pscratch/sd/h/hhelal/LaserProdShock/runs/P5/P5_raycfl_025/inputs_P5_raycfl_025 deck
for nf in 1.e-1 1.e-2 1.e-3; do
    w1 deck max_step=200 laser_deposition.n_floor=$nf > "run_$nf.log" 2>&1
    printf '  n_floor=%-7s Eabs=%s  clampfrac=%s\n' "$nf" \
      "$(grep -oE 'Eabs [^ ]+' "run_$nf.log" | tail -1 | awk '{print $2}')" \
      "$(grep -oE 'clampfrac [^ ]+' "run_$nf.log" | tail -1 | awk '{print $2}')"
done

echo; echo "--- [C] REGRESSION: the four registered operator CI tests ---"
E=$OLD/Examples/Tests/laser_deposition
for t in 1d_laser_deposition 1d_laser_deposition_ramp; do
    d="$OUT/ci_$t"; rm -rf "$d"; mkdir -p "$d"; cd "$d"
    w1 "$E/inputs_test_$t" > run.log 2>&1
    a="analysis.py"; [[ $t == *ramp ]] && a="analysis_ramp.py"
    printf '  %-28s ' "$t"
    python3 "$E/$a" . 2>&1 | tail -2 | tr '\n' ' '; echo
done
for t in 2d_laser_deposition_straight 2d_laser_deposition_oblique; do
    d="$OUT/ci_$t"; rm -rf "$d"; mkdir -p "$d"; cd "$d"
    w2 "$E/inputs_test_$t" > run.log 2>&1
    a="analysis_default_regression.py"; [[ $t == *oblique ]] && a="analysis_oblique.py"
    printf '  %-28s ' "$t"
    python3 "$E/$a" . 2>&1 | tail -2 | tr '\n' ' '; echo
done
echo; echo "=== done ==="
