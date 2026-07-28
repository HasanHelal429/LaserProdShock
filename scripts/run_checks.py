#!/usr/bin/env python3
"""Bring-up checks for a run: derived scales, the numerical gates, and a figure.

Works **before** any simulation output exists — that is the point. A laser run has two
ways to be silently wrong before it starts (the target is transparent because it sits
too far below n_cr, or omega_pe*dt is over the limit at the compression the run will
reach), and both are visible in the config alone.

    python scripts/run_checks.py runs/<ID>
    python scripts/run_checks.py runs/<ID> --no-figure

Writes ``media/<ID>/checks.png``:

  1. the initial density profile, drawn from the deck's **own** density_function, with
     the critical surface and the injection face marked;
  2. the predicted IB absorption K(z) and the cumulative optical depth tau(z) as two
     stacked panels (never a dual axis);
  3. the gate table G1-G7, each row carrying a colour, a glyph and a word;
  4. once the run has produced output, the laser history and the G6 energy closure.

Exit status is 1 if any gate FAILs, so it can gate a launch in a script.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import deck as lpdeck       # noqa: E402
from laserprod import io as lpio           # noqa: E402
from laserprod import plotting as lpp      # noqa: E402


def _linspace(a, b, n):
    if n < 2:
        return [a]
    step = (b - a) / (n - 1)
    return [a + i * step for i in range(n)]


def make_figure(cfg, sc, gates, run_dir, run_id):
    import matplotlib.pyplot as plt

    hist = lpio.laserdep_history(run_dir)
    has_output = len(hist) > 0

    # Rows: density, K(z), tau(z), then either the gate table (pre-run) or the laser
    # history + energy closure (post-run, with the gates promoted to their own figure
    # so nothing gets cropped).
    heights = ([1.5, 1.0, 0.85, 1.15, 1.15] if has_output
               else [1.6, 1.05, 0.9, 0.05 * 7 + 0.9])
    fig = plt.figure(figsize=(12.0, sum(heights) * 2.05 + 0.7))
    gs = fig.add_gridspec(len(heights), 1, height_ratios=heights, hspace=0.42)

    # --- 1. density profile, sampled from the deck expression itself ---
    z_de = _linspace(sc.domain_lo / sc.de_ref, sc.domain_hi / sc.de_ref, 1200)
    z_m = [v * sc.de_ref for v in z_de]
    n_t = lpdeck.sample_density(cfg, "target", z_m)
    n_a = lpdeck.sample_density(cfg, "ambient", z_m)
    ax0 = fig.add_subplot(gs[0])
    lpp.density_panel(ax0, z_de, n_t, n_a, sc, cfg)

    # --- 2. predicted absorption: K(z) then cumulative tau(z) ---
    n_tot = [a + b for a, b in zip(n_t, n_a)]
    axK = fig.add_subplot(gs[1], sharex=ax0)
    axT = fig.add_subplot(gs[2], sharex=ax0)
    lpp.absorption_panel(axK, axT, z_de, n_tot, sc, cfg)
    axK.tick_params(labelbottom=False)
    ax0.tick_params(labelbottom=False)
    ax0.set_xlabel("")
    axK.set_xlabel("")

    # --- 3. gates (pre-run) or the laser history (post-run) ---
    axg = fig.add_subplot(gs[3])
    if not has_output:
        lpp.gate_panel(axg, gates)
    else:
        # laser history: absorbed fraction (top) and cumulative energy, stacked
        P_inc = lpio.incident_power(sc, cfg)
        f = hist.f_abs(P_inc)
        t_ps = [v * 1e12 for v in hist.t]
        axg.plot(t_ps, f, color=lpp.C_LASER)
        axg.set_ylabel("f$_{abs}$ = P$_{abs}$/P$_{inc}$")
        axg.set_title("Laser history — the SELF-LIMITING shutoff "
                      "(K ∝ n$_e^2$T$_e^{-3/2}$)", loc="left", fontweight="bold")
        t_off = hist.shutoff_time()
        if t_off:
            axg.axvline(t_off * 1e12, color=lpp.INK, ls=":", lw=1.2)
            axg.text(t_off * 1e12, 0.95, " shutoff (½ peak)", va="top",
                     transform=axg.get_xaxis_transform(), fontsize=8,
                     color=lpp.INK)
        lpp.label_line(axg, t_ps[-1] if t_ps else 0, f[-1] if f else 0,
                       " f$_{abs}$", lpp.C_LASER)
        axg.set_xlabel("t  [ps]")
        lpp.style_axes(axg)

        # --- 4. energy closure (gate G6) ---
        ax6 = fig.add_subplot(gs[4])
        tp, ke = lpio.particle_energy(run_dir)
        E_las = [(v) for v in hist.Eabs]
        ax6.plot([v * 1e12 for v in hist.t], E_las, color=lpp.C_LASER,
                 label="tracer E$_{abs}$ (grid-heating immune)")
        if tp and ke:
            ke0 = ke[0]
            ax6.plot([v * 1e12 for v in tp], [v - ke0 for v in ke],
                     color=lpp.C_TARGET, label="particle KE gain")
        tf, fe = lpio.field_energy(run_dir)
        if tf and fe:
            fe0 = fe[0]
            ax6.plot([v * 1e12 for v in tf], [v - fe0 for v in fe],
                     color=lpp.C_FOURTH, lw=1.3, label="field energy gain")
        ax6.set_xlabel("t  [ps]")
        ax6.set_ylabel("energy  [J per absent dim]")
        ax6.set_title("Gate G6 — energy closure. The gap between the tracer and the "
                      "particles IS the grid-heating budget.",
                      loc="left", fontweight="bold")
        ax6.legend(loc="upper left")
        lpp.style_axes(ax6)

    if has_output:
        # gates get their own figure when the run has output, so nothing is cropped
        figg, axgg = plt.subplots(figsize=(12.0, 0.42 * len(gates) + 0.9))
        lpp.gate_panel(axgg, gates)
        lpp.stamp(figg, cfg, sc)
        lpp.savefig(figg, "gates.png", run_id=run_id)

    lpp.stamp(fig, cfg, sc,
              extra=(f"{lpio.last_step(run_dir)} steps run" if has_output
                     else "PRE-RUN (no output yet)"))
    return lpp.savefig(fig, "checks.png", run_id=run_id)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("--no-figure", action="store_true")
    args = ap.parse_args()

    cfg = lpconfig.load(args.run_dir)
    rid = lpconfig.run_id(cfg)
    sc = lpconfig.derive(cfg)

    print(sc.pretty())

    warns = lpconfig.validate(cfg)
    print()
    if warns:
        for w in warns:
            print(f"WARN  {w}")
    else:
        print("structural validation: OK")

    gates = lpconfig.gates(cfg, sc)
    print(f"\nGATES ({lpconfig.gate_summary(gates)}):")
    for g in gates:
        val = "" if g.value is None else f"{g.value:.4g}"
        print(f"  {g.key}  [{g.status.upper():4s}] {g.label:34s} {val}")
        print(f"        {' '.join(str(g.detail).split())}")

    # --- a couple of physics sanity reads that are easy to get wrong ---
    print("\nPHYSICS SANITY:")
    print(f"  target sits at {sc.n_targ_over_ncr:.4g} n_cr — "
          + ("OVERDENSE: the beam turns inside it" if sc.n_targ_over_ncr > 1 else
             "underdense: the beam passes through"))
    print(f"  predicted single-pass tau through the flat top = {sc.tau_est:.4g} "
          f"(absorption depth 1/K = {sc.abs_depth_targ/sc.de_ref:.3g} d_e); "
          f"f_abs ~ {sc.f_abs_est:.3f}")
    if sc.f_abs_est < 0.01:
        print("  *** the target is essentially TRANSPARENT. A laser run is measured "
              "against n_cr:\n      raise density_over_ncr, Z_eff*coulomb_log, or "
              "the thickness.")
    if sc.f_abs_amb is not None:
        print(f"  ambient traverse eats {sc.f_abs_amb*100:.4g}% of the beam "
              + ("(upstream stays cold — good)" if sc.f_abs_amb < 0.02 else
                 "*** the upstream is being PRE-HEATED before the shock arrives"))
    if sc.n_gyroperiods is not None:
        phase = int(cfg.get("meta", {}).get("phase", 0) or 0)
        print(f"  run covers {sc.n_gyroperiods:.3g} gyroperiods "
              f"({sc.steps_per_wci0:.0f} steps each)")
        # Only a shock run is obliged to reach Schaeffer's timescales; a boundary or
        # ablation test is not, and flagging it there would train the reader to ignore
        # the warning that matters.
        if phase >= 2 and sc.n_gyroperiods < 2.5:
            print("  *** shorter than t*_2 = 2.5 /wci0: too short for a shock to "
                  "separate from the piston (Schaeffer's t*_1/t*_2/t*_3 = 1/2.5/5).")
        elif phase < 2:
            print("      (a shock needs t*_2 = 2.5 /wci0; not required of a phase-"
                  f"{phase} test)")
    if sc.rho_i0 is not None:
        span = (sc.domain_hi - sc.domain_lo) / sc.rho_i0
        print(f"  domain spans {span:.3g} rho_i0 (rho_i0 = "
              f"{sc.rho_i0/sc.de_ref:.1f} d_e)")

    if not args.no_figure:
        print()
        make_figure(cfg, sc, gates, cfg["_run_dir"], rid)

    return 1 if any(g.status == "fail" for g in gates) else 0


if __name__ == "__main__":
    raise SystemExit(main())
