import { chromium } from "playwright";
const port = process.env.PORT, tag = process.env.TAG, base = `http://127.0.0.1:${port}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const b = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const [w, h] of [[1600, 1000], [1280, 800]]) {
  const r = await post("/api/runs", { viz: "p04_fluids", preset: "cavity" });
  const ctx = await b.newContext({ viewport: { width: w, height: h } });
  const page = await ctx.newPage();
  await page.goto(`${base}/run?id=${r.id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 60000 });
  await post(`/api/runs/${r.id}/command`, { cmd: "play", args: {} });
  await sleep(5000);
  const sz = await page.evaluate(() => { const c = document.querySelector(".sw-canvas"); const r = c.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; });
  console.log(JSON.stringify({ tag, w, h, canvas: sz }));
  await page.screenshot({ path: `/pw/shots/${tag}_p04_cavity_${w}.jpg`, type: "jpeg", quality: 70 });
  await post(`/api/runs/${r.id}/stop`, {});
  await ctx.close();
}
await b.close();
