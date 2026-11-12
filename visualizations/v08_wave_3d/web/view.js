// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v08 view: the 3-D scene of the run (the screen with its aperture, the incident wave, the light behind the screen,
// the energy current, the target) and up to three slice planes with their windows (the shared 3-D environment:
// /static/js/env3d.js). Every element can be switched off; planes are placed, moved and turned by hand (gizmo) or by
// parameters; each slice is computed by the run for its plane (view command "plane").
import { el, fill, num, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";

export function createView(ctx) {
  // the log scale starts at (3 x the window's error)^2 of the peak, in the windows and in the 3-D scene alike
  const env = createEnv3D(ctx, { logFloor: (H) => Math.max(1e-6, (3 * ((H && H.accuracy && H.accuracy.window) || 0)) ** 2) });
  let modelling = null;  // the modelling in force: the header's, then the latest "modelling" message
  const modeBox = el("div", {}), accBox = el("div", { class: "kv" }), devBox = el("div", { class: "kv" });
  const rightPanels = [panel("Слои сцены", env.layersPanel), panel("Срез: положение и наклон", env.planePanel),
                       panel("Моделирование", modeBox), panel("Точность", accBox), panel("Где считалось", devBox)];

  function drawPanels() {
    const H = env.header();
    if (!H) return;
    const m = modelling || {};
    fill(modeBox,
      el("div", {}, el("b", {}, m.mode === "full3d" ? "Весь объём" : "Только срезы")),
      el("div", { class: m.approximation ? "st-bad" : "muted" }, m.mode === "full3d"
        ? "посчитан весь объём: в 3D — свет и поток энергии; любой срез считается точно для своей плоскости"
        : (m.note || "") + " Каждый поставленный срез считается для своей плоскости; объём не считается."));
    const a = H.accuracy || {};
    fill(accBox, el("span", {}, "окно расчёта"), el("span", { class: "mono" }, a.pad ? `×${a.pad}${a.band_limit ? ", с ограничением полосы" : ""}` : "—"),
      el("span", {}, "ошибка на z_max"), el("span", { class: "mono" }, a.window !== undefined ? `≈ ${num(a.window, 2)} пика амплитуды (нужно ≤ ${num(a.tol, 2)})` : "—"),
      el("span", {}, "у отверстия"), el("span", {}, a.z_near ? `z < ${num(a.z_near, 2)} мкм — поле, ограниченное сеткой (штриховка)` : "—"),
      el("span", {}, "срезы"), el("span", {}, "каждый сверяется с точным полем в своих точках (строка под окном)"));
    const u = (((H.backend || {}).used || {})["optics.angular_spectrum"] || {}).drawn;
    fill(devBox, el("span", {}, "угловой спектр"), el("span", { class: "mono" }, u ? `${u.device === "gpu" ? "GPU" : "CPU"}, ${u.precision}` : "—"),
      el("span", {}, "почему"), el("span", {}, u ? u.reason : ""),
      el("span", {}, "проверки"), el("span", {}, "всегда fp64"),
      el("span", {}, "настройки"), el("a", { href: "/settings", target: "_blank" }, "⚙ Устройства"));
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, "3D-сцена"),
      el("p", {}, "В центре — 3D-сцена этого запуска: заслонка с отверстием в плоскости z = 0, падающая плоская волна (задана), свет за отверстием (посчитанный объём; в режиме «весь объём»), поток энергии (стрелки; включается в «Слоях сцены») и мишень на глубине z_max с посчитанной интенсивностью. Любую часть можно выключить в панели «Слои сцены»."),
      el("p", {}, "Срезы — плоскости под любым углом, до трёх. «＋ Срез» ставит следующую плоскость в середину области, перпендикулярно уже стоящим (и повёрнутым тоже). Щелчок по плоскости выбирает её: стрелка двигает её вдоль нормали, кольца наклоняют (W / E переключают); то же — числами в панели «Срез: положение и наклон». После того как плоскость отпущена, движок считает поле на ней точно и сверяет с точным полем в её точках; пока плоскость тащат, окно показывает предпросмотр. Срезы сохраняются при новом мире этого запуска; «по умолчанию» возвращает один срез y = 0."),
      el("p", {}, "Окно каждого среза — справа от 3D, в цвете своей плоскости; наведение на окно подсвечивает плоскость. В окне: интенсивность, амплитуда, логарифм или фаза; оси в мкм; под курсором — координаты и значение; CSV — данные среза. Штриховка — зона у отверстия, где поле ограничено сеткой."),
      el("p", {}, "Срезы стоят, где их поставили. Автосмещение (по желанию, для каждого среза) ведёт плоскость по нормали, пока идёт время мира."),
      el("p", {}, "Камера: левая кнопка — вращать, правая — сдвигать, колесо — приближать; кнопки видов: изо, сбоку, сверху, с источника, с мишени; 📷 — снимок.")),
    reset() { env.reset(); modelling = null; },
    // key frames (player.js): the environment's own key frame and the modelling in force (a view variable: the header
    // the player keeps is never written, review CK-14)
    snapshot() { return { env: env.snapshot(), modelling }; },
    restore(k) { env.restore(k.env); modelling = k.modelling; drawPanels(); },
    onHeader(meta) { env.onHeader(meta); modelling = meta.modelling || null; drawPanels(); },
    onMessage(meta, blobs) {
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "modelling") { modelling = meta.modelling; drawPanels(); }
    },
    render() { env.scene.requestRender(); },
  };
}
