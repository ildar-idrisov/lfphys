// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v14 view: the wave functions of a heavy quark pair in the Cornell model (the shared wave-function view
// /static/js/orbitview.js over the 3-D environment). Drawing only: every value comes from the run.
import { el, num } from "/static/js/ui.js";
import { createOrbitView } from "/static/js/orbitview.js";
import { withPreparation } from "/viz/v13_hydrogen_3d/view.js";  // the state is live: prepared at the current moment

export function createView(ctx) {
  return withPreparation(createOrbitView(ctx, {
    energyName: "M − M(1S), модель",
    levelColumns: ["S", "P", "D"],
    describeAtom: (H) => {
      const s = H.system || {};
      return el("div", {},
        el("div", { class: "warn" }, "Модель (подогнанные параметры): верны расщепления уровней, не абсолютные массы."),
        el("div", { class: "kv" }, el("span", {}, "пара"), el("span", {}, s.label || ""),
          el("span", {}, "потенциал"), el("span", { class: "mono" }, `−κ/r + r/a², κ = ${num(s.kappa, 3)}, a = ${num(s.a, 3)} ГэВ⁻¹`),
          el("span", {}, "масса кварка"), el("span", { class: "mono" }, `${num(s.m_q, 4)} ГэВ (приведённая ${num(s.mu, 4)})`)));
    },
    help: [
      "Кварконий в 3D",
      "Пара тяжёлых кварков (cc̄ — чармоний, bb̄ — боттомоний) в модели Корнелла: кулоновское притяжение обмена глюоном на малых расстояниях и линейно растущая «струна» конфайнмента. Модель нерелятивистская, без спиновых сил, её параметры подогнаны под спектр; она предсказывает расщепления уровней (1P − 1S, 2S − 1S) с точностью 2–10 %, но не абсолютные массы. Это модель вне ядра движка, и мир так помечен.",
      "Облако — плотность вероятности |ψ|² для вектора r между кварком и антикварком (центр масс в начале координат). Радиальные функции — численное решение радиального уравнения (синус-базис, экстраполяция Ричардсона); его точность проверяется вторым решением на более мелкой сетке («сходимость»: разница меньше полшага 8-битной картинки).",
      "Слева уровни модели: расщепления от 1S (сплошные) и опыт PDG — спин-усреднённые массы (пунктир). Справа — состояние, радиальное распределение r²|R|², срезы с |ψ|² и фазой (сверены в точках со вторым решением и гармониками scipy).",
      "Суперпозиция 1S + 1P колеблется с частотой перехода модели (период ~10⁻²³ с): фазы открываются, когда до них доходит время мира.",
      "Состояние меняется на ходу (слева, «Установка»): новое состояние приготовлено в текущий момент (идеальная подготовка, прежнее отброшено) — мир, время и срезы остаются, период отсчитывается от момента подготовки. Другая пара кварков — новый мир.",
    ],
  }));
}
