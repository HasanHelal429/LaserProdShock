#!/usr/bin/env python3
"""D-1: is the far-field trough/shelf REAL PLASMA or a handful of macroparticles?

    /opt/anaconda3/envs/physics/bin/python studies/plume_structure/d1_trough.py

THE QUESTION. Every WarpX leg shows a density MINIMUM beyond the plume front, with
material again beyond it (RESULTS.md 2026-08-18: the slope of `flashic` goes POSITIVE at
zeta ~ 25). FLASH shows nothing of the kind -- one constant log-slope from zeta 10 to 100.
Two candidate causes, with opposite consequences:

  REAL      a hot-electron-driven fast ion precursor. Collisionless expansion accelerates
            a small ion population well ahead of the quasi-neutral plume through the
            ambipolar field. A 3T fluid code has no mechanism for it, so its ABSENCE in
            FLASH is expected and the feature is a RESULT, not a defect.
  ARTIFACT  shot noise. The corona is loaded at fixed ppc onto an exponential profile, so
            macroparticle weights span SEVEN DECADES (1.7e10 .. 1.3e17). A few of the
            lightest fly out ballistically and paint a shelf at 1e-5 n_cr that no real
            plasma is in.

THE DISCRIMINATOR is not the density -- both stories produce the same n_e -- it is the
MACROPARTICLE COUNT per bin and the CHARGE SEPARATION:

  * count < ~10 per bin  -> the bin's density is a sample of size 10; it is noise.
  * a real ambipolar precursor is CHARGE SEPARATED at its front (electrons run ahead,
    ions follow, that is what makes the accelerating field), so n_e/(Z n_i) departs from
    1 systematically at the leading edge and returns to 1 in the quasi-neutral plume.
  * noise is charge separated too, but RANDOMLY -- the sign flips bin to bin.

So the test is: count, then ask whether the departure from quasineutrality is COHERENT
(one sign over many bins) or incoherent.
"""
from __future__ import annotations
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import numpy as np
import xcode_compare as X

QE = X.QE

LEGS = (("kin_bg",     "runs/P4/P4_lez_kin_bg",         2698.0),
        ("flashic",    "runs/P4/P4_lez_kin_flashic",    2698.0),
        ("flashic_ct", "runs/P4/P4_lez_kin_flashic_ct",  100.0))


def binned(run_dir, sc, tau, nbin=400):
    """Per-bin macroparticle COUNT and weight-summed density, electrons and ions apart."""
    import yt
    from laserprod import io as lpio
    files = lpio.plotfiles(run_dir, prefix="diag1")
    if not files:
        return None
    # nearest dump to the requested tau
    best, bestd = None, 1e30
    for path in files:
        try:
            ds = yt.load(path)
        except Exception:
            continue
        t = float(ds.current_time) / sc["tau"]
        if abs(t - tau) < bestd:
            best, bestd = (ds, t), abs(t - tau)
    if best is None:
        return None
    ds, tau_act = best
    ds.force_periodicity()
    ad = ds.all_data()
    edges = np.linspace(-50.0 * X.DE_CR / sc["di0"], 2450.0 * X.DE_CR / sc["di0"], nbin + 1)
    mid = 0.5 * (edges[1:] + edges[:-1])
    dz = (edges[1] - edges[0]) * sc["di0"]
    out = {"zeta": mid, "tau": tau_act}
    for kind, names in (("e", X.SP_KIN["electron"]), ("i", X.SP_KIN["ion"])):
        Z, W = [], []
        for s in names:
            try:
                Z.append(np.asarray(ad[(s, "particle_position_x")]) / sc["di0"])
                W.append(np.asarray(ad[(s, "particle_weight")]))
            except Exception:
                continue
        if not Z:
            continue
        z = np.concatenate(Z); w = np.concatenate(W)
        cnt, _ = np.histogram(z, bins=edges)                 # MACROPARTICLES, unweighted
        sw, _ = np.histogram(z, bins=edges, weights=w)       # physical weight
        out[f"n_{kind}"] = sw / dz / X.N_CR
        out[f"c_{kind}"] = cnt
    return out


def main():
    print(__doc__)
    for lab, path, mr in LEGS:
        sc = X.warpx_scales(mr)
        b = binned(path, sc, 27.0)
        if b is None:
            print(f"\n{lab}: no plotfiles"); continue
        ne, ni = b.get("n_e"), b.get("n_i")
        ce, ci = b.get("c_e"), b.get("c_i")
        if ne is None or ni is None:
            print(f"\n{lab}: missing a species"); continue
        nZ = ni * X.Z_AL                       # what quasineutrality predicts for n_e
        print("\n" + "=" * 100)
        print(f"{lab}   (tau = {b['tau']:.1f},  m_i/m_e = {mr:.0f})")
        print(f"{'zeta':>7} {'n_e/n_cr':>11} {'Z n_i/n_cr':>11} {'n_e/(Z n_i)':>12} "
              f"{'N_e':>8} {'N_i':>8}   verdict")
        # walk outward from the plume into the shelf
        for z0 in (10, 20, 30, 40, 50, 60, 70, 80, 90, 100):
            j = int(np.argmin(np.abs(b["zeta"] - z0)))
            r = ne[j] / nZ[j] if nZ[j] > 0 else np.nan
            v = ("NOISE (<10 macroparticles)" if min(ce[j], ci[j]) < 10 else
                 "resolved" if min(ce[j], ci[j]) >= 100 else "marginal (10-100)")
            print(f"{b['zeta'][j]:7.1f} {ne[j]:11.3e} {nZ[j]:11.3e} {r:12.3f} "
                  f"{ce[j]:8d} {ci[j]:8d}   {v}")
        # coherence of the charge separation in the shelf
        m = (b["zeta"] > 40) & (b["zeta"] < 110) & (ce >= 10) & (ci >= 10) & (nZ > 0)
        if m.sum() > 4:
            r = ne[m] / nZ[m]
            frac = float(np.mean(r > 1.0))
            print(f"  shelf (zeta 40-110, resolved bins only): {m.sum()} bins, "
                  f"n_e/(Z n_i) mean {np.mean(r):.3f} +/- {np.std(r):.3f}, "
                  f"{frac*100:.0f}% of bins electron-rich")
            print("  -> COHERENT (a real ambipolar front) if that fraction is near 0 or 100;"
                  " incoherent (noise) if near 50.")
        else:
            print(f"  shelf: only {m.sum()} bins have >=10 macroparticles of BOTH species"
                  f" -> the shelf is NOT RESOLVED; it is macroparticle noise.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
