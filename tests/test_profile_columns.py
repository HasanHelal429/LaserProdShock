"""`laserdep_profile` column resolution.

These exist because inferring the column layout from the column COUNT silently
mis-read every 2D dump written before ``lnLambda`` was appended to the operator's
per-cell table: 7 columns looks like 1D-with-lnLambda as much as 2D-without, so every
name shifted by one and ``P_abs`` was read out of the ``theta_e`` column. Nothing
crashes when that happens -- the numbers are simply the wrong quantity, which is the
worst way for an analysis to be wrong.
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from laserprod import io as lpio  # noqa: E402

PROSE = (
    "# laser_deposition per-cell profile\n"
    "# step 0 time 6.91752681e-17 dt_dep 6.91752681e-16\n"
    "# P_abs = H * n_e * m_e [W/m^3]; H [m^2/s^3]; n_e [m^-3]; coordinates [m]\n"
)

LAYOUTS = [
    # (label, coord names, whether lnLambda is present)
    ("1d_without", ["z"], False),
    ("1d_with", ["z"], True),
    ("2d_without", ["x", "z"], False),      # the case that was mis-read
    ("2d_with", ["x", "z"], True),
    ("3d_without", ["x", "y", "z"], False),
    ("3d_with", ["x", "y", "z"], True),
]


def _write(tmp_path, coords, ln, header=True):
    tail = ["n_e", "H", "P_abs", "theta_e", "A"] + (["lnLambda"] if ln else [])
    cols = coords + tail
    p = tmp_path / "laserdep_profile_000000.txt"
    with open(p, "w") as fh:
        fh.write(PROSE)
        if header:
            fh.write("# " + " ".join(cols) + "\n")
        for r in range(3):
            fh.write(" ".join(f"{float(r * 100 + i):.8e}" for i in range(len(cols))) + "\n")
    return str(p), cols


@pytest.mark.parametrize("label,coords,ln", LAYOUTS, ids=[l[0] for l in LAYOUTS])
def test_names_come_from_the_header_not_the_count(tmp_path, label, coords, ln):
    path, cols = _write(tmp_path, coords, ln)
    assert lpio.profile_column_names(path, len(cols)) == cols


@pytest.mark.parametrize("label,coords,ln", LAYOUTS, ids=[l[0] for l in LAYOUTS])
def test_reference_reader_agrees(tmp_path, label, coords, ln):
    """`read_profile_table` and `profile_column_names` must not diverge."""
    path, cols = _write(tmp_path, coords, ln)
    tbl = lpio.read_profile_table(path)
    assert list(tbl.keys()) == cols


def test_the_2d_without_lnlambda_case_is_not_read_as_1d(tmp_path):
    """The specific regression: 7 columns in 2D must not become 1D-with-lnLambda.

    Asserted on the VALUES, not just the names -- a positional read put column 0 (x) under
    the name `z`, so every subsequent quantity was off by one and `P_abs` held theta_e.
    """
    path, cols = _write(tmp_path, ["x", "z"], ln=False)
    arr = np.loadtxt(path)
    names = lpio.profile_column_names(path, arr.shape[1])
    assert names[0] == "x" and names[1] == "z"
    assert "lnLambda" not in names
    # column index of P_abs is 4 (x z n_e H P_abs), not 3
    assert names.index("P_abs") == 4
    assert arr[0, names.index("P_abs")] == pytest.approx(4.0)


def test_falls_back_when_the_header_is_missing(tmp_path):
    """A dump with no name row still resolves, via the positional scheme."""
    path, cols = _write(tmp_path, ["x", "z"], ln=True, header=False)
    assert lpio.profile_column_names(path, len(cols)) == cols


def test_header_disagreeing_with_the_data_is_not_trusted(tmp_path):
    """A truncated write must fall back rather than mislabel."""
    path, cols = _write(tmp_path, ["x", "z"], ln=True)
    got = lpio.profile_column_names(path, len(cols) - 1)
    assert len(got) == len(cols) - 1


def test_the_fast_readers_use_the_shared_resolver():
    """spot_report.py and spot_isolation.py must not re-derive the layout themselves.

    A grep-level check on purpose: the bug was a *duplicate* implementation drifting from
    the reference one, so what matters is that the duplicate is gone.
    """
    root = os.path.join(os.path.dirname(__file__), "..", "scripts")
    for name in ("spot_report.py", "spot_isolation.py"):
        src = open(os.path.join(root, name)).read()
        assert "profile_column_names" in src, f"{name} does not use the shared resolver"
        assert 'PROFILE_TAIL[:' not in src, (
            f"{name} still slices PROFILE_TAIL by column count -- that is the bug")
