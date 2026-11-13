// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The playground's panels (plan P15.0; owner, 2026-10-28), shared by every section's view: the palette (add an object
// at the current moment), the scene's objects (select, duplicate, remove), the inspector (the selected object's
// parameters, applied at once: command "scene" set), the scene's changes in time (click: to that moment), the probes'
// readings, the scene as a file (save / load: a new world from it), and the record's window (owner, 2026-10-29: the
// record is the last minutes unless "keep the record" is on; then what the window holds and all that follows is kept).
// Drawing is the section's; this module only shows and sends. A view is a function of the messages fed: the latest
// scene message, the scene's events and the record's state (snapshot / restore for the player's key frames).
//
// Direct manipulation (plan P16.2; the integrator's API of 2026-11-11, §1): a click on an object in the 3-D scene or in
// a slice window selects it (picked from the frame's `at[id]` and the type's declared `size`, else within a few pixels;
// the smallest object under the pointer wins); dragging it moves a ghost — in the plane through the object
// perpendicular to the view, in the plane of a 2-D world, in a window's plane, or along the axis of an axis-bound handle
// — and the release sends ONE scene edit (op "edit") with the type's position handles; Shift + drag throws: the velocity
// is the pointer's world displacement over the last 100 ms, divided by that wall time and by the playback rate (world
// time per wall second), times the throw scale shown in «Объекты сцены» (automatic unless set by hand: 1, or, for a type
// that declares `velocity_max`, half of it for a flick of the view's width per wall second; a throw is clamped to
// `velocity_max` and says so); Delete removes the selected object, Esc
// cancels a drag. A refusal of the world is shown (the player's toast) and the ghost snaps back. A gesture that starts
// on an object is never the camera's. Edits respect the read-only history and a busy world (ctx.readOnly, ctx.busy).
import { fmtField, parseNum, t } from "./i18n.js";
import { control, el, fill, num, numberInput, panel, time, toast } from "./ui.js";
import { armPick, isFixedWindow, picking, redrawWindows, setFrameOverlay, setWindowManipulator } from "./slices.js";

// a scene file is at most 900 000 characters (the server's limit for a JSON parameter, below the socket's message
// limit: review B6-F20)
async function sceneText(f) {
  const text = await f.text();
  if (text.length > 900000) throw new Error(t("the scene file is longer than {max:d} characters ({n:d})", { max: 900000, n: text.length }));
  return text;
}

const KIND_LABEL = { body: t("Bodies"), particle: t("Particles"), light: t("Light"), field: t("Fields"), potential: t("Potentials"),
                     detector: t("Detectors"), probe: t("Probes"), observer: t("Observers"), source: t("Sources") };

// The point of the plane z = zc under a screen point (client px) of the 3-D view: the plane's image is a homography of
// the plane, fixed by four of its points (scene3d's screenOf), inverted (review UX-ui U4: «a click in the scene to choose
// the point»). Null when the plane is seen edge on.
function planePoint(scene, cx, cy, box) {
  const b = box || [[-1, -1, 0], [1, 1, 0]], zc = 0.5 * (b[0][2] + b[1][2]);
  const P = [[b[0][0], b[0][1]], [b[1][0], b[0][1]], [b[1][0], b[1][1]], [b[0][0], b[1][1]]];
  const Q = P.map(([x, y]) => scene.screenOf([x, y, zc]));
  // H maps (x, y, 1) to (u w, v w, w); h33 = 1: eight unknowns from four point pairs
  const A = [], r = [];
  for (let i = 0; i < 4; i++) {
    const [x, y] = P[i], [u, v] = Q[i];
    A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); r.push(u);
    A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); r.push(v);
  }
  const h = solve(A, r);
  if (!h) return null;
  const [a, bb, c, d, e, f, g, k] = h;
  // invert the 3 x 3 matrix [[a b c] [d e f] [g k 1]] applied to (cx, cy, 1)
  const M = [[a, bb, c], [d, e, f], [g, k, 1]];
  const det = M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1]) - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0]) + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]);
  if (!Number.isFinite(det) || Math.abs(det) < 1e-12) return null;
  const inv = [
    [M[1][1] * M[2][2] - M[1][2] * M[2][1], M[0][2] * M[2][1] - M[0][1] * M[2][2], M[0][1] * M[1][2] - M[0][2] * M[1][1]],
    [M[1][2] * M[2][0] - M[1][0] * M[2][2], M[0][0] * M[2][2] - M[0][2] * M[2][0], M[0][2] * M[1][0] - M[0][0] * M[1][2]],
    [M[1][0] * M[2][1] - M[1][1] * M[2][0], M[0][1] * M[2][0] - M[0][0] * M[2][1], M[0][0] * M[1][1] - M[0][1] * M[1][0]]];
  const X = inv[0][0] * cx + inv[0][1] * cy + inv[0][2], Y = inv[1][0] * cx + inv[1][1] * cy + inv[1][2], Wt = inv[2][0] * cx + inv[2][1] * cy + inv[2][2];
  if (!Number.isFinite(Wt) || Math.abs(Wt) < 1e-15) return null;
  return [X / Wt, Y / Wt, zc];
}
function solve(A, r) {  // Gaussian elimination with partial pivoting
  const n = r.length, M = A.map((row, i) => [...row, r[i]]);
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let i = c + 1; i < n; i++) if (Math.abs(M[i][c]) > Math.abs(M[p][c])) p = i;
    if (Math.abs(M[p][c]) < 1e-14) return null;
    [M[c], M[p]] = [M[p], M[c]];
    for (let i = 0; i < n; i++) {
      if (i === c) continue;
      const f = M[i][c] / M[c][c];
      for (let j = c; j <= n; j++) M[i][j] -= f * M[c][j];
    }
  }
  return M.map((row, i) => row[n] / row[i]);
}
const round = (x) => { const a = Math.abs(x); if (!a) return 0; const q = 10 ** (Math.floor(Math.log10(a)) - 3); return Math.round(x / q) * q; };

// opts: onSelect(id), describeProbe(obj, reading), and the 3-D environment of the view (`env`, or its `scene`): with it
// the pre-placement form can take its point from a click in the 3-D scene (slice windows always work)
export function createPlayground(ctx, { onSelect = () => {}, describeProbe = null, env = null, scene: scene3 = null } = {}) {
  let P = null;               // header.playground: palette, limits
  let scene = null;           // the latest scene message: {rev, objects, palette_state?}
  let changes = [];           // the scene's events: {t, text, name}
  let rec = null;             // the record's window: {window_s, recording, kept_from_t, trimmed, size}
  let selected = null;
  let exportAsked = false;
  let placing = null;         // the pre-placement form: {ot, values, position, ctls}
  // the 3-D scene: the view's (opts), else the page's 3-D view (scene3d keeps its api on its element)
  const s3 = () => scene3 || (env && env.scene) || (document.querySelector(".s3d-view") || {}).__scene3d || null;
  const runId = new URLSearchParams(location.search).get("id");

  const paletteBox = el("div", {}), placeBox = el("div", {}), objectsBox = el("div", {}), inspectorBox = el("div", {}), nowBox = el("div", { class: "kv" });
  const changesBox = el("div", { class: "events" }), probesBox = el("div", {}), fileBox = el("div", {}), recBox = el("div", {});
  const ro = () => (ctx.readOnly ? ctx.readOnly() : "");
  // while the world computes a change, the palette and the inspector wait (review UX-ui U9: repeated clicks queued)
  const busy = () => (ctx.busy ? ctx.busy() : null);
  const why = () => ro() || (busy() ? t("The world is computing the previous change — wait (or cancel it at the top).") : "");
  const byType = (tt) => (P ? P.palette.find((x) => x.type === tt) : null);
  const objById = (id) => (scene ? scene.objects.find((o) => o.id === id) : null);

  // the inspector's edits are sent even while the world computes (they apply in order, and the focus stays in the field
  // the owner is typing in: U10); additions, copies and removals wait (U9)
  function send(args) {
    const w = args.op === "set" || args.op === "label" ? ro() : why();
    if (w) { toast(w, "notice"); return false; }
    ctx.send("scene", args);
    return true;
  }

  // --- palette ----------------------------------------------------------------------------------------------
  // a button per type; one the world cannot take now is disabled with the reason, as its tooltip and under it (U22, U7)
  function typeWhy(ot) {
    const n = scene ? scene.objects.length : 0;
    const count = scene ? scene.objects.filter((o) => o.type === ot.type).length : 0;
    if (n >= P.max_objects) return t("the scene already holds {n:d} objects — no more", { n: P.max_objects });
    if (ot.limit !== null && ot.limit !== undefined && count >= ot.limit) return t("at most {n:d} in a scene", { n: ot.limit });
    return t(((scene && scene.palette_state) || {})[ot.type]);
  }
  function drawPalette() {
    if (!P) { fill(paletteBox, el("div", { class: "muted" }, t("waiting for the world…"))); return; }
    const groups = new Map();
    for (const ot of P.palette) {
      if (!groups.has(ot.kind)) groups.set(ot.kind, []);
      groups.get(ot.kind).push(ot);
    }
    const off = why();
    fill(paletteBox,
      el("div", { class: "help" }, t("Click — set the parameters and the place, then “Place” (Shift+click — at once, with the default parameters). The object appears at the world's current moment; then it can be changed in the inspector.")),
      ...[...groups].map(([kind, list]) => el("div", { class: "pg-group" },
        el("div", { class: "muted" }, KIND_LABEL[kind] || kind),
        el("div", { class: "pg-buttons" }, list.map((ot) => {
          const w = typeWhy(ot);
          const b = el("button", { title: w ? t("Not possible now: {why}", { why: w }) : t(ot.help || ot.label), disabled: !!off || !!w,
                                   class: placing && placing.ot.type === ot.type ? "on" : "",
                                   style: { borderLeft: `4px solid ${ot.color}` },
                                   onclick: (e) => { if (e.shiftKey) send({ op: "add", type: ot.type, values: {} }); else openPlace(ot); } }, "＋ " + t(ot.label));
          return w ? el("span", { class: "pg-btn" }, b, el("span", { class: "pg-why" }, w)) : b;
        })))));
  }

  // --- the pre-placement form: the type's parameters set before the object exists, its point typed or clicked in the
  // scene or a slice window (review UX-ui U4); the world completes the values (lfviz.playground `place`) ------------
  function openPlace(ot) {
    if (placing && placing.ot.type === ot.type) { closePlace(); return; }
    const values = {};
    for (const p of ot.params) values[p.id] = p.default;
    placing = { ot, values, position: null, ctls: {} };
    drawPlace(); drawPalette();
    const card = placeBox.firstChild;
    if (card && card.scrollIntoView) card.scrollIntoView({ block: "nearest" });
  }
  function closePlace() { placing = null; armPick(null); fill(placeBox); drawPalette(); }
  function drawPlace() {
    if (!placing) { fill(placeBox); return; }
    const { ot, values } = placing;
    const typing = Object.entries(placing.ctls).find(([, c]) => c.input && document.activeElement === c.input);  // keep it
    placing.ctls = {};
    const shownP = (p) => !p.hidden && shown(p, values);
    const rows = ot.params.filter(shownP).map((p) => {
      const c = control(p, values[p.id], (v) => { values[p.id] = v; if (["x", "y", "z"].includes(p.id)) placing.position = null; if (p.type === "select" || p.type === "bool") drawPlace(); });
      placing.ctls[p.id] = c;
      return c.el;
    });
    const hasXY = ot.params.some((p) => p.id === "x") && ot.params.some((p) => p.id === "y");
    const canClick = hasXY && (!!s3() || !!document.querySelector(".sw-canvas"));
    const pickBtn = canClick ? el("button", { class: picking() ? "toggle on" : "", title: t("Click a point in the 3-D scene (on the plane z at the middle of the region) or in a slice window: x, y are taken from there"),
      onclick: () => armScenePick() }, picking() ? t("⌖ click in the scene… (Esc — cancel)") : t("⌖ Point at a place in the scene")) : null;
    const w = typeWhy(ot);
    fill(placeBox, el("div", { class: "pg-place" },
      el("div", { class: "name" }, "＋ " + t("{type}: before placing it", { type: ot.label })),
      ot.help ? el("div", { class: "help" }, t(ot.help)) : null,
      pickBtn, placing.position ? el("div", { class: "muted" }, t("the point from the scene: {p}", { p: placing.position.map((x) => num(x, 4)).join(", ") })) : null,
      rows,
      w ? el("div", { class: "warn" }, t("Not possible now: {why}", { why: w })) : null,
      el("div", { class: "row" },
        placing.go = el("button", { class: "primary", disabled: !!why() || !!w, onclick: () => place() }, t("Place")),
        el("button", { onclick: closePlace }, t("Cancel")))));
    if (typing && placing.ctls[typing[0]] && placing.ctls[typing[0]].input) {
      const inp = placing.ctls[typing[0]].input;
      if (inp.classList.contains("num")) inp.value = typing[1].input.value;  // what was typed and not yet committed
      inp.focus();
    }
  }
  function place() {
    if (!placing) return;
    const values = { ...placing.values };
    if (placing.position) values.position = placing.position;
    if (send({ op: "add", type: placing.ot.type, values })) closePlace();
  }
  function setPoint(pt) {
    if (!placing || !pt) return;
    placing.position = pt.map(round);
    for (const [i, k] of ["x", "y", "z"].entries()) if (k in placing.values && Number.isFinite(pt[i])) placing.values[k] = round(pt[i]);
    drawPlace();
  }
  let sceneClick = null;
  function armScenePick() {
    if (picking()) { armPick(null); drawPlace(); return; }
    armPick((pt) => { disarmScene(); setPoint(pt); });  // a slice window's point
    const sc = s3();
    if (sc && sc.el && !sceneClick) {  // or the 3-D scene's: the plane z = the middle of the region under the pointer
      sceneClick = (e) => {
        if (!picking()) { disarmScene(); return; }
        if (e.target.tagName !== "CANVAS") return;  // the view's own buttons keep working
        const box = (sc.state && sc.state.box) || null;
        const pt = planePoint(sc, e.clientX, e.clientY, box);
        e.stopPropagation(); e.preventDefault();
        armPick(null); disarmScene();
        if (pt) setPoint(pt); else toast(t("The plane is seen edge on: turn the scene or type x, y as numbers"), "notice");
      };
      sc.el.addEventListener("click", sceneClick, true);
    }
    drawPlace();
  }
  function disarmScene() { const sc = s3(); if (sceneClick && sc && sc.el) sc.el.removeEventListener("click", sceneClick, true); sceneClick = null; }
  window.addEventListener("keydown", (e) => { if (e.key === "Escape" && picking()) { armPick(null); disarmScene(); drawPlace(); } });

  // --- the camera on an object (review UX-3d A6): "◎ Centre" puts the 3-D view's pivot on the object, "Follow"
  // keeps it there while the object moves; following stops when the owner turns or pans the view by hand (a zoom keeps
  // it) or the object is gone. Where an object is: the frame's `at[id]` when the section sends it, else the frame's
  // `ids` with its array `pos` (one point per id, as p01's bodies), else the object's set x, y, z.
  let lastFrame = null, lastBlobs = null, follow = null, headerWorld = null;
  function posOf(id) {
    const f = lastFrame, b = lastBlobs || (ctx.frameBlobs ? ctx.frameBlobs() : null);
    if (f && f.at && Array.isArray(f.at[id]) && f.at[id].length >= 2) return [f.at[id][0], f.at[id][1], f.at[id][2] ?? 0];
    const ids = f && f.ids, pos = b && b.pos;
    if (Array.isArray(ids) && pos && pos.length === 3 * ids.length) {
      const i = ids.indexOf(id);
      if (i >= 0 && Number.isFinite(pos[3 * i])) return [pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]];
    }
    const o = objById(id), v = o ? o.values : {};
    if (o && Number.isFinite(v.x) && Number.isFinite(v.y)) {
      const sc = s3(), bx = sc && sc.state && sc.state.box;
      return [v.x, v.y, Number.isFinite(v.z) ? v.z : bx ? 0.5 * (bx[0][2] + bx[1][2]) : 0];
    }
    return null;
  }
  const sub3 = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]], len3 = (a) => Math.hypot(a[0], a[1], a[2]);
  function camNow(sc) { const c = sc.cameraState(); const d = sub3(c.pos, c.target), r = len3(d) || 1; return { target: c.target, dir: d.map((x) => x / r), r }; }
  function centerOnObject(id, { quiet = false } = {}) {
    const sc = s3(), p = posOf(id);
    if (!sc || !sc.centerOn || !p) { if (!quiet) toast(t("Centring works in the 3-D scene, on an object with a position"), "notice"); return false; }
    sc.centerOn(p);
    if (follow && follow.id === id) follow.cam = camNow(sc);
    return true;
  }
  function setFollow(id) {
    follow = id ? { id, cam: null } : null;
    if (id && !centerOnObject(id)) follow = null;
    drawFollow();
  }
  function stepFollow() {
    if (!follow || (drag && drag.moved)) return;  // the view holds still under a drag (its plane was fixed at the press)
    const sc = s3();
    if (!sc || !objById(follow.id)) { setFollow(null); return; }
    const c = camNow(sc), k = follow.cam;
    if (k) {
      const scale = Math.max(k.r, 1e-300);
      const zoom = Math.abs(c.r - k.r) > 1e-6 * scale;
      const turned = len3(sub3(c.dir, k.dir)) > 1e-5;
      const panned = len3(sub3(c.target, k.target)) > 1e-6 * scale;
      if (!zoom && (turned || panned)) { setFollow(null); toast(t("Following the object is off: the view was turned or moved by hand"), "notice", 4000); return; }
    }
    centerOnObject(follow.id, { quiet: true });
  }
  function drawFollow() {
    if (insp.follow) {
      const on = !!follow && follow.id === selected;
      insp.follow.classList.toggle("on", on);
      insp.follow.title = on ? t("Following is on: the view keeps the object in the centre; turn or move the view by hand and it goes off") : t("Keep the view's centre on the object while it moves");
    }
    for (const [id, r] of rowEls) if (r.eye) r.eye.style.display = follow && follow.id === id ? "" : "none";
  }

  // --- direct manipulation (plan P16.2) ----------------------------------------------------------------------------
  const THROW_MS = 100;        // the pointer's motion over the last 100 ms makes a throw's velocity
  const MIN_PX = 9;            // the smallest pick radius on the screen (CSS px)
  const SNAP_MS = 220;         // a refused ghost goes back in this time
  const AUTO_CROSS_S = 2;      // the automatic throw: a brisk flick crosses the world's region in this many wall seconds
  const AX = ["x", "y", "z"];
  const vsub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]], vadd = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const vmul = (a, k) => [a[0] * k, a[1] * k, a[2] * k], vdot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const unitv = (a) => { const L = len3(a) || 1; return vmul(a, 1 / L); };
  const e3 = (k) => [0, 1, 2].map((i) => (i === k ? 1 : 0));
  // the axis an axis-bound handle names: "x" | "y" | "z", 0 | 1 | 2 or "0" | "1" | "2" (lfviz.playground.axis_index)
  function axisIdx(v) {
    if (typeof v === "string") { const i = AX.indexOf(v); return i >= 0 ? i : ["0", "1", "2"].includes(v) ? Number(v) : null; }
    return v === 0 || v === 1 || v === 2 ? v : null;
  }
  const handlesOf = (o) => { const ot = o && byType(o.type); return ot && ot.handles ? ot.handles : null; };
  const sizeOf = (o) => { const h = handlesOf(o), r = h && h.size ? Number(o.values[h.size]) : NaN; return Number.isFinite(r) && r > 0 ? r : 0; };
  // the throw's scale: null = automatic (scaleFor: from the world's own scale, the region and the playback rate); a
  // number set by hand overrides it for every object
  let throwScale = null;
  try { const v = Number(localStorage.getItem("lf.throwScale")); if (v > 0 && Number.isFinite(v)) throwScale = v; } catch (e) { /* storage off */ }
  let lastRelease = "";  // the readout at the last release (tests)
  let drag = null;   // the gesture: {o, h, where: "3d" | window helper, G (its geometry), offset, start, ghost, samples, moved, why}
  let pend = null;   // an edit sent and not answered yet: {id, ghost, start, vel, timer}
  let snap = null;   // a refused ghost going back: {id, from, to, t0}

  // why the object cannot be dragged now ("" when it can)
  function dragWhy(o) {
    const w = ro(); if (w) return w;
    if (busy()) return t("The world is computing the previous change — wait (or cancel it at the top).");
    if (pend) return t("The previous move is still being applied — wait.");
    const h = handlesOf(o);
    if (!h || !h.position) return t("“{label}” cannot be dragged: an object of this type has no position moved by hand; change it in the inspector", { label: o.label });
    if (!Array.isArray(h.position) && axisIdx(o.values[h.position.axis_param]) === null) return t("“{label}”: the axis is not set", { label: o.label });
    return "";
  }
  // the coordinates a 2-element position names: the plane of a 2-D world (its normal axis k), else x, y
  const planeAxes = (k) => [0, 1, 2].filter((i) => i !== (k ?? 2));

  // the geometry of a drag in the 3-D view: a plane through the object (perpendicular to the view; the world's plane in
  // a 2-D world or for a 2-element position) or the line of an axis-bound handle
  function geom3d(sc, o, p0) {
    const h = handlesOf(o), k2 = sc.state ? sc.state.plane2d : null;
    if (!Array.isArray(h.position)) { const ax = axisIdx(o.values[h.position.axis_param]); return { kind: "axis", p0, a: e3(ax), ax }; }
    if (k2 !== null && k2 !== undefined) return { kind: "plane", p0, n: e3(k2), k2 };
    if (h.position.length === 2) return { kind: "plane", p0, n: e3(2), k2: 2 };
    return { kind: "plane", p0, n: unitv(sc.viewDir()) };
  }
  // the point of the drag's geometry under an eye ray (null: the plane seen edge on, the axis along the ray)
  function onRay(G, ray) {
    const d = unitv(ray.dir);
    if (G.kind === "plane") {
      const den = vdot(d, G.n);
      if (Math.abs(den) < 1e-4) return null;
      const tt = vdot(vsub(G.p0, ray.origin), G.n) / den;
      return tt > 0 ? vadd(ray.origin, vmul(d, tt)) : null;
    }
    const w = vsub(G.p0, ray.origin), b = vdot(d, G.a), den = 1 - b * b;
    if (den < 1e-4) return null;
    return vadd(G.p0, vmul(G.a, (b * vdot(d, w) - vdot(G.a, w)) / den));
  }
  // the geometry of a drag in a window: its plane (the object's offset from it kept), or the axis when it lies in it
  function geomWin(hw, o, p0) {
    const h = handlesOf(o), n = unitv(hw.plane.normal), dn = vdot(vsub(p0, hw.plane.origin), n);
    if (!Array.isArray(h.position)) {
      const ax = axisIdx(o.values[h.position.axis_param]);
      if (Math.abs(n[ax]) > 0.98) return { why: t("the axis {axis} crosses the plane of this window: drag “{label}” in the 3-D scene or in another window", { axis: AX[ax], label: o.label }) };
      return { kind: "axis", p0, a: e3(ax), ax, n, dn };
    }
    if (h.position.length === 2 && Math.abs(n[2]) < 0.999) return { why: t("“{label}” lives in the plane z = const: drag it in the window of that plane or in the 3-D scene", { label: o.label }) };
    return { kind: "plane", p0, n, dn };
  }
  const onWin = (G, P) => {  // the window's point under the pointer, put back at the object's distance from the plane
    if (!P) return null;
    const q = vadd(P, vmul(G.n, G.dn));
    if (G.kind === "axis") { const out = [...G.p0]; out[G.ax] = q[G.ax]; return out; }
    return q;
  };

  // the objects that can be picked: those with a place (the frame's at[id], else the section's arrays or values)
  function candidates() {
    const out = [];
    for (const o of scene ? scene.objects : []) { const p = posOf(o.id); if (p) out.push({ o, p }); }
    return out;
  }
  // the object under a screen point of the 3-D view: within its declared size or MIN_PX; the smallest one wins
  function hit3d(sc, x, y) {
    let best = null;
    for (const { o, p } of candidates()) {
      const q = sc.project(p);
      if (!q.inside) continue;
      const reff = Math.max(sizeOf(o) / sc.pixelSize(p), MIN_PX), d = Math.hypot(x - q.x, y - q.y);
      if (d > reff) continue;
      if (!best || reff < best.reff - 1e-6 || (Math.abs(reff - best.reff) <= 1e-6 && (d < best.d - 1e-6 || (Math.abs(d - best.d) <= 1e-6 && q.z < best.z)))) best = { o, p, reff, d, z: q.z };
    }
    return best;
  }
  // in a window: objects near its plane (within their size, or 3 % of the window's width), by their projection
  function hitWin(hw, x, y) {
    const r = hw.el.getBoundingClientRect(), mx = x - r.left, my = y - r.top, n = unitv(hw.plane.normal);
    const tol = 0.03 * hw.el.clientWidth / hw.unitPx;
    let best = null;
    for (const { o, p } of candidates()) {
      const off = Math.abs(vdot(vsub(p, hw.plane.origin), n)), size = sizeOf(o);
      if (off > Math.max(size, tol)) continue;
      const [cx, cy] = hw.toCanvas(p), reff = Math.max(size * hw.unitPx, MIN_PX), d = Math.hypot(mx - cx, my - cy);
      if (d > reff) continue;
      if (!best || reff < best.reff - 1e-6 || (Math.abs(reff - best.reff) <= 1e-6 && d < best.d)) best = { o, p, reff, d };
    }
    return best;
  }

  // values sent: positions on a grid 1e-5 of the region (no float noise in the record), velocities to 4 digits; in the
  // world's units (those of `at` and of its time), never scaled for display
  const regionSize = () => { const sc = s3(); return (sc && sc.state && sc.state.size) || 1; };
  const qpos = (x) => { const st = 10 ** Math.floor(Math.log10(regionSize() * 1e-5)); return Math.round(x / st) * st; };
  const qvel = (v) => { const a = Math.abs(v); if (!a || !Number.isFinite(a)) return 0; const st = 10 ** (Math.floor(Math.log10(a)) - 3); return Math.round(v / st) * st; };
  function editValues(o, ghost, vel) {
    const h = handlesOf(o), sc = s3(), out = {};
    if (Array.isArray(h.position)) {
      const idx = h.position.length === 3 ? [0, 1, 2] : planeAxes(sc && sc.state ? sc.state.plane2d : null);
      h.position.forEach((pid, i) => { out[pid] = qpos(ghost[idx[i]]); });
      if (vel && Array.isArray(h.velocity)) h.velocity.forEach((pid, i) => { out[pid] = qvel(vel[idx[i]]); });
    } else out[h.position.param] = qpos(ghost[axisIdx(o.values[h.position.axis_param])]);
    return out;
  }
  // the playback rate in world time per wall second (the speed control's value, also while paused)
  const rate = () => { const r = ctx.speed ? Number(ctx.speed()) : 1; return r > 0 && Number.isFinite(r) ? r : 1; };
  // a throw's velocity: the world displacement over the last THROW_MS of the pointer (the position at that moment
  // interpolated between its events; the pointer is still after its last one), per wall second, over the rate, times
  // the throw scale
  function throwVelocity(now) {
    const S = drag.samples;
    if (S.length < 2) return [0, 0, 0];
    const t0 = Math.max(now - THROW_MS, S[0].t);
    let a = S[S.length - 1].p;  // the pointer still since its last event
    for (let i = 0; i < S.length - 1; i++) {
      if (S[i + 1].t <= t0) continue;
      const f = S[i + 1].t > S[i].t ? Math.min(1, Math.max(0, (t0 - S[i].t) / (S[i + 1].t - S[i].t))) : 1;
      a = vadd(S[i].p, vmul(vsub(S[i + 1].p, S[i].p), f));
      break;
    }
    const dt = (now - t0) / 1000;
    if (dt < 0.015) return [0, 0, 0];
    return vmul(vsub(S[S.length - 1].p, a), scaleFor(drag).k / (dt * rate()));
  }
  const canThrow = (o) => { const h = handlesOf(o); return !!(h && Array.isArray(h.position) && Array.isArray(h.velocity)); };
  // the largest speed the object's world carries (world length per world time), or null
  function vmaxOf(o) {
    const h = handlesOf(o), vm = h ? h.velocity_max : null;
    const v = typeof vm === "number" ? vm : typeof vm === "string" ? Number(o.values[vm]) : NaN;
    return v > 0 && Number.isFinite(v) ? v : null;
  }
  // the view's width at the object, in world lengths (the 3-D view at the object's depth, or the window)
  function viewWidth(d) {
    if (d.where === "3d") { const sc = s3(), cv = sc && sc.el.querySelector("canvas"); return sc && cv ? sc.pixelSize(d.p0) * cv.clientWidth : NaN; }
    return d.where.el.clientWidth / d.where.unitPx;
  }
  // The automatic scale (reviews LB1-F14, LB1-p02-ux X4: ×1 threw a molecule at 10¹² m/s, half the ceiling threw a
  // planet at 0,025 c): from the world's own scale — a brisk flick, the view's width in a wall second, throws the object
  // across the world's region in AUTO_CROSS_S wall seconds at the current playback rate, so what is thrown stays in
  // view whatever the zoom; never above half the largest speed the world declares (`velocity_max`, which still clamps)
  function scaleFor(d) {
    if (throwScale !== null) return { k: throwScale, auto: false };
    const W = viewWidth(d), R = regionSize(), r = rate();
    if (!(W > 0) || !(R > 0)) return { k: 1, auto: true };
    let v = R / (AUTO_CROSS_S * r);
    const vm = vmaxOf(d.o);
    if (vm) v = Math.min(v, 0.5 * vm);
    return { k: v * r / W, auto: true };
  }
  // the unit a throw is shown in: the type's `velocity_display` (its factor turns world units into it; the edit stays in
  // world units), else the velocity parameter's unit
  const velShow = (o) => { const h = handlesOf(o), d = h && h.velocity_display; return d && d.factor > 0 ? d : null; };
  function velUnit(o) {
    const d = velShow(o);
    if (d) return t(d.unit);
    const h = handlesOf(o), ot = byType(o.type), p = ot && h && h.velocity ? ot.params.find((q) => q.id === h.velocity[0]) : null;
    if (p && p.unit) return t(p.unit);
    const m = p ? /,\s*([^,(]+?)\s*(\(|$)/.exec(t(p.label)) : null;  // a unit the label carries: "Velocity vx, nm/s (…)"
    return m ? m[1] : t("length unit / time unit");
  }
  // a vector in the player's number format; a component below a millionth of the vector's length is the arithmetic's
  // round-off, shown as 0 (review LB1-p02-ux X6)
  const fmtVec = (v, n) => { const L = Math.hypot(...v.slice(0, n)); return "(" + v.slice(0, n).map((x) => num(Math.abs(x) <= 1e-6 * L ? 0 : x, 3)).join("; ") + ")"; };

  // the markers: the selected object (a ring and its name) and the ghost (3-D scene and windows)
  function selectionSpec() {
    const o = selected ? objById(selected) : null, p = o ? posOf(o.id) : null;
    return o && p ? { pos: p, radius: sizeOf(o), color: "#ffe066", text: t(o.label) } : null;
  }
  let selKey = "", selWinKey = "";
  function drawSelection() {
    const sc = s3(), spec = selectionSpec();
    if (sc && sc.setMarker) {
      const key = spec ? `${selected}|${spec.text}|${spec.radius}` : "";
      if (key !== selKey || !sc.moveMarker || !sc.moveMarker("sel", spec && spec.pos, spec && spec.radius)) { selKey = key; sc.setMarker("sel", spec); }
    }
    // the windows too, when the selected object moved (a view may have drawn its windows before the frame reached here)
    const wk = spec ? JSON.stringify([selected, spec.pos, spec.radius, spec.text]) : "";
    if (wk !== selWinKey) { selWinKey = wk; redrawWindows(); }
  }
  function ghostSpec() {
    const g = drag && drag.moved ? drag : pend ? pend : snap ? snap : null;
    if (!g) return null;
    const pos = g === snap ? g.at : g.ghost;
    return { pos, radius: sizeOf(g.o), color: g === snap ? "#ff8787" : "#8ce99a", ghost: true, from: g.start, vel: g.velShown || null,
             axis: g.G && g.G.kind === "axis" ? g.axisLine : null, text: g.text || "" };
  }
  function drawGhost() {
    const sc = s3(), spec = ghostSpec();
    if (sc && sc.setMarker) sc.setMarker("ghost", spec);
    redrawWindows();
  }
  // the framework's overlay of every window: the selected object and the ghost, at their projections on the plane, when
  // they are near it (as near as an object must be to be picked there)
  const drawnRings = {};  // window id -> where the selected object's ring was drawn last (canvas px; tests)
  const nearPlane = (hw, P, r) => Math.abs(vdot(vsub(P, hw.plane.origin), unitv(hw.plane.normal))) <= Math.max(r, 0.03 * hw.el.clientWidth / hw.unitPx);
  setFrameOverlay((g, hw) => {
    const ring = (P, r, color, dashed, text) => {
      const [x, y] = hw.toCanvas(P), R = Math.max(r * hw.unitPx * 1.25, 11);
      g.strokeStyle = color; g.lineWidth = 2; g.setLineDash(dashed ? [5, 4] : []);
      g.beginPath(); g.arc(x, y, R, 0, 2 * Math.PI); g.stroke(); g.setLineDash([]);
      if (text) {  // beside the ring, on the side where it fits in the window
        g.font = "12px system-ui"; g.fillStyle = color;
        const tw = g.measureText(text).width, right = x + R + 3 + tw <= hw.el.clientWidth - 4;
        g.fillText(text, right ? x + R + 3 : Math.max(2, x - R - 3 - tw), y - R + 2);
      }
      return [x, y];
    };
    const sel = selectionSpec();
    drawnRings[hw.id] = sel && nearPlane(hw, sel.pos, sel.radius) ? ring(sel.pos, sel.radius, sel.color, false, sel.text) : null;
    const gh = ghostSpec();
    if (gh && (nearPlane(hw, gh.pos, gh.radius) || nearPlane(hw, gh.from, gh.radius))) {
      const [x0, y0] = hw.toCanvas(gh.from), [x, y] = ring(gh.pos, gh.radius, gh.color, true, gh.text);
      g.strokeStyle = gh.color; g.setLineDash([4, 4]); g.beginPath(); g.moveTo(x0, y0); g.lineTo(x, y); g.stroke(); g.setLineDash([]);
      if (gh.axis) { const [a, b] = hw.toCanvas(gh.axis[0]), [c, d] = hw.toCanvas(gh.axis[1]); g.globalAlpha = 0.6; g.beginPath(); g.moveTo(a, b); g.lineTo(c, d); g.stroke(); g.globalAlpha = 1; }
      if (gh.vel) {
        const [x1, y1] = hw.toCanvas(vadd(gh.pos, gh.vel)), ang = Math.atan2(y1 - y, x1 - x);
        g.lineWidth = 2; g.beginPath(); g.moveTo(x, y); g.lineTo(x1, y1);
        g.lineTo(x1 - 8 * Math.cos(ang - 0.4), y1 - 8 * Math.sin(ang - 0.4)); g.moveTo(x1, y1); g.lineTo(x1 - 8 * Math.cos(ang + 0.4), y1 - 8 * Math.sin(ang + 0.4)); g.stroke();
      }
    }
  });

  // the axis of an axis-bound drag drawn across the region (box) through the object
  function axisLine(G) {
    const sc = s3(), b = (sc && sc.state && sc.state.box) || [[-1, -1, -1], [1, 1, 1]];
    const a = [...G.p0], c = [...G.p0]; a[G.ax] = b[0][G.ax]; c[G.ax] = b[1][G.ax];
    return [a, c];
  }

  function begin(o, p, G, where, e) {
    const why = G && G.why ? G.why : dragWhy(o);
    drag = { o, p0: p, G, where, start: p, ghost: p, samples: [], moved: false, why, x0: e.clientX, y0: e.clientY, warned: false, shift: e.shiftKey };
    // the throw's readout follows the hand also while the pointer rests (review LB1-F13: it kept «ограничено» from the
    // last move while the throw sent at the release was slower and not clamped): looked at only after THROW_MS without
    // a move, and redrawn only when its text changes (a redraw per tick slowed the pointer's own events)
    const d0 = drag;
    d0.tick = setInterval(() => {
      if (drag !== d0) { clearInterval(d0.tick); return; }
      const now = performance.now(), last = d0.samples.length ? d0.samples[d0.samples.length - 1].t : now;
      if (!d0.moved || d0.why || !d0.G || !d0.shift || now - last < THROW_MS) return;
      const before = d0.text;
      describeDrag(true, now);
      if (d0.text !== before) drawGhost();
    }, 60);
    if (!why && G) {
      const q = where === "3d" ? onRay(G, s3().rayAt(e.clientX, e.clientY)) : onWin(G, where.point(e));
      drag.offset = q ? vsub(p, q) : [0, 0, 0];
      if (G.kind === "axis") drag.axisLine = axisLine(G);
    }
  }
  function moveTo(e) {
    if (!drag) return;
    if (!drag.moved && Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) < 4) return;
    if (drag.why || !drag.G) {
      if (!drag.warned) { drag.warned = true; toast(drag.why || t("This object cannot be dragged here"), "notice", 5000); }
      return;
    }
    const q = drag.where === "3d" ? onRay(drag.G, s3().rayAt(e.clientX, e.clientY)) : onWin(drag.G, drag.where.point(e));
    if (!q) return;
    drag.moved = true;
    drag.ghost = vadd(q, drag.offset);
    if (drag.G.kind === "axis") drag.ghost[drag.G.ax] = q[drag.G.ax] + drag.offset[drag.G.ax];
    const now = performance.now();
    drag.samples.push({ t: now, p: drag.ghost });
    while (drag.samples.length > 2 && drag.samples[1].t < now - 4 * THROW_MS) drag.samples.shift();
    describeDrag(e.shiftKey, now);
    drawGhost();
  }
  // the ghost's text: where it is, and for a throw the velocity it would get (world units per world time)
  function describeDrag(shift, now) {
    const o = drag.o, axisB = drag.G.kind === "axis";
    drag.shift = shift;
    if (shift && !axisB && canThrow(o)) {
      const sc = scaleFor(drag), n = handlesOf(o).position.length, vm = vmaxOf(o);
      let v = throwVelocity(now);
      const speed = len3(v);
      drag.asked = null;
      if (vm && speed > vm) { drag.asked = speed; v = vmul(v, vm / speed); }  // clamped to what the world carries
      drag.vel = v; drag.velShown = vmul(v, 0.5 * rate());  // where it would be after 0,5 s of wall time
      const kd = velShow(o) ? velShow(o).factor : 1;
      const shown = (n === 2 ? v.filter((_, i) => planeAxes(s3() && s3().state ? s3().state.plane2d : null).includes(i)) : v).map((x) => x * kd);
      drag.text = t("throw: v = {v} {unit} (×{k:.3g}{auto})", { v: fmtVec(shown, n), unit: velUnit(o), k: sc.k, auto: sc.auto ? ", " + t("auto") : "" })
        + (drag.asked !== null ? " — " + t("clamped to {vmax:.3g} {unit}: reduce the throw scale", { vmax: vm * kd, unit: velUnit(o) }) : "");
    } else {
      drag.vel = null; drag.velShown = null;
      drag.text = axisB ? `${AX[drag.G.ax]} = ${num(drag.ghost[drag.G.ax], 5)}` : (shift && !axisB ? t("it cannot be thrown: the object has no velocity") + " · " : "") + fmtVec(drag.ghost, 3);
    }
    if (shift && axisB) drag.text += " " + t("(there is no throw along an axis)");
  }
  function finish(e) {
    if (!drag) return;
    clearInterval(drag.tick);
    if (drag.moved && !drag.why && drag.G && e) describeDrag(e.shiftKey, performance.now());
    const d = drag; drag = null;
    if (!d.moved || d.why || !d.G) { drawGhost(); return; }
    lastRelease = d.text;
    const throwing = d.shift && d.G.kind !== "axis" && canThrow(d.o);
    const values = editValues(d.o, d.ghost, throwing ? d.vel : null);
    const ok = send({ op: "edit", id: d.o.id, values, ...(throwing && d.asked ? { asked: qvel(d.asked) } : {}) });
    if (!ok) { startSnap(d); return; }
    pend = { o: d.o, id: d.o.id, ghost: d.ghost, start: d.start, G: d.G, axisLine: d.axisLine, velShown: d.velShown, text: d.text,
             throwing, scale: throwing ? scaleFor(d) : null,
             timer: setTimeout(() => { if (pend) { pend = null; drawGhost(); } }, 6000) };
    drawGhost();
  }
  function cancelDrag() {
    if (!drag) return false;
    clearInterval(drag.tick);
    const d = drag; drag = null;
    if (d.moved) startSnap(d); else drawGhost();
    return true;
  }
  // the ghost goes back to where the object is (a refusal, Esc)
  function startSnap(d) {
    snap = { o: d.o, from: d.ghost, to: d.start, start: d.start, at: d.ghost, t0: performance.now(), G: d.G, axisLine: d.axisLine, text: "" };
    const step = () => {
      if (!snap) return;
      const f = Math.min(1, (performance.now() - snap.t0) / SNAP_MS), k = 1 - (1 - f) ** 3;
      snap.at = vadd(snap.from, vmul(vsub(snap.to, snap.from), k));
      drawGhost();
      if (f < 1) requestAnimationFrame(step); else { snap = null; drawGhost(); }
    };
    requestAnimationFrame(step);
  }
  // the world's answer to an edit: done (its scene event) or refused (an error while it was pending)
  function editAnswered(ok) {
    if (!pend) return;
    const d = pend; pend = null; clearTimeout(d.timer);
    if (ok) drawGhost(); else startSnap({ o: d.o, ghost: d.ghost, start: d.start, G: d.G, axisLine: d.axisLine });
    // a throw the world refused: what the owner can do about it (review LB1-p02-ux X4)
    if (!ok && d.throwing) {
      toast(t("The throw was not accepted. Throw slower or reduce the throw scale (now ×{k:.3g}{auto}) — the field “Throw (Shift): scale ×” in the panel “Scene objects”", { k: d.scale.k, auto: d.scale.auto ? ", " + t("auto") : "" }), "notice", 12000);
    }
  }
  window.addEventListener("lferror", () => editAnswered(false));

  function pickSelect(o) { if (o.id !== selected) select(o.id); }
  const manip3d = {
    hover(e) { const sc = s3(); if (!sc || picking()) return ""; const h = hit3d(sc, e.clientX, e.clientY); return h ? (handlesOf(h.o) && handlesOf(h.o).position ? "grab" : "pointer") : ""; },
    down(e) {
      const sc = s3();
      if (!sc || picking() || !scene) return false;
      const h = hit3d(sc, e.clientX, e.clientY);
      if (!h) return false;
      pickSelect(h.o);
      const why = dragWhy(h.o);
      begin(h.o, h.p, why ? null : geom3d(sc, h.o, h.p), "3d", e);
      sc.el.querySelector("canvas").style.cursor = "grabbing";
      return true;
    },
    move(e) { moveTo(e); },
    up(e) { const sc = s3(); if (sc) sc.el.querySelector("canvas").style.cursor = ""; finish(e); },
    cancel() { cancelDrag(); },
  };
  const manipWin = {
    hover(hw, e) { if (picking()) return ""; const h = hitWin(hw, e.clientX, e.clientY); return h ? (handlesOf(h.o) && handlesOf(h.o).position ? "grab" : "pointer") : ""; },
    down(hw, e) {
      if (picking() || !scene) return false;
      const h = hitWin(hw, e.clientX, e.clientY);
      if (!h) return false;
      pickSelect(h.o);
      const why = dragWhy(h.o);
      begin(h.o, h.p, why ? null : geomWin(hw, h.o, h.p), hw, e);
      hw.el.style.cursor = "grabbing";
      return true;
    },
    move(hw, e) { moveTo(e); },
    up(hw, e) { hw.el.style.cursor = ""; finish(e); },
    cancel() { cancelDrag(); },
  };
  setWindowManipulator(manipWin);
  // for automated tests of the page
  window.__lfManip = { selected: () => selected, dragging: () => !!(drag && drag.moved), pending: () => !!pend, released: () => lastRelease,
                       snapping: () => !!snap, throwScale: () => throwScale, text: () => (drag ? drag.text : pend ? pend.text : ""),
                       at: (id) => posOf(id), objects: () => (scene ? scene.objects.map((o) => ({ id: o.id, type: o.type, label: o.label, values: o.values })) : []),
                       handles: (type) => { const ot = byType(type); return ot ? ot.handles || null : null; },
                       ringInWindow: (k) => drawnRings[k] || null };
  let manipOn = null;  // the 3-D scene the manipulator is installed on
  function ensureManip() {
    const sc = s3();
    if (!sc || !sc.setManipulator || manipOn === sc) return;
    sc.setManipulator(manip3d);
    manipOn = sc;
    // a click on the scene that no object took (empty space, a slice plane) deselects the object
    sc.el.addEventListener("s3dclick", () => { if (selected && !drag) select(null); });
  }

  // keys: Esc cancels a drag (before the scene's own Esc), Delete removes the selected object (a slice plane selected
  // instead is the 3-D environment's)
  window.addEventListener("keydown", (e) => {
    const tag = e.target && e.target.tagName;
    if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
    if (e.key === "Escape" && drag) { cancelDrag(); e.preventDefault(); e.stopPropagation(); return; }
    if (e.key === "Delete" && selected && objById(selected) && !drag) {
      const sc = s3();
      // a slice plane selected after the object takes the key; the world's own window never does (review LB1-p02-ux
      // X2: Delete in p02's plane window answered "Slice not built")
      if (sc && sc.state && sc.state.selected && !isFixedWindow(sc.state.selected)) return;
      e.preventDefault(); e.stopPropagation();
      const o = objById(selected);
      if (send({ op: "remove", id: o.id })) toast(t("Removing “{label}”…", { label: o.label }), "notice", 2500);
    }
    if (e.key === "Shift" && drag && drag.moved) { describeDrag(true, performance.now()); drawGhost(); }
  }, true);
  window.addEventListener("keyup", (e) => { if (e.key === "Shift" && drag && drag.moved) { describeDrag(false, performance.now()); drawGhost(); } }, true);

  // the throw's scale and the help on manipulation (panel "Scene objects")
  const throwInput = numberInput(throwScale ?? "", { placeholder: t("auto"), style: { width: "6em" },
                                   title: t("Throw velocity = the pointer's displacement in the world over the last 0.1 s ÷ (0.1 s × the playback speed) × the scale. Empty — auto: a brisk flick (the view's width in a second) throws the object across the whole region of the world in 2 s at the current playback speed, but not faster than half the largest speed the world declared; a faster throw is clamped") });
  throwInput.onchange = () => {
    const r = parseNum(throwInput.value), v = r.value;  // a decimal comma or point (review i18n-browser F1)
    if (r.err === "empty") throwScale = null;
    else if (v > 0 && Number.isFinite(v)) throwScale = v;
    else { throwInput.value = throwScale === null ? "" : fmtField(throwScale); return; }
    throwInput.value = throwScale === null ? "" : fmtField(throwScale);
    try { if (throwScale === null) localStorage.removeItem("lf.throwScale"); else localStorage.setItem("lf.throwScale", String(throwScale)); } catch (e) { /* storage off */ }
  };
  const autoBtn = el("button", { class: "pg-auto", title: t("The throw scale — automatic"), onclick: () => { throwInput.value = ""; throwInput.onchange(); } }, t("auto"));
  const manipBox = el("div", { class: "pg-manip" },
    el("div", { class: "help" }, t("In the scene and in a slice window: click an object — select it; drag — move it (in the plane perpendicular to the view; in the plane of a 2-D world or of the window; along the axis for objects on an axis); Shift + drag — throw; Delete — remove; Esc — cancel the drag. The change applies on release, at the world's current moment.")),
    el("div", { class: "row" }, el("span", { class: "muted" }, t("Throw (Shift): scale ×")), throwInput, autoBtn,
      el("span", { class: "muted", title: t("At scale 1 a body flies on with the speed the hand carried it at the current playback speed") }, " ⓘ")));

  // --- objects and the inspector -----------------------------------------------------------------------------
  // The list is kept and its rows updated in place: its scroll stays where the owner put it when the scene changes or
  // an object is selected in it (review UX-ui U1: a new list came back at its top); a selection made elsewhere (the
  // scene) scrolls its row into view.
  let listEl = null;
  const rowEls = new Map();
  function drawObjects() {
    const objs = scene ? scene.objects : [];
    if (!objs.length) { listEl = null; rowEls.clear(); fill(objectsBox, el("div", { class: "muted" }, t("The scene is empty: add objects from the palette."))); drawInspector(); return; }
    if (!listEl || listEl.parentNode !== objectsBox) { listEl = el("div", { class: "pg-list" }); fill(objectsBox, listEl); rowEls.clear(); }
    const off = !!why(), ids = new Set(objs.map((o) => o.id));
    for (const [id, r] of rowEls) if (!ids.has(id)) { r.row.remove(); rowEls.delete(id); }
    let prev = null;
    for (const o of objs) {
      let r = rowEls.get(o.id);
      if (!r) {
        const ot = byType(o.type);
        const name = el("span", { class: "grow" });
        const dup = el("button", { title: t("A copy (at the current moment)"), onclick: (e) => { e.stopPropagation(); send({ op: "duplicate", id: o.id }); } }, "⧉");
        const del = el("button", { title: t("Remove from the scene (at the current moment)"), onclick: (e) => { e.stopPropagation(); send({ op: "remove", id: o.id }); } }, "✕");
        const ctr = el("button", { title: t("Centre the view on the object (the centre of rotation on it)"), onclick: (e) => { e.stopPropagation(); centerOnObject(o.id); } }, "◎");
        const eye = el("span", { class: "pg-eye", title: t("The view follows this object (to switch off — “Follow” in the inspector)"), style: { display: "none" } }, "👁");
        const row = el("div", { class: "pg-obj", onclick: () => select(o.id, { fromList: true }) },
          el("span", { class: "pg-sw", style: { background: ot ? ot.color : "#888" } }), name, eye, ctr, dup, del);
        r = { row, name, dup, del, eye, ctr };
        rowEls.set(o.id, r);
      }
      if (r.name.textContent !== t(o.label)) r.name.textContent = t(o.label);
      r.row.classList.toggle("sel", o.id === selected);
      r.dup.disabled = off; r.del.disabled = off;
      r.ctr.style.display = s3() ? "" : "none";
      const want = prev ? prev.nextSibling : listEl.firstChild;
      if (want !== r.row) listEl.insertBefore(r.row, want);
      prev = r.row;
    }
    drawInspector();
    drawFollow();
  }

  function select(id, { fromList = false } = {}) {
    if (follow && follow.id !== id) setFollow(null);  // following is for the selected object
    selected = id;
    drawObjects();
    if (!fromList && id && rowEls.get(id)) rowEls.get(id).row.scrollIntoView({ block: "nearest" });
    // one selection on the page: an object selected deselects a slice plane (its Delete and gizmo are the plane's)
    const sc = s3();
    if (id && sc && sc.state && sc.state.selected && sc.select) sc.select(null);
    drawSelection(); redrawWindows();
    onSelect(id);
  }

  // The inspector is rebuilt only when another object (or its type, or what may be edited) is shown; otherwise its
  // controls take the new values in place and keep the focus (review UX-ui U10: every scene message replaced them).
  let insp = { key: null, ctls: {} };
  function drawInspector() {
    const o = selected ? objById(selected) : null;
    if (!o) { insp = { key: null, ctls: {} }; fill(inspectorBox, el("div", { class: "muted" }, t("Choose an object in the list of the scene."))); return; }
    if (insp.key === null) insp = { key: null, ctls: {} };
    const ot = byType(o.type);
    const w = ro();
    const vis = (ot ? ot.params : []).filter((p) => !p.hidden && shown(p, o.values)).map((p) => p.id).join(",");
    const key = `${o.id}|${o.type}|${w ? 1 : 0}|${vis}`;
    if (key === insp.key) {
      for (const [pid, c] of Object.entries(insp.ctls)) c.set(o.values[pid]);
      if (insp.name && document.activeElement !== insp.name) insp.name.value = t(o.label);
      if (insp.added) insp.added.textContent = t("added at t = {t}", { t: time(o.t_added, 6) });
      return;
    }
    const name = el("input", { type: "text", class: "pg-insp-name", value: t(o.label), disabled: !!w, title: t("The object's name") });
    name.onchange = () => send({ op: "label", id: o.id, label: name.value });
    const ctls = {};
    const rows = (ot ? ot.params : []).filter((p) => !p.hidden && shown(p, o.values)).map((p) => {
      const c = control(p, o.values[p.id], (v) => send({ op: "set", id: o.id, values: { [p.id]: v } }));
      c.disable(!!w);
      ctls[p.id] = c;
      return c.el;
    });
    const added = el("div", { class: "muted" }, t("added at t = {t}", { t: time(o.t_added, 6) }));
    const camRow = s3() ? el("div", { class: "row pg-cam" },
      el("button", { title: t("Move the 3-D view's centre of rotation to the object (the direction of view unchanged)"), onclick: () => centerOnObject(o.id) }, t("◎ Centre")),
      el("button", { class: "toggle", onclick: () => setFollow(follow && follow.id === o.id ? null : o.id) }, t("👁 Follow"))) : null;
    // keep the field the owner was in: the same parameter's field of the new controls takes the focus back
    const focusPid = Object.entries(insp.ctls).find(([, c]) => c.input && document.activeElement === c.input);
    insp = { key, ctls, name, added, follow: camRow ? camRow.lastChild : null };
    fill(inspectorBox,
      el("div", { class: "ctl" }, el("label", {}, (ot ? t(ot.label) : o.type) + ":"), name), camRow,
      w ? el("div", { class: "warn" }, w) : el("div", { class: "help" }, t("Changes apply at once, at the world's current moment. The fields are the values set; “now” is the object's state at this moment of the world.")),
      ...rows,
      el("div", { class: "muted", style: { marginTop: "6px" } }, t("now:")), nowBox,
      added);
    if (focusPid && ctls[focusPid[0]] && ctls[focusPid[0]].input && !ctls[focusPid[0]].input.disabled) ctls[focusPid[0]].input.focus();
    drawFollow();
  }

  // the selected object's state at the time shown (the section's frame: now[id] = {label: text}), redrawn every frame
  // in its own box (the inputs above keep their focus)
  function drawNow(frame) {
    const r = selected && frame && frame.now ? frame.now[selected] : null;
    fill(nowBox, r ? Object.entries(r).flatMap(([k, v]) => [el("span", {}, t(k)), el("span", { class: "mono" }, typeof v === "number" ? num(v, 6) : t(v))])
      : [el("span", { class: "muted" }, "—")]);
  }

  function shown(p, values) {
    if (!p.show_if) return true;
    return Object.entries(p.show_if).every(([k, allowed]) => allowed.includes(values[k]));
  }

  // --- the scene's changes in time --------------------------------------------------------------------------
  function drawChanges(tNow) {
    const list = changes.filter((c) => c.t <= tNow + 1e-12 * Math.abs(tNow));
    if (!list.length) { fill(changesBox, el("div", { class: "muted" }, t("The scene has not been changed yet."))); return; }
    fill(changesBox, list.slice(-200).reverse().map((c) => el("div", { class: "ev", style: { cursor: "pointer" },
      title: t("Go to this moment of the record"), onclick: () => ctx.jumpTo && ctx.jumpTo(c.t) },
      el("span", { class: "mono" }, time(c.t, 6)), " — ", t(c.text))));
  }

  // --- probes ----------------------------------------------------------------------------------------------
  function drawProbes(frame) {
    const probes = (frame && frame.probes) || {};
    const ids = Object.keys(probes);
    if (!ids.length) { fill(probesBox, el("div", { class: "muted" }, t("No probes: add them from the palette."))); return; }
    fill(probesBox, ids.map((id) => {
      const o = objById(id), r = probes[id];
      const rows = describeProbe ? describeProbe(o, r) : Object.entries(r).map(([k, v]) => [k, typeof v === "number" ? num(v, 6) : v]);
      return el("div", { class: "pg-probe" }, el("b", {}, o ? t(o.label) : id),
        el("div", { class: "kv" }, rows.flatMap(([k, v]) => [el("span", {}, t(k)), el("span", { class: "mono" }, t(v))])));
    }));
  }

  // --- the scene as a file --------------------------------------------------------------------------------
  function drawFile() {
    const save = el("button", { title: t("The scene's objects with their parameters and current state, the world's laws and the time — into a file"), onclick: () => {
      if (!ctx.atEnd || ctx.atEnd()) { exportAsked = true; ctx.send("scene", { op: "export" }); }
      else toast(t("The scene of the world's current moment is saved: go to the end of the record (⏭)"), "notice");
    } }, t("💾 Save the scene"));
    const input = el("input", { type: "file", accept: ".lfscene,.json,application/json", style: { display: "none" } });
    input.onchange = async () => {
      const f = input.files[0];
      input.value = "";
      if (!f) return;
      let sc;
      try { sc = JSON.parse(await sceneText(f)); } catch (e) { toast(t("The scene file was not read: {why}", { why: e.message })); return; }
      if (!sc || sc.format !== "lfscene") { toast(t("This is not a scene file (lfscene)")); return; }
      if (P && sc.viz && sc.viz !== P.viz) { toast(t("A scene of another section ({other}): open it from the catalogue", { other: sc.viz })); return; }
      if (!confirm(t("Start a new world in this run from the file's scene? The current world stays in the record."))) return;
      ctx.send("new_world", { params: { ...(sc.laws || {}), scene: sc }, seed: null });
    };
    const load = el("button", { title: t("A new world of this run from a scene file (the laws and the objects from the file)"), onclick: () => input.click() }, t("📂 Load a scene…"));
    fill(fileBox, el("div", { class: "row" }, save, load, input),
      el("div", { class: "help" }, t("The file holds the objects, their parameters and current state (positions, velocities), the world's laws and the time. The wave of the quantum section is saved as the packets it started from; the continuation of the wave itself is in the run's record.")));
  }

  function download(sc) {
    const blob = new Blob([JSON.stringify(sc, null, 1)], { type: "application/json" });
    const a = el("a", { href: URL.createObjectURL(blob), download: `${sc.viz || "scene"}-t${Number(sc.t || 0).toPrecision(4)}.lfscene` });
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  }

  // --- the record's window ------------------------------------------------------------------------------------
  function drawRec() {
    if (!rec) { fill(recBox, el("div", { class: "muted" }, "…")); return; }
    const mins = Math.round((rec.window_s || 600) / 60);
    const win = numberInput(mins, { style: { width: "5em" },
                              title: t("How many last minutes the record's window holds") }, { int: true, step: 1, min: 1, max: 1440 });
    win.onchange = () => {  // the window only (B6-F11, F12)
      const r = parseNum(win.value);
      if (r.err || !(r.value >= 1 && r.value <= 1440)) { win.value = fmtField(mins, true); toast(t("The window is from {lo:d} to {hi:d} minutes", { lo: 1, hi: 1440 }), "notice", 4000); return; }
      postRec({ window_s: 60 * Math.round(r.value) });
    };
    const btn = el("button", { class: rec.recording ? "toggle on" : "", title: rec.recording
      ? t("The record is kept whole; press to hold only the window again (what was kept stays)")
      : t("Keep what the window holds and record everything from now on (like a dashcam)"),
      onclick: () => postRec({ on: !rec.recording }) }, rec.recording ? t("■ Being kept — window only") : t("● Keep the record"));
    fill(recBox,
      el("div", { class: "row" }, btn),
      el("div", { class: "row" }, el("span", { class: "muted" }, t("Window: the last")), win, el("span", { class: "muted" }, t("min"))),
      el("div", { class: "help" }, rec.recording
        ? t("Everything that was in the window, and everything after it, is kept until you switch it off.")
        : t("Only the last minutes are kept: older ones are removed. If you notice an effect, press “● Keep the record”: the window with it is kept, and from then on the record is kept in full.")),
      el("div", { class: "muted" }, t("the record from t = {t}; on the disk {mb:.3g} MB", { t: rec.kept_from_t === null || rec.kept_from_t === undefined ? "—" : time(rec.kept_from_t, 5), mb: (rec.size || 0) / 1e6 })));
  }

  async function postRec(body) {
    try {
      const r = await fetch(`/api/runs/${encodeURIComponent(runId)}/record`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error !== undefined ? t(j.error) : r.statusText);
      rec = j; drawRec();
    } catch (e) { toast(t("Record: {why}", { why: e.message })); }
  }

  // redrawn only when what they show changed: an input being edited must keep its focus between frames
  let keyScene = "", keyChanges = "", keyRec = "", fileDrawn = false;
  function drawAll(frame, tt) {
    const ks = `${P ? P.viz : ""}|${scene ? scene.rev + ":" + scene.objects.length + ":" + JSON.stringify(scene.palette_state || {}) : ""}|${selected}|${ro()}`;
    if (ks !== keyScene) { keyScene = ks; drawPalette(); drawObjects(); if (placing) drawPlace(); }
    const shownChanges = changes.filter((c) => c.t <= (tt ?? Infinity) + 1e-12 * Math.abs(tt ?? 0)).length;
    if (`${shownChanges}|${changes.length}` !== keyChanges) { keyChanges = `${shownChanges}|${changes.length}`; drawChanges(tt ?? Infinity); }
    const kr = JSON.stringify(rec);
    if (kr !== keyRec) { keyRec = kr; drawRec(); }
    if (!fileDrawn) { fileDrawn = true; drawFile(); }
    drawProbes(frame);
    drawNow(frame);
    stepFollow();
  }

  window.addEventListener("editablechange", () => { keyScene = ""; drawAll(null, undefined); });
  // the world started or ended computing a change: the palette and the list's buttons wait meanwhile; the open form
  // keeps what is being typed in it (only its button follows)
  window.addEventListener("busychange", () => {
    if (!P) return;
    drawPalette(); drawObjects();
    if (placing && placing.go) placing.go.disabled = !!why() || !!typeWhy(placing.ot);
  });

  return {
    leftPanels: [panel(t("Palette: add to the scene"), el("div", {}, paletteBox, placeBox)), panel(t("Scene objects"), el("div", {}, manipBox, objectsBox)),
                 panel(t("Inspector"), inspectorBox), panel(t("Scene: file"), fileBox, { closed: true }),
                 panel(t("Record: window"), recBox, { closed: true })],
    rightPanels: [panel(t("Probes"), probesBox), panel(t("Scene changes"), changesBox, { closed: true })],
    selected: () => selected,
    objects: () => (scene ? scene.objects : []),
    object: objById,
    type: byType,
    select,
    // the record's window is the run's state now, not the world's at the cursor: kept through a rebuild and out of
    // the key frames (review B6-F11)
    reset() {
      P = null; scene = null; changes = []; selected = null; keyScene = keyChanges = keyRec = ""; lastFrame = lastBlobs = null;
      drag = null; snap = null; if (pend) { clearTimeout(pend.timer); pend = null; }
      const sc = s3(); if (sc && sc.setMarker) { sc.setMarker("sel", null); sc.setMarker("ghost", null); } selKey = selWinKey = "";
    },
    // a point for the open pre-placement form (a view that picks its own points, e.g. on its plane)
    placeAt: (pt) => setPoint(pt),
    snapshot() { return { scene, n: changes.length }; },
    restore(k) { scene = k.scene; changes.length = k.n; },
    onHeader(meta) {
      P = meta.playground || null;
      if (follow && meta.world !== headerWorld) setFollow(null);  // another world: its objects are others
      headerWorld = meta.world;
      const now = ctx.recordState ? ctx.recordState() : null;  // as the server sent it on (re)connection
      if (now) rec = now;
      else if (!rec && ctx.runMeta) {  // else as the run's passport had it (live record_state messages follow)
        const m = ctx.runMeta(), b = (m && m.buffer) || null;
        if (b) rec = { window_s: b.window_s, recording: !!b.recording, kept_from_t: (b.segs && b.segs[0] ? b.segs[0].t0 : null), size: m.size };
      }
      keyScene = "";
      drawAll(null, meta.t);
      ensureManip();
    },
    // true when the message was one of the playground's
    onMessage(meta) {
      switch (meta.type) {
        case "scene":
          scene = meta;
          if (selected && !objById(selected)) { selected = null; drawSelection(); }
          if (drag && !objById(drag.o.id)) cancelDrag();
          return true;
        case "event":
          if (meta.kind === "scene") changes.push({ t: meta.t, text: meta.text, name: meta.name });
          if (meta.kind === "scene" && pend && meta.name === "edit" && (meta.args || {}).id === pend.id) editAnswered(true);
          return false;  // the player keeps it in "Events" too
        case "record_state":
          rec = meta; return true;
        case "scene_export":
          if (exportAsked) { exportAsked = false; download(meta.scene); }
          return true;
        case "record_segment":
          return true;
        default:
          return false;
      }
    },
    setRecord(state) { rec = state; drawRec(); },
    render(frame, tt, blobs) {
      lastFrame = frame || lastFrame; lastBlobs = blobs || null; drawAll(frame, tt);
      ensureManip();
      if (selected || selWinKey) drawSelection();
    },
    centerOn: (id) => centerOnObject(id),
    follow: (id) => setFollow(id),
  };
}
