// R-P probe: the closed drawer in the tab order; focus when it opens; what a slider says to assistive technology
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const br = await chromium.launch();
const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
const page = await ctx.newPage();
// as the site: lf-mode static (sliders over the grid's indices)
await ctx.route(/\/run(\?|$)/, async (route) => { const r = await route.fetch(); const html = (await r.text()).replace('content="server"', 'content="static"'); await route.fulfill({ response: r, body: html }); });
await ctx.route(/\/api\/(.+)\.json(\?.*)?$/, async (route) => { const name = new URL(route.request().url()).pathname.replace(/^\/api\//, "").replace(/\.json$/, ""); const r = await route.fetch({ url: `${base}/api/${name}` }); await route.fulfill({ response: r }); });
await ctx.route(/\/aliases\.json$/, (route) => route.fulfill({ status: 200, contentType: "application/json", body: "{}" }));
await page.goto(`${base}/run?demo=s03_projectile&screen=explore&lang=en`);
await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 30000 });
await page.locator('.dm-ctl[data-param="h_m"] .dm-detent').nth(3).click();
await page.waitForTimeout(500);
const sl = await page.evaluate(() => { const s = document.querySelector('.dm-ctl[data-param="h_m"] .dm-slider'); return { value: s.value, valuetext: s.getAttribute("aria-valuetext"), label: s.getAttribute("aria-label"), shown: document.querySelector('.dm-ctl[data-param="h_m"] output').textContent }; });
out("site slider: h = 5 m", sl);
const tog = await page.evaluate(() => [...document.querySelectorAll('.dm-ctl[data-param="air"] button, .dm-speed button, .dm-detent')].slice(0, 4).map((b) => ({ t: b.textContent, pressed: b.getAttribute("aria-pressed"), cls: b.className })));
out("toggle/speed/detent state for AT", { tog });
// the closed drawer in the tab order
await page.locator(".dm-play").focus();
const stops = [];
for (let i = 0; i < 25; i++) { await page.keyboard.press("Tab"); stops.push(await page.evaluate(() => { const e = document.activeElement; const d = e && e.closest(".dm-drawer"); return `${e.tagName.toLowerCase()}.${String(e.className).split(" ")[0]}[${(e.textContent || "").trim().slice(0, 14)}]${d ? " IN-DRAWER(aria-hidden=" + d.getAttribute("aria-hidden") + ")" : ""}`; })); }
out("Tab after ▶ with the drawer closed", { stops: stops.filter((s, i) => i < 25) });
// open the drawer by the keyboard: where is the focus?
await page.locator(".dm-how").focus(); await page.keyboard.press("Enter"); await page.waitForTimeout(400);
out("drawer opened by Enter: the focus", { active: await page.evaluate(() => { const e = document.activeElement; return `${e.tagName.toLowerCase()}.${e.className} in drawer: ${!!e.closest(".dm-drawer")}`; }), dialogRole: await page.evaluate(() => document.querySelector(".dm-drawer").getAttribute("role")) });
await br.close();
