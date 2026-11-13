// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v13 view: the hydrogen atom's orbital cloud, current and slices (the shared wave-function view
// /static/js/orbitview.js over the 3-D environment). Drawing only: every value comes from the run.
import { el, num } from "/static/js/ui.js";
import { t, fmt, lang } from "/static/js/i18n.js";
import { createOrbitView } from "/static/js/orbitview.js";

// The state is live (review UX-ui U12): a change prepares the new state at the current moment, and the run sends
// `prepared` with the parts of the header that describe it (states, levels, period, the scene's box). The shared view
// is started again from the world's header with those parts (its cloud, current and slices of the former state are
// dropped; the messages that follow bring the new ones), and the phase of the period is counted from the preparation
// (frames carry `t_prep`). Also used by v14.
export function withPreparation(view) {
  let H0 = null;
  return {
    ...view,
    reset() { H0 = null; view.reset(); },
    onHeader(meta, blobs) { H0 = meta; view.onHeader(meta, blobs); },
    onMessage(meta, blobs) {
      if (meta.type === "prepared") {  // the panel "State" names the state; the title names only the atom
        if (H0) view.onHeader({ ...H0, ...meta.header });
        return;
      }
      view.onMessage(meta, blobs);
    },
    render(meta, tNow) { view.render(meta, meta && Number.isFinite(tNow) ? tNow - (meta.t_prep || 0) : tNow); },
  };
}

export function createView(ctx) {
  return withPreparation(createOrbitView(ctx, {
    energyName: t("energy E"),
    describeAtom: (H) => {
      const a = H.atom || {};
      return el("div", { class: "kv" }, el("span", {}, t("atom")), el("span", {}, t(a.label || "")),
        el("span", {}, t("reduced mass")), el("span", { class: "mono" }, `μ = ${num(a.mu_over_me, 9)} mₑ`),
        el("span", {}, t("Bohr radius")), el("span", { class: "mono" }, `a_μ = ${num(a.a_A, 7)} Å`));
    },
    help: [
      t("The hydrogen atom in 3-D"),
      t("The cloud is the probability density |ψ|² of finding the electron at a point (the electron's coordinate relative to the nucleus; the motion of the centre of mass is separated, hence the reduced mass μ). The wave function is the exact solution of the Schrödinger equation: R_nl(r) (Laguerre polynomials) × Y_lm(θ, φ); the engine computes it in this run, on a grid of up to {n}³ points.", { n: 96 }),
      t("Real orbitals (p_x, d_xy, d_z², …) are standing waves: there is no probability current. Complex states with m ≠ 0 make a doughnut cloud, and the current flows in rings around the z axis (the arrows). A superposition of two levels (for example 1s + 2p_z) oscillates at the Bohr frequency ω = ΔE/ħ: the phases of the period are revealed when the world's time reaches them; after that the cloud repeats (verified: one period T later it equals the initial one)."),
      t("The slices are planes at any angle (up to three): |ψ|² and the phase of ψ computed for the plane itself; in every slice ψ at several points is verified against an independent calculation (the series of the Laguerre polynomial and scipy's harmonics). The “phase” mode in a slice window shows arg ψ: in complex states the phase winds m times around the z axis."),
      t("On the right: the state (the energy, ⟨r⟩ by quadrature and by the formula), the radial distribution r²|R|² (its maxima are the “shells”, its zeros the radial nodes) and the energy levels (this world's levels highlighted). Checks: the normalisation, ⟨r⟩, the energy ⟨T⟩ + ⟨V⟩ from the wave function itself against Bohr's formula, the number of nodes, the current against the closed form or the continuity equation, the oscillation ⟨z⟩(t) against the matrix element."),
      t("The 3-D cloud stores the amplitude in 8 bits (as does the texture): values of |ψ|² below {f} of the peak are drawn as zero; the exact values are in the slice windows.", { f: 1.5e-5 }),
      t("The state changes on the fly (on the left, “Set-up”): a new n, l, m, kind of orbital or superposition is prepared at the current moment; the world, its time and the slices stay, the cloud, the current, the slices and the checks are computed for the new state, and the period of a superposition counts from the moment of preparation. The preparation is ideal: the former state is discarded; how the atom got into the new one (a photon, a measurement) is not modelled here. Checks of the former state that the new one does not have are marked “former state”. Another atom is a new world."),
    ],
  }));
}
