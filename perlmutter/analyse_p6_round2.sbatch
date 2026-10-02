#!/bin/bash -l
#SBATCH -N 1 -n 1 -c 16
#SBATCH -t 02:00:00
#SBATCH -J lp6_round2
#SBATCH -o /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.out
#SBATCH -e /pscratch/sd/h/hhelal/LaserProdShock/slurm-%j.err
source "$HOME/perlmutter_gpu_warpx.profile"
export LP_FLASH_DIR=/pscratch/sd/h/hhelal/flash/Ablation_prod_08-17 MPLBACKEND=Agg
cd /pscratch/sd/h/hhelal/LaserProdShock
python3 -u scripts/p6_g3.py --legs full heavy light_sim light ${DZ:+heavy_dz025} 2>&1 | grep -v '^yt :'
python3 -u scripts/p6_movie.py --legs full heavy light_sim ${DZ:+heavy_dz025} --out media/P6/movie_flash_round2.mp4 2>&1 | grep -v '^yt :'
