#!/usr/bin/env python3
"""Strip a finished run's `run.log` to the lines the analysis tools actually parse.

    python scripts/prune_run_log.py runs/P4/P4_lez_kin_thick --dry-run
    python scripts/prune_run_log.py runs/P4/*/ --apply

WHY. A completed 1D run writes a four-line block per step -- `STEP n starts`, `STEP n ends`,
`Evolve time`, a blank -- and at 2e6 steps that is a 692 MB file whose diagnostic content is a
few hundred thousand LASERDEP lines. On the Phase-4 runs `run.log` is LARGER than `diags/`.

WHAT IS KEPT, and why each is load-bearing:
  * every `LASERDEP` line          -- xcode_compare.absorbed(), laser_report, io.laserdep_history,
                                      floor_effect, xcode_matrix all parse these for f_abs/E_abs
  * everything before the first    -- `Level 0: dt`, `dz`, n_cell, the deck echo
    STEP line (the header)
  * everything after the last      -- the TinyProfiler table, i.e. the wall-time record
    STEP line (the footer)
  * the LAST `STEP n ends` line    -- io.last_step() takes steps[-1], so one is enough
  * any line matching a warning /  -- so a silently-degraded run stays diagnosable
    error / abort / NaN pattern

Refuses to touch a run that is still going (no TinyProfiler footer), and never deletes the
original until the rewritten file has been re-parsed and the LASERDEP count, the last step and
the wall time all match. Use --keep-original to leave a `.orig` behind.
"""
from __future__ import annotations
import argparse, os, re, shutil, sys

STEP_START = re.compile(r"^STEP \d+ starts")
STEP_ENDS  = re.compile(r"^STEP (\d+) ends")
NOISE      = re.compile(r"^(STEP \d+ (starts|ends)|Evolve time =|--- INFO\s|\s*$)")
KEEP_ALWAYS= re.compile(r"LASERDEP|WARNING|ERROR|Error|abort|Abort|SIGSEGV|Assertion|nan|NaN"
                        r"|TinyProfiler|Total GPU|reached max_step")

def scan(path):
    """(n_lines, n_laserdep, last_step, wall) without holding the file in memory."""
    n=ld=0; last=0; wall=None
    with open(path, errors="replace") as fh:
        for ln in fh:
            n+=1
            if ln.startswith("LASERDEP"): ld+=1
            m=STEP_ENDS.match(ln)
            if m: last=int(m.group(1))
            if "TinyProfiler total" in ln: wall=ln.strip()
    return n, ld, last, wall

def prune(rd, apply=False, keep_original=False):
    path=os.path.join(rd,"run.log")
    if not os.path.isfile(path): return None
    size0=os.path.getsize(path)
    n0,ld0,last0,wall0=scan(path)
    if wall0 is None:
        return dict(rd=rd, skipped="still running or never finished (no TinyProfiler footer)")
    # find the first and last STEP line so header/footer survive intact
    first_step=last_step_line=None
    with open(path, errors="replace") as fh:
        for i,ln in enumerate(fh):
            if STEP_START.match(ln) or STEP_ENDS.match(ln):
                if first_step is None: first_step=i
                last_step_line=i
    out=path+".pruned"
    kept=0
    with open(path, errors="replace") as fh, open(out,"w") as w:
        for i,ln in enumerate(fh):
            keep = (first_step is None or i < first_step or i > last_step_line
                    or KEEP_ALWAYS.search(ln) or not NOISE.match(ln)
                    or (STEP_ENDS.match(ln) and int(STEP_ENDS.match(ln).group(1))==last0))
            if keep: w.write(ln); kept+=1
    n1,ld1,last1,wall1=scan(out)
    ok = (ld1==ld0 and last1==last0 and wall1==wall0)
    size1=os.path.getsize(out)
    res=dict(rd=rd, size0=size0, size1=size1, n0=n0, n1=n1, ld=ld0, ok=ok,
             last=last0, freed=size0-size1)
    if not ok:
        os.remove(out); res["skipped"]=f"VERIFY FAILED (LASERDEP {ld0}->{ld1}, step {last0}->{last1})"
        return res
    if apply:
        if keep_original: shutil.copy2(path, path+".orig")
        os.replace(out, path)
    else:
        os.remove(out)
    return res

def main():
    ap=argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--apply", action="store_true", help="rewrite in place (default is a dry run)")
    ap.add_argument("--keep-original", action="store_true")
    a=ap.parse_args()
    tot=0
    print(f"{'run':32s} {'before':>9s} {'after':>9s} {'freed':>9s}  {'LASERDEP':>9s} {'verify':>7s}")
    for rd in a.run_dirs:
        rd=rd.rstrip("/")
        r=prune(rd, apply=a.apply, keep_original=a.keep_original)
        if r is None: continue
        if r.get("skipped"):
            print(f"{os.path.basename(rd):32s}  skipped -- {r['skipped']}"); continue
        tot+=r["freed"]
        print(f"{os.path.basename(rd):32s} {r['size0']/1e6:8.1f}M {r['size1']/1e6:8.1f}M "
              f"{r['freed']/1e6:8.1f}M  {r['ld']:9d} {'OK' if r['ok'] else 'FAIL':>7s}")
    print(f"\n{'APPLIED' if a.apply else 'DRY RUN'} — total {tot/1e9:.2f} GB")

if __name__ == "__main__":
    main()
