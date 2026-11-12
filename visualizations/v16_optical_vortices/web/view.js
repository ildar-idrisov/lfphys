// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v16 view: an optical vortex in the shared 3-D environment (/static/js/env3d.js): the helical surfaces of equal phase
// (one mesh per phase of the slowed optical period, revealed by the run as its time reaches it; a frame names the phase
// it shows), the intensity as a volume, the energy flow lines, the generator, the rotating element turned by the
// matrix each frame carries, the detector; slice planes with intensity and phase. Panels: the beam, the angular
// momentum per photon (measured against the closed forms: per unit length in the canonical split and Barnett's split
// of the flux through the plane), the detector's samples and the spectrum of the last
// measurement. Drawing only: every number and every surface comes from the run.
import { el, fill, num, panel, css, fresh2d } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "sqrt" });
  const beamBox = el("div", { class: "kv" }), amBox = el("div", {}), timeBox = el("div", { class: "kv" });
  const detText = el("div", { class: "kv" });
  const cvTrace = el("canvas", { style: { width: "100%", height: "120px", display: "block" } });
  const cvSpec = el("canvas", { style: { width: "100%", height: "120px", display: "block" } });
  const rightPanels = [panel("Пучок", beamBox), panel("Момент импульса на фотон", amBox),
                       panel("Вращение и детектор", el("div", {}, detText, cvTrace, cvSpec)),
                       panel("Время и фаза", timeBox),
                       panel("Слои сцены", env.layersPanel), panel("Срез: положение и наклон", env.planePanel)];
  let H = null, am = null, beat = null, helix = new Map(), want = 0, shownBin = -1, lastFrame = null;
  let trace = { ts: [], v: [], n: 0 };
  for (const cv of [cvTrace, cvSpec]) new ResizeObserver(() => drawDetector()).observe(cv);

  // --- the equiphase sheets of the phase a frame names ------------------------------------------------------------
  function nearest(k) {  // the phase k, or the last one revealed before it (never a later one)
    if (helix.has(k)) return k;
    let best = -1;
    for (const b of helix.keys()) if (b <= k && b > best) best = b;
    return best;
  }
  function showBin(force = false) {
    const k = nearest(want);
    if (k < 0) { if (shownBin >= 0) env.scene.removeLayer("helix"); shownBin = -1; return; }
    if (!force && k === shownBin) return;
    const h = helix.get(k);
    env.scene.setMesh("helix", h.blobs.pos, h.blobs.idx, h.blobs.rgb, { label: h.meta.label, opacity: 0.62 });
    shownBin = k;
  }
  function placeRotor(f) {
    const b = H && H.beam;
    if (!b || b.z_rot === null || b.z_rot === undefined) return;
    const A = f && f.rotA ? f.rotA : [1, 0, 0, 0, 1, 0, 0, 0, 1];
    env.scene.transformMesh("rotor", A, [0, 0, b.z_rot]);
  }

  // --- panels --------------------------------------------------------------------------------------------------------
  function drawBeam() {
    if (!H) return;
    const b = H.beam || {};
    if (b.model === "fork") {
      fill(beamBox, el("span", {}, "источник"), el("span", {}, "гауссов пучок на голограмме-«вилке»"),
        el("span", {}, "заряд l, голограмма"), el("span", { class: "mono" }, `${b.l}, ${b.kind}`),
        el("span", {}, "период Λ, w0, λ"), el("span", { class: "mono" }, `${num(b.period, 4)}, ${num(b.w0, 4)}, ${num(b.lam, 4)} мкм`),
        el("span", {}, "глубина области"), el("span", { class: "mono" }, `${num(b.z_end, 4)} мкм`),
        el("span", {}, "что смотреть"), el("span", {}, "порядок m уходит под углом sin θ = −mλ/Λ (порядок +1 — к отрицательным x) и несёт заряд m·l; доли мощности порядков — в проверках"));
      return;
    }
    const pol = { "+1": "круговая σ = +1", "-1": "круговая σ = −1", lin: "линейная (x): σ̄ = 0" }[b.pol] || b.pol;
    fill(beamBox,
      el("span", {}, "источник"), el("span", {}, b.gen === "mode" ? `мода LG, p = ${b.p}, l = ${b.l}` : `гауссов пучок за спиральной пластинкой, l = ${b.l}`),
      el("span", {}, "модель"), el("span", { class: b.model === "exact" ? "" : "st-bad" }, b.model === "exact" ? "точная: векторное решение уравнений Максвелла" : "ПРИБЛИЖЕНИЕ: параксиальная"),
      el("span", {}, "w0, λ"), el("span", { class: "mono" }, `${num(b.w0, 4)} мкм, ${num(b.lam, 4)} мкм (w0/λ = ${num(b.w0 / b.lam, 3)})`),
      el("span", {}, "z_R, расходимость"), el("span", { class: "mono" }, `${num(b.zr, 4)} мкм, θ = λ/(πw0) = ${num(b.theta_div, 3)} рад`),
      el("span", {}, "поляризация"), el("span", {}, pol),
      b.model === "exact" && b.kept !== undefined ? el("span", {}, "источник в пучке") : null,
      b.model === "exact" && b.kept !== undefined ? el("span", { class: b.kept < 0.9999 ? "warn" : "mono" }, b.kept < 0.9999
        ? (b.gen === "mode" ? `${num(100 * b.kept, 4)} % мощности перетяжки: остальное — затухающие волны (q > k), их у пучка нет; w0 — ширина спектра, а не измеренная перетяжка`
          : `${num(100 * b.kept, 4)} % мощности на z = 0: остальное — затухающие волны ближнего поля пластинки, они гаснут за несколько λ (в заголовке мира); дальше пучок точен`)
        : "весь (спектр за q = k пренебрежимо мал)") : null,
      el("span", {}, "винтовые фронты"), el("span", { class: "mono" }, b.helix_region ? `z = ${num(b.helix_region[0], 4)} … ${num(b.helix_region[1], 4)} мкм` : "нет (l = 0: фронты — не винты)"));
  }
  function drawAm() {
    if (H && H.beam && H.beam.model === "fork") { fill(amBox, el("div", { class: "muted" }, "Для голограммы момент на фотон не считается: смотрите заряды и доли мощности порядков в проверках.")); return; }
    if (!am) { fill(amBox, el("div", { class: "muted" }, "Считается…")); return; }
    const exact = H && H.beam && H.beam.model === "exact";
    const rows = [["L_z (орбитальный)", am.L, am.L_ref, "#22b8ff"], [exact ? "S_z (спин)" : "S_z (спин, по полю модели)", am.S, am.S_ref, "#ff8a1f"], ["J_z = L_z + S_z", am.J, am.J_ref, "#9fe870"]];
    const big = Math.max(1, ...rows.map((r) => Math.abs(r[1] ?? 0)), ...rows.map((r) => Math.abs(r[2] ?? 0)));
    const bar = (v, c) => el("div", { style: { position: "relative", height: "8px", background: "rgba(127,127,127,0.15)", margin: "2px 0 6px" } },
      el("div", { style: { position: "absolute", left: v >= 0 ? "50%" : `${50 - 50 * Math.abs(v) / big}%`, width: `${50 * Math.abs(v) / big}%`, top: 0, bottom: 0, background: c } }),
      el("div", { style: { position: "absolute", left: "50%", top: "-2px", bottom: "-2px", width: "1px", background: "#888" } }));
    const zt = am.z !== undefined && am.z !== null ? `z = ${num(am.z, 4)} мкм` : "z_c";
    fill(amBox,
      el("div", { class: "muted" }, `на единицу длины, каноническое разделение (Блиох и др. 2010), плоскость ${zt}`),
      rows.map(([lab, v, r, c]) => el("div", {}, el("div", { class: "kv" }, el("span", {}, lab),
        el("span", { class: "mono" }, `${num(v, 7)} ħ (формула ${num(r, 7)})`)), bar(v ?? 0, c))),
      el("div", { class: "kv" },
        exact ? el("span", {}, "⟨cos θ⟩ спектра") : null, exact ? el("span", { class: "mono" }, num(am.cos, 6)) : null,
        exact ? el("span", {}, "поток момента / поток энергии × ω") : null, exact ? el("span", { class: "mono" }, `${num(am.flux_J, 7)} ħ`) : null,
        exact ? el("span", {}, "по потоку (Барнетт): спин") : null, exact ? el("span", { class: "mono" }, `${num(am.S_flux, 7)} ħ (формула ${num(am.S_flux_ref, 7)})`) : null,
        exact ? el("span", {}, "по потоку (Барнетт): орбита") : null, exact ? el("span", { class: "mono" }, `${num(am.L_flux, 7)} ħ (формула ${num(am.L_flux_ref, 7)})`) : null,
        exact ? el("span", {}, "по Пойнтингу ∫(r×P)_z") : null, exact ? el("span", { class: "mono" }, `${num(am.J_poynting, 7)} ħ (формула ${num(am.J_poynting_ref, 7)})`) : null,
        exact && am.ez !== undefined ? el("span", {}, "продольное поле |E_z|/|E|") : null, exact && am.ez !== undefined ? el("span", { class: "mono" }, num(am.ez, 4)) : null),
      el("div", { class: "help" }, exact
        ? `Точный пучок: каждая плоская волна имеет спиральность σ, полный момент на фотон J_z = l + σ точно. Как его делить на спин и орбиту — вопрос определения. В каноническом разделении на единицу длины (верхние строки) спин S_z = σ⟨cos θ⟩ по модулю меньше 1, а орбитальный L_z = l + σ(1 − ⟨cos θ⟩) сдвинут от l в сторону σ. В разделении потока через плоскость по Барнетту (Монтейру и др. 2009) спин σ⟨(1 + cos²θ)/2⟩/⟨cos θ⟩ по модулю больше 1 — сдвиг в другую сторону. От определения не зависит только J_z. Измерено по полю на плоскости ${zt} (плотности Берри).`
        : `Параксиальная модель: поляризация однородна, поэтому спин S_z = σ̄ (он посчитан по полю модели, но так она устроена); L_z измерен по фазе поля — равен l. Плоскость ${zt}. Точная модель покажет расщепление.`));
  }
  function drawTime(f) {
    if (!H) return;
    const T = H.t_show, lam = (H.beam && H.beam.lam) || 1;
    const Topt = lam * 1e-6 / 299792458;
    const k = f ? f.bin : 0, have = f ? f.revealed : helix.size;
    fill(timeBox,
      el("span", {}, "оптическая фаза"), el("span", {}, `показана замедленно: 1 период за ${num(T * 1e3, 4)} мс мира (в действительности ${num(Topt * 1e15, 4)} фс, замедление ×${num(T / Topt, 3)})`),
      el("span", {}, "фаза на рисунке"), el("span", { class: "mono" }, helix.size || have ? `${k + 1} из ${H.nb}` : "—"),
      el("span", {}, "фаз открыто"), el("span", { class: have < H.nb ? "warn" : "muted" }, helix.size === 0 && !have ? "нет винтовых фронтов в этом мире" : have < H.nb ? `${have}: остальные — когда до них дойдёт время` : "все: дальше фронты повторяются"),
      f && f.f_rot !== undefined ? el("span", {}, "элемент повернулся на") : null,
      f && f.f_rot !== undefined ? el("span", { class: "mono" }, `${num((f.angle * 180 / Math.PI) % 360, 4)}° (f = ${num(f.f_rot, 4)} Гц)`) : null,
      f && f.f_rot !== undefined ? el("span", {}, "два хода времени") : null,
      f && f.f_rot !== undefined ? el("span", { class: "muted" }, "элемент вращается в реальном времени мира, оптическая фаза замедлена: взаимное вращение винтов и элемента на экране — не измеряемый сдвиг (он отсчитан от истинной частоты света)") : null);
  }
  function sizeCanvas(cv) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2), W = cv.clientWidth, Hh = cv.clientHeight;
    if (!W || !Hh) return null;
    if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(Hh * dpr); }
    const g = fresh2d(cv.getContext("2d"), dpr);
    g.fillStyle = css("--canvas") || "#0b0e14"; g.fillRect(0, 0, W, Hh);
    return { g, W, H: Hh };
  }
  function drawDetector() {
    if (!H) return;
    const b = H.beam || {};
    if (!b.rot || b.rot === "none") {
      fill(detText, el("span", {}, "элемент"), el("span", { class: "muted" }, "нет вращающегося элемента в этом мире"));
      for (const cv of [cvTrace, cvSpec]) cv.style.display = "none";
      return;
    }
    for (const cv of [cvTrace, cvSpec]) cv.style.display = "block";
    const what = b.rot === "disc" ? "шероховатый диск; детектор за фильтром мод ±l" : "призма Дове в одном плече интерферометра";
    fill(detText, el("span", {}, "элемент"), el("span", {}, what),
      el("span", {}, "отсчётов"), el("span", { class: "mono" }, String(trace.n)),
      el("span", {}, "биения: измерено"), el("span", { class: "mono" }, beat ? `${num(beat.f_meas, 7)} Гц (измерение ${beat.n})` : "— (нужно 128 отсчётов: два оборота)"),
      el("span", {}, "формула 2|l|f"), el("span", { class: "mono" }, beat ? `${num(beat.f_ref, 7)} Гц` : "—"),
      el("span", {}, b.rot === "disc" ? "сдвиг частоты света, рассеянного на ось" : "сдвиг частоты повёрнутого плеча (против плеча в покое)"),
      el("span", { class: "mono" }, beat ? `${num(beat.shift_meas, 6)} Гц (формула ${num(beat.shift_ref, 6)})` : "—"));
    // the samples: the last 256
    const c = sizeCanvas(cvTrace);
    if (c && trace.n > 1) {
      const { g, W, H: Hh } = c, n0 = Math.max(0, trace.n - 256), left = 6, right = 6, top = 12, bot = 6;
      let lo = Infinity, hi = -Infinity;
      for (let i = n0; i < trace.n; i++) { lo = Math.min(lo, trace.v[i]); hi = Math.max(hi, trace.v[i]); }
      if (!(hi > lo)) { hi = lo + Math.abs(lo || 1) * 1e-6; }
      const t0 = trace.ts[n0], t1 = trace.ts[trace.n - 1] || t0 + 1;
      const X = (t) => left + (W - left - right) * (t - t0) / ((t1 - t0) || 1), Y = (v) => top + (Hh - top - bot) * (1 - (v - lo) / (hi - lo));
      g.strokeStyle = "#9fe870"; g.lineWidth = 1.2; g.beginPath();
      for (let i = n0; i < trace.n; i++) { const x = X(trace.ts[i]), y = Y(trace.v[i]); if (i === n0) g.moveTo(x, y); else g.lineTo(x, y); }
      g.stroke();
      g.fillStyle = css("--muted") || "#999"; g.font = "10px system-ui";
      g.fillText(`сигнал детектора, последние ${trace.n - n0} отсчётов (${num((t1 - t0) * 1e3, 4)} мс)`, left, 10);
    }
    const s = sizeCanvas(cvSpec);
    if (s && beat) {
      const { g, W, H: Hh } = s, f = beat.f, P = beat.P, left = 6, right = 6, top = 12, bot = 14;
      const fmax = f[f.length - 1] || 1;
      const X = (x) => left + (W - left - right) * x / fmax, Y = (p) => top + (Hh - top - bot) * (1 - p);
      g.strokeStyle = css("--ink") || "#ddd"; g.lineWidth = 1; g.beginPath();
      for (let i = 0; i < f.length; i++) { const x = X(f[i]), y = Y(P[i]); if (i) g.lineTo(x, y); else g.moveTo(x, y); }
      g.stroke();
      if (beat.f_ref > 0) { g.strokeStyle = "#ff8a1f"; g.setLineDash([4, 3]); g.beginPath(); g.moveTo(X(beat.f_ref), top); g.lineTo(X(beat.f_ref), Hh - bot); g.stroke(); g.setLineDash([]); }
      if (beat.f_meas > 0) { g.strokeStyle = "#9fe870"; g.beginPath(); g.moveTo(X(beat.f_meas), top); g.lineTo(X(beat.f_meas), Hh - bot); g.stroke(); }
      g.fillStyle = css("--muted") || "#999"; g.font = "10px system-ui";
      g.fillText("спектр измерения: зелёный — пик, оранжевый пунктир — 2|l|f", left, 10);
      for (let q = 0; q <= 4; q++) g.fillText(num(fmax * q / 4, 3), X(fmax * q / 4) - (q === 4 ? 24 : 4), Hh - 2);
    }
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, "Оптические вихри"),
      el("p", {}, "У пучка с фазой e^{ilφ} поверхности равной фазы — не плоскости, а l переплетённых винтов с шагом lλ: в 3D это полупрозрачные винтовые поверхности (слой «Поверхности равной фазы»). Свет на экране замедлен: один оптический период длится несколько сотен миллисекунд времени мира, поэтому винты «вращаются» (на самом деле фронт бежит вдоль z со скоростью света). Фазы периода посчитаны движком и открываются, когда до них доходит время мира; дальше фронты повторяются."),
      el("p", {}, "Объём — интенсивность |E|² пучка (кольцо: на оси вихря поле равно нулю). Жёлтые линии — поток энергии (вектор Пойнтинга), голубые — орбитальный (канонический) ток: они закручиваются вокруг оси, как спирали. В срезах — интенсивность и фаза на цветовом круге (режим «фаза»): обход вокруг оси даёт l полных оборотов цвета."),
      el("p", {}, "Модель: «точная» — векторное решение уравнений Максвелла (сумма плоских волн спиральности σ, только распространяющиеся волны: при w0 ≲ λ часть спектра источника за q = k отброшена — мир это помечает, а если отброшено больше 10 % мощности, не строится); «параксиальная» — мода Лагерра–Гаусса на однородной поляризации (помечено как приближение). При острой фокусировке (w0 ~ λ) параксиальная картина ломается: появляется продольное поле (первого порядка по λ/w0), а момент делится на спин и орбиту иначе. Как именно — зависит от определения: в каноническом разделении на единицу длины спин S_z = σ⟨cos θ⟩ по модулю меньше 1, в разделении потока по Барнетту — больше 1; сумма J_z = l + σ одна и та же и сохраняется точно (панель «Момент импульса»)."),
      el("p", {}, "Вращение: шероховатый диск на пути пучка рассеивает свет; детектор смотрит через фильтр мод ±l (как у Лавери и др., 2013): часть, сохранившая +l, не сдвинута, часть, рассеянная в −l, сдвинута на −2lf — интенсивность бьётся с частотой 2|l|f; свет, рассеянный на ось, сдвинут на −lf. Призма Дове (Куртиаль и др., 1998) поворачивает изображение вдвое быстрее себя и меняет знак l: в интерферометре мощность бьётся с частотой 2|l|f. Детектор копит отсчёты по ходу времени; каждые два оборота спектр отсчётов даёт измеренную частоту, которая сравнивается с формулой. Частоту вращения f можно менять на ходу (слева). Элемент на экране вращается в реальном времени мира, а оптическая фаза замедлена: их взаимное вращение на картинке — не тот сдвиг, который измеряется."),
      el("p", {}, "Генераторы (тонкие маски — приближение): спиральная фазовая пластинка (толщина растёт с азимутом) делает из гауссова пучка вихрь с зарядом l — не одну моду LG; у скалярного поля орбитальный момент lħ на фотон, у векторного L_z = l + σ(1 − ⟨cos θ⟩), где ⟨cos θ⟩ задан светом, который особая точка в центре идеальной пластинки отправляет под большими углами; голограмма-«вилка» даёт порядки, m-й несёт заряд m·l и уходит к x < 0 при m > 0.")),
    reset() { env.reset(); H = null; am = null; beat = null; helix = new Map(); want = 0; shownBin = -1; lastFrame = null; trace = { ts: [], v: [], n: 0 }; },
    snapshot() { return { env: env.snapshot(), helix: new Map(helix), am, beat, n: trace.n }; },
    restore(k) {
      env.restore(k.env);
      helix = new Map(k.helix); am = k.am; beat = k.beat; trace.n = k.n;
      showBin(true); placeRotor(lastFrame); drawAm(); drawDetector(); drawTime(lastFrame);
    },
    onHeader(meta) {
      env.onHeader(meta); H = meta; am = null; beat = null; helix = new Map(); want = 0; shownBin = -1; lastFrame = null;
      trace = { ts: [], v: [], n: 0 };
      drawBeam(); drawAm(); drawDetector(); drawTime(null);
    },
    onMessage(meta, blobs) {
      if (meta.type === "helix") { helix.set(meta.bin, { meta, blobs }); if (meta.bin === want || shownBin < 0) showBin(); return; }
      if (meta.type === "trace") {
        for (let i = 0; i < meta.count; i++) { trace.ts[trace.n + i] = blobs.ts[i]; trace.v[trace.n + i] = blobs.v[i]; }
        trace.n += meta.count; return;
      }
      if (meta.type === "beat") { beat = { ...meta, f: blobs.f, P: blobs.P }; drawDetector(); return; }
      if (meta.type === "am") { am = meta; drawAm(); return; }
      if (env.onMessage(meta, blobs)) { if (meta.type === "mesh" && meta.id === "rotor") placeRotor(lastFrame); return; }
    },
    render(meta) {
      if (!H) return;
      if (meta) {
        lastFrame = meta;
        if (meta.bin !== want) { want = meta.bin; showBin(); }
        placeRotor(meta);
        drawTime(meta);
      }
      drawDetector();
      env.scene.requestRender();
    },
  };
}
