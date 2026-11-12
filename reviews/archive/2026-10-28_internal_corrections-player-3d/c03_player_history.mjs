// C1 review, check 03: does everything the player shows follow the cursor, whichever way it got there?
// For each visualization: record ~REC s with ⏺, then show the same frame (the middle of the history) twice:
//   A — reached FORWARD (⏮, ▶ history playback up to just before it, then one step forward: views fed message by
//       message, many render() calls on the way);
//   B — reached BACKWARD from the end (⏭ then the timeline: the view rebuilt from the record, one render()).
// The centre (scene, windows, canvases) and the panels (checks, events, set-up) of A and B are compared pixel by pixel
// / text by text. Then ◀ (backward playback) from the end: distinct frames shown per second, and (3-D worlds) the GPU
// objects alive before and after (scene3d.gpuInfo()).
// Own server 127.0.0.1:8502 only. Run (playwright 1.58.2 image, node_modules in the pw folder):
//   docker run --rm --name lf-c1rev-c03 --network host --shm-size=2g --init -v <pw>:/pw -w /pw \
//     mcr.microsoft.com/playwright:v1.58.2-jammy node c1rev_c03.mjs
// Output: out/c03_player_history.txt (+ PNGs out/c03_<viz>_{fwd,back}.png)
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8502";
const OUT = process.env.OUT || "/pw/c1rev_out";
fs.mkdirSync(OUT, { recursive: true });
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const SMALL = {
  v08_wave_3d: { n: 128, zmax: 10.0 },
  v09_thomas_3d: { ngrid: 48 },
  v11_double_slit_2d: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 200, n_tracks: 20 },
  v12_arrival_times_2d: { grid: "coarse", n_bohm: 200, n_tracks: 20, L: 12.0, sigma_z: 2.0, sigma_x: 2.0 },
};
const VIZ = (process.env.VIZ || "v01_light_travel,v02_double_slit,v04_orbits,v08_wave_3d,v09_thomas_3d,v10_fast_observer,v11_double_slit_2d,v12_arrival_times_2d,v13_hydrogen_3d").split(",");
const REC = Number(process.env.REC || 14);

async function pixDiff(page, a, b) {
  return page.evaluate(async ([a, b]) => {
    const load = (src) => new Promise((res) => { const i = new Image(); i.onload = () => res(i); i.src = src; });
    const [A, B] = await Promise.all([load(a), load(b)]);
    const w = Math.min(A.width, B.width), h = Math.min(A.height, B.height);
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const g = c.getContext("2d");
    g.drawImage(A, 0, 0); const da = g.getImageData(0, 0, w, h).data;
    g.clearRect(0, 0, w, h); g.drawImage(B, 0, 0); const db = g.getImageData(0, 0, w, h).data;
    let n = 0, mx = 0;
    for (let i = 0; i < da.length; i += 4) {
      const d = Math.max(Math.abs(da[i] - db[i]), Math.abs(da[i + 1] - db[i + 1]), Math.abs(da[i + 2] - db[i + 2]));
      if (d > 8) n++; mx = Math.max(mx, d);
    }
    return { size: [w, h], differing: n, frac: n / (w * h), max: mx };
  }, [a, b]);
}
const tl = (page) => page.evaluate(() => ({ v: +document.getElementById("timeline").value, max: +document.getElementById("timeline").max, time: document.getElementById("time").textContent, status: document.getElementById("status").textContent, busy: document.getElementById("busy").style.display !== "none" ? document.getElementById("busy").textContent : "" }));
const setTL = (page, i) => page.evaluate((i) => { const t = document.getElementById("timeline"); t.value = String(i); t.dispatchEvent(new Event("input")); }, i);
const panels = (page) => page.evaluate(() => ({
  checks: document.querySelector(".checks") ? document.querySelector(".checks").innerText : "",
  events: [...document.querySelectorAll(".events .ev")].filter((e) => !e.classList.contains("future")).length,
  future: [...document.querySelectorAll(".events .ev.future")].length,
  live: [...document.querySelectorAll("#left .ctl")].map((c) => { const i = c.querySelector("input,select"); return i ? (i.type === "checkbox" ? i.checked : i.value) + (i.disabled ? "(off)" : "") : ""; }).join("|"),
  right: [...document.querySelectorAll("#right .panel")].map((p) => p.innerText).join("\n---\n"),
}));
const gpu = (page) => page.evaluate(() => { const v = document.querySelector(".s3d-view"); return v && v.__scene3d && v.__scene3d.gpuInfo ? v.__scene3d.gpuInfo() : null; });

for (const viz of VIZ) {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
  const errs = [];
  page.on("pageerror", (e) => errs.push("pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
  try {
    const r = await post("/api/runs", { viz, params: SMALL[viz] || {}, seed: 5 });
    if (!r.id) { log(`${viz}: start refused ${JSON.stringify(r)}`); continue; }
    await page.goto(base + "/run?id=" + r.id);
    await page.waitForTimeout(4000);
    await page.click("#rec");
    await page.waitForTimeout(REC * 1000);
    await page.click("#rec");  // pause
    await page.waitForTimeout(1500);
    const end = await tl(page);
    const mid = Math.floor(end.max / 2);
    // A: forward
    await page.click("#tostart"); await page.waitForTimeout(800);
    await page.click("#fwd");
    const t0 = Date.now();
    while (Date.now() - t0 < 60000) { const s = await tl(page); if (s.v >= mid - 40) break; await page.waitForTimeout(20); }
    await page.click("#fwd");  // pause the history playback
    await page.waitForTimeout(300);
    let before = await tl(page);
    if (before.v > mid) log(`  (overshot to ${before.v} > ${mid}: A is then reached backwards too)`);
    while (before.v < mid) {  // frame by frame, forward; the timeline shows the new index only after the next animation frame
      await page.click("#step");
      const v0 = before.v;
      for (let k = 0; k < 100 && before.v === v0; k++) { await page.waitForTimeout(30); before = await tl(page); }
    }
    await page.waitForTimeout(2500);
    const A = await tl(page), PA = await panels(page);
    const shotA = await page.locator("#center").screenshot({ path: `${OUT}/c03_${viz}_fwd.png` });
    // B: from the end, back to the same frame
    await page.click("#toend"); await page.waitForTimeout(1500);
    const g0 = await gpu(page);
    await setTL(page, mid); await page.waitForTimeout(2500);
    const B = await tl(page), PB = await panels(page);
    const shotB = await page.locator("#center").screenshot({ path: `${OUT}/c03_${viz}_back.png` });
    const d = await pixDiff(page, "data:image/png;base64," + shotA.toString("base64"), "data:image/png;base64," + shotB.toString("base64"));
    log(`${viz} run ${r.id}: ${end.max + 1} frames, end ${end.time}; middle frame ${mid}: A ${A.time} / B ${B.time}`);
    log(`  centre A vs B: ${d.differing} px differ (${(100 * d.frac).toFixed(2)} %), max channel diff ${d.max}`);
    log(`  panels: checks ${PA.checks === PB.checks ? "same" : "DIFFER"}; events shown ${PA.events}/${PB.events} (future ${PA.future}/${PB.future}); set-up ${PA.live === PB.live ? "same" : "DIFFER: " + PA.live + " vs " + PB.live}; right panels ${PA.right === PB.right ? "same" : "DIFFER"}`);
    if (PA.right !== PB.right) {
      const a = PA.right.split("\n"), b = PB.right.split("\n");
      const k = a.findIndex((x, i) => x !== b[i]);
      log(`    first differing line: A «${(a[k] || "").slice(0, 140)}» / B «${(b[k] || "").slice(0, 140)}»`);
    }
    // ▶ from the start and ◀ from the end: distinct frames per second, rAF rate
    const sample = () => page.evaluate(() => new Promise((res) => {
      const seen = new Set(); let n = 0; const t0 = performance.now(); let worst = 0, last = t0;
      function f() { const now = performance.now(); worst = Math.max(worst, now - last); last = now; n++; seen.add(document.getElementById("timeline").value); if (now - t0 < 5000) requestAnimationFrame(f); else res({ raf: n / 5, distinct: seen.size / 5, worst_ms: Math.round(worst) }); }
      requestAnimationFrame(f);
    }));
    await page.click("#tostart"); await page.waitForTimeout(1000);
    await page.click("#fwd");
    const sf = await sample();
    if ((await tl(page)).v < (await tl(page)).max) await page.click("#fwd");
    await page.click("#toend"); await page.waitForTimeout(1000);
    await page.click("#back");
    const samp = await sample();
    await page.click("#back");
    await page.waitForTimeout(500);
    const g1 = await gpu(page);
    log(`  ▶ from the start: ${sf.distinct.toFixed(1)} distinct frames/s, ${sf.raf.toFixed(1)} animation frames/s, longest gap ${sf.worst_ms} ms`);
    log(`  ◀ from the end: ${samp.distinct.toFixed(1)} distinct frames/s, ${samp.raf.toFixed(1)} animation frames/s, longest gap ${samp.worst_ms} ms` + (g0 ? `; GPU objects before ${JSON.stringify(g0)} after ${JSON.stringify(g1)}` : ""));
    if (errs.length) log("  page errors: " + errs.slice(0, 5).join(" | "));
    await post(`/api/runs/${r.id}/stop`, {});
  } catch (e) {
    log(`${viz}: ERROR ${e.message}`);
  }
  await page.close();
}
fs.writeFileSync(`${OUT}/c03_player_history.txt`, lines.join("\n") + "\n");
await browser.close();
