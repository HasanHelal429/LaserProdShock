"""Load, validate and gate a per-run LaserProdShock config.

The config holds only PRIMARY quantities; :mod:`laserprod.units` derives the rest.

Two kinds of check live here:

``validate``
    **structural** checks — things that would make WarpX abort, or that are silently
    wrong (a single periodic face, oblique incidence in 1D, Silver-Mueller fields
    with a background B). These are hard errors where WarpX would abort anyway, and
    warnings where the deck is merely suspicious.

``gates``
    the **numerical gates G1-G7** of ``TEST_PLAN.md`` 6, each of which exists because
    it was violated somewhere in the prior work. Gates never raise: they return a
    list of :class:`Gate` results so ``run_checks.py`` can print them, plot them, and
    a run README can record them. A deck may legitimately sit outside a gate (the
    cold target *always* fails G2), but it may not do so silently.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

import yaml

from . import units

# Semantic boundary names understood by the config (deck.py maps them to WarpX
# tokens). Kept here so validate() can check names before deck.render() runs.
BOUNDARY_NAMES = ("periodic", "reflecting", "open", "absorbing")

# lnLambda modes the operator accepts, mirrored from units.coulomb_log_for so
# validate() can reject a typo before WarpX aborts on it.
COULOMB_LOG_MODES = units.COULOMB_LOG_MODES

REQUIRED_SECTIONS = ["meta", "laser", "reference", "plasma", "geometry", "numerics"]


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def load(path: str) -> dict:
    """Load a config from a YAML file or a run directory (containing config.yaml)."""
    if os.path.isdir(path):
        path = os.path.join(path, "config.yaml")
    with open(path, "r") as fh:
        try:
            cfg = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            # These configs carry long prose `description:` / `note:` fields, and the
            # commonest way to break one is a bare ": " inside an unquoted multi-line
            # scalar ("see P1_vac_1d: the band spreads..."), which YAML reads as a new
            # mapping key. The raw traceback is 30 frames of yaml internals and never
            # says that, so name the actual cause here.
            mark = getattr(exc, "problem_mark", None)
            where = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
            hint = ""
            if mark is not None:
                try:
                    with open(path) as f2:
                        line = f2.read().splitlines()[mark.line]
                    hint = (f"\n  offending line: {line.strip()!r}"
                            "\n  A bare ': ' inside an unquoted multi-line string starts a "
                            "new YAML key. Use ' -- ' instead, or quote the whole value.")
                except Exception:
                    pass
            raise ValueError(f"{path} is not valid YAML{where}: "
                             f"{getattr(exc, 'problem', exc)}{hint}") from exc
    cfg["_path"] = os.path.abspath(path)
    cfg["_run_dir"] = os.path.dirname(cfg["_path"])
    _inject_flash_table_scales(cfg)
    missing = [k for k in REQUIRED_SECTIONS if k not in cfg]
    if missing:
        raise KeyError(f"config missing required section(s): {missing}")
    return cfg


def derive(cfg: dict) -> units.Scales:
    """Convenience: config dict -> derived :class:`laserprod.units.Scales`."""
    return units.derive(cfg)


def run_id(cfg: dict) -> str:
    return str(cfg.get("meta", {}).get("run_id") or
               os.path.basename(cfg.get("_run_dir", "unknown")))


# --------------------------------------------------------------------------- #
# boundary helpers (dimension-general)
# --------------------------------------------------------------------------- #
def boundary_faces(cfg: dict) -> dict:
    """``{axis_name: (lo_name, hi_name)}`` in WarpX axis order.

    The config's ``geometry.boundary`` has an ``axis`` entry (the propagation axis)
    and, in 2D, a ``transverse`` entry. Each is either a single name applied to both
    faces or a ``{lo, hi}`` mapping.
    """
    geo = cfg["geometry"]
    b = geo.get("boundary") or {}
    names = units.axis_names(int(geo["dims"]))
    normal = str(geo.get("normal_axis", "z"))

    def pair(spec, default="periodic"):
        if spec is None:
            return (default, default)
        if isinstance(spec, dict):
            return (str(spec.get("lo", default)), str(spec.get("hi", default)))
        return (str(spec), str(spec))

    out = {}
    for ax in names:
        out[ax] = pair(b.get("axis")) if ax == normal else pair(b.get("transverse"))
    return out


def has_background_field(cfg: dict) -> bool:
    fld = cfg.get("field") or {}
    return (str(fld.get("orientation", "none")) != "none"
            and float(fld.get("vA_over_c", 0.0) or 0.0) != 0.0)


def is_vacuum(cfg: dict) -> bool:
    return not (cfg.get("plasma") or {}).get("ambient")


# --------------------------------------------------------------------------- #
# structural validation
# --------------------------------------------------------------------------- #
def validate(cfg: dict) -> list[str]:
    """Structural checks. Returns warning strings; raises only on a hard error."""
    warns: list[str] = []
    geo, las, num = cfg["geometry"], cfg["laser"], cfg["numerics"]
    dims = int(geo["dims"])

    if dims not in (1, 2, 3):
        raise ValueError(f"geometry.dims must be 1, 2 or 3 (got {dims})")

    normal = str(geo.get("normal_axis", "z"))
    if normal != "z":
        raise ValueError(
            f"geometry.normal_axis = {normal!r}: only 'z' is supported. The laser "
            "propagates along the target normal, and WarpX's 1D geometry is z-only, "
            "so every deck in this project keeps the propagation axis on z (2D is "
            "XZ, with x transverse).")
    if str(las.get("direction", "z")) != normal:
        raise ValueError(f"laser.direction ({las.get('direction')}) must equal "
                         f"geometry.normal_axis ({normal})")

    if dims == 1:
        if geo.get("transverse"):
            warns.append("geometry.transverse is ignored in 1D")
        if abs(float(las.get("incidence_angle_deg", 0.0))) > 1e-12:
            raise ValueError("laser.incidence_angle_deg must be 0 in 1D (oblique "
                             "incidence needs a transverse dimension to refract into)")
        beam = las.get("beam") or {}
        if str(beam.get("profile", "uniform")) != "uniform":
            warns.append("laser.beam.profile is meaningless in 1D (no transverse "
                         "dimension); it will be written as 'uniform'")
    else:
        if not geo.get("transverse"):
            raise ValueError(f"geometry.transverse.{{lo_de,hi_de}} is required in {dims}D")

    # --- boundaries ---
    faces = boundary_faces(cfg)
    for ax, (lo, hi) in faces.items():
        for name in (lo, hi):
            if name not in BOUNDARY_NAMES:
                raise ValueError(f"unknown boundary {name!r} on axis {ax}; expected "
                                 f"one of {list(BOUNDARY_NAMES)}")
        n_per = (lo == "periodic") + (hi == "periodic")
        if n_per == 1:
            raise ValueError(
                f"axis {ax}: exactly one face is 'periodic' -- WarpX requires both "
                f"faces periodic together or neither (got lo={lo}, hi={hi})")

    if has_background_field(cfg):
        bad = [ax for ax, p in faces.items() if "absorbing" in p]
        if bad:
            warns.append(
                f"boundary 'absorbing' (Silver-Mueller) on axis {bad} is incompatible "
                "with the B-field divergence cleaner that runs when a background B is "
                "set -- use 'open' (pec fields + absorbing particles) instead")

    # The hazard that cost two decks upstream: a free expansion behind periodic
    # boundaries wraps its runaway ion front back onto the upstream.
    ax_faces = faces[normal]
    if "periodic" in ax_faces and not (cfg.get("meta", {}).get("expect_wrap")):
        warns.append(
            "propagation axis is periodic: a free ablation expansion has a runaway "
            "ion front (measured at 0.20 c upstream) that will WRAP and pollute the "
            "far side, and WarpX forces particle BCs periodic when field BCs are. "
            "Set meta.expect_wrap: true if this is a deliberate control run.")

    # --- laser block ---
    beam = las.get("beam") or {}
    prof = str(beam.get("profile", "uniform"))
    if prof not in ("uniform", "gaussian", "super_gaussian"):
        raise ValueError(f"laser.beam.profile must be uniform|gaussian|"
                         f"super_gaussian (got {prof!r})")
    if prof != "uniform" and not beam.get("waist_de"):
        raise ValueError(f"laser.beam.waist_de is required for beam profile {prof!r}")
    if beam.get("focus_de") is not None and len(beam["focus_de"]) != dims:
        raise ValueError(f"laser.beam.focus_de needs one entry per dimension "
                         f"({dims}), got {len(beam['focus_de'])}")
    if str(las.get("inject_side", "lo")) not in ("lo", "hi"):
        raise ValueError("laser.inject_side must be 'lo' or 'hi'")
    # 'hybrid_fluid' is the third value: it reads T_e from the Ohm's-law solver's
    # temperature field instead of measuring it from electron macroparticles -- which a
    # hybrid run does not have. Only meaningful under a hybrid solver, and the operator
    # itself asserts the same pairing with density_source.
    tmode = str(las.get("temperature_mode", "local"))
    if tmode not in ("local", "fixed", "hybrid_fluid"):
        raise ValueError("laser.temperature_mode must be 'local', 'fixed' or "
                         "'hybrid_fluid'")
    solver = (cfg.get("solver") or {})
    is_hybrid = str(solver.get("type", "em")) == "hybrid"
    if tmode == "hybrid_fluid" and not is_hybrid:
        raise ValueError("laser.temperature_mode = 'hybrid_fluid' requires "
                         "solver.type = 'hybrid'")
    dsrc = str(las.get("density_source", "species"))
    if dsrc not in ("species", "hybrid_rho"):
        raise ValueError("laser.density_source must be 'species' or 'hybrid_rho'")
    if tmode == "hybrid_fluid" and dsrc != "hybrid_rho":
        # mirrors the operator's own assert: the fluid T_e is read onto the same grid as
        # the fluid n_e, so taking one without the other is incoherent.
        raise ValueError("laser.temperature_mode = 'hybrid_fluid' requires "
                         "laser.density_source = 'hybrid_rho'")
    # Tokens are the OPERATOR's own ('species' | 'electron_fluid'), not a friendlier
    # synonym: a translation layer here is one more place for the deck to drift from what
    # WarpX actually parses.
    dep = str(las.get("deposit_to", "species"))
    if dep not in ("species", "electron_fluid"):
        raise ValueError("laser.deposit_to must be 'species' or 'electron_fluid'")
    if dep == "electron_fluid" and dsrc != "hybrid_rho":
        raise ValueError("laser.deposit_to = 'electron_fluid' requires "
                         "laser.density_source = 'hybrid_rho'")
    if is_hybrid:
        hyb = solver.get("hybrid") or {}
        ee = str(hyb.get("electron_energy_mode", "none"))
        if ee not in ("none", "source_only", "advected"):
            # 'conducting' parses in WarpX only to abort with an explanation; refuse it
            # here so the failure arrives at config time, not 500k steps in.
            raise ValueError(
                "solver.hybrid.electron_energy_mode must be none|source_only|advected"
                + (" -- 'conducting' is NOT implemented in WarpX (it aborts: the energy "
                   "equation is solved without a heat flux)" if ee == "conducting" else ""))
        if ee == "advected" and hyb.get("gamma") is not None:
            raise ValueError(
                "solver.hybrid.gamma must be absent when electron_energy_mode = "
                "'advected': that mode solves eps = (3/2) n kB Te, which fixes "
                "gamma = 5/3, and applying the polytropic closure on top double-counts "
                "compression heating")
        if dep != "electron_fluid":
            raise ValueError("solver.type = 'hybrid' requires laser.deposit_to = "
                             "'electron_fluid' -- a hybrid run has no electron "
                             "macroparticles to kick")

    # --- collisions block (optional) ---
    col = cfg.get("collisions") or {}
    if col.get("enabled"):
        if str(col.get("type", "coulomb")) != "coulomb":
            raise ValueError("collisions.type must be 'coulomb'")
        pairs = col.get("pairs")
        if not isinstance(pairs, list) or not pairs:
            raise ValueError("collisions.enabled requires a non-empty collisions.pairs "
                             "list of [species_a, species_b]")
        # Validate against the species that will ACTUALLY be emitted. A pair naming a
        # species the deck never creates aborts inside WarpX at startup -- after the
        # queue has handed over the GPU, which is the expensive place to find out.
        from . import deck as _deck          # local import: deck imports config
        known = set(_deck._species_table(cfg))
        for pr in pairs:
            if not (isinstance(pr, (list, tuple)) and len(pr) == 2):
                raise ValueError(f"collisions.pairs entries must be [a, b] (got {pr!r})")
            for nm in pr:
                if str(nm) not in known:
                    raise ValueError(
                        f"collisions.pairs names unknown species {str(nm)!r}; "
                        f"this run has {sorted(known)}")
    # --- target injector block (optional) ---
    # Same principle as the collisions block: a species name the deck never creates, or a
    # box outside the domain, aborts inside WarpX at startup -- after the queue has handed
    # over the GPU. Catch it at config time.
    inj = cfg.get("injector") or {}
    if inj.get("enabled"):
        from . import deck as _deck          # local import: deck imports config
        known = set(_deck._species_table(cfg))
        for key in ("species", "lo_de", "hi_de", "density_over_ncr", "ppc_reference",
                    "tau_over_wpe"):
            if inj.get(key) is None:
                raise ValueError(f"injector.enabled requires injector.{key}")
        for key in ("species", "neutralizing_species"):
            nm = inj.get(key)
            if nm is not None and str(nm) not in known:
                raise ValueError(f"injector.{key} names unknown species {str(nm)!r}; "
                                 f"this run has {sorted(known)}")
        lo, hi = float(inj["lo_de"]), float(inj["hi_de"])
        if hi <= lo:
            raise ValueError(f"injector.hi_de ({hi}) must exceed injector.lo_de ({lo})")
        ax = (cfg.get("geometry") or {}).get("axis") or {}
        alo, ahi = ax.get("lo_de"), ax.get("hi_de")
        if alo is not None and ahi is not None and not (float(alo) <= lo < hi <= float(ahi)):
            raise ValueError(f"injector box [{lo}, {hi}] d_e is not inside the domain "
                             f"[{alo}, {ahi}] d_e")
        # The injector REPLENISHES a deficit; pinning above the initial slab density would
        # make it a source rather than a reservoir, and the run would not be comparable to
        # one without it.
        tgt = (cfg.get("plasma") or {}).get("target") or {}
        n_t = tgt.get("density_over_ncr")
        if n_t is not None and float(inj["density_over_ncr"]) > float(n_t) * 1.001:
            raise ValueError(
                f"injector.density_over_ncr ({inj['density_over_ncr']}) exceeds the "
                f"target's own density ({n_t}); the injector replenishes a DEFICIT, so a "
                f"higher value makes it a particle source and G6 will not close")
        if float(inj["tau_over_wpe"]) <= 0:
            raise ValueError("injector.tau_over_wpe must be positive")
        if int(inj["ppc_reference"]) <= 0:
            raise ValueError("injector.ppc_reference must be positive")

    # lnLambda: a constant knob, or evaluated per cell from the local (n_e, T_e).
    # See units.coulomb_log_for for what each mode is and which one is physical.
    if str(las.get("coulomb_log_mode", "constant")) not in COULOMB_LOG_MODES:
        raise ValueError(f"laser.coulomb_log_mode must be one of "
                         f"{'|'.join(COULOMB_LOG_MODES)} "
                         f"(got {las['coulomb_log_mode']!r})")
    if float(las.get("intensity", 0.0)) < 0:
        raise ValueError("laser.intensity must be non-negative")
    rc = float(las.get("ray_cfl", 0.25))
    if not (0.0 < rc <= 1.0):
        raise ValueError("laser.ray_cfl must be in (0, 1]")
    # Ray-march performance knobs (Phase 1.5). None of these may change the
    # answer, and n_accumulators only fixes the summation ORDER -- but a run that
    # is to be compared bit for bit with another must declare the same value, so
    # they are validated here rather than left to WarpX to reject at launch.
    if las.get("ray_threads") is not None and int(las["ray_threads"]) < 0:
        raise ValueError("laser.ray_threads must be >= 0 (0 = whatever OpenMP offers)")
    if las.get("n_accumulators") is not None and int(las["n_accumulators"]) < 1:
        raise ValueError("laser.n_accumulators must be >= 1")

    # --- geometry sanity vs the target ---
    # --- does the target fit, and does it touch the injection face? ---
    # Both questions are about DENSITY, not about a nominal extent: the corona is a
    # Gaussian on the laser-facing side only, so "where the target ends" means "where
    # its density stops mattering optically". n_edge below is that threshold.
    sc = units.derive(cfg)
    tgt = cfg["plasma"]["target"]
    z_t = float(tgt.get("center_de", 0.0)) * sc.de_ref
    half_t = 0.5 * sc.thickness
    inject_hi = str(las.get("inject_side", "lo")) == "hi"
    n_edge = 1e-3 * sc.n_cr                 # optically negligible at any Z_eff lnLambda
    reach = 0.0
    if sc.scale_length > 0 and sc.n_targ > n_edge:
        reach = sc.scale_length * math.sqrt(math.log(sc.n_targ / n_edge))
    face_pos = z_t + half_t if inject_hi else z_t - half_t
    if inject_hi:
        z_min, z_max = z_t - half_t, face_pos + reach
    else:
        z_min, z_max = face_pos - reach, z_t + half_t
    if z_min < sc.domain_lo or z_max > sc.domain_hi:
        warns.append(
            f"the target spans [{z_min/sc.de_ref:.0f}, {z_max/sc.de_ref:.0f}] d_e "
            f"(flat top {sc.thickness/sc.de_ref:.0f} d_e plus the one-sided corona out "
            f"to 1e-3 n_cr) but the domain is [{sc.domain_lo/sc.de_ref:.0f}, "
            f"{sc.domain_hi/sc.de_ref:.0f}] d_e")

    # Plasma sitting ON the injection face is not a harmless overlap: rays launch
    # exactly on that plane (LaserDeposition.cpp), so the beam would be absorbed in the
    # boundary cell from step 0 and the drive becomes a boundary quantity.
    face = sc.domain_hi if inject_hi else sc.domain_lo
    d_face = abs(face - face_pos)
    n_at_face = (sc.n_targ * math.exp(-(d_face / sc.scale_length) ** 2)
                 if sc.scale_length > 0 else (sc.n_targ if d_face <= 0 else 0.0))
    if n_at_face > n_edge and not cfg.get("meta", {}).get("expect_face_plasma"):
        warns.append(
            f"the target's corona is {n_at_face/sc.n_cr:.2g} n_cr at the laser "
            "injection face, and rays launch EXACTLY ON that face -- the beam will be "
            "absorbed in the boundary cell from step 0. Set meta.expect_face_plasma: "
            "true if that is the point of the run.")

    if float(geo.get("dx_over_dz", 1.0)) != 1.0 and dims > 1:
        warns.append(
            f"dx_over_dz = {geo['dx_over_dz']}: the ray tracer's arc-length step is "
            "ray_cfl * min(dx) -- non-square cells make the ray step finer than the "
            "coarse direction needs, raising cost without accuracy")

    if is_vacuum(cfg) and has_background_field(cfg):
        warns.append("a background field is set but there is no ambient plasma: vA "
                     "and B0 are undefined without n_amb, so the field is ignored")
    return warns


# --------------------------------------------------------------------------- #
# the numerical gates (TEST_PLAN.md 6)
# --------------------------------------------------------------------------- #
@dataclass
class Gate:
    key: str          # 'G1' ...
    label: str
    status: str       # 'pass' | 'warn' | 'fail' | 'info' | 'post'
    value: float | None
    detail: str

    @property
    def ok(self) -> bool:
        return self.status in ("pass", "info")


def gates(cfg: dict, sc: units.Scales | None = None) -> list[Gate]:
    """Evaluate the pre-run numerical gates. Never raises."""
    sc = sc or units.derive(cfg)
    g = (cfg.get("gates") or {})
    out: list[Gate] = []

    # A hybrid run has NO electron macroparticles, so the omega_pe and Debye
    # constraints do not exist for it -- not "are relaxed", do not exist. A config says
    # so by setting the gate limit to null, and the gate then reports `n/a` rather than
    # silently passing (which would read as "checked and fine").
    hybrid_solver = str((cfg.get("solver") or {}).get("type", "em")) == "hybrid"

    # --- G1: omega_pe*dt at the PEAK compressed density ---
    if "omega_pe_dt_max" in g and g["omega_pe_dt_max"] is None:
        out.append(Gate("G1", "omega_pe*dt at peak", "info", None,
                        "n/a: no electron macroparticles to be resolved"
                        if hybrid_solver else
                        "n/a: gates.omega_pe_dt_max explicitly null"))
        lim = None
    else:
        lim = float(g.get("omega_pe_dt_max", 1.2))
    comp = float(g.get("compression_factor", 2.0))
    if lim is not None:
      status = "pass" if sc.wpe_dt_peak <= lim else (
        "warn" if sc.wpe_dt_peak < 2.0 else "fail")
      out.append(Gate(
        "G1", f"omega_pe*dt at {comp:g}x compression", status, sc.wpe_dt_peak,
        f"initial {sc.wpe_dt_targ:.3f} at {sc.n_targ_over_ncr:.2f} n_cr; "
        f"{sc.wpe_dt_peak:.3f} at {comp:g}x; limit 2 reached at "
        f"{sc.n_over_ncr_at_wpe_dt_2:.2f} n_cr (budget {lim:g}). "
        "The grid CFL cannot see this limit -- it is set by dz/c and knows nothing "
        "about how dense the plasma is."))

    # --- G2: dz/lambda_D per region ---
    if "dz_over_lambdaD_max" in g and g["dz_over_lambdaD_max"] is None:
        out.append(Gate("G2", "dz/lambda_D per region", "info", None,
                        "n/a: the hybrid does not resolve the Debye length by design"
                        if hybrid_solver else
                        "n/a: gates.dz_over_lambdaD_max explicitly null"))
        lim2 = None
    else:
        lim2 = float(g.get("dz_over_lambdaD_max", 8.0))
    parts = [f"target(cold) {sc.dz_over_lD_targ:.0f}"]
    if sc.dz_over_lD_amb is not None:
        parts.append(f"ambient {sc.dz_over_lD_amb:.1f}")
    if lim2 is not None:
      amb_bad = sc.dz_over_lD_amb is not None and sc.dz_over_lD_amb > lim2
      out.append(Gate(
        "G2", "dz/lambda_D per region", "warn" if amb_bad else "info",
        sc.dz_over_lD_targ,
        ", ".join(parts) + f" (ambient budget {lim2:g}). "
        "The cold near-critical target is Debye-under-resolved by construction on "
        "one uniform grid -- this is a MEASUREMENT, made meaningful by G3, not a "
        "pass/fail. Economise via ppc/domain/duration, never by coarsening dz (G7)."))

    # --- G3: laser-off control ---
    off = (cfg.get("controls") or {}).get("laser_off")
    rd = cfg.get("_run_dir", "")
    if float(cfg["laser"].get("intensity", 0.0)) == 0.0:
        out.append(Gate("G3", "laser-off control", "info", None,
                        "this run IS a laser-off control (intensity = 0)"))
    elif off:
        sib = os.path.join(os.path.dirname(rd), str(off)) if rd else str(off)
        exists = os.path.isdir(sib)
        out.append(Gate("G3", "laser-off control", "pass" if exists else "warn", None,
                        f"declared control {off!r}"
                        + ("" if exists else " -- but that run directory does not exist")))
    elif hybrid_solver:
        # G3 exists to separate laser heating from GRID heating, and grid heating is an
        # electron-macroparticle effect. A hybrid run has none, so the control does not
        # buy what it buys elsewhere. Reported as info, never silently passed.
        out.append(Gate("G3", "laser-off control", "info", None,
                        "n/a: no electron macroparticles, so there is no particle "
                        "grid-heating channel for a laser-off run to isolate. The "
                        "energy question here is the electron energy equation (G6)."))
    else:
        out.append(Gate("G3", "laser-off control", "warn", None,
                        "no controls.laser_off declared. The cold target is Debye-"
                        "under-resolved (G2), so grid heating can only be separated "
                        "from laser heating by an identical laser-off run."))

    # --- G4: ray_cfl / turning point ---
    interior_crit = sc.n_targ_over_ncr > 1.0
    declared = bool((cfg.get("controls") or {}).get("ray_cfl_ladder"))
    out.append(Gate(
        "G4", "ray_cfl convergence", "info" if not interior_crit else
        ("pass" if declared else "warn"), float(cfg["laser"].get("ray_cfl", 0.25)),
        (f"target peak {sc.n_targ_over_ncr:.2f} n_cr > 1: there IS an interior "
         "critical surface, and ray_cfl convergence is non-monotonic for "
         "turning-point problems (the 0.25 default sits near a 2.5% excursion). "
         "Declare controls.ray_cfl_ladder once checked."
         if interior_crit else
         f"target peak {sc.n_targ_over_ncr:.2f} n_cr < 1: underdense, no turning "
         "point, and uniform slabs are exact at any ray_cfl.")))

    # --- G5: ppc for local temperature mode ---
    ppc = (cfg["numerics"].get("ppc") or {})
    ppc_t = int(ppc.get("target", 0))
    _tm = str(cfg["laser"].get("temperature_mode", "local"))
    local = _tm == "local"
    lim5 = int(g.get("ppc_target_min", 200))
    status = "info" if not local else ("pass" if ppc_t >= lim5 else "warn")
    # Order-of-magnitude bias on <T^-3/2>: with N macroparticles per cell the
    # temperature has relative spread ~sqrt(2/3N), giving a bias ~(15/8)(2/3N). This
    # OVER-estimates the measured values (it gives 5% where 25 ppc was measured at ~3%,
    # and 0.16% where 800 ppc was measured at <0.1%), so quote it as an upper bound.
    bias = (15.0 / 8.0) * (2.0 / (3.0 * ppc_t)) if ppc_t else float("nan")
    out.append(Gate(
        "G5", "ppc for local T_e", status, float(ppc_t),
        f"target ppc {ppc_t}, mode {_tm}. "
        + (f"Absorption bias <~{bias*100:.1f}% (upper bound; T^-3/2 is convex, so "
           f"per-cell noise biases K HIGH -- measured ~3% at 25 ppc, <0.1% at 800; "
           f"budget {lim5} ppc). Watch Tlocalfrac."
           if local else
           ("hybrid_fluid mode: T_e is a SOLVED FIELD, not a particle moment, so there "
            "is no ppc-driven absorption bias -- and no Tlocalfrac to watch. The "
            "accuracy question moves to the electron energy equation instead."
            if _tm == "hybrid_fluid"
            else "fixed mode: no ppc-driven absorption bias."))))

    # --- G6: energy closure (post-run) ---
    out.append(Gate("G6", "energy closure", "post", None,
                    "post-run: tracer E_abs (immune to grid heating) vs the particle KE "
                    "gain + field energy gain. Their difference is the grid-heating "
                    "budget ONLY WHEN BOUNDARY LOSSES ARE SMALL: absorbed particles "
                    "carry energy out and WarpX does not report it, so at 5.8% and 17% "
                    "particle loss the raw gap read +218% and +235% (RESULTS "
                    "2026-07-28). Always quote the loss fraction beside it."))

    # --- G7: dz provenance ---
    out.append(Gate("G7", "dz unchanged when economising", "info",
                    float(cfg["geometry"]["dz_over_de"]),
                    f"dz = {cfg['geometry']['dz_over_de']} d_e,{sc.length_scale} "
                    f"= {sc.dz*1e6:.4f} um. The free parameter is dz/lambda_D (G2), "
                    "not resolution in d_e: coarsening 0.5 -> 1.0 d_e blew a run up "
                    "upstream (ambient to u ~ 0.15 c, B_y/B_0 = 82)."))
    return out


def gate_summary(gs: list[Gate]) -> str:
    n = {k: sum(1 for x in gs if x.status == k) for k in
         ("pass", "warn", "fail", "info", "post")}
    return (f"{n['pass']} pass, {n['warn']} warn, {n['fail']} fail, "
            f"{n['info']} info, {n['post']} post-run")


# --------------------------------------------------------------------------- #
# ASCII geometry diagram (for run READMEs)
# --------------------------------------------------------------------------- #
def _beam_intensity_frac(cfg: dict, x_de: float) -> float:
    """Local intensity / peak intensity at transverse offset ``x_de``, for the diagram.

    Mirrors what ``LaserDeposition`` applies: ``I = I0 exp(-((r/w)^2)^order)``, with
    ``order = 1`` for ``profile = gaussian`` -- so the waist is the 1/e radius of the
    INTENSITY, not of the field. A uniform beam is flat across the box.
    """
    beam = (cfg["laser"].get("beam") or {})
    prof = str(beam.get("profile", "uniform"))
    if prof == "uniform":
        return 1.0
    w = float(beam.get("waist_de", 0.0))
    if w <= 0:
        return 1.0
    ctr = beam.get("center_de", 0.0)
    if isinstance(ctr, (list, tuple)):
        ctr = float(ctr[0]) if ctr else 0.0
    r = abs(x_de - float(ctr))
    order = float(beam.get("order", 1.0) or 1.0)
    return math.exp(-((r / w) ** 2) ** order)


def _target_face_de(cfg: dict, x_de: float, face_planar: float,
                    inject_hi: bool) -> float | None:
    """The target's laser-facing face at transverse offset ``x_de``, or None if the
    target does not exist there.

    Kept in step with ``deck._face_expr`` / ``deck._density_exprs``: ``curved`` displaces
    the face by ``x^2/(2 Rc)`` (towards the laser for ``inject_hi``), and
    ``finite_width`` simply has no target beyond ``+-w/2``.
    """
    tgt = cfg["plasma"]["target"]
    shape = str(tgt.get("shape", "planar"))
    if shape == "finite_width":
        if abs(x_de) > 0.5 * float(tgt["width_de"]):
            return None
        return face_planar
    if shape == "curved":
        Rc = float(tgt["curvature_radius_de"])
        return face_planar - x_de**2 / (2.0 * Rc) if inject_hi \
            else face_planar + x_de**2 / (2.0 * Rc)
    return face_planar


def _geometry_diagram_2d(cfg: dict, width: int = 58, height: int = 17) -> str:
    """The x-z plane of a 2D/3D run: target, corona, all four boundaries, and the beam.

    ``height`` is odd so that one row lands exactly on x = 0, which is where a centred
    beam peaks and where every on-axis quantity is measured.
    """
    sc = units.derive(cfg)
    geo, las = cfg["geometry"], cfg["laser"]
    tgt = cfg["plasma"]["target"]
    de = sc.de_ref
    z_lo, z_hi = sc.domain_lo / de, sc.domain_hi / de
    zspan = z_hi - z_lo
    tr = geo["transverse"]
    x_lo, x_hi = float(tr["lo_de"]), float(tr["hi_de"])
    inject_hi = str(las.get("inject_side", "lo")) == "hi"
    faces = boundary_faces(cfg)
    ax_lo, ax_hi = faces[str(geo.get("normal_axis", "z"))]
    t_lo, t_hi = faces["x"]

    centre = float(tgt.get("center_de", 0.0))
    half = 0.5 * float(tgt["thickness_de"])
    Ln = float(tgt.get("scale_length_de", 0.0))
    face0 = centre + half if inject_hi else centre - half
    reach = 0.0
    if Ln > 0 and sc.n_targ > 1e-3 * sc.n_cr:
        reach = Ln * math.sqrt(math.log(sc.n_targ / (1e-3 * sc.n_cr)))

    vac = is_vacuum(cfg)
    fill = " " if vac else "."
    laser_off = float(las.get("intensity", 0.0) or 0.0) == 0.0
    BARMAX = 9
    LBL = 7                                    # width of the "  +160 " x-label column
    gutter = 0 if inject_hi else BARMAX + 2    # beam is drawn on the injection side

    def col(z_de):
        return max(0, min(width - 1, int(round((z_de - z_lo) / zspan * (width - 1)))))

    def beam_bar(x_de):
        if laser_off:
            return ""
        frac = _beam_intensity_frac(cfg, x_de)
        n = int(round(BARMAX * frac))
        if frac <= 5e-3 and n <= 0:
            return ""
        return ("<" + "=" * n) if inject_hi else ("=" * n + ">")

    body = []
    for i in range(height):
        x = x_hi - (x_hi - x_lo) * i / (height - 1)
        line = [fill] * width
        f = _target_face_de(cfg, x, face0, inject_hi)
        if f is not None:
            if inject_hi:
                for c in range(col(f), col(f + reach) + 1):
                    line[c] = "~"
                for c in range(col(f - 2 * half), col(f) + 1):
                    line[c] = "#"
            else:
                for c in range(col(f - reach), col(f) + 1):
                    line[c] = "~"
                for c in range(col(f), col(f + 2 * half) + 1):
                    line[c] = "#"
        bar = beam_bar(x)
        lbl = f"{x:+6.0f} "
        if inject_hi:
            body.append(" " * gutter + lbl + "|" + "".join(line) + "|" + bar)
        else:
            body.append(bar.rjust(gutter - 1) + " " + lbl + "|" + "".join(line) + "|")

    pad = " " * (gutter + LBL)
    border = pad + "+" + "-" * width + "+"
    L = ["```"]
    a = L.append
    a(f"{int(geo['dims'])}D  |  z = propagation axis (across), x = transverse (down)"
      f"  |  lengths in d_e at {sc.length_scale} density = {de*1e6:.4f} um")
    a("")
    a(pad + f" x = {x_hi:+.0f}   ({t_hi})")
    a(border)
    L += body
    a(border)
    a(pad + f" x = {x_lo:+.0f}   ({t_lo})")
    a(pad + " " + "^" + " " * (width - 2) + "^")
    a(pad + " " + ax_lo + " " * max(1, width - len(ax_lo) - len(ax_hi)) + ax_hi)
    zl, zr = f"z = {z_lo:+.0f}", f"z = {z_hi:+.0f}"
    a(pad + " " + zl + " " * max(1, width - len(zl) - len(zr)) + zr)
    a("")
    shape = str(tgt.get("shape", "planar"))
    extra = ""
    if shape == "curved":
        extra = (f", CURVED face (R_c = {tgt['curvature_radius_de']:g} d_e, so the face "
                 f"is displaced by x^2/(2 R_c))")
    elif shape == "finite_width":
        extra = f", FINITE WIDTH {tgt['width_de']:g} d_e in x"
    a(f"  #  target flat top : {tgt['density_over_ncr']:g} n_cr, "
      f"{tgt['thickness_de']:g} d_e thick, centred at {centre:+g} d_e{extra}")
    if Ln > 0:
        # The FORM is a config primary (deck.py keys off corona_profile), and a diagram
        # that names the wrong one is worse than no diagram: an exponential and a Gaussian
        # of the same L_n put the critical surface in different places, which is the whole
        # subject of decision D1.
        a(f"  ~  coronal ramp   : {_corona_form(tgt)}, L_n = {Ln:g} d_e on the "
          f"LASER-FACING side (face at z = {face0:+g}), drawn out to 1e-3 n_cr")
    if vac:
        a("  ' ' vacuum        : no ambient plasma")
    else:
        amb = cfg["plasma"]["ambient"]
        a(f"  .  ambient        : {amb['density_over_ncr']:g} n_cr, theta_e = "
          f"{amb['theta_e']:g}  (fills BOTH sides -- no vacuum gap)")
    beam = (las.get("beam") or {})
    if laser_off:
        a("  x  LASER OFF      : intensity = 0 (gate-G3 control; geometrically identical "
          "to its physics run)")
    else:
        prof = str(beam.get("profile", "uniform"))
        if prof == "uniform":
            a(f"  <  laser          : uniform (plane wave), I0 = {float(las['intensity']):g} W/m^2, "
              f"enters the {'hi' if inject_hi else 'lo'} z face")
        else:
            a(f"  <  laser          : {prof}, w0 = {float(beam['waist_de']):g} d_e "
              f"(1/e radius of INTENSITY), I0 = {float(las['intensity']):g} W/m^2 peak, "
              f"enters the {'hi' if inject_hi else 'lo'} z face")
            a("                      bar length is proportional to the LOCAL intensity, so "
              "the beam is drawn to scale against x")
    if sc.B0 is not None:
        axis = {"perpendicular": "y", "perpendicular_y": "y",
                "perpendicular_x": "x"}[str(cfg["field"]["orientation"])]
        a(f"  B  field          : B0 = {sc.B0:.3g} T along {axis} "
          f"(perpendicular to z), 1/w_ci0 = {sc.wci0_inv*1e12:.3g} ps")
    a(f"  grid              : {' x '.join(str(c) for c in sc.n_cell)} cells "
      f"(x by z), dz = dx = {geo['dz_over_de']:g} d_e, dt = {sc.dt*1e15:.4g} fs, "
      f"{sc.max_step} steps = {sc.t_end*1e12:.4g} ps")
    a("```")
    return "\n".join(L)


def _inject_flash_table_scales(cfg: dict) -> None:
    """For a `flash_table` run, take the gate/scale temperatures from the table.

    `units.derive` needs one theta per species to build lambda_D, omega_pe*dt and C_S.
    A lifted initial condition has a PROFILE, not a scalar, so the table carries a
    density-weighted plume-band representative under `derived:` and it is injected here.

    Deliberately NOT copied into config.yaml: two copies of the same number is how a
    config and its initial condition drift apart, and this project has already paid for
    that once (HANDOFF.md 6, the drift_uz_de families). config.yaml says which table to
    use; the table says what is in it.
    """
    tgt = ((cfg.get("plasma") or {}).get("target") or {})
    if str(tgt.get("corona_profile", "")) != "flash_table":
        return
    if tgt.get("theta_e_init") is not None:
        return
    path = os.path.join(cfg.get("_run_dir", "."), str(tgt.get("ic_table", "ic_flash.yaml")))
    if not os.path.exists(path):
        return          # deck.py raises the actionable error; do not pre-empt it here
    with open(path) as fh:
        d = yaml.safe_load(fh) or {}
    der = d.get("derived") or {}
    for k in ("theta_e_init", "theta_i_init"):
        if der.get(k) is not None:
            tgt[k] = float(der[k])


def _corona_form(tgt):
    """The coronal ramp's functional form, as deck.py decides it.

    Kept in one place so the diagram and the deck cannot disagree: deck.py reads
    `corona_profile` with the same default.
    """
    cp = str(tgt.get("corona_profile", "gaussian"))
    if cp == "flash_table":
        return "FLASH table (lifted)"
    return "exponential" if cp == "exponential" else "Gaussian"


def geometry_diagram(cfg: dict, width: int = 66) -> str:
    """An ASCII sketch of the run's geometry, GENERATED FROM THE CONFIG.

    Generated rather than hand-drawn so it cannot drift away from what the deck actually
    builds -- the same reason the density panel in ``run_checks`` is sampled from the
    deck's own ``density_function``. Shows the propagation axis with the target slab, its
    coronal ramp, the ambient fill, the boundary condition on each face, and which face
    the laser enters through.

    In 2D (and 3D, which is drawn as its x-z plane) this is a genuine TWO-DIMENSIONAL
    map rather than an axial strip with the transverse extent noted underneath. That
    matters for a finite-spot run specifically -- the target is uniform in x while the
    BEAM is not, so a 1D sketch draws the one thing a spot run is not about and omits
    the one thing it is. The beam bar length is proportional to the local intensity, so
    the waist is visible against the box rather than only quoted.
    """
    if int(cfg["geometry"]["dims"]) > 1:
        return _geometry_diagram_2d(cfg)
    sc = units.derive(cfg)
    geo, las = cfg["geometry"], cfg["laser"]
    tgt = cfg["plasma"]["target"]
    dims = int(geo["dims"])
    de = sc.de_ref
    z_lo, z_hi = sc.domain_lo / de, sc.domain_hi / de
    span = z_hi - z_lo
    inject_hi = str(las.get("inject_side", "lo")) == "hi"
    faces = boundary_faces(cfg)
    ax_lo, ax_hi = faces[str(geo.get("normal_axis", "z"))]

    centre = float(tgt.get("center_de", 0.0))
    half = 0.5 * float(tgt["thickness_de"])
    Ln = float(tgt.get("scale_length_de", 0.0))
    face = centre + half if inject_hi else centre - half

    def col(z_de):
        return max(0, min(width - 1, int(round((z_de - z_lo) / span * (width - 1)))))

    # the bar: '#' flat top, '~' corona (out to 1e-3 n_cr), '.' ambient, ' ' vacuum
    fill = "." if not is_vacuum(cfg) else " "
    bar = [fill] * width
    reach = 0.0
    if Ln > 0 and sc.n_targ > 1e-3 * sc.n_cr:
        reach = Ln * math.sqrt(math.log(sc.n_targ / (1e-3 * sc.n_cr)))
    c0, c1 = col(centre - half), col(centre + half)
    if inject_hi:
        for c in range(c1, col(face + reach) + 1):
            bar[c] = "~"
    else:
        for c in range(col(face - reach), c0 + 1):
            bar[c] = "~"
    for c in range(c0, c1 + 1):
        bar[c] = "#"

    L = []
    a = L.append
    a("```")
    a(f"{dims}D  |  propagation axis z  |  lengths in d_e at "
      f"{sc.length_scale} density = {de*1e6:.4f} um")
    a("")
    arrow_row = [" "] * width
    # A laser-off control (gate G3) is geometrically IDENTICAL to its physics run, so the
    # drive is the only thing that can distinguish the two diagrams -- say so here, or the
    # control's README shows an incoming beam that the deck does not have.
    laser_off = float(las.get("intensity", 0.0) or 0.0) == 0.0
    lab = ("x  LASER OFF (I = 0)" if laser_off else
           ("<== laser" if inject_hi else "laser ==>"))
    if inject_hi:
        for i, ch in enumerate(lab):
            arrow_row[width - len(lab) + i] = ch
    else:
        for i, ch in enumerate(lab):
            arrow_row[i] = ch
    a("      " + "".join(arrow_row))
    a("      " + "".join(bar))
    a("      " + "^" + " " * (width - 2) + "^")
    a(f"      {ax_lo:<{max(len(ax_lo), 1)}}" + " " * max(1, width - len(ax_lo)
                                                         - len(ax_hi)) + f"{ax_hi}")
    a(f"      z = {z_lo:+.0f}" + " " * max(1, width - 16) + f"z = {z_hi:+.0f}")
    a("")
    a(f"  #  target flat top : {tgt['density_over_ncr']:g} n_cr, "
      f"{tgt['thickness_de']:g} d_e thick, centred at {centre:+g} d_e")
    if Ln > 0:
        a(f"  ~  coronal ramp   : {_corona_form(tgt)}, L_n = {Ln:g} d_e on the "
          f"LASER-FACING side (face at z = {face:+g})")
    if is_vacuum(cfg):
        a("  ' ' vacuum        : no ambient plasma")
    else:
        amb = cfg["plasma"]["ambient"]
        a(f"  .  ambient        : {amb['density_over_ncr']:g} n_cr, theta_e = "
          f"{amb['theta_e']:g}  (fills BOTH sides -- no vacuum gap)")
    if dims > 1:
        tr = geo["transverse"]
        t_lo, t_hi = faces["x"]
        a(f"  x  transverse     : {tr['lo_de']:g} .. {tr['hi_de']:g} d_e, "
          f"boundaries {t_lo}/{t_hi}")
    if sc.B0 is not None:
        axis = {"perpendicular": "y", "perpendicular_y": "y",
                "perpendicular_x": "x"}[str(cfg["field"]["orientation"])]
        a(f"  B  field          : B0 = {sc.B0:.3g} T along {axis} "
          f"(perpendicular to z), 1/w_ci0 = {sc.wci0_inv*1e12:.3g} ps")
    a(f"  grid              : {' x '.join(str(c) for c in sc.n_cell)} cells, "
      f"dz = {geo['dz_over_de']:g} d_e, dt = {sc.dt*1e15:.4g} fs, "
      f"{sc.max_step} steps = {sc.t_end*1e12:.4g} ps")
    a("```")
    return "\n".join(L)
