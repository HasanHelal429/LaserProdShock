"""E_abs must survive checkpoint restarts.

The operator's cumulative E_abs is not checkpointed: it restarts at zero on every resume,
and run_warpx appends to run.log across segments. Reading the last value gave P6_mr_full a
time-integrated <f_abs> of 0.28 against a true 0.94.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from laserprod.io import stitch_restarts   # noqa: E402


def test_no_restart_is_unchanged():
    st, E = [10, 20, 30], [1.0, 2.0, 3.0]
    assert stitch_restarts(st, [0]*3, [0]*3, E)[3] == E


def test_reset_is_summed_across_segments():
    # segment 1 reaches 5, restart from the LAST step, segment 2 adds 4 more
    st = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    E  = [1., 2., 3., 4., 5., 1., 2., 3., 4.]
    s2, _, _, e2 = stitch_restarts(st, [0]*9, [0]*9, E)
    assert s2 == st
    assert e2[-1] == 9.0, "the final value must be the WHOLE run, not the last segment"


def test_replay_is_not_double_counted():
    # segment 1 reaches step 50; restart from an EARLIER checkpoint at 30 re-runs 30..50.
    # A line at step s covers (s-10, s], so segment 2 replaces segment 1 from (20,30] on.
    st = [10, 20, 30, 40, 50, 30, 40, 50, 60]
    E  = [1., 2., 3., 4., 5., 1., 2., 3., 4.]
    s2, _, _, e2 = stitch_restarts(st, [0]*9, [0]*9, E)
    assert s2 == [10, 20, 30, 40, 50, 60]
    assert e2[-1] == 6.0          # (0,20] from seg 1 = 2, plus (20,60] from seg 2 = 4
