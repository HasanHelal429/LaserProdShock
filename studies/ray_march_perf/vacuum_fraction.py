#!/usr/bin/env python3
"""How much of the ray march is spent in vacuum? Measure it before implementing O2.

`TEST_PLAN.md` §7.5.2 proposes skipping the march from the injection face to the plasma
edge, and estimates the win on `P1_vac_2d` as "~9x" from its 89 %-vacuum geometry. That is a
geometric argument about the domain, not a measurement of the march -- and the two differ,
because a ray does not stop at the plasma edge: it keeps marching through the plasma, and it
is the ratio of the two path lengths that sets the speedup, per ray, per dump.

This measures it from the `n_e` in `laserdep_profile` dumps that already exist, so O2's
payoff is predicted before it is written -- and per run, since the answer depends entirely on
how much vacuum sits in front of the target.

    python studies/ray_march_perf/vacuum_fraction.py runs/P1/P1_vac_2d_spot [more runs...]

Reported per dump: the mean over columns of (vacuum path)/(total path), and the implied
speedup 1/(1 - f_vac) for the march alone. The `n_th` threshold is the same one O2 would
use; §7.5.2's error budget rests on `tau_skipped` at that threshold being negligible, and
that is checked here too rather than assumed.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))

import numpy as np                          # noqa: E402

from laserprod import config as lpconfig    # noqa: E402
from laserprod import io as lpio            # noqa: E402


def analyse(rd, n_th_frac, max_dumps):
    cfg = lpconfig.load(rd)
    sc = lpconfig.derive(cfg)
    rid = lpconfig.run_id(cfg)
    paths = lpio.profile_tables(cfg["_run_dir"])
    if not paths:
        print(f"{rid}: no profile dumps")
        return
    if len(paths) > max_dumps:
        keep = np.linspace(0, len(paths) - 1, max_dumps).round().astype(int)
        paths = [paths[i] for i in keep]

    dims = int(cfg["geometry"]["dims"])
    inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
    n_th = n_th_frac * sc.n_cr

    print(f"\n{rid}  ({dims}D, inject {'hi' if inject_hi else 'lo'}, "
          f"n_th = {n_th_frac:g} n_cr = {n_th:.3e} m^-3)")
    hdr = (f"  {'t [ps]':>7} {'f_vac':>7} {'speedup':>8} {'L_vac':>9} {'L_tot':>9} "
           f"{'I(ne/ncr)2dz':>13}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for p in paths:
        a = np.loadtxt(p)
        # Resolve columns BY NAME. lpio.PROFILE_TAIL is ["n_e", "H", "P_abs", "theta_e",
        # "A"] -- DENSITY FIRST -- so in 2D n_e is column 2 and P_abs is column 4. A
        # hardcoded offset here read P_abs as n_e in the first draft of this script.
        ncoord = max(a.shape[1] - len(lpio.PROFILE_TAIL), 0)
        names = {1: ["z"], 2: ["x", "z"], 3: ["x", "y", "z"]}[ncoord]
        cols = names + lpio.PROFILE_TAIL[:a.shape[1] - ncoord]
        z = a[:, cols.index("z")]
        ne = a[:, cols.index("n_e")]
        zs = np.unique(z)
        dz = float(zs[1] - zs[0])
        # per-column axial profile of n_e
        if dims == 1:
            colprofiles = [ne[np.argsort(z)]]
        else:
            x = a[:, cols.index("x")]
            xs = np.unique(x)
            colprofiles = []
            for xv in xs:
                m = x == xv
                zz, nn = z[m], ne[m]
                colprofiles.append(nn[np.argsort(zz)])
        f_vac, tsk = [], []
        for nn in colprofiles:
            seq = nn[::-1] if inject_hi else nn
            hit = np.nonzero(seq >= n_th)[0]
            # A ray that never meets the threshold traverses only vacuum; count the full
            # path so the mean is not silently biased by dropping those columns.
            n_vac = int(hit[0]) if hit.size else len(seq)
            f_vac.append(n_vac / len(seq))
            # Optical depth DISCARDED by the skip: integral of (n_e/n_cr)^2 dz over the
            # skipped stretch. K ~ n_e^2 / n_ref, and n_ref -> 1 in vacuum, so this is the
            # shape of what O2 throws away (bar the constant IB coefficient) and is
            # dominated by the last cell before the plasma edge.
            tsk.append(float(((seq[:n_vac] / sc.n_cr) ** 2).sum()) * dz)
        fv = float(np.mean(f_vac))
        Ltot = len(colprofiles[0]) * dz
        print(f"  {lpio_time(p)*1e12:7.3f} {fv:7.4f} {1/(1-fv) if fv < 1 else float('inf'):8.2f} "
              f"{fv*Ltot*1e6:8.1f}u {Ltot*1e6:8.1f}u {np.mean(tsk):13.2e}")


def lpio_time(path):
    with open(path) as fh:
        for line in fh:
            if line.startswith("#") and " time " in line:
                return float(line.split(" time ")[1].split()[0])
            if not line.startswith("#"):
                break
    return float("nan")


def sweep(rd, max_dumps, thresholds):
    """f_vac and the DISCARDED optical depth against n_th, for the last dump of a run.

    O2 has one free parameter and two competing pressures: a higher `n_th` skips more path
    (more speedup) but discards more absorption (more error). Both are measurable from a dump
    that already exists, so the threshold can be chosen rather than guessed.

    tau_discarded = (A / n_cr) * integral n_e^2 dz  over the skipped stretch, with n_ref -> 1
    in the tenuous region. `A` is carried in the dump, so this is the real optical depth and
    not a proxy.
    """
    cfg = lpconfig.load(rd)
    sc = lpconfig.derive(cfg)
    rid = lpconfig.run_id(cfg)
    paths = lpio.profile_tables(cfg["_run_dir"])
    if not paths:
        return
    inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
    a = np.loadtxt(paths[-1])
    ncoord = max(a.shape[1] - len(lpio.PROFILE_TAIL), 0)
    names = {1: ["z"], 2: ["x", "z"], 3: ["x", "y", "z"]}[ncoord]
    cols = names + lpio.PROFILE_TAIL[:a.shape[1] - ncoord]
    z, ne = a[:, cols.index("z")], a[:, cols.index("n_e")]
    A = float(np.median(a[:, cols.index("A")])) if "A" in cols else float("nan")
    zs = np.unique(z)
    dz = float(zs[1] - zs[0])
    if ncoord == 1:
        profs = [ne[np.argsort(z)]]
    else:
        x = a[:, cols.index("x")]
        profs = []
        for xv in np.unique(x):
            m = x == xv
            profs.append(ne[m][np.argsort(z[m])])

    t = lpio_time(paths[-1])
    print(f"\n{rid}: choosing O2's threshold, at the LAST dump (t = {t*1e12:.3f} ps), "
          f"A = {A:.3e} m^2")
    hdr = f"  {'n_th [n_cr]':>12} {'f_vac':>7} {'speedup':>8} {'tau_discarded':>14}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for frac in thresholds:
        n_th = frac * sc.n_cr
        fv, tau = [], []
        for nn in profs:
            seq = nn[::-1] if inject_hi else nn
            hit = np.nonzero(seq >= n_th)[0]
            n_vac = int(hit[0]) if hit.size else len(seq)
            fv.append(n_vac / len(seq))
            tau.append((A / sc.n_cr) * float((seq[:n_vac] ** 2).sum()) * dz)
        f = float(np.mean(fv))
        print(f"  {frac:12.1e} {f:7.4f} {1/(1-f) if f < 1 else float('inf'):8.2f} "
              f"{np.mean(tau):14.3e}")
    print("  (tau_discarded must sit far below the 10.4 % 1-sigma seed spread on f_abs; "
          "TEST_PLAN 7.5.2)")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--n-th", type=float, default=1e-4,
                    help="vacuum threshold in units of n_cr (default 1e-4, as §7.5.2)")
    ap.add_argument("--max-dumps", type=int, default=5)
    ap.add_argument("--sweep", action="store_true",
                    help="also sweep n_th on the last dump, to CHOOSE O2's threshold")
    args = ap.parse_args()
    print("VACUUM FRACTION OF THE RAY PATH -- O2's payoff, measured per run")
    print("  f_vac   = mean over columns of (cells before n_e >= n_th) / (cells on the axis)")
    print("  speedup = 1/(1-f_vac), the march-only factor if the vacuum stretch costs nothing")
    print("  I(ne/ncr)2dz = SHAPE of the discarded optical depth [m]: integral of "
          "(n_e/n_cr)^2 dz over the")
    print("                 skipped stretch. NOT tau -- multiply by the IB coefficient A "
          "(n_ref -> 1 in vacuum).")
    for rd in args.runs:
        try:
            analyse(rd, args.n_th, args.max_dumps)
        except Exception as exc:
            print(f"\n{rd}: {type(exc).__name__}: {exc}")
    if args.sweep:
        grid = [1e-4, 1e-3, 1e-2, 3e-2, 1e-1, 3e-1]
        for rd in args.runs:
            try:
                sweep(rd, args.max_dumps, grid)
            except Exception as exc:
                print(f"\n{rd} sweep: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
