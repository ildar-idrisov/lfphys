// R-P probe: Space on the focused «⏱ Stop» during a flight and after the landing (S03 lab part 1)
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch();
const page = await (await br.newContext({ viewport: { width: 1280, height: 800 } })).newPage();
await page.goto(`${base}/run?demo=s03_projectile&screen=lab&lang=en`);
await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 30000 });
const st = () => page.evaluate(() => { const s = window.__lfLab.step(), L = window.__lfLab.state; return { sw: s.sw && { t: +s.sw.t.toFixed(3), running: s.sw.running, stopped: s.sw.stopped }, playing: L.playing, paused: L.paused, local: +(s.clock - (s.cur.launchedAt ?? s.clock)).toFixed(3) }; });
await page.locator(".dm-play").click();
await sleep(150);
await page.locator(".dm-sw-btn").focus();
await page.keyboard.press("Space"); await sleep(300);
out("Space on «⏱ Stop» during the flight", await st());
await page.keyboard.press("Space"); await sleep(1500);  // play on to the end
out("after the landing (the stopwatch still running)", await st());
await page.locator(".dm-sw-btn").focus();
await page.keyboard.press("Space"); await sleep(300);
out("Space on «⏱ Stop» after the landing", await st());
await br.close();
