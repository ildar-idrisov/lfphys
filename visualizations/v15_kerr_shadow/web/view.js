// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v15 view: the shadow of a Kerr black hole and its photon rings. Next to the 3-D scene (the shared environment
// /static/js/env3d.js: the horizon, the ergosphere, the disk, the equatorial photon orbits and the ISCO, the observer's
// direction and sample light rays, all from the run) the screen window (/static/js/imagewin.js) shows the image the run
// computed row by row: brightness, the order n of the disk images, the redshift or the fate of each pixel, with
// Bardeen's critical curve (and in a "what if" world the deviating metric's shadow edge) drawn over it. Drawing only.
import { el, fill, num, panel } from "/static/js/ui.js";
import { t, fmt, lang } from "/static/js/i18n.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createImageWindow } from "/static/js/imagewin.js";

const MODES = [["seen", t("brightness: the sum of g⁴J over the crossings of the disc")],
               ["order", t("which crossing shines brightest: n = 0, 1, 2")],
               ["redshift", t("redshift g (false colours)")],
               ["fate", t("the ray's fate: captured (the shadow) or arrived from far away")]];
const ORDER_RGB = [[255, 170, 60], [90, 200, 255], [255, 255, 255]];

function describe(meta, f, i, j) {
  if (!f.cap) return "";
  const W = meta.shape[1], k = j * W + i;
  const a = meta.camera.alpha[0] + (i + 0.5) / W * (meta.camera.alpha[1] - meta.camera.alpha[0]);
  const b = meta.camera.beta[1] - (j + 0.5) / meta.shape[0] * (meta.camera.beta[1] - meta.camera.beta[0]);
  const parts = [`α = ${num(a, 4)} M, β = ${num(b, 4)} M`];
  if (j >= f.rows) return parts.concat([t("not computed yet")]).join(" · ");
  if (f.cap[k]) parts.push(t("the ray is captured by the hole (the shadow)"));
  else parts.push(t("the ray came from far away"));
  // the n-th crossing of the equatorial plane along the ray traced back; on the disk only between its edges
  for (let n = 0; n <= f.nmax; n++) {
    const q = n * W * f.ny + k, r = f.r[q], g = f.g[q], face = f.face ? f.face[q] : 0;
    if (!(r > 0)) continue;
    if (r > f.r_out) parts.push(t("n = {n}: the plane of the disc at r = {r:.4g} M, beyond the edge of the disc ({e:.3g} M)", { n, r, e: f.r_out }));
    else if (r < f.r_in) parts.push(t("n = {n}: the plane of the disc at r = {r:.4g} M, inside the edge of the disc ({e:.4g} M), no gas", { n, r, e: f.r_in }));
    else if (face > 0) parts.push(t("n = {n}: the disc at r = {r:.4g} M, side +z, g = {g:.4g}", { n, r, g }));
    else if (face < 0) parts.push(t("n = {n}: the disc at r = {r:.4g} M, side −z, g = {g:.4g}", { n, r, g }));
    else parts.push(t("n = {n}: the disc at r = {r:.4g} M, g = {g:.4g}", { n, r, g }));
  }
  return parts.join(" · ");
}

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin" });
  let H = null, curve = null, img = null, mode = "seen";
  // images by their number: rows arrive in order (accumulative "rows" messages); the curve of the latest set-up
  let images = new Map(), curves = [], drawnKey = "";
  const win = createImageWindow({ title: t("The distant observer's screen: the computed image"), describe, overlay });
  env.center.append(win.el);
  const modeSel = el("select", { title: t("What to show on the screen (from the same computed data)") }, MODES.map(([v, label]) => el("option", { value: v }, label)));
  modeSel.onchange = () => { mode = modeSel.value; drawnKey = ""; draw(); };
  const holeBox = el("div", { class: "kv" }), imgBox = el("div", {}), ehtBox = el("div", {});
  const rightPanels = [panel(t("Black hole"), holeBox), panel(t("Screen"), el("div", {}, modeSel, imgBox)),
                       panel(t("Scene layers"), env.layersPanel)];

  function curveAt(seq) { for (let k = curves.length - 1; k >= 0; k--) if (curves[k].seq <= seq) return curves[k]; return null; }

  function overlay(g, geom, meta) {
    const c = curveAt(meta.seq);
    if (!c) return;
    // the reference curve only over the rows the run has computed (review B5-kerr-v15 K10)
    g.save(); g.beginPath(); g.rect(geom.left, geom.top, geom.pw, geom.ph * Math.min(1, meta.rows_shown / meta.shape[0])); g.clip();
    const [a0, a1] = meta.camera.alpha, [b0, b1] = meta.camera.beta;
    const X = (a) => geom.left + (a - a0) / (a1 - a0) * geom.pw, Y = (b) => geom.top + (b1 - b) / (b1 - b0) * geom.ph;
    const line = (A, B, color, dash) => {
      g.strokeStyle = color; g.lineWidth = 1.2; g.setLineDash(dash); g.beginPath();
      for (let k = 0; k < A.length; k++) { const x = X(A[k]), y = Y(B[k]); if (k) g.lineTo(x, y); else g.moveTo(x, y); }
      g.stroke(); g.setLineDash([]);
    };
    if (c.meta.metric !== "kerr") line(c.kerr_alpha, c.kerr_beta, "rgba(160,200,255,0.8)", [4, 3]);
    line(c.alpha, c.beta, c.meta.metric !== "kerr" ? "#ff8a3a" : "rgba(127,255,170,0.85)", c.meta.metric !== "kerr" ? [] : [5, 4]);
    g.restore();
  }

  function colourOf(I, cap, g, r, k, ny, W, nmax, Imax) {
    if (mode === "fate") return cap ? [70, 20, 20] : [30, 50, 80];
    if (mode === "order") {
      let best = -1, bv = 0;
      for (let n = 0; n <= nmax; n++) { const v = I[n * W * ny + k]; if (v > bv) { bv = v; best = n; } }
      if (best < 0) return cap ? [0, 0, 0] : [12, 14, 20];
      const s = Math.min(1, Math.sqrt(bv / Imax) * 1.5);
      return ORDER_RGB[best].map((c) => Math.round(c * (0.25 + 0.75 * s)));
    }
    if (mode === "redshift") {
      const gg = g[k];  // the direct image's g (n = 0)
      if (!(gg > 0)) return cap ? [0, 0, 0] : [12, 14, 20];
      const f = Math.max(0, Math.min(1, 0.5 + Math.log2(gg) / 2));  // g from 1/2 (red) to 2 (blue)
      return [Math.round(255 * (1 - f)), Math.round(120 + 80 * (1 - Math.abs(2 * f - 1))), Math.round(255 * f)];
    }
    let s = 0;
    for (let n = 0; n <= nmax; n++) s += I[n * W * ny + k];
    const v = Math.pow(Math.min(1, s / Imax), 0.5);
    return [Math.round(255 * Math.min(1, 1.2 * v)), Math.round(255 * Math.pow(v, 1.5)), Math.round(255 * Math.pow(v, 3) * 0.7)];
  }

  function draw() {
    if (!img) return;
    const key = `${img.seq}|${img.rows}|${mode}`;
    if (key === drawnKey) return;
    drawnKey = key;
    const { nx: W, ny, nmax } = img;
    // the brightness scale from the rows shown only: rows computed later must not change it (review B5-kerr-v15 K3:
    // through a key frame the image was scaled by rows not yet revealed); the 99.5th percentile of the lit pixels,
    // so that a few Doppler-boosted pixels do not leave the rest black (K17: the edge-on preset)
    const sums = [];
    for (let k = 0; k < img.rows * W; k++) {
      let v = 0;
      for (let n = 0; n <= nmax; n++) v += img.I[n * W * ny + k];
      if (v > 0) sums.push(v);
    }
    sums.sort((a, b) => a - b);
    const Imax = sums.length ? sums[Math.min(sums.length - 1, Math.floor(0.995 * (sums.length - 1)))] : 1;
    const rgb = new Uint8Array(3 * W * ny);
    for (let j = 0; j < ny; j++) for (let i = 0; i < W; i++) {
      const k = j * W + i;
      const c = j < img.rows ? colourOf(img.I, img.cap[k], img.g, img.r, k, ny, W, nmax, Imax) : [24, 26, 32];
      rgb[3 * k] = c[0]; rgb[3 * k + 1] = c[1]; rgb[3 * k + 2] = c[2];
    }
    const meta = { shape: [ny, W], seq: img.seq, mode, mode_label: MODES.find((m) => m[0] === mode)[1], rows_shown: img.rows,
                   camera: { kind: "screen", alpha: [-img.half, img.half], beta: [-img.half * ny / W, img.half * ny / W],
                             axis_label: t("α, M (along the screen; the hole's spin axis up)") } };
    win.setImage(meta, rgb, { cap: img.cap, I: img.I, g: img.g, r: img.r, face: img.face, rows: img.rows, ny, nmax, r_in: img.r_in, r_out: img.r_out },
                 img.rows < ny ? t("computing: {k:d} of {n:d} rows", { k: img.rows, n: ny }) : t("done: {w:d} × {h:d}", { w: W, h: ny }) + (img.device ? ` · ${img.device.device === "gpu" ? "GPU" : "CPU"}` : ""));
  }

  function addRows(m, b) {
    let im = images.get(m.seq);
    const { nx, ny, n_max: nmax } = m;
    if (!im) {
      im = { seq: m.seq, nx, ny, nmax, half: m.half, rows: 0, cap: new Uint8Array(nx * ny),
             I: new Float32Array((nmax + 1) * nx * ny), g: new Float32Array((nmax + 1) * nx * ny),
             r: new Float32Array((nmax + 1) * nx * ny), face: new Int8Array((nmax + 1) * nx * ny), device: null,
             r_in: m.r_in, r_out: m.r_out };
      images.set(m.seq, im);
    }
    const i0 = m.i0, i1 = m.i1, nr = i1 - i0;
    im.cap.set(b.cap, i0 * nx);
    for (let n = 0; n <= nmax; n++) {
      im.I.set(b.I.subarray(n * nr * nx, (n + 1) * nr * nx), n * ny * nx + i0 * nx);
      im.g.set(b.g.subarray(n * nr * nx, (n + 1) * nr * nx), n * ny * nx + i0 * nx);
      im.r.set(b.r.subarray(n * nr * nx, (n + 1) * nr * nx), n * ny * nx + i0 * nx);
      if (b.face) im.face.set(b.face.subarray(n * nr * nx, (n + 1) * nr * nx), n * ny * nx + i0 * nx);
    }
    im.rows = Math.max(im.rows, i1); im.device = m.device || im.device;
  }

  function drawHole() {
    if (!H) return;
    const h = H.hole, m = H.metric, k = h.kerr;  // k: Kerr with the same spin, for comparison in a "what if" world
    const cmp = (a, b) => (k ? t("{a} (Kerr: {b})", { a, b }) : a);
    fill(holeBox, el("span", {}, t("spin a/M")), el("span", { class: "mono" }, num(h.chi, 4)),
      el("span", {}, t("horizon r₊")), el("span", { class: "mono" }, `${num(h.r_plus, 6)} M`),
      el("span", {}, k ? t("equatorial photon orbits (of this metric)") : t("equatorial photon orbits")),
      el("span", { class: "mono" }, cmp(`${num(h.ph_pro, 5)} … ${num(h.ph_retro, 5)} M`, `${num(k && k.ph_pro, 5)} … ${num(k && k.ph_retro, 5)}`)),
      el("span", {}, k ? t("ISCO prograde / retrograde (of this metric)") : t("ISCO (prograde / retrograde)")),
      el("span", { class: "mono" }, cmp(`${num(h.isco_pro, 5)} / ${num(h.isco_retro, 5)} M`, `${num(k && k.isco_pro, 5)} / ${num(k && k.isco_retro, 5)}`)),
      el("span", {}, t("metric")), el("span", { class: m.kind === "kerr" ? "" : "warn" },
        m.kind === "kerr" ? t("Kerr (GR)") : t("Johannsen: α₁₂ = {a12:.3g}, α₁₃ = {a13:.3g}, α₂₂ = {a22:.3g}", { a12: m.a12, a13: m.a13, a22: m.a22 })));
  }
  function drawImgPanel() {
    const notes = [];
    if (H && H.metric.kind !== "kerr") notes.push(el("div", { class: "warn" }, t("In this metric the engine computes only the edge of the shadow (orange), from its photon orbits; the image of the disc is not computed. Dashed: the edge of the shadow of Kerr with the same spin.")));
    notes.push(el("div", { class: "help" }, t("Every pixel is a photon traced back: in the shadow it fell into the hole; outside, where it crossed the plane of the disc, n is the number of the crossing along the ray traced back. At a moderate inclination n = 0 is the direct image of the disc, n = 1 the lensing ring, n = 2 the photon ring; nearly edge-on (θ ≳ {deg}°) the rays below the centre first cross the plane far beyond the edge of the disc, and the lower face of the disc is seen directly as n = 1. Dashed: Bardeen's critical curve (the edge of the shadow by the formula), where the rows are already computed. Point at the image to see the radius, the side of the disc and the redshift of every crossing.", { deg: 75 })));
    notes.push(el("div", { class: "help" }, t("The brightness is a source model: a thin disc, each crossing gives g⁴J(r) (bolometric brightness), without a correction for the thickness of the disc and the ray's path length in it (Gralla, Lupsasca & Marrone 2020 use a factor {f} for n ≥ 1, Chael et al. 2021 g³ and 2/3); the scale is percentile {p} of the computed pixels.", { f: 1.5, p: 99.5 })));
    if (mode === "order") notes.push(el("div", { class: "help" }, t("Orange: the crossing n = 0, blue: n = 1, white: n = 2 (the brightest contribution in the pixel).")));
    if (mode === "redshift") notes.push(el("div", { class: "help" }, t("g of the direct image: red, g = 1/2 (the gas recedes from the observer); blue, g = 2 (it approaches); g⁴ changes the brightness by a factor of 256.")));
    fill(imgBox, notes);
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {},
      el("h4", {}, t("The shadow of a Kerr black hole")),
      el("p", {}, t("The observer is far away, at an angle θ to the spin axis. Every pixel of the observer's screen is a photon traced back in closed form (elliptic functions, Gralla & Lupsasca 2020): either it came out of the hole (this does not happen, so that direction is dark: the shadow), or it came from far away, crossing on its way the equatorial plane, where a thin disc of gas shines. The brightness of a pixel is the sum of g⁴J(r) over the crossings: g is the redshift of the gas (rotation and gravity), J(r) the emission of the disc (a source model).")),
      el("p", {}, t("The shadow is bounded by the critical curve: the rays on it wind onto the spherical photon orbits. The images of the disc n = 1, 2, … (n is the number of the crossing of the disc's plane along the ray traced back, the half-periods of the motion in θ) approach it by a factor e^γ with each order (γ is the orbit's Lyapunov exponent). When the image is complete, the run checks: the edge of the shadow by the tracer itself against Bardeen's formula; the captured pixels against the inside of the curve; the demagnification of the rings against e^(−γ); at a = 0, the radius √27 M; the size of the shadow δ from the tracer's edge against the formula and against EHT: for Sgr A* the size itself (EHT 2022), for M87* the deviation from Kerr's (EHT 2019 calibrated the ring with Kerr models).")),
      el("p", {}, t("A “what if” world: the Johannsen metric (α = 0 is Kerr). The engine computes the edge of its shadow from its photon orbits, its circular orbits and ergosphere, and δ against the EHT bounds; the image of the disc is not computed in it.")),
      el("p", {}, t("The scene is stationary: the picture does not change in time; the screen's rows are computed as the world's time goes on, and a change of the set-up starts a new image."))),
    reset() { env.reset(); H = null; curve = null; img = null; images = new Map(); curves = []; drawnKey = ""; },
    // key frames (player.js): the environment's own; images by number (rows only grow; a key frame keeps how many
    // rows each had), the curves of the set-ups (a list that only grows)
    snapshot() {
      return { env: env.snapshot(), curves: curves.length, rows: new Map([...images].map(([s, im]) => [s, im.rows])) };
    },
    restore(k) {
      env.restore(k.env);
      curves.length = k.curves;
      for (const [s, im] of [...images]) { if (k.rows.has(s)) im.rows = k.rows.get(s); else images.delete(s); }
      img = null; drawnKey = "";
    },
    onHeader(meta) { H = meta; env.onHeader(meta); drawHole(); drawImgPanel(); },
    onMessage(meta, blobs) {
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "curve") { curves.push({ seq: meta.seq, meta, alpha: blobs.alpha, beta: blobs.beta, kerr_alpha: blobs.kerr_alpha, kerr_beta: blobs.kerr_beta }); }
      else if (meta.type === "rows") addRows(meta, blobs);
    },
    render(frame) {
      if (!H || !frame) return;
      const im = images.get(frame.seq);
      if (im && im.rows !== (img && img.seq === frame.seq ? img.rows : -1)) drawnKey = "";
      img = im ? { ...im, rows: Math.min(im.rows, frame.rows) } : (H.metric.kind !== "kerr" ? blankFor(frame.seq) : null);
      draw();
      drawImgPanel();
      env.scene.requestRender();
    },
  };

  // a "what if" world has no image: an empty screen of the curve's size, so that the curves can be drawn on it
  function blankFor(seq) {
    const c = curveAt(seq);
    if (!c) return null;
    const n = c.meta.n;
    return { seq, nx: n, ny: n, nmax: 0, half: c.meta.half, rows: n, cap: new Uint8Array(n * n), I: new Float32Array(n * n),
             g: new Float32Array(n * n), r: new Float32Array(n * n), device: null };
  }
}
