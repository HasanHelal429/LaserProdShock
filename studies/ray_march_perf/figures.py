#!/usr/bin/env python3
"""O2's payoff, measured rather than assumed: how much of the ray march is vacuum?

`TEST_PLAN.md` §7.5.2 estimated the vacuum skip as "~9x on P1_vac_2d" from that run's
89 %-vacuum *geometry*. This plots what the density in the dumps actually says, and the answer
is different in kind: the vacuum stretch is **consumed during the run** by the fast-electron
halo, which travels at `v_th,e` ~ 43 `d_e`/ps -- ten times `c_s` -- so O2's benefit decays from
the geometric estimate toward nothing.

  (a) `f_vac(t)` for each run, against the halo model `(L_vac(0) - v_th,e t)/L_tot`
  (b) the threshold trade-off: march speedup against the optical depth O2 discards, so `n_th`
      can be CHOSEN

    python studies/ray_march_perf/figures.py runs/P1/P1_vac_1d_thick runs/P1/P1_vac_2d ...
"""

from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import io as lpio           # noqa: E402
from laserprod import plotting as lpp      # noqa: E402
from laserprod.units import ME             # noqa: E402

STUDY = "ray_march_perf"
EV = 1.602176634e-19
NOISE = 0.104          # the 10.4 % 1-sigma seed spread on f_abs(0): the error O2 must sit under


def profiles(rd):
    """Per-column axial n_e profiles for every dump, plus geometry."""
    cfg = lpconfig.load(rd)
    sc = lpconfig.derive(cfg)
    out = []
    for p in lpio.profile_tables(cfg["_run_dir"]):
        a = np.loadtxt(p)
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
            profs = [ne[x == xv][np.argsort(z[x == xv])] for xv in np.unique(x)]
        t = float("nan")
        with open(p) as fh:
            for line in fh:
                if line.startswith("#") and " time " in line:
                    t = float(line.split(" time ")[1].split()[0]); break
                if not line.startswith("#"):
                    break
        out.append(dict(t=t, profs=profs, dz=dz, A=A))
    return cfg, sc, lpconfig.run_id(cfg), out


def f_vac_of(dump, n_th, inject_hi):
    fv, tau = [], []
    for nn in dump["profs"]:
        seq = nn[::-1] if inject_hi else nn
        hit = np.nonzero(seq >= n_th)[0]
        n_vac = int(hit[0]) if hit.size else len(seq)
        fv.append(n_vac / len(seq))
        tau.append(float((seq[:n_vac] ** 2).sum()) * dump["dz"])
    return float(np.mean(fv)), float(np.mean(tau))


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--n-th", type=float, default=1e-4)
    args = ap.parse_args()
    import matplotlib.pyplot as plt

    data = []
    for rd in args.runs:
        try:
            data.append(profiles(rd))
        except Exception as exc:
            print(f"  (skipping {rd}: {type(exc).__name__}: {exc})")
    if not data:
        return 1

    palette = [lpp.C_TARGET, lpp.C_LASER, lpp.C_AMBIENT, lpp.C_FOURTH]
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.6, 4.5))

    for (cfg, sc, rid, dumps), c in zip(data, palette):
        inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
        n_th = args.n_th * sc.n_cr
        t = np.array([d["t"] for d in dumps]) * 1e12
        fv = np.array([f_vac_of(d, n_th, inject_hi)[0] for d in dumps])
        axA.plot(t, fv, "o-", color=c, lw=1.7, ms=4.5, label=rid)
        # the halo model, anchored on this run's own t=0 vacuum fraction
        Ltot = len(dumps[0]["profs"][0]) * dumps[0]["dz"]
        Lvac0 = fv[0] * Ltot
        Te = 300.0 * EV                      # the measured coronal T_e at these times
        vth = math.sqrt(Te / ME)
        tt = np.linspace(0, max(t.max(), 1e-3), 100)
        # Anchored on each run's OWN t = 0 vacuum fraction. It tracks P1_vac_2d closely and
        # over-predicts the spot's decay: the front of the 1e-4 n_cr contour is a rarefaction
        # with a velocity spectrum, not a free-streaming step at exactly v_th,e. Treat the
        # line as the mechanism and the timescale, not a fit. (The obvious alternative
        # explanation for the spot -- that only the ILLUMINATED columns get a hot halo -- was
        # tested and FALSIFIED: dark columns retain 1.01x the vacuum of lit ones, because the
        # halo crosses the 160 d_e transverse box in ~4 ps and fills it.)
        axA.plot(tt, np.maximum(Lvac0 - vth * tt * 1e-12, 0) / Ltot, ls="--",
                 color=c, lw=1.2, alpha=0.75)
    axA.plot([], [], ls="--", color=lpp.INK, lw=1.2,
             label=r"$(L_{vac}(0)-v_{th,e}t)/L_{tot}$,  $v_{th,e}$ at 300 eV")
    axA.set_xlabel("t [ps]")
    axA.set_ylabel(r"$f_{vac}$ = vacuum fraction of the ray path")
    axA.set_ylim(0, None)
    axA.set_title("(a) O2's headroom is consumed during the run at $v_{th,e}$,\n"
                  r"$\approx10\,c_s$ -- the dashed model is a MECHANISM, not a fit",
                  fontsize=9.5)
    axA.legend(fontsize=7.4, frameon=False)
    lpp.style_axes(axA)

    grid = np.array([1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1, 3e-1])
    for (cfg, sc, rid, dumps), c in zip(data, palette):
        inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
        d = dumps[-1]
        sp, td = [], []
        for frac in grid:
            f, tau = f_vac_of(d, frac * sc.n_cr, inject_hi)
            sp.append(1 / (1 - f) if f < 1 else np.inf)
            td.append(d["A"] / sc.n_cr * tau)
        axB.plot(td, sp, "o-", color=c, lw=1.7, ms=4.5,
                 label=f"{rid}  (t = {d['t']*1e12:.1f} ps)")
        for frac, x, y in zip(grid, td, sp):
            if frac in (1e-4, 3e-2, 3e-1):
                axB.annotate(f"{frac:g}", (x, y), textcoords="offset points",
                             xytext=(4, -9), fontsize=6.8, color=c)
    axB.axvline(NOISE, color=lpp.INK, ls="-.", lw=1.2)
    axB.text(NOISE * 0.8, axB.get_ylim()[0], r" 10.4 % seed noise on $f_{abs}$ ",
             rotation=90, fontsize=7.2, color=lpp.INK, va="bottom", ha="right")
    axB.set_xscale("log")
    axB.set_xlabel(r"optical depth DISCARDED by the skip,  $\tau_{\rm skipped}$")
    axB.set_ylabel("march speedup  $1/(1-f_{vac})$")
    axB.set_title(r"(b) choosing $n_{th}$: labels are $n_{th}/n_{cr}$;"
                  "\nthe knee sits near $3\\times10^{-2}$", fontsize=9.5)
    axB.legend(fontsize=7.4, frameon=False, loc="upper left")
    lpp.style_axes(axB)

    lpp.stamp(fig, data[0][0], data[0][1], extra=f"{STUDY}: O2 vacuum-skip payoff, measured")
    fig.tight_layout()
    lpp.savefig(fig, "o2_vacuum_fraction", STUDY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
