// Response to the C1 review (rerun of the reviewer's c06_checks_at_cursor on the processed code, port 8501), check 06: the checks panel at the cursor. The player keeps ONE version of each check (a Map by id, the
// latest) and hides it while the cursor is before that version's time. A check recomputed during the run (e.g. v04's
// periapsis, apoapsis, period per orbit) had an earlier value at the cursor's time: is it shown?
// The record is parsed here (u32 length | u32 json length | JSON ...) to list, for the cursor's time, every check id
// whose FIRST version is not later than the cursor; the panel's rows are compared with that list.
// Usage: RUN=<id of a recorded v04 run on 127.0.0.1:8501> node c1rev_c06.mjs   (own server only)
// Output: out/r06_checks_at_cursor.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8501";
const OUT = process.env.OUT || "/pw/c1rev_out";
const run = process.env.RUN;
const buf = Buffer.from(await (await fetch(`${base}/api/runs/${run}/stream`)).arrayBuffer());
let pos = 8; const msgs = [];
while (pos + 4 <= buf.length) {
  const n = buf.readUInt32LE(pos); if (pos + 4 + n > buf.length) break;
  const jl = buf.readUInt32LE(pos + 4);
  msgs.push(JSON.parse(buf.subarray(pos + 8, pos + 8 + jl).toString("utf8")));
  pos += 4 + n;
}
const frames = msgs.filter((m) => m.type === "frame").map((m) => m.t);
const checks = msgs.filter((m) => m.type === "check");
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
await page.goto(`${base}/run?id=${run}`);
// wait for the whole record (history_end): the status leaves «загрузка записи…» and the timeline stops growing
for (let k = 0, last = -1; k < 120; k++) {
  await page.waitForTimeout(500);
  const s = await page.evaluate(() => [document.getElementById("status").textContent, +document.getElementById("timeline").max]);
  if (!/загрузка/.test(s[0]) && s[1] === last) break;
  last = s[1];
}
const lines = [];
const max = await page.evaluate(() => +document.getElementById("timeline").max);
for (const frac of [0.25, 0.5, 0.75, 1.0]) {
  const i = Math.round(frac * max);
  await page.evaluate((i) => { const t = document.getElementById("timeline"); t.value = String(i); t.dispatchEvent(new Event("input")); }, i);
  await page.waitForTimeout(1200);
  const t = frames[Math.min(i, frames.length - 1)];
  const existed = new Map();
  for (const c of checks) if ((c.t ?? 0) <= t * (1 + 1e-12)) existed.set(c.id, c);
  const shown = await page.evaluate(() => [...document.querySelectorAll(".checks tr")].filter((r) => r.children.length === 3).map((r) => r.children[0].childNodes[0].textContent));
  const label = await page.evaluate(() => document.getElementById("time").textContent);
  const missing = [...existed.values()].filter((c) => !shown.includes(c.label)).map((c) => `${c.id} «${c.label}» (value then ${c.value})`);
  lines.push(`cursor at frame ${i}/${max} (record t = ${t}; player ${label}): checks computed by then ${existed.size}, rows shown ${shown.length}; missing: ${missing.length ? missing.join("; ") : "none"}`);
}
fs.writeFileSync(`${OUT}/r06_checks_at_cursor.txt`, `run ${run} (frames in the record ${frames.length}; the player may thin them)\n` + lines.join("\n") + "\n");
console.log(lines.join("\n"));
await browser.close();
