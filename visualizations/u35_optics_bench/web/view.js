// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u35 view: the optical bench. Left: the geometry (the structure to scale, the beams at the angles the run computed
// by Snell's law, single photons under way, the two detectors) and the run's |E|² of s light through the structure.
// Right: the run's curves R(θ), T(θ) for s and p, R(λ), T(λ), and the photon counters against the run's expectation.
// Everything drawn comes from the run: segments (curves, field, angles), clicks (detections with their times) and
// frames (photons under way as the viewer may know them at that moment). The view computes no physics.
import { fmt, t } from "/static/js/i18n.js";
import { css, el, fresh2d, num, panel, time } from "/static/js/ui.js";

const S_COL = "#f76707", P_COL = "#1c7ed6", A_COL = "#868e96";
const outLabel = (k) => (k === "R" ? t("Reflected") : k === "T" ? t("Transmitted") : t("Absorbed"));

// a perceptual colormap (magma-like), 256 entries
const LUT = (() => {
  const stops = [[0, 0, 4], [28, 16, 68], [79, 18, 123], [129, 37, 129], [181, 54, 122], [229, 80, 100],
                 [251, 135, 97], [254, 194, 135], [252, 253, 191]];
  const out = new Uint8ClampedArray(256 * 3);
  for (let i = 0; i < 256; i++) {
    const f = i / 255 * (stops.length - 1), k = Math.min(Math.floor(f), stops.length - 2), w = f - k;
    for (let c = 0; c < 3; c++) out[3 * i + c] = stops[k][c] * (1 - w) + stops[k + 1][c] * w;
  }
  return out;
})();
const lut = (v) => { const c = Math.min(255, Math.max(0, Math.round(v * 255))); return `rgb(${LUT[3 * c]},${LUT[3 * c + 1]},${LUT[3 * c + 2]})`; };

// approximate display colour of a wavelength (drawing only); null outside the visible range
function lamRGB(nm) {
  if (nm < 380 || nm > 780) return null;
  let r = 0, g = 0, b = 0;
  if (nm < 440) { r = (440 - nm) / 60; b = 1; }
  else if (nm < 490) { g = (nm - 440) / 50; b = 1; }
  else if (nm < 510) { g = 1; b = (510 - nm) / 20; }
  else if (nm < 580) { r = (nm - 510) / 70; g = 1; }
  else if (nm < 645) { r = 1; g = (645 - nm) / 65; }
  else r = 1;
  const f = nm < 420 ? 0.3 + 0.7 * (nm - 380) / 40 : nm > 700 ? 0.3 + 0.7 * (780 - nm) / 80 : 1;
  const q = (x) => Math.round(255 * Math.pow(x * f, 0.8));
  return `rgb(${q(r)},${q(g)},${q(b)})`;
}
const polCol = (p) => (p ? P_COL : S_COL);
const fmtN = (n) => (n[1] ? `${num(n[0], 4)} + ${num(n[1], 4)}i` : num(n[0], 5));
const sceneText = (su) => t("{label}; λ = {lam:.4g} nm, θ = {th:.4g}°, {pol}",
  { label: su.label, lam: su.lam, th: su.theta, pol: su.pol === "unpol" ? "s+p" : su.pol });

export function createView(ctx) {
  let H = null, segs = [], clk = null, flashes = [], lastT = null, lastFrame = null, inFlight = [0, 0];

  // --- DOM --------------------------------------------------------------------------------------------
  const cvGeo = el("canvas"), cvCur = el("canvas");

  const btnFly = el("button", { title: t("A speed at which the flight of one photon is seen (an arm in ≈ {s} s)", { s: 1.2 }) },
    t("▷ photon flight"));
  const btnStat = el("button", { title: t("A speed for collecting statistics (≈ {n:d} photons per second)", { n: 2000 }) },
    t("▷▷ collect statistics"));
  const quick = el("div", { class: "toolbar quick", title: t("Set-up: changes at once (the same as in the panel on the left)") },
    el("span", { class: "muted" }, t("Set-up:")),
    ctx.liveControl ? [ctx.liveControl("lam_nm", { label: t("λ, nm") }), ctx.liveControl("theta_deg", { label: "θ, °" }),
      ctx.liveControl("pol", { label: t("polarisation") }), ctx.liveControl("structure", { label: t("structure") })] : null,
    btnFly, btnStat);
  const center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, quick,
    el("div", { class: "split" },
      el("div", {}, el("div", { class: "canvas-wrap" }, cvGeo)),
      el("div", {}, el("div", { class: "canvas-wrap" }, cvCur))));
  const infoBox = el("div", {}), statBox = el("div", {}), approxBox = el("div", { class: "help" });
  const rightPanels = [panel(t("Set-up of this segment"), infoBox), panel(t("Photons"), statBox),
    panel(t("Approximations"), approxBox)];
  btnFly.onclick = () => { const s = now(); if (s) ctx.send("speed", { value: s.t_in / 1.2 }); };
  btnStat.onclick = () => { const s = now(); if (s) ctx.send("speed", { value: 2000 / s.rate }); };
  for (const cv of [cvGeo, cvCur]) new ResizeObserver(() => ctx.requestRender()).observe(cv);

  // --- data ---------------------------------------------------------------------------------------------
  function newClicks() { return { n: 0, cap: 0, t: null, det: null, pol: null }; }
  function pushClicks(b) {
    const m = b.t.length;
    if (!m) return;
    if (clk.n + m > clk.cap) {
      const cap = Math.max(1024, 2 * (clk.n + m));
      const grow = (old, T) => { const a = new T(cap); if (old) a.set(old.subarray(0, clk.n)); return a; };
      clk.t = grow(clk.t, Float64Array); clk.det = grow(clk.det, Uint8Array); clk.pol = grow(clk.pol, Uint8Array);
      clk.cap = cap;
    }
    clk.t.set(b.t, clk.n); clk.det.set(b.det, clk.n); clk.pol.set(b.pol, clk.n);
    clk.n += m;
  }
  function firstAfter(tw) {  // index of the first click with time > t (clicks are in time order)
    let lo = 0, hi = clk.n;
    while (lo < hi) { const m = (lo + hi) >> 1; if (clk.t[m] <= tw) lo = m + 1; else hi = m; }
    return lo;
  }
  function segAt(tw) { let s = segs[0]; for (const g of segs) if (g.t <= tw) s = g; return s; }
  function now() { const s = segs[segs.length - 1]; return (s && s.setup) || H; }

  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr); return g;
  }
  function text(g, s, x, y, { color = css("--ink"), align = "left", bg = true, font = "11px system-ui" } = {}) {
    g.font = font; g.textAlign = align;
    if (bg) {
      const w = g.measureText(s).width, x0 = align === "left" ? x : align === "right" ? x - w : x - w / 2;
      g.fillStyle = hexA(css("--canvas"), 0.78);
      g.fillRect(x0 - 2, y - 10, w + 4, 13);
    }
    g.fillStyle = color; g.fillText(s, x, y); g.textAlign = "left";
  }
  function hexA(c, a) {  // "#rrggbb" -> rgba with alpha (theme tokens are hex)
    const m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(c.trim());
    return m ? `rgba(${parseInt(m[1], 16)},${parseInt(m[2], 16)},${parseInt(m[3], 16)},${a})` : c;
  }
  const medium = (n) => `rgba(110,165,235,${0.05 + 0.25 * Math.min(1, Math.max(0, (n - 1) / 2))})`;
  function layerFill(L) {
    if (L.role === "metal") return "rgba(242,183,5,0.85)";
    if (L.role === "gap") return medium(L.n[0]);
    if (L.role === "H") return "rgba(76,110,245,0.75)";
    if (L.role === "L") return "rgba(102,217,232,0.55)";
    return `rgba(116,192,252,${0.35 + 0.3 * Math.min(1, (L.n[0] - 1) / 2)})`;
  }

  // --- the geometry and the field -------------------------------------------------------------------------
  function drawGeometry(frame, tw, blobs) {
    const cv = cvGeo, g = setup(cv);
    const W = cv.clientWidth, Hh = cv.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const seg = segAt(tw);
    if (!seg) return;
    const su = seg.setup, ang = seg.angles, b = seg.b;
    const pw = Math.max(130, Math.min(230, W * 0.3)), W1 = W - pw;
    const z = b.z, E2 = b.E2, nz = z.length, zmin = z[0], zmax = z[nz - 1];
    const y0 = Hh * 0.36, y1 = Hh * 0.68, k = (y1 - y0) / (zmax - zmin);
    const yz = (zz) => y0 + (zz - zmin) * k;
    const D = su.thickness, yTop = yz(0), yBot = yz(D);
    // media and layers (to scale in depth)
    g.fillStyle = medium(su.n_in); g.fillRect(0, 0, W, yTop);
    g.fillStyle = medium(su.n_out); g.fillRect(0, yBot, W, Hh - yBot);
    let zc = 0;
    const thin = su.layers.some((L) => L.d * k < 12);
    for (const L of su.layers) {
      const ya = yz(zc), yb = yz(zc + L.d);
      g.fillStyle = layerFill(L); g.fillRect(0, ya, W, Math.max(yb - ya, 0.6));
      zc += L.d;
    }
    g.strokeStyle = hexA(css("--ink"), 0.55); g.lineWidth = 1;
    zc = 0;
    for (const e of [0, ...su.layers.map((L) => (zc += L.d))]) { const y = yz(e); g.beginPath(); g.moveTo(0, y); g.lineTo(W1, y); g.stroke(); }
    // labels of the media and the layers
    const muted = css("--muted");
    text(g, t("incidence medium n₀ = {n:.5g}", { n: su.n_in }), 8, yTop - 8, { color: muted });
    text(g, t("{name} n = {n:.5g}", { name: su.out_name, n: su.n_out }), 8, Math.min(Hh - 6, yBot + 16), { color: muted });
    if (su.layers.length && !thin) {
      zc = 0;
      for (const L of su.layers) {
        const ya = yz(zc), yb = yz(zc + L.d); zc += L.d;
        text(g, t("{name}: n = {n}, d = {d:.4g} nm", { name: L.name, n: fmtN(L.n), d: L.d }), W1 - 24, (ya + yb) / 2 + 4, { align: "right" });
      }
    } else if (su.layers.length) {
      const uniq = new Map();
      for (const L of su.layers) uniq.set(t(L.name), L);
      const parts = [...uniq.values()].map((L) => t("{name}: n = {n}, {d:.4g} nm", { name: L.name, n: fmtN(L.n), d: L.d }));
      const head = su.kind === "bragg" ? `(H L)×${su.layers.length / 2}` : t(su.label);
      text(g, `${head}; ${parts.join("; ")}`, W1 - 24, (yTop + yBot) / 2 + 4, { align: "right" });
    }
    // the scale: one wavelength in depth
    const lamPx = su.lam * k;
    g.strokeStyle = css("--ink"); g.lineWidth = 2;
    const xs = W1 - 12, ys = Math.max(4, Math.min(yz(zmin) + 4, Hh - lamPx - 4));
    g.beginPath(); g.moveTo(xs, ys); g.lineTo(xs, ys + lamPx); g.moveTo(xs - 4, ys); g.lineTo(xs + 4, ys); g.moveTo(xs - 4, ys + lamPx); g.lineTo(xs + 4, ys + lamPx); g.stroke();
    text(g, t("λ = {lam:.4g} nm", { lam: su.lam }), xs - 7, ys + 10, { align: "right" });

    // beams: directions from the run (Snell's law of the engine, approximate ray picture)
    const m = 16, xc = W1 * 0.44, th = ang.theta * Math.PI / 180;
    const dx = Math.sin(th), dy = Math.cos(th);
    const reach = (x, y, ux, uy, xmin, xmax, ymin, ymax) => {
      let s = 1e5;
      if (ux > 1e-9) s = Math.min(s, (xmax - x) / ux); if (ux < -1e-9) s = Math.min(s, (xmin - x) / ux);
      if (uy > 1e-9) s = Math.min(s, (ymax - y) / uy); if (uy < -1e-9) s = Math.min(s, (ymin - y) / uy);
      return Math.max(s, 0);
    };
    const P = [xc, yTop];
    const sIn = reach(xc, yTop, -dx, -dy, m, W1 - m, 44, Hh);
    const Sp = [xc - dx * sIn, yTop - dy * sIn];
    const normal = ang.theta < 3;  // the reflected beam goes back to the source: drawn shifted aside
    const off = normal ? 22 : 0;
    const PR = [xc + off, yTop];
    const sR = reach(PR[0], yTop, dx, -dy, m, W1 - m, 44, Hh);
    const DR = [PR[0] + dx * sR, yTop - dy * sR];
    // through the layers
    let x = xc; zc = 0;
    const inner = [];
    su.layers.forEach((L, j) => {
      const a = ang.layers[j], ya = yz(zc), yb = yz(zc + L.d); zc += L.d;
      if (a === null || a === undefined) { inner.push([x, ya, x, yb, true]); return; }
      let x1 = x + Math.tan(a * Math.PI / 180) * (yb - ya);
      x1 = Math.min(x1, W1 - m);
      inner.push([x, ya, x1, yb, false]); x = x1;
    });
    const Q = [x, yBot];
    const prop = ang.out !== null && ang.out !== undefined;
    const tho = (prop ? ang.out : ang.theta) * Math.PI / 180;
    const sT = reach(Q[0], yBot, Math.sin(tho), Math.cos(tho), m, W1 - m, 0, Hh - m - 4);
    const DT = [Q[0] + Math.sin(tho) * sT, yBot + Math.cos(tho) * sT];
    const cur = seg.cur.mix, beamC = lamRGB(su.lam) || "#adb5bd";
    const beam = (a, bb, alpha, w, dash) => {
      g.save(); g.globalAlpha = alpha; g.strokeStyle = beamC; g.lineWidth = w; g.setLineDash(dash || []);
      g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(bb[0], bb[1]); g.stroke(); g.restore();
    };
    beam(Sp, P, 0.9, 4);
    beam(PR, DR, 0.12 + 0.88 * cur.R, 4);
    for (const [xa, ya, xb, yb, ev] of inner) beam([xa, ya], [xb, yb], ev ? 0.5 : 0.8, ev ? 1.5 : 3, ev ? [2, 3] : null);
    if (prop) beam(Q, DT, 0.12 + 0.88 * cur.T, 4);
    else {  // evanescent: no transmitted beam; the field strip shows the decay computed by the run
      const gr = g.createLinearGradient(0, yBot, 0, yBot + 26);
      gr.addColorStop(0, hexA("#ffa94d", 0.55)); gr.addColorStop(1, hexA("#ffa94d", 0));
      g.fillStyle = gr; g.fillRect(Q[0] - 10, yBot, Math.min(160, W1 - Q[0] - 4), 26);
      text(g, t("evanescent wave"), Q[0] + 4, yBot + 40, { color: muted });
    }
    // the normal
    g.save(); g.setLineDash([4, 4]); g.strokeStyle = hexA(css("--ink"), 0.35); g.lineWidth = 1;
    g.beginPath(); g.moveTo(xc, yTop - 70); g.lineTo(xc, yBot + 70); g.stroke(); g.restore();
    // the source and the detectors
    g.fillStyle = beamC; g.beginPath(); g.arc(Sp[0], Sp[1], 7, 0, 2 * Math.PI); g.fill();
    g.strokeStyle = css("--ink"); g.lineWidth = 1; g.stroke();
    const pol = su.pol === "unpol" ? t("s and p") : su.pol;
    const srcLab = lamRGB(su.lam) ? t("source: λ = {lam:.4g} nm, {pol}", { lam: su.lam, pol })
      : su.lam < 380 ? t("source: λ = {lam:.4g} nm (UV), {pol}", { lam: su.lam, pol })
        : t("source: λ = {lam:.4g} nm (IR), {pol}", { lam: su.lam, pol });
    if (normal) text(g, srcLab, Sp[0] - 12, Sp[1] + 4, { align: "right" });
    else text(g, srcLab, Math.min(Sp[0] + 10, W1 - 190), Sp[1] - 9);
    const c = frame.counts || {};
    detector(g, DR, [dx, -dy], t("detector R: {k:d}", { k: c.R ?? 0 }), !normal);
    detector(g, DT, [Math.sin(tho), Math.cos(tho)], prop ? t("detector T: {k:d}", { k: c.T ?? 0 })
      : t("detector T: {k:d} (no light goes here)", { k: c.T ?? 0 }), true, !prop);
    // photons under way: on the way in a dot; after the structure the two packets with their weights
    const fl = (blobs && blobs.fl) || [];
    let nin = 0, nout = 0;
    for (let i = 0; i + 5 < fl.length; i += 6) {
      const col = polCol(fl[i + 1]);
      if (fl[i] === 0) { nin++; dot(g, lerp(Sp, P, clamp01(fl[i + 2])), col, 1); continue; }
      nout++;
      if (fl[i + 3] > 0) dot(g, lerp(PR, DR, clamp01(fl[i + 2])), col, fl[i + 3]);
      if (fl[i + 5] > 0 && prop) dot(g, lerp(Q, DT, clamp01(fl[i + 4])), col, fl[i + 5]);
    }
    // clicks since the previous frame flash at their detector (absorptions at the structure)
    if (lastT !== null && tw > lastT && clk.n) {  // one flash per detector (the newest click there)
      const i0 = firstAfter(lastT), i1 = firstAfter(tw);
      const seen = new Set();
      for (let i = i1 - 1; i >= i0 && seen.size < 3; i--) {
        if (seen.has(clk.det[i])) continue;
        seen.add(clk.det[i]);
        flashes = flashes.filter((f) => f.det !== clk.det[i]);
        flashes.push({ det: clk.det[i], pol: clk.pol[i], w: performance.now() });
      }
    }
    lastT = tw;
    const wall = performance.now();
    flashes = flashes.filter((f) => wall - f.w < 450);
    for (const f of flashes) {
      const a = 1 - (wall - f.w) / 450, pos = f.det === 0 ? DR : f.det === 1 ? DT : P;
      g.save(); g.globalAlpha = 0.8 * a; g.strokeStyle = f.det === 2 ? "#c92a2a" : polCol(f.pol); g.lineWidth = 1.6;
      g.beginPath(); g.arc(pos[0], pos[1], 8 + 12 * (1 - a), 0, 2 * Math.PI); g.stroke(); g.restore();
    }
    // the field strip: |E|² of s light through the structure, same depth scale
    const xS = W1;
    g.fillStyle = css("--canvas"); g.fillRect(xS, y0 - 34, pw, y1 - y0 + 52);
    g.strokeStyle = css("--line"); g.beginPath(); g.moveTo(xS, 0); g.lineTo(xS, Hh); g.stroke();
    zc = 0;
    for (const L of su.layers) { const ya = yz(zc), yb = yz(zc + L.d); zc += L.d; g.fillStyle = layerFill(L); g.globalAlpha = 0.35; g.fillRect(xS + 30, ya, pw - 36, Math.max(yb - ya, 0.6)); g.globalAlpha = 1; }
    let emax = 0; for (let i = 0; i < nz; i++) emax = Math.max(emax, E2[i]);
    emax = emax || 1;
    for (let i = 0; i + 1 < nz; i++) { g.fillStyle = lut(E2[i] / emax); g.fillRect(xS + 8, yz(z[i]), 16, Math.max(yz(z[i + 1]) - yz(z[i]), 0.7)); }
    g.strokeStyle = hexA(css("--ink"), 0.5); g.lineWidth = 1;
    for (const e of [0, D]) { g.beginPath(); g.moveTo(xS + 4, yz(e)); g.lineTo(W - 4, yz(e)); g.stroke(); }
    const xl = (v) => xS + 32 + (v / emax) * (pw - 40);
    g.strokeStyle = css("--accent"); g.lineWidth = 1.4; g.beginPath();
    for (let i = 0; i < nz; i++) { const X = xl(E2[i]), Y = yz(z[i]); if (i) g.lineTo(X, Y); else g.moveTo(X, Y); }
    g.stroke();
    text(g, t("|E|² (s), the run"), xS + 6, y0 - 20, { bg: false });
    text(g, t("0 … {e:.3g} of the incident", { e: emax }), xS + 6, y0 - 6, { color: muted, bg: false });
    if (su.pol !== "s") text(g, t("the field shown is for s"), xS + 6, y1 + 14, { color: muted, bg: false });
    text(g, t("the structure is to scale, the {arm:.3g} cm arms are not", { arm: (su.arm_m ?? 0.3) * 100 }), 8, 15, { color: muted });
    inFlight = [nin, nout];
  }
  function detector(g, pos, dir, label, show = true, dim = false) {
    if (!show && !label) return;
    const nx = -dir[1], ny = dir[0];
    g.save(); g.globalAlpha = dim ? 0.35 : 1;
    g.strokeStyle = css("--ink"); g.lineWidth = 5;
    g.beginPath(); g.moveTo(pos[0] - 11 * nx, pos[1] - 11 * ny); g.lineTo(pos[0] + 11 * nx, pos[1] + 11 * ny); g.stroke();
    g.restore();
    const right = pos[0] > cvGeo.clientWidth * 0.45;
    text(g, label, pos[0] + (right ? -14 : 14), pos[1] + (pos[1] < 40 ? 22 : -12), { align: right ? "right" : "left" });
  }
  function dot(g, p, col, w) {
    g.save(); g.globalAlpha = 0.2 + 0.8 * w; g.fillStyle = col;
    g.beginPath(); g.arc(p[0], p[1], 4.2, 0, 2 * Math.PI); g.fill();
    if (w < 0.999) { g.globalAlpha = 0.9; g.strokeStyle = col; g.lineWidth = 1; g.beginPath(); g.arc(p[0], p[1], 6.5, 0, 2 * Math.PI); g.stroke(); }
    g.restore();
  }
  const lerp = (a, b, f) => [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f];
  const clamp01 = (f) => Math.min(1, Math.max(0, f));

  // --- the curves and the counters ------------------------------------------------------------------------
  function axes(g, bx, xmin, xmax, xticks, xfmt, title) {
    g.strokeStyle = css("--grid"); g.lineWidth = 1;
    for (const v of [0, 0.25, 0.5, 0.75, 1]) { const y = bx.y + (1 - v) * bx.h; g.beginPath(); g.moveTo(bx.x, y); g.lineTo(bx.x + bx.w, y); g.stroke(); }
    g.strokeStyle = css("--line"); g.strokeRect(bx.x, bx.y, bx.w, bx.h);
    const muted = css("--muted");
    for (const v of [0, 0.5, 1]) text(g, fmt(v), bx.x - 4, bx.y + (1 - v) * bx.h + 4, { align: "right", color: muted, bg: false });
    for (const v of xticks) {
      const X = bx.x + (v - xmin) / (xmax - xmin) * bx.w;
      g.fillStyle = muted; g.fillRect(X, bx.y + bx.h, 1, 4);
      text(g, xfmt(v), X, bx.y + bx.h + 14, { align: "center", color: muted, bg: false });
    }
    text(g, title, bx.x, bx.titleY ?? bx.y - 6, { bg: false, font: "600 12px system-ui" });
  }
  function curve(g, bx, xs, ys, xmin, xmax, col, w, dash, alpha = 1) {
    g.save(); g.strokeStyle = col; g.lineWidth = w; g.setLineDash(dash || []); g.globalAlpha = alpha;
    g.beginPath();
    for (let i = 0; i < xs.length; i++) {
      const X = bx.x + (xs[i] - xmin) / (xmax - xmin) * bx.w, Y = bx.y + (1 - Math.min(1, Math.max(0, ys[i]))) * bx.h;
      if (i) g.lineTo(X, Y); else g.moveTo(X, Y);
    }
    g.stroke(); g.restore();
  }
  function vline(g, bx, X, col, dash, label, frac = 0.92) {  // frac: height of the label (0 top .. 1 bottom)
    g.save(); g.strokeStyle = col; g.lineWidth = 1.2; g.setLineDash(dash || []);
    g.beginPath(); g.moveTo(X, bx.y); g.lineTo(X, bx.y + bx.h); g.stroke(); g.restore();
    if (label) {
      g.font = "11px system-ui";
      const w = g.measureText(label).width, right = X + 3 + w > bx.x + bx.w;
      text(g, label, right ? X - 3 : X + 3, bx.y + frac * bx.h + 4, { color: col, align: right ? "right" : "left" });
    }
  }

  function drawCurves(frame, tw) {
    const cv = cvCur, g = setup(cv);
    const W = cv.clientWidth, Hh = cv.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const seg = segAt(tw);
    if (!seg) return;
    const su = seg.setup, b = seg.b, pm = su.pol;
    const ink = css("--ink"), muted = css("--muted"), accent = css("--accent");
    const curC = pm === "s" ? S_COL : pm === "p" ? P_COL : ink;
    const hA = Math.round(Hh * 0.36), hB = Math.round(Hh * 0.30);
    const A1 = { x: 40, y: 48, w: W - 52, h: hA - 70, titleY: 20 };
    const A2 = { x: 40, y: hA + 34, w: W - 52, h: hB - 58 };
    const A3 = { x: 10, y: hA + hB + 16, w: W - 20, h: Hh - hA - hB - 22 };
    // R(θ), T(θ)
    axes(g, A1, 0, 90, [0, 15, 30, 45, 60, 75, 90], (v) => v + "°", t("R(θ), T(θ) at λ = {lam:.4g} nm", { lam: su.lam }));
    if (seg.theta_c !== null && seg.theta_c !== undefined) {
      const X = A1.x + seg.theta_c / 90 * A1.w;
      g.fillStyle = hexA(css("--accent").startsWith("#") ? css("--accent") : "#1c6dd0", 0.07); g.fillRect(X, A1.y, A1.x + A1.w - X, A1.h);
    }
    const lossy = !su.lossless;
    const thick = (q) => (pm === q ? 2.4 : pm === "unpol" ? 1.3 : 1.0);
    const alp = (q) => (pm === q || pm === "unpol" ? 1 : 0.35);
    for (const [q, col] of [["s", S_COL], ["p", P_COL]]) {
      curve(g, A1, b.th, b["R" + q], 0, 90, col, thick(q), null, alp(q));
      curve(g, A1, b.th, b["T" + q], 0, 90, col, thick(q), [6, 4], alp(q));
      if (lossy) curve(g, A1, b.th, b["A" + q], 0, 90, col, thick(q), [1.5, 3], alp(q));
    }
    if (pm === "unpol") { curve(g, A1, b.th, b.Rc, 0, 90, ink, 2.2); curve(g, A1, b.th, b.Tc, 0, 90, ink, 2.2, [6, 4]); }
    if (seg.theta_c !== null && seg.theta_c !== undefined) {
      const lab = su.kind === "tir" && su.layers.length ? t("θ_c of the face = {a:.5g}°", { a: seg.theta_c })
        : `θ_c = ${fmt(seg.theta_c, ".5g")}°`;
      vline(g, A1, A1.x + seg.theta_c / 90 * A1.w, accent, [3, 3], lab, 0.62);
    } else if (seg.theta_c_face !== null && seg.theta_c_face !== undefined) {
      vline(g, A1, A1.x + seg.theta_c_face / 90 * A1.w, accent, [3, 3], t("θ_c of the face = {a:.5g}°", { a: seg.theta_c_face }), 0.62);
    }
    if (seg.theta_B) vline(g, A1, A1.x + seg.theta_B.deg / 90 * A1.w, P_COL, [3, 3], `θ_B = ${fmt(seg.theta_B.deg, ".5g")}°`, 0.86);
    else if (seg.min_rp) vline(g, A1, A1.x + seg.min_rp.deg / 90 * A1.w, P_COL, [2, 4], t("min. R_p = {r:.3g} at {a:.4g}°", { r: seg.min_rp.Rp, a: seg.min_rp.deg }), 0.86);
    const Xc = A1.x + su.theta / 90 * A1.w, cm = seg.cur.mix;
    vline(g, A1, Xc, curC, null, null);
    for (const v of [cm.R, cm.T]) { g.fillStyle = curC; g.beginPath(); g.arc(Xc, A1.y + (1 - v) * A1.h, 4, 0, 2 * Math.PI); g.fill(); }
    text(g, `θ = ${fmt(su.theta, ".5g")}°: R = ${fmt(cm.R, ".5g")}, T = ${fmt(cm.T, ".5g")}` + (lossy ? `, A = ${fmt(cm.A, ".4g")}` : ""),
      Math.min(Xc + 6, A1.x + A1.w - 230), A1.y + 26, { color: curC });
    legend(g, A1.x + A1.w, A1.y - 8, lossy, pm);
    // R(λ), T(λ)
    axes(g, A2, 300, 1600, [300, 500, 700, 900, 1100, 1300, 1600], (v) => String(v),
      t("R(λ), T(λ) at θ = {th:.5g}°, polarisation {pol}; λ, nm", { th: su.theta, pol: pm === "unpol" ? t("s+p (mixture)") : pm }));
    for (let L = 380; L < 780; L += 2) {
      const X = A2.x + (L - 300) / 1300 * A2.w; g.fillStyle = lamRGB(L); g.fillRect(X, A2.y + A2.h - 4, Math.ceil(A2.w * 2 / 1300) + 1, 4);
    }
    if (pm === "unpol") for (const [q, col] of [["s", S_COL], ["p", P_COL]]) curve(g, A2, b.lam, b["lR" + q], 300, 1600, col, 1, null, 0.35);
    curve(g, A2, b.lam, b.lRc, 300, 1600, curC, 2);
    curve(g, A2, b.lam, b.lTc, 300, 1600, curC, 2, [6, 4]);
    if (lossy) curve(g, A2, b.lam, b.lAc, 300, 1600, curC, 1.6, [1.5, 3]);
    if (su.lam0) vline(g, A2, A2.x + (su.lam0 - 300) / 1300 * A2.w, muted, [3, 3], `λ₀ = ${fmt(su.lam0, ".4g")}`, 0.5);
    const Xl = A2.x + (su.lam - 300) / 1300 * A2.w;
    vline(g, A2, Xl, curC, null, null);
    for (const v of [cm.R, cm.T]) { g.fillStyle = curC; g.beginPath(); g.arc(Xl, A2.y + (1 - v) * A2.h, 4, 0, 2 * Math.PI); g.fill(); }
    // counters
    drawCounters(g, A3, frame, seg);
  }
  function legend(g, xr, y, lossy, pm) {
    const items = [["R_s", S_COL, null], ["T_s", S_COL, [6, 4]], ["R_p", P_COL, null], ["T_p", P_COL, [6, 4]]];
    if (pm === "unpol") items.push([t("R, T of the mixture"), css("--ink"), null]);
    if (lossy) items.push(["A", css("--muted"), [1.5, 3]]);
    g.font = "11px system-ui";
    let x = xr;
    for (const [lab, col, dash] of items.reverse()) {
      const w = g.measureText(lab).width + 26; x -= w;
      g.save(); g.strokeStyle = col; g.lineWidth = 2; g.setLineDash(dash || []); g.beginPath(); g.moveTo(x, y - 4); g.lineTo(x + 16, y - 4); g.stroke(); g.restore();
      g.fillStyle = css("--ink"); g.fillText(lab, x + 19, y);
    }
  }
  function drawCounters(g, bx, frame, seg) {
    const c = frame.counts || { n: 0, R: 0, T: 0, A: 0 }, e = frame.expected || seg.expected, sg = frame.sigma || {};
    const ink = css("--ink"), muted = css("--muted");
    text(g, frame.z === null || frame.z === undefined ? t("Photons of this segment: n = {n:d}", { n: c.n })
      : t("Photons of this segment: n = {n:d}; reflected: z = {z:+.3g}σ", { n: c.n, z: frame.z }),
      bx.x, bx.y + 6, { bg: false, font: "600 12px system-ui" });
    // the legend under the bars, wrapped to the box's width (the Russian line is longer than the canvas: browser review
    // F10); the rows leave room for its extra lines
    g.font = "11px system-ui";
    const legendLines = wrapWords(g, t("bar: the fraction among the detected; tick: the run's expectation; whisker: ±2σ"), bx.w);
    const rowH = Math.min(40, (bx.h - 26 - 13 * (legendLines.length - 1)) / 3), labW = 76, barW = Math.max(80, bx.w * 0.42);
    ["R", "T", "A"].forEach((key, i) => {
      const y = bx.y + 16 + i * rowH, f = c.n ? c[key] / c.n : 0, p = e[key];
      text(g, outLabel(key), bx.x, y + 13, { bg: false, color: muted });
      const x0 = bx.x + labW;
      g.fillStyle = css("--chip"); g.fillRect(x0, y + 3, barW, 13);
      g.fillStyle = key === "R" ? "#ae3ec9" : key === "T" ? "#2b8a3e" : A_COL; g.fillRect(x0, y + 3, barW * f, 13);
      if (sg[key] !== null && sg[key] !== undefined) {
        g.strokeStyle = ink; g.lineWidth = 1;
        const a = Math.max(0, p - 2 * sg[key]), bb = Math.min(1, p + 2 * sg[key]);
        g.beginPath(); g.moveTo(x0 + barW * a, y + 9.5); g.lineTo(x0 + barW * bb, y + 9.5); g.stroke();
      }
      g.fillStyle = ink; g.fillRect(x0 + barW * p - 1, y, 2.5, 19);
      text(g, fmt(c[key], "d") + (c.n ? ` (${fmt(f, ".4g")})` : ""), x0 + barW + 8, y + 13, { bg: false });
      text(g, sg[key] ? t("expected {p:.5g}, σ = {s:.2g}", { p, s: sg[key] }) : t("expected {p:.5g}", { p }), x0, y + 29,
        { bg: false, color: muted, font: "10.5px system-ui" });
    });
    legendLines.forEach((line, i) => text(g, line, bx.x, bx.y + 16 + 3 * rowH + 8 + 13 * i, { bg: false, color: muted }));
  }
  function wrapWords(g, s, maxW) {  // greedy word wrap with the context's current font
    const lines = [];
    let cur = "";
    for (const w of s.split(" ")) {
      const next = cur ? cur + " " + w : w;
      if (cur && g.measureText(next).width > maxW) { lines.push(cur); cur = w; } else cur = next;
    }
    if (cur) lines.push(cur);
    return lines;
  }

  // --- panels ---------------------------------------------------------------------------------------------
  function drawInfo() {
    const su = now();
    if (!su) return;
    const rows = [[t("Structure"), t(su.label)], [t("Incidence medium n₀"), num(su.n_in, 6)], [t("{name:cap}", { name: su.out_name }), num(su.n_out, 6)],
      [t("Wavelength λ"), t("{v:.6g} nm", { v: su.lam })], [t("Angle of incidence θ"), num(su.theta, 6) + "°"], [t("Polarisation"), t(su.pol_label)],
      [t("Source rate"), t("{v:.4g} photons/s", { v: su.rate })], [t("Flight to the structure"), time(su.t_in, 4)],
      [t("Layers"), su.layers.length ? t("{k:d}, total thickness {d:.5g} nm", { k: su.layers.length, d: su.thickness }) : "0"]];
    if (su.lam0) rows.push([t("Design λ₀"), t("{v:.5g} nm", { v: su.lam0 })]);
    const items = [el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)]))];
    if (su.layers.length && su.layers.length <= 8) {
      items.push(el("table", { style: { fontSize: "12px", marginTop: "6px" } },
        el("tr", {}, el("th", {}, t("layer")), el("th", {}, "n"), el("th", {}, t("d, nm"))),
        su.layers.map((L) => el("tr", {}, el("td", {}, t(L.name)), el("td", { class: "mono" }, fmtN(L.n)), el("td", { class: "mono" }, num(L.d, 5))))));
    }
    infoBox.replaceChildren(...items);
  }
  function drawStats(frame) {
    const tt = frame.totals || {}, c = frame.counts || {};
    const rows = [[t("emitted in all"), tt.emitted], [t("in flight: to the structure / after it"), `${inFlight[0]} / ${inFlight[1]}`],
      [t("reflected (in all)"), tt.R], [t("transmitted (in all)"), tt.T], [t("absorbed (in all)"), tt.A],
      [t("transitional (emitted before a change)"), tt.transitional], [t("lost at a rebuild"), tt.lost],
      [t("counted in this segment"), c.n]];
    statBox.replaceChildren(el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, String(v ?? 0))])),
      el("div", { class: "help" }, t("In an experiment absorption is seen as “no detector clicked”; here the photon vanishes in the structure at the moment it reaches it.")),
      frame.lag ? el("p", { class: "st-bad" }, t("The computation cannot keep up with the chosen speed: the world runs slower.")) : "");
  }

  return {
    center, rightPanels,
    help: () => el("div", {},
      el("h4", {}, t("What is on the screen")),
      el("p", {}, t("On the left, the diagram: the source, the planar structure (to scale in depth: the layers are coloured bands, the bar on the left is one wavelength), the incident, reflected and transmitted beams at the angles the run computed by Snell's law (inside the layers, an approximate ray picture), and the two detectors. The brightness of the beams is the computed R and T. To the right of the diagram, the field |E|² of the s wave in and near the structure (the engine's function field_profile): a standing wave above the structure, the decay in a metal and beyond the face at total reflection.")),
      el("p", {}, t("Photons fly one by one (orange: s, blue: p). When a photon reaches the structure, its fate is drawn by the Born rule with this run's probabilities R, T, A. While no detector has clicked, two packets (rings) are shown after the structure, their brightness by the probabilities; the click of one detector (a flash) is the outcome. When the arrival time at one detector has passed without a click, its packet fades. An absorbed photon vanishes in the structure (a red flash).")),
      el("p", {}, t("On the right, this run's curves: R(θ), T(θ) for s and p at the current λ (θ_B: where the run's r_p vanishes, θ_c: where the run's transmission vanishes), the spectrum R(λ), T(λ) at the current angle, and the photon counters with the expected values and ±2σ.")),
      el("p", {}, t("Any change of the set-up (λ, angle, polarisation, media, structure) applies at once and starts a new segment. Photons emitted before a change of the source or the structure fly on and are counted as transitional; when the angle or the media change, the beam paths are rebuilt and the photons in flight are lost (this is counted)."))),
    reset() { H = null; segs = []; clk = newClicks(); flashes = []; lastT = null; lastFrame = null; },
    // key frames (player.js): segments and clicks only grow (lengths); the panels follow the last segment
    snapshot() { return { segs: segs.length, clk: clk.n }; },
    restore(k) {
      segs.length = k.segs; clk.n = k.clk; lastT = null; flashes = [];
      const last = segs[segs.length - 1];
      approxBox.replaceChildren(...((last && last.approx) || []).map((a) => el("div", { style: { margin: "4px 0" } }, "• " + t(a))));
      if (last) ctx.setScene && ctx.setScene(sceneText(last.setup));
      drawInfo();
    },
    onHeader(meta) { H = meta; },
    onMessage(meta, blobs) {
      if (meta.type === "segment") {
        segs.push({ ...meta, b: blobs });
        approxBox.replaceChildren(...(meta.approx || []).map((a) => el("div", { style: { margin: "4px 0" } }, "• " + t(a))));
        ctx.setScene && ctx.setScene(sceneText(meta.setup));
        drawInfo();
        lastT = null;
      } else if (meta.type === "clicks") {
        pushClicks(blobs);
      }
    },
    render(frame, tw, blobs) {
      if (!H) return;
      if (lastT !== null && tw < lastT) { lastT = null; flashes = []; }
      lastFrame = frame;
      drawGeometry(frame, tw, blobs);
      drawCurves(frame, tw);
      drawStats(frame);
    },
  };
}
