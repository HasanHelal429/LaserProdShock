#!/bin/bash -l
# PHYSICS VALIDATION of the merged operator fixes (near-critical + species electron mass).
#
# Three groups. A is the regression: every one of these compares against a CLOSED-FORM
# reference, not against a previous run, so it tests physics rather than reproducibility.
# B and C test what each fix claims.
#SBATCH -C gpu
#SBATCH -N 1 -n 1 -c 32 -G 1
#SBATCH -J lp5_physval
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.err
set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"
export MPICH_OFI_NIC_POLICY=GPU OMP_NUM_THREADS=16 MPLBACKEND=Agg
B1=/pscratch/sd/h/hhelal/warpx-fix/build_fix/bin/warpx.1d
B2=/pscratch/sd/h/hhelal/warpx-fix/build_fix/bin/warpx.2d
W=/pscratch/sd/h/hhelal/warpx-cda
E=$W/Examples/Tests/laser_deposition
LD=$W/laser_deposition
O=/pscratch/sd/h/hhelal/tier_fixes/physval
ME=9.1093837015e-31
mkdir -p "$O"
w1(){ srun -n 1 --cpu-bind=cores "$B1" "$@"; }
w2(){ srun -n 1 --cpu-bind=cores "$B2" "$@"; }

echo "=== binary: $(ls -la $B1 | awk '{print $6,$7,$8}') ==="
echo "=== commit: $(cd /pscratch/sd/h/hhelal/warpx-fix && git rev-parse --short HEAD) ==="

echo; echo "########## A. REGRESSION vs CLOSED-FORM THEORY ##########"
for t in 1d_laser_deposition 1d_laser_deposition_ramp; do
    d=$O/ci_$t; rm -rf $d; mkdir -p $d; cd $d
    w1 $E/inputs_test_$t > run.log 2>&1
    a=analysis.py; [[ $t == *ramp ]] && a=analysis_ramp.py
    printf '  %-26s ' "$t"; python3 $E/$a . 2>&1 | tail -1
done
d=$O/ci_obl; rm -rf $d; mkdir -p $d; cd $d
w2 $E/inputs_test_2d_laser_deposition_oblique > run.log 2>&1
printf '  %-26s ' "2d_oblique"; python3 $E/analysis_oblique.py . 2>&1 | tail -1

echo; echo "--- Beer-Lambert profile + fitted K (exact interior expected) ---"
d=$LD/run_profile_uniform; cd $d && w1 inputs_profile_uniform > run.log 2>&1
python3 ../scripts/plot_profile_uniform.py 2>&1 | grep -E 'ratio|residual'

echo; echo "--- coefficient audit: every factor in K against theory ---"
cd $LD/run_scaling && WARPX_1D=$B1 ../scripts/run_scaling.sh > sweep.log 2>&1
python3 ../scripts/plot_scaling.py 2>&1 | tail -8

echo; echo "--- energy closure: tracer vs particles vs I0*t ---"
cd $LD/run_energy_closure && w1 inputs_energy_closure > run.log 2>&1
python3 ../scripts/plot_energy_closure.py 2>&1 | grep -E 'ratio|tracer|KE gain'

echo; echo "########## B. NEAR-CRITICAL FIX ##########"
R=/pscratch/sd/h/hhelal/LaserProdShock/runs/P5
for leg in P5_raycfl_025 P5_under_025; do
    d=$O/nc_$leg; rm -rf $d; mkdir -p $d; cd $d
    cp $R/$leg/inputs_$leg deck; cp $R/$leg/ic_flash.yaml . 2>/dev/null || true
    w1 deck laser_deposition.refraction=0 > run.log 2>&1
    printf '  %-16s Eabs=%-11s max overfrac=%s\n' "$leg" \
      "$(grep -oE 'Eabs [0-9.e+-]+' run.log|tail -1|awk '{print $2}')" \
      "$(grep -oE 'overfrac [0-9.e+-]+' run.log|awk '{print $2}'|sort -g|tail -1)"
done

echo; echo "########## C. SPECIES ELECTRON MASS ##########"
echo "  n_cr must scale LINEARLY with the electron mass (n_cr = eps0 m_e omega^2/e^2),"
echo "  and particle KE gain must equal the tracer's E_abs at every mass."
for a in 1 2 4; do
    m=$(python3 -c "print(f'{$a*$ME:.10e}')")
    d=$O/mass_x$a; rm -rf $d; mkdir -p $d; cd $d
    w1 $O/../massfix/deck_heavy electrons.mass=$m > run.log 2>&1
    printf '  x%-2s  n_cr=%-13s Eabs=%-12s KEgain=%s\n' "$a" \
      "$(grep -oE 'rescaled to [0-9.e+-]+' run.log|tail -1|awk '{print $3}')" \
      "$(grep -oE 'Eabs [0-9.e+-]+' run.log|tail -1|awk '{print $2}')" \
      "$(python3 -c "
import numpy as np,glob
f=glob.glob('diags/reducedfiles/EP.txt')
a=np.loadtxt(f[0],skiprows=1) if f else None
print(f'{a[-1,3]-a[0,3]:.6e}' if f else 'n/a')" 2>/dev/null)"
done
echo
echo "  CONTROL -- 4x electron with the operator forced to the REAL mass (the old bug):"
d=$O/mass_x4_bug; rm -rf $d; mkdir -p $d; cd $d
w1 $O/../massfix/deck_heavy electrons.mass=$(python3 -c "print(f'{4*$ME:.10e}')") \
   laser_deposition.electron_mass=$ME > run.log 2>&1
printf '  bug  n_cr=%-13s Eabs=%-12s KEgain=%s\n' \
  "$(grep -oE 'rescaled to [0-9.e+-]+' run.log|tail -1|awk '{print $3}')" \
  "$(grep -oE 'Eabs [0-9.e+-]+' run.log|tail -1|awk '{print $2}')" \
  "$(python3 -c "
import numpy as np,glob
f=glob.glob('diags/reducedfiles/EP.txt')
a=np.loadtxt(f[0],skiprows=1) if f else None
print(f'{a[-1,3]-a[0,3]:.6e}' if f else 'n/a')" 2>/dev/null)"
echo; echo "=== done ==="
