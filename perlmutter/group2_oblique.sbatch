#!/bin/bash -l
# GROUP 2 -- settle the oblique-absorption discrepancy found in Tier 2.
#
# run_turning_angles reported the turning DEPTH exactly right (0.6-1.4 cells across
# 0-60 deg, as ACCURACY.md documents) but the absorbed FRACTION 36-43% BELOW analytic at
# every oblique angle, against a documented 2.1%. Normal incidence agreed to 0.8%.
#
# Two independent checks, because the discrepancy has two possible homes:
#
#   1. The registered CI test test_2d_laser_deposition_oblique, which ships its own
#      closed-form reference in analysis_oblique.py (tau = A n_cr z_crit (16/15)
#      r_m^{5/2} for a linear ramp at theta0). If the operator were wrong at oblique
#      incidence this test should fail -- it is the same physics on a cleaner deck.
#   2. The angle sweep rerun with refraction = 0. ACCURACY.md's Finding 1 notes the
#      straight-ray path "turns EVERY oblique ray at n_m instead of no ray at all", so
#      the two modes are not interchangeable at angle and the baseline may have been
#      taken in the other one. Our Tier 2 runs reported refraction 1.
#
# The rerun goes to $PSCRATCH/tier_fixes/turning_r0 rather than into warpx-cda: the
# upstream driver writes its a<NN>/ dirs into $PWD, so running it elsewhere leaves the
# refraction = 1 results we already have intact for comparison.
#SBATCH -C gpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32
#SBATCH -G 1
#SBATCH -J lp5_g2_oblique
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.err
set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"
export MPICH_OFI_NIC_POLICY=GPU OMP_NUM_THREADS=16 MPLBACKEND=Agg
W=/pscratch/sd/h/hhelal/warpx-cda
LD=$W/laser_deposition
OUT=/pscratch/sd/h/hhelal/tier_fixes

mkdir -p "$OUT/bin"
cat > "$OUT/bin/w2" <<'WEOF'
#!/bin/bash
exec srun -n 1 --cpu-bind=cores /pscratch/sd/h/hhelal/warpx-cda/build_pm_23/bin/warpx.2d "$@"
WEOF
# same binary, but every invocation carries refraction = 0
cat > "$OUT/bin/w2_r0" <<'WEOF'
#!/bin/bash
exec srun -n 1 --cpu-bind=cores /pscratch/sd/h/hhelal/warpx-cda/build_pm_23/bin/warpx.2d "$@" laser_deposition.refraction=0
WEOF
chmod +x "$OUT/bin/w2" "$OUT/bin/w2_r0"

echo "=== GROUP 2 on $(hostname); commit $(cd $W && git rev-parse --short HEAD) ==="

echo; echo "--- [1] registered CI test: test_2d_laser_deposition_oblique"
mkdir -p "$OUT/ci_oblique"; cd "$OUT/ci_oblique"
"$OUT/bin/w2" "$W/Examples/Tests/laser_deposition/inputs_test_2d_laser_deposition_oblique" \
    > run.log 2>&1 && echo "    ran ok" || { echo "    RUN FAILED"; tail -5 run.log; }
python3 "$W/Examples/Tests/laser_deposition/analysis_oblique.py" . 2>&1 | tail -20 \
    || python3 "$W/Examples/Tests/laser_deposition/analysis_oblique.py" 2>&1 | tail -20

echo; echo "--- [2] angle sweep with refraction = 0"
mkdir -p "$OUT/turning_r0"; cd "$OUT/turning_r0"
WARPX_2D="$OUT/bin/w2_r0" "$LD/scripts/run_turning_angles.sh" 2>&1 | tail -8
echo; echo "    scoring refraction=0 sweep:"
python3 "$LD/scripts/plot_turning_angles.py" 2>&1 | tail -10

echo; echo "=== done ==="
