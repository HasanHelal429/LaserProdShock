"""Each numerical gate must FIRE on a config built to violate it.

A gate that cannot fail is not a gate. Every case here corresponds to something that
actually went wrong in the prior work (TEST_PLAN.md 6), so these tests are the guard
against the gates quietly degrading into decoration.
"""

from __future__ import annotations

import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laserprod import config as lpconfig   # noqa: E402


BASE = {
    "meta": {"run_id": "t", "phase": 0},
    "laser": {"wavelength_um": 1.053, "intensity": 1e18, "direction": "z",
              "inject_side": "hi", "incidence_angle_deg": 0.0, "Z_eff": 5.0,
              "coulomb_log": 5.0, "temperature_mode": "local", "intervals": 10,
              "ray_cfl": 0.25},
    "reference": {"length_scale": "critical", "mass_ratio": 100.0, "charge_state": 1},
    "plasma": {"target": {"density_over_ncr": 1.5, "thickness_de": 20,
                          "scale_length_de": 15, "theta_e_init": 1e-4,
                          "theta_i_init": 1e-6, "center_de": -50, "shape": "planar"},
               "ambient": {"density_over_ncr": 0.06, "theta_e": 5e-3,
                           "theta_i": 5e-5}},
    "field": {"orientation": "perpendicular", "vA_over_c": 0.003},
    "geometry": {"dims": 1, "normal_axis": "z",
                 "axis": {"lo_de": -100, "hi_de": 100}, "dz_over_de": 0.5,
                 "boundary": {"axis": {"lo": "open", "hi": "open"}}},
    "numerics": {"cfl": 0.35, "particle_shape": 2, "max_step": 24000,
                 "ppc": {"target": 200, "ambient": 48}},
    "gates": {"compression_factor": 2.0, "omega_pe_dt_max": 1.2,
              "dz_over_lambdaD_max": 8.0, "ppc_target_min": 200},
}


def cfg(**patch):
    c = copy.deepcopy(BASE)
    for dotted, val in patch.items():
        node = c
        parts = dotted.split(".")
        for p in parts[:-1]:
            node = node[p]
        node[parts[-1]] = val
    return c


def gate(c, key):
    return next(g for g in lpconfig.gates(c) if g.key == key)


# --------------------------------------------------------------------------- #
def test_baseline_has_no_failing_gate():
    gs = lpconfig.gates(cfg())
    assert not [g for g in gs if g.status == "fail"]
    assert {g.key for g in gs} == {"G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8"}


def test_G1_reproduces_the_upstream_failure():
    """The exact configuration that went unstable upstream must FAIL the gate.

    `run_laser_shock` at cfl = 0.75, a 1.5 n_cr target, dz = 0.5 d_e,ambient: the deck
    reports omega_pe*dt = 1.91 initially, rising to 2.43 as the target compressed under
    its own ablation. Everything measured past t ~ 0.1 gyroperiods was a measurement of
    the resulting instability.
    """
    c = cfg(**{"reference.length_scale": "ambient", "numerics.cfl": 0.75,
               "geometry.dz_over_de": 0.5})
    sc = lpconfig.derive(c)
    assert sc.wpe_dt_targ == pytest.approx(1.91, rel=0.02)      # deck: 1.91
    assert sc.n_over_ncr_at_wpe_dt_2 == pytest.approx(1.71, rel=0.02)
    g = gate(c, "G1")
    assert g.value > 2.0 and g.status == "fail"


def test_G1_reproduces_the_upstream_fix():
    """And the fix must pass: cfl = 0.35 is what made that deck valid again.

    The deck's own numbers are omega_pe*dt = 0.89 initially, 1.07 at the 2.23 n_cr the
    target actually reached (1.49x compression), and the hard limit of 2 not touched
    until 7.84 n_cr. All three are reproduced here, which is what makes this gate a
    check on the physics rather than on an arbitrary threshold.
    """
    c = cfg(**{"reference.length_scale": "ambient", "numerics.cfl": 0.35,
               "gates.compression_factor": 1.49})
    sc = lpconfig.derive(c)
    assert sc.wpe_dt_targ == pytest.approx(0.89, rel=0.03)       # deck: 0.89
    assert sc.wpe_dt_peak == pytest.approx(1.07, rel=0.03)       # deck: 1.07
    assert sc.n_over_ncr_at_wpe_dt_2 == pytest.approx(7.84, rel=0.01)   # deck: 7.84
    assert gate(c, "G1").status == "pass"


def test_G1_default_compression_is_conservative():
    """With the default 2x compression assumption (rather than the 1.49x that deck
    happened to reach), the same settings land just over the 1.2 budget and WARN.

    That is intended: the gate's job is to say how much margin there is against a
    compression the run has not done yet, and the upstream deck survived partly
    because it compressed less than a factor 2.
    """
    c = cfg(**{"reference.length_scale": "ambient", "numerics.cfl": 0.35})
    g = gate(c, "G1")
    assert g.value == pytest.approx(1.237, rel=0.02)
    assert g.status == "warn"       # over the 1.2 budget, under the hard limit of 2


def test_G1_reads_compression_not_t0():
    """A config that passes at t = 0 must still fail if it will compress into trouble."""
    c = cfg(**{"reference.length_scale": "ambient", "numerics.cfl": 0.5,
               "gates.compression_factor": 20.0})
    sc = lpconfig.derive(c)
    assert sc.wpe_dt_targ < 2.0            # fine initially
    assert gate(c, "G1").status == "fail"  # not fine at compression


def test_G2_warns_on_an_underresolved_ambient_but_only_informs_on_the_target():
    """The cold target is Debye-under-resolved by construction, so G2 reports it as a
    measurement; a coarse AMBIENT is a real warning (that is what blew a run up)."""
    g = gate(cfg(), "G2")
    assert g.status == "info" and g.value > 50      # target ~61
    c = cfg(**{"gates.dz_over_lambdaD_max": 1.0})   # tighten past the ambient's 1.73
    assert gate(c, "G2").status == "warn"


def test_G3_fires_unless_a_control_exists():
    assert gate(cfg(), "G3").status == "warn"
    # a run with the laser off IS the control
    assert gate(cfg(**{"laser.intensity": 0.0}), "G3").status == "info"
    # a declared but non-existent control still warns
    c = cfg()
    c["controls"] = {"laser_off": "definitely_not_a_run_dir"}
    c["_run_dir"] = os.path.dirname(os.path.abspath(__file__))
    assert gate(c, "G3").status == "warn"


def test_G4_only_applies_when_there_is_a_turning_point():
    """ray_cfl convergence is non-monotonic for turning-point problems; uniform slabs
    are exact at any ray_cfl. So the gate must distinguish overdense from underdense."""
    assert gate(cfg(), "G4").status == "warn"                       # 1.5 n_cr
    under = cfg(**{"plasma.target.density_over_ncr": 0.5})
    assert gate(under, "G4").status == "info"                       # no critical surface
    c = cfg()
    c["controls"] = {"ray_cfl_ladder": True}
    assert gate(c, "G4").status == "pass"


def test_G5_scales_with_ppc_and_is_inert_in_fixed_mode():
    """T^-3/2 is convex, so per-cell noise biases absorption HIGH; the bias must fall
    as ppc rises, and must not be claimed at all in fixed-temperature mode."""
    lo = gate(cfg(**{"numerics.ppc": {"target": 25, "ambient": 48}}), "G5")
    hi = gate(cfg(**{"numerics.ppc": {"target": 800, "ambient": 48}}), "G5")
    assert lo.status == "warn" and hi.status == "pass"

    # The quoted bias is an upper bound ~ (15/8)(2/3N): it must fall like 1/ppc, and
    # must bracket the measured values (~3% at 25 ppc, <0.1% at 800) from above.
    def quoted(g):
        return float(g.detail.split("<~")[1].split("%")[0])

    # (compare the bound itself, not the rounded string's ratio -- the detail text is
    # formatted to one decimal, which is not enough digits to test a 32x ratio)
    assert quoted(lo) > 10 * quoted(hi)
    assert 3.0 <= quoted(lo) <= 9.0        # above the measured 3%, same order
    assert 0.1 <= quoted(hi) <= 0.5        # above the measured <0.1%
    assert gate(cfg(**{"laser.temperature_mode": "fixed"}), "G5").status == "info"


def test_G6_is_post_run_only():
    assert gate(cfg(), "G6").status == "post"


def test_G7_reports_dz_in_both_units():
    g = gate(cfg(), "G7")
    assert g.value == 0.5
    assert "lambda_D" in g.detail and "um" in g.detail


# --------------------------------------------------------------------------- #
# structural validation
# --------------------------------------------------------------------------- #
def test_single_periodic_face_is_a_hard_error():
    """WarpX requires both faces periodic together or neither."""
    c = cfg(**{"geometry.boundary": {"axis": {"lo": "periodic", "hi": "open"}}})
    with pytest.raises(ValueError, match="exactly one face is 'periodic'"):
        lpconfig.validate(c)


def test_periodic_axis_warns_about_the_wrap_unless_acknowledged():
    c = cfg(**{"geometry.boundary": {"axis": {"lo": "periodic", "hi": "periodic"}}})
    assert any("WRAP" in w for w in lpconfig.validate(c))
    c["meta"]["expect_wrap"] = True
    assert not any("WRAP" in w for w in lpconfig.validate(c))


def test_silver_mueller_with_a_background_field_warns():
    """The projection B-divergence cleaner accepts only periodic/pec/pmc/neumann."""
    c = cfg(**{"geometry.boundary": {"axis": {"lo": "absorbing", "hi": "absorbing"}}})
    assert any("divergence cleaner" in w for w in lpconfig.validate(c))
    # with no background field it is fine
    c2 = cfg(**{"geometry.boundary": {"axis": {"lo": "absorbing", "hi": "absorbing"}},
                "field": {"orientation": "none"}})
    assert not any("divergence cleaner" in w for w in lpconfig.validate(c2))


def test_oblique_incidence_in_1d_is_a_hard_error():
    with pytest.raises(ValueError, match="must be 0 in 1D"):
        lpconfig.validate(cfg(**{"laser.incidence_angle_deg": 30.0}))


def test_2d_requires_a_transverse_extent():
    with pytest.raises(ValueError, match="transverse"):
        lpconfig.validate(cfg(**{"geometry.dims": 2}))


def test_2d_config_validates_clean():
    c = cfg(**{"geometry.dims": 2, "numerics.cfl": 0.5})
    c["geometry"]["transverse"] = {"lo_de": -20, "hi_de": 20}
    c["geometry"]["dx_over_dz"] = 1.0
    c["geometry"]["boundary"]["transverse"] = {"lo": "periodic", "hi": "periodic"}
    assert lpconfig.validate(c) == []
    faces = lpconfig.boundary_faces(c)
    assert faces == {"x": ("periodic", "periodic"), "z": ("open", "open")}


def test_target_must_fit_the_domain():
    c = cfg(**{"geometry.axis": {"lo_de": -50, "hi_de": 50},
               "plasma.target.center_de": -45})
    assert any("does not fit" in w or "but the domain is" in w
               for w in lpconfig.validate(c))


def test_corona_on_the_injection_face_warns():
    """Rays launch EXACTLY on the injection face, so plasma there makes the drive a
    boundary quantity from step 0."""
    c = cfg(**{"plasma.target.center_de": 90})
    assert any("injection face" in w for w in lpconfig.validate(c))
    c["meta"]["expect_face_plasma"] = True
    assert not any("injection face" in w for w in lpconfig.validate(c))


def test_unknown_boundary_name_is_a_hard_error():
    c = cfg(**{"geometry.boundary": {"axis": {"lo": "sponge", "hi": "open"}}})
    with pytest.raises(ValueError, match="unknown boundary"):
        lpconfig.validate(c)


def test_non_z_normal_axis_is_rejected_with_an_explanation():
    with pytest.raises(ValueError, match="only 'z' is supported"):
        lpconfig.validate(cfg(**{"geometry.normal_axis": "x"}))


def test_bad_coulomb_log_mode_is_rejected():
    """A typo here must not reach WarpX, where it aborts mid-launch."""
    for good in lpconfig.COULOMB_LOG_MODES:
        assert lpconfig.validate(cfg(**{"laser.coulomb_log_mode": good})) is not None
    with pytest.raises(ValueError, match="coulomb_log_mode"):
        lpconfig.validate(cfg(**{"laser.coulomb_log_mode": "debye"}))
    # Absent means 'constant', the back-compatible default.
    c = copy.deepcopy(BASE)
    c["laser"].pop("coulomb_log_mode", None)
    lpconfig.validate(c)


# --------------------------------------------------------------------------- #
# G8 -- critical-layer resolution. Added 2026-08-31 from the Tier 1 measurement:
# the only ladder that converged to the 0.80% seed floor was the only one with
# ~1 cell across the 1-r < 0.01 layer, and refining ray_cfl on an unresolved
# layer made absorption WORSE (+18.3% over 0.50 -> 0.025).

def test_G8_underdense_has_no_layer_to_resolve():
    """No critical surface means no singular layer, so the gate must not warn."""
    c = cfg(**{"plasma.target.density_over_ncr": 0.5,
               "plasma.target.corona_density_over_ncr": 0.5})
    g = gate(c, "G8")
    assert g.status == "info"
    assert "underdense" in g.detail


def test_G8_flags_a_subgrid_layer_and_passes_a_resolved_one():
    """The gate keys on 0.01*L_n/dz, i.e. cells across the layer -- not on ray_cfl.

    An exponential corona's L_n at critical IS its scale length, so this is a clean
    single-knob test: at dz = 0.5 d_e, L_n = 10 d_e gives 0.20 cells (sub-grid) and
    L_n = 60 d_e gives 1.20 cells (resolved).
    """
    thin = gate(cfg(**{"plasma.target.corona_profile": "exponential",
                       "plasma.target.scale_length_de": 10.0,
                       "geometry.dz_over_de": 0.5}), "G8")
    assert thin.status == "warn"
    assert thin.value < 1.0

    wide = gate(cfg(**{"plasma.target.corona_profile": "exponential",
                       "plasma.target.scale_length_de": 60.0,
                       "geometry.dz_over_de": 0.5}), "G8")
    assert wide.status == "pass"
    assert wide.value >= 1.0


def test_G8_scales_with_dz_not_with_ray_cfl():
    """Refining the MARCH must not change the gate; refining the GRID must.

    This is the whole content of the Tier 1 finding, encoded so it cannot be lost:
    ray_cfl is not a remedy for an unresolved layer.
    """
    base = {"plasma.target.corona_profile": "exponential",
            "plasma.target.scale_length_de": 30.0, "geometry.dz_over_de": 0.5}
    g0 = gate(cfg(**base), "G8")
    g_march = gate(cfg(**{**base, "laser.ray_cfl": 0.01}), "G8")
    g_grid = gate(cfg(**{**base, "geometry.dz_over_de": 0.125}), "G8")
    assert g_march.value == g0.value          # ray_cfl buys nothing here
    assert g_grid.value > g0.value            # dz does
