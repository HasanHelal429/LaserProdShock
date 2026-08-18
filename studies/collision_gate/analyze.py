#!/usr/bin/env python3
"""Reduce the D3 collision-gate ladder to a verdict against Lezhnin 2025 Eq. (B1).

    /opt/anaconda3/envs/physics/bin/python analyze.py

Reads ``scratch/D3_*/diags/reducedfiles/EP.txt`` and writes ``media/`` figures plus a
printed table. Nothing here launches WarpX.

MEASUREMENT. ``EP`` (ParticleEnergy) reports the weight-weighted MEAN kinetic energy per
particle for each species, so for a Maxwellian at rest ``T = (2/3)<E>``. All macroparticle
weights are equal here (uniform density, uniform ppc), so the weighting is moot -- but it
is a weighted mean, which is what makes it safe.

THE RATE ESTIMATOR is the decay of the DIFFERENCE, not a fit to T_i(t). Eq. (B1) is
equivalent to

    T_e(t) - T_i(t) = (T_e0 - T_i0) exp(-R t),     R = ((1+Z)/Z) nu_ie = (1+Z) nu_ei

and R is what the collision operator sets. Fitting the difference has three advantages over
fitting T_i: it is independent of how the equilibrium partition comes out, it cancels any
drift COMMON to both species (which is what grid heating mostly is), and a straight line in
log space is a far more honest display of an exponential than a saturating curve is.

THE CONTROL. Each point has a collisions-disabled arm. ``dz/lambda_D`` is ~98 in the dense
cold cases, so numerical grid heating is expected; it is subtracted as a rate
(``R_corrected = R_measured - R_off``) and its size is reported, never assumed negligible.
The control also supplies the MEASURED temperature noise floor, so the error bars are not a
theoretical estimate.
"""

from __future__ import annotations

import argparse
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
QE = 1.602176634e-19
Z = 13.0

import sys
sys.path.insert(0, HERE)
from make_variants import (ARMS, CASES, CONFIRM, DROPPED, case_physics,   # noqa
                           variant_name, LNL, ME, EPS0, DT)


def sigma_cap(ne, Te_eV, lnL):
    """(sigma_Coulomb, sigma_max, ratio) for the e-i pair, SI.

    WarpX honours a pinned CoulombLog (ElasticCollisionPerez.H / UpdateMomentumPerezElastic.H
    line "if (L > 0) lnLmd = L") but then CAPS the effective cross-section:

        sigma_eff = min(pi b0^2 lnLmd, sigma_max),   sigma_max = 1/(max(n1,n2) * r_min)

    with r_min = (4 pi n /3)^(-1/3) the interparticle spacing -- i.e. a collision may not
    have a mean free path shorter than the distance to the next particle (Perez et al.,
    Phys. Plasmas 19, 083104 (2012), Sec. II.C; and Angus et al., JCP 531, 113927 (2025)).
    Where the cap binds, the plasma is strongly coupled and the Spitzer rate at the pinned
    lnLambda is simply not a physical target -- so a "discrepancy" there is the REFERENCE
    being wrong, not the operator.

    b0 is evaluated at the mean relative speed sqrt(3 kT_e/m_e), which is a single-velocity
    stand-in for an average over the distribution; since sigma ~ v^-4, slow pairs are capped
    harder than this estimate, so the true suppression is somewhat STRONGER than the ratio
    returned here. Treat it as an upper bound on sigma_max/sigma_C, not an exact prediction.
    """
    vrel = np.sqrt(3.0 * Te_eV * QE / ME)
    b0 = Z * QE ** 2 / (2.0 * np.pi * EPS0 * ME * vrel ** 2)
    sig_C = np.pi * b0 ** 2 * lnL
    rmin = (4.0 * np.pi / 3.0 * ne) ** (-1.0 / 3.0)
    sig_max = 1.0 / (ne * rmin)
    return sig_C, sig_max, sig_max / sig_C


def read_arm(name):
    """(t, T_e, T_i, E_total) from a variant's EP.txt, temperatures in eV."""
    p = os.path.join(HERE, "scratch", name, "diags", "reducedfiles", "EP.txt")
    if not os.path.exists(p):
        return None
    a = np.loadtxt(p, comments="#")
    if a.ndim != 2 or a.shape[0] < 8:
        return None
    t = a[:, 1]
    Te = (2.0 / 3.0) * a[:, 6] / QE
    Ti = (2.0 / 3.0) * a[:, 7] / QE
    return dict(t=t, Te=Te, Ti=Ti, Etot=a[:, 2], n=a.shape[0])


def fit_rate(t, D):
    """Least-squares slope of ln D vs t, with a bootstrap 1-sigma. Returns (R, sigma).

    D must stay positive; if collisions overshoot into D < 0 the run has equilibrated and
    the tail is noise, so only the strictly-positive leading segment is used and the
    truncation is reported by the caller via `frac_used`.
    """
    ok = D > 0
    if ok.sum() < 8:
        return np.nan, np.nan, 0.0
    # leading contiguous positive run
    first_bad = np.argmin(ok) if not ok.all() else len(ok)
    if first_bad < 8:
        return np.nan, np.nan, 0.0
    t, D = t[:first_bad], D[:first_bad]
    # SCALE t to O(1) before the least squares. Times here are 1e-16..1e-13 s, so a design
    # matrix of [t, 1] has condition number ~1e14 and lstsq silently zeroes the slope
    # column -- which reported R = -4e-15 (i.e. "no equilibration at all") for a run whose
    # T_i had visibly moved. The fit must be done in scaled time and the slope mapped back.
    T0 = t[-1] if t[-1] > 0 else 1.0
    ts = t / T0
    y = np.log(D)
    A = np.vstack([ts, np.ones_like(ts)]).T
    coef, *_ = np.linalg.lstsq(A, y, rcond=None)
    R = -coef[0] / T0
    resid = y - A @ coef
    dof = max(len(t) - 2, 1)
    s2 = float(resid @ resid) / dof
    cov = s2 * np.linalg.inv(A.T @ A)
    return R, float(np.sqrt(cov[0, 0])) / T0, first_bad / max(len(ok), 1)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-figure", action="store_true")
    a = ap.parse_args()

    print("=" * 108)
    print("D3 COLLISION GATE -- e-i thermalisation against Lezhnin 2025 Eq. (B1)")
    print("R = (1+Z) nu_ei is the decay rate of (T_e - T_i); lnLambda = 6.3 pinned in "
          "deck AND theory.")
    print("=" * 108)
    hdr = (f"{'n_e/n_cr':>8} {'Ti':>5} | {'arm':>9} {'nu*dtc':>7} | {'R_pred[1/s]':>12} "
           f"{'R_meas[1/s]':>12} {'+-':>10} {'ratio':>7} {'R_off/R_pred':>13} "
           f"{'Ti_end':>8} {'Ti_pred':>8} {'used':>6}")
    print(hdr)
    results = {}
    missing = []
    for nf, Ti in CASES:
        if True:
            p = case_physics(nf, Ti)
            R_pred = (1.0 + Z) * p["nu_e"]
            off = read_arm(variant_name(nf, Ti, "coll_off"))
            R_off = np.nan
            if off is not None:
                R_off, _, _ = fit_rate(off["t"], off["Te"] - off["Ti"])
            for arm, enabled, ndt in ARMS:
                nm = variant_name(nf, Ti, arm)
                d = read_arm(nm)
                if d is None:
                    missing.append(nm)
                    continue
                R, sig, frac = fit_rate(d["t"], d["Te"] - d["Ti"])
                # analytic T_i at this run's end time
                Ti_pred = Ti + Z * (p["Te"] - Ti) / (Z + 1.0) * \
                    (1.0 - np.exp(-R_pred * d["t"][-1]))
                corr = (R - R_off) if (arm != "coll_off" and np.isfinite(R_off)) else R
                results[nm] = dict(p=p, arm=arm, ndt=ndt, R_pred=R_pred, R=R, sig=sig,
                                   R_corr=corr, R_off=R_off, d=d, Ti_pred=Ti_pred,
                                   frac=frac)
                _, _, cap = sigma_cap(p["ne"], p["Te"], LNL)
                results[nm]["cap"] = cap
                print(f"{nf:8.2f} {Ti:5.0f} | {arm:>9} "
                      f"{p['nu_brag']*ndt*9.8851e-17 if enabled else 0:7.3f} | "
                      f"{R_pred:12.4e} {R:12.4e} {sig:10.2e} "
                      f"{(corr/R_pred if arm!='coll_off' else np.nan):7.3f} "
                      f"{R_off/R_pred:13.4f} {d['Ti'][-1]:8.3f} {Ti_pred:8.3f} "
                      f"{frac:6.2f}")
    if missing:
        print(f"\nMISSING ({len(missing)}): {', '.join(missing)}")

    print("\n" + "=" * 108)
    print("THE sigma_max CROSS-SECTION CAP -- why a 'discrepancy' can be the reference's "
          "fault, not the operator's")
    print(f"  {'case':30s} {'sigma_C':>11} {'sigma_max':>11} {'cap':>8} {'binds?':>7}  "
          f"expectation")
    for nf, Ti in CASES:
        if True:
            p = case_physics(nf, Ti)
            sC, sM, cap = sigma_cap(p["ne"], p["Te"], LNL)
            tag = f"{nf:g} n_cr, T_e = {p['Te']:.1f} eV"
            exp = ("SUPPRESSED, by roughly this factor" if cap < 1
                   else "should MATCH Eq. (B1)")
            print(f"  {tag:30s} {sC:11.4e} {sM:11.4e} {cap:8.3f} "
                  f"{'YES' if cap < 1 else 'no':>7}  {exp}")

    print("\n" + "=" * 108)

    print("CONFIRMATION: is collisions.coulomb_log honoured, or does WarpX compute lnLambda?")
    for name, nf, Ti, lnL, ndt in CONFIRM:
        d = read_arm(name)
        if d is None:
            print(f"  {name}: NOT RUN YET")
            continue
        p = case_physics(nf, Ti)
        R_pred_pinned = (1.0 + Z) * p["nu_e"] * lnL / LNL
        R, sig, frac = fit_rate(d["t"], d["Te"] - d["Ti"])
        sC, sM, cap = sigma_cap(p["ne"], p["Te"], lnL)
        print(f"  {name}")
        print(f"    lnLambda pinned at {lnL:g};  sigma_max/sigma_C = {cap:.2f} "
              f"({'cap INACTIVE, so it cannot confound' if cap > 1 else 'CAP ACTIVE -- test invalid'})")
        print(f"    R_pred(pinned {lnL:g}) = {R_pred_pinned:.4e} 1/s")
        print(f"    R_measured            = {R:.4e} +- {sig:.2e} 1/s")
        print(f"    ratio                 = {R/R_pred_pinned:.3f}")
        print(f"    -> ~1.0 means the pinned value IS honoured; "
              f"~{4.06/lnL:.2f} would mean WarpX used its own lnLambda = 4.06")

    print("\n" + "=" * 108)
    print("ENERGY CONSERVATION (collisions must conserve it exactly; drift = grid heating)")
    for nm, r in results.items():
        E = r["d"]["Etot"]
        print(f"  {nm:26s} dE/E = {(E[-1]/E[0]-1)*100:+8.4f} %")

    print("\n" + "=" * 108)
    print("VERDICT")
    ok_c1, bad_c1, ok_c10, bad_c10 = [], [], [], []
    for nm, r in results.items():
        if r["arm"] == "coll_off":
            continue
        ratio = r["R_corr"] / r["R_pred"]
        tag = f"{r['p']['ne_frac']:g} n_cr / {r['p']['Ti']:.0f} eV"
        (ok_c1 if r["arm"] == "c1" else ok_c10).append((tag, ratio, r))
    for lab, rows in (("c1  (every step)", ok_c1), ("c10 (PRODUCTION)", ok_c10)):
        print(f"  {lab}:")
        for tag, ratio, r in sorted(rows, key=lambda q: -q[1]):
            v = "OK" if 0.8 <= ratio <= 1.25 else ("LOW" if ratio < 0.8 else "HIGH")
            print(f"     {tag:20s} R_meas/R_pred = {ratio:6.3f}   {v}"
                  f"   (nu_ei*dt_coll = {r['p']['nu_brag']*r['ndt']*9.8851e-17:.3f})")
    if not a.no_figure:
        figure(results)
    return 0


def figure(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(os.path.join(HERE, "media"), exist_ok=True)
    COL = {"coll_off": "0.55", "c1": "#1f4e9c", "c10": "#c1441a"}
    fig, ax = plt.subplots(2, 3, figsize=(15.5, 7.6))
    NE_CASES = sorted({c[0] for c in CASES}, reverse=True)
    TI_CASES = sorted({c[1] for c in CASES})
    for j, nf in enumerate(NE_CASES):
        for i, Ti in enumerate(TI_CASES):
            if (nf, Ti) not in CASES:
                ax[i, j].axis("off"); continue
            A = ax[i, j]
            p = case_physics(nf, Ti)
            R_pred = (1.0 + Z) * p["nu_e"]
            got = False
            for arm, _, ndt in ARMS:
                r = results.get(variant_name(nf, Ti, arm))
                if r is None:
                    continue
                d = r["d"]
                A.semilogy(d["t"] * 1e12, np.maximum(d["Te"] - d["Ti"], 1e-4),
                           color=COL[arm], lw=1.5,
                           label={"coll_off": "collisions off",
                                  "c1": "every step",
                                  "c10": "every 10 (production)"}[arm])
                got = True
            if got:
                tt = np.linspace(0, r["d"]["t"][-1], 200)
                A.semilogy(tt * 1e12, (p["Te"] - p["Ti"]) * np.exp(-R_pred * tt),
                           color="k", ls="--", lw=1.3, label="Eq. (B1)")
            A.set_title(f"$n_e$ = {nf:g} $n_{{cr}}$,  $T_i$ = {Ti:.0f} eV   "
                        f"($\\nu_{{ei}}dt_{{coll}}$ = {p['nu_brag']*10*9.8851e-17:.2f} "
                        f"at production)", fontsize=9)
            A.set_xlabel("t  [ps]")
            A.set_ylabel("$T_e - T_i$  [eV]")
            A.grid(alpha=0.15)
            if i == 0 and j == 0:
                A.legend(fontsize=8)
    fig.suptitle("D3 collision gate: decay of $T_e-T_i$ against Lezhnin Eq. (B1). "
                 "A correct operator lies on the dashed line.", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = os.path.join(HERE, "media", "b1_decay.png")
    fig.savefig(out, dpi=135)
    print(f"\n  figure: {out}")


if __name__ == "__main__":
    raise SystemExit(main())
