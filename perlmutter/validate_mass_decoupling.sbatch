#!/bin/bash -l
# VALIDATION of the optical/dynamical electron-mass split.
#
# Claim under test: `laser_deposition.electron_mass` now pins ONLY the optical mass
# (n_cr, the IB coefficient, the lnLambda cutoffs). The kick and momenta->T always use
# the heated species' own mass. That is what makes the heavy-electron reduced-mass-ratio
# convention (PSC's) runnable: n_cr stays at the real laser value while m_e inflates.
#
# Falsifiable predictions, written BEFORE the runs:
#   A. BACKWARD COMPATIBILITY. With no `electron_mass` input, nothing changes: n_cr is
#      still linear in the species mass and KE gain / Eabs is still 1.0. The 1x leg must
#      reproduce Eabs = 4.46124e+06 from job 58221478.
#   B. THE SPLIT. With `electron_mass` pinned real and a heavy species, n_cr must be
#      UNCHANGED at 1.0054520e+27, and KE gain / Eabs must be 1.0 -- where the same
#      configuration measured 3.98 before the split. A "masses DECOUPLED" line must
#      appear; its absence means the pin silently did nothing.
#   C. OPTICS INVARIANT. With the optics pinned, Eabs must be essentially independent of
#      the species mass, because K and n_cr no longer move with it.
#SBATCH -C gpu
#SBATCH -N 1 -n 1 -c 32 -G 1
#SBATCH -J lp5_decouple
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.err
set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"
export MPICH_OFI_NIC_POLICY=GPU OMP_NUM_THREADS=16 MPLBACKEND=Agg
B1=/pscratch/sd/h/hhelal/warpx-fix/build_fix/bin/warpx.1d
W=/pscratch/sd/h/hhelal/warpx-cda
E=$W/Examples/Tests/laser_deposition
O=/pscratch/sd/h/hhelal/tier_fixes/decouple
DECK=/pscratch/sd/h/hhelal/tier_fixes/massfix/deck_heavy
ME=9.1093837015e-31
mkdir -p "$O"
w1(){ srun -n 1 --cpu-bind=cores "$B1" "$@"; }

# KE gain from column 3 (electrons), NOT [2:] -- see GOTCHAS on EP.txt columns.
keg(){ python3 -c "
import numpy as np,glob
f=glob.glob('diags/reducedfiles/EP.txt')
a=np.loadtxt(f[0],skiprows=1) if f else None
print(f'{a[-1,3]-a[0,3]:.6e}' if f else 'nan')" 2>/dev/null; }
# n_cr AFTER resolution -- the 'rescaled to' line if present, else the setup value.
ncr(){ r=$(grep -oE 'rescaled to [0-9.e+-]+' run.log|tail -1|awk '{print $3}')
       [ -n "$r" ] || r=$(grep -m1 -oE 'n_cr [0-9.e+-]+' run.log|awk '{print $2}')
       echo "$r"; }
eabs(){ grep -oE 'Eabs [0-9.e+-]+' run.log|tail -1|awk '{print $2}'; }
row(){ local k e r
       k=$(keg); e=$(eabs)
       r=$(awk -v k="$k" -v e="$e" 'BEGIN{ if (e+0!=0 && k!="nan") printf "%.4f", k/e; else printf "n/a" }')
       printf '  %-22s n_cr=%-15s Eabs=%-13s KEgain=%-13s ratio=%s\n' "$1" "$(ncr)" "$e" "$k" "$r"; }

echo "=== binary: $(ls -la $B1 | awk '{print $6,$7,$8}') ==="
echo "=== commit: $(cd /pscratch/sd/h/hhelal/warpx-fix && git rev-parse --short HEAD) ==="

echo; echo "########## A. BACKWARD COMPATIBILITY (no electron_mass input) ##########"
echo "   expect n_cr linear in mass, ratio 1.0, and x1 Eabs = 4.46124e+06"
for a in 1 4; do
    m=$(python3 -c "print(f'{$a*$ME:.10e}')")
    d=$O/compat_x$a; rm -rf $d; mkdir -p $d; cd $d
    w1 $DECK electrons.mass=$m > run.log 2>&1
    row "x$a (unpinned)"
done

echo; echo "########## B. THE SPLIT (electron_mass pinned to the real mass) ##########"
echo "   expect n_cr FROZEN at 1.0054520e+27 and ratio 1.0 (was 3.98 before the split)"
MP100=1.67262192e-29     # m_p/100 = 18.36 x m_e : the PSC convention
for spec in "4 $(python3 -c "print(f'{4*$ME:.10e}')")" "18.36 $MP100"; do
    set -- $spec
    d=$O/pin_x$1; rm -rf $d; mkdir -p $d; cd $d
    w1 $DECK electrons.mass=$2 laser_deposition.electron_mass=$ME > run.log 2>&1
    row "x$1 (optics pinned)"
    if grep -q 'masses DECOUPLED' run.log; then echo "      DECOUPLED line present"
    else echo "      *** NO 'masses DECOUPLED' LINE -- the pin did nothing ***"; fi
done

echo; echo "########## D. THE OTHER TWO CHANGED SITES ##########"
echo "   deck_heavy runs constant-lnLambda and fixed-T, so A-C never touch coulombLog"
echo "   (me_opt) or momenta->T (me_dyn). Force both modes on so all four sites run."
echo "   expect ratio 1.0 with the optics pinned, and n_cr still frozen."
MODES="laser_deposition.coulomb_log_mode=ib laser_deposition.temperature_mode=local"
d=$O/modes_unpinned; rm -rf $d; mkdir -p $d; cd $d
w1 $DECK electrons.mass=$MP100 $MODES > run.log 2>&1
row "x18.36 unpinned"
d=$O/modes_pinned; rm -rf $d; mkdir -p $d; cd $d
w1 $DECK electrons.mass=$MP100 laser_deposition.electron_mass=$ME $MODES > run.log 2>&1
row "x18.36 pinned"
grep -q 'masses DECOUPLED' run.log && echo "      DECOUPLED line present" \
                                   || echo "      *** NO DECOUPLED LINE ***"

echo; echo "########## C. CI REGRESSION (nothing else moved) ##########"
for t in 1d_laser_deposition 1d_laser_deposition_ramp; do
    d=$O/ci_$t; rm -rf $d; mkdir -p $d; cd $d
    w1 $E/inputs_test_$t > run.log 2>&1
    a=analysis.py; [[ $t == *ramp ]] && a=analysis_ramp.py
    printf '  %-26s ' "$t"; python3 $E/$a . 2>&1 | tail -1
done
echo; echo "=== done ==="
