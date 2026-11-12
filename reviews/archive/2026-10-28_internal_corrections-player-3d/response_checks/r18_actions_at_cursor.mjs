// Response to the C1 review, check for C1-18: the live action forms follow the cursor. v01 (default scenario): record,
// boost a movable object to 0.5 c at t1, record on; in the player the boost form's value for that object at the end and
// at a cursor before t1. Own server 127.0.0.1:8501 (processed code). Output: out/r18_actions_at_cursor.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8501";
const OUT = process.env.OUT || "/pw/c1proc_out";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b ?? {}) })).json();
const getj = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const lines = [];
const log = (s) => { lines.push(s); console.log(s); };
const r = await post("/api/runs", { viz: "v01_light_travel", seed: 3 });
await post(`/api/runs/${r.id}/command`, { cmd: "play" });
await sleep(2500);
await post(`/api/runs/${r.id}/command`, { cmd: "pause" });
await sleep(500);
const stream = Buffer.from(await (await fetch(`${base}/api/runs/${r.id}/stream`)).arrayBuffer());
let pos = 8, header = null;
while (pos + 4 <= stream.length) { const n = stream.readUInt32LE(pos); const jl = stream.readUInt32LE(pos + 4); const m = JSON.parse(stream.subarray(pos + 8, pos + 8 + jl).toString("utf8")); if (m.type === "header") { header = m; break; } pos += 4 + n; }
const boost = header.actions.find((a) => a.name === "boost");
const obj = boost.args.find((x) => x.id === "obj").options[0].value;
const t1 = (await getj(`/api/runs/${r.id}`)).sim_t;
await post(`/api/runs/${r.id}/command`, { cmd: "action", args: { name: "boost", args: { obj, v: 0.5, angle: 0 } } });
await post(`/api/runs/${r.id}/command`, { cmd: "play" });
await sleep(2500);
await post(`/api/runs/${r.id}/command`, { cmd: "pause" });
log(`v01 run ${r.id}: boost of ${obj} to 0.5 c at t1 = ${t1}`);
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-accelerated-2d-canvas"] });
const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });
await page.goto(`${base}/run?id=${r.id}`);
await page.waitForTimeout(4000);
const form = () => page.evaluate(() => {
  const a = [...document.querySelectorAll(".action")].find((x) => /Скорость/.test(x.textContent));
  return { time: document.getElementById("time").textContent, values: a ? [...a.querySelectorAll("input")].map((i) => i.value) : null, disabled: a ? [...a.querySelectorAll("input,select")].every((i) => i.disabled) : null };
});
log(`at the end: ${JSON.stringify(await form())}`);
await page.evaluate(() => { const t = document.getElementById("timeline"); t.value = "2"; t.dispatchEvent(new Event("input")); });
await page.waitForTimeout(1500);
log(`cursor at frame 2 (before t1): ${JSON.stringify(await form())}`);
await page.click("#toend"); await page.waitForTimeout(1500);
log(`back at the end: ${JSON.stringify(await form())}`);
await post(`/api/runs/${r.id}/stop`);
fs.writeFileSync(`${OUT}/r18_actions_at_cursor.txt`, lines.join("\n") + "\n");
await browser.close();
