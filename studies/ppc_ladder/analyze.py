#!/usr/bin/env python3
"""Does the outward T_e rise survive more particles?

    /opt/anaconda3/envs/physics/bin/python studies/ppc_ladder/analyze.py

THE ONE NUMBER. FLASH's plume is an isothermal plateau; WarpX's T_e rises outward. If that
rise is a sampling artifact it must weaken as ppc goes up. The metric is deliberately blunt
and density-weighted, so it cannot be moved by a few featherweight particles in the far
wing:

    RISE = <T_e> over the OUTER half of the underdense band (by log-density)
         / <T_e> over the INNER half

    FLASH (isothermal plateau)  -> RISE ~ 1
    a hot tail                  -> RISE > 1
    noise                       -> RISE falls toward 1 as ppc rises

Reported beside it: the density-weighted plume T_e, and the count of macroparticles in the
outer half, which is what any noise claim actually rests on.

The ladder rungs also differ from `P4_lez_kin` in `density_min_frac` (1e-6 against 1e-4),
so `P4_lez_kin` is included as the four-decade reference: rung 500 against it isolates the
dynamic range, and the rungs against each other isolate ppc.
"""
from __future__ import annotations
import argparse, glob, os, sys, warnings
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))
import numpy as np
import xcode_compare as X

BAND = (1e-2, 1.0)
TAUS = (6.7, 13.5, 20.3, 27.0)
TAU_TOL = 0.08     # fractional; a dump further than this from the request is DROPPED

# xcode_compare.pick() returns the NEAREST dump unconditionally, so on a run that is still
# going it happily answers a tau = 27 request with a tau = 6 dump and the label lies. The
# first version of this script did exactly that: a 20%-complete rung reported IDENTICAL
# numbers at tau 13.5, 20.3 and 27.0, which is one dump wearing three labels. Drop, never
# relabel.


def rise(zeta, ne, Te):
    """(RISE, plume <T_e>, n points outer) over the underdense band, split by log-density."""
    ne = np.asarray(ne, float); Te = np.asarray(Te, float); z = np.asarray(zeta, float)
    m = np.isfinite(ne) & np.isfinite(Te) & (ne >= BAND[0]) & (ne <= BAND[1]) & (Te > 0)
    if m.sum() < 8:
        return None
    z, ne, Te = z[m], ne[m], Te[m]
    # split by POSITION within the band, outer = larger zeta
    cut = np.median(z)
    inner, outer = z <= cut, z > cut
    if inner.sum() < 3 or outer.sum() < 3:
        return None
    wi, wo = ne[inner], ne[outer]
    Ti = np.average(Te[inner], weights=wi)
    To = np.average(Te[outer], weights=wo)
    Tall = np.average(Te, weights=ne)
    return To / Ti, Tall, int(outer.sum())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--leg", action="append", metavar="LABEL=PATH",
                    help="extra leg to include; repeatable")
    ap.add_argument("--no-scratch", action="store_true",
                    help="skip the ladder rungs under scratch/")
    a = ap.parse_args()
    print(__doc__)
    legs = [("P4_lez_kin (4 dec, Gauss)", os.path.join(HERE, "..", "..", "runs", "P4", "P4_lez_kin"))]
    if not a.no_scratch:
        for d in sorted(glob.glob(os.path.join(HERE, "scratch", "L_ppc*"))):
            legs.append((os.path.basename(d) + " (6 dec, Gauss)", d))
    for spec in (a.leg or []):
        lab, path = spec.split("=", 1)
        legs.append((lab, path))

    F = X.flash_series(X.FLASH_DIR, "lez1d")
    print(f"  {'leg':<28} {'tau':>6} {'RISE':>7} {'<T_e> eV':>10} {"bins out":>9}")
    print("  " + "-" * 64)
    for tau in TAUS:
        f = X.pick(F, tau)
        r = rise(f["zeta"], f["ne"], f["Te"])
        if r:
            print(f"  {'FLASH':<28} {tau:6.1f} {r[0]:7.3f} {r[1]:10.1f} {r[2]:9d}")
    print()
    sc = X.warpx_scales(2698.0)
    for lab, path in legs:
        if not glob.glob(os.path.join(path, "diags", "diag1*")):
            print(f"  {lab:<28} (no diags yet)"); continue
        S = X.warpx_particles(path, X.SP_KIN, sc=sc)
        for tau in TAUS:
            s = X.pick(S, tau)
            if s is None or s.get("Te") is None:
                continue
            if abs(s["tau"] - tau) > TAU_TOL * tau:
                continue        # this rung has not reached that time yet
            r = rise(s["zeta"], s["ne"], s["Te"])
            if r:
                print(f"  {lab:<28} {tau:6.1f} {r[0]:7.3f} {r[1]:10.1f} {r[2]:9d}")
        print()
    print("  RISE ~ 1 is FLASH's isothermal plateau. Falling toward 1 with ppc => noise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
