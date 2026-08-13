"""The Phase-4 schema additions: the hybrid solver path and the collisions block.

These exist because both paths can fail SILENTLY in ways that produce a running
simulation of the wrong problem:

  * A hybrid deck that also emits electron macroparticles double-counts charge -- the
    Ohm's-law solver forms J_e by subtraction, so a stray electron species is counted as
    an ion and subtracted twice. Nothing crashes.
  * A `laser_deposition.species` list left in the deck while the operator reads n_e from
    the fluid makes the deck CLAIM it heats something it does not. WarpX aborts on this
    one, which is the good case -- and the test pins that we never emit it.
  * A collisions pair naming a species the deck never creates aborts at WarpX startup,
    i.e. after the queue has already handed over the GPU.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from laserprod import config as lpconfig   # noqa: E402
from laserprod import deck as lpdeck       # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
KIN = os.path.join(ROOT, "runs", "P4", "P4_lez_kin")
HYB = os.path.join(ROOT, "runs", "P4", "P4_lez_hyb")


# --------------------------------------------------------------------------- hybrid
def test_hybrid_emits_no_electron_macroparticles():
    d = lpdeck.parse_inputs_str(lpdeck.render(lpconfig.load(HYB)))
    names = d["particles.species_names"].split()
    assert "targ_electrons" not in names
    assert names == ["targ_ions"]


def test_hybrid_omits_the_laser_species_key_entirely():
    """Omitted, not emptied -- WarpX aborts if the key is present and unread."""
    text = lpdeck.render(lpconfig.load(HYB))
    assert "laser_deposition.species" not in text


def test_hybrid_emits_the_three_swaps_with_the_operators_own_tokens():
    d = lpdeck.parse_inputs_str(lpdeck.render(lpconfig.load(HYB)))
    assert d["laser_deposition.density_source"] == "hybrid_rho"
    assert d["laser_deposition.temperature_mode"] == "hybrid_fluid"
    # 'electron_fluid', NOT 'fluid': the operator's parser accepts only the former.
    assert d["laser_deposition.deposit_to"] == "electron_fluid"
    assert d["algo.maxwell_solver"] == "hybrid"


def test_hybrid_swaps_must_move_together():
    cfg = lpconfig.load(HYB)
    cfg["laser"]["density_source"] = "species"
    with pytest.raises(ValueError, match="hybrid_rho"):
        lpconfig.validate(cfg)


def test_conducting_mode_is_refused_at_config_time():
    """WarpX aborts on it; better to fail before the queue than 500k steps in."""
    cfg = lpconfig.load(HYB)
    cfg["solver"]["hybrid"]["electron_energy_mode"] = "conducting"
    with pytest.raises(ValueError, match="NOT implemented"):
        lpconfig.validate(cfg)


def test_advected_refuses_a_gamma():
    """eps = (3/2) n kB Te fixes gamma = 5/3; both closures would double-count."""
    cfg = lpconfig.load(HYB)
    cfg["solver"]["hybrid"]["gamma"] = 5.0 / 3.0
    with pytest.raises(ValueError, match="gamma"):
        lpconfig.validate(cfg)


def test_hybrid_gates_report_na_rather_than_passing():
    """The omega_pe and Debye limits do not EXIST without electron macroparticles.
    Reporting `pass` would read as "checked and fine", which is a different claim."""
    gs = {g.key: g for g in lpconfig.gates(lpconfig.load(HYB))}
    for k in ("G1", "G2"):
        assert gs[k].status == "info"
        assert "n/a" in gs[k].detail


# ----------------------------------------------------------------------- collisions
def test_collisions_reach_the_deck():
    d = lpdeck.parse_inputs_str(lpdeck.render(lpconfig.load(KIN)))
    names = d["collisions.collision_names"].split()
    assert len(names) == 3
    for nm in names:
        assert d[f"{nm}.type"] == "pairwisecoulomb"
        assert float(d[f"{nm}.CoulombLog"]) == pytest.approx(6.3)


def test_intra_species_collisions_take_one_name():
    """WarpX wants ONE species for intra-species collisions, two otherwise."""
    d = lpdeck.parse_inputs_str(lpdeck.render(lpconfig.load(KIN)))
    by = {nm: d[f"{nm}.species"].split()
          for nm in d["collisions.collision_names"].split()}
    assert any(len(v) == 1 for v in by.values()), "no intra-species pair emitted"
    assert any(len(v) == 2 for v in by.values()), "no inter-species pair emitted"


def test_a_pair_naming_an_unknown_species_is_refused():
    """Otherwise WarpX aborts at startup -- after the GPU has been handed over."""
    cfg = lpconfig.load(KIN)
    cfg["collisions"]["pairs"] = [["electrons", "targ_ions"]]
    with pytest.raises(ValueError, match="unknown species"):
        lpconfig.validate(cfg)


def test_the_paper_requires_collisions_on_for_the_kinetic_leg():
    """Lezhnin 2025: turning off EITHER collisions or laser heating gives
    'drastically different plasma evolution'. This leg is void without them."""
    cfg = lpconfig.load(KIN)
    assert cfg["collisions"]["enabled"] is True
    assert len(cfg["collisions"]["pairs"]) == 3


# --------------------------------------------------------------------------- verify
@pytest.mark.parametrize("run", [KIN, HYB], ids=["kin", "hyb"])
def test_the_new_keys_round_trip_through_verify(tmp_path, run):
    """A stale binary silently ignoring a new flag is how `refraction = 0` was lost for
    2000 steps (CLAUDE.md). Every new key belongs in --verify."""
    cfg = lpconfig.load(run)
    p = tmp_path / "inputs"
    p.write_text(lpdeck.render(cfg))
    assert lpdeck.verify(cfg, str(p)) == []


# ------------------------------------------------------------------ charge neutrality
def _dens_of(text, sp):
    for line in text.splitlines():
        if line.startswith(f"{sp}.density_function"):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def test_ions_carry_n_e_over_Z_so_the_plasma_is_neutral():
    """The density expressions are ELECTRON densities (n_cr is defined on electrons), so an
    ion of charge Z e needs n_i = n_e / Z.

    Emitting the same number density for both is correct ONLY at Z = 1 and otherwise leaves
    a net charge of (Z - 1) e n_e -- 12x e n_e at the Z = 13 of these runs. Every earlier run
    in this project used Z = 1, which is exactly why this survived to Phase 4.
    """
    cfg = lpconfig.load(KIN)
    assert int(cfg["reference"]["charge_state"]) == 13
    text = lpdeck.render(cfg)
    ne = _dens_of(text, "targ_electrons")
    ni = _dens_of(text, "targ_ions")
    assert ne is not None and ni is not None
    assert ni != ne, "ions must not carry the electron NUMBER density when Z != 1"
    assert ni == f"({ne})/13"


def test_hybrid_ion_density_is_also_divided():
    """A hybrid deck has no electron species, so n_e = rho/e = Z n_i. The same slip makes the
    electron density come out Z times too LARGE -- 130 n_cr against an intended 10."""
    text = lpdeck.render(lpconfig.load(HYB))
    ni = _dens_of(text, "targ_ions")
    assert ni is not None and ni.endswith("/13")


def test_Z_equals_one_is_unchanged():
    """The Z = 1 runs must be byte-identical -- 20 of them predate this fix."""
    import glob
    z1 = sorted(glob.glob(os.path.join(ROOT, "runs", "P?", "*", "config.yaml")))
    checked = 0
    for p in z1:
        cfg = lpconfig.load(os.path.dirname(p))
        if int(cfg["reference"].get("charge_state", 1)) != 1:
            continue
        text = lpdeck.render(cfg)
        ne, ni = _dens_of(text, "targ_electrons"), _dens_of(text, "targ_ions")
        if ne is None or ni is None:
            continue
        assert ni == ne, f"{p}: Z=1 must emit identical densities (no /1 suffix)"
        checked += 1
    assert checked >= 10, f"expected many Z=1 runs, checked {checked}"
