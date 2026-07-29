#!/usr/bin/env python3
"""Finite-spot diagnostics: what a LOCALIZED beam does that a planar one cannot.

Every other analysis script in this repo reduces the transverse direction away -- which is
correct for a planar run, where transverse structure is either noise or a bug (RESULTS
2026-07-29), but throws away the entire subject of a finite-spot run. This script keeps
`x` and answers the three questions `TEST_PLAN.md` 7.2 asks of a spot:

1. **Does the deposition follow the beam?** The column-integrated absorbed power must equal
   the incident `I(x)` profile wherever the target is optically thick, so the step-0 dump is
   an absolute test of the operator against `I0*exp(-(x/w0)^2)` -- no fitting.
2. **Does the drive spread, and how fast?** The second-moment width `w_eff(t)` of the
   absorbed-power profile, the transverse `n_e` profile at the front face, and the
   transverse `T_e` profile all measure lateral rarefaction, which is what H5 is about.
3. **Do the transverse boundaries stay quiet?** The two edge columns of an unilluminated
   wall must carry `exp(-(x_wall/w0)^2)` of the peak and nothing more. This is the standing
   regression test for the transverse-wrap fix (`warpx-cda` c817b63): the bug it fixed only
   switched on once structure developed (edge share 3.2 % at t = 0 -> 98.8 % at 26.9 ps), so
   a step-0 check cannot catch a regression and the whole dump series has to be tracked.

    python scripts/spot_report.py runs/P1/P1_vac_2d_spot
    python scripts/spot_report.py runs/P1/P1_vac_2d_spot --baseline runs/P1/P1_vac_1d_thick

Writes ``media/<phase>/<ID>/spot_transverse.png`` (the four transverse panels) and, with
``--baseline``, ``media/<phase>/<ID>/spot_vs_baseline.png`` (`f_abs(t)` and cumulative
coupling against a 1D run of the same target -- the degradation curve).

Note on units: `P_abs` in the dumps is a volumetric W/m^3, so a column integral carries
`dx*dz` and comes out in W per metre of the invariant direction, the same convention as
``laserprod.io.incident_power`` in 2D. Comparing a 2D run to a 1D one is therefore only
meaningful through the DIMENSIONLESS `f_abs = P_abs/P_inc`, never through the raw powers.
"""

from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import io as lpio           # noqa: E402
from laserprod import plotting as lpp      # noqa: E402


def _trapz(y, x):
    """numpy.trapezoid on new numpy, numpy.trapz on old -- one place, not five."""
    fn = getattr(np, "trapezoid", None) or np.trapz
    return float(fn(y, x))


def read_profile_array(path: str) -> dict:
    """``laserdep_profile_<step>.txt`` -> ``{column: ndarray}``, via numpy.

    ``laserprod.io.read_profile_table`` is the reference reader, but these dumps are one
    row per cell -- 704 000 rows for a 320x2200 spot run -- and its pure-Python lists cost
    seconds and hundreds of MB each. The column layout is taken from
    ``lpio.PROFILE_TAIL`` so the two readers cannot disagree about which column is
    ``P_abs`` and which is ``theta_e``.
    """
    arr = np.loadtxt(path)
    ncol = arr.shape[1]
    ncoord = max(ncol - len(lpio.PROFILE_TAIL), 0)
    names = {1: ["z"], 2: ["x", "z"], 3: ["x", "y", "z"]}[ncoord]
    cols = names + lpio.PROFILE_TAIL[:ncol - ncoord]
    return {c: arr[:, i] for i, c in enumerate(cols)}


def time_of(path: str) -> float:
    """Physical time of a dump, from its own header (not from step*dt)."""
    with open(path) as fh:
        for line in fh:
            if line.startswith("#") and " time " in line:
                return float(line.split(" time ")[1].split()[0])
            if not line.startswith("#"):
                break
    return float("nan")


class SpotDump:
    """The transverse reduction of one profile dump."""

    def __init__(self, path, sc, cfg):
        self.path = path
        self.t = time_of(path)
        d = read_profile_array(path)
        self.xs = np.unique(d["x"])
        self.zs = np.unique(d["z"])
        nx, nz = len(self.xs), len(self.zs)
        self.dx = float(self.xs[1] - self.xs[0])
        self.dz = float(self.zs[1] - self.zs[0])
        # SCATTER by cell index rather than reshape. The dump is written box by box (the
        # operator gathers to one rank and walks its MFIter), so the row order is the
        # AMReX box decomposition and is NOT globally row-major -- a reshape silently
        # transposes patches of the domain. Rounding the coordinate to an index is
        # order-independent, and the count check catches a duplicated or missing cell.
        ix = np.rint((d["x"] - self.xs[0]) / self.dx).astype(np.int64)
        iz = np.rint((d["z"] - self.zs[0]) / self.dz).astype(np.int64)
        if ix.min() < 0 or ix.max() >= nx or iz.min() < 0 or iz.max() >= nz:
            raise SystemExit(f"{path}: cell coordinates do not map onto a uniform grid")
        flat = ix * nz + iz
        if len(np.unique(flat)) != nx * nz:
            raise SystemExit(f"{path}: {len(np.unique(flat))} distinct cells for a "
                             f"{nx}x{nz} grid -- the dump is incomplete")
        def grid(key):
            g = np.empty(nx * nz, dtype=float)
            g[flat] = d[key]
            return g.reshape(nx, nz)
        self.P = grid("P_abs")                      # W/m^3
        self.ne = grid("n_e")                       # m^-3
        self.th = grid("theta_e")                   # kT_e/(m_e c^2)
        self.Pcol = self.P.sum(axis=1) * self.dx * self.dz   # W/m per column
        self.total = float(self.Pcol.sum())
        self.sc, self.cfg = sc, cfg

    # --- transverse measures ------------------------------------------------ #
    @property
    def w_eff(self):
        """Second-moment width, normalised so a Gaussian exp(-(x/w)^2) returns w."""
        if self.total <= 0:
            return float("nan")
        xc = self.centroid
        var = float((self.Pcol * (self.xs - xc) ** 2).sum() / self.total)
        return math.sqrt(2.0 * var)

    @property
    def centroid(self):
        return float((self.Pcol * self.xs).sum() / self.total) if self.total > 0 else 0.0

    def edge_share(self):
        """Fraction of all absorption in the two outermost columns."""
        if self.total <= 0:
            return float("nan")
        return float(self.Pcol[0] + self.Pcol[-1]) / self.total

    def leak_share(self, w0, k=2.5):
        """Share of absorption OUTSIDE |x| > k*w0 -- power that left the spot.

        This, not the edge-column share, is the finite-spot number. Rays scatter off the
        transverse density ripple near the critical surface, where `n_ref = sqrt(1 -
        n_e/n_cr)` -> 0 amplifies a gradient by 1/n_ref, and with periodic transverse faces
        the scattered light wraps and fills the box. The result is a broad flat PEDESTAL,
        which an edge-column statistic reports as if it were a boundary pile-up: at 1 ps in
        P1_vac_2d_spot the edge share read 4e-4 (10^5 above its t=0 value, alarming) while
        the actual wall columns sat BELOW their inward neighbours. Two measures, two
        distinct failure modes -- keep both.
        """
        if self.total <= 0 or not w0:
            return float("nan")
        m = np.abs(self.xs) > k * w0
        return float(self.Pcol[m].sum()) / self.total

    def wall_ratio(self, n_edge=2, lo=10, hi=30):
        """(mean of the outermost n_edge columns) / (mean of columns lo..hi inward).

        The pile-up detector, insensitive to a broad pedestal: the clamp bug of
        warpx-cda pre-c817b63 drove this to 20-25, an unilluminated wall on a smooth
        profile keeps it at or below 1.
        """
        if self.total <= 0:
            return float("nan")
        edge = 0.5 * (self.Pcol[:n_edge].mean() + self.Pcol[-n_edge:].mean())
        inner = 0.5 * (self.Pcol[lo:hi].mean() + self.Pcol[-hi:-lo].mean())
        return float(edge / inner) if inner > 0 else float("nan")

    def core_share(self, w):
        """Fraction of all absorption inside |x| < w of the beam centre."""
        if self.total <= 0 or not w:
            return float("nan")
        m = np.abs(self.xs) < w
        return float(self.Pcol[m].sum()) / self.total

    def f_axis(self, w0, frac=0.25):
        """LOCAL absorbed fraction inside |x| < frac*w0 -- the H5 measure.

        The run-integrated `f_abs` of a Gaussian is NOT comparable to a flat-top's, even at
        equal peak intensity, because the wings sit at lower intensity, heat less, and so
        keep `K ~ T_e^{-3/2}` high: that raises the total `f_abs` while lateral rarefaction
        is lowering it on axis. Dividing the absorption in the central columns by the
        incident power in those same columns separates the two, and the result is directly
        comparable to a 1D run's `f_abs`.
        """
        m = np.abs(self.xs) < frac * w0
        if not m.any():
            return float("nan")
        inc = float((np.exp(-((self.xs[m] / w0) ** 2))).sum()) * self.dx * self.sc.intensity
        return float(self.Pcol[m].sum()) / inc if inc > 0 else float("nan")

    def roughness(self, k=9):
        """Column-to-column scatter about a smooth trend, and its lag-1 autocorrelation.

        This is the cheap test of WHETHER a `rays_per_cell` convergence study is needed.
        Sub-cell ray sampling matters when ray wander becomes COHERENT -- rays bending
        systematically into density valleys, as refractive self-channelling would do. A
        random exchange of power between neighbouring columns instead shows up as scatter
        that is anti-correlated at lag 1 (one column loses what the next one gains) and it
        averages out of any multi-column measure. Positive autocorrelation growing with
        time is the signature that would demand the ladder; that is a measurement, not an
        assumption, and it costs nothing.
        """
        y = self.Pcol
        if y.sum() <= 0 or len(y) < 4 * k:
            return float("nan"), float("nan")
        # QUADRATIC (Savitzky-Golay) trend, not a boxcar. A boxcar mean of a curved
        # profile sits below its centre value wherever the profile is convex, and the
        # Gaussian's own curvature then leaks into the residual as a POSITIVE lag-1
        # correlation -- which is exactly the signature this measure exists to detect. A
        # local quadratic removes curvature to O(h^4), so what is left is the scatter.
        h = k // 2
        o = np.arange(-h, h + 1, dtype=float)
        A = np.vstack([np.ones_like(o), o, o * o]).T
        ker = np.linalg.pinv(A)[0]              # value of the fit at the window centre
        trend = np.convolve(y, ker[::-1], mode="valid")
        core = y[h: h + len(trend)]
        keep = trend > 1e-4 * max(trend.max(), 1e-300)      # only where the beam is
        r = (core[keep] / trend[keep]) - 1.0
        if len(r) < 4:
            return float("nan"), float("nan")
        return float(r.std()), float(np.corrcoef(r[:-1], r[1:])[0, 1])

    def front_face(self, z_lo, z_hi):
        """Transverse n_e and T_e[eV] averaged over an axial band (the front face)."""
        m = (self.zs >= z_lo) & (self.zs <= z_hi)
        ne = self.ne[:, m].mean(axis=1)
        te = self.th[:, m].mean(axis=1) * 510998.95          # theta -> eV
        return ne, te

    def axial(self, w):
        """On-axis (|x| < w) axial P_abs profile and its 50/99 % depth positions."""
        m = np.abs(self.xs) < w
        p = self.P[m, :].mean(axis=0)
        if p.sum() <= 0:
            return p, float("nan"), float("nan")
        c = np.cumsum(p) / p.sum()
        return (p, float(self.zs[np.searchsorted(c, 0.5)]),
                float(self.zs[np.searchsorted(c, 0.99)]))


def transverse_figure(dumps, sc, cfg, rid, w0, P_inc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    de = sc.de_ref
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 7.6))
    cmap = plt.get_cmap("viridis")
    n = max(len(dumps) - 1, 1)
    cols = [cmap(0.08 + 0.85 * i / n) for i in range(len(dumps))]

    d0 = dumps[0]
    I0 = float(cfg["laser"]["intensity"])
    launch = I0 * np.exp(-((d0.xs / w0) ** 2)) * d0.dx      # W/m per column at f_abs = 1

    # (a) column-integrated absorbed power, each normalised to the launch peak
    ax = axes[0][0]
    for d, c in zip(dumps, cols):
        ax.plot(d.xs / de, d.Pcol / launch.max(), color=c, lw=1.1,
                label=f"{d.t*1e12:.2f} ps")
    ax.plot(d0.xs / de, launch / launch.max(), color=lpp.INK, ls="--", lw=1.4,
            label="incident I(x)")
    ax.set_yscale("log")
    ax.set_ylim(1e-8, 3.0)
    ax.set_xlabel("x  [d$_e$]")
    ax.set_ylabel("column P$_{abs}$ / peak incident")
    ax.set_title("(a) Absorption follows the beam -- and the walls stay dark",
                 loc="left", fontweight="bold", fontsize=9.5)
    ax.legend(fontsize=6.5, ncol=2, loc="lower center")
    lpp.style_axes(ax)

    # (b) spreading and the boundary regression tracker
    ax = axes[0][1]
    t = np.array([d.t for d in dumps]) * 1e12
    ax.plot(t, [d.w_eff / w0 for d in dumps], "o-", color=lpp.C_LASER, lw=1.6)
    ax.axhline(1.0, color=lpp.INK_MUTED, ls=":", lw=1.0)
    ax.set_xlabel("t  [ps]")
    ax.set_ylabel("w$_{eff}$ / w$_0$", color=lpp.C_LASER)
    ax2 = ax.twinx()
    ax2.semilogy(t, [max(d.edge_share(), 1e-12) for d in dumps], "s--",
                 color=lpp.C_TARGET, lw=1.4)
    wall = 2.0 * math.exp(-((float(d0.xs[0]) / w0) ** 2)) * d0.dx * I0 / max(d0.total, 1e-300)
    ax2.axhline(wall, color=lpp.C_TARGET, ls=":", lw=1.0)
    ax2.set_ylabel("edge-column share of P$_{abs}$", color=lpp.C_TARGET)
    ax.set_title("(b) Lateral spreading (green), transverse-wrap regression (orange)",
                 loc="left", fontweight="bold", fontsize=9.5)
    lpp.style_axes(ax)

    # (c) transverse n_e at the front face -- the lateral rarefaction itself
    ax = axes[1][0]
    for d, c in zip(dumps, cols):
        ne, _ = d.front_face(-10 * de, 10 * de)
        ax.plot(d.xs / de, ne / sc.n_cr, color=c, lw=1.1)
    ax.axvspan(-w0 / de, w0 / de, color=lpp.C_LASER, alpha=0.08)
    ax.set_yscale("log")
    ax.set_xlabel("x  [d$_e$]")
    ax.set_ylabel("n$_e$ / n$_{cr}$   (mean over |z| < 10 d$_e$)")
    ax.set_title("(c) Transverse density at the front face (shaded: |x| < w$_0$)",
                 loc="left", fontweight="bold", fontsize=9.5)
    lpp.style_axes(ax)

    # (d) transverse T_e -- lateral heat transport out of the spot
    ax = axes[1][1]
    for d, c in zip(dumps, cols):
        _, te = d.front_face(-10 * de, 10 * de)
        ax.plot(d.xs / de, te, color=c, lw=1.1)
    ax.axvspan(-w0 / de, w0 / de, color=lpp.C_LASER, alpha=0.08)
    ax.set_yscale("log")
    ax.set_xlabel("x  [d$_e$]")
    ax.set_ylabel("T$_e$  [eV]   (the value the operator used)")
    ax.set_title("(d) Transverse electron temperature", loc="left",
                 fontweight="bold", fontsize=9.5)
    lpp.style_axes(ax)

    lpp.stamp(fig, cfg, sc,
              extra=f"w0 = {w0/de:g} d_e,  P_inc = {P_inc:.3g} W/m")
    fig.tight_layout()
    lpp.savefig(fig, "spot_transverse", rid)


def baseline_figure(cfg, sc, rid, hist, P_inc, bcfg, bhist, bP_inc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def smooth(a, k):
        a = np.asarray(a, dtype=float)
        if k < 2 or len(a) < 4 * k:
            return a
        c = np.cumsum(np.insert(a, 0, 0.0))
        return (c[k:] - c[:-k]) / k

    fig, axes = plt.subplots(2, 1, figsize=(11.0, 6.4), sharex=True)
    t = np.array(hist.t) * 1e12
    f = np.array(hist.f_abs(P_inc))
    tb = np.array(bhist.t) * 1e12
    fb = np.array(bhist.f_abs(bP_inc))

    ax = axes[0]
    ax.plot(t, f, color=lpp.C_LASER, lw=0.4, alpha=0.22)
    ax.plot(smooth(t, max(1, len(t) // 200)), smooth(f, max(1, len(f) // 200)),
            color=lpp.C_LASER, lw=1.8, label=f"{lpconfig.run_id(cfg)} (spot)")
    ax.plot(smooth(tb, max(1, len(tb) // 200)), smooth(fb, max(1, len(fb) // 200)),
            color=lpp.C_AMBIENT, lw=1.8, label=f"{lpconfig.run_id(bcfg)} (planar)")
    ax.set_ylabel("f$_{abs}$ = P$_{abs}$/P$_{inc}$")
    ax.set_title("Absorbed FRACTION is the only quantity comparable across "
                 "dimensionality", loc="left", fontweight="bold", fontsize=9.5)
    ax.legend(fontsize=8)
    lpp.style_axes(ax)

    ax = axes[1]
    for tt, hh, pp, cc, lab in ((t, hist, P_inc, lpp.C_LASER, "spot"),
                                (tb, bhist, bP_inc, lpp.C_AMBIENT, "planar")):
        e = np.array(hh.Eabs)
        tsec = np.array(hh.t)
        with np.errstate(divide="ignore", invalid="ignore"):
            ax.plot(tt, e / (pp * tsec), color=cc, lw=1.6, label=lab)
    ax.set_xlabel("t  [ps]")
    ax.set_ylabel("E$_{abs}$ / (P$_{inc}$ t)")
    ax.set_title("Time-integrated coupling -- the number to quote, never the median "
                 "f$_{abs}$", loc="left", fontweight="bold", fontsize=9.5)
    ax.legend(fontsize=8)
    lpp.style_axes(ax)

    lpp.stamp(fig, cfg, sc)
    fig.tight_layout()
    lpp.savefig(fig, "spot_vs_baseline", rid)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--baseline", default=None,
                    help="a run of the same target to compare f_abs(t) against -- normally "
                         "the matched 1D run (P1_vac_1d_thick for the Phase-1 spot)")
    ap.add_argument("--max-dumps", type=int, default=12,
                    help="cap the number of profile dumps read (each is ~75 MB)")
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args()

    cfg = lpconfig.load(args.run_dir)
    rid = lpconfig.run_id(cfg)
    sc = lpconfig.derive(cfg)
    rd = cfg["_run_dir"]
    if int(cfg["geometry"]["dims"]) < 2:
        print(f"{rid} is {cfg['geometry']['dims']}D -- a spot report needs a transverse "
              "dimension. Use scripts/laser_report.py.")
        return 1

    beam = (cfg["laser"].get("beam") or {})
    prof = str(beam.get("profile", "uniform"))
    w0 = float(beam.get("waist_de", 0.0)) * sc.de_ref
    if not w0:
        print(f"{rid} has beam.profile = {prof} with no waist -- this script measures a "
              "LOCALIZED spot. For a planar run the transverse profile is a bug check, "
              "not a physics measurement.")
        return 1
    P_inc = lpio.incident_power(sc, cfg)

    paths = lpio.profile_tables(rd)
    if not paths:
        print(f"no laserdep_profile dumps in {rd}/diags -- is "
              "laser.profile_intervals set in config.yaml?")
        return 1
    if len(paths) > args.max_dumps:
        keep = np.linspace(0, len(paths) - 1, args.max_dumps).round().astype(int)
        paths = [paths[i] for i in sorted(set(keep.tolist()))]

    xw = float(cfg["geometry"]["transverse"]["hi_de"]) * sc.de_ref
    print(f"SPOT REPORT -- {rid}   beam = {prof}, w0 = {w0/sc.de_ref:g} d_e = "
          f"{w0*1e6:.2f} um,  P_inc = {P_inc:.4g} W/m")
    print(f"  total power I0*w0*sqrt(pi) = {sc.intensity*w0*math.sqrt(math.pi):.4g} W/m"
          f"  (= a uniform beam {w0*math.sqrt(math.pi)/sc.de_ref:.1f} d_e wide)")
    print(f"  wall at {xw/sc.de_ref:g} d_e = {xw/w0:.2f} w0 -> incident there is "
          f"{math.exp(-((xw/w0)**2)):.2e} of peak")

    hdr = (f"{'t [ps]':>8} {'f_abs':>8} {'f_ax':>7} {'w_eff/w0':>9} {'x_cen':>7} "
           f"{'leak>2.5w0':>11} {'wall/in':>8} {'core<w0':>8} {'z50':>7} {'z99':>7} "
           f"{'ne_ax':>8} {'Te_ax[eV]':>10} {'rough':>7} {'ac1':>6}")
    print("\n" + hdr)
    print("-" * len(hdr))
    dumps = []
    for p in paths:
        d = SpotDump(p, sc, cfg)
        dumps.append(d)
        _, z50, z99 = d.axial(0.25 * w0)
        ne, te = d.front_face(-10 * sc.de_ref, 10 * sc.de_ref)
        ax_m = np.abs(d.xs) < 0.25 * w0
        rough, ac1 = d.roughness()
        print(f"{d.t*1e12:8.3f} {d.total/P_inc:8.4f} {d.f_axis(w0):7.4f} "
              f"{d.w_eff/w0:9.4f} "
              f"{d.centroid/sc.de_ref:7.2f} {d.leak_share(w0):11.4f} "
              f"{d.wall_ratio():8.2f} "
              f"{d.core_share(w0):8.4f} {z50/sc.de_ref:7.1f} {z99/sc.de_ref:7.1f} "
              f"{ne[ax_m].mean()/sc.n_cr:8.4f} {te[ax_m].mean():10.1f} "
              f"{rough*100:6.2f}% {ac1:+6.2f}")

    print("  rough = column-to-column scatter about a 9-column trend; ac1 = its lag-1\n"
          "  autocorrelation. ac1 < 0 means power is exchanged between NEIGHBOURS (random\n"
          "  ray wander, averages out of f_ax). ac1 turning positive and growing is what\n"
          "  would demand a rays_per_cell ladder -- coherent refractive channelling.")

    d0, dl = dumps[0], dumps[-1]
    wall_expect = (2.0 * math.exp(-((float(d0.xs[0]) / w0) ** 2)) * d0.dx
                   * sc.intensity / max(d0.total, 1e-300))
    print("\nTRANSVERSE BOUNDARY (standing regression test for warpx-cda c817b63)")
    print(f"  wall/interior column ratio   t=0: {d0.wall_ratio():.2f}   "
          f"t={dl.t*1e12:.2f} ps: {dl.wall_ratio():.2f}     (clamp bug drove this to 20-25)")
    print(f"  raw edge-column share        t=0: {d0.edge_share():.3e}   "
          f"t={dl.t*1e12:.2f} ps: {dl.edge_share():.3e}  (unilluminated wall: "
          f"{wall_expect:.3e})")
    print("  The RATIO is the regression test, not the share. A growing share with a ratio "
          "at or\n  below 1 is light scattered out of the spot filling the box (see the "
          "leak column), which\n  is a physics/ppc question; a ratio of 20+ is the index "
          "clamp coming back.")

    launch = sc.intensity * np.exp(-((d0.xs / w0) ** 2)) * d0.dx
    sel = np.exp(-((d0.xs / w0) ** 2)) > 1e-3
    r = d0.Pcol[sel] / launch[sel]
    print(f"\nSTEP-0 PROFILE vs analytic I0*exp(-(x/w0)^2)  ({int(sel.sum())} illuminated columns)")
    print(f"  mean ratio {r.mean():.5f}   column-to-column spread {r.std()*100:.3f} %"
          f"   min {r.min():.4f} max {r.max():.4f}")
    if len(r) > 3:
        lag1 = float(np.corrcoef(r[:-1] - 1, r[1:] - 1)[0, 1])
        print(f"  lag-1 autocorrelation of the residual {lag1:+.3f} -- negative means power "
              "moved between NEIGHBOURS (ray wander), not into a boundary")
    print(f"  total absorbed {d0.total:.6e} W/m vs incident {P_inc:.6e} "
          f"=> f_abs(0) = {d0.total/P_inc:.6f}")

    if not args.no_figure:
        transverse_figure(dumps, sc, cfg, rid, w0, P_inc)

    if args.baseline:
        bcfg = lpconfig.load(args.baseline)
        bsc = lpconfig.derive(bcfg)
        hist = lpio.laserdep_history(rd)
        bhist = lpio.laserdep_history(bcfg["_run_dir"])
        if not len(hist) or not len(bhist):
            print("\n(no LASERDEP history in one of the two runs -- skipping the "
                  "baseline comparison)")
            return 0
        bP_inc = lpio.incident_power(bsc, bcfg)
        t = np.array(hist.t)
        f = np.array(hist.f_abs(P_inc))
        tb = np.array(bhist.t)
        fb = np.array(bhist.f_abs(bP_inc))
        print(f"\nVS BASELINE {lpconfig.run_id(bcfg)}  (dimensionless f_abs only -- "
              "raw powers are not comparable across dimensionality)")
        print("  NOTE the whole-beam f_abs mixes two opposite finite-spot effects: lateral "
              "rarefaction\n  lowers it, while the cooler wings (lower I, so less heating, "
              "so higher K ~ T^-3/2) raise it.\n  The f_ax column of the table above is the "
              "one to compare against the baseline's f_abs.")
        print(f"{'window [ps]':>14} {'spot mean':>10} {'baseline':>10} {'ratio':>8}")
        t_end = min(t[-1], tb[-1])
        edges = np.linspace(0.0, t_end, 6)
        for a, b in zip(edges[:-1], edges[1:]):
            m, mb = (t >= a) & (t < b), (tb >= a) & (tb < b)
            if m.sum() and mb.sum():
                print(f"{a*1e12:6.2f}-{b*1e12:6.2f} {f[m].mean():10.4f} "
                      f"{fb[mb].mean():10.4f} {f[m].mean()/fb[mb].mean():8.4f}")
        # On-axis degradation at the dump times: the H5 curve. Both sides are noisy --
        # the baseline is a SINGLE ray per application (10.4 % 1-sigma on f_abs(0) across
        # RNG seeds, RESULTS 2026-07-28) and the spot's f_ax averages ~10 columns of a
        # profile whose column-to-column scatter reaches 20 %. So average the baseline
        # over +-HALF_WIN rather than reading one application, and print how many
        # applications went into each mean so the reader can size the error bar.
        HALF_WIN = 0.10e-12
        print(f"\n{'t [ps]':>8} {'f_ax (spot)':>12} {'f_abs (1D)':>11} {'ratio':>8} "
              f"{'n_1D':>6}")
        for d in dumps:
            wnd = (tb >= d.t - HALF_WIN) & (tb <= d.t + HALF_WIN)
            if wnd.sum() and d.t <= tb[-1]:
                b = fb[wnd].mean()
                print(f"{d.t*1e12:8.3f} {d.f_axis(w0):12.4f} {b:11.4f} "
                      f"{d.f_axis(w0)/b:8.4f} {int(wnd.sum()):6d}")
        mi, mbi = t <= t_end, tb <= t_end
        e, eb = _trapz(f[mi], t[mi]), _trapz(fb[mbi], tb[mbi])
        print(f"  time-integrated coupling to t = {t_end*1e12:.2f} ps: "
              f"spot {e/t_end:.4f}, baseline {eb/t_end:.4f}, ratio {e/eb:.4f}")
        if not args.no_figure:
            baseline_figure(cfg, sc, rid, hist, P_inc, bcfg, bhist, bP_inc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
