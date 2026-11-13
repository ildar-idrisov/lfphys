// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v09 view: the manoeuvre in the shared 3-D environment (/static/js/env3d.js). Velocity space (the ball of
// velocities, light at its boundary) or ordinary space; the path revealed as the run's time reaches it, the gyroscope
// triads along it, the craft with its gyroscopes, spin and thrust, the rotation axis when the loop closes; in velocity
// space the field of three-burn loops as a volume, its rotation axes as arrows, and up to three slice planes with
// their windows. Drawing only: every number comes from the run.
import { el, fill, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";
import { t, fmt, lang } from "/static/js/i18n.js";

const deg = (r) => r * 180 / Math.PI;
// a vector of three numbers: the separator follows the language (ru: decimal commas, so "; " between the components)
const vec = (v, d) => t("({x}, {y}, {z})", { x: fmt(v[0], `.${d}g`), y: fmt(v[1], `.${d}g`), z: fmt(v[2], `.${d}g`) });

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin" });
  const loopBox = el("div", { class: "kv" }), nowBox = el("div", { class: "kv" }), resBox = el("div", {});
  const legend = el("div", { class: "help" },
    el("div", {}, el("span", { style: { color: "#ff5a5a" } }, "■"), " ", el("span", { style: { color: "#5adc78" } }, "■"), " ",
      el("span", { style: { color: "#5aa0ff" } }, "■"), " ", t("— the gyroscopes' axes 1, 2, 3 (relative to the frame reached from rest by one boost)")),
    el("div", {}, el("span", { style: { color: "#ffd23f" } }, "➜"), " ", t("spin (the axis of gyroscope 1)"), "  ",
      el("span", { style: { color: "#ff8a1f" } }, "➜"), " ", t("thrust (the direction of acceleration)")));
  // panel(title, body): one body element each (the result and the legend were once passed as a third argument and lost)
  const rightPanels = [panel(t("Manoeuvre and holonomy"), el("div", {}, loopBox, resBox)), panel(t("Now"), el("div", {}, nowBox, legend)),
                       panel(t("Scene layers"), env.layersPanel), panel(t("Slice: position and tilt"), env.planePanel)];
  let H = null, R = null;

  function drawLoop() {
    if (!H) return;
    const L = H.loop || {};
    fill(loopBox,
      el("span", {}, t("loop")), el("span", {}, L.planar ? t("planar (a closed form exists)") : t("non-planar")),
      el("span", {}, t("pieces of thrust")), el("span", { class: "mono" }, fmt(L.pieces, "d")),
      el("span", {}, t("planned fuel L")), el("span", { class: "mono" }, t("{L:.5g} (the sum of rapidities, ∫|a|dτ/c)", { L: L.fuel })),
      el("span", {}, t("reference")), el("span", {}, L.ref_how ? t(L.ref_how) : "—"));
  }
  function drawResult() {
    if (!R) { fill(resBox, el("div", { class: "muted" }, t("The result appears when the loop closes (the craft is back at rest)."))); return; }
    const sign = R.spinor_sign < 0 ? t("−1: the spinor changed its sign") : "+1";
    fill(resBox, el("div", { class: "kv" },
      el("span", {}, t("rotation of the gyroscopes, SO(3)")), el("span", { class: "mono" }, t("{a}° about {axis}", { a: fmt(deg(R.angle), ".6g"), axis: vec(R.axis, 3) })),
      el("span", {}, t("spinor, SU(2)")), el("span", { class: "mono" }, t("{a}° · sign {sign}", { a: fmt(deg(R.su2_angle), ".6g"), sign })),
      R.planar ? el("span", {}, t("accumulated angle (along the computation)")) : null,
      R.planar ? el("span", { class: "mono" }, t("{a:.8g} rad (the reference is the area; in the checks)", { a: R.accumulated })) : null,
      el("span", {}, t("duration of the manoeuvre")), el("span", { class: "mono" }, t("{T} by the clocks at rest, {tau} by the craft's clock", { T: years(R.T_end), tau: years(R.tau_end) })),
      el("span", {}, t("largest γ")), el("span", { class: "mono" }, fmt(R.gamma_max, ".5g")),
      el("span", {}, t("bound of planar loops")), el("span", { class: "mono" }, t("{b:.6g} rad at L = {L:.5g}", { b: R.bound, L: R.per_fuel_L })),
      el("span", {}, t("angle / bound")), el("span", { class: "mono" }, t("{r:.6g} ({how})", { r: R.per_bound, how: R.per_fuel_how }))),
      el("div", { class: "help" }, R.planar
        ? t("A planar loop: the gyroscopes rotate by the loop's area in velocity space, opposite to the sense in which it is traversed; the circle is the only case of equality in the isoperimetric bound.")
        : t("A non-planar loop: the bound is proven only for planar loops; here it is a line of comparison.")));
  }
  // a time in years with the plural form of the number as shown (5 significant digits): «1,4794 года», «5 лет»
  function years(x) { return t("{x} yr", { x: fmt(x, ".5g"), n: Number(Number(x).toPrecision(5)) }); }
  function drawNow(f) {
    if (!f) return;
    fill(nowBox,
      el("span", {}, t("time t / τ")), el("span", { class: "mono" }, `${fmt(f.t_yr, ".5g")} / ${years(f.tau)}`),
      el("span", {}, t("fuel")), el("span", { class: "mono" }, fmt(f.s, ".5g")),
      el("span", {}, t("velocity β")), el("span", { class: "mono" }, `${vec(f.beta, 4)}, γ = ${fmt(f.gamma, ".5g")}`),
      el("span", {}, t("largest γ so far")), el("span", { class: "mono" }, fmt(f.gamma_so_far, ".5g")),
      el("span", {}, t("gyroscopes turned by")), el("span", { class: "mono" }, t("{a}° about {axis}", { a: fmt(deg(f.rot_angle), ".5g"), axis: vec(f.rot_axis, 3) })));
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, t("Thomas–Wigner precession in 3-D")),
      el("p", {}, t("A craft starts at rest and flies a manoeuvre: burns (thrust in a fixed direction) and turns of the thrust, both given in its own frame. The gyroscopes on board do not rotate (Fermi–Walker transport). When the craft is back at rest, the gyroscopes are found to be rotated: this is the holonomy of the loop its velocity traces in velocity space (Thomas precession; for two boosts, the Wigner rotation).")),
      el("p", {}, t("Velocity space is the ball β = v/c; its boundary is light. A burn in a fixed direction is a straight segment (this is how the picture is constructed: geodesics are chords). For a planar loop the rotation equals its area (Gauss–Bonnet, curvature −1), opposite to the sense in which the loop is traversed; for uniform circular motion it is 2π(γ − 1) per revolution (Thomas). SU(2) keeps more than SO(3): a rotation by 2π brings the gyroscopes back but changes the spinor's sign (the “SU(2): the gyroscopes are back (a rotation by 2π), the spinor changed its sign” preset).")),
      el("p", {}, t("The fuel L is the sum of rapidities (∫|a|dτ/c). Of the planar loops with a given L, the circle encloses the largest area: √(4π² + L²) − 2π (the isoperimetric inequality of the Lobachevsky plane). For non-planar loops this value is a line of comparison, not a proven bound.")),
      el("p", {}, t("The field in the ball: for every velocity w, the rotation of the gyroscopes after the loop rest → u → w → rest (u is set in the field's parameters), or that rotation divided by the bound at the same fuel. Slices are planes at any angle (up to three); each is computed for its own plane and checked against the area of the triangle of velocities at its points.")),
      el("p", {}, t("Time is lab time (years). The path, the gyroscopes and the result appear as the time runs («▶»). In ordinary space the scene shows the craft's trajectory in light-years; there are no slices there."))),
    reset() { env.reset(); H = null; R = null; },
    // key frames (player.js): the environment's own key frame (the path and the triads are cut back) and the result
    snapshot() { return { env: env.snapshot(), R }; },
    restore(k) { env.restore(k.env); R = k.R; drawResult(); },
    onHeader(meta) { H = meta; R = null; env.onHeader(meta); drawLoop(); drawResult(); },
    onMessage(meta, blobs) {
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "holonomy") { R = meta; drawResult(); }
    },
    // the player hands every frame (the state at the time shown) to render
    render(meta) {
      if (H && meta && meta.pos) {
        env.scene.setBody("craft", { pos: meta.pos, O: meta.O, spin: meta.spin, thrust: meta.done ? null : meta.thrust });
        drawNow(meta);
      }
      env.scene.requestRender();
    },
  };
}
