"""Shared figure style, media paths and reusable panels.

Every script writes into ``media/<run_id>/`` (gitignored, regenerable) and prints the
path, so a run's figures are always in one predictable place.

THE PALETTE IS VALIDATED, NOT EYEBALLED. The three categorical series colours below
were checked with the ``dataviz`` skill's ``validate_palette.js`` in the exact order
they are used (target, ambient, laser): all hard checks pass on the light surface
(worst adjacent CVD dE 23.1 protan / 9.6 tritan, worst normal-vision dE 24.0). The
one WARN is sub-3:1 contrast for the aqua and yellow slots, whose required relief is
*visible labels* -- which is why every series in these figures is directly labelled
rather than identified by colour alone.

Two rules these figures never break:

* **No dual axis.** Two measures of different scale go in stacked panels sharing an
  x-axis, never on twin y-axes. (Comparing an absorbed *power* against a *density*
  on one frame is exactly the mistake that makes a shutoff look like a compression.)
* **Status is never colour alone.** Gate rows carry a glyph and a word as well as a
  colour, because a red cell is meaningless to a reader who cannot see red and
  useless in a printed lab notebook.
"""

from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

# --- categorical series colours, in the fixed order they are assigned ---
C_TARGET = "#eb6834"    # slot 1: the target / piston population (warm)
C_AMBIENT = "#2a78d6"   # slot 2: the ambient / upstream population (cool)
C_LASER = "#1baf7a"     # slot 3: the laser (absorbed power, optical depth)
C_FOURTH = "#eda100"    # slot 4: a fourth series (field energy, totals)

# --- non-series inks (never used to carry identity) ---
INK = "#1a1a19"
INK_2 = "#5c5b55"
INK_MUTED = "#8a8a82"
GRID = "#d8d7d0"
SURFACE = "#fcfcfb"

# --- status palette (fixed, never themed); always paired with a glyph + word ---
STATUS = {
    "pass": ("#0ca30c", "OK"),
    "info": ("#5c5b55", "i"),
    "warn": ("#fab219", "!"),
    "fail": ("#d03b3b", "X"),
    "post": ("#8a8a82", "-"),
}

ROLE_COLORS = {"target": C_TARGET, "ambient": C_AMBIENT, "laser": C_LASER}

# repo root = two levels up from this file (.../LaserProdShock/src/laserprod/plotting.py)
_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_PKG_DIR))
MEDIA = os.path.join(ROOT, "media")

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "axes.edgecolor": INK_MUTED,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK_2,
    "ytick.color": INK_2,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "legend.frameon": False,
    "lines.linewidth": 2.0,
    "font.size": 9,
})


def media_dir(run_id=None, testing=False):
    """Path under media/: ``media/testing`` (bring-up) or ``media/<run_id>``."""
    d = os.path.join(MEDIA, "testing") if testing else \
        (os.path.join(MEDIA, run_id) if run_id else MEDIA)
    os.makedirs(d, exist_ok=True)
    return d


def savefig(fig, name, run_id=None, testing=False, dpi=130):
    """Save ``fig`` under media/ and return (and print) its path."""
    out = os.path.join(media_dir(run_id=run_id, testing=testing), name)
    fig.savefig(out, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"  figure: {out}")
    return out


def style_axes(ax, grid_axis="both"):
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.7, alpha=0.9)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def label_line(ax, x, y, text, color, dx=0.0, dy=0.0, **kw):
    """Direct label at the end of a series — the required relief for a low-contrast
    slot, and better than a legend when the series is a single curve."""
    ax.annotate(text, xy=(x, y), xytext=(x + dx, y + dy), color=color,
                fontsize=8, fontweight="bold", va="center",
                ha=kw.pop("ha", "left"), **kw)


def stamp(fig, cfg, sc, extra=None):
    """Header line so every figure in media/ is self-describing."""
    rid = cfg.get("meta", {}).get("run_id", "?")
    bits = [f"{rid}", f"{sc.dims}D",
            f"target {sc.n_targ_over_ncr:.3g} n_cr",
            ("ambient VACUUM" if sc.n_amb_over_ncr is None
             else f"ambient {sc.n_amb_over_ncr:.3g} n_cr"),
            f"I0 {sc.intensity:.2g} W/m²",
            f"lam0 {sc.lam0*1e6:.3f} um"]
    if sc.MA is not None:
        bits.append(f"M_A {sc.MA:.2f} / M_ms {sc.Mms:.2f}")
    if extra:
        bits.append(extra)
    fig.text(0.005, 0.995, "  |  ".join(bits), ha="left", va="top",
             fontsize=8, color=INK_2)


# --------------------------------------------------------------------------- #
# reusable panels
# --------------------------------------------------------------------------- #
def gate_panel(ax, gates, title="Numerical gates (TEST_PLAN.md §6)"):
    """Render gate results as a status table: colour chip + glyph + word + detail.

    Not a chart — a table, because the data's job is *identity of state*, not
    magnitude. Status colour is accompanied by a glyph and a word so it never
    carries meaning alone.
    """
    ax.axis("off")
    ax.set_title(title, loc="left", fontweight="bold")
    n = len(gates)
    row_h = 1.0 / max(n, 1)
    for i, g in enumerate(gates):
        y = 1.0 - (i + 0.5) * row_h
        color, glyph = STATUS.get(g.status, STATUS["info"])
        ax.add_patch(Rectangle((0.0, y - 0.36 * row_h), 0.018, 0.72 * row_h,
                               transform=ax.transAxes, color=color, clip_on=False))
        ax.text(0.030, y, f"{g.key}", transform=ax.transAxes, va="center",
                fontsize=9, fontweight="bold", color=INK)
        ax.text(0.075, y, f"[{glyph}] {g.status.upper()}", transform=ax.transAxes,
                va="center", fontsize=8, fontweight="bold", color=color)
        ax.text(0.215, y, g.label, transform=ax.transAxes, va="center",
                fontsize=8, color=INK)
        val = "" if g.value is None else f"{g.value:.4g}"
        ax.text(0.560, y, val, transform=ax.transAxes, va="center",
                fontsize=8, color=INK, fontweight="bold")
        detail = " ".join(str(g.detail).split())
        ax.text(0.635, y, _clip(detail, 78), transform=ax.transAxes, va="center",
                fontsize=6.5, color=INK_MUTED)


def _clip(s, n):
    return s if len(s) <= n else s[:n - 1] + "…"


def density_panel(ax, z_de, n_target, n_ambient, sc, cfg, log=True):
    """Initial density profile along the propagation axis, in units of n_cr.

    Both populations are drawn from the deck's own density expressions, so the panel
    cannot disagree with what WarpX injects. The critical surface and the injection
    face are marked, because the two facts that matter for a laser run are *where the
    beam turns* and *which way it came in*.
    """
    ncr = sc.n_cr
    tot = [(a + b) / ncr for a, b in zip(n_target, n_ambient)]
    ax.plot(z_de, [v / ncr for v in n_target], color=C_TARGET, label="target")
    if any(n_ambient):
        ax.plot(z_de, [v / ncr for v in n_ambient], color=C_AMBIENT, label="ambient")
    ax.plot(z_de, tot, color=INK_MUTED, lw=1.0, ls="--", label="total (what the ray sees)")

    ax.axhline(1.0, color=INK, lw=1.2, ls=":")
    ax.text(0.005, 1.0, " n$_{cr}$", transform=ax.get_yaxis_transform(),
            va="bottom", ha="left", fontsize=8, color=INK)
    if sc.n_targ_over_ncr > 1.0:
        ax.text(0.99, 0.94, "target is OVERDENSE → interior critical surface\n"
                            "(turning point + specular reflection; gate G4 applies)",
                transform=ax.transAxes, ha="right", va="top", fontsize=7,
                color=INK_2)

    inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
    x_in = z_de[-1] if inject_hi else z_de[0]
    ax.axvline(x_in, color=C_LASER, lw=1.5, alpha=0.7)
    # Label placed at the bottom of the axis, not at n_cr, so it cannot collide with
    # the n_cr line or its label.
    ax.text(x_in, 0.02, "laser in  " if inject_hi else "  laser in",
            transform=ax.get_xaxis_transform(), color=C_LASER, fontsize=8,
            fontweight="bold", ha="right" if inject_hi else "left", va="bottom")

    if log:
        ax.set_yscale("log")
        floor = max(1e-6, 0.5 * min([v for v in tot if v > 0] or [1e-6]))
        ax.set_ylim(floor, max(5.0, 2.0 * max(tot)))
    ax.set_xlabel(f"z  [d$_e$ at {sc.length_scale} density]")
    ax.set_ylabel("n$_e$ / n$_{cr}$")
    ax.set_title("Initial density — from the deck's own density_function",
                 loc="left", fontweight="bold")
    ax.legend(loc="upper left" if inject_hi else "upper right")
    style_axes(ax)


def inject_hi_of(cfg) -> bool:
    """True when the laser enters at the high face of the propagation axis."""
    return str(cfg["laser"].get("inject_side", "lo")) == "hi"


def absorption_panel(ax_K, ax_tau, z_de, n_tot, sc, cfg, n_targ=None, n_amb=None):
    """Predicted IB absorption along the beam: K(z), then cumulative optical depth.

    TWO STACKED PANELS SHARING x, never a dual axis: K spans decades while tau is
    O(1), and overlaying them on twin scales is how a reader ends up misreading which
    curve saturates. The point of the pair is that tau is the integral of K.
    """
    Z_eff = float(cfg["laser"].get("Z_eff", 1.0))
    lnL = float(cfg["laser"].get("coulomb_log", 2.0))
    from .units import K_ib, theta_group

    # K is evaluated at the GROUP temperature the operator measures per cell, not at the
    # target's cold theta. With a hot ambient in the heated species list that is a 1-2
    # order-of-magnitude difference exactly where the tau = 1 surface sits, and using the
    # cold theta over-predicted the absorbed fraction by 3.6x (RESULTS 2026-07-28).
    K = []
    for i, n in enumerate(n_tot):
        if n <= 0:
            K.append(0.0)
            continue
        th = (theta_group(n_targ[i], sc.theta_e_targ, n_amb[i], sc.theta_e_amb)
              if (n_targ is not None and n_amb is not None) else sc.theta_e_targ)
        x = min(n / sc.n_cr, 0.999999)
        K.append(K_ib(x * sc.n_cr, th, sc.n_cr, Z_eff, lnL))

    # March from the injection face and STOP AT THE TURNING POINT. The ray reflects at
    # n_e = n_cr cos^2(theta0) and never enters the overdense interior, so integrating
    # tau through the flat top predicts near-total absorption where the operator measured
    # 0.28. The absorbed fraction is the DOUBLE pass to the turning point and back,
    # 1 - exp(-2 tau_turn) -- which is also the closed form the upstream CI tests use.
    import math as _m

    inject_hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
    theta0 = _m.radians(float(cfg["laser"].get("incidence_angle_deg", 0.0)))
    n_turn = sc.n_cr * _m.cos(theta0) ** 2
    order = list(range(len(z_de) - 1, -1, -1)) if inject_hi else list(range(len(z_de)))
    dz = abs(z_de[1] - z_de[0]) * sc.de_ref
    tau, acc, z_turn = [0.0] * len(z_de), 0.0, None
    for i in order:
        if n_tot[i] >= n_turn:
            z_turn = z_de[i]
            break
        acc += K[i] * dz
        tau[i] = acc
    tau_turn = acc
    f_abs_pred = 1.0 - _m.exp(-2.0 * min(tau_turn, 500.0))

    ax_K.plot(z_de, K, color=C_LASER)
    label_line(ax_K, z_de[len(z_de) // 2], max(K) if K else 1.0, "", C_LASER)
    ax_K.set_yscale("log")
    ax_K.set_ylabel("K  [1/m]")
    ax_K.set_title("Predicted inverse-bremsstrahlung absorption at the initial "
                   "profile, at the GROUP T$_e$ the operator measures", loc="left",
                   fontweight="bold")
    ax_K.text(0.99, 0.93, f"K ∝ Z$_{{eff}}$ lnΛ n$_e^2$ T$_e^{{-3/2}}$   "
                          f"(Z$_{{eff}}$={Z_eff:g}, lnΛ={lnL:g})",
              transform=ax_K.transAxes, ha="right", va="top", fontsize=7.5,
              color=C_LASER, fontweight="bold")
    style_axes(ax_K)

    # Log scale: tau spans ~6 decades between the transparent ambient and the target,
    # and the only feature that matters -- WHERE tau crosses 1, i.e. where the beam is
    # actually stopped -- is invisible on a linear axis dominated by the peak.
    ax_tau.plot(z_de, tau, color=C_LASER)
    ax_tau.set_yscale("log")
    pos = [v for v in tau if v > 0]
    if pos:
        ax_tau.set_ylim(max(min(pos), 1e-6 * max(pos)), 3.0 * max(pos))
    ax_tau.axhline(1.0, color=INK, lw=1.0, ls=":")
    ax_tau.text(0.005, 1.0, " τ = 1  (beam stopped)",
                transform=ax_tau.get_yaxis_transform(), va="bottom", fontsize=8,
                color=INK)
    # where tau first reaches 1, marching from the injection face
    z_stop = None
    for i in (range(len(z_de) - 1, -1, -1) if inject_hi_of(cfg) else range(len(z_de))):
        if tau[i] >= 1.0:
            z_stop = z_de[i]
            break
    if z_stop is not None:
        ax_tau.axvline(z_stop, color=INK, lw=1.0, ls="--", alpha=0.6)
        ax_tau.text(z_stop, 0.04, f"  τ=1 at z = {z_stop:.0f} d$_e$",
                    transform=ax_tau.get_xaxis_transform(), fontsize=7.5,
                    color=INK_2, va="bottom")
    if z_turn is not None:
        ax_tau.axvline(z_turn, color=C_TARGET, lw=1.4, alpha=0.8)
        ax_tau.text(z_turn, 0.72, "turning point  ", rotation=90, ha="right",
                    va="bottom", transform=ax_tau.get_xaxis_transform(),
                    fontsize=7.5, color=C_TARGET, fontweight="bold")
    ax_tau.text(0.99, 0.93,
                f"τ integrated to the TURNING POINT only (the ray never enters the "
                f"overdense interior)\ndouble-pass f$_{{abs}}$ = 1 − e$^{{-2τ}}$ → "
                f"{f_abs_pred:.3f}   (τ$_{{turn}}$ = {tau_turn:.3g})",
                transform=ax_tau.transAxes, ha="right", va="top", fontsize=7.5,
                color=INK_2)
    ax_tau.set_ylabel("optical depth τ")
    ax_tau.set_xlabel(f"z  [d$_e$ at {sc.length_scale} density]")
    style_axes(ax_tau)
    return K, tau, f_abs_pred
