// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The start page by audience (DESIGN of the start page §1.1–§1.6; owner, 2026-11-13), in a browser, for the language in
// LFVIZ_LANG (en by default), on the server (lf-mode "server"):
//  - the home: the four audiences (school, university, research, laboratories) with their counts; «My runs (n)» → /runs;
//  - each audience page: its heading, the section chips with counts (a chip filters), the sections in teaching order, the
//    search box (it narrows the cards);
//  - university and research cards: the scenario, «▶ Compute live», «▷ Recording m:ss» (enabled where a recording
//    exists, its link /run?rec=…), «Same topic» links labelled with the audience, «▸ More» (folded at university, open in
//    research); research cards: the question, «Status: hypothesis», «Prior art: n references»;
//  - «▶ Compute live» starts a run and opens it in the player;
//  - the school page before AB1: the honest banner «Ready: 0 of n», planned cards, nothing startable, «Already there at
//    university level» links;
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
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const { t: tr } = await loadI18n(base);

const viz = (await get("/api/viz")).filter((v) => !v.error);
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
    check("school: planned cards, nothing startable", s.planned >= 1 && !(await page.$(".st-card button.primary")) && (n("school") > 0 || !(await page.$(".st-card"))), { planned: s.planned });
    check("school: «Already there at university level» links", s.text.includes(tr("Already there at university level:")) && !!(await page.$(".st-there a[href^='#university/'], .st-there a[href^='#research/']")));
    check("school: no modified physics or options", !(await page.$(".st-moreopts")));
  } else {
    const live = await page.$$eval(".st-card button.primary", (a) => a.map((b) => b.textContent));
    check(`${hash}: «▶ Compute live» on every card`, live.length === s.cards && live.every((x) => x === tr("▶ Compute live")), { n: live.length, cards: s.cards });
    const rb = await page.$$eval(".st-card a.button", (a) => a.map((b) => ({ text: b.textContent, href: b.getAttribute("href"), off: b.classList.contains("disabled"), title: b.title })));
    check(`${hash}: «▷ Recording» on the cards`, rb.length === s.cards && rb.every((b) => b.off ? b.title === tr("No recording for this scenario: compute it live") : /\/run\?rec=\w+(\/|%2F)\w+/.test(b.href)), { rb: rb.slice(0, 3) });
    const local = viz.filter((v) => v.audience === aud && recs[v.id]);
    for (const v of local) {
      const b = await page.$eval(`#card-${v.id} a.button`, (e) => ({ text: e.textContent, href: e.getAttribute("href") }));
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

// «▶ Compute live» starts a run and opens the player
{
  const page = await open(ctx, "university/u34_orbits");
  await Promise.all([page.waitForURL(/\/run\?id=/, { timeout: 60000 }), page.click("#card-u34_orbits button.primary")]);
  const id = new URL(page.url()).searchParams.get("id");
  check("«▶ Compute live» starts a run and opens it", !!id, { url: page.url() });
  if (id) await post(`/api/runs/${id}/stop`);
  await page.close();
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

check("no page errors", !errs.length, { errs });
await br.close();
console.log(failed ? `${failed} failed` : "all passed");
process.exit(failed ? 1 : 0);
