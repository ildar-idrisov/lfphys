// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The view of the 3-D wave-function worlds (u40 hydrogen, u41 quarkonium; server: lfviz/orbitals3d.py), over the
// shared 3-D environment (env3d.js): the cloud |ψ|², the probability current, the slice planes, and the panels
// "State", "Radial distribution" and "Energy levels". A superposition's cloud, current and slices come per
// phase of its period (`bin`), revealed by the run as its time reaches them; a frame names the phase it shows, so
// that a viewer who scrolls back sees the cloud of that moment. Drawing only: every value comes from the run.
import { t } from "./i18n.js";
import { el, fill, num, panel, css, fresh2d } from "./ui.js";
import { createEnv3D } from "./env3d.js";
import { inflate } from "./imagewin.js";

export function createOrbitView(ctx, { describeAtom = () => [], levelColumns = ["s", "p", "d", "f"], energyName = "E",
                                       help = [] } = {}) {
  // the cloud's amplitude has 8 bits: |ψ|²/peak below (1/255)² ≈ 1.5e-5 is drawn as zero; the log scale starts there
  const env = createEnv3D(ctx, { logFloor: () => 1.5e-5, scale: "sqrt" });
  const stateBox = el("div", {}), phaseBox = el("div", { class: "kv" });
  const cvRad = el("canvas", { style: { width: "100%", height: "150px", display: "block" } });
  const cvLev = el("canvas", { style: { width: "100%", height: "190px", display: "block" } });
  const rightPanels = [panel(t("State"), el("div", {}, stateBox, phaseBox)),
                       panel(t("Radial distribution r²|R(r)|²"), cvRad), panel(t("Energy levels"), cvLev),
                       panel(t("Scene layers"), env.layersPanel), panel(t("Slice: position and tilt"), env.planePanel)];
  let H = null, radial = null, want = 0;
  let clouds = new Map(), vecs = new Map(), slices = new Map(), shown = { cloud: -1, vec: -1 };
  const COLORS = ["#ff8a1f", "#22b8ff"];
  for (const cv of [cvRad, cvLev]) new ResizeObserver(() => { drawRadial(); drawLevels(); }).observe(cv);

  // --- the cloud, the current and the slices of the phase a frame names --------------------------------------------
  // the cloud is kept as sent (8-bit amplitudes √(|ψ|²/peak)·255): the scene paints a new phase through a 256-entry
  // table, without a pass over the voxels in floats (review UX-3d A17)
  async function storeCloud(meta, blobs) {
    try {
      const q = new Uint8Array(await inflate(blobs.data));
      clouds.set(meta.bin, { meta, data: q });
      if (meta.bin === want || shown.cloud < 0) showPhase(true);
    } catch (e) { console.error(e); }
  }
  function nearest(map, k) {  // the phase k, or the last one revealed before it (never a later one)
    if (map.has(k)) return k;
    let best = -1;
    for (const b of map.keys()) if (b <= k && b > best) best = b;
    return best >= 0 ? best : (map.size ? Math.min(...map.keys()) : -1);
  }
  function showPhase(force = false) {
    const kc = nearest(clouds, want);
    if (kc >= 0 && (force || kc !== shown.cloud)) {
      const c = clouds.get(kc);
      // the cloud's optical depth τ = 4 along its densest line of sight, in every state (review UX-3d A10: the header's one
      // density per ångström made a compact 1s cloud nearly invisible and a large one dense)
      if (!(shown.cloud >= 0 && env.scene.updateVolume("cloud", c.data, { amp8: true }))) env.scene.setVolume("cloud", c.meta.dims, c.data, { amp8: true, tau: 4 });
      shown.cloud = kc;
    }
    const kv = nearest(vecs, want);
    if (kv >= 0 && (force || kv !== shown.vec)) {
      // the glyphs of the same number are updated in place, others replaced (the scene frees the old ones)
      const v = vecs.get(kv), old = env.scene.layers().find((L) => L.id === v.meta.id);
      const thr = old && old.obj.userData ? old.obj.userData.threshold : undefined;
      env.scene.setVectors(v.meta.id, v.pos, v.vec);
      if (thr !== undefined) env.scene.setVectorThreshold(v.meta.id, thr);
      shown.vec = kv;
    }
    for (const [pid, P] of slices) {
      const ks = nearest(P.bins, want);
      if (ks >= 0 && (force || ks !== P.shown)) {
        const s = P.bins.get(ks);
        env.onMessage(s.meta, s.blobs);
        P.shown = ks;
      }
    }
  }
  function storeSlice(meta, blobs) {
    let P = slices.get(meta.id);
    if (!P || meta.rev > P.rev) { P = { rev: meta.rev, bins: new Map(), shown: -1 }; slices.set(meta.id, P); }
    if (meta.rev < P.rev) return;
    P.bins.set(meta.bin, { meta, blobs });
    if (meta.bin === want || meta.bin === nearest(P.bins, want)) { env.onMessage(meta, blobs); P.shown = meta.bin; }
  }

  // --- panels ------------------------------------------------------------------------------------------------------------
  function drawState() {
    if (!H) return;
    const unit = t(H.energy_unit), rows = [];
    for (const [i, s] of (H.states || []).entries()) {
      rows.push(el("div", { style: { marginTop: i ? "6px" : "0" } },
        H.states.length > 1 ? el("span", { class: "sw-chip", style: { background: COLORS[i] } }, String(i + 1)) : null,
        el("b", {}, " " + t(s.label)), el("span", { class: "muted" }, s.real ? " " + t("(real)") : (s.l ? " " + t("(complex, e^{imφ})") : ""))));
      const kv = [el("span", {}, t(energyName)), el("span", { class: "mono" }, `${num(s.E, 7)} ${unit}`)];
      if (H.states.length > 1) kv.push(el("span", {}, t("weight |c|², phase")), el("span", { class: "mono" }, `${num(s.w, 4)}, ${num(s.phase_deg, 4)}°`));
      kv.push(el("span", {}, t("⟨r⟩ (quadrature)")), el("span", { class: "mono" }, `${num(s.r_mean_quad, 7)} ${t(H.scene3d.units)}` + (s.r_mean !== undefined && s.r_mean !== null ? " · " + t("formula {v}", { v: num(s.r_mean, 7) }) : "")));
      for (const [k, v, u] of s.extra || []) kv.push(el("span", {}, t(k)), el("span", { class: "mono" }, `${typeof v === "number" ? num(v, 6) : t(v)} ${t(u)}`));
      rows.push(el("div", { class: "kv" }, kv));
    }
    fill(stateBox, describeAtom(H), rows);
  }
  function drawPhase(meta, tNow) {
    if (!H) return;
    if (!(H.nb > 1)) { fill(phaseBox, el("span", {}, t("time")), el("span", { class: "muted" }, t("a stationary state: the cloud does not change, only the phase of ψ turns"))); return; }
    // the phases the run had revealed by this frame's moment (a frame of the record may be an earlier one)
    const tt = tNow ?? (meta ? meta.t : undefined);
    const k = meta ? meta.bin : 0, have = Number.isFinite(tt) ? Math.min(H.nb, Math.floor(tt / H.period * H.nb + 1e-9) + 1) : clouds.size;
    fill(phaseBox, el("span", {}, t("Bohr period T")), el("span", { class: "mono" }, `${t("{t:.5g} s", { t: H.period })} (ħω = ${num(H.omega_E, 6)} ${t(H.energy_unit)})`),
      el("span", {}, t("phase in the picture")), el("span", { class: "mono" }, t("{k:d} of {n:d}", { k: k + 1, n: H.nb }) + (Number.isFinite(tt) ? ` · t/T = ${num(tt / H.period, 4)}` : "")),
      el("span", {}, t("phases revealed")), el("span", { class: have < H.nb ? "warn" : "muted" }, have < H.nb ? t("{n:d} by this moment: the others when the time reaches them", { n: have }) : t("all: from here on the cloud repeats")));
  }
  function sizeCanvas(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth, Hh = cv.clientHeight;
    if (!W || !Hh) return null;
    if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(Hh * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr);
    g.fillStyle = css("--canvas") || "#0b0e14"; g.fillRect(0, 0, W, Hh);
    return { g, W, H: Hh };
  }
  function drawRadial() {
    const c = sizeCanvas(cvRad); if (!c || !radial || !H) return;
    const { g, W, H: Hh } = c, { meta, P } = radial, n = meta.count, ns = meta.states;
    const left = 34, right = 8, top = 8, bot = 22, rmax = meta.r_max;
    let pmax = 0; for (let i = 0; i < P.length; i++) pmax = Math.max(pmax, P[i]);
    const X = (r) => left + (W - left - right) * r / rmax, Y = (p) => top + (Hh - top - bot) * (1 - p / (pmax || 1));
    g.strokeStyle = css("--grid") || "#333"; g.strokeRect(left, top, W - left - right, Hh - top - bot);
    for (let s = 0; s < ns; s++) {
      g.strokeStyle = ns > 1 ? COLORS[s] : (css("--ink") || "#ddd"); g.lineWidth = 1.5; g.beginPath();
      for (let i = 0; i < n; i++) { const x = X(rmax * i / (n - 1)), y = Y(P[s * n + i]); if (i) g.lineTo(x, y); else g.moveTo(x, y); }
      g.stroke();
      const rm = (H.states[s] || {}).r_mean_quad;
      if (rm) { g.setLineDash([4, 3]); g.beginPath(); g.moveTo(X(rm), top); g.lineTo(X(rm), Hh - bot); g.stroke(); g.setLineDash([]); }
    }
    g.fillStyle = css("--muted") || "#999"; g.font = "10px system-ui";
    for (let q = 0; q <= 4; q++) g.fillText(num(rmax * q / 4, 3), X(rmax * q / 4) - 6, Hh - 9);
    g.fillText(`r, ${t(meta.units)}   ` + t("(dashes — ⟨r⟩)"), left + 4, Hh - 1);
  }
  function drawLevels() {
    const c = sizeCanvas(cvLev); if (!c || !H) return;
    const { g, W, H: Hh } = c, L = H.levels || [];
    if (!L.length) return;
    const columns = H.level_columns || levelColumns, cols = columns.length, left = 52, right = 8, top = 16, bot = 8, cw = (W - left - right) / cols;
    let lo = Infinity, hi = -Infinity;
    for (const v of L) { lo = Math.min(lo, v.E, v.data ?? v.E); hi = Math.max(hi, v.E, v.data ?? v.E); }
    if (H.levels_top !== undefined) hi = Math.max(hi, H.levels_top);
    const pad = 0.04 * (hi - lo || 1), Y = (E) => top + (Hh - top - bot) * (1 - (E - lo + pad) / (hi - lo + 2 * pad));
    g.font = "10px system-ui"; g.fillStyle = css("--muted") || "#999";
    columns.forEach((c, i) => g.fillText(t(c), left + cw * i + cw / 2 - 4, 11));
    const keys = (H.states || []).map((s) => s.key);
    const at = {};
    for (const v of L) {
      const x0 = left + cw * v.col + 6, x1 = left + cw * (v.col + 1) - 6, y = Y(v.E), k = keys.indexOf(v.key);
      g.strokeStyle = k >= 0 ? (keys.length > 1 ? COLORS[k] : (css("--accent") || "#5aa2ff")) : (css("--ink") || "#ccc");
      g.lineWidth = k >= 0 ? 3 : 1; g.beginPath(); g.moveTo(x0, y); g.lineTo(x1, y); g.stroke();
      if (v.data !== undefined && v.data !== null) {  // a measured value (a model's world): a tick for comparison
        g.strokeStyle = css("--muted") || "#999"; g.setLineDash([2, 2]); g.lineWidth = 1;
        g.beginPath(); g.moveTo(x0, Y(v.data)); g.lineTo(x1, Y(v.data)); g.stroke(); g.setLineDash([]);
      }
      if (v.label) { const lab = t(v.label); g.fillStyle = css("--muted") || "#999"; g.fillText(lab, x1 - g.measureText(lab).width, y - 2); }
      at[v.key] = [(x0 + x1) / 2, y];
    }
    g.fillStyle = css("--muted") || "#999";
    g.fillText(`${num(hi, 4)}`, 2, Y(hi) + 3); g.fillText(`${num(lo, 4)}`, 2, Y(lo) + 3); g.fillText(t(H.energy_unit), 2, Hh / 2);
    if (keys.length === 2 && at[keys[0]] && at[keys[1]] && keys[0] !== keys[1]) {  // the Bohr frequency of the pair
      const [a, b] = [at[keys[0]], at[keys[1]]];
      g.strokeStyle = css("--ink") || "#ddd"; g.lineWidth = 1; g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
      g.fillStyle = css("--ink") || "#ddd"; g.fillText(`ħω = ${num(H.omega_E, 4)} ${t(H.energy_unit)}`, Math.min(a[0], b[0]) + 4, (a[1] + b[1]) / 2);
    }
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, ...help.map((p, i) => (i === 0 ? el("h4", {}, t(p)) : el("p", {}, t(p))))),
    reset() { env.reset(); H = null; radial = null; want = 0; clouds = new Map(); vecs = new Map(); slices = new Map(); shown = { cloud: -1, vec: -1 }; },
    onHeader(meta) {
      env.onHeader(meta); H = meta; clouds = new Map(); vecs = new Map(); slices = new Map(); shown = { cloud: -1, vec: -1 }; want = 0;
      drawState(); drawPhase(null); drawLevels();
    },
    onMessage(meta, blobs) {
      if (meta.type === "cloud") { storeCloud(meta, blobs); drawPhase(null); return; }
      if (meta.type === "vectors" && meta.bin !== undefined) { vecs.set(meta.bin, { meta, pos: blobs.pos, vec: blobs.vec }); if (meta.bin === want || shown.vec < 0) showPhase(); return; }
      if (meta.type === "slice" && meta.bin !== undefined && !meta.preview) { storeSlice(meta, blobs); return; }
      if (meta.type === "radial") { radial = { meta, P: blobs.P }; drawRadial(); return; }
      env.onMessage(meta, blobs);
    },
    render(meta, tt) {
      if (!H || !meta) return;
      if (meta.bin !== want) { want = meta.bin; showPhase(); }
      drawPhase(meta, tt);
      env.scene.requestRender();
    },
  };
}
