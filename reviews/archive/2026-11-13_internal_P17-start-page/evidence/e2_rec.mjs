// review P, e2: the player on a recording (server): view buttons, title, help, old links, old runs, screenshots
import { chromium } from "playwright";
const base = process.argv[2] || "http://127.0.0.1:8682";
const OUT = "/shots";
const L = (k, v) => console.log(JSON.stringify({ k, v }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });

async function openRec(ctx, q, lang = "en") {
  const page = await ctx.newPage();
  const errs = [], sockets = [], reqs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
  page.on("websocket", (ws) => sockets.push(ws.url()));
  page.on("request", (r) => { if (r.method() !== "GET") reqs.push(r.method() + " " + r.url()); });
  await page.goto(`${base}/run?${q}&lang=${lang}`);
  try { await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 120000 }); }
  catch (e) { L("load failed " + q, { errs, body: (await page.evaluate(() => document.body.innerText)).slice(0, 300) }); }
  await sleep(1200);
  return { page, errs, sockets, reqs };
}
const ui = (page) => page.evaluate(() => ({
  title: document.title, badge: document.getElementById("recbadge")?.textContent, status: document.getElementById("status")?.textContent,
  speed: document.getElementById("speedv")?.textContent, back: document.querySelector('.topbar a[data-page=""]')?.getAttribute("href"),
  backText: document.querySelector('.topbar a[data-page=""]')?.textContent, t: window.__lfPlayer?.t(), frames: window.__lfPlayer?.frames(),
  toasts: [...document.querySelectorAll(".toast")].map((e) => e.textContent.slice(0, 120)),
}));

const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
// the views' own speed buttons on a recording
for (const [rec, labels] of [["u32_double_slit/young", ["▷ flight", "▷▷ build-up"]], ["u37_bell_test/chsh", ["▷ flight", "▷▷ collect statistics", "⟲ reset the statistics"]],
  ["u35_optics_bench/tir", null], ["u34_orbits/mercury", ["push +5 %", "↻ launch"]]]) {
  const { page, errs, sockets, reqs } = await openRec(ctx, `rec=${rec}`);
  const before = await ui(page);
  L(rec + " before", before);
  const btns = await page.$$eval("#center button, #right button, #left button", (a) => a.map((b) => ({ text: b.textContent.trim(), disabled: b.disabled, title: b.title })).filter((b) => b.text));
  L(rec + " buttons", btns);
  for (const b of btns.filter((x) => !x.disabled && (labels ? labels.includes(x.text) : /▷|flight|statistic/i.test(x.text)))) {
    await page.getByRole("button", { name: b.text, exact: true }).first().click();
    await sleep(700);
    const a = await ui(page);
    L(rec + " after click " + b.text, { speed_before: before.speed, speed_after: a.speed, toasts: a.toasts });
  }
  L(rec + " sockets/requests/errs", { sockets, reqs, errs });
  await page.screenshot({ path: `${OUT}/e2_${rec.replace("/", "_")}_en.png` });
  // help on a recording
  await page.keyboard.press("?");
  await sleep(400);
  L(rec + " help", (await page.evaluate(() => document.querySelector(".modal, dialog, .overlay-modal")?.innerText || document.body.innerText.slice(-1500))).slice(0, 1500));
  await page.screenshot({ path: `${OUT}/e2_${rec.replace("/", "_")}_help_en.png` });
  await page.close();
}
// RU title, phone screenshot
{
  const c2 = await br.newContext({ viewport: { width: 390, height: 844 } });
  const { page, errs } = await openRec(c2, "rec=u32_double_slit/young", "ru");
  L("ru 390 u32", { ...(await ui(page)), errs, sw: await page.evaluate(() => document.scrollingElement.scrollWidth) });
  await page.screenshot({ path: `${OUT}/e2_u32_ru_390.png`, fullPage: true });
  await page.close(); await c2.close();
  const c3 = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const r = await openRec(c3, "rec=u32_double_slit/young", "ru");
  L("ru 1280 u32", await ui(r.page));
  await r.page.screenshot({ path: `${OUT}/e2_u32_ru_1280.png` });
  await r.page.close(); await c3.close();
}
// old links
for (const q of ["rec=v04_orbits/mercury", "rec=v02_double_slit/young", "rec=u32_double_slit/nonexistent", "rec=u32_double_slit", "rec=zz99_none/x"]) {
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  await page.goto(`${base}/run?${q}&lang=en`);
  await sleep(6000);
  L("old/odd link " + q, { ...(await ui(page)), errs, body: (await page.evaluate(() => document.body.innerText)).slice(0, 250) });
  await page.close();
}
// old runs (records made before the rename)
for (const id of ["20261111-170830-v04-2ca9", "20261029-144431-v09-505c", "20261111-171659-v02-8d90", "20261111-183110-p01-0377"]) {
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
  page.on("response", (r) => { if (r.status() >= 400) errs.push(`${r.status()} ${r.url()}`); });
  await page.goto(`${base}/run?id=${id}&lang=en`);
  try { await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 120000 }); } catch (e) { errs.push("timeout"); }
  await sleep(1500);
  L("old run " + id, { ...(await ui(page)), errs });
  await page.screenshot({ path: `${OUT}/e2_oldrun_${id}.png` });
  await page.close();
}
await br.close();
