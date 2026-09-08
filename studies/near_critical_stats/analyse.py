#!/usr/bin/env python3
"""Pool the repeats and decide the near-critical verdict properly.

    python studies/near_critical_stats/analyse.py

The 2026-09-04 attempt failed because it compared single runs whose scatter it had
underestimated. This does three things that fixes:

* reports each rung as a MEAN with its standard error, not a single value;
* propagates that error into every increment (sigma_inc = sqrt(se_a^2 + se_b^2)), so an
  increment carries an honest uncertainty rather than borrowing a global constant;
* refuses to call convergence when the increment is inside its own error, and says how
  many more repeats would be needed instead of guessing.
"""
from __future__ import annotations
import glob, os, re, statistics as st, sys

OUT = os.environ.get("STATS_OUT", "/pscratch/sd/h/hhelal/tier_fixes/ncstats")
RUNGS = [("0025", 0.025), ("005", 0.05), ("010", 0.10), ("025", 0.25)]


def eabs(path):
    v = None
    try:
        for ln in open(path, errors="replace"):
            m = re.search(r"Eabs ([0-9.eE+-]+)", ln)
            if m:
                v = float(m.group(1))
    except OSError:
        return None
    return v


def collect(rung, fix):
    vals, ovf = [], []
    for d in sorted(glob.glob(os.path.join(OUT, f"P5_raycfl_{rung}_fix{fix}_r*"))):
        log = os.path.join(d, "run.log")
        if not os.path.isfile(log):
            continue
        try:
            if "finalized" not in open(log, errors="replace").read()[-4000:]:
                continue        # incomplete run must not enter the statistics
        except OSError:
            continue
        v = eabs(log)
        if v:
            vals.append(v)
            o = [float(x) for x in re.findall(r"overfrac ([0-9.eE+-]+)", open(log, errors="replace").read())]
            ovf.append(max(o) if o else 0.0)
    return vals, ovf


def main():
    print(f"\nNEAR-CRITICAL STATISTICS  (straight rays, seed varied per repeat)")
    print(f"source: {OUT}\n")
    summary = {}
    for fix in (0, 1):
        rows = []
        for rung, x in RUNGS:
            vals, ovf = collect(rung, fix)
            if not vals:
                continue
            m = st.mean(vals)
            sd = st.stdev(vals) if len(vals) > 1 else float("nan")
            se = sd / len(vals) ** 0.5 if len(vals) > 1 else float("nan")
            rows.append((x, m, sd, se, len(vals), max(ovf) if ovf else 0.0))
        if not rows:
            print(f"  near_critical_fix = {fix}: no completed runs yet")
            continue
        rows.sort(key=lambda r: -r[0])
        summary[fix] = rows
        print(f"  near_critical_fix = {fix}")
        print(f"    {'ray_cfl':>8} {'n':>3} {'mean E_abs':>12} {'sd':>8} {'s.e.':>8} "
              f"{'max overfrac':>13}")
        for x, m, sd, se, n, o in rows:
            print(f"    {x:>8g} {n:>3} {m:>12.0f} {sd:>7.0f}  {se:>7.0f}  {o:>13.4f}")
        print(f"    {'increments (mean-to-mean, with propagated error)':<58}")
        for i in range(len(rows) - 1):
            x0, m0, _, se0, _, _ = rows[i]
            x1, m1, _, se1, _, _ = rows[i + 1]
            inc = 100 * (m1 - m0) / m0
            # relative error on the ratio, first order
            sig = 100 * ((se1 / m0) ** 2 + (m1 * se0 / m0 ** 2) ** 2) ** 0.5
            n = abs(inc) / sig if sig else float("inf")
            verdict = "REAL" if n >= 3 else ("marginal" if n >= 2 else "not resolved")
            print(f"      {x0:g} -> {x1:<6g} {inc:+7.2f} % +- {sig:.2f}   ({n:.1f} sigma, {verdict})")
        print()

    if 0 in summary and 1 in summary:
        print("  VERDICT")
        for fix in (0, 1):
            rows = summary[fix]
            if len(rows) < 3:
                continue
            incs = [(100 * (rows[i+1][1] - rows[i][1]) / rows[i][1]) for i in range(len(rows)-1)]
            sigs = [100 * ((rows[i+1][3] / rows[i][1]) ** 2
                           + (rows[i+1][1] * rows[i][3] / rows[i][1] ** 2) ** 2) ** 0.5
                    for i in range(len(rows)-1)]
            last, slast = abs(incs[-1]), sigs[-1]
            lab = "corrected" if fix else "previous  "
            if last < slast:
                print(f"    fix={fix} ({lab}): last increment {incs[-1]:+.2f} % is inside its own "
                      f"error (+-{slast:.2f}) -- CONSISTENT WITH CONVERGED")
            elif last < 2 * slast:
                need = int((2.5 * slast / last) ** 2 * rows[0][4]) + 1
                print(f"    fix={fix} ({lab}): last increment {incs[-1]:+.2f} % +-{slast:.2f} is "
                      f"{last/slast:.1f} sigma -- UNDECIDED; ~{need} repeats/rung would settle it")
            else:
                shrinking = abs(incs[-1]) < abs(incs[-2])
                print(f"    fix={fix} ({lab}): last increment {incs[-1]:+.2f} % +-{slast:.2f} is "
                      f"real and {'shrinking' if shrinking else 'NOT shrinking'} -- "
                      f"{'converging' if shrinking else 'NOT CONVERGED'}")
        o0 = max((r[5] for r in summary[0]), default=0.0)
        o1 = max((r[5] for r in summary[1]), default=0.0)
        print(f"\n    evanescent deposition: max overfrac {o0:.3f} (fix off) -> {o1:.3f} (fix on)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
