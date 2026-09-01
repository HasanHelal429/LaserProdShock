#!/bin/bash -l
# TIER 2 -- run warpx-cda's own laser-deposition accuracy suite on THIS build.
#
#   sbatch -A <proj> -q shared -t 04:00:00 perlmutter/upstream_suite.sbatch
#
# The suite in warpx-cda/laser_deposition/ carries documented baselines in ACCURACY.md
# (Beer-Lambert profile exact to 0.000% over 510 interior cells, tracer energy closure
# 1.000000, coefficient audit flat to 1e-5 over 275x in K, and so on). None of it has ever
# been run on a Perlmutter CUDA build -- every number in ACCURACY.md was measured on
# chablis. Re-running is a regression check on the binary P5 is being produced with, and
# it also gives us the analytic-comparison harness the P5 ladders lack.
#
# ONLY the 1D tests are here. run_convergence, run_turning_angles, run_refraction,
# run_expanding, run_psc_oblique and run_laser_shock_2d are 2D and run_3d_slab is 3D;
# they need build_pm_23, which is a separate target.
#SBATCH -C gpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32
#SBATCH -G 1
#SBATCH -J lp5_upstream
#SBATCH -o slurm-%j.out
#SBATCH -e slurm-%j.err

set -uo pipefail          # NOT -e: one failing test must not abort the suite
source "$HOME/perlmutter_gpu_warpx.profile"

LD="${LD_DIR:-$PSCRATCH/warpx-cda/laser_deposition}"
BIN="${WARPX_BIN:-$PSCRATCH/warpx-cda/build_pm_1d/bin/warpx.1d}"
[[ -x "$BIN" ]] || { echo "no binary at $BIN" >&2; exit 1; }

# The upstream sweep scripts invoke "$WARPX_1D" directly. On Perlmutter a WarpX built with
# MPI must be launched through srun, so point them at a wrapper instead of the raw binary.
WRAP="${SLURM_SUBMIT_DIR:-$PWD}/.warpx1d_srun"
cat > "$WRAP" <<WEOF
#!/bin/bash
exec srun -n 1 --cpu-bind=cores $BIN "\$@"
WEOF
chmod +x "$WRAP"
export WARPX_1D="$WRAP"

export MPICH_OFI_NIC_POLICY=GPU
export OMP_NUM_THREADS=16

echo "=== TIER 2 (1D) on $(hostname) ==="
echo "binary: $BIN"
echo "commit: $(cd $PSCRATCH/warpx-cda && git rev-parse HEAD)"
echo

one () {   # one <dir> <deck> [overrides...]
    local d="$1" deck="$2"; shift 2
    echo "--- $d"
    ( cd "$LD/$d" && "$WRAP" "$deck" "$@" > run.log 2>&1 )
    local rc=$?
    if [[ $rc -ne 0 ]]; then
        echo "    FAILED rc=$rc"; tail -5 "$LD/$d/run.log" | sed 's/^/    /'
    else
        echo "    ok  $(grep -m1 -o 'Pabs [^ ]*' "$LD/$d/run.log" 2>/dev/null || echo '')"
    fi
}

# Cheap first (1-100 steps, 256-1250 cells): a setup mistake surfaces in seconds.
one run_psc_xcheck      inputs_psc_xcheck
one run_sharp_edge      inputs_sharp_edge
one run_te_gradient     inputs_te_gradient
mkdir -p "$LD/run_te_gradient/fixed"
( cd "$LD/run_te_gradient/fixed" && "$WRAP" ../inputs_te_gradient \
      laser_deposition.temperature_mode=fixed > run.log 2>&1 ) \
  && echo "--- run_te_gradient/fixed ok"
one run_profile_uniform inputs_profile_uniform
one run_profile_ramp    inputs_profile_ramp
one run_testC_match     inputs_testC_match

# Sweeps (many short runs each)
for s in run_scaling run_te_error; do
    echo "--- $s (sweep)"
    ( cd "$LD/$s" && "$LD/scripts/${s}.sh" ) 2>&1 | sed 's/^/    /'
done

# The long ones
one run_energy_closure  inputs_energy_closure          # 63000 steps
one run_laser_shock_dt  inputs_laser_shock_dt          # 30000 steps, the CORRECTED deck

echo
echo "=== done ==="
