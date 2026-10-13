"""P8: hybrid twins of the OMEGA 2019 shot -- the generator changes they need.

1. A profiled (coil) field goes on the GRID when the solver is hybrid (Ohm's law sees only
   the grid B), and stays particle-applied for explicit runs.
2. operators.heater (electron fluid) renders the particle_heater block, and validate()
   refuses it without the hybrid solver / advected energy / a known species.
3. units.derive takes dt from const_dt when it is set (the hybrid's mandatory fixed dt).
"""
import copy
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from laserprod import config as lconf, deck as lpdeck, units  # noqa: E402

P7 = os.path.join(ROOT, "runs", "P7", "P7_omega19_I5e13")
P8H = os.path.join(ROOT, "runs", "P8", "P8_hyb_heater_CpH")
P8L = os.path.join(ROOT, "runs", "P8", "P8_hyb_laser_CH")


def _keys(text):
    return lpdeck.parse_inputs_str(text)


def test_profiled_field_on_grid_when_hybrid():
    d = _keys(lpdeck.render(lconf.load(P8L)))
    assert d["warpx.By_external_grid_function(x,y,z)"].strip('"').startswith("Bpk*x0B/(max(")
    assert "particles.B_ext_particle_init_style" not in d


def test_profiled_field_on_particles_when_explicit():
    d = _keys(lpdeck.render(lconf.load(P7)))
    assert d["warpx.By_external_grid_function(x,y,z)"].strip('"') == "0."
    assert d["particles.B_ext_particle_init_style"] == "parse_B_ext_particle_function"


def test_heater_block_renders():
    d = _keys(lpdeck.render(lconf.load(P8H)))
    assert d["particle_heater.target"] == "electron_fluid"
    assert d["particle_heater.species"] == "targ_ions_C"
    assert "(t<heatoff)" in d["particle_heater.targ_ions_C.heating_rate_function(x,y,z,t)"]
    assert float(d["laser_deposition.intensity"]) == 0.0


@pytest.mark.parametrize("mutate, msg", [
    (lambda c: c.pop("solver"), "hybrid"),   # refused (laser swaps or heater, whichever first)
    (lambda c: c["solver"]["hybrid"].update(electron_energy_mode="none"), "advected"),
    (lambda c: c["operators"]["heater"].update(species="nope"), "unknown species"),
    (lambda c: c["operators"]["heater"].update(hi_de=-100.0), "must exceed"),
])
def test_heater_validation_refuses(mutate, msg):
    cfg = copy.deepcopy(lconf.load(P8H))
    mutate(cfg)
    with pytest.raises(ValueError, match=msg):
        lconf.validate(cfg)


def test_const_dt_sets_the_timestep():
    cfg = lconf.load(P8H)
    sc = units.derive(cfg)
    want = float(cfg["numerics"]["const_dt_de_over_c"]) * sc.de_ref / units.C
    assert abs(sc.dt / want - 1.0) < 1e-12
    assert abs(sc.dt * int(cfg["numerics"]["max_step"]) - 4.5e-9) < 1e-12
