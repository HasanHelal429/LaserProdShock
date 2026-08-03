"""Fast checks on laserprod.units — the relations everything else is built on."""

from __future__ import annotations

import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laserprod import units as u   # noqa: E402


LAM = 1.053e-6


def test_de_cr_is_lambda_over_two_pi():
    """d_e at critical density is EXACTLY lam0/(2 pi).

    Because n_e = n_cr is the definition of the density at which omega_pe = omega_0,
    so d_e = c/omega_pe = c/omega_0 = lam0/(2 pi). This is the identity the whole
    length convention rests on, and it is worth a test because it is the kind of
    thing that looks like an approximation.
    """
    n_cr = u.critical_density(LAM)
    assert u.skin_depth(n_cr) == pytest.approx(LAM / (2 * math.pi), rel=1e-12)
    assert u.omega_pe(n_cr) == pytest.approx(u.omega_of_lambda(LAM), rel=1e-12)


def test_critical_density_value():
    """n_cr(1.053 um) = 1.005e27 m^-3, the number every density in the project
    is quoted against."""
    assert u.critical_density(LAM) == pytest.approx(1.005e27, rel=2e-3)
    # n_cr ~ lam^-2
    assert (u.critical_density(LAM / 2) / u.critical_density(LAM)
            == pytest.approx(4.0, rel=1e-12))


def test_schaeffer_table_i_in_n_cr():
    """Schaeffer 2020's Table I densities land in a natural range for a 1 um laser.

    Ablation 6e20 cm^-3 -> 0.6 n_cr, upstream 4.8e18 cm^-3 -> 0.0048 n_cr. Recorded
    as a test because it is the reason a real laser can be placed in the paper's
    regime at all (TEST_PLAN.md 2.1).
    """
    n_cr = u.critical_density(LAM)
    assert 6e26 / n_cr == pytest.approx(0.6, abs=0.02)
    assert 4.8e24 / n_cr == pytest.approx(0.0048, abs=1e-4)


def test_ib_coefficient_exponents():
    """K ~ Z_eff^1 lnLambda^1 n_e^2 T_e^{-3/2}.

    The operator's own coefficient audit measured 2.018 / 0.9999 / 0.9999 / -1.4999
    on (n_e, Z_eff, lnLambda, T_e). This checks the *analytic* reference used by the
    pre-run absorption estimate reproduces the same exponents, so a discrepancy
    against the operator can never be blamed on this side of the comparison.
    """
    n_cr = u.critical_density(LAM)
    n0, th0, Z0, lnL0 = 0.01 * n_cr, 1e-3, 2.0, 5.0

    def K(n=n0, th=th0, Z=Z0, lnL=lnL0):
        return u.K_ib(n, th, n_cr, Z, lnL)

    def slope(f, x0, key):
        y1, y2 = f(**{key: x0}), f(**{key: 1.01 * x0})
        return math.log(y2 / y1) / math.log(1.01)

    # n_e enters as n_e^2 / sqrt(1 - n_e/n_cr); at n_e << n_cr the exponent is 2.
    assert slope(K, n0, "n") == pytest.approx(2.0, abs=0.02)
    assert slope(K, Z0, "Z") == pytest.approx(1.0, abs=1e-6)
    assert slope(K, lnL0, "lnL") == pytest.approx(1.0, abs=1e-6)
    assert slope(K, th0, "th") == pytest.approx(-1.5, abs=1e-6)


def test_ib_singular_at_critical():
    """K diverges at the critical surface (the 1/sqrt(1 - n/n_cr) path-length factor),
    which is why the operator integrates that layer analytically."""
    n_cr = u.critical_density(LAM)
    k_far = u.K_ib(0.5 * n_cr, 1e-3, n_cr, 1.0, 2.0)
    k_near = u.K_ib(0.999 * n_cr, 1e-3, n_cr, 1.0, 2.0)
    assert k_near > 10 * k_far
    assert u.K_ib(n_cr, 1e-3, n_cr, 1.0, 2.0) == float("inf")


def test_debye_and_sound_speed():
    n = 1e26
    assert u.debye_length(n, 1e-4) == pytest.approx(0.01 * u.skin_depth(n), rel=1e-12)
    # C_s = sqrt(Z theta/mu) c
    assert u.sound_speed(1e-4, 100.0) == pytest.approx(1e-3 * u.C, rel=1e-12)


def test_timestep_1d_and_2d():
    """dt = cfl/(c sqrt(sum 1/dx^2)): 1D reduces to cfl*dz/c, and square 2D cells pick
    up the 1/sqrt(2) that is the reason 2D decks can use a larger nominal cfl."""
    dz = 1e-7
    assert u.timestep(0.35, dz, None) == pytest.approx(0.35 * dz / u.C, rel=1e-12)
    assert (u.timestep(0.5, dz, dz)
            == pytest.approx(0.5 * dz / (u.C * math.sqrt(2)), rel=1e-12))


def test_axis_names_and_extent_are_dimension_general():
    """WarpX mesh-coordinate order, and the propagation axis last in every dimension."""
    assert u.axis_names(1) == ["z"]
    assert u.axis_names(2) == ["x", "z"]
    assert u.axis_names(3) == ["x", "y", "z"]

    de = 1e-7
    geo1 = {"dims": 1, "axis": {"lo_de": -100, "hi_de": 100}, "dz_over_de": 0.5}
    n, lo, hi, dz, dx = u.cells_and_extent(geo1, de)
    assert n == (400,) and dx is None
    assert lo == (-100 * de,) and hi == (100 * de,)

    geo2 = dict(geo1, dims=2, transverse={"lo_de": -20, "hi_de": 20},
                dx_over_dz=1.0)
    n, lo, hi, dz, dx = u.cells_and_extent(geo2, de)
    assert n == (80, 400)                      # (nx, nz)
    assert lo == (-20 * de, -100 * de)
    assert dx == pytest.approx(dz)


def _cfg(**over):
    cfg = {
        "meta": {"run_id": "t"},
        "laser": {"wavelength_um": 1.053, "intensity": 1e18, "direction": "z",
                  "inject_side": "hi", "Z_eff": 5.0, "coulomb_log": 5.0},
        "reference": {"mass_ratio": 100.0, "charge_state": 1},
        "plasma": {"target": {"density_over_ncr": 1.5, "thickness_de": 20,
                              "scale_length_de": 15, "theta_e_init": 1e-4,
                              "center_de": -50},
                   "ambient": {"density_over_ncr": 0.06, "theta_e": 5e-3}},
        "field": {"orientation": "perpendicular", "vA_over_c": 0.003},
        "geometry": {"dims": 1, "normal_axis": "z",
                     "axis": {"lo_de": -100, "hi_de": 100}, "dz_over_de": 0.5},
        "numerics": {"cfl": 0.35, "max_step": 24000,
                     "ppc": {"target": 200, "ambient": 48}},
    }
    for k, v in over.items():
        cfg[k] = v
    return cfg


def test_length_scale_selects_the_right_de():
    """reference.length_scale picks WHICH d_e the config's lengths mean.

    This is the project's most confusable quantity (TEST_PLAN.md 2.1), so all three
    choices are pinned, including that 'ambient' really is sqrt(n_targ/n_amb) times
    'target'.
    """
    n_cr = u.critical_density(LAM)
    for scale, n_ref in (("critical", n_cr), ("target", 1.5 * n_cr),
                         ("ambient", 0.06 * n_cr)):
        cfg = _cfg()
        cfg["reference"]["length_scale"] = scale
        sc = u.derive(cfg)
        assert sc.length_scale == scale
        assert sc.de_ref == pytest.approx(u.skin_depth(n_ref), rel=1e-12)
        # the domain in metres scales with the chosen unit
        assert sc.domain_hi == pytest.approx(100 * sc.de_ref, rel=1e-12)


def test_vacuum_run_cannot_reference_the_ambient():
    cfg = _cfg()
    cfg["plasma"]["ambient"] = None
    cfg["reference"]["length_scale"] = "ambient"
    with pytest.raises(ValueError, match="no plasma.ambient"):
        u.derive(cfg)


def test_vacuum_run_derives_without_ambient_or_field():
    cfg = _cfg()
    cfg["plasma"]["ambient"] = None
    cfg["field"] = {"orientation": "none"}
    cfg["reference"]["length_scale"] = "critical"
    sc = u.derive(cfg)
    assert sc.n_amb is None and sc.B0 is None and sc.rho_i0 is None
    assert sc.dz_over_lD_amb is None
    assert sc.n_targ_over_ncr == pytest.approx(1.5)


def test_wpe_dt_gate_uses_the_compressed_density():
    """G1 must read omega_pe*dt at the density the run REACHES, not at t = 0.

    omega_pe ~ sqrt(n), so a 2x compression is a sqrt(2) rise -- and the whole reason
    the gate exists is that a deck which passes at t = 0 failed after its own
    ablation compressed the target.
    """
    cfg = _cfg()
    cfg["gates"] = {"compression_factor": 4.0}
    sc = u.derive(cfg)
    assert sc.wpe_dt_peak == pytest.approx(2.0 * sc.wpe_dt_targ, rel=1e-12)
    # the reported crossing density is self-consistent
    n_at_2 = sc.n_over_ncr_at_wpe_dt_2 * sc.n_cr
    assert u.omega_pe(n_at_2) * sc.dt == pytest.approx(2.0, rel=1e-9)


def test_field_scales_match_the_known_good_deck():
    """B0, 1/wci0 and rho_i0 for the upstream run_laser_shock parameters.

    These are the numbers TEST_PLAN.md 2.1 quotes and that the known-good deck
    reports independently (74.7 T, 7.61 ps), so agreement here means the field
    derivation is not drifting.
    """
    cfg = _cfg()
    cfg["reference"]["length_scale"] = "ambient"
    cfg["targets"] = {"vp_over_c": 0.0196}
    sc = u.derive(cfg)
    assert sc.B0 == pytest.approx(74.7, rel=5e-3)
    assert sc.wci0_inv * 1e12 == pytest.approx(7.61, rel=5e-3)
    assert sc.rho_i0 * 1e6 == pytest.approx(44.7, rel=1e-2)
    assert sc.rho_i0 / sc.de_ref == pytest.approx(65.3, rel=1e-2)
    assert sc.de_ref * 1e6 == pytest.approx(0.684, rel=2e-3)
    assert sc.di_amb * 1e6 == pytest.approx(6.84, rel=2e-3)


# --------------------------------------------------------------------------- #
# per-cell Coulomb logarithm (laser_deposition.coulomb_log_mode)
# --------------------------------------------------------------------------- #
# Values READ OUT of an actual WarpX run: the `run_profile_ramp` accuracy deck
# (lambda0 = 1.053 um, Z_eff = 1, theta_e = 2e-3 fixed) re-run once per mode, taking
# lnLambda straight from the per-cell `laserdep_profile` dump. These therefore pin the
# Python mirror against the C++ operator, not against itself. Two densities each,
# because one point cannot distinguish the modes' density dependence -- which is the
# whole difference between them.
_LAM = 1.053e-6
_NCR = u.critical_density(_LAM)
_LNL_FROM_RUN = {
    #                n_e            theta    lnLambda from the dump
    "nrl":   [(1.0050291900e27, 2.0e-3, 6.7498629500),
              (2.0128637700e26, 2.0e-3, 7.5538845500)],
    "flash": [(1.0050291900e27, 2.0e-3, 7.3156904500),
              (2.0128637700e26, 2.0e-3, 8.1197120600)],
    "ib":    [(1.0050291900e27, 2.0e-3, 7.3154801600),
              (2.0128637700e26, 2.0e-3, 7.3154801600)],
}


@pytest.mark.parametrize("mode", ["nrl", "flash", "ib"])
def test_coulomb_log_matches_the_operator(mode):
    for n_e, theta, expect in _LNL_FROM_RUN[mode]:
        got = u.coulomb_log_for(mode, n_e, theta, 1.0, _LAM)
        # abs=1e-6 rather than exact: this module's ME/EPS0 differ from WarpX's
        # PhysConst in the 9th digit, which a logarithm barely propagates at all.
        assert got == pytest.approx(expect, abs=1e-6)


def test_ib_saturates_below_critical_and_flash_does_not():
    """The one physical difference between the two b_max cutoffs.

    Below critical omega > omega_pe, so mode ``ib`` cuts off at v_th/omega -- a length
    with NO density dependence. lnLambda therefore freezes at its critical-surface
    value all the way out into the corona, while ``flash`` (b_max = Debye) keeps
    growing as n_e falls. That growth is the unphysical part: an encounter lasting
    longer than 1/omega cannot absorb from the wave.
    """
    at_cr = u.coulomb_log_for("ib", _NCR, 2e-3, 1.0, _LAM)
    for frac in (0.5, 0.1, 1e-3, 1e-6):
        assert u.coulomb_log_for("ib", frac * _NCR, 2e-3, 1.0, _LAM) == \
            pytest.approx(at_cr, rel=1e-12)
        assert u.coulomb_log_for("flash", frac * _NCR, 2e-3, 1.0, _LAM) > at_cr
    # ... and where the plasma is OVERDENSE the two agree exactly, because there
    # omega_pe is the faster clock.
    for frac in (1.01, 2.0, 10.0):
        assert u.coulomb_log_for("ib", frac * _NCR, 2e-3, 1.0, _LAM) == \
            pytest.approx(u.coulomb_log_for("flash", frac * _NCR, 2e-3, 1.0, _LAM),
                          rel=1e-12)
    # flash grows like ln(1/sqrt(n)), i.e. 0.5*ln(10) per decade of density
    d1 = u.coulomb_log_for("flash", 1e-2 * _NCR, 2e-3, 1.0, _LAM)
    d2 = u.coulomb_log_for("flash", 1e-3 * _NCR, 2e-3, 1.0, _LAM)
    assert d2 - d1 == pytest.approx(0.5 * math.log(10.0), rel=1e-9)


def test_constant_mode_ignores_the_local_state():
    """`constant` is the knob: nothing about the cell may move it."""
    for n_e in (1e24, _NCR, 5 * _NCR):
        for theta in (1e-5, 1e-2):
            assert u.coulomb_log_for("constant", n_e, theta, 3.0, _LAM,
                                     coulomb_log=7.5) == 7.5


def test_coulomb_log_is_floored_and_vacuum_safe():
    # No plasma -> 1, as in PSC's get_lnlambda. A cell like this contributes nothing
    # to K (which goes as n_e^2) and is reached only via edge interpolation.
    for mode in ("nrl", "flash", "ib"):
        assert u.coulomb_log_for(mode, 0.0, 2e-3, 1.0, _LAM) == 1.0
        assert u.coulomb_log_for(mode, 1e26, 0.0, 1.0, _LAM) == 1.0
        # Dense and cold enough that the raw formula goes negative -> floored at 1.
        assert u.coulomb_log_for(mode, 1e32, 1e-8, 1.0, _LAM) == 1.0


def test_unknown_coulomb_log_mode_raises():
    with pytest.raises(ValueError):
        u.coulomb_log_for("debye", 1e26, 2e-3, 1.0, _LAM)


def test_K_ib_takes_the_mode_and_derive_reports_the_logarithm():
    """K must scale linearly in lnLambda, and Scales must say which one it used."""
    n_e, theta = 0.5 * _NCR, 2e-3
    K_const = u.K_ib(n_e, theta, _NCR, 1.0, 2.0)
    K_ib_ = u.K_ib(n_e, theta, _NCR, 1.0, 2.0, "ib")
    lnL_ib = u.coulomb_log_for("ib", n_e, theta, 1.0, _LAM)
    assert K_ib_ / K_const == pytest.approx(lnL_ib / 2.0, rel=1e-12)
    # K_ib needs no wavelength argument: omega_laser IS omega_pe(n_cr).
    assert u.omega_pe(_NCR) == pytest.approx(u.omega_of_lambda(_LAM), rel=1e-12)

    cfg = _cfg()
    assert u.derive(cfg).coulomb_log_targ == 5.0        # constant, from the config
    cfg["laser"]["coulomb_log_mode"] = "ib"
    sc = u.derive(cfg)
    assert sc.coulomb_log_targ > 5.0                   # a keV-ish corona sits near 7-8
    assert sc.K_targ / u.derive(_cfg()).K_targ == \
        pytest.approx(sc.coulomb_log_targ / 5.0, rel=1e-12)
