#!/usr/bin/env python3
"""Read a convergence ladder as a SET, which is the only way it can be read.

    python scripts/ladder_report.py runs/P5/P5_raycfl_050 runs/P5/P5_raycfl_025 ...
    python scripts/ladder_report.py --glob 'runs/P5/P5_ramp_*' --var ray_cfl
    python scripts/ladder_report.py --glob 'runs/P5/P5_dz_*' --var dz --off runs/P5/P5_raycfl_off

A single rung says nothing: convergence for turning-point problems is documented
non-monotonic, so a narrow step between two rungs is not evidence of an asymptote --
that mistake was made and retracted on 2026-08-30, when +1.18% between ray_cfl 0.10
and 0.05 was read as near-convergence and the next rung moved +2.04%.

Four things this prints that a per-run tool cannot:

1. E_abs across the ladder with the step-to-step change, and a verdict that keys on
   whether the INCREMENT is shrinking rather than on any single value.
2. The critical-layer resolution: L_n at the crossing in CELLS. This is the quantity
   that decides whether a ladder can converge at all -- the operator interpolates
   density multilinearly, which is exact for a linear ramp (upstream ACCURACY.md
   says so) and invents a straight line when the layer is sub-grid.
3. Where the rungs disagree, per cell. A divergence localised at the turning point
   is a different defect from one localised at the domain edge (upstream Finding 1).
4. Energy closure against a MATCHED laser-off control, if one is given. Grid heating
   accumulates with step count, so a control at a different duration cannot be
   rescaled onto the ladder.
"""

from __future__ import annotations

import argparse
import glob as globmod
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import io as lpio           # noqa: E402
from laserprod import plotting as lpp     # noqa: E402

RUNS = os.path.join(lpp.ROOT, "runs", "P5")

# Run-to-run 1 sigma on E_abs, in %. MEASURED 2026-09-04 from four repeats of ONE identical
# configuration (same deck, same binary, same seed, ray_cfl = 0.025): mean 103451, sd 1361.
# The earlier 0.80 % came from a SINGLE seed pair, which estimates a difference rather than
# a spread and happened to land low; it is retracted. WarpX on GPU is not reproducible at
# fixed seed (ablastr/math/RandomSeed.H), so this is irreducible at this duration -- the
# only ways to shrink it are repeats or a longer run.
FLOOR = 1.32


def _ladder_value(cfg, var):
    if var == "ray_cfl":
        return float(cfg["laser"]["ray_cfl"])
    if var == "dz":
        return float(cfg["geometry"]["dz_over_de"])
    raise SystemExit(f"unknown --var {var!r} (use ray_cfl or dz)")


def _profiles(run_dir):
    fs = sorted(globmod.glob(os.path.join(run_dir, "diags", "laserdep_profile_*.txt")))
    return {os.path.basename(f).split("_")[-1].split(".")[0]: f for f in fs}


def _e_abs(run_dir, cfg, sc):
    """Total coupled energy from the operator's own tracer, immune to grid heating."""
    hist = lpio.laserdep_history(run_dir)
    if hist is None or len(hist) == 0:
        return None
    return float(hist.Eabs_final)


def crossing_resolution(run_dir, n_cr, dz):
    """L_n = |1/(dr/dz)| at r = 1, in metres and in cells, from the last profile dump.

    The layer the operator must integrate is where 1-r is small; its thickness is
    eps*L_n. If that is under a cell the grid cannot represent it and no arc-length
    refinement can recover it.
    """
    ps = _profiles(run_dir)
    if not ps:
        return None
    a = np.loadtxt(ps[sorted(ps)[len(ps) // 2]])
    z, ne = a[:, 0], a[:, 1]
    r = ne / n_cr
    # THE crossing is where the profile goes overdense -> underdense on the laser side,
    # not simply the first cell under critical: a domain whose low-z end is vacuum has
    # r < 1 at index 0, which is not a turning point at all. (That edge case silently
    # returned "no crossing" for the analytic-ramp ladder until 2026-08-31.)
    cross = np.nonzero((r[:-1] >= 1.0) & (r[1:] < 1.0))[0]
    if cross.size == 0:
        return None
    i = int(cross[-1]) + 1
    if i < 1 or i >= len(r) - 1:
        return None
    drdz = (r[i + 1] - r[i - 1]) / (z[i + 1] - z[i - 1])
    if drdz == 0:
        return None
    Ln = abs(1.0 / drdz)
    return {"L_n_m": Ln, "L_n_cells": Ln / dz, "cell": int(i),
            "r_at_cell": float(r[i]), "r_prev": float(r[i - 1]),
            "n_in_band": int(((r > 0.99) & (r < 1.01)).sum())}


def localise(run_a, run_b, n_cr, step=None):
    """Which cells carry the difference between two rungs, at a common dump."""
    pa, pb = _profiles(run_a), _profiles(run_b)
    common = sorted(set(pa) & set(pb))
    if not common:
        return None
    k = step if step in pa and step in pb else common[len(common) // 2]
    A, B = np.loadtxt(pa[k]), np.loadtxt(pb[k])
    # Compare in PHYSICAL z, never by cell index: a dz ladder's rungs have different cell
    # counts, so index i is a different location in each and an index-wise difference is
    # meaningless (it reported vacuum cells as top contributors until 2026-08-31).
    # P_abs is a density [W/m^3]; resample the other rung onto this one's centres.
    z, ne = A[:, 0], A[:, 1]
    dz = z[1] - z[0]
    Pb = np.interp(z, B[:, 0], B[:, 3]) if len(B) != len(A) else B[:, 3]
    d = (Pb - A[:, 3]) * dz
    tot = d.sum()
    order = np.argsort(-np.abs(d))
    top = [{"cell": int(i), "z": float(z[i]), "r": float(ne[i] / n_cr),
            "dE": float(d[i]), "frac": float(abs(d[i]) / abs(tot)) if tot else float("nan")}
           for i in order[:5]]
    # When the rungs agree, |total| collapses toward zero while individual cells still
    # carry PIC-noise-sized differences that CANCEL. Fractions of |total| are then
    # meaningless (they read in the thousands of percent), so flag that case rather than
    # printing nonsense: it is the signature of convergence, not of a divergence.
    peak = float(np.abs(d).max()) if len(d) else 0.0
    return {"step": k, "total": float(tot), "top": top, "peak_abs": peak,
            "cancels": bool(peak > 0 and abs(tot) < 0.1 * peak),
            "edge_lo": float(d[:5].sum()), "edge_hi": float(d[-5:].sum())}


def closure(run_dir, e_abs, off_dKE=None):
    """(dKE + dE_field)/E_abs, and the same after subtracting a matched control."""
    try:
        d = os.path.join(run_dir, "diags", "reducedfiles")
        ep = np.loadtxt(os.path.join(d, "EP.txt"), skiprows=1)
        fe = np.loadtxt(os.path.join(d, "FE.txt"), skiprows=1)
        pn = np.loadtxt(os.path.join(d, "PN.txt"), skiprows=1)
    except OSError:
        return None
    dKE = ep[-1, 2:].sum() - ep[0, 2:].sum()
    dEf = fe[-1, 2:].sum() - fe[0, 2:].sum()
    n0, n1 = pn[0, 2:].sum(), pn[-1, 2:].sum()
    out = {"dKE": float(dKE), "dEf": float(dEf),
           "loss_pct": float(100 * (n0 - n1) / n0) if n0 else float("nan"),
           "ratio": float((dKE + dEf) / e_abs) if e_abs else float("nan")}
    if off_dKE is not None:
        out["dKE_laser"] = float(dKE - off_dKE)
        out["ratio_corr"] = float((dKE - off_dKE + dEf) / e_abs) if e_abs else float("nan")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="*")
    ap.add_argument("--glob", help="shell glob for the rungs, e.g. 'runs/P5/P5_ramp_*'")
    ap.add_argument("--var", default="ray_cfl", choices=("ray_cfl", "dz"),
                    help="the ladder variable (default ray_cfl)")
    ap.add_argument("--off", help="matched laser-off control, for the energy closure")
    ap.add_argument("--tol", type=float, default=1.0,
                    help="acceptance band on the last increment, %% (default 1)")
    ap.add_argument("--floor", type=float, default=FLOOR,
                    help=f"run-to-run 1 sigma on E_abs in %% (default {FLOOR}, measured)")
    args = ap.parse_args()

    dirs = list(args.run_dirs)
    if args.glob:
        dirs += [d for d in sorted(globmod.glob(args.glob)) if os.path.isfile(
            os.path.join(d, "config.yaml"))]
    if args.off and args.off in dirs:
        dirs.remove(args.off)
    if not dirs:
        raise SystemExit("no rungs given (positional dirs or --glob)")

    rows = []
    for d in dirs:
        cfg = lpconfig.load(d)
        sc = lpconfig.derive(cfg)
        e = _e_abs(d, cfg, sc)
        if e is None:
            print(f"  (skipping {os.path.basename(d)}: no LASERDEP history yet)")
            continue
        rows.append({"dir": d, "id": os.path.basename(d),
                     "x": _ladder_value(cfg, args.var), "E": e,
                     "n_cr": float(sc.n_cr), "dz": float(sc.dz)})
    if not rows:
        raise SystemExit("no rung has finished yet")
    rows.sort(key=lambda r: -r["x"])          # coarse -> fine

    off_dKE = None
    if args.off:
        c = closure(args.off, 1.0)
        if c:
            off_dKE = c["dKE"]

    print(f"\nLADDER — variable: {args.var}, {len(rows)} rungs, coarse to fine\n")
    print(f"  (run-to-run 1 sigma on E_abs: {args.floor:.2f} %)")
    print(f"  {'rung':<16} {args.var:>8} {'E_abs':>12} {'d vs coarser':>16} "
          f"{'(dKE+dEf)/E':>12} {'loss%':>7}")
    prev = None
    incs = []
    for r in rows:
        dstr = ""
        if prev is not None:
            inc = (r["E"] - prev) / prev * 100.0
            incs.append(inc)
            # Always in units of the measured spread: an increment smaller than the
            # run-to-run sigma is not a measurement, and printing it bare invites exactly
            # the reading that had to be retracted on 2026-09-04.
            dstr = f"{inc:+.2f} % ({abs(inc)/args.floor:.1f}s)"
        cl = closure(r["dir"], r["E"], off_dKE)
        cstr = f"{cl['ratio']:.3f}" if cl else "-"
        if cl and off_dKE is not None:
            cstr = f"{cl['ratio']:.3f}/{cl['ratio_corr']:.3f}"
        lstr = f"{cl['loss_pct']:.2f}" if cl else "-"
        print(f"  {r['id']:<16} {r['x']:>8g} {r['E']:>12.4e} {dstr:>16} {cstr:>12} {lstr:>7}")
        prev = r["E"]

    if len(rows) >= 2:
        span = (rows[-1]["E"] - rows[0]["E"]) / rows[0]["E"] * 100.0
        print(f"\n  total change coarsest -> finest: {span:+.1f} %")
    if len(incs) >= 2:
        last, prev_inc = abs(incs[-1]), abs(incs[-2])
        print(f"  last increment {incs[-1]:+.2f} % (previous {incs[-2]:+.2f} %)")
        if last < args.floor:
            print(f"  VERDICT: UNDECIDABLE -- the last increment is {last/args.floor:.1f} "
                  f"sigma of the {args.floor:.2f} % run-to-run spread. It is not a "
                  f"measurement.\n           Repeat each rung ~5x, or run longer.")
        elif last > args.tol and last >= prev_inc:
            print(f"  VERDICT: NOT CONVERGED — the increment is not shrinking. A narrow "
                  f"step here would be a coincidence of a non-monotonic sequence, not an "
                  f"asymptote.")
        elif last > args.tol:
            print(f"  VERDICT: NOT CONVERGED — last step {last:.2f} % exceeds the "
                  f"{args.tol:g} % band, though it is shrinking. Add a finer rung.")
        else:
            print(f"  VERDICT: converged to within {args.tol:g} % at "
                  f"{args.var} = {rows[-1]['x']:g}.")

    r0 = rows[0]
    res = crossing_resolution(r0["dir"], r0["n_cr"], r0["dz"])
    if res:
        print(f"\n  CRITICAL-LAYER RESOLUTION (at {r0['id']}, dz = {r0['dz']:.4e} m)")
        print(f"    L_n at the crossing = {res['L_n_m']:.3e} m = {res['L_n_cells']:.1f} cells")
        for eps in (1e-1, 1e-2):
            print(f"      layer 1-r < {eps:<5g}: {eps*res['L_n_cells']:8.3f} cells")
        print(f"    cells with 0.99 < r < 1.01: {res['n_in_band']}")
        if res["n_in_band"] == 0:
            print("    ^ the singular layer is SUB-GRID: the operator is integrating a "
                  "straight line\n      between two cells straddling critical, so refining "
                  "the march cannot converge.")

    if len(rows) >= 2:
        loc = localise(rows[0]["dir"], rows[-1]["dir"], rows[0]["n_cr"])
        if loc:
            print(f"\n  WHERE THEY DISAGREE (dump {loc['step']}, finest minus coarsest)")
            print(f"    total {loc['total']:+.4e};  domain edges: "
                  f"lo {loc['edge_lo']:+.2e}, hi {loc['edge_hi']:+.2e}")
            if loc["cancels"]:
                print(f"    NOTE |total| is under 10% of the largest single-cell difference "
                      f"({loc['peak_abs']:.2e}):\n         the per-cell differences CANCEL. "
                      f"That is local PIC-noise redistribution with\n         no net effect "
                      f"-- i.e. the rungs agree. The percentages below are not meaningful.")
            for t in loc["top"]:
                print(f"      cell {t['cell']:6d}  r = {t['r']:7.3f}  "
                      f"dE = {t['dE']:+.4e}  ({100*t['frac']:5.1f} % of |total|)")
            print("    A divergence at the turning point (r ~ 1) is the sub-grid layer;\n"
                  "    one at the domain edge is upstream Finding 1 instead.")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
