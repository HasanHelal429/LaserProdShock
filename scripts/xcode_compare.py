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


def warpx_scales(mass_ratio=MASS_RATIO_SIM):
    """(d_i0, C_S0, tau_unit, T_e,SS, mu) for a WarpX leg of the given m_ion/m_e.

    NOT a constant. `P4_lez_kin_flashic_ct` runs the ION at 100 m_e where every earlier
    Phase-4 leg ran aluminium at 26.98 x 100 = 2698, and the two differ by 5.2x in the tau
    unit -- so a hardcoded TAU_W labels a completed tau = 27 run as tau = 5.2 and every
    profile is read at the wrong time.

    d_i0 is the PROTON skin depth at n_cr, the paper's convention and the one every
    recorded Phase-4 number uses -- the sim's proton being m_i/A_Al, so mass_ratio = 2698
    gives sqrt(2698/26.98) = 10.00 d_e and reproduces the module constant DI0_W exactly.
    Using the ION inertial length instead would give 51.94 d_e at 2698 and silently
    restate every result in RESULTS.md by a factor 5.19. C_S0 keeps the ION mass. That
    mixed pairing is the paper's own (TEST_PLAN 12.2) and is preserved deliberately.
    """
    mi = float(mass_ratio) * ME
    d = C / np.sqrt(N_CR * QE ** 2 / (EPS0 * mi / A_AL))
    c_s = np.sqrt(Z_AL * TE_REF * QE / mi)
    mu = MASS_RATIO_REAL / float(mass_ratio)
    return dict(mass_ratio=float(mass_ratio), di0=d, cs0=c_s, tau=d / c_s,
                tss=TE_REF / mu ** (1.0 / 3.0), mu=mu)


SC_W = dict(mass_ratio=MASS_RATIO_SIM, di0=DI0_W, cs0=CS0_W, tau=TAU_W,
            tss=TE_REF / (MASS_RATIO_REAL / MASS_RATIO_SIM) ** (1.0 / 3.0),
            mu=MASS_RATIO_REAL / MASS_RATIO_SIM)

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
                        depo=v["depo"], dens=v["dens"]))
    return out


# ---------------------------------------------------------------------------------------
# WarpX
# ---------------------------------------------------------------------------------------
def warpx_fields(run_dir, sc=None):
    sc = sc or SC_W
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
        d = dict(t=float(ds.current_time), tau=float(ds.current_time) / sc["tau"],
                 zeta=z / sc["di0"], ne=ne / N_CR)
        if "Te" in fl:
            d["Te"] = np.asarray(g["boxlib", "Te"])[:, 0, 0]
        out.append(d)
    return out


def warpx_particles(run_dir, species, nbin=400, sc=None):
    sc = sc or SC_W
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
    edges = np.linspace(-50.0 * DE_CR / sc["di0"], 2450.0 * DE_CR / sc["di0"], nbin + 1)
    mid = 0.5 * (edges[1:] + edges[:-1])
    dz = (edges[1] - edges[0]) * sc["di0"]      # bin width in metres
    out = []
    for p in lpio.plotfiles(run_dir, "diag1"):
        ds = yt.load(p)
        ad = ds.all_data()
        have = {f[0] for f in ds.field_list}
        acc = dict(t=float(ds.current_time), tau=float(ds.current_time) / sc["tau"], zeta=mid)
        for kind, names in species.items():
            Zs, Ws, U = [], [], []
            for s in names:
                if s not in have:
                    continue
                try:
                    Zs.append(np.asarray(ad[(s, "particle_position_x")]) / sc["di0"])
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
                m = sc["mass_ratio"] * ME
                # NB: in 1D WarpX the geometry axis is z. yt exposes the single spatial
                # coordinate as particle_position_x, but the momentum keeps its three
                # PHYSICAL components, so the longitudinal one is momentum_z, not _x.
                # Using _x here silently reports the transverse thermal spread (0.13 C_S0)
                # in place of the outflow (up to 9.9 C_S0).
                un = u / (m * C)
                vz = un[:, 2] / np.sqrt(1.0 + (un * un).sum(axis=1)) * C
                sv, _ = np.histogram(z, bins=edges, weights=w * vz)
                acc["v"] = np.where(ok, sv / np.where(ok, sw, 1), np.nan) / sc["cs0"]
                acc["ni"] = dens
                acc.setdefault("ne", dens * Z_AL)        # quasineutral fallback
                # Ion temperature, same second-moment-minus-drift form as the electrons.
                # m_i c^2 in eV is mass_ratio * 511 keV. Needed by paper_fig3.py panel (c);
                # additive, so existing callers are unaffected.
                u2i = (un * un).sum(axis=1)
                s2i, _ = np.histogram(z, bins=edges, weights=w * u2i)
                mu2i = np.where(ok, s2i / np.where(ok, sw, 1), np.nan)
                dri = np.zeros_like(mu2i)
                for k in range(3):
                    ski, _ = np.histogram(z, bins=edges, weights=w * un[:, k])
                    mki = np.where(ok, ski / np.where(ok, sw, 1), 0.0)
                    dri += mki * mki
                acc["Ti"] = (mu2i - dri) / 3.0 * (sc["mass_ratio"] * 511e3)
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

def psc_norm(data_dir):
    """PSC's SI normalisation, read from the run's OWN log rather than hardcoded.

    PSC is a normalised code with two independent knobs, and the second one is easy to miss:

        ReducedMassRatio  sets d_i0 and the mass unit   (100 in every run here)
        ReducedSoL        sets m_e c^2 = 3000 eV / ReducedSoL

    `run_ourflash` runs the paper's ReducedSoL = 0.05, i.e. m_e c^2 = 60 keV, while
    `run_ourflash_511keV` runs 3000/511000, i.e. the REAL electron rest energy. K_length and
    K_mass are identical between them, so every length and every physical mass is the same;
    what moves is K_time (by sqrt(ReducedSoL)), the temperature unit K_temperature (by 8.52x)
    and the collision rate (by ReducedSoL^2, 72.5x). Hardcoding the 60 keV constants and then
    pointing a script at the 511 keV dumps reads T_e 8.52x too cold on a clock 2.92x too slow,
    silently -- hence this reader.

    Returns dict(K_temperature [eV], K_time [s], dt [s], reduced_sol, K_vel [m/s], mec2_keV).
    K_vel converts PSC's code velocity to m/s: CS0_phys / CS0_code with the REAL proton.
    """
    log = os.path.join(os.path.dirname(os.path.normpath(data_dir)), "run.log")
    if not os.path.exists(log):                       # a data dir may be passed directly
        log = os.path.join(os.path.normpath(data_dir), "run.log")
    got = {}
    for ln in open(log, errors="ignore"):
        s = ln.strip()
        for k in ("K_temperature=", "K_time=", "dt="):
            if s.startswith(k) and k[:-1] not in got:
                try:
                    got[k[:-1]] = float(s[len(k):].split()[0])
                except (ValueError, IndexError):
                    pass
        if len(got) == 3:
            break
    missing = {"K_temperature", "K_time", "dt"} - set(got)
    if missing:
        raise RuntimeError(f"{log}: could not read {sorted(missing)} -- PSC's normalisation "
                           "must come from the run, not from a default")
    rsol = 3000.0 / got["K_temperature"]              # ReducedSoL, by K_temperature's definition
    return dict(K_temperature=got["K_temperature"], K_time=got["K_time"],
                dt=got["dt"] * got["K_time"],         # 'dt' is logged in CODE units
                reduced_sol=rsol,
                K_vel=np.sqrt(3000.0 * QE / MP) / np.sqrt(rsol / 100.0),
                mec2_keV=got["K_temperature"] / 1e3)

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
TAUS = [2.7, 6.7, 13.5, 20.3, 27.0]   # FLASH's clock; override with --taus.
# These run well past the end of a short leg. A WarpX leg at mass_ratio 2698 reaches
# tau_own 5.39, i.e. FLASH tau 8.09, so only the first two rows are real for it.

# Kept as a three-key dict, and kept exactly, because scripts/talk_xcode.py reads it.
COLS = {"FLASH": "#1f4e9c", "kinetic": "#c1441a", "hybrid": "#2a8a5f"}
PALETTE = ("#c1441a", "#7a3fa0", "#2a8a5f", "#b8860b", "#1f6f8b")  # WarpX legs, in order

# The default set of WarpX legs. `P4_lez_kin_flashic` is here because it is the only leg
# whose initial condition was FITTED to FLASH rather than assumed, and the comparison is
# unreadable without both it and the analytic-IC leg side by side: the two bracket FLASH
# from opposite directions (front 2.03x vs 0.50x), which is the whole result.
# UPDATED 2026-08-18 (evening). The headline pair is now the SAME DECK at four and six
# decades of resolved density (`density_min_frac` 1e-4 vs 1e-6), because that one parameter
# — and not the closure, the reservoir or the ppc — is what moved the T_e shape from
# RISE = 1.504 to 1.133 against FLASH's 1.148.
#
# The two m_i = 100 legs (`flashic_ct`, `flashic_res`) are DELIBERATELY OUT: changing the
# mass ratio rescaled their temperatures and drift but not their corona geometry, which was
# derived assuming d_i0 = 10 d_e, so in normalised units their corona is 5.19x too extended
# and they are not FLASH matches at all. They remain valid against EACH OTHER (the reservoir
# A/B) and are still selectable with --leg.
# Three curves only. Five made the panel unreadable, and the legs that were dropped are
# each still one `--leg` away: `P4_lez_kin` (the same deck at four decades, the density-floor
# A/B), `P4_lez_kin_bg` (analytic IC + 1e-3 background) and `P4_lez_kin_flashic`.
LEGS_DEFAULT = (("kinetic, 6 dec + FLASH IC", "runs/P4/P4_lez_kin_ic6"),
                ("hybrid", "runs/P4/P4_lez_hyb_bg3"))


def absorbed(run_dir, i0=1.0e17):
    """(t_end, E_abs, <f_abs>, f_abs(end), f_abs(0)) from the LASERDEP log lines.

    E_abs is per unit area [J/m^2] in 1D. <f_abs> is the TIME-INTEGRATED fraction, which is
    the one that sets the energy budget; f_abs(end) shows whether coupling is still live.
    """
    t, P, E = [], [], []
    path = os.path.join(run_dir, "run.log")
    if not os.path.exists(path):
        return None
    for ln in open(path, errors="ignore"):
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


def load_leg(label, path, colour):
    """One WarpX leg, with its species map and T_e source chosen from its own config.

    A hybrid run has no electron macroparticles at all, so its T_e is the `Te` FIELD and its
    species map has only ions; a kinetic run's T_e is a particle moment. Deciding that from
    the config rather than from a flag passed by the caller is what lets the leg list be
    arbitrary -- and stops a hybrid leg being silently read as if it had electrons.
    """
    from laserprod import config as lpconfig
    cfg = lpconfig.load(path)
    hybrid = str((cfg.get("solver") or {}).get("type", "em")) == "hybrid"
    # The ion mass is a per-run primary, not a project constant: flashic_ct runs it at
    # 100 m_e where the others run 2698, which is 5.2x in the tau unit.
    sc = warpx_scales(float(cfg["reference"]["mass_ratio"]))
    return dict(label=label, path=path, colour=colour, hybrid=hybrid, sc=sc,
                rid=lpconfig.run_id(cfg),
                S=warpx_particles(path, SP_HYB if hybrid else SP_KIN, sc=sc),
                F=warpx_fields(path, sc=sc) if hybrid else None)


def leg_state(leg, tau):
    """(zeta, ne, Te, v) for one leg at the nearest tau, with the hybrid T_e interpolated.

    Also returns ``tau_want`` and ``stale``. A leg that ended before the requested tau has
    its LAST dump returned by ``pick`` with no complaint, so every row past the end of a
    short leg silently repeats it -- which is how "the FLASH-kinetic benchmark passes" got
    into RESULTS at line 3085 comparing FLASH at tau 27 against WarpX at tau 5 (retracted,
    line 4411). ``stale`` marks those rows so the table can flag them instead.
    """
    s = pick(leg["S"], tau)
    if s is None:
        return None
    Te = s.get("Te")
    if leg["hybrid"]:
        hf = pick(leg["F"], tau, "Te")
        Te = np.interp(s["zeta"], hf["zeta"], hf["Te"]) if hf else None
    return dict(zeta=s["zeta"], ne=s["ne"], Te=Te, v=s.get("v"), tau=s["tau"],
                tau_want=tau, stale=abs(s["tau"] - tau) > 0.25)


# The WarpX legs' clocks do NOT start where FLASH's does. Every Phase-4 initial condition
# stands for FLASH's t = 0.1 ns state -- the fitted ones by construction, and the analytic
# one because its scale length was DERIVED as C_S t at 0.1 ns ("2.69 ion response times, so
# C_S t = 2.69 d_i0 = 27 d_e", P4_lez_kin's config). 0.1 ns is tau = 2.696, so a WarpX leg
# at its own tau = 27 is FLASH's tau = 29.7, and comparing at equal tau compares states
# 2.7 apart -- 10 % of the run.
#
# TAU is FLASH's clock here. A leg is sampled at tau - TAU_HANDOFF.
TAU_HANDOFF = 2.696


def collect(legs, offset=TAU_HANDOFF):
    F = flash_series(FLASH_DIR, "lez1d")
    data = {}
    for tau in TAUS:
        f = pick(F, tau)
        row = {"FLASH": dict(zeta=f["zeta"], ne=f["ne"], Te=f["Te"], v=f["v"],
                             tau=f["tau"])}
        for leg in legs:
            st = leg_state(leg, max(tau - offset, 0.0))
            if st is not None:
                row[leg["label"]] = st
        data[tau] = row
    return data, F


def table(data, legs):
    keys = ["ne_peak", "zeta_cr", "zeta_front", "Te_mean_plume", "Te_max_plume",
            "v_at_0p1", "v_band_max", "L_n"]
    names = ["FLASH"] + [q["label"] for q in legs]
    sc = {n: {} for n in names}
    for tau in TAUS:
        for n in names:
            d = data[tau].get(n)
            if d is None:
                continue
            sc[n][tau] = scalars(d["zeta"], d["ne"], d["Te"], d["v"])
    for n in names:
        print("\n" + "=" * 116)
        print(f"{n}   (band {BAND[0]:g} <= n_e/n_cr <= {BAND[1]:g};  "
              f"density-weighted where a mean is taken)")
        print(f"{'tau':>6} " + " ".join(f"{k:>14}" for k in keys))
        for tau in TAUS:
            if tau not in sc[n]:
                continue
            d = data[tau].get(n) or {}
            mark = "  <-- STALE: leg ended at tau %.2f" % (d.get("tau", np.nan) + TAU_HANDOFF) \
                   if d.get("stale") else ""
            print(f"{tau:6.1f} " + " ".join(f"{sc[n][tau].get(k, np.nan):14.3f}"
                                           for k in keys) + mark)
    print("\n" + "=" * 116)
    # Compare at the LAST tau every leg actually reaches, not at the end of the grid --
    # otherwise a short leg's last dump is silently set against FLASH hundreds of ps later.
    live = [t for t in TAUS
            if all(not (data[t].get(n) or {}).get("stale", False) for n in names[1:])]
    tcmp = max(live) if live else TAUS[0]
    if tcmp != max(TAUS):
        print(f"NOTE: comparing at tau = {tcmp} -- the last tau EVERY leg reaches. "
              f"The grid runs to {max(TAUS)}, where the short legs are stale.")
    print(f"STATE AT tau = {tcmp}, each WarpX leg as a ratio to FLASH")
    for k in keys:
        f = sc["FLASH"][tcmp].get(k, np.nan)
        line = f"  {k:16s} FLASH {f:10.3f}"
        for n in names[1:]:
            v = sc[n].get(tcmp, {}).get(k, np.nan)
            line += f" | {n} {v:9.3f} ({v/f:5.2f}x)" if f else f" | {n} {v:9.3f}"
        print(line)
    print(f"\n  T_e (plume, density-weighted) against EACH LEG'S OWN Manheimer value")
    print(f"    real m_i  T_e,SS = {TE_REF:.0f} eV      "
          f"reduced m_i T_e,SS = {TSS_REDUCED:.1f} eV")
    print("  and against what its OWN absorbed fraction supports, T_e ~ I_abs^(2/3):")
    ss_of = {q["label"]: q["sc"]["tss"] for q in legs}
    fabs = {"FLASH": 0.870}
    for leg in legs:
        q = absorbed(leg["path"])
        fabs[leg["label"]] = q["f_mean"] if q else np.nan
    for n in names:
        ref = TE_REF if n == "FLASH" else ss_of.get(n, TSS_REDUCED)
        T = sc[n].get(tcmp, {}).get("Te_mean_plume", np.nan)
        supported = ref * (fabs[n] / 0.870) ** (2.0 / 3.0)
        print(f"    {n:22s} f_abs {fabs[n]:5.3f}  T_e {T:7.1f} eV  "
              f"/ own SS {ref:6.1f} = {T/ref:5.3f}  "
              f"/ absorption-supported {supported:6.1f} = {T/supported:5.3f}")
    return sc


def figure(data, legs, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = ["FLASH"] + [q["label"] for q in legs]
    colour = {"FLASH": COLS["FLASH"]}
    style = {"FLASH": ("-", 2.0)}
    for j, leg in enumerate(legs):
        colour[leg["label"]] = leg["colour"]
        style[leg["label"]] = (("--", "-.", ":")[j % 3], 1.5)

    n = len(TAUS)
    fig, ax = plt.subplots(3, n, figsize=(3.5 * n, 9.6), sharex=True)
    for c, tau in enumerate(TAUS):
        for name in names:
            d = data[tau].get(name)
            if d is None:
                continue
            ls, lw = style[name]
            ax[0, c].semilogy(d["zeta"], np.maximum(d["ne"], 1e-9), color=colour[name],
                              lw=lw, ls=ls, label=name)
            inb = np.isfinite(d["ne"]) & (d["ne"] >= BAND[0]) & (d["ne"] <= BAND[1])
            for r, y in ((1, d["Te"]), (2, d["v"])):
                if y is None:
                    continue
                ax[r, c].plot(d["zeta"], np.where(inb, y, np.nan), color=colour[name],
                              lw=lw, ls=ls)
                ax[r, c].plot(d["zeta"], np.where(inb, np.nan, y), color=colour[name],
                              lw=lw * 0.7, ls=ls, alpha=0.20)
        ax[0, c].axhline(1.0, color="0.4", ls=":", lw=0.9)
        ax[0, c].set_ylim(1e-4, 5e3)
        ax[0, c].set_title(rf"$\tau$ = {tau:.1f}", loc="left", fontsize=9.5,
                           fontweight="bold")
        ax[1, c].axhline(TE_REF, color="0.35", ls=":", lw=1.0)
        for v, col in {round(q["sc"]["tss"], 1): q["colour"] for q in legs}.items():
            ax[1, c].axhline(v, color=col, ls="--", lw=1.0, alpha=0.55)
        ax[1, c].set_ylim(0, 1100)
        ax[2, c].set_ylim(-0.5, 6.0)
        ax[2, c].axhline(0.0, color="0.7", lw=0.7)
        ax[2, c].set_xlabel(r"$\zeta = z/d_{i0}$")
        for r in range(3):
            ax[r, c].set_xlim(-8, 110)
            ax[r, c].grid(alpha=0.15)
            if c:
                ax[r, c].tick_params(labelleft=False)
    ax[0, 0].set_ylabel(r"$n_e/n_{cr}$")
    ax[1, 0].set_ylabel(r"$T_e$  [eV]")
    ax[2, 0].set_ylabel(r"$v_z/C_{S0}$")
    ax[0, 0].legend(loc="lower left", fontsize=8, framealpha=0.9)
    ax[1, 0].text(0.03, TE_REF, f" {TE_REF:.0f} eV real $m_i$",
                  transform=ax[1, 0].get_yaxis_transform(), va="bottom", fontsize=7,
                  color="0.25")
    for q in legs:
        ax[1, 0].text(0.03, q["sc"]["tss"],
                      f" {q['sc']['tss']:.0f} eV  ($m_i/m_e$={q['sc']['mass_ratio']:.0f})",
                      transform=ax[1, 0].get_yaxis_transform(), va="bottom", fontsize=6.5,
                      color=q["colour"])
    fig.suptitle("FLASH (real $m_i$) vs the WarpX legs (reduced $m_i$), on the normalised "
                 "axes. $T_e$ and $v$ are solid inside the comparison band and faded "
                 "outside. Overdense interiors are NOT comparable ($n_{max}$ 795 $n_{cr}$ "
                 "vs 40 / 10) -- decision D5.", fontsize=9.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.972))
    fig.savefig(out, dpi=135)
    print(f"\n  figure: {out}")


def history(legs, out):
    """Time histories of the four quantities that survive the mass rescaling."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    F = flash_series(FLASH_DIR, "lez1d")
    ser = {"FLASH": [dict(tau=s["tau"],
                          **scalars(s["zeta"], s["ne"], s["Te"], s["v"]))
                     for s in F if s["tau"] > 0]}
    for leg in legs:
        rows = []
        for s in leg["S"]:
            if s["tau"] <= 0:
                continue
            st = leg_state(leg, s["tau"])
            rows.append(dict(tau=s["tau"],
                             **scalars(st["zeta"], st["ne"], st["Te"], st["v"])))
        for r in rows:
            r["tau"] = r["tau"] + TAU_HANDOFF     # onto FLASH's clock
        ser[leg["label"]] = rows

    keys = [("Te_mean_plume", r"$T_e$ in the plume [eV] (density-weighted)"),
            ("zeta_front", r"plume front  $\zeta(n_e = 10^{-2} n_{cr})$"),
            ("v_at_0p1", r"$v_z/C_{S0}$ at $n_e = 0.1\,n_{cr}$"),
            ("L_n", r"density scale length $L_n/d_{i0}$")]
    fig, ax = plt.subplots(1, 4, figsize=(17.5, 4.1))
    for j, (k, lab) in enumerate(keys):
        for name, rows in ser.items():
            col = COLS["FLASH"] if name == "FLASH" else \
                next(q["colour"] for q in legs if q["label"] == name)
            ls = "-" if name == "FLASH" else "--"
            ax[j].plot([q["tau"] for q in rows], [q.get(k, np.nan) for q in rows],
                       color=col, lw=1.9 if name == "FLASH" else 1.5, ls=ls, label=name)
        ax[j].set_xlabel(r"$\tau = t/(d_{i0}/C_{S0})$")
        ax[j].set_title(lab, fontsize=9.5)
        ax[j].grid(alpha=0.15)
        ax[j].set_xlim(0, 27.5)
    # ONE LINE PER DISTINCT ION MASS. The legs no longer share a mass ratio -- flashic_ct
    # runs m_i = 100 m_e against the others' 2698 -- so a single "reduced m_i" line would
    # be the wrong target for at least one curve on the panel.
    ax[0].axhline(TE_REF, color="0.35", ls=":", lw=1.0)
    ax[0].text(0.5, TE_REF + 12, f"Manheimer, real $m_i$ ({TE_REF:.0f} eV)", fontsize=7,
               color="0.25")
    seen = set()
    for leg in legs:
        v = round(leg["sc"]["tss"], 1)
        if v in seen:
            continue
        seen.add(v)
        ax[0].axhline(v, color=leg["colour"], ls="--", lw=1.0, alpha=0.55)
        ax[0].text(0.5, v + 12, f"$m_i/m_e$ = {leg['sc']['mass_ratio']:.0f}  ({v:.0f} eV)",
                   fontsize=7, color=leg["colour"])
    ax[0].set_ylim(0, 1000)
    ax[0].legend(loc="lower right", fontsize=8)
    # Say what the legs ACTUALLY are, rather than a hardcoded sentence that goes stale the
    # moment the default leg set changes -- as it did when the m_i = 100 legs were dropped.
    uniq = sorted({q["sc"]["mass_ratio"] for q in legs})
    mtxt = (f"all at $m_i/m_e$ = {uniq[0]:.0f}" if len(uniq) == 1 else
            "and they do NOT share an ion mass: "
            + ", ".join(f"{m:.0f}" for m in uniq) + " $m_e$")
    fig.suptitle("The four quantities that survive the mass rescaling. FLASH has real "
                 "$m_i$; each WarpX leg is plotted against its OWN $d_{i0}$, "
                 f"$d_{{i0}}/C_{{S0}}$ and $T_{{e,SS}}(\\mu)$ -- {mtxt}.",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out, dpi=135)
    print(f"  figure: {out}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--leg", action="append", metavar="LABEL=PATH",
                    help="a WarpX leg to include; repeatable. Kinetic or hybrid is decided "
                         "from the run's own config. Default: "
                         + "; ".join(f"{a}={b}" for a, b in LEGS_DEFAULT))
    ap.add_argument("--outdir", default="media/xcode")
    ap.add_argument("--taus", type=float, nargs="+", default=None, metavar="TAU",
                    help="FLASH-clock taus to compare at (default 2.7 6.7 13.5 20.3 27.0). "
                         "Rows past the end of a leg are marked STALE, not silently filled "
                         "with its last dump -- keep them inside every leg's window.")
    ap.add_argument("--tau-offset", dest="tau_offset", type=float, default=TAU_HANDOFF,
                    help="shift the WarpX legs by this much in tau before comparing. Every "
                         "Phase-4 IC stands for FLASH's t = 0.1 ns = tau 2.696, so the "
                         "default ALIGNS the handoff. Pass 0 to reproduce the unaligned "
                         "convention every RESULTS.md number before 2026-08-18 was "
                         "measured on.")
    a = ap.parse_args()

    if a.taus:
        TAUS[:] = list(a.taus)
    spec = [tuple(q.split("=", 1)) for q in a.leg] if a.leg else list(LEGS_DEFAULT)
    legs = [load_leg(lab, path, PALETTE[i % len(PALETTE)])
            for i, (lab, path) in enumerate(spec)]

    banner()
    print(f"\nManheimer steady state  T_e,SS = 5.94 mu^(1/3) Z^(-1/3) lambda^(4/3) I^(2/3)")
    print(f"  real aluminium          : {TE_REF:.0f} eV")
    print("  ^ each WarpX leg is judged against ITS OWN value below, NOT 823 eV.")
    print("\nLEGS")
    for leg in legs:
        q = absorbed(leg["path"])
        print(f"  {leg['label']:22s} {leg['path']:34s} "
              f"{'hybrid' if leg['hybrid'] else 'kinetic':8s} "
              + (f"<f_abs> {q['f_mean']:.3f}  E_abs {q['E_abs']:.4e} J/m2"
                 if q else "(no run.log)")
              + f"  | m_i/m_e {leg['sc']['mass_ratio']:6.0f}  mu {leg['sc']['mu']:6.1f}"
                f"  T_e,SS {leg['sc']['tss']:6.1f} eV"
                f"  d_i0 {leg['sc']['di0']/DE_CR:5.2f} d_e"
                f"  tau {leg['sc']['tau']*1e12:.4f} ps")
    print(f"  {'FLASH (rad off)':22s} {FLASH_DIR.split('/')[-1]:34s} "
          f"{'radhydro':8s} <f_abs> 0.870  E_abs 8.2740e+07 J/m2 "
          f"(in its own, 18.36x longer, time base)")

    os.makedirs(a.outdir, exist_ok=True)
    print(f"\n  tau offset {a.tau_offset:.3f} -- WarpX legs sampled at "
          f"(FLASH tau - {a.tau_offset:.3f}); 0 would compare states 2.7 apart")
    data, _ = collect(legs, offset=a.tau_offset)
    table(data, legs)
    figure(data, legs, os.path.join(a.outdir, "profiles.png"))
    figure_reduced(data, legs, os.path.join(a.outdir, "profiles_reduced.png"))
    history(legs, os.path.join(a.outdir, "history.png"))
    return 0




# ---------------------------------------------------------------------------------------
# The same profiles in SIMILARITY-REDUCED variables.
# ---------------------------------------------------------------------------------------
def figure_reduced(data, legs, out):
    """The same three rows, each leg divided by its OWN references.

    WHY THIS EXISTS. The mass-ratio reduction is not a rescaling of z and t alone.
    Manheimer's steady state carries T_e,SS ~ mu^(1/3), so a leg run 18.36x lighter is
    EXPECTED to sit 2.638x cooler, and its flow correspondingly slower, at the same
    normalised zeta and tau. Plotting T_e in raw eV on a shared axis therefore shows a
    2.4x "disagreement" that is the unit map working, not the codes disagreeing --
    TEST_PLAN 12.2's rule "temperatures in absolute eV" and criterion A6's 823 eV both
    predate the 2026-08-18 retraction and are stale.

    Reduced variables, each leg against ITS OWN reference:
        n_e/n_cr                            unchanged; already a similarity variable
        T_e / T_e,SS(own mu)                FLASH / 823, WarpX / 312 -- both near 1
        v_z / C_S(own MEASURED plume T_e)   removes the sqrt(T) a cool plume carries;
                                            d["v"] is v/C_S0 at the 823 eV reference, so
                                            the correction is a divide by sqrt(T/823)
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = ["FLASH"] + [q["label"] for q in legs]
    colour = {"FLASH": COLS["FLASH"]}
    style = {"FLASH": ("-", 2.0)}
    for j, leg in enumerate(legs):
        colour[leg["label"]] = leg["colour"]
        style[leg["label"]] = (("--", "-.", ":")[j % 3], 1.5)
    ss_of = {q["label"]: q["sc"]["tss"] for q in legs}
    ref_ss = {n: (TE_REF if n == "FLASH" else ss_of.get(n, TSS_REDUCED)) for n in names}

    n = len(TAUS)
    fig, ax = plt.subplots(3, n, figsize=(3.5 * n, 9.6), sharex=True)
    for c, tau in enumerate(TAUS):
        for name in names:
            d = data[tau].get(name)
            if d is None:
                continue
            ls, lw = style[name]
            inb = np.isfinite(d["ne"]) & (d["ne"] >= BAND[0]) & (d["ne"] <= BAND[1])
            ax[0, c].semilogy(d["zeta"], np.maximum(d["ne"], 1e-9), color=colour[name],
                              lw=lw, ls=ls, label=name)
            # the density-weighted plume T_e of THIS leg at THIS tau sets both corrections
            Tp = scalars(d["zeta"], d["ne"], d["Te"], d["v"]).get("Te_mean_plume", np.nan)
            rows = []
            if d["Te"] is not None:
                rows.append((1, np.asarray(d["Te"], float) / ref_ss[name]))
            if d["v"] is not None and np.isfinite(Tp) and Tp > 0:
                rows.append((2, np.asarray(d["v"], float) / np.sqrt(Tp / TE_REF)))
            for r, y in rows:
                ax[r, c].plot(d["zeta"], np.where(inb, y, np.nan), color=colour[name],
                              lw=lw, ls=ls)
                ax[r, c].plot(d["zeta"], np.where(inb, np.nan, y), color=colour[name],
                              lw=lw * 0.7, ls=ls, alpha=0.20)
        ax[0, c].axhline(1.0, color="0.4", ls=":", lw=0.9)
        ax[0, c].set_ylim(1e-4, 5e3)
        ax[0, c].set_title(rf"$\tau$ = {tau:.1f}", loc="left", fontsize=9.5,
                           fontweight="bold")
        ax[1, c].axhline(1.0, color="0.35", ls="--", lw=1.0)
        ax[1, c].set_ylim(0, 2.6)
        ax[2, c].set_ylim(-0.5, 8.0)
        ax[2, c].axhline(0.0, color="0.7", lw=0.7)
        ax[2, c].set_xlabel(r"$\zeta = z/d_{i0}$")
        for r in range(3):
            ax[r, c].set_xlim(-8, 110)
            ax[r, c].grid(alpha=0.15)
            if c:
                ax[r, c].tick_params(labelleft=False)
    ax[0, 0].set_ylabel(r"$n_e/n_{cr}$")
    ax[1, 0].set_ylabel(r"$T_e\ /\ T_{e,SS}(\mathrm{own}\ \mu)$")
    ax[2, 0].set_ylabel(r"$v_z\ /\ C_S(\mathrm{own\ measured}\ T_e)$")
    ax[0, 0].legend(loc="lower left", fontsize=8, framealpha=0.9)
    ax[1, 0].text(0.03, 1.0, " each leg's own Manheimer value",
                  transform=ax[1, 0].get_yaxis_transform(), va="bottom", fontsize=7,
                  color="0.25")
    # Dedupe: when every WarpX leg shares an ion mass -- which is again the case now that
    # the m_i = 100 legs are out of the default set -- listing it once per leg overflows
    # the title with five copies of the same string.
    uniq = sorted({(q["sc"]["mass_ratio"], round(q["sc"]["tss"], 1)) for q in legs})
    ss_txt = ", ".join(f"$m_i/m_e$={m:.0f}$\\to${t:.0f} eV" for m, t in uniq)
    # Two short lines, not one long one: the single-line version ran off BOTH edges of a
    # 5-panel figure and lost its first and last words.
    fig.suptitle("SIMILARITY-REDUCED -- each leg against its OWN $T_{e,SS}(\\mu)$ and its "
                 "own measured sound speed.\n"
                 f"$T_{{e,SS}}\\propto\\mu^{{1/3}}$, so a lighter leg is EXPECTED cooler: "
                 f"FLASH$\\to$823 eV, {ss_txt}.  What remains here is real disagreement.",
                 fontsize=9.5, y=0.998)
    fig.tight_layout(rect=(0, 0, 1, 0.972))
    fig.savefig(out, dpi=135)
    print(f"  figure: {out}")

if __name__ == "__main__":
    raise SystemExit(main())
