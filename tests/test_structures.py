"""Repo-level invariants: every run renders, every run is documented, decks round-trip.

The rule `launch.sh` enforces at launch time (a run must have a README.md) is checked
here at commit time, and the config -> deck -> numbers round trip is checked so that
`make_inputs.py --verify` can be trusted after a run.
"""

from __future__ import annotations

import glob
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import deck as lpdeck       # noqa: E402

RUN_DIRS = sorted(d for d in glob.glob(os.path.join(ROOT, "runs", "*"))
                  if os.path.isfile(os.path.join(d, "config.yaml")))
RUN_IDS = [os.path.basename(d) for d in RUN_DIRS]


def test_there_are_runs():
    assert RUN_DIRS, "no run directories with a config.yaml"


@pytest.mark.parametrize("run_dir", RUN_DIRS, ids=RUN_IDS)
def test_every_run_has_a_readme(run_dir):
    """The project's second rule. launch.sh refuses to start without one; this catches
    it before a commit rather than at launch."""
    path = os.path.join(run_dir, "README.md")
    assert os.path.isfile(path), f"{os.path.basename(run_dir)} has no README.md"
    text = open(path).read()
    for heading in ("**Phase.**", "**Question.**", "## Geometry", "## Result",
                    "## Retracted"):
        assert heading in text, f"{os.path.basename(run_dir)} README lacks {heading}"


@pytest.mark.parametrize("run_dir", RUN_DIRS, ids=RUN_IDS)
def test_every_config_loads_validates_and_renders(run_dir):
    cfg = lpconfig.load(run_dir)
    lpconfig.validate(cfg)              # raises on a hard error
    sc = lpconfig.derive(cfg)
    text = lpdeck.render(cfg)
    assert "laser_deposition.species" in text
    assert f"geometry.dims     = {sc.dims}" in text
    # the operator needs verbose output for its LASERDEP diagnostic
    assert "warpx.verbose = 1" in text


@pytest.mark.parametrize("run_dir", RUN_DIRS, ids=RUN_IDS)
def test_on_disk_deck_matches_the_config(run_dir):
    """`config.yaml` is the single source of truth: a committed deck must be exactly
    what the config renders. A failure here means someone hand-edited a deck."""
    cfg = lpconfig.load(run_dir)
    name = cfg.get("meta", {}).get("deck") or f"inputs_{lpconfig.run_id(cfg)}"
    path = os.path.join(run_dir, name)
    if not os.path.isfile(path):
        pytest.skip(f"{name} not generated yet")
    assert open(path).read() == lpdeck.render(cfg), (
        f"{name} differs from config.yaml -- regenerate with make_inputs.py "
        "(and never hand-edit a deck)")


@pytest.mark.parametrize("run_dir", RUN_DIRS, ids=RUN_IDS)
def test_no_gate_fails(run_dir):
    cfg = lpconfig.load(run_dir)
    bad = [g for g in lpconfig.gates(cfg) if g.status == "fail"]
    assert not bad, f"failing gates: {[(g.key, g.detail) for g in bad]}"


@pytest.mark.parametrize("run_dir", RUN_DIRS, ids=RUN_IDS)
def test_deck_round_trips_to_the_same_numbers(run_dir):
    """render -> parse -> resolve reproduces the config's primaries, which is what
    make_inputs.py --verify relies on after a run."""
    import tempfile

    cfg = lpconfig.load(run_dir)
    sc = lpconfig.derive(cfg)
    with tempfile.NamedTemporaryFile("w", suffix=".inputs", delete=False) as fh:
        fh.write(lpdeck.render(cfg))
        p = fh.name
    try:
        kp = lpdeck.key_params(p)
        assert lpdeck.verify(cfg, p) == []          # a deck must verify against itself
    finally:
        os.unlink(p)

    assert kp["dims"] == sc.dims
    assert kp["max_step"] == sc.max_step
    assert kp["n_cell"] == " ".join(str(c) for c in sc.n_cell)
    assert kp["const:ncr"] == pytest.approx(sc.n_cr, rel=1e-9)
    assert kp["const:de"] == pytest.approx(sc.de_ref, rel=1e-9)
    assert kp["laser_deposition.intensity"] == pytest.approx(sc.intensity, rel=1e-12)
    lo = [float(v) for v in kp["geometry.prob_lo"].split()]
    hi = [float(v) for v in kp["geometry.prob_hi"].split()]
    assert lo[-1] == pytest.approx(sc.domain_lo, rel=1e-9)
    assert hi[-1] == pytest.approx(sc.domain_hi, rel=1e-9)


@pytest.mark.parametrize("run_dir", RUN_DIRS, ids=RUN_IDS)
def test_boundary_tokens_are_consistent(run_dir):
    """No axis may have exactly one periodic face, and the token lists must have one
    entry per dimension in WarpX's mesh-coordinate order."""
    cfg = lpconfig.load(run_dir)
    sc = lpconfig.derive(cfg)
    d = lpdeck.parse_inputs_str(lpdeck.render(cfg))
    for key in ("boundary.field_lo", "boundary.field_hi",
                "boundary.particle_lo", "boundary.particle_hi"):
        assert len(d[key].split()) == sc.dims, f"{key} has the wrong number of entries"
    flo, fhi = d["boundary.field_lo"].split(), d["boundary.field_hi"].split()
    for a, b in zip(flo, fhi):
        assert (a == "periodic") == (b == "periodic"), \
            "one face periodic and the other not -- WarpX will abort"


@pytest.mark.parametrize("run_dir", RUN_DIRS, ids=RUN_IDS)
def test_background_field_is_transverse_to_the_propagation_axis(run_dir):
    """A perpendicular shock needs B0 perpendicular to the shock normal, which is the
    propagation axis z. A z-component would make the geometry parallel, not
    perpendicular."""
    cfg = lpconfig.load(run_dir)
    d = lpdeck.parse_inputs_str(lpdeck.render(cfg))
    bz = d['warpx.Bz_external_grid_function(x,y,z)'].strip('"')
    assert bz == "0.", f"B has a z (propagation-axis) component: {bz}"
    if lpconfig.has_background_field(cfg):
        bx = d['warpx.Bx_external_grid_function(x,y,z)'].strip('"')
        by = d['warpx.By_external_grid_function(x,y,z)'].strip('"')
        assert "B0" in (bx, by), "a background field was requested but B is all zero"


def test_vacuum_runs_have_only_target_species():
    for run_dir in RUN_DIRS:
        cfg = lpconfig.load(run_dir)
        d = lpdeck.parse_inputs_str(lpdeck.render(cfg))
        names = d["particles.species_names"].split()
        if lpconfig.is_vacuum(cfg):
            assert names == ["targ_electrons", "targ_ions"], os.path.basename(run_dir)
        else:
            assert names == ["targ_electrons", "targ_ions",
                             "amb_electrons", "amb_ions"], os.path.basename(run_dir)
