// Review LB1-p02-ux, Part B, tour b4: «Приборы» as the owner uses them — p02 (double slit): pick quantities, the plots
// (units of the time axis), the CSV, a sweep from the panel (what «Что менять» offers, Оценить, Запустить, ✕ отменить,
// a second sweep run to the end, the table and plot) — and the time axis after a live grid change; light and dark.
import { browser, newRun, openRun, shot, log, sleep, attachErrors, cmd, record, get, waitFor, toasts } from "./b_lib.mjs";

const W = Number(process.env.W || 1600), H = Number(process.env.H || 1000);
const tag = `${W}x${H}`;
const VIZ = process.env.VIZ || "p02_quantum", PRESET = process.env.PRESET || "double_slit";
const br = await browser();
const errs = [];
const id = await newRun(VIZ, PRESET);
log(`b4 ${VIZ} ${tag} run`, id);
const page = await br.newPage({ viewport: { width: W, height: H } });
attachErrors(page, errs);
await openRun(page, id);
await cmd(id, "play"); await sleep(8000); await cmd(id, "pause"); await sleep(2000);
// 1. pick quantities: energy and <x> of the first particle (or the first two unchecked of the second group)
const names = await page.evaluate(() => [...document.querySelectorAll(".in-panel .in-q")].map((q) => q.querySelector(".in-name")?.textContent));
log("b4 quantities", names.length, names.slice(0, 40));
const pick = names.filter((n) => /энергия|⟨x⟩|скорость|Поток|поглотил|Температура|Сила|давлен|Кинетич/i.test(n || "")).slice(0, 4);
for (const n of pick) await page.locator(".in-q", { hasText: n }).first().locator("input").check().catch((e) => log("  check failed", n, e.message.slice(0, 80)));
await sleep(1500);
await page.locator(".in-panel").scrollIntoViewIfNeeded();
await shot(page, `b4_${VIZ}_${tag}_01_plots`, ".in-panel");
const plots = await page.evaluate(() => [...document.querySelectorAll(".in-panel .in-plot")].map((p) => p.innerText.replace(/\n/g, " | ").slice(0, 200)));
log("b4 plots (title | value | axis ticks)", plots);
// 2. CSV
const csv = await page.evaluate(async () => { const a = document.querySelector(".in-panel .in-csv"); if (!a) return null; const r = await fetch(a.href); const t = await r.text(); return { href: a.href, head: t.split(/\r?\n/).slice(0, 3), rows: t.split(/\r?\n/).length }; });
log("b4 csv", csv);
// 3. the sweep form
await page.evaluate(() => { const b = document.querySelector(".in-sweep-box"); if (b) b.open = true; });
await page.waitForSelector(".in-sweep select", { timeout: 20000 }).catch(() => {});
const targets = await page.evaluate(() => [...(document.querySelector(".in-sweep select")?.options || [])].map((o) => `${o.value} = ${o.textContent}`));
log("b4 sweep targets", targets);
const measures = await page.evaluate(() => { const s = [...document.querySelectorAll(".in-sweep .ctl")].find((c) => /Что измерять/.test(c.textContent))?.querySelector("select"); return s ? [...s.options].map((o) => o.textContent).slice(0, 30) : null; });
log("b4 sweep measures", measures);
await shot(page, `b4_${VIZ}_${tag}_02_sweep_form`, ".in-sweep-box");
const want = process.env.TARGET || targets.find((t) => /^law:size|^law:n2|ширин|wavelength|λ|Длина волны/.test(t))?.split(" = ")[0] || targets[1]?.split(" = ")[0];
log("b4 sweep target chosen", want);
if (want) {
  await page.selectOption(".in-sweep select >> nth=0", want);
  await sleep(500);
  const form = page.locator(".in-sweep");
  const cur = await page.evaluate(() => document.querySelector(".in-sweep")?.innerText.slice(0, 600));
  log("b4 sweep form text:\n" + cur);
  await form.locator("input[placeholder^='например']").fill(process.env.VALUES || "1,5; 2; 2,5; 3");
  await form.locator(".ctl", { hasText: "Сколько считать" }).locator("input").fill(process.env.DUR || "0,02");
  const m = await page.evaluate(() => { const s = [...document.querySelectorAll(".in-sweep .ctl")].find((c) => /Что измерять/.test(c.textContent))?.querySelector("select"); return s ? [...s.options].map((o) => o.value) : []; });
  const mv = m.find((v) => /\.absorbed$|^absorbed$|\.P$/.test(v)) || m[0];
  await form.locator(".ctl", { hasText: "Что измерять" }).locator("select").selectOption(mv);
  let t0 = Date.now();
  await form.locator("button", { hasText: "Оценить" }).click();
  await page.waitForFunction(() => /≈|не измерила|нельзя|ошибка|отказ/i.test(document.querySelector(".in-est")?.textContent || ""), null, { timeout: 120000 }).catch(() => {});
  log(`b4 estimate after ${Date.now() - t0} ms:`, await page.textContent(".in-est").catch(() => null), "toasts", await toasts(page));
  t0 = Date.now();
  await form.locator("button", { hasText: "Запустить свип" }).click();
  await sleep(2500);
  const st1 = await page.evaluate(() => document.querySelector(".in-sh")?.textContent);
  log("b4 sweep 1 state after 2.5 s", st1);
  await shot(page, `b4_${VIZ}_${tag}_03_sweep_running`, ".in-sweep-box");
  const cancel = page.locator(".in-sh button.cancel");
  if (await cancel.count()) { await cancel.click(); await sleep(3000); }
  log("b4 sweep 1 after cancel", await page.evaluate(() => document.querySelector(".in-sh")?.textContent), await get(`/api/runs/${id}/sweeps`));
  // a second one to the end: «Запустить» is disabled after a run until «Оценить» again
  log("b4 after cancel: start disabled?", await form.locator("button", { hasText: "Запустить свип" }).isDisabled(), "estimate text", await page.textContent(".in-est"));
  await form.locator("button", { hasText: "Оценить" }).click();
  await sleep(1500);
  t0 = Date.now();
  await form.locator("button", { hasText: "Запустить свип" }).click();
  await page.waitForFunction(() => /готово|не посчитан/.test((document.querySelector(".in-sh") || {}).textContent || ""), null, { timeout: 600000 }).catch(() => {});
  log(`b4 sweep 2 after ${Date.now() - t0} ms:`, await page.evaluate(() => document.querySelector(".in-sh")?.textContent));
  const rows = await page.evaluate(() => [...document.querySelectorAll(".in-tab tr")].map((tr) => [...tr.children].map((td) => td.textContent).join(" | ")));
  log("b4 sweep table", rows);
  const sw = await get(`/api/runs/${id}/sweeps`);
  if (sw.length) log("b4 sweep api", JSON.stringify(await get(`/api/runs/${id}/sweeps/${sw.at(-1).n}`)).slice(0, 1500));
  await page.evaluate(() => document.querySelectorAll(".toast").forEach((t) => t.remove()));
  await shot(page, `b4_${VIZ}_${tag}_04_sweep_done`, ".in-sweep-box");
}
// 4. the live world went on? (the time of the world before/after the sweep)
log("b4 world frames", await page.evaluate(() => window.__lfPlayer.frames()));
await page.keyboard.press("t"); await sleep(800);
await shot(page, `b4_${VIZ}_${tag}_05_dark_panel`, ".in-panel");
await shot(page, `b4_${VIZ}_${tag}_06_dark_page`);
log("b4 page errors", errs);
await page.close();
await br.close();
