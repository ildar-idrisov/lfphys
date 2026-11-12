// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Settings page (plan P11): the devices the engine sees, its kernels, the device and precision of each kernel.
// A change is saved at once (no "apply" button) and holds for runs started after it.
import { getJSON, postJSON } from "./api.js";
import { el, fill, initTheme, num, toast, toggleTheme } from "./ui.js";

initTheme();
document.getElementById("theme").onclick = toggleTheme;

const DEV = { auto: "Авто (где быстрее)", cpu: "CPU", gpu: "GPU" };
let state = { devices: null, kernels: [], settings: {} };

const $ = (id) => document.getElementById(id);

function bytes(b) { return b == null ? "—" : num(b / 2 ** 30, 3) + " ГБ"; }
function side(n) { const s = Math.round(Math.sqrt(n)); return s * s === n ? `${s}×${s}` : String(n); }

function renderDevices() {
  const d = state.devices;
  const cpu = el("div", { class: "card" }, el("h3", {}, "CPU"),
    el("div", { class: "kv" }, el("span", {}, "процессор"), el("span", { class: "mono" }, d.cpu.name || "—"),
      el("span", {}, "потоков"), el("span", { class: "mono" }, String(d.cpu.threads)),
      el("span", {}, "NumPy"), el("span", { class: "mono" }, d.cpu.numpy)),
    el("div", { class: "muted", style: { marginTop: "6px" } }, "Есть всегда: на нём считается всё, что не выигрывает на GPU, и все строгие эталоны."));
  const g = d.gpu;
  const gpu = g.available
    ? el("div", { class: "card" }, el("h3", {}, "GPU 0 ", el("span", { class: "badge std" }, "доступен")),
        el("div", { class: "kv" }, el("span", {}, "карта"), el("span", { class: "mono" }, g.name),
          el("span", {}, "память"), el("span", { class: "mono" }, `${bytes(g.memory_free)} свободно из ${bytes(g.memory_total)}`),
          el("span", {}, "CuPy / CUDA"), el("span", { class: "mono" }, `${g.cupy} / ${g.cuda_runtime} (драйвер ${g.driver})`),
          el("span", {}, "шина PCI"), el("span", { class: "mono" }, g.pci_bus_id || "—")),
        el("div", { class: "muted", style: { marginTop: "6px" } }, "Только GPU 0: вторая карта этой машины считает неверно."))
    : el("div", { class: "card" }, el("h3", {}, "GPU ", el("span", { class: "badge" }, "недоступен")),
        el("div", { class: "muted" }, "Всё считается на CPU. Причина: " + (g.reason || "—")));
  const errs = d.kernel_import_errors || {};
  const broken = Object.keys(errs).length
    ? el("div", { class: "card" }, el("h3", {}, "Ядра, которые не загрузились"),
        el("div", { class: "kv" }, Object.entries(errs).flatMap(([k, e]) => [el("span", { class: "mono" }, k), el("span", { class: "warn" }, e)])),
        el("div", { class: "muted", style: { marginTop: "6px" } }, "Эти ядра пропущены; остальные работают. Ошибка — в коде движка: сообщите о ней."))
    : null;
  fill($("devices"), cpu, gpu, broken);
}

function kernelSetting(name) {
  const k = (state.settings.kernels || {})[name] || {};
  return { device: k.device || "auto", precision: k.precision || "fp64" };
}

function renderKernels() {
  const gpuOk = state.devices && state.devices.gpu.available;
  const rows = state.kernels.map((k) => {
    const s = kernelSetting(k.name);
    const dev = el("select", { title: "Где считать это ядро в новых запусках" },
      Object.entries(DEV).map(([v, t]) => el("option", { value: v, disabled: v === "gpu" && (!k.gpu || !gpuOk) ? true : null }, t)));
    dev.value = k.gpu ? s.device : "cpu";
    dev.disabled = !k.gpu;
    const precs = Object.entries(k.precisions).filter(([, p]) => p.allowed);
    const prec = el("select", { title: "Точность результатов, которые рисуются; проверки и эталоны всегда fp64" },
      precs.map(([v]) => el("option", { value: v }, v)));
    prec.value = s.precision;
    prec.disabled = precs.length < 2;
    const save = () => saveKernel(k.name, { device: dev.value, precision: prec.value });
    dev.onchange = save;
    prec.onchange = save;
    const crossover = ((state.settings.crossover || {})[k.name]) ?? k.crossover;
    const p32 = k.precisions.fp32;
    return el("tr", {},
      el("td", {}, el("b", {}, k.title), el("div", { class: "muted" }, k.what), el("div", { class: "mono muted" }, k.name)),
      el("td", {}, k.gpu ? "CPU и GPU" : el("span", {}, "только CPU", el("div", { class: "muted" }, k.cpu_reason))),
      el("td", {}, dev),
      el("td", {}, prec, p32 && p32.allowed ? el("div", { class: "muted" }, `fp32: ошибка ≤ ${num(p32.bound, 2)}, ${p32.use}`) :
        el("div", { class: "muted" }, "только fp64")),
      el("td", {}, k.gpu ? (crossover == null ? "GPU не выигрывает" : `GPU с ${side(crossover)} точек`) : "—",
        k.gpu ? el("div", { class: "muted" }, k.crossover_note) : null));
  });
  fill($("kernels"), el("table", { class: "runs" },
    el("tr", {}, ["Ядро", "Реализации", "Устройство", "Точность", "Порог «Авто»"].map((h) => el("th", {}, h))), rows));
}

// one save at a time, each carrying every change made so far (review B1-11: an older answer could overwrite a newer
// choice); the server also serialises writes of the settings file
let want = null, chain = Promise.resolve();
function saveKernel(name, value) {
  want = { ...(want || state.settings.kernels || {}), [name]: value };
  chain = chain.then(async () => {
    if (!want) return;
    const kernels = want;
    try {
      const r = await postJSON("/api/settings", { kernels }, "PUT");
      state.settings = r.settings;
      if (want === kernels) want = null;
      for (const n of r.notes || []) toast(n, "notice");
      $("saved").textContent = "сохранено — действует для новых запусков";
      setTimeout(() => { $("saved").textContent = ""; }, 4000);
    } catch (e) { want = null; toast("Не сохранено: " + e.message); }
    renderKernels();
  });
}

function renderCalibration() {
  const cal = state.settings.calibration;
  if (!cal) { fill($("calib")); return; }
  const blocks = Object.entries(cal).map(([name, c]) => el("div", { class: "card", style: { marginTop: "8px" } },
    el("h3", {}, (state.kernels.find((k) => k.name === name) || { title: name }).title,
      el("span", { class: "muted", style: { fontWeight: 400 } }, ` — измерено ${c.measured}${c.gpu ? " на " + c.gpu : ""}`)),
    el("table", { class: "runs" }, el("tr", {}, ["точек", "CPU, мс", "GPU, мс", "ускорение"].map((h) => el("th", {}, h))),
      c.rows.map((r) => el("tr", {}, el("td", { class: "mono" }, side(r.size)), el("td", { class: "mono" }, num(r.cpu_s * 1e3, 3)),
        el("td", { class: "mono" }, r.gpu_s == null ? "—" : num(r.gpu_s * 1e3, 3)),
        el("td", { class: "mono" }, r.gpu_s == null ? "—" : "×" + num(r.cpu_s / r.gpu_s, 2)))))));
  fill($("calib"), blocks);
}

$("calibrate").onclick = async () => {
  const b = $("calibrate");
  b.disabled = true; b.textContent = "Измеряю… (несколько секунд)";
  await chain;  // pending choices first
  try { state.settings = await postJSON("/api/settings/calibrate", {}); toast("Пороги «Авто» обновлены по замеру", "notice", 4000); }
  catch (e) { toast("Замер не удался: " + e.message); }
  b.disabled = false; b.textContent = "Измерить заново";
  renderKernels(); renderCalibration();
};

$("reset").onclick = async () => {
  await chain;
  want = null;
  try {
    const r = await postJSON("/api/settings", { kernels: {}, crossover: {} }, "PUT");
    state.settings = r.settings;
    toast("Все ядра: авто и fp64", "notice", 4000);
  } catch (e) { toast(e.message); }
  renderKernels(); renderCalibration();
};

function renderHowto() {
  $("intro").textContent = "Здесь выбирается, где считаются тяжёлые части движка: на процессоре или на видеокарте, и с какой точностью. " +
    "Изменения сохраняются сразу и действуют на новые запуски; в каждом запуске записано, что на чём считалось (панель «О запуске»).";
  fill($("howto"),
    el("p", {}, "«Авто» берёт GPU только там, где он есть, где у ядра есть GPU-реализация и где задача не меньше измеренного порога; иначе CPU. " +
      "На GPU уходит только тяжёлая часть (БПФ, поля), результат возвращается в общую память."),
    el("p", {}, "Точность: fp64 — всегда. fp32 предлагается только для ядер, у которых ошибка fp32 против fp64 проверена тестом и мала, " +
      "и только для того, что рисуется: эталоны и проверки в запуске всегда считаются в fp64. " +
      "fp16 не предлагается: БПФ комплексных полей в половинной точности теряют около 10⁻³ — это заметно меняет результат."),
    el("p", {}, "Ядра «только CPU» не выигрывают от GPU (последовательные уравнения, малые матрицы) или существуют только для CPU (строгая арифметика Arb)."));
}

async function load() {
  renderHowto();
  try {
    const r = await getJSON("/api/devices");
    state.devices = r.devices; state.kernels = r.kernels; state.settings = r.settings || {};
  } catch (e) { toast(e.message); return; }
  renderDevices(); renderKernels(); renderCalibration();
}
load();
