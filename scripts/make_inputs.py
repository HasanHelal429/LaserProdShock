#!/usr/bin/env python3
"""Generate a WarpX input deck from a run's ``config.yaml`` — the forward direction.

``config.yaml`` is the single source of truth. This script is the only thing that
writes a deck; **never hand-edit one**. Three modes:

    python scripts/make_inputs.py runs/<ID>            # write the deck
    python scripts/make_inputs.py runs/<ID> --check    # would the deck change? (no write)
    python scripts/make_inputs.py runs/<ID> --verify   # does warpx_used_inputs match?

``--verify`` is the post-run check: it re-renders the deck from the config, resolves both
it and the ``warpx_used_inputs`` WarpX actually parsed down to numbers, and diffs them.
That catches a hand-edit, a stale deck, and any ParmParse override passed on the command
line (``launch.sh ... -- max_step=20``), which is why overrides are for smoke tests only.

Structural validation and the numerical gates run on every invocation, because a deck
that renders is not the same as a deck that should be launched.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from laserprod import config as lpconfig   # noqa: E402
from laserprod import deck as lpdeck       # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", help="run directory containing config.yaml")
    ap.add_argument("--check", action="store_true",
                    help="report whether the on-disk deck differs; write nothing")
    ap.add_argument("--verify", action="store_true",
                    help="verify warpx_used_inputs against config.yaml (post-run)")
    ap.add_argument("--quiet", "-q", action="store_true", help="less chatter")
    args = ap.parse_args()

    cfg = lpconfig.load(args.run_dir)
    rid = lpconfig.run_id(cfg)
    sc = lpconfig.derive(cfg)

    # --- structural validation (hard errors raise out of load/validate) ---
    warns = lpconfig.validate(cfg)
    if not args.quiet:
        print(sc.pretty())
    for w in warns:
        print(f"WARN  {w}")

    # --- gates ---
    gates = lpconfig.gates(cfg, sc)
    print(f"\ngates: {lpconfig.gate_summary(gates)}")
    for g in gates:
        if g.status in ("warn", "fail"):
            print(f"  {g.status.upper():4s} {g.key} {g.label} = "
                  f"{'' if g.value is None else f'{g.value:.4g}'}\n"
                  f"       {' '.join(str(g.detail).split())}")
    if any(g.status == "fail" for g in gates):
        print("\n*** A GATE FAILED. Fix the config before launching: a deck that\n"
              "*** violates G1 produces numbers that measure an instability, not\n"
              "*** physics (TEST_PLAN.md §1.2 hazard 2).")

    deck_name = cfg.get("meta", {}).get("deck") or f"inputs_{rid}"
    deck_path = os.path.join(cfg["_run_dir"], deck_name)
    text = lpdeck.render(cfg)

    # --- verify mode -----------------------------------------------------
    if args.verify:
        used = os.path.join(cfg["_run_dir"], "warpx_used_inputs")
        if not os.path.isfile(used):
            print(f"\nverify: no warpx_used_inputs in {args.run_dir} "
                  "(has the run started?)")
            return 1
        diffs = lpdeck.verify(cfg, used)
        if diffs:
            print(f"\nverify: {len(diffs)} MISMATCH(es) between config.yaml and "
                  "what WarpX ran:")
            for d in diffs:
                print(f"  {d}")
            return 1
        print("\nverify: OK — warpx_used_inputs matches config.yaml")
        return 0

    # --- check mode ------------------------------------------------------
    if args.check:
        if not os.path.isfile(deck_path):
            print(f"\ncheck: {deck_name} does not exist yet (would be created)")
            return 1
        old = open(deck_path).read()
        if old == text:
            print(f"\ncheck: {deck_name} is up to date with config.yaml")
            return 0
        print(f"\ncheck: {deck_name} DIFFERS from config.yaml — regenerate")
        return 1

    # --- write -----------------------------------------------------------
    existed = os.path.isfile(deck_path)
    unchanged = existed and open(deck_path).read() == text
    with open(deck_path, "w") as fh:
        fh.write(text)
    verb = "unchanged" if unchanged else ("rewrote" if existed else "wrote")
    print(f"\n{verb} {deck_path}  ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
