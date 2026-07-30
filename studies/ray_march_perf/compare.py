#!/usr/bin/env python3
"""Tier 1 of the Phase 1.5 acceptance suite: two captures of the CI decks, compared.

`TEST_PLAN.md` §7.5.4 -- "no acceptance test in this phase may be a total alone", because the
clamp bug passed all five of these decks for its whole life by relocating energy while
conserving the total to 7 digits. So this compares the **per-cell profile dump at every
step**, not the analysis scripts' single numbers, and it reports WHERE any difference is.

    python studies/ray_march_perf/compare.py <baseline_dir> <candidate_dir>

O3 and O1 must come out BIT-IDENTICAL: O3 reuses a sample of a pure function at the same
position, and O1's fixed-N_ACC accumulators are reduced in a thread-independent order. O2 is
the only optimisation allowed to move a digit, and then only in cells the beam has not
reached (its own criterion is in §7.5.2, not here).
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))

from laserprod import io as lpio            # noqa: E402

# Analytic expectation for the oblique deck: 30 deg tilt, rays drift 2.9 transverse domain
# widths, density uniform in x -- so the correct per-column share is EXACTLY 1/8, known in
# closed form rather than to shot noise. This is the deck that would have caught the clamp.
OBLIQUE = "2d_laser_deposition_oblique"
OBLIQUE_COLS = 8


def columns(path):
    """Per-column absorbed power from a profile dump (2D only).

    Columns are resolved BY NAME through `lpio.PROFILE_TAIL`, never by a hardcoded index.
    The tail is `["n_e", "H", "P_abs", "theta_e", "A"]` -- density FIRST -- so in 2D
    `P_abs` is column 4 and column 2 is `n_e`. Reading index 2 gives the per-column
    DENSITY share, which in the oblique deck is uniform in x by construction and therefore
    passes the 1/8 test no matter what the ray march does.
    """
    a = np.loadtxt(path)
    ncoord = max(a.shape[1] - len(lpio.PROFILE_TAIL), 0)
    names = {1: ["z"], 2: ["x", "z"], 3: ["x", "y", "z"]}[ncoord]
    cols = names + lpio.PROFILE_TAIL[:a.shape[1] - ncoord]
    if "x" not in cols or "P_abs" not in cols:
        raise SystemExit(f"{path}: no transverse coordinate or no P_abs in {cols}")
    x, P = a[:, cols.index("x")], a[:, cols.index("P_abs")]
    xs = np.unique(x)
    return xs, np.array([P[x == v].sum() for v in xs])


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    base, cand = (os.path.abspath(p) for p in sys.argv[1:3])
    decks = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))
    if not decks:
        print(f"no decks in {base} -- run capture.sh first")
        return 1

    print(f"baseline  {base}")
    print(f"candidate {cand}\n")
    hdr = f"{'deck':32} {'files':>6} {'byte-identical':>15} {'worst rel diff':>15}"
    print(hdr)
    print("-" * len(hdr))

    all_ok, notes = True, []
    for deck in decks:
        files = sorted(glob.glob(os.path.join(base, deck, "diags", "laserdep_profile_*.txt")))
        ep = os.path.join(base, deck, "diags", "reducedfiles", "EP.txt")
        if os.path.exists(ep):
            files.append(ep)
        n_same, worst, worst_where = 0, 0.0, ""
        missing = 0
        for f in files:
            g = f.replace(base, cand, 1)
            if not os.path.exists(g):
                missing += 1
                continue
            with open(f, "rb") as fh1, open(g, "rb") as fh2:
                if fh1.read() == fh2.read():
                    n_same += 1
                    continue
            # differs: quantify it rather than just reporting "not identical"
            try:
                a, b = np.loadtxt(f), np.loadtxt(g)
            except Exception:
                worst, worst_where = float("inf"), os.path.basename(f) + " (unparseable)"
                continue
            if a.shape != b.shape:
                worst, worst_where = float("inf"), f"{os.path.basename(f)} shape {a.shape}->{b.shape}"
                continue
            scale = np.maximum(np.abs(a), np.abs(b))
            with np.errstate(divide="ignore", invalid="ignore"):
                rel = np.where(scale > 0, np.abs(a - b) / scale, 0.0)
            if rel.max() > worst:
                worst, worst_where = float(rel.max()), os.path.basename(f)
        ok = (n_same == len(files)) and missing == 0
        all_ok &= ok
        mark = "yes" if ok else f"{n_same}/{len(files)}"
        print(f"{deck:32} {len(files):6d} {mark:>15} "
              f"{('-' if ok else f'{worst:.3e}'):>15}")
        if missing:
            notes.append(f"{deck}: {missing} file(s) missing from the candidate")
        if not ok and worst_where:
            notes.append(f"{deck}: worst at {worst_where}")

    # --- the oblique deck's closed-form criterion, checked on the CANDIDATE alone -------- #
    # Independent of the baseline: even if both captures agreed, they could agree on a wrong
    # answer. This is the one number in the suite known analytically.
    print()
    ob = os.path.join(cand, OBLIQUE, "diags", "laserdep_profile_000000.txt")
    try:
        xs, col = (columns(ob) if os.path.exists(ob) else (None, None))
    except Exception as exc:          # a truncated or corrupt dump is a real failure mode
        print(f"oblique deck step-0 dump is unreadable ({exc}) -- cannot check 1/8")
        xs = None
        all_ok = False
    if xs is not None:
        sh = col / col.sum()
        mm = sh.max() / sh.min()
        good = len(xs) == OBLIQUE_COLS and abs(sh.max() - 1 / OBLIQUE_COLS) < 1e-12 and abs(mm - 1) < 1e-12
        print(f"oblique deck, step 0, {len(xs)} columns: share "
              f"{sh.min()*100:.4f}-{sh.max()*100:.4f} %, max/min {mm:.6f}  "
              f"-> {'EXACT (1/8)' if good else 'NOT UNIFORM'}")
        all_ok &= good
    elif not os.path.exists(ob):
        print("oblique deck step-0 dump missing from the candidate -- cannot check 1/8")
        all_ok = False

    for n in notes:
        print(f"  note: {n}")
    print(f"\nTIER 1: {'PASS -- bit-identical, and the oblique deck is still exactly 1/8' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
