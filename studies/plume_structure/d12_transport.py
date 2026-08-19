#!/usr/bin/env python3
"""D-1/D-2 follow-up: is FLASH's conduction model even VALID in the plume we compare?

    /opt/anaconda3/envs/physics/bin/python studies/plume_structure/d12_transport.py

WHY THIS COMES BEFORE ANY MORE RUNS. The whole remaining FLASH<->WarpX discrepancy is the
SHAPE of T_e: FLASH is a flat isothermal plateau, WarpX rises outward. FLASH's plateau is
produced by FLUX-LIMITED Spitzer-Harm conduction, and a flux limiter is a phenomenological
fudge introduced precisely because Spitzer-Harm fails when the electron mean free path is
not small against the temperature scale length. So before treating FLASH's shape as the
target to hit, ask two questions of the delivered data:

  (1) HOW HARD IS THE LIMITER BINDING?  `fllm` is in the delivered checkpoints and nobody
      has looked at it. fllm = 1 means the classical (Spitzer) flux is used unmodified;
      fllm < 1 means the code is throwing flux away. Where fllm << 1, FLASH's temperature
      profile is set by the limiter's free parameter, NOT by conduction physics.

  (2) IS THE PLASMA IN THE LOCAL REGIME AT ALL?  The Spitzer-Harm closure requires the
      electron mean free path to be small against the temperature scale length; the
      standard threshold is

          Kn = lambda_ei / L_T  <~ 0.06        (Gray & Kilkenny; the usual flux-limit onset)

      Above it, heat transport is NON-LOCAL: the flux at a point is set by electrons that
      came from somewhere else, which is exactly what a kinetic code computes correctly and
      a fluid closure cannot. If Kn > 0.06 across the plume in BOTH codes, then the codes
      SHOULD disagree on the T_e shape, WarpX is the more trustworthy of the two there, and
      the right deliverable is that statement rather than a forced match.

NRL formulary, T_e in eV, n_e in cm^-3:
    v_Te   = 4.19e7 sqrt(T_e)                       cm/s
    nu_ei  = 2.91e-6 n_e lnLambda T_e^(-3/2)        s^-1
    lambda_ei = v_Te / nu_ei
"""
from __future__ import annotations
import glob, os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import numpy as np
import xcode_compare as X

BAND = (1e-2, 1.0)          # the underdense comparison band, TEST_PLAN 12.6
LNL = 6.3                   # the pinned Coulomb log the Phase-4 decks use
KN_CRIT = 0.06              # Spitzer-Harm / flux-limit onset


def knudsen(z_m, ne_cm3, Te_eV, smooth=0):
    """lambda_ei / L_T, with L_T = T_e/|dT_e/dz|.

    `smooth` is a rolling-mean window in CELLS applied to T_e before differentiating, and
    it is not cosmetic. A PIC T_e is a binned particle moment carrying shot noise, so a
    POINTWISE dT_e/dz is dominated by bin-to-bin scatter; that makes L_T artificially tiny
    and Kn artificially huge. Unsmoothed, `flashic` reports a median Kn of 19, which is not
    a plasma statement -- it is the noise floor of a numerical derivative. FLASH's profile
    is a fluid solution and needs no smoothing, so smoothing the PIC side ALONE is the
    like-for-like choice, not a thumb on the scale.
    """
    ne = np.maximum(ne_cm3, 1e-30); Te = np.maximum(Te_eV, 1e-6)
    vte = 4.19e7 * np.sqrt(Te)                       # cm/s
    nu = 2.91e-6 * ne * LNL * Te ** -1.5             # s^-1
    lam = vte / np.maximum(nu, 1e-30) * 1e-2         # cm -> m
    if smooth and smooth >= 3 and Te.size > smooth:
        k = np.ones(int(smooth)) / float(int(smooth))
        Te = np.convolve(Te, k, mode="same")
        # convolution edges are biased low; drop them from consideration
        Te[:smooth] = np.nan; Te[-smooth:] = np.nan
    dT = np.gradient(Te, z_m)
    LT = Te / np.maximum(np.abs(dT), 1e-30)
    return lam / np.maximum(LT, 1e-30), lam, LT


def flash_chk(path):
    import h5py
    with h5py.File(path, "r") as h:
        m = h["node type"][:] == 1
        names = [n[0].decode().strip() for n in h["unknown names"][:]]
        bb = h["bounding box"][:][m]
        v = {n: np.concatenate(h[n][:][m][:, 0, 0, :]) for n in names}
        nxb = h[names[0]][:][m].shape[-1]
        x = np.concatenate([np.linspace(b[0, 0], b[0, 1], nxb + 1)[:-1]
                            + (b[0, 1] - b[0, 0]) / nxb / 2 for b in bb])
        t = float(dict((k.decode().strip(), val)
                       for k, val in h["real scalars"][:])["time"])
    o = np.argsort(x)
    v = {k: val[o] for k, val in v.items()}
    x = x[o] * 1e-2                                   # cm -> m
    ne = v["dens"] * v["ye"] * X.NA * 1e6             # m^-3
    return dict(t=t, tau=t / X.TAU_F, x=x, zeta=(x - X.X_IFACE * 1e-2) / X.DI0_F,
                ne=ne, ne_ncr=ne / X.N_CR, Te=v["tele"] / X.KELV,
                fllm=v.get("fllm"), cond=v.get("cond"))


def main():
    print(__doc__)
    chks = sorted(glob.glob(os.path.join(X.FLASH_DIR, "lez1d_hdf5_chk_[0-9]*")))
    print(f"FLASH checkpoints: {len(chks)}\n")

    print("(1) HOW HARD IS FLASH'S FLUX LIMITER BINDING, inside the compared plume?")
    print(f"    band {BAND[0]:g} <= n_e/n_cr <= {BAND[1]:g}; fllm = 1 is unlimited Spitzer\n")
    print(f"    {'tau':>6} {'cells':>6} {'median fllm':>12} {'% fllm<1':>9} "
          f"{'% fllm<0.5':>11} {'% fllm<0.1':>11}")
    rows = []
    for p in chks:
        d = flash_chk(p)
        if d["fllm"] is None or d["tau"] <= 0.5:
            continue
        m = (d["ne_ncr"] >= BAND[0]) & (d["ne_ncr"] <= BAND[1])
        if m.sum() < 4:
            continue
        fl = d["fllm"][m]
        rows.append((d["tau"], m.sum(), np.median(fl), np.mean(fl < 0.999),
                     np.mean(fl < 0.5), np.mean(fl < 0.1)))
        print(f"    {d['tau']:6.1f} {m.sum():6d} {np.median(fl):12.4f} "
              f"{100*np.mean(fl<0.999):9.1f} {100*np.mean(fl<0.5):11.1f} "
              f"{100*np.mean(fl<0.1):11.1f}")
    if rows:
        a = np.array(rows)
        print(f"\n    MEAN over tau: median fllm {a[:,2].mean():.3f}, "
              f"{100*a[:,3].mean():.0f} % of plume cells limited, "
              f"{100*a[:,4].mean():.0f} % cut by more than half.")

    print("\n(2) IS EITHER CODE IN THE LOCAL (Spitzer-Harm) REGIME?")
    print(f"    Kn = lambda_ei/L_T, density-weighted over the same band. "
          f"Spitzer-Harm needs Kn <~ {KN_CRIT}\n")
    print(f"    {'leg':<26} {'tau':>6} {'median Kn':>11} {'% cells Kn>0.06':>16}")
    print("    (PIC T_e smoothed over 9 cells before differentiating -- see knudsen())")
    for p in chks:
        d = flash_chk(p)
        if d["tau"] <= 0.5:
            continue
        m = (d["ne_ncr"] >= BAND[0]) & (d["ne_ncr"] <= BAND[1])
        if m.sum() < 6:
            continue
        Kn, _, _ = knudsen(d["x"], d["ne"] * 1e-6, d["Te"])
        k = Kn[m]
        print(f"    {'FLASH':<26} {d['tau']:6.1f} {np.median(k):11.4f} "
              f"{100*np.mean(k > KN_CRIT):16.1f}")
    print()
    for lab, path, mr in (("kin_bg (2698)", "runs/P4/P4_lez_kin_bg", 2698.0),
                          ("flashic (2698)", "runs/P4/P4_lez_kin_flashic", 2698.0),
                          ("flashic_ct (100)", "runs/P4/P4_lez_kin_flashic_ct", 100.0)):
        sc = X.warpx_scales(mr)
        S = X.warpx_particles(path, X.SP_KIN, sc=sc)
        for tau in (6.7, 13.5, 20.3, 27.0):
            s = X.pick(S, tau)
            if s is None or s.get("Te") is None:
                continue
            z = np.asarray(s["zeta"]) * sc["di0"]
            ne = np.asarray(s["ne"]) * X.N_CR
            Te = np.asarray(s["Te"])
            m = np.isfinite(ne) & (s["ne"] >= BAND[0]) & (s["ne"] <= BAND[1]) & np.isfinite(Te)
            if m.sum() < 6:
                continue
            k_raw = knudsen(z, ne * 1e-6, Te)[0][m]
            k = knudsen(z, ne * 1e-6, Te, smooth=9)[0][m]
            k = k[np.isfinite(k)]
            if k.size < 4:
                continue
            print(f"    {lab:<26} {tau:6.1f} {np.median(k):11.4f} "
                  f"{100*np.mean(k > KN_CRIT):16.1f}"
                  f"   (unsmoothed {np.median(k_raw[np.isfinite(k_raw)]):.3f})")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
