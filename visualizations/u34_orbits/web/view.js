// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v04 view: the orbit plane (trail of the body, the other theory's ghost, apsides, the special radii of the
// Schwarzschild geometry, the central body) and the plots r(t) and 1 − dτ/dt; panels "Orbit" and "Clocks".
// Everything drawn is data of the run: trail samples and apsides are messages revealed when the world's time
// reached them, the current state comes with each frame, the special radii come from the engine (header).
// The view only draws, scales and formats; it computes no physics.
import { Plane } from "/static/js/canvas.js";
import { t } from "/static/js/i18n.js";
import { css, el, fresh2d, length, num, panel, time } from "/static/js/ui.js";

const AU_M = 149597870700;

export function createView(ctx) {
  let H = null, units = null, liveVals = {};
  let segs = [];                 // segment messages, in time order
  let trails = new Map();        // seg -> columns {n, t, x, y, r, lag}
  let gtrails = new Map();       // seg -> columns {n, t, x, y, r}
  let apsides = new Map();       // seg -> [apsis]
  let gapsides = new Map();      // seg -> [ghost periapsis]
  let ghostInfo = new Map();     // seg -> ghost info (or null)
  // the plane is fitted to a new launch once, when it first appears; scrubbing back and forth, a rebuild or a key frame
  // keep the owner's pan and zoom (review UX-ui U1: a step back refitted the plane); a new world fits again
  let lastT = 0, fittedSeg = -1, fittedWorld = null;
  const opt = { allSegs: true, radii: true, apsides: true, follow: false, history: false };

  // --- DOM -----------------------------------------------------------------------------------------------
  const live = (id, label) => (ctx.liveControl ? ctx.liveControl(id, { label }) : null);
  const btnPlus = el("button", { title: t("Push: +{p} % of the speed along the motion (at the current moment)", { p: 5 }) }, t("push +{p} %", { p: 5 }));
  const btnMinus = el("button", { title: t("Brake: −{p} % of the speed along the motion", { p: 5 }) }, t("−{p} %", { p: 5 }));
  const btnRelaunch = el("button", { title: t("Launch the body again from the initial data (r₀, speed, angle)") }, t("↻ launch"));
  const quick = el("div", { class: "toolbar quick", title: t("Launch of the body: changes apply at once (the same as in the panel on the left)") },
    el("span", { class: "muted" }, t("Launch:")), live("r0", "r₀, M"), live("speed", t("speed, × circular")),
    live("angle", t("angle, °")), live("ghost", t("ghost")), btnPlus, btnMinus, btnRelaunch);
  const cbAll = el("input", { type: "checkbox", checked: true });
  const cbRadii = el("input", { type: "checkbox", checked: true });
  const cbAps = el("input", { type: "checkbox", checked: true });
  const cbFollow = el("input", { type: "checkbox" });
  const cbHist = el("input", { type: "checkbox" });
  const btnFit = el("button", { title: t("Fit the orbit of the current segment") }, t("⌖ orbit"));
  const btnCenter = el("button", { title: t("Fit the region near the centre (up to {r}M)", { r: 12 }) }, t("⌖ centre"));
  const toolbar = el("div", { class: "toolbar" },
    el("label", { title: t("Show the traces of earlier segments (faded)") }, cbAll, " ", t("earlier segments")),
    el("label", { title: t("Horizon 2M, photon sphere 3M, marginally bound orbit 4M, ISCO 6M") }, cbRadii, " ", t("GR radii")),
    el("label", {}, cbAps, " ", t("periapses")),
    el("label", { title: t("Keep the body in the centre of the view") }, cbFollow, " ", t("follow the body")),
    el("label", { title: t("Plots: the whole history of the segment instead of the last orbits") }, cbHist, " ", t("plots: whole segment")),
    btnFit, btnCenter);
  const cvOrb = el("canvas"), cvPlot = el("canvas");
  const ovOrb = el("div", { class: "overlay" }), ovPlot = el("div", { class: "overlay" });
  const center = el("div", { style: { display: "flex", flexDirection: "column", flex: 1, minHeight: 0 } }, quick, toolbar,
    el("div", { class: "split", style: { gridTemplateColumns: "1.5fr 1fr" } },
      el("div", {}, el("div", { class: "canvas-wrap" }, cvOrb, ovOrb)),
      el("div", {}, el("div", { class: "canvas-wrap" }, cvPlot, ovPlot))));
  const orbBox = el("div", {});
  const clockBox = el("div", {});
  const rightPanels = [panel(t("Orbit"), orbBox), panel(t("Clocks"), clockBox)];

  const plane = new Plane(cvOrb, { onChange: () => ctx.requestRender() });
  new ResizeObserver(() => ctx.requestRender()).observe(cvPlot);
  for (const [cb, k] of [[cbAll, "allSegs"], [cbRadii, "radii"], [cbAps, "apsides"], [cbFollow, "follow"], [cbHist, "history"]])
    cb.onchange = () => { opt[k] = cb.checked; ctx.requestRender(); };
  btnPlus.onclick = () => ctx.action("boost", { dv: 0.05 });
  btnMinus.onclick = () => ctx.action("boost", { dv: -0.05 });
  btnRelaunch.onclick = () => ctx.action("relaunch", {});
  btnFit.onclick = () => { const s = segAt(lastT); if (s) fitSeg(s); };
  btnCenter.onclick = () => { const R = Math.max(12, (H && H.body.R) ? 1.5 * H.body.R : 0); plane.fit(-R, R, -R, R); };

  // --- data helpers -----------------------------------------------------------------------------------------
  function cols(withLag) { return { n: 0, cap: 0, t: null, x: null, y: null, r: null, lag: withLag ? null : undefined }; }
  function push(map, seg, b, withLag) {
    let c = map.get(seg);
    if (!c) { c = cols(withLag); map.set(seg, c); }
    const m = b.t.length;
    if (c.n + m > c.cap) {
      const cap = Math.max(1024, 2 * (c.n + m));
      const grow = (old, T) => { const a = new T(cap); if (old) a.set(old.subarray(0, c.n)); return a; };
      c.t = grow(c.t, Float64Array); c.x = grow(c.x, Float64Array); c.y = grow(c.y, Float64Array); c.r = grow(c.r, Float64Array);
      if (withLag) c.lag = grow(c.lag, Float64Array);
      c.cap = cap;
    }
    c.t.set(b.t, c.n); c.x.set(b.x, c.n); c.y.set(b.y, c.n); c.r.set(b.r, c.n);
    if (withLag) c.lag.set(b.lag, c.n);
    c.n += m;
  }
  function upTo(c, tw) {  // number of samples with time <= t (samples are in time order)
    if (!c) return 0;
    let lo = 0, hi = c.n;
    while (lo < hi) { const m = (lo + hi) >> 1; if (c.t[m] <= tw) lo = m + 1; else hi = m; }
    return lo;
  }
  function segAt(tw) { let s = null; for (const g of segs) if (g.t <= tw) s = g; return s || segs[0] || null; }
  const M = () => (units ? units.M_m : 1);
  function lenM(rM) { return `${num(rM, 7)} M (${length(rM * M(), { au: AU_M }, 6)})`; }
  function tfmt(s, d = 7) {
    if (s === null || s === undefined) return "—";
    return liveVals.time_units === "geo" && units ? `${num(s / units.T_s, d)} GM/c³` : time(s, d);
  }
  function angFmt(rad) {
    if (rad === null || rad === undefined) return "—";
    const a = Math.abs(rad);
    if (a < Math.PI / 180) return num(rad * 180 / Math.PI * 3600, 7) + "″";
    return num(rad * 180 / Math.PI, 7) + "°";
  }
  function extent(s) {
    const i = s.init || {}, r0 = i.r0 || 10;
    let R = r0;
    if (s.kind === "bound" && s.r_apo) R = s.r_apo;
    else if (s.kind === "escape" || s.kind === "radial_escape") R = 4 * r0;
    else if (s.r_apo && Number.isFinite(s.r_apo)) R = Math.max(r0, s.r_apo);
    const g = ghostInfo.get(s.seg);
    if (g && g.r_apo && Number.isFinite(g.r_apo)) R = Math.max(R, Math.min(g.r_apo, 20 * r0));
    return 1.12 * R;
  }
  function fitSeg(s) { const R = extent(s); plane.fit(-R, R, -R, R); }

  // --- orbit plane -------------------------------------------------------------------------------------------
  function polyline(g, c, n, color, width, dash, alpha) {
    if (!c || n < 2) return;
    g.save(); g.strokeStyle = color; g.lineWidth = width; g.globalAlpha = alpha; g.setLineDash(dash || []);
    g.beginPath();
    let px = plane.X(c.x[0]), py = plane.Y(c.y[0]);
    g.moveTo(px, py);
    for (let i = 1; i < n; i++) {
      const X = plane.X(c.x[i]), Y = plane.Y(c.y[i]);
      if (Math.abs(X - px) + Math.abs(Y - py) < 0.7 && i < n - 1) continue;  // sub-pixel: skip (drawing only)
      g.lineTo(X, Y); px = X; py = Y;
    }
    g.stroke(); g.restore();
  }
  function circle(g, r, stroke, dash, label, fill, angDeg = -45) {
    const R = r * plane.sx;
    if (R < 2) return;
    g.save(); g.beginPath(); g.arc(plane.X(0), plane.Y(0), R, 0, 2 * Math.PI);
    if (fill) { g.fillStyle = fill; g.fill(); }
    if (stroke) { g.strokeStyle = stroke; g.lineWidth = 1; g.setLineDash(dash || []); g.stroke(); }
    g.restore();
    if (label && R > 22) {
      g.save(); g.fillStyle = stroke || css("--muted"); g.font = "11px system-ui";
      const a = angDeg * Math.PI / 180;
      g.fillText(label, plane.X(r * Math.cos(a)) + 3, plane.Y(r * Math.sin(a)) + 4); g.restore();
    }
  }
  function drawOrbit(frame, tw) {
    const g = plane.ctx;
    plane.clear();
    if (!H) return;
    const s = segAt(tw);
    if (s && s.seg > fittedSeg && s.launch !== false) { fittedSeg = s.seg; fitSeg(s); }
    if (opt.follow && frame) { plane.cx = frame.x; plane.cy = frame.y; }
    plane.grid({ labelX: (v) => num(v, 4) + " M", labelY: (v) => num(v, 4) + " M" });
    const gr = H.law === "GR" || (s && ghostInfo.get(s.seg) && ghostInfo.get(s.seg).law === "GR");
    const body = H.body;
    // central body
    if (body.R > 0) circle(g, body.R, css("--warn"), null, null, "rgba(240,140,0,0.35)");
    if (H.law === "GR" && !(body.R > 0)) circle(g, H.special.horizon, "#000", null, null, "#000");
    if (!(body.R > 0)) {  // a point mass / a black hole too small to see: a marker of fixed size
      g.save(); g.fillStyle = H.law === "GR" ? "#000" : css("--warn"); g.strokeStyle = css("--muted");
      g.beginPath(); g.arc(plane.X(0), plane.Y(0), 3, 0, 2 * Math.PI); g.fill(); g.stroke(); g.restore();
    }
    // special radii (from the engine: lfphys.core.gravity.kerr at zero spin)
    if (opt.radii && gr) {  // only outside the body: inside it the exterior (Schwarzschild) metric does not apply
      const sp = H.special, out = (r) => !(body.R > 0) || r > body.R;
      if (out(sp.horizon)) circle(g, sp.horizon, "#868e96", null, t("{r:.3g}M horizon", { r: sp.horizon }), null, -100);
      if (out(sp.photon)) circle(g, sp.photon, "#ae3ec9", [4, 3], t("{r:.3g}M photon sphere", { r: sp.photon }), null, -75);
      if (out(sp.mb)) circle(g, sp.mb, "#1c7ed6", [1, 3], `${num(sp.mb, 3)}M`, null, -45);
      if (out(sp.isco)) circle(g, sp.isco, "#e8590c", [6, 4], `${num(sp.isco, 3)}M ISCO`, null, -20);
    }
    // trails: earlier segments faded
    const accent = css("--accent");
    if (opt.allSegs) for (const [sg, c] of trails) if (!s || sg !== s.seg) polyline(g, c, upTo(c, tw), css("--muted"), 1, null, 0.45);
    if (s) {
      const gc = gtrails.get(s.seg);
      if (gc) polyline(g, gc, upTo(gc, tw), "#f08c00", 1.3, [6, 5], 0.95);
      const c = trails.get(s.seg);
      const n = upTo(c, tw);
      polyline(g, c, n, accent, 1.6, null, 1);
      // from the last revealed sample to the body's current position
      if (c && n && frame && frame.seg === s.seg) {
        g.save(); g.strokeStyle = accent; g.lineWidth = 1.6; g.beginPath();
        g.moveTo(plane.X(c.x[n - 1]), plane.Y(c.y[n - 1])); g.lineTo(plane.X(frame.x), plane.Y(frame.y)); g.stroke(); g.restore();
      }
      // launch point and the direction of the initial velocity
      const i = s.init;
      if (i) {
        const x0 = i.r0 * Math.cos(i.phi0), y0 = i.r0 * Math.sin(i.phi0);
        const vx = i.v_r * Math.cos(i.phi0) - i.v_phi * Math.sin(i.phi0), vy = i.v_r * Math.sin(i.phi0) + i.v_phi * Math.cos(i.phi0);
        const vn = Math.hypot(vx, vy);
        g.save(); g.strokeStyle = css("--ok"); g.fillStyle = css("--ok"); g.lineWidth = 1.5;
        const X0 = plane.X(x0), Y0 = plane.Y(y0);
        g.beginPath(); g.arc(X0, Y0, 3.5, 0, 2 * Math.PI); g.stroke();
        if (vn > 0) {
          const L = 34, ux = vx / vn, uy = -vy / vn;
          g.beginPath(); g.moveTo(X0, Y0); g.lineTo(X0 + L * ux, Y0 + L * uy); g.stroke();
          g.beginPath(); g.moveTo(X0 + L * ux, Y0 + L * uy);
          g.lineTo(X0 + (L - 7) * ux - 4 * uy, Y0 + (L - 7) * uy + 4 * ux); g.lineTo(X0 + (L - 7) * ux + 4 * uy, Y0 + (L - 7) * uy - 4 * ux); g.fill();
        }
        g.restore();
      }
      if (opt.apsides) drawApsides(g, s, tw);
    }
    // the body and the ghost
    if (frame && s && frame.seg === s.seg) {
      if (frame.ghost) {
        g.save(); g.strokeStyle = "#f08c00"; g.lineWidth = 2; g.beginPath();
        g.arc(plane.X(frame.ghost.x), plane.Y(frame.ghost.y), 6, 0, 2 * Math.PI); g.stroke(); g.restore();
      }
      g.save();
      const X = plane.X(frame.x), Y = plane.Y(frame.y);
      if (frame.alive) {
        g.fillStyle = accent; g.strokeStyle = css("--canvas"); g.lineWidth = 1.5;
        g.beginPath(); g.arc(X, Y, 6, 0, 2 * Math.PI); g.fill(); g.stroke();
      } else {
        g.strokeStyle = css("--bad"); g.lineWidth = 2;
        g.beginPath(); g.moveTo(X - 6, Y - 6); g.lineTo(X + 6, Y + 6); g.moveTo(X - 6, Y + 6); g.lineTo(X + 6, Y - 6); g.stroke();
        g.fillStyle = css("--bad"); g.font = "12px system-ui";
        g.fillText(END_TEXT[frame.status] || frame.status, X + 9, Y - 8);
      }
      g.restore();
    }
    // scale bar
    const bw = 120, wM = bw / plane.sx;
    g.save(); g.strokeStyle = css("--ink"); g.fillStyle = css("--ink"); g.lineWidth = 2; g.font = "11px system-ui";
    const yb = plane.h - 26;
    g.beginPath(); g.moveTo(14, yb); g.lineTo(14 + bw, yb); g.stroke();
    g.fillText(`${num(wM, 3)} M = ${length(wM * M(), { au: AU_M }, 3)}`, 14, yb - 5); g.restore();
    const gi = s ? ghostInfo.get(s.seg) : null;
    ovOrb.textContent = gi
      ? t("The orbit plane from above. Solid: the orbit of this world ({law}), dashed: the ghost ({ghost}) from the same initial data. The green arrow is the initial velocity. Wheel: zoom, drag: pan.",
        { law: lawShort(H.law), ghost: lawShort(gi.law) })
      : t("The orbit plane from above. Solid: the orbit of this world ({law}). The green arrow is the initial velocity. Wheel: zoom, drag: pan.",
        { law: lawShort(H.law) });
  }
  function drawApsides(g, s, tw) {
    const list = (apsides.get(s.seg) || []).filter((a) => a.t <= tw);
    const peri = list.filter((a) => a.kind === "peri"), apo = list.filter((a) => a.kind === "apo");
    g.save();
    g.fillStyle = css("--muted");
    for (const a of apo.slice(-40)) { const X = plane.X(a.x), Y = plane.Y(a.y); g.fillRect(X - 2.5, Y - 2.5, 5, 5); }
    const show = peri.slice(-8);
    if (peri.length) {  // apsidal lines: the first and the latest periapsis
      const f = peri[0], l = peri[peri.length - 1];
      g.strokeStyle = css("--muted"); g.lineWidth = 1; g.setLineDash([3, 4]);
      g.beginPath(); g.moveTo(plane.X(0), plane.Y(0)); g.lineTo(plane.X(f.x), plane.Y(f.y)); g.stroke();
      g.setLineDash([]); g.strokeStyle = "#c2255c";
      g.beginPath(); g.moveTo(plane.X(0), plane.Y(0)); g.lineTo(plane.X(l.x), plane.Y(l.y)); g.stroke();
    }
    g.font = "11px system-ui";
    // labels: the newest periapsis of each cluster closer than 14 px (Mercury: all of them at one point)
    let lastXY = null;
    for (let k = show.length - 1; k >= 0; k--) {
      const a = show[k], X = plane.X(a.x), Y = plane.Y(a.y);
      g.fillStyle = "#c2255c";
      g.beginPath(); g.moveTo(X, Y - 5); g.lineTo(X + 5, Y); g.lineTo(X, Y + 5); g.lineTo(X - 5, Y); g.closePath(); g.fill();
      if (lastXY && Math.hypot(X - lastXY[0], Y - lastXY[1]) < 14) continue;
      if (k < show.length - 4) continue;
      let deg = (a.phi * 180 / Math.PI) % 360;
      if (deg > 180) deg -= 360; else if (deg <= -180) deg += 360;
      if (Math.abs(deg) < 5e-7) deg = 0;  // below the display precision of the angle (the shift is shown separately)
      let txt = t("p{n:d}: φ = {phi:.7g}°", { n: a.n, phi: deg });
      if (a.n > 1 && peri.length && k === show.length - 1) txt = t("{a}, shift from p{k:d}: {s}", { a: txt, k: peri[0].n, s: angFmt(a.shift) });
      const w = g.measureText(txt).width;
      g.fillText(txt, X + 7 + w > plane.w - 4 ? X - 7 - w : X + 7, Y - 6);
      lastXY = [X, Y];
    }
    for (const a of (gapsides.get(s.seg) || []).filter((q) => q.t <= tw).slice(-8)) {
      const X = plane.X(a.x), Y = plane.Y(a.y);
      g.strokeStyle = "#f08c00"; g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(X, Y - 5); g.lineTo(X + 5, Y); g.lineTo(X, Y + 5); g.lineTo(X - 5, Y); g.closePath(); g.stroke();
    }
    g.restore();
  }

  // --- plots: r(t) and 1 − dτ/dt ------------------------------------------------------------------------
  function setup(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = cv.clientWidth, h = cv.clientHeight;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr); return g;
  }
  function drawPlots(frame, tw) {
    const g = setup(cvPlot), W = cvPlot.clientWidth, Hh = cvPlot.clientHeight;
    g.fillStyle = css("--canvas"); g.fillRect(0, 0, W, Hh);
    const s = segAt(tw);
    if (!H || !s) return;
    const c = trails.get(s.seg), gc = gtrails.get(s.seg);
    const n = upTo(c, tw), ng = upTo(gc, tw);
    const t1 = tw, t0 = opt.history ? s.t : Math.max(s.t, tw - (s.t_window || (tw - s.t)));
    const left = 66, right = 10, top1 = 74, h1 = Math.max(40, (Hh - 140) / 2), top2 = top1 + h1 + 36, h2 = Math.max(40, Hh - top2 - 26);
    const span = Math.max(t1 - t0, 1e-300);
    const X = (tt) => left + (W - left - right) * (tt - t0) / span;
    const i0 = c ? Math.max(0, upTo(c, t0) - 1) : 0;
    // r(t)
    let lo = Infinity, hi = -Infinity;
    for (let i = i0; i < n; i++) { lo = Math.min(lo, c.r[i]); hi = Math.max(hi, c.r[i]); }
    if (frame && frame.seg === s.seg) { lo = Math.min(lo, frame.r); hi = Math.max(hi, frame.r); }
    const gi0 = gc ? Math.max(0, upTo(gc, t0) - 1) : 0;
    for (let i = gi0; i < ng; i++) { lo = Math.min(lo, gc.r[i]); hi = Math.max(hi, gc.r[i]); }
    if (!Number.isFinite(lo)) { lo = 0; hi = 1; }
    if (hi - lo < 1e-9 * Math.max(Math.abs(hi), 1)) { const m = 0.5 * (hi + lo); lo = m * (1 - 1e-6) - 1e-9; hi = m * (1 + 1e-6) + 1e-9; }
    const pad = 0.08 * (hi - lo); lo -= pad; hi += pad;
    const Y1 = (r) => top1 + h1 * (1 - (r - lo) / (hi - lo));
    const dig = Math.min(12, Math.max(5, Math.ceil(Math.log10(Math.abs(hi) / Math.max(hi - lo, 1e-300))) + 2));
    axes(g, left, top1, W - left - right, h1, lo, hi, (v) => num(v, dig), "r, M");
    if (H.law === "GR" || (ghostInfo.get(s.seg) && ghostInfo.get(s.seg).law === "GR")) {
      for (const [r, lab, col] of [[H.special.isco, "ISCO", "#e8590c"], [H.special.horizon, "2M", "#868e96"], [H.special.photon, "3M", "#ae3ec9"]]) {
        if (r > lo && r < hi) { g.save(); g.strokeStyle = col; g.setLineDash([5, 4]); g.beginPath(); g.moveTo(left, Y1(r)); g.lineTo(W - right, Y1(r)); g.stroke();
          g.fillStyle = col; g.font = "10px system-ui"; g.fillText(lab, W - right - 28, Y1(r) - 3); g.restore(); }
      }
    }
    series(g, gc, gi0, ng, X, (i) => Y1(gc.r[i]), "#f08c00", [6, 5]);
    series(g, c, i0, n, X, (i) => Y1(c.r[i]), css("--accent"), null);
    if (frame && frame.seg === s.seg) dot(g, X(tw), Y1(frame.r), css("--accent"));
    // 1 − dτ/dt
    if (H.law === "GR") {
      let lo2 = Infinity, hi2 = -Infinity;
      for (let i = i0; i < n; i++) { const v = c.lag[i]; lo2 = Math.min(lo2, v); hi2 = Math.max(hi2, v); }
      if (frame && frame.seg === s.seg) { lo2 = Math.min(lo2, frame.deficit); hi2 = Math.max(hi2, frame.deficit); }
      if (!Number.isFinite(lo2)) { lo2 = 0; hi2 = 1; }
      if (hi2 - lo2 < 1e-6 * Math.max(Math.abs(hi2), 1e-300)) { const m = 0.5 * (hi2 + lo2); lo2 = m * 0.999; hi2 = m * 1.001 + 1e-300; }
      const pad2 = 0.08 * (hi2 - lo2); lo2 -= pad2; hi2 += pad2;
      const Y2 = (v) => top2 + h2 * (1 - (v - lo2) / (hi2 - lo2));
      axes(g, left, top2, W - left - right, h2, lo2, hi2, (v) => num(v, 4), "1 − dτ/dt");
      series(g, c, i0, n, X, (i) => Y2(c.lag[i]), "#2b8a3e", null);
      if (frame && frame.seg === s.seg) dot(g, X(tw), Y2(frame.deficit), "#2b8a3e");
    } else {
      g.fillStyle = css("--muted"); g.font = "12px system-ui";
      g.fillText(t("Newton: time is absolute:"), left, top2 + 20);
      g.fillText(t("the body's clock runs like the distant observer's clock (dτ/dt = 1)."), left, top2 + 38);
    }
    // time axis
    g.fillStyle = css("--muted"); g.font = "11px system-ui";
    g.fillText(tfmt(t0, 5), left, Hh - 6);
    const tl = tfmt(t1, 5); g.fillText(tl, W - right - g.measureText(tl).width, Hh - 6);
    ovPlot.textContent = opt.history
      ? t("r(t) of the body (dashed: the ghost) and the lag of its clock 1 − dτ/dt; the axis is the world's time t (the whole segment).")
      : t("r(t) of the body (dashed: the ghost) and the lag of its clock 1 − dτ/dt; the axis is the world's time t (the last orbits).");
  }
  function axes(g, x, y, w, h, lo, hi, fmt, title) {
    g.save(); g.strokeStyle = css("--line"); g.strokeRect(x, y, w, h);
    g.fillStyle = css("--muted"); g.font = "10px system-ui";
    for (let k = 0; k <= 4; k++) {
      const v = lo + (hi - lo) * k / 4, Y = y + h * (1 - k / 4);
      g.strokeStyle = css("--grid"); g.beginPath(); g.moveTo(x, Y); g.lineTo(x + w, Y); g.stroke();
      g.fillText(fmt(v), 2, Y + 3);
    }
    g.fillStyle = css("--ink"); g.font = "11px system-ui"; g.fillText(title, x + 4, y - 6);
    g.restore();
  }
  function series(g, c, i0, n, X, Y, col, dash) {
    if (!c || n - i0 < 1) return;
    g.save(); g.strokeStyle = col; g.lineWidth = 1.4; g.setLineDash(dash || []); g.beginPath();
    let px = -1e9;
    for (let i = i0; i < n; i++) {
      const x = X(c.t[i]);
      if (i === i0) g.moveTo(x, Y(i)); else if (x - px >= 0.5 || i === n - 1) g.lineTo(x, Y(i)); else continue;
      px = x;
    }
    g.stroke(); g.restore();
  }
  function dot(g, x, y, col) { g.save(); g.fillStyle = col; g.beginPath(); g.arc(x, y, 4, 0, 2 * Math.PI); g.fill(); g.restore(); }

  // --- panels -----------------------------------------------------------------------------------------------
  function kv(rows) { return el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, k), el("span", { class: "mono" }, v)])); }
  function drawOrbPanel(frame, tw) {
    const s = segAt(tw);
    if (!H || !s) { orbBox.replaceChildren(); return; }
    const i = s.init, el2 = s.elements;
    const peri = (apsides.get(s.seg) || []).filter((a) => a.kind === "peri" && a.t <= tw);
    const last = peri.length ? peri[peri.length - 1] : null;
    const mean = peri.length >= 2 ? (peri[peri.length - 1].shift / (peri.length - 1)) : null;
    const rows = [[t("Law"), H.law === "GR" ? t("GR (Schwarzschild)") : t("Newton (approximation)")],
      [t("Central body"), H.body.R > 0
        ? t("{m:.6g} M☉, R = {R:.6g} M ({km:.6g} km)", { m: H.body.mass_msun, R: H.body.R, km: H.body.R_km })
        : t("{m:.6g} M☉, {body}", { m: H.body.mass_msun, body: H.law === "GR" ? t("a black hole") : t("a point mass") })],
      ["1 M = GM/c²", length(M(), { au: AU_M }, 6)], [t("Segment"), t("{seg:d}: {reason}", { seg: s.seg, reason: s.reason })], [t("Orbit"), t(s.kind_text)],
      [t("Start"), `r = ${lenM(i.r0)}`], [t("Speed"), t("{v:.7g} c = {k:.6g} × circular, angle {a:.5g}°", { v: i.v, k: i.k, a: i.alpha })]];
    if (H.law === "GR") rows.push([t("e (energy per mc²)"), num(s.e, 12)], ["e² − 1", num(s.em1, 8)], [t("l (angular momentum, M·c)"), num(s.l, 10)]);
    else rows.push([t("E (per c²)"), num(s.E, 10)], ["h (M·c)", num(s.h, 10)]);
    if (s.r_peri && s.kind !== "plunge") rows.push([t("Periapsis"), lenM(s.r_peri)]);
    if (s.r_apo) rows.push([t("Apoapsis"), lenM(s.r_apo)]);
    if (el2) rows.push([t("Eccentricity ε"), num(el2.ecc, 8)], [t("p (parameter)"), lenM(el2.p)], ["a = p/(1 − ε²)", lenM(el2.a)]);
    rows.push([t("Periapses passed"), String(peri.length)]);
    if (last && last.adv !== null) rows.push([t("Advance over the last orbit"), angFmt(last.adv)]);
    if (mean !== null) rows.push([t("Advance, mean"), angFmt(mean)]);
    if (s.adv_exact !== null && s.adv_exact !== undefined) rows.push([t("Exact formula (reference)"), angFmt(s.adv_exact)]);
    if (last && last.dt) rows.push([t("Radial period (t)"), tfmt(last.dt)]);
    if (frame && frame.n_lap) rows.push([t("Turns in φ"), String(frame.n_lap)]);
    const items = [kv(rows)];
    const gi = ghostInfo.get(s.seg);
    if (gi) {
      const grow = [[t("Law"), lawShort(gi.law)], [t("Orbit"), t(gi.kind_text)]];
      if (gi.r_peri && gi.kind !== "plunge") grow.push([t("Periapsis"), lenM(gi.r_peri)]);
      if (gi.r_apo) grow.push([t("Apoapsis"), lenM(gi.r_apo)]);
      const gp = (gapsides.get(s.seg) || []).filter((a) => a.t <= tw);
      grow.push([t("Periapses passed"), String(gp.length)]);
      items.push(el("h5", { style: { margin: "10px 0 4px" } }, t("Ghost (dashed)")), kv(grow));
    }
    orbBox.replaceChildren(...items);
  }
  function drawClockPanel(frame, tw) {
    if (!H || !frame) { clockBox.replaceChildren(); return; }
    const since = tw - frame.t_launch;
    const rows = [[t("t, the world's time (a distant observer)"), tfmt(tw, 10)], [t("t since the launch of the body"), tfmt(since, 10)],
      [t("τ, the body's clock since the launch"), tfmt(frame.tau, 10)],
      [t("τ / t (mean since the launch)"), since > 0 ? num(frame.tau / since, 12) : "—"],
      [t("dτ/dt now"), num(frame.rate, 12)], ["1 − dτ/dt", num(frame.deficit, 10)]];
    if (H.law === "GR") {
      rows.push(["   " + t("gravity √(1 − 2M/r)"), num(frame.grav, 12)], ["   " + t("motion √(1 − v²/c²)"), num(frame.kin, 12)]);
    }
    rows.push([t("r now"), lenM(frame.r)], [t("Speed (a static observer)"), frame.v === null || frame.v === undefined ? "—" : num(frame.v, 8) + " c"]);
    if (frame.ghost) rows.push([t("Ghost's clock τ"), tfmt(frame.ghost.tau, 10)]);
    const items = [kv(rows)];
    if (H.law === "GR") items.push(el("div", { class: "help" },
      t("dτ/dt = (1 − 2M/r)/e along the geodesic: the product of the gravitational factor (the clock of a static observer at this r) and the factor of the speed relative to that observer.")));
    if (!frame.alive) items.push(el("div", { class: "st-bad" }, END_TEXT[frame.status] || frame.status));
    if (frame.lag === true) items.push(el("div", { class: "st-bad" }, t("The computation cannot keep up with the chosen speed: the world runs slower.")));
    clockBox.replaceChildren(...items);
  }

  const END_TEXT = { horizon: t("at the horizon (r − 2M = 2·10⁻⁶ M; beyond it t → ∞)"), surface: t("fell onto the surface"),
    center: t("fell into the centre"), escape: t("gone to infinity") };
  const lawShort = (law) => (law === "GR" ? t("GR") : t("Newton"));

  return {
    center, rightPanels,
    help: () => el("div", {},
      el("h4", {}, t("What is on the screen")),
      el("p", {}, t("On the left: the orbit plane from above. The solid line is the orbit computed in this run by the world's laws; it appears as the world's time t (the clock of a distant static observer) reaches it. Diamonds are periapses (the numbers are their angle φ), squares apoapses; the solid ray from the centre is the latest periapsis, the dashed one the first: the angle between them is the accumulated periapsis advance. The orange dashed line is the “ghost”: the orbit under the other theory (GR ↔ Newton) from the same initial data; it does not affect the world.")),
      el("p", {}, t("Circles (GR): the horizon 2M, the photon sphere 3M (the circular orbit of light), the marginally bound circular orbit 4M, the ISCO 6M (innermost stable circular orbit); the radii come from the engine (lfphys.core.gravity.kerr at zero spin).")),
      el("p", {}, t("On the right: r(t) and the lag of the body's clock 1 − dτ/dt: the body's clock runs slower because of gravity (√(1 − 2M/r)) and because of its speed relative to the static observer (√(1 − v²/c²)).")),
      el("p", {}, t("The launch of the body (r₀, the speed as a fraction of the circular one, the angle to the tangent) changes apply at once: the body is launched again at the world's current moment from its current direction to the centre. “Push” changes the speed along the motion instantly; the body's clock keeps running. The law of gravitation and the mass and radius of the central body are the world's laws: changing them is a new world in the same run.")),
      el("p", {}, t("A fall through the horizon: for a distant observer the body only approaches r = 2M asymptotically (the time t grows logarithmically), while the body's proper time to the horizon is finite; the computation stops at r − 2M = 2·10⁻⁶ M."))),
    reset() {
      H = null; units = null; liveVals = {}; segs = []; trails = new Map(); gtrails = new Map(); apsides = new Map();
      gapsides = new Map(); ghostInfo = new Map(); lastT = 0;  // fittedSeg kept: the same world keeps its view
    },
    // key frames (player.js): the columns and lists only grow (their objects and lengths are kept, so a ghost orbit
    // switched off later comes back); the small maps and the live values are copied
    snapshot() {
      const lens = (m) => new Map([...m].map(([k, v]) => [k, { o: v, n: Array.isArray(v) ? v.length : v.n }]));
      return { segs: segs.length, trails: lens(trails), gtrails: lens(gtrails), apsides: lens(apsides),
               gapsides: lens(gapsides), ghostInfo: new Map(ghostInfo), liveVals: { ...liveVals } };
    },
    restore(k) {
      const back = (m) => new Map([...m].map(([key, { o, n }]) => { if (Array.isArray(o)) o.length = n; else o.n = n; return [key, o]; }));
      segs.length = k.segs; trails = back(k.trails); gtrails = back(k.gtrails); apsides = back(k.apsides);
      gapsides = back(k.gapsides); ghostInfo = new Map(k.ghostInfo); liveVals = { ...k.liveVals };
    },
    onHeader(meta) {
      H = meta; units = meta.units; liveVals = { ...(meta.live || {}) };
      if (meta.world !== fittedWorld) { fittedWorld = meta.world; fittedSeg = -1; }  // a new world is framed anew
    },
    onMessage(meta, blobs) {
      switch (meta.type) {
        case "segment": segs.push(meta); ghostInfo.set(meta.seg, meta.ghost || null); break;
        case "trail": push(trails, meta.seg, blobs, true); break;
        case "gtrail": push(gtrails, meta.seg, blobs, false); break;
        case "apsis": { if (!apsides.has(meta.seg)) apsides.set(meta.seg, []); apsides.get(meta.seg).push(meta); break; }
        case "gapsis": { if (!gapsides.has(meta.seg)) gapsides.set(meta.seg, []); gapsides.get(meta.seg).push(meta); break; }
        case "ghost": {
          ghostInfo.set(meta.seg, meta.info || null);
          if (!meta.info) { gtrails.delete(meta.seg); gapsides.delete(meta.seg); }
          break;
        }
        case "event":
          if (meta.kind === "action" && meta.name === "set" && meta.args) Object.assign(liveVals, meta.args);
          break;
        default: break;
      }
      ctx.requestRender();
    },
    render(frame, tw) {
      if (!H) return;
      lastT = tw;
      drawOrbit(frame, tw);
      drawPlots(frame, tw);
      drawOrbPanel(frame, tw);
      drawClockPanel(frame, tw);
    },
  };
}
