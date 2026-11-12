// s10: screenshots of v16 runs on the reviewer's PRIVATE server (port given), for the labels and panels: presets lg3
// (exact, disc), tight_par (paraxial) and dove; plays ~1.2 s of world time, pauses, opens the run page, saves a
// full-page PNG and the right panels' text.
import { chromium } from "playwright";
import fs from "fs";

const port = process.argv[2] || "8532";
const out = process.argv[3] || "/out";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-unsafe-swiftshader"] });
for (const preset of ["lg3", "tight_par", "dove"]) {
  const r = await post("/api/runs", { viz: "v16_optical_vortices", preset, seed: 3 });
  const id = r.id;
  await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: 0.5 } });
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  await sleep(4000);
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1100 } });
  await page.goto(`${base}/run?id=${id}`);
  await sleep(5000);
  await page.screenshot({ path: `${out}/s10_${preset}.png`, fullPage: true });
  const txt = await page.evaluate(() => document.body.innerText);
  fs.writeFileSync(`${out}/s10_${preset}_text.txt`, txt);
  console.log(preset, id, "saved", txt.length, "chars");
  await page.close();
  await post(`/api/runs/${id}/stop`, {});
}
await browser.close();
