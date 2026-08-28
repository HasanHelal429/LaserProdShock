#!/usr/bin/env python3
"""Measure plume T_e across the WarpX mass-ratio scan.

    /opt/anaconda3/envs/physics/bin/python scripts/mass_ratio_scan.py

THE QUESTION. Every WarpX Phase-4 leg sits at 0.26-0.38x FLASH's plume T_e in raw eV while
PSC -- same reduced mass ratio, same normalisation convention -- sits at 0.87-0.96x. Two
readings survive and they predict opposite things:

  similarity : mu^(1/3) = sqrt(mu)^(2/3) = 2.638 is EXACTLY the factor that leaves the
               inverse-bremsstrahlung optical depth invariant when lengths scale by
               sqrt(mu), so T_e should track T_ss = 823/mu^(1/3) -- a 2.52x spread here.
  invariance : the paper's own m_p/m_e = {100, 400} scan reports "good convergence", which
               a 1.587x shift would exclude -- so T_e should not move at all.

They differ by 20x relative to the measured 12% run-to-run noise floor, so this is decidable
from three short runs and NO cross-code normalisation is involved.

WHY THE BINNING IS PER-LEG. xcode_compare hardcodes edges at -50..2450 d_e, which is the
mr100 domain. d_i0/d_e = sqrt(mass_ratio/A_Al) is 5, 10 and 20 across the scan and the
domains were rescaled with it, so a shared d_e grid would cover a quarter of mr400 and
overrun mr25. Every leg is therefore binned on its OWN zeta = z/d_i0, which is the axis on
which the three runs are geometrically identical by construction.
"""
import glob, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warnings; warnings.filterwarnings("ignore")

QE=1.602176634e-19; ME=9.1093837015e-31; MP=1.67262192369e-27
EPS0=8.8541878128e-12; C=2.99792458e8; LAM0=1.064e-6
N_CR=EPS0*ME*(2*np.pi*C/LAM0)**2/QE**2; DE_CR=LAM0/(2*np.pi)
A_AL=26.9815; Z_AL=13.0; TE_REF=823.0
MRR=A_AL*MP/ME                                   # real m_Al/m_e

# plume band -- the same one used for PSC, and the only region TEST_PLAN 12.6 admits
NLO, NHI = 0.05, 1.0

def leg(run_dir, mass_ratio, lo_de, hi_de, nbin=400):
    import yt
    from laserprod import io as lpio
    di0 = DE_CR*np.sqrt(mass_ratio/A_AL)          # PROTON skin depth, the paper's d_i0
    cs0 = np.sqrt(Z_AL*TE_REF*QE/(mass_ratio*ME))
    mu  = MRR/mass_ratio
    edges = np.linspace(lo_de*DE_CR/di0, hi_de*DE_CR/di0, nbin+1)
    dz = (edges[1]-edges[0])*di0
    ps = lpio.plotfiles(run_dir, "diag1")
    if not ps: return None
    ds = yt.load(ps[-1]); ad = ds.all_data()
    have = {f[0] for f in ds.field_list}
    s = next((n for n in ("targ_electrons","electrons") if n in have), None)
    if s is None: return None
    z = np.asarray(ad[(s,"particle_position_x")])/di0
    w = np.asarray(ad[(s,"particle_weight")])
    u = np.stack([np.asarray(ad[(s,f"particle_momentum_{c}")]) for c in "xyz"],axis=1)/(ME*C)
    sw,_ = np.histogram(z,bins=edges,weights=w); ok = sw>0
    ne = sw/dz/N_CR
    s2,_ = np.histogram(z,bins=edges,weights=w*(u*u).sum(axis=1))
    mu2 = np.where(ok, s2/np.where(ok,sw,1), np.nan)
    dr = np.zeros_like(mu2)
    for k in range(3):
        sk,_ = np.histogram(z,bins=edges,weights=w*u[:,k])
        mk = np.where(ok, sk/np.where(ok,sw,1), 0.0); dr += mk*mk
    Te = (mu2-dr)/3.0*511e3
    b = (ne>NLO)&(ne<NHI)&np.isfinite(Te)
    return dict(tau=float(ds.current_time)/(di0/cs0), mu=mu, tss=TE_REF/mu**(1/3.),
                Te=float(np.average(Te[b],weights=ne[b])), ncell=int(b.sum()),
                di0_de=di0/DE_CR, t_ps=float(ds.current_time)*1e12)

LEGS = [("P4_lez_kin_mr25",  25,   26.9815*25,     -25.0,   1223.0),
        ("P4_lez_kin_mr100", 100,  26.9815*100,    -50.0,   2450.0),
        ("P4_lez_kin_mr400", 400,  26.9815*400,   -100.0,   4900.0),
        # The real mass ratio: real aluminium against a real electron, no transform at all.
        # It anchors the scan, which every cross-code statement had been extrapolating to
        # mu = 1 -- a factor 4.6 past the top rung (RESULTS 2026-08-27 evening).
        ("P4_lez_kin_mrreal", 1836, 49542.0,     -214.2514, 10497.7486)]

def figure(res, out="mass_ratio_scan.png", run_id="P4_lez_kin_mrreal",
           xcode=(("FLASH", 647.0, 0.870), ("PSC 511 keV", 508.8, 0.5833))):
    """Two panels: the mu-sweep against mu^(1/3), and the raw-eV cross-code comparison.

    Panel (b) is the one only the real-mass leg makes possible -- every other WarpX leg has to
    be reduced before it can be set beside FLASH or PSC, and the reduction is the thing under
    test. Here all three carry a real aluminium ion and the eV are directly comparable.
    """
    import matplotlib.pyplot as plt
    from laserprod import plotting as lpp
    res = sorted(res, key=lambda r: r["mpme"])
    b = next(x for x in res if x["mpme"] == 100)
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.4, 4.5),
                                 gridspec_kw=dict(width_ratios=[1.35, 1.0], wspace=0.28))

    # (a) the sweep
    lpp.style_axes(ax)
    x = np.array([r["mpme"] for r in res]); y = np.array([r["Te"] for r in res])
    xs = np.logspace(np.log10(x.min() * 0.75), np.log10(x.max() * 1.35), 200)
    ax.plot(xs, b["Te"] * (xs / 100.0) ** (1 / 3.), color=lpp.INK_MUTED, lw=1.2,
            ls=(0, (5, 3)), zorder=1)
    # label the guide at the LOW-mass end -- the high end is crowded by the mrreal point,
    # its prediction marker and its label
    ax.annotate(r"$T_e \propto \mu^{1/3}$", xy=(xs[0], b["Te"] * (xs[0] / 100) ** (1 / 3.)),
                xytext=(6, -14), textcoords="offset points", ha="left",
                color=lpp.INK_MUTED, fontsize=9, style="italic")
    ax.plot(x, y, color=lpp.C_LASER, lw=1.6, alpha=0.9, zorder=2)
    ax.scatter(x[:-1], y[:-1], s=62, color=lpp.C_LASER, edgecolor="white", lw=1.2, zorder=4)
    ax.scatter(x[-1:], y[-1:], s=145, marker="*", color=lpp.C_TARGET,
               edgecolor="white", lw=1.1, zorder=5)
    for r in res:
        lab = r["rid"].replace("P4_lez_kin_", "")
        ax.annotate(f"{lab}\n{r['Te']:.1f} eV", xy=(r["mpme"], r["Te"]),
                    xytext=(0, 11 if lab != "mrreal" else 13), textcoords="offset points",
                    ha="center", fontsize=7.8, linespacing=1.25,
                    color=(lpp.C_TARGET if lab == "mrreal" else lpp.INK_MUTED),
                    fontweight=("bold" if lab == "mrreal" else "normal"))
    pred = b["Te"] * (res[-1]["mpme"] / 100.0) ** (1 / 3.)
    ax.scatter([res[-1]["mpme"]], [pred], s=70, facecolor="none",
               edgecolor=lpp.INK_MUTED, lw=1.4, zorder=4)
    ax.annotate(f"$\\mu^{{1/3}}$ predicts\n{pred:.0f} eV", xy=(res[-1]["mpme"], pred),
                xytext=(-11, -14), textcoords="offset points", ha="right", va="top",
                fontsize=8, color=lpp.INK_MUTED, linespacing=1.25)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel(r"$m_p/m_e$ of the leg")
    ax.set_ylabel(r"plume $T_e$  [eV]")
    ax.set_xticks(x); ax.set_xticklabels([f"{v:g}" for v in x])
    ax.set_yticks([120, 160, 250, 400, 600]); ax.set_yticklabels(["120", "160", "250", "400", "600"])
    ax.minorticks_off(); ax.tick_params(labelsize=8.6, colors=lpp.INK_MUTED)
    ax.set_title(f"(a) the sweep now reaches real mass\n"
                 f"measured {res[-1]['Te']:.1f} eV vs {pred:.0f} predicted "
                 f"({abs(res[-1]['Te']/pred-1)*100:.1f}%, floor 13.5%)",
                 fontsize=10, color=lpp.INK, pad=9, linespacing=1.3)

    # (b) raw eV
    lpp.style_axes(bx, grid_axis="y")
    names = [n for n, _, _ in xcode] + ["WarpX mrreal"]
    vals = [t for _, t, _ in xcode] + [res[-1]["Te"]]
    fabs = [f for _, _, f in xcode] + [None]
    cols = [lpp.C_FOURTH, lpp.C_AMBIENT, lpp.C_TARGET]
    bx.bar(range(len(vals)), vals, color=cols, width=0.6, edgecolor="white", linewidth=1.2)
    for i, (v, f) in enumerate(zip(vals, fabs)):
        bx.annotate(f"{v:.1f} eV", xy=(i, v), xytext=(0, 5), textcoords="offset points",
                    ha="center", fontsize=9, fontweight="bold", color=lpp.INK)
    bx.set_xticks(range(len(names))); bx.set_xticklabels(names, fontsize=8.8)
    bx.tick_params(labelsize=8.6, colors=lpp.INK_MUTED)
    bx.set_ylabel(r"plume $T_e$  [eV]")
    bx.set_ylim(0, max(vals) * 1.22)
    bx.set_title("(b) raw eV, no normalisation\nall three on a REAL aluminium ion",
                 fontsize=10, color=lpp.INK, pad=9, linespacing=1.3)
    bx.annotate(f"WarpX/PSC = {vals[2]/vals[1]:.3f}", xy=(1.5, max(vals) * 1.06),
                ha="center", fontsize=8.6, color=lpp.INK_MUTED)

    fig.text(0.5, -0.03,
             "All legs at $\\tau_{\\rm own}$ = 5.39, plume band 0.05 < $n_e/n_{cr}$ < 1, n-weighted, "
             "each leg on its own $\\zeta$.   Panel (b) $\\langle f_{\\rm abs}\\rangle$: "
             "FLASH 0.870, PSC 0.583, WarpX 0.623.",
             ha="center", fontsize=8, color=lpp.INK_MUTED)
    lpp.savefig(fig, out, run_id=run_id)


if __name__ == "__main__":
    print(f"plume band {NLO} < n_e/n_cr < {NHI}, n-weighted, each leg on its OWN zeta\n")
    print(f"{'leg':10s} {'m_p/m_e':>8s} {'mu':>7s} {'d_i0/d_e':>9s} {'tau_own':>8s} "
          f"{'t (ps)':>8s} {'T_ss':>7s} {'plume Te':>9s} {'Te/T_ss':>8s} {'cells':>6s}")
    res = []
    for rid, mpme, mr, lo, hi in LEGS:
        r = leg(f"runs/P4/{rid}", mr, lo, hi)
        if r is None: print(f"{rid:10s}  no plotfiles"); continue
        r.update(rid=rid, mpme=mpme); res.append(r)
        print(f"{rid.replace('P4_lez_kin_',''):10s} {mpme:8d} {r['mu']:7.2f} {r['di0_de']:9.1f} "
              f"{r['tau']:8.2f} {r['t_ps']:8.2f} {r['tss']:7.1f} {r['Te']:9.1f} "
              f"{r['Te']/r['tss']:8.3f} {r['ncell']:6d}")
    if len(res) >= 3:
        b = next(x for x in res if x["mpme"] == 100)
        print(f"\n{'':10s} {'measured Te/Te(mr100)':>34s}   {'similarity predicts':>20s}")
        for r in res:
            print(f"{r['rid'].replace('P4_lez_kin_',''):10s} {r['Te']/b['Te']:34.3f}   "
                  f"{r['tss']/b['tss']:20.3f}")
        figure(res)
        spread = max(x["Te"] for x in res)/min(x["Te"] for x in res)
        print(f"\nmeasured spread {spread:.2f}x   |   similarity predicts 2.52x   |   "
              f"invariance predicts 1.00x (noise floor 1.12x)")
