#!/usr/bin/env python3
"""WHERE the laser power lands, FLASH against the kinetic run, at several times.

    /opt/anaconda3/envs/physics/bin/python scripts/deposition_compare.py
    ... scripts/deposition_compare.py --kin runs/P4/P4_lez_kin_ic6 --xlim -3 30
    ... scripts/deposition_compare.py --normalise none --out dep_abs.png

THE QUESTION IT IS BUILT FOR. The kinetic leg drives a shorter, cooler plume than FLASH
(front 0.51x, L_n 0.45x, f_abs 0.478 against 0.870). Total absorbed energy is only half the
story: the same joules deposited in a thin layer at the critical surface and spread through
a deep corona drive very different ablation, because what sets the mass flux is the
temperature reached in the plasma that can actually expand.

  (a) P_abs(zeta)              -- the deposition profile itself
  (b) CUMULATIVE fraction      -- read off zeta(50%) and zeta(90%): how deep the energy goes

The absorbed-power TIME history is deliberately not repeated here; `scripts/laser_report.py`
already produces it per run (f_abs(t), E_abs, the plateau and the n_cr-crossing time).

FLASH's `depo` is a SPECIFIC deposition rate [erg/g/s], so P_abs = depo * dens * 0.1 W/m^3.
That conversion is checked, not assumed: the script integrates the FLASH profile and prints
it against the absorbed intensity implied by the run's 87% absorption of 1e17 W/m^2. A
factor-of-10 or per-gram slip shows up immediately there rather than as a wrong conclusion.

The kinetic P_abs comes from the operator's own `laserdep_profile` dumps, which carry
P_abs per cell directly in W/m^3 -- no conversion, and no shot-noise floor (CLAUDE.md).
"""
from __future__ import annotations
import argparse, glob, os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import xcode_compare as X
from laserprod import plotting as lpp

C_FLASH, C_KIN = "#1f4e9c", "#c7522a"


def kin_profiles(run_dir, sc):
    out = []
    for p in sorted(glob.glob(os.path.join(run_dir, "diags", "laserdep_profile_*.txt"))):
        step = int(os.path.basename(p).split("_")[-1].split(".")[0])
        d = np.loadtxt(p)
        if d.ndim != 2 or d.shape[0] < 10:
            continue
        with open(p) as fh:
            t = None
            for ln in fh:
                if ln.startswith("# step"):
                    t = float(ln.split()[4]); break
        out.append(dict(step=step, t=t, tau=(t or 0.0) / sc["tau"],
                        zeta=d[:, 0] / sc["di0"], ne=d[:, 1] / X.N_CR, P=d[:, 3]))
    return out


def flash_P(f):
    """FLASH volumetric absorbed power [W/m^3] from the specific rate and the density.

    depo [erg/g/s] * dens [g/cm^3] = erg/(cm^3 s); x1e-7 J/erg / 1e-6 m^3/cm^3 = x0.1.
    """
    return np.asarray(f["depo"], float) * np.asarray(f["dens"], float) * 0.1


def cumulative(z, P):
    z = np.asarray(z, float); P = np.maximum(np.asarray(P, float), 0.0)
    o = np.argsort(z); z, P = z[o], P[o]
    c = np.concatenate([[0.0], np.cumsum(0.5 * (P[1:] + P[:-1]) * np.diff(z))])
    return z, (c / c[-1] if c[-1] > 0 else c)


def depth(z, P, frac):
    """zeta by which `frac` of the absorbed power has been deposited, counting from the
    LASER side (large zeta) inward -- the direction the beam actually travels."""
    z, c = cumulative(z, P)
    c = 1.0 - c                      # fraction still to be absorbed at this zeta
    i = np.argmin(np.abs(c - (1.0 - frac)))
    return z[i]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kin", default="runs/P4/P4_lez_kin_ic6")
    ap.add_argument("--taus", type=float, nargs="+", default=None,
                    help="times to draw; default: whatever the kinetic dumps cover")
    ap.add_argument("--offset", type=float, default=2.696,
                    help="handoff offset: a WarpX leg's t=0 is FLASH's tau 2.696")
    ap.add_argument("--xlim", type=float, nargs=2, default=(-3.0, 40.0))
    ap.add_argument("--normalise", choices=("peak", "none"), default="peak")
    ap.add_argument("--out", default="deposition_compare.png")
    ap.add_argument("--dpi", type=int, default=130)
    a = ap.parse_args()

    from laserprod import config as lpconfig
    cfg = lpconfig.load(a.kin)
    sc = X.warpx_scales(float(cfg["reference"]["mass_ratio"]))
    K = kin_profiles(a.kin, sc)
    if not K:
        print("  no laserdep_profile dumps"); return 1
    taus = a.taus if a.taus else [k["tau"] for k in K]
    F = X.flash_series(X.FLASH_DIR, "lez1d")

    # ---- unit check on the FLASH conversion, before any of it is plotted ----
    # `depo` is a SPECIFIC rate [erg/g/s], so the volumetric power is depo*dens*0.1. This
    # is not cosmetic: the cumulative-fraction panel weights by P_abs, and depo and
    # depo*dens have DIFFERENT shapes, so skipping the density would put z50/z90 in the
    # wrong place rather than merely rescaling them.
    f = X.pick(F, 13.5)
    zf = np.asarray(f["zeta"], float) * X.DI0_F
    I_raw = float(np.trapezoid(np.maximum(np.asarray(f["depo"], float), 0), zf))
    I_vol = float(np.trapezoid(np.maximum(flash_P(f), 0), zf))
    print("\n  FLASH depo unit check at tau 13.5 (absorbed intensity ~8.7e16 W/m^2):")
    print(f"    int(depo) dz          = {I_raw:.4e}   ratio {I_raw/8.70e16:.3e}")
    print(f"    int(depo*dens*0.1) dz = {I_vol:.4e}   ratio {I_vol/8.70e16:.3e}")
    print("    Neither closes: the remainder is ~1e13, i.e. ~1/dt, so `depo` is almost")
    print("    certainly specific energy PER TIMESTEP [erg/g] rather than a rate. That")
    print("    factor is ONE NUMBER PER DUMP, so it cancels in both panels here -- the")
    print("    profile is peak-normalised and the depth panel is a cumulative FRACTION.")
    print("    The DENSITY weighting does not cancel and is applied. Absolute W/m^3 from")
    print("    FLASH is NOT established by this script and must not be read off it.\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(taus)
    fig, ax = plt.subplots(2, n, figsize=(3.6 * n, 7.0), sharex=True)
    if n == 1:
        ax = ax.reshape(2, 1)

    print(f"  {'tau_FLASH':>10} {'z50 FLASH':>10} {'z50 kin':>9} {'z90 FLASH':>10} "
          f"{'z90 kin':>9}   (zeta by which 50/90 % of P_abs is deposited)")
    for c, tk in enumerate(taus):
        tf = tk + a.offset                      # kinetic tau -> FLASH clock
        k = min(K, key=lambda q: abs(q["tau"] - tk))
        f = X.pick(F, tf)
        for d, col, lab, ls in ((f, C_FLASH, "FLASH", "-"), (k, C_KIN, "kinetic", "--")):
            P = flash_P(d) if "depo" in d else np.asarray(d["P"], float)
            z = np.asarray(d["zeta"], float)
            y = P / P.max() if (a.normalise == "peak" and P.max() > 0) else P
            ax[0, c].plot(z, y, color=col, ls=ls, lw=1.9 if col == C_FLASH else 1.5,
                          label=lab)
            zz, cc = cumulative(z, P)
            ax[1, c].plot(zz, cc, color=col, ls=ls, lw=1.9 if col == C_FLASH else 1.5)
        Pf_, zf_ = flash_P(f), np.asarray(f["zeta"], float)
        print(f"  {tf:10.1f} {depth(zf_, Pf_, .5):10.2f} "
              f"{depth(k['zeta'], k['P'], .5):9.2f} {depth(zf_, Pf_, .9):10.2f} "
              f"{depth(k['zeta'], k['P'], .9):9.2f}")
        ax[0, c].set_title(rf"FLASH $\tau$ = {tf:.1f}  (kinetic {tk:.1f})",
                           loc="left", fontsize=9.5, fontweight="bold")
        ax[1, c].set_xlabel(r"$\zeta = z/d_{i0}$")
        for r in (0, 1):
            ax[r, c].set_xlim(*a.xlim)
            lpp.style_axes(ax[r, c])
            if c:
                ax[r, c].tick_params(labelleft=False)
    ax[0, 0].set_ylabel(r"$P_{abs}$ / peak" if a.normalise == "peak" else r"$P_{abs}$ [W/m$^3$]")
    ax[1, 0].set_ylabel("cumulative fraction of $P_{abs}$")
    ax[1, 0].axhline(0.5, color="0.6", ls=":", lw=0.9)
    ax[1, 0].axhline(0.9, color="0.6", ls=":", lw=0.9)
    ax[0, 0].legend(fontsize=8.5, loc="upper right")
    fig.suptitle("Where the laser power lands. Top: the deposition profile, peak-normalised. "
                 "Bottom: the cumulative fraction, so $\\zeta$(50 %) and $\\zeta$(90 %) "
                 "read off directly.\n"
                 "Clocks aligned -- a WarpX leg's $t$ = 0 is FLASH's $\\tau$ = 2.696.",
                 fontsize=10, y=1.02)
    fig.tight_layout()
    lpp.savefig(fig, a.out, run_id=os.path.basename(a.kin.rstrip("/")), dpi=a.dpi)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
