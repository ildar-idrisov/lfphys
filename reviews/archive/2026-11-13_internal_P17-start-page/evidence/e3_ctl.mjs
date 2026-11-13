// review P, e3: are the live controls on a recording disabled (left panel and the copies the view places), and what a change does
import { chromium } from "playwright";
const base = process.argv[2] || "http://127.0.0.1:8682";
const L = (k, v) => console.log(JSON.stringify({ k, v }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
for (const rec of ["u32_double_slit/young", "u31_light_travel/sun_earth", "u38_wave_3d/double", "r11_thomas_3d/thomas", "u39_fast_observer/city"]) {
  const page = await ctx.newPage();
  await page.goto(`${base}/run?rec=${rec}&lang=en`);
  try { await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 180000 }); } catch (e) { L(rec, "load timeout"); await page.close(); continue; }
  await sleep(1500);
  const s = await page.evaluate(() => {
    const desc = (e) => ({ tag: e.tagName, type: e.type, disabled: e.disabled, readOnly: e.readOnly, label: (e.closest(".ctl,.field,label,div")?.innerText || "").trim().slice(0, 40) });
    return {
      left: [...document.querySelectorAll("#left input, #left select")].filter((e) => e.offsetParent).map(desc).slice(0, 12),
      leftEnabled: [...document.querySelectorAll("#left input, #left select")].filter((e) => e.offsetParent && !e.disabled).length,
      centerEnabled: [...document.querySelectorAll("#center input:not([type=checkbox]), #center select")].filter((e) => e.offsetParent && !e.disabled).map(desc).slice(0, 12),
      centerButtons: [...document.querySelectorAll("#center button")].filter((e) => e.offsetParent && !e.disabled).map((b) => b.textContent.trim()).slice(0, 20),
      timeline: document.getElementById("timeline").max,
    };
  });
  L(rec, s);
  // change the first enabled centre select or range: what happens
  const h = await page.$("#center select:not([disabled]), #center input[type=range]:not([disabled])");
  if (h) {
    const tag = await h.evaluate((e) => e.tagName);
    if (tag === "SELECT") { const opts = await h.$$eval("option", (o) => o.map((x) => x.value)); if (opts.length > 1) await h.selectOption(opts[1]); }
    else await h.evaluate((e) => { e.value = String(Number(e.min) + (Number(e.max) - Number(e.min)) * 0.9); e.dispatchEvent(new Event("input", { bubbles: true })); e.dispatchEvent(new Event("change", { bubbles: true })); });
    await sleep(800);
    L(rec + " after centre change", await page.evaluate(() => [...document.querySelectorAll(".toast")].map((e) => e.textContent.slice(0, 100))));
  }
  await page.screenshot({ path: `/shots/e3_${rec.replace("/", "_")}.png` });
  await page.close();
}
await br.close();
