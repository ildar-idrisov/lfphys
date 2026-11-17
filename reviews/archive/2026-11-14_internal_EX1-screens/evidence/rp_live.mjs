// R-P probe: «compute live» on the server: an off-grid point, its label, a refusal, a full queue, «▶ Compute live», «Another sample»
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const LANG = process.env.LFVIZ_LANG || "en";
const SH = process.env.SHOTS || "/pw/shots";
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const settle = (page, ms = 300) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
const setSlider = (page, param, v) => page.evaluate(([p, x]) => {
  const s = document.querySelector(`.dm-screen:not([hidden]) .dm-ctl[data-param="${p}"] .dm-slider`);
  s.value = String(x); s.dispatchEvent(new Event("input")); s.dispatchEvent(new Event("change"));
}, [param, v]);
const drawer = async (page) => { await page.locator(".dm-how").click(); await settle(page); const d = await page.locator(".dm-drawer-body").innerText(); await page.keyboard.press("Escape"); return d; };
const mode = process.argv[3] || "all";
if (mode === "all" || mode === "s03") {
  const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  const resp = [];
  page.on("response", (r) => { if (r.url().includes("/api/atlas/")) resp.push({ st: r.status(), src: r.headers()["x-lf-source"] || null, url: r.url().split("/api/")[1] }); });
  await page.goto(`${base}/run?demo=s03_projectile&screen=explore&lang=${LANG}`);
  const X = "window.__lfExplore.explore";
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 30000 });
  // the slider's step on the server and what positions it takes
  const sl = await page.evaluate(() => [...document.querySelectorAll(".dm-screen:not([hidden]) .dm-slider")].map((s) => ({ min: s.min, max: s.max, step: s.step })));
  out("server sliders", { sl });
  await setSlider(page, "angle_deg", 37.3);
  await page.waitForFunction(() => { const p = window.__lfExplore.explore.point(); return p && p.live; }, null, { timeout: 60000 });
  const p1 = await page.evaluate(`({ values: ${X}.point().values, live: ${X}.point().live, source: ${X}.point().source, at: ${X}.point().at, out: document.querySelector('.dm-ctl[data-param="angle_deg"] output').textContent, offGridMark: document.querySelector('.dm-ctl[data-param="angle_deg"] output').className })`);
  out("off-grid 37.3° computed live", { p1, resp: resp.slice(-2) });
  await page.locator(".dm-play").click();
  await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 30000 });
  const d1 = await drawer(page);
  out("its drawer", { text: d1.split("\n").slice(0, 40).join(" | ").slice(0, 1400) });
  // the same value again: from the cache (server) — still labelled «computed live … at <now>»?
  await setSlider(page, "angle_deg", 45); await page.waitForFunction(() => !window.__lfExplore.explore.point().live);
  await page.locator(".dm-play").click(); await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 30000 });
  await page.screenshot({ path: `${SH}/rp_live_trace_${LANG}.png` });
  // a refused off-grid value: h 0, angle 0, v0 12.5
  await page.locator('.dm-ctl[data-param="h_m"] .dm-detent').nth(0).click();
  await page.locator('.dm-ctl[data-param="angle_deg"] .dm-detent').nth(0).click();
  await page.waitForFunction(() => !!window.__lfExplore.explore.state.refused, null, { timeout: 20000 });
  const r0 = await page.locator(".dm-refusal-side").innerText();
  await setSlider(page, "v0", 12.5);
  await sleep(2500);
  const r1 = await page.locator(".dm-refusal-side").innerText();
  out("refused: grid (h 0, θ 0) then off-grid v0 12.5", { grid: r0, offGrid: r1, resp: resp.slice(-1), playDisabled: await page.locator(".dm-play").isDisabled() });
  // «▶ Compute live» with non-default values
  await page.locator('.dm-ctl[data-param="h_m"] .dm-detent').nth(3).click();
  await page.locator('.dm-ctl[data-param="angle_deg"] .dm-detent').nth(6).click();
  await page.locator('.dm-ctl[data-param="air"] button[data-value="true"]').click();
  await page.waitForFunction(() => { const v = window.__lfExplore.explore.point(); return v && v.values.h_m === 5 && v.values.angle_deg === 30 && v.values.air === true; }, null, { timeout: 20000 });
  const vals = await page.evaluate(`${X}.values()`);
  await Promise.all([page.waitForURL(/\/run\?id=/, { timeout: 30000 }), page.locator(".dm-live").click()]);
  const id = new URL(page.url()).searchParams.get("id");
  const meta = await (await fetch(`${base}/api/runs/${id}`)).json();
  out("«▶ Compute live» from Explore", { vals, url: page.url().replace(base, ""), preset: meta.preset, params: Object.fromEntries(["h_m", "v0", "angle_deg", "air", "object", "companion"].map((k) => [k, (meta.params || {})[k]])) });
  await ctx.close();
}
if (mode === "all" || mode === "lab") {
  const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  await page.goto(`${base}/run?demo=s03_projectile&screen=lab&lang=${LANG}`);
  await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 30000 });
  await page.locator(".dm-steps button").nth(1).click();
  await page.waitForFunction(() => window.__lfLab.step() && window.__lfLab.step().step.id === "angles" && window.__lfLab.step().cur);
  await page.locator('.dm-ctl[data-param="angle_deg"] .dm-detent').nth(9).click();
  await page.waitForFunction(() => window.__lfLab.step().cur.pt.values.angle_deg === 60);
  await Promise.all([page.waitForURL(/\/run\?id=/, { timeout: 30000 }), page.locator(".dm-live").click()]);
  const id = new URL(page.url()).searchParams.get("id");
  const meta = await (await fetch(`${base}/api/runs/${id}`)).json();
  out("«▶ Compute live» from Lab part 2 at 60°", { preset: meta.preset, params: Object.fromEntries(["h_m", "v0", "angle_deg", "air", "object", "companion"].map((k) => [k, (meta.params || {})[k]])) });
  await page.goto(`${base}/run?demo=s03_projectile&screen=watch&lang=${LANG}`);
  await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 30000 });
  await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(700); s.dispatchEvent(new Event("input")); });
  await Promise.all([page.waitForURL(/\/run\?id=/, { timeout: 30000 }), page.locator(".dm-live").click()]);
  const id2 = new URL(page.url()).searchParams.get("id");
  const meta2 = await (await fetch(`${base}/api/runs/${id2}`)).json();
  out("«▶ Compute live» from Watch at its 4th world (the vacuum comparison)", { preset: meta2.preset, params: Object.fromEntries(["h_m", "v0", "angle_deg", "air", "object", "companion"].map((k) => [k, (meta2.params || {})[k]])) });
  await ctx.close();
}
if (mode === "all" || mode === "u32") {
  const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  await page.goto(`${base}/run?demo=u32_double_slit&screen=explore&lang=${LANG}`);
  const X = "window.__lfExplore.explore";
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 60000 });
  // «Another sample»
  const btn = page.getByRole("button", { name: LANG === "ru" ? /Другая выборка|выборк/i : /Another sample/ });
  const has = await btn.count();
  if (has) {
    await btn.first().click();
    await page.waitForFunction(() => { const p = window.__lfExplore.explore.point(); return p && p.live; }, null, { timeout: 120000 });
    const d = await drawer(page);
    out("u32 «Another sample»", { seed: await page.evaluate(`${X}.point().seed`), drawerSeed: (d.match(/(Random seed|Затравка|сид|Сид)[^\n]*\n?[^\n]*/i) || [""])[0], live: d.includes("live") || d.includes("на этом сервере") });
  } else out("u32 «Another sample»: no button", {});
  // a full queue: six concurrent off-grid points, then one from the UI
  const codes = page.evaluate((b) => Promise.all([410, 420, 430, 440, 450, 460, 470].map((lam) => fetch(`${b}/api/atlas/u32_double_slit/explore/point`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ values: { lam_nm: lam } }) }).then((r) => r.status))), base);
  await sleep(300);
  await setSlider(page, "lam_nm", 655);
  await sleep(1500);
  const msg = await page.locator(".dm-refusal-side").innerText();
  out("u32: a full queue (7 concurrent + 1 from the UI)", { statuses: await codes, shown: msg, lang: LANG });
  await ctx.close();
}
await br.close();
