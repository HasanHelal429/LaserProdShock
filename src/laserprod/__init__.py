"""laserprod — config-driven tooling for the LaserProdShock test campaign.

Tests the WarpX ``LaserDeposition`` ray-tracing operator
(``warpx-cda/Source/Particles/LaserDeposition/``) used as a *shock driver*: an actual
ray-traced laser ablating a target, in place of the prescribed ``ParticleHeater`` +
``TargetInjector`` piston surrogate that ``../KinShock2020/`` used.

See ``TEST_PLAN.md`` for the campaign, ``OVERVIEW.md`` for the physics, ``CLAUDE.md`` for
the enforced rules.

Design, inherited from ``kinshock`` (``../KinShock2020/src/kinshock/``):

    ``runs/<ID>/config.yaml`` holds only PRIMARY quantities. Everything the analysis
    needs beyond them is derived HERE, so there is exactly one source of truth and no
    risk of a script drifting out of sync with the deck.

Planned modules (none implemented yet -- this is Phase 0, ``TEST_PLAN.md`` §5.1):

``units``
    Derived scales from the config primaries. Everything hangs off the laser wavelength:
    ``n_cr = eps0 m_e omega^2/e^2`` and, because ``omega_pe = omega_0`` at critical
    density, ``d_e,cr = c/omega_0 = lambda_0/(2 pi)`` exactly. Reports all three length
    scales (critical / target / ambient), the ambient ion scales (``d_i0``, ``rho_i0``,
    ``omega_ci0``), the IB absorption coefficient ``K`` and absorption depth, and the
    numerical health quantities ``omega_pe*dt`` (at peak compressed density) and
    ``dz/lambda_D`` per region. Pure ``math`` only, so it imports without yt/numpy.

``config``
    Load + validate a run config; resolve ``reference.length_scale``; report the numerical
    gates G1-G7 as warnings rather than exceptions (a deck may legitimately explore an
    off-plan point, but it may not do so silently).

``deck``
    ``config.yaml`` -> WarpX deck, plus ``verify`` (diff ``warpx_used_inputs`` against the
    config) and the boundary-token map. Ported from ``kinshock.deck``, extended for the
    ``laser_deposition.*`` block, transverse faces, and the laser injection face.

``io``
    Plotfile / reduced-diagnostic readers, plus the parser for the operator's own
    ``LASERDEP step <n> t <s> Pabs <W> Eabs <J>`` history and its per-cell
    ``laserdep_profile_*.txt`` dumps. The ``LASERDEP`` accounting is measured directly from
    the ray tracer and is therefore immune to grid heating -- unlike particle energies,
    which is why it is the primary laser diagnostic.

``metrics``
    Ablation and shock kinematics: absorbed fraction and shutoff time, the isothermal
    rarefaction / Schaeffer Eq. 1 expansion speed, piston speed from the ion front and the
    magnetic cavity, and the Schaeffer 2020 seven criteria / three timescales
    (``F(z,t)``, ``G(t)``, compressions, ramp scales, piston-shock separation). Port from
    ``kinshock.metrics``.

``plotting``
    Shared figure style.
"""

__all__ = []
