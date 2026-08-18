#!/usr/bin/env python3
"""Three-panel kinetic-vs-hybrid movie: n_e, T_e, and P_abs.

    /opt/anaconda3/envs/physics/bin/python scripts/compare_movie3.py \
        runs/P4/P4_lez_kin_bg runs/P4/P4_lez_hyb_bg3

Writes ``media/<idA>_vs_<idB>/movie_compare3.mp4``.

**The three panels come from three different places, because that is where the quantities
actually live, and the cadences differ.** Stating this on the figure matters more than
hiding it:

* ``n_e``  -- ``diag_fields`` ``rho``/e for both runs. Dense cadence.
* ``T_e``  -- the HYBRID has a real ``Te`` field (added 2026-08-13); the KINETIC run has no
  such field, because its electron temperature is a *particle moment*. It is therefore
  computed here from the electron macroparticles,
  ``k_B T_e = m_e(<|u|^2> - |<u>|^2)/3``, weighted, binned per cell. That is the same
  definition ``temperature_mode = local`` uses inside the operator. Only ``diag1`` carries
  the particle record, so the movie runs at the ``diag1`` cadence.
* ``P_abs`` -- only in the operator's sparse ``laserdep_profile`` text dumps (a handful per
  run). The panel shows the NEAREST dump and **annotates its time**, dimming the curve when
  it is stale. A held-over curve presented as current is exactly how a reader concludes the
  deposition is doing something at a time it was never measured.
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

import numpy as np                          # noqa: E402

from laserprod import config as lpconfig    # noqa: E402
from laserprod import io as lpio            # noqa: E402
from laserprod import plotting as lpp       # noqa: E402
from laserprod import units as lpunits      # noqa: E402

# The Manheimer steady state T_e,SS = 5.94 mu^(1/3) Z^(-1/3) lambda^(4/3) I^(2/3) is 823 eV
# for REAL aluminium. These runs use the paper's REDUCED mass ratio (m_Al/m_e = 2698 rather
# than 49542), and T_e,SS ~ mu^(1/3), so the value a WarpX leg should be judged against is
# 823 / 18.363^(1/3) = 312 eV. Annotating 823 eV on a reduced-mass run overstates the target
# by 2.6x -- which is how the hybrid's 423 eV was read as "0.5x of expectation" when it is
# 1.36x. See scripts/xcode_compare.py and RESULTS.md 2026-08-18.
TSS_REDUCED = 823.0 / 18.363 ** (1.0 / 3.0)      # 312 eV

NBIN = 500          # z bins for the particle-moment temperature; coarser than the grid so
                    # each bin holds enough macroparticles for a stable second moment


def profile_dumps(cfg, sc):
    out = []
    for p in sorted(glob.glob(os.path.join(cfg["_run_dir"], "diags",
                                           "laserdep_profile_*.txt"))):
        with open(p) as fh:
            hdr = [next(fh) for _ in range(3)]
        arr = np.loadtxt(p)
        nm = lpio.profile_column_names(p, arr.shape[1])
        out.append(dict(t=float(hdr[1].split()[4]),
                        z=arr[:, nm.index("z")] / sc.de_ref,
                        P=arr[:, nm.index("P_abs")]))
    return out


def kinetic_Te(ds, sc, zedges):
    """k_B T_e [eV] per z-bin from the electron macroparticles, weighted."""
    ad = ds.all_data()
    Z, U2, U, W = [], [], [], []
    for s in ("targ_electrons", "amb_electrons"):
        try:
            z = np.asarray(ad[(s, "particle_position_x")]) / sc.de_ref
            w = np.asarray(ad[(s, "particle_weight")])
            u = np.stack([np.asarray(ad[(s, f"particle_momentum_{c}")])
                          for c in "xyz"], axis=1) / (lpunits.ME * lpunits.C)
        except Exception:
            continue
        Z.append(z); W.append(w); U.append(u); U2.append((u * u).sum(axis=1))
    if not Z:
        return np.full(len(zedges) - 1, np.nan)
    z = np.concatenate(Z); w = np.concatenate(W)
    u = np.concatenate(U, axis=0); u2 = np.concatenate(U2)
    sw, _ = np.histogram(z, bins=zedges, weights=w)
    s2, _ = np.histogram(z, bins=zedges, weights=w * u2)
    mean_u2 = np.divide(s2, sw, out=np.full_like(s2, np.nan), where=sw > 0)
    drift2 = np.zeros_like(mean_u2)
    for k in range(3):
        sk, _ = np.histogram(z, bins=zedges, weights=w * u[:, k])
        mk = np.divide(sk, sw, out=np.zeros_like(sk), where=sw > 0)
        drift2 += mk * mk
    theta = (mean_u2 - drift2) / 3.0            # kT/(m_e c^2), drift subtracted
    return theta * 511e3


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_a"); ap.add_argument("run_b")
    ap.add_argument("--fps", type=int, default=6)
    ap.add_argument("--labels", nargs=2, default=None)
    ap.add_argument("--zmax", type=float, default=1200.0)
    args = ap.parse_args()

    import matplotlib.pyplot as plt
    import yt
    from plot_fields import load_series, electron_density
    from laserprod.deck import _species_table

    runs = []
    for rd in (args.run_a, args.run_b):
        cfg = lpconfig.load(rd); sc = lpconfig.derive(cfg)
        sp = list(_species_table(cfg))
        tf, zf, rows = load_series(cfg["_run_dir"], "diag_fields", sc, sp)
        runs.append(dict(cfg=cfg, sc=sc, rid=lpconfig.run_id(cfg), sp=sp,
                         tf=tf, zf=zf / sc.de_ref,
                         ne=electron_density(rows, sp, sc) / sc.n_cr,
                         Te_fld=(rows["Te"] if "Te" in rows else None),
                         p1=lpio.plotfiles(cfg["_run_dir"], "diag1"),
                         prof=profile_dumps(cfg, sc)))
    a, b = runs
    la, lb = args.labels or (a["rid"], b["rid"])
    if abs(a["sc"].de_ref / b["sc"].de_ref - 1.0) > 1e-9:
        raise SystemExit("REFUSING: different d_e,ref -- a shared z axis would be a rescale")

    # Frame on diag1 (the only series with the particle record the kinetic T_e needs)
    times = []
    for p in a["p1"]:
        try:
            times.append((p, float(yt.load(p).current_time)))
        except Exception:
            pass
    print(f"  {len(times)} frames at the diag1 cadence "
          f"({times[0][1]*1e12:.2f}..{times[-1][1]*1e12:.2f} ps)")

    zedges = np.linspace(-50.0, args.zmax, NBIN + 1)
    zmid = 0.5 * (zedges[1:] + zedges[:-1])

    d = lpp.movie_dir(f"{a['rid']}_vs_{b['rid']}", "compare3")
    for i, (pa, tt) in enumerate(times):
        ja = int(np.argmin(np.abs(a["tf"] - tt)))
        jb = int(np.argmin(np.abs(b["tf"] - tt)))
        Te_kin = kinetic_Te(yt.load(pa), a["sc"], zedges)
        Te_hyb = b["Te_fld"][jb] if b["Te_fld"] is not None else None

        fig, ax = plt.subplots(3, 1, figsize=(9.2, 9.4), sharex=True)

        ax[0].semilogy(a["zf"], np.maximum(a["ne"][ja], 1e-8), color=lpp.C_TARGET,
                       lw=1.8, label=la)
        ax[0].semilogy(b["zf"], np.maximum(b["ne"][jb], 1e-8), color=lpp.C_AMBIENT,
                       lw=1.5, ls="--", label=lb)
        ax[0].axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
        ax[0].text(0.004, 1.0, " n$_{cr}$", transform=ax[0].get_yaxis_transform(),
                   va="bottom", fontsize=8, color=lpp.INK)
        ax[0].set_ylim(1e-5, 20); ax[0].set_ylabel("n$_e$ / n$_{cr}$")
        ax[0].legend(loc="upper right", fontsize=8.5)
        ax[0].set_title(f"t = {tt*1e12:6.2f} ps", loc="left", fontweight="bold")

        ax[1].plot(zmid, Te_kin, color=lpp.C_TARGET, lw=1.8)
        if Te_hyb is not None:
            ax[1].plot(b["zf"], Te_hyb, color=lpp.C_AMBIENT, lw=1.5, ls="--")
        ax[1].axhline(TSS_REDUCED, color=lpp.C_LASER, ls="-.", lw=1.1)
        ax[1].text(0.004, TSS_REDUCED, f" T$_{{e,SS}}$ = {TSS_REDUCED:.0f} eV (reduced $m_i$)",
                   transform=ax[1].get_yaxis_transform(), va="bottom", fontsize=7.5,
                   color=lpp.C_LASER)
        ax[1].set_ylim(0, 2000)
        ax[1].set_ylabel("T$_e$  [eV]\nkinetic: particle moment · hybrid: fluid field")

        # P_abs: nearest sparse dump, with its staleness stated rather than hidden
        for r, col, ls in ((a, lpp.C_TARGET, "-"), (b, lpp.C_AMBIENT, "--")):
            if not r["prof"]:
                continue
            k = int(np.argmin([abs(q["t"] - tt) for q in r["prof"]]))
            q = r["prof"][k]
            stale = abs(q["t"] - tt) * 1e12
            ax[2].semilogy(q["z"], np.maximum(q["P"], 1e12), color=col, ls=ls,
                           lw=1.6 if stale < 1.0 else 1.0,
                           alpha=1.0 if stale < 1.0 else 0.35)
        ax[2].set_ylim(1e14, 1e24)
        ax[2].set_ylabel("P$_{abs}$  [W/m$^3$]")
        ax[2].set_xlabel("z  [d$_e$]")
        near = min(min(abs(q["t"] - tt) for q in r["prof"]) for r in (a, b) if r["prof"])
        ax[2].text(0.995, 0.05,
                   ("P$_{abs}$ dump at this time"
                    if near * 1e12 < 1.0 else
                    f"nearest P$_{{abs}}$ dump is {near*1e12:.1f} ps away — FADED, not current"),
                   transform=ax[2].transAxes, ha="right", va="bottom", fontsize=7.5,
                   color=lpp.INK, alpha=0.85)

        for k in range(3):
            ax[k].set_xlim(-50, args.zmax); ax[k].grid(alpha=0.15)
        fig.tight_layout()
        fig.savefig(os.path.join(d, f"frame_{i:04d}.png"), dpi=115)
        plt.close(fig)

    out = os.path.join(lpp.media_dir(run_id=f"{a['rid']}_vs_{b['rid']}"),
                       "movie_compare3.mp4")
    lpp.encode(d, out, fps=args.fps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
