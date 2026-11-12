// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v10 view: what a fast observer sees. Next to the 3-D scene (the shared environment /static/js/env3d.js: the lab now
// — bodies Lorentz-contracted at their lab-simultaneous places, the retarded shapes the light comes from, the observer
// with its velocity and the lab directions its field of view takes the light from) the camera window
// (/static/js/imagewin.js) shows the image the run computed by light-time ray tracing. Drawing only: images, retarded
// shapes, Doppler factors and emission times all come from the run.
import { el, fill, num, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";
import { createImageWindow, inflate, unsubRows } from "/static/js/imagewin.js";

function describe(meta, f, i, j) {
  const [H, W] = meta.shape, k = j * W + i;
  if (!f.body) return "";
  const b = f.body[k];
  if (b === -2) return "ничего: свет сюда не приходит (чёрный фон)";
  const Dq = f.D[k], D = Dq ? Math.pow(2, (Dq - 1) / 65534 * 32 - 16) : NaN, T = f.T[k];
  const who = b === -1 ? "небо (чёрное тело в покое в лаборатории)" : (meta.bodies[b] || `тело ${b}`);
  const parts = [`${who}`];
  if (meta.mode === "snapshot") parts.push(`температура покоя ${num(T, 5)} K (снимок без времени света — так не видно)`);
  else if (meta.mode === "geometry") parts.push(`D = ${num(D, 4)}`, `нарисовано в цвете покоя ${num(T, 5)} K; на самом деле видно как чёрное тело ${num(D * T, 4)} K`);  // review B3-11
  else parts.push(`D = ${num(D, 4)}`, `видно как чёрное тело ${num(D * T, 4)} K (в покое ${num(T, 5)} K)`);
  const dq = f.delay[k];
  if (dq && meta.mode !== "snapshot") parts.push(`свет излучён за ${num((dq - 1) / 65534 * meta.delay_max * 1e9, 4)} нс до наблюдения`);
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
  let q = 0, t = 0;
  for (let i = 0; i < ku - 1; i++) for (let j = 0; j < kv - 1; j++) {
    const fi = Math.abs(i + 1 - ic) > Math.abs(i - ic) ? i + 1 : i, fj = Math.abs(j + 1 - jc) > Math.abs(j - jc) ? j + 1 : j;
    const far = fi * kv + fj;
    for (const k of [i * kv + j, i * kv + j + 1, (i + 1) * kv + j + 1, (i + 1) * kv + j]) {
      P.set(pos.subarray(3 * k, 3 * k + 3), 3 * q); C.set(rgb.subarray(3 * far, 3 * far + 3), 3 * q); q++;
    }
    I.set([q - 4, q - 3, q - 2, q - 4, q - 2, q - 1], t); t += 6;
  }
  return { meta: { ...meta, count: q }, blobs: { ...blobs, pos: P, idx: I, rgb: C } };
}

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin" });
  const win = createImageWindow({ title: "Камера наблюдателя: посчитанное изображение", describe });
  env.center.append(win.el);
  const nowBox = el("div", { class: "kv" }), imgBox = el("div", {}), devBox = el("div", { class: "kv" });
  const rightPanels = [panel("Наблюдатель сейчас", nowBox), panel("Изображение", imgBox), panel("Слои сцены", env.layersPanel),
                       panel("Где считалось", devBox)];
  let H = null, images = new Map(), shown = -1, pending = null;

  function drawDev(img) {
    // the image's own device (sent with every image, review B3-8); before the first image, the header's record
    const u = (((H && H.backend) || {}).used || {})["relativity.raytrace"];
    const d = (img && img.device) || (u && u.drawn);
    fill(devBox, el("span", {}, "трассировка лучей"), el("span", { class: "mono" }, d ? `${d.device === "gpu" ? "GPU" : "CPU"}, ${d.precision}` : "—"),
      el("span", {}, "почему"), el("span", {}, d ? d.reason : ""), el("span", {}, "настройки"), el("a", { href: "/settings", target: "_blank" }, "⚙ Устройства"));
  }
  function drawImgPanel(meta) {
    const legend = [];
    if (!meta) { fill(imgBox, el("div", { class: "muted" }, "Изображение появится, когда его посчитает запуск.")); return; }
    legend.push(el("div", { class: meta.mode === "seen" ? "" : "warn" }, meta.mode_label));
    if (meta.mode === "doppler") legend.push(el("div", { class: "help" }, "Ложные цвета: красный — D < 1 (свет покраснел и ослаб), серый — D ≈ 1, синий — D > 1 (посинел и стал ярче); шкала от D = 1/8 до 8 (логарифмическая)."));
    else if (meta.mode === "delay") legend.push(el("div", { class: "help" }, `Ложные цвета: синий — свет излучён недавно, красный — давно (до ${num(meta.delay_max * 1e9, 4)} нс назад).`));
    else legend.push(el("div", { class: "help" }, "Каждая поверхность светит как чёрное тело своей температуры (узор — в системе тела). Наблюдатель видит чёрное тело при D·T: цвет и яркость посчитаны по закону Планка. Наведите на изображение — D, температура, когда излучён свет."));
    legend.push(el("div", { class: "kv" }, el("span", {}, "экспозиция"), el("span", { class: "mono" }, `${meta.auto ? "по кадру" : "как для сцены в покое"}, поправка ${num(meta.ev, 3)} ступ.`),
      el("span", {}, "время кадра"), el("span", { class: "mono" }, `${num(meta.t * 1e9, 6)} нс`),
      el("span", {}, "размер"), el("span", { class: "mono" }, `${meta.shape[1]} × ${meta.shape[0]}`)));
    fill(imgBox, legend);
  }
  function drawNow(f) {
    if (!f || !f.obs) return;
    const b = Math.hypot(...f.obs.beta);
    fill(nowBox, el("span", {}, "время t (лаборатория)"), el("span", { class: "mono" }, `${num(f.t_ns, 6)} нс`),
      el("span", {}, "собственное время τ"), el("span", { class: "mono" }, `${num(f.tau_ns, 6)} нс`),
      el("span", {}, "скорость β"), el("span", { class: "mono" }, b > 0 ? `${num(b, 5)} вдоль (${f.obs.beta.map((c) => num(c / b, 3)).join(", ")}), γ = ${num(f.obs.gamma, 5)}` : "0 (покоится)"),
      el("span", {}, "положение"), el("span", { class: "mono" }, `(${f.obs.x.map((c) => num(c, 4)).join(", ")}) м`));
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
                   `${meta.mode_label} · t = ${num(meta.t * 1e9, 6)} нс`);
      for (const r of meta.retarded || []) {
        if (!blobs.ret_pos) break;
        env.scene.updateMesh(r.id, blobs.ret_pos.subarray(3 * r.from, 3 * (r.from + r.count)), blobs.ret_rgb.subarray(3 * r.from, 3 * (r.from + r.count)));
      }
      shown = seq;
      drawImgPanel(meta);
      drawDev(meta);
    } catch (e) { console.error(e); win.setStatus(el("span", { class: "st-bad" }, "изображение не прочитано: " + e.message)); }
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, "Что видит быстрый наблюдатель"),
      el("p", {}, "Справа — изображение, которое посчитал запуск: для каждого пикселя камеры — фотон, пришедший к наблюдателю в этот момент. Его направление переведено в лабораторию преобразованием Лоренца (аберрация), его путь прослежен назад во времени до тела, которое его излучило (время света), а цвет и яркость — чёрное тело при температуре D·T, где D — доплеровский множитель (цвет Доплера и прожекторный эффект)."),
      el("p", {}, "Быстрое тело не выглядит сплюснутым: шар остаётся кругом (Пенроуз), куб выглядит повёрнутым — видна его задняя грань (Террелл). Приближаясь, тело выглядит дальше и синее, удаляясь — ближе и краснее. Быстрый наблюдатель видит мир стянутым вперёд, впереди — синим и ярким."),
      el("p", {}, "В 3D — лаборатория сейчас: тела в лоренцевом сокращении на своих местах в этот момент (полупрозрачные) и места, откуда пришёл свет, видимый сейчас (запаздывающие формы, яркие — видимые точки), наблюдатель, его скорость и направления в лаборатории, откуда приходит свет на края кадра."),
      el("p", {}, "Скорость наблюдателя меняется на ходу: это буст в текущий момент — изображение меняется сразу (тот же свет, другие направления и частоты). Скорость тел — параметр мира. Режимы «только геометрия» и «мгновенный снимок» — для сравнения: так не видно."),
      el("p", {}, "Сверки (справа, «Проверки»): небо против T/(γ(1 − β cos θ′)), звёзды против формулы аберрации, время излучения и D против запаздывающего времени, контур шара — окружность (Пенроуз), сцена в покое — обычные лучи.")),
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
