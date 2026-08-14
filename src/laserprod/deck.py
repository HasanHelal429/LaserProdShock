"""Generate a WarpX input deck from a LaserProdShock ``config.yaml``.

``config.yaml`` holds only the PRIMARY, physically-intuitive parameters (densities in
``n_cr``, temperatures as ``theta = kT/m_e c^2``, lengths in ``d_e,ref``, speeds as
fractions of c, intensity in W/m^2). :func:`render` maps those onto a WarpX deck whose
``my_constants`` are written *symbolically* -- ``ncr = epsilon0*m_e*omega0^2/q_e^2``,
``nt = 1.5*ncr``, ``B0 = vA*sqrt(mu0*namb*Mi)`` -- so the deck stays readable and WarpX
still records the fully-resolved values in ``warpx_used_inputs``.

The mapping is one-way (config -> deck), so the deck never has to be hand-edited:
change ``config.yaml`` and regenerate. :func:`verify` closes the loop after a run by
parsing ``warpx_used_inputs`` and confirming the numbers WarpX actually used match the
config.

DIMENSION-GENERAL BY CONSTRUCTION. Every list-valued input (``amr.n_cell``,
``geometry.prob_lo/hi``, the boundary tokens, ``num_particles_per_cell_each_dim``,
``beam_center``, ``beam_focus``) is built from :func:`laserprod.units.axis_names`, so
1D (z) and 2D (WarpX XZ) come out of one code path with the components in WarpX's
mesh-coordinate order. The propagation axis is always ``z`` and is always last.
"""

from __future__ import annotations

import math

from . import units
from .config import boundary_faces, has_background_field, is_vacuum

# --- WarpX physical-constant namespace (names as used in input decks) ---
CONSTS = {
    "m_e": units.ME, "q_e": units.QE, "clight": units.C,
    "epsilon0": units.EPS0, "mu0": units.MU0, "kb": units.KB,
    "pi": math.pi, "m_p": 1.67262192369e-27,
}
_FUNCS = {"sqrt": math.sqrt, "abs": abs, "exp": math.exp, "log": math.log,
          "sin": math.sin, "cos": math.cos, "tan": math.tan, "pow": pow}


def _num(x: float) -> str:
    """Format a number the WarpX way: integer-valued floats get a trailing dot,
    scientific notation drops the redundant ``+`` (``1e+18`` -> ``1e18``)."""
    x = float(x)
    if x == int(x) and abs(x) < 1e6:
        return f"{int(x)}."
    return repr(x).replace("e+", "e")


# Semantic boundary name -> (field_bc, particle_bc) WarpX tokens.
#
#   periodic   : wrap. Both faces must be periodic together. On the propagation axis
#                this is the KNOWN FAILURE MODE for an ablation run: WarpX forces
#                particle BCs periodic whenever field BCs are
#                (Source/Particles/ParticleBoundaries.cpp), and a free expansion has
#                a runaway ion front (0.20 c upstream) that then wraps onto the far
#                side. No vacuum gap is large enough. Deliberate control runs only.
#   reflecting : pec fields + specular particles. A wall, not an outlet.
#   open       : particles LEAVE (absorbing) while fields use pec. pec rather than
#                Silver-Mueller because the projection B-divergence cleaner -- active
#                whenever an external B is set -- accepts only periodic/pec/pmc/
#                neumann, and pmc/neumann would zero the tangential B0. So pec is the
#                one div-safe choice that preserves a uniform applied B0.
#   absorbing  : true EM outflow (Silver-Mueller + particles leave). NOT compatible
#                with the B-divergence cleaner, so B0 = 0 runs only.
_BC_MAP = {
    "periodic":   ("periodic", "periodic"),
    "reflecting": ("pec", "reflecting"),
    "open":       ("pec", "absorbing"),
    "absorbing":  ("absorbing_silver_mueller", "absorbing"),
}

# Perpendicular geometry: B0 must be transverse to the propagation axis z. In 2D XZ
# the OUT-OF-PLANE direction is y, which is the standard choice for a 2D perpendicular
# shock (it leaves the in-plane x-z dynamics free), and it matches the known-good
# run_laser_shock decks. 'perpendicular_x' puts B0 in-plane instead.
_FIELD_AXIS = {"perpendicular": "y", "perpendicular_y": "y", "perpendicular_x": "x"}


def _bc_tokens(cfg: dict):
    """((field...), (particle...)) WarpX boundary tokens in mesh-coordinate order."""
    faces = boundary_faces(cfg)
    names = units.axis_names(int(cfg["geometry"]["dims"]))
    flo, fhi, plo, phi = [], [], [], []
    for ax in names:
        lo_name, hi_name = faces[ax]
        f0, p0 = _BC_MAP[lo_name]
        f1, p1 = _BC_MAP[hi_name]
        flo.append(f0); fhi.append(f1); plo.append(p0); phi.append(p1)
    return (flo, fhi), (plo, phi)


def _species_table(cfg: dict) -> dict:
    """``{name: {kind, role, charge_state}}``, derived from the plasma blocks.

    Auto-generated rather than hand-listed in the config: the species set is fully
    determined by which plasma populations exist (a vacuum run simply has no ambient),
    so listing them by hand only creates an opportunity to disagree with the density
    functions. ``species_extra`` in the config can add per-species overrides.
    """
    Z = int(cfg["reference"].get("charge_state", 1))
    # A hybrid run's electrons are a FLUID: there are no electron macroparticles at all,
    # and emitting some would both cost the compute the hybrid exists to save and
    # double-count the charge the Ohm's-law solver already carries.
    hybrid = str((cfg.get("solver") or {}).get("type", "em")) == "hybrid"
    tab = {}
    if not hybrid:
        tab["targ_electrons"] = {"kind": "electron", "role": "target"}
    tab["targ_ions"] = {"kind": "ion", "role": "target", "charge_state": Z}
    if not is_vacuum(cfg):
        if not hybrid:
            tab["amb_electrons"] = {"kind": "electron", "role": "ambient"}
        tab["amb_ions"] = {"kind": "ion", "role": "ambient", "charge_state": Z}
    for name, over in (cfg.get("species_extra") or {}).items():
        tab.setdefault(name, {}).update(over)
    return tab


def _face_expr(cfg: dict) -> str:
    """The target's laser-facing face position as a WarpX expression.

    ``zt`` for a planar target; for ``shape: curved`` the face is displaced with the
    transverse coordinate, ``zt -/+ x^2/(2 Rc)``, so the plume is focused (Rc > 0) or
    defocused (Rc < 0). Requires a transverse dimension.
    """
    tgt = cfg["plasma"]["target"]
    if str(tgt.get("shape", "planar")) != "curved":
        return "zt"
    sign = "-" if str(cfg["laser"].get("inject_side", "lo")) == "hi" else "+"
    return f"(zt {sign} x^2/(2.*Rc))"


def _density_exprs(cfg: dict) -> tuple[str, str | None]:
    """(target_density_expr, ambient_density_expr) as WarpX parser strings.

    The target is a flat top of thickness ``wt`` behind its laser-facing face, plus a
    Gaussian corona of scale length ``Ln`` on the laser side (Gaussian, matching the
    known-good decks -- the corona is where most of the absorption happens, so its
    functional form is a physics choice, not a detail). The ambient fills everything
    the flat top does not.

    Both are written in terms of the face expression, so the laser always sees the
    corona first regardless of ``inject_side``.
    """
    tgt = cfg["plasma"]["target"]
    zf = _face_expr(cfg)
    hi = str(cfg["laser"].get("inject_side", "lo")) == "hi"
    Ln = float(tgt.get("scale_length_de", 0.0))

    if hi:   # laser from +z travelling -z: slab is [face - wt, face], corona at z > face
        slab = f"(z<={zf})*(z>={zf}-wt)"
        corona = f" + (z>{zf})*exp(-((z-{zf})/Ln)^2)" if Ln > 0 else ""
        outside = f"((z>{zf})+(z<{zf}-wt))"
    else:    # laser from -z travelling +z: slab is [face, face + wt], corona at z < face
        slab = f"(z>={zf})*(z<={zf}+wt)"
        corona = f" + (z<{zf})*exp(-((z-{zf})/Ln)^2)" if Ln > 0 else ""
        outside = f"((z<{zf})+(z>{zf}+wt))"

    t_expr = f"nt*({slab}{corona})"
    if str(tgt.get("shape", "planar")) == "finite_width":
        t_expr = f"({t_expr})*(abs(x)<=0.5*targw)"
    a_expr = f"namb*{outside}" if not is_vacuum(cfg) else None
    return t_expr, a_expr


def _theta_expr(role: str, kind: str) -> str:
    """my_constants expression for a species' initial thermal u_std^2 (= theta)."""
    if role == "target":
        return "th_t" if kind == "electron" else "th_ti"
    return "th_a" if kind == "electron" else "th_ai"


def _ppc_str(cfg: dict, role: str) -> str:
    """``num_particles_per_cell_each_dim``: one entry per dimension."""
    ppc = cfg["numerics"]["ppc"]
    n = int(ppc["target" if role == "target" else "ambient"])
    dims = int(cfg["geometry"]["dims"])
    if dims == 1:
        return str(n)
    # In multi-D the input is per-dimension, so a request of N ppc becomes the integer
    # per-dim count whose product is closest to N without exceeding it.
    per = max(1, int(round(n ** (1.0 / dims))))
    return " ".join([str(per)] * dims)


def _diag_intervals(cfg: dict):
    d = cfg.get("diagnostics", {}) or {}
    max_step = int(cfg["numerics"]["max_step"])
    plot = int(d.get("plotfile_intervals", max(1, round(max_step / 10))))
    red = int(d.get("reduced_intervals", max(1, round(max_step / 250))))
    fields = d.get("field_intervals")
    phase = d.get("phase_intervals")
    return (plot, red,
            int(fields) if fields else None,
            int(phase) if phase else None)


# --------------------------------------------------------------------------- #
# forward direction: config -> deck
# --------------------------------------------------------------------------- #
def render(cfg: dict) -> str:
    """Build a WarpX input deck (as a string) from a loaded config."""
    las, ref = cfg["laser"], cfg["reference"]
    tgt = cfg["plasma"]["target"]
    amb = (cfg["plasma"].get("ambient") or None)
    geo, num, meta = cfg["geometry"], cfg["numerics"], cfg.get("meta", {})
    sc = units.derive(cfg)
    dims = int(geo["dims"])
    ax_names = units.axis_names(dims)
    n_cell, lo, hi, dz, dx = units.cells_and_extent(geo, sc.de_ref)
    (flo, fhi), (plo_bc, phi_bc) = _bc_tokens(cfg)
    plot_int, red_int, field_int, phase_int = _diag_intervals(cfg)
    species = _species_table(cfg)
    t_expr, a_expr = _density_exprs(cfg)
    inject_hi = str(las.get("inject_side", "lo")) == "hi"

    L: list[str] = []
    a = L.append

    # --- header ----------------------------------------------------------
    a("# " + "=" * 74)
    a(f"# LaserProdShock / {meta.get('run_id', '?')} -- GENERATED from config.yaml by")
    a("# scripts/make_inputs.py. DO NOT EDIT THIS FILE: edit config.yaml and")
    a("# regenerate (the config is the single source of truth).")
    a("#")
    if meta.get("description"):
        for line in _wrap(" ".join(str(meta["description"]).split()), 72):
            a(f"# {line}")
    a("#")
    a(f"# Derived scales ({dims}D, lengths in d_e,{sc.length_scale} "
      f"= {sc.de_ref*1e6:.4f} um):")
    a(f"#   n_cr = {sc.n_cr:.4g} m^-3   d_e,cr = lam0/2pi = {sc.de_cr*1e6:.4f} um")
    a(f"#   target {sc.n_targ_over_ncr:.3g} n_cr (d_e = {sc.de_targ*1e6:.4f} um)"
      + (f"   ambient {sc.n_amb_over_ncr:.4g} n_cr (d_e = {sc.de_amb*1e6:.4f} um, "
         f"d_i = {sc.di_amb*1e6:.3f} um)" if amb else "   ambient: VACUUM"))
    a(f"#   dt = {sc.dt*1e15:.4f} fs   t_end = {sc.t_end*1e12:.4f} ps   "
      f"n_cell = {' x '.join(str(c) for c in n_cell)}")
    a(f"#   GATE G1 omega_pe*dt: {sc.wpe_dt_targ:.3f} initial, "
      f"{sc.wpe_dt_peak:.3f} at compression; hits 2 at "
      f"{sc.n_over_ncr_at_wpe_dt_2:.2f} n_cr")
    a(f"#   GATE G2 dz/lambda_D: target(cold) {sc.dz_over_lD_targ:.0f}"
      + (f", ambient {sc.dz_over_lD_amb:.1f}" if sc.dz_over_lD_amb else ""))
    a(f"#   predicted absorption: tau(flat top) = {sc.tau_est:.3g}, "
      f"f_abs ~ {sc.f_abs_est:.3f}"
      + (f"; ambient traverse eats {sc.f_abs_amb*100:.3f}%" if amb else ""))
    if sc.B0 is not None:
        a(f"#   B0 = {sc.B0:.4g} T   1/wci0 = {sc.wci0_inv*1e12:.4f} ps   "
          f"rho_i0 = {sc.rho_i0/sc.de_ref:.1f} d_e   "
          f"M_A = {sc.MA:.2f}  M_ms = {sc.Mms:.2f}  "
          f"({sc.n_gyroperiods:.2f} gyroperiods)")
    a("# " + "=" * 74)
    a("")

    # --- my_constants (symbolic; order respects dependencies) ------------
    a("# --- laser / reference (the laser PINS the absolute density scale: IB")
    a("#     absorption is measured against n_cr, so lam0 fixes densities in m^-3) ---")
    a(f"my_constants.lam0   = {_num(sc.lam0)}")
    a("my_constants.omega0 = 2.*pi*clight/lam0")
    a("my_constants.ncr    = epsilon0*m_e*omega0*omega0/(q_e*q_e)")
    a(f"my_constants.mass_ratio = {_num(sc.mass_ratio)}")
    a("my_constants.Mi     = mass_ratio*m_e")
    a("")
    a("# --- densities (in n_cr) and the reference skin depth ---")
    a(f"my_constants.nt     = {_num(tgt['density_over_ncr'])}*ncr")
    if amb:
        a(f"my_constants.namb   = {_num(amb['density_over_ncr'])}*ncr")
    a(f"my_constants.wpe    = sqrt({_nref_name(cfg)}*q_e^2/(epsilon0*m_e))")
    a(f"my_constants.de     = clight/wpe          # d_e,{sc.length_scale} "
      f"= {sc.de_ref*1e6:.4f} um")
    a("my_constants.di     = de*sqrt(mass_ratio)")
    a("")
    a("# --- target geometry (zt = the LASER-FACING face) ---")
    a(f"my_constants.zt     = {_num(_face_center(cfg, sc))}*de")
    a(f"my_constants.wt     = {_num(tgt['thickness_de'])}*de")
    if float(tgt.get("scale_length_de", 0.0)) > 0:
        a(f"my_constants.Ln     = {_num(tgt['scale_length_de'])}*de")
    if str(tgt.get("shape", "planar")) == "finite_width":
        a(f"my_constants.targw  = {_num(tgt['width_de'])}*de")
    if str(tgt.get("shape", "planar")) == "curved":
        a(f"my_constants.Rc     = {_num(tgt['curvature_radius_de'])}*de")
    a("")
    a("# --- temperatures (theta = kT/(m_e c^2)) ---")
    a(f"my_constants.th_t   = {_num(tgt['theta_e_init'])}"
      f"        # target electrons: {sc.theta_e_targ*units.ME_C2_EV:.4g} eV")
    a(f"my_constants.th_ti  = {_num(tgt.get('theta_i_init', float(tgt['theta_e_init']) / sc.mass_ratio))}")
    if amb:
        a(f"my_constants.th_a   = {_num(amb['theta_e'])}")
        a(f"my_constants.th_ai  = {_num(amb.get('theta_i', float(amb['theta_e']) / sc.mass_ratio))}")
    a("")
    if sc.B0 is not None:
        a("# --- background field (perpendicular: B0 transverse to the z propagation")
        a(f"#     axis, along {_FIELD_AXIS[str(cfg['field']['orientation'])]}) ---")
        a(f"my_constants.vA     = {_num(cfg['field']['vA_over_c'])}*clight")
        a("my_constants.B0     = vA*sqrt(mu0*namb*Mi)"
          f"      # {sc.B0:.4g} T")
        a("")

    # --- domain constants ------------------------------------------------
    a("# --- domain ---")
    # Taken straight from the config (not lo[]/de_ref) so the deck carries the exact
    # number the author wrote, with no float round-trip through metres.
    normal = str(geo.get("normal_axis", "z"))
    for name in ax_names:
        blk = geo["axis"] if name == normal else geo["transverse"]
        a(f"my_constants.{name}lo = {_num(blk['lo_de'])}*de")
        a(f"my_constants.{name}hi = {_num(blk['hi_de'])}*de")
    a("")

    # --- time / solver ---------------------------------------------------
    a("# --- time / solver ---")
    a("#")
    a("# THE BINDING STABILITY CONDITION IS omega_pe*dt < 2, AND THE GRID CFL CANNOT")
    a("# SEE IT. The grid CFL is set by dz/c and knows nothing about how dense the")
    a("# plasma is. Upstream, cfl = 0.75 gave omega_pe*dt = 1.91 in a 1.5 n_cr target,")
    a("# which then COMPRESSED under its own ablation to 2.43 -- total particle energy")
    a("# grew 21x while the laser had supplied 1/1400 of it, and every number measured")
    a("# past t ~ 0.1 gyroperiods was a measurement of that instability.")
    a(f"#   here: omega_pe*dt = {sc.wpe_dt_targ:.3f} initially, "
      f"{sc.wpe_dt_peak:.3f} at the assumed compression,")
    a(f"#   and the limit of 2 is not touched until {sc.n_over_ncr_at_wpe_dt_2:.2f} n_cr.")
    a(f"max_step      = {int(num['max_step'])}")
    # The hybrid-PIC solver REQUIRES a fixed step: WarpX aborts with
    # "warpx.const_dt must be specified with the hybrid-PIC solver". There is no electron
    # macroparticle CFL for it to derive one from, so the step is a physics choice (the
    # ion CFL and the T_e advection CFL, which WarpX checks and aborts on) rather than
    # something the grid hands you.
    cdt = num.get("const_dt_de_over_c")
    if cdt is not None:
        a(f"warpx.const_dt = {_num(float(cdt) * sc.de_ref / units.C)}"
          f"   # {float(cdt):g} d_e/c")
    a(f"warpx.cfl     = {_num(num['cfl'])}")
    a("warpx.verbose = 1          # REQUIRED: the LASERDEP diagnostic lines")
    a("")

    # --- grid ------------------------------------------------------------
    a(f"# --- grid (dz = {geo['dz_over_de']} d_e"
      + (f", dx = {geo.get('dx_over_dz', 1.0)} dz" if dims > 1 else "")
      + "; z = propagation axis) ---")
    a(f"amr.n_cell        = {' '.join(str(c) for c in n_cell)}")
    a("amr.max_level     = 0      # the operator asserts finestLevel() == 0 (no AMR)")
    # Grid decomposition. Only emitted when the config asks, because AMReX's default
    # is what every single-rank run here used and writing a line unconditionally would
    # rewrite completed decks for a no-op.
    #
    # This exists for MULTI-RANK runs. AMReX's DistributionMapping balances CELLS, and
    # in an ablation deck the plasma occupies a small slab at one end of a long vacuum
    # domain -- so a decomposition that splits the PROPAGATION axis hands one rank
    # nearly all the macroparticles and the other rank vacuum. Splitting the TRANSVERSE
    # axis instead is exactly balanced whenever the target is uniform in x, which a
    # planar slab is, and needs no load-balancing machinery to stay that way.
    #
    # NAMING TRAP: `amr.max_grid_size` is per-LEVEL (one scalar applied to every
    # dimension), NOT per-dimension. Per-dimension needs the suffixed names, and those
    # are AMReX's dimension indices, not WarpX's axis letters -- in 2D XZ,
    # `max_grid_size_y` is dimension 1, which is **z**. Verified in
    # AMReX_AmrMesh.cpp (max_grid_size_z is compiled out below 3D).
    mgs = num.get("max_grid_size")
    if mgs is not None:
        if isinstance(mgs, (list, tuple)):
            if len(mgs) != dims:
                raise ValueError(
                    f"numerics.max_grid_size has {len(mgs)} entries for a {dims}D run; "
                    f"give one per axis in mesh order {units.axis_names(dims)}, or a "
                    f"single number to apply to every axis")
            suffix = ("x", "y", "z")
            for i, v in enumerate(mgs):
                ax = units.axis_names(dims)[i]
                note = ("  # this is the PROPAGATION axis"
                        if ax == str(geo.get("normal_axis", "z")) else
                        "  # transverse: split here to balance particles")
                a(f"amr.max_grid_size_{suffix[i]} = {int(v)}{note}")
        else:
            a(f"amr.max_grid_size = {int(mgs)}")
    a(f"geometry.dims     = {dims}")
    a(f"geometry.prob_lo  = {' '.join(f'{n}lo' for n in ax_names)}")
    a(f"geometry.prob_hi  = {' '.join(f'{n}hi' for n in ax_names)}")
    a("")
    faces = boundary_faces(cfg)
    a("# boundaries: " + ", ".join(f"{ax} {faces[ax][0]}/{faces[ax][1]}"
                                   for ax in ax_names))
    if "periodic" in faces[str(geo.get("normal_axis", "z"))]:
        a("#   NOTE the propagation axis is PERIODIC: WarpX ties particle BCs to field")
        a("#   BCs, so a runaway ablation front will WRAP onto the far side. Control")
        a("#   runs only (meta.expect_wrap).")
    a(f"boundary.field_lo    = {' '.join(flo)}")
    a(f"boundary.field_hi    = {' '.join(fhi)}")
    a(f"boundary.particle_lo = {' '.join(plo_bc)}")
    a(f"boundary.particle_hi = {' '.join(phi_bc)}")
    a("")
    # --- Coulomb collisions -----------------------------------------------
    # Load-bearing for the Phase-4 benchmark: Lezhnin 2025 reports that turning off
    # EITHER collisions or laser heating gives "drastically different plasma evolution".
    col = cfg.get("collisions") or {}
    if col.get("enabled"):
        names, blocks = [], []
        for pr in col["pairs"]:
            a_s, b_s = str(pr[0]), str(pr[1])
            # WarpX wants exactly TWO names always; intra-species is expressed by naming
            # the same species twice, and BinaryCollision infers it via
            # `m_isSameSpecies = (names[0] == names[1])`. The documentation says "provide
            # only one name for intra-species collisions", which this version aborts on:
            # "Binary collision <name> must have exactly two species."
            spec = f"{a_s} {b_s}"
            nm = f"c_{a_s}_{b_s}" if a_s != b_s else f"c_{a_s}"
            names.append(nm)
            blocks.append((nm, spec))
        a("")
        a("# --- Coulomb collisions ----------------------------------------------")
        a(f"collisions.collision_names = {' '.join(names)}")
        for nm, spec in blocks:
            a(f"{nm}.type    = pairwisecoulomb")
            a(f"{nm}.species = {spec}")
            if col.get("coulomb_log") is not None:
                # One global lnLambda, matching the paper's own simplification. Note the
                # laser operator can evaluate lnLambda PER CELL; the paper flags the
                # global value as a source of its FLASH<->PSC heat-flux discrepancy, so
                # the two settings are recorded separately rather than silently unified.
                a(f"{nm}.CoulombLog = {_num(col['coulomb_log'])}")
            if col.get("intervals") is not None:
                a(f"{nm}.ndt_supercycle = {int(col['intervals'])}")
        a("")

    solver = (cfg.get("solver") or {})
    if str(solver.get("type", "em")) == "hybrid":
        hyb = solver.get("hybrid") or {}
        a("")
        a("# --- hybrid (Ohm's law) field solver ---------------------------------")
        a("# Kinetic ions, fluid electrons. There are no electron macroparticles, which is")
        a("# why the omega_pe and Debye gates report n/a for this run.")
        a("algo.maxwell_solver = hybrid")
        ee = str(hyb.get("electron_energy_mode", "none"))
        a(f"hybrid_pic_model.electron_energy_mode = {ee}")
        if ee == "advected":
            # eps = (3/2) n kB Te fixes gamma = 5/3; WarpX aborts on a conflicting gamma,
            # and config.validate() refuses one, so none is emitted here by construction.
            a(f"hybrid_pic_model.electron_temp_init = "
              f"{str(hyb.get('electron_temp_init', 'polytropic'))}")
        if hyb.get("elec_temp") is not None:
            a(f"hybrid_pic_model.elec_temp = {_num(hyb['elec_temp'])}")
        if hyb.get("n0_ref_over_ncr") is not None:
            a(f"hybrid_pic_model.n0_ref = {_num(float(hyb['n0_ref_over_ncr']) * sc.n_cr)}")
        if hyb.get("plasma_resistivity") is not None:
            a(f"hybrid_pic_model.plasma_resistivity(rho,J,t) = "
              f"{_num(hyb['plasma_resistivity'])}")
        if hyb.get("plasma_hyper_resistivity") is not None:
            a(f"hybrid_pic_model.plasma_hyper_resistivity(rho,B) = "
              f"{_num(hyb['plasma_hyper_resistivity'])}")
        if hyb.get("n_floor_over_ncr") is not None:
            a(f"hybrid_pic_model.n_floor = {_num(float(hyb['n_floor_over_ncr']) * sc.n_cr)}")
        if hyb.get("substeps") is not None:
            a(f"hybrid_pic_model.substeps = {int(hyb['substeps'])}")
        # The two bounded alternatives to aborting on the electron-energy advection CFL.
        # Both change what the solver DOES, so both belong in --verify: a stale binary that
        # silently ignored one would run the unbounded scheme while the deck claimed
        # otherwise, which is how `refraction = 0` was lost for 2000 steps (CLAUDE.md).
        if hyb.get("ue_cfl_max") is not None:
            a(f"hybrid_pic_model.ue_cfl_max = {_num(hyb['ue_cfl_max'])}")
        if hyb.get("n_trust_over_ncr") is not None:
            a(f"hybrid_pic_model.n_trust = "
              f"{_num(float(hyb['n_trust_over_ncr']) * sc.n_cr)}")
        a("")
    a(f"algo.particle_shape = {int(num.get('particle_shape', 2))}")
    if num.get("random_seed") is not None:
        # Fixing the seed makes a run bit-reproducible AND lets a seed sweep measure the
        # PIC noise floor on any derived quantity -- necessary before attributing a small
        # difference between two runs to physics.
        a(f"warpx.random_seed  = {int(num['random_seed'])}")
    if num.get("filter_npass"):
        a("warpx.use_filter    = 1")
        a(f"warpx.filter_npass_each_dir = {num['filter_npass']}")
    a("")

    # --- background field ------------------------------------------------
    orient = str((cfg.get("field") or {}).get("orientation", "none"))
    a(f"# --- background field ({orient}) ---")
    fax = _FIELD_AXIS.get(orient)
    for comp in ("x", "y", "z"):
        val = "B0" if (sc.B0 is not None and comp == fax) else "0."
        a(f'warpx.B{comp}_external_grid_function(x,y,z) = "{val}"')
    a("warpx.B_ext_grid_init_style       = parse_B_ext_grid_function")
    a("")

    # --- species ---------------------------------------------------------
    a(f"particles.species_names = {' '.join(species)}")
    a("")
    for name, spec in species.items():
        kind, role = spec["kind"], spec["role"]
        dens = t_expr if role == "target" else a_expr
        theta = _theta_expr(role, kind)
        floor = "namb" if amb else "nt"
        a(f"# --- {role} {kind}s ---")
        if kind == "electron":
            a(f"{name}.species_type = electron")
        else:
            Z = int(spec.get("charge_state", 1))
            a(f"{name}.charge = {'' if Z == 1 else f'{Z}*'}q_e")
            a(f"{name}.mass   = Mi")
        a(f'{name}.injection_style = "NUniformPerCell"')
        a(f"{name}.num_particles_per_cell_each_dim = {_ppc_str(cfg, role)}")
        a(f"{name}.profile = parse_density_function")
        # The density expressions are ELECTRON densities -- `plasma.*.density_over_ncr` is
        # quoted in n_cr, and n_cr is defined on the electrons. An ion carrying charge Z e
        # therefore needs n_i = n_e / Z for the plasma to be neutral. Emitting the SAME
        # number density for both is only correct at Z = 1, and silently gives a net charge
        # of (Z - 1) e n_e otherwise -- 12x e n_e at the Z = 13 of the Phase-4 aluminium
        # runs. In a hybrid deck, which has no electron species at all, the same slip makes
        # n_e = rho/e = Z n_i come out Z times too LARGE. Both were live bugs found by
        # reading a movie of P4_lez_hyb (RESULTS 2026-08-12).
        ion_dens = dens if int(spec.get("charge_state", 1)) == 1 else \
            f"({dens})/{int(spec.get('charge_state', 1))}"
        a(f'{name}.density_function(x,y,z) = "{dens if kind == "electron" else ion_dens}"')
        a(f"{name}.density_min = 1.e-4*{floor}")
        a(f"{name}.momentum_distribution_type = maxwellian")
        a(f'{name}.maxwellian_u_std_distribution_type = "constant"')
        for comp in ("ux_std", "uy_std", "uz_std"):
            a(f"{name}.{comp} = sqrt({theta})")
        a("")

    # --- the laser -------------------------------------------------------
    heated = [n for n, s in species.items() if s["kind"] == "electron"]
    beam = las.get("beam") or {}
    a("# " + "-" * 72)
    a("# --- LASER DEPOSITION (ray tracing) -- the operator under test ---")
    a("#")
    a("# K ~ Z_eff lnLambda n_e^2 T_e^{-3/2} / sqrt(1 - n_e/n_cr), so absorption is")
    a("# SELF-LIMITING: a cold target absorbs strongly and shuts itself off as the")
    a("# corona heats and rarefies. That is real laser-plasma coupling, and it is only")
    a("# captured because temperature_mode = local measures T_e per cell.")
    a("#")
    a("# Z_eff/lnLambda are a VERY STRONG knob: upstream, 5/5 -> 13/7 coupled 16x more")
    a("# energy and produced a 0.06 c piston that crossed the domain in a fraction of a")
    a("# gyroperiod. Change them in small steps.")
    a("# " + "-" * 72)
    # The operator ABORTS if `species` is present while density_source = hybrid_rho and
    # deposit_to = electron_fluid: nothing would read it, and a stale list is how a deck
    # comes to claim it heats something it does not. So omit the key, do not empty it.
    if heated:
        a(f"laser_deposition.species              = {' '.join(heated)}")
    a(f"laser_deposition.wavelength           = lam0")
    a(f"laser_deposition.intensity            = {_num(las['intensity'])}")
    a(f"laser_deposition.direction            = {str(las.get('direction', 'z'))}")
    a(f"laser_deposition.inject_side          = {'hi' if inject_hi else 'lo'}")
    ang = float(las.get("incidence_angle_deg", 0.0))
    a(f"laser_deposition.incidence_angle      = {_num(math.radians(ang))}"
      f"        # {ang:g} deg")
    a(f"laser_deposition.Z_eff                = {_num(las.get('Z_eff', 1.0))}")
    a(f"laser_deposition.coulomb_log          = {_num(las.get('coulomb_log', 2.0))}")
    # lnLambda: 'constant' uses the value above; 'nrl'/'flash'/'ib' evaluate it per cell
    # from the local (n_e, T_e) and IGNORE it -- which multiplies K by a factor of a few
    # (2 vs the ~7 a keV corona actually has is 3.6x in absorption), so the deck must say
    # so on its face. Emitted only when the config asks, like the ray-march knobs below:
    # the operator's default is `constant` and bit-identical to having no such option, so
    # writing the line unconditionally would rewrite every already-completed run's deck
    # for a no-op.
    if las.get("coulomb_log_mode") is not None:
        a(f"laser_deposition.coulomb_log_mode     = "
          f"{str(las['coulomb_log_mode'])}")
    a(f"laser_deposition.electron_temperature = th_t")
    a(f"laser_deposition.temperature_mode     = {str(las.get('temperature_mode', 'local'))}")
    # The three hybrid swaps. A hybrid run has no electron macroparticles, so the operator
    # cannot form a CIC electron density or a per-cell kinetic temperature -- it reads the
    # fluid's instead, and deposits into the fluid's energy equation rather than kicking
    # particles. config.validate() enforces that these three move together.
    if str(las.get("density_source", "species")) != "species":
        a(f"laser_deposition.density_source       = "
          f"{str(las['density_source'])}")
    if str(las.get("deposit_to", "particles")) != "particles":
        a(f"laser_deposition.deposit_to           = {str(las['deposit_to'])}")
    if las.get("temperature_floor_theta") is not None:
        a(f"laser_deposition.temperature_floor    = "
          f"{_num(las['temperature_floor_theta'])}")
    if las.get("min_macroparticles_per_cell") is not None:
        a(f"laser_deposition.min_macroparticles_per_cell = "
          f"{_num(las['min_macroparticles_per_cell'])}")
    # refraction = 0 marches every ray STRAIGHT down the axis and carries the
    # refraction analytically through the Snell invariant (n_m = n_cr cos^2 theta0).
    # It is EXACT for a plane-stratified target at any angle and 3.2x cheaper on the
    # march -- but it is blind to transverse structure the plasma itself creates: on a
    # 12.5 % corrugated front it read +8.5 % high and collapsed the transverse contrast
    # of P_abs from 4.086 to 0.089. A Gaussian beam's own profile survives untouched
    # (each column still gets its own incident intensity); what is lost is rays bending
    # INTO or OUT OF a feature such as an ablation crater. Emitted only when the config
    # asks, because the operator's default is 1 and writing the line unconditionally
    # would rewrite every completed run's deck for a no-op.
    if las.get("refraction") is not None:
        a(f"laser_deposition.refraction           = "
          f"{1 if las['refraction'] else 0}")
    a(f"laser_deposition.ray_cfl              = {_num(las.get('ray_cfl', 0.25))}")
    # intervals: an IntervalsParser, so 'start:stop:period' expresses a FINITE PULSE
    a(f"laser_deposition.intervals            = {str(las.get('intervals', 1))}")
    # Ray-march performance (Phase 1.5). `ray_threads` is separate from
    # OMP_NUM_THREADS on purpose: a GPU run keeps the push on the device with one
    # host thread, but the march is host code. `n_accumulators` fixes the
    # summation order, so two runs are only comparable bit for bit at the same
    # value -- which is why it is written into the deck rather than left default.
    if las.get("ray_threads") is not None:
        a(f"laser_deposition.ray_threads          = {int(las['ray_threads'])}")
    if las.get("n_accumulators") is not None:
        a(f"laser_deposition.n_accumulators       = {int(las['n_accumulators'])}")
    if las.get("vacuum_skip") is not None:
        a(f"laser_deposition.vacuum_skip          = "
          f"{1 if las['vacuum_skip'] else 0}")
    if dims > 1:
        prof = str(beam.get("profile", "uniform"))
        if prof != "uniform":
            a(f"laser_deposition.beam_profile         = {prof}")
            a(f"laser_deposition.beam_waist           = "
              f"{_num(float(beam['waist_de']))}*de")
            if beam.get("order") is not None:
                a(f"laser_deposition.beam_order           = {_num(beam['order'])}")
            if beam.get("center_de") is not None:
                a(f"laser_deposition.beam_center          = "
                  f"{' '.join(f'{_num(v)}*de' for v in _as_list(beam['center_de']))}")
        if int(beam.get("rays_per_cell", 1)) != 1:
            a(f"laser_deposition.rays_per_cell        = "
              f"{int(beam['rays_per_cell'])}")
        if beam.get("focus_de") is not None:
            a(f"laser_deposition.beam_focus           = "
              f"{' '.join(f'{_num(v)}*de' for v in beam['focus_de'])}")
    if las.get("profile_intervals") is not None:
        a("# per-cell (coords, n_e, H, P_abs) dump. ANALYSE THE STEP-0 TABLE: later")
        a("# dumps drift as the kicks move electrons.")
        a(f"laser_deposition.profile_intervals    = {str(las['profile_intervals'])}")
        a("laser_deposition.profile_prefix       = diags/laserdep_profile")
    if las.get("ray_intervals") is not None:
        a("# ray PATH dump -- the trajectories, not their footprint. Read with")
        a("# scripts/plot_rays.py --dump. A full dump is (transverse cells x")
        a("# rays_per_cell) x (path/(ray_cfl dz)) rows PER APPLICATION (~6e5 for a 2D")
        a("# P1 deck), so thin it with ray_stride / ray_step_stride, and note that")
        a("# `intervals = 0` is the only thing that disables a diagnostic.")
        a(f"laser_deposition.ray_intervals        = {str(las['ray_intervals'])}")
        a("laser_deposition.ray_prefix           = diags/laserdep_rays")
        a(f"laser_deposition.ray_stride           = "
          f"{int(las.get('ray_stride', 1))}")
        a(f"laser_deposition.ray_step_stride      = "
          f"{int(las.get('ray_step_stride', 1))}")
    a("")

    # --- diagnostics -----------------------------------------------------
    a("# --- diagnostics ---")
    a("# EP/FE close gate G6: the tracer's own LASERDEP Eabs is immune to grid heating,")
    a("# the particle energy is not, so their difference IS the grid-heating budget.")
    a("warpx.reduced_diags_names = EP FE PN")
    for nm, typ in (("EP", "ParticleEnergy"), ("FE", "FieldEnergy"),
                    ("PN", "ParticleNumber")):
        a(f"{nm}.type      = {typ}")
        a(f"{nm}.intervals = {red_int}")
    a("")
    diags = ["diag1"] + (["diag_fields"] if field_int else []) \
                      + (["diag_phase"] if phase_int else [])
    a(f"diagnostics.diags_names = {' '.join(diags)}")
    a("")
    a(f"# diag1: fields + all particles (~{int(num['max_step'])//plot_int} frames)")
    a(f"diag1.intervals = {plot_int}")
    a("diag1.diag_type = Full")
    if field_int:
        fvars = ["Ez", "Ex", "By", "Bx", "jz", "rho"] if dims > 1 else \
                ["Ez", "Ey", "By", "Bx", "jz", "rho"]
        fvars += [f"rho_{sp}" for sp in species]
        # A hybrid run's DEFINING quantity is the electron fluid temperature, and it was
        # not being dumped at all: the Phase-4 diagnosis of the density spike at the
        # critical surface had to recover T_e from the laser operator's own
        # `laserdep_profile` text dumps, which are written on a different cadence and only
        # where the ray reached. `Te` (eV) and `Pe` (Pa) are already exposed by
        # FullDiagnostics; they simply have to be asked for.
        if str((cfg.get("solver") or {}).get("type", "em")) == "hybrid":
            fvars += ["Te", "Pe"]
        a("")
        a(f"# diag_fields: field-only, high cadence "
          f"(~{int(num['max_step'])//field_int} frames) for streaks. Cheap: no particles.")
        a(f"diag_fields.intervals     = {field_int}")
        a("diag_fields.diag_type     = Full")
        a("diag_fields.write_species = 0")
        a(f"diag_fields.fields_to_plot = {' '.join(fvars)}")
    if phase_int:
        ions = [n for n, s in species.items() if s["kind"] == "ion"]
        frac = float((cfg.get("diagnostics") or {}).get("phase_random_fraction", 0.05))
        a("")
        a("# diag_phase: particles only, subsampled -- PHASE SPACE IS THE ARBITER of a")
        a("# shock claim (density/B streaks of a decaying magnetosonic pulse look")
        a("# shock-like; only phase space shows whether ions are reflected).")
        a(f"diag_phase.intervals     = {phase_int}")
        a("diag_phase.diag_type     = Full")
        a("diag_phase.fields_to_plot = none")
        a(f"diag_phase.species       = {' '.join(ions)}")
        for sp in ions:
            a(f"diag_phase.{sp}.random_fraction = {_num(frac)}")
    a("")
    return "\n".join(L)


def sample_density(cfg: dict, role: str, z, x=0.0) -> list:
    """Evaluate the deck's own density expression for ``role`` at positions ``z``.

    Generated figures then show *exactly* what WarpX will inject, because the number
    plotted comes from the same parser string the deck contains — a diagnostic cannot
    drift away from the deck by re-deriving the profile independently. Returns
    densities in m^-3 (0.0 where the expression is undefined).
    """
    t_expr, a_expr = _density_exprs(cfg)
    expr = t_expr if role == "target" else a_expr
    if expr is None:
        return [0.0 for _ in z]
    ns = {**CONSTS, **resolve_constants(parse_inputs_str(render(cfg)))}
    out = []
    for zi in z:
        try:
            out.append(_eval(expr, {**ns, "x": x, "y": 0.0, "z": zi}))
        except Exception:
            out.append(0.0)
    return out


def parse_inputs_str(text: str) -> dict:
    """Same as :func:`parse_inputs`, for a deck already in memory."""
    d = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, val = line.split("=", 1)
        d[key.strip()] = val.strip()
    return d


def _wrap(text: str, width: int) -> list[str]:
    out, cur = [], ""
    for word in text.split():
        if cur and len(cur) + 1 + len(word) > width:
            out.append(cur); cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        out.append(cur)
    return out or [""]


def _as_list(v):
    return v if isinstance(v, (list, tuple)) else [v]


def _nref_name(cfg: dict) -> str:
    """The my_constants name whose density defines d_e,ref."""
    from .config import is_vacuum as _iv
    scale = str(cfg["reference"].get("length_scale")
                or ("ambient" if not _iv(cfg) else "critical"))
    return {"critical": "ncr", "target": "nt", "ambient": "namb"}[scale]


def _face_center(cfg: dict, sc: units.Scales) -> float:
    """Laser-facing face position in d_e,ref, from the target centre and thickness."""
    tgt = cfg["plasma"]["target"]
    centre = float(tgt.get("center_de", 0.0))
    half = 0.5 * float(tgt["thickness_de"])
    return centre + half if str(cfg["laser"].get("inject_side", "lo")) == "hi" \
        else centre - half


# --------------------------------------------------------------------------- #
# reverse direction: parse a deck (for post-run verification)
# --------------------------------------------------------------------------- #
def parse_inputs(path: str) -> dict:
    """Parse a WarpX inputs / warpx_used_inputs file into {key: raw_value_string}."""
    d = {}
    with open(path) as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            key, val = line.split("=", 1)
            d[key.strip()] = val.strip()
    return d


def _eval(expr: str, ns: dict) -> float:
    """Evaluate a WarpX scalar expression (translate ^ -> **) in a restricted namespace."""
    py = expr.replace("^", "**")
    return float(eval(py, {"__builtins__": {}}, {**ns, **_FUNCS}))


def resolve_constants(d: dict) -> dict:
    """Numerically resolve all my_constants.* expressions (iterative dependency pass)."""
    exprs = {k[len("my_constants."):]: v for k, v in d.items()
             if k.startswith("my_constants.")}
    resolved = dict(CONSTS)
    pending = dict(exprs)
    for _ in range(len(pending) + 2):
        if not pending:
            break
        progressed = False
        for name, expr in list(pending.items()):
            try:
                resolved[name] = _eval(expr, resolved)
                del pending[name]
                progressed = True
            except (NameError, KeyError, ValueError, ZeroDivisionError):
                continue
        if not progressed:
            break
    if pending:
        raise ValueError(f"could not resolve my_constants: {list(pending)}")
    return {k: resolved[k] for k in exprs}


def key_params(path: str) -> dict:
    """Resolve the deck at ``path`` to a flat dict of comparable numeric quantities.

    Used to verify ``warpx_used_inputs`` against a config independently of formatting,
    comments, or whether a value was written as ``40.*de`` or ``2.*di``.
    """
    d = parse_inputs(path)
    c = resolve_constants(d)
    ns = {**CONSTS, **c}
    out = {f"const:{k}": v for k, v in c.items()}
    out["max_step"] = int(float(d["max_step"]))
    out["cfl"] = float(d["warpx.cfl"])
    if "warpx.const_dt" in d:
        out["warpx.const_dt"] = _eval(d["warpx.const_dt"], ns)
    out["dims"] = int(float(d.get("geometry.dims", "1")))
    out["particle_shape"] = int(float(d["algo.particle_shape"]))
    if "warpx.random_seed" in d:
        out["warpx.random_seed"] = int(float(d["warpx.random_seed"]))
    out["n_cell"] = " ".join(str(int(float(v))) for v in d["amr.n_cell"].split())
    # Decomposition: changes which rank owns which particles, so a multi-rank run is
    # only reproducible at the same value -- same argument as n_accumulators.
    for k in ("amr.max_grid_size", "amr.max_grid_size_x", "amr.max_grid_size_y",
              "amr.max_grid_size_z", "amr.blocking_factor"):
        if k in d:
            out[k] = int(float(d[k]))
    for key in ("geometry.prob_lo", "geometry.prob_hi"):
        out[key] = " ".join(f"{_eval(v, ns):.10g}" for v in d[key].split())
    for bkey in ("boundary.field_lo", "boundary.field_hi",
                 "boundary.particle_lo", "boundary.particle_hi"):
        if bkey in d:
            out[bkey] = d[bkey].lower()
    for comp in ("x", "y", "z"):
        k = f"warpx.B{comp}_external_grid_function(x,y,z)"
        if k in d:
            out[k] = _eval(d[k].strip('"'), {**ns, "x": 0.0, "y": 0.0, "z": 0.0})

    # --- the laser block: this is the operator under test, so compare it strictly ---
    for k, conv in (("species", str), ("direction", str), ("inject_side", str),
                    ("temperature_mode", str), ("coulomb_log_mode", str),
                    ("intervals", str),
                    ("beam_profile", str), ("profile_intervals", str),
                    # The three hybrid swaps change WHAT is measured and WHERE the energy
                    # goes, so a stale binary silently ignoring one would invalidate the
                    # run exactly the way a stale `refraction` did (CLAUDE.md).
                    ("density_source", str), ("deposit_to", str),
                    ("profile_prefix", str)):
        kk = f"laser_deposition.{k}"
        if kk in d:
            out[kk] = conv(d[kk]).lower()
    for k in ("intensity", "incidence_angle", "Z_eff", "coulomb_log", "ray_cfl",
              "wavelength", "electron_temperature", "temperature_floor",
              "min_macroparticles_per_cell", "beam_waist", "beam_order",
              "rays_per_cell",
              # Phase 1.5. `ray_threads` cannot change the answer, but
              # `n_accumulators` fixes the summation order and `vacuum_skip`
              # gates an exact optimisation -- both belong in --verify.
              "ray_threads", "n_accumulators", "vacuum_skip",
              # `refraction` selects between two different marches, so it is the
              # least skippable line in the block.
              "refraction"):
        kk = f"laser_deposition.{k}"
        if kk in d:
            out[kk] = _eval(d[kk], ns)
    for k in ("beam_center", "beam_focus"):
        kk = f"laser_deposition.{k}"
        if kk in d:
            out[kk] = " ".join(f"{_eval(v, ns):.10g}" for v in d[kk].split())

    for sp in d.get("particles.species_names", "").split():
        k = f"{sp}.num_particles_per_cell_each_dim"
        if k in d:
            out[f"ppc:{sp}"] = d[k].strip()
        k = f"{sp}.density_function(x,y,z)"
        if k in d:
            out[f"dens:{sp}"] = d[k].strip('"').replace(" ", "")
    out["species_names"] = d.get("particles.species_names", "").strip()
    # --- hybrid solver + collisions ---
    for k in ("algo.maxwell_solver",
              "hybrid_pic_model.electron_energy_mode",
              "hybrid_pic_model.electron_temp_init"):
        if k in d:
            out[k] = str(d[k]).strip().lower()
    for k in ("hybrid_pic_model.elec_temp", "hybrid_pic_model.n0_ref",
              "hybrid_pic_model.n_floor", "hybrid_pic_model.substeps",
              "hybrid_pic_model.ue_cfl_max", "hybrid_pic_model.n_trust",
              "hybrid_pic_model.plasma_resistivity(rho,J,t)"):
        if k in d:
            out[k] = _eval(d[k], ns)
    cn = d.get("collisions.collision_names", "").strip()
    if cn:
        out["collisions.collision_names"] = cn
        for nm in cn.split():
            for suf, conv in (("type", str), ("species", str),
                              ("CoulombLog", None), ("ndt_supercycle", None)):
                k = f"{nm}.{suf}"
                if k in d:
                    out[k] = (str(d[k]).strip() if conv is str
                              else _eval(d[k], ns))
    for diag in ("EP", "FE", "PN", "diag1", "diag_fields", "diag_phase"):
        k = f"{diag}.intervals"
        if k in d:
            out[k] = int(float(d[k]))
    if "diag_fields.write_species" in d:
        out["diag_fields.write_species"] = int(float(d["diag_fields.write_species"]))
    return out


def verify(cfg: dict, inputs_path: str, rtol: float = 1e-6) -> list[str]:
    """Confirm the deck at ``inputs_path`` matches ``cfg``. Returns warnings."""
    import os
    import tempfile

    with tempfile.NamedTemporaryFile("w", suffix=".inputs", delete=False) as fh:
        fh.write(render(cfg))
        gen_path = fh.name
    try:
        want = key_params(gen_path)
        got = key_params(inputs_path)
    finally:
        os.unlink(gen_path)

    warns = []
    for k in sorted(set(want) | set(got)):
        # my_constants are an implementation detail: WarpX prunes unused ones from
        # warpx_used_inputs, and the same value may be written two ways. Value-check
        # only constants present in BOTH; the scalar settings carry the strict test.
        if k not in got:
            if not k.startswith("const:"):
                warns.append(f"{k}: missing from {os.path.basename(inputs_path)}")
            continue
        if k not in want:
            continue                      # extra keys in the deck are allowed
        gv, wv = got[k], want[k]
        try:
            if abs(float(gv) - float(wv)) > rtol * max(abs(float(wv)), 1e-30):
                warns.append(f"{k}: deck {float(gv):.6g} vs config {float(wv):.6g}")
        except (TypeError, ValueError):
            if gv != wv:
                warns.append(f"{k}: deck {gv!r} vs config {wv!r}")
    return warns
