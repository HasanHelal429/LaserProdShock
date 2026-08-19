#!/usr/bin/env python3
"""D-2: how much of the FLASH<->WarpX profile-shape gap is non-isothermality?

    /opt/anaconda3/envs/physics/bin/python studies/plume_structure/d2_shape.py

THE HYPOTHESIS BEING TESTED. FLASH's plume is a smooth exponential because it is
ISOTHERMAL: the self-similar rarefaction is

    n(z,t) = n_cr exp(-z / C_S t)      =>      d ln n / d zeta = -1 / (tau * C_S/C_S0)

and that slope is constant in z ONLY if T_e is constant in z. FLASH imposes that flatness
through flux-limited Spitzer-Harm conduction. WarpX has NO conduction operator, so if the
shape difference is simply "WarpX is not isothermal", then dividing the measured slope by
the prediction formed from each leg's OWN LOCAL T_e(z) should flatten the WarpX profiles
onto FLASH's.

WHAT IS REPORTED. Over the underdense band, at each tau:

    raw     std of the measured log-slope           -- how non-exponential the profile is
    corr    std after dividing by the local-T_e prediction
    R       1 - var(corr)/var(raw), the fraction of the shape variance that KNOWING
            T_e(z) explains. R near 1 means non-isothermality is the whole story; R near
            0 means T_e(z) does not account for the structure and something else does.

READ `R`, NOT THE MEAN RATIO. Every leg already has roughly the right MEAN slope (they all
sit near the analytic solution on average); the disagreement is entirely in the local
structure, so a mean-based statistic shows nothing.
"""
from __future__ import annotations
import os, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "scripts"))
import numpy as np
import xcode_compare as X

LEGS = (("kin_bg",     "runs/P4/P4_lez_kin_bg",         2698.0),
        ("flashic",    "runs/P4/P4_lez_kin_flashic",    2698.0),
        ("flashic_ct", "runs/P4/P4_lez_kin_flashic_ct",  100.0),
        ("flashic_res","runs/P4/P4_lez_kin_flashic_res", 100.0))
TAUS = (6.7, 13.5, 20.3, 27.0)
BAND = (1e-2, 1.0)          # the underdense comparison band, TEST_PLAN 12.6

# ...but the self-similar rarefaction is NOT expected to hold across all of it. Near the
# ablation front T_e ramps from ~0 to its plateau over a few d_i0, so 1/sqrt(T_e) blows up
# there and swamps the statistic: the first version of this script reported R < 0 for
# FLASH ITSELF, i.e. "knowing T_e makes FLASH less exponential", which is a broken metric
# rather than a result. The rarefaction ansatz applies where the plume is ISOTHERMAL, so
# the fit region is restricted to beyond the T_e plateau onset -- defined here as the
# first zeta at which T_e exceeds HALF its in-band maximum.
def _plateau_start(z, T, m):
    Tb = T[m]
    if Tb.size == 0:
        return -np.inf
    half = 0.5 * np.nanmax(Tb)
    zb = z[m]
    ok = np.where(Tb >= half)[0]
    return zb[ok[0]] if ok.size else -np.inf


def shape(zeta, ne, Te, tau, npt=40):
    """(raw slope std, T_e-corrected std, R) over the underdense band."""
    z = np.asarray(zeta, float); n = np.asarray(ne, float)
    if Te is None:
        return None
    T = np.asarray(Te, float)
    o = np.argsort(z); z, n, T = z[o], n[o], T[o]
    m = np.isfinite(n) & (n >= BAND[0]) & (n <= BAND[1]) & np.isfinite(T) & (T > 0)
    if m.sum() < 8:
        return None
    lo, hi = max(z[m].min(), _plateau_start(z, T, m)), z[m].max()
    if hi - lo < 5:
        return None
    q = np.linspace(lo, hi, npt)
    ln = np.interp(q, z, np.log(np.maximum(n, 1e-30)))
    Tq = np.interp(q, z, T)
    slope = np.gradient(ln, q)
    pred = -1.0 / (tau * np.sqrt(np.maximum(Tq, 1e-3) / X.TE_REF))
    corr = slope / pred                       # 1.0 everywhere == on the analytic solution
    raw = slope / np.nanmean(slope)           # same normalisation, no T_e knowledge
    vr, vc = np.nanvar(raw), np.nanvar(corr)
    return dict(raw=np.sqrt(vr), corr=np.sqrt(vc), R=1.0 - vc / vr if vr > 0 else np.nan,
                mean=np.nanmean(corr), npts=int(m.sum()), span=(lo, hi))


def main():
    print(__doc__)
    F = X.flash_series(X.FLASH_DIR, "lez1d")
    rows = {}
    print(f"{'leg':<12} {'tau':>6} {'raw std':>9} {'corr std':>9} {'R':>7} "
          f"{'mean ratio':>11}   span in zeta")
    print("-" * 76)
    for tau in TAUS:
        f = X.pick(F, tau)
        r = shape(f["zeta"], f["ne"], f["Te"], tau)
        if r:
            rows.setdefault("FLASH", []).append(r)
            print(f"{'FLASH':<12} {tau:6.1f} {r['raw']:9.3f} {r['corr']:9.3f} "
                  f"{r['R']:7.2f} {r['mean']:11.2f}   {r['span'][0]:.0f}-{r['span'][1]:.0f}")
    print()
    for lab, path, mr in LEGS:
        sc = X.warpx_scales(mr)
        S = X.warpx_particles(path, X.SP_KIN, sc=sc)
        for tau in TAUS:
            s = X.pick(S, tau)
            if s is None:
                continue
            r = shape(s["zeta"], s["ne"], s.get("Te"), tau)
            if r:
                rows.setdefault(lab, []).append(r)
                print(f"{lab:<12} {tau:6.1f} {r['raw']:9.3f} {r['corr']:9.3f} "
                      f"{r['R']:7.2f} {r['mean']:11.2f}   "
                      f"{r['span'][0]:.0f}-{r['span'][1]:.0f}")
        print()
    print("=" * 76)
    print("SUMMARY -- mean over tau")
    print(f"  {'leg':<12} {'raw std':>9} {'corr std':>9} {'R':>7}")
    for k, v in rows.items():
        print(f"  {k:<12} {np.mean([q['raw'] for q in v]):9.3f} "
              f"{np.mean([q['corr'] for q in v]):9.3f} {np.mean([q['R'] for q in v]):7.2f}")
    print("\n  R = fraction of the profile-shape variance explained by knowing T_e(z).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
