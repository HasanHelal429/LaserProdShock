#!/usr/bin/env python3
"""Does the finite-spot transverse leak scale with macroparticle noise?

`runs/P1/P1_vac_2d_spot` puts ~7 % of its absorbed power outside 2.5 beam waists by 2 ps, as
a broad flat pedestal (the wall columns sit BELOW their inward neighbours, so this is not the
pre-c817b63 index clamp). The transverse density ripple at its critical surface is 9.4 %,
which is the 36 ppc shot-noise floor -- and `n_ref = sqrt(1 - n_e/n_cr)` -> 0 there amplifies
any gradient by `1/n_ref`. This reduces the ppc pair to the one number that decides it.

    python studies/spot_leak_ppc/analyze.py
"""

from __future__ import annotations

import glob
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import io as lpio           # noqa: E402
from spot_report import SpotDump           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    rows = []
    for d in sorted(glob.glob(os.path.join(HERE, "scratch", "ppc_*")),
                    key=lambda p: int(os.path.basename(p).split("_")[1])):
        cfg = lpconfig.load(d)
        sc = lpconfig.derive(cfg)
        ppc = int(cfg["numerics"]["ppc"]["target"])
        w0 = float(cfg["laser"]["beam"]["waist_de"]) * sc.de_ref
        paths = lpio.profile_tables(cfg["_run_dir"])
        if not paths:
            print(f"  (skipping {os.path.basename(d)}: no profile dump)")
            continue
        last = SpotDump(paths[-1], sc, cfg)
        first = SpotDump(paths[0], sc, cfg)
        # transverse ripple at the critical surface, the quantity the mechanism turns on
        kc = int(np.abs(last.ne.mean(axis=0) / sc.n_cr - 1.0).argmin())
        nec = last.ne[:, kc]
        rows.append(dict(ppc=ppc, t=last.t, leak=last.leak_share(w0),
                         leak0=first.leak_share(w0), w=last.w_eff / w0,
                         ripple=float(nec.std() / nec.mean()),
                         floor=1.0 / math.sqrt(ppc), wall=last.wall_ratio(),
                         fax=last.f_axis(w0), fabs=last.total / lpio.incident_power(sc, cfg)))
    if not rows:
        print("no variants with output -- run studies/spot_leak_ppc/run_variants.sh first")
        return 1

    print("TRANSVERSE-LEAK ppc DISCRIMINATOR")
    hdr = (f"{'ppc':>5} {'t [ps]':>8} {'leak>2.5w0':>11} {'w_eff/w0':>9} "
           f"{'ripple@ncr':>11} {'1/sqrt(ppc)':>12} {'wall/in':>8} {'f_ax':>7} {'f_abs':>7}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['ppc']:5d} {r['t']*1e12:8.3f} {r['leak']:11.4f} {r['w']:9.3f} "
              f"{r['ripple']*100:10.2f}% {r['floor']*100:11.2f}% {r['wall']:8.2f} "
              f"{r['fax']:7.4f} {r['fabs']:7.4f}")

    if len(rows) >= 2:
        a, b = rows[0], rows[-1]
        f_ppc = b["ppc"] / a["ppc"]
        print(f"\n{a['ppc']} -> {b['ppc']} ppc  (x{f_ppc:g} particles, so the shot-noise "
              f"floor falls x{math.sqrt(f_ppc):.2f})")
        print(f"  measured ripple at n_cr   x{b['ripple']/a['ripple']:.2f}   "
              f"(noise-limited would be x{1/math.sqrt(f_ppc):.2f})")
        print(f"  leak share                x{b['leak']/a['leak']:.2f}")
        print(f"  absorption width w_eff/w0 {a['w']:.3f} -> {b['w']:.3f}")
        verdict = ("NOISE-DRIVEN: the leak falls with ppc, so it is a resolution artifact "
                   "and\n    a finite-spot coupling number needs a ppc budget, not a "
                   "physics caveat."
                   if b["leak"] < 0.7 * a["leak"] else
                   "NOT noise-limited: the leak survives x%g the particles, so it is "
                   "refraction\n    off a real transverse gradient and belongs in the "
                   "finite-spot error budget." % f_ppc)
        print(f"  VERDICT: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
