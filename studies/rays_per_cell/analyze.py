#!/usr/bin/env python3
"""Reduce the rays_per_cell ladder: does sub-cell ray sampling change the spot's profile?

The measurement is absolute, not relative. At step 0 the target's density is the one the
deck built (a 0.01 % ripple from `NUniformPerCell`), and the slab is optically thick
(tau ~ 1400), so every ray is fully absorbed and the column-integrated absorbed power MUST
equal the incident `I0*exp(-(x/w0)^2)*dx` in that column. No fitting, no reference run.

Two numbers separate the two ways sub-sampling could matter:

* the **mean** ratio to the analytic profile, and the measured 1/e radius -- these test
  whether one ray per cell resolves the BEAM;
* the column-to-column **scatter** and its lag-1 autocorrelation -- these test how far
  individual rays wander through the density ripple. Scatter that is anti-correlated at
  lag 1 is power exchanged between neighbours and averages out of any multi-column
  measure, which is what `f_ax` in `scripts/spot_report.py` is.

    python studies/rays_per_cell/analyze.py            # all variants in scratch/
"""

from __future__ import annotations

import glob
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import io as lpio           # noqa: E402
from laserprod import plotting as lpp      # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
from spot_report import SpotDump           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = "rays_per_cell"


def variants():
    out = []
    for d in sorted(glob.glob(os.path.join(HERE, "scratch", "rpc_*"))):
        try:
            cfg = lpconfig.load(d)
        except Exception as exc:                      # a variant that failed to launch
            print(f"  (skipping {os.path.basename(d)}: {exc})")
            continue
        paths = lpio.profile_tables(cfg["_run_dir"])
        if not paths:
            print(f"  (skipping {os.path.basename(d)}: no profile dump -- did it run?)")
            continue
        out.append((int((cfg["laser"]["beam"] or {}).get("rays_per_cell", 1)), cfg, paths[0]))
    return sorted(out)


def main() -> int:
    vs = variants()
    if not vs:
        print("no variants with output in studies/rays_per_cell/scratch -- run "
              "studies/rays_per_cell/run_variants.sh first")
        return 1

    rows = []
    for rpc, cfg, path in vs:
        sc = lpconfig.derive(cfg)
        w0 = float(cfg["laser"]["beam"]["waist_de"]) * sc.de_ref
        d = SpotDump(path, sc, cfg)
        launch = sc.intensity * np.exp(-((d.xs / w0) ** 2)) * d.dx
        sel = np.exp(-((d.xs / w0) ** 2)) > 1e-3
        r = d.Pcol[sel] / launch[sel]
        P_inc = lpio.incident_power(sc, cfg)
        # measured 1/e radius of the deposition profile, by interpolation on the right wing
        prof = d.Pcol / d.Pcol.max()
        right = d.xs > 0
        w_meas = float(np.interp(math.exp(-1.0), prof[right][::-1], d.xs[right][::-1]))
        rough, ac1 = d.roughness()
        rows.append(dict(rpc=rpc, f_abs=d.total / P_inc, mean=r.mean(), scatter=r.std(),
                         rough=rough, ac1=ac1, w=w_meas / sc.de_ref, w0=w0 / sc.de_ref,
                         total=d.total, inc=P_inc, dump=d, sc=sc, cfg=cfg))

    print(f"RAYS_PER_CELL LADDER -- {len(rows)} variants, step-0 deposition vs analytic "
          f"I0*exp(-(x/w0)^2)")
    hdr = (f"{'rpc':>4} {'f_abs(0)':>9} {'mean ratio':>11} {'scatter':>8} {'rough':>7} "
           f"{'ac1':>6} {'w_1/e [d_e]':>12}")
    print(hdr)
    print("-" * len(hdr))
    for x in rows:
        print(f"{x['rpc']:4d} {x['f_abs']:9.6f} {x['mean']:11.5f} {x['scatter']*100:7.3f}% "
              f"{x['rough']*100:6.2f}% {x['ac1']:+6.2f} {x['w']:12.2f}")

    base = rows[0]
    print(f"\nset waist w0 = {base['w0']:g} d_e; {2*base['rpc']} sample(s) per d_e at "
          f"rays_per_cell = {base['rpc']}")
    if len(rows) > 1:
        dm = max(abs(x["mean"] / base["mean"] - 1.0) for x in rows[1:]) * 100
        ds = rows[-1]["scatter"] / base["scatter"]
        print(f"MEAN moves by at most {dm:.3f} % across the ladder; "
              f"SCATTER changes by x{ds:.2f} from rpc = {base['rpc']} to {rows[-1]['rpc']}")
        print("  -> the mean is what f_ax averages over, so a ladder that moves only the "
              "scatter\n     leaves the finite-spot result intact; a ladder that moves the "
              "mean does not.")

    # figure: the profiles on top of each other, and the residual per column
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.0, 6.6), sharex=True)
    cols = [lpp.C_LASER, lpp.C_TARGET, lpp.C_AMBIENT, lpp.C_FOURTH]
    for i, x in enumerate(rows):
        d, sc = x["dump"], x["sc"]
        w0 = x["w0"] * sc.de_ref
        launch = sc.intensity * np.exp(-((d.xs / w0) ** 2)) * d.dx
        c = cols[i % len(cols)]
        ax1.plot(d.xs / sc.de_ref, d.Pcol / launch.max(), color=c, lw=1.1,
                 label=f"rays_per_cell = {x['rpc']}")
        sel = np.exp(-((d.xs / w0) ** 2)) > 1e-3
        ax2.plot(d.xs[sel] / sc.de_ref, (d.Pcol[sel] / launch[sel] - 1.0) * 100,
                 color=c, lw=0.9)
    d0, sc0 = rows[0]["dump"], rows[0]["sc"]
    w00 = rows[0]["w0"] * sc0.de_ref
    lau = sc0.intensity * np.exp(-((d0.xs / w00) ** 2)) * d0.dx
    ax1.plot(d0.xs / sc0.de_ref, lau / lau.max(), color=lpp.INK, ls="--", lw=1.3,
             label="analytic I(x)")
    ax1.set_yscale("log")
    ax1.set_ylim(1e-8, 3)
    ax1.set_ylabel("column P$_{abs}$ / peak incident")
    ax1.set_title("Step-0 deposition profile vs sub-ray sampling", loc="left",
                  fontweight="bold", fontsize=9.5)
    ax1.legend(fontsize=8)
    lpp.style_axes(ax1)
    ax2.axhline(0, color=lpp.INK_MUTED, lw=0.8)
    ax2.set_ylabel("residual vs analytic  [%]")
    ax2.set_xlabel("x  [d$_e$]")
    ax2.set_title("The residual is scatter, not shape -- check that it stays centred on 0",
                  loc="left", fontweight="bold", fontsize=9.5)
    lpp.style_axes(ax2)
    lpp.stamp(fig, rows[0]["cfg"], rows[0]["sc"], extra=STUDY)
    fig.tight_layout()
    lpp.savefig(fig, "rays_per_cell", STUDY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
