"""The Phase 1.5 comparator must be able to FAIL.

`studies/ray_march_perf/compare.py` is what will certify that O1/O2/O3 did not change the
physics. A comparator that only ever passes certifies nothing, so its sensitivity is pinned
here the same way `test_gates.py` pins each gate by feeding it a violating config.

The bar is deliberately extreme: **one cell, one ULP, out of a whole capture**. O3 and O1
are supposed to be bit-identical, so anything coarser than that would let a real change
through. And the oblique deck's closed-form 1/8 check must still read EXACT on the
perturbed capture -- that is TEST_PLAN §2.8 in miniature (the clamp bug passed every
single-number test for its entire life), and it is why Tier 1 compares dumps rather than
analysis output.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPARE = os.path.join(ROOT, "studies", "ray_march_perf", "compare.py")

# A synthetic 2D dump with 8 transverse columns and a uniform per-column share, i.e. the
# shape of the oblique deck's step-0 output. Two cells per column so a column sum is a real
# sum.
#
# The layout MUST resemble a real dump, and `test_fixture_layout_matches_the_real_dump_format`
# pins it to `lpio.PROFILE_TAIL` so it cannot drift. The tail is
# ["n_e", "H", "P_abs", "theta_e", "A"] -- DENSITY FIRST -- so in 2D `P_abs` is column 4 and
# column 2 is `n_e`. The first version of this fixture wrote six columns with the varying
# value in position 2, which is `n_e`. The comparator then compared the per-column DENSITY
# share, and because the oblique deck's density is uniform in x BY CONSTRUCTION, its 1/8 check
# passed regardless of what the ray march did. A fixture that does not match reality hides
# precisely the bug the test exists to catch.
HEADER = ("# laser_deposition per-cell profile\n"
          "# step 0 time 0.00000000e+00 dt_dep 1.00000000e-15\n"
          "# P_abs = H * n_e * m_e [W/m^3]; H [m^2/s^3]; n_e [m^-3]; coordinates [m]\n")
DX, DZ = 1.0e-6, 2.0e-6
P_CELL = 1.0854e18                  # a P_abs magnitude, as in the real oblique dump
NE_CELL = 2.5601878200000002e24     # an n_e magnitude, as in the real oblique dump
TAIL = ["n_e", "H", "P_abs", "theta_e", "A"]


def test_fixture_layout_matches_the_real_dump_format():
    """If PROFILE_TAIL ever changes, this fixture must change with it."""
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from laserprod import io as lpio
    assert list(lpio.PROFILE_TAIL) == TAIL, (
        f"PROFILE_TAIL is now {list(lpio.PROFILE_TAIL)}; these synthetic dumps still write "
        f"{TAIL}, so they no longer resemble a real dump and the comparator is being tested "
        f"against a format it will never see.")


def _dump(path, bump=None):
    """Write a synthetic step-0 dump; `bump` = (row, value) replaces one cell's P_abs."""
    rows = []
    for ix in range(8):
        for iz in range(2):
            p = P_CELL
            if bump is not None and bump[0] == len(rows):
                p = bump[1]
            #        x            z            n_e        H  P_abs   theta_e  A
            rows.append(f"{ix*DX:.17g} {iz*DZ:.17g} {NE_CELL:.17g} 1.0 {p:.17g} "
                        f"2.0e-3 5.9344e-25")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(HEADER + "\n".join(rows) + "\n")


def _capture(root, bump=None):
    """A capture tree with the one deck compare.py checks analytically."""
    d = os.path.join(root, "2d_laser_deposition_oblique", "diags")
    _dump(os.path.join(d, "laserdep_profile_000000.txt"), bump=bump)
    return root


def _run(base, cand):
    r = subprocess.run([sys.executable, COMPARE, base, cand],
                       capture_output=True, text=True, cwd=ROOT)
    return r.returncode, r.stdout + r.stderr


def test_compare_script_exists():
    assert os.path.exists(COMPARE), "the Tier 1 comparator is missing"


def test_identical_captures_pass(tmp_path):
    base = _capture(str(tmp_path / "base"))
    cand = _capture(str(tmp_path / "cand"))
    rc, out = _run(base, cand)
    assert rc == 0, out
    assert "TIER 1: PASS" in out, out


def test_one_ulp_in_one_cell_fails(tmp_path):
    """The whole point: a single last-bit difference must not pass as bit-identical."""
    import math
    base = _capture(str(tmp_path / "base"))
    cand = _capture(str(tmp_path / "cand"), bump=(0, math.nextafter(P_CELL, math.inf)))
    rc, out = _run(base, cand)
    assert rc != 0, "a 1 ULP difference in one cell was reported as bit-identical:\n" + out
    assert "TIER 1: FAIL" in out, out
    # ...and it must say WHERE, not just that something moved
    assert "laserdep_profile_000000.txt" in out, out


def test_summary_number_is_blind_to_what_the_dump_catches(tmp_path):
    """TEST_PLAN §2.8: the oblique deck's 1/8 share cannot see a 1 ULP cell move.

    This is not a defect in the closed-form check -- it is the reason Tier 1 may not rest
    on it. If this test ever fails because the share DID move, the perturbation got large
    enough to matter and the test needs a smaller one, not a weaker assertion.
    """
    import math
    base = _capture(str(tmp_path / "base"))
    cand = _capture(str(tmp_path / "cand"), bump=(0, math.nextafter(P_CELL, math.inf)))
    rc, out = _run(base, cand)
    assert rc != 0
    assert "EXACT (1/8)" in out, ("the analytic check should still read EXACT -- that is the "
                                 "point being demonstrated:\n" + out)


def test_missing_candidate_file_is_a_failure(tmp_path):
    base = _capture(str(tmp_path / "base"))
    cand = str(tmp_path / "cand")
    os.makedirs(os.path.join(cand, "2d_laser_deposition_oblique", "diags"), exist_ok=True)
    rc, out = _run(base, cand)
    assert rc != 0, "a candidate missing its dumps passed:\n" + out


def test_corrupt_candidate_dump_is_a_failure(tmp_path):
    base = _capture(str(tmp_path / "base"))
    cand = _capture(str(tmp_path / "cand"))
    p = os.path.join(cand, "2d_laser_deposition_oblique", "diags",
                     "laserdep_profile_000000.txt")
    with open(p, "a") as fh:
        fh.write("this is not a number\n")
    rc, out = _run(base, cand)
    assert rc != 0, "an unparseable dump passed:\n" + out
