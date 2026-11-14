// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// u32's screens in a browser (design lfphys/sources/explore_2026-11-14_design.md §6, §8 "Browser"), in the language of
// LFVIZ_LANG (en by default), at every viewport size given (1280x800 and 390x844 by default):
//  - the tabs «Watch · Explore» in the language;
//  - Explore as on the public site (lf-mode "static", the API as JSON files, no live endpoint): the sliders stop only at
//    the grid's values; ▶ builds the point up to its end, and the readout line shows the frame's hits and χ² ✓; a change
//    of a slider keeps the time and the earlier points stay as traces (at most the screen's number); an overlay toggles
//    and changes the picture; the points fetched are only those shown and their neighbours; «How we know this is right»
//    lists the point's checks ✓ and folds in the view's panels («Particle», «Model of the slit screen», «Counters and
//    statistics», «Approximations of this segment»: demo.js's view.rightPanels hook);
//  - Watch: the story plays from its start; one chapter tick per caption, and each tick shows its caption in the
//    language; after «Slit 2 is closed» the screen starts again (fewer hits in the new segment); «More recordings» offers
//    the four recordings; the fold «Latest particles: the chain of causes» is there (and not in Explore);
//  - on the server: «▶ Compute live» from Explore opens the full live player with the quick set-up bar;
//  - every screen: no horizontal scroll, no page error, in English no Cyrillic in the visible text, in Russian the tabs'
//    Russian labels; screenshots per screen, language and size.
//
// Run against a PRIVATE server with u32's recordings and atlas built (site/record.py --world u32_double_slit --out DIR),
// never the shared one on 8479:
//   docker run -d --name lf-u32-srv --memory=6g -p 8696:8479 -v <repo>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
//     -v DIR:/rec:ro -e LFVIZ_RECORDINGS=/rec -e LFPHYS_NO_GPU=1 -w /lf/visualizations lfphys-viz \
//     python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
//   docker run --rm --init --shm-size=2g --network host --memory=4g -v <scratch with node_modules/playwright@1.58.2>:/pw \
//     -v <repo>/visualizations:/v:ro -w /pw -e LFVIZ_LANG=en|ru -e SHOTS=/pw/shots mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp /v/tests/browser/lfi18n.mjs /v/u32_double_slit/tests/u32_screens.mjs /pw/ && node /pw/u32_screens.mjs 8696"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { LANG, inLang, loadI18n } from "./lfi18n.mjs";

const port = process.argv[2] || "8696";
const SIZES = (process.argv[3] || "1280x800,390x844").split(",").map((s) => s.split("x").map(Number));
const base = `http://127.0.0.1:${port}`;
const SHOTS = process.env.SHOTS || "/pw/shots";
mkdirSync(SHOTS, { recursive: true });
const WORLD = "u32_double_slit";
const CYR = /[Ѐ-ӿ]/;  // i18n-ok: recognises Cyrillic
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: `${LANG} ${name}`, ok: !!ok, ...info })); };
const get = async (u) => (await fetch(base + u)).json();
const { t: tr } = await loadI18n(base);

const viz = await get(`/api/viz/${WORLD}`);
const recs = await get("/api/recordings");
const index = recs.worlds[WORLD];
const ex = viz.screens.find((s) => s.kind === "explore"), wa = viz.screens.find((s) => s.kind === "watch");
check("u32 has Watch and Explore, its recordings and its atlas", viz.screens.length === 2 && ex && wa && index
  && index.atlases.some((a) => a.id === ex.atlas) && index.recordings.some((r) => r.id === wa.recording));
const mf = await get(`/recordings/${WORLD}/${index.atlases.find((a) => a.id === ex.atlas).file}`);
check("the atlas: every point computed, every check ✓", mf.points.every((p) => p[2] === 0) && mf.checks.failed === 0, { checks: mf.checks });
const story = (viz.recordings || []).find((r) => r.id === wa.recording);

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });

async function asSite(ctx) {  // the page as the public site serves it (as tests/browser/demo_screens.mjs does)
  await ctx.route(/\/run(\.html)?(\?|$)/, async (route) => {
    const r = await route.fetch({ url: base + "/run" });
    const html = (await r.text()).replace('<meta name="lf-mode" content="server">', '<meta name="lf-mode" content="static">');
    await route.fulfill({ response: r, body: html, headers: { ...r.headers(), "content-type": "text/html; charset=utf-8" } });
  });
  await ctx.route(/\/api\/(.+)\.json(\?.*)?$/, async (route) => {
    const name = new URL(route.request().url()).pathname.replace(/^\/api\//, "").replace(/\.json$/, "");
    await route.fulfill({ response: await route.fetch({ url: `${base}/api/${name}` }) });
  });
  await ctx.route(/\/aliases\.json$/, (route) => route.fulfill({ status: 200, contentType: "application/json", body: "{}" }));
  await ctx.route(/\/api\/atlas\//, (route) => route.abort());
}
async function open(ctx, screen) {
  const page = await ctx.newPage();
  const errs = [], reqs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") errs.push("console: " + m.text().slice(0, 200)); });
  page.on("request", (r) => reqs.push(r.url()));
  await page.goto(inLang(`${base}/run?demo=${WORLD}&screen=${screen}`));
  await page.waitForFunction((s) => document.querySelector(`.dm-screen[data-screen="${s}"]`) && !document.querySelector(`.dm-screen[data-screen="${s}"]`).hidden, screen, { timeout: 30000 });
  return { page, errs, reqs };
}
const settle = (page, ms = 300) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
async function common(page, tag, W, errs) {
  const sw = await page.evaluate(() => document.scrollingElement.scrollWidth);
  check(`${tag}: no horizontal scroll`, sw <= W, { scrollWidth: sw, width: W });
  const txt = await page.evaluate(() => document.getElementById("demo").innerText);
  if (LANG === "en") check(`${tag}: no Cyrillic in the visible text`, !CYR.test(txt), { sample: (txt.match(/.{0,30}[Ѐ-ӿ].{0,30}/) || [""])[0] });  // i18n-ok
  else check(`${tag}: the tabs in Russian`, [tr("Watch"), tr("Explore")].every((s) => txt.includes(s)) && CYR.test(txt));
  check(`${tag}: no page error`, errs.length === 0, { errs });
}
const detent = (page, param, k) => page.locator(`.dm-screen:not([hidden]) .dm-ctl[data-param="${param}"] .dm-detent`).nth(k);
const readout = (page) => page.locator('.dm-screen:not([hidden]) [data-u32="readouts"]').innerText();
const canvasSum = (page, k) => page.evaluate((j) => {  // a fingerprint of the pixels of the view's k-th canvas
  const c = document.querySelectorAll(".dm-screen:not([hidden]) .dm-stage canvas")[j];
  const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data;
  let s = 0; for (let i = 0; i < d.length; i += 4) s = (s * 31 + d[i] + 7 * d[i + 1] + 13 * d[i + 2]) % 1000000007;
  return s;
}, k);
const pointOf = (page) => page.evaluate(() => { const p = window.__lfExplore.explore.point(); return p ? { i: p.i, values: p.values } : null; });
const shown = (page, i) => page.waitForFunction((j) => { const p = window.__lfExplore.explore.point(); return p && p.i === j; }, i, { timeout: 20000 });
const flat = (vals) => mf.controls.reduce((i, c) => i * c.values.length + c.values.indexOf(vals[c.param]), 0);

for (const [W, H] of SIZES) {
  const tag0 = `${W}x${H}`;
  // --- Explore, as the site ------------------------------------------------------------------------------------------
  {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs, reqs } = await open(ctx, "explore");
    await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 30000 });
    const tabs = await page.locator(".dm-tab").allInnerTexts();
    check(`${tag0} tabs`, tabs.length === 2 && tabs[0].includes(tr("Watch")) && tabs[1].includes(tr("Explore")), { tabs });
    const sl = await page.evaluate(() => [...document.querySelectorAll(".dm-screen:not([hidden]) .dm-slider")].map((s) => ({ min: s.min, max: s.max, step: s.step })));
    check(`${tag0} explore (site): the sliders stop only at the grid's values`, sl.length === 3
      && sl.every((s, i) => s.min === "0" && Number(s.max) === mf.controls[i].values.length - 1 && s.step === "1"), { sl });
    const labels = await page.locator(".dm-screen:not([hidden]) .dm-ctl-label").allInnerTexts();
    const want = [["Wavelength λ", "nm"], ["Slit period d", "µm"], ["Slit width a", "µm"]].map(([l, u]) => tr("{label}, {unit}", { label: tr(l), unit: tr(u) }));
    check(`${tag0} explore: the controls' labels with their units`, JSON.stringify(labels) === JSON.stringify(want), { labels, want });
    await page.locator(".dm-screen:not([hidden]) .dm-play").click();
    await page.waitForFunction(() => { const E = window.__lfExplore.explore.state; return E.cur && !E.playing && E.clock - E.cur.launchedAt >= E.cur.pt.tEnd - 1e-9; }, null, { timeout: 30000 });
    await settle(page);
    const n0 = await page.evaluate(() => { const F = window.__lfExplore.explore.point().W.frames; return F[F.length - 1].meta.n_seg; });
    const r0 = await readout(page);
    check(`${tag0} explore: at the end the readout shows the point's hits and χ² ✓`, r0.replace(/[\s,  ]/g, "").includes(String(n0)) && r0.includes("χ²/dof") && r0.includes("✓"), { r0, n0 });
    await page.screenshot({ path: `${SHOTS}/u32_explore_${LANG}_${tag0}.png` });
    // two changes: λ 400 nm, then a 40 µm; the time is kept and the earlier points stay as traces
    const tEnd = await page.evaluate(() => { const E = window.__lfExplore.explore.state; return Math.min(E.cur.pt.tEnd, E.clock - E.cur.launchedAt); });
    await detent(page, "lam_nm", 0).click();
    await shown(page, flat({ ...mf.controls.reduce((o, c) => ({ ...o, [c.param]: c.default }), {}), lam_nm: 400 }));
    await detent(page, "a_um", 2).click();
    await page.waitForFunction(() => { const v = window.__lfExplore.explore.values(); return v.a_um === 40 && window.__lfExplore.explore.point().values.a_um === 40; }, null, { timeout: 20000 });
    const tAfter = await page.evaluate(() => { const E = window.__lfExplore.explore.state; return Math.min(E.cur.pt.tEnd, E.clock - E.cur.launchedAt); });
    check(`${tag0} explore: a change of a slider keeps the time (acts «now»)`, Math.abs(tAfter - tEnd) < 1e-6, { tEnd, tAfter });
    for (const k of [1, 2]) { await detent(page, "d_um", k).click(); await sleep(400); }
    await page.waitForFunction(() => window.__lfExplore.explore.point().values.d_um === 200, null, { timeout: 20000 });
    const ntr = await page.evaluate(() => window.__lfExplore.explore.state.traces.length);
    check(`${tag0} explore: earlier points stay as traces (at most ${ex.traces})`, ntr >= 2 && ntr <= ex.traces, { traces: ntr });
    await settle(page, 600);
    await page.screenshot({ path: `${SHOTS}/u32_explore_traces_${LANG}_${tag0}.png` });
    // an overlay: the wave off changes the view from above
    if (W < 1000) await page.locator(".dm-screen:not([hidden]) .dm-overlays > summary").click().catch(() => {});
    const wave = page.locator('.dm-screen:not([hidden]) input[data-overlay="wave"]');
    const a0 = await canvasSum(page, 0);
    await wave.uncheck(); await settle(page);
    const a1 = await canvasSum(page, 0);
    await wave.check(); await settle(page);
    check(`${tag0} explore: the overlay «wave» toggles the map`, a0 !== a1 && (await wave.isChecked()), { a0, a1 });
    const noint = page.locator('.dm-screen:not([hidden]) input[data-overlay="no_interference"]');
    const s0 = await canvasSum(page, 1);
    await noint.check(); await settle(page);
    check(`${tag0} explore: the overlay «without interference» draws its curve`, (await canvasSum(page, 1)) !== s0);
    // the network: only the points shown and their neighbours (±1 along a control)
    const pts = reqs.filter((u) => /\/atlas\/explore\/p\d+\./.test(u)).map((u) => Number(u.match(/\/p(\d+)\./)[1]));
    const dims = mf.controls.map((c) => c.values.length);
    const idx = (i) => { const out = []; for (let k = dims.length - 1; k >= 0; k--) { out.unshift(i % dims[k]); i = Math.floor(i / dims[k]); } return out; };
    const shownPts = [...new Set(await page.evaluate(() => [window.__lfExplore.explore.point().i, ...window.__lfExplore.explore.state.traces.map((s) => s.pt.i)]))];
    const def = flat(mf.controls.reduce((o, c) => ({ ...o, [c.param]: c.default }), {}));
    const visited = [def, ...shownPts];
    const near = (i) => visited.some((j) => { const a = idx(i), b = idx(j); return a.reduce((s, x, k) => s + Math.abs(x - b[k]), 0) <= 1; });
    check(`${tag0} explore: only the points shown and their neighbours were fetched`, pts.length > 0 && pts.every(near), { fetched: [...new Set(pts)].sort((x, y) => x - y) });
    check(`${tag0} explore: no request to the live endpoint on the site`, !reqs.some((u) => u.includes("/api/atlas/")));
    check(`${tag0} explore: no chain of causes in Explore (its stories are dropped)`, (await page.locator(".dm-screen:not([hidden]) .u32-stories").count()) === 0);
    // «How we know this is right»: the point's checks ✓ and the view's panels folded in
    if (W < 1000) { await page.locator(".dm-menu > summary").click(); await page.locator(".dm-menu-box button").first().click(); }
    else await page.locator(".dm-how").click();
    await settle(page);
    const sums = await page.locator(".dm-drawer-body summary").allInnerTexts();
    const folds = ["Particle", "Model of the slit screen", "Counters and statistics", "Approximations of this segment"].map((x) => tr(x));
    check(`${tag0} explore: the drawer folds in the view's panels`, folds.every((f) => sums.includes(f)), { sums });
    await page.evaluate(() => { for (const d of document.querySelectorAll(".dm-drawer details")) d.open = true; });
    const dr = await page.locator(".dm-drawer-body").innerText();
    check(`${tag0} explore: the drawer's checks agree ✓ and the particle's panel is filled`, /✓/.test(dr) && !dr.includes("✗")
      && dr.includes(tr("Wavelength λ")) && dr.includes(mf.key), { dr: dr.slice(0, 300) });
    await page.screenshot({ path: `${SHOTS}/u32_drawer_${LANG}_${tag0}.png` });
    await page.keyboard.press("Escape");
    await common(page, `${tag0} explore`, W, errs);
    await ctx.close();
  }
  // --- Watch, as the site --------------------------------------------------------------------------------------------
  {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    await asSite(ctx);
    const { page, errs } = await open(ctx, "watch");
    await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 30000 });
    const s0 = await page.evaluate(() => window.__lfWatch.step());
    await sleep(800);
    const s1 = await page.evaluate(() => window.__lfWatch.step());
    check(`${tag0} watch: the story plays from its start`, s1 > s0, { s0, s1 });
    const caps = await page.evaluate(() => window.__lfWatch.state.story.captions.map((c) => ({ step: c.step, text: c.text })));
    check(`${tag0} watch: the captions of the spec, in order`, caps.length === story.captions.length
      && caps.every((c, k) => tr(c.text) === tr(story.captions[k].text)), { n: caps.length, want: story.captions.length,
      bad: caps.map((c, k) => [tr(c.text), tr(story.captions[k].text)]).filter(([a, b]) => a !== b).slice(0, 1) });
    const ticks = page.locator(".dm-screen:not([hidden]) .dm-tick");
    check(`${tag0} watch: a chapter tick per caption`, (await ticks.count()) === caps.length);
    const capNow = async () => (await page.locator(".dm-screen:not([hidden]) .dm-caption").innerText()).trim();
    const hitsNow = async () => Number((await readout(page)).replace(/[^\d]+/, "").match(/^[\d\s,  ]+/)[0].replace(/[^\d]/g, ""));
    let before = null;
    for (const [k, c] of caps.entries()) {
      if (k === 4) {  // just before «Slit 2 is closed»: thousands of hits in the first segment
        await page.evaluate((st) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(st); s.dispatchEvent(new Event("input")); }, c.step - 1);
        await settle(page, 100);
        before = await hitsNow();
      }
      await ticks.nth(k).click({ force: true });
      await settle(page, 100);
      const got = await capNow();
      check(`${tag0} watch: the caption of chapter ${k}`, got === tr(c.text).trim(), { got: got.slice(0, 60) });
      if (k === 4) {
        await page.evaluate((st) => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = String(st); s.dispatchEvent(new Event("input")); }, c.step + 40);
        await settle(page, 100);
        const after = await hitsNow();
        check(`${tag0} watch: after «Slit 2 is closed» the screen starts again`, before > 1500 && after < before / 2, { before, after });
        await page.screenshot({ path: `${SHOTS}/u32_watch_slit_${LANG}_${tag0}.png` });
      }
      if (k === 3) await page.screenshot({ path: `${SHOTS}/u32_watch_${LANG}_${tag0}.png` });
    }
    const opts = await page.locator(".dm-screen:not([hidden]) select.dm-more option").count();
    check(`${tag0} watch: «More recordings» offers the four recordings`, opts === 1 + wa.more.length, { opts });
    check(`${tag0} watch: the fold «Latest particles: the chain of causes»`, (await page.locator(".dm-screen:not([hidden]) .u32-stories summary").innerText()).trim() === tr("Latest particles: the chain of causes"));
    await common(page, `${tag0} watch`, W, errs);
    await ctx.close();
  }
  // --- the server: «▶ Compute live» opens the full player ------------------------------------------------------------
  if (W >= 1000) {
    const ctx = await br.newContext({ viewport: { width: W, height: H } });
    const { page, errs } = await open(ctx, "explore");
    await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 30000 });
    await page.locator(".dm-top .dm-live").click();
    await page.waitForURL(/\/run\?id=/, { timeout: 30000 });
    await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 60000 });
    await settle(page, 800);
    const quick = await page.locator(".toolbar.quick").count();
    check(`${tag0} live: «▶ Compute live» opens the full player with the quick set-up bar`, quick === 1, { url: page.url() });
    const id = new URL(page.url()).searchParams.get("id");
    const m = await get(`/api/runs/${id}`);
    check(`${tag0} live: the run is u32 with the Explore point's values`, m.viz === WORLD && (m.params || {}).lam_nm === 600 && (m.params || {}).screen_um === 30000, { params: m.params && { lam: m.params.lam_nm, screen: m.params.screen_um } });
    await page.screenshot({ path: `${SHOTS}/u32_live_${LANG}_${tag0}.png` });
    await fetch(`${base}/api/runs/${id}/command`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ cmd: "pause" }) }).catch(() => {});
    check(`${tag0} live: no page error`, errs.length === 0, { errs });
    await ctx.close();
  }
}
await br.close();
console.log(failed ? `FAILED: ${failed}` : "all passed");
process.exit(failed ? 1 : 0);
