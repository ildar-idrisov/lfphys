// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// v09 view: the manoeuvre in the shared 3-D environment (/static/js/env3d.js). Velocity space (the ball of
// velocities, light at its boundary) or ordinary space; the path revealed as the run's time reaches it, the gyroscope
// triads along it, the craft with its gyroscopes, spin and thrust, the rotation axis when the loop closes; in velocity
// space the field of three-burn loops as a volume, its rotation axes as arrows, and up to three slice planes with
// their windows. Drawing only: every number comes from the run.
import { el, fill, num, panel } from "/static/js/ui.js";
import { createEnv3D } from "/static/js/env3d.js";

const deg = (r) => r * 180 / Math.PI;

export function createView(ctx) {
  const env = createEnv3D(ctx, { scale: "lin" });
  const loopBox = el("div", { class: "kv" }), nowBox = el("div", { class: "kv" }), resBox = el("div", {});
  const legend = el("div", { class: "help" },
    el("div", {}, el("span", { style: { color: "#ff5a5a" } }, "■"), " ", el("span", { style: { color: "#5adc78" } }, "■"), " ",
      el("span", { style: { color: "#5aa0ff" } }, "■"), " — оси гироскопов 1, 2, 3 (относительно системы, достигнутой одним бустом из покоя)"),
    el("div", {}, el("span", { style: { color: "#ffd23f" } }, "➜"), " спин (ось гироскопа 1)  ",
      el("span", { style: { color: "#ff8a1f" } }, "➜"), " тяга (направление ускорения)"));
  // panel(title, body): one body element each (the result and the legend were once passed as a third argument and lost)
  const rightPanels = [panel("Манёвр и голономия", el("div", {}, loopBox, resBox)), panel("Сейчас", el("div", {}, nowBox, legend)),
                       panel("Слои сцены", env.layersPanel), panel("Срез: положение и наклон", env.planePanel)];
  let H = null, R = null;

  function drawLoop() {
    if (!H) return;
    const L = H.loop || {};
    fill(loopBox,
      el("span", {}, "петля"), el("span", {}, L.planar ? "плоская (есть замкнутая формула)" : "неплоская"),
      el("span", {}, "участков тяги"), el("span", { class: "mono" }, String(L.pieces)),
      el("span", {}, "топливо по программе L"), el("span", { class: "mono" }, `${num(L.fuel, 5)} (сумма быстрот, ∫|a|dτ/c)`),
      el("span", {}, "эталон"), el("span", {}, L.ref_how || "—"));
  }
  function drawResult() {
    if (!R) { fill(resBox, el("div", { class: "muted" }, "Итог появится, когда петля замкнётся (корабль вернётся к покою).")); return; }
    const sign = R.spinor_sign < 0 ? "−1: спинор сменил знак" : "+1";
    fill(resBox, el("div", { class: "kv" },
      el("span", {}, "поворот гироскопов, SO(3)"), el("span", { class: "mono" }, `${num(deg(R.angle), 6)}° вокруг (${R.axis.map((c) => num(c, 3)).join(", ")})`),
      el("span", {}, "спинор, SU(2)"), el("span", { class: "mono" }, `${num(deg(R.su2_angle), 6)}° · знак ${sign}`),
      R.planar ? el("span", {}, "накопленный угол (по ходу расчёта)") : null,
      R.planar ? el("span", { class: "mono" }, `${num(R.accumulated, 8)} рад (эталон — площадь; в проверках)`) : null,
      el("span", {}, "время манёвра"), el("span", { class: "mono" }, `${num(R.T_end, 5)} лет по часам покоя, ${num(R.tau_end, 5)} лет по часам корабля`),
      el("span", {}, "наибольшая γ"), el("span", { class: "mono" }, num(R.gamma_max, 5)),
      el("span", {}, "граница плоских петель"), el("span", { class: "mono" }, `${num(R.bound, 6)} рад при L = ${num(R.per_fuel_L, 5)}`),
      el("span", {}, "угол / граница"), el("span", { class: "mono" }, `${num(R.per_bound, 6)} (${R.per_fuel_how})`)),
      el("div", { class: "help" }, R.planar
        ? "Плоская петля: гироскопы поворачиваются на площадь петли в пространстве скоростей, против обхода; круг — единственный случай равенства в изопериметрической границе."
        : "Неплоская петля: граница доказана только для плоских петель; здесь она — линия сравнения."));
  }
  function drawNow(f) {
    if (!f) return;
    fill(nowBox,
      el("span", {}, "время t / τ"), el("span", { class: "mono" }, `${num(f.t_yr, 5)} / ${num(f.tau, 5)} лет`),
      el("span", {}, "топливо"), el("span", { class: "mono" }, num(f.s, 5)),
      el("span", {}, "скорость β"), el("span", { class: "mono" }, `(${f.beta.map((c) => num(c, 4)).join(", ")}), γ = ${num(f.gamma, 5)}`),
      el("span", {}, "наибольшая γ до сих пор"), el("span", { class: "mono" }, num(f.gamma_so_far, 5)),
      el("span", {}, "гироскопы повёрнуты на"), el("span", { class: "mono" }, `${num(deg(f.rot_angle), 5)}° вокруг (${f.rot_axis.map((c) => num(c, 3)).join(", ")})`));
  }

  return {
    center: env.center, rightPanels,
    help: () => el("div", {}, el("h4", {}, "Прецессия Томаса–Вигнера в 3D"),
      el("p", {}, "Корабль стартует из покоя и выполняет манёвр: импульсы (тяга постоянного направления) и повороты тяги — оба заданы в его собственной системе. Гироскопы на борту не вращаются (перенос Ферми–Уокера). Когда корабль возвращается к покою, гироскопы оказываются повёрнутыми: это голономия петли, которую его скорость пробежала в пространстве скоростей (прецессия Томаса; для двух бустов — вращение Вигнера)."),
      el("p", {}, "Пространство скоростей — шар β = v/c; его граница — свет. Импульс постоянного направления — прямой отрезок (так устроена эта картина: геодезические — хорды). Для плоской петли поворот равен её площади (Гаусс–Бонне, кривизна −1), против обхода; для равномерного движения по окружности это 2π(γ − 1) за оборот (Томас). SU(2) хранит больше, чем SO(3): поворот на 2π возвращает гироскопы, но меняет знак спинора («SU(2): спинор сменил знак»)."),
      el("p", {}, "Топливо L — сумма быстрот (∫|a|dτ/c). Среди плоских петель с данным L наибольшую площадь охватывает круг: √(4π² + L²) − 2π (изопериметрическое неравенство плоскости Лобачевского). Для неплоских петель эта величина — линия сравнения, не доказанная граница."),
      el("p", {}, "Поле в шаре: для каждой скорости w — поворот гироскопов после петли покой → u → w → покой (u задан в параметрах поля) или этот поворот, делённый на границу при том же топливе. Срезы — плоскости под любым углом (до трёх); каждый считается для своей плоскости и сверяется с площадью треугольника скоростей в своих точках."),
      el("p", {}, "Время — лабораторное (годы). Путь, гироскопы и итог появляются по мере хода времени («▶»). В обычном пространстве — траектория корабля в световых годах; срезов там нет.")),
    reset() { env.reset(); H = null; R = null; },
    // key frames (player.js): the environment's own key frame (the path and the triads are cut back) and the result
    snapshot() { return { env: env.snapshot(), R }; },
    restore(k) { env.restore(k.env); R = k.R; drawResult(); },
    onHeader(meta) { H = meta; R = null; env.onHeader(meta); drawLoop(); drawResult(); },
    onMessage(meta, blobs) {
      if (env.onMessage(meta, blobs)) return;
      if (meta.type === "holonomy") { R = meta; drawResult(); }
    },
    // the player hands every frame (the state at the time shown) to render
    render(meta) {
      if (H && meta && meta.pos) {
        env.scene.setBody("craft", { pos: meta.pos, O: meta.O, spin: meta.spin, thrust: meta.done ? null : meta.thrust });
        drawNow(meta);
      }
      env.scene.requestRender();
    },
  };
}
