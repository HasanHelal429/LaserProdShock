#!/usr/bin/env python3
"""talk_xcode.py -- the ablation cross-code comparison, drawn for a projector.

``xcode_compare.py`` writes the working figures: ``history.png`` is four panels
across 17.5 inches and ``profiles.png`` is a 5x3 grid. Both are meant to be read
at a desk. On a slide the panel titles land near 4 pt and the grid is
unparseable, so this redraws the SAME series -- same loaders, same unit map,
same scalars -- as two or three large panels sized for one slide.

    /opt/anaconda3/envs/physics/bin/python scripts/talk_xcode.py
    /opt/anaconda3/envs/physics/bin/python scripts/talk_xcode.py --panels front,v,Te
    /opt/anaconda3/envs/physics/bin/python scripts/talk_xcode.py --figure profiles \
        --kinetic runs/P4/P4_lez_kin

Two figures:
  --figure history  (default)  the scalar histories, one large panel each.
                               Writes media/xcode/talk_ablation.png.
  --figure profiles            the density profiles themselves, overplotted at
                               several times with one colour per time, FLASH
                               solid against the kinetic dashed. Writes
                               media/xcode/talk_profiles.png.

The profiles figure is built to be run against a run that is still moving. It
prints the tau range each code actually covers, DROPS a requested time rather
than substituting the nearest dump for it (--tol), skips a plotfile that is
mid-write, and picks its own times from the shared range on --taus 0.

Nothing here recomputes physics; it imports xcode_compare so the talk figure
cannot drift from the notebook figure.

ONLY THE UNDERDENSE PLUME IS COMPARABLE. The WarpX target is 10 n_cr where
FLASH's is 795 n_cr (decision D5, TEST_PLAN 12.6), so the profiles figure caps
its y axis just above critical rather than showing two interiors that are
different objects by construction.

CAVEAT TO CARRY ONTO THE SLIDE: RESULTS.md 2026-08-18 records two disqualifiers
on the hybrid's agreement with FLASH -- it absorbs 2.1x less laser yet expands
faster, and it is not robust to the background density (bg3 -> bg4 moves the
plume front 1.8x). The right claim from this figure is that the ray-traced
laser drives an ablation whose bulk hydrodynamics are the right SHAPE, not that
the hybrid is validated against FLASH.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                                          # noqa: E402
import xcode_compare as X                                   # noqa: E402

DEFAULT_OUT = "media/xcode/talk_ablation.png"

# Time colours. A sequential colormap (viridis) was tried first and failed on
# the slide: adjacent times differed only in lightness, and four curves of the
# same hue crossing each other are unreadable at the back of a room. These are
# four Okabe-Ito hues -- distinguishable under the common colour-vision
# deficiencies, and distinguishable from each other in luminance too, so they
# survive a bad projector and a greyscale handout.
TIME_COLOURS = ("#0072B2",   # blue
                "#D55E00",   # vermillion
                "#009E73",   # bluish green
                "#CC79A7",   # reddish purple
                "#E69F00",   # orange
                "#56B4E9",   # sky blue
                "#8B4513")   # saddle brown, for a 7th time nobody should need

# How far a plotfile may sit from a requested tau before it is dropped rather
# than drawn. xcode_compare.pick() returns the NEAREST entry unconditionally, so
# on a run that stopped early it will happily return tau = 12 for a request of
# tau = 27 and the label will lie. See _pick_near().
TAU_TOL = 0.08

PANELS = {
    "Te":    ("Te_mean_plume", r"$T_e$ in the plume  [eV]"),
    "front": ("zeta_front",    r"plume front  $\zeta$  [$d_{i0}$]"),
    "v":     ("v_at_0p1",      r"outflow  $v_z/C_{S0}$"),
    "Ln":    ("L_n",           r"scale length  $L_n/d_{i0}$"),
}


def series(kin, hyb):
    """The same three legs history() builds, in the same units."""
    F = X.flash_series(X.FLASH_DIR, "lez1d")
    K = X.warpx_particles(kin, X.SP_KIN)
    H = X.warpx_particles(hyb, X.SP_HYB)
    Hf = X.warpx_fields(hyb)
    out = {}
    for name, S in (("FLASH", F), ("kinetic", K), ("hybrid", H)):
        rows = []
        for s in S:
            if s["tau"] <= 0:
                continue
            if name == "hybrid":
                hf = X.pick(Hf, s["tau"], "Te")
                Te = np.interp(s["zeta"], hf["zeta"], hf["Te"]) if hf else None
            else:
                Te = s.get("Te")
            sc = X.scalars(s["zeta"], s["ne"], Te, s.get("v"))
            sc["tau"] = s["tau"]
            rows.append(sc)
        out[name] = rows
    return out


def _require_dir(path, what):
    if not os.path.isdir(path):
        raise SystemExit(f"error: no {what} at {path!r}\n"
                         f"       (cwd is {os.getcwd()}; paths are relative to "
                         f"the repo root)")
    return path


def _plotfiles(run_dir, prefix):
    """Plotfiles for a run, with the failure modes of a LIVE run handled.

    Two things bite while a run is still going. A plotfile currently being
    written is not readable and yt raises on it -- so the last one is skipped
    with a warning rather than taking the whole figure down. And a run that has
    not dumped anything yet gives an empty list, which downstream turns into an
    IndexError a long way from the cause.
    """
    from laserprod import io as lpio
    _require_dir(run_dir, "run directory")
    ps = lpio.plotfiles(run_dir, prefix)
    if not ps:
        raise SystemExit(f"error: {run_dir} has no {prefix}* plotfiles yet.\n"
                         f"       If the run is still going, wait for its first "
                         f"dump; if it finished, check diags/ went where you "
                         f"think (launch.sh cd's into the run dir).")
    return ps


def warpx_ne_from_ions(run_dir):
    """Quasineutral n_e = Z n_i on the grid, from the ION charge density.

    xcode_compare.warpx_fields prefers the electron species where they exist. In a
    run with NO ambient that is not the same quantity in the far field: the hot
    electron tail streams ahead of the ions, so n_e overstates how far the plume
    itself has got. Comparing against a fluid code, Z n_i is the like-for-like
    profile. Same loader, same grid, same normalisation -- only the field differs.
    """
    import yt
    out, skipped = [], []
    for p in _plotfiles(run_dir, "diag_fields"):
        try:
            ds = yt.load(p)
            g = ds.covering_grid(0, ds.domain_left_edge, ds.domain_dimensions)
            fl = {f[1] for f in ds.field_list if f[0] == "boxlib"}
            isp = [f for f in fl if f.startswith("rho_") and "ion" in f]
            if not isp:
                skipped.append((os.path.basename(p), "no rho_*ion* field"))
                continue
            z = np.linspace(float(ds.domain_left_edge[0]),
                            float(ds.domain_right_edge[0]),
                            int(ds.domain_dimensions[0]) + 1)
            z = 0.5 * (z[1:] + z[:-1])
            ne = sum(np.asarray(g["boxlib", f])[:, 0, 0] for f in isp) / X.QE
        except Exception as e:                       # a dump still being written
            skipped.append((os.path.basename(p), type(e).__name__))
            continue
        out.append(dict(t=float(ds.current_time), tau=float(ds.current_time) / X.TAU_W,
                        zeta=z / X.DI0_W, ne=ne / X.N_CR))
    for name, why in skipped:
        print(f"  skipped {name}: {why}")
    if not out:
        raise SystemExit(f"error: no readable diag_fields dump in {run_dir}")
    return out


def _pick_near(series, tau, tol, key=None):
    """Nearest entry in tau, but only if it is actually near.

    The reason this is not just X.pick: that returns the nearest entry however
    far away it is. A run that stopped at tau = 12 then answers a request for
    tau = 27 with its last dump, and the figure draws it under a "tau = 27"
    label -- a wrong plot that looks entirely right. This returns (entry, dtau)
    and lets the caller drop or annotate it.
    """
    hit = X.pick(series, tau, key)
    if hit is None:
        return None, None
    d = abs(hit["tau"] - tau)
    return (hit, d) if d <= tol * max(tau, 1.0) else (None, d)


def profiles(flash, kin, taus, ax, ylim, xlim, tol=TAU_TOL, colours=None):
    """n_e(zeta) at several times, one colour per time, two codes per colour.

    Draws whatever is available and reports what is not, rather than failing or
    -- worse -- quietly substituting the wrong time. Returns the number of
    (code, time) curves actually drawn.
    """
    colours = colours or TIME_COLOURS
    if len(taus) > len(colours):
        raise SystemExit(f"error: {len(taus)} times requested but only "
                         f"{len(colours)} distinct colours are defined. More "
                         f"than that is unreadable on a slide anyway -- split "
                         f"the figure or pass fewer --taus.")

    drawn = 0
    for tau, col in zip(taus, colours):
        f, df = _pick_near(flash, tau, tol)
        k, dk = _pick_near(kin, tau, tol, "ne")
        if f is None:
            print(f"  tau = {tau:g}: no FLASH dump within {tol:.0%}"
                  + (f" (nearest is {df:+.1f} away)" if df is not None
                     else " (no FLASH data at all)"))
        else:
            ax.semilogy(f["zeta"], f["ne"], color=col, lw=2.4, ls="-")
            drawn += 1
        if k is None:
            print(f"  tau = {tau:g}: no kinetic dump within {tol:.0%}"
                  + (f" (nearest is {dk:+.1f} away)" if dk is not None
                     else " (no kinetic data at all)"))
        else:
            ax.semilogy(k["zeta"], k["ne"], color=col, lw=1.8, ls="--")
            drawn += 1
    ax.axhline(1.0, color="0.45", ls=":", lw=1.2)
    ax.text(xlim[1], 0.86, r"$n_{cr}$", ha="right", va="top", color="0.35")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    # One tick per decade. Matplotlib thins them to every other decade on a
    # panel this short, which drops 10^0 -- the one value the reader needs,
    # since the n_cr line sits on it.
    import matplotlib.ticker as mt
    ax.yaxis.set_major_locator(mt.LogLocator(base=10.0, numticks=99))
    ax.yaxis.set_minor_locator(mt.LogLocator(base=10.0, subs="auto", numticks=99))
    ax.yaxis.set_minor_formatter(mt.NullFormatter())
    ax.set_xlabel(r"$\zeta = z/d_{i0}$")
    ax.set_ylabel(r"$n_e/n_{cr}$")
    ax.grid(alpha=0.15)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)

    # Two legends: colour carries the time, dash carries the code. One combined
    # legend would need len(taus) x 2 entries to say the same thing.
    from matplotlib.lines import Line2D
    t_keys = [Line2D([], [], color=c, lw=2.4,
                     label=rf"$\tau = {t:g}$") for t, c in zip(taus, colours)]
    c_keys = [Line2D([], [], color="0.25", lw=2.4, ls="-", label="FLASH"),
              Line2D([], [], color="0.25", lw=1.8, ls="--", label="kinetic")]
    # The times run ABOVE the axes in one row: this panel is wide and short, and
    # a stacked legend in any corner sat on the curves or the n_cr tag. It goes
    # on the FIGURE, not the axes -- an axes legend anchored outside its axes is
    # invisible to tight_layout, and the bbox_inches="tight" workaround dropped
    # it from the saved PNG altogether. The caller reserves the strip.
    ax.figure.legend(handles=t_keys, frameon=False, ncol=len(taus),
                     loc="upper center", handlelength=1.6, columnspacing=1.8)
    ax.legend(handles=c_keys, frameon=False, loc="lower left", handlelength=2.4)
    return drawn


def coverage(series, label):
    """Print what times a series actually spans. The first thing to know when a
    requested tau comes back empty."""
    taus = sorted(s["tau"] for s in series)
    print(f"  {label}: {len(taus)} dumps, tau {taus[0]:.2f} .. {taus[-1]:.2f}")
    return taus


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kinetic", default="runs/P4/P4_lez_kin_bg")
    ap.add_argument("--hybrid", default="runs/P4/P4_lez_hyb_bg3")
    ap.add_argument("--figure", choices=("history", "profiles"), default="history")
    ap.add_argument("--panels", default="front,v",
                    help="history only: comma list from " + ",".join(PANELS))
    ap.add_argument("--taus", type=float, nargs="+", default=(6.7, 13.5, 20.3, 27.0),
                    help="profiles only: the times to overplot, in tau. Pass a "
                         "single 0 to choose them automatically from the range "
                         "the two codes actually share -- useful on a partial run")
    ap.add_argument("--tol", type=float, default=TAU_TOL,
                    help="profiles only: how close a dump must be to a requested "
                         "tau, as a fraction of it. A dump further away is "
                         "DROPPED, never relabelled")
    ap.add_argument("--from", dest="src", choices=("electrons", "ions"),
                    default="ions",
                    help="profiles only: take the kinetic n_e from the electron "
                         "species, or as Z n_i from the ions. With no ambient the "
                         "hot electron tail runs ahead of the plume, so ions is "
                         "the like-for-like comparison against a fluid code")
    ap.add_argument("--cmap", default=None,
                    help="profiles only: sample a matplotlib colormap for the "
                         "time colours instead of the built-in distinct set. "
                         "Sequential maps read poorly here -- see TIME_COLOURS")
    ap.add_argument("--ylim", type=float, nargs=2, default=(1.0e-3, 3.0e1),
                    help="profiles only: n_e/n_cr window. The default stops just "
                         "above critical -- the overdense interiors are 795 vs 10 "
                         "n_cr and are NOT comparable (D5)")
    ap.add_argument("--xlim", type=float, nargs=2, default=(0.0, 110.0),
                    help="profiles only: zeta window")
    ap.add_argument("--fontsize", type=float, default=17.0)
    ap.add_argument("--figsize", type=float, nargs=2, default=None,
                    help="inches; default 5.2 per panel x 4.3")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--out", default=DEFAULT_OUT,
                    help="default: talk_ablation.png for history, "
                         "talk_profiles.png for profiles")
    a = ap.parse_args()

    keys = [k.strip() for k in a.panels.split(",") if k.strip()]
    bad = [k for k in keys if k not in PANELS]
    if bad:
        ap.error(f"unknown panel(s) {bad}; choose from {list(PANELS)}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.size": a.fontsize,
        "axes.labelsize": a.fontsize,
        "axes.titlesize": a.fontsize,
        "xtick.labelsize": a.fontsize - 3,
        "ytick.labelsize": a.fontsize - 3,
        "legend.fontsize": a.fontsize - 2,
    })

    if a.figure == "profiles":
        out = a.out if a.out != DEFAULT_OUT else "media/xcode/talk_profiles.png"
        _require_dir(X.FLASH_DIR, "FLASH delivery")
        fl = X.flash_series(X.FLASH_DIR, "lez1d")
        if not fl:
            raise SystemExit(f"error: no lez1d plotfiles under {X.FLASH_DIR}")
        load = warpx_ne_from_ions if a.src == "ions" else X.warpx_fields
        kin = load(a.kinetic)

        tf = coverage(fl, "FLASH")
        tk = coverage(kin, f"kinetic ({os.path.basename(a.kinetic)})")

        taus = tuple(a.taus)
        if len(taus) == 1 and taus[0] == 0:
            # Auto: evenly spaced over the range BOTH codes cover. On a partial
            # run this is the difference between a figure and a puzzle.
            lo = max(min(tf), min(tk))
            hi = min(max(tf), max(tk))
            if not hi > lo:
                raise SystemExit(f"error: the two codes do not overlap in tau "
                                 f"(FLASH {min(tf):.2f}..{max(tf):.2f}, kinetic "
                                 f"{min(tk):.2f}..{max(tk):.2f})")
            taus = tuple(round(float(t), 1)
                         for t in np.linspace(lo + 0.25 * (hi - lo), hi, 4))
            print(f"  --taus auto -> {taus}")
        elif max(taus) > min(max(tf), max(tk)) * (1 + a.tol):
            print(f"  note: tau up to {max(taus):g} requested but the codes only "
                  f"share up to {min(max(tf), max(tk)):.2f} -- the late times "
                  f"will be dropped, not substituted. --taus 0 picks for you.")

        colours = None
        if a.cmap:
            colours = plt.get_cmap(a.cmap)(np.linspace(0.12, 0.88, len(taus)))

        # Wide and short by default. The slide gives this figure the full text
        # width but only ~4.5 cm of height under two bullets, so a 4:3-ish panel
        # is bound by the height and comes out half a slide wide.
        fig, ax = plt.subplots(figsize=tuple(a.figsize) if a.figsize else (8.0, 3.2))
        drawn = profiles(fl, kin, taus, ax, tuple(a.ylim), tuple(a.xlim),
                         tol=a.tol, colours=colours)
        if not drawn:
            raise SystemExit("error: nothing was drawn -- no dump in either code "
                             "landed near any requested tau. Run with --taus 0.")
        # Reserve the top strip for the figure-level time key drawn by profiles().
        fig.tight_layout(rect=(0, 0, 1, 0.88))
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        fig.savefig(out, dpi=a.dpi)
        print(f"  figure: {out}  ({drawn} curves)")
        return 0

    ser = series(a.kinetic, a.hybrid)
    fs = tuple(a.figsize) if a.figsize else (5.2 * len(keys), 4.3)
    fig, ax = plt.subplots(1, len(keys), figsize=fs, squeeze=False)
    ax = ax[0]

    for j, k in enumerate(keys):
        field, label = PANELS[k]
        for name, col in X.COLS.items():
            r = ser[name]
            ls = "-" if name == "FLASH" else ("--" if name == "kinetic" else "-.")
            ax[j].plot([q["tau"] for q in r], [q.get(field, np.nan) for q in r],
                       color=col, ls=ls, lw=2.6 if name == "FLASH" else 2.2,
                       label=name)
        ax[j].set_xlabel(r"$\tau = t/(d_{i0}/C_{S0})$")
        ax[j].set_title(label)
        ax[j].set_xlim(0, 27.5)
        ax[j].grid(alpha=0.15)
        for side in ("top", "right"):
            ax[j].spines[side].set_visible(False)
        if k == "Te":
            # Each leg has its OWN Manheimer target: T_e,SS ~ mu^(1/3), and the
            # WarpX legs run 18.36x lighter. Drawing only 823 eV is the error
            # RESULTS.md 2026-08-18 retracts.
            ax[j].axhline(X.TE_REF, color="0.45", ls=":", lw=1.2)
            ax[j].axhline(X.TSS_REDUCED, color="0.45", ls="--", lw=1.2)
            ax[j].set_ylim(0, 1000)

    ax[0].legend(frameon=False, loc="upper left")
    fig.tight_layout()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    fig.savefig(a.out, dpi=a.dpi)
    print(f"  figure: {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
