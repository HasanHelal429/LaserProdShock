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

LEGS = [("P4_lez_kin_mr25",  25,  26.9815*25,   -25,  1223),
        ("P4_lez_kin_mr100", 100, 26.9815*100,  -50,  2450),
        ("P4_lez_kin_mr400", 400, 26.9815*400, -100,  4900)]

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
    if len(res) == 3:
        b = next(x for x in res if x["mpme"] == 100)
        print(f"\n{'':10s} {'measured Te/Te(mr100)':>34s}   {'similarity predicts':>20s}")
        for r in res:
            print(f"{r['rid'].replace('P4_lez_kin_',''):10s} {r['Te']/b['Te']:34.3f}   "
                  f"{r['tss']/b['tss']:20.3f}")
        spread = max(x["Te"] for x in res)/min(x["Te"] for x in res)
        print(f"\nmeasured spread {spread:.2f}x   |   similarity predicts 2.52x   |   "
              f"invariance predicts 1.00x (noise floor 1.12x)")
