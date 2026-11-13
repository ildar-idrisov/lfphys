// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u39 view: what a fast observer sees. Next to the 3-D scene (the shared environment /static/js/env3d.js: the lab now
// — bodies Lorentz-contracted at their lab-simultaneous places, the retarded shapes the light comes from, the observer
// with its velocity and the lab directions its field of view takes the light from) the camera window
// (/static/js/imagewin.js) shows the image the run computed by light-time ray tracing. Drawing only: images, retarded
// shapes, Doppler factors and emission times all come from the run.
import { el, fill, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createImageWindow, inflate, unsubRows } from "/static/js/imagewin.js";
import { t, fmt, lang } from "/static/js/i18n.js";
import { MODE, page } from "/static/js/base.js";

function describe(meta, f, i, j) {
  const [H, W] = meta.shape, k = j * W + i;
  if (!f.body) return "";
  const b = f.body[k];
  if (b === -2) return t("nothing: no light comes here (black background)");
  const Dq = f.D[k], D = Dq ? Math.pow(2, (Dq - 1) / 65534 * 32 - 16) : NaN, T = f.T[k];
  const who = b === -1 ? t("the sky (a black body at rest in the lab)") : (meta.bodies[b] ? t(meta.bodies[b]) : t("body {b:d}", { b }));
  const parts = [`${who}`];
  if (meta.mode === "snapshot") parts.push(t("rest temperature {T:.5g} K (a snapshot without the light's travel time: not what is seen)", { T }));
  else if (meta.mode === "geometry") parts.push(`D = ${fmt(D, ".4g")}`, t("drawn in the colour at rest {T:.5g} K; actually seen as a black body at {DT:.4g} K", { T, DT: D * T }));  // review B3-11
  else parts.push(`D = ${fmt(D, ".4g")}`, t("seen as a black body at {DT:.4g} K (at rest {T:.5g} K)", { T, DT: D * T }));
  const dq = f.delay[k];
  if (dq && meta.mode !== "snapshot") parts.push(t("the light was emitted {d:.4g} ns before it is seen", { d: (dq - 1) / 65534 * meta.delay_max * 1e9 }));
  return parts.join(" · ");
}

// A panel body (the floor) comes as a grid of vertices one checker cell apart, each vertex coloured by the cell between
// it and the panel's centre (the run samples the pattern at q (1 - 1e-9), lfphys.core.raytrace._pattern): blending
// those colours across a cell drew the checkerboard as diagonal saw-teeth. Each cell is drawn here in one colour, the
// colour of its corner farthest from the centre, which is the cell's own (review UX-3d A12). Other meshes pass as sent.
function flatCells(meta, blobs) {
  const pos = blobs.pos, idx = blobs.idx, rgb = blobs.rgb, n = pos.length / 3;
  if (!idx || idx.length < 6) return null;
  const kv = idx[2] - idx[0] - 1;  // triangles (a, a+1, a+kv+1), (a, a+kv+1, a+kv)
  if (!(kv >= 2) || n % kv) return null;
  const ku = n / kv, cells = (ku - 1) * (kv - 1);
  if (idx.length !== 6 * cells) return null;
  const P = new Float32Array(12 * cells), C = new Uint8Array(12 * cells), I = new Uint32Array(6 * cells);
  const ic = (ku - 1) / 2, jc = (kv - 1) / 2;
  let q = 0, ti = 0;
  for (let i = 0; i < ku - 1; i++) for (let j = 0; j < kv - 1; j++) {
    const fi = Math.abs(i + 1 - ic) > Math.abs(i - ic) ? i + 1 : i, fj = Math.abs(j + 1 - jc) > Math.abs(j - jc) ? j + 1 : j;
    const far = fi * kv + fj;
    for (const k of [i * kv + j, i * kv + j + 1, (i + 1) * kv + j + 1, (i + 1) * kv + j]) {
      P.set(pos.subarray(3 * k, 3 * k + 3), 3 * q); C.set(rgb.subarray(3 * far, 3 * far + 3), 3 * q); q++;
    }
    I.set([q - 4, q - 3, q - 2, q - 4, q - 2, q - 1], ti); ti += 6;
  }
  return { meta: { ...meta, count: q }, blobs: { ...blobs, pos: P, idx: I, rgb: C } };
}

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin" });
  const win = createImageWindow({ title: t("The observer's camera: the computed image"), describe });
  env.center.append(win.el);
  const nowBox = el("div", { class: "kv" }), imgBox = el("div", {}), devBox = el("div", { class: "kv" });
  const rightPanels = [panel(t("Observer now"), nowBox), panel(t("Image"), imgBox), panel(t("Scene layers"), env.layersPanel),
                       panel(t("Where it was computed"), devBox)];
  let H = null, images = new Map(), shown = -1, pending = null;

  function drawDev(img) {
    // the image's own device (sent with every image, review B3-8); before the first image, the header's record
    const u = (((H && H.backend) || {}).used || {})["relativity.raytrace"];
    const d = (img && img.device) || (u && u.drawn);
    fill(devBox, el("span", {}, t("ray tracing")), el("span", { class: "mono" }, d ? `${d.device === "gpu" ? "GPU" : "CPU"}, ${d.precision}` : "—"),
      el("span", {}, t("why")), el("span", {}, d ? t(d.reason) : ""),
      ...(MODE === "server" ? [el("span", {}, t("settings")), el("a", { href: page("settings"), target: "_blank" }, t("⚙ Devices"))] : []));  // the site has no settings
  }
  function drawImgPanel(meta) {
    const legend = [];
    if (!meta) { fill(imgBox, el("div", { class: "muted" }, t("The image appears when the run has computed it."))); return; }
    legend.push(el("div", { class: meta.mode === "seen" ? "" : "warn" }, t(meta.mode_label)));
    if (meta.mode === "doppler") legend.push(el("div", { class: "help" }, t("False colours: red — D < 1 (the light got redder and weaker), grey — D ≈ 1, blue — D > 1 (bluer and brighter); the scale runs from D = 1/8 to 8 (logarithmic).")));
    else if (meta.mode === "delay") legend.push(el("div", { class: "help" }, t("False colours: blue — the light was emitted recently, red — long ago (up to {d:.4g} ns before).", { d: meta.delay_max * 1e9 })));
    else legend.push(el("div", { class: "help" }, t("Every surface shines as a black body of its temperature (the pattern is in the body's frame). The observer sees a black body at D·T: the colour and the brightness are computed by Planck's law. Point at the image for D, the temperature and when the light was emitted.")));
    legend.push(el("div", { class: "kv" }, el("span", {}, t("exposure")), el("span", { class: "mono" }, t("{how}, correction {ev:.3g} stops", { how: meta.auto ? t("per frame") : t("as for the scene at rest"), ev: meta.ev })),
      el("span", {}, t("frame time")), el("span", { class: "mono" }, t("{t:.6g} ns", { t: meta.t * 1e9 })),
      el("span", {}, t("size")), el("span", { class: "mono" }, `${meta.shape[1]} × ${meta.shape[0]}`)));
    fill(imgBox, legend);
  }
  function drawNow(f) {
    if (!f || !f.obs) return;
    const b = Math.hypot(...f.obs.beta);
    const vec = (v, d) => t("({x}, {y}, {z})", { x: fmt(v[0], `.${d}g`), y: fmt(v[1], `.${d}g`), z: fmt(v[2], `.${d}g`) });
    fill(nowBox, el("span", {}, t("time t (lab)")), el("span", { class: "mono" }, t("{t:.6g} ns", { t: f.t_ns })),
      el("span", {}, t("proper time τ")), el("span", { class: "mono" }, t("{t:.6g} ns", { t: f.tau_ns })),
      el("span", {}, t("velocity β")), el("span", { class: "mono" }, b > 0 ? t("{b:.5g} along {dir}, γ = {g:.5g}", { b, dir: vec(f.obs.beta.map((c) => c / b), 3), g: f.obs.gamma }) : t("0 (at rest)")),
      el("span", {}, t("position")), el("span", { class: "mono" }, t("{pos} m", { pos: vec(f.obs.x, 4) })));
  }

  async function show(seq) {
    const rec = images.get(seq);
    if (!rec) return;
    pending = seq;
    const { meta, blobs } = rec;
    try {
      const [rgb, Db, dl, T, body] = await Promise.all(["rgb", "D", "delay", "T", "body"].map((k) => inflate(blobs[k])));
      if (pending !== seq) return;
      const W = meta.shape[1];
      win.setImage(meta, new Uint8Array(rgb), { D: unsubRows(new Uint16Array(Db), W), delay: unsubRows(new Uint16Array(dl), W),
                                                T: new Uint16Array(T), body: new Int8Array(body) },
                   t("{mode} · t = {t:.6g} ns", { mode: meta.mode_label, t: meta.t * 1e9 }));
      for (const r of meta.retarded || []) {
        if (!blobs.ret_pos) break;
        env.scene.updateMesh(r.id, blobs.ret_pos.subarray(3 * r.from, 3 * (r.from + r.count)), blobs.ret_rgb.subarray(3 * r.from, 3 * (r.from + r.count)));
      }
      shown = seq;
      drawImgPanel(meta);
      drawDev(meta);
    } catch (e) { console.error(e); win.setStatus(el("span", { class: "st-bad" }, t("the image was not read: {error}", { error: e.message }))); }
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, t("What a fast observer sees")),
      el("p", {}, t("On the right is the image the run computed: for every pixel of the camera, a photon that reaches the observer at this moment. Its direction is taken into the lab frame by a Lorentz transformation (aberration), its path is followed back in time to the body that emitted it (the light's travel time), and its colour and brightness are those of a black body at the temperature D·T, where D is the Doppler factor (the Doppler colour and the searchlight effect).")),
      el("p", {}, t("A fast body does not look flattened: the ball stays a circle (Penrose), the cube looks turned — its rear face is seen (Terrell). Approaching, a body looks farther and bluer; receding, nearer and redder. A fast observer sees the world crowded forward, blue and bright ahead.")),
      el("p", {}, t("The 3-D view shows the lab now: the bodies Lorentz-contracted at their places at this moment (semi-transparent) and the places the light seen now came from (the retarded shapes; the points that are seen are bright), the observer, its velocity and the directions in the lab from which light reaches the edges of the frame.")),
      el("p", {}, t("The observer's speed changes on the fly: this is a boost at the current moment, and the image changes at once (the same light, other directions and frequencies). The bodies' speed is a world parameter. The modes “geometry only” and “instantaneous snapshot” are for comparison: they are not what is seen.")),
      el("p", {}, t("Checks (on the right, “Checks”): the sky against T/(γ(1 − β cos θ′)), the stars against the aberration formula, the emission time and D against the retarded time, the ball's outline is a circle (Penrose), the scene at rest gives ordinary rays."))),
    reset() { env.reset(); H = null; images = new Map(); shown = -1; pending = null; drawImgPanel(null); },
    // key frames (player.js): the environment's own key frame; the images only grow (their number), the one shown is
    // chosen again by the next frame drawn
    snapshot() { return { env: env.snapshot(), images: images.size }; },
    restore(k) {
      env.restore(k.env);
      let i = 0;
      for (const seq of [...images.keys()]) { if (i++ >= k.images) images.delete(seq); }
      shown = -1; pending = null;
    },
    onHeader(meta) { H = meta; env.onHeader(meta); drawDev(); drawImgPanel(null); },
    onMessage(meta, blobs) {
      if (meta.type === "mesh" && H && (H.bodies || []).some((bd) => `body${bd.id}` === meta.id && bd.kind === "panel")) {
        const f = flatCells(meta, blobs);  // the environment keeps (and a key frame sets again) the mesh as drawn
        if (f) { meta = f.meta; blobs = f.blobs; }
      }
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "image") images.set(meta.seq, { meta, blobs });
    },
    render(meta) {
      if (!H || !meta) return;
      for (const b of meta.bodies || []) env.scene.transformMesh(b.id, b.A, b.b);
      if (meta.obs) env.scene.setObserver("observer", { pos: meta.obs.x, beta: meta.obs.beta, cone: meta.cone });
      drawNow(meta);
      if (meta.img_seq && meta.img_seq !== shown && meta.img_seq !== pending) show(meta.img_seq);
      env.scene.requestRender();
    },
  };
}
