#!/usr/bin/env python3
"""Animated mass-convention comparison: the P6 legs on FLASH-normalised axes.

    python3 scripts/p6_movie.py                      # every completed P6 leg
    python3 scripts/p6_movie.py --legs heavy full    # a subset
    LP_FLASH_DIR=/path/to/Ablation_prod_08-17 python3 scripts/p6_movie.py   # + FLASH

Writes ``media/P6/movie_massconv.mp4``.

WHY NOT compare_movie.py. That one overlays two WarpX runs on a SHARED axis, which is only
valid when they share a unit system. The P6 legs deliberately do not: `light` runs
d_i0 = 1.6934 um and tau = 2.028 ps against `heavy`/`full` at 7.2563 um and 37.232 ps. A
shared micron axis would be a 4.29x rescaling error -- exactly the mistake the normalised
axes exist to prevent. Every leg here is drawn on its OWN zeta = z/d_i0 and sampled at its
OWN tau, which is the only map on which the three describe the same experiment.

WHY THE LEGS ARE NOT INTERCHANGEABLE. `heavy` and `full` come out identical in every
derived scale (d_i0 7.2563 um, tau 37.232 ps, mu 1.000, T_ss 823 eV) because they are the
same physical system reached two ways -- a real ion via a heavy electron, and a real ion
via a real electron. `light` has mu = 0.0545 and is the leg predicted to fail. If heavy
tracks full and light does not, the convention works.

FLASH IS OPTIONAL AND ITS ABSENCE IS STATED ON THE FIGURE. The delivery is not on
Perlmutter; xcode_compare's own comment records that it needs only the 51 plotfiles plus
lez1d_LaserEnergyProfile.dat, 7.6 MB. Set $LP_FLASH_DIR and the FLASH curve appears in
every panel. Without it the movie still answers the convention question -- heavy vs full
vs light -- and says plainly in the title that the FLASH reference is missing, rather than
quietly drawing two curves and letting a reader assume the third was checked.
"""
from __future__ import annotations
import argparse, os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter
from xcode_compare import load_leg, leg_state, flash_series, pick, FLASH_DIR, TAU_HANDOFF, scalars, BAND
from laserprod import plotting as lpp

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LEGS = [("full",  "P6_mr_full",  lpp.C_TARGET),
        ("heavy", "P6_mr_heavy", lpp.C_LASER),
        ("light_sim", "P6_mr_light_sim", lpp.C_AMBIENT),
        ("heavy_dz025", "P6_mr_heavy_dz025", lpp.C_LASER),
        ("light", "P6_mr_light", "0.6")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs", nargs="*", default=["full", "heavy", "light_sim"])
    ap.add_argument("--fps", type=int, default=5)
    ap.add_argument("--psc", metavar="DATADIR", default=os.environ.get("LP_PSC_DIR"),
                    help="PSC (Fortran psc-raytrace) data dir; its run.log sets the units")
    ap.add_argument("--psc-code", default=os.environ.get("LP_PSC_CODE", "/home/hhelal/psc-raytrace"),
                    help="directory holding read_pmt.py")
    ap.add_argument("--out", default=os.path.join(ROOT, "media/P6/movie_massconv.mp4"))
    a = ap.parse_args()

    legs = []
    for name, rid, col in LEGS:
        if name not in a.legs:
            continue
        path = os.path.join(ROOT, "runs/P6", rid)
        if not os.path.isdir(path):
            print(f"  skip {name}: no {path}"); continue
        try:
            # Bin every leg over the SAME normalised span, wide enough for FLASH's plume
            # (~zeta 100). The historical default is a fixed 415 um, which truncates the
            # mu = 1 legs at zeta 57.
            leg = load_leg(name, path, col, zeta_range=(-5.0, 115.0))
        except Exception as e:
            print(f"  skip {name}: {e}"); continue
        if not leg["S"]:
            print(f"  skip {name}: no particle dumps yet"); continue
        sc = leg["sc"]
        print(f"  {name:<6} d_i0={sc['di0']*1e6:.4f}um tau={sc['tau']*1e12:.3f}ps "
              f"mu={sc['mu']:.4f} dumps={len(leg['S'])} tau_own_max={leg['S'][-1]['tau']:.2f}")
        legs.append(leg)
    if not legs:
        print("no legs with data"); return 1

    # FLASH counts as present only if plotfiles were actually READ. An existing but empty
    # directory -- which is exactly what a failed copy leaves behind -- must not flip the
    # title to "FLASH overlaid" over a figure with no FLASH curve in it.
    F = None
    if os.path.isdir(FLASH_DIR):
        try:
            F = flash_series(FLASH_DIR, "lez1d") or None
        except Exception as e:
            print(f"  FLASH unreadable ({e})")
        print(f"  FLASH: {len(F) if F else 0} plotfiles in {FLASH_DIR}")
    if F is None:
        print(f"  FLASH: NOT AVAILABLE ({FLASH_DIR} absent) -- set $LP_FLASH_DIR")

    # PSC, on the same normalised axes, exactly as paper_fig3.py reads it: units from the run's
    # OWN log (psc_norm), zeta = zi*0.02, T_e from the electron stress trace, v in FLASH's C_S0.
    # Its clock is FLASH's (t starts at the 0.1 ns handoff), so it is matched to FLASH's tau.
    P = None
    if a.psc:
        from xcode_compare import psc_norm, TAU_F, CS0_F
        sys.path.insert(0, a.psc_code)
        from read_pmt import assemble
        N_ = psc_norm(a.psc)
        P = []
        for st, zi, Q in assemble(a.psc, want=("NNe", "Sxxe", "Syye", "Szze", "NVze")):
            zi = np.asarray(zi, float)[1:-1]; Q = {k: np.asarray(v, float)[1:-1] for k, v in Q.items()}
            ne_ = Q["NNe"]; d = np.maximum(ne_, 1e-30)
            te_ = np.where(ne_ > 0, (Q["Sxxe"] + Q["Syye"] + Q["Szze"]) / (3 * d) * N_["K_temperature"], np.nan)
            v_ = np.where(ne_ > 0, Q["NVze"] / d, np.nan) * N_["K_vel"] / CS0_F
            tF = 0.1e-9 + st * N_["dt"]
            P.append(dict(tau=tF / TAU_F, zeta=zi * 0.02, ne=ne_, Te=te_, v=v_))
        print(f"  PSC: {len(P)} dumps, FLASH-clock tau {P[0]['tau']:.2f} -> {P[-1]['tau']:.2f}, "
              f"m_e c^2 = {N_['mec2_keV']:.1f} keV")

    # Frame grid: every leg's own tau, capped at the SHORTEST leg so no frame silently
    # repeats a finished leg's last dump (the failure `stale` exists to catch).
    tau_end = min(l["S"][-1]["tau"] for l in legs)
    taus = [s["tau"] for s in legs[0]["S"] if s["tau"] <= tau_end + 1e-9]
    print(f"  frames: {len(taus)}  tau_own 0 -> {tau_end:.2f}")

    # Fixed limits across all frames, computed first (per make_movies.py's rule).
    zlo, zhi, nlo, nhi, tlo, thi, vlo, vhi = 1e9, -1e9, 1e9, -1e9, 1e9, -1e9, 1e9, -1e9
    for t in taus:
        for leg in legs:
            st = leg_state(leg, t)
            if st is None: continue
            zlo, zhi = min(zlo, st["zeta"].min()), max(zhi, st["zeta"].max())
            g = st["ne"][st["ne"] > 0]
            if g.size: nlo, nhi = min(nlo, g.min()), max(nhi, g.max())
            if st["Te"] is not None and np.isfinite(st["Te"]).any():
                tlo, thi = min(tlo, np.nanmin(st["Te"])), max(thi, np.nanmax(st["Te"]))
            if st["v"] is not None and np.isfinite(st["v"]).any():
                vlo, vhi = min(vlo, np.nanmin(st["v"])), max(vhi, np.nanmax(st["v"]))
    nlo = max(nlo, 1e-5)

    fig, ax = plt.subplots(3, 1, figsize=(9.5, 10), sharex=True)
    for x in ax: lpp.style_axes(x)
    lpp.use_ffmpeg()
    writer = FFMpegWriter(fps=a.fps, bitrate=2400)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    with writer.saving(fig, a.out, dpi=120):
        for t in taus:
            for x in ax: x.clear(); lpp.style_axes(x)
            for leg in legs:
                st = leg_state(leg, t)
                if st is None: continue
                lab = f"{leg['label']} (mu={leg['sc']['mu']:.3g})"
                if leg["label"] == "light":
                    # P6_mr_light's IC was NOT similarity-scaled (lengths and velocities
                    # held at the mu = 1 values), so its offset from FLASH is partly a
                    # setup artifact -- see runs/P6/P6_mr_light/README.md, Retracted.
                    lab += " - IC NOT similarity-scaled"
                if st["stale"]: lab += " [stale]"
                al = 0.35 if st["stale"] else 1.0
                ax[0].semilogy(st["zeta"], np.maximum(st["ne"], nlo), color=leg["colour"],
                               lw=1.6, alpha=al, label=lab)
                if st["Te"] is not None:
                    ax[1].semilogy(st["zeta"], np.maximum(st["Te"], 10.0),
                                   color=leg["colour"], lw=1.6, alpha=al)
                if st["v"] is not None:
                    ax[2].plot(st["zeta"], st["v"], color=leg["colour"], lw=1.6, alpha=al)
            if F is not None:
                f = pick(F, t + TAU_HANDOFF)
                if f is not None:
                    ax[0].semilogy(f["zeta"], np.maximum(f["ne"], nlo), color="k",
                                   lw=2.0, ls="--", label=f"FLASH (tau={f['tau']:.2f})")
                    ax[1].semilogy(f["zeta"], np.maximum(f["Te"], 10.0),
                                   color="k", lw=2.0, ls="--")
                    ax[2].plot(f["zeta"], f["v"], color="k", lw=2.0, ls="--")
            if P is not None:
                q = min(P, key=lambda r: abs(r["tau"] - (t + TAU_HANDOFF)))
                if abs(q["tau"] - (t + TAU_HANDOFF)) < 0.5:
                    ax[0].semilogy(q["zeta"], np.maximum(q["ne"], nlo), color=lpp.C_FOURTH,
                                   lw=1.6, label="PSC (m_p/m_e=100, heavy e-)")
                    ax[1].semilogy(q["zeta"], np.maximum(q["Te"], 10.0), color=lpp.C_FOURTH, lw=1.6)
                    ax[2].plot(q["zeta"], q["v"], color=lpp.C_FOURTH, lw=1.6)
            ax[0].axhline(1.0, color="0.55", lw=0.8, ls=":")
            ax[0].set_ylabel(r"$n_e/n_{cr}$"); ax[0].set_ylim(nlo, nhi * 1.5)
            # LOG: the n_e < 1e-2 tail reaches tens of keV and on a linear axis it flattens
            # the ~1 keV plume -- where the comparison actually lives -- into the baseline.
            ax[1].set_ylabel(r"$T_e$  [eV]");  ax[1].set_ylim(10.0, thi * 1.5)
            ax[2].set_ylabel(r"$v_z/C_{S0}$"); ax[2].set_ylim(vlo, vhi)
            ax[2].set_xlabel(r"$\zeta = z/d_{i0}$  (each leg on its OWN $d_{i0}$)")
            ax[0].set_xlim(zlo, zhi)
            ax[0].legend(loc="upper right", fontsize=8, framealpha=0.9)
            sub = "FLASH overlaid" if F is not None else \
                  "FLASH REFERENCE NOT AVAILABLE — set $LP_FLASH_DIR (7.6 MB delivery)"
            fig.suptitle(f"P6 mass conventions — $\\tau_{{own}}$ = {t:.2f}   "
                         f"(FLASH clock $\\tau$ = {t + TAU_HANDOFF:.2f})\n{sub}",
                         fontsize=11)
            fig.tight_layout(rect=(0, 0, 1, 0.94))
            writer.grab_frame()
    plt.close(fig)
    print(f"wrote {a.out}")
    write_table(legs, F, taus, os.path.splitext(a.out)[0] + "_scalars.txt")
    return 0


def write_table(legs, F, taus, out):
    """The acceptance quantities at matched tau: geometry first, temperature last.

    zeta_cr / zeta_front / L_n are what P6 is judged on (the broken real-mass leg's T_e was
    off 5% while its scale length was off 4x). Te_mean_plume is density-weighted over the
    plume band only, so the hot tenuous tail below 1e-2 n_cr does not enter it.
    """
    want = [1.0, 5.0, 10.0, 15.0, taus[-1]]
    keys = ["zeta_cr", "zeta_front", "L_n", "Te_mean_plume", "v_band_max"]
    lines = [f"P6 acceptance scalars at matched tau_own (FLASH at tau_own + {TAU_HANDOFF})",
             f"plume band {BAND[0]:g}..{BAND[1]:g} n_cr; '*' = leg's nearest dump is > 0.25 tau away",
             f"{'tau_own':>7} {'leg':<7}" + "".join(f"{k:>15}" for k in keys)]
    for t in want:
        rows = []
        if F is not None:
            f = pick(F, t + TAU_HANDOFF)
            if f is not None:
                rows.append(("FLASH", scalars(f["zeta"], f["ne"], f["Te"], f["v"]), False))
        for leg in legs:
            st = leg_state(leg, t)
            if st is not None:
                rows.append((leg["label"], scalars(st["zeta"], st["ne"], st["Te"], st["v"]),
                             st["stale"]))
        for name, d, stale in rows:
            lines.append(f"{t:7.2f} {name + ('*' if stale else ''):<7}"
                         + "".join(f"{d.get(k, np.nan):15.4g}" for k in keys))
        lines.append("")
    open(out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
