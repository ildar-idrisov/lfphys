// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// p01 view: the gravity playground (plan P15.1). The 3-D environment (/static/js/env3d.js: the hole's horizon and
// ergosphere, its circular orbits, from the run) with the bodies as spheres at the time shown and their trails; the
// shared playground panels (/static/js/playground.js). Everything drawn comes from the run: positions and trails are
// the solver's (frames and "trail" messages), the hole's surfaces its meshes. Drawing only.
//
// Trails (review UX-ui U2, UX-3d A13). The run sends points of each orbit with their positions, velocities and times,
// at most 20 degrees of turn of the direction of motion apart (viz.py, TRAIL_TURN); between two of them the view draws
// the cubic Hermite curve of their positions and velocities — interpolation along computed data — split into chords of
// at most HERMITE_STEP = 2° of turn. On a circle the curve is off by r θ⁴/384 = 3.9e-5 r (θ = 20°) and a chord of 2°
// by r (1 − cos 1°) = 1.5e-4 r: together below 2e-4 of the local radius of curvature, under 0.25 px for any orbit whose
// radius on the screen is under ~1200 px, at any speed of the world. The last piece runs from the trail's last point
// to the body's position and velocity in the frame shown.
import { el, num, panel } from "/static/js/ui.js";
import { t } from "/static/js/i18n.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createPlayground } from "/static/js/playground.js";

const TRAIL_SHOWN = 300;                     // points of each trail drawn (all are kept: key frames cut back to lengths)
const HERMITE_STEP = 2 * Math.PI / 180;      // the largest turn of one drawn chord
const MAX_SUB = 24;                          // chords per Hermite piece at most
const GENS_KEPT = 12;

// a growable trail: positions, velocities (NaN: a record without them — chords), times; a break is a NaN position
function newTrail(rgb) {
  return { n: 0, p: new Float32Array(3 * 64), v: new Float32Array(3 * 64), t: new Float64Array(64), rgb };
}
function push(T, x, y, z, vx, vy, vz, tw) {
  if (T.n === T.t.length) {
    const p = new Float32Array(2 * T.p.length), v = new Float32Array(2 * T.v.length), tt = new Float64Array(2 * T.t.length);
    p.set(T.p); v.set(T.v); tt.set(T.t); T.p = p; T.v = v; T.t = tt;
  }
  const i = T.n++;
  T.p[3 * i] = x; T.p[3 * i + 1] = y; T.p[3 * i + 2] = z;
  T.v[3 * i] = vx; T.v[3 * i + 1] = vy; T.v[3 * i + 2] = vz;
  T.t[i] = tw;
}
const turn = (a, b) => {
  const cx = a[1] * b[2] - a[2] * b[1], cy = a[2] * b[0] - a[0] * b[2], cz = a[0] * b[1] - a[1] * b[0];
  return Math.atan2(Math.hypot(cx, cy, cz), a[0] * b[0] + a[1] * b[1] + a[2] * b[2]);
};
// the Hermite piece from (x0, v0) at t0 to (x1, v1) at t1, without its first point, onto P (and the fades onto F)
function hermite(P, F, x0, v0, t0, x1, v1, t1, f0, f1) {
  const dt = t1 - t0;
  const ok = dt > 0 && Number.isFinite(dt) && v0.every(Number.isFinite) && v1.every(Number.isFinite);
  const n = ok ? Math.min(MAX_SUB, Math.max(1, Math.ceil(turn(v0, v1) / HERMITE_STEP))) : 1;
  for (let k = 1; k <= n; k++) {
    const u = k / n, u2 = u * u, u3 = u2 * u;
    const h00 = 2 * u3 - 3 * u2 + 1, h10 = u3 - 2 * u2 + u, h01 = -2 * u3 + 3 * u2, h11 = u3 - u2;
    for (let c = 0; c < 3; c++) {
      P.push(ok ? h00 * x0[c] + h10 * dt * v0[c] + h01 * x1[c] + h11 * dt * v1[c] : x0[c] + u * (x1[c] - x0[c]));
    }
    F.push(f0 + u * (f1 - f0));
  }
}

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin" });
  let H = null;
  // trails by object id; a segment of the record starts with the kept trails (a reset, the same points the view
  // draws): each generation keeps its own map, so that a key frame taken before a reset is still restored after it; only
  // the latest GENS_KEPT generations are kept (the tab's memory: review B6-F13)
  let gens = new Map([[0, new Map()]]), gen = 0, trails = gens.get(0);
  let holeMarks = new Map();  // label layer -> {at, size, text} of a hole's drawn label (redrawn when it moved)
  let labels = new Map();     // object id -> its label (the latest scene message)
  const pg = createPlayground(ctx, { onSelect: () => ctx.requestRender(), describeProbe, env });

  function describeProbe(o, r) {
    // keys are msgids (the playground renders them with t), values numbers, lists of numbers or texts (T)
    return Object.entries(r).map(([k, v]) => [k, typeof v === "number" ? num(v, 6) : Array.isArray(v) ? v.map((x) => num(x, 4)).join("; ") : v]);
  }

  function onTrail(meta, b) {
    if (meta.reset) {
      gen += 1; trails = new Map(); gens.set(gen, trails);
      for (const g of [...gens.keys()]) if (g <= gen - GENS_KEPT) gens.delete(g);
    }
    const P = b.pts, V = b.vel, TT = b.tt;
    let off = 0;
    meta.ids.forEach((id, i) => {
      const n = meta.counts[i];
      let T = trails.get(id);
      if (!T) { T = newTrail(meta.rgb ? meta.rgb[i] : [0.7, 0.7, 0.7]); trails.set(id, T); }
      for (let k = off; k < off + n; k++) {
        push(T, P[3 * k], P[3 * k + 1], P[3 * k + 2], V ? V[3 * k] : NaN, V ? V[3 * k + 1] : NaN, V ? V[3 * k + 2] : NaN,
             TT ? TT[k] : NaN);
      }
      off += n;
    });
  }

  // the drawn polyline of every trail up to the frame's time, its last piece to the body's state in the frame
  function drawTrails(frame, blobs, tNow) {
    const P = [], F = [], C = [];
    const tf = frame && Number.isFinite(frame.t) ? frame.t : Number.isFinite(tNow) ? tNow : Infinity;
    const heads = new Map();
    const tid = (frame && frame.trail_ids) || [], pos = blobs.pos, vel = blobs.vel;
    tid.forEach((id, i) => { if (id != null && pos) heads.set(id, [[pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]], vel ? [vel[3 * i], vel[3 * i + 1], vel[3 * i + 2]] : [NaN, NaN, NaN]]); });
    for (const [id, T] of trails) {
      let end = T.n;
      while (end > 0 && T.t[end - 1] > tf) end--;  // a cursor between thinned frames: the points up to its time
      const i0 = Math.max(0, end - TRAIL_SHOWN), nShown = end - i0;
      if (nShown <= 0) continue;
      const fade = (i) => 0.25 + 0.75 * (i - i0 + 1) / (nShown + 1);  // older parts fainter
      const q0 = P.length;
      let prev = null;
      for (let i = i0; i < end; i++) {
        const x = [T.p[3 * i], T.p[3 * i + 1], T.p[3 * i + 2]], v = [T.v[3 * i], T.v[3 * i + 1], T.v[3 * i + 2]];
        if (!Number.isFinite(x[0])) { if (prev) { P.push(NaN, NaN, NaN); F.push(0); } prev = null; continue; }
        if (!prev) { P.push(...x); F.push(fade(i)); }
        else hermite(P, F, prev.x, prev.v, prev.t, x, v, T.t[i], prev.f, fade(i));
        prev = { x, v, t: T.t[i], f: fade(i) };
      }
      const h = heads.get(id);
      if (prev && h && tf > prev.t && Number.isFinite(tf)) hermite(P, F, prev.x, prev.v, prev.t, h[0], h[1], tf, prev.f, 1.0);
      if (P.length > q0) { P.push(NaN, NaN, NaN); F.push(0); }
      for (let k = q0 / 3; k < P.length / 3; k++) C.push(T.rgb[0] * F[k], T.rgb[1] * F[k], T.rgb[2] * F[k]);
    }
    env.scene.setLines("trails", new Float32Array(P), new Float32Array(C), { label: t("Trails of the bodies (computed)") });
  }

  // a Newtonian hole: a light marker of the scene's size with its name (review UX-ui U18: a dark sphere of the
  // Schwarzschild radius on the dark scene could not be found); placed again only when it moved visibly
  function drawHoles(frame, pos) {
    const seen = new Set();
    const size = env.scene.state.size || 1;
    for (const i of (frame && frame.holes) || []) {
      const id = frame.ids[i], at = [pos[3 * i], pos[3 * i + 1], pos[3 * i + 2]], lid = `hole_${id}`;
      seen.add(lid);
      const name = t(labels.get(id) || "Black hole"), hole = t("black hole");
      const text = name.toLowerCase().includes(hole.toLowerCase()) ? name : `${name} (${hole})`;
      const m = holeMarks.get(lid);
      if (!m || m.size !== size || m.text !== text || Math.hypot(at[0] - m.at[0], at[1] - m.at[1], at[2] - m.at[2]) > 0.004 * size) {
        env.scene.setObject({ id: lid, kind: "point", pos: at, text, color: "#e5dbff", label: t("Black hole marker: {text}", { text }) });
        holeMarks.set(lid, { at, size, text });
      }
    }
    for (const lid of [...holeMarks.keys()]) if (!seen.has(lid)) { env.scene.removeLayer(lid); holeMarks.delete(lid); }
  }

  function clearHoles() { for (const lid of holeMarks.keys()) env.scene.removeLayer(lid); holeMarks = new Map(); }

  return {
    center: env.center,
    leftPanels: pg.leftPanels,
    rightPanels: [...pg.rightPanels, panel(t("Scene layers"), env.layersPanel)],
    help: () => el("div", {},
      el("h4", {}, t("Laboratory: space and gravity")),
      el("p", {}, t("Add bodies from the palette (stars, planets, black holes, test bodies, light, observers with clocks) and change their parameters on the fly in the inspector. The motion is computed according to the laws of the chosen world: Newtonian gravity of N bodies, a post-Newtonian binary radiating gravitational waves, or geodesics around a Kerr–Newman black hole.")),
      el("p", {}, t("A body from the palette is placed at the given point, or, if it is occupied, at the nearest free place along the x axis (a message says so). The collision mode (merge or pass through) can be changed on the fly, at the current moment.")),
      el("p", {}, t("Trails are the computed orbits: solution points at most {deg}° of turn of the direction of motion apart, joined by Hermite curves through the positions and velocities; on the screen the deviation is below {px} pixel at any speed of the world.", { deg: 20, px: 0.25 })),
      el("p", {}, t("The conservation laws are checked live (“Checks”): energy, momentum and angular momentum (Newton); the energy, angular momentum and Carter's constant of every body (Kerr–Newman); the energy balance against the energy carried away by the waves (the binary). The numerical error is estimated against a run of the same interval with half the accuracy parameter η (a step √2 times shorter, an error about 4 times smaller).")),
      el("p", {}, t("The record keeps a window of the last minutes; when you notice an effect, press “● Keep the record” in the “Record: window” panel. The scene can be saved to a file and a new world started from it."))),
    reset() { env.reset(); pg.reset(); H = null; gens = new Map([[0, new Map()]]); gen = 0; trails = gens.get(0); holeMarks = new Map(); labels = new Map(); },
    snapshot() {
      return { env: env.snapshot(), pg: pg.snapshot(), gen, lens: new Map([...trails].map(([id, T]) => [id, T.n])), labels: new Map(labels) };
    },
    restore(k) {
      if (k.gen > gen || !gens.has(k.gen)) throw new Error("the key frame's trails are not kept");
      clearHoles();
      env.restore(k.env); pg.restore(k.pg);
      for (const g of [...gens.keys()]) if (g > k.gen) gens.delete(g);
      trails = gens.get(k.gen); gen = k.gen; labels = new Map(k.labels);
      for (const [id, T] of [...trails]) { if (k.lens.has(id)) T.n = k.lens.get(id); else trails.delete(id); }
    },
    onHeader(meta) { H = meta; env.onHeader(meta); pg.onHeader(meta); ctx.setScene && ctx.setScene(meta.title); },
    onMessage(meta, blobs) {
      if (meta.type === "scene") labels = new Map((meta.objects || []).map((o) => [o.id, o.label]));
      if (pg.onMessage(meta, blobs)) return;
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "trail") onTrail(meta, blobs);
    },
    render(frame, tNow, blobs) {
      if (!H || !frame) return;
      const pos = blobs.pos || new Float32Array(0), rad = blobs.rad || new Float32Array(0), rgb = blobs.rgb ? Float32Array.from(blobs.rgb) : new Float32Array(0);
      const ids = frame.ids || [], sel = pg.selected();
      for (let i = 0; i < ids.length; i++) if (ids[i] === sel) { rgb[3 * i] = Math.min(1, rgb[3 * i] + 0.4); rgb[3 * i + 1] = Math.min(1, rgb[3 * i + 1] + 0.4); }
      env.scene.setSpheres("bodies", pos, rad, rgb, { label: t("Bodies now") });
      drawTrails(frame, blobs, tNow);
      drawHoles(frame, pos);
      pg.render(frame, tNow);
      env.scene.requestRender();
    },
  };
}
