#!/usr/bin/env python3
"""The ppc pair in one figure: which part of the "7 % leak" is noise and which is physics.

Four panels, each carrying one of the study's conclusions:

  (a) `w_eff/w0` -- 1.000 at t = 0 and rising identically at both ppc: the broadening is NOT
      the noise.
  (b) the far-wing leak -- falls as the noise POWER (x1/4 for x4 particles) while the
      scattering stays weak, so it IS the noise.
  (c) `f_ax` vs the whole-beam `f_abs` -- the 16 % ppc bias, and the 0.39-vs-0.63 gap that
      makes them different quantities.
  (d) the mechanism -- transverse `T_e` is strongly peaked while `n_e` is flat, so the rays
      are refracting off nothing and the coupling is being suppressed thermally.

    python studies/spot_leak_ppc/figures.py
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "scripts"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import io as lpio           # noqa: E402
from laserprod import plotting as lpp      # noqa: E402
from spot_report import SpotDump           # noqa: E402

STUDY = "spot_leak_ppc"
MEC2_EV = 510998.95


def load(dirname):
    cfg = lpconfig.load(dirname)
    sc = lpconfig.derive(cfg)
    ppc = int(cfg["numerics"]["ppc"]["target"])
    w0 = float(cfg["laser"]["beam"]["waist_de"]) * sc.de_ref
    P_inc = lpio.incident_power(sc, cfg)
    dumps = [SpotDump(p, sc, cfg) for p in lpio.profile_tables(cfg["_run_dir"])]
    return dict(cfg=cfg, sc=sc, ppc=ppc, w0=w0, P_inc=P_inc, dumps=dumps)


def main() -> int:
    import matplotlib.pyplot as plt

    runs = []
    for d in sorted(glob.glob(os.path.join(HERE, "scratch", "ppc_*")),
                    key=lambda p: int(os.path.basename(p).split("_")[1])):
        try:
            runs.append(load(d))
        except Exception as exc:
            print(f"  (skipping {os.path.basename(d)}: {exc})")
    if len(runs) < 2:
        print("need both ppc variants -- run studies/spot_leak_ppc/run_variants.sh first")
        return 1

    cols = [lpp.C_TARGET, lpp.C_LASER]
    fig, axes = plt.subplots(2, 2, figsize=(11.4, 8.2))
    (axA, axB), (axC, axD) = axes

    # ---- (a) the width: real, thermal, ppc-independent ------------------------------- #
    for r, c in zip(runs, cols):
        t = np.array([d.t for d in r["dumps"]]) * 1e12
        w = np.array([d.w_eff / r["w0"] for d in r["dumps"]])
        axA.plot(t, w, "o-", color=c, lw=1.6, ms=4.5, label=f"{r['ppc']} ppc")
    axA.axhline(1.0, color=lpp.INK, ls="--", lw=1.1)
    # No arrow: a leader line here reads as a third data series. The dashed y = 1 line and
    # the fact that both curves start exactly on it carry the point already.
    axA.text(0.035, 1.012, "$w_{\\rm eff}/w_0 = 1.0000$ at $t = 0$, at BOTH ppc\n"
             "-- the deposition is an exact image of the beam,\n"
             "so this measurement has no shot-noise floor",
             fontsize=7.4, color=lpp.INK, va="bottom", ha="left")
    axA.set_xlabel("t [ps]")
    axA.set_ylabel(r"$w_{\rm eff}/w_0$  of the absorbed power")
    axA.set_title("(a) the WIDTH does not scale with ppc: it is real", fontsize=9.5)
    axA.legend(fontsize=8, frameon=False)
    lpp.style_axes(axA)

    # ---- (b) the leak: noise, and a POWER not an amplitude --------------------------- #
    for r, c in zip(runs, cols):
        t = np.array([d.t for d in r["dumps"]]) * 1e12
        lk = np.array([d.leak_share(r["w0"]) for d in r["dumps"]])
        axB.plot(t, lk * 100, "o-", color=c, lw=1.6, ms=4.5, label=f"{r['ppc']} ppc")
    # what the 36 ppc curve would become if the leak were a weakly-scattered power
    f = runs[-1]["ppc"] / runs[0]["ppc"]
    t0 = np.array([d.t for d in runs[0]["dumps"]]) * 1e12
    lk0 = np.array([d.leak_share(runs[0]["w0"]) for d in runs[0]["dumps"]])
    axB.plot(t0, lk0 / f * 100, ls=":", color=lpp.INK, lw=1.5,
             label=fr"{runs[0]['ppc']} ppc $\div\,{f:g}$  (noise POWER, $\propto\delta n^2$)")
    axB.set_xlabel("t [ps]")
    axB.set_ylabel(r"absorbed power beyond $2.5\,w_0$  [%]")
    axB.set_title(r"(b) the LEAK falls as $\delta n^2$: it is shot noise", fontsize=9.5)
    axB.legend(fontsize=7.6, frameon=False)
    lpp.style_axes(axB)

    # ---- (c) f_ax is not f_abs, and 36 ppc reads it low ----------------------------- #
    for r, c in zip(runs, cols):
        t = np.array([d.t for d in r["dumps"]]) * 1e12
        fax = np.array([d.f_axis(r["w0"]) for d in r["dumps"]])
        fabs = np.array([d.total / r["P_inc"] for d in r["dumps"]])
        axC.plot(t, fax, "o-", color=c, lw=1.7, ms=4.5, label=f"{r['ppc']} ppc  $f_{{ax}}$")
        axC.plot(t, fabs, "s--", color=c, lw=1.2, ms=3.6, alpha=0.75,
                 label=f"{r['ppc']} ppc  $f_{{abs}}$ (whole beam)")
    a, b = runs[0], runs[-1]
    fa = a["dumps"][-1].f_axis(a["w0"]); fb = b["dumps"][-1].f_axis(b["w0"])
    tl = a["dumps"][-1].t * 1e12
    axC.annotate("", xy=(tl, fa), xytext=(tl, fb),
                 arrowprops=dict(arrowstyle="<->", color=lpp.INK, lw=1.2))
    axC.text(tl - 0.04, 0.5 * (fa + fb), f"  {100*(fb-fa)/fb:.0f} %", fontsize=8.5,
             color=lpp.INK, ha="right", va="center")
    axC.set_xlabel("t [ps]")
    axC.set_ylabel("absorbed fraction")
    axC.set_title("(c) on-axis coupling is not the whole-beam fraction", fontsize=9.5)
    axC.legend(fontsize=7.2, frameon=False, ncol=2)
    lpp.style_axes(axC)

    # ---- (d) the mechanism: T_e peaked, n_e flat ------------------------------------ #
    axD2 = axD.twinx()
    for r, c in zip(runs, cols):
        d = r["dumps"][-1]
        wgt = d.P / max(d.P.sum(), 1e-300)
        with np.errstate(invalid="ignore", divide="ignore"):
            Te = np.where(wgt.sum(axis=1) > 0,
                          (d.th * wgt).sum(axis=1) / np.maximum(wgt.sum(axis=1), 1e-300),
                          np.nan) * MEC2_EV
        ne = d.ne.max(axis=1) / r["sc"].n_cr
        xw = d.xs / r["w0"]
        axD.plot(xw, Te, "-", color=c, lw=1.7, label=f"{r['ppc']} ppc  $T_e$")
        axD2.plot(xw, ne, ":", color=c, lw=1.4, alpha=0.85, label=f"{r['ppc']} ppc  $n_e$")
    axD.set_xlabel(r"$x/w_0$")
    axD.set_ylabel(r"absorption-weighted $T_e$  [eV]")
    axD2.set_ylabel(r"peak $n_e$  [$n_{cr}$]")
    axD2.set_ylim(0, None)
    axD.set_xlim(-3, 3)
    axD.set_title(r"(d) $T_e$ is peaked, $n_e$ is flat $\Rightarrow$ thermal, not refractive",
                  fontsize=9.5)
    h1, l1 = axD.get_legend_handles_labels()
    h2, l2 = axD2.get_legend_handles_labels()
    axD.legend(h1 + h2, l1 + l2, fontsize=7.2, frameon=False, ncol=2, loc="lower center")
    lpp.style_axes(axD)

    lpp.stamp(fig, runs[0]["cfg"], runs[0]["sc"],
              extra=f"{STUDY}: {runs[0]['ppc']} vs {runs[-1]['ppc']} ppc, "
                    f"t_end = {runs[0]['dumps'][-1].t*1e12:.2f} ps")
    fig.tight_layout()
    lpp.savefig(fig, "spot_leak_ppc", STUDY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
