#!/usr/bin/env python3
"""Does the FITTED corona absorb like FLASH's ACTUAL corona?

`scripts/flash_absorption.py` shows that at the 0.1 ns handoff the two codes absorb
differently from what is nominally the same plasma: FLASH's instantaneous fraction is
0.5295 and WarpX's `f_abs(0)` is 0.6821, a factor 1.29. The deposition operator is not a
candidate -- it is validated against analytic IB/WKB to 0.02-1.6 % and reproduces PSC's
kernel to 6.7e-16 (RESULTS 2026-07-28). An operator that is right on the profile it is
given can still absorb the wrong amount if the PROFILE is wrong.

The WarpX initial condition is not FLASH's profile. It is a four-parameter exponential
FITTED to it, with rms(ln n) = 0.107 over 1e-3..1 n_cr. Inverse bremsstrahlung goes as
n_e^2, so a 10.7 % rms error in ln n is a ~21 % error in the integrand, and the optical
depth is an integral of it along the whole ray path.

This script tests that directly and offline, with NO simulation: it builds both profiles,
integrates the SAME inverse-bremsstrahlung kernel along a normally-incident ray to the
turning point and back, and compares. The absolute prefactor cancels -- it is calibrated
so that the FLASH profile reproduces FLASH's own measured instantaneous absorption -- so
what is being tested is purely the shape.

    tau = 2 * int  K dz ,   K ~ nhat^2 / sqrt(1 - nhat) * Z * lnLambda(n,T) * T^(-3/2)
    f   = 1 - exp(-tau)

Reading it
----------
* predicted f close to WarpX's measured 0.68  -> the FIT explains the absorption gap.
  The repair is a higher-fidelity initial condition, not a code change.
* predicted f close to FLASH's 0.53           -> the fit is exonerated and the two codes
  disagree about ray handling on the same profile. That is a much more serious finding
  and it lands on the operator's turning-point treatment (the known G4 non-monotonicity).

Usage
-----
    python3 scripts/ic_optical_depth.py
    python3 scripts/ic_optical_depth.py --run runs/P5/P5_full --time 0.1
"""
import argparse
import os
import sys

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

DEFAULT_RUN = "runs/P4/P4_lez_kin_mrreal_drift"
DE_UM = 0.169336          # lambda_0 / 2pi at 1.064 um
N_CR_CM3 = 9.8477e20

# The band the ray actually traverses. Below 1e-4 n_cr the integrand is 1e-8 of its peak
# and the FLASH chamber gas (a numerical floor at 1e-10 g/cm^3) is not plasma we model.
N_LO = 1.0e-4


def ln_lambda_nrl(ne_cm3, Te_eV, Z=13.0):
    """NRL e-i Coulomb logarithm, the branch the operator uses (coulomb_log_mode: nrl).

    Clipped at 2.0: the NRL fit goes negative in cold dense matter and the operator floors
    it. Not clipping it is retraction-ledger item 2 waiting to happen.
    """
    ll = 24.0 - np.log(np.sqrt(ne_cm3) / Te_eV)
    return np.clip(ll, 2.0, None)


def kernel(nhat, Te_eV, Z=13.0):
    """The IB absorption integrand, up to a constant. Zero at and above n_cr.

    nhat^2 / sqrt(1 - nhat) is the standard collisional-absorption form (Kruer); the
    sqrt divergence at the turning point is integrable and is handled by the trapezoid
    on a fine grid, which is what the operator's march does too.
    """
    ne_cm3 = nhat * N_CR_CM3
    k = np.zeros_like(nhat)
    ok = (nhat > 0) & (nhat < 0.9999) & (Te_eV > 0)
    k[ok] = (nhat[ok] ** 2 / np.sqrt(1.0 - nhat[ok])
             * Z * ln_lambda_nrl(ne_cm3[ok], Te_eV[ok], Z) * Te_eV[ok] ** -1.5)
    return k


def tau_of(z_um, nhat, Te_eV, Z=13.0):
    """Optical depth to the turning point and back, over the band the ray sees.

    The ray enters from +z, so integrate inward from the outer edge to the OUTERMOST
    crossing of n_cr and double it for the return leg. If the profile never reaches
    n_cr the ray traverses everything once and exits -- doubling would be wrong there,
    so that case is flagged rather than silently handled.
    """
    o = np.argsort(z_um)
    z, n, T = z_um[o], nhat[o], Te_eV[o]
    band = (n >= N_LO) & np.isfinite(n) & np.isfinite(T)
    if band.sum() < 8:
        return np.nan, False
    z, n, T = z[band], n[band], T[band]
    over = np.where(n >= 1.0)[0]
    turns = over.size > 0
    if turns:
        i = over.max()          # outermost critical crossing; the ray never gets past it
        z, n, T = z[i:], n[i:], T[i:]
    k = kernel(n, T, Z)
    tau = np.trapezoid(k, z * 1e-6) if hasattr(np, "trapezoid") else np.trapz(k, z * 1e-6)
    return (2.0 if turns else 1.0) * tau, turns


def flash_profile(t_ns=0.1):
    from xcode_compare import flash_series, FLASH_DIR, DI0_F, X_IFACE
    S = flash_series(FLASH_DIR, "lez1d")
    s = min(S, key=lambda q: abs(q["t"] - t_ns * 1e-9))
    z_um = s["zeta"] * DI0_F * 1e6
    return z_um, s["ne"], s["Te"], s["t"] * 1e9


def fitted_profile(run_dir, npts=200000):
    """The WarpX initial condition, rebuilt from config.yaml exactly as deck.py builds it.

    Flat top at `density_over_ncr` behind the face, then an exponential corona of scale
    `scale_length_de` anchored so that n = `corona_density_over_ncr` at `corona_offset_de`
    in FRONT of the face. Temperature is the single `theta_e_init` through the corona and
    `theta_e_solid` inside the slab -- which is itself part of what is being tested, since
    FLASH's corona is not isothermal.
    """
    cfg = yaml.safe_load(open(os.path.join(run_dir, "config.yaml")))
    t = cfg["plasma"]["target"]
    lo = float(cfg["geometry"]["axis"]["lo_de"])
    hi = float(cfg["geometry"]["axis"]["hi_de"])
    n0 = float(t["density_over_ncr"])
    L = float(t["scale_length_de"])
    off = float(t["corona_offset_de"])
    nanch = float(t.get("corona_density_over_ncr", 1.0))
    Te_c = float(t["theta_e_init"]) * 511000.0
    Te_s = float(t["theta_e_solid"]) * 511000.0

    z_de = np.linspace(lo, hi, npts)
    # face at z = 0; corona for z > 0 decaying outward from n = nanch at z = off
    n = np.where(z_de <= 0.0, n0, nanch * np.exp(-(z_de - off) / L))
    n = np.minimum(n, n0)
    Te = np.where(z_de <= 0.0, Te_s, Te_c)
    return z_de * DE_UM, n, Te


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default=DEFAULT_RUN, help="run dir holding the fitted IC")
    ap.add_argument("--time", type=float, default=0.1, help="FLASH time [ns]")
    ap.add_argument("--f-flash", type=float, default=0.5295,
                    help="FLASH's measured instantaneous f at --time "
                         "(scripts/flash_absorption.py)")
    ap.add_argument("--f-warpx", type=float, default=0.6821,
                    help="WarpX's measured f_abs(0) for the leg carrying this IC")
    a = ap.parse_args()

    zF, nF, TF, tF = flash_profile(a.time)
    zW, nW, TW = fitted_profile(a.run)

    tauF, turnF = tau_of(zF, nF, TF)
    tauW, turnW = tau_of(zW, nW, TW)

    print(f"FLASH plotfile at t = {tF:.4f} ns   vs   the fitted IC in {a.run}\n")
    print(f"  {'':22s} {'tau (arb)':>12s} {'turns?':>8s} {'n_max/n_cr':>12s}")
    print("  " + "-" * 58)
    print(f"  {'FLASH actual':22s} {tauF:12.4e} {str(turnF):>8s} {np.nanmax(nF):12.1f}")
    print(f"  {'WarpX fitted IC':22s} {tauW:12.4e} {str(turnW):>8s} {np.nanmax(nW):12.1f}")
    print(f"\n  shape ratio tau_W / tau_F = {tauW/tauF:.4f}")

    # Calibrate the one free constant on FLASH, then predict WarpX. This is the whole test.
    if not (0.0 < a.f_flash < 1.0):
        sys.exit("--f-flash must be a fraction")
    C = -np.log(1.0 - a.f_flash) / tauF
    f_pred = 1.0 - np.exp(-C * tauW)
    print(f"\n  calibrating on FLASH: f = 1 - exp(-C tau) with f_FLASH = {a.f_flash:.4f}")
    print(f"  -> PREDICTED WarpX f_abs(0) from the fitted profile = {f_pred:.4f}")
    print(f"     MEASURED  WarpX f_abs(0)                         = {a.f_warpx:.4f}")

    span = a.f_warpx - a.f_flash
    if abs(span) < 1e-9:
        return
    frac = (f_pred - a.f_flash) / span
    print(f"\n  the fitted profile explains {100*frac:.0f}% of the measured gap "
          f"({a.f_flash:.3f} -> {a.f_warpx:.3f}).")
    print("  NOTE f_abs(0) carries 10.4% 1-sigma on RNG seed alone (retraction ledger 1),")
    print("  so read this as an attribution, not a closure. The time-integrated <f_abs>")
    print("  ratio of 1.23 is the number on firm ground.")


if __name__ == "__main__":
    main()
