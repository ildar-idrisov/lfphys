// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// Settings page (plan P11): the devices the engine sees, its kernels, the device and precision of each kernel.
// A change is saved at once (no "apply" button) and holds for runs started after it.
import { getJSON, postJSON } from "./api.js";
import { t } from "./i18n.js";
import { el, fill, initTheme, num, toast, toggleTheme } from "./ui.js";

initTheme();
document.getElementById("theme").onclick = toggleTheme;

const DEV = { auto: t("Auto (where faster)"), cpu: "CPU", gpu: "GPU" };
let state = { devices: null, kernels: [], settings: {} };

const $ = (id) => document.getElementById(id);

function bytes(b) { return b == null ? "—" : t("{n:.3g} GB", { n: b / 2 ** 30 }); }
function side(n) { const s = Math.round(Math.sqrt(n)); return s * s === n ? `${s}×${s}` : String(n); }

function renderDevices() {
  const d = state.devices;
  const cpu = el("div", { class: "card" }, el("h3", {}, "CPU"),
    el("div", { class: "kv" }, el("span", {}, t("processor")), el("span", { class: "mono" }, d.cpu.name || "—"),
      el("span", {}, t("threads")), el("span", { class: "mono" }, String(d.cpu.threads)),
      el("span", {}, "NumPy"), el("span", { class: "mono" }, d.cpu.numpy)),
    el("div", { class: "muted", style: { marginTop: "6px" } }, t("Always there: it computes everything that does not gain on the GPU, and all the strict references.")));
  const g = d.gpu;
  const gpu = g.available
    ? el("div", { class: "card" }, el("h3", {}, "GPU 0 ", el("span", { class: "badge std" }, t("available"))),
        el("div", { class: "kv" }, el("span", {}, t("card")), el("span", { class: "mono" }, g.name),
          el("span", {}, t("memory")), el("span", { class: "mono" }, t("{free} free of {total}", { free: bytes(g.memory_free), total: bytes(g.memory_total) })),
          el("span", {}, "CuPy / CUDA"), el("span", { class: "mono" }, t("{cupy} / {cuda} (driver {driver})", { cupy: String(g.cupy), cuda: String(g.cuda_runtime), driver: String(g.driver) })),
          el("span", {}, t("PCI bus")), el("span", { class: "mono" }, g.pci_bus_id || "—")),
        el("div", { class: "muted", style: { marginTop: "6px" } }, t("GPU 0 only: the second card of this machine computes wrongly.")))
    : el("div", { class: "card" }, el("h3", {}, "GPU ", el("span", { class: "badge" }, t("not available"))),
        el("div", { class: "muted" }, t("Everything is computed on the CPU. The reason: {why}", { why: g.reason || "—" })));
  const errs = d.kernel_import_errors || {};
  const broken = Object.keys(errs).length
    ? el("div", { class: "card" }, el("h3", {}, t("Kernels that did not load")),
        el("div", { class: "kv" }, Object.entries(errs).flatMap(([k, e]) => [el("span", { class: "mono" }, k), el("span", { class: "warn" }, t(e))])),
        el("div", { class: "muted", style: { marginTop: "6px" } }, t("These kernels are skipped; the others work. The error is in the engine's code: please report it.")))
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
    const dev = el("select", { title: t("Where this kernel computes in new runs") },
      Object.entries(DEV).map(([v, s]) => el("option", { value: v, disabled: v === "gpu" && (!k.gpu || !gpuOk) ? true : null }, s)));
    dev.value = k.gpu ? s.device : "cpu";
    dev.disabled = !k.gpu;
    const precs = Object.entries(k.precisions).filter(([, p]) => p.allowed);
    const prec = el("select", { title: t("The precision of the results that are drawn; checks and references are always fp64") },
      precs.map(([v]) => el("option", { value: v }, v)));
    prec.value = s.precision;
    prec.disabled = precs.length < 2;
    const save = () => saveKernel(k.name, { device: dev.value, precision: prec.value });
    dev.onchange = save;
    prec.onchange = save;
    const crossover = ((state.settings.crossover || {})[k.name]) ?? k.crossover;
    const p32 = k.precisions.fp32;
    return el("tr", {},
      el("td", {}, el("b", {}, t(k.title)), el("div", { class: "muted" }, t(k.what)), el("div", { class: "mono muted" }, k.name)),
      el("td", {}, k.gpu ? t("CPU and GPU") : el("span", {}, t("CPU only"), el("div", { class: "muted" }, t(k.cpu_reason)))),
      el("td", {}, dev),
      el("td", {}, prec, p32 && p32.allowed ? el("div", { class: "muted" }, t("fp32: error ≤ {bound:.2g}, {use}", { bound: p32.bound, use: p32.use })) :
        el("div", { class: "muted" }, t("fp64 only"))),
      el("td", {}, k.gpu ? (crossover == null ? t("the GPU does not gain") : t("GPU from {size} points", { size: side(crossover) })) : "—",
        k.gpu ? el("div", { class: "muted" }, t(k.crossover_note)) : null));
  });
  fill($("kernels"), el("table", { class: "runs" },
    el("tr", {}, [t("Kernel"), t("Implementations"), t("Device"), t("Precision"), t("“Auto” threshold")].map((h) => el("th", {}, h))), rows));
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
      $("saved").textContent = t("saved — holds for new runs");
      setTimeout(() => { $("saved").textContent = ""; }, 4000);
    } catch (e) { want = null; toast(t("Not saved: {why}", { why: e.message })); }
    renderKernels();
  });
}

function renderCalibration() {
  const cal = state.settings.calibration;
  if (!cal) { fill($("calib")); return; }
  const blocks = Object.entries(cal).map(([name, c]) => el("div", { class: "card", style: { marginTop: "8px" } },
    el("h3", {}, t((state.kernels.find((k) => k.name === name) || { title: name }).title),
      el("span", { class: "muted", style: { fontWeight: 400 } }, " — " + (c.gpu ? t("measured {when} on {gpu}", { when: String(c.measured), gpu: String(c.gpu) }) : t("measured {when}", { when: String(c.measured) })))),
    el("table", { class: "runs" }, el("tr", {}, [t("points"), t("CPU, ms"), t("GPU, ms"), t("speed-up")].map((h) => el("th", {}, h))),
      c.rows.map((r) => el("tr", {}, el("td", { class: "mono" }, side(r.size)), el("td", { class: "mono" }, num(r.cpu_s * 1e3, 3)),
        el("td", { class: "mono" }, r.gpu_s == null ? "—" : num(r.gpu_s * 1e3, 3)),
        el("td", { class: "mono" }, r.gpu_s == null ? "—" : "×" + num(r.cpu_s / r.gpu_s, 2)))))));
  fill($("calib"), blocks);
}

$("calibrate").onclick = async () => {
  const b = $("calibrate");
  b.disabled = true; b.textContent = t("Measuring… (a few seconds)");
  await chain;  // pending choices first
  try { state.settings = await postJSON("/api/settings/calibrate", {}); toast(t("The “Auto” thresholds were updated by the measurement"), "notice", 4000); }
  catch (e) { toast(t("The measurement failed: {why}", { why: e.message })); }
  b.disabled = false; b.textContent = t("Measure again");
  renderKernels(); renderCalibration();
};

$("reset").onclick = async () => {
  await chain;
  want = null;
  try {
    const r = await postJSON("/api/settings", { kernels: {}, crossover: {} }, "PUT");
    state.settings = r.settings;
    toast(t("All kernels: auto and fp64"), "notice", 4000);
  } catch (e) { toast(e.message); }
  renderKernels(); renderCalibration();
};

function renderHowto() {
  $("intro").textContent = t("Here you choose where the heavy parts of the engine compute: on the processor or on the graphics card, and with what precision. Changes are saved at once and hold for new runs; every run records what computed on what (the “About the run” panel).");
  fill($("howto"),
    el("p", {}, t("“Auto” takes the GPU only where there is one, where the kernel has a GPU implementation and where the task is not smaller than the measured threshold; otherwise the CPU. Only the heavy part (FFTs, fields) goes to the GPU; the result comes back to the common memory.")),
    el("p", {}, t("Precision: fp64 always. fp32 is offered only for kernels whose fp32 error against fp64 is verified by a test and small, and only for what is drawn: the references and checks of a run are always computed in fp64. fp16 is not offered: FFTs of complex fields in half precision lose about 10⁻³, which changes the result visibly.")),
    el("p", {}, t("“CPU only” kernels do not gain from the GPU (sequential equations, small matrices) or exist only for the CPU (Arb's rigorous arithmetic).")));
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
