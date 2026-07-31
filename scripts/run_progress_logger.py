#!/usr/bin/env python3
"""Sidecar progress logger for a WarpX run — real wall-clock checkpoints.

Watches a run's ``run.log`` and appends a checkpoint line to ``<run_dir>/progress.log``
every N percent of ``max_step``. Each line reports real (wall-clock) elapsed time and
ETA, the WarpX compute rate, a contention factor (wall-rate / compute-rate, >1 when the
machine is shared), and the system load — so compute cost is trackable after the fact
and runs can be paced/scheduled without babysitting them.

Ported from KinShock2020/scripts/run_progress_logger.py with one addition for this
project: when the deck enables the ray-tracing laser and ``warpx.verbose = 1``, WarpX
emits one ``LASERDEP step <n> t <s> Pabs <W> Eabs <J>`` line per application. The
logger tracks those too and reports ``Pabs`` as a fraction of its running maximum,
which is the cheapest live read on the **self-limiting absorption shutoff**
(K ~ n_e^2 T_e^-3/2, so the drive switches itself off as the corona heats and
rarefies — see TEST_PLAN.md §2.3). A run whose ``Pabs/Pmax`` has collapsed to ~0 is no
longer being driven, however many steps remain.

Launch it right after starting WarpX (it waits for run.log to appear) — normally via
``scripts/launch.sh -L``, which does exactly that:

    scripts/launch.sh -b -L runs/P1_vac_1d

    python scripts/run_progress_logger.py runs/P1_vac_1d --every-pct 5 --poll 20
    python scripts/run_progress_logger.py runs/P1_vac_1d --total 125000 --log run.log

--total is auto-detected from warpx_used_inputs / the input deck (last ``max_step``
wins, matching ParmParse), so appended overrides are respected. The logger stops when
the run reaches max_step, prints its end marker, or goes stale.
"""

from __future__ import annotations

import argparse
import atexit
import glob
import os
import re
import time

STEP_RE = re.compile(r"STEP (\d+) ends")
AVG_RE = re.compile(r"Avg\. per step = ([0-9.eE+-]+)")
EVOLVE_RE = re.compile(r"Evolve time = ([0-9.eE+-]+)")
MAXSTEP_RE = re.compile(r"^\s*max_step\s*=\s*(\d+)", re.MULTILINE)
# LASERDEP step <n> t <s> Pabs <W> Eabs <J> [Tlocalfrac <f>]
LASERDEP_RE = re.compile(r"LASERDEP step (\d+) t ([0-9.eE+-]+) "
                         r"Pabs ([0-9.eE+-]+) Eabs ([0-9.eE+-]+)")
END_MARKERS = ("AMReX finalized", "Total Time")


def detect_total(run_dir: str) -> int | None:
    """Last max_step across warpx_used_inputs and any input deck (ParmParse last-wins)."""
    candidates = [os.path.join(run_dir, "warpx_used_inputs")]
    candidates += sorted(glob.glob(os.path.join(run_dir, "inputs*")))
    last = None
    for path in candidates:
        try:
            with open(path) as fh:
                hits = MAXSTEP_RE.findall(fh.read())
            if hits:
                last = int(hits[-1])
        except OSError:
            continue
    return last


def read_state(run_dir_log: str):
    """State from run.log: (step, warpx_s_per_step, evolve_s, ended?, laser)

    ``laser`` is ``None`` when the run has no LASERDEP output, else
    ``(Pabs_latest, Pabs_max, Eabs_latest)``.
    """
    try:
        with open(run_dir_log, errors="replace") as fh:
            txt = fh.read()
    except OSError:
        return None
    steps = STEP_RE.findall(txt)
    step = int(steps[-1]) if steps else 0
    avg = float(AVG_RE.findall(txt)[-1]) if AVG_RE.search(txt) else float("nan")
    ev = float(EVOLVE_RE.findall(txt)[-1]) if EVOLVE_RE.search(txt) else float("nan")
    ended = any(m in txt for m in END_MARKERS)

    laser = None
    hits = LASERDEP_RE.findall(txt)
    if hits:
        pabs = [float(h[2]) for h in hits]
        laser = (pabs[-1], max(pabs), float(hits[-1][3]))
    return step, avg, ev, ended, laser


def fmt_dur(sec: float) -> str:
    sec = int(max(sec, 0))
    return f"{sec // 3600}h{(sec % 3600) // 60:02d}m"


def _release_pidfile(path: str, mine: int) -> None:
    """Remove the PID file only if it is still ours.

    A logger that is killed and immediately relaunched must not have its
    successor's claim deleted by its own atexit handler.
    """
    try:
        with open(path) as fh:
            if int(fh.read().split()[0]) == mine:
                os.remove(path)
    except (OSError, ValueError, IndexError):
        pass


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", help="run directory containing run.log")
    ap.add_argument("--log", default="run.log", help="log filename inside run_dir (default run.log)")
    ap.add_argument("--out", default="progress.log", help="output filename inside run_dir")
    ap.add_argument("--total", type=int, default=None, help="total steps (default: auto-detect max_step)")
    ap.add_argument("--every-pct", type=float, default=10.0, help="checkpoint every this many %% (default 10)")
    ap.add_argument("--poll", type=float, default=30.0, help="seconds between polls (default 30)")
    ap.add_argument("--stale-min", type=float, default=15.0,
                    help="give up if run.log stops advancing this long (default 15 min)")
    args = ap.parse_args()

    log_path = os.path.join(args.run_dir, args.log)
    out_path = os.path.join(args.run_dir, args.out)
    total = args.total or detect_total(args.run_dir)
    if not total:
        raise SystemExit(f"could not determine total steps; pass --total (looked in {args.run_dir})")

    # ------------------------------------------------------------------ #
    # One logger per run directory.
    #
    # Two loggers on one run append to the same progress.log, and the result is
    # not obviously wrong -- it is *subtly* wrong. Each computes wall_elapsed,
    # wall_rate, ETA and contention from ITS OWN start time, so a stale logger
    # left over from a killed run reports the live run's step count against its
    # own clock. That happened on 2026-07-30 (P1_vac_2d_spot_omp): two "10.1%"
    # lines one second apart, 0h18m vs 0h26m elapsed, ETA 2h43m vs 3h51m, and a
    # fabricated x1.41 contention factor. Only warpx_rate agreed, because that
    # one is read out of WarpX's own output instead of being timed here.
    #
    # The claim is a PID file rather than a lock, so a logger killed with -9
    # leaves a stale file that the next one reclaims (the recorded PID is dead).
    pid_path = os.path.join(args.run_dir, ".logger.pid")
    try:
        with open(pid_path) as fh:
            other = int(fh.read().split()[0])
        os.kill(other, 0)                      # signal 0 = "does it exist?"
    except (OSError, ValueError, IndexError):
        pass                                   # no file, junk, or a dead PID
    else:
        raise SystemExit(
            f"a progress logger (pid {other}) is already running for {args.run_dir}.\n"
            f"  Two loggers append to the same {args.out} and each times the run from its\n"
            f"  own start, so the wall-clock columns of both become wrong.\n"
            f"  Kill it BY PID -- `kill {other}` -- not with `pkill -f`, which also matches\n"
            f"  the shell you type it in. Or pass --out to write somewhere else.")
    with open(pid_path, "w") as fh:
        fh.write(f"{os.getpid()}\n")
    atexit.register(lambda: os.path.exists(pid_path)
                    and _release_pidfile(pid_path, os.getpid()))

    def loadavg() -> float:
        try:
            return float(open("/proc/loadavg").read().split()[0])
        except OSError:
            return float("nan")

    def emit(line: str):
        with open(out_path, "a") as fh:
            fh.write(line + "\n")

    # wait for run.log
    t_wait = time.time()
    while not os.path.isfile(log_path):
        if time.time() - t_wait > args.stale_min * 60:
            raise SystemExit(f"run.log never appeared at {log_path}")
        time.sleep(args.poll)

    header = (
        f"# WarpX progress — {os.path.abspath(args.run_dir)}\n"
        f"# logging_started {time.strftime('%Y-%m-%dT%H:%M:%S')}  total_steps={total}  "
        f"every={args.every_pct:g}%  poll={args.poll:g}s\n"
        f"# wall_time | step/total (pct) | wall_elapsed | wall_rate | warpx_rate | "
        f"ETA_wall | contention | load [| laser Pabs/Pmax, Eabs]"
    )
    emit(header)

    t0 = time.time()
    last_pct_bucket = -1
    prev_wall, prev_step = t0, 0
    last_advance_wall, last_seen_step = t0, 0

    while True:
        time.sleep(args.poll)
        st = read_state(log_path)
        if st is None:
            continue
        step, avg, ev, ended, laser = st
        now = time.time()

        if step > last_seen_step:
            last_seen_step, last_advance_wall = step, now
        stale = (now - last_advance_wall) > args.stale_min * 60

        pct = 100.0 * step / total
        bucket = int(pct // args.every_pct)
        done = step >= total or ended
        checkpoint = bucket > last_pct_bucket or done or stale

        if checkpoint and step > 0:
            d_wall = now - prev_wall
            d_step = step - prev_step
            wall_rate = d_wall / d_step if d_step > 0 else float("nan")
            eta = (total - step) * wall_rate if d_step > 0 else float("nan")
            cont = wall_rate / avg if (avg == avg and avg > 0) else float("nan")
            line = (
                f"{time.strftime('%Y-%m-%dT%H:%M:%S')} | {step}/{total} ({pct:4.1f}%) | "
                f"{fmt_dur(now - t0)} | {wall_rate:.4f} s/step(wall) | {avg:.4f} s/step(warpx) | "
                f"ETA ~{fmt_dur(eta)} | x{cont:.2f} | load {loadavg():.1f}"
            )
            if laser is not None:
                pabs, pmax, eabs = laser
                # A laser-off control (gate G3) has Pabs == Pmax == 0 for the whole run, and
                # "laser nan of peak, Eabs 0 J" on every line is noise the reader has to
                # decode. Say what it is instead -- these controls are mandatory companions
                # to every headline run, so this line gets read as often as the driven one.
                if pmax > 0:
                    line += f" | laser {pabs / pmax:.3f} of peak, Eabs {eabs:.4g} J"
                else:
                    line += " | laser OFF (I0 = 0)"
            emit(line)
            last_pct_bucket = bucket
            prev_wall, prev_step = now, step

        if done or stale:
            mean = (now - t0) / max(step, 1)
            status = ("reached max_step" if step >= total
                      else "end marker" if ended else "STALLED (no progress)")
            emit(f"DONE {time.strftime('%Y-%m-%dT%H:%M:%S')} | {step}/{total} "
                 f"({100.0*step/total:.1f}%) | total wall {fmt_dur(now - t0)} | "
                 f"mean {mean:.4f} s/step(wall) | {status}")
            break


if __name__ == "__main__":
    main()
