// U-scroll: does a scroll position survive live data? For the catalogue, demonstration runs and playground runs: the
// page and every scroll container (left and right panels, events, the scene's object list, the slice windows) are
// scrolled with the mouse wheel while a run records; scrollTop is sampled every 250 ms for 8 s. Instrumented: every
// programmatic scrollTop write, scrollIntoView and focus() is logged with its stack; DOM replacements of scroll
// containers are counted. Usage: node scroll.mjs [case ...]
import { base, browser, newRun, openRun, play, sleep, shot, post } from "./common.mjs";
import fs from "fs";

const INSTR = () => {
  window.__ux = { log: [], removed: [] };
  const d = (e) => e === document.scrollingElement ? "document" : (e.id ? "#" + e.id : "") + (e.className && typeof e.className === "string" ? "." + e.className.split(" ").join(".") : "") || e.tagName;
  const desc = Object.getOwnPropertyDescriptor(Element.prototype, "scrollTop");
  Object.defineProperty(Element.prototype, "scrollTop", { get: desc.get, set(v) {
    window.__ux.log.push({ t: performance.now(), kind: "set scrollTop", el: d(this), v, stack: new Error().stack.split("\n").slice(2, 6).join(" | ") });
    desc.set.call(this, v); }, configurable: true });
  const siv = Element.prototype.scrollIntoView;
  Element.prototype.scrollIntoView = function (...a) { window.__ux.log.push({ t: performance.now(), kind: "scrollIntoView", el: d(this), stack: new Error().stack.split("\n").slice(2, 6).join(" | ") }); return siv.apply(this, a); };
  const foc = HTMLElement.prototype.focus;
  HTMLElement.prototype.focus = function (...a) { window.__ux.log.push({ t: performance.now(), kind: "focus", el: d(this), stack: new Error().stack.split("\n").slice(2, 6).join(" | ") }); return foc.apply(this, a); };
  // scroll containers removed from the document (a new one starts at scrollTop 0)
  new MutationObserver((ms) => { for (const m of ms) for (const n of m.removedNodes) {
    if (n.nodeType === 1 && n.scrollTop > 0) window.__ux.removed.push({ t: performance.now(), el: d(n), scrollTop: n.scrollTop });
    if (n.nodeType === 1) for (const c of n.querySelectorAll("*")) if (c.scrollTop > 0) window.__ux.removed.push({ t: performance.now(), el: d(c), scrollTop: c.scrollTop });
  } }).observe(document, { childList: true, subtree: true });
};

async function sample(page, sel, ms = 8000) {
  const out = [];
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    out.push(await page.evaluate((s) => { const e = s === "document" ? document.scrollingElement : document.querySelector(s); return e ? Math.round(e.scrollTop) : null; }, sel));
    await sleep(250);
  }
  return out;
}

async function wheelOver(page, sel, dy = 500, times = 2) {
  const box = await page.evaluate((s) => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + Math.min(r.height / 2, 200), sh: e.scrollHeight, ch: e.clientHeight }; }, sel);
  if (!box) return null;
  await page.mouse.move(box.x, box.y);
  for (let i = 0; i < times; i++) { await page.mouse.wheel(0, dy); await sleep(120); }
  await sleep(300);
  return box;
}

async function containers(page, sels, tag) {
  const res = {};
  for (const sel of sels) {
    const info = await page.evaluate((s) => { const e = document.querySelector(s); return e ? { sh: e.scrollHeight, ch: e.clientHeight } : null; }, sel);
    if (!info) { res[sel] = "absent"; continue; }
    if (info.sh <= info.ch + 4) { res[sel] = `not scrollable (${info.sh}/${info.ch})`; continue; }
    await page.evaluate(() => { window.__ux.log.length = 0; window.__ux.removed.length = 0; });
    await wheelOver(page, sel);
    const s = await sample(page, sel);
    const log = await page.evaluate(() => window.__ux.log.filter((x) => x.kind !== "focus").slice(-6));
    const removed = await page.evaluate(() => window.__ux.removed.slice(-6));
    const s0 = s[0], resets = s.filter((v, i) => i > 0 && v < s[i - 1] - 20).length;
    res[sel] = { after_wheel: s0, min: Math.min(...s), max: Math.max(...s), final: s[s.length - 1], resets, series: s.join(","), log, removed };
  }
  return res;
}

const CASES = {
  catalog: async (b) => {
    // a live run viewed in another tab keeps the runs list changing every 2 s
    const id = await newRun("v04_orbits", { preset: "default" });
    const v = await openRun(b, id); await play(v.page);
    const ctx = await b.newContext({ viewport: { width: 1600, height: 1000 } });
    const page = await ctx.newPage();
    await page.addInitScript(INSTR);
    await page.goto(base + "/");
    await sleep(2500);
    const out = {};
    for (const mode of ["demo", "playground"]) {
      await page.click(mode === "demo" ? "#modes button:nth-child(1)" : "#modes button:nth-child(2)");
      await sleep(500);
      await page.evaluate(() => { window.__ux.log.length = 0; window.__ux.removed.length = 0; });
      await page.mouse.move(800, 500);
      for (let i = 0; i < 6; i++) { await page.mouse.wheel(0, 600); await sleep(100); }
      await sleep(400);
      const s = await sample(page, "document", 8000);
      out[mode] = { series: s.join(","), resets: s.filter((v, i) => i > 0 && v < s[i - 1] - 20).length, log: await page.evaluate(() => window.__ux.log.slice(-5)), removed: await page.evaluate(() => window.__ux.removed.slice(-5)) };
      await shot(page, `/pw/shots/scroll_catalog_${mode}.jpg`);
    }
    await ctx.close(); await v.ctx.close();
    return out;
  },
};
const RUNS = {
  v04: ["v04_orbits", { preset: "default" }],
  v02: ["v02_double_slit", { preset: "photon_young" }],
  v08: ["v08_wave_3d", { preset: "double", params: { n: 128, zmax: 10.0 } }],
  p01: ["p01_gravity", { preset: "inner" }],
  p03: ["p03_molecules", { preset: "maxwell" }],
  p04: ["p04_fluids", { preset: "cylinder_re20", params: { nx: "256" } }],
};
for (const [k, [viz, body]] of Object.entries(RUNS)) {
  CASES[k] = async (b) => {
    const out = {};
    for (const [w, h] of [[1600, 1000], [1280, 800]]) {
      const id = await newRun(viz, body);
      const ctx = await b.newContext({ viewport: { width: w, height: h } });
      const page = await ctx.newPage();
      await page.addInitScript(INSTR);
      await page.goto(`${base}/run?id=${id}`);
      await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка/.test(document.getElementById("status").textContent), null, { timeout: 120000 });
      await play(page);
      await sleep(4000);
      // open every closed panel: a user looking for something opens them (more to scroll)
      await page.evaluate(() => { for (const p of document.querySelectorAll(".panel.closed")) p.classList.remove("closed"); });
      await sleep(500);
      const r = await containers(page, ["#left", "#right", "#right .events", ".pg-list", ".s3d-windows"], k);
      // the folded older check groups: opened by the user, do they stay open?
      const older = await page.evaluate(() => { const d = document.querySelector("details.older"); if (!d) return null; d.open = true; return true; });
      let olderSeries = null;
      if (older) {
        olderSeries = [];
        for (let i = 0; i < 24; i++) { olderSeries.push(await page.evaluate(() => { const d = document.querySelector("details.older"); return d ? (d.open ? 1 : 0) : -1; })); await sleep(250); }
      }
      r.older_checks_open_series = olderSeries && olderSeries.join("");
      out[`${w}x${h}`] = r;
      await shot(page, `/pw/shots/scroll_${k}_${w}.jpg`);
      await ctx.close();
      await post(`/api/runs/${id}/stop`, {});
    }
    return out;
  };
}

const b = await browser();
fs.mkdirSync("/pw/shots", { recursive: true });
const want = process.argv.slice(2);
for (const name of (want.length ? want : Object.keys(CASES))) {
  try { const r = await CASES[name](b); console.log(JSON.stringify({ case: name, ...r })); fs.appendFileSync("/pw/out_scroll.jsonl", JSON.stringify({ case: name, ...r }) + "\n"); }
  catch (e) { console.log(JSON.stringify({ case: name, error: String(e).slice(0, 500) })); }
}
await b.close();
