#!/usr/bin/env python3
"""Stage A: attribute the n_floor sensitivity to one of its three roles.

    python studies/nfloor_roles/analyse.py

Reports, for each march mode, E_abs and layerfrac against n_floor with per-point errors
from the repeats, then the per-decade slope of each. The attribution logic is stated in
the study README and applied here rather than left to the reader.
"""
from __future__ import annotations
import glob, math, os, re, statistics as st

OUT = os.environ.get("NFLOOR_OUT", "/pscratch/sd/h/hhelal/tier_fixes/nfloor")
FLOORS = ["1.e-1", "1.e-2", "1.e-3", "1.e-4"]


def scrape(d):
    log = os.path.join(d, "run.log")
    if not os.path.isfile(log):
        return None
    txt = open(log, errors="replace").read()
    if "finalized" not in txt[-4000:]:
        return None                     # incomplete runs stay out of the statistics
    def last(key):
        v = re.findall(key + r" ([0-9.eE+-]+)", txt)
        return float(v[-1]) if v else None
    def mx(key):
        v = [float(x) for x in re.findall(key + r" ([0-9.eE+-]+)", txt)]
        return max(v) if v else None
    return {"E": last("Eabs"), "layer": mx("layerfrac"),
            "over": mx("overfrac"), "rmax": mx("rmax")}


def agg(refr, nf):
    rows = [r for r in (scrape(d) for d in
            sorted(glob.glob(os.path.join(OUT, f"nf{nf}_refr{refr}_r*")))) if r]
    if not rows:
        return None
    def ms(k):
        v = [r[k] for r in rows if r[k] is not None]
        if not v:
            return (float("nan"), float("nan"))
        return (st.mean(v), st.stdev(v) / len(v) ** 0.5 if len(v) > 1 else 0.0)
    return {"n": len(rows), "E": ms("E"), "layer": ms("layer"),
            "over": ms("over"), "rmax": ms("rmax")}


def slope_per_decade(xs, ys):
    """Least-squares slope of y (in %) against log10(n_floor)."""
    pts = [(math.log10(x), y) for x, y in zip(xs, ys) if y == y]
    if len(pts) < 2:
        return float("nan")
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    num = sum((p[0] - mx) * (p[1] - my) for p in pts)
    den = sum((p[0] - mx) ** 2 for p in pts)
    return num / den if den else float("nan")


def main():
    print("\nSTAGE A -- attributing the n_floor sensitivity\n")
    res = {}
    for refr, label in ((0, "straight-ray  (roles 2+3 only)"),
                        (1, "refracting    (roles 1+2+3)")):
        print(f"  {label}")
        print(f"    {'n_floor':>9} {'n':>2} {'E_abs':>12} {'s.e.':>7} "
              f"{'layerfrac':>10} {'overfrac':>9} {'rmax':>7}")
        xs, Es, Ls = [], [], []
        for nf in FLOORS:
            a = agg(refr, nf)
            if not a:
                print(f"    {nf:>9} -- no completed runs")
                continue
            x = float(nf)
            xs.append(x); Es.append(a["E"][0]); Ls.append(a["layer"][0])
            print(f"    {nf:>9} {a['n']:>2} {a['E'][0]:>12.0f} {a['E'][1]:>7.0f} "
                  f"{a['layer'][0]:>10.4f} {a['over'][0]:>9.4f} {a['rmax'][0]:>7.4f}")
        if len(xs) >= 2:
            E0 = Es[0]
            sE = slope_per_decade(xs, [100 * (e - E0) / E0 for e in Es])
            sL = slope_per_decade(xs, [100 * l for l in Ls])
            res[refr] = (sE, sL, xs, Es, Ls)
            print(f"    slope: E_abs {sE:+.2f} %/decade   layerfrac {sL:+.2f} pts/decade\n")
        else:
            print()

    if 0 in res and 1 in res:
        sE0, sL0, *_ = res[0]
        sE1, sL1, *_ = res[1]
        print("  ATTRIBUTION")
        print(f"    roles 2+3 (straight-ray) : {sE0:+.2f} %/decade in E_abs")
        print(f"    roles 1+2+3 (refracting) : {sE1:+.2f} %/decade in E_abs")
        print(f"    -> role 1 (trajectory)   : {sE1 - sE0:+.2f} %/decade  "
              f"({abs(sE1-sE0)/max(abs(sE1),1e-9)*100:.0f} % of the total)")
        print()
        # does the layer's share move with the answer?
        for refr in (0, 1):
            sE, sL, xs, Es, Ls = res[refr]
            mode = "straight-ray" if refr == 0 else "refracting"
            if abs(sL) < 1.0:
                print(f"    {mode}: layerfrac is FLAT ({sL:+.2f} pts/decade) while E_abs moves "
                      f"{sE:+.2f} %/decade\n      -> role 3 is NOT the driver here; the cap "
                      f"(role 2) is doing the work.")
            else:
                frac = abs(sL) / max(abs(sE), 1e-9)
                print(f"    {mode}: layerfrac tracks E_abs ({sL:+.2f} pts/decade vs "
                      f"{sE:+.2f} %/decade)\n      -> role 3 (the analytic layer's extent) is "
                      f"implicated; ratio {frac:.2f}.")
        print("\n  Stage B follows the README's decision table from these slopes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
