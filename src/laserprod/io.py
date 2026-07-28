"""Readers for WarpX output — the laser diagnostic, reduced diags, and plotfiles.

The most important reader here is :func:`laserdep_history`. With ``warpx.verbose = 1``
the operator prints one line per application::

    LASERDEP step <n> t <s> Pabs <W> Eabs <J> [Tlocalfrac <f>]

``Pabs``/``Eabs`` are accumulated across all rays and reduced over ranks, and are
**measured directly from the ray tracer**, so they are immune to any grid heating of
the plasma — unlike the particle energies in ``EP.txt``. That is precisely what makes
gate G6 (energy closure) possible: the difference between the tracer's ``Eabs`` and the
particle kinetic-energy gain *is* the grid-heating budget.

``Pabs`` and ``Eabs`` are per unit length in each invariant direction (so W/m and J/m
in 1D... actually W/m^2 and J/m^2 in 1D, W/m and J/m in 2D — one factor of metre per
absent dimension). :func:`incident_power` computes the matching incident power from the
deck geometry so an absorbed *fraction* can be formed consistently.
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass

LASERDEP_RE = re.compile(
    r"LASERDEP\s+step\s+(\d+)\s+t\s+([0-9.eE+-]+)\s+"
    r"Pabs\s+([0-9.eE+-]+)\s+Eabs\s+([0-9.eE+-]+)"
    r"(?:\s+Tlocalfrac\s+([0-9.eE+-]+))?")
STEP_RE = re.compile(r"STEP (\d+) ends")


# --------------------------------------------------------------------------- #
# the laser diagnostic
# --------------------------------------------------------------------------- #
@dataclass
class LaserHistory:
    """Time series from the operator's own ``LASERDEP`` output."""
    step: list          # timestep index
    t: list             # time [s]
    Pabs: list          # instantaneous absorbed power [W, per absent dim]
    Eabs: list          # cumulative absorbed energy [J, per absent dim]
    Tlocalfrac: list    # n_e^2-weighted fraction with a measured (not floored) T_e

    def __len__(self):
        return len(self.step)

    @property
    def Pabs_peak(self) -> float:
        return max(self.Pabs) if self.Pabs else float("nan")

    @property
    def Eabs_final(self) -> float:
        return self.Eabs[-1] if self.Eabs else float("nan")

    def f_abs(self, P_inc: float) -> list:
        """Absorbed fraction history for an incident power ``P_inc``."""
        return [p / P_inc for p in self.Pabs] if P_inc else [float("nan")] * len(self)

    def shutoff_time(self, frac: float = 0.5) -> float | None:
        """First time ``Pabs`` falls below ``frac`` of its peak, after the peak.

        The self-limiting shutoff (K ~ n_e^2 T_e^{-3/2}) is the quantity that sets how
        long the piston is driven, and therefore whether a shock has time to form
        (Schaeffer: formation needs >~ 1 gyroperiod of drive). Returns ``None`` if the
        laser never shuts off within the run.
        """
        if not self.Pabs:
            return None
        pk = self.Pabs_peak
        i_pk = self.Pabs.index(pk)
        for i in range(i_pk, len(self.Pabs)):
            if self.Pabs[i] < frac * pk:
                return self.t[i]
        return None


def laserdep_history(run_dir: str, log: str = "run.log") -> LaserHistory:
    """Parse ``<run_dir>/run.log`` for the operator's LASERDEP lines."""
    path = log if os.path.isabs(log) else os.path.join(run_dir, log)
    step, t, P, E, Tf = [], [], [], [], []
    if not os.path.isfile(path):
        return LaserHistory(step, t, P, E, Tf)
    with open(path, errors="replace") as fh:
        for line in fh:
            if "LASERDEP" not in line:
                continue
            m = LASERDEP_RE.search(line)
            if not m:
                continue
            step.append(int(m.group(1)))
            t.append(float(m.group(2)))
            P.append(float(m.group(3)))
            E.append(float(m.group(4)))
            Tf.append(float(m.group(5)) if m.group(5) else float("nan"))
    return LaserHistory(step, t, P, E, Tf)


def incident_power(scales, cfg: dict) -> float:
    """Incident laser power in the same per-unit-length convention as ``Pabs``.

    The operator launches one ray bundle across the injection face and gives each
    sub-ray a power ``I(r_perp) * sub_area * |u_axis|``, with 1 m assumed per absent
    dimension. So in 1D the incident "power" is just the intensity (W/m^2 -> W per m^2
    of face); in 2D it is the intensity integrated over the transverse extent of the
    face (W/m), reduced by the beam profile and the incidence angle.
    """
    import math

    las = cfg["laser"]
    I0 = float(las["intensity"])
    dims = int(cfg["geometry"]["dims"])
    cos_t = math.cos(math.radians(float(las.get("incidence_angle_deg", 0.0))))
    if dims == 1:
        return I0 * cos_t

    beam = las.get("beam") or {}
    tr = cfg["geometry"]["transverse"]
    x_lo = float(tr["lo_de"]) * scales.de_ref
    x_hi = float(tr["hi_de"]) * scales.de_ref
    prof = str(beam.get("profile", "uniform"))
    if prof == "uniform":
        return I0 * (x_hi - x_lo) * cos_t

    # integral of exp(-((r/w)^2)^m) dx over the face, evaluated numerically so the
    # super-Gaussian order does not need a closed form
    w = float(beam["waist_de"]) * scales.de_ref
    m_ord = float(beam.get("order", 1.0 if prof == "gaussian" else 2.0))
    c0 = beam.get("center_de")
    xc = (float(c0[0] if isinstance(c0, (list, tuple)) else c0) * scales.de_ref
          if c0 is not None else 0.5 * (x_lo + x_hi))
    n = 4001
    dx = (x_hi - x_lo) / (n - 1)
    total = 0.0
    for i in range(n):
        x = x_lo + i * dx
        r2 = (x - xc) ** 2
        wgt = 0.5 if i in (0, n - 1) else 1.0
        total += wgt * math.exp(-((r2 / (w * w)) ** m_ord)) * dx
    return I0 * total * cos_t


def profile_tables(run_dir: str, prefix: str = "laserdep_profile") -> list[str]:
    """Paths to the per-cell deposition-profile dumps, sorted by step.

    ANALYSE THE STEP-0 TABLE. Later dumps drift as the deposition kicks move
    electrons, so only the first one is a clean read of the operator's own profile
    against the initial density.
    """
    pats = [os.path.join(run_dir, "diags", f"{prefix}_*.txt"),
            os.path.join(run_dir, f"{prefix}_*.txt")]
    hits: list[str] = []
    for p in pats:
        hits.extend(glob.glob(p))
    return sorted(set(hits))


# Trailing columns of a laserdep_profile dump, in order, AFTER the coordinates. The
# file's `#` lines are prose, not a column-name row, so the layout is positional:
# <coords...> n_e H P_abs theta_e A   -- 6 columns in 1D, 7 in 2D, 8 in 3D.
PROFILE_TAIL = ["n_e", "H", "P_abs", "theta_e", "A"]


def read_profile_table(path: str) -> dict:
    """Read a ``laserdep_profile_<step>.txt`` dump into ``{column: [values]}``.

    Keys are ``z`` (and ``x`` in 2D) for the cell-centre coordinates, then ``n_e``
    [m^-3], ``H`` [m^2/s^3], ``P_abs`` [W/m^3], ``theta_e`` (the value actually used for
    K) and ``A`` (the IB coefficient). The coordinate keys are named so callers never
    have to index by position -- getting that wrong silently reads ``theta_e`` as
    ``P_abs``, which is how this reader was first written.
    """
    rows: list[list[float]] = []
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            rows.append([float(v) for v in s.split()])
    if not rows:
        return {}
    ncol = len(rows[0])
    ncoord = max(ncol - len(PROFILE_TAIL), 0)
    coord_names = {1: ["z"], 2: ["x", "z"], 3: ["x", "y", "z"]}.get(
        ncoord, [f"c{i}" for i in range(ncoord)])
    cols = coord_names + PROFILE_TAIL[:ncol - ncoord]
    return {c: [r[i] for r in rows] for i, c in enumerate(cols)}


# --------------------------------------------------------------------------- #
# reduced diagnostics
# --------------------------------------------------------------------------- #
def reduced_diag(run_dir: str, name: str) -> dict:
    """Read a WarpX reduced diagnostic (``diags/reducedfiles/<name>.txt``).

    Returns ``{column_name: [values]}``. WarpX writes a ``#``-commented header whose
    entries look like ``3]total(J)``; the index prefix is stripped.
    """
    for cand in (os.path.join(run_dir, "diags", "reducedfiles", f"{name}.txt"),
                 os.path.join(run_dir, "reducedfiles", f"{name}.txt")):
        if os.path.isfile(cand):
            path = cand
            break
    else:
        return {}
    cols, rows = [], []
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                if not cols:
                    cols = [re.sub(r"^\[?\d+\]", "", t) for t in s.lstrip("#").split()]
                continue
            rows.append([float(v) for v in s.split()])
    if not rows:
        return {}
    return {c: [r[i] for r in rows] for i, c in enumerate(cols) if i < len(rows[0])}


def particle_energy(run_dir: str) -> tuple[list, list]:
    """(t, total_particle_KE) from the EP reduced diagnostic, for gate G6."""
    d = reduced_diag(run_dir, "EP")
    if not d:
        return [], []
    t = d.get("time(s)") or d.get("time") or []
    for key in d:
        if key.startswith("total") and "(J)" in key:
            return t, d[key]
    vals = [v for k, v in d.items() if k not in ("step", "time(s)", "time")]
    return t, (vals[0] if vals else [])


def field_energy(run_dir: str) -> tuple[list, list]:
    """(t, total_field_energy) from the FE reduced diagnostic, for gate G6."""
    d = reduced_diag(run_dir, "FE")
    if not d:
        return [], []
    t = d.get("time(s)") or d.get("time") or []
    for key in d:
        if key.startswith("total") and "(J)" in key:
            return t, d[key]
    return t, []


# --------------------------------------------------------------------------- #
# plotfiles
# --------------------------------------------------------------------------- #
def plotfiles(run_dir: str, prefix: str = "diag") -> list[str]:
    """Sorted plotfile directories under ``<run_dir>/diags/``."""
    hits = glob.glob(os.path.join(run_dir, "diags", f"{prefix}*"))
    hits = [h for h in hits if os.path.isdir(h)]
    return sorted(hits, key=lambda p: _step_of(p))


def _step_of(path: str) -> int:
    m = re.search(r"(\d+)$", os.path.basename(path))
    return int(m.group(1)) if m else -1


def last_step(run_dir: str, log: str = "run.log") -> int:
    """Highest completed step reported in run.log (0 if none)."""
    path = os.path.join(run_dir, log)
    if not os.path.isfile(path):
        return 0
    with open(path, errors="replace") as fh:
        steps = STEP_RE.findall(fh.read())
    return int(steps[-1]) if steps else 0
