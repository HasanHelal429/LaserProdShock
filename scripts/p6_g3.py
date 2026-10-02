#!/usr/bin/env python3
"""P6 plume T_e and geometry with each leg's OWN G3 laser-off background subtracted.

    python3 scripts/p6_g3.py [--legs full heavy light_sim ...] [--taus 4 8 12 16 20 24]

Writes ``media/P6/g3_table.txt``.

Plume T_e is the density-weighted mean over 0.01-1 n_cr (xcode_compare.scalars). The G3
correction subtracts the laser-off leg's plume T_e at the same tau_own, each on its own band:
grid heating differs between legs (dz/lambda_D 58 vs 249), so a shared control is useless.
Geometry (zeta_cr, L_n, zeta_front) is reported RAW -- the laser-off target barely expands,
so there is no background to subtract from it.

Ratios are to `full` (mu = 1, real electron), the reference. Predictions: a similarity-scaled
reduced-mass leg should give T_e/full = mu^(1/3) = 0.379 at mu = 0.0545.
"""
import argparse, os, sys, warnings
warnings.filterwarnings("ignore")
H = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(H, "..", "src"), H]
import numpy as np
from xcode_compare import load_leg, leg_state, scalars

ROOT = os.path.join(H, "..")
RID = dict(full="P6_mr_full", heavy="P6_mr_heavy", light="P6_mr_light",
           light_sim="P6_mr_light_sim", heavy_dz025="P6_mr_heavy_dz025")
KEYS = ["Te_mean_plume", "zeta_cr", "L_n", "zeta_front"]


def state(leg, t):
    st = leg_state(leg, t)
    if st is None or st["stale"]:
        return None
    return scalars(st["zeta"], st["ne"], st["Te"], st["v"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs", nargs="*", default=["full", "heavy", "light_sim", "light", "heavy_dz025"])
    ap.add_argument("--taus", nargs="*", type=float, default=[4, 8, 12, 16, 20, 23.7])
    ap.add_argument("--out", default=os.path.join(ROOT, "media/P6/g3_table.txt"))
    a = ap.parse_args()
    L = {}
    for n in a.legs:
        p = os.path.join(ROOT, "runs/P6", RID[n])
        try:
            L[n] = (load_leg(n, p, "k", zeta_range=(-5, 115)),
                    load_leg(n + "_off", p + "_off", "k", zeta_range=(-5, 115)))
            print(f"loaded {n}: {len(L[n][0]['S'])} dumps, mu={L[n][0]['sc']['mu']:.4f}", flush=True)
        except Exception as e:
            print(f"skip {n}: {e}", flush=True)
    out = ["P6 plume T_e, G3-subtracted (own laser-off control), and raw geometry; ratios to full",
           f"{'tau':>5} {'leg':<12} {'Te_raw':>8} {'Te_off':>8} {'Te_G3':>8} {'G3/full':>8}"
           f" {'zeta_cr':>8} {'/full':>6} {'L_n':>7} {'/full':>6} {'z_front':>8} {'/full':>6}"]
    for t in a.taus:
        rows = {}
        for n, (on, off) in L.items():
            s_on, s_off = state(on, t), state(off, t)
            if s_on is None:
                continue
            te_off = s_off["Te_mean_plume"] if s_off else np.nan
            rows[n] = (s_on, te_off, s_on["Te_mean_plume"] - (te_off if np.isfinite(te_off) else 0))
        ref = rows.get("full")
        for n, (s, toff, tg3) in rows.items():
            r = lambda k, v: v / ref[0][k] if ref and ref[0][k] else np.nan
            rg = tg3 / ref[2] if ref else np.nan
            out.append(f"{t:5.1f} {n:<12} {s['Te_mean_plume']:8.1f} {toff:8.1f} {tg3:8.1f} {rg:8.3f}"
                       f" {s['zeta_cr']:8.3f} {r('zeta_cr', s['zeta_cr']):6.2f}"
                       f" {s['L_n']:7.2f} {r('L_n', s['L_n']):6.2f}"
                       f" {s['zeta_front']:8.2f} {r('zeta_front', s['zeta_front']):6.2f}")
        out.append("")
    open(a.out, "w").write("\n".join(out) + "\n")
    print("\n".join(out)); print("wrote", a.out)


if __name__ == "__main__":
    main()
