#!/usr/bin/env python3
"""FLASH's absorbed fraction, on the SAME convention as the PIC legs.

Closes the Phase-4 open item "FLASH's `f_abs` convention never re-derived" (RESULTS.md
CURRENT STATE), which the matched-`f_abs` cross-code claim rests on.

The number in `DELIVERY.md` -- 87.04 % -- is a WHOLE-RUN figure: cumulative energy in
against cumulative energy out over 0 -> 1 ns, and it reproduces exactly. But the PIC legs
never simulate 0 -> 0.1 ns. They are handed FLASH's state at the end of the laser ramp and
integrate absorption from there, so `xcode_compare.absorbed()` reports

    <f_abs> = E_abs / (I0 * t_elapsed)

over the leg's OWN window. Comparing that against FLASH's whole-run 0.870 compares two
different integrals, and FLASH's absorption is strongly time-dependent -- it is still
climbing through the entire run -- so the mismatch does not average out.

This script computes FLASH's fraction over an arbitrary window, on both conventions:

    time-integrated   f = (dEin - dEout) / dEin     <- compare against <f_abs>
    instantaneous     f = 1 - dEout/dEin per step   <- compare against f_end

Usage
-----
    python3 scripts/flash_absorption.py                       # the standard windows
    python3 scripts/flash_absorption.py --t0 0.1 --t1 0.3     # one window, ns
    python3 scripts/flash_absorption.py --against runs/P4/P4_lez_kin_mrreal_drift
    python3 scripts/flash_absorption.py --rad                 # the radiation-ON run
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

NORAD = ("/home/hhelal/shared/simulations/FLASH_LaserAblation-Ploegstra_2026-08/"
         "Ablation_prod_08-17/lez1d_LaserEnergyProfile.dat")
RAD = ("/home/hhelal/shared/simulations/FLASH_LaserAblationRad-Ploegstra_2026-08/"
       "Ablation_prod_rad_08-17/lez1drad_LaserEnergyProfile.dat")

T_HANDOFF = 0.1     # ns -- where every PIC leg starts
T_END = 1.0         # ns -- end of FLASH's flat top

# The windows worth printing by default: the ramp the PIC legs skip, the parent leg's
# window, and P5_full's window.
WINDOWS = [("laser ramp, skipped by every PIC leg", 0.0, 0.1),
           ("P4_lez_kin_mrreal_drift window", 0.1, 0.3),
           ("P5_full window (the whole flat top)", 0.1, 1.0),
           ("whole FLASH run (the DELIVERY.md basis)", 0.0, 1.0)]


def load(path):
    """Columns: step, t, dt, Ein, Eout, dEin, dEout. Energies cumulative, in erg."""
    if not os.path.exists(path):
        sys.exit(f"no such file: {path}\n"
                 "The FLASH delivery lives under ~/shared/simulations -- see "
                 "runs/P4/P4_lez_flash/DELIVERY.md.")
    d = np.loadtxt(path, comments="#")
    return dict(t=d[:, 1], dt=d[:, 2], Ein=d[:, 3], Eout=d[:, 4],
                dEin=d[:, 5], dEout=d[:, 6])


def integrated(F, t0_ns, t1_ns):
    """Time-integrated absorbed fraction over [t0, t1], the <f_abs> convention.

    Uses the CUMULATIVE columns differenced across the window rather than summing the
    per-step increments: the two agree to round-off, and the cumulative pair is what
    DELIVERY.md quotes, so this reproduces its number exactly on the whole-run window.
    """
    t = F["t"]
    i0 = int(np.searchsorted(t, t0_ns * 1e-9))
    i1 = min(int(np.searchsorted(t, t1_ns * 1e-9)), len(t) - 1)
    if i1 <= i0:
        return None
    dI = F["Ein"][i1] - F["Ein"][i0]
    dO = F["Eout"][i1] - F["Eout"][i0]
    if dI <= 0:
        return None
    return dict(f=1.0 - dO / dI, E_in_erg=dI, E_abs_erg=dI - dO,
                nstep=i1 - i0, t0=t[i0], t1=t[i1])


def instantaneous(F, t_ns, nsmooth=50):
    """1 - dEout/dEin averaged over the `nsmooth` steps ending at t, the f_end convention.

    Smoothed because the per-step increments are noisy at the 1e-4 level once the corona
    is optically thick and dEout is a small difference of large numbers.
    """
    t = F["t"]
    i = min(int(np.searchsorted(t, t_ns * 1e-9)), len(t) - 1)
    j = max(0, i - nsmooth)
    dI = F["dEin"][j:i].sum()
    dO = F["dEout"][j:i].sum()
    return 1.0 - dO / dI if dI > 0 else np.nan


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rad", action="store_true",
                    help="the radiation-ON run (default: radiation OFF, the comparison leg)")
    ap.add_argument("--file", default=None, help="an explicit LaserEnergyProfile.dat")
    ap.add_argument("--t0", type=float, default=None, help="window start [ns]")
    ap.add_argument("--t1", type=float, default=None, help="window end [ns]")
    ap.add_argument("--against", metavar="RUN_DIR", default=None,
                    help="a WarpX run dir: print its <f_abs> on the SAME window and the ratio")
    a = ap.parse_args()

    path = a.file or (RAD if a.rad else NORAD)
    F = load(path)
    print(f"FLASH laser energy profile: {path}")
    print(f"  {len(F['t'])} steps, t = 0 -> {F['t'][-1]*1e9:.4f} ns\n")

    windows = ([(f"window {a.t0} -> {a.t1} ns", a.t0, a.t1)]
               if a.t0 is not None and a.t1 is not None else WINDOWS)

    print(f"  {'window':44s} {'<f_abs>':>9s} {'f_inst(t1)':>11s} {'steps':>7s}")
    print("  " + "-" * 74)
    for lab, t0, t1 in windows:
        r = integrated(F, t0, t1)
        if r is None:
            continue
        fi = instantaneous(F, t1)
        star = " *" if abs(t0 - T_HANDOFF) < 1e-12 else "  "
        print(f"  {lab:42s}{star} {r['f']:9.4f} {fi:11.4f} {r['nstep']:7d}")
    print("\n  * = a window a PIC leg can actually be compared against.")

    if a.against:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from xcode_compare import absorbed
        w = absorbed(a.against)
        if w is None:
            sys.exit(f"\nno LASERDEP lines in {a.against}/run.log")
        # A WarpX leg's clock starts at the handoff, so its elapsed time maps onto FLASH's
        # clock by adding it. t_end is in seconds of WarpX time; at mu = 1 that IS FLASH
        # time, but a reduced-mass leg's seconds are NOT, so refuse to guess.
        import yaml
        cfg = yaml.safe_load(open(os.path.join(a.against, "config.yaml")))
        mr = float(cfg["reference"]["mass_ratio"])
        mu = mr / 49542.0
        t1 = T_HANDOFF + w["t_end"] * 1e9
        print(f"\n  WarpX leg: {a.against}")
        print(f"    mass_ratio {mr:.0f}  (mu = {mu:.4f})")
        if abs(mu - 1.0) > 1e-3:
            print("    !! REDUCED MASS. Its seconds are not FLASH's seconds (HANDOFF.md 4),")
            print("       and its absorption is broken by construction as mu^0.490 (7.4).")
            print("       No window on FLASH's clock is the right comparison. Refusing.")
            return
        r = integrated(F, T_HANDOFF, t1)
        print(f"    window on FLASH's clock: {T_HANDOFF:.3f} -> {t1:.4f} ns")
        print(f"    WarpX <f_abs> = {w['f_mean']:.4f}   f_end = {w['f_end']:.4f}")
        print(f"    FLASH <f_abs> = {r['f']:.4f}   f_inst = {instantaneous(F, t1):.4f}")
        print(f"    ratio WarpX/FLASH, time-integrated = {w['f_mean']/r['f']:.4f}")
        # Manheimer carries f_abs^(2/3) on the ABSORBED intensity (RESULTS 2026-08-28,
        # exact to 2.3%), so this is what correcting WarpX onto FLASH's absorption does
        # to its temperature.
        print(f"    T_e correction to matched f_abs, (f_F/f_W)^(2/3) = "
              f"{(r['f']/w['f_mean'])**(2/3):.4f}")


if __name__ == "__main__":
    main()
