"""Repo-level invariants: every run renders, every run is documented, decks round-trip.

The rule `launch.sh` enforces at launch time (a run must have a README.md) is checked
here at commit time, and the config -> deck -> numbers round trip is checked so that
`make_inputs.py --verify` can be trusted after a run.
"""

from __future__ import annotations

import copy
import glob
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import deck as lpdeck       # noqa: E402

# Runs live in runs/<phase>/<run_id>/ (see runs/README.md). Glob both that and the old
# flat runs/<run_id>/ layout, so a stray un-migrated run dir is still checked rather than
# silently skipped -- these tests are the repo's only guarantee that every run has a
# README and a deck matching its config.
RUN_DIRS = sorted(
    d for pat in (("runs", "*"), ("runs", "*", "*"))
    for d in glob.glob(os.path.join(ROOT, *pat))
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
    # `species` must be OMITTED, not emptied, when the operator reads n_e from the fluid
    # and deposits into it: WarpX aborts on a species list nothing would read, because a
    # stale list is how a deck comes to claim it heats something it does not.
    if str(cfg["laser"].get("deposit_to", "species")) == "electron_fluid":
        assert "laser_deposition.species" not in text
        assert "laser_deposition.deposit_to           = electron_fluid" in text
    else:
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


def test_ray_march_knobs_reach_the_deck_and_are_verified():
    """The Phase-1.5 knobs must survive config -> deck -> --verify.

    `n_accumulators` fixes the ray-march summation order, so two runs are comparable bit
    for bit only at the same value; `vacuum_skip` gates an optimisation that is exact but
    is still a code path. If either is emitted but not checked by `verify`, a deck could
    drift from its config in precisely the way that makes two runs incomparable without
    anything failing. So this pins BOTH directions -- emitted, and caught when changed.
    """
    import copy
    import tempfile

    cfg = lpconfig.load(RUN_DIRS[0])
    cfg = copy.deepcopy(cfg)
    cfg["laser"].update(ray_threads=8, n_accumulators=32, vacuum_skip=False)
    text = lpdeck.render(cfg)
    d = lpdeck.parse_inputs_str(text)
    assert d["laser_deposition.ray_threads"].strip() == "8"
    assert d["laser_deposition.n_accumulators"].strip() == "32"
    assert d["laser_deposition.vacuum_skip"].strip() == "0"

    with tempfile.NamedTemporaryFile("w", suffix=".inputs", delete=False) as fh:
        fh.write(text)
        p = fh.name
    try:
        assert lpdeck.verify(cfg, p) == []
        cfg["laser"]["n_accumulators"] = 16          # the deck now disagrees
        assert lpdeck.verify(cfg, p), (
            "verify() ignores n_accumulators, so a deck and its config can differ in the "
            "ray-march summation order undetected")
    finally:
        os.unlink(p)


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


OFF_RUNS = [d for d in RUN_DIRS if os.path.basename(d).endswith("_off")]


@pytest.mark.parametrize("run_dir", OFF_RUNS,
                         ids=[os.path.basename(d) for d in OFF_RUNS])
def test_laser_off_control_differs_only_in_intensity(run_dir):
    """A `_off` control (gate G3) is only a valid control if the deck is identical to its
    physics run apart from the drive. Grid heating accumulates with step count and depends
    on the grid, the ppc and the species, so ANY other difference makes the subtraction
    meaningless -- and the subtraction is the only thing that turns G2's `dz/lambda_D` = 61
    from a number into a bound. Checked here rather than trusted, because the two configs
    are edited by hand and a drifted duration would be invisible in the result."""
    off = lpconfig.load(run_dir)
    physics_id = (off.get("controls") or {}).get("physics_run")
    assert physics_id, f"{os.path.basename(run_dir)} declares no controls.physics_run"
    sib = os.path.join(os.path.dirname(run_dir), str(physics_id))
    assert os.path.isdir(sib), f"controls.physics_run -> {physics_id} does not exist"
    on = lpconfig.load(sib)

    assert float(off["laser"]["intensity"]) == 0.0, "a laser-off control needs intensity 0"
    assert float(on["laser"]["intensity"]) > 0.0, f"{physics_id} has no drive to control for"

    # Compare the rendered decks line by line, ignoring the header comment block (which
    # carries each run's own description) and the intensity line itself.
    def body(cfg):
        return [ln for ln in lpdeck.render(cfg).splitlines()
                if not ln.startswith("#") and "laser_deposition.intensity" not in ln]

    d_off, d_on = body(off), body(on)
    assert d_off == d_on, (
        f"{os.path.basename(run_dir)} is not a valid control for {physics_id}: "
        + "; ".join(f"{a!r} != {b!r}" for a, b in zip(d_on, d_off) if a != b)[:400])


def test_vacuum_runs_have_only_target_species():
    for run_dir in RUN_DIRS:
        cfg = lpconfig.load(run_dir)
        d = lpdeck.parse_inputs_str(lpdeck.render(cfg))
        names = d["particles.species_names"].split()
        # A hybrid run's electrons are a FLUID -- there are no electron macroparticles,
        # and emitting some would double-count the charge the Ohm's-law solver already
        # carries (it forms J_e by subtraction, so a stray electron species is counted
        # as an ion and subtracted twice).
        hybrid = str((cfg.get("solver") or {}).get("type", "em")) == "hybrid"
        if lpconfig.is_vacuum(cfg):
            expect = ["targ_ions"] if hybrid else ["targ_electrons", "targ_ions"]
        elif hybrid:
            expect = ["targ_ions", "amb_ions"]
        else:
            expect = ["targ_electrons", "targ_ions", "amb_electrons", "amb_ions"]
        assert names == expect, os.path.basename(run_dir)


def test_coulomb_log_mode_reaches_the_deck_and_is_verified():
    """lnLambda multiplies K directly, so `coulomb_log_mode` must survive
    config -> deck -> --verify in BOTH directions.

    A mode that renders but is not verified would let a deck absorb a factor of a few
    differently from what its config says, with nothing failing -- the same failure
    shape the ray-march knobs above guard against, but on the physics rather than on
    the summation order.
    """
    import copy
    import tempfile

    cfg = copy.deepcopy(lpconfig.load(RUN_DIRS[0]))
    for mode in lpconfig.COULOMB_LOG_MODES:
        cfg["laser"]["coulomb_log_mode"] = mode
        d = lpdeck.parse_inputs_str(lpdeck.render(cfg))
        assert d["laser_deposition.coulomb_log_mode"].strip() == mode

    cfg["laser"]["coulomb_log_mode"] = "ib"
    with tempfile.NamedTemporaryFile("w", suffix=".inputs", delete=False) as fh:
        fh.write(lpdeck.render(cfg))
        p = fh.name
    try:
        assert lpdeck.verify(cfg, p) == []
        cfg["laser"]["coulomb_log_mode"] = "constant"   # the deck now disagrees
        assert lpdeck.verify(cfg, p), (
            "verify() ignores coulomb_log_mode, so a deck could use a per-cell "
            "Coulomb logarithm while its config claims a constant one")
    finally:
        os.unlink(p)

    # A config that never mentions it emits NOTHING, so every deck written before this
    # option existed still matches its config byte for byte -- the operator's default is
    # `constant` and bit-identical to having no such option at all.
    cfg2 = copy.deepcopy(lpconfig.load(RUN_DIRS[0]))
    cfg2["laser"].pop("coulomb_log_mode", None)
    assert "coulomb_log_mode" not in lpdeck.render(cfg2)


def test_profile_table_columns_come_from_the_header():
    """`read_profile_table` must name columns from the dump's own header row.

    Appending `lnLambda` made the old column-count heuristic AMBIGUOUS: 7 trailing
    columns is 1D-with-lnLambda or 2D-without, and 8 is 2D-with or 3D-without. Reading
    the header settles it, and keeps dumps written before the column existed readable.
    """
    import tempfile

    from laserprod import io as lpio

    new_1d = ("# laser_deposition per-cell profile\n"
              "# P_abs = H * n_e * m_e [W/m^3]\n"
              "# z n_e H P_abs theta_e A lnLambda\n"
              "1e-6 2e26 3e16 4e10 2e-3 2.1e-24 7.3\n"
              "2e-6 4e26 5e16 6e10 2e-3 2.2e-24 7.2\n")
    old_2d = ("# laser_deposition per-cell profile\n"
              "# x z n_e H P_abs theta_e A\n"
              "0.0 1e-6 2e26 3e16 4e10 2e-3 2.1e-24\n")
    for text, want in ((new_1d, ["z", "n_e", "H", "P_abs", "theta_e", "A", "lnLambda"]),
                       (old_2d, ["x", "z", "n_e", "H", "P_abs", "theta_e", "A"])):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
            fh.write(text)
            p = fh.name
        try:
            got = lpio.read_profile_table(p)
        finally:
            os.unlink(p)
        assert list(got) == want, "both files have 7 columns; only the header tells them apart"
    # and the values land on the right keys, not shifted by one
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as fh:
        fh.write(new_1d)
        p = fh.name
    try:
        t = lpio.read_profile_table(p)
    finally:
        os.unlink(p)
    assert t["lnLambda"] == [7.3, 7.2]
    assert t["theta_e"] == [2e-3, 2e-3]


def test_density_min_is_scaled_with_the_ion_density_function():
    """Both species must be culled at the same PLASMA density, not the same number density.

    The ion density function is (n_e expression)/Z, so an identical `density_min` culls ions
    a factor Z earlier in n_e than electrons and leaves an uncompensated electron shell at
    the tenuous edge -- measured at net charge -1.000 of the local density over 18 d_e in
    the P4_lez_kin_flashic smoke test, before the fix.
    """
    import re
    from laserprod import config as lpconfig, deck as lpdeck

    cfg = lpconfig.load("runs/P4/P4_lez_kin_flashic")
    Z = int(cfg["reference"]["charge_state"])
    assert Z != 1, "this test is only meaningful for a multiply-charged ion"
    txt = lpdeck.render(cfg)
    got = dict(re.findall(r"^(\w+)\.density_min\s*=\s*(.+)$", txt, re.M))
    assert "targ_electrons" in got and "targ_ions" in got
    assert got["targ_electrons"].strip() == "1.e-4*nt"
    assert got["targ_ions"].strip() == f"1.e-4*nt/{Z}", got["targ_ions"]


# --------------------------------------------------------------------------- #
# Checkpoint/restart. A G8-passing spine costs ~145 h against a 48 h queue limit,
# so the phase's headline result depends on chaining working. These pin the deck
# side; runs/P5/P5_ckpt is the live end-to-end acceptance test.

def _ckpt_cfg(**patch):
    """A real P5 config, patched. Built from a run dir rather than from a synthetic BASE
    so these tests exercise the same rendering path the campaign actually launches."""
    c = copy.deepcopy(lpconfig.load(os.path.join(ROOT, "runs", "P5", "P5_raycfl_025")))
    c.setdefault("diagnostics", {})
    for dotted, val in patch.items():
        node = c
        parts = dotted.split(".")
        for q in parts[:-1]:
            node = node[q]
        node[parts[-1]] = val
    return c


def test_checkpoint_is_opt_in():
    """A checkpoint is the FULL state -- every particle -- and WarpX keeps every one it
    writes, so defaulting it on would quietly fill $PSCRATCH. Absent unless asked for."""
    d = lpdeck.parse_inputs_str(lpdeck.render(_ckpt_cfg()))
    assert "chk.diag_type" not in d
    assert "chk.format" not in d
    assert "warpx.break_signals" not in d
    assert "chk" not in d["diagnostics.diags_names"].split()


def test_checkpoint_emits_diag_and_break_signal():
    """Both halves are required, and the second is the non-obvious one: without
    break_signals the wall arrives as SIGKILL and everything since the last scheduled
    checkpoint is lost -- which is how P5_flashic_off lost 65% of a 24 h run."""
    c = _ckpt_cfg(**{"diagnostics.checkpoint_intervals": 5000})
    d = lpdeck.parse_inputs_str(lpdeck.render(c))
    assert "chk" in d["diagnostics.diags_names"].split()
    # `checkpoint` is the FORMAT; diag_type must be Full. Asserting both because the
    # first implementation set diag_type = checkpoint and WarpX aborted at init.
    assert d["chk.diag_type"] == "Full"
    assert d["chk.format"] == "checkpoint"
    assert d["chk.intervals"] == "5000"
    assert d["warpx.break_signals"] == "HUP"


def test_checkpoint_does_not_disturb_the_other_diagnostics():
    """The checkpoint is an ADDITION: a leg's plotfile/field/phase cadence, which is what
    every analysis tool reads, must be identical with and without it."""
    a = lpdeck.parse_inputs_str(lpdeck.render(_ckpt_cfg()))
    b = lpdeck.parse_inputs_str(
        lpdeck.render(_ckpt_cfg(**{"diagnostics.checkpoint_intervals": 5000})))
    for k in ("diag1.intervals", "diag1.diag_type", "EP.intervals", "FE.intervals",
              "PN.intervals", "max_step"):
        assert a.get(k) == b.get(k), f"{k} changed when checkpointing was enabled"
