"""Derived scales for a LaserProdShock run — everything hangs off the wavelength.

``runs/<ID>/config.yaml`` holds only PRIMARY quantities; everything the analysis and
the deck need beyond them is computed HERE, so there is exactly one source of truth
and no risk of a script drifting out of sync with the deck.

THE ONE THING THAT MAKES A LASER RUN DIFFERENT from the heater-driven runs of
``../KinShock2020/``: inverse-bremsstrahlung absorption is measured against the
critical density ``n_cr = eps0 m_e omega^2 / e^2``, so the laser **pins the absolute
density scale**. A scale-free heater run cannot be relabelled as a laser run. Every
density in this project is therefore expressed in ``n_cr``.

A pleasant consequence: since ``omega_pe = omega_0`` exactly when ``n_e = n_cr``, the
electron skin depth at critical density is

    d_e,cr = c/omega_0 = lambda_0 / (2 pi)

Pure Python (``math`` only), so it imports and runs without yt / numpy — which keeps
the units tests fast and dependency-free.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict

# --- physical constants (SI, CODATA-ish; match WarpX's PhysConst) ---
ME = 9.1093837015e-31      # electron mass [kg]
QE = 1.602176634e-19       # elementary charge [C]
C = 299792458.0            # speed of light [m/s]
EPS0 = 8.8541878128e-12    # vacuum permittivity [F/m]
MU0 = 1.25663706212e-6     # vacuum permeability [H/m]
KB = 1.380649e-23          # Boltzmann constant [J/K]
HBAR = 1.0545718176461565e-34  # reduced Planck constant [J s] (de Broglie b_min)
ME_C2_J = ME * C * C       # electron rest energy [J]
ME_C2_EV = ME_C2_J / QE    # electron rest energy [eV] (~511 keV)


# --------------------------------------------------------------------------- #
# elementary relations
# --------------------------------------------------------------------------- #
def omega_of_lambda(lam0: float) -> float:
    """Laser angular frequency [rad/s] for a vacuum wavelength [m]."""
    return 2.0 * math.pi * C / lam0


def critical_density(lam0: float) -> float:
    """n_cr = eps0 m_e omega^2 / e^2 [m^-3] for a vacuum wavelength [m]."""
    w = omega_of_lambda(lam0)
    return EPS0 * ME * w * w / (QE * QE)


def omega_pe(n_e: float) -> float:
    """Electron plasma frequency [rad/s] at density ``n_e`` [m^-3]."""
    return math.sqrt(n_e * QE * QE / (EPS0 * ME))


def skin_depth(n_e: float) -> float:
    """Electron skin depth c/omega_pe [m] at density ``n_e`` [m^-3]."""
    return C / omega_pe(n_e)


def debye_length(n_e: float, theta: float) -> float:
    """Electron Debye length [m] = sqrt(theta) * d_e, theta = k_B T_e/(m_e c^2)."""
    return math.sqrt(max(theta, 0.0)) * skin_depth(n_e)


def sound_speed(theta_e: float, mass_ratio: float, Z: float = 1.0) -> float:
    """Ion-acoustic speed sqrt(Z k_B T_e/m_i) [m/s] from theta_e and m_i/m_e."""
    return math.sqrt(Z * theta_e / mass_ratio) * C


# lnLambda modes the operator accepts (`laser_deposition.coulomb_log_mode`), in its
# order. Mirrored by config.COULOMB_LOG_MODES so validate() can reject a typo.
COULOMB_LOG_MODES = ("constant", "nrl", "flash", "ib")


def coulomb_log_for(mode: str, n_e: float, theta_e: float, Z_eff: float,
                    wavelength: float, coulomb_log: float = 2.0) -> float:
    """lnLambda for IB absorption -- the mirror of the operator's ``coulombLog``.

    This has to agree with ``LaserDeposition.cpp``'s ``coulombLog`` to round-off,
    because every prediction here (the gates, ``absorption_panel``, ``Scales``) is
    compared against what the operator measures. ``tests/test_units.py`` pins all four
    modes against values read back out of an actual run's profile dump.

    ``constant``
        ``coulomb_log`` everywhere. A deliberate knob, not merely a fallback: lnLambda
        is how a reduced-parameter run dials collisionality to a target, and pinning it
        is the only way to hold that fixed while something else varies.
    ``nrl``
        NRL formulary electron-ion, two branches split at ``T_e = 10 Z_eff^2`` eV. This
        is the **transport** logarithm, not the absorption one -- it is here to
        cross-validate against PSC's ray-trace module, which uses it for IB.
    ``flash``
        ``ln(b_max/b_min)``, ``b_max`` the electron Debye length and ``b_min`` the larger
        of the classical turning radius and the de Broglie length: Eqs. (11)-(13) of
        Lezhnin et al., Phys. Plasmas 32, 022701 (2025), i.e. FLASH's IB logarithm.
    ``ib``
        the same with ``b_max = v_th/max(omega_pe, omega_laser)``. Below critical the
        laser frequency wins, so lnLambda SATURATES at its critical-surface value
        instead of growing logarithmically out into the tenuous corona -- an encounter
        lasting longer than ``1/omega`` is adiabatic and absorbs nothing. This is the
        physically correct cutoff for IB, and correction (I) that Lezhnin et al.
        recommend over the FLASH operator they were constrained to use. Identical to
        ``flash`` wherever the plasma is overdense.

    Floored at 1, and 1 where there is no plasma (as PSC's ``get_lnlambda`` does).
    """
    if mode == "constant":
        return coulomb_log
    if mode not in COULOMB_LOG_MODES:
        raise ValueError(f"coulomb_log_mode must be one of "
                         f"{'|'.join(COULOMB_LOG_MODES)} (got {mode!r})")
    kT = theta_e * ME_C2_J
    if n_e <= 0.0 or kT <= 0.0:
        return 1.0
    if mode == "nrl":
        Te_eV = kT / QE
        ne_cm = n_e * 1e-6
        v = (23.0 - math.log(math.sqrt(ne_cm) * Z_eff / Te_eV ** 1.5)
             if Te_eV <= 10.0 * Z_eff ** 2
             else 24.0 - math.log(math.sqrt(ne_cm) / Te_eV))
        return max(v, 1.0)
    b_min = max(Z_eff * QE ** 2 / (12.0 * math.pi * EPS0 * kT),
                HBAR / math.sqrt(3.0 * kT * ME))
    w_pe = omega_pe(n_e)
    w_cut = max(w_pe, omega_of_lambda(wavelength)) if mode == "ib" else w_pe
    return max(math.log(math.sqrt(kT / ME) / w_cut / b_min), 1.0)


def nu_ei_ib(n_e: float, theta_e: float, Z_eff: float, coulomb_log: float) -> float:
    """High-frequency (laser) electron-ion collision frequency [s^-1].

    The form the operator uses (``Docs/source/usage/parameters.rst``, "Laser
    deposition"):

        nu_ei = (4/3) sqrt(2 pi) Z_eff e^4 n_e lnLambda
                / [ (4 pi eps0)^2 sqrt(m_e) (k_B T_e)^{3/2} ]

    NOTE this is the Johnston-type IB collision frequency, **not** the NRL/Braginskii
    transport rate that ``kinshock.units.nu_ei`` uses for Coulomb collisions. They
    differ by an O(1) coefficient and are not interchangeable.
    """
    kT = theta_e * ME_C2_J
    if kT <= 0.0:
        return float("inf")
    return ((4.0 / 3.0) * math.sqrt(2.0 * math.pi)
            * Z_eff * QE ** 4 * n_e * coulomb_log
            / ((4.0 * math.pi * EPS0) ** 2 * math.sqrt(ME) * kT ** 1.5))


def theta_group(n_targ: float, theta_targ: float,
                n_amb: float | None, theta_amb: float | None) -> float:
    """Density-weighted GROUP electron temperature, as the operator measures it.

    ``laser_deposition.species`` lists every electron population that (a) is heated and
    (b) contributes to ``n_e`` -- the operator does not let those be separated. In
    ``temperature_mode = local`` it forms one *group* temperature from the combined
    moments, so a hot ambient raises the temperature that ``K ~ T_e^{-3/2}`` sees even
    where the cold target dominates the density.

    This matters enormously and was measured, not assumed: with a 0.06 n_cr ambient at
    theta = 5e-3 against a target at theta = 1e-4, the group temperature in the CORONA
    (where the tau = 1 surface actually sits) is ~25x the target's, so K falls 43-129x
    and the measured absorbed fraction dropped from 1.000 (vacuum) to 0.28. A prediction
    evaluated at the target's cold theta is wrong by that factor -- see RESULTS
    2026-07-28.
    """
    if not n_amb or theta_amb is None:
        return theta_targ
    tot = n_targ + n_amb
    return (n_targ * theta_targ + n_amb * theta_amb) / tot if tot > 0 else theta_targ


def K_ib(n_e: float, theta_e: float, n_cr: float, Z_eff: float,
         coulomb_log: float, mode: str = "constant") -> float:
    """Inverse-bremsstrahlung absorption coefficient K [1/m].

        K = (nu_ei/c) (n_e/n_cr) / sqrt(1 - n_e/n_cr)

    so K ~ Z_eff lnLambda n_e^2 T_e^{-3/2}, singular at the critical surface (the
    operator integrates that singularity analytically over a locally linear ramp).
    Returns ``inf`` at or above critical density.

    ``mode`` selects how lnLambda is obtained (see :func:`coulomb_log_for`); the
    default ``constant`` uses ``coulomb_log`` and leaves every existing caller
    unchanged. No wavelength argument is needed even for mode ``ib``, because the
    laser frequency IS ``omega_pe(n_cr)`` -- that is what critical density means.
    """
    x = n_e / n_cr
    if x >= 1.0:
        return float("inf")
    lnL = coulomb_log_for(mode, n_e, theta_e, Z_eff,
                          2.0 * math.pi * C / omega_pe(n_cr), coulomb_log)
    return (nu_ei_ib(n_e, theta_e, Z_eff, lnL) / C) * x / math.sqrt(1.0 - x)


# --------------------------------------------------------------------------- #
# derived scales
# --------------------------------------------------------------------------- #
@dataclass
class Scales:
    """Derived physical + normalized scales for one run.

    SI unless the name carries a unit suffix. Speeds are also reported as fractions
    of c, temperatures as theta = kT/(m_e c^2), densities also in n_cr.
    Fields that need an ambient plasma or a background field are ``None`` for a
    vacuum run (Phase 1) or an unmagnetized run (Phase 2A).
    """

    # --- laser / reference ---
    lam0: float               # vacuum wavelength [m]
    omega0: float             # angular frequency [rad/s]
    n_cr: float               # critical density [m^-3]
    de_cr: float              # skin depth at n_cr = lam0/(2 pi) [m]
    intensity: float          # incident intensity [W/m^2]
    mass_ratio: float
    mi: float                 # ion mass [kg]

    # --- length reference (which d_e the config's lengths are quoted in) ---
    length_scale: str         # 'critical' | 'target' | 'ambient'
    de_ref: float             # d_e,ref [m]

    # --- target ---
    n_targ: float             # target peak density [m^-3]
    n_targ_over_ncr: float
    de_targ: float
    theta_e_targ: float       # initial target electron theta
    theta_e_group: float      # density-weighted GROUP theta at the target peak
    Cs_targ: float            # ion-acoustic speed at theta_e_targ [m/s]
    thickness: float          # flat-top thickness [m]
    scale_length: float       # coronal Gaussian scale length [m]
    areal_ne: float           # areal electron density n_targ*thickness [m^-2]

    # --- geometry / numerics ---
    dims: int
    dz: float                 # cell size along the propagation axis [m]
    dx: float | None          # transverse cell size [m] (2D only)
    dt: float                 # timestep [s]
    n_cell: tuple             # (nz,) in 1D, (nx, nz) in 2D
    domain_lo: float          # axis lo [m]
    domain_hi: float          # axis hi [m]
    max_step: int
    t_end: float              # max_step * dt [s]

    # --- numerical health (gates G1, G2) ---
    wpe_dt_targ: float        # omega_pe(target) * dt, initial
    wpe_dt_peak: float        # ... at the assumed peak compression
    n_over_ncr_at_wpe_dt_2: float   # density (in n_cr) where omega_pe*dt = 2
    dz_over_lD_targ: float    # dz/lambda_D in the cold target
    dz_over_lD_amb: float | None

    # --- absorption estimate (before running) ---
    K_targ: float             # K at target peak density & initial theta [1/m]
    abs_depth_targ: float     # 1/K [m]
    tau_est: float            # optical depth through the flat top (one pass)
    f_abs_est: float          # 1 - exp(-2 tau): double pass w/ critical reflection
    # The lnLambda that actually went into K_targ. Worth carrying explicitly: in a
    # per-cell mode it is nothing the config states, and it is the single largest
    # multiplier on K -- 2 vs 7 is a 3.6x change in absorption.
    coulomb_log_targ: float = 2.0

    # --- ambient (None for a vacuum run) ---
    n_amb: float | None = None
    n_amb_over_ncr: float | None = None
    de_amb: float | None = None
    di_amb: float | None = None
    theta_e_amb: float | None = None
    Cs_amb: float | None = None
    tau_amb: float | None = None      # optical depth of the ambient traverse
    f_abs_amb: float | None = None    # fraction of the beam eaten before the target

    # --- background field (None when B0 = 0) ---
    B0: float | None = None
    vA: float | None = None
    wci0: float | None = None
    wci0_inv: float | None = None
    v_ms: float | None = None         # sqrt(vA^2 + Cs_amb^2)
    beta_amb: float | None = None
    rho_i0: float | None = None       # v_p/wci0, the z* normalization [m]
    vp_model: float | None = None     # assumed/target piston speed [m/s]
    MA: float | None = None
    Mms: float | None = None
    steps_per_wci0: float | None = None
    n_gyroperiods: float | None = None

    _meta: dict = field(default_factory=dict)

    # ---- normalization helpers (SI -> project units) ----
    def z_over_de(self, z):      return _div(z, self.de_ref)
    def z_over_di0(self, z):     return _div(z, self.di_amb)
    def z_over_rho_i0(self, z):  return _div(z, self.rho_i0)
    def t_wci0(self, t):         return _mul(t, self.wci0)
    def t_ps(self, t):           return _mul(t, 1e12)
    def v_over_c(self, v):       return _div(v, C)
    def v_over_vA(self, v):      return _div(v, self.vA)
    def v_over_Cs(self, v):      return _div(v, self.Cs_targ)
    def n_over_ncr(self, n):     return _div(n, self.n_cr)
    def n_over_namb(self, n):    return _div(n, self.n_amb)
    def b_over_b0(self, b):      return _div(b, self.B0)

    def report(self) -> dict:
        d = asdict(self)
        d.pop("_meta", None)
        d["intensity_W_cm2"] = self.intensity / 1e4
        d["n_cr_cm3"] = self.n_cr / 1e6
        d["Te_targ_eV"] = self.theta_e_targ * ME_C2_EV
        d["Cs_targ_over_c"] = self.Cs_targ / C
        d["de_cr_um"] = self.de_cr * 1e6
        d["de_ref_um"] = self.de_ref * 1e6
        d["domain_de"] = (self.domain_hi - self.domain_lo) / self.de_ref
        if self.vA is not None:
            d["vA_over_c"] = self.vA / C
            d["rho_i0_over_de"] = self.rho_i0 / self.de_ref
            d["wci0_inv_ps"] = self.wci0_inv * 1e12
        if self.di_amb is not None:
            d["di_amb_um"] = self.di_amb * 1e6
        d["dt_fs"] = self.dt * 1e15
        d["t_end_ps"] = self.t_end * 1e12
        return d

    def pretty(self) -> str:
        r = self.report()
        out = [f"Scales for run {self._meta.get('run_id', '?')} "
               f"(phase {self._meta.get('phase', '?')}, {self.dims}D):"]

        def add(section, keys):
            out.append(f"  --- {section} ---")
            for k in keys:
                v = r.get(k)
                if v is None:
                    continue
                out.append(f"    {k:26s} = {v:.5g}" if isinstance(v, (int, float))
                           else f"    {k:26s} = {v}")

        add("laser", ["lam0", "n_cr", "n_cr_cm3", "de_cr_um", "intensity",
                      "intensity_W_cm2"])
        add("target", ["n_targ_over_ncr", "Te_targ_eV", "theta_e_group",
                       "Cs_targ_over_c",
                       "areal_ne", "coulomb_log_targ", "K_targ",
                       "abs_depth_targ", "tau_est", "f_abs_est"])
        add("ambient", ["n_amb_over_ncr", "de_amb", "di_amb_um", "tau_amb",
                        "f_abs_amb"])
        add("field", ["B0", "vA_over_c", "wci0_inv_ps", "v_ms", "beta_amb",
                      "rho_i0", "rho_i0_over_de", "MA", "Mms"])
        add("grid", ["dims", "dz", "dx", "domain_de", "dt_fs", "max_step",
                     "t_end_ps", "n_gyroperiods", "steps_per_wci0"])
        add("gates", ["wpe_dt_targ", "wpe_dt_peak", "n_over_ncr_at_wpe_dt_2",
                      "dz_over_lD_targ", "dz_over_lD_amb"])
        out.append(f"    {'n_cell':26s} = {self.n_cell}")
        return "\n".join(out)


def _div(x, y):
    if y is None:
        return None
    try:
        return [xi / y for xi in x]
    except TypeError:
        return x / y


def _mul(x, y):
    if y is None:
        return None
    try:
        return [xi * y for xi in x]
    except TypeError:
        return x * y


# --------------------------------------------------------------------------- #
# geometry helpers — dimension-general (1D: z only; 2D: WarpX XZ ordering)
# --------------------------------------------------------------------------- #
def axis_names(dims: int) -> list[str]:
    """WarpX mesh-coordinate order: ('z',) in 1D, ('x', 'z') in 2D, xyz in 3D.

    The deck writes ``amr.n_cell``, ``geometry.prob_lo/hi`` and the boundary tokens
    in this order, so every dimension-general list in :mod:`laserprod.deck` is built
    from it.
    """
    return {1: ["z"], 2: ["x", "z"], 3: ["x", "y", "z"]}[int(dims)]


def cells_and_extent(geo: dict, de_ref: float):
    """((n_cell...), (lo...), (hi...), dz, dx) in WarpX axis order.

    The config gives the propagation-axis extent in ``geometry.axis.{lo_de,hi_de}``
    and, in 2D, the transverse extent in ``geometry.transverse.{lo_de,hi_de}``;
    ``dz_over_de`` sets the propagation-axis cell and ``dx_over_dz`` the transverse
    aspect (1.0 = square cells, which is what the ray tracer's ``ray_cfl`` assumes
    since its arc-length step keys off the *smallest* cell).
    """
    dims = int(geo["dims"])
    dz = float(geo["dz_over_de"]) * de_ref
    ax = geo["axis"]
    z_lo, z_hi = float(ax["lo_de"]) * de_ref, float(ax["hi_de"]) * de_ref
    nz = int(round((z_hi - z_lo) / dz))

    if dims == 1:
        return (nz,), (z_lo,), (z_hi,), dz, None

    dx = float(geo.get("dx_over_dz", 1.0)) * dz
    tr = geo["transverse"]
    x_lo, x_hi = float(tr["lo_de"]) * de_ref, float(tr["hi_de"]) * de_ref
    nx = int(round((x_hi - x_lo) / dx))
    # WarpX XZ ordering: (x, z)
    return (nx, nz), (x_lo, z_lo), (x_hi, z_hi), dz, dx


def timestep(cfl: float, dz: float, dx: float | None) -> float:
    """WarpX Yee CFL timestep: dt = cfl / (c sqrt(sum 1/dx_d^2))."""
    inv2 = 1.0 / (dz * dz) + (1.0 / (dx * dx) if dx else 0.0)
    return cfl / (C * math.sqrt(inv2))


# --------------------------------------------------------------------------- #
# the main entry point
# --------------------------------------------------------------------------- #
def derive(cfg: dict) -> Scales:
    """Compute all derived scales from a loaded config dict."""
    las, ref = cfg["laser"], cfg["reference"]
    tgt = cfg["plasma"]["target"]
    amb = (cfg["plasma"].get("ambient") or None)
    geo, num = cfg["geometry"], cfg["numerics"]
    fld = cfg.get("field") or {}

    lam0 = float(las["wavelength_um"]) * 1e-6
    w0 = omega_of_lambda(lam0)
    n_cr = critical_density(lam0)
    de_cr = C / w0                                   # == lam0/(2 pi)
    intensity = float(las["intensity"])

    mass_ratio = float(ref["mass_ratio"])
    mi = mass_ratio * ME
    Z = float(ref.get("charge_state", 1))

    n_targ = float(tgt["density_over_ncr"]) * n_cr
    de_targ = skin_depth(n_targ)
    theta_e_targ = float(tgt["theta_e_init"])

    n_amb = float(amb["density_over_ncr"]) * n_cr if amb else None
    de_amb = skin_depth(n_amb) if n_amb else None
    theta_e_amb = float(amb["theta_e"]) if amb else None

    # --- which d_e the config's lengths mean (the project's most confusable
    #     quantity -- see TEST_PLAN.md 2.1) ---
    length_scale = str(ref.get("length_scale") or ("ambient" if amb else "critical"))
    de_ref = {"critical": de_cr, "target": de_targ, "ambient": de_amb}[length_scale]
    if de_ref is None:
        raise ValueError("reference.length_scale = 'ambient' but the config has no "
                         "plasma.ambient block (a vacuum run must use 'critical' "
                         "or 'target')")

    # --- geometry / numerics ---
    n_cell, lo, hi, dz, dx = cells_and_extent(geo, de_ref)
    dt = timestep(float(num["cfl"]), dz, dx)
    max_step = int(num["max_step"])
    dims = int(geo["dims"])
    z_lo, z_hi = lo[-1], hi[-1]                      # propagation axis is last

    thickness = float(tgt["thickness_de"]) * de_ref
    scale_length = float(tgt.get("scale_length_de", 0.0)) * de_ref

    # --- gates G1/G2 ---
    compression = float((cfg.get("gates") or {}).get("compression_factor", 2.0))
    wpe_dt_targ = omega_pe(n_targ) * dt
    wpe_dt_peak = omega_pe(n_targ * compression) * dt
    # omega_pe ~ sqrt(n), so the density at which omega_pe*dt = 2:
    n_at_2 = n_targ * (2.0 / wpe_dt_targ) ** 2 / n_cr
    dz_over_lD_targ = dz / debye_length(n_targ, theta_e_targ)
    dz_over_lD_amb = (dz / debye_length(n_amb, theta_e_amb)) if amb else None

    # --- absorption estimate (pre-run sanity: will this target even absorb?) ---
    Z_eff = float(las.get("Z_eff", 1.0))
    lnL = float(las.get("coulomb_log", 2.0))
    # lnLambda may be per-cell; every K below must use the same mode the deck will,
    # or the predicted absorption is a prediction of a different operator.
    lnL_mode = str(las.get("coulomb_log_mode", "constant"))
    # Evaluate K at the GROUP temperature the operator will actually measure, not at the
    # target's cold theta: with an ambient in the heated species list the group theta in
    # the corona is far hotter and K falls by 1-2 orders of magnitude (see theta_group).
    th_grp_targ = theta_group(n_targ, theta_e_targ, n_amb, theta_e_amb)
    n_at_targ = min(n_targ + (n_amb or 0.0), 0.999 * n_cr)
    K_targ = K_ib(n_at_targ, th_grp_targ, n_cr, Z_eff, lnL, lnL_mode)
    abs_depth = 1.0 / K_targ if K_targ > 0 else float("inf")
    tau_est = K_targ * thickness
    f_abs_est = 1.0 - math.exp(-2.0 * min(tau_est, 500.0))

    tau_amb = f_abs_amb = None
    if amb:
        # the beam crosses the ambient from the injection face to the target
        z_t = float(tgt.get("center_de", 0.0)) * de_ref
        path = abs((z_hi if str(las.get("inject_side", "lo")) == "hi" else z_lo) - z_t)
        tau_amb = K_ib(n_amb, theta_e_amb, n_cr, Z_eff, lnL, lnL_mode) * path
        f_abs_amb = 1.0 - math.exp(-min(tau_amb, 500.0))

    Cs_targ = sound_speed(theta_e_targ, mass_ratio, Z)
    Cs_amb = sound_speed(theta_e_amb, mass_ratio, Z) if amb else None

    # --- background field ---
    B0 = vA = wci0 = wci0_inv = v_ms = beta_amb = None
    rho_i0 = vp_model = MA = Mms = steps_per_wci0 = n_gyro = None
    orientation = str(fld.get("orientation", "none"))
    vA_over_c = float(fld.get("vA_over_c", 0.0) or 0.0)
    if orientation != "none" and vA_over_c and n_amb:
        vA = vA_over_c * C
        B0 = vA * math.sqrt(MU0 * n_amb * mi)
        wci0 = QE * B0 / mi
        wci0_inv = 1.0 / wci0
        v_ms = math.sqrt(vA * vA + Cs_amb * Cs_amb)
        beta_amb = 2.0 * MU0 * n_amb * theta_e_amb * ME_C2_J / (B0 * B0)
        # the piston speed the run is designed around: measured value if the config
        # declares one, else the ablation estimate alpha*Cs (alpha ~ 3).
        vp_over_c = (cfg.get("targets") or {}).get("vp_over_c")
        vp_model = (float(vp_over_c) * C if vp_over_c
                    else float((cfg.get("model") or {}).get("alpha_cs", 3.0)) * Cs_targ)
        rho_i0 = vp_model / wci0
        MA = vp_model / vA
        Mms = vp_model / v_ms
        steps_per_wci0 = wci0_inv / dt
        n_gyro = max_step * dt * wci0

    di_amb = de_amb * math.sqrt(mass_ratio) if de_amb else None

    return Scales(
        lam0=lam0, omega0=w0, n_cr=n_cr, de_cr=de_cr, intensity=intensity,
        mass_ratio=mass_ratio, mi=mi,
        length_scale=length_scale, de_ref=de_ref,
        n_targ=n_targ, n_targ_over_ncr=n_targ / n_cr, de_targ=de_targ,
        theta_e_targ=theta_e_targ, theta_e_group=th_grp_targ, Cs_targ=Cs_targ,
        thickness=thickness, scale_length=scale_length,
        areal_ne=n_targ * thickness,
        dims=dims, dz=dz, dx=dx, dt=dt, n_cell=n_cell,
        domain_lo=z_lo, domain_hi=z_hi, max_step=max_step, t_end=max_step * dt,
        wpe_dt_targ=wpe_dt_targ, wpe_dt_peak=wpe_dt_peak,
        n_over_ncr_at_wpe_dt_2=n_at_2,
        dz_over_lD_targ=dz_over_lD_targ, dz_over_lD_amb=dz_over_lD_amb,
        K_targ=K_targ, abs_depth_targ=abs_depth, tau_est=tau_est,
        f_abs_est=f_abs_est,
        coulomb_log_targ=coulomb_log_for(
            lnL_mode, n_at_targ, th_grp_targ, Z_eff,
            2.0 * math.pi * C / omega_pe(n_cr), lnL),
        n_amb=n_amb, n_amb_over_ncr=(n_amb / n_cr) if n_amb else None,
        de_amb=de_amb, di_amb=di_amb, theta_e_amb=theta_e_amb, Cs_amb=Cs_amb,
        tau_amb=tau_amb, f_abs_amb=f_abs_amb,
        B0=B0, vA=vA, wci0=wci0, wci0_inv=wci0_inv, v_ms=v_ms,
        beta_amb=beta_amb, rho_i0=rho_i0, vp_model=vp_model, MA=MA, Mms=Mms,
        steps_per_wci0=steps_per_wci0, n_gyroperiods=n_gyro,
        _meta=dict(cfg.get("meta", {})),
    )
