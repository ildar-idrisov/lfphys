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
//  - Lab work (its first step): «Measure» before a launch says there is nothing to measure yet; up to five values of the
//    step's control measured → as many rows with ±; the plot drawn, the step's fit gives b ± σ; «Check against the law» ✓
//    against the reference of the step's atlas; a manual stopwatch, when the step has one, refuses «slow»;
//  - the worksheet: printed (page.pdf) without and with the teacher's answers (on pages of their own: one page more for a
//    one-step lab), its texts in the language;
//  - every screen: no horizontal scroll (scrollWidth ≤ the window's width), no page error, in English no Cyrillic in
//    the visible text and in Russian the tabs' Russian labels; screenshots of every screen per language and size.
//
// Run against a PRIVATE server with the toy world and its built atlases (never the shared one on 8479):
//   docker run -d --name lf-p3-srv --memory=6g -p 8692:8479 -v <repo>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
//     -e LFPHYS_NO_GPU=1 -e LFVIZ_EXTRA=/lf/visualizations/tests/site_worlds \
//     -e LFVIZ_RECORDINGS=/lf/visualizations/tests/site_worlds/recordings \
//     -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
//   docker run --rm --init --shm-size=2g --network host --memory=4g -v <scratch with node_modules/playwright@1.58.2>:/pw \
//     -v <repo>/visualizations/tests/browser:/t:ro -w /pw -e LFVIZ_LANG=en|ru -e SHOTS=/pw/shots \
//     mcr.microsoft.com/playwright:v1.58.2-jammy sh -c "cp /t/*.mjs /pw/ && node /pw/demo_screens.mjs 8692 [1280x800,390x844] [world]"
//   For s03_projectile and u32_double_slit the server needs their recordings (visualizations/recordings, the default, or
//   LFVIZ_RECORDINGS); for the toy, LFVIZ_RECORDINGS=…/tests/site_worlds/recordings.
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
  else check(`${tag}: the tabs in Russian`, viz.screens.map((s) => tr({ watch: "Watch", explore: "Explore", lab: "Lab work" }[s.kind])).every((s) => txt.includes(s)) && CYR.test(txt));
  check(`${tag}: no page error`, errs.length === 0, { errs });
}
// a slider's control row by its parameter; a detent by its value
const detent = (page, param, k) => page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${param}"] .dm-detent`).nth(k);
// choose a grid value of a control: its detent (a slider) or its button (a toggle, a select)
const choose = (page, c, v) => (isNum(c) ? detent(page, c.param, c.values.indexOf(v))
  : page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${c.param}"] .dm-ctl-seg button[data-value='${JSON.stringify(v)}']`)).click();

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
      }
    };
    await note();
    const tabs = await page.locator(".dm-tab").allInnerTexts();
    const want = viz.screens.map((s) => tr({ watch: "Watch", explore: "Explore", lab: "Lab work" }[s.kind]));
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
    check(`${tag0} explore: only the points shown and their neighbours were fetched`, pts.length > 0 && pts.every((i) => nb.has(i)), { fetched: [...new Set(pts)].slice(0, 40), shown });
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
      check(`${tag0} explore (server): the passport says «computed live»`, dr.includes(tr("Computed live on this server at {at}.", { at: "" }).replace(/\.$/, "").trim()), { dr: dr.slice(0, 300) });
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
    await sleep(800);
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
    await common(page, `${tag0} watch`, W, errs);
    await ctx.close();
  } else skip(`${tag0} watch (the world has no Watch screen)`);
  // --- Lab work ------------------------------------------------------------------------------------------------------
  if (lab) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs } = await open(ctx, lab.id);
    await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 20000 });
    await page.locator(".dm-measure").click();
    const msg0 = await page.locator(".dm-msg").innerText();
    check(`${tag0} lab: «Measure» before the landing says there is nothing to measure yet`, msg0.includes(tr("Nothing to measure yet: “{what}” has not been reached at this moment", { what: tr("Range") }).slice(0, 12)), { msg0 });
    const st0 = lab.steps[0];
    if (st0.instruments.some((id) => (lab.instruments[id] || {}).manual)) {
      const slow = page.locator('.dm-screen:not([hidden]) .dm-speed [data-rate="0.25"]');
      check(`${tag0} lab: the manual stopwatch refuses «slow»`, await slow.isDisabled());
    } else skip(`${tag0} lab: the manual stopwatch (not in the first step)`);
    const lc = mfL.controls[0], all = lc.values;
    const hv = all.length <= 5 ? all : [0, 1, 2, 3, 4].map((j) => all[Math.round(j * (all.length - 1) / 4)]);
    for (const v of hv) {
      await detent(page, lc.param, all.indexOf(v)).click();
      await page.waitForFunction(([p, x]) => { const s = window.__lfLab.step(); return s.cur && s.cur.pt.values[p] === x; }, [lc.param, v], { timeout: 10000 });
      // to the landing: the last frame of the point
      await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); });
      await settle(page, 50);
      await page.locator(".dm-measure").click();
    }
    const rows = await page.evaluate(() => window.__lfLab.rows().length);
    check(`${tag0} lab: ${hv.length} measurements, ${hv.length} rows`, rows === hv.length, { rows });
    const cell = await page.locator(".dm-table tbody tr").first().innerText();
    check(`${tag0} lab: a reading carries its error`, cell.includes("±"), { cell });
    const fitTxt = await page.locator(".dm-fit").innerText();
    check(`${tag0} lab: the fit gives b ± σ`, /b = .*±/.test(fitTxt), { fitTxt });
    await page.locator(".dm-check-law").click();
    await settle(page, 100);
    const law = await page.locator(".dm-law").innerText();
    const ok = await page.evaluate(() => window.__lfLab.check());
    const ref = Object.values(mfL.references)[0].value;
    const res = await page.evaluate(() => ({ b: window.__lfLab.fit().params.b, s: window.__lfLab.fit().sigma.b }));
    check(`${tag0} lab: «Check against the law» agrees with the reference`, ok && ok.ok && law.includes(tr("✓ agrees within two errors")) && Math.abs(res.b - ref) <= 2 * res.s, { law, ref, res });
    // the plot is drawn (not blank)
    const plotInk = await page.evaluate(() => { const c = document.querySelector(".dm-plot"); const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data; const s = new Set(); for (let i = 0; i < d.length; i += 64) s.add(d[i] << 16 | d[i + 1] << 8 | d[i + 2]); return s.size; });
    check(`${tag0} lab: the plot is drawn`, plotInk > 3, { colours: plotInk });
    const tb = await page.evaluate(() => { const b = document.querySelector(".dm-table-box"); return { sw: b.scrollWidth, cw: b.clientWidth }; });
    check(`${tag0} lab: the table scrolls inside its box`, tb.cw <= W);
    await page.evaluate(() => { document.querySelector(".dm-screens").scrollTop = 0; window.scrollTo(0, 0); });
    await settle(page);
    await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_lab_${LANG}_${tag0}.png` });
    await page.evaluate(() => { document.querySelector(".dm-screens").scrollTop = 1e6; window.scrollTo(0, 1e6); });
    await settle(page);
    await page.screenshot({ path: `${SHOTS}/demo_${WORLD}_lab_table_${LANG}_${tag0}.png` });
    // the CSV
    const csvHref = await page.locator('a[download$=".csv"]').getAttribute("href");
    const csv = decodeURIComponent(csvHref.replace(/^data:text\/csv;charset=utf-8,/, ""));
    check(`${tag0} lab: the CSV has the rows and the errors`, csv.trim().split("\n").length === hv.length + 1 && csv.split("\n")[0].includes("σ"));
    await common(page, `${tag0} lab`, W, errs);
    await ctx.close();
  } else skip(`${tag0} lab work (the world has no Lab work screen)`);
  // --- the worksheet -------------------------------------------------------------------------------------------------
  if (W >= 1000 && lab) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", (e) => errs.push(e.message));
    await page.goto(inLang(`${base}/worksheet?demo=${WORLD}`));
    await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
    const txt = await page.locator("#ws").innerText();
    check("worksheet: the programme's lab, the step, the questions, the equipment in the language", txt.includes(tr(lab.worksheet.frp[0].name)) && txt.includes(tr(lab.steps[0].title))
      && txt.includes(tr(lab.worksheet.questions[0].q)) && txt.includes(tr(lab.worksheet.equipment[0])) && !txt.includes("[object"));
    check("worksheet: the answers hidden without «For the teacher»", !(await page.locator(".teacher").isVisible()));
    await page.emulateMedia({ media: "print" });
    const pdf0 = await page.pdf({ format: "A4" });
    await page.emulateMedia({ media: "screen" });
    await page.locator(".ws-tools input[type=checkbox]").check();
    check("worksheet: «For the teacher» shows the answers", (await page.locator(".teacher").innerText()).includes(tr(lab.worksheet.questions[0].answer)));
    check("worksheet: the switch is in the address", new URL(page.url()).searchParams.get("teacher") === "1");
    await page.emulateMedia({ media: "print" });
    const pdf1 = await page.pdf({ format: "A4" });
    const pages = (b) => (b.toString("latin1").match(/\/Type\s*\/Page[^s]/g) || []).length;
    writeFileSync(`${SHOTS}/worksheet_${WORLD}_${LANG}.pdf`, pdf0);
    writeFileSync(`${SHOTS}/worksheet_${WORLD}_teacher_${LANG}.pdf`, pdf1);
    const brk = await page.evaluate(() => getComputedStyle(document.querySelector(".teacher")).breakBefore);
    check("worksheet: printed; the teacher's answers on pages of their own (a page break before them)", pages(pdf0) >= 1 && pages(pdf1) > pages(pdf0)
      && (lab.steps.length > 1 || pages(pdf1) === pages(pdf0) + 1) && brk === "page", { pages: [pages(pdf0), pages(pdf1)], brk });
    if (LANG === "en") check("worksheet: no Cyrillic but the programme's own wording", !CYR.test(txt.replace(/«[^»]*»/g, "")));  // i18n-ok: the quoted original
    await page.emulateMedia({ media: "screen" });
    await page.screenshot({ path: `${SHOTS}/worksheet_${WORLD}_${LANG}.png`, fullPage: true });
    check("worksheet: no page error", errs.length === 0, { errs });
    await ctx.close();
  }
}

await br.close();
console.log(failed ? `FAILED: ${failed}` : "all passed");
process.exit(failed ? 1 : 0);
