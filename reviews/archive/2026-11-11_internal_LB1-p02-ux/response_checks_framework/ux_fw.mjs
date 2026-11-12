// Response to reviews LB1-p02-ux (X2, X3, X8, X13) and LB1-framework (F13), framework part: browser checks of the
// player, run against a PRIVATE server (never the shared one on 8479), once on the code before the fixes and once after.
//   docker run --rm --init --shm-size=2g --network host --name lf-lpf-pw -v <scratch>/pw:/pw -v <this folder>:/t:ro \
//     -e SHOTS=/pw/shots -e PHASE=after -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp /t/ux_fw.mjs /pw/ && node /pw/ux_fw.mjs 8612 1600x1000,1280x800"
// One JSON line per check; "all passed" or the number failed (exit code 1). Screenshots <PHASE>_<check>_<size>.png.
//   X2  p02 (plane world): an object picked in the world's own window is removed by Delete (one scene remove, no view
//       command, no «Срез не построен»); negative control: Delete with nothing of the scene selected removes nothing.
//   X3  «Новый мир» of p02 with the space chosen shows the new world's grid and window (the live laws) in its form.
//   X8  the top bar stays one row (also with the world selector of a second world and in p01); toasts never overlap.
//   X13 the window's axis ticks are round (1-2-5 steps) and the last label fits in the window.
import { chromium } from "playwright";

const port = process.argv[2] || "8612";
const SIZES = (process.argv[3] || "1600x1000,1280x800").split(",").map((s) => s.split("x").map(Number));
const OUT = process.env.SHOTS || "/pw";
const PHASE = process.env.PHASE || "after";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cmd = (id, c, a) => post(`/api/runs/${id}/command`, { cmd: c, args: a || {} });
async function record(id) {
  const buf = new Uint8Array(await (await fetch(`${base}/api/runs/${id}/stream`)).arrayBuffer());
  const dv = new DataView(buf.buffer), out = [], dec = new TextDecoder();
  for (let off = 8; off + 4 <= buf.length;) {
    const n = dv.getUint32(off, true), m = off + 4, jl = dv.getUint32(m, true);
    out.push(JSON.parse(dec.decode(buf.subarray(m + 4, m + 4 + jl))));
    off = m + n;
  }
  return out;
}
async function waitFor(fn, ms = 20000, step = 150) {
  const t0 = Date.now();
  for (;;) { const v = await fn(); if (v) return v; if (Date.now() - t0 > ms) return null; await sleep(step); }
}
const checks = [];
function check(name, ok, detail = {}) { checks.push({ name, ok: !!ok }); console.log(JSON.stringify({ name, ok: !!ok, ...detail })); }

async function newRun(viz, preset, params) {
  const r = await post("/api/runs", { viz, preset, params, seed: 3 });
  if (!r.id) throw new Error("run not started: " + JSON.stringify(r));
  await waitFor(async () => (await get(`/api/runs/${r.id}`)).state === "running", 120000, 300);
  return r.id;
}
async function openRun(page, id) {
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && window.__lfManip, null, { timeout: 180000 });
  await sleep(1500);
}
const scrWin = (page, oid, k = 1) => page.evaluate(([id, k]) => {
  const ws = [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean);
  const p = window.__lfManip.at(id);
  for (const W of ws) {
    const h = W.helper(k); if (!h || !p) continue;
    const [x, y] = h.toCanvas(p), r = h.el.getBoundingClientRect();
    if (x > 2 && y > 2 && x < r.width - 2 && y < r.height - 2) return [r.left + x, r.top + y];
  }
  return null;
}, [oid, k]);
const topbar = (page) => page.evaluate(() => {
  const t = document.querySelector(".topbar"), r = t.getBoundingClientRect();
  // rows: items whose vertical centres lie more than 12 px apart are on different rows (items of different heights in
  // one row are centred on one line)
  const kids = [...t.children].filter((c) => c.offsetParent !== null && c.getBoundingClientRect().height > 0).map((c) => c.getBoundingClientRect());
  const cs = kids.map((k) => (k.top + k.bottom) / 2).sort((a, b) => a - b);
  let rows = cs.length ? 1 : 0;
  for (let i = 1; i < cs.length; i++) if (cs[i] - cs[i - 1] > 12) rows++;
  // every visible item inside the bar (nothing pushed out at the right)
  const out = kids.filter((k) => k.right > r.right + 0.5).length;
  return { h: Math.round(r.height), rows, out };
});
const toastRects = (page) => page.evaluate(() => [...document.querySelectorAll(".toast")].filter((t) => t.offsetParent !== null || getComputedStyle(t).position === "fixed")
  .map((t) => { const r = t.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, text: t.textContent.slice(0, 60) }; }));
const overlaps = (R) => { let n = 0; for (let i = 0; i < R.length; i++) for (let j = i + 1; j < R.length; j++) { const a = R[i], b = R[j]; if (a.left < b.right && b.left < a.right && a.top < b.bottom - 0.5 && b.top < a.bottom - 0.5) n++; } return n; };

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const [Wd, Ht] of SIZES) {
  const tag = `${Wd}x${Ht}`;
  // --- X2, X13, X8 on p02's plane world --------------------------------------------------------------------------
  const id = await newRun("p02_quantum", "double_slit");
  const page = await br.newPage({ viewport: { width: Wd, height: Ht } });
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message));
  await openRun(page, id);
  await cmd(id, "play"); await sleep(2500); await cmd(id, "pause"); await sleep(1200);
  const tb1 = await topbar(page);
  check(`X8 top bar one row, p02 (${tag})`, tb1.rows === 1 && tb1.h <= 48 && tb1.out === 0, tb1);
  // X13: the ticks of window 1 (exposed by slices.js for tests after the fix; before it, only the screenshot)
  const ax = await page.evaluate(() => { const W = document.querySelector(".s3d-windows").__slices; return W.ticks ? W.ticks(1) : null; });
  const round = (v, step) => Math.abs(v / step - Math.round(v / step)) < 1e-6;
  const nice125 = (s) => { const e = Math.floor(Math.log10(s) + 1e-12), m = s / 10 ** e; return [1, 2, 5, 10].some((k) => Math.abs(m - k) < 1e-6); };
  check(`X13 window ticks round, last label inside (${tag})`, !!ax && ax.h.values.length >= 2 && ax.v.values.length >= 2
    && nice125(ax.h.step) && nice125(ax.v.step) && ax.h.values.every((v) => round(v, ax.h.step)) && ax.v.values.every((v) => round(v, ax.v.step))
    && ax.h.lastRight <= ax.width + 0.5, ax ? { h: ax.h, v: ax.v, width: ax.width } : { ticks: "not exposed (before the fix)" });
  // X2: pick the detector (o2) in the world's own window, Delete
  const rec0 = await record(id);
  const nRem = (r) => r.filter((m) => m.type === "command" && m.cmd === "scene" && m.args.op === "remove").length;
  const nView = (r) => r.filter((m) => m.type === "command" && m.cmd === "view").length;
  // negative control first: a click on the window's empty part (nothing of the scene there), then Delete: nothing goes
  const emptyPt = await page.evaluate(() => { const h = document.querySelector(".s3d-windows").__slices.helper(1), r = h.el.getBoundingClientRect(); return [r.left + 50, r.top + 14]; });
  await page.evaluate(() => window.__lfManip && document.querySelector(".pg-obj.sel") && document.querySelector(".pg-obj.sel").click());
  await page.mouse.click(emptyPt[0], emptyPt[1]); await sleep(300);
  const selNone = await page.evaluate(() => window.__lfManip.selected());
  await page.keyboard.press("Delete"); await sleep(1500);
  const recN = await record(id);
  const toastsN = await page.evaluate(() => [...document.querySelectorAll(".toast")].map((t) => t.textContent));
  check(`X2 control: Delete on the world's own window removes nothing (${tag})`, nRem(recN) === nRem(rec0) && nView(recN) === nView(rec0)
    && !toastsN.some((t) => /Срез не построен/.test(t)), { selectedBefore: selNone, removes: nRem(recN) - nRem(rec0), views: nView(recN) - nView(rec0), toasts: toastsN });
  const pd = await scrWin(page, "o2", 1);
  if (!pd) check(`X2 detector visible in window (${tag})`, false);
  else {
    await page.mouse.click(pd[0], pd[1]); await sleep(500);
    const st = await page.evaluate(() => ({ sel: window.__lfManip.selected(), slice: document.querySelector(".s3d-view")?.__scene3d?.state?.selected ?? null }));
    await page.keyboard.press("Delete");
    await waitFor(async () => nRem(await record(id)) > nRem(rec0), 8000, 300);
    await sleep(800);
    const rec1 = await record(id);
    const ts = await page.evaluate(() => [...document.querySelectorAll(".toast")].map((t) => t.textContent));
    check(`X2 Delete removes the object picked in the plane window (${tag})`, st.sel === "o2" && nRem(rec1) - nRem(rec0) === 1 && nView(rec1) === nView(rec0)
      && !ts.some((t) => /Срез не построен/.test(t)), { picked: st, removes: nRem(rec1) - nRem(rec0), views: nView(rec1) - nView(rec0), toasts: ts });
    await page.screenshot({ path: `${OUT}/${PHASE}_X2_delete_${tag}.png` });
  }
  // X8: three toasts at once never overlap (the player's own toast function)
  await page.evaluate(async () => { const ui = await import("/static/js/ui.js"); ui.toast("Первое сообщение об ошибке: проверка стопки", "error", 20000); ui.toast("Второе: уведомление о переносе сцены, длинное, чтобы занять две строки текста в окне сообщения справа внизу", "notice", 20000); ui.toast("Третье сообщение", "notice", 20000); });
  await sleep(400);
  const tr = await toastRects(page);
  check(`X8 toasts do not overlap (${tag})`, tr.length >= 3 && overlaps(tr) === 0, { n: tr.length, overlaps: overlaps(tr), rects: tr.map((r) => [Math.round(r.top), Math.round(r.bottom)]) });
  await page.screenshot({ path: `${OUT}/${PHASE}_X8_toasts_${tag}.png` });
  await page.evaluate(() => document.querySelectorAll(".toast").forEach((t) => t.remove()));
  // --- X3: «Новый мир» with the space chosen -----------------------------------------------------------------------
  const head = page.locator("text=Новый мир: законы и начальные условия").first();
  await head.scrollIntoViewIfNeeded(); await head.click(); await sleep(600);
  const dimSel = page.locator("#left select, #right select").filter({ has: page.locator("option[value='3d']") }).first();
  await dimSel.selectOption("3d"); await sleep(500);
  const form = await page.evaluate(() => {
    const box = [...document.querySelectorAll(".panel")].find((d) => /Новый мир/.test(d.querySelector("h4")?.textContent || ""));
    const labs = box ? [...box.querySelectorAll("label")].filter((l) => l.offsetParent !== null).map((l) => l.textContent.trim()) : [];
    return { labels: labs };
  });
  const hasGrid = form.labels.some((l) => /Точек сетки/.test(l)), hasWin = form.labels.some((l) => /Размер окна/.test(l));
  check(`X3 new-world form of the space shows the grid and the window (${tag})`, hasGrid && hasWin, { labels: form.labels.slice(0, 30) });
  await page.locator("text=Новый мир: законы и начальные условия").first().screenshot({ path: `${OUT}/${PHASE}_X3_form_head_${tag}.png` }).catch(() => {});
  await page.screenshot({ path: `${OUT}/${PHASE}_X3_form_${tag}.png` });
  // the new world (carried): the top bar with the world selector stays one row
  await page.locator("button", { hasText: "Начать новый мир" }).click();
  await waitFor(async () => (await record(id)).filter((m) => m.type === "header").length >= 2, 180000, 500);
  await sleep(3000);
  const tb2 = await topbar(page);
  check(`X8 top bar one row with the world selector (${tag})`, tb2.rows === 1 && tb2.h <= 48 && tb2.out === 0, tb2);
  const tr2 = await toastRects(page);
  check(`X8 the carry-over's toasts do not overlap (${tag})`, overlaps(tr2) === 0, { n: tr2.length, texts: tr2.map((r) => r.text) });
  await page.screenshot({ path: `${OUT}/${PHASE}_X8_new_world_${tag}.png` });
  check(`no page errors p02 (${tag})`, errs.length === 0, { errs: errs.slice(0, 3) });
  await page.close();
  await cmd(id, "stop").catch(() => {});
  // --- X8 in p01 (its long title and badges) -------------------------------------------------------------------------
  const id1 = await newRun("p01_gravity", null);
  const p1 = await br.newPage({ viewport: { width: Wd, height: Ht } });
  await openRun(p1, id1);
  const tb3 = await topbar(p1);
  check(`X8 top bar one row, p01 (${tag})`, tb3.rows === 1 && tb3.h <= 48 && tb3.out === 0, tb3);
  await p1.screenshot({ path: `${OUT}/${PHASE}_X8_p01_${tag}.png` });
  await p1.close();
  await cmd(id1, "stop").catch(() => {});
}
await br.close();
const bad = checks.filter((c) => !c.ok).length;
console.log(bad ? `${bad} failed` : "all passed");
process.exit(bad ? 1 : 0);
