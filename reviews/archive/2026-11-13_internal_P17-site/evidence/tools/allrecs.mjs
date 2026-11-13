// Play every recording of the built site under its sub-path: load, frames vs index, poster frame time, errors.
import { chromium } from "playwright";
const ROOT = process.argv[2];
const only = process.argv[3] ? new Set(process.argv[3].split(",")) : null;
const SHOTS = process.env.SHOTS || "";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const idx = (await (await fetch(ROOT + "api/recordings.json")).json()).worlds;
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const ctx = await br.newContext({ viewport: { width: 1280, height: 860 } });
const PREFIX = new URL(ROOT).pathname;
let bad = 0;
const list = [];
for (const [w, ix] of Object.entries(idx)) for (const r of ix.recordings) list.push([w, r]);
list.push(["v04_orbits", { id: "rosette", alias: true }]);
list.push(["u34_orbits", { id: "nope", missing: true }]);
for (const [w, r] of list) {
  if (only && !only.has(w)) continue;
  const page = await ctx.newPage();
  const errs = [], fails = [], outside = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 160)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 160)); });
  page.on("response", (x) => { if (x.status() >= 400) fails.push(`${x.status()} ${x.url()}`); });
  page.on("request", (x) => { const u = new URL(x.url()); if (!["data:", "blob:"].includes(u.protocol) && !u.pathname.startsWith(PREFIX)) outside.push(x.url()); });
  const t0 = Date.now();
  await page.goto(`${ROOT}run.html?rec=${w}/${r.id}&lang=en`);
  let loaded = true;
  try {
    await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: r.missing ? 8000 : 180000 });
  } catch { loaded = false; }
  const out = { rec: `${w}/${r.id}`, loaded, ms: Date.now() - t0 };
  if (loaded) {
    out.frames = await page.evaluate(() => window.__lfPlayer.frames());
    out.want = r.frames;
    if (r.poster_frame !== undefined) {
      await page.evaluate((i) => window.__lfPlayer.goTo(i), r.poster_frame);
      await sleep(300);
      out.t = await page.evaluate(() => window.__lfPlayer.t());
      out.poster_t = r.poster_t;
    }
  } else {
    out.text = (await page.evaluate(() => document.body.innerText)).slice(0, 300);
  }
  out.errs = errs.slice(0, 3); out.fails = fails.slice(0, 3); out.outside = outside.slice(0, 3);
  const ok = (r.missing ? !loaded : loaded && (r.alias || out.frames === out.want)) && !errs.length && !fails.length && !outside.length;
  if (!ok) bad++;
  out.ok = ok;
  if (SHOTS && (r.shot || ["u32_double_slit/young", "u38_wave_3d/double", "r12_double_slit_2d/narrow"].includes(`${w}/${r.id}`)))
    await page.screenshot({ path: `${SHOTS}/rec_${w}_${r.id}.png` });
  console.log(JSON.stringify(out));
  await page.close();
}
await br.close();
console.log(bad ? `${bad} not ok` : "all ok");
