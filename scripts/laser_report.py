#!/usr/bin/env python3
"""Report what the laser actually did: absorption history, shutoff, deposition profile.

Reads the operator's own diagnostics — the ``LASERDEP`` lines in ``run.log`` and the
per-cell ``diags/laserdep_profile_<step>.txt`` dumps — rather than particle energies,
because the tracer's accounting is **immune to grid heating** while the particles' is
not. That distinction is the whole basis of gate G6.

    python scripts/laser_report.py runs/<ID>
    python scripts/laser_report.py runs/<ID> --step 0     # which profile dump to plot

Writes:
  ``media/<ID>/laser_history.png``  f_abs(t), cumulative E_abs(t), Tlocalfrac(t)
  ``media/<ID>/laser_profile.png``  the per-cell n_e / P_abs profile from one dump

and prints the numbers Phase 1 and Phase 3 are built on: peak and final absorbed
fraction, shutoff time (absolute, and in gyroperiods when there is a field), total
coupled energy, energy per target ion, and the implied ablation temperature.
"""

from __future__ import annotations

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import io as lpio           # noqa: E402
from laserprod import plotting as lpp      # noqa: E402
from laserprod import units as lpunits     # noqa: E402


def history_figure(cfg, sc, hist, run_id, run_dir):
    import matplotlib.pyplot as plt

    P_inc = lpio.incident_power(sc, cfg)
    f = hist.f_abs(P_inc)
    t_ps = [v * 1e12 for v in hist.t]
    have_Tf = any(v == v for v in hist.Tlocalfrac)

    nrows = 3 if have_Tf else 2
    fig, axes = plt.subplots(nrows, 1, figsize=(11.0, 2.5 * nrows + 0.6),
                             sharex=True)
    fig.subplots_adjust(hspace=0.35)

    # --- absorbed fraction: the self-limiting shutoff ---
    ax = axes[0]
    ax.plot(t_ps, f, color=lpp.C_LASER)
    lpp.label_line(ax, t_ps[-1], f[-1], " f$_{abs}$", lpp.C_LASER)
    ax.set_ylabel("f$_{abs}$ = P$_{abs}$/P$_{inc}$")
    # DESCRIPTIVE, computed from this run's own data -- the same rule the E_abs panel
    # below already follows. The old fixed title asserted "then shuts itself off", which
    # P1_vac_1d flatly contradicts: f_abs falls from 1.000 to a ~0.23 PLATEAU and keeps
    # delivering for the remaining 97% of the run. A panel must not state a conclusion
    # its own curve refutes.
    if f_fin := [v for v in f if v == v]:
        pk, fin = max(f_fin), f_fin[-1]
        late = sum(f_fin[int(0.8 * len(f_fin)):]) / max(1, len(f_fin) - int(0.8 * len(f_fin)))
        verdict = (f"decays to a PLATEAU at f$_{{abs}}$ ≈ {late:.2f}, not to zero — "
                   f"the drive keeps delivering" if late > 0.05 * pk else
                   f"SHUTS OFF (late f$_{{abs}}$ ≈ {late:.3f})")
        title = (f"Absorbed fraction — K ∝ Z$_{{eff}}$lnΛ n$_e^2$ T$_e^{{-3/2}}$ is "
                 f"self-limiting: peak {pk:.3f} → final {fin:.3f}, and it {verdict}")
    else:
        title = "Absorbed fraction — laser off (I₀ = 0), nothing to report"
    ax.set_title(title, loc="left", fontweight="bold", fontsize=9.5)
    t_off = hist.shutoff_time()
    if t_off is not None:
        ax.axvline(t_off * 1e12, color=lpp.INK, ls=":", lw=1.2)
        ax.text(t_off * 1e12, 0.96, "  shutoff (½ peak)", va="top", fontsize=8,
                transform=ax.get_xaxis_transform(), color=lpp.INK)
    # A laser-off control (gate G3) has P_inc = 0, so every f_abs is nan and both max()
    # and set_ylim() raise. The control is a MANDATORY run type here, so it has to be a
    # first-class case rather than a crash: keep the panel and say why it is empty.
    f_ok = [v for v in f if v == v]                      # drops nan
    if f_ok:
        ax.set_ylim(0, max(1.02 * max(f_ok), 0.05))
    else:
        ax.set_ylim(0, 1)
        ax.text(0.5, 0.5, "laser off (I₀ = 0) — no absorbed fraction to report;\n"
                          "this run exists to measure grid heating (gate G3)",
                transform=ax.transAxes, ha="center", va="center", fontsize=9,
                color=lpp.INK_2)
    lpp.style_axes(ax)

    # --- cumulative coupled energy (own panel; NOT a second y-axis) ---
    # The title is DESCRIPTIVE, computed from this run's own data. H2 predicts E_abs
    # saturates once the drive shuts off; whether it actually does is the measurement,
    # so the panel must not assert it. (In P0_bc_periodic it does NOT: f_abs falls to a
    # ~0.12 floor rather than to zero, so E_abs keeps climbing almost linearly.)
    ax = axes[1]
    ax.plot(t_ps, hist.Eabs, color=lpp.C_FOURTH)
    lpp.label_line(ax, t_ps[-1], hist.Eabs[-1], " E$_{abs}$", lpp.C_FOURTH)
    ax.set_ylabel("E$_{abs}$  [J per absent dim]")
    # late-time slope relative to the early slope: ~0 means saturated, ~1 means the
    # drive is still delivering at its initial rate
    n = len(hist.t)
    verdict = ""
    if n > 20:
        i1, i2 = n // 10, n // 2
        early = ((hist.Eabs[i1] - hist.Eabs[0]) / (hist.t[i1] - hist.t[0])
                 if hist.t[i1] > hist.t[0] else float("nan"))
        late = ((hist.Eabs[-1] - hist.Eabs[i2]) / (hist.t[-1] - hist.t[i2])
                if hist.t[-1] > hist.t[i2] else float("nan"))
        if early and early == early:
            r = late / early
            verdict = (f" — late/early dE/dt = {r:.2f}: "
                       + ("SATURATED (H2 holds here)" if r < 0.15 else
                          f"NOT saturated; f$_{{abs}}$ floors near {min(f[n//2:]):.2f} "
                          "rather than 0, so the drive keeps delivering"))
    ax.set_title("Cumulative coupled energy" + verdict, loc="left", fontweight="bold")
    lpp.style_axes(ax)

    if have_Tf:
        ax = axes[2]
        ax.plot(t_ps, hist.Tlocalfrac, color=lpp.C_TARGET)
        lpp.label_line(ax, t_ps[-1], hist.Tlocalfrac[-1], " T$_{localfrac}$",
                       lpp.C_TARGET)
        ax.set_ylim(0, 1.05)
        ax.set_ylabel("T$_{localfrac}$")
        ax.set_title("Fraction of the plasma (n$_e^2$-weighted) with a MEASURED T$_e$ "
                     "rather than the floor — gate G5", loc="left", fontweight="bold")
        lpp.style_axes(ax)

    axes[-1].set_xlabel("t  [ps]"
                        + (f"    (1/ω$_{{ci0}}$ = {sc.wci0_inv*1e12:.3g} ps)"
                           if sc.wci0_inv else ""))
    lpp.stamp(fig, cfg, sc, extra=f"{len(hist)} LASERDEP applications")
    return lpp.savefig(fig, "laser_history.png", run_id=run_id)


def profile_figure(cfg, sc, path, run_id):
    import matplotlib.pyplot as plt

    tab = lpio.read_profile_table(path)
    if not tab:
        print(f"  (profile table {path} is empty)")
        return None
    ne, H, Pabs = tab["n_e"], tab["H"], tab["P_abs"]
    zc = tab.get("z", list(range(len(ne))))
    z_de = [v / sc.de_ref for v in zc]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11.0, 6.0), sharex=True)
    fig.subplots_adjust(hspace=0.3)

    ax1.plot(z_de, [v / sc.n_cr for v in ne], color=lpp.C_TARGET)
    lpp.label_line(ax1, z_de[len(z_de) // 2], max(v / sc.n_cr for v in ne),
                   " n$_e$ (as the ray measured it)", lpp.C_TARGET)
    ax1.axhline(1.0, color=lpp.INK, ls=":", lw=1.0)
    ax1.text(0.004, 1.0, " n$_{cr}$", transform=ax1.get_yaxis_transform(),
             va="bottom", fontsize=8, color=lpp.INK)
    ax1.set_yscale("log")
    ax1.set_ylabel("n$_e$ / n$_{cr}$")
    step = os.path.basename(path).split("_")[-1].split(".")[0]
    ax1.set_title(f"Per-cell deposition profile, step {step}"
                  + ("  — the clean read: later dumps drift as the kicks move "
                     "electrons" if step.strip("0") == "" else
                     "  — NOTE: not step 0, so the profile has already drifted"),
                  loc="left", fontweight="bold")
    lpp.style_axes(ax1)

    ax2.plot(z_de, Pabs, color=lpp.C_LASER)
    lpp.label_line(ax2, z_de[len(z_de) // 2], max(Pabs) if Pabs else 0,
                   " P$_{abs}$", lpp.C_LASER)
    ax2.set_yscale("log")
    ax2.set_ylabel("P$_{abs}$  [W/m³]")
    ax2.set_xlabel(f"z  [d$_e$ at {sc.length_scale} density]")
    ax2.set_title("Where the energy actually lands — coronal gradient vs the "
                  "critical surface", loc="left", fontweight="bold")
    lpp.style_axes(ax2)

    lpp.stamp(fig, cfg, sc, extra=os.path.basename(path))
    return lpp.savefig(fig, "laser_profile.png", run_id=run_id)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--step", type=int, default=None,
                    help="which profile dump to plot (default: the earliest, i.e. "
                         "the only one that has not drifted)")
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args()

    cfg = lpconfig.load(args.run_dir)
    rid = lpconfig.run_id(cfg)
    sc = lpconfig.derive(cfg)
    rd = cfg["_run_dir"]

    hist = lpio.laserdep_history(rd)
    if not len(hist):
        print(f"no LASERDEP lines in {rd}/run.log.\n"
              "  - has the run started? (check progress.log)\n"
              "  - is warpx.verbose = 1 in the deck? (make_inputs.py always sets it)\n"
              "  - does the deck have a laser_deposition.species line?")
        return 1

    P_inc = lpio.incident_power(sc, cfg)
    f = hist.f_abs(P_inc)
    t_off = hist.shutoff_time()

    print(f"LASER REPORT — {rid}  ({len(hist)} applications, "
          f"steps {hist.step[0]}..{hist.step[-1]}, "
          f"t = {hist.t[-1]*1e12:.4g} ps)")
    print(f"  incident power        {P_inc:.4g} W per absent dim "
          f"(I0 = {sc.intensity:.4g} W/m^2)")
    print(f"  f_abs  peak           {max(f):.4f}   at t = "
          f"{hist.t[f.index(max(f))]*1e12:.4g} ps")
    print(f"  f_abs  final          {f[-1]:.4f}")
    print(f"  P_abs  peak           {hist.Pabs_peak:.4g} W")
    print(f"  E_abs  final          {hist.Eabs_final:.4g} J per absent dim")
    if t_off is not None:
        msg = f"  shutoff (½ peak)      {t_off*1e12:.4g} ps"
        if sc.wci0_inv:
            msg += f"  = {t_off/sc.wci0_inv:.3g} /wci0"
        print(msg)
        if sc.wci0_inv and t_off / sc.wci0_inv < 1.0:
            print("      *** the drive shuts off in under ONE gyroperiod. Schaeffer "
                  "finds formation\n      needs >~ 1 /wci0 of drive, so this run is "
                  "unlikely to form a shock however\n      long it continues "
                  "(TEST_PLAN.md H4).")
    else:
        print("  shutoff               not reached within the run")

    # --- energy bookkeeping: what the coupled energy implies for the piston ---
    areal_i = sc.areal_ne                      # ions per m^2 (Z = 1)
    if areal_i > 0:
        # 1D: E_abs is J/m^2 so this is directly energy per unit area
        e_per_ion = hist.Eabs_final / areal_i if sc.dims == 1 else float("nan")
        if e_per_ion == e_per_ion:
            print(f"  energy per target ion {e_per_ion/lpunits.QE/1e3:.4g} keV "
                  f"(areal n_e = {areal_i:.4g} m^-2)")
            # electron thermal energy -> ablation sound speed -> piston estimate
            kT = (2.0 / 3.0) * e_per_ion
            theta = kT / lpunits.ME_C2_J
            cs = lpunits.sound_speed(theta, sc.mass_ratio)
            print(f"  implied T_e,ab        {kT/lpunits.QE/1e3:.4g} keV "
                  f"(theta = {theta:.4g})  ->  C_s = {cs/lpunits.C:.4g} c")
            if sc.vA:
                print(f"  implied piston        v_p ~ 3 C_s = "
                      f"{3*cs/sc.vA:.3g} v_A  (M_ms would be "
                      f"{3*cs/sc.v_ms:.3g})")
                if 3 * cs / sc.v_ms < 1.0:
                    print("      *** SUBSONIC piston: no shock can form at these "
                          "parameters, however long\n      the run. This is exactly "
                          "the failure that was retracted upstream.")

    if any(v == v for v in hist.Tlocalfrac):
        tf = [v for v in hist.Tlocalfrac if v == v]
        print(f"  Tlocalfrac            {tf[0]:.3f} -> {tf[-1]:.3f} "
              "(fraction with a measured, not floored, T_e)")

    tables = lpio.profile_tables(rd)
    print(f"  profile dumps         {len(tables)}"
          + (f"  ({', '.join(os.path.basename(t) for t in tables[:4])}"
             + (" ..." if len(tables) > 4 else "") + ")" if tables else
             "  (set laser.profile_intervals in config.yaml to get one)"))

    if not args.no_figure:
        print()
        history_figure(cfg, sc, hist, rid, rd)
        if tables:
            pick = tables[0]
            if args.step is not None:
                want = f"_{args.step:06d}.txt"
                pick = next((t for t in tables if t.endswith(want)), tables[0])
            profile_figure(cfg, sc, pick, rid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
