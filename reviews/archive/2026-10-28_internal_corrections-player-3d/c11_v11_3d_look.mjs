// C1 review, check 11: v11 in 3-D at the end of an experiment (small geometry, CPU): screenshots of the scene from
// the world's camera buttons, with the 3-D layers listed, and the same after going back to 40 % of the history
// (the tracks, the particles and the screen's P(x, y) must rewind). The screen's image orientation (fringes along x,
// the y-factor's Gaussian along y) and the volume's y extent are judged on the images.
// Own server 127.0.0.1:8502. Output: out/c11_v11_*.png, out/c11_v11_3d_look.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8502";
const OUT = process.env.OUT || "/pw/c1rev_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
const params = { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 400, n_tracks: 30, sigma_y: Number(process.env.SY || 3) };
const r = await post("/api/runs", { viz: "v11_double_slit_2d", params, seed: 9 });
await page.goto(base + "/run?id=" + r.id);
await page.waitForTimeout(5000);
await page.evaluate(() => { const s = document.getElementById("speed"); s.value = String(+s.value + 60); s.dispatchEvent(new Event("change")); });
await page.click("#rec");
const t0 = Date.now();
while (Date.now() - t0 < 600000) {
  await page.waitForTimeout(3000);
  const done = await page.evaluate(() => [...document.querySelectorAll(".events .ev")].some((e) => /завершена/.test(e.textContent)));
  if (done) break;
}
await page.waitForTimeout(3000);
if ((await page.evaluate(() => document.getElementById("rec").textContent)).includes("⏸")) await page.click("#rec");
await page.waitForTimeout(2000);
const layers = await page.evaluate(() => document.querySelector(".s3d-view").__scene3d.layers().map((L) => `${L.id}:${L.kind}:${L.visible}`));
log(`v11 run ${r.id} (sigma_y ${params.sigma_y}): layers ${layers.join(", ")}`);
const views = await page.evaluate(() => [...document.querySelectorAll(".s3d-tools button")].map((b) => b.textContent.trim()).filter((t) => t && !/Срез/.test(t)));
log(`camera buttons: ${views.join(" | ")}`);
await page.locator("#center").screenshot({ path: `${OUT}/c11_v11_end_default.png` });
for (const v of views.slice(0, 5)) {
  await page.click(`.s3d-tools button:has-text("${v}")`).catch(() => {});
  await page.waitForTimeout(1500);
  await page.locator("#center").screenshot({ path: `${OUT}/c11_v11_end_${v.replace(/[^a-zA-Zа-яА-Я0-9]/g, "_")}.png` });
}
const max = await page.evaluate(() => +document.getElementById("timeline").max);
await page.evaluate((i) => { const t = document.getElementById("timeline"); t.value = String(i); t.dispatchEvent(new Event("input")); }, Math.round(0.4 * max));
await page.waitForTimeout(3000);
await page.locator("#center").screenshot({ path: `${OUT}/c11_v11_at40pct.png` });
log(`history ${max + 1} frames; screenshots at the end (per camera button) and at 40 % (last camera)`);
fs.writeFileSync(`${OUT}/c11_v11_3d_look.txt`, lines.join("\n") + "\n");
await post(`/api/runs/${r.id}/stop`);
await browser.close();
