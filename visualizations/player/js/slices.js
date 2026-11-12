// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Slice windows of the 3-D environment (owner, 2026-10-27): one window per slice plane (up to three), next to the 3-D
// view, in the plane's colour; selecting or pointing at a window highlights its plane in 3-D. Each window shows what
// the run computed on that plane (a wave: intensity, amplitude, log or phase; any other field, named by the slice's
// `quantity`: linear or log), its axes in physical units (the slice's `units`), how it was computed and checked, the
// values under the cursor, and can export its data (CSV). While a plane is dragged, a preview is shown, marked as such.
import { el, fill, num, fresh2d } from "./ui.js";
import { LUT, PLANE_COLORS, transfer } from "./scene3d.js";

const MODES = [["sqrt", "амплитуда"], ["lin", "интенсивность"], ["log", "логарифм"], ["phase", "фаза"]];
const FIELD_MODES = [["lin", "линейно"], ["log", "логарифм"]];  // a field that is not a wave (meta.quantity)
const COORDS = ["x", "y", "z"];

function phaseColor(a) {  // cyclic: hue from the phase
  const h = ((a / (2 * Math.PI)) % 1 + 1) % 1, i = Math.floor(h * 6), f = h * 6 - i;
  const q = 1 - f, rgb = [[1, f, 0], [q, 1, 0], [0, 1, f], [0, q, 1], [f, 0, 1], [1, 0, q]][i % 6];
  return rgb.map((c) => Math.round(255 * (0.15 + 0.85 * c)));
}

// an in-plane direction as a physical axis: a coordinate when it runs along one (with its sign), else a direction
function axisOf(d, o, units = "мкм", names = COORDS) {
  for (const [i, a] of [[0, names[0]], [1, names[1]], [2, names[2]]]) {
    if (Math.abs(Math.abs(d[i]) - 1) < 1e-9) return { name: `${a}, ${units}`, at: (p) => o[i] + p * d[i], sign: Math.sign(d[i]) };
  }
  const dir = `(${num(d[0], 2)}, ${num(d[1], 2)}, ${num(d[2], 2)})`;
  return { name: `от центра плоскости вдоль ${dir}, ${units}`, at: (p) => p, sign: 1 };
}

// A one-shot pick (the playground's «⌖ указать место», review UX-ui U4): the next click in any slice window gives the
// physical point under the pointer to `cb(point, "window")` instead of selecting the window; `armPick(null)` disarms.
let pickCb = null;
export function armPick(cb) {
  pickCb = cb || null;
  document.body.classList.toggle("picking", !!pickCb);
}
export function picking() { return !!pickCb; }

// Direct manipulation in the windows (plan P16.2): one manipulator for every window of the page (the playground's),
// given a window's helper on a press (down(win, e) -> true takes the gesture; move, up, cancel; hover(win, e) -> a
// cursor), and one overlay of the framework drawn over each window after the world's own (the selected object, the
// ghost of a drag). The helper: {id, plane: {origin, u, v, normal}, point(e) -> the physical point under the pointer
// (null outside the drawn slice), toCanvas(P) -> [x, y] in the canvas's CSS pixels, unitPx: CSS pixels per length
// unit, el: the canvas}.
let winManip = null, frameOverlay = null;
const allWindows = new Set();
export function setWindowManipulator(m) { winManip = m || null; }
// whether window `id` shows the world's own plane (a 2-D world's: never removed; its Delete belongs to the scene's
// selected object: review LB1-p02-ux X2)
export function isFixedWindow(id) { for (const api of allWindows) if (api.isFixed(id)) return true; return false; }
export function setFrameOverlay(fn) { frameOverlay = fn || null; for (const api of allWindows) api.redraw(); }
export function redrawWindows() { for (const api of allWindows) api.redraw(); }

export function createSliceWindows({ onSelect, onHighlight, onRemove } = {}) {
  const root = el("div", { class: "s3d-windows" });
  const W = new Map();
  let selected = null;

  function make(id) {
    const color = PLANE_COLORS[id];
    const mode = el("select", { title: "Что показывать" }, MODES.map(([v, t]) => el("option", { value: v }, t)));
    const title = el("span", { class: "sw-title" });
    const csv = el("button", { title: "Скачать данные среза (CSV: s, t, x, y, z, I/Iпик, фаза)" }, "CSV");
    const del = el("button", { title: "Убрать срез" }, "✕");
    const head = el("div", { class: "sw-head" }, el("span", { class: "sw-chip", style: { background: color } }, String(id)), title, el("span", { class: "grow" }), mode, csv, del);
    const cv = el("canvas", { class: "sw-canvas" });
    const status = el("div", { class: "sw-status" });
    const readout = el("div", { class: "sw-readout mono" }, "наведите на срез");
    const box = el("div", { class: "slicewin", style: { borderColor: color } }, head, cv, status, readout);
    const w = { id, box, cv, title, status, readout, mode, data: null, preview: null, geom: null, busy: "", del, overlay: null };
    // a click selects the window, unless it was a gesture on an object of the window (the manipulator took it: the
    // object is the selection then, and its Delete removes it; review LB1-p02-ux X2)
    let took = false;
    box.addEventListener("pointerdown", () => { took = false; }, true);
    box.addEventListener("click", () => { if (took) { took = false; return; } select(id); onSelect && onSelect(id); });
    box.addEventListener("mouseenter", () => onHighlight && onHighlight(id));
    box.addEventListener("mouseleave", () => onHighlight && onHighlight(null));
    mode.onchange = () => draw(w);
    del.onclick = (e) => { e.stopPropagation(); onRemove && onRemove(id); };
    csv.onclick = (e) => { e.stopPropagation(); exportCsv(w); };
    cv.addEventListener("mousemove", (e) => hover(w, e));
    // a gesture on an object of the window is the manipulator's (the window's own click still selects the window)
    let gest = null;
    cv.addEventListener("pointerdown", (e) => {
      if (!winManip || pickCb || e.button !== 0 || !w.geom) return;
      const h = helper(w);
      if (!winManip.down(h, e)) return;
      took = true;
      gest = { h, id: e.pointerId };
      e.preventDefault();
      const a = document.activeElement;  // the keys (Esc, Delete) go to the object, not to a field left focused
      if (a && a !== document.body && /^(INPUT|SELECT|TEXTAREA)$/.test(a.tagName)) a.blur();
      try { cv.setPointerCapture(e.pointerId); } catch (err) { /* a synthetic pointer */ }
    });
    cv.addEventListener("pointermove", (e) => {
      if (gest) { winManip.move(gest.h, e); return; }
      if (winManip && winManip.hover && !e.buttons && w.geom) { const c = winManip.hover(helper(w), e) || ""; if (cv.style.cursor !== c) cv.style.cursor = c; }
    });
    const end = (e, cancelled) => {
      if (!gest) return;
      const g = gest; gest = null;
      try { cv.releasePointerCapture(e.pointerId); } catch (err) { /* released already */ }
      if (cancelled) winManip.cancel(g.h); else winManip.up(g.h, e);
    };
    cv.addEventListener("pointerup", (e) => end(e, false));
    cv.addEventListener("pointercancel", (e) => end(e, true));
    cv.addEventListener("click", (e) => {
      if (!pickCb) return;
      const P = pointAt(w, e);
      if (!P) return;
      e.stopPropagation();
      const cb = pickCb;
      armPick(null);
      cb(P, "window");
    }, true);
    cv.addEventListener("mouseleave", () => { w.readout.textContent = "наведите на срез"; });
    new ResizeObserver(() => draw(w)).observe(cv);
    W.set(id, w);
    return w;
  }

  function sync(planes) {
    const ids = new Set(planes.map((p) => p.id));
    for (const [id, w] of W) if (!ids.has(id)) { w.box.remove(); W.delete(id); }
    for (const p of [...planes].sort((a, b) => a.id - b.id)) {
      const w = W.get(p.id) || make(p.id);
      w.plane = p;
      w.title.textContent = `Срез ${p.id}: ${p.label}`;
      if (!w.box.parentNode || w.box.parentNode !== root) root.append(w.box);
    }
    [...root.children].sort((a, b) => a.dataset.id - b.dataset.id);
    root.style.display = W.size ? "" : "none";
    for (const w of W.values()) w.box.classList.toggle("sel", w.id === selected);
  }

  function setModes(w, meta) {  // a wave's modes, or a field's (named by meta.quantity)
    const want = meta.quantity ? FIELD_MODES : MODES;
    if (w.modes === want) return;
    w.modes = want;
    fill(w.mode, want.map(([v, t]) => el("option", { value: v }, t)));
  }
  function setSlice(id, meta, blobs) {
    const w = W.get(id) || make(id);
    setModes(w, meta);
    w.data = { meta, I: blobs.I, phase: blobs.phase };
    w.preview = null; w.busy = "";
    w.del.style.display = meta.fixed ? "none" : "";  // a world's own plane (e.g. a 2-D world's): not removable
    if (meta.title) w.title.textContent = meta.title;
    if (!w.box.parentNode) root.append(w.box);
    root.style.display = "";
    draw(w);
  }
  function setPreview(id, preview) {  // {meta-like geometry, I} from the volume, while dragging
    const w = W.get(id); if (!w) return;
    setModes(w, preview.meta);
    w.preview = preview; draw(w);
  }
  function setBusy(id, text) { const w = W.get(id); if (w) { w.busy = text; draw(w); } }
  function select(id) { selected = id; for (const w of W.values()) w.box.classList.toggle("sel", w.id === id); }

  function geometry(d) {
    const m = d.meta, [ns, nt] = [m.s[2], m.tt[2]];
    const longi = m.depth !== false && Math.abs(m.v[2]) > 0.5;  // the depth (z) runs along t: draw it horizontally
    return { m, ns, nt, longi, units: m.units || "мкм", names: m.coord_names || COORDS };
  }

  function draw(w) {
    const d = w.preview || w.data;
    const cv = w.cv, dpr = Math.min(window.devicePixelRatio || 1, 2);
    const Wc = cv.clientWidth, Hc = cv.clientHeight;
    if (!Wc || !Hc) return;
    if (cv.width !== Math.round(Wc * dpr) || cv.height !== Math.round(Hc * dpr)) { cv.width = Math.round(Wc * dpr); cv.height = Math.round(Hc * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr);
    g.fillStyle = "#0b0e14"; g.fillRect(0, 0, Wc, Hc);
    statusLine(w);
    if (!d) return;
    const { m, ns, nt, longi, units, names } = geometry(d);
    const mode = w.mode.value, floor = Math.max(1e-6, (3 * (m.window_est || 0)) ** 2);
    // axes in physical coordinates (review C2): horizontal = t (the depth) for longitudinal planes, else s
    const aS = axisOf(m.u, m.origin, units, names), aT = axisOf(m.v, m.origin, units, names);
    const zOfT = (t) => m.origin[2] + t * m.v[2];
    const H_ = longi ? { ax: { name: `${names[2]}, ${units}`, at: zOfT, sign: 1 }, p0: m.tt[0], p1: m.tt[1], n: nt } : { ax: aS, p0: m.s[0], p1: m.s[1], n: ns };
    const V_ = longi ? { ax: aS, p0: m.s[0], p1: m.s[1], n: ns } : { ax: aT, p0: m.tt[0], p1: m.tt[1], n: nt };
    const flipH = H_.ax.sign < 0, flipV = V_.ax.sign < 0;  // draw so that the coordinate grows to the right / upwards
    const nh = H_.n, nv = V_.n;
    // the image of the data is made once per data and mode (a redraw for an overlay — a drag's ghost — reuses it)
    const imgKey = `${mode}|${floor}|${flipH}|${flipV}|${longi}`;
    let off = w.offFor === d && w.offKey === imgKey ? w.off : null;
    if (!off) {
    off = document.createElement("canvas"); off.width = nh; off.height = nv;
    const id = off.getContext("2d").createImageData(nh, nv);
    for (let it = 0; it < nt; it++) for (let is = 0; is < ns; is++) {
      const k = it * ns + is, v = d.I[k];
      let ih = longi ? it : is, iv = longi ? is : it;
      if (flipH) ih = nh - 1 - ih;
      if (flipV) iv = nv - 1 - iv;
      const o = 4 * ((nv - 1 - iv) * nh + ih);
      if (!(v >= 0)) { id.data[o] = 30; id.data[o + 1] = 34; id.data[o + 2] = 40; id.data[o + 3] = 255; continue; }
      let rgb;
      if (mode === "phase" && d.phase && !w.preview) {
        const c = phaseColor(d.phase[k]), b = Math.sqrt(Math.min(1, v));
        rgb = c.map((x) => x * (0.25 + 0.75 * b));
      } else {
        const c = Math.round(255 * transfer(v, mode === "phase" ? "sqrt" : mode, floor));
        rgb = [LUT[3 * c], LUT[3 * c + 1], LUT[3 * c + 2]];
      }
      id.data[o] = rgb[0]; id.data[o + 1] = rgb[1]; id.data[o + 2] = rgb[2]; id.data[o + 3] = 255;
    }
    off.getContext("2d").putImageData(id, 0, 0);
    w.off = off; w.offFor = d; w.offKey = imgKey;
    }
    const left = 44, right = 8, top = 6, bot = 28;
    const hv = [H_.ax.at(H_.p0), H_.ax.at(H_.p1)].sort((a, b) => a - b), vv = [V_.ax.at(V_.p0), V_.ax.at(V_.p1)].sort((a, b) => a - b);
    // the window takes the height its image needs at the column's width (review B3-14: a tall window left two thirds
    // of it empty); the column scrolls when several windows need more than it has
    const need = Math.round(Math.abs(V_.p1 - V_.p0) * (Wc - left - right) / Math.abs(H_.p1 - H_.p0)) + top + bot;
    const want = Math.max(140, Math.min(900, need));
    if (Math.abs(Hc - want) > 2) { w.box.style.flex = "0 0 auto"; cv.style.flex = "0 0 auto"; cv.style.height = `${want}px`; return; }
    const sc = Math.min((Wc - left - right) / Math.abs(H_.p1 - H_.p0), (Hc - top - bot) / Math.abs(V_.p1 - V_.p0));
    const pw = Math.abs(H_.p1 - H_.p0) * sc, ph = Math.abs(V_.p1 - V_.p0) * sc;
    g.imageSmoothingEnabled = true;
    g.drawImage(off, left, top, pw, ph);
    // the zone next to the aperture (z < z_near): hatched, along whichever axis the depth varies (review C11)
    if (m.z_near > 0 && Math.abs(m.v[2]) > 1e-9) {
      const ta = (m.z_near - m.origin[2]) / m.v[2];  // t where z = z_near; z < z_near for t < ta (v_z > 0)
      const f = (ta - m.tt[0]) / (m.tt[1] - m.tt[0]);
      if (f > 0) {
        const ff = Math.min(1, f);
        g.save(); g.beginPath();
        if (longi) g.rect(left + (flipH ? pw * (1 - ff) : 0), top, Math.max(pw * ff, 2), ph);
        else g.rect(left, flipV ? top : top + ph * (1 - ff), pw, Math.max(ph * ff, 2));
        g.clip(); g.strokeStyle = "rgba(255,255,255,0.5)";
        for (let y = -pw; y < ph + pw; y += 6) { g.beginPath(); g.moveTo(left, top + y); g.lineTo(left + pw, top + y - pw); g.stroke(); }
        g.restore();
      }
    }
    g.strokeStyle = "#3a4350"; g.strokeRect(left, top, pw, ph);
    g.fillStyle = "#9aa3ad"; g.font = "10px system-ui";
    // round ticks (steps 1, 2, 5 × 10ⁿ; review LB1-p02-ux X13), every label inside the window (the last one too)
    const ticksOf = (a, b, px, gap) => {
      if (!(b > a)) return { step: 0, values: [] };
      const raw = (b - a) / Math.max(1, px / gap), e = 10 ** Math.floor(Math.log10(raw)), m = raw / e;
      const step = (m <= 1 ? 1 : m <= 2 ? 2 : m <= 5 ? 5 : 10) * e, values = [];  // rounded up: labels never closer than `gap`
      for (let k = Math.ceil(a / step - 1e-9); k * step <= b + 1e-9 * step; k++) values.push(Math.abs(k) < 1e-12 ? 0 : k * step);
      return { step, values };
    };
    const lab = (v, step) => num(Math.abs(v) < 1e-6 * step ? 0 : v, 4);
    const th = ticksOf(hv[0], hv[1], pw, 64), tv = ticksOf(vv[0], vv[1], ph, 36);
    let lastRight = 0;
    for (const v of th.values) {
      const x = left + (v - hv[0]) / (hv[1] - hv[0]) * pw, t = lab(v, th.step), tw = g.measureText(t).width;
      const x0 = Math.min(Math.max(x - tw / 2, 1), Wc - tw - 2);
      g.fillRect(x - 0.5, top + ph, 1, 3);
      g.fillText(t, x0, top + ph + 13);
      lastRight = Math.max(lastRight, x0 + tw);
    }
    for (const v of tv.values) {
      const y = top + ph - (v - vv[0]) / (vv[1] - vv[0]) * ph, t = lab(v, tv.step), tw = g.measureText(t).width;
      g.fillRect(left - 3, y - 0.5, 3, 1);
      g.fillText(t, Math.max(1, left - 4 - tw), Math.min(Math.max(y + 3, top + 8), top + ph + 3));
    }
    w.ticks = { h: { ...th, lastRight }, v: tv, width: Wc };  // for automated tests of the page
    g.fillText(H_.ax.name, Math.max(left, left + pw - g.measureText(H_.ax.name).width), top + ph + 24);
    g.fillText(V_.ax.name, left + 2, top + 10);
    w.geom = { left, top, pw, ph, longi, m, ns, nt, flipH, flipV, units, names };
    // a world's overlay in the plane's coordinates (s along u, t along v), e.g. computed trajectories (v11)
    if (w.overlay && !w.preview) {
      const at = (p, a) => (p - a.p0) / (a.p1 - a.p0);
      const map = (s, t) => {
        let fh = at(longi ? t : s, H_), fv = at(longi ? s : t, V_);
        if (flipH) fh = 1 - fh;
        if (flipV) fv = 1 - fv;
        return [left + fh * pw, top + (1 - fv) * ph];
      };
      g.save(); g.beginPath(); g.rect(left, top, pw, ph); g.clip();
      try { w.overlay(g, map, { left, top, pw, ph }); } catch (e) { console.error(e); }
      g.restore();
    }
    if (frameOverlay && !w.preview) {
      g.save(); g.beginPath(); g.rect(left, top, pw, ph); g.clip();
      try { frameOverlay(g, helper(w)); } catch (e) { console.error(e); }
      g.restore();
    }
    w.axes = { h: [H_.ax.name, hv[0], hv[1]], v: [V_.ax.name, vv[0], vv[1]] };  // for automated tests of the page
    if (w.preview || (w.data && w.data.meta.coarse)) {
      const txt = w.preview ? (w.preview.coarse ? "предпросмотр: грубый срез (48 строк), без сверки" : "предпросмотр по объёму (приближённо)")
        : "автосмещение: грубый срез, без сверки";
      g.fillStyle = "rgba(0,0,0,0.6)"; g.fillRect(left, top, g.measureText(txt).width + 8, 16); g.fillStyle = "#ffd28a"; g.fillText(txt, left + 4, top + 11);
    }
  }

  function statusLine(w) {
    const d = w.data;
    if (w.busy) { fill(w.status, el("span", { class: "warn" }, w.busy)); return; }
    if (!d) { fill(w.status, el("span", { class: "muted" }, "ждём расчёт…")); return; }
    const m = d.meta, v = m.verify || {};
    fill(w.status,
      el("span", { class: m.approximation ? "st-bad" : "muted", title: m.reason || "" }, m.route_label),
      v.points ? el("span", { class: v.ok ? "st-ok" : "st-bad", title: m.verify_title || "поле в точках плоскости против точного поля без БПФ" },
        ` · сверено в ${v.points} точк.: ${num(v.max_err, 2)} ≤ ${num(v.tol, 2)} ${v.ok ? "✓" : "✗"}`)
        : el("span", { class: "muted" }, v.note ? " · " + v.note : ""));
  }

  // a window as the manipulator sees it (setWindowManipulator)
  function helper(w) {
    const G = w.geom, m = G.m;
    const n = m.normal || [m.u[1] * m.v[2] - m.u[2] * m.v[1], m.u[2] * m.v[0] - m.u[0] * m.v[2], m.u[0] * m.v[1] - m.u[1] * m.v[0]];
    const hs = (G.longi ? m.tt : m.s), vs = (G.longi ? m.s : m.tt);
    const unitPx = G.pw / Math.abs(hs[1] - hs[0]);
    const toCanvas = (P) => {  // the point's projection on the plane, in the canvas's CSS pixels
      const d = [P[0] - m.origin[0], P[1] - m.origin[1], P[2] - m.origin[2]];
      const s_ = d[0] * m.u[0] + d[1] * m.u[1] + d[2] * m.u[2], t_ = d[0] * m.v[0] + d[1] * m.v[1] + d[2] * m.v[2];
      let fh = ((G.longi ? t_ : s_) - hs[0]) / (hs[1] - hs[0]), fv = ((G.longi ? s_ : t_) - vs[0]) / (vs[1] - vs[0]);
      if (G.flipH) fh = 1 - fh;
      if (G.flipV) fv = 1 - fv;
      return [G.left + fh * G.pw, G.top + (1 - fv) * G.ph];
    };
    return { id: w.id, el: w.cv, plane: { origin: m.origin, u: m.u, v: m.v, normal: n }, unitPx, toCanvas,
             point: (e) => pointAt(w, e), fixed: !!m.fixed };
  }

  // the physical point of the plane under the pointer (null outside the drawn slice)
  function pointAt(w, e) {
    const G = w.geom;
    if (!G) return null;
    const r = w.cv.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top;
    let fh = (px - G.left) / G.pw, fv = 1 - (py - G.top) / G.ph;
    if (fh < 0 || fh > 1 || fv < 0 || fv > 1) return null;
    if (G.flipH) fh = 1 - fh;
    if (G.flipV) fv = 1 - fv;
    const fs = G.longi ? fv : fh, ft = G.longi ? fh : fv;
    const m = G.m, s = m.s[0] + (m.s[1] - m.s[0]) * fs, t = m.tt[0] + (m.tt[1] - m.tt[0]) * ft;
    return [0, 1, 2].map((i) => m.origin[i] + s * m.u[i] + t * m.v[i]);
  }

  function hover(w, e) {
    const G = w.geom, d = w.preview || w.data;
    if (!G || !d) return;
    const r = w.cv.getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top;
    let fh = (px - G.left) / G.pw, fv = 1 - (py - G.top) / G.ph;
    if (fh < 0 || fh > 1 || fv < 0 || fv > 1) { w.readout.textContent = "наведите на срез"; return; }
    if (G.flipH) fh = 1 - fh;
    if (G.flipV) fv = 1 - fv;
    const fs = G.longi ? fv : fh, ft = G.longi ? fh : fv;
    const is = Math.min(G.ns - 1, Math.round(fs * (G.ns - 1))), it = Math.min(G.nt - 1, Math.round(ft * (G.nt - 1)));
    const m = G.m, s = m.s[0] + (m.s[1] - m.s[0]) * is / Math.max(1, G.ns - 1), t = m.tt[0] + (m.tt[1] - m.tt[0]) * it / Math.max(1, G.nt - 1);
    const P = [0, 1, 2].map((i) => m.origin[i] + s * m.u[i] + t * m.v[i]);
    const k = it * G.ns + is, v = d.I[k];
    const q = m.quantity, nm = G.names;
    w.readout.textContent = `${nm[0]} = ${num(P[0], 4)}, ${nm[1]} = ${num(P[1], 4)}, ${nm[2]} = ${num(P[2], 4)} ${G.units} · ` +
      (!(v >= 0) ? "вне области расчёта"
        : q ? `${q.label} = ${num(v * q.peak, 5)}${q.unit ? " " + q.unit : ""}`
        : `I/Iпик = ${num(v, 4)}` + (d.phase && !w.preview ? ` · фаза ${num(d.phase[k], 3)} рад` : ""));
  }

  function exportCsv(w) {
    const d = w.data; if (!d) return;
    const m = d.meta, [ns, nt] = [m.s[2], m.tt[2]], q = m.quantity;
    const rows = [q ? `s,t,x,y,z,${q.label}${q.unit ? " (" + q.unit + ")" : ""}` : "s,t,x,y,z,I_over_peak,phase"];
    for (let it = 0; it < nt; it++) for (let is = 0; is < ns; is++) {
      const s = m.s[0] + (m.s[1] - m.s[0]) * is / Math.max(1, ns - 1), t = m.tt[0] + (m.tt[1] - m.tt[0]) * it / Math.max(1, nt - 1);
      const P = [0, 1, 2].map((i) => m.origin[i] + s * m.u[i] + t * m.v[i]), k = it * ns + is;
      if (d.I[k] >= 0) rows.push((q ? [s, t, ...P, d.I[k] * q.peak] : [s, t, ...P, d.I[k], d.phase ? d.phase[k] : ""]).map((x) => typeof x === "number" ? x.toPrecision(8) : x).join(","));
    }
    const a = el("a", { href: URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv" })), download: `slice${w.id}.csv` });
    a.click();
  }

  root.style.display = "none";
  function setOverlay(id, fn) { const w = W.get(id); if (w) { w.overlay = fn; draw(w); } }
  const api = { el: root, sync, setSlice, setPreview, setBusy, select, setOverlay, redraw: () => { for (const w of W.values()) draw(w); },
                // tests: a window as the manipulator sees it (its plane, the maps to its canvas)
                helper: (id) => { const w = W.get(id); return w && w.geom ? helper(w) : null; },
                axes: (id) => (W.get(id) || {}).axes, lastMeta: (id) => ((W.get(id) || {}).data || {}).meta,
                ticks: (id) => (W.get(id) || {}).ticks || null,
                isFixed: (id) => { const w = W.get(id); return !!(w && w.data && w.data.meta && w.data.meta.fixed); } };
  root.__slices = api;  // for automated tests of the page
  allWindows.add(api);
  return api;
}
