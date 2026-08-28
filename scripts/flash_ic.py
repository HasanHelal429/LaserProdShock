#!/usr/bin/env python3
"""The FLASH state that becomes the PIC initial condition — the four transferred quantities.

    /opt/anaconda3/envs/physics/bin/python scripts/flash_ic.py
    /opt/anaconda3/envs/physics/bin/python scripts/flash_ic.py --overlay runs/P4/P4_lez_kin_mr100
    /opt/anaconda3/envs/physics/bin/python scripts/flash_ic.py --time 0.1 --zlim -2 25 --units um

WHAT THIS SHOWS. Every PIC leg in Phase 4 starts from FLASH's t = 0.1 ns state rather than
from a cold solid (`HANDOFF.md` §2). Exactly four profiles cross that boundary --
`n_e`, `T_e`, `T_i` and `v_z` -- and each is fitted into a handful of config primaries. This
draws what was actually handed over, so the fit can be judged against it rather than against
the prose.

The shaded band on the density panel is the part the PIC legs DO NOT represent: FLASH's
overdense interior runs to ~795 n_cr and the decks cap the target at 10, which is why
`ne_peak` is never comparable between the codes.

With `--overlay <run_dir>` the WarpX config's fitted IC is drawn dashed on top, reconstructed
from the config primaries (the same expressions `deck.py` renders), so you can see what
`scale_length_de`, `theta_e_init` and `drift_uz_de` each stand for.

Axes default to the comparison units -- zeta = z/d_i0 and each quantity normalised the way
`xcode_compare` normalises it. `--units um` switches the abscissa to microns and the
temperatures to raw eV, which is what you want when talking to someone outside the project.
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warnings; warnings.filterwarnings("ignore")
import xcode_compare as xc                                   # noqa: E402
from laserprod import plotting as lpp                        # noqa: E402

ME_C2_EV = xc.ME * xc.C ** 2 / xc.QE      # 510999 eV
N_MAX_PIC = 10.0            # the decks' density cap, paper Appendix A


def warpx_ic(cfg, sc, zlim):
    """Reconstruct a leg's initial profile from its config primaries, on zeta.

    Built only over the plotted window: the drift ramp `uza + uzb*z/d_e` grows without
    bound, so reconstructing it over the whole domain and letting matplotlib autoscale
    flattens every FLASH curve on the velocity panel.
    """
    tgt = cfg["plasma"]["target"]
    de_per_di0 = sc["di0"] / xc.DE_CR
    z_de = np.linspace(zlim[0] * de_per_di0, zlim[1] * de_per_di0, 4000)   # in d_e
    zeta = z_de / de_per_di0
    w, c = float(tgt["thickness_de"]), float(tgt["center_de"])
    face = c + w / 2.0
    n = np.where(np.abs(z_de - c) <= w / 2.0, float(tgt["density_over_ncr"]), 0.0)
    Ln = float(tgt.get("scale_length_de", 0) or 0)
    if Ln:
        ncor = float(tgt.get("corona_density_over_ncr", 1.0))
        zcor = float(tgt.get("corona_offset_de", 0.0))
        n = np.maximum(n, np.where(z_de > face, ncor * np.exp(-(z_de - face - zcor) / Ln), 0.0))
    Te = np.where(np.abs(z_de - c) <= w / 2.0,
                  float(tgt["theta_e_solid"]) * ME_C2_EV,
                  float(tgt["theta_e_init"]) * ME_C2_EV)
    Ti = np.where(np.abs(z_de - c) <= w / 2.0,
                  float(tgt.get("theta_i_solid", tgt["theta_e_solid"])) * ME_C2_EV,
                  float(tgt["theta_i_init"]) * ME_C2_EV)
    v = np.zeros_like(z_de)
    if tgt.get("drift_uz_de") is not None:
        a, b = (float(q) for q in tgt["drift_uz_de"])
        v = np.where(z_de > face, (a + b * (z_de - face)) * xc.C / sc["cs0"], 0.0)
    return dict(zeta=zeta, ne=n, Te=Te, Ti=Ti, v=v, face=face / de_per_di0)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--time", type=float, default=0.1002,
                    help="FLASH time in ns to draw (default 0.1002, the handoff dump)")
    ap.add_argument("--flash-dir", default=xc.FLASH_DIR)
    ap.add_argument("--flash-base", default="lez1d")
    ap.add_argument("--overlay", default=None, metavar="RUN_DIR",
                    help="draw a WarpX config's fitted IC dashed on top")
    ap.add_argument("--zlim", type=float, nargs=2, default=(-2.0, 22.0), metavar=("LO", "HI"))
    ap.add_argument("--units", choices=["zeta", "um"], default="zeta")
    ap.add_argument("--nfloor", type=float, default=1e-4, help="lower limit of the density panel")
    ap.add_argument("--no-cap-band", action="store_true", help="hide the >10 n_cr shading")
    ap.add_argument("--out", default="flash_ic.png")
    ap.add_argument("--run-id", default="P4_lez_flash")
    a = ap.parse_args()

    import matplotlib.pyplot as plt

    F = xc.flash_series(a.flash_dir, a.flash_base)
    f = min(F, key=lambda d: abs(d["t"] * 1e9 - a.time))
    print(f"FLASH dump at t = {f['t']*1e9:.4f} ns  (tau = {f['tau']:.3f}), "
          f"{len(f['zeta'])} leaf cells")

    W = sc = None
    if a.overlay:
        from laserprod import config as lpconfig
        cfg = lpconfig.load(a.overlay)
        sc = xc.warpx_scales(float(cfg["reference"]["mass_ratio"]))
        W = warpx_ic(cfg, sc, a.zlim)
        print(f"overlay: {os.path.basename(os.path.normpath(a.overlay))}  "
              f"mass_ratio {cfg['reference']['mass_ratio']}  d_i0 {sc['di0']*1e6:.3f} um")

    xs = (lambda z: z) if a.units == "zeta" else (lambda z: z * xc.DI0_F * 1e6)
    xlab = (r"$\zeta = z/d_{i0}$   (FLASH's real $d_{i0}$ = 7.256 µm)" if a.units == "zeta"
            else r"z  [µm from the initial target face]")

    PAN = [("ne",  r"$n_e / n_{cr}$",                       lpp.C_TARGET,  True),
           ("Te",  r"$T_e$  [eV]",                          lpp.C_LASER,   True),
           ("Ti",  r"$T_i$  [eV]",                          lpp.C_FOURTH,  True),
           ("v",   r"$v_z / C_{S0}$",                       lpp.C_AMBIENT, False)]
    fig, axes = plt.subplots(len(PAN), 1, figsize=(8.2, 9.4), sharex=True,
                             gridspec_kw=dict(hspace=0.14))
    for ax, (key, lab, col, logy) in zip(axes, PAN):
        lpp.style_axes(ax)
        ax.plot(xs(f["zeta"]), f[key], color=col, lw=1.9, zorder=3,
                label="FLASH at handoff")
        if W is not None:
            ax.plot(xs(W["zeta"]), W[key], color=lpp.INK_MUTED, lw=1.4, ls=(0, (5, 3)),
                    zorder=4, label="WarpX config IC")
        if logy:
            ax.set_yscale("log")
        ax.set_ylabel(lab, fontsize=10.5)
        ax.axvline(0.0, color=lpp.INK_MUTED, lw=0.9, ls=":", zorder=1)
        ax.tick_params(labelsize=9, colors=lpp.INK_MUTED)
    # density panel: mark what the PIC legs throw away
    ax = axes[0]
    ax.set_ylim(a.nfloor, max(f["ne"].max(), 1e3) * 2)
    if not a.no_cap_band:
        ax.axhspan(N_MAX_PIC, ax.get_ylim()[1], color=lpp.C_TARGET, alpha=0.10, zorder=0)
        ax.axhline(N_MAX_PIC, color=lpp.C_TARGET, lw=1.0, ls="--", alpha=0.8, zorder=2)
        ax.annotate(f"PIC legs cap here ({N_MAX_PIC:g} $n_{{cr}}$)\n"
                    f"FLASH peaks at {f['ne'].max():.0f}",
                    xy=(a.zlim[1] if a.units == "zeta" else xs(a.zlim[1]), N_MAX_PIC),
                    xytext=(-8, 9), textcoords="offset points", ha="right",
                    fontsize=8, color=lpp.C_TARGET, linespacing=1.3)
    ax.axhline(1.0, color=lpp.INK_MUTED, lw=0.9, ls=":", zorder=2)
    ax.annotate("$n_{cr}$", xy=(xs(a.zlim[0]), 1.0), xytext=(4, 4),
                textcoords="offset points", fontsize=8, color=lpp.INK_MUTED)
    # FLASH's delivered T_i carries a vacuum artifact reaching ~1e5 eV where there is no
    # plasma -- the thing ic_ourflash's generator masks. Say so rather than let it read as
    # physics, and keep it out of the autoscale.
    mask = (f["zeta"] >= a.zlim[0]) & (f["zeta"] <= a.zlim[1])
    for ax, (key, _, _, logy) in zip(axes, PAN):
        if key == "ne" or not logy:
            continue
        y = f[key][mask]; y = y[np.isfinite(y) & (y > 0)]
        if len(y):
            ax.set_ylim(max(y.min() * 0.4, 1e-3), y.max() * 3)
    axes[2].annotate("FLASH's delivered $T_i$ carries a vacuum artifact here\n"
                     "(no plasma to carry it) — the IC generator masks it",
                     xy=(0.985, 0.93), xycoords="axes fraction", ha="right", va="top",
                     fontsize=7.8, color=lpp.INK_MUTED, linespacing=1.35)
    axes[1].annotate("solid: FLASH 290 K = 0.025 eV,\nWarpX floor 1.26 eV (Debye)",
                     xy=(0.02, 0.06), xycoords="axes fraction", ha="left", va="bottom",
                     fontsize=7.8, color=lpp.INK_MUTED, linespacing=1.35)
    axes[3].legend(loc="upper left", fontsize=8.6, frameon=False)
    axes[-1].set_xlabel(xlab, fontsize=10.5, labelpad=8)
    axes[-1].set_xlim(*(xs(np.array(a.zlim))))
    v = f["v"][mask]; v = v[np.isfinite(v)]
    if len(v):
        axes[3].set_ylim(min(v.min(), 0) - 0.5, v.max() * 1.35 + 0.5)

    fig.suptitle(f"What FLASH hands to the PIC legs — t = {f['t']*1e9:.3f} ns "
                 f"($\\tau$ = {f['tau']:.2f})",
                 fontsize=12.5, color=lpp.INK, y=0.945)
    fig.text(0.5, 0.005,
             "These four profiles are the entire handoff. Everything left of "
             "$\\zeta$ = 0 is inside the target; the shaded\nband is the overdense interior "
             "the PIC decks do not represent. See HANDOFF.md §5.",
             ha="center", fontsize=8.4, color=lpp.INK_MUTED, linespacing=1.5)
    fig.subplots_adjust(bottom=0.105, top=0.905)
    lpp.savefig(fig, a.out, run_id=a.run_id)


if __name__ == "__main__":
    main()
