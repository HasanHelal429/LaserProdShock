#!/usr/bin/env python3
"""Lezhnin 2025 Fig. 2 -- the INITIAL CONDITIONS of FLASH and PIC, overplotted.

    /opt/anaconda3/envs/physics/bin/python scripts/fig2_ic.py
    ... scripts/fig2_ic.py --leg "flashic=runs/P4/P4_lez_kin_flashic" --xlim -5 40
    ... scripts/fig2_ic.py --normalise peak --out fig2_ic_peak.png

WHAT THE PAPER'S FIG. 2 IS, AND WHY IT IS THE RIGHT PLACE TO START. The paper initialises
its PIC run from the FLASH t = 0.1 ns snapshot and shows four panels -- (a) electron
density, (b) electron temperature, (c) flow speed, (d) LASER POWER ABSORPTION -- with
FLASH and PSC overplotted. It names exactly two acceptable differences:

    (I)  the capped maximum density,  n_max,PIC << n_max,FLASH  (computational)
    (II) the density FLOOR,  n_cr/N_ppc ~ 1e-5 n_cr >> n_floor,FLASH

and then claims "identical laser power absorption profiles" in (d).

**Panel (d) is the paper's own acceptance test for an initial condition.** The corona is
not required to match FLASH pointwise -- it is required to absorb the laser the same way.
That makes this figure the direct answer to "is the corona just a smoothing device, or is
it changing the physics?": if ICs that differ in corona shape give the same P_abs(z), the
corona is bookkeeping; if they do not, it is load-bearing and no amount of late-time
comparison is meaningful until it converges.

WHAT WE ALREADY KNOW IT WILL SHOW, so the figure can be read critically rather than
credulously (RESULTS.md 2026-08-18): a Gaussian corona of scale 27 d_e put the critical
surface at 40.6 d_e where FLASH has it at 2.31 -- a factor 18 -- and absorbed 7.3x too
strongly. So the corona is NOT bookkeeping. This figure quantifies that on the paper's own
axes.

UNITS. Each code on its OWN d_i0 (TEST_PLAN 12.2). FLASH's `depo` is a specific deposition
rate [erg/g/s], so P_abs = depo * dens * 0.1 -> W/m^3; the PIC P_abs comes from the step-0
`laserdep_profile` dump, which CLAUDE.md singles out as the one absorption diagnostic with
no shot-noise floor.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                    # noqa: E402
import xcode_compare as X                             # noqa: E402
from laserprod import plotting as lpp                 # noqa: E402

C_FLASH = "#1f4e9c"
PALETTE = ("#c7522a", "#7a3fa0", "#2a8a5f", "#b8860b")


def pic_deposition(run_dir, sc, step=0):
    """(zeta, n_e/n_cr, P_abs [W/m^3], theta_e) from a laserdep_profile dump."""
    hits = sorted(glob.glob(os.path.join(run_dir, "diags",
                                         f"laserdep_profile_{step:06d}.txt")))
    if not hits:
        return None
    d = np.loadtxt(hits[0])
    if d.ndim != 2 or d.shape[1] < 5:
        return None
    z, ne, _H, P, th = d[:, 0], d[:, 1], d[:, 2], d[:, 3], d[:, 4]
    return dict(zeta=z / sc["di0"], ne=ne / X.N_CR, P=P,
                Te=th * X.ME * X.C ** 2 / X.QE)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--leg", action="append", metavar="LABEL=PATH",
                    help="PIC leg to overplot; repeatable")
    ap.add_argument("--flash-tau", type=float, default=2.696,
                    help="FLASH time to draw, in tau. 2.696 = 0.1 ns, the handoff")
    ap.add_argument("--xlim", type=float, nargs=2, default=(-8.0, 45.0))
    ap.add_argument("--nelim", type=float, nargs=2, default=(1e-6, 2e3))
    ap.add_argument("--telim", type=float, nargs=2, default=(0.0, 700.0))
    ap.add_argument("--vlim", type=float, nargs=2, default=(-0.5, 8.0))
    ap.add_argument("--normalise", choices=("none", "peak"), default="peak",
                    help="panel (d): raw W/m^3, or each curve to its own peak so the "
                         "SHAPES can be compared across a 3-decade span in magnitude")
    ap.add_argument("--out", default="fig2_ic.png")
    ap.add_argument("--dpi", type=int, default=130)
    a = ap.parse_args()

    from laserprod import config as lpconfig
    spec = ([tuple(q.split("=", 1)) for q in a.leg] if a.leg else
            [("kinetic, FLASH IC (2698)", "runs/P4/P4_lez_kin_flashic"),
             ("kinetic, analytic IC (2698)", "runs/P4/P4_lez_kin_bg"),
             ("kinetic, FLASH IC (100)", "runs/P4/P4_lez_kin_flashic_ct")])

    F = X.flash_series(X.FLASH_DIR, "lez1d")
    f = X.pick(F, a.flash_tau)
    print(f"  FLASH at tau = {f['tau']:.3f}  (t = {f['t']*1e9:.3f} ns)")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 4, figsize=(19.0, 4.3))

    # FLASH: depo [erg/g/s] * dens [g/cc] -> W/m^3
    with_dep = ("depo" in f) and ("dens" in f)
    Pf = None
    if "depo" in f:
        Pf = np.asarray(f["depo"], float)
    ax[0].semilogy(f["zeta"], np.maximum(f["ne"], 1e-30), color=C_FLASH, lw=2.2,
                   label="FLASH (0.1 ns)")
    ax[1].plot(f["zeta"], f["Te"], color=C_FLASH, lw=2.2)
    ax[2].plot(f["zeta"], f["v"], color=C_FLASH, lw=2.2)

    rows = []
    for i, (lab, path) in enumerate(spec):
        col = PALETTE[i % len(PALETTE)]
        try:
            cfg = lpconfig.load(path)
        except Exception as exc:
            print(f"  {lab}: {exc}"); continue
        sc = X.warpx_scales(float(cfg["reference"]["mass_ratio"]))
        dep = pic_deposition(path, sc)
        if dep is None:
            print(f"  {lab}: no step-0 laserdep_profile"); continue
        ls = ("--", "-.", ":")[i % 3]
        ax[0].semilogy(dep["zeta"], np.maximum(dep["ne"], 1e-30), color=col, lw=1.6,
                       ls=ls, label=f"{lab}")
        ax[1].plot(dep["zeta"], dep["Te"], color=col, lw=1.6, ls=ls)
        # Panel (c) cannot come from the deposition dump -- it carries no velocity -- so
        # the flow speed is a weight-weighted ion moment from the step-0 plotfile.
        try:
            S0 = X.warpx_particles(path, X.SP_KIN, sc=sc)
            s0 = S0[0] if S0 else None
            if s0 is not None and s0.get("v") is not None:
                ax[2].plot(s0["zeta"], s0["v"], color=col, lw=1.4, ls=ls)
        except Exception as exc:
            print(f"    {lab}: no step-0 velocity ({exc})")
        ax[3].plot(dep["zeta"],
                   dep["P"] / (dep["P"].max() if a.normalise == "peak" and dep["P"].max() > 0 else 1.0),
                   color=col, lw=1.6, ls=ls)
        # The critical surface is the OUTERMOST n_cr crossing -- the one the laser meets
        # first. Scanning from the start of the array finds the REAR of the slab instead,
        # which is inside the target and physically meaningless here.
        hit = np.where(np.asarray(dep["ne"]) >= 1.0)[0]
        zcr = dep["zeta"][hit[-1]] if hit.size else np.nan
        tot = np.trapezoid(dep["P"], dep["zeta"] * sc["di0"])
        rows.append((lab, sc["mass_ratio"], zcr, dep["Te"].max(), tot,
                     dep["zeta"][int(np.argmax(dep["P"]))]))

    if Pf is not None:
        ax[3].plot(f["zeta"], Pf / (Pf.max() if a.normalise == "peak" and Pf.max() > 0 else 1.0),
                   color=C_FLASH, lw=2.2, label="FLASH")
        hitF = np.where(np.asarray(f["ne"]) >= 1.0)[0]
        rows.append(("FLASH", np.nan,
                     np.asarray(f["zeta"])[hitF[-1]] if hitF.size else np.nan,
                     float(np.max(f["Te"])), np.nan,
                     np.asarray(f["zeta"])[int(np.argmax(Pf))]))

    print(f"\n  {'leg':<28} {'m_i/m_e':>8} {'zeta(n_cr)':>11} {'T_e max':>9} "
          f"{'peak P_abs at':>14}")
    for lab, mr, zcr, tmax, tot, zp in rows:
        print(f"  {lab:<28} {mr:8.0f} {zcr:11.2f} {tmax:9.1f} {zp:14.2f}"
              if np.isfinite(mr) else
              f"  {lab:<28} {'--':>8} {zcr:11.2f} {tmax:9.1f} {zp:14.2f}")

    for k, (lab, ylab) in enumerate(((None, r"$n_e/n_{cr}$"), (None, r"$T_e$  [eV]"),
                                     (None, r"$v_z/C_{S0}$"),
                                     (None, r"$P_{abs}$" + (" / peak" if a.normalise == "peak" else r"  [W/m$^3$]")))):
        ax[k].set_xlabel(r"$\zeta = z/d_{i0}$")
        ax[k].set_ylabel(ylab)
        ax[k].set_xlim(*a.xlim)
        lpp.style_axes(ax[k])
    ax[0].set_ylim(*a.nelim); ax[0].axhline(1.0, color="0.55", ls=":", lw=0.9)
    ax[1].set_ylim(*a.telim); ax[2].set_ylim(*a.vlim)
    for k, t in enumerate(("(a) electron density", "(b) electron temperature",
                           "(c) flow speed", "(d) laser power absorption")):
        ax[k].set_title(t, loc="left", fontsize=10, fontweight="bold")
    ax[0].legend(fontsize=7.5, loc="lower left", framealpha=0.92)
    fig.suptitle("Lezhnin 2025 Fig. 2 replicated -- the INITIAL CONDITIONS. The paper's "
                 "own acceptance test for an IC is panel (d): the corona need not match "
                 "FLASH pointwise, it must ABSORB THE SAME WAY.", fontsize=10.5, y=1.02)
    fig.tight_layout()
    lpp.savefig(fig, a.out, run_id="P4_lez_kin_flashic", dpi=a.dpi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
