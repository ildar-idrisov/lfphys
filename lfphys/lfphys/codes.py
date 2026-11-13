# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""Stable machine codes of the engine's refusals (review 2026-11-12 i18n-code F5).

An exception the engine raises for a user's set-up (a value out of range, a combination it cannot compute, an
instability, a resource limit) carries its text as a translatable ``T`` and, where a caller may need to tell one
refusal from another, a machine code: ``exc.code`` (a string from ``CODES``) and ``exc.data`` (the numbers of the text,
a dict; the ``T``'s arguments and any extras). A caller matches the code, never the wording: the English msgid may be
reworded and translated, the code stays. The exception keeps its type (``ValueError``, ``RuntimeError``,
``FloatingPointError``), so that every ``except`` keeps working; the attributes survive pickling.

    raise coded(ValueError(T("airy: total reflection at a film boundary (no propagating wave)")),
                "airy.total_reflection")

A code is never renamed or reused for another meaning; ``lfphys/tests/test_codes.py`` freezes the list.
"""

from __future__ import annotations

from .i18n import is_t

__all__ = ["CODES", "coded", "code_of", "data_of"]

#: every code and what it means (one line, English: for developers)
CODES: dict[str, str] = {
    # fluids (core.fluids.lbm)
    "lbm.tau": "the relaxation time is too close to 1/2 (viscosity too small for the grid and time step)",
    "lbm.mach": "the Mach number exceeds the scheme's limit (compressibility error too large)",
    "lbm.cell_reynolds": "the grid Reynolds number exceeds the limit: the grid does not resolve the flow",
    "lbm.rest_density": "an outlet pressure or a body force would push the rest density beyond the limit",
    "lbm.interp_moving": "an interpolated (Bouzidi) wall on a moving surface",
    "lbm.unstable": "the populations became non-finite during a step (lbm.Unstable)",
    "lbm.rebuild_unstable": "after a rebuild of the grid the populations left the admissible range (lbm.Unstable)",
    "lbm.adopt_unstable": "an adopted flow lies outside the admissible populations (lbm.Unstable)",
    "lbm.cut_by_edge": "a body or a source would be cut by the edge of a resized domain",
    "lbm.dye_has_sources": "the dye cannot be switched off while it has sources",
    # electromagnetism (core.em.fdtd, core.em.slit)
    "fdtd.unstable_medium": "the scheme is unstable in a medium (fdtd.Unstable, raised before a step)",
    "fdtd.unstable_interface": "the scheme is unstable at an interface of media (fdtd.Unstable)",
    "fdtd.non_finite": "the fields became non-finite during a step (fdtd.Unstable)",
    "fdtd.monitor_region": "a flux or far-field box lies on the wrong side of the total-field region",
    "fdtd.outside_grid": "a source, a probe or a monitor lies outside the grid",
    "fdtd.incident_memory": "the incident wave's series would take more memory than the limit",
    "slit.geometry": "the slits' widths, thickness or angle are not admissible",
    "slit.overlap": "the slits overlap",
    # optics (core.optics, theories.approx)
    "airy.lossy_index": "the Airy formula needs real positive indices (a lossless film)",
    "airy.total_reflection": "total reflection at a film boundary: no propagating wave in the film",
    "airy.grazing": "the wave grazes inside the film: the Airy formula is 0/0",
    "film.too_many_nodes": "joule_absorption_s needs more quadrature nodes in a layer than the limit",
    "film.below_critical": "an evanescent length below the critical angle",
    "mie.size_bound": "no tested truncation bound above the size parameter MAX_X",
    "mie.mx_too_large": "|m x| too large to start the logarithmic derivative D_n",
    "mie.no_convergence": "the continued fraction for D_n did not converge",
    "mie.index": "the sphere's relative index is not admissible (kappa < 0 or m = 0)",
    "mie.size": "the size parameter is not positive",
    "beams.memory": "a vortex beam's quadrature would take more elements than its budget",
    "beams.z": "a vortex beam's field at a z the method does not cover",
    "angular_spectrum.backward": "the angular spectrum propagates only forward (z >= 0)",
    "angular_spectrum.plane_extent": "a plane's extent is empty or longer than the window",
    "optics.z": "a field at a distance the formula does not cover (z must be positive)",
    "rainbow.order": "no rainbow of this order for this index",
    "rainbow.impact": "an impact parameter or an index without a refracted ray",
    "beams.mode_index": "a paraxial mode index out of range",
    "water.out_of_range": "a water property outside the range of its formulation (temperature, wavelength, density)",
    # quantum (core.quantum)
    "qscene.resolution": "the grid does not resolve a particle's wave next to what acts on it (an object or a packet "
                         "refused)",
    "qscene.packet_band": "a packet's |k| + 6 sigma_k exceeds pi/d along an axis: the grid does not resolve the wave",
    "qscene.field_with_charge": "the magnetic field cannot be changed while a charged particle is in the window",
    "qscene.gauge": "closed (periodic) window edges where the vector potential is not periodic (a charged particle)",
    "qscene.regrid_dimension": "a wave carried over from a scene of another dimension",
    "qscene.regrid_kind": "a wave with a spin or a mark carried over to a particle without them",
    "qscene.regrid_loss": "a change of the grid or the window would drop more of a wave than the tolerance",
    "qscene.layers": "more of a wave than the tolerance would lie in the absorbing layers of the window's edges",
    "qscene.no_wave": "a particle already registered by a detector has no wave to move or to change",
    "qscene.wrap": "a shift would carry more of a wave than the tolerance across a face of the periodic window",
    "qscene.alias": "a momentum kick or a move would not keep the wave (aliasing or a changed field)",
    "qscene.refused": "another refused live change of the scene (the exception's ``what`` says which)",
    "qscene.device_memory": "a scene operator and the scene are on different devices (GPU memory short)",
    "qscene.no_localisation_point": "a localisation jump found no point in the environment's region",
    "quantum.negative_probability": "a negative probability beyond round-off",
    "hydrogen.level": "no Dirac level with these quantum numbers",
    "cornell.box": "the Cornell states need a larger box",
    # QCD (core.qcd.running)
    "qcd.landau_pole": "the running coupling diverges on the way (running.LandauPole)",
    "qcd.rg_failed": "the integration of the renormalisation-group equation failed",
    # relativity, kinematics, gravity
    "kinematics.superluminal": "a speed at or above the speed of light",
    "gr.inside_horizon": "a clock, a body or an observer inside a horizon",
    "gr.not_timelike": "a worldline that is not timelike",
    "worldline.boost_order": "a boost before the last change of motion",
    "geometry.zero_normal": "a plane with a zero normal",
    "raytrace.camera_up": "the camera's up direction is parallel to its look direction",
    "kerr.spin": "a Kerr spin outside the allowed range",
    "kerr.axis_view": "an observer on the axis: the shadow is centred on the origin",
    "kerr.image": "a source or an image the shadow computation cannot place",
    "kn.no_horizon": "a Kerr-Newman hole without a horizon (chi^2 + q^2 >= 1 or chi < 0)",
    "kn.no_photon_orbit": "no circular photon orbit found",
    "kn.no_isco": "no ISCO found",
    "kn.on_axis": "a body on the symmetry axis, where the Boyer-Lindquist frame is singular",
    "kn.superluminal": "a body's local speed is not below c",
    "kn.zero_direction": "a photon with a zero direction",
    "kn.inside_capture": "a start inside the capture radius",
    "kn.step_underflow": "the integrator's step size underflowed for a body",
    "kn.observer": "an observer inside the horizon or on the axis",
    "kn_change.refused": "the declared rule cannot carry this change (kn_change_whatif.Refused)",
    "jp.irregular": "the Johannsen metric is not regular outside the horizon",
    "jp.photon_sphere": "no single photon sphere (or photon shell) outside the horizon",
    "jp.no_photon_orbit": "no circular photon orbit of the deviating metric within the searched range",
    "jp.no_stable_orbit": "no stable circular orbit of the deviating metric at the outer radius",
    "jp.no_isco": "no ISCO of the deviating metric within the searched range",
    "jp.no_bound_orbit": "no bound orbit is visible at this inclination",
    "jp.outside_bounds": "zero deviation is already outside the bounds",
    "orbit.horizon": "a start inside the horizon or below the body's surface",
    "orbit.not_bound": "no bound orbit with two turning points (or not a stable one)",
    "orbit.no_circular": "no circular orbit at this radius",
    "orbit.no_fall": "an outward start without an apoapsis does not fall",
    "orbit.superluminal": "a local speed at or above c",
    "newton.unbound": "a corpuscle orbit is not bound",
    "nbody.collision": "two bodies (or a field point and a body) at the same point",
    "nbody.body": "a body's mass, radius or vector is not admissible",
    "nbody.refused": "an edit of the bodies refused because it would put two bodies at the same point",
    "pn.invalid": "no bound PN orbit: eps <= 0 or j <= 0 (pn_binary.NoOrbit)",
    "pn.above_circular": "j above the circular value for this energy (pn_binary.NoOrbit)",
    "pn.plunge": "the bound region reaches the floor r_min: the orbit falls in (pn_binary.NoOrbit)",
    "pn.pn_breakdown": "a turning point of E and J that the equations of motion do not have (pn_binary.NoOrbit)",
    "pn.no_circular": "no circular PN orbit at this radius or energy (pn_binary.NoOrbit)",
    "pn.unresolved": "a numerical check of the PN orbit failed (pn_binary.NoOrbit)",
    "pn.start_below_stop": "the start is not above the stopping radius",
    "pn.plunge_integration": "the integration stopped: the orbit plunges and the PN equations break down",
    "pn.unbound": "an orbit-averaged quantity of an unbound orbit, or one without periapsides",
    # molecular dynamics (core.md, theories.models.interatomic)
    "md.value": "a value of the set-up is not admissible (a box, a density, a temperature, a species, a step)",
    "md.region": "a region is empty or lies outside the walls",
    "md.lattice_cell": "the region is smaller than one lattice cell at this density",
    "md.no_free_site": "no free lattice site in the block",
    "md.jammed": "random placement jammed: not every particle could be placed without overlaps",
    "md.overlap": "an inserted particle's potential energy exceeds the limit (atoms would overlap)",
    "md.insertion": "the insertion of molecules did not settle",
    "md.outside_walls": "a particle or a molecule outside the walls (or the piston)",
    "md.same_point": "two interacting particles, charges or bonded atoms at the same point",
    "md.non_finite": "non-finite forces, positions or velocities",
    "md.drift": "a particle crossed the walls too many times in one drift (time step too large)",
    "md.periodic_axis": "an axis is periodic: it has no wall to move or to put",
    "md.piston": "the piston forbids the change (its axis, its face, its side, one per system)",
    "md.ramp": "a box ramp is running, or its rate is above the limit",
    "md.bond_strain": "a bond would change its length by more than the limit",
    "md.cutoff": "the pair cutoff + skin exceeds half a periodic box length",
    "md.ewald": "charges in a box with a periodic axis: the Ewald sum is not implemented",
    "md.thermal_wall": "a thermal wall needs a temperature above 0",
    "md.thermostat": "a thermostat's parameters are not admissible",
    "md.hard_box": "a periodic box shorter than four diameters of the largest hard particle",
    "md.hard_overlap": "overlapping hard particles",
    "md.hard_affine": "an affine jump of hard spheres does no work of the collisional pressure",
    "md.hard_unsupported": "a term the hard-sphere solver does not have",
    "md.samples": "too few samples, or a radius beyond half a periodic box",
    "md.refused": "an addition refused because a force would become infinite",
    "md.potential": "a potential's parameter is not admissible",
    "md.bond_broke": "a FENE bond stretched to its maximum length (the bond broke)",
}


def coded(exc: BaseException, code: str, **data) -> BaseException:
    """``exc`` with the machine code ``code`` (a key of ``CODES``) and its numbers: ``exc.data`` holds the arguments of
    the exception's ``T`` and ``data``. Returns ``exc`` (``raise coded(ValueError(T(...)), "...")``)."""
    if code not in CODES:
        raise KeyError(f"unknown refusal code {code!r} (add it to lfphys.codes.CODES)")
    text = exc.args[0] if exc.args else None
    exc.code = code
    exc.data = {**(dict(text.get("a") or {}) if is_t(text) else {}), **data}
    return exc


def code_of(exc) -> str | None:
    """The machine code of an exception (``None`` when it has none)."""
    return getattr(exc, "code", None)


def data_of(exc) -> dict:
    """The numbers of a coded exception (``{}`` when it has none)."""
    return dict(getattr(exc, "data", None) or {})
