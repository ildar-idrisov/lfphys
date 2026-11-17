// R-P probe: u32 Explore (time "buildup", acts "now"): a change keeps the cursor; the frame shown is a computed frame
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
const page = await ctx.newPage();
await page.goto(`${base}/run?demo=u32_double_slit&screen=explore&lang=en`);
const X = "window.__lfExplore.explore";
await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 60000 });
await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = "8"; s.dispatchEvent(new Event("input")); });
await page.waitForTimeout(400);
const a = await page.evaluate(`({ t: ${X}.state.clock - ${X}.state.cur.launchedAt, i: ${X}.point().i, label: document.querySelector(".dm-time").textContent })`);
await page.locator('.dm-ctl[data-param="d_um"] .dm-detent').nth(2).click();
await page.waitForFunction(() => window.__lfExplore.explore.point().values.d_um === 200, null, { timeout: 60000 });
await page.waitForTimeout(400);
const b = await page.evaluate(`({ t: ${X}.state.clock - ${X}.state.cur.launchedAt, i: ${X}.point().i, label: document.querySelector(".dm-time").textContent, traces: ${X}.state.traces.length, frames: ${X}.point().W.frames.map((f) => f.t).slice(0, 12) })`);
out("u32 explore: cursor at frame 8, then d 100 → 200 µm", { before: a, after: b });
await br.close();
