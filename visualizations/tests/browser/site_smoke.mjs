// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The smoke test of the built public site (DESIGN of the start page §5.2, §7 row I): the site as site/build.py writes
// it, served by Python's http.server from a parent folder so that it lives under a sub-path (/lfphys/), as on GitHub
// Pages. In every language given (EN and RU by default):
//  - no request leaves the sub-path (same origin, path under the base), none goes to an API (/api/, a WebSocket; the
//    site's api/*.json files are static), no request fails, no page error and no console error;
//  - the start page shows the four audiences in order, with their names; the site's note «recordings of real runs»;
//    no «My runs», no device settings;
//  - an audience page (#university) renders its cards, with recording links to run.html?rec=… under the base and no
//    «▶ Compute live»;
//  - a recording plays in run.html?rec=<world>/<rec>: the timeline moves and the world time grows, the badge is there,
//    the checks appear, the canvas is not blank;
//  - EVERY recording of api/recordings.json loads (review P17-site F5: a missing view, vendor or locale module shows up
//    only when its world is played): the frames the player holds are the index's «frames», going to «poster_frame»
//    shows «poster_t» (a recording of several worlds: it loads, with at most the index's frames; STATUS.md V52); an old id (aliases.json) plays too; an unknown recording id says so with a link to the start
//    page, not «No recording for this version» (integrator D4);
//  - the server's addresses on the site (start-page F12): run.html?id=… and a bare run.html say «This site plays
//    recordings; runs are computed by a local server», never a raw parse error or a server address «/run?id=…»;
//  - the laboratories are greyed: the tile and the cards marked off, nothing to start, the note «Works only with a
//    running server» with the way to the quick start;
//  - the school banner is honest: «Ready: k of n» with k the school worlds of api/viz.json and n = k + the school items
//    of api/planned.json; nothing startable;
//  - the screens (design lfphys/sources/explore_2026-11-14_design.md §3, §8 "site_smoke"): every card's screen buttons
//    link run.html?demo=<world>&screen=<id> under the base; EVERY screen of every world with screens opens on the site
//    (Watch: its recording and captions; Explore: its atlas's default point; Lab work: its first step's point), with no
//    request to the live endpoint; the worksheet page (worksheet.html?demo=…) renders a lab's worksheet;
//  - legal.html shows the full texts (each loaded, not empty) and the citation;
//  - English: no Cyrillic in the visible text of any page; Russian: the page is in Russian.
// The texts are compared in the language under test through the player's own i18n.js and the site's catalogue
// (static/locales/<lang>.json), so nothing Russian is written here.
//
//   node site_smoke.mjs <site URL, e.g. http://127.0.0.1:8000/lfphys/> [en,ru] [world/rec]
//
// With the site in _site (CI: .github/workflows/pages.yml):
//   docker run -d --name lf-site-srv --memory=512m -p 127.0.0.1:8000:8000 -v "$PWD/_site:/srv/lfphys:ro" -w /srv \
//     python:3.11-slim python3 -m http.server 8000
//   docker run --rm --init --shm-size=2g --network host --memory=4g -v <dir with node_modules/playwright>:/pw \
//     -v <repo>/visualizations/tests/browser:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp /t/*.mjs /pw/ && node /pw/site_smoke.mjs http://127.0.0.1:8000/lfphys/ en,ru"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1). SHOTS=<dir> keeps screenshots.
// ALL_RECS=0 plays only the one recording (a quick run); by default every recording is played in every language.
import { chromium } from "playwright";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const ROOT = (() => { const r = process.argv[2] || "http://127.0.0.1:8000/lfphys/"; return r.endsWith("/") ? r : r + "/"; })();
const LANGS = (process.argv[3] || "en,ru").split(",").map((s) => s.trim()).filter(Boolean);
const ORIGIN = new URL(ROOT).origin, PREFIX = new URL(ROOT).pathname;
const SHOTS = process.env.SHOTS || "";
if (SHOTS) mkdirSync(SHOTS, { recursive: true });
const CYR = /[Ѐ-ӿ]/;  // i18n-ok: recognises Cyrillic
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = 0, L = "";
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: `${L} ${name}`, ok: !!ok, ...info })); };
const getJSON = async (p) => { const r = await fetch(ROOT + p); if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); };

// the player's renderer with the site's catalogue of a language (what the page shows: tr(msgid, args))
const I = await (async () => {
  const dir = mkdtempSync(join(tmpdir(), "lfsmoke-"));
  writeFileSync(join(dir, "package.json"), '{"type": "module"}');
  for (const m of ["i18n.js", "base.js"]) {
    const r = await fetch(`${ROOT}static/js/${m}`);
    if (!r.ok) throw new Error(`static/js/${m}: ${r.status}`);
    writeFileSync(join(dir, m), await r.text());
  }
  return import(pathToFileURL(join(dir, "i18n.js")).href);
})();
const CATS = {};
for (const l of LANGS) CATS[l] = (await getJSON(`static/locales/${l}.json`)).messages || {};
const tr = (x, a) => I.t(x, a);

// the site's data, as the pages read it
const viz = (await getJSON("api/viz.json")).filter((v) => !v.error);
const planned = await getJSON("api/planned.json");
const recIndex = (await getJSON("api/recordings.json")).worlds || {};
const count = (aud) => viz.filter((v) => v.audience === aud).length;
// the recording to play: given, or the first of u34_orbits (light, with checks), or the smallest one there is
const REC = process.argv[4] || (() => {
  const all = Object.entries(recIndex).flatMap(([w, ix]) => (ix.recordings || []).map((r) => ({ w, r })));
  const pick = all.find((x) => x.w === "u34_orbits") || all.sort((a, b) => (a.r.bytes_gz || 0) - (b.r.bytes_gz || 0))[0];
  return pick ? `${pick.w}/${pick.r.id}` : "";
})();

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

for (const lang of LANGS) {
  L = lang;
  I.setCatalogue(lang, CATS[lang]);
  const ctx = await br.newContext({ viewport: { width: 1400, height: 950 }, locale: lang === "ru" ? "ru-RU" : "en-US" });
  let favicon = 0;  // the browser's own /favicon.ico requests (reported, not failed)
  const outside = [], apiCalls = [], bad = [], errs = [], consoleErrs = [], sockets = [];
  ctx.on("request", (r) => {
    const u = new URL(r.url());
    if (u.protocol === "data:" || u.protocol === "blob:") return;
    const rel = u.pathname.startsWith(PREFIX) ? u.pathname.slice(PREFIX.length) : "";
    if (u.pathname.startsWith("/api/") || (rel.startsWith("api/") && !rel.endsWith(".json"))) apiCalls.push(r.url());
    if (u.origin !== ORIGIN || !u.pathname.startsWith(PREFIX)) {
      // the browser's own favicon request is not the site's (no page asks for it)
      if (u.origin === ORIGIN && u.pathname === "/favicon.ico") favicon++; else outside.push(r.url());
    }
  });
  ctx.on("response", (r) => { if (r.status() >= 400 && new URL(r.url()).pathname !== "/favicon.ico") bad.push(`${r.status()} ${r.url()}`); });
  const open = async (path, wait) => {
    const page = await ctx.newPage();
    page.on("pageerror", (e) => errs.push(`${path}: ${e.message.slice(0, 200)}`));
    page.on("console", (m) => { if (m.type() === "error" && !/favicon\.ico/.test(m.location()?.url || "")) consoleErrs.push(`${path}: ${m.text().slice(0, 200)}`); });
    page.on("websocket", (ws) => sockets.push(ws.url()));
    await page.goto(ROOT + path + (path.includes("?") ? "&" : "?") + "lang=" + lang + (wait.hash ? "#" + wait.hash : ""));
    if (wait.selector) {
      try { await page.waitForSelector(wait.selector, { timeout: 60000 }); } catch (e) {  // said, and the checks go on
        check(`${path || "start"}${wait.hash ? "#" + wait.hash : ""}: the page renders (${wait.selector})`, false, { error: e.message.split("\n")[0], errs: errs.slice(-3) });
      }
    }
    await sleep(wait.ms ?? 600);
    return page;
  };
  const language = async (page, name) => {
    const s = await page.evaluate(() => ({ text: document.body.innerText, lang: document.documentElement.lang }));
    if (lang === "en") check(`${name}: no Cyrillic`, !CYR.test(s.text), { sample: s.text.split("\n").filter((x) => CYR.test(x)).slice(0, 4) });
    else check(`${name}: in the language`, s.lang === lang && (lang !== "ru" || CYR.test(s.text)), { lang: s.lang });
  };
  const shot = async (page, name, full = true) => { if (SHOTS) await page.screenshot({ path: `${SHOTS}/site_${name}_${lang}.png`, fullPage: full }); };

  // the start page
  {
    const page = await open("", { selector: ".st-tiles" });
    const s = await page.evaluate(() => ({
      tiles: [...document.querySelectorAll(".st-tile")].map((e) => ({ id: e.id, text: e.innerText, off: e.classList.contains("off") })),
      note: document.querySelector(".st-note")?.innerText || "",
      myruns: !!document.querySelector("#myruns"), settings: !!document.querySelector('a[data-page="settings"], a[href$="/settings"]'),
    }));
    check("start: the four audiences, in order", s.tiles.map((x) => x.id).join() === "tile-school,tile-university,tile-research,tile-labs", { tiles: s.tiles.map((x) => x.id) });
    check("start: the audiences' names", [tr("School"), tr("University"), tr("Research"), tr("Laboratories")].every((n, i) => s.tiles[i] && s.tiles[i].text.toLowerCase().includes(n.toLowerCase())),
      { tiles: s.tiles.map((x) => x.text.split("\n")[0]) });
    check("start: the note «recordings of real runs»", s.note.includes(tr("These are recordings of real runs: you can play them, go back and look at the checks. To compute live, change the set-up or use the laboratories, run lfphys on your computer (Docker).")), { note: s.note.slice(0, 160) });
    const labs = s.tiles[3] || {};
    check("start: the laboratories' tile greyed, «Works only with a running server»", labs.off && labs.text.includes(tr("Works only with a running server")), { labs: labs.text });
    check("start: no «My runs», no device settings", !s.myruns && !s.settings);
    await language(page, "start");
    await shot(page, "start");
    await page.close();
  }

  // an audience page
  {
    const page = await open("", { hash: "university", selector: ".st-head" });
    const s = await page.evaluate(() => ({
      cards: [...document.querySelectorAll(".st-card")].map((c) => c.id),
      live: document.querySelectorAll(".st-card button.primary").length,
      recs: [...document.querySelectorAll(".st-card a.button:not(.st-screen)")].map((a) => a.getAttribute("href")),
      screens: [...document.querySelectorAll(".st-card a.st-screen")].map((a) => a.getAttribute("href")),
      h1: document.querySelector(".st-head h1")?.innerText || "",
    }));
    check("#university: the heading", s.h1.toLowerCase().includes(tr("University").toLowerCase()), { h1: s.h1 });
    check("#university: a card per university world", s.cards.length === count("university") && s.cards.length > 0, { cards: s.cards.length, worlds: count("university") });
    check("#university: recording links under the base, no «▶ Compute live»", s.live === 0 && s.recs.length > 0
      && s.recs.every((h) => h && h.startsWith(`${PREFIX}run.html?rec=`)), { live: s.live, recs: s.recs.slice(0, 3) });
    const withScreens = viz.filter((v) => v.audience === "university" && (v.screens || []).length);
    check("#university: the screens' links under the base (run.html?demo=…&screen=…)", s.screens.length >= withScreens.length
      && s.screens.every((h) => h && new RegExp(`^${PREFIX}run\\.html\\?demo=\\w+&screen=\\w+`).test(h)), { screens: s.screens.slice(0, 4) });
    await language(page, "#university");
    await shot(page, "university");
    await page.close();
  }

  // the school: the honest banner
  {
    const page = await open("", { hash: "school", selector: ".st-head" });
    const k = count("school"), n = k + planned.filter((p) => p.audience === "school").length;
    const want = tr("Ready: {k:d} of {n:d}.", { k, n });
    const s = await page.evaluate(() => ({ ready: document.querySelector(".st-ready")?.innerText || "", startable: document.querySelectorAll(".st-card button.primary, .planned-card button").length }));
    check("#school: the banner «Ready: k of n» from the catalogue and the plan", s.ready.includes(want), { ready: s.ready.slice(0, 120), want });
    check("#school: nothing startable", s.startable === 0, s);
    await language(page, "#school");
    await page.close();
  }

  // the laboratories
  {
    const page = await open("", { hash: "labs", selector: ".st-head" });
    const s = await page.evaluate(() => ({
      warn: document.querySelector(".st-note.warn")?.innerText || "", how: document.querySelector(".st-note.warn a")?.getAttribute("href") || "",
      cards: document.querySelectorAll(".st-card").length, off: document.querySelectorAll(".st-card.off").length,
      buttons: document.querySelectorAll(".st-card button").length,
    }));
    check("#labs: greyed, nothing to start", s.cards === count("playground") && s.off === s.cards && s.buttons === 0, s);
    check("#labs: the note «Works only with a running server» with the quick start", s.warn.includes(tr("Works only with a running server:"))
      && /^https:\/\/github\.com\//.test(s.how), { warn: s.warn.slice(0, 120), how: s.how });
    await language(page, "#labs");
    await shot(page, "labs");
    await page.close();
  }

  // every screen of every world with screens, on the site (design of 2026-11-14 §3.8, §8)
  for (const v of viz.filter((x) => (x.screens || []).length)) {
    for (const sc of v.screens) {
      const page = await open(`run.html?demo=${v.id}&screen=${sc.id}`, { ms: 0 });
      const out = { screen: `${v.id}/${sc.id}` };
      try {
        await page.waitForFunction((id) => { const e = document.querySelector(`.dm-screen[data-screen="${id}"]`); return e && !e.hidden; }, sc.id, { timeout: 60000 });
        if (sc.kind === "watch") {
          await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 120000 });
          out.captions = await page.evaluate(() => window.__lfWatch.state.story.captions.length);
          out.ok = out.captions >= 1;
        } else if (sc.kind === "explore") {
          await page.waitForFunction((id) => window.__lfExplore && window.__lfExplore[id] && window.__lfExplore[id].point(), sc.id, { timeout: 60000 });
          out.point = await page.evaluate((id) => window.__lfExplore[id].point().i, sc.id);
          out.ok = out.point !== null && out.point !== undefined;
        } else {
          await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 60000 });
          out.ok = true;
        }
        await sleep(400);
        const nb = await page.evaluate(() => { const c = document.querySelector(".dm-screen:not([hidden]) canvas"); return !!c && c.width > 0; });
        check(`${out.screen}: the screen opens on the site`, out.ok && nb, out);
        await language(page, out.screen);
        await shot(page, `screen_${v.id}_${sc.id}`, false);
      } catch (e) { check(`${out.screen}: the screen opens on the site`, false, { error: e.message.split("\n")[0].slice(0, 200), errs: errs.slice(-3) }); }
      await page.close();
    }
    const lab = v.screens.find((x) => x.kind === "lab");
    if (lab) {
      const page = await open(`worksheet.html?demo=${v.id}`, { ms: 0 });
      const ok = await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 60000 }).then(() => true, () => false);
      const txt = ok ? await page.locator("#ws").innerText() : "";
      check(`${v.id}: the worksheet renders on the site`, ok && txt.includes(tr(lab.steps[0].title)), { ok, sample: txt.slice(0, 120) });
      // the programme's own lab name is quoted in Russian in every language («…»): the rest is in the language
      if (lang === "en") check(`worksheet ${v.id}: no Cyrillic but the programme's own wording`, !CYR.test(txt.replace(/«[^»]*»/g, "")));  // i18n-ok
      else check(`worksheet ${v.id}: in the language`, CYR.test(txt));
      await page.close();
    }
  }

  // a recording plays
  if (!REC) check("a recording to play", false, { recordings: Object.keys(recIndex) });
  else {
    const page = await open(`run.html?rec=${REC}`, { ms: 0 });
    let loaded = true;
    try {
      await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
    } catch (e) { loaded = false; check(`${REC}: the recording loads`, false, { error: e.message.slice(0, 200), errs }); }
    if (loaded) {
      const t0 = await page.evaluate(() => window.__lfPlayer.t());
      const tl0 = await page.$eval("#timeline", (e) => Number(e.value));
      let checks = 0;
      for (let i = 0; i < 30 && !checks; i++) { await sleep(500); checks = await page.$$eval(".checks td.ck-st", (a) => a.length); }
      await sleep(1000);
      const t1 = await page.evaluate(() => window.__lfPlayer.t());
      const tl1 = await page.$eval("#timeline", (e) => Number(e.value));
      check(`${REC}: it plays (the timeline moves, the world time grows)`, t1 > t0 && tl1 > tl0, { t0, t1, tl0, tl1 });
      check(`${REC}: the checks appear`, checks > 0, { checks });
      const badge = await page.$eval("#recbadge", (e) => e.textContent).catch(() => "");
      check(`${REC}: the badge «${tr("RECORDING · {date} · code {code}").split(" · ")[0]}»`, badge.startsWith(tr("RECORDING · {date} · code {code}").split(" · ")[0]), { badge });
      const live = await page.$(".rec-note button.primary");
      check(`${REC}: no «Compute live» on the site`, !live);
      const nb = await notBlank(page);
      check(`${REC}: the canvas is not blank`, nb.share > 0.002 && nb.colours > 3, nb);
      await language(page, REC);
      await shot(page, "record", false);
    }
    await page.close();
  }

  // every recording: it loads, its frames are the index's, the poster frame is at poster_t (F5)
  if (process.env.ALL_RECS !== "0") {
    const all = Object.entries(recIndex).flatMap(([w, ix]) => (ix.recordings || []).map((r) => ({ w, r })));
    const aliases = await getJSON("aliases.json").catch(() => ({}));
    const oldId = Object.entries(aliases).find(([, nw]) => recIndex[nw]);
    if (oldId) all.push({ w: oldId[0], r: { ...recIndex[oldId[1]].recordings[0], alias: true } });
    let played = 0;
    const badRecs = [];
    for (const { w, r } of all) {
      const page = await open(`run.html?rec=${w}/${r.id}`, { ms: 0 });
      const out = { rec: `${w}/${r.id}` };
      try {
        await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 180000 });
        out.frames = await page.evaluate(() => window.__lfPlayer.frames());
        if (r.poster_frame !== undefined) {
          await page.evaluate((i) => window.__lfPlayer.goTo(i), r.poster_frame);
          await sleep(200);
          out.t = await page.evaluate(() => window.__lfPlayer.t());
        }
        // a recording of several worlds (a script's new_world; S03's «independence»: 4) holds, in this player, the frames
        // of the world it shows (the last), so the index's whole count and the poster's index do not apply to it (its
        // Watch screen plays it whole; STATUS.md V52): it loads with at most the index's frames
        const multi = (r.worlds || 1) > 1;
        const okFrames = multi ? out.frames > 0 && out.frames <= r.frames : out.frames === r.frames;
        const okPoster = multi || r.poster_frame === undefined || Math.abs(out.t - r.poster_t) <= 1e-9 * Math.max(1, Math.abs(r.poster_t));
        if (okFrames && okPoster) played++; else badRecs.push({ ...out, want: r.frames, poster_t: r.poster_t });
      } catch (e) { badRecs.push({ ...out, error: e.message.split("\n")[0].slice(0, 160) }); }
      await page.close();
    }
    check(`every recording plays with the index's frames and poster time (${all.length}, an old id among them)`,
      badRecs.length === 0 && played === all.length && all.length > 0, { played, of: all.length, bad: badRecs.slice(0, 5) });
  }

  // an unknown recording id: said, with the way to the start page; not «No recording for this version» (D4)
  if (REC) {
    const w = REC.split("/")[0];
    const page = await open(`run.html?rec=${w}/no_such_recording`, { ms: 0 });
    let s = null;
    for (let i = 0; i < 60; i++) {  // the player's page gives way to the refusal
      s = await page.evaluate(() => ({ text: document.body.innerText, player: !!document.getElementById("timeline"),
        start: [...document.querySelectorAll("a")].map((a) => a.getAttribute("href")) }));
      if (!s.player) break;
      await sleep(250);
    }
    const version = tr("No recording for this version: record it locally or compute live");
    check("an unknown recording: «No such recording», with a link to the start page, not «for this version»",
      !s.player && s.text.includes(tr("No such recording")) && !s.text.includes(version)
        && s.start.some((h) => h === PREFIX || (h || "").startsWith(PREFIX + "?") || h === PREFIX + "index.html"),
      { text: s.text.slice(0, 200), links: s.start.slice(0, 4) });
    await page.close();
  }

  // the server's addresses on the site (start-page F12)
  for (const q of ["run.html?id=20261111-170830-v04-2ca9", "run.html"]) {
    const page = await open(q, { ms: 0 });
    let text = "";
    for (let i = 0; i < 40 && !text.trim(); i++) { await sleep(250); text = await page.evaluate(() => document.body.innerText); }
    await sleep(300);
    text = await page.evaluate(() => document.body.innerText);
    const want = tr("This site plays recordings; runs are computed by a local server");
    check(`${q}: «${want}», no raw error, no server address`, text.includes(want) && !/Unexpected token|is not valid JSON|\/run\?id=/.test(text),
      { text: text.slice(0, 200) });
    await page.close();
  }

  // the licence page
  {
    const page = await open("legal.html", { selector: "#legal pre", ms: 0 });
    let s = null;
    for (let i = 0; i < 40; i++) {
      s = await page.evaluate(() => ({ pre: [...document.querySelectorAll("#legal pre")].map((p) => p.textContent), cite: document.getElementById("cite")?.textContent || "" }));
      if (s.pre.length && s.pre.every((x) => x !== "") && !s.pre.some((x) => x.length < 40) && /lfphys/.test(s.cite)) break;
      await sleep(250);
    }
    const loading = tr("loading…"), couldNot = tr("could not load: {why}", { why: "" });
    check("legal.html: every text loaded", s.pre.length >= 5 && s.pre.every((x) => x.length > 40 && x !== loading && !x.startsWith(couldNot)),
      { texts: s.pre.map((x) => x.length), first: (s.pre.find((x) => x.length <= 40) || "").slice(0, 80) });
    check("legal.html: the citation", /lfphys/.test(s.cite), { cite: s.cite.slice(0, 120) });
    await language(page, "legal.html");
    await page.close();
  }

  check("no request outside the sub-path", outside.length === 0, { outside: [...new Set(outside)].slice(0, 10), favicon });
  check("no request to an API (/api/, api/<name> that is no file, a WebSocket)", apiCalls.length === 0 && sockets.length === 0, { api: [...new Set(apiCalls)].slice(0, 10), sockets });
  check("no failed request", bad.length === 0, { bad: [...new Set(bad)].slice(0, 10) });
  check("no page errors", errs.length === 0, { errs: errs.slice(0, 5) });
  check("no console errors", consoleErrs.length === 0, { console: consoleErrs.slice(0, 5) });
  await ctx.close();
}

await br.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
