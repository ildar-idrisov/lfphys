// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The 3-D environment of a world (owner, 2026-10-27; RULES.md §2.10), shared by every 3-D visualization: the scene
// (scene3d.js) and the slice windows (slices.js) side by side, the panels «Слои сцены» and «Срез: положение и наклон»,
// «＋ Срез» (the next plane through the middle, perpendicular to the planes there), previews while a plane is dragged,
// the keys, and the messages of the 3-D protocol (volume, vectors, target, planes, slice, path, triads, marks, arrow,
// mesh).
// A visualization adds its own panels, help and frame drawing; it never computes what a plane shows.
import { el, fill } from "./ui.js";
import { PLANE_COLORS, SCALES, anglesOfNormal, createScene3D, normalFromAngles } from "./scene3d.js";
import { createSliceWindows } from "./slices.js";

// plane2d(header): for a 2-D world, the axis (0, 1, 2) normal to its plane (the view opens looking at the plane from
// above; review UX-3d A3), else null
export function createEnv3D(ctx, { logFloor = () => 1e-6, scale = "sqrt", plane2d = () => null } = {}) {
  let H = null, planes = [], selected = null, volQuantity = null;
  // the latest message of the 3-D protocol that set each object (key frames of the player: what to set again)
  let last = new Map(), setSeq = 0;  // each entry {meta, blobs, seq}: seq orders them as the record did
  const SET = new Set(["volume", "box", "vectors", "target", "marks", "arrow", "mesh", "lines", "planes", "slice"]);
  const keyOf = (m) => (m.type === "box" || m.type === "planes" ? m.type : `${m.type}:${m.id}`);
  // why the planes cannot be changed now (an archived world, the cursor in the history, a rebuild), or ""
  const roText = () => (ctx.readOnly ? ctx.readOnly() : ctx.isArchived && ctx.isArchived() ? "Это мир из записи: срезы менять нельзя." : "");
  const ro = () => !!roText();
  const maxPlanes = () => ((H && H.scene3d.planes) || {}).max ?? 3;
  const sendPlane = (id, fields) => {
    if (ro()) return;
    windows.setBusy(id, "считается…");
    ctx.send("view", { op: "plane", id, ...fields });
  };
  const scene = createScene3D({
    readOnly: ro,
    onSelect: (id) => { selected = id; windows.select(id); drawPlanePanel(); },
    onPlaneEdit: (id, pose) => sendPlane(id, pose),
    onPlaneMoving: (id, g) => preview(id, g),
  });
  const windows = createSliceWindows({
    onSelect: (id) => scene.select(id),
    onHighlight: (id) => scene.highlight(id),
    onRemove: (id) => { if (!ro()) ctx.send("view", { op: "remove", id }); },
  });
  const addBtn = el("button", { class: "primary", title: "Добавить плоскость среза (до трёх): ставится в середину, перпендикулярно уже стоящим", onclick: addPlane }, "＋ Срез");
  const scaleSel = el("select", { title: "Шкала яркости 3D-сцены" }, SCALES.map(([v, t]) => el("option", { value: v }, t)));
  scaleSel.value = scale;
  scaleSel.onchange = () => { scene.setScale(scaleSel.value, logFloor(H)); };
  scene.buildTools([addBtn, scaleSel]);
  const center = el("div", { class: "s3d" }, scene.el, windows.el);
  const layersBox = el("div", {}), planeBoxEl = el("div", {});
  scene.onLayersChanged(drawLayers);

  function drawLayers() {
    const rows = scene.layers().map((L) => {
      const cb = el("input", { type: "checkbox" }); cb.checked = L.visible;
      cb.onchange = () => scene.setLayerVisible(L.id, cb.checked, true);
      const extra = [];
      if (L.kind === "volume") {
        const look = scene.volumeLook();  // the sliders start where the scene is
        // the density is an optical depth τ: that of the volume's densest line of sight along an axis of the region, the
        // same meaning in every world (review UX-3d A10)
        const dens = el("input", { type: "range", min: "0", max: "100", value: String(Math.round(33 * Math.log10(look.density / 0.05))),
                                   title: "Плотность свечения: оптическая толщина самого плотного луча вдоль оси области (0,05…54; одинаково во всех мирах)" });
        dens.oninput = () => scene.setVolumeLook({ density: 0.05 * Math.pow(10, dens.value / 33) }, true);
        const thr = el("input", { type: "range", min: "0", max: "100", value: String(Math.round(200 * look.threshold)), title: "Порог: слабее не показывать" });
        thr.oninput = () => scene.setVolumeLook({ threshold: thr.value / 200 }, true);
        extra.push(el("div", { class: "s3d-sub" }, el("span", { class: "muted" }, "плотность"), dens, el("span", { class: "muted" }, "порог"), thr));
      }
      if (L.kind === "vectors") {
        const thr = el("input", { type: "range", min: "0", max: "100", value: "3", title: "Не показывать стрелки слабее этой доли" });
        thr.oninput = () => scene.setVectorThreshold(L.id, thr.value / 100);
        extra.push(el("div", { class: "s3d-sub" }, el("span", { class: "muted" }, "порог"), thr));
      }
      return el("div", {}, el("label", { class: "s3d-layer" }, cb, " ", L.label), extra);
    });
    const prow = scene.planes().map((P) => {
      const cb = el("input", { type: "checkbox" }); cb.checked = P.visible;
      cb.onchange = () => scene.setPlaneVisible(P.id, cb.checked);
      return el("label", { class: "s3d-layer" }, cb, " ", el("span", { class: "sw-chip", style: { background: PLANE_COLORS[P.id] } }, String(P.id)), ` срез в 3D: ${(P.meta || {}).label || ""}`);
    });
    fill(layersBox, rows, prow, el("div", { class: "help" }, "Каждую часть можно выключить, чтобы видеть остальные. Окна срезов остаются."));
  }

  function drawPlanePanel() {
    if (!H) { fill(planeBoxEl, el("div", { class: "muted" }, "Мир строится…")); return; }
    if (maxPlanes() === 0) { fill(planeBoxEl, el("div", { class: "muted" }, "В этой сцене срезов нет: поля в ней не считаются.")); return; }
    const p = planes.find((q) => q.id === selected);
    if (!p) { fill(planeBoxEl, el("div", { class: "muted" }, planes.length ? "Выберите срез: щелчок по плоскости в 3D или по её окну." : "Срезов нет: «＋ Срез».")); return; }
    const box = H.scene3d.box, a = anglesOfNormal(p.normal), units = H.scene3d.units || "";
    const inp = (v, lo, hi, step) => el("input", { type: "number", value: (+v).toFixed(3), min: lo, max: hi, step, style: { width: "6.5em" } });
    const xs = [0, 1, 2].map((i) => inp(p.origin[i], box[0][i], box[1][i], 0.01 * (box[1][i] - box[0][i])));
    const th = inp(a.theta, 0, 180, 1), ph = inp(a.phi, 0, 360, 1);
    const auto = el("input", { type: "checkbox" }); auto.checked = p.auto;
    const spd = inp(p.speed, -100, 100, 0.5);
    const apply = () => sendPlane(p.id, { origin: xs.map((x) => +x.value), normal: normalFromAngles(+th.value, +ph.value), auto: auto.checked, speed: +spd.value });
    for (const x of [...xs, th, ph, spd]) x.onchange = apply;
    auto.onchange = apply;
    const preset = (label, n, title) => el("button", { title, onclick: () => sendPlane(p.id, { normal: n }) }, label);
    const names = (H.scene3d.coord_names || ["x", "y", "z"]);
    fill(planeBoxEl,
      el("div", {}, el("span", { class: "sw-chip", style: { background: PLANE_COLORS[p.id] } }, String(p.id)), el("b", {}, ` ${p.label}`)),
      el("div", { class: "kv" },
        el("span", {}, `центр ${names.join(", ")}, ${units}`), el("span", {}, xs),
        el("span", {}, `наклон нормали от оси ${names[2]} θ, °`), th,
        el("span", {}, "азимут нормали φ, °"), ph),
      el("div", { class: "row" }, preset(`${names[1]} = c`, [0, -1, 0], `Плоскость ${names[0]}–${names[2]}`), preset(`${names[0]} = c`, [1, 0, 0], `Плоскость ${names[1]}–${names[2]}`),
        preset(`${names[2]} = c`, [0, 0, 1], `Плоскость ${names[0]}–${names[1]}`),
        el("button", { title: "Центр плоскости — в середину области", onclick: () => sendPlane(p.id, { origin: H.scene3d.planes.center }) }, "в центр"),
        el("button", { title: "Убрать срез", onclick: () => ctx.send("view", { op: "remove", id: p.id }) }, "убрать"),
        el("button", { title: "Вернуть срезы по умолчанию: один срез в середине", onclick: () => ctx.send("view", { op: "reset" }) }, "по умолчанию")),
      el("div", { class: "row" }, el("label", {}, auto, " автосмещение по нормали"), el("span", { class: "muted" }, `скорость, ${units}/${H.scene3d.planes.time_unit || "с"}`), spd),
      el("div", { class: "help" }, "Срез стоит, где его поставили, и сохраняется в новом мире этого запуска. Автосмещение (по умолчанию выключено) ведёт плоскость вдоль её нормали, пока идёт время мира («▶»); в движении срез грубый (без сверки), полный — когда автосмещение выключено. Мышью: стрелка двигает срез вдоль нормали (W), кольца наклоняют (E)."),
      ro() ? el("div", { class: "warn" }, roText()) : null);
    if (ro()) for (const x of planeBoxEl.querySelectorAll("input,button")) x.disabled = true;
  }

  // the next plane goes to the middle of the region, perpendicular to the planes there, also to turned ones
  // (owner, 2026-10-27; review C5): one plane -> its default if perpendicular, else n1 x (the axis least along n1);
  // two planes -> n1 x n2
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const unit = (a) => { const L = Math.hypot(...a); return a.map((c) => c / L); };
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  function nextNormal(id) {
    const def = H.scene3d.planes.defaults[String(id)], taken = planes.map((p) => unit(p.normal));
    if (taken.every((t) => Math.abs(dot(t, def)) < 1e-6)) return def;
    if (taken.length === 1) {
      const n1 = taken[0], axes = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
      const e = axes.reduce((a, b) => (Math.abs(dot(a, n1)) <= Math.abs(dot(b, n1)) ? a : b));
      return unit(cross(n1, e));
    }
    const c = cross(taken[0], taken[1]);
    return Math.hypot(...c) > 1e-9 ? unit(c) : unit(cross(taken[0], [0, 0, 1]));
  }
  function addPlane() {
    if (!H || ro() || planes.length >= maxPlanes()) return;  // before the world's header there is no scene yet
    const used = new Set(planes.map((p) => p.id));
    const id = [1, 2, 3].find((i) => !used.has(i));
    if (!id) return;
    sendPlane(id, { origin: H.scene3d.planes.center, normal: nextNormal(id) });
  }

  // while a plane is dragged: a preview from the volume in its window (when a volume was computed), or a coarse slice
  // from the run (one request in flight at a time)
  let lastPrev = 0;
  const inflight = new Set();
  function preview(id, g) {
    if (!H) return;
    const now = performance.now();
    if (!scene.state.vol) {
      if (!inflight.has(id) && !ro()) { inflight.add(id); ctx.send("view", { op: "preview", id, origin: g.origin, normal: g.normal }); }
      return;
    }
    if (now - lastPrev < 80) return;
    lastPrev = now;
    const ss = g.poly.map((q) => q[0]), ts = g.poly.map((q) => q[1]);
    const s0 = Math.min(...ss), s1 = Math.max(...ss), t0 = Math.min(...ts), t1 = Math.max(...ts);
    const ns = 96, nt = 96, I = new Float32Array(ns * nt);
    for (let it = 0; it < nt; it++) for (let is = 0; is < ns; is++) {
      const s = s0 + (s1 - s0) * is / (ns - 1), t = t0 + (t1 - t0) * it / (nt - 1);
      I[it * ns + is] = scene.sampleVolume([0, 1, 2].map((i) => g.origin[i] + s * g.u[i] + t * g.v[i]));
    }
    // the volume's values are fractions of the VOLUME's peak: read them with the volume's own quantity (review B2-4)
    const last = windows.lastMeta ? windows.lastMeta(id) : null;
    windows.setPreview(id, { meta: { s: [s0, s1, ns], tt: [t0, t1, nt], origin: g.origin, u: g.u, v: g.v, z_near: H.accuracy?.z_near, window_est: 0,
                                     units: last?.units ?? H.scene3d.units, coord_names: last?.coord_names ?? H.scene3d.coord_names, depth: last?.depth,
                                     quantity: volQuantity || undefined }, I });
  }

  window.addEventListener("editablechange", () => {  // the player's cursor or run state changed what may be edited
    addBtn.disabled = !H || ro() || planes.length >= maxPlanes();
    addBtn.title = ro() ? roText() : "Добавить плоскость среза (до трёх): ставится в середину, перпендикулярно уже стоящим";
    scene.select(selected);  // the gizmo only where planes can be moved
  });

  // Delete removes the selected slice (not Backspace, a key pressed by habit; review UX-3d A16)
  document.addEventListener("keydown", (e) => {
    if (!scene.el.isConnected || e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;
    // the world's own window (a 2-D world's plane) is never removed: nothing to send (review LB1-p02-ux X2)
    if (e.key === "Delete" && selected && !ro() && !windows.isFixed(selected)) ctx.send("view", { op: "remove", id: selected });
  });

  return {
    scene, windows, center, addBtn, scaleSel,
    layersPanel: layersBox, planePanel: planeBoxEl,
    header: () => H,
    reset() { H = null; planes = []; selected = null; volQuantity = null; last = new Map(); setSeq = 0; },
    // key frames (player.js): the objects set last (references to their messages) and the lengths of the appending
    // layers; restoring cuts the appending layers back, removes what was set since and sets again what changed
    snapshot() {
      return { last: new Map(last), appends: scene.snapshotAppends(), planes, selected, volQuantity };
    },
    restore(k) {
      const planesThen = (k.last.get("planes") || { meta: { planes: [] } }).meta.planes;
      const objectOf = (id) => ((H && H.scene3d.objects) || []).find((o) => o.id === id);
      for (const [key, m] of last) {  // checked first: nothing changes when a key frame cannot be restored
        if (k.last.has(key)) continue;
        if (m.meta.type === "target" && !objectOf(m.meta.id)) throw new Error(`${key} set after the key frame`);
        if (m.meta.type === "slice" && planesThen.some((q) => q.id === m.meta.id)) throw new Error(`${key} computed after the key frame`);
      }
      scene.restoreAppends(k.appends);
      for (const [key, m] of last) {
        if (k.last.has(key)) continue;
        if (m.meta.type === "planes") apply({ type: "planes", planes: [] }, {});
        else if (m.meta.type === "box") scene.setBox(H.scene3d.box);  // the box of the header, as before the message
        else if (m.meta.type === "target") scene.setObject(objectOf(m.meta.id));  // the object without its image
        else if (m.meta.type !== "slice") scene.removeLayer(m.meta.id);
      }
      // the box first (objects are sized by it), then what changed in the order of the record (review CK-13); when the
      // planes are set again, every slice of the key frame on them too: a plane recreated by setPlanes has lost its
      // image and its window (review CK-2)
      const changed = [...k.last].filter(([key, m]) => last.get(key) !== m);
      const replanes = changed.some(([key]) => key === "planes");
      const again = replanes ? [...k.last].filter(([key, m]) => last.get(key) !== m || key.startsWith("slice:")) : changed;
      again.sort((a, b) => (a[0] === "box" ? -1 : b[0] === "box" ? 1 : a[1].seq - b[1].seq));
      for (const [, m] of again) apply(m.meta, m.blobs);
      last = new Map(k.last);
      planes = k.planes; volQuantity = k.volQuantity;
      selected = planes.some((q) => q.id === k.selected) ? k.selected : null;
      scene.select(selected); drawPlanePanel(); drawLayers();
      addBtn.disabled = ro() || planes.length >= maxPlanes();
    },
    onHeader(meta) {
      H = meta;
      scene.setScene(meta.scene3d, { plane2d: plane2d(meta) });
      scene.setScale(scaleSel.value, logFloor(H));
      drawLayers(); drawPlanePanel();
      addBtn.disabled = ro() || maxPlanes() === 0;
      addBtn.style.display = maxPlanes() === 0 ? "none" : "";
    },
    // the 3-D protocol's messages; returns true when the message was one of them
    onMessage(meta, blobs) {
      const ok = apply(meta, blobs);
      if (ok && SET.has(meta.type) && !(meta.type === "slice" && meta.preview)) last.set(keyOf(meta), { meta, blobs, seq: ++setSeq });
      return ok;
    },
  };

  function apply(meta, blobs) {
      switch (meta.type) {
        case "volume": volQuantity = meta.quantity || null; scene.setVolume(meta.id, meta.dims, blobs.data); return true;
        case "box": scene.setBox(meta.box); return true;
        case "vectors": scene.setVectors(meta.id, blobs.pos, blobs.vec); return true;
        case "target": scene.setObjectImage(meta.id, meta.shape[0], meta.shape[1], blobs.img); return true;
        case "path": scene.appendPath(meta.id, meta.from, blobs.pts, { label: meta.label }); return true;
        case "triads": scene.addTriads(meta.id, blobs.pos, blobs.mats, { label: meta.label }); return true;
        case "marks": scene.setMarks(meta.id, blobs.pos, { label: meta.label }); return true;
        case "lines": scene.setLines(meta.id, blobs.pts, blobs.rgb, { label: meta.label, visible: meta.visible !== false }); return true;
        case "arrow": scene.setArrow(meta.id, meta.from, meta.vec, { label: meta.layer || meta.label, color: meta.color, text: meta.label }); return true;
        case "mesh": scene.setMesh(meta.id, blobs.pos, blobs.idx, blobs.rgb, { label: meta.label, opacity: meta.opacity ?? 1, visible: meta.visible !== false }); return true;
        case "planes":
          planes = meta.planes;
          scene.setPlanes(planes); windows.sync(planes);
          addBtn.disabled = ro() || planes.length >= maxPlanes();
          if (selected && !planes.some((p) => p.id === selected)) selected = null;
          drawPlanePanel(); drawLayers();
          return true;
        case "slice":
          inflight.delete(meta.id);
          if (meta.preview) { windows.setPreview(meta.id, { meta, I: blobs.I, coarse: true }); return true; }
          scene.setPlaneImage(meta.id, meta, blobs.I, blobs.phase); windows.setSlice(meta.id, meta, blobs);
          return true;
        default: return false;
      }
  }
}
