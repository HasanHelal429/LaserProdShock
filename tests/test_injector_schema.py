"""The `injector:` block -- the semi-infinite reservoir (decision D5).

WarpX's `TargetInjector` replenishes a density deficit inside a box, co-injecting a
neutralizing species in exact charge balance. It is the tool that converts a PIC slab
capped at 40 n_cr -- which loses 5-15 % of its mass over 27 tau and stops being the same
object as FLASH's 795 n_cr solid -- back into an effectively infinite reservoir.

Every check here exists because the failure it guards is SILENT or expensive:

  * a species name the deck never creates aborts inside WarpX at startup, i.e. after the
    queue has handed over the GPU (the same trap the collisions block already guards);
  * a box outside the domain injects nothing and the run merely looks like the
    no-injector case;
  * pinning ABOVE the target's own density turns a reservoir into a particle SOURCE, which
    breaks the energy/mass closure (G6) rather than crashing;
  * the injected ions must carry `u_std = sqrt(theta/mass_ratio)` like every other ion
    block in the deck -- getting that wrong injects ions hot by sqrt(mass_ratio) = 52x
    and quietly heats the reservoir it was supposed to hold cold.
"""

import copy
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from laserprod import config as lpconfig   # noqa: E402
from laserprod import deck as lpdeck       # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
CT = os.path.join(ROOT, "runs", "P4", "P4_lez_kin_flashic_ct")


def _cfg(**over):
    c = copy.deepcopy(lpconfig.load(CT))
    inj = dict(enabled=True, species="targ_electrons",
               neutralizing_species="targ_ions", intervals=20, tau_over_wpe=400.0,
               lo_de=-200.0, hi_de=-100.0, density_over_ncr=40.0,
               reference_density_over_ncr=40.0, ppc_reference=500)
    inj.update(over)
    c["injector"] = inj
    return c


def test_absent_block_emits_nothing():
    """A run without an injector must be byte-unchanged by this feature."""
    c = copy.deepcopy(lpconfig.load(CT))
    c.pop("injector", None)
    assert "target_injector" not in lpdeck.render(c)


def test_emits_the_keys_the_operator_actually_reads():
    d = lpdeck.render(_cfg())
    for key in ("target_injector.species", "target_injector.neutralizing_species",
                "target_injector.intervals", "target_injector.tau",
                "target_injector.lo", "target_injector.hi",
                "target_injector.density", "target_injector.reference_density",
                "target_injector.ppc_reference"):
        assert key in d, f"{key} missing from the deck"


def test_ion_u_std_divides_by_mass_ratio():
    """The one that would silently heat the reservoir 52x."""
    d = lpdeck.render(_cfg())
    assert "target_injector.targ_ions.u_std = sqrt(th_tis/mass_ratio)" in d
    assert "target_injector.targ_electrons.u_std = sqrt(th_ts)" in d


def test_injected_particles_are_cold_solid_not_corona():
    """They stand for undisturbed solid, so they carry th_ts/th_tis, never th_t/th_ti."""
    d = lpdeck.render(_cfg())
    line = [l for l in d.splitlines() if l.startswith("target_injector.targ_electrons.u_std")][0]
    assert "th_ts" in line and "th_t)" not in line


def test_unknown_species_is_refused_at_config_time():
    with pytest.raises(ValueError, match="unknown species"):
        lpconfig.validate(_cfg(species="not_a_species"))
    with pytest.raises(ValueError, match="unknown species"):
        lpconfig.validate(_cfg(neutralizing_species="also_not"))


def test_box_must_be_inside_the_domain():
    with pytest.raises(ValueError, match="not inside the domain"):
        lpconfig.validate(_cfg(lo_de=-9999.0, hi_de=-9000.0))


def test_inverted_box_is_refused():
    with pytest.raises(ValueError, match="must exceed"):
        lpconfig.validate(_cfg(lo_de=-100.0, hi_de=-200.0))


def test_pinning_above_the_target_density_is_refused():
    """A reservoir replenishes a DEFICIT; a higher value is a particle source."""
    with pytest.raises(ValueError, match="particle source"):
        lpconfig.validate(_cfg(density_over_ncr=400.0))


def test_required_keys_are_enforced():
    for key in ("species", "lo_de", "hi_de", "density_over_ncr", "ppc_reference",
                "tau_over_wpe"):
        c = _cfg()
        c["injector"].pop(key)
        with pytest.raises(ValueError, match=f"injector.{key}"):
            lpconfig.validate(c)


def test_nonpositive_tau_and_ppc_are_refused():
    with pytest.raises(ValueError, match="tau_over_wpe must be positive"):
        lpconfig.validate(_cfg(tau_over_wpe=0.0))
    with pytest.raises(ValueError, match="ppc_reference must be positive"):
        lpconfig.validate(_cfg(ppc_reference=0))
