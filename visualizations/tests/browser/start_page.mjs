// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The start page by audience (DESIGN of the start page §1.1–§1.6; owner, 2026-11-13), in a browser, for the language in
// LFVIZ_LANG (en by default), on the server (lf-mode "server"):
//  - the home: the four audiences (school, university, research, laboratories) with their counts; «My runs (n)» → /runs;
//  - each audience page: its heading, the section chips with counts (a chip filters), the sections in teaching order, the
//    search box (it narrows the cards);
//  - the tiles: each audience's own picture (registry.AUDIENCES "picture"), the names at 4.5:1 or more, a visible focus
//    ring for the keyboard (review P17-start-page F7, F8, F10); a malformed hash (/#%E0) still shows the page (F13);
//  - university and research cards: the scenario, «▶ Compute live», «▷ Recording m:ss» (enabled only where a local
//    recording exists, the site being unpublished: integrator D4; its link /run?rec=…; disabled with the reason
//    otherwise), «Same topic» links labelled with the audience, «▸ More» (folded at university, open in research);
//    research cards: the question, «Status: hypothesis», «Prior art: n references»; the section chips say aria-pressed;
//  - «▶ Compute live» starts a run and opens it in the player; the home's «Continue» then names it as computing or
//    paused, never as a recording (integrator D1); the run is left to suspend (there is no stop);
//  - the school page before AB1: the honest banner «Ready: k of n» (k = 1 since s03: «Ready: 1 of 45»), planned cards,
//    the ready card(s) with their screens only (and «▶ Compute live» on a server), no scenario list, no «▷ Recording»,
//    no options, «Already there at another level» links;
//  - the screens' buttons of every card with screens (design lfphys/sources/explore_2026-11-14_design.md §3.1, §3.10,
//    §8): in the registry's order «▷ Watch m:ss», «◎ Explore», «✎ Lab work»; each enabled with its link
//    /run?demo=<world>&screen=<id> exactly when its recording or atlases exist (/api/recordings), else greyed with the
//    reason; a click opens the screen's tab in the demonstration page;
//  - the laboratories (server): «▶ Begin», «Laws…», «📂 From a scene file…» and the planned benches; the old #playground
//    opens them;
//  - /runs: the runs table and the retention setting;
//  - English: no Cyrillic; Russian: the page is in Russian; at 390 px no horizontal scroll;
//  - screenshots of the home and each audience at 1280 and 390 px.
//
// Run against a PRIVATE server (never the shared one on 8479), as record_mode.mjs (a recording in LFVIZ_RECORDINGS makes
// the «▷ Recording» check meaningful):
//   docker run --rm --init --shm-size=2g --network host --memory=4g -e LFVIZ_LANG=en -v <dir with node_modules/playwright>:/pw \
//     -v <repo>/visualizations/tests/browser:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp /t/*.mjs /pw/ && node /pw/start_page.mjs 8679"
//  - NOREC_PORT=<port of a second private server with an empty LFVIZ_RECORDINGS and an unpublished site>: every
//    «▷ Recording» there is disabled with «No recording yet…» (D4).
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
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
const { t: tr } = await loadI18n(base);

const viz = (await get("/api/viz")).filter((v) => !v.error);
const audiences = (await get("/api/audiences")).audiences || [];
const planned = await get("/api/planned");
const recs = (await get("/api/recordings")).worlds || {};
const n = (aud) => viz.filter((v) => v.audience === aud).length;

const br = await chromium.launch();
const errs = [];
const open = async (ctx, hash = "") => {
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  await page.goto(inLang(`${base}/`) + (hash ? `#${hash}` : ""));
  await page.waitForSelector(hash ? ".st-head" : ".st-tiles", { timeout: 60000 });
  await sleep(500);
  return page;
};
const language = (name, text) => {
  if (LANG === "en") check(`${name}: no Cyrillic`, !CYR.test(text), { sample: text.split("\n").filter((s) => CYR.test(s)).slice(0, 4) });
  else check(`${name}: in the language`, CYR.test(text));
};

const ctx = await br.newContext({ viewport: { width: 1280, height: 900 } });

// the home
{
  const page = await open(ctx);
  const tiles = await page.$$eval(".st-tile", (a) => a.map((e) => ({ id: e.id, text: e.innerText, href: e.getAttribute("href") })));
  check("home: the four audiences, in order", tiles.map((x) => x.id).join() === "tile-school,tile-university,tile-research,tile-labs", { tiles: tiles.map((x) => x.id) });
  check("home: the audiences' names", [tr("School"), tr("University"), tr("Research"), tr("Laboratories")].every((s, i) => tiles[i] && tiles[i].text.toLowerCase().includes(s.toLowerCase())));
  check("home: the counts", tiles[1]?.text.includes(tr("{n:d} demonstrations", { n: n("university") })) && tiles[2]?.text.includes(tr("{n:d} research set-ups", { n: n("research") }))
    && tiles[3]?.text.includes(tr("{n:d} benches", { n: n("playground") })), { tiles: tiles.map((x) => x.text.replace(/\n/g, " | ")) });
  await sleep(3500);  // the runs' poll
  const runs = await get("/api/runs");
  const my = await page.$eval("#myruns", (e) => ({ text: e.textContent, href: e.getAttribute("href") }));
  check("home: «My runs (n)» → /runs", my.text === tr("My runs ({n:d})", { n: runs.length }) && my.href === "/runs", my);
  language("home", await page.evaluate(() => document.body.innerText));
  // each audience's own picture (F10), where the registry names one and that world has a picture
  const pics = await page.$$eval(".st-tile", (a) => a.map((e) => ({ id: e.id, src: e.querySelector("img.pic")?.getAttribute("src") || "", ph: !!e.querySelector("div.pic.ph"), h: (e.querySelector(".pic") || {}).offsetHeight || 0 })));
  for (const a of audiences.filter((x) => x.picture)) {
    const tile = pics.find((x) => x.id === `tile-${a.id === "playground" ? "labs" : a.id}`);
    const has = viz.some((v) => v.id === a.picture && v.picture);
    if (has) check(`home: the ${a.id} tile shows ${a.picture}`, tile && tile.src.endsWith(`images/${a.picture}.jpg`), tile);
  }
  check("home: every tile has a picture's room (a placeholder too)", pics.every((x) => x.h > 40), { pics });
  // the tiles' names readable (F8): 4.5:1 on the tile
  const ratios = await page.evaluate(() => {
    const rgb = (s) => (s.match(/[\d.]+/g) || []).slice(0, 3).map(Number);
    const lum = (c) => { const v = c.map((x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
    return [...document.querySelectorAll(".st-tile")].map((t) => {
      const a = lum(rgb(getComputedStyle(t.querySelector(".name")).color)), b = lum(rgb(getComputedStyle(t).backgroundColor));
      return Math.round(100 * (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05)) / 100;
    });
  });
  check("home: the tiles' names at 4.5:1 or more", ratios.every((r) => r >= 4.5), { ratios });
  // the keyboard: a visible ring round a focused tile (F7)
  let ring = null;
  for (let i = 0; i < 25 && !ring; i++) {
    await page.keyboard.press("Tab");
    ring = await page.evaluate(() => { const e = document.activeElement; if (!e || !e.classList.contains("st-tile")) return null;
      const c = getComputedStyle(e); return { id: e.id, style: c.outlineStyle, width: c.outlineWidth }; });
  }
  check("home: a focused tile has a visible ring", ring && ring.style !== "none" && parseFloat(ring.width) >= 2, { ring });
  await page.close();
}
// a malformed hash shows the page, not «Catalogue: URI malformed» (F13)
{
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  await page.goto(inLang(`${base}/`) + "#%E0");
  const ok = await page.waitForSelector(".st-tiles", { timeout: 30000 }).then(() => true, () => false);
  check("a malformed hash (#%E0) still shows the start page", ok);
  await page.close();
}

// the audience pages
for (const [hash, aud] of [["university", "university"], ["research", "research"], ["school", "school"]]) {
  const page = await open(ctx, hash);
  const s = await page.evaluate(() => ({
    h1: document.querySelector(".st-head h1")?.innerText || "",
    chips: [...document.querySelectorAll(".st-chips button")].map((b) => b.textContent),
    secs: [...document.querySelectorAll(".st-sec > h2")].map((h) => h.textContent),
    cards: document.querySelectorAll(".st-card").length, planned: document.querySelectorAll(".planned-card").length,
    text: document.body.innerText,
  }));
  check(`${hash}: the heading`, s.h1.toLowerCase().includes(tr({ university: "University", research: "Research", school: "School" }[aud]).toLowerCase()), { h1: s.h1 });
  check(`${hash}: the section chips with counts`, s.chips.length >= 2 && /\d+$/.test(s.chips[0]) && s.chips.slice(1).every((c) => /\d+$/.test(c)), { chips: s.chips });
  check(`${hash}: the sections`, s.secs.length >= 1, { secs: s.secs });
  const pressed = await page.$$eval(".st-chips button, .st-by button", (a) => a.map((b) => b.getAttribute("aria-pressed")));
  check(`${hash}: the chips say aria-pressed, one per group`, pressed.every((x) => x === "true" || x === "false") && pressed.filter((x) => x === "true").length === (aud === "school" ? 2 : 1), { pressed });
  language(hash, s.text);
  // a chip filters to its section
  const chip = await page.$$(".st-chips button");
  if (chip.length > 1) {
    const label = (await chip[1].textContent()).replace(/\s*\d+$/, "");
    await chip[1].click();
    await sleep(300);
    const secs = await page.$$eval(".st-sec > h2", (a) => a.map((h) => h.textContent));
    check(`${hash}: a chip shows its section only`, secs.length >= 1 && secs.every((x) => x.toLowerCase().startsWith(label.toLowerCase()) || x === tr("Planned in other sections")), { label, secs });
    await (await page.$(".st-chips button")).click();
  }
  // the search narrows the list
  const before = await page.$$eval(".st-card, .planned-card", (a) => a.length);
  const word = aud === "school" ? "S02" : aud === "research" ? "r12" : "u34";
  await page.fill(".st-search", word);
  await sleep(400);
  const after = await page.$$eval(".st-card, .planned-card", (a) => a.map((e) => e.id));
  check(`${hash}: the search narrows the cards`, after.length >= 1 && after.length < Math.max(before, 2) && after.some((id) => id.toLowerCase().includes(word.toLowerCase())), { before, after });
  await page.fill(".st-search", "");
  await sleep(300);
  if (aud === "school") {
    const P = planned.filter((p) => p.audience === "school");
    check("school: the banner «Ready: k of n»", s.text.includes(tr("Ready: {k:d} of {n:d}.", { k: n("school"), n: n("school") + P.length })), { want: tr("Ready: {k:d} of {n:d}.", { k: n("school"), n: n("school") + P.length }) });
    check("school: s03 is ready (k ≥ 1) and has its card", n("school") >= 1 && !!(await page.$("#card-s03_projectile")), { k: n("school") });
    check("school: planned cards; a ready card has its screens only (no scenario list, no «▷ Recording», no primary «▶ Compute live»)",
      s.planned >= 1 && !(await page.$(".st-card button.primary")) && !(await page.$(".st-card select")) && !(await page.$(".st-card a.button:not(.st-screen)"))
      && (await page.$$eval(".st-card", (a) => a.every((c) => c.querySelectorAll("a.st-screen").length >= 1))), { planned: s.planned });
    check("school: «Already there at another level» links", s.text.includes(tr("Already there at another level:")) && !!(await page.$(".st-there a[href^='#university/'], .st-there a[href^='#research/']")));
    check("school: no modified physics or options", !(await page.$(".st-moreopts")));
  } else {
    const live = await page.$$eval(".st-card button.primary", (a) => a.map((b) => b.textContent));
    check(`${hash}: «▶ Compute live» on every card`, live.length === s.cards && live.every((x) => x === tr("▶ Compute live")), { n: live.length, cards: s.cards });
    const rb = await page.$$eval(".st-card a.button:not(.st-screen)", (a) => a.map((b) => ({ text: b.textContent, href: b.getAttribute("href"), off: b.classList.contains("disabled"), title: b.title })));
    check(`${hash}: «▷ Recording» on the cards`, rb.length === s.cards && rb.every((b) => b.off ? [tr("No recording yet: record it locally (site/record.py) or compute live"), tr("No recording for this scenario: compute it live")].includes(b.title) : /\/run\?rec=\w+(\/|%2F)\w+/.test(b.href)), { rb: rb.slice(0, 3) });
    // enabled only where this server has the recording (the test server's site is unpublished: D4)
    const pub = (await get("/api/recordings")).published === true;
    if (!pub) {
      const wrong = [];
      for (const v of viz.filter((x) => x.audience === aud)) {
        const b = await page.$eval(`#card-${v.id} a.button:not(.st-screen)`, (e) => ({ off: e.classList.contains("disabled"), href: e.getAttribute("href") || "" }));
        const m = decodeURIComponent(b.href).match(/rec=[^/]+\/([^&]+)/);
        const local = !!(recs[v.id] && m && (recs[v.id].recordings || []).some((r) => r.id === m[1]));
        if (b.off ? false : !local) wrong.push(v.id);
      }
      check(`${hash}: «▷ Recording» enabled only for a local recording`, !wrong.length, { wrong });
    }
    const local = viz.filter((v) => v.audience === aud && recs[v.id]);
    for (const v of local) {
      const b = await page.$eval(`#card-${v.id} a.button:not(.st-screen)`, (e) => ({ text: e.textContent, href: e.getAttribute("href") }));
      const r = recs[v.id].recordings[0];
      check(`${hash}: ${v.id} «▷ Recording m:ss» of its local recording`, b.href.includes(`rec=${v.id}%2F${r.id}`) || b.href.includes(`rec=${v.id}/${r.id}`), b);
    }
    const more = await page.$$eval(".st-moreopts", (a) => a.map((d) => d.open));
    check(`${hash}: «▸ More» ${aud === "research" ? "open" : "folded"}`, more.length === s.cards && more.every((o) => o === (aud === "research")), { more });
    const rel = await page.$$eval(".st-related a:not(.st-relmore)", (a) => a.map((x) => ({ text: x.textContent, href: x.getAttribute("href") })));
    const labels = [tr("School"), tr("University"), tr("Research"), tr("Laboratories")];
    check(`${hash}: «Same topic» links labelled with the audience`, rel.length >= 1 && rel.every((x) => labels.some((l) => x.text.startsWith(l + " · ")) && /^#(school|university|research|labs)\//.test(x.href)), { rel: rel.slice(0, 4) });
    if (aud === "research") {
      const rc = await page.$$eval(".st-card", (a) => a.map((c) => ({ q: !!c.querySelector(".st-question"), st: c.querySelector(".st-hyp")?.textContent, pa: c.querySelector(".st-prior summary")?.textContent || "" })));
      check("research: the question, «Status: hypothesis», «Prior art: n references»", rc.every((c) => c.q && c.st === tr("Status: {status}", { status: tr("hypothesis") }) && /\d/.test(c.pa)), { rc });
    }
    // a «Same topic» link leads to that card on its audience page
    if (rel.length) {
      await page.click(".st-related a:not(.st-relmore)");
      await sleep(500);
      const target = rel[0].href.split("/")[1];
      const f = await page.evaluate(() => ({ hash: location.hash, focus: document.querySelector(".card.focus")?.id }));
      check(`${hash}: «Same topic» opens the card on its page`, f.hash === rel[0].href && f.focus === `card-${target}`, f);
    }
  }
  await page.close();
}

// the screens' buttons of every card with screens (design of 2026-11-14 §3.1, §3.10, §8)
{
  const mss = (sec) => { const x = Math.round(sec || 0); return `${Math.floor(x / 60)}:${String(x % 60).padStart(2, "0")}`; };
  const withScreens = viz.filter((v) => (v.screens || []).length);
  check("screens: at least s03 and u32 have screens", ["s03_projectile", "u32_double_slit"].every((id) => withScreens.some((v) => v.id === id)), { ids: withScreens.map((v) => v.id) });
  for (const v of withScreens) {
    const page = await open(ctx, `${v.audience === "playground" ? "labs" : v.audience}/${v.id}`);
    const got = await page.$$eval(`#card-${v.id} a.st-screen`, (a) => a.map((b) => ({ id: b.dataset.screen, text: b.textContent,
      href: b.getAttribute("href") || "", off: b.classList.contains("disabled"), aria: b.getAttribute("aria-disabled"), title: b.title })));
    const idx = recs[v.id] || {};
    const atl = new Set((idx.atlases || []).map((a) => a.id));
    const want = v.screens.map((s) => {
      if (s.kind === "watch") {
        const r = (idx.recordings || []).find((x) => x.id === s.recording);
        return { id: s.id, ready: !!r, label: r ? tr("▷ Watch {time}", { time: mss(r.seconds) }) : tr("▷ Watch") };
      }
      if (s.kind === "explore") return { id: s.id, ready: atl.has(s.atlas), label: tr("◎ Explore") };
      return { id: s.id, ready: (s.steps || []).length > 0 && s.steps.every((st) => atl.has(st.atlas)), label: tr("✎ Lab work") };
    });
    check(`screens: ${v.id} buttons in the registry's order with their labels`, got.length === want.length
      && want.every((w, i) => got[i].id === w.id && got[i].text === w.label), { got: got.map((g) => g.text), want: want.map((w) => w.label) });
    const bad = want.filter((w, i) => !got[i] || (w.ready
      ? got[i].off || !new RegExp(`/run(\\.html)?\\?demo=${v.id}&screen=${w.id}(&|$)`).test(got[i].href)
      : !got[i].off || got[i].href || got[i].aria !== "true" || got[i].title !== tr("Not made yet: build it locally (site/record.py) or compute live")));
    check(`screens: ${v.id} enabled with /run?demo=…&screen=… exactly when made, else greyed with the reason`, !bad.length, { bad, got });
    const first = got.find((g) => !g.off);
    if (first) {
      await Promise.all([page.waitForURL(/\/run\?demo=/, { timeout: 30000 }), page.click(`#card-${v.id} a.st-screen[data-screen="${first.id}"]`)]);
      const tab = await page.waitForSelector(`.dm-tabs button[data-screen="${first.id}"][aria-selected="true"]`, { timeout: 30000 }).then(() => true, () => false);
      check(`screens: ${v.id} «${first.text}» opens its screen`, tab && new URL(page.url()).searchParams.get("screen") === first.id, { url: page.url() });
    }
    await page.close();
  }
}

// «▶ Compute live» starts a run and opens the player
{
  const page = await open(ctx, "university/u34_orbits");
  await Promise.all([page.waitForURL(/\/run\?id=/, { timeout: 60000 }), page.click("#card-u34_orbits button.primary")]);
  const id = new URL(page.url()).searchParams.get("id");
  check("«▶ Compute live» starts a run and opens it", !!id, { url: page.url() });
  // the home's «Continue» names the live run (watched in the other tab) by its state, never as a recording (D1)
  const home = await open(ctx);
  await sleep(3500);
  const cont = await home.$$eval(".st-cont", (a) => a.map((e) => e.innerText));
  check("home: «Continue» says computing or paused", cont.length >= 1 && cont.every((x) => x.includes(tr("computing")) || x.includes(tr("paused"))), { cont });
  await home.close();
  await page.close();  // the run is left to suspend by itself: there is no stop (owner, 2026-10-28)
}

// the laboratories, and the old #playground
{
  const page = await open(ctx, "playground");
  const s = await page.evaluate(() => ({ hash: location.hash, cards: document.querySelectorAll(".st-card").length,
    buttons: [...document.querySelectorAll(".st-card button")].map((b) => b.textContent), planned: document.querySelectorAll(".planned-card").length,
    text: document.body.innerText }));
  check("old #playground opens the laboratories (#labs)", s.hash === "#labs" && s.cards === n("playground"), { hash: s.hash, cards: s.cards });
  check("labs (server): «▶ Begin», «Laws…», «📂 From a scene file…» on every card",
    [tr("▶ Begin"), tr("Laws…"), tr("📂 From a scene file…")].every((b) => s.buttons.filter((x) => x === b).length === s.cards), { buttons: s.buttons.slice(0, 6) });
  check("labs: the planned benches", s.planned === planned.filter((p) => p.audience === "playground").length, { planned: s.planned });
  language("labs", s.text);
  await page.close();
}

// /runs
{
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  await page.goto(inLang(`${base}/runs`));
  await page.waitForSelector("#retention input", { timeout: 30000 });
  await page.waitForSelector("#runs table, #runs .muted", { timeout: 30000 });
  const s = await page.evaluate(() => ({ rows: document.querySelectorAll("#runs tr").length, back: document.querySelector('.topbar a[data-page=""]')?.getAttribute("href"), text: document.body.innerText }));
  check("/runs: the runs and the retention setting", s.rows >= 1 && s.back === "/", s);
  language("/runs", s.text);
  await page.close();
}

// screenshots, and no horizontal scroll at 390 px
for (const w of [1280, 390]) {
  const c2 = await br.newContext({ viewport: { width: w, height: 900 } });
  for (const hash of ["", "school", "university", "research", "labs"]) {
    const page = await open(c2, hash);
    const o = await page.evaluate(() => ({ sw: document.scrollingElement.scrollWidth, w: innerWidth }));
    if (w === 390) check(`${hash || "home"} at 390 px: no horizontal scroll`, o.sw <= o.w + 1, o);
    await page.screenshot({ path: `${SHOTS}/start_${hash || "home"}_${LANG}_${w}.png`, fullPage: true });
    await page.close();
  }
  await c2.close();
}

// a server with no local recordings, the site unpublished (every fresh clone): nothing to play, the reason said (D4)
if (process.env.NOREC_PORT) {
  const nb = `http://127.0.0.1:${process.env.NOREC_PORT}`;
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  await page.goto(inLang(`${nb}/`) + "#university");
  await page.waitForSelector(".st-head", { timeout: 60000 });
  await sleep(500);
  const rb = await page.$$eval(".st-card a.button", (a) => a.map((b) => ({ off: b.classList.contains("disabled"), title: b.title, href: b.getAttribute("href") })));
  check("no local recordings: every «▷ Recording» disabled with «No recording yet…»", rb.length > 0 && rb.every((b) => b.off && !b.href
    && [tr("No recording yet: record it locally (site/record.py) or compute live"), tr("No recording for this scenario: compute it live")].includes(b.title)), { rb: rb.slice(0, 3), n: rb.length });
  await page.close();
}

check("no page errors", !errs.length, { errs });
await br.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
