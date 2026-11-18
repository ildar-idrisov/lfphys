// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// A demonstration's screens in a browser (design lfphys/sources/explore_2026-11-14_design.md §3, §8 "Browser"): one
// world with screens, the third argument (by default the toy world s98_atlas_toy of tests/site_worlds, its atlases and
// recordings built in tests/site_worlds/recordings; s03_projectile and u32_double_slit with the recordings and atlases of
// site/record.py), in the language of LFVIZ_LANG (en by default), at every viewport size given (1280x800 and 390x844 by
// default). Everything is read from the world's catalogue entry and its manifests (the grid, the refused points, the
// readouts, the traces, the captions, the first lab step); a part the world has not is skipped with a line saying so.
// u32's own browser check (u32_double_slit/tests/u32_screens.mjs) adds what is particular to it.
//  - the tabs «Watch · Explore · Lab work» in the language, the tab in the address, each screen's state kept across tabs;
//  - Explore, as on the public site (the page served with lf-mode "static" and the API's JSON files, by routing): the
//    sliders' positions are the grid's values only; a refused combination (the manifest's first) says why and disables
//    ▶; a readout is «—» before its event and filled after (time "flight"); ▶ Launch flies the point to its landing;
//    earlier shots (or, acts "now", earlier points) stay as traces (≤ N); overlays toggle; the points fetched are only
//    those shown and their neighbours (±1 along a control); «How we know this is right» lists the point's checks ✓;
//  - Explore on the server: a value near a detent snaps to it; an off-grid value is computed live (POST
//    /api/atlas/…/point) and labelled «computed live» in the passport; a refused off-grid value says why;
//  - Watch: the recording plays from its start; the caption shown is the latest one as of the cursor (each caption's
//    chapter tick on the timeline jumps to it; ◀◀ / ▶▶); the captions are the recording's texts in the language;
//  - Explore, the keyboard (integrator D7): Space on a focused toggle presses it, → on a focused slider moves it (and its
//    aria-valuetext tells the value); at 390 px every control on the screen together with the view and the time bar (D12);
//  - Explore on the server: the live point's own passport (its key, code and time with its zone; D13);
//  - Watch: a caption's hold (F12), the time label with the world's time and the playback factor (D8), written as
//    Explore's (EX2 §5 F12): at the start, at each caption and at the end, the world's time of the frame shown on its
//    human scale (ps … s), in the header's units.t_show or at school in seconds, and the factor (the frames' own Δt × the
//    frames per played second × the speed chosen, normal and slow) in powers of ten from 10⁶ on;
//  - Lab work, every step (a bench, EX2 §1.4, §5 F6): «Measure» before a launch says there is nothing to measure yet; a
//    slow reply of an earlier pick is not shown and «Measure» waits for the set-up (D6); → on a focused slider; the
//    manual stopwatch on the wall clock, a pause refused while it runs, its reading in its column; the set-ups measured
//    (Space on a focused «Measure» too), one row each, a repeat replaces its row (D5); the fit on each law's plot prints
//    its parameters with their σ (and, at standard, χ², dof, p and the Birge ratio, the scaled σ on its own line) and no
//    verdict, no «Check against the law» (the owner, 2026-11-18); an empty time without the stopwatch; the drawer's
//    events with their times, as in Explore (EX1's D10 withdrawn); at 390 px the view, a control, «Measure», «⏱ Stop» and
//    the time bar together (D12); Space on a focused tab;
//  - EX2: every Explore screen's compound controls, time label, readouts with error and reference, counted stop and
//    «CSV of this point» (standard); every lab step's counters, the run's σ, formula columns (an empty cell with its
//    reason), the drawer as Explore's with «Computed for this bench», «MODIFIED PHYSICS»; &variant= preselecting the
//    controls (nothing locked);
//  - the task sheet (F8): the goal, the bench, the procedure, the record list, the programme or the basis (quoted
//    verbatim in its language), no questions, answers or teacher's pages; one A4 page per sheet (the PDF's pages = the
//    sheets, none overflowing at A4's printable width), each with the attribution line; record_rows blank rows per part;
//    an edit printed, kept in the browser and restored; &computed=1 on a page of its own; each variant's sheet; no raw id
//    or Latin unit in Russian;
//  - TRANSITION: a world with EX1's worksheet (S03 until WS03) is only opened: each screen and its sheet without a page
//    error;
//  - every screen: no horizontal scroll (scrollWidth ≤ the window's width), no page error, in English no Cyrillic in
//    the visible text and in Russian the tabs' Russian labels; screenshots of every screen per language and size.
//
// Run against a PRIVATE server (never the shared one on 8479) whose recordings and atlases were built by the code under
// test: a screen opens an atlas only with the key the server would build now (integrator D11), so the committed fixture
// goes stale with any code change. Build them fresh with site/fixtures.py (the toy by default; --world for others):
//   docker run --rm --memory=8g -e LFPHYS_NO_GPU=1 --user "$(id -u):$(id -g)" -v <repo>:/lf:ro -v <scratch>/rec:/rec \
//     -w /lf/visualizations lfphys-viz python3 site/fixtures.py --out /rec [--world s03_projectile --world u32_double_slit]
//   docker run -d --name lf-p3-srv --memory=6g -p 8692:8479 -v <repo>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
//     -v <scratch>/rec:/rec:ro -e LFPHYS_NO_GPU=1 -e LFVIZ_EXTRA=/lf/visualizations/tests/site_worlds -e LFVIZ_RECORDINGS=/rec \
//     -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
//   docker run --rm --init --shm-size=2g --network host --memory=4g -v <scratch with node_modules/playwright@1.58.2>:/pw \
//     -v <repo>/visualizations/tests/browser:/t:ro -w /pw -e LFVIZ_LANG=en|ru -e SHOTS=/pw/shots \
//     mcr.microsoft.com/playwright:v1.58.2-jammy sh -c "cp /t/*.mjs /pw/ && node /pw/demo_screens.mjs 8692 [1280x800,390x844] [world]"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { LANG, inLang, loadI18n } from "./lfi18n.mjs";

const port = process.argv[2] || "8692";
const SIZES = (process.argv[3] || "1280x800,390x844").split(",").map((s) => s.split("x").map(Number));
const base = `http://127.0.0.1:${port}`;
const SHOTS = process.env.SHOTS || "/pw/shots";
mkdirSync(SHOTS, { recursive: true });
const WORLD = process.argv[4] || "s98_atlas_toy";
const CYR = /[Ѐ-ӿ]/;  // i18n-ok: recognises Cyrillic
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: `${LANG} ${name}`, ok: !!ok, ...info })); };
const get = async (u) => (await fetch(base + u)).json();
const { t: tr } = await loadI18n(base);

const viz = await get(`/api/viz/${WORLD}`);
const recs = await get("/api/recordings");
const index = recs.worlds[WORLD];
const scr = (kind) => (viz.screens || []).find((s) => s.kind === kind) || null;
const explore = scr("explore"), watchScr = scr("watch"), lab = scr("lab");
check(`${WORLD} has its screens, recordings and atlases`, (viz.screens || []).length >= 2 && index && (index.atlases || []).length >= 1
  && (viz.screens || []).every((s) => s.kind === "watch" ? index.recordings.some((r) => r.id === s.recording)
    : s.kind === "explore" ? index.atlases.some((a) => a.id === s.atlas) : s.steps.every((st) => index.atlases.some((a) => a.id === st.atlas))));
const exploreAtlas = explore && index.atlases.find((a) => a.id === explore.atlas);
const mfE = exploreAtlas ? await get(`/recordings/${WORLD}/${exploreAtlas.file}`) : null;
const stepAtlas = lab && index.atlases.find((a) => a.id === lab.steps[0].atlas);
const mfL = stepAtlas ? await get(`/recordings/${WORLD}/${stepAtlas.file}`) : null;
const isNum = (c) => c.values.every((x) => typeof x === "number");
// the manifest's grid: a point's flat index (row-major, the last control fastest) and its values
const flat = (mf, vals) => mf.controls.reduce((i, c) => i * c.values.length + c.values.findIndex((x) => x === vals[c.param]), 0);
const valuesAt = (mf, i) => { const out = {}; for (const c of [...mf.controls].reverse()) { out[c.param] = c.values[i % c.values.length]; i = Math.floor(i / c.values.length); } return out; };
const nbOf = (mf, i) => { const v = valuesAt(mf, i), out = [i];
  for (const c of mf.controls) { const k = c.values.indexOf(v[c.param]); for (const d of [-1, 1]) if (c.values[k + d] !== undefined) out.push(flat(mf, { ...v, [c.param]: c.values[k + d] })); }
  return out; };
// the explore control to vary: the numeric one with the most values (the first such)
const varied = mfE && mfE.controls.filter(isNum).reduce((a, c) => (!a || c.values.length > a.values.length ? c : a), null);
const firstRefused = mfE ? mfE.points.findIndex((p) => p[2] >= 1) : -1;
const skip = (what) => console.log(JSON.stringify({ check: `${LANG} ${what}`, skipped: true }));

// Watch's time label against the frame shown (EX2 §5 F12), computed here without the player's code: null when right,
// else what is wrong. st: {tt (the frame's world time), units (its header's), r (world seconds per played second)}.
const schoolUi = (viz.ui === "school" || viz.ui === "full") ? viz.ui === "school" : viz.audience === "school";
const SUPS = "⁰¹²³⁴⁵⁶⁷⁸⁹";
function shownNumber(x) {  // a number as the player writes it, in the language: «1,015», «1 015», «0,45», «1.2·10⁹»
  let s = x.replace(/[\s\u00a0\u202f]/g, "").replace("−", "-");
  let e = 0;
  const m = /^(.*)·10(⁻?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)$/.exec(s);
  if (m) { s = m[1]; e = Number(m[2].replace("⁻", "-").replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g, (d) => String(SUPS.indexOf(d)))); }
  s = LANG === "ru" ? s.replace(",", ".") : s.replace(/,/g, "");
  return /^-?\d+(\.\d+)?$/.test(s) ? Number(s) * 10 ** e : NaN;
}
function watchLabelWrong(label, st, school) {
  const parts = label.split(" · ");
  const head = tr("world {t}", { t: "\u0000" }).split("\u0000");
  if (!(parts[0].startsWith(head[0]) && parts[0].endsWith(head[1] || ""))) return "no «world …» first";
  const wt = parts[0].slice(head[0].length, parts[0].length - (head[1] || "").length).trim();
  const sp = wt.lastIndexOf("\u00a0");
  const num = shownNumber(sp > 0 ? wt.slice(0, sp) : wt), unit = sp > 0 ? wt.slice(sp + 1) : "";
  const ts = st.units && st.units.t_show;
  const human = [[1e-9, "ps", 1e-12], [1e-6, "ns", 1e-9], [1e-3, "µs", 1e-6], [1, "ms", 1e-3], [120, "s", 1]];
  if (ts && ts.s > 0) {  // the world's own unit, four significant digits
    if (unit !== tr(ts.unit) || !(Math.abs(num - st.tt / ts.s) <= 5e-4 * Math.abs(st.tt / ts.s) + 1e-12)) return `not ${st.tt / ts.s} ${ts.unit}`;
  } else if (school) {  // seconds to two decimals
    if (unit !== tr("s") || !(Math.abs(num - st.tt) <= 0.0051)) return `not ${st.tt} s at school`;
  } else if (st.tt === 0) {
    if (!(num === 0 && unit === tr("s"))) return "not 0 s";
  } else if (st.tt < 120) {  // the human scale, three significant digits
    const [, u, f] = human.find(([lim]) => st.tt < lim);
    if (unit !== tr(u) || !(Math.abs(num * f - st.tt) <= 5e-3 * st.tt)) return `not ${st.tt / f} ${u}`;
  }
  if (!(st.r > 0)) return parts.length === 2 ? null : "a factor without a rate";
  if (Math.abs(st.r - 1) <= 0.05) return parts[1] === tr("real time") ? null : "not «real time»";
  const k = st.r < 1 ? 1 / st.r : st.r;
  const pre = tr(st.r < 1 ? "slow motion ×{k}" : "sped up ×{k}", { k: "\u0000" }).split("\u0000");
  if (!(parts[1] && parts[1].startsWith(pre[0]))) return `not «${pre[0]}…»`;
  const ks = parts[1].slice(pre[0].length, parts[1].length - (pre[1] || "").length), kv = shownNumber(ks);
  if (k >= 1e6 && !ks.includes("·10")) return `×${ks}: not in powers of ten`;
  if (k < 1e6 && ks.includes("·10")) return `×${ks}: a power of ten below 10⁶`;
  return Math.abs(kv - k) <= 0.051 * k ? null : `×${ks}: not ${k}`;
}

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });


// the page as the public site serves it: lf-mode "static", the API as JSON files (api/<name>.json), no live endpoint
async function asSite(ctx) {
  await ctx.route(/\/run(\.html)?(\?|$)/, async (route) => {
    const r = await route.fetch({ url: base + "/run" });
    const html = (await r.text()).replace('<meta name="lf-mode" content="server">', '<meta name="lf-mode" content="static">');
    await route.fulfill({ response: r, body: html, headers: { ...r.headers(), "content-type": "text/html; charset=utf-8" } });
  });
  await ctx.route(/\/api\/(.+)\.json(\?.*)?$/, async (route) => {
    const name = new URL(route.request().url()).pathname.replace(/^\/api\//, "").replace(/\.json$/, "");
    const r = await route.fetch({ url: `${base}/api/${name}` });
    await route.fulfill({ response: r });
  });
  await ctx.route(/\/aliases\.json$/, (route) => route.fulfill({ status: 200, contentType: "application/json", body: "{}" }));
  await ctx.route(/\/api\/atlas\//, (route) => route.abort());  // the site has no server
}

async function open(ctx, screen, extra = "") {
  const page = await ctx.newPage();
  const errs = [], reqs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
  page.on("request", (r) => reqs.push(r.url()));
  await page.goto(inLang(`${base}/run?demo=${WORLD}&screen=${screen}${extra}`));
  await page.waitForFunction((s) => document.querySelector(`.dm-screen[data-screen="${s}"]`) && !document.querySelector(`.dm-screen[data-screen="${s}"]`).hidden, screen, { timeout: 20000 });
  return { page, errs, reqs };
}
const settle = (page, ms = 300) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
const visibleText = (page) => page.evaluate(() => document.getElementById("demo").innerText);
async function common(page, tag, W, errs) {
  const sw = await page.evaluate(() => document.scrollingElement.scrollWidth);
  check(`${tag}: no horizontal scroll`, sw <= W, { scrollWidth: sw, width: W });
  const txt = await visibleText(page);
  if (LANG === "en") check(`${tag}: no Cyrillic in the visible text`, !CYR.test(txt), { sample: (txt.match(/.{0,30}[Ѐ-ӿ].{0,30}/) || [""])[0] });  // i18n-ok
  else check(`${tag}: the tabs in Russian`, viz.screens.map((s) => tr(s.label || { watch: "Watch", explore: "Explore", lab: "Lab work" }[s.kind])).every((s) => txt.includes(s)) && CYR.test(txt));
  check(`${tag}: no page error`, errs.length === 0, { errs });
}
// a slider's control row by its parameter; a detent by its value
const detent = (page, param, k) => page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${param}"] .dm-detent`).nth(k);
// choose a grid value of a control: its detent (a slider) or its button (a toggle, a select)
const choose = (page, c, v) => (isNum(c) ? detent(page, c.param, c.values.indexOf(v))
  : page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${c.param}"] .dm-ctl-seg button[data-value='${JSON.stringify(v)}']`)).click();

// TRANSITION (registry.EX1_WORKSHEETS; WS03 removes it): a world whose Lab work still has EX1's worksheet (S03 until its
// rework) is only opened: each screen and the task sheet without a page error, in every size (the integrator, 2026-11-18)
if (lab && lab.worksheet && lab.worksheet.ex1) {
  for (const [W, H] of SIZES) {
    for (const sc of viz.screens) {
      const ctx = await br.newContext({ viewport: { width: W, height: H } });
      const { page, errs } = await open(ctx, sc.id);
      await settle(page, 1500);
      check(`${W}x${H} ${sc.id} (EX1 world, transition): the screen opens without a page error`, errs.length === 0, { errs });
      await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_${sc.id}_${LANG}_${W}x${H}.png` });
      await ctx.close();
    }
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", (e) => errs.push(e.message));
    await page.goto(inLang(`${base}/worksheet?demo=${WORLD}`));
    await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
    const txt = await page.locator("#ws").innerText();
    check(`${W}x${H} task sheet (EX1 world, transition): opens, prints its parts, no question or answer`, errs.length === 0
      && lab.steps.every((st) => txt.includes(tr(st.title))) && !lab.worksheet.questions.some((q) => txt.includes(tr(q.answer))), { errs });
    await ctx.close();
  }
  await br.close();
  console.log(failed ? `FAILED: ${failed}` : "all passed");
  process.exit(failed ? 1 : 0);
}

for (const [W, H] of SIZES) {
  const tag0 = `${W}x${H}`;
  // --- Explore, as the site ---------------------------------------------------------------------------------------
  if (explore) {
    const SID = explore.id;
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs, reqs } = await open(ctx, SID);
    const X = `(window.__lfExplore || {})[${JSON.stringify(SID)}]`;
    const until = (body, timeout = 15000) => page.waitForFunction(`(() => { const X = ${X}; return ${body}; })()`, null, { timeout });
    await until("X && X.point()", 30000);
    const shown = [];
    const note = async () => { const i = await page.evaluate(`${X}.point() ? ${X}.point().i : null`); if (i !== null) shown.push(i); };
    const pickTo = async (vals) => {  // choose values control by control, noting every point shown on the way
      for (const c of mfE.controls) {
        if (!(c.param in vals) || (await page.evaluate(`${X}.values()`))[c.param] === vals[c.param]) continue;
        await choose(page, c, vals[c.param]);
        await until(`X.values()[${JSON.stringify(c.param)}] === ${JSON.stringify(vals[c.param])} && (X.state.refused || (X.point() && X.point().values[${JSON.stringify(c.param)}] === ${JSON.stringify(vals[c.param])}))`);
        await note();
        shown.push(flat(mfE, await page.evaluate(`${X}.values()`)));  // the set-up asked for (a refused one too: its neighbours are prefetched)
      }
    };
    await note();
    const tabs = await page.locator(".dm-tab").allInnerTexts();
    const want = viz.screens.map((s) => tr(s.label || { watch: "Watch", explore: "Explore", lab: "Lab work" }[s.kind]));  // a screen's own label (the toy's «Throws»)
    check(`${tag0} tabs`, tabs.length === want.length && want.every((w, i) => tabs[i].includes(w)), { tabs, want });
    const nums = mfE.controls.filter(isNum);
    const sl = await page.evaluate(() => [...document.querySelectorAll(".dm-screen:not([hidden]) .dm-slider")].map((s) => ({ min: s.min, max: s.max, step: s.step })));
    check(`${tag0} explore (site): the sliders' positions are the grid's values only`, sl.length === nums.length
      && sl.every((s, i) => s.min === "0" && Number(s.max) === nums[i].values.length - 1 && s.step === "1"), { sl });
    const flight = (explore.time || "flight") === "flight";
    const play = async () => {
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();
      await until("!X.state.playing && X.state.cur && X.state.cur.launchedAt !== null", 60000);
    };
    const ro = (explore.readouts || [])[0];
    if (flight && ro) {  // a readout before its event, then the launch
      await settle(page);
      const before = await page.locator(`[data-readout="${ro}"] b`).innerText();
      check(`${tag0} explore: a readout is «—» before its event`, before.trim() === "—", { ro, before });
      await play();
      await settle(page);
      const after = await page.locator(`[data-readout="${ro}"] b`).innerText();
      check(`${tag0} explore: the readout «${ro}» is filled once its event is reached`, /\d/.test(after) && after !== "—", { after });
    } else {
      skip(`${tag0} explore: readouts before and after their event (no readout or not a flight)`);
      await play();
      await settle(page);
      check(`${tag0} explore: ▶ plays the point to its end`, await page.evaluate(`${X}.state.cur.launchedAt !== null`));
      if (!(explore.readouts || []).length) check(`${tag0} explore: no empty readouts box`, await page.evaluate(() => [...document.querySelectorAll(".dm-screen:not([hidden]) .dm-readouts")].every((b) => b.children.length || getComputedStyle(b).display === "none")));
    }
    await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_explore_${LANG}_${tag0}.png` });
    // two more values of the varied control: the earlier shots (or points) stay as traces
    if (explore.traces && varied) {
      const cur = (await page.evaluate(`${X}.values()`))[varied.param];
      const others = varied.values.filter((v) => v !== cur).slice(0, 2);
      for (const v of others) { await pickTo({ [varied.param]: v }); if (flight) await play(); }
      const ntr = await page.evaluate(`${X}.state.traces.length`);
      check(`${tag0} explore: earlier ${flight ? "shots" : "points"} stay as traces (at most ${explore.traces})`, ntr >= 1 && ntr <= explore.traces, { traces: ntr });
    } else skip(`${tag0} explore: traces (none declared)`);
    // an overlay toggles (the first one off by default)
    const ovs = await page.$$eval(".dm-screen:not([hidden]) input[data-overlay]", (a) => a.map((x) => ({ id: x.dataset.overlay, on: x.checked })));
    const ov = ovs.find((o) => !o.on) || ovs[0];
    if (ov) {
      if (W < 1000) await page.locator(".dm-screen:not([hidden]) .dm-overlays > summary").click().catch(() => {});
      const box = page.locator(`.dm-screen:not([hidden]) input[data-overlay="${ov.id}"]`);
      await box.setChecked(!ov.on);
      check(`${tag0} explore: an overlay toggles (${ov.id})`, (await box.isChecked()) === !ov.on);
    } else skip(`${tag0} explore: overlays (none)`);
    await settle(page);
    await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_explore_traces_${LANG}_${tag0}.png` });
    // the keyboard (D7): Space on a focused toggle presses it (no playback); → on a focused slider moves the slider
    const tog = mfE.controls.find((c) => !isNum(c));
    if (tog) {
      const cur = (await page.evaluate(`${X}.values()`))[tog.param];
      const other = tog.values.find((v) => v !== cur);
      const btn = page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${tog.param}"] .dm-ctl-seg button[data-value='${JSON.stringify(other)}']`);
      await btn.focus();
      await page.keyboard.press("Space");
      await until(`X.values()[${JSON.stringify(tog.param)}] === ${JSON.stringify(other)}`).catch(() => {});
      const st = await page.evaluate(`({ v: ${X}.values()[${JSON.stringify(tog.param)}], playing: ${X}.state.playing, pressed: document.activeElement.getAttribute("aria-pressed") })`);
      check(`${tag0} explore: Space on a focused toggle presses it, not ▶ (D7)`, st.v === other && !st.playing && st.pressed === "true", st);
      await until(`X.state.refused || (X.point() && X.point().values[${JSON.stringify(tog.param)}] === X.values()[${JSON.stringify(tog.param)}])`).catch(() => {});
      await note();
    }
    if (varied) {
      const sl = page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${varied.param}"] .dm-slider`);
      const v0 = (await page.evaluate(`${X}.values()`))[varied.param];
      const clock0 = await page.evaluate(`${X}.state.clock`);
      await sl.focus();
      await page.keyboard.press(varied.values.indexOf(v0) < varied.values.length - 1 ? "ArrowRight" : "ArrowLeft");
      await until(`X.values()[${JSON.stringify(varied.param)}] !== ${JSON.stringify(v0)}`).catch(() => {});
      const st = await page.evaluate(`({ v: ${X}.values()[${JSON.stringify(varied.param)}], clock: ${X}.state.clock, vt: document.activeElement.getAttribute("aria-valuetext") })`);
      check(`${tag0} explore: → on a focused slider moves it, not the time; it tells its value, not its index (D7, F10)`, st.v !== v0 && st.clock === clock0 && !!st.vt && st.vt.includes(String(st.v).replace(".", LANG === "ru" ? "," : ".")), { v0, ...st });
      await until(`X.point() && X.point().values[${JSON.stringify(varied.param)}] === X.values()[${JSON.stringify(varied.param)}]`).catch(() => {});
      await note();
    }
    // D12: at phone width every control on the screen together with the view and the time bar
    if (W < 1000) {
      const bad = [];
      for (const c of mfE.controls) {
        await page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${c.param}"]`).scrollIntoViewIfNeeded();
        await settle(page, 50);
        const vis = await page.evaluate((prm) => {
          const r = (q) => { const e = document.querySelector(`.dm-screen:not([hidden]) ${q}`); if (!e) return null; const b = e.getBoundingClientRect(); return { top: Math.round(b.top), bottom: Math.round(b.bottom) }; };
          return { H: innerHeight, canvas: r(".dm-stage canvas"), ctl: r(`.dm-ctl[data-param="${prm}"]`), bar: r(".dm-bar") };
        }, c.param);
        const inV = (b) => b && b.top >= -1 && b.bottom <= vis.H + 1;
        const overlap = vis.bar && vis.ctl && vis.ctl.bottom > vis.bar.top + 1;
        if (!(inV(vis.canvas) && inV(vis.ctl) && inV(vis.bar)) || overlap) bad.push({ param: c.param, ...vis });
      }
      check(`${tag0} explore (phone): each control on the screen together with the view and the time bar (D12)`, !bad.length, { bad });
    }
    // a refused combination: the manifest's first
    if (firstRefused >= 0) {
      const rv = valuesAt(mfE, firstRefused);
      await pickTo(rv);
      await until("!!X.state.refused");
      await settle(page);
      const ref = await page.locator(".dm-screen:not([hidden]) .dm-refusal-side").innerText();
      const playOff = await page.locator(".dm-screen:not([hidden]) .dm-play").isDisabled();
      const why = tr(mfE.refusals[mfE.points[firstRefused][2] - 1]).trim();
      check(`${tag0} explore: a refused point says why and ▶ is off`, ref.trim() === why && playOff, { values: rv, ref, want: why });
      await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_explore_refused_${LANG}_${tag0}.png` });
    } else skip(`${tag0} explore: a refused point (the grid has none)`);
    // back to the default point, launched
    await pickTo(Object.fromEntries(mfE.controls.map((c) => [c.param, c.default])));
    await until("!X.state.refused");
    await play();
    // the network: only the points shown and their neighbours
    const re = new RegExp(`/atlas/${SID}/p(\\d+)\\.`);
    const pts = reqs.filter((u) => re.test(u)).map((u) => Number(u.match(re)[1]));
    const nb = new Set(shown.flatMap((i) => nbOf(mfE, i)));
    check(`${tag0} explore: only the points shown and their neighbours were fetched`, pts.length > 0 && pts.every((i) => nb.has(i)), { outside: [...new Set(pts)].filter((i) => !nb.has(i)), shown });
    check(`${tag0} explore: no request to the API's live endpoint on the site`, !reqs.some((u) => u.includes("/api/atlas/")));
    // «How we know this is right»: the point's checks
    if (W < 1000) { await page.locator(".dm-menu > summary").click(); await page.locator(".dm-menu-box button").first().click(); }
    else await page.locator(".dm-how").click();
    await settle(page);
    const dr = await page.locator(".dm-drawer-body").innerText();
    const agree = [...Array(200).keys()].some((n) => n > 0 && dr.includes(tr("✓ {n:d} checks agree with the laws", { n })));
    check(`${tag0} explore: the drawer lists the point's checks ✓`, agree && dr.includes(mfE.key), { dr: dr.slice(0, 200) });
    await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_drawer_${LANG}_${tag0}.png` });
    await page.keyboard.press("Escape");
    await common(page, `${tag0} explore`, W, errs);
    // switching tabs keeps the state
    const vals = await page.evaluate(`${X}.values()`);
    const other = viz.screens.find((s) => s.id !== SID);
    await page.locator(`.dm-tab[data-screen="${other.id}"]`).click();
    await page.waitForFunction((s) => document.querySelector(`.dm-screen[data-screen="${s}"]`) && !document.querySelector(`.dm-screen[data-screen="${s}"]`).hidden, other.id, { timeout: 20000 });
    check(`${tag0} the tab is in the address`, new URL(page.url()).searchParams.get("screen") === other.id);
    await page.locator(`.dm-tab[data-screen="${SID}"]`).click();
    check(`${tag0} switching tabs keeps Explore's controls`, JSON.stringify(await page.evaluate(`${X}.values()`)) === JSON.stringify(vals));
    await ctx.close();
  } else skip(`${tag0} explore (the world has no Explore screen)`);
  // --- Explore on the server: snapping near a detent, an off-grid value computed live ----------------------------------
  if (explore && varied) {
    const SID = explore.id;
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs, reqs } = await open(ctx, SID);
    const X = `(window.__lfExplore || {})[${JSON.stringify(SID)}]`;
    const until = (body, timeout = 15000) => page.waitForFunction(`(() => { const X = ${X}; return ${body}; })()`, null, { timeout });
    await until("X && X.point()", 30000);
    const setSlider = (param, v) => page.evaluate(([p, x]) => {
      const s = document.querySelector(`.dm-screen:not([hidden]) .dm-ctl[data-param="${p}"] .dm-slider`);
      s.value = String(x); s.dispatchEvent(new Event("input")); s.dispatchEvent(new Event("change"));
    }, [param, v]);
    const P = JSON.stringify(varied.param), vs = varied.values;
    const k = vs.length > 2 ? 1 : 0, gap = vs[k + 1] - vs[k];
    await setSlider(varied.param, vs[k] + 0.05 * gap);
    await until(`X.point().values[${P}] === ${vs[k]}`);
    check(`${tag0} explore (server): a value near a detent snaps to it`, (await page.evaluate(`${X}.point().live`)) === false);
    const off = Number((vs[k] + 0.5 * gap).toPrecision(3));
    await setSlider(varied.param, off);
    let live = false;
    try {
      await until(`X.point() && X.point().live && X.point().values[${P}] === ${off}`, 90000);
      live = true;
    } catch (e) { live = false; }
    check(`${tag0} explore (server): an off-grid value (${varied.param} ${off}) is computed live`, live && reqs.some((u) => u.includes(`/api/atlas/${WORLD}/${SID}/point`)));
    if (live) {
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();
      await until("!X.state.playing", 60000);
      if (W < 1000) { await page.locator(".dm-menu > summary").click(); await page.locator(".dm-menu-box button").first().click(); }
      else await page.locator(".dm-how").click();
      await settle(page);
      const dr = await page.locator(".dm-drawer-body").innerText();
      const lp = await page.evaluate(`({ key: ${X}.point().key, code: ${X}.point().code, made: ${X}.point().made, source: ${X}.point().source })`);
      check(`${tag0} explore (server): the passport says «computed live», with the point's own key, code and time with its zone (D13)`,
        dr.includes(tr("Computed live on this server at {at}.", { at: "" }).replace(/\.$/, "").trim().split(" ").slice(0, 3).join(" ")) && !!lp.key && dr.includes(lp.key)
        && (!lp.code || dr.includes(lp.code)) && /UTC/.test(dr), { dr: dr.slice(0, 400), lp });
      await page.screenshot({ path: `${SHOTS}/demo_explore_live_${LANG}_${tag0}.png` });
      await page.keyboard.press("Escape");
    }
    // a refused point on the server too: the manifest's first
    if (firstRefused >= 0) {
      const rv = valuesAt(mfE, firstRefused);
      for (const c of mfE.controls) {
        if ((await page.evaluate(`${X}.values()`))[c.param] === rv[c.param]) continue;
        if (isNum(c)) await setSlider(c.param, rv[c.param]); else await choose(page, c, rv[c.param]);
        await until(`X.values()[${JSON.stringify(c.param)}] === ${JSON.stringify(rv[c.param])}`);
      }
      await until("!!X.state.refused", 20000);
      check(`${tag0} explore (server): a refused point says why`, (await page.locator(".dm-screen:not([hidden]) .dm-refusal-side").innerText()).length > 10);
    }
    await common(page, `${tag0} explore (server)`, W, errs);
    await ctx.close();
  }
  // --- Watch -------------------------------------------------------------------------------------------------------
  if (watchScr) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs } = await open(ctx, watchScr.id);
    await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 20000 });
    const caps = await page.evaluate(() => window.__lfWatch.state.story.captions.map((c) => ({ step: c.step, text: c.text, n: c.n })));
    const n = await page.evaluate(() => window.__lfWatch.state.story.steps.length);
    const s0 = await page.evaluate(() => window.__lfWatch.step());
    const hold0 = await page.evaluate(() => (window.__lfWatch.state.story.captions.find((c) => c.step === 0 && c.hold) || {}).hold || 0);
    if (hold0) {  // the first caption's hold: the story waits at its start; ❚❚ then ▶ go on at once (F12)
      await sleep(Math.min(600, 400 * hold0));
      const held = await page.evaluate(() => window.__lfWatch.step());
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();
      await sleep(400);
      const after = await page.evaluate(() => ({ k: window.__lfWatch.step(), btn: document.querySelector(".dm-screen:not([hidden]) .dm-play").textContent }));
      check(`${tag0} watch: the first caption's hold keeps the start; ▶ during it goes on at once`, held === 0 && after.k > 0 && after.btn === "❚❚", { held, after, hold0 });
    } else await sleep(800);
    const s1 = await page.evaluate(() => window.__lfWatch.step());
    check(`${tag0} watch: the recording plays from its start`, s1 > s0, { s0, s1 });
    const capNow = async () => (await page.locator(".dm-screen:not([hidden]) .dm-caption").innerText()).trim();
    check(`${tag0} watch: at least three captions, the first shown at the start`, caps.length >= 3 && caps[0].step === 0, { n: caps.length });
    const ticks = page.locator(".dm-screen:not([hidden]) .dm-tick");
    check(`${tag0} watch: a chapter tick per caption on the timeline`, (await ticks.count()) === caps.length);
    for (const [k, c] of caps.entries()) {
      await ticks.nth(k).click({ force: true });
      await settle(page, 100);
      const got = await capNow();
      check(`${tag0} watch: the caption as of chapter ${k}`, got === tr(c.text).trim(), { got, want: tr(c.text) });
      if (k === 1) await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_watch_${LANG}_${tag0}.png` });
    }
    // the cursor just before caption 1: caption 0; ◀◀ from the end goes to the last caption's frame
    await page.evaluate((k) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(k); s.dispatchEvent(new Event("input")); }, caps[1].step - 1);
    await settle(page, 100);
    check(`${tag0} watch: before a caption's frame, the earlier caption`, (await capNow()) === tr(caps[0].text).trim());
    await page.evaluate((k) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(k); s.dispatchEvent(new Event("input")); }, n - 1);
    await page.locator(".dm-screen:not([hidden]) .dm-chap").first().click();
    await settle(page, 100);
    const m = caps.length;
    check(`${tag0} watch: ◀◀ goes to the previous caption`, (await page.evaluate(() => window.__lfWatch.step())) === caps[m - 1].step);
    await page.locator(".dm-screen:not([hidden]) .dm-chap").first().click();
    await settle(page, 100);
    check(`${tag0} watch: ◀◀ again, the one before`, (await page.evaluate(() => window.__lfWatch.step())) === caps[m - 2].step);
    await page.locator(".dm-screen:not([hidden]) .dm-chap").nth(1).click();
    await settle(page, 100);
    check(`${tag0} watch: ▶▶ goes to the next caption`, (await page.evaluate(() => window.__lfWatch.step())) === caps[m - 1].step);
    // the time label: the world's time and the playback factor (integrator D8)
    const tl = (await page.locator(".dm-screen:not([hidden]) .dm-time").innerText()).trim();
    check(`${tag0} watch: the time label states the world's time and the playback factor`, tl.startsWith(tr("world {t}", { t: "" }).trim())
      && [tr("real time"), tr("slow motion ×{k}", { k: "" }), tr("sped up ×{k}", { k: "" })].some((x) => tl.includes(x.trim())), { tl });
    // the label as Explore's (EX2 §5 F12), read back against the frame shown: at the start, each caption, the end, at
    // normal speed and at «slow»
    const bad = [], seen = [];
    for (const rate of [1, 0.25]) {
      await page.locator(`.dm-screen:not([hidden]) .dm-speed [data-rate="${rate}"]`).click();
      for (const k of [...new Set([0, ...caps.map((c) => c.step), n - 1])]) {
        await page.evaluate((j) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(j); s.dispatchEvent(new Event("input")); }, k);
        await settle(page, 30);
        const lab = (await page.locator(".dm-screen:not([hidden]) .dm-time").innerText()).trim();
        const st = await page.evaluate(() => {
          const V = window.__lfWatch.state, S = V.story, k = window.__lfWatch.step(), { w, i } = S.steps[k], F = S.worlds[w].frames;
          const a = Math.max(0, i - 3), b = Math.min(F.length - 1, i + 3), e = V.rec.entry;
          const fps = (e.fps || 20) / Math.max(1, e.frame_stride || 1);
          return { k, tt: F[i].t, units: (S.worlds[w].header || {}).units || null, r: b > a ? ((F[b].t - F[a].t) / (b - a)) * fps * V.rate : null };
        });
        const why = watchLabelWrong(lab, st, schoolUi);
        if (why) bad.push({ k, rate, lab, why, tt: st.tt, r: st.r });
        if (seen.length < 6) seen.push(lab);
      }
    }
    await page.locator('.dm-screen:not([hidden]) .dm-speed [data-rate="1"]').click();
    check(`${tag0} watch: the time label as Explore's: the frame's world time on its scale, the factor in powers of ten, normal and slow (EX2 F12)`,
      bad.length === 0, { bad: bad.slice(0, 4), seen });
    // a caption's hold stops the playback there; ❚❚ then ▶ during the hold go on at once (review EX1-screens F12)
    const hc = await page.evaluate(() => window.__lfWatch.state.story.captions.find((c) => c.hold && c.step > 0));
    if (hc) {
      await page.evaluate((k) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(Math.max(0, k - 3)); s.dispatchEvent(new Event("input")); }, hc.step);
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();
      await page.waitForFunction((k) => window.__lfWatch.step() === k, hc.step, { timeout: 10000 });
      await sleep(Math.min(600, 500 * hc.hold));
      const held = await page.evaluate(() => window.__lfWatch.step());
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();  // ❚❚
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();  // ▶
      await sleep(400);
      const after = await page.evaluate(() => ({ k: window.__lfWatch.step(), playing: window.__lfWatch.state.playing, btn: document.querySelector(".dm-screen:not([hidden]) .dm-play").textContent }));
      check(`${tag0} watch: a hold stops at its caption; ▶ during the hold goes on at once, the button says so`, held === hc.step && after.playing && after.k > hc.step && after.btn === "❚❚", { held, after, at: hc.step, hold: hc.hold });
    } else skip(`${tag0} watch: a caption's hold (none declared)`);
    await common(page, `${tag0} watch`, W, errs);
    await ctx.close();
  } else skip(`${tag0} watch (the world has no Watch screen)`);
  // --- Lab work ------------------------------------------------------------------------------------------------------
  // every step (review EX1-screens F19): the race of two picks (integrator D6), the keyboard (D7), one row per set-up
  // (D5), the manual stopwatch on the wall clock (F5), each law's own plot checked ✓ and another plot refused (D4), at
  // 390 px «Measure» and the view on the screen together (D12)
  if (lab) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs } = await open(ctx, lab.id);
    const LB = (body, timeout = 15000) => page.waitForFunction(`(() => { const s = window.__lfLab && window.__lfLab.step(); return ${body}; })()`, null, { timeout });
    await LB("s && s.cur", 20000);
    const msgNow = async () => (await page.locator(".dm-screen:not([hidden]) .dm-msg").innerText()).trim();
    await page.locator(".dm-measure").click();
    const msg0 = await msgNow();
    check(`${tag0} lab: «Measure» before the landing says there is nothing to measure yet`, msg0.includes(tr("Nothing to measure yet: “{what}” has not been reached at this moment", { what: "" }).slice(0, 12)), { msg0 });
    const toEnd = async () => { await settle(page, 30); await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); }); await settle(page, 50); };
    const pickAndWait = async (c, v) => {  // a slider's detent, or a select's button (a compound control's values)
      if (await page.evaluate((p) => window.__lfLab.step().values[p], c.param) !== v) await choose(page, c, v);
      await LB(`s.cur && s.cur.pt.values[${JSON.stringify(c.param)}] === ${JSON.stringify(v)} && !s.pending`);
    };
    for (const [k, st] of lab.steps.entries()) {
      const tagS = `${tag0} lab part ${k + 1}`;
      if (k > 0) { await page.locator(".dm-steps button").nth(k).click(); await LB(`s && s.step.id === ${JSON.stringify(st.id)} && s.cur`); }
      const entryS = index.atlases.find((a) => a.id === st.atlas);
      const mf = await get(`/recordings/${WORLD}/${entryS.file}`);
      const lc = mf.controls[0], all = lc.values;
      const manual = st.instruments.some((id) => (lab.instruments[id] || {}).manual);
      check(`${tagS}: a manual stopwatch refuses «slow»`, (await page.locator('.dm-screen:not([hidden]) .dm-speed [data-rate="0.25"]').isDisabled()) === manual);
      if (k === 0 && all.length >= 5 && isNum(lc)) {  // D6: a slow reply of an earlier pick is not applied; «Measure» waits for the set-up
        const d = all.indexOf(lc.default ?? all[0]);
        const far = [...all.keys()].filter((j) => Math.abs(j - d) > 2).sort((a, b) => Math.abs(b - d) - Math.abs(a - d));
        const A = far[0], B = far.find((j) => Math.abs(j - A) > 1);
        if (B !== undefined) {
          const pA = flat(mf, { [lc.param]: all[A] });
          await page.route(new RegExp(`/atlas/${st.atlas.replace(".", "\\.")}/p${pA}\\.`), async (route) => { await sleep(2500); await route.continue(); });
          await detent(page, lc.param, A).click();
          await sleep(150);
          const pending = await page.locator(".dm-measure").isDisabled();
          await detent(page, lc.param, B).click();
          await LB(`s.cur && s.cur.pt.values[${JSON.stringify(lc.param)}] === ${JSON.stringify(all[B])}`);
          await sleep(3000);
          const after = await page.evaluate((p) => { const s = window.__lfLab.step(); return { slider: s.values[p], shown: s.cur.pt.values[p] }; }, lc.param);
          check(`${tagS}: a slower reply of an earlier pick is not shown; «Measure» waited for the set-up (D6)`, pending && after.slider === all[B] && after.shown === all[B], { pending, after });
          await page.unroute(new RegExp(`/atlas/${st.atlas.replace(".", "\\.")}/p${pA}\\.`));
        }
      }
      // the keyboard (D7): the arrows on a focused slider move it and do not launch; Space on a focused «Measure» measures
      if (k === 0 && isNum(lc)) {
        const slider = page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${lc.param}"] .dm-slider`);
        const before = await page.evaluate((p) => { const s = window.__lfLab.step(); return { v: s.values[p], launched: s.cur.launchedAt }; }, lc.param);
        await slider.focus();
        await page.keyboard.press(all.indexOf(before.v) < all.length - 1 ? "ArrowRight" : "ArrowLeft");
        await LB(`s.values[${JSON.stringify(lc.param)}] !== ${JSON.stringify(before.v)} && s.cur && s.cur.pt.values[${JSON.stringify(lc.param)}] === s.values[${JSON.stringify(lc.param)}]`).catch(() => {});
        const moved = await page.evaluate((p) => { const s = window.__lfLab.step(); return { v: s.values[p], launched: s.cur.launchedAt, playing: window.__lfLab.state.playing }; }, lc.param);
        check(`${tagS}: → on a focused slider moves the slider, not the time (D7)`, moved.v !== before.v && moved.launched === null && !moved.playing, { before, moved });
      }
      // the manual stopwatch: launched with the flight, on the wall clock; pause refused while it runs (F5)
      if (manual) {
        await page.locator(".dm-screen:not([hidden]) .dm-play").click();
        await sleep(200);
        await page.evaluate(() => document.activeElement && document.activeElement.blur());
        await page.keyboard.press("Space");
        const refusedPause = await msgNow();
        const stillPlaying = await page.evaluate(() => window.__lfLab.state.playing || (window.__lfLab.step().sw && window.__lfLab.step().sw.running));
        await sleep(600);
        await page.locator(".dm-screen:not([hidden]) .dm-sw-btn").click();
        const sw = await page.evaluate(() => window.__lfLab.step().sw);
        check(`${tagS}: the stopwatch runs on the wall clock; a pause is refused while it runs (F5)`, refusedPause.length > 10 && stillPlaying && sw && sw.stopped && sw.t >= 0.7, { refusedPause, sw });
        await LB("!window.__lfLab.state.playing", 20000);
        // its reading goes into its column (review EX1-worlds F6); a row measured without it leaves the cell empty
        const swCol = st.columns.find((c) => c.from && (lab.instruments[c.from] || {}).manual);
        if (swCol) {
          await page.locator(".dm-measure").click();
          const got = await page.evaluate((cid) => { const r = window.__lfLab.rows(); const x = r[r.length - 1]; return x ? x.cols[cid] : undefined; }, swCol.id);
          check(`${tagS}: «Measure» records the stopwatch's reading in «${swCol.id}»`, !!got && Math.abs(got.v - sw.t) < 0.011, { got, sw: sw.t });
          await page.locator(".dm-del").last().click();  // the set-ups are measured below without the stopwatch
        }
      }
      // measure the set-ups (every one up to 17, else five spread over the grid)
      const hv = all.length <= 17 ? all : [0, 1, 2, 3, 4].map((j) => all[Math.round(j * (all.length - 1) / 4)]);
      const before0 = await page.evaluate(() => window.__lfLab.rows().length);
      const said = [];
      for (const [j, v] of hv.entries()) {
        await pickAndWait(lc, v);
        await toEnd();
        if (j === 0) {  // Space on the focused «Measure» measures (D7)
          await page.locator(".dm-measure").focus();
          await page.keyboard.press("Space");
        } else await page.locator(".dm-measure").click();
        said.push(`${v}: ${await msgNow()}`);
      }
      const rows = await page.evaluate(() => window.__lfLab.rows().length);
      check(`${tagS}: ${hv.length} set-ups measured, one row each`, rows - before0 <= hv.length && rows >= hv.length, { rows, before0, n: hv.length, said });
      // D5: a repeat replaces its row
      await page.locator(".dm-measure").click();
      const rows2 = await page.evaluate(() => window.__lfLab.rows().length);
      const m2 = await msgNow();
      check(`${tagS}: «Measure» again on the same set-up replaces its row and says so (D5)`, rows2 === rows && m2.includes(tr("Row {n:d} replaced: this set-up was already measured; the bench repeats exactly, so a repeat is not a new independent point", { n: 1 }).slice(-30)), { rows, rows2, m2 });
      const cell = await page.locator(".dm-table tbody tr").first().innerText();
      check(`${tagS}: a reading carries its error`, cell.includes("±"), { cell });
      // the fit on each of the step's laws' plots prints its output and no verdict (EX2 §5 F6 (c): the parameters with
      // their σ; at standard χ², dof, p and the Birge ratio, the scaled σ on a line of its own when χ²/dof > 1)
      for (const [j, law] of (st.laws || []).entries()) {
        const sels = page.locator(".dm-screen:not([hidden]) .dm-work select");
        await sels.nth(0).selectOption(law.x); await sels.nth(1).selectOption(law.y); await sels.nth(2).selectOption(law.model);
        await settle(page, 50);
        const res = await page.evaluate(() => { const r = window.__lfLab.fit(); return r ? { birge: r.birge, unit: r.unit, p: r.p } : null; });
        const txt = (await page.locator(".dm-screen:not([hidden]) .dm-fit").innerText()).trim();
        const lines = txt.split("\n").filter(Boolean);
        const wantLines = !res ? 0 : res.unit ? 2 : viz.ui === "school" ? 1 : res.birge > 1 ? 3 : 2;
        check(`${tagS}: law ${j + 1}'s plot (${law.y} against ${law.x}, ${law.model}): the fit prints its output, no verdict`,
          !!res && lines.length === wantLines && lines[0].includes("±") && !/[✓✗]/.test(txt) && !(await page.locator(".dm-check-law").count())
          && (viz.ui === "school" || res.unit || (txt.includes("χ²") && txt.includes("p = "))), { txt: txt.slice(0, 300), res, wantLines });
        if (LANG === "ru") check(`${tagS}: law ${j + 1}'s fit output has no Latin word (F7)`, !/\b(slope|vertex|dof|Birge)\b/.test(txt), { txt: txt.slice(0, 200) });
      }
      if (!(await page.locator(".dm-check-law").count())) check(`${tagS}: no «Check against the law» anywhere in Lab work (the owner, 2026-11-18)`, !(await page.locator(".dm-screen:not([hidden])").innerText()).includes(tr("Check against the law")));
      const plotInk = await page.evaluate(() => { const c = document.querySelector(".dm-screen:not([hidden]) .dm-plot"); const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data; const s = new Set(); for (let i = 0; i < d.length; i += 64) s.add(d[i] << 16 | d[i + 1] << 8 | d[i + 2]); return s.size; });
      check(`${tagS}: the plot is drawn`, plotInk > 3, { colours: plotInk });
      const csvHref = await page.locator('a[download$=".csv"]').getAttribute("href");
      const csv = decodeURIComponent(csvHref.replace(/^data:text\/csv;charset=utf-8,/, ""));
      check(`${tagS}: the CSV has the rows and the errors`, csv.trim().split("\n").length === rows + 1 && csv.split("\n")[0].includes("σ"));
      const swCol2 = st.columns.findIndex((c) => c.from && (lab.instruments[c.from] || {}).manual);
      if (swCol2 >= 0) {  // measured without the stopwatch: an empty cell, «—» in the table, never 0
        const line = csv.trim().split("\n")[1].split(",");
        const td = await page.locator(".dm-screen:not([hidden]) .dm-table tbody tr").first().locator("td").nth(swCol2 + 1).innerText();
        check(`${tagS}: a row without a stopwatch reading has an empty time («—», empty in the CSV)`, line[2 * swCol2] === "" && td.trim() === "—", { td, line });
      }
      // the drawer of Lab work lists the events with their times, as Explore does (the owner, 2026-11-18: a lab is a
      // bench, nothing is hidden; EX1's D10 withdrawn)
      if (W >= 1000) {
        await page.locator(".dm-how").click();
        await settle(page);
        const evs = await page.$$eval(".dm-drawer-body .dm-ev", (a) => a.map((e) => ({ mono: !!e.querySelector(".mono"), text: e.textContent })));
        check(`${tagS}: the drawer's events have their times in Lab work, as in Explore`, evs.every((e) => e.mono), { evs: evs.slice(0, 3) });
        await page.keyboard.press("Escape");
      }
      // D12: at phone width «Measure» and the view on the screen together, with the time bar
      if (W < 1000) {
        await page.locator(".dm-screen:not([hidden]) .dm-ctl").first().scrollIntoViewIfNeeded();
        await settle(page);
        const vis = await page.evaluate(() => {
          const r = (q) => { const e = document.querySelector(`.dm-screen:not([hidden]) ${q}`); if (!e) return null; const b = e.getBoundingClientRect(); return { top: b.top, bottom: b.bottom }; };
          return { H: innerHeight, canvas: r(".dm-stage canvas"), measure: r(".dm-measure"), bar: r(".dm-bar"), ctl: r(".dm-ctl"), stop: r(".dm-sw-btn") };
        });
        const inView = (b) => b && b.top >= -1 && b.bottom <= vis.H + 1;
        check(`${tagS} (phone): the view, a control, «Measure»${manual ? ", «⏱ Stop»" : ""} and the time bar on the screen together (D12)`,
          inView(vis.canvas) && inView(vis.measure) && inView(vis.bar) && inView(vis.ctl) && (!manual || inView(vis.stop)), vis);
      }
      await page.evaluate(() => { document.querySelector(".dm-screens").scrollTop = 0; window.scrollTo(0, 0); });
      await settle(page);
      await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_lab${k + 1}_${LANG}_${tag0}.png` });
      await page.evaluate(() => { document.querySelector(".dm-screens").scrollTop = 1e6; window.scrollTo(0, 1e6); });
      await settle(page);
      await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_lab${k + 1}_table_${LANG}_${tag0}.png` });
    }
    const tb = await page.evaluate(() => { const b = document.querySelector(".dm-screen:not([hidden]) .dm-table-box"); return { sw: b.scrollWidth, cw: b.clientWidth }; });
    check(`${tag0} lab: the table scrolls inside its box`, tb.cw <= W);
    // D7: Space on a focused tab opens it (the tab's own key), not the playback
    const tabOther = viz.screens.find((s) => s.id !== lab.id);
    if (tabOther) {
      await page.locator(`.dm-tab[data-screen="${tabOther.id}"]`).focus();
      await page.keyboard.press("Space");
      await page.waitForFunction((sid) => !document.querySelector(`.dm-screen[data-screen="${sid}"]`)?.hidden, tabOther.id, { timeout: 15000 }).catch(() => {});
      check(`${tag0}: Space on a focused tab opens that tab (D7)`, new URL(page.url()).searchParams.get("screen") === tabOther.id);
      await page.locator(`.dm-tab[data-screen="${lab.id}"]`).click();
    }
    await common(page, `${tag0} lab`, W, errs);
    await ctx.close();
  } else skip(`${tag0} lab work (the world has no Lab work screen)`);
  // --- EX2 (design lfphys/sources/explore_EX2_2026-11-18_design.md §5, §7) -----------------------------------------
  // every Explore screen: its compound controls (their values' names, the parameters a value sets in the point and in
  // the passport), its time label (the world's time, the playback factor with normal and slow), readouts with their
  // error and reference, a stop by counted events, «CSV of this point» (standard only); Lab work: counters (√N), the
  // run's own σ, formula columns (an empty cell says why, empty in the CSV), the drawer as Explore's (every check's value
  // and reference, the events with their texts and times: the owner, 2026-11-18), «MODIFIED PHYSICS» on a modified step
  // (F6). A feature the world has not is skipped with a line.
  for (const ex of (viz.screens || []).filter((x) => x.kind === "explore")) {
    const compound = (ex.controls || []).filter((c) => c.sets);
    const declared = ex.speed !== undefined && ex.speed !== null;
    const csvWanted = viz.ui === "standard";
    const entryX = index.atlases.find((a) => a.id === ex.atlas);
    const mfX = await get(`/recordings/${WORLD}/${entryX.file}`);
    const tagX = `${tag0} explore «${ex.id}» (EX2)`;
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs } = await open(ctx, ex.id);
    const X = `(window.__lfExplore || {})[${JSON.stringify(ex.id)}]`;
    const until = (body, timeout = 15000) => page.waitForFunction(`(() => { const X = ${X}; return ${body}; })()`, null, { timeout });
    await until("X && X.point()", 30000);
    const playToEnd = async () => {
      if (await page.evaluate(`${X}.state.refused`)) return;
      await page.locator(".dm-screen:not([hidden]) .dm-play").click();
      await until("!X.state.playing && X.state.cur && X.state.cur.launchedAt !== null", 60000);
      await settle(page);
    };
    const tlabel = async () => (await page.locator(".dm-screen:not([hidden]) .dm-time").innerText()).trim();
    // the time label (F1)
    if (declared) {
      await page.locator('.dm-screen:not([hidden]) .dm-speed [data-rate="1"]').click();
      const l1 = await tlabel();
      await page.locator('.dm-screen:not([hidden]) .dm-speed [data-rate="0.25"]').click();
      await settle(page, 50);
      const l2 = await tlabel();
      await page.locator('.dm-screen:not([hidden]) .dm-speed [data-rate="1"]').click();
      const factor = (x) => { const m = /×\s?([\d.,·⁰-⁹⁻]+)/.exec(x); return m ? m[1] : null; };
      check(`${tagX}: the time label states the world's time and the playback factor; «slow» makes it four times slower (F1)`,
        l1.startsWith(tr("world {t}", { t: "" }).trim()) && [tr("real time"), tr("slow motion ×{k}", { k: "" }).trim(), tr("sped up ×{k}", { k: "" }).trim()].some((x) => l1.includes(x))
        && l1 !== l2 && factor(l1) !== factor(l2), { l1, l2 });
      const pt = await page.evaluate(`({ speed: ${X}.point().speed, want: ${JSON.stringify(ex.speed)} })`);
      check(`${tagX}: the point knows the world's default speed (its state message), for a «world» speed`, ex.speed !== "world" || pt.speed > 0, pt);
    } else skip(`${tagX}: the time label (no speed declared)`);
    // compound controls (F3)
    for (const c of compound) {
      const names = await page.$$eval(`.dm-screen:not([hidden]) .dm-ctl[data-param="${c.param}"] .dm-ctl-seg button, .dm-screen:not([hidden]) .dm-ctl[data-param="${c.param}"] .dm-detent`, (a) => a.map((x) => x.getAttribute("title") || x.textContent));
      check(`${tagX}: the compound control «${c.param}» names its values`, !c.labels || c.labels.every((l) => names.includes(tr(l))), { names });
      const cur = (await page.evaluate(`${X}.values()`))[c.param];
      const k = (c.values.indexOf(cur) + 1) % c.values.length, v = c.values[k];
      await choose(page, c, v);
      await until(`X.state.refused || (X.point() && X.point().values[${JSON.stringify(c.param)}] === ${JSON.stringify(v)})`);
      const params = await page.evaluate(`${X}.state.refused ? null : ${X}.point().W.header.params`);
      const want = Object.fromEntries(Object.entries(c.sets).map(([p, list]) => [p, list[k]]));
      check(`${tagX}: «${c.param}» = ${JSON.stringify(v)} sets ${JSON.stringify(want)} in the point shown`, params === null || Object.entries(want).every(([p, x]) => params[p] === x), { params, want });
      if (W >= 1000 && params) {
        await page.locator(".dm-how").click();
        await settle(page);
        const dr = await page.locator(".dm-drawer-body").innerText();
        const setNames = Object.keys(c.sets).map((p) => tr(((viz.schema.params || []).find((x) => x.id === p) || { label: p }).label));
        check(`${tagX}: the passport names the parameters «${c.param}» set`, setNames.every((x) => dr.includes(x)), { setNames, dr: dr.slice(-400) });
        await page.keyboard.press("Escape");
      }
    }
    if (!compound.length) skip(`${tagX}: compound controls (none)`);
    await playToEnd();
    // readouts with an error and a reference (F7)
    const decl = await page.evaluate(`${X}.point() && ${X}.point().W ? ${X}.point().W.header.measurables || [] : []`);
    const shownR = decl.filter((m) => (ex.readouts || []).includes(m.id));
    const withE = shownR.filter((m) => m.sigma), withR = shownR.filter((m) => m.ref);
    if (withE.length || withR.length) {
      const got = {};
      for (const m of shownR) got[m.id] = (await page.locator(`.dm-screen:not([hidden]) [data-readout="${m.id}"]`).innerText()).replace(/\s+/g, " ");
      check(`${tagX}: a readout with the run's error shows «±», one with a reference names it (F7)`,
        withE.every((m) => got[m.id].includes("±") || got[m.id].includes("—")) && withR.every((m) => got[m.id].includes(`(${m.ref_label ? tr(m.ref_label) : tr("reference")}`) || got[m.id].includes("—"))
        && [...withE, ...withR].some((m) => !got[m.id].includes("—")), got);
    } else skip(`${tagX}: readouts with an error or a reference (none)`);
    // a stop by counted events (F2): the point ends after_s after the first kind to reach its count (or its own frame)
    const evs = ex.stop && ex.stop.events;
    if (evs) {
      const r = await page.evaluate(`(() => { const W = ${X}.point().W, out = {}; for (const e of W.events) { for (const k of [e.kind, e.name]) if (k in ${JSON.stringify(evs)}) (out[k] = out[k] || []).push(e.t); } return { out, tEnd: ${X}.point().tEnd, dt: W.frames.length > 1 ? W.frames[1].t - W.frames[0].t : 0 }; })()`);
      const firsts = Object.entries(evs).map(([k, n]) => (r.out[k] || [])[n - 1]).filter((x) => x !== undefined);
      const stopT = Math.min(...firsts) + (ex.stop.after_s || 0);
      check(`${tagX}: the point stops after_s after the first counted event kind (F2)`, firsts.length > 0 && r.tEnd >= stopT - 1e-9 && r.tEnd <= stopT + r.dt + 1e-9, { ...r, stopT });
    } else skip(`${tagX}: a stop by counted events (none)`);
    // «CSV of this point» (F7): standard only, one row per frame up to the time shown
    const btn = page.locator(".dm-screen:not([hidden]) .dm-point-csv");
    if (csvWanted) {
      await btn.scrollIntoViewIfNeeded().catch(() => {});
      await btn.click({ modifiers: [] }).catch(() => {});
      const href = await btn.getAttribute("href");
      const text = href ? decodeURIComponent(href.replace(/^data:text\/csv;charset=utf-8,/, "")) : "";
      const lines = text.trim().split("\n");
      const n = await page.evaluate(`(() => { const p = ${X}.point(), F = p.W.frames, tt = Math.min(p.tEnd, ${X}.state.clock - (${X}.state.cur.launchedAt ?? 0)); return F.filter((f) => f.t <= tt + 1e-9).length; })()`);
      check(`${tagX}: «CSV of this point» has t and the declared measurables, with σ, one row per frame shown (F7)`, lines.length === n + 1
        && lines[0].startsWith(`"${tr("t, {unit}", { unit: tr("s") })}"`) && (!decl.some((m) => m.sigma) || lines[0].includes("σ ")), { head: lines[0], rows: lines.length - 1, frames: n });
    } else check(`${tagX}: no «CSV of this point» at school`, (await btn.count()) === 0);
    await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_ex2_${ex.id}_${LANG}_${tag0}.png` });
    await common(page, `${tagX}`, W, errs);
    await ctx.close();
  }
  if (lab) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs } = await open(ctx, lab.id);
    const LB = (body, timeout = 15000) => page.waitForFunction(`(() => { const s = window.__lfLab && window.__lfLab.step(); return ${body}; })()`, null, { timeout });
    await LB("s && s.cur", 20000);
    const toEnd = async () => { await settle(page, 30); await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); }); await settle(page, 50); };
    for (const [k, st] of lab.steps.entries()) {
      const tagS = `${tag0} lab part ${k + 1} (EX2)`;
      if (k > 0) { await page.locator(".dm-steps button").nth(k).click(); await LB(`s && s.step.id === ${JSON.stringify(st.id)} && s.cur`); }
      const counters = st.instruments.filter((id) => (lab.instruments[id] || {}).kind === "counter");
      const sigmas = st.instruments.filter((id) => (lab.instruments[id] || {}).sigma);
      const formulas = st.columns.filter((c) => c.expr);
      if (counters.length || sigmas.length || formulas.length) {
        const entryS = index.atlases.find((a) => a.id === st.atlas);
        const mf = await get(`/recordings/${WORLD}/${entryS.file}`);
        const lc = mf.controls[0];
        await page.locator(".dm-screen:not([hidden]) .dm-work button").filter({ hasText: tr("Clear the table") }).click().catch(() => {});
        for (const v of lc.values.slice(0, 17)) {
          if (await page.evaluate((p) => window.__lfLab.step().values[p], lc.param) !== v) await choose(page, lc, v);
          await LB(`s.cur && s.cur.pt.values[${JSON.stringify(lc.param)}] === ${JSON.stringify(v)} && !s.pending`);
          await toEnd();
          await page.locator(".dm-measure").click();
        }
        const rows = await page.evaluate(() => window.__lfLab.rows());
        const cells = await page.$$eval(".dm-screen:not([hidden]) .dm-table tbody tr", (trs) => trs.map((tr) => [...tr.querySelectorAll("td")].map((td) => ({ text: td.innerText.trim(), undef: td.classList.contains("dm-undef"), why: (td.querySelector(".dm-why") || {}).textContent || "" }))));
        const colIdx = (id) => st.columns.findIndex((c) => c.id === id) + 1;
        for (const id of counters) {
          const c = st.columns.find((x) => x.from === id), i = lab.instruments[id];
          if (!c) continue;
          const okc = rows.every((r) => !r.cols[c.id] || (Number.isInteger(r.cols[c.id].v) && Math.abs(r.cols[c.id].e - (i.error === "poisson" ? (r.cols[c.id].v > 0 ? Math.sqrt(r.cols[c.id].v) : 1) : Number(i.error))) < 1e-12));
          const texts = cells.map((r) => r[colIdx(c.id)].text);
          check(`${tagS}: the counter «${id}» reads whole counts with ${i.error === "poisson" ? "√N" : "its exact count"} (F4)`, okc && texts.every((x) => (i.error === "poisson" ? /^\d[\d,\s ]* ± \d/.test(x) : /^\d+$/.test(x))), { texts });
        }
        for (const id of sigmas) {
          const c = st.columns.find((x) => x.from === id);
          if (!c) continue;
          check(`${tagS}: the readout «${id}» carries the run's own error (F4)`, rows.every((r) => r.cols[c.id] && r.cols[c.id].e > 0) && cells.every((r) => r[colIdx(c.id)].text.includes("±")), { texts: cells.map((r) => r[colIdx(c.id)].text) });
        }
        if (formulas.length) {
          const undef = cells.flat().filter((x) => x.undef);
          const okF = rows.every((r) => formulas.every((f) => (r.cols[f.id] && Number.isFinite(r.cols[f.id].v) && r.cols[f.id].e >= 0) || (r.why && r.why[f.id])));
          check(`${tagS}: formula columns have values with errors, an undefined cell is empty with its reason (F5)`, okF && undef.every((x) => x.text.startsWith("—") && x.why.length > 5), { undef: undef.slice(0, 2) });
          if (WORLD === "s98_atlas_toy" && st.id === "ticks") check(`${tagS}: the toy's √(n − 2.5) is empty at n = 2, with its reason`, undef.length >= 1 && undef[0].why === tr("the square root of a negative number"), { undef });
          const csvHref = await page.locator('.dm-screen:not([hidden]) a[download$=".csv"]').first().getAttribute("href");
          const text = decodeURIComponent(csvHref.replace(/^data:text\/csv;charset=utf-8,/, ""));
          check(`${tagS}: the CSV leaves an undefined cell empty, never «null» (F5)`, !text.includes("null") && !text.includes("NaN"));
        }
        // the fit on the law's plot, with the counted and computed columns: its parameters with errors (no verdict)
        for (const law of st.laws || []) {
          const sels = page.locator(".dm-screen:not([hidden]) .dm-work select");
          await sels.nth(0).selectOption(law.x); await sels.nth(1).selectOption(law.y); await sels.nth(2).selectOption(law.model);
          await settle(page, 50);
          const r = await page.evaluate(() => { const x = window.__lfLab.fit(); return x ? { params: x.params, s: x.sigmaDeclared } : null; });
          check(`${tagS}: the fit «${law.model}» of ${law.y} against ${law.x} on the counted and computed columns`, !!r && Object.values(r.params).every(Number.isFinite), r);
        }
      } else skip(`${tagS}: counters, the run's σ and formula columns (none)`);
      // F6: the modified-physics band of a step whose points carry modifications
      const mods = await page.evaluate(() => { const s = window.__lfLab.step(); return (s.cur && s.cur.pt.W && s.cur.pt.W.header.modifications) || []; });
      await settle(page);
      const band = await page.evaluate(() => { const b = document.querySelector(".dm-screen:not([hidden]) .dm-lab-mod"); return { shown: !!b && !b.hidden, text: b ? b.textContent : "", body: document.body.classList.contains("dm-modified") }; });
      if (mods.length) check(`${tagS}: «MODIFIED PHYSICS» on the step card and in the bar (F6)`, band.shown && band.text.startsWith(tr("MODIFIED PHYSICS:")) && band.body, band);
      else check(`${tagS}: no «MODIFIED PHYSICS» band on accepted physics`, !band.shown && !band.body, band);
      // the drawer of Lab work is Explore's (the owner, 2026-11-18): at the point's end, every check of the point with
      // its value and reference (the table at standard, the list with the notes at school), the events with their times
      if (W >= 1000) {
        await toEnd();
        await page.locator(".dm-how").click();
        await settle(page);
        const dr = await page.evaluate(() => ({ rows: document.querySelectorAll(".dm-drawer-body .dm-ck-table tr").length - (document.querySelector(".dm-drawer-body .dm-ck-table") ? 1 : 0),
          items: document.querySelectorAll(".dm-drawer-body .dm-ck-list li").length,
          evs: [...document.querySelectorAll(".dm-drawer-body .dm-ev")].map((e) => ({ mono: !!e.querySelector(".mono"), text: e.textContent.trim() })) }));
        const nCk = await page.evaluate(() => window.__lfLab.step().cur.pt.W.checks.size);
        const nEv = await page.evaluate(() => window.__lfLab.step().cur.pt.W.events.length);
        check(`${tagS}: the drawer of Lab work shows every check of the point, with its value at standard, and the events with their times, as Explore (the owner, 2026-11-18)`,
          (viz.ui === "school" ? dr.items : dr.rows) === nCk && dr.evs.length === nEv && dr.evs.every((e) => e.mono), { ...dr, evs: dr.evs.slice(0, 3), nCk, nEv });
        // «Computed for this bench» (F6 (d)): the step's laws with the atlas's references, in the drawer only
        const comp = await page.$$eval(".dm-drawer-body .dm-computed-list li", (a) => a.map((li) => ({ law: li.dataset.law, text: li.textContent })));
        const refs = await page.evaluate(() => { const s = window.__lfLab.step(); return s.A ? s.A.manifest.references || {} : {}; });
        const key = (law) => (st.shared ? `${st.id}/${law.reference}` : law.reference);
        const want = (st.laws || []).filter((law) => refs[key(law)]);
        check(`${tagS}: «Computed for this bench» lists the step's laws with the world's values (F6 (d))`, comp.length === want.length
          && want.every((law) => comp.some((c) => c.law === law.reference && c.text.includes(tr(law.label === undefined ? "" : refs[key(law)].label)))), { comp: comp.slice(0, 3), want: want.length });
        check(`${tagS}: the computed values are not beside the student's fit`, !(await page.locator(".dm-screen:not([hidden]) .dm-work .dm-computed-list").count()));
        await page.keyboard.press("Escape");
      }
    }
    await common(page, `${tag0} lab (EX2)`, W, errs);
    await ctx.close();
  }
  // the teacher's variant from the address (EX2 §5 F8 (b)): run.html?…&screen=lab&variant=<id> preselects its controls
  for (const v of (lab && !lab.worksheet.ex1 ? lab.worksheet.variants || [] : []).filter((x) => x.values)) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs } = await open(ctx, lab.id, `&variant=${v.id}`);
    await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 20000 });
    const firstId = v.steps ? v.steps[0] : lab.steps[0].id;
    const got = await page.evaluate(() => ({ step: window.__lfLab.step().step.id, values: window.__lfLab.step().values, shown: window.__lfLab.step().cur.pt.values }));
    const want = v.values[firstId] || {};
    check(`${tag0} lab: &variant=${v.id} opens its first step with its controls preselected, the point shown (nothing locked)`, got.step === firstId
      && Object.entries(want).every(([k, x]) => got.values[k] === x && got.shown[k] === x)
      && !(await page.locator(".dm-screen:not([hidden]) .dm-ctl input:disabled, .dm-screen:not([hidden]) .dm-ctl button:disabled").count()), { got, want });
    const href = await page.locator(".dm-screen:not([hidden]) .dm-ws a").getAttribute("href");
    check(`${tag0} lab: the task sheet's link keeps the variant`, (href || "").includes(`variant=${v.id}`), { href });
    await common(page, `${tag0} lab variant ${v.id}`, W, errs);
    await ctx.close();
  }
  // --- the task sheet (EX2 §5 F8) ---------------------------------------------------------------------------------------
  // one A4 page per sheet (the head and the task, each part, «Computed for this bench» when asked for), each with the
  // attribution line, no sheet overflowing its page, record_rows blank rows per part (review EX1-screens F6, EX1-worlds F7)
  if (W >= 1000 && lab) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", (e) => errs.push(e.message));
    const pages = (b) => (b.toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []).length;
    const sheets = () => page.evaluate(() => [...document.querySelectorAll(".ws .sheet")].filter((x) => getComputedStyle(x).display !== "none").map((x) => {
      const b = x.querySelector(".sheet-body");
      return { cls: x.className, over: b.scrollHeight - b.clientHeight, credit: !!x.querySelector(".credit"), rows: [...x.querySelectorAll("table.blank tr")].length - (x.querySelector("table.blank") ? 1 : 0), cols: x.querySelector("table.blank") ? x.querySelectorAll("table.blank tr:first-child th").length - 1 : 0 };
    }));
    const printed = async (tag) => {
      await page.emulateMedia({ media: "print" });
      await page.setViewportSize({ width: 703, height: 1000 });  // A4's width less the page's margins (186 mm): the printed layout
      const sh = await sheets();
      await page.setViewportSize({ width: W, height: H });
      const pdf = await page.pdf({ format: "A4" });
      await page.emulateMedia({ media: "screen" });
      check(`worksheet${tag}: one A4 page per sheet, none overflowing, each with the attribution line`, pages(pdf) === sh.length && sh.every((x) => x.over <= 1 && x.credit), { pages: pages(pdf), sheets: sh });
      return { pdf, sh };
    };
    await page.goto(inLang(`${base}/worksheet?demo=${WORLD}`));
    await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
    const txt = await page.locator("#ws").innerText();
    const WS = lab.worksheet;
    const frp0 = (WS.frp || [])[0], basis0 = (WS.basis || [])[0];
    // the task sheet (EX2 §5 F8): the head with the programme (school) or the basis (university), the goal, the bench,
    // the procedure, the record list; no questions, answers or teacher's pages
    const task = [tr(WS.goal), ...(WS.bench || []).map(tr), ...(WS.procedure || []).map(tr), ...(WS.record || []).map(tr)];
    check("task sheet: the goal, the bench, the procedure and the record list in the language, the parts' titles", task.every((x) => txt.includes(x))
      && lab.steps.every((st) => txt.includes(tr(st.title))) && !txt.includes("[object"), { missing: task.filter((x) => !txt.includes(x)).slice(0, 2) });
    if (frp0) check("task sheet: the programme's lab by its name (no raw id)", txt.includes(tr(frp0.name)) && (!frp0.programme || txt.includes(tr(frp0.programme))) && !txt.includes(frp0.system));
    else {  // a university sheet names its basis, its words quoted verbatim in their own language (EX2 §5 F8)
      const q = await page.evaluate(() => [...document.querySelectorAll(".ws .basis q.quote")].map((e) => ({ text: e.textContent, lang: e.lang })));
      check("task sheet (university): its basis, the source and the quotation verbatim in its language", !!basis0
        && txt.includes(tr(basis0.text)) && txt.includes(tr(basis0.source)) && (!basis0.quote || q.some((x) => x.text === basis0.quote && x.lang === (basis0.quote_lang || "en"))), { q });
    }
    check("task sheet: no questions, answers or teacher's pages (the owner, 2026-11-18)", !(await page.locator(".ws .teacher, .ws .answer").count())
      && !txt.includes(tr("For the teacher")) && !txt.includes(tr("Answers")));
    // every instrument as the step card writes it: an exact one with its reason, never «±0» (V52 (y)); a counter's √N
    const instrTxt = (await page.locator(".ws .instr").allInnerTexts()).join(" | ");
    check("task sheet: no instrument says «±0» (V52 (y)); a counter's line its √N (EX2 §5 F4)", !/±\s?0(?![.,\d])/.test(instrTxt)
      && (!Object.values(lab.instruments).some((i) => i.kind === "counter" && i.error === "poisson") || instrTxt.includes(tr("counts; error √N (a count of 0 has the error of one count)"))), { instrTxt: instrTxt.slice(0, 300) });
    const { pdf: pdf0, sh: sh0 } = await printed("");
    const parts = sh0.filter((x) => x.cls.includes("part"));
    check("task sheet: a sheet per part, record_rows blank rows each", parts.length === lab.steps.length && parts.every((x) => x.rows === (WS.record_rows || 10)), { rows: parts.map((x) => x.rows), want: WS.record_rows });
    writeFileSync(`${SHOTS}/worksheet_${WORLD}_${LANG}.pdf`, pdf0);
    if (LANG === "en") check("task sheet: no Cyrillic but the programme's own wording", !CYR.test(txt.replace(/«[^»]*»/g, "")));  // i18n-ok: the quoted original
    else check("task sheet: no Latin unit or raw id in the Russian text (F7)", !/\bm\^½|\bFRP-|\b(slope|vertex)\b/.test(txt.replace(/“[^”]*”/g, "")), { sample: (txt.match(/.{0,30}(m\^½|FRP-|slope|vertex).{0,30}/) || [""])[0] });
    await page.screenshot({ path: `${SHOTS}/worksheet_${WORLD}_${LANG}.png`, fullPage: true });
    // the sheet is editable before printing: an edit prints, is kept in this browser, and «Restore the original» undoes it
    const mark = "EDITED-BY-THE-TEST";
    await page.locator('.ws .editable[data-edit="goal"]').click();
    await page.keyboard.press("End");
    await page.keyboard.type(` ${mark}`);
    await page.locator('.ws .editable[data-edit="teacher_task"]').click();
    await page.keyboard.type(mark);
    await page.reload();
    await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
    const kept = (await page.locator('.ws .editable[data-edit="goal"]').innerText()).includes(mark) && (await page.locator('.ws .editable[data-edit="teacher_task"]').innerText()).includes(mark);
    await page.emulateMedia({ media: "print" });
    const printedTxt = await page.locator("#ws").innerText();
    await page.emulateMedia({ media: "screen" });
    await page.locator(".ws-restore").click();
    const restored = !(await page.locator("#ws").innerText()).includes(mark);
    await page.reload();
    await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
    check("task sheet: an edit is kept in this browser and prints; «Restore the original» restores the original", kept && printedTxt.includes(mark) && restored
      && !(await page.locator("#ws").innerText()).includes(mark), { kept, restored });
    // «Computed for this bench» on a page of its own (&computed=1)
    await page.goto(inLang(`${base}/worksheet?demo=${WORLD}&computed=1`));
    await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
    const comp = await page.locator(".ws .sheet.computed").innerText().catch(() => "");
    const nLaws = lab.steps.reduce((n, st) => n + (st.laws || []).length, 0);
    const { pdf: pdfC } = await printed(" (computed)");
    check("task sheet: &computed=1 prints the world's computed values for the bench on a page of their own", comp.includes(tr("Computed for this bench"))
      && (nLaws === 0 || (await page.locator(".ws .sheet.computed li").count()) === nLaws) && pages(pdfC) === pages(pdf0) + 1, { comp: comp.slice(0, 300), nLaws });
    // a variant (the teacher's task): its label and id, the set-up it preselects, its own goal
    for (const v of WS.variants || []) {
      await page.goto(inLang(`${base}/worksheet?demo=${WORLD}&variant=${v.id}`));
      await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
      const vt = await page.locator("#ws").innerText();
      const { sh } = await printed(` variant ${v.id}`);
      const vsteps = lab.steps.filter((st) => !v.steps || v.steps.includes(st.id));
      check(`task sheet variant ${v.id}: its label and id, its steps, its goal, the set-up it preselects`, vt.includes(tr("Variant {id}: {label}", { id: v.id, label: tr(v.label) }))
        && sh.filter((x) => x.cls.includes("part")).length === vsteps.length && (!v.text || !v.text.goal || vt.includes(tr(v.text.goal)))
        && (!v.values || (await page.locator(".ws .preset").count()) === Object.keys(v.values).filter((sid) => vsteps.some((st) => st.id === sid)).length), { vt: vt.slice(0, 200) });
      await page.screenshot({ path: `${SHOTS}/worksheet_${WORLD}_${v.id}_${LANG}.png`, fullPage: true });
    }
    check("worksheet: no page error", errs.length === 0, { errs });
    await ctx.close();
  }
  if (W < 1000 && lab) {  // the worksheet at phone width: no horizontal scroll
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const page = await ctx.newPage();
    await page.goto(inLang(`${base}/worksheet?demo=${WORLD}`));
    await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
    const sw = await page.evaluate(() => document.scrollingElement.scrollWidth);
    check(`${tag0} worksheet: no horizontal scroll`, sw <= W, { sw });
    await page.screenshot({ path: `${SHOTS}/worksheet_${WORLD}_${LANG}_${tag0}.png`, fullPage: true });
    await ctx.close();
  }
}

await br.close();
console.log(failed ? `FAILED: ${failed}` : "all passed");
process.exit(failed ? 1 : 0);
