#!/usr/bin/env python3
"""Three-way FLASH / kinetic-PIC / hybrid-PIC comparison on common normalised axes.

    /opt/anaconda3/envs/physics/bin/python scripts/xcode_compare.py

Writes ``media/xcode/`` : ``profiles.png``, ``history.png`` and a printed table.

WHY THE AXES ARE NORMALISED (TEST_PLAN 12.2). FLASH runs real aluminium,
m_Al/m_e = 49535. The WarpX legs run the paper's REDUCED ratio, 2698 = 26.98 x 100.
Only the ION mass differs -- WarpX keeps real c, real m_e, real lambda_0, and therefore
real n_cr and real d_e = lambda_0/2pi = 0.1693 um. The consequence is NOT that lengths are
fine and times are wrong; it is that the ablative flow itself is rescaled:

    C_S ∝ m_i^(-1/2)  ->  faster by sqrt(18.36) = 4.285
    d_i0 = c/omega_pi ∝ m_i^(1/2)  ->  smaller by 4.285
    d_i0/C_S0 ∝ m_i  ->  smaller by 18.36

So the plume is 4.285x more COMPACT in real microns and evolves 18.36x faster in real
seconds, and both are absorbed exactly by measuring z in each code's own d_i0 and t in
each code's own d_i0/C_S0. That is the only map on which the two codes describe the same
flow, and it is why overlaying a micron axis in this phase is a 4.29x error.

d_i0 here is the paper's: the PROTON skin depth at n_cr, with that code's proton mass.
C_S0 = sqrt(Z k T_e0 / m_i) at the reference T_e0 = 823 eV (Manheimer steady state) with
the ALUMINIUM mass and Z = 13. That mixed convention is the paper's, and it is the one the
run configs were built on -- it reproduces their "0.1 ns = 2.69 ion response times".

WHAT IS COMPARABLE AND WHAT IS NOT.
  comparable : n_e/n_cr, T_e and T_i in eV, v/C_S0, the shape of P_abs, and every
               dimensionless ratio.
  NOT        : any length or time in physical units; the absorbed FLUENCE (WarpX delivers
               18.36x less J/cm^2 because it runs 18.36x less real time at the same
               absolute intensity); and the overdense interior, because the WarpX target
               is 10 n_cr where FLASH's is 795 n_cr (decision D5).

ALWAYS QUOTE THE ABSORBED FRACTION BESIDE ANY TEMPERATURE. T_e,SS ~ I_abs^(2/3), so a leg
that absorbs less is EXPECTED to be cooler and the comparison is meaningless without it.
Measured over the full run: FLASH 0.870, kinetic 0.769, hybrid(1e-3 bg) 0.364. The hybrid
absorbs 2.1x less than the kinetic and its instantaneous f_abs collapses 0.94 -> 0.37, so
its temperature must be read against its own absorbed flux, not against the kinetic's.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np                          # noqa: E402

# ---------------------------------------------------------------------------------------
# Physical constants and the unit map, derived rather than asserted.
# ---------------------------------------------------------------------------------------
QE   = 1.602176634e-19
ME   = 9.1093837015e-31
MP   = 1.67262192369e-27
AMU  = 1.66053906660e-27
EPS0 = 8.8541878128e-12
C    = 2.99792458e8
NA   = 6.02214076e23
KELV = 11604.518                # K per eV

LAM0   = 1.064e-6
N_CR   = EPS0 * ME * (2 * np.pi * C / LAM0) ** 2 / QE ** 2
DE_CR  = LAM0 / (2 * np.pi)
A_AL   = 26.9815
Z_AL   = 13.0
TE_REF = 823.0                  # eV, Manheimer steady state for 1e13 W/cm^2 at 1.064 um

MASS_RATIO_SIM  = 2698.0                     # m_Al/m_e in the WarpX legs (paper's)
MASS_RATIO_REAL = A_AL * MP / ME             # m_Al/m_e for real aluminium
RESCALE         = MASS_RATIO_REAL / MASS_RATIO_SIM   # 18.36


def di0(m_proton):
    """Proton skin depth c/omega_pi at n_cr, for the given proton mass."""
    return C / np.sqrt(N_CR * QE ** 2 / (EPS0 * m_proton))


def cs0(m_ion):
    """sqrt(Z k T_e0 / m_i) at T_e0 = 823 eV."""
    return np.sqrt(Z_AL * TE_REF * QE / m_ion)


# FLASH: real proton, real aluminium.
DI0_F = di0(MP)
CS0_F = cs0(A_AL * AMU)
TAU_F = DI0_F / CS0_F
# WarpX: the paper's reduced proton (100 m_e) and the correspondingly light aluminium.
DI0_W = di0(100.0 * ME)
CS0_W = cs0(MASS_RATIO_SIM * ME)
TAU_W = DI0_W / CS0_W

X_IFACE = 50.0e-4               # cm; the FLASH solid/vacuum interface (sim_targetHeight)


def banner():
    print("=" * 86)
    print("UNIT MAP  (derived, not asserted)")
    print(f"  n_cr = {N_CR:.4e} m^-3     d_e = lambda_0/2pi = {DE_CR*1e6:.4f} um")
    print(f"  m_Al/m_e  real {MASS_RATIO_REAL:.0f}   sim {MASS_RATIO_SIM:.0f}   "
          f"rescale {RESCALE:.3f}   sqrt {np.sqrt(RESCALE):.4f}")
    print(f"  FLASH : d_i0 = {DI0_F*1e6:.4f} um   C_S0 = {CS0_F:.4e} m/s   "
          f"d_i0/C_S0 = {TAU_F*1e12:.3f} ps")
    print(f"  WarpX : d_i0 = {DI0_W*1e6:.4f} um = {DI0_W/DE_CR:.2f} d_e   "
          f"C_S0 = {CS0_W:.4e} m/s   d_i0/C_S0 = {TAU_W*1e12:.4f} ps")
    print(f"  ratios: d_i0 {DI0_F/DI0_W:.3f}   C_S0 {CS0_W/CS0_F:.3f}   "
          f"time unit {TAU_F/TAU_W:.3f}  (all = 18.36 or its sqrt)")
    print("=" * 86)


# ---------------------------------------------------------------------------------------
# FLASH
# ---------------------------------------------------------------------------------------
def flash_series(run_dir, base):
    """Leaf-block profiles from every plotfile, on the normalised axes."""
    import h5py
    out = []
    for p in sorted(glob.glob(os.path.join(run_dir, f"{base}_hdf5_plt_cnt_[0-9]*"))):
        with h5py.File(p, "r") as h:
            m = h["node type"][:] == 1
            bb = h["bounding box"][:][m]
            names = [n[0].decode().strip() for n in h["unknown names"][:]]
            v = {n: h[n][:][m][:, 0, 0, :] for n in names}
            nxb = v[names[0]].shape[1]
            x = np.concatenate([np.linspace(b[0, 0], b[0, 1], nxb + 1)[:-1]
                                + (b[0, 1] - b[0, 0]) / nxb / 2 for b in bb])
            o = np.argsort(x)
            t = float(dict((k.decode().strip(), val)
                           for k, val in h["real scalars"][:])["time"])
        x = x[o] * 1e-2                                   # cm -> m
        v = {k: np.concatenate(val)[o] for k, val in v.items()}
        ne = v["dens"] * v["ye"] * NA * 1e6               # g/cm^3 -> m^-3
        out.append(dict(t=t, tau=t / TAU_F,
                        zeta=(x - X_IFACE * 1e-2) / DI0_F,
                        ne=ne / N_CR,
                        Te=v["tele"] / KELV, Ti=v["tion"] / KELV,
                        v=v["velx"] * 1e-2 / CS0_F,
                        depo=v["depo"]))
    return out


# ---------------------------------------------------------------------------------------
# WarpX
# ---------------------------------------------------------------------------------------
def warpx_fields(run_dir):
    """n_e/n_cr (and Te when the run carries the field) at the diag_fields cadence."""
    import yt
    from laserprod import io as lpio
    out = []
    for p in lpio.plotfiles(run_dir, "diag_fields"):
        ds = yt.load(p)
        g = ds.covering_grid(0, ds.domain_left_edge, ds.domain_dimensions)
        fl = {f[1] for f in ds.field_list if f[0] == "boxlib"}
        z = np.linspace(float(ds.domain_left_edge[0]), float(ds.domain_right_edge[0]),
                        int(ds.domain_dimensions[0]) + 1)
        z = 0.5 * (z[1:] + z[:-1])
        # Electron density: sum the electron species where they exist (kinetic), else
        # quasineutrality from the total charge density (hybrid has no electron species).
        esp = [f for f in fl if f.startswith("rho_") and "electron" in f]
        if esp:
            ne = sum(np.asarray(g["boxlib", f])[:, 0, 0] for f in esp) / (-QE)
        else:
            isp = [f for f in fl if f.startswith("rho_") and "ion" in f]
            ne = sum(np.asarray(g["boxlib", f])[:, 0, 0] for f in isp) / QE
        d = dict(t=float(ds.current_time), tau=float(ds.current_time) / TAU_W,
                 zeta=z / DI0_W, ne=ne / N_CR)
        if "Te" in fl:
            d["Te"] = np.asarray(g["boxlib", "Te"])[:, 0, 0]
        out.append(d)
    return out


def warpx_particles(run_dir, species, nbin=400):
    """Binned particle moments on a common zeta grid.

    Returns per bin: ``ne`` (electron or Z*ion number density / n_cr), ``v`` (ion
    mass-weighted mean velocity / C_S0) and ``Te`` (electron second moment, eV).

    The moments MUST be weight-weighted, not per-macroparticle. The target is loaded with
    an exponential density ramp at fixed ppc, so macroparticle weights span seven decades
    (1.7e10 .. 1.3e17); an unweighted max reports one featherweight particle in the far
    wing and an unweighted mean is dominated by wherever the ppc happens to be densest.
    """
    import yt
    from laserprod import io as lpio
    edges = np.linspace(-50.0 * DE_CR / DI0_W, 2450.0 * DE_CR / DI0_W, nbin + 1)
    mid = 0.5 * (edges[1:] + edges[:-1])
    dz = (edges[1] - edges[0]) * DI0_W          # bin width in metres
    out = []
    for p in lpio.plotfiles(run_dir, "diag1"):
        ds = yt.load(p)
        ad = ds.all_data()
        have = {f[0] for f in ds.field_list}
        acc = dict(t=float(ds.current_time), tau=float(ds.current_time) / TAU_W, zeta=mid)
        for kind, names in species.items():
            Zs, Ws, U = [], [], []
            for s in names:
                if s not in have:
                    continue
                try:
                    Zs.append(np.asarray(ad[(s, "particle_position_x")]) / DI0_W)
                    Ws.append(np.asarray(ad[(s, "particle_weight")]))
                    U.append(np.stack([np.asarray(ad[(s, f"particle_momentum_{c}")])
                                       for c in "xyz"], axis=1))
                except Exception:
                    pass
            if not Zs:
                continue
            z = np.concatenate(Zs); w = np.concatenate(Ws); u = np.concatenate(U, axis=0)
            sw, _ = np.histogram(z, bins=edges, weights=w)
            ok = sw > 0
            dens = sw / dz / N_CR               # 1D: weight is a per-area count
            if kind == "ion":
                m = MASS_RATIO_SIM * ME
                # NB: in 1D WarpX the geometry axis is z. yt exposes the single spatial
                # coordinate as particle_position_x, but the momentum keeps its three
                # PHYSICAL components, so the longitudinal one is momentum_z, not _x.
                # Using _x here silently reports the transverse thermal spread (0.13 C_S0)
                # in place of the outflow (up to 9.9 C_S0).
                un = u / (m * C)
                vz = un[:, 2] / np.sqrt(1.0 + (un * un).sum(axis=1)) * C
                sv, _ = np.histogram(z, bins=edges, weights=w * vz)
                acc["v"] = np.where(ok, sv / np.where(ok, sw, 1), np.nan) / CS0_W
                acc["ni"] = dens
                acc.setdefault("ne", dens * Z_AL)        # quasineutral fallback
            else:
                un = u / (ME * C)
                u2 = (un * un).sum(axis=1)
                s2, _ = np.histogram(z, bins=edges, weights=w * u2)
                mu2 = np.where(ok, s2 / np.where(ok, sw, 1), np.nan)
                dr = np.zeros_like(mu2)
                for k in range(3):
                    sk, _ = np.histogram(z, bins=edges, weights=w * un[:, k])
                    mk = np.where(ok, sk / np.where(ok, sw, 1), 0.0)
                    dr += mk * mk
                acc["Te"] = (mu2 - dr) / 3.0 * 511e3     # kT/(m_e c^2) -> eV
                acc["ne"] = dens                          # real electrons: use them
        out.append(acc)
    return out


def pick(series, tau, key=None):
    """Nearest entry in tau, optionally requiring a key to be present."""
    cand = [s for s in series if key is None or key in s]
    if not cand:
        return None
    return cand[int(np.argmin([abs(s["tau"] - tau) for s in cand]))]

# ---------------------------------------------------------------------------------------
# Scalars. All defined on the UNDERDENSE PLUME, 1e-2 <= n_e/n_cr <= 1, which is the only
# region TEST_PLAN 12.6 admits: the WarpX target is 10 n_cr where FLASH's is 795 n_cr, so
# the overdense interiors are different objects (decision D5) and comparing them is
# meaningless. The lower bound sits a decade above the WarpX ambient floor (1e-3 n_cr) so
# the background never enters a mean.
# ---------------------------------------------------------------------------------------
BAND = (1.0e-2, 1.0)


def outermost(zeta, y, level):
    """Outermost zeta at which y crosses `level`, linearly interpolated. nan if never."""
    ok = np.isfinite(y)
    z, y = zeta[ok], y[ok]
    above = y >= level
    if not above.any() or above.all():
        return np.nan
    i = np.where(above)[0].max()
    if i + 1 >= len(z):
        return z[i]
    y0, y1 = y[i], y[i + 1]
    if y1 == y0:
        return z[i]
    return z[i] + (z[i + 1] - z[i]) * (level - y0) / (y1 - y0)


def scalars(zeta, ne, Te=None, v=None):
    """The comparison scalars for one profile."""
    d = {}
    d["ne_peak"] = float(np.nanmax(ne))
    d["zeta_cr"] = outermost(zeta, ne, 1.0)
    d["zeta_front"] = outermost(zeta, ne, BAND[0])
    band = np.isfinite(ne) & (ne >= BAND[0]) & (ne <= BAND[1])
    if Te is not None:
        Tb = np.where(np.isfinite(Te), Te, np.nan)
        d["Te_max_plume"] = float(np.nanmax(Tb[band])) if band.any() else np.nan
        if band.any() and np.isfinite(Tb[band]).any():
            w = ne[band]
            good = np.isfinite(Tb[band])
            d["Te_mean_plume"] = float(np.average(Tb[band][good], weights=w[good]))
        else:
            d["Te_mean_plume"] = np.nan
        # T_e at the critical surface: nearest finite sample to zeta_cr
        if np.isfinite(d["zeta_cr"]):
            j = int(np.nanargmin(np.abs(zeta - d["zeta_cr"])))
            d["Te_at_cr"] = float(Tb[j]) if np.isfinite(Tb[j]) else np.nan
        else:
            d["Te_at_cr"] = np.nan
    if v is not None:
        z01 = outermost(zeta, ne, 0.1)
        if np.isfinite(z01):
            j = int(np.nanargmin(np.abs(zeta - z01)))
            d["v_at_0p1"] = float(v[j])
        else:
            d["v_at_0p1"] = np.nan
        d["v_band_max"] = float(np.nanmax(v[band])) if band.any() else np.nan
    # exponential density scale length across the plume band, in units of d_i0
    if band.sum() >= 4:
        zz, nn = zeta[band], ne[band]
        k = np.polyfit(zz, np.log(nn), 1)[0]
        d["L_n"] = float(-1.0 / k) if k < 0 else np.nan
    return d


TSS_REDUCED = TE_REF / RESCALE ** (1.0 / 3.0)      # 312 eV -- see main()'s note

FLASH_DIR = ("/home/hhelal/shared/simulations/FLASH_LaserAblation-Ploegstra_2026-08/"
             "Ablation_prod_08-17")
FLASH_RAD = ("/home/hhelal/shared/simulations/FLASH_LaserAblationRad-Ploegstra_2026-08/"
             "Ablation_prod_rad_08-17")
SP_KIN = {"electron": ["targ_electrons", "amb_electrons"],
          "ion": ["targ_ions", "amb_ions"]}
SP_HYB = {"ion": ["targ_ions", "amb_ions"]}
TAUS = (2.7, 6.7, 13.5, 20.3, 27.0)
COLS = {"FLASH": "#1f4e9c", "kinetic": "#c1441a", "hybrid": "#2a8a5f"}


def absorbed(run_dir, i0=1.0e17):
    """(t_end, E_abs, <f_abs>, f_abs(end), f_abs(0)) from the LASERDEP log lines.

    E_abs is per unit area [J/m^2] in 1D. <f_abs> is the TIME-INTEGRATED fraction, which is
    the one that sets the energy budget; f_abs(end) shows whether coupling is still live.
    """
    t, P, E = [], [], []
    for ln in open(os.path.join(run_dir, "run.log"), errors="ignore"):
        if not ln.startswith("LASERDEP step"):
            continue
        f = ln.split()
        try:
            t.append(float(f[4])); P.append(float(f[6])); E.append(float(f[8]))
        except Exception:
            pass
    if not t:
        return None
    t = np.array(t); P = np.array(P); E = np.array(E)
    return dict(t_end=t[-1], E_abs=E[-1], f_mean=E[-1] / (i0 * t[-1]),
                f_end=P[-1] / i0, f_0=P[0] / i0)


def history(kin, hyb, out):
    """Time histories of the four scalars that survive the rescaling."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    F = flash_series(FLASH_DIR, "lez1d")
    K = warpx_particles(kin, SP_KIN)
    H = warpx_particles(hyb, SP_HYB)
    Hf = warpx_fields(hyb)
    ser = {}
    for name, S in (("FLASH", F), ("kinetic", K), ("hybrid", H)):
        rows = []
        for s in S:
            if s["tau"] <= 0:
                continue
            if name == "hybrid":
                hf = pick(Hf, s["tau"], "Te")
                Te = np.interp(s["zeta"], hf["zeta"], hf["Te"]) if hf else None
            else:
                Te = s.get("Te")
            sc = scalars(s["zeta"], s["ne"], Te, s.get("v"))
            sc["tau"] = s["tau"]
            rows.append(sc)
        ser[name] = rows

    keys = [("Te_mean_plume", r"$T_e$ in the plume  [eV]  (density-weighted)", None),
            ("zeta_front", r"plume front  $\zeta(n_e = 10^{-2} n_{cr})$", None),
            ("v_at_0p1", r"$v_z/C_{S0}$  at  $n_e = 0.1\,n_{cr}$", None),
            ("L_n", r"density scale length  $L_n/d_{i0}$", None)]
    fig, ax = plt.subplots(1, 4, figsize=(17.5, 4.1))
    for j, (k, lab, _) in enumerate(keys):
        for name, col in COLS.items():
            r = ser[name]
            x = [q["tau"] for q in r]
            y = [q.get(k, np.nan) for q in r]
            ls = "-" if name == "FLASH" else ("--" if name == "kinetic" else "-.")
            ax[j].plot(x, y, color=col, lw=1.9 if name == "FLASH" else 1.5, ls=ls,
                       label=name)
        ax[j].set_xlabel(r"$\tau = t/(d_{i0}/C_{S0})$")
        ax[j].set_title(lab, fontsize=9.5)
        ax[j].grid(alpha=0.15)
        ax[j].set_xlim(0, 27.5)
    ax[0].axhline(TE_REF, color="0.35", ls=":", lw=1.0)
    ax[0].axhline(TSS_REDUCED, color="0.35", ls="--", lw=1.0)
    ax[0].set_ylim(0, 1000)
    ax[0].text(0.5, TE_REF + 12, f"Manheimer, real $m_i$ ({TE_REF:.0f} eV)", fontsize=7,
               color="0.25")
    ax[0].text(0.5, TSS_REDUCED + 12,
               f"Manheimer, REDUCED $m_i$ ({TSS_REDUCED:.0f} eV)", fontsize=7,
               color="0.25")
    ax[0].legend(loc="lower right", fontsize=8.5)
    fig.suptitle("The four quantities that survive the mass rescaling. FLASH has real "
                 "$m_i$; both WarpX legs are 18.36x lighter, so each is plotted against "
                 "its OWN $d_{i0}$ and $d_{i0}/C_{S0}$.", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, dpi=135)
    print(f"  figure: {out}")


def collect(kin="runs/P4/P4_lez_kin_bg", hyb="runs/P4/P4_lez_hyb_bg3"):
    F = flash_series(FLASH_DIR, "lez1d")
    K = warpx_particles(kin, SP_KIN)
    H = warpx_particles(hyb, SP_HYB)
    Hf = warpx_fields(hyb)
    out = {}
    for tau in TAUS:
        f, k, h = pick(F, tau), pick(K, tau), pick(H, tau)
        hf = pick(Hf, tau, "Te")
        Th = np.interp(h["zeta"], hf["zeta"], hf["Te"]) if hf else None
        out[tau] = dict(
            FLASH=dict(zeta=f["zeta"], ne=f["ne"], Te=f["Te"], v=f["v"], tau=f["tau"]),
            kinetic=dict(zeta=k["zeta"], ne=k["ne"], Te=k.get("Te"), v=k.get("v"),
                         tau=k["tau"]),
            hybrid=dict(zeta=h["zeta"], ne=h["ne"], Te=Th, v=h.get("v"), tau=h["tau"]))
    return out, F, K, H, Hf


def table(data):
    keys = ["ne_peak", "zeta_cr", "zeta_front", "Te_mean_plume", "Te_max_plume",
            "v_at_0p1", "v_band_max", "L_n"]
    sc = {c: {} for c in COLS}
    for tau in TAUS:
        for c in COLS:
            d = data[tau][c]
            sc[c][tau] = scalars(d["zeta"], d["ne"], d["Te"], d["v"])
    for c in COLS:
        print("\n" + "=" * 112)
        print(f"{c}   (band {BAND[0]:g} <= n_e/n_cr <= {BAND[1]:g};  "
              f"density-weighted where a mean is taken)")
        print(f"{'tau':>6} " + " ".join(f"{k:>14}" for k in keys))
        for tau in TAUS:
            print(f"{tau:6.1f} " + " ".join(f"{sc[c][tau].get(k, np.nan):14.3f}"
                                           for k in keys))
    print("\n" + "=" * 112)
    print("FINAL STATE (tau = 27), WarpX legs as a ratio to FLASH")
    for k in keys:
        f = sc["FLASH"][27.0][k]
        line = f"  {k:16s} FLASH {f:10.3f}"
        for c in ("kinetic", "hybrid"):
            v = sc[c][27.0][k]
            line += f" | {c} {v:9.3f} ({v/f:5.2f}x)" if f else f" | {c} {v:9.3f}"
        print(line)
    print(f"\n  T_e (plume, density-weighted) against EACH CODE'S OWN Manheimer value")
    print(f"    real m_i  T_e,SS = {TE_REF:.0f} eV      "
          f"reduced m_i T_e,SS = {TSS_REDUCED:.1f} eV")
    for c, ref in (("FLASH", TE_REF), ("kinetic", TSS_REDUCED), ("hybrid", TSS_REDUCED)):
        print(f"    {c:9s} {sc[c][27.0]['Te_mean_plume']:7.1f} eV / {ref:6.1f} eV "
              f"= {sc[c][27.0]['Te_mean_plume']/ref:.3f}")
    return sc


def figure(data, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(TAUS)
    fig, ax = plt.subplots(3, n, figsize=(3.5 * n, 9.6), sharex=True)
    for c, tau in enumerate(TAUS):
        for name, col in COLS.items():
            d = data[tau][name]
            ls = "-" if name == "FLASH" else ("--" if name == "kinetic" else "-.")
            lw = 2.0 if name == "FLASH" else 1.6
            ax[0, c].semilogy(d["zeta"], np.maximum(d["ne"], 1e-9), color=col, lw=lw,
                              ls=ls, label=name)
            if d["Te"] is not None:
                ax[1, c].plot(d["zeta"], d["Te"], color=col, lw=lw, ls=ls)
            if d["v"] is not None:
                ax[2, c].plot(d["zeta"], d["v"], color=col, lw=lw, ls=ls)
        ax[0, c].axhline(1.0, color="0.4", ls=":", lw=0.9)
        ax[0, c].set_ylim(1e-4, 5e3)
        ax[0, c].set_title(rf"$\tau$ = {tau:.1f}   ($t/(d_{{i0}}/C_{{S0}})$)",
                           loc="left", fontsize=9.5, fontweight="bold")
        ax[1, c].axhline(TE_REF, color="0.35", ls=":", lw=1.0)
        ax[1, c].axhline(TSS_REDUCED, color="0.35", ls="--", lw=1.0)
        ax[1, c].set_ylim(0, 1100)
        ax[2, c].set_ylim(-0.5, 6.0)
        ax[2, c].axhline(0.0, color="0.7", lw=0.7)
        ax[2, c].set_xlabel(r"$\zeta = z/d_{i0}$   (each code's own $d_{i0}$)")
        for r in range(3):
            ax[r, c].set_xlim(-6, 110)
            ax[r, c].grid(alpha=0.15)
            if c:
                ax[r, c].tick_params(labelleft=False)
    ax[0, 0].set_ylabel(r"$n_e/n_{cr}$")
    ax[1, 0].set_ylabel(r"$T_e$  [eV]")
    ax[2, 0].set_ylabel(r"$v_z/C_{S0}$")
    ax[0, 0].legend(loc="lower left", fontsize=8.5, framealpha=0.9)
    ax[1, 0].text(0.03, TE_REF, f" {TE_REF:.0f} eV: Manheimer, real $m_i$",
                  transform=ax[1, 0].get_yaxis_transform(), va="bottom", fontsize=7,
                  color="0.25")
    ax[1, 0].text(0.03, TSS_REDUCED, f" {TSS_REDUCED:.0f} eV: same, REDUCED $m_i$",
                  transform=ax[1, 0].get_yaxis_transform(), va="bottom", fontsize=7,
                  color="0.25")
    fig.suptitle("FLASH (real $m_i$) vs kinetic and hybrid WarpX (reduced $m_i$), on the "
                 "normalised axes.  Overdense interiors are NOT comparable: "
                 "$n_{max}$ = 795 $n_{cr}$ in FLASH, 10 in WarpX (D5).",
                 fontsize=10, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fig.savefig(out, dpi=135)
    print(f"\n  figure: {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kinetic", default="runs/P4/P4_lez_kin_bg")
    ap.add_argument("--hybrid", default="runs/P4/P4_lez_hyb_bg3")
    ap.add_argument("--outdir", default="media/xcode")
    a = ap.parse_args()
    banner()
    print(f"\nManheimer steady state  T_e,SS = 5.94 mu^(1/3) Z^(-1/3) lambda^(4/3) I^(2/3)")
    print(f"  real aluminium          : {TE_REF:.0f} eV")
    print(f"  at the REDUCED ion mass : {TSS_REDUCED:.1f} eV   "
          f"(mu is down {RESCALE:.2f}x, and T_e,SS ~ mu^(1/3))")
    print("  ^ this is the reference the WarpX legs must be judged against, NOT 823 eV.")
    os.makedirs(a.outdir, exist_ok=True)
    print("\nABSORBED LASER ENERGY -- quote this beside every temperature")
    print(f"  {'leg':22s} {'E_abs[J/m2]':>13} {'<f_abs>':>9} {'f_abs(0)':>9} {'f_abs(end)':>11}")
    for lab, rd in (("kinetic", a.kinetic), ("hybrid", a.hybrid)):
        q = absorbed(rd)
        if q:
            print(f"  {lab+' '+os.path.basename(rd):22s} {q['E_abs']:13.4e} "
                  f"{q['f_mean']:9.3f} {q['f_0']:9.3f} {q['f_end']:11.3f}")
    print(f"  {'FLASH (rad off)':22s} {8.274e7:13.4e} {0.870:9.3f} "
          f"{'--':>9} {'--':>11}   (in its own, 18.36x longer, time base)")
    data, *_ = collect(a.kinetic, a.hybrid)
    table(data)
    figure(data, os.path.join(a.outdir, "profiles.png"))
    history(a.kinetic, a.hybrid, os.path.join(a.outdir, "history.png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
