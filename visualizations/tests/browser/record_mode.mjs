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
//  - (server) «▶ Compute this scenario live» is offered; an unknown recording says «No such recording» with a link to the
//    start page instead of a blank page (integrator D4);
//  - the tab's title «… · recording» (integrator D1); the help (?) describes a recording, not a live run (review F4);
//  - a view's own speed buttons (u32, u35, u37) change the player's speed (review P17-start-page F2);
//  - an old id (?rec=v04_orbits/…) plays (the README promises it);
//  - English: no Cyrillic on the page;
//  - at 390 px (a phone; integrator D8): no horizontal scroll, the badge whole inside the top bar, the view first, the
//    canvas not blank, no page or console errors (NARROW=0 skips this pass);
//  - NOREC_PORT=<port of a second private server with an empty LFVIZ_RECORDINGS and an unpublished site>: a scenario that
//    has a recording spec but no recording says «No recording yet…» (integrator D4).
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
// (clip: only that part of the window — at 390 px the view is taller than the screen, and the part on the first screen
// is what counts)
async function notBlank(page, clip = null) {
  const png = clip ? await page.screenshot({ clip, timeout: 90000 }) : await page.locator("#center").screenshot({ timeout: 90000 });
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
  // not vacuous (review F14): a world with live parameters shows them, every one disabled
  const vz = await get(`/api/viz/${rec.split("/")[0]}`);
  const nLive = (vz.schema.params || []).filter((p) => p.live).length;
  check(`${rec}: the set-up is read-only`, ui.ctlDisabled && (nLive === 0 || ui.nCtl > 0), { n: ui.nCtl, nLive });
  const title = await page.title();
  check(`${rec}: the tab's title says «recording»`, title === tr("{title} · recording", { title: tr(vz.title) }), { title });
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
  // a view's own speed buttons («▷ flight», «▷▷ build-up» …) act on the player's speed (F2)
  const speedBtns = [];
  for (const b of await page.$$("#center button")) if (/^▷/.test(((await b.textContent()) || "").trim())) speedBtns.push(b);
  if (speedBtns.length) {
    let changed = 0;
    for (const b of speedBtns) {
      const s0 = await page.$eval("#speedv", (e) => e.textContent);
      await b.click();
      await sleep(200);
      if ((await page.$eval("#speedv", (e) => e.textContent)) !== s0) changed++;
    }
    check(`${rec}: a view's own speed buttons change the player's speed`, changed >= 1, { buttons: speedBtns.length, changed });
  }
  // a view's own action buttons (u34 push/brake/launch, u37 reset) are off with the reason (F2, STATUS V51 (f))
  const ACTION_BUTTONS = { u34_orbits: 3, u37_bell_test: 1 };
  const nAct = ACTION_BUTTONS[rec.split("/")[0]];
  if (nAct) {
    const off = await page.$$eval("#center button", (a, why) => a.filter((b) => b.disabled && b.title === why).length, tr("a recording: this needs a live run"));
    check(`${rec}: the view's action buttons are disabled with the reason`, off >= nAct, { off, want: nAct });
  }
  // the help describes the recording, not a live run
  await page.keyboard.press("?");
  await page.waitForSelector(".modal", { timeout: 5000 }).catch(() => null);
  const help = await page.evaluate(() => (document.querySelector(".modal") || {}).innerText || "");
  const want = tr("This is a recording: a real run of this world, made by the recorder from the world's code and saved to a file (the badge at the top gives its date and code). It plays in the browser without computing anything.");
  check(`${rec}: the help describes a recording`, help.includes(want.slice(0, 40)) && !help.includes("⏺"), { help: help.slice(0, 160) });
  await page.keyboard.press("Escape");
  await page.screenshot({ path: `${SHOTS}/record_${rec.replace("/", "_")}_${LANG}.png` });
  check(`${rec}: no page errors`, !errs.length, { errs });
  await ctx.close();
}

// a phone (integrator D8): every recording at 390 × 844
if (process.env.NARROW !== "0") {
  for (const rec of RECS) {
    const ctx = await br.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
    page.on("console", (m) => { if (m.type() === "error") errs.push(m.text().slice(0, 200)); });
    await page.goto(inLang(`${base}/run?rec=${rec}`));
    try {
      await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
    } catch (e) { check(`390 px ${rec}: the recording loads`, false, { error: e.message.slice(0, 200), errs }); await ctx.close(); continue; }
    await sleep(2000);
    const o = await page.evaluate(() => {
      const b = document.getElementById("recbadge"), r = b.getBoundingClientRect(), bar = document.querySelector(".topbar").getBoundingClientRect();
      const c = document.getElementById("center").getBoundingClientRect();
      return { sw: document.scrollingElement.scrollWidth, w: innerWidth, badge: [Math.round(r.left), Math.round(r.right)], full: b.scrollWidth <= b.clientWidth + 1,
               inBar: r.top >= bar.top && r.bottom <= bar.bottom && r.left >= 0 && r.right <= innerWidth, center: [Math.round(c.width), Math.round(c.height), Math.round(c.top)] };
    });
    check(`390 px ${rec}: no horizontal scroll`, o.sw <= o.w + 1, o);
    check(`390 px ${rec}: the badge whole, inside the top bar`, o.inBar && o.full, o);
    check(`390 px ${rec}: the view first, at least 300 px high`, o.center[1] >= 300 && o.center[2] < 200, o);
    // the picture itself first: the first canvas starts within 60 px of the view's top (its own control rows under it)
    const firstCanvas = await page.evaluate(() => { const c = document.querySelector("#center canvas"); const r = c.getBoundingClientRect();
      return Math.round(r.top - document.getElementById("center").getBoundingClientRect().top); });
    check(`390 px ${rec}: the picture before the view's own controls`, firstCanvas <= 60, { firstCanvas });
    // paused for the picture: a heavy view on a software renderer (swiftshader) may not hand over a frame while it plays
    await page.evaluate(() => { const b = document.getElementById("fwd"); if (b.textContent === "⏸") b.click(); });
    await sleep(300);
    const bottom = await page.$eval(".bottombar", (e) => e.getBoundingClientRect().top);
    const nb = await notBlank(page, { x: 0, y: o.center[2], width: 390, height: Math.max(50, Math.min(o.center[1], bottom - o.center[2])) });
    check(`390 px ${rec}: the canvas on the first screen is not blank`, nb.share > 0.002 && nb.colours > 3, nb);
    check(`390 px ${rec}: no page or console errors`, !errs.length, { errs: [...new Set(errs)].slice(0, 3) });
    await page.screenshot({ path: `${SHOTS}/record_${rec.replace("/", "_")}_${LANG}_390.png`, timeout: 90000 });
    await ctx.close();
  }
}

// an old id (the README's old links, ?rec=v04_orbits/…) plays as its new world
if (all.worlds && all.worlds.u34_orbits) {
  const r0 = all.worlds.u34_orbits.recordings[0].id;
  const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  await page.goto(inLang(`${base}/run?rec=v04_orbits/${r0}`));
  const ok = await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 60000 }).then(() => true, () => false);
  check(`the old id v04_orbits/${r0} plays`, ok && !!(await page.$("#recbadge")));
  await ctx.close();
}

// an unknown recording (a mistyped scenario or world): «No such recording», with the way back to the start page (D4)
for (const bad of ["u32_double_slit/no_such_recording", "no_such_world/young", "u32_double_slit"]) {
  const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  await page.goto(inLang(`${base}/run?rec=${bad}`));
  await page.waitForSelector(".page h2", { timeout: 30000 });
  const s = await page.evaluate(() => ({ text: document.body.innerText, home: [...document.querySelectorAll(".page a")].some((a) => a.getAttribute("href").startsWith("/")) }));
  check(`?rec=${bad}: «No such recording», a link to the start page`, s.text.includes(tr("No such recording")) && s.home, { text: s.text.slice(0, 200) });
  await ctx.close();
}

// a server without recordings, the site unpublished (every fresh clone): the real reason, and the live way (D4)
if (process.env.NOREC_PORT) {
  const nb = `http://127.0.0.1:${process.env.NOREC_PORT}`;
  const ctx = await br.newContext({ viewport: { width: 1280, height: 800 } });
  const page = await ctx.newPage();
  await page.goto(inLang(`${nb}/run?rec=u32_double_slit/young`));
  await page.waitForSelector(".page h2", { timeout: 30000 });
  const s = await page.evaluate(() => ({ text: document.body.innerText, live: !!document.querySelector(".page button.primary") }));
  check("no local recording, site unpublished: «No recording yet…» and «▶ Compute this scenario live»",
    s.text.includes(tr("No recording yet: record it locally (site/record.py) or compute live")) && s.live, { text: s.text.slice(0, 200) });
  await ctx.close();
}

await br.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
