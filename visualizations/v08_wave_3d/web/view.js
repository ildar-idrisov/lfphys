// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v08 view: the 3-D scene of the run (the screen with its aperture, the incident wave, the light behind the screen,
// the energy current, the target) and up to three slice planes with their windows (the shared 3-D environment:
// /static/js/env3d.js). Every element can be switched off; planes are placed, moved and turned by hand (gizmo) or by
// parameters; each slice is computed by the run for its plane (view command "plane").
import { el, fill, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";
import { t, fmt, lang } from "/static/js/i18n.js";

export function createView(ctx) {
  // the log scale starts at (3 x the window's error)^2 of the peak, in the windows and in the 3-D scene alike
  const env = createEnv3D(ctx, { logFloor: (H) => Math.max(1e-6, (3 * ((H && H.accuracy && H.accuracy.window) || 0)) ** 2) });
  let modelling = null;  // the modelling in force: the header's, then the latest "modelling" message
  const modeBox = el("div", {}), accBox = el("div", { class: "kv" }), devBox = el("div", { class: "kv" });
  const rightPanels = [panel(t("Scene layers"), env.layersPanel), panel(t("Slice: position and tilt"), env.planePanel),
                       panel(t("Modelling"), modeBox), panel(t("Accuracy"), accBox), panel(t("Where it was computed"), devBox)];

  function drawPanels() {
    const H = env.header();
    if (!H) return;
    const m = modelling || {};
    fill(modeBox,
      el("div", {}, el("b", {}, m.mode === "full3d" ? t("Whole volume") : t("Slices only"))),
      el("div", { class: m.approximation ? "st-bad" : "muted" }, m.mode === "full3d"
        ? t("the whole volume is computed: the light and the energy current in 3-D; any slice is computed exactly for its plane")
        : t("{note} Each slice placed is computed for its own plane; the volume is not computed.", { note: m.note || "" })));
    const a = H.accuracy || {};
    fill(accBox, el("span", {}, t("computation window")), el("span", { class: "mono" }, a.pad ? (a.band_limit ? t("×{pad:d}, band-limited", { pad: a.pad }) : t("×{pad:d}", { pad: a.pad })) : "—"),
      el("span", {}, t("error at z_max")), el("span", { class: "mono" }, a.window !== undefined ? t("≈ {err:.2g} of the peak amplitude (at most {tol:.2g} needed)", { err: a.window, tol: a.tol }) : "—"),
      el("span", {}, t("next to the aperture")), el("span", {}, a.z_near ? t("z < {z:.2g} µm: the field band-limited by the grid (hatched)", { z: a.z_near }) : "—"),
      el("span", {}, t("slices")), el("span", {}, t("each is checked against the exact field at its own points (the line under its window)")));
    const u = (((H.backend || {}).used || {})["optics.angular_spectrum"] || {}).drawn;
    fill(devBox, el("span", {}, t("angular spectrum")), el("span", { class: "mono" }, u ? `${u.device === "gpu" ? "GPU" : "CPU"}, ${u.precision}` : "—"),
      el("span", {}, t("why")), el("span", {}, u ? t(u.reason) : ""),
      el("span", {}, t("checks")), el("span", {}, t("always fp64")),
      el("span", {}, t("settings")), el("a", { href: "/settings", target: "_blank" }, t("⚙ Devices")));
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, t("3-D scene")),
      el("p", {}, t("In the centre is the 3-D scene of this run: the screen with its aperture in the plane z = 0, the incident plane wave (given), the light behind the aperture (the computed volume; in the mode «whole volume»), the energy current (arrows; switched on in «Scene layers») and the target at the depth z_max with its computed intensity. Any part can be switched off in the panel «Scene layers».")),
      el("p", {}, t("Slices are planes at any angle, up to three. «＋ Slice» places the next plane through the middle of the region, perpendicular to those already there (turned ones included). A click on a plane selects it: the arrow moves it along its normal, the rings tilt it (W / E switch between them); the same by numbers in the panel «Slice: position and tilt». Once a plane is released, the engine computes the field on it exactly and checks it against the exact field at its points; while a plane is dragged, its window shows a preview. Slices are kept in a new world of this run; «defaults» brings back one slice y = 0.")),
      el("p", {}, t("The window of each slice is to the right of the 3-D view, in the colour of its plane; pointing at a window highlights its plane. A window shows the intensity, the amplitude, its logarithm or the phase; the axes are in µm; under the cursor, the coordinates and the value; CSV gives the slice's data. The hatched zone next to the aperture is where the field is band-limited by the grid.")),
      el("p", {}, t("Slices stay where they are put. Auto-move (optional, per slice) moves a plane along its normal while the world's time runs.")),
      el("p", {}, t("Camera: left button to rotate, right button to pan, wheel to zoom; view buttons: iso, side, top, from the source, from the target; 📷 takes a picture."))),
    reset() { env.reset(); modelling = null; },
    // key frames (player.js): the environment's own key frame and the modelling in force (a view variable: the header
    // the player keeps is never written, review CK-14)
    snapshot() { return { env: env.snapshot(), modelling }; },
    restore(k) { env.restore(k.env); modelling = k.modelling; drawPanels(); },
    onHeader(meta) { env.onHeader(meta); modelling = meta.modelling || null; drawPanels(); },
    onMessage(meta, blobs) {
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "modelling") { modelling = meta.modelling; drawPanels(); }
    },
    render() { env.scene.requestRender(); },
  };
}
