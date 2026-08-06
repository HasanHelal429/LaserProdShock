#!/usr/bin/env python3
"""Is a finite-spot run still a FINITE SPOT? The transverse-isolation check.

A localized-heating run only means anything while the transverse box still holds a region the
beam has not heated. With periodic transverse faces the run is really an infinite periodic
ARRAY of spots at pitch `L_t`, so once heat has crossed `L_t/2` the array merges and the
result is planar with extra steps -- and it will not announce itself, because every gate still
passes and energy is still conserved.

This measures the contrast directly: the transverse profile of the **net absorbed energy**
(driven particle-KE gain minus the laser-off control's boundary drain, per band), against the
profile of the beam that produced it.

    python scripts/spot_isolation.py <run> --control <run>_off

**The timescale is `v_th,e`, not `c_s`.** Electrons carry the energy, and `v_th,e/c_s` = √(m_i/Zm_e)
× √(T_e/T_i)-ish ~ 10 here, so a box sized from the ion sound speed is optimistic by an order of
magnitude. `P1_vac_2d_spot` was sized with `c_s` = 4.0 `d_e`/ps (80 `d_e` in 20 ps, comfortably
beyond its 9.96 ps) and lost its contrast in **~2 ps**, because `v_th,e` = 39 `d_e`/ps crosses
80 `d_e` in 2.0 ps.

Requirement for a valid run, in the form to size a box with:

    L_transverse/2  >~  v_th,e(T_e,corona) * t_end + (heated radius at t=0)

Verdict thresholds on `dark/lit` (mean net energy per band beyond 2.5 `w₀`, over that within
`w₀`): < 0.2 isolated; 0.2-0.5 marginal, quote it; > 0.5 the run is effectively planar.
"""

from __future__ import annotations

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import numpy as np                          # noqa: E402

from laserprod import config as lpconfig    # noqa: E402
from laserprod import io as lpio            # noqa: E402
from laserprod import plotting as lpp       # noqa: E402
from laserprod.units import C, ME           # noqa: E402

EV = 1.602176634e-19
ISOLATED, MARGINAL = 0.2, 0.5


def ke_bands(path, edges, species, mass):
    import yt
    ds = yt.load(path)
    ad = ds.all_data()
    out = np.zeros(len(edges) - 1)
    for name in species:
        if name not in {f[0] for f in ds.field_list}:
            continue
        x = np.asarray(ad[(name, "particle_position_x")])
        px, py, pz = (np.asarray(ad[(name, f"particle_momentum_{k}")]) for k in "xyz")
        w = np.asarray(ad[(name, "particle_weight")])
        m = mass[name]
        ke = w * (np.sqrt(1.0 + (px * px + py * py + pz * pz) / (m * C) ** 2) - 1.0) * m * C * C
        i = np.digitize(x, edges) - 1
        ok = (i >= 0) & (i < len(out))
        np.add.at(out, i[ok], ke[ok])
    return out, float(ds.current_time)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--control", required=True, help="the laser-off run (its drain is subtracted)")
    ap.add_argument("--bands", type=int, default=16)
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args()

    import yt
    yt.set_log_level("error")
    from laserprod.deck import _species_table

    cfg = lpconfig.load(args.run_dir)
    ccfg = lpconfig.load(args.control)
    sc = lpconfig.derive(cfg)
    rid = lpconfig.run_id(cfg)
    if int(cfg["geometry"]["dims"]) < 2:
        print(f"{rid} is 1D -- there is no transverse direction to lose.")
        return 1
    beam = (cfg["laser"].get("beam") or {})
    w0 = float(beam.get("waist_de", 0.0)) * sc.de_ref
    if not w0:
        print(f"{rid} has beam.profile = {beam.get('profile','uniform')} with no waist -- "
              f"transverse isolation is only meaningful for a LOCALIZED beam.")
        return 1

    tlo = float(cfg["geometry"]["transverse"]["lo_de"]) * sc.de_ref
    thi = float(cfg["geometry"]["transverse"]["hi_de"]) * sc.de_ref
    edges = np.linspace(tlo, thi, args.bands + 1)
    ctr = 0.5 * (edges[1:] + edges[:-1])
    species = list(_species_table(cfg))
    mass = {s: (ME if "electron" in s else sc.mi) for s in species}

    dp = {lpio._step_of(p): p for p in lpio.plotfiles(cfg["_run_dir"], "diag1")}
    cp = {lpio._step_of(p): p for p in lpio.plotfiles(ccfg["_run_dir"], "diag1")}
    steps = sorted(set(dp) & set(cp))
    if len(steps) < 2:
        print(f"need t=0 and at least one later matched dump; found {len(steps)}")
        return 1

    a0, _ = ke_bands(dp[steps[0]], edges, species, mass)
    b0, _ = ke_bands(cp[steps[0]], edges, species, mass)

    lit = np.abs(ctr) < 1.0 * w0
    dark = np.abs(ctr) > 2.5 * w0
    print(f"TRANSVERSE ISOLATION -- {rid}  (control {lpconfig.run_id(ccfg)})")
    print(f"  w0 = {w0/sc.de_ref:.1f} d_e; box +-{thi/sc.de_ref:.0f} d_e = "
          f"{thi/w0:.2f} w0; the beam itself has I(wall)/I(0) = "
          f"{math.exp(-(thi/w0)**2):.2e}")
    print(f"  {args.bands} bands; {lit.sum()} lit (|x|<w0), {dark.sum()} dark (|x|>2.5w0)\n")
    print(f"{'t [ps]':>8} {'min/max':>8} {'dark/lit':>9}  verdict")
    print("-" * 46)
    hist = []
    for k in steps[1:]:
        a, t = ke_bands(dp[k], edges, species, mass)
        b, _ = ke_bands(cp[k], edges, species, mass)
        net = (a - a0) - (b - b0)
        dl = float(net[dark].mean() / net[lit].mean())
        mm = float(net.min() / net.max())
        v = ("isolated" if dl < ISOLATED else
             "marginal -- quote it" if dl < MARGINAL else "EFFECTIVELY PLANAR")
        print(f"{t*1e12:8.3f} {mm:8.3f} {dl:9.3f}  {v}")
        hist.append((t, mm, dl, net))

    # when the run stopped being a spot
    t_ok = [t for t, _, dl, _ in hist if dl < MARGINAL]
    t_lost = [t for t, _, dl, _ in hist if dl >= MARGINAL]
    print()
    if t_lost:
        print(f"  CONTRAST LOST after t = {max(t_ok)*1e12:.2f} ps"
              if t_ok else "  CONTRAST NEVER ESTABLISHED at any dumped time")
        print(f"  -> results beyond that are planar-with-extra-steps, not finite-spot physics")
    else:
        print(f"  isolation held to t = {hist[-1][0]*1e12:.2f} ps (dark/lit "
              f"{hist[-1][2]:.3f})")

    # the box a valid run of this duration would need
    print()
    Te_cor = _corona_Te(cfg, sc)
    if Te_cor:
        v = math.sqrt(Te_cor * EV / ME) * 1e-12 / sc.de_ref   # m/s -> d_e per ps
        t_end = hist[-1][0] * 1e12
        need = v * t_end + w0 / sc.de_ref
        print(f"  SIZING: coronal T_e = {Te_cor:.0f} eV -> v_th,e = {v:.1f} d_e/ps, so a "
              f"{t_end:.1f} ps run needs")
        print(f"    L_t/2 >~ v_th,e*t_end + w0 = {need:.0f} d_e, against the "
              f"{thi/sc.de_ref:.0f} d_e used ({need/(thi/sc.de_ref):.1f}x too small).")
        print(f"    Or hold the box and stop at t <~ "
              f"{(thi/sc.de_ref - w0/sc.de_ref)/v:.1f} ps.")

    if not args.no_figure:
        _figure(hist, ctr, w0, sc, cfg, rid, thi)
    return 0


def _corona_Te(cfg, sc):
    """Absorption-weighted T_e at the last profile dump, in eV -- the corona the heat leaves from."""
    paths = lpio.profile_tables(cfg["_run_dir"])
    if not paths:
        return None
    a = np.loadtxt(paths[-1])
    cols = lpio.profile_column_names(paths[-1], a.shape[1])
    P, th = a[:, cols.index("P_abs")], a[:, cols.index("theta_e")]
    if P.sum() <= 0:
        return None
    return float((th * P).sum() / P.sum()) * 510998.95


def _figure(hist, ctr, w0, sc, cfg, rid, thi):
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 4.4))
    cmap = plt.get_cmap("viridis")
    for i, (t, mm, dl, net) in enumerate(hist):
        c = cmap(i / max(len(hist) - 1, 1))
        ax1.plot(ctr / w0, net / net.max(), "-o", color=c, lw=1.4, ms=3.2,
                 label=f"{t*1e12:.1f} ps")
    xx = np.linspace(ctr.min() / w0, ctr.max() / w0, 400)
    ax1.plot(xx, np.exp(-xx ** 2), ls="--", color=lpp.INK, lw=1.6,
             label="the BEAM, $e^{-(x/w_0)^2}$")
    ax1.set_xlabel(r"$x/w_0$")
    ax1.set_ylabel("net absorbed energy per band, / peak")
    ax1.set_title("(a) the deposited energy flattens onto the box", fontsize=9.5)
    ax1.legend(fontsize=6.8, frameon=False, ncol=2)
    lpp.style_axes(ax1)

    t = np.array([h[0] for h in hist]) * 1e12
    dl = np.array([h[2] for h in hist])
    ax2.plot(t, dl, "o-", color=lpp.C_LASER, lw=1.8, ms=5)
    ax2.axhspan(MARGINAL, 1.05, color=lpp.C_TARGET, alpha=0.13)
    ax2.axhspan(ISOLATED, MARGINAL, color=lpp.C_FOURTH, alpha=0.13)
    ax2.text(t.max(), MARGINAL + 0.02, "effectively planar ", fontsize=7.4, ha="right",
             va="bottom", color=lpp.INK)
    ax2.text(t.max(), ISOLATED + 0.02, "marginal ", fontsize=7.4, ha="right", va="bottom",
             color=lpp.INK)
    ax2.text(t.max(), 0.02, "isolated ", fontsize=7.4, ha="right", va="bottom", color=lpp.INK)
    Te = _corona_Te(cfg, sc)
    if Te:
        v = math.sqrt(Te * EV / ME) * 1e-12 / sc.de_ref
        cs = getattr(sc, "Cs_targ", None) or 0.0
        ax2.axvline((thi / sc.de_ref) / v, color=lpp.INK, ls=":", lw=1.4)
        ax2.annotate(rf"$L_t/2 \div v_{{th,e}}$ = {(thi/sc.de_ref)/v:.1f} ps",
                     xy=((thi / sc.de_ref) / v, 0.55), fontsize=7.4, rotation=90,
                     color=lpp.INK, ha="right", va="center")
        if cs:
            csd = cs * 1e-12 / sc.de_ref
            ax2.annotate(rf"($\div c_s$ would say {(thi/sc.de_ref)/csd:.0f} ps)",
                         xy=(0.5, 0.06), xycoords="axes fraction", fontsize=7.4,
                         color=lpp.INK)
    ax2.set_ylim(0, 1.05)
    ax2.set_xlabel("t [ps]")
    ax2.set_ylabel(r"dark/lit  (|x|>2.5$w_0$ over |x|<$w_0$)")
    ax2.set_title("(b) contrast decays on the ELECTRON transit time", fontsize=9.5)
    lpp.style_axes(ax2)

    lpp.stamp(fig, cfg, sc, extra="transverse isolation of a finite spot")
    fig.tight_layout()
    lpp.savefig(fig, "spot_isolation", rid)


if __name__ == "__main__":
    raise SystemExit(main())
