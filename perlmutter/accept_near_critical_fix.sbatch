#!/bin/bash -l
# ACCEPTANCE for 1c/1d/1e -- the first changes in this campaign that alter results.
#
# THE CRITERION, stated before the run: with the fix on, the lifted-FLASH ray_cfl ladder
# must CONVERGE. With it off that ladder drifts +18.3% over 0.50 -> 0.025 and the increment
# grows at the fine end. The measured run-to-run floor on E_abs is 0.80%, so "converged"
# means the last increment is inside a few times that and, above all, SHRINKING.
#
# Falsified by: a drift that still grows at the fine end. That would mean the near-critical
# branch has a second defect these three fixes do not reach, and 1c/1d/1e should not be
# presented as the fix.
#
# Three further things must hold, or the fix is not safe:
#   * overfrac -> ~0. Depositing at c_old instead of c is the whole point.
#   * the underdense control stays EXACTLY flat -- it has no turning point, so nothing
#     here should touch it. If it moves, the change is reaching code it should not.
#   * the registered operator CI tests still pass. run_profile_ramp HAS a turning point,
#     so a shift there is expected and is a result, not a failure -- it is reported, not
#     asserted.
#
# The A/B runs in ONE binary via laser_deposition.near_critical_fix, so nothing here is
# confounded by a rebuild.
#SBATCH -C gpu
#SBATCH -N 1 -n 1 -c 32 -G 1
#SBATCH -J lp5_accept
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.err
set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"
export MPICH_OFI_NIC_POLICY=GPU OMP_NUM_THREADS=16 MPLBACKEND=Agg
W1=/pscratch/sd/h/hhelal/warpx-fix/build_fix/bin/warpx.1d
W2=/pscratch/sd/h/hhelal/warpx-fix/build_fix/bin/warpx.2d
R=/pscratch/sd/h/hhelal/LaserProdShock/runs/P5
OUT=/pscratch/sd/h/hhelal/tier_fixes/accept; mkdir -p "$OUT"

run () {  # run <tag> <leg> <fixflag>
    local d="$OUT/$1"
    # Resume-friendly: a rung that already finished (AMReX prints "finalized" on a clean
    # exit) is not repeated, so a resubmission after a wall picks up where it stopped.
    if [[ -f "$d/run.log" ]] && tail -1 "$d/run.log" | grep -q finalized; then
        printf '%s' "$(grep -oE 'Eabs [0-9.e+-]+' "$d/run.log" | tail -1 | awk '{print $2}')"
        return
    fi
    rm -rf "$d"; mkdir -p "$d"; cd "$d"
    cp "$R/$2/inputs_$2" deck; cp "$R/$2/ic_flash.yaml" . 2>/dev/null || true
    srun -n 1 --cpu-bind=cores "$W1" deck laser_deposition.near_critical_fix="$3" \
        > run.log 2>&1
    printf '%s' "$(grep -oE 'Eabs [0-9.e+-]+' run.log | tail -1 | awk '{print $2}')"
}
ovf () { grep -oE 'overfrac [0-9.e+-]+' "$OUT/$1/run.log" | awk '{print $2}' | sort -g | tail -1; }

echo "=== [1] lifted-FLASH ray_cfl ladder: fix OFF vs ON ==="
printf '  %-8s %14s %14s   %s\n' "ray_cfl" "OFF" "ON" "max overfrac (ON)"
declare -A ON OFF
for r in 050 025 010 005 0025; do
    OFF[$r]=$(run "off_$r" "P5_raycfl_$r" 0)
    ON[$r]=$(run "on_$r"  "P5_raycfl_$r" 1)
    printf '  %-8s %14s %14s   %s\n' "$r" "${OFF[$r]}" "${ON[$r]}" "$(ovf "on_$r")"
done
python3 - <<PY
off=[${OFF[050]},${OFF[025]},${OFF[010]},${OFF[005]},${OFF[0025]}]
on =[${ON[050]},${ON[025]},${ON[010]},${ON[005]},${ON[0025]}]
def rep(name,v):
    inc=[100*(v[i+1]-v[i])/v[i] for i in range(len(v)-1)]
    print(f"  {name:4} total {100*(v[-1]-v[0])/v[0]:+.2f}%   increments " +
          ", ".join(f"{i:+.2f}%" for i in inc))
    return inc
print()
io=rep("OFF",off); ie=rep("ON",on)
print()
print(f"  last increment: OFF {io[-1]:+.2f}%  ON {ie[-1]:+.2f}%   (seed floor 0.80%)")
print(f"  shrinking at the fine end?  OFF {abs(io[-1])<abs(io[-2])}   ON {abs(ie[-1])<abs(ie[-2])}")
PY

echo; echo "=== [2] underdense control must not move (it has no turning point) ==="
u0=$(run "und_off" P5_under_025 0); u1=$(run "und_on" P5_under_025 1)
echo "  OFF $u0    ON $u1"

echo; echo "=== [3] registered operator CI tests, fix ON ==="
E=/pscratch/sd/h/hhelal/warpx-cda/Examples/Tests/laser_deposition
for t in 1d_laser_deposition 1d_laser_deposition_ramp; do
    d="$OUT/ci_$t"; rm -rf "$d"; mkdir -p "$d"; cd "$d"
    srun -n 1 --cpu-bind=cores "$W1" "$E/inputs_test_$t" > run.log 2>&1
    a="analysis.py"; [[ $t == *ramp ]] && a="analysis_ramp.py"
    printf '  %-28s ' "$t"; python3 "$E/$a" . 2>&1 | tail -1
done
d="$OUT/ci_obl"; rm -rf "$d"; mkdir -p "$d"; cd "$d"
srun -n 1 --cpu-bind=cores "$W2" "$E/inputs_test_2d_laser_deposition_oblique" > run.log 2>&1
printf '  %-28s ' "2d_oblique"; python3 "$E/analysis_oblique.py" . 2>&1 | tail -1
echo; echo "=== done ==="
