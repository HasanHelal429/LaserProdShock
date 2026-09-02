#!/bin/bash -l
# Generic single-GPU WarpX job body. ONE ARRAY TASK = ONE RUN.
#
# Do not sbatch this directly -- perlmutter/submit.sh supplies -A/-q/-t/--array and the
# RUNLIST/WORKROOT environment, all of which come from perlmutter/site.conf.
#
# Single-GPU by construction: every P5 config sets numerics.max_grid_size = n_cell, i.e.
# ONE box, and one box cannot be split across ranks. More GPUs would idle. That is also
# the fastest configuration -- 7.9x over the default decomposition in 1D (project memory).
#SBATCH -C gpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH -c 32
#SBATCH -G 1
#SBATCH -J laserprod
#SBATCH -o slurm-%A_%a.out
#SBATCH -e slurm-%A_%a.err
# Signal the job steps 10 min before the wall so WarpX (warpx.break_signals = HUP, emitted
# by deck.py whenever a leg asks for checkpoints) can stop cleanly and write a final
# checkpoint on the way out. Without this the wall arrives as SIGKILL and everything since
# the last scheduled checkpoint is lost -- which is how P5_flashic_off lost 65% of a 24 h
# run with nothing to resume from. Harmless on a leg with no checkpoint diagnostic: WarpX
# does not register the handler, and the signal is ignored.
#SBATCH --signal=1@600

set -euo pipefail
# shellcheck disable=SC1090
source "${LP_PM}/_common.sh"

IDX="${SLURM_ARRAY_TASK_ID:-0}"
SPEC="$(sed -n "$((IDX + 1))p" "${RUNLIST:?RUNLIST not set - submit via perlmutter/submit.sh}")"
[[ -n "$SPEC" ]] || { echo "job: no run at index $IDX in $RUNLIST" >&2; exit 2; }

RUN_REL="${SPEC%%:*}"
LABEL="${SPEC#*:}"
[[ "$LABEL" == "$SPEC" ]] && LABEL=""

run_warpx "$RUN_REL" "$LABEL"
