#!/usr/bin/env python3
"""Three-panel kinetic-vs-hybrid comparison of n_e, T_e and P_abs at matched times.

    /opt/anaconda3/envs/physics/bin/python scripts/compare_deposition.py \
        runs/P4/P4_lez_kin_bg runs/P4/P4_lez_hyb_bg3

Writes ``media/<idA>_vs_<idB>/deposition_compare.png``.

**Source: the laser operator's own `laserdep_profile` dumps, not the field diagnostics.**
They carry `n_e`, `P_abs` and `theta_e` on ONE grid, written by the operator at the moment
it deposits -- so all three panels are the same quantity the physics used, at the same
instant, with no interpolation between diagnostics of different cadence. `theta_e` in
particular is *the temperature K was evaluated at*: a particle moment in the kinetic run and
the fluid field in the hybrid, which is exactly the comparison of interest.

The catch is cadence: these dumps are sparse (`profile_intervals`), so this is a small-multiples
figure rather than a movie. The two runs' dump STEPS differ because their `dt` differs; their
TIMES match, and the script asserts that rather than assuming it.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import numpy as np                          # noqa: E402

from laserprod import config as lpconfig    # noqa: E402
from laserprod import io as lpio            # noqa: E402
from laserprod import plotting as lpp       # noqa: E402


# The Manheimer steady state T_e,SS = 5.94 mu^(1/3) Z^(-1/3) lambda^(4/3) I^(2/3) is 823 eV
# for REAL aluminium. These runs use the paper's REDUCED mass ratio (m_Al/m_e = 2698 rather
# than 49542), and T_e,SS ~ mu^(1/3), so the value a WarpX leg should be judged against is
# 823 / 18.363^(1/3) = 312 eV. Annotating 823 eV on a reduced-mass run overstates the target
# by 2.6x -- which is how the hybrid's 423 eV was read as "0.5x of expectation" when it is
# 1.36x. See scripts/xcode_compare.py and RESULTS.md 2026-08-18.
TSS_REDUCED = 823.0 / 18.363 ** (1.0 / 3.0)      # 312 eV

def series(run_dir):
    cfg = lpconfig.load(run_dir)
    sc = lpconfig.derive(cfg)
    out = []
    for p in sorted(glob.glob(os.path.join(cfg["_run_dir"], "diags",
                                           "laserdep_profile_*.txt"))):
        with open(p) as fh:
            hdr = [next(fh) for _ in range(3)]
        t = float(hdr[1].split()[4])                 # "# step N time T dt_dep D"
        arr = np.loadtxt(p)
        nm = lpio.profile_column_names(p, arr.shape[1])
        out.append(dict(t=t,
                        z=arr[:, nm.index("z")] / sc.de_ref,
                        ne=arr[:, nm.index("n_e")] / sc.n_cr,
                        P=arr[:, nm.index("P_abs")],
                        Te=arr[:, nm.index("theta_e")] * 511e3))
    return lpconfig.run_id(cfg), sc, out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_a")
    ap.add_argument("run_b")
    ap.add_argument("--labels", nargs=2, default=None)
    ap.add_argument("--zmax", type=float, default=None, help="crop z axis [d_e]")
    args = ap.parse_args()

    import matplotlib.pyplot as plt

    ida, sca, A = series(args.run_a)
    idb, scb, B = series(args.run_b)
    la, lb = args.labels or (ida, idb)

    # Pair by TIME and refuse if they do not match: the runs have different dt, so equal
    # step numbers would be different instants and the figure would be a lie.
    pairs = []
    for a in A:
        j = int(np.argmin([abs(b["t"] - a["t"]) for b in B]))
        # Tolerance is 0.1% relative, not machine epsilon: the two runs deposit on
        # different sub-cadences (dt_dep differs with dt), so matched dumps sit up to one
        # deposition substep apart -- 7e-5 relative here. That is far below any physical
        # change and must not be mistaken for a mismatch; anything larger is a real one.
        dt_rel = abs(B[j]["t"] - a["t"]) / max(a["t"], B[j]["t"], 1e-30)
        if dt_rel < 1e-3:
            pairs.append((a, B[j]))
    if not pairs:
        raise SystemExit("no matched dump times between the two runs")
    print(f"  {len(pairs)} matched times: "
          + ", ".join(f"{a['t']*1e12:.2f} ps" for a, _ in pairs))

    n = len(pairs)
    fig, axes = plt.subplots(3, n, figsize=(4.2 * n, 9.0), sharex="col")
    axes = np.atleast_2d(axes)
    if n == 1:
        axes = axes.reshape(3, 1)

    for c, (a, b) in enumerate(pairs):
        zmax = args.zmax or max(a["z"].max(), b["z"].max())

        ax = axes[0, c]
        ax.semilogy(a["z"], np.maximum(a["ne"], 1e-8), color=lpp.C_TARGET, lw=1.7, label=la)
        ax.semilogy(b["z"], np.maximum(b["ne"], 1e-8), color=lpp.C_AMBIENT, lw=1.5,
                    ls="--", label=lb)
        ax.axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
        ax.text(0.01, 1.0, " n$_{cr}$", transform=ax.get_yaxis_transform(), va="bottom",
                fontsize=7, color=lpp.INK)
        ax.set_ylim(1e-5, 20)
        ax.set_title(f"t = {a['t']*1e12:.2f} ps", loc="left", fontweight="bold")
        if c == 0:
            ax.set_ylabel("n$_e$ / n$_{cr}$")
            ax.legend(fontsize=7.5, loc="upper right")

        ax = axes[1, c]
        ax.plot(a["z"], a["Te"], color=lpp.C_TARGET, lw=1.7)
        ax.plot(b["z"], b["Te"], color=lpp.C_AMBIENT, lw=1.5, ls="--")
        ax.axhline(TSS_REDUCED, color=lpp.C_LASER, ls="-.", lw=1.1)
        ax.text(0.01, TSS_REDUCED, f" T$_{{e,SS}}$ = {TSS_REDUCED:.0f} eV (reduced $m_i$)", transform=ax.get_yaxis_transform(),
                va="bottom", fontsize=7, color=lpp.C_LASER)
        if c == 0:
            ax.set_ylabel("T$_e$  [eV]   (the value K was evaluated at)")

        ax = axes[2, c]
        ax.semilogy(a["z"], np.maximum(a["P"], 1e12), color=lpp.C_TARGET, lw=1.7)
        ax.semilogy(b["z"], np.maximum(b["P"], 1e12), color=lpp.C_AMBIENT, lw=1.5, ls="--")
        # Mark where each run's critical surface is -- P_abs is exactly zero beyond it,
        # which is the whole point of the figure.
        for r, col in ((a, lpp.C_TARGET), (b, lpp.C_AMBIENT)):
            over = r["ne"] > 1.0
            if over.any():
                ax.axvline(r["z"][over].max(), color=col, ls=":", lw=1.2, alpha=0.8)
        if c == 0:
            ax.set_ylabel("P$_{abs}$  [W/m$^3$]\n(dotted: each run's n$_e$ = n$_{cr}$)")
        ax.set_xlabel("z  [d$_e$]")

        for r in range(3):
            axes[r, c].set_xlim(-50, zmax)
            axes[r, c].grid(alpha=0.15)

    fig.tight_layout()
    rid = f"{ida}_vs_{idb}"
    out = os.path.join(lpp.media_dir(run_id=rid), "deposition_compare.png")
    fig.savefig(out, dpi=140)
    print(f"  figure: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
