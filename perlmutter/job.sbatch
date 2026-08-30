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
