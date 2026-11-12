// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v13 view: the hydrogen atom's orbital cloud, current and slices (the shared wave-function view
// /static/js/orbitview.js over the 3-D environment). Drawing only: every value comes from the run.
import { el, num } from "/static/js/ui.js";
import { createOrbitView } from "/static/js/orbitview.js";

// The state is live (review UX-ui U12): a change prepares the new state at the current moment, and the run sends
// `prepared` with the parts of the header that describe it (states, levels, period, the scene's box). The shared view
// is started again from the world's header with those parts (its cloud, current and slices of the former state are
// dropped; the messages that follow bring the new ones), and the phase of the period is counted from the preparation
// (frames carry `t_prep`). Also used by v14.
export function withPreparation(view) {
  let H0 = null;
  return {
    ...view,
    reset() { H0 = null; view.reset(); },
    onHeader(meta, blobs) { H0 = meta; view.onHeader(meta, blobs); },
    onMessage(meta, blobs) {
      if (meta.type === "prepared") {  // the panel «Состояние» names the state; the title names only the atom
        if (H0) view.onHeader({ ...H0, ...meta.header });
        return;
      }
      view.onMessage(meta, blobs);
    },
    render(meta, t) { view.render(meta, meta && Number.isFinite(t) ? t - (meta.t_prep || 0) : t); },
  };
}

export function createView(ctx) {
  return withPreparation(createOrbitView(ctx, {
    energyName: "энергия E",
    describeAtom: (H) => {
      const a = H.atom || {};
      return el("div", { class: "kv" }, el("span", {}, "атом"), el("span", {}, a.label || ""),
        el("span", {}, "приведённая масса"), el("span", { class: "mono" }, `μ = ${num(a.mu_over_me, 9)} mₑ`),
        el("span", {}, "боровский радиус"), el("span", { class: "mono" }, `a_μ = ${num(a.a_A, 7)} Å`));
    },
    help: [
      "Атом водорода в 3D",
      "Облако — плотность вероятности |ψ|² найти электрон в точке (координата электрона относительно ядра; движение центра масс отделено, отсюда приведённая масса μ). Волновая функция — точное решение уравнения Шрёдингера: R_nl(r) (полиномы Лагерра) × Y_lm(θ, φ); её считает движок в этом запуске, на сетке до 96³ точек.",
      "Вещественные орбитали (p_x, d_xy, d_z², …) — стоячие волны: тока вероятности нет. Комплексные состояния с m ≠ 0 — облако-бублик, ток течёт кольцами вокруг оси z (стрелки). Суперпозиция двух уровней (например 1s + 2p_z) колеблется с частотой Бора ω = ΔE/ħ: фазы периода открываются, когда до них доходит время мира; дальше облако повторяется (проверено: через период T оно совпадает с исходным).",
      "Срезы — плоскости под любым углом (до трёх): |ψ|² и фаза ψ, посчитанные для самой плоскости; в каждом срезе ψ в нескольких точках сверена с независимым расчётом (ряд для полинома Лагерра и гармоники scipy). Режим «фаза» в окне среза показывает arg ψ: у комплексных состояний фаза обходит ось z m раз.",
      "Справа: состояние (энергия, ⟨r⟩ — квадратурой и по формуле), радиальное распределение r²|R|² (его максимумы — «оболочки», нули — радиальные узлы) и уровни энергии (выделены уровни этого мира). Проверки: нормировка, ⟨r⟩, энергия ⟨T⟩ + ⟨V⟩ по самой волновой функции против формулы Бора, число узлов, ток против замкнутой формулы или уравнения непрерывности, колебание ⟨z⟩(t) против матричного элемента.",
      "Облако в 3D хранит амплитуду в 8 битах (как и текстура): значения |ψ|² меньше 1,5·10⁻⁵ пика рисуются нулём; точные значения — в окнах срезов.",
      "Состояние меняется на ходу (слева, «Установка»): новое n, l, m, вид орбитали или суперпозиция приготовлены в текущий момент — мир, его время и срезы остаются, облако, ток, срезы и проверки посчитаны для нового состояния, а период суперпозиции отсчитывается от момента подготовки. Подготовка идеальная: прежнее состояние отброшено, как атом в него попал (фотон, измерение), здесь не моделируется. Проверки прежнего состояния, которых у нового нет, помечены «прежнее состояние». Другой атом — новый мир.",
    ],
  }));
}
