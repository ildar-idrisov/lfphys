// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The player on a saved recording (/run?rec=<world>/<rec>; DESIGN of the start page §1.7, §4.5), in a browser, for the
// language in LFVIZ_LANG (en by default), on every local recording the server lists (GET /api/recordings) or the ones
// given:
//  - the recording loads and plays by itself: the timeline moves, the world time grows, the canvas is not blank;
//  - the badge «RECORDING · date · code»; ⏺, «Keep» (☆) and ⚙ are absent; nothing is sent to a server (no WebSocket);
//  - the checks appear where the world computes any; the set-up is read-only;
//  - a world with slice planes: «＋ Slice» is disabled with the reason «a recording: this needs a live run»;
//  - a world with measurable quantities: the CSV is built in the browser and downloads, its header says it is from the
//    recording; the sweeps are absent;
//  - (server) «▶ Compute this scenario live» is offered; an unknown recording says why instead of a blank page;
//  - English: no Cyrillic on the page.
//
// Run against a PRIVATE server (never the shared one on 8479) with recordings in LFVIZ_RECORDINGS, e.g. the test
// world's: python tests/make_record_fixture.py --frames 400 --out <scratch>/recordings (and site/record.py for others):
//   docker run -d --name lf-rec-srv --memory=6g -p 8679:8479 -v <repo>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
//     -v <scratch>/recordings:/recs:ro -e LFVIZ_RECORDINGS=/recs -e LFPHYS_NO_GPU=1 \
//     -e LFVIZ_EXTRA=/lf/visualizations/tests/playgrounds:/lf/visualizations/tests/instruments_worlds \
//     -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 3
//   docker run --rm --init --shm-size=2g --network host --memory=4g -e LFVIZ_LANG=en -v <dir with node_modules/playwright>:/pw \
//     -v <repo>/visualizations/tests/browser:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp /t/*.mjs /pw/ && node /pw/record_mode.mjs 8679 [world/rec,...]"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync, readFileSync } from "node:fs";
import { inLang, LANG, loadI18n } from "./lfi18n.mjs";

const port = process.argv[2] || "8679";
const base = `http://127.0.0.1:${port}`;
const SHOTS = process.env.SHOTS || "/pw/shots";
mkdirSync(SHOTS, { recursive: true });
const CYR = /[Ѐ-ӿ]/;  // i18n-ok: recognises Cyrillic
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: `${LANG} ${name}`, ok: !!ok, ...info })); };
const get = async (u) => (await fetch(base + u)).json();
const { t: tr } = await loadI18n(base);  // what the page shows, in the language under test

const all = await get("/api/recordings");
const RECS = process.argv[3] ? process.argv[3].split(",")
  : Object.entries(all.worlds || {}).map(([w, ix]) => `${w}/${(ix.recordings || [])[0]?.id}`).filter((x) => !x.endsWith("/undefined"));
check("there are recordings to play", RECS.length > 0, { recs: RECS });

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });

// the share of the picture's pixels that differ from its most common colour (a blank canvas: 0)
async function notBlank(page) {
  const png = await page.locator("#center").screenshot();
  return page.evaluate(async (b64) => {
    const img = new Image();
    img.src = "data:image/png;base64," + b64;
    await img.decode();
    const c = document.createElement("canvas");
    c.width = img.width; c.height = img.height;
    const g = c.getContext("2d");
    g.drawImage(img, 0, 0);
    const d = g.getImageData(0, 0, c.width, c.height).data, n = new Map();
    for (let i = 0; i < d.length; i += 16) { const k = (d[i] >> 3) << 10 | (d[i + 1] >> 3) << 5 | (d[i + 2] >> 3); n.set(k, (n.get(k) || 0) + 1); }
    const tot = d.length / 16, top = Math.max(...n.values());
    return { share: 1 - top / tot, colours: n.size };
  }, png.toString("base64"));
}

for (const rec of RECS) {
  const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 }, acceptDownloads: true });
  const page = await ctx.newPage();
  const errs = [], sockets = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("websocket", (ws) => sockets.push(ws.url()));
  await page.goto(inLang(`${base}/run?rec=${rec}`));
  try {
    await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
  } catch (e) { check(`${rec}: the recording loads`, false, { error: e.message.slice(0, 200), errs }); await ctx.close(); continue; }
  const t0 = await page.evaluate(() => window.__lfPlayer.t());
  const tl0 = await page.$eval("#timeline", (e) => Number(e.value));
  await sleep(2500);
  const t1 = await page.evaluate(() => window.__lfPlayer.t());
  const tl1 = await page.$eval("#timeline", (e) => Number(e.value));
  check(`${rec}: it plays by itself (the timeline moves, the world time grows)`, t1 > t0 && tl1 > tl0, { t0, t1, tl0, tl1 });
  const ui = await page.evaluate(() => ({
    badge: document.getElementById("recbadge")?.textContent || "",
    rec: getComputedStyle(document.getElementById("rec")).display, keep: getComputedStyle(document.getElementById("keep")).display,
    gear: !!document.querySelector('.topbar a[data-page="settings"]'),
    live: !!document.querySelector(".rec-note button.primary"),
    status: document.getElementById("status").textContent,
    checks: document.querySelectorAll(".checks td.ck-st").length,
    ctlDisabled: [...document.querySelectorAll("#left .ctl input, #left .ctl select")].every((e) => e.disabled),
    nCtl: document.querySelectorAll("#left .ctl input, #left .ctl select").length,
    lang: document.documentElement.lang, text: document.body.innerText,
  }));
  check(`${rec}: the badge «RECORDING · date · code»`, ui.badge.startsWith(tr("RECORDING · {date} · code {code}").split(" · ")[0]) && /\d{4}-\d\d-\d\d/.test(ui.badge), { badge: ui.badge });
  check(`${rec}: ⏺, «Keep» and ⚙ are absent`, ui.rec === "none" && ui.keep === "none" && !ui.gear, ui);
  check(`${rec}: nothing is sent to a server (no WebSocket)`, sockets.length === 0, { sockets });
  check(`${rec}: «▶ Compute this scenario live» is offered (server)`, ui.live);
  check(`${rec}: the set-up is read-only`, ui.ctlDisabled, { n: ui.nCtl });
  // the checks the record holds up to the cursor; a world that computes none says so
  const none = await page.evaluate((msg) => (document.querySelector(".checks")?.textContent || "").includes(msg), tr("No checks up to this moment of the recording."));
  const recChecks = await page.evaluate(() => window.__lfPlayer.t());  // (the cursor's time, for the report)
  check(`${rec}: the checks are shown (or said to be none)`, ui.checks > 0 || none, { checks: ui.checks, none, t: recChecks });
  const nb = await notBlank(page);
  check(`${rec}: the canvas is not blank`, nb.share > 0.002 && nb.colours > 3, nb);
  if (LANG === "en") check(`${rec}: no Cyrillic`, !CYR.test(ui.text), { sample: ui.text.split("\n").filter((s) => CYR.test(s)).slice(0, 4) });
  // a world with slice planes: adding one needs a live run
  const add = await page.$(".s3d-tools button.primary");
  if (add) {
    const a = await add.evaluate((e) => ({ disabled: e.disabled, title: e.title }));
    check(`${rec}: «＋ Slice» is disabled with the reason`, a.disabled && a.title === tr("a recording: this needs a live run"), a);
  }
  // the instruments: the CSV made in the browser, no sweeps
  const q = await page.$(".in-panel .in-q input[type=checkbox]");
  if (q) {
    await page.evaluate(() => { const p = document.querySelector(".in-panel"); if (p.classList.contains("closed")) p.querySelector("h4").click(); });
    if (!(await q.isChecked())) await q.check();
    const [dl] = await Promise.all([page.waitForEvent("download", { timeout: 15000 }), page.click(".in-panel a.in-csv")]);
    const text = readFileSync(await dl.path(), "utf-8");
    const lines = text.trim().split(/\r?\n/);
    check(`${rec}: the CSV downloads, made in the browser from the recording`, lines.length > 5 && lines[0].includes(tr("t, {unit} (from the recording: every frame)").split(" (")[1].slice(0, 6)) && /^[0-9.e+-]+,/.test(lines[1]),
      { file: dl.suggestedFilename(), head: lines[0], rows: lines.length - 1 });
    check(`${rec}: no sweeps on a recording`, !(await page.$(".in-sweep-box")));
  }
  await page.screenshot({ path: `${SHOTS}/record_${rec.replace("/", "_")}_${LANG}.png` });
  check(`${rec}: no page errors`, !errs.length, { errs });
  await ctx.close();
}

// an unknown recording: said, not a blank page
{
  const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  await page.goto(inLang(`${base}/run?rec=u32_double_slit/no_such_recording`));
  await page.waitForSelector(".page h2", { timeout: 30000 });
  const txt = await page.evaluate(() => document.body.innerText);
  check("an unknown recording says why", txt.includes(tr("No recording for this version: record it locally or compute live")), { text: txt.slice(0, 300) });
  await ctx.close();
}

await br.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
