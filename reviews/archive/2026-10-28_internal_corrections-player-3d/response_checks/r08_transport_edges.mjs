// Response to the C1 review (rerun of the reviewer's c08_transport_edges on the processed code, port 8501), check 08: transport edge cases in the player (own server 127.0.0.1:8501, max_workers = 2).
//  (a) Space while the ⏺ button has the focus (after a click on it): one toggle or two?
//  (b) ← / → while the speed slider has the focus.
//  (c) ⏺ on a suspended run while both workers serve viewed runs: what the owner sees, and after a worker is free.
//  (d) a resume of a longer record: how long the owner waits and what is shown meanwhile.
// Output: out/r08_transport_edges.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8501";
const OUT = process.env.OUT || "/pw/c1rev_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const getj = async (u) => (await fetch(base + u)).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const ui = (page) => page.evaluate(() => ({
  rec: document.getElementById("rec").textContent, status: document.getElementById("status").textContent,
  busy: document.getElementById("busy").style.display !== "none" ? document.getElementById("busy").textContent : "",
  fwd: document.getElementById("fwd").textContent, back: document.getElementById("back").textContent,
  speed: document.getElementById("speedv").textContent, timeline: `${document.getElementById("timeline").value}/${document.getElementById("timeline").max}`,
  toasts: [...document.querySelectorAll(".toast")].map((t) => t.textContent.slice(0, 90)),
}));
async function open(id) {
  const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });
  await page.goto(base + "/run?id=" + id);
  await page.waitForTimeout(3000);
  return page;
}
// (a)
const A = await post("/api/runs", { viz: "v04_orbits", seed: 2 });
const pa = await open(A.id);
await pa.click("#rec"); await pa.waitForTimeout(3000); await pa.click("#rec"); await pa.waitForTimeout(1500);
let m = await getj(`/api/runs/${A.id}`);
log(`(a) after clicking ⏺ twice: server playing ${m.playing}; focus on #${await pa.evaluate(() => document.activeElement.id)}`);
await pa.keyboard.press("Space"); await pa.waitForTimeout(1500);
m = await getj(`/api/runs/${A.id}`);
log(`    one Space with the focus on ⏺: server playing ${m.playing} (expected true); commands logged since: ${m.commands.slice(-3).map((c) => c.cmd).join(", ")}`);
if (m.playing) { await pa.keyboard.press("Space"); await pa.waitForTimeout(1000); }
m = await getj(`/api/runs/${A.id}`);
log(`    state now: playing ${m.playing}`);
// (b)
await pa.click("#speed"); await pa.waitForTimeout(300);
const s0 = await ui(pa);
await pa.keyboard.press("ArrowLeft"); await pa.waitForTimeout(1200);
const s1 = await ui(pa);
log(`(b) ← with the focus on the speed slider: speed ${s0.speed} -> ${s1.speed}; ◀ button ${s0.back} -> ${s1.back}; timeline ${s0.timeline} -> ${s1.timeline}`);
await pa.evaluate(() => document.getElementById("back").textContent === "⏸" && document.getElementById("back").click());
// (c) both workers busy with viewed runs, A suspended
await post(`/api/runs/${A.id}/stop`); await pa.waitForTimeout(2500);
const B = await post("/api/runs", { viz: "v01_light_travel" }), C = await post("/api/runs", { viz: "v01_light_travel" });
const pb = await open(B.id), pc = await open(C.id);
log(`(c) A ${(await getj(`/api/runs/${A.id}`)).state}, B ${(await getj(`/api/runs/${B.id}`)).state}, C ${(await getj(`/api/runs/${C.id}`)).state}`);
await pa.bringToFront();
await pa.click("#rec"); await pa.waitForTimeout(3000);
log(`    ⏺ on A: ${JSON.stringify(await ui(pa))}`);
await pa.waitForTimeout(10000);
log(`    13 s later: ${JSON.stringify(await ui(pa))}`);
await pb.close(); await pa.waitForTimeout(1500);
await pa.click("#rec"); await pa.waitForTimeout(6000);
log(`    B's tab closed, ⏺ on A again: ${JSON.stringify(await ui(pa))}; server: A ${(await getj(`/api/runs/${A.id}`)).state}`);
await pa.click("#rec").catch(() => {}); await pa.waitForTimeout(1000);
await pc.close();
await post(`/api/runs/${B.id}/stop`); await post(`/api/runs/${C.id}/stop`);
// (d) a longer record resumed: v04 at a high speed for 30 s, suspended, then ⏺
await pa.evaluate(() => { const s = document.getElementById("speed"); s.value = "900"; s.dispatchEvent(new Event("change")); });
await pa.click("#rec"); await pa.waitForTimeout(30000); await pa.click("#rec"); await pa.waitForTimeout(1500);
await post(`/api/runs/${A.id}/stop`); await pa.waitForTimeout(3000);
const before = await getj(`/api/runs/${A.id}`);
const t0 = Date.now();
await pa.click("#rec");
const seen = [];
for (let k = 0; k < 240; k++) {
  await pa.waitForTimeout(500);
  const u = await ui(pa);
  const key = `${u.rec}|${u.status}|${u.busy}`;
  if (!seen.length || seen[seen.length - 1][1] !== key) seen.push([((Date.now() - t0) / 1000).toFixed(1), key]);
  if (/запись идёт/.test(u.status)) break;
}
log(`(d) v04 record of ${before.n_messages} messages (sim_t ${before.sim_t}) resumed by ⏺; what the page showed (s since ⏺ | button | status | busy):`);
for (const [t, k] of seen) log(`    ${t} s: ${k}`);
await pa.click("#rec").catch(() => {}); await pa.waitForTimeout(1000);
await post(`/api/runs/${A.id}/stop`);
fs.writeFileSync(`${OUT}/r08_transport_edges.txt`, lines.join("\n") + "\n");
await browser.close();
