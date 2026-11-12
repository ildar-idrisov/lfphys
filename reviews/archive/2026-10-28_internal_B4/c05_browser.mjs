// Review B4, check c05 (browser): the speed bar's tick placement against the slider thumb's travel, the ticks of
// narrow speed ranges, «факт», v11's observer box in the 3-D scene, and what v12 shows at t = 0 (the window).
//
// Root (fix after archiving): the reviewer's own server on port 8502 (engine mounted read-only at /lf, runs in a
// scratch folder); this script is copied to the playwright scratch folder (node_modules) and run there:
//   docker run --rm --network host --shm-size=2g --init --user "$(id -u):$(id -g)" -v <pw>:/pw -w /pw \
//     mcr.microsoft.com/playwright:v1.58.2-jammy node b4rev_c05_browser.mjs > <review>/out/c05_browser.txt
// Screenshots land in <pw>/b4rev_shots/ and are copied to <review>/out/.
import { chromium } from "playwright";
import fs from "node:fs";

const base = "http://127.0.0.1:8502";
fs.mkdirSync("b4rev_shots", { recursive: true });
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [];
const log = (...a) => console.log(...a);
async function open(viz, preset, params = {}, wait = 6000) {
  const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });
  page.on("pageerror", (e) => errs.push(`${viz}/${preset} pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`${viz}/${preset} console: ${m.text()}`); });
  const r = await post("/api/runs", { viz, preset, params, seed: 3 });
  if (!r.id) { errs.push(`${viz}/${preset} start: ${JSON.stringify(r)}`); return [page, null]; }
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(wait);
  return [page, r.id];
}
const cmd = (id, c, args = {}) => post(`/api/runs/${id}/command`, { cmd: c, args });
const S = (page, f, a) => page.evaluate(f, a);

// the thumb's centre (px from the input's left edge) at a slider value, from a screenshot of the input: the columns
// where the thumb-coloured pixels are taller than the track
async function thumbCentre(page, value) {
  await S(page, (v) => { document.getElementById("speed").value = String(v); }, value);
  await page.waitForTimeout(150);
  const buf = await page.locator("#speed").screenshot();
  return S(page, async (b64) => {
    const img = new Image(); img.src = "data:image/png;base64," + b64; await img.decode();
    const c = document.createElement("canvas"); c.width = img.width; c.height = img.height;
    const g = c.getContext("2d"); g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, c.width, c.height).data, dpr = window.devicePixelRatio || 1;
    // reference colour: the most saturated pixel
    let best = 0, ref = null;
    for (let i = 0; i < d.length; i += 4) { const s = Math.max(d[i], d[i + 1], d[i + 2]) - Math.min(d[i], d[i + 1], d[i + 2]); if (s > best) { best = s; ref = [d[i], d[i + 1], d[i + 2]]; } }
    const near = (i) => Math.abs(d[i] - ref[0]) + Math.abs(d[i + 1] - ref[1]) + Math.abs(d[i + 2] - ref[2]) < 60;
    const cols = [];
    for (let x = 0; x < c.width; x++) { let n = 0; for (let y = 0; y < c.height; y++) if (near(4 * (y * c.width + x))) n++; cols.push(n); }
    const tall = Math.max(...cols), sel = []; cols.forEach((n, x) => { if (n >= 0.6 * tall) sel.push(x); });
    return { centre: (sel.reduce((a, b) => a + b, 0) / sel.length) / dpr, width: c.width / dpr, thumbCols: sel.length / dpr, ref };
  }, buf.toString("base64"));
}

// A. v04: ticks against the thumb
{
  const [page, id] = await open("v04_orbits", "default");
  const info = await S(page, () => {
    const box = document.querySelector(".speedbox").getBoundingClientRect(), inp = document.getElementById("speed").getBoundingClientRect();
    return { boxLeft: box.left, boxW: box.width, inpLeft: inp.left, inpW: inp.width,
             ticks: [...document.querySelectorAll("#speedticks span")].map((s) => [s.textContent, parseFloat(s.style.left)]) };
  });
  log("v04 speed box", JSON.stringify(info));
  const t0 = await thumbCentre(page, 0), t1 = await thumbCentre(page, 1000);
  log(`v04 thumb centre at value 0: ${t0.centre.toFixed(2)} px, at 1000: ${t1.centre.toFixed(2)} px of ${t0.width} px (thumb ~${t1.thumbCols.toFixed(1)} px wide); renderSpeedTicks assumes 8 and ${(info.boxW - 8).toFixed(2)}`);
  // the tick "1 s": the slider value whose speed is 1 s/s, and where the thumb is then
  const st = await S(page, () => null);
  const [lo, hi] = [1e-10, 1e18];
  const v1s = Math.round(1000 * (0 - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo)));
  const t1s = await thumbCentre(page, v1s);
  const tick1s = info.ticks.find((t) => t[0] === "1 с");
  log(`tick «1 с» at ${tick1s ? tick1s[1].toFixed(2) : "—"} px; thumb at the value of 1 s/s (${v1s}/1000): ${t1s.centre.toFixed(2)} px`);
  try { await page.locator(".bottombar").screenshot({ path: "b4rev_shots/c05_v04_speedbar.png", timeout: 60000 }); } catch (e) { errs.push("v04 bar shot: " + e.message.slice(0, 80)); }
  // the actual speed when the computation cannot keep up
  const d = 0.011620276913293521;
  await cmd(id, "speed", { value: d * 1e4 }); await cmd(id, "play");
  await page.waitForTimeout(6000);
  log("v04 at 1e4 x default:", JSON.stringify(await S(page, () => ({ speedv: document.getElementById("speedv").textContent, fact: document.getElementById("speedfact").textContent }))));
  try { const bb = await page.locator(".bottombar").boundingBox(); await page.screenshot({ path: "b4rev_shots/c05_v04_fact.png", clip: bb, timeout: 60000 }); } catch (e) { errs.push("v04 fact shot: " + e.message.slice(0, 80)); }
  await cmd(id, "pause");
  await page.waitForTimeout(1500);
  log("v04 after pause:", JSON.stringify(await S(page, () => ({ fact: document.getElementById("speedfact").textContent }))));
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}

// B. v11 observer (small geometry, CPU): the narrow range's ticks, the box in the scene
{
  const small = { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 300, n_tracks: 20 };
  const [page, id] = await open("v11_double_slit_2d", "observer", small, 8000);
  if (id) {
    const hd = await (await fetch(`${base}/api/runs/${id}`)).json();
    log("v11 ticks:", JSON.stringify(await S(page, () => [...document.querySelectorAll("#speedticks span")].map((s) => s.textContent))));
    try { await page.screenshot({ path: "b4rev_shots/c05_v11_observer.png", timeout: 90000 }); } catch (e) { errs.push("v11 shot: " + e.message.slice(0, 80)); }
    await post(`/api/runs/${id}/stop`, {});
  }
  await page.close();
}

// C. v12 small free packet: what the page shows at t = 0, before anything has arrived
{
  const [page, id] = await open("v12_arrival_times_2d", "gauss", { grid: "coarse", n_bohm: 300, L: 12.0, sigma_z: 2.0, sigma_x: 2.0, soft: false }, 9000);
  if (id) {
    const o = await S(page, () => [...document.querySelectorAll(".panel")].map((p) => p.innerText.slice(0, 600)).filter((t) => /опыт: время прихода/i.test(t)));
    log("v12 at t = 0, panel «Опыт: время прихода»:", JSON.stringify(o));
    const loc = page.locator(".panel", { hasText: "Распределение времени прихода" }).first();
    try { await loc.scrollIntoViewIfNeeded(); await loc.screenshot({ path: "b4rev_shots/c05_v12_t0_chart.png" }); } catch (e) { errs.push("v12 chart shot " + e.message.slice(0, 80)); }
    log("v12 ticks:", JSON.stringify(await S(page, () => [...document.querySelectorAll("#speedticks span")].map((s) => s.textContent))));
    await post(`/api/runs/${id}/stop`, {});
  }
  await page.close();
}

// D. v13 superposition: ticks
{
  const [page, id] = await open("v13_hydrogen_3d", "super_1s2p", {}, 7000);
  if (id) {
    log("v13 ticks:", JSON.stringify(await S(page, () => [...document.querySelectorAll("#speedticks span")].map((s) => [s.textContent, s.style.left]))));
    try { await page.locator(".bottombar").screenshot({ path: "b4rev_shots/c05_v13_speedbar.png", timeout: 60000 }); } catch (e) { errs.push("v13 shot: " + e.message.slice(0, 80)); }
    await post(`/api/runs/${id}/stop`, {});
  }
  await page.close();
}
log("errors:", JSON.stringify(errs, null, 1));
await browser.close();
