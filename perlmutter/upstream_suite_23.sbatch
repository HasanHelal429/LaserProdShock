#!/bin/bash -l
# TIER 2 (2D/3D) -- the half of warpx-cda's accuracy suite that a 1D build cannot run.
#
#   sbatch -A <proj> -q shared -t 04:00:00 perlmutter/upstream_suite_23.sbatch
#
# run_convergence is the one that matters most here: it is upstream's OWN discretization
# study, and ACCURACY.md's claim that "the ray_cfl and n_cell sweeps give bit-identical
# answers at equal ray_cfl x dz, because multilinear density interpolation is exact for a
# linear ramp" is the sentence the whole 2026-08-31 diagnosis turns on. Re-running it here
# tests that explanation on this build rather than taking it on trust.
#
# run_turning_angles is the oblique turning-point test, n_e(z_m) = n_cr cos^2(theta0). It
# covers most of what Tier 3d wanted and 1D cannot do at all (config.py refuses a nonzero
# incidence_angle_deg in 1D).
#
# run_laser_shock_2d is NOT here: 118000 steps at 160x3200 is ~12 h on one A100, and it is
# a physics application run rather than an operator check. ACCURACY.md lists it under "Not
# covered"; it stays that way for now, deliberately.
#SBATCH -C gpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32
#SBATCH -G 1
#SBATCH -J lp5_upstream23
#SBATCH -o slurm-%j.out
#SBATCH -e slurm-%j.err

set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"

LD="${LD_DIR:-$PSCRATCH/warpx-cda/laser_deposition}"
B1="$PSCRATCH/warpx-cda/build_pm_1d/bin/warpx.1d"
B2="$PSCRATCH/warpx-cda/build_pm_23/bin/warpx.2d"
B3="$PSCRATCH/warpx-cda/build_pm_23/bin/warpx.3d"
for b in "$B1" "$B2" "$B3"; do [[ -x "$b" ]] || { echo "missing binary $b" >&2; exit 1; }; done

mkwrap () { local out="$1" bin="$2"; cat > "$out" <<WEOF
#!/bin/bash
exec srun -n 1 --cpu-bind=cores $bin "\$@"
WEOF
chmod +x "$out"; }
D="${SLURM_SUBMIT_DIR:-$PWD}"
mkwrap "$D/.w1" "$B1"; mkwrap "$D/.w2" "$B2"; mkwrap "$D/.w3" "$B3"
export WARPX_1D="$D/.w1" WARPX_2D="$D/.w2" WARPX_3D="$D/.w3"
export MPICH_OFI_NIC_POLICY=GPU OMP_NUM_THREADS=16

echo "=== TIER 2 (2D/3D) on $(hostname) ==="
echo "commit: $(cd $PSCRATCH/warpx-cda && git rev-parse HEAD)"; echo

one () { local d="$1" deck="$2" w="$3"; shift 3
    echo "--- $d"
    ( cd "$LD/$d" && "$w" "$deck" "$@" > run.log 2>&1 ); local rc=$?
    if [[ $rc -ne 0 ]]; then echo "    FAILED rc=$rc"; tail -6 "$LD/$d/run.log" | sed 's/^/    /'
    else echo "    ok  $(grep -m1 -o 'Pabs [^ ]*' "$LD/$d/run.log" 2>/dev/null || echo '')"; fi; }

one run_psc_oblique  inputs_psc_oblique  "$WARPX_2D"
one run_refraction   "$(ls $LD/run_refraction/inputs_* | head -1 | xargs basename)" "$WARPX_2D"
one run_expanding    inputs_expanding_laser "$WARPX_2D"   # NOT inputs_expanding -- the deck carries the _laser suffix
one run_3d_slab      inputs_3d_slab      "$WARPX_3D"

for s in run_turning_angles run_convergence; do
    echo "--- $s (sweep)"
    ( cd "$LD/$s" && "$LD/scripts/${s}.sh" ) 2>&1 | sed 's/^/    /'
done
echo; echo "=== done ==="
