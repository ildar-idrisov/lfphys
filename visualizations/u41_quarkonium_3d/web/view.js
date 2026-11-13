// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v14 view: the wave functions of a heavy quark pair in the Cornell model (the shared wave-function view
// /static/js/orbitview.js over the 3-D environment). Drawing only: every value comes from the run.
import { el } from "/static/js/ui.js";
import { t, fmt, lang } from "/static/js/i18n.js";
import { createOrbitView } from "/static/js/orbitview.js";
import { withPreparation } from "/viz/v13_hydrogen_3d/view.js";  // the state is live: prepared at the current moment

export function createView(ctx) {
  return withPreparation(createOrbitView(ctx, {
    energyName: t("M − M(1S), model"),
    levelColumns: ["S", "P", "D"],
    describeAtom: (H) => {
      const s = H.system || {};
      return el("div", {},
        el("div", { class: "warn" }, t("A model (fitted parameters): the splittings of the levels are right, not the absolute masses.")),
        el("div", { class: "kv" }, el("span", {}, t("pair")), el("span", {}, t(s.label || "")),
          el("span", {}, t("potential")), el("span", { class: "mono" }, t("−κ/r + r/a², κ = {kappa:.3g}, a = {a:.3g} GeV⁻¹", { kappa: s.kappa, a: s.a })),
          el("span", {}, t("quark mass")), el("span", { class: "mono" }, t("{m:.4g} GeV (reduced {mu:.4g})", { m: s.m_q, mu: s.mu }))));
    },
    help: [
      t("Quarkonium in 3-D"),
      t("A pair of heavy quarks (cc̄, charmonium; bb̄, bottomonium) in the Cornell model: the Coulomb attraction due to gluon exchange at short distances and the linearly rising “string” of confinement. The model is non-relativistic, without spin-dependent forces, and its parameters are fitted to the spectrum; it predicts the splittings of the levels (1P − 1S, 2S − 1S) to {lo}–{hi} %, but not the absolute masses. It is a model outside the engine's core, and the world is marked as such.", { lo: 2, hi: 10 }),
      t("The cloud is the probability density |ψ|² of the vector r between the quark and the antiquark (the centre of mass at the origin). The radial functions are a numerical solution of the radial equation (a sine basis, Richardson extrapolation); its accuracy is checked by a second solution on a finer grid (“Convergence”: the difference is below half a quantisation step of the 8-bit image)."),
      t("On the left, the model's levels: the splittings from 1S (solid) and experiment (PDG), the spin-averaged masses (dashed). On the right, the state, the radial distribution r²|R|², and the slices with |ψ|² and the phase (verified at points against the second solution and scipy's harmonics)."),
      t("The superposition 1S + 1P oscillates at the model's transition frequency (a period of ~{T} s): the phases are revealed when the world's time reaches them.", { T: 1e-23 }),
      t("The state changes on the fly (on the left, “Set-up”): the new state is prepared at the current moment (an ideal preparation, the former one discarded); the world, its time and the slices stay, and the period counts from the moment of preparation. Another quark pair is a new world."),
    ],
  }));
}
