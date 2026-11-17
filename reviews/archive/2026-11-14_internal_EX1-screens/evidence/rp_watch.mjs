// R-P probe: Watch's captions over the timeline and «hold» (toy: hold 1 s at 1.5 s; u32: hold 3 s at 22 s)
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const LANG = process.env.LFVIZ_LANG || "en";
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
for (const world of (process.argv[3] || "s98_atlas_toy,u32_double_slit").split(",")) {
  const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  await page.goto(`${base}/run?demo=${world}&screen=watch&lang=${LANG}`);
  await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 60000 });
  const caps = await page.evaluate(() => window.__lfWatch.state.story.captions.map((c) => ({ step: c.step, hold: c.hold, at: c.at, t: c.t, n: c.n })));
  const fps = await page.evaluate(() => { const e = window.__lfWatch.state.rec.entry; return e.fps / (e.frame_stride || 1); });
  out(`${world}: captions`, { fps, caps });
  const hc = caps.find((c) => c.hold);
  if (!hc) { await ctx.close(); continue; }
  // from 1 s of played time before the hold caption: play and sample the step every 100 ms
  await page.evaluate((k) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(k); s.dispatchEvent(new Event("input")); }, Math.max(0, hc.step - fps));
  await page.locator(".dm-screen:not([hidden]) .dm-play").click();
  const t0 = Date.now(), samples = [];
  while (Date.now() - t0 < (hc.hold + 2.5) * 1000) { samples.push([Date.now() - t0, await page.evaluate(() => window.__lfWatch.step()), (await page.evaluate(() => window.__lfWatch.caption())).slice(0, 25)]); await sleep(100); }
  const atHold = samples.filter((s) => s[1] === hc.step);
  out(`${world}: playback around the hold caption`, { holdStep: hc.step, hold: hc.hold, msAtHoldStep: atHold.length ? atHold[atHold.length - 1][0] - atHold[0][0] : 0, first: samples.slice(0, 3), atHold: atHold.slice(0, 2), after: samples.slice(-2) });
  // pause and play again during a hold: does the playback go on?
  await page.evaluate((k) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(k); s.dispatchEvent(new Event("input")); }, Math.max(0, hc.step - 3));
  await page.locator(".dm-screen:not([hidden]) .dm-play").click();
  await page.waitForFunction((k) => window.__lfWatch.step() === k, hc.step, { timeout: 10000, polling: 20 });
  await sleep(200);
  await page.keyboard.press("Space"); await sleep(150);  // pause
  const lbl1 = await page.locator(".dm-screen:not([hidden]) .dm-play").innerText();
  await page.keyboard.press("Space"); await sleep(400);  // play again, within the hold
  const lbl2 = await page.locator(".dm-screen:not([hidden]) .dm-play").innerText();
  const st = await page.evaluate(() => ({ step: window.__lfWatch.step(), playing: window.__lfWatch.state.playing, holdLeft: window.__lfWatch.state.holdUntil - performance.now() }));
  out(`${world}: pause and play during the hold`, { afterPause: lbl1, afterPlay: lbl2, ...st });
  // the hold's frame reached by scrubbing to it then ▶ (held? the design says scrubbing is not held)
  await ctx.close();
}
await br.close();
