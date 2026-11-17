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
//  - Watch: a caption's hold (F12), the time label with the world's time and the playback factor (D8);
//  - Lab work, every step: «Measure» before a launch says there is nothing to measure yet; a slow reply of an earlier pick
//    is not shown and «Measure» waits for the set-up (D6); → on a focused slider; the manual stopwatch on the wall clock,
//    a pause refused while it runs, its reading in its column; the set-ups measured (Space on a focused «Measure» too),
//    one row each, a repeat replaces its row (D5); each law ✓ on its own plot, another plot refused with the reason (D4);
//    the RU verdict without Latin units; an empty time without the stopwatch; the drawer's events without times (D10);
//    at 390 px the view, a control, «Measure», «⏱ Stop» and the time bar together (D12); Space on a focused tab;
//  - the worksheet: one A4 page per sheet (the PDF's pages = the sheets, none overflowing at A4's printable width), each
//    with the attribution line; one blank row per set-up; the teacher's sheets; a variant's steps, columns and questions;
//    no raw id or Latin unit in Russian;
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
        shown.push(flat(mfE, await page.evaluate(`${X}.values()`)));  // the set-up asked for (a refused one too: its neighbours are prefetched)
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
    const pickAndWait = async (param, values, v) => {
      await detent(page, param, values.indexOf(v)).click();
      await LB(`s.cur && s.cur.pt.values[${JSON.stringify(param)}] === ${JSON.stringify(v)} && !s.pending`);
    };
    for (const [k, st] of lab.steps.entries()) {
      const tagS = `${tag0} lab part ${k + 1}`;
      if (k > 0) { await page.locator(".dm-steps button").nth(k).click(); await LB(`s && s.step.id === ${JSON.stringify(st.id)} && s.cur`); }
      const entryS = index.atlases.find((a) => a.id === st.atlas);
      const mf = await get(`/recordings/${WORLD}/${entryS.file}`);
      const lc = mf.controls[0], all = lc.values;
      const manual = st.instruments.some((id) => (lab.instruments[id] || {}).manual);
      check(`${tagS}: a manual stopwatch refuses «slow»`, (await page.locator('.dm-screen:not([hidden]) .dm-speed [data-rate="0.25"]').isDisabled()) === manual);
      if (k === 0 && all.length >= 5) {  // D6: a slow reply of an earlier pick is not applied; «Measure» waits for the set-up
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
      if (k === 0) {
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
        await pickAndWait(lc.param, all, v);
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
      // each law on its own plot: ✓; another plot: the check is off with the reason (D4)
      const refs = mf.references || {};
      for (const [j, law] of (st.laws || []).entries()) {
        // the law's plot: «plot it» when offered, else the selects (x, y, fit)
        const sels = page.locator(".dm-screen:not([hidden]) .dm-work select");
        await sels.nth(0).selectOption(law.x); await sels.nth(1).selectOption(law.y); await sels.nth(2).selectOption(law.model);
        await settle(page, 50);
        const disabled = await page.locator(".dm-check-law").isDisabled();
        if (!disabled) await page.locator(".dm-check-law").click();
        await settle(page, 100);
        const out = await page.evaluate(() => window.__lfLab.check());
        const txt = await page.locator(".dm-law").innerText().catch(() => "");
        const okLaw = out && out.law === law.reference && out.ok;
        check(`${tagS}: law ${j + 1} (${law.y} against ${law.x}, ${law.model}) ✓ against its reference`, okLaw && !!refs[law.reference], { out, txt: txt.slice(0, 200) });
        if (LANG === "ru") check(`${tagS}: law ${j + 1}'s verdict has no Latin unit or id (F7)`, !/\b(m|slope|vertex|dof)\b|m\^½/.test(txt), { txt: txt.slice(0, 200) });
      }
      if ((st.laws || []).length) {  // a plot that is no law's: the check off, with the reason
        const cols = st.columns.map((c) => c.id), L0 = st.laws[0];
        const other = cols.find((c) => c !== L0.x && c !== L0.y && !(st.laws || []).some((L) => L.x === c && L.y === L0.y));
        if (other) {
          await page.locator(".dm-screen:not([hidden]) .dm-work select").first().selectOption(other);
          await settle(page, 50);
          const off = await page.locator(".dm-check-law").isDisabled();
          const why = (await page.locator(".dm-law-why").innerText().catch(() => "")).trim();
          check(`${tagS}: on a plot that is no law's, «Check against the law» is off with the reason (D4)`, off && why.length > 5, { other, why });
        }
      }
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
      // the drawer of Lab work lists the events without their times (integrator D10: the flight time is measured)
      if (W >= 1000) {
        await page.locator(".dm-how").click();
        await settle(page);
        const evs = await page.$$eval(".dm-drawer-body .dm-ev", (a) => a.map((e) => ({ mono: !!e.querySelector(".mono"), text: e.textContent })));
        check(`${tagS}: the drawer's events have no times in Lab work (D10)`, evs.every((e) => !e.mono), { evs: evs.slice(0, 3) });
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
  // --- the worksheet -------------------------------------------------------------------------------------------------
  // one A4 page per sheet (the head and part 1, each part, the questions, the teacher's sheets), each with the
  // attribution line, no sheet overflowing its page, one blank row per set-up (review EX1-screens F6, EX1-worlds F7)
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
    const frp0 = lab.worksheet.frp[0];
    check("worksheet: the programme's lab by its name (no raw id), the step, the questions, the equipment in the language", txt.includes(tr(frp0.name)) && txt.includes(tr(lab.steps[0].title))
      && (!frp0.programme || txt.includes(tr(frp0.programme))) && !txt.includes(frp0.system)
      && txt.includes(tr(lab.worksheet.questions[0].q)) && txt.includes(tr(lab.worksheet.equipment[0])) && !txt.includes("[object"));
    check("worksheet: the answers hidden without «For the teacher»", !(await page.locator(".teacher").first().isVisible()));
    const { pdf: pdf0, sh: sh0 } = await printed("");
    const setups = (st) => (st.controls || []).reduce((n, c) => n * c.values.length, 1);
    const parts = sh0.filter((x) => x.cls.includes("part"));
    check("worksheet: a sheet per part, one blank row per set-up of its step", parts.length === lab.steps.length && parts.every((x, k) => x.rows === setups(lab.steps[k])), { rows: parts.map((x) => x.rows), want: lab.steps.map(setups) });
    await page.locator(".ws-tools input[type=checkbox]").check();
    check("worksheet: «For the teacher» shows the answers", (await page.locator(".teacher").first().innerText()).includes(tr(lab.worksheet.questions[0].answer)));
    check("worksheet: the switch is in the address", new URL(page.url()).searchParams.get("teacher") === "1");
    const { pdf: pdf1, sh: sh1 } = await printed(" (for the teacher)");
    check("worksheet: the teacher's sheets are pages of their own", pages(pdf1) > pages(pdf0) && sh1.filter((x) => x.cls.includes("teacher")).length === pages(pdf1) - pages(pdf0));
    writeFileSync(`${SHOTS}/worksheet_${WORLD}_${LANG}.pdf`, pdf0);
    writeFileSync(`${SHOTS}/worksheet_${WORLD}_teacher_${LANG}.pdf`, pdf1);
    if (LANG === "en") check("worksheet: no Cyrillic but the programme's own wording", !CYR.test(txt.replace(/«[^»]*»/g, "")));  // i18n-ok: the quoted original
    else check("worksheet: no Latin unit or raw id in the Russian text (F7)", !/\bm\^½|\bFRP-|\b(slope|vertex)\b/.test(txt), { sample: (txt.match(/.{0,30}(m\^½|FRP-|slope|vertex).{0,30}/) || [""])[0] });
    await page.screenshot({ path: `${SHOTS}/worksheet_${WORLD}_${LANG}.png`, fullPage: true });
    // a variant (S03's grade 7): its steps, its plot's columns only, its questions
    for (const v of lab.worksheet.variants || []) {
      await page.goto(inLang(`${base}/worksheet?demo=${WORLD}&variant=${v.id}`));
      await page.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 20000 });
      const vt = await page.locator("#ws").innerText();
      const { sh } = await printed(` variant ${v.id}`);
      const vparts = sh.filter((x) => x.cls.includes("part"));
      const vsteps = lab.steps.filter((st) => v.steps.includes(st.id));
      const wantCols = vsteps.map((st) => st.columns.filter((c) => c.from || c.id === v.plot[st.id].x || c.id === v.plot[st.id].y).length);
      check(`worksheet variant ${v.id}: its steps, the measured and plotted columns, its questions`, vparts.length === vsteps.length
        && vparts.every((x, k) => x.cols === wantCols[k]) && vt.includes(tr(v.label)) && v.questions.every((q) => vt.includes(tr(q.q))), { cols: vparts.map((x) => x.cols), wantCols });
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
