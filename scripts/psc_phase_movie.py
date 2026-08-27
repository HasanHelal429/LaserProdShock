#!/usr/bin/env python
"""Movie: WarpX ion phase space against PSC's bulk ion flow, on the aligned clock.

**What this is and is not.** PSC as configured writes NO particle data -- every
`OUT_part*` / `OUT_particle_parallel` call in `VLI.f` is commented out -- so there is no PSC
phase space to compare against. What PSC does write are moments. This therefore overlays

  * WarpX's TRUE ion phase space, (zeta, v_z/C_S0) per macroparticle from `diag_phase`, and
  * PSC's MEAN ion flow, <v_z> = NVzi/NNi, a ratio of two moments that needs no mass factor
    (unlike its pressure tensor, whose normalisation is unresolved -- RESULTS 2026-08-20),
  * FLASH's flow profile for reference.

It answers "does WarpX's ion population sit on the bulk flow the other codes predict", which
is a real question. It is NOT a distribution-function comparison; do not present it as one.

Clocks: each code by its own validated mapping to FLASH. PSC t_F = 0.1 ns + elapsed; WarpX
t_F = (tau_own + 2.696) * TAU_F.
"""
import argparse, glob, os, re, sys, warnings
import numpy as np
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, "/home/hhelal/psc-raytrace")
import xcode_compare as xc                                   # noqa: E402
from laserprod import plotting as lpp                        # noqa: E402
from read_pmt import assemble                                # noqa: E402

QE, MP = 1.602176634e-19, 1.67262192e-27


def psc_flow(datadir):
    """(t_F [ns], zeta, <v_z>/C_S0_FLASH) per PSC moment dump.

    The clock and the velocity unit are read from the run's own log: the 511 keV leg runs
    dt = 1.557 fs against the 60 keV leg's 4.544 fs, so a hardcoded DT_PSC would place its
    dumps 2.92x too late (RESULTS 2026-08-27).
    """
    N_ = xc.psc_norm(datadir)
    DT_PSC, K_VEL = N_["dt"], N_["K_vel"]
    out = []
    for step, zi, P in assemble(datadir, want=("NNi", "NVzi")):
        zi = zi[1:-1]
        ni = np.asarray(P["NNi"], float)[1:-1]
        vz = np.where(ni > 0, np.asarray(P["NVzi"], float)[1:-1] / np.maximum(ni, 1e-30), np.nan)
        out.append((0.1 + step * DT_PSC * 1e9, zi * 0.02, vz * K_VEL / xc.CS0_F, ni))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", nargs="?", default="runs/P4/P4_lez_kin_ic6_coldsolid")
    ap.add_argument("--psc", default="/home/hhelal/psc-raytrace/run_ourflash_511keV/data",
                    help="PSC leg. Defaults to the 511 keV run (real m_e c^2, collisions at\n"
                         "1.00x physical); the paper's 60 keV leg is run_ourflash/data, which\n"
                         "runs 2.92x slower and 72.5x over-collisional. The clock and velocity\n"
                         "unit are read from whichever run is given.")
    ap.add_argument("--zlim", type=float, nargs=2, default=(-5.0, 25.0))
    ap.add_argument("--vlim", type=float, nargs=2, default=(-1.0, 6.0))
    ap.add_argument("--fps", type=int, default=6)
    ap.add_argument("--frac", type=float, default=1.0, help="fraction of WarpX particles drawn")
    ap.add_argument("--out", default="movie_phase_vs_psc")
    a = ap.parse_args()
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import yt; yt.set_log_level(50)
    from laserprod import io as lpio

    sc = xc.warpx_scales(2698.0)
    run_id = os.path.basename(os.path.normpath(a.run_dir))
    P = psc_flow(a.psc)
    F = xc.flash_series(xc.FLASH_DIR, "lez1d")
    plots = lpio.plotfiles(a.run_dir, "diag_phase")
    fdir = os.path.join(lpp.media_dir(run_id), "_frames_phase_vs_psc")
    os.makedirs(fdir, exist_ok=True)
    n = 0
    for p in plots:
        ds = yt.load(p); ad = ds.all_data()
        tau = float(ds.current_time) / sc["tau"]
        tF = (tau + xc.TAU_HANDOFF) * xc.TAU_F * 1e9
        try:
            z = np.asarray(ad[("targ_ions", "particle_position_x")]) / sc["di0"]
            uz = np.asarray(ad[("targ_ions", "particle_momentum_z")])
        except Exception:
            continue
        m = sc["mass_ratio"] * 9.1093837015e-31
        u = uz / (m * xc.C)
        # only u_z is dumped, so gamma uses it alone -- fine, these are non-relativistic ions
        v = u / np.sqrt(1.0 + u * u) * xc.C / sc["cs0"]
        if a.frac < 1.0:
            k = np.random.default_rng(0).random(len(z)) < a.frac
            z, v = z[k], v[k]
        fig, ax = plt.subplots(figsize=(8.2, 4.6), constrained_layout=True)
        ax.plot(z, v, ".", ms=1.0, color="#c1441a", alpha=0.35,
                label=f"WarpX ions ({run_id})")
        j = int(np.argmin([abs(q[0] - tF) for q in P]))
        if abs(P[j][0] - tF) < 0.02:
            ok = P[j][3] >= 1e-3
            ax.plot(P[j][1][ok], P[j][2][ok], "-", color="#2a8a5f", lw=2.2,
                    label=f"PSC mean ion flow (t$_F$ {P[j][0]:.3f} ns)")
        f = xc.pick(F, tau + xc.TAU_HANDOFF)
        fm = f["ne"] >= 1e-3
        ax.plot(f["zeta"][fm], f["v"][fm], "-", color="#1f4e9c", lw=2.0, label="FLASH flow")
        lpp.style_axes(ax)
        ax.set_xlim(*a.zlim); ax.set_ylim(*a.vlim)
        ax.set_xlabel(r"$\zeta = z/d_{i0}$   (each code in its OWN $d_{i0}$)")
        ax.set_ylabel(r"$v_z / C_{S0}$")
        ax.set_title(f"Ion phase space vs bulk flow   |   $t_F$ = {tF:.3f} ns "
                     f"($\\tau_{{own}}$ {tau:.2f})\n"
                     "WarpX points are true macroparticles; PSC/FLASH lines are MEAN flow "
                     "(PSC writes no particle data)", fontsize=9.5)
        ax.legend(fontsize=8, loc="upper left", frameon=False)
        fig.savefig(os.path.join(fdir, f"frame_{n:04d}.png"), dpi=120)
        plt.close(fig); n += 1
    print(f"  {n} frames")
    lpp.encode(fdir, os.path.join(lpp.media_dir(run_id), a.out + ".mp4"), fps=a.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
