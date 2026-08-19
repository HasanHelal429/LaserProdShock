"""`numerics.density_min_frac` -- the resolved dynamic range.

WarpX creates no macroparticles below `density_min`, so that floor, not the ppc, is what
sets how many decades of plume a run can represent. The paper's PSC setup resolves SIX
decades (10 n_cr target down to a 1e-5 n_cr floor); the project default of 1e-4 gives four.

The default must not move: every run before 2026-08-18 was rendered with 1e-4, and silently
changing it would restate their profiles.
"""
import copy, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from laserprod import config as lpconfig   # noqa: E402
from laserprod import deck as lpdeck       # noqa: E402

KIN = os.path.join(os.path.dirname(__file__), "..", "runs", "P4", "P4_lez_kin")


def test_default_renders_BYTE_IDENTICALLY():
    """Not just numerically equal -- the same string. `%g` would give `0.0001`, and 36
    tests compare rendered decks against committed ones."""
    c = copy.deepcopy(lpconfig.load(KIN))
    c.get("numerics", {}).pop("density_min_frac", None)
    d = lpdeck.render(c)
    assert "targ_electrons.density_min = 1.e-4*nt" in d


def test_frac_is_honoured_and_scaled_by_Z_for_ions():
    c = copy.deepcopy(lpconfig.load(KIN))
    c["numerics"]["density_min_frac"] = 1.0e-6
    d = lpdeck.render(c)
    assert "targ_electrons.density_min = 1.e-6*nt" in d
    # the ion floor must carry the SAME factor divided by Z, or the two species are culled
    # at different PLASMA densities and the plume tip is left charge-separated
    assert "targ_ions.density_min = 1.e-6*nt/13" in d
