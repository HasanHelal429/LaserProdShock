#!/bin/bash -l
# Render the P6 mass-convention movies with FLASH overlaid. CPU job, not a login-node
# process: two session teardowns killed background renders, and loading ~130 particle
# dumps through yt is not login-node work.
#
#   sbatch -A m5032 -q shared -C cpu perlmutter/render_p6_movies.sbatch
#
# Two movies, because the legs are not all complete yet and the script caps every frame at
# the SHORTEST leg (so no frame silently repeats a finished leg's last dump):
#   movie_flash_heavy_light.mp4  heavy + light + FLASH, the WHOLE 1 ns pulse (both done)
#   movie_flash_all3.mp4         + full, but only as far as the full leg has run
#SBATCH -N 1 -n 1 -c 16
#SBATCH -t 02:00:00
#SBATCH -J lp6_movies
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.err
set -uo pipefail
source "$HOME/perlmutter_gpu_warpx.profile"
export LP_FLASH_DIR=/pscratch/sd/h/hhelal/flash/Ablation_prod_08-17
export MPLBACKEND=Agg
cd /pscratch/sd/h/hhelal/LaserProdShock
echo "=== movie 1: heavy + light vs FLASH, full pulse ==="
python3 -u scripts/p6_movie.py --legs heavy light --out media/P6/movie_flash_heavy_light.mp4 2>&1 | grep -v '^yt :'
echo "=== movie 2: all three vs FLASH, to the full leg's extent ==="
python3 -u scripts/p6_movie.py --out media/P6/movie_flash_all3.mp4 2>&1 | grep -v '^yt :'
echo "=== done ==="; ls -l media/P6/*.mp4
