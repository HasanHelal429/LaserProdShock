#!/usr/bin/env python3
"""The PIC noise floor on f_abs(0), from a seed sweep of one identical config.

WHY THIS EXISTS. The near-critical turning-point deposition is extremely sensitive to
per-cell density noise: `K ~ 1/sqrt(1 - n_e/n_cr)` diverges at the critical surface, and the
operator integrates that layer analytically over the *locally interpolated* density and
gradient. Both are noisy at finite ppc. So before any f_abs difference between two runs is
attributed to a geometry or boundary change, it has to clear the spread that statistically
identical runs already show.

    /opt/anaconda3/envs/physics/bin/python studies/fabs_noise/analyze.py
"""
from __future__ import annotations
import glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "LaserProdShock", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
import numpy as np
from laserprod import config as lpconfig, io as lpio

dirs = sorted(glob.glob(os.path.join(HERE, "scratch", "seed_*")),
              key=lambda d: int(os.path.basename(d).split("_")[1]))
rows = []
for d in dirs:
    cfg = lpconfig.load(d); sc = lpconfig.derive(cfg)
    h = lpio.laserdep_history(d)
    if not len(h):
        continue
    P = lpio.incident_power(sc, cfg)
    rows.append((int(cfg["numerics"]["random_seed"]), h.Pabs[0] / P))
if not rows:
    raise SystemExit("no variants; run studies/fabs_noise/run_variants.sh first")
f = np.array([r[1] for r in rows])
print("f_abs(0) across statistically identical runs (only the RNG seed differs):")
for s, v in rows:
    print(f"  seed {s:<3d}  f_abs(0) = {v:.4f}")
print(f"\n  n = {len(f)}   mean {f.mean():.4f}   std {f.std(ddof=1):.4f}   "
      f"range {f.min():.4f}..{f.max():.4f}")
print(f"  relative std      {f.std(ddof=1)/f.mean()*100:.2f}%")
print(f"  full spread       {(f.max()-f.min())/f.mean()*100:.2f}%")
print("\n  ANY f_abs(0) difference between two runs smaller than this is NOISE, not physics.")
