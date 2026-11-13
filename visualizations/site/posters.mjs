// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The posters of the worlds (design of the start page §5.1, §5.3): docs/images/<id>.jpg, JPEG, 1200 px wide, at most
// 150 kB, for the README and the start page's cards.
//
// A demonstration's poster is the poster frame (index.json: poster_frame) of its first recording, played by the player
// on a PRIVATE server that serves the local recordings (/run?rec=<world>/<rec>); a laboratory has no recordings, so its
// poster is taken from a live run of one of its scenarios (LAB_PRESET, else its first) after a few seconds of computing. Only the centre view is
// taken, with both side columns folded. A picture is made again only when its recording's key changed (kept in
// docs/images/posters.json), or with --force.
//
// Run with Playwright's image and a playwright package next to the script (ES modules resolve packages from the
// script's folder), against a server with LFVIZ_RECORDINGS set (never the shared one on 8479):
//   docker run --rm --init --shm-size=2g --network host --memory=4g -v <dir with node_modules/playwright@1.58.2>:/pw \
//     -v <repo>/docs/images:/images -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp <repo>/visualizations/site/posters.mjs /pw/ && node /pw/posters.mjs 8678 /images [--force] [--only a,b]
//     [--run p04_fluids:<run id>]"
// Prints one JSON line per world; exit code 1 when a poster could not be made or is over 400 kB.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
const port = args[0] || "8678";
const dir = args[1] || "/images";
const force = args.includes("--force");
const onlyArg = args.indexOf("--only");
const only = onlyArg >= 0 ? new Set(args[onlyArg + 1].split(",")) : null;
// --run <lab>:<run id>: a laboratory's poster from a run already computed on this server (one that reached LAB_T, e.g.
// computed earlier or on the GPU); the run is left as it is
const fromRun = Object.fromEntries(args.flatMap((a, i) => (a === "--run" ? [args[i + 1].split(":")] : [])));
const base = `http://127.0.0.1:${port}`;
const WIDTH = 1200, HEIGHT = 720, TARGET = 150_000, LIMIT = 400_000, LIVE_SECONDS = 8;
// a laboratory's scenario for its poster (the ones its README pictures showed before 2026-11-13); else its first
const LAB_PRESET = { p01_gravity: "inner", p02_quantum: "double_slit", p03_molecules: "maxwell", p04_fluids: "karman" };
const LAB_SECONDS = { p02_quantum: 20, p03_molecules: 20 };  // wall seconds of computing on the CPU
// or the world time to reach (seconds), when the phenomenon needs it: the Kármán street of p04 behind the cylinder
// (Re = 100, D = 0.1 m, mean inflow 1 m/s) is shed from about t = 3 s and its dye fills the channel by t ≈ 6 s; the CPU
// computes about 0.005 s of it per wall second (2026-11-13), so this takes about 20 minutes
const LAB_T = { p04_fluids: 6.0 };
const LAB_T_TIMEOUT = 45 * 60 * 1000;
const presetIds = (v) => (v.schema.presets || []).map((p) => p.id);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const get = async (u) => (await fetch(base + u)).json();
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify(b || {}) })).json();
const settle = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 600)))));

async function until(page, fn, ms, what, arg) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    if (await page.evaluate(fn, arg).catch(() => false)) return;
    await sleep(250);
  }
  throw new Error(`timeout: ${what}`);
}

async function fold(page) {  // only the centre view: both side columns folded
  await page.evaluate(() => {
    const app = document.getElementById("app");
    for (const side of ["left", "right"]) if (!app.classList.contains(`fold-${side}`)) document.getElementById(`fold-${side}`).click();
  });
}

async function shoot(page, file) {  // the centre view as JPEG, the quality lowered until it fits the target
  await fold(page);
  await page.evaluate(() => window.__lfPlayer && window.__lfPlayer.redraw());
  await settle(page);
  const el = page.locator("#center");
  let buf = null, q = 85;
  for (; q >= 35; q -= 10) {
    buf = await el.screenshot({ type: "jpeg", quality: q });
    if (buf.length <= TARGET) break;
  }
  fs.writeFileSync(file, buf);
  const box = await el.boundingBox();
  return { bytes: buf.length, quality: q, width: Math.round(box.width), height: Math.round(box.height) };
}

const catalogue = await get("/api/viz");
const recs = (await get("/api/recordings")).worlds || {};
const metaFile = path.join(dir, "posters.json");
let meta = {};
try { meta = JSON.parse(fs.readFileSync(metaFile, "utf8")); } catch { meta = {}; }

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: WIDTH, height: HEIGHT }, deviceScaleFactor: 1, locale: "en-US",
  colorScheme: "light" });
let failed = 0;
for (const v of catalogue) {
  if (only && !only.has(v.id)) continue;
  const file = path.join(dir, `${v.id}.jpg`);
  const page = await ctx.newPage();
  const out = { id: v.id };
  try {
    if (v.kind === "playground") {
      const ids = presetIds(v);
      const preset = ids.includes(LAB_PRESET[v.id]) ? LAB_PRESET[v.id] : (ids[0] || null);
      const key = `live:${v.version}:${preset || ""}` + (LAB_T[v.id] ? `:t${LAB_T[v.id]}` : "");
      if (!force && meta[v.id] && meta[v.id].key === key && fs.existsSync(file)) { out.skipped = "same key"; continue; }
      const given = fromRun[v.id];
      const run = given ? { id: given } : await post("/api/runs", { viz: v.id, preset, label: "poster" });
      if (!run.id) throw new Error(`run not started: ${JSON.stringify(run)}`);
      await page.goto(`${base}/run?id=${run.id}&lang=en`);
      await until(page, () => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, 600000, "the world's first frame");
      if (given) {
        const meta = await get(`/api/runs/${run.id}`);
        if (meta.viz !== v.id || (meta.preset || null) !== preset) throw new Error(`run ${run.id} is not ${v.id}/${preset}`);
        if (LAB_T[v.id] && !((await page.evaluate(() => window.__lfPlayer.t())) >= LAB_T[v.id])) throw new Error(`run ${run.id} has not reached ${LAB_T[v.id]} s`);
        if (meta.playing) { await page.click("#rec"); await sleep(800); }  // paused where it is
      } else {
        await page.click("#rec");  // compute a few seconds, or until the world's time shows the phenomenon
        if (LAB_T[v.id]) await until(page, (tt) => window.__lfPlayer.t() >= tt, LAB_T_TIMEOUT, `the world's time ${LAB_T[v.id]} s`, LAB_T[v.id]);
        else await sleep((LAB_SECONDS[v.id] || LIVE_SECONDS) * 1000);
        await page.click("#rec");
        await sleep(800);
      }
      Object.assign(out, await shoot(page, file), { key, from: `live run ${run.id}, preset ${preset}`, t: await page.evaluate(() => window.__lfPlayer.t()) });
      if (!given) await fetch(`${base}/api/runs/${run.id}`, { method: "DELETE" }).catch(() => {});
    } else {
      const idx = recs[v.id];
      const spec = (v.recordings || [])[0];
      const rec = idx && spec && (idx.recordings || []).find((r) => r.id === spec.id);
      if (!rec) throw new Error("no local recording of its first spec (site/record.py)");
      if (!force && meta[v.id] && meta[v.id].key === rec.key && fs.existsSync(file)) { out.skipped = "same key"; continue; }
      await page.goto(`${base}/run?rec=${v.id}/${rec.id}&lang=en`);
      await until(page, () => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, 180000, "the recording loaded");
      await page.evaluate((i) => window.__lfPlayer.goTo(i), rec.poster_frame);
      await sleep(500);
      Object.assign(out, await shoot(page, file), { key: rec.key, from: `${v.id}/${rec.id}`, poster_frame: rec.poster_frame,
        t: await page.evaluate(() => window.__lfPlayer.t()) });
    }
    if (out.bytes > LIMIT) { failed++; out.error = `over ${LIMIT} bytes`; }
    meta[v.id] = { key: out.key, from: out.from, bytes: out.bytes, width: out.width, quality: out.quality };
  } catch (e) {
    failed++;
    out.error = String(e && e.message || e);
  } finally {
    console.log(JSON.stringify(out));
    await page.close();
  }
}
await browser.close();
fs.writeFileSync(metaFile, JSON.stringify(Object.fromEntries(Object.entries(meta).sort()), null, 1) + "\n");
process.exit(failed ? 1 : 0);
