// U-use: every world's default page and one more preset, as the owner sees it at 1600x1000 and 1280x800: screenshots,
// horizontal overflow of the panels and bars (elements cut off or pushing a horizontal scrollbar), text smaller than
// 11 px, the canvas's share of the window, raw errors (toasts, events, console), and the response to the first live
// control changed by hand (how long the "rebuilding" indicator stays). Usage: node usability.mjs [viz ...]
import { base, browser, get, newRun, play, sleep, shot, post } from "./common.mjs";
import fs from "fs";

const SMALL = {
  v08_wave_3d: { n: 128, zmax: 10.0 },
  v09_thomas_3d: { ngrid: 48 },
  v11_double_slit_2d: { grid: "coarse", n_bohm: 100, n_tracks: 10 },
  v12_arrival_times_2d: { grid: "coarse", n_bohm: 100, n_tracks: 10 },
  v15_kerr_shadow: { res: "s" },
  v17_mie_scattering: { n_lam: 8 },
  p04_fluids: { nx: "256" },
};

async function metrics(page) {
  return page.evaluate(() => {
    const out = { overflow: [], small_text: 0, small_examples: [], hscroll: {} };
    for (const sel of ["#left", "#right", ".topbar", ".bottombar"]) {
      const e = document.querySelector(sel); if (!e) continue;
      out.hscroll[sel] = e.scrollWidth > e.clientWidth + 1 ? `${e.scrollWidth}>${e.clientWidth}` : 0;
      const R = e.getBoundingClientRect();
      for (const c of e.querySelectorAll("*")) {
        if (!c.offsetParent) continue;
        const r = c.getBoundingClientRect();
        if (r.width > 0 && (r.right > R.right + 2 || r.left < R.left - 2) && c.children.length === 0) {
          out.overflow.push(`${sel} ${c.tagName.toLowerCase()}${c.className && typeof c.className === "string" ? "." + c.className.split(" ")[0] : ""} «${(c.textContent || c.value || "").trim().slice(0, 50)}» +${Math.round(r.right - R.right)}px`);
        }
      }
    }
    // text cut by its own box (ellipsis or overflow hidden)
    for (const c of document.querySelectorAll(".run *")) {
      if (!c.offsetParent || c.children.length) continue;
      const cs = getComputedStyle(c);
      if ((cs.overflow === "hidden" || cs.textOverflow === "ellipsis") && c.scrollWidth > c.clientWidth + 1 && (c.textContent || "").trim())
        out.overflow.push(`cut ${c.tagName.toLowerCase()}.${(c.className || "").toString().split(" ")[0]} «${c.textContent.trim().slice(0, 60)}»`);
      const fs = parseFloat(cs.fontSize);
      if ((c.textContent || "").trim() && fs < 11) { out.small_text++; if (out.small_examples.length < 4) out.small_examples.push(`${fs}px «${c.textContent.trim().slice(0, 30)}»`); }
    }
    out.overflow = [...new Set(out.overflow)].slice(0, 12);
    const vh = innerHeight, vw = innerWidth;
    const cen = document.querySelector("#center").getBoundingClientRect();
    const canv = [...document.querySelectorAll("#center canvas")].filter((c) => c.offsetParent).map((c) => c.getBoundingClientRect());
    const big = canv.sort((a, b) => b.width * b.height - a.width * a.height)[0];
    out.center = `${Math.round(cen.width)}x${Math.round(cen.height)}`;
    out.main_canvas = big ? `${Math.round(big.width)}x${Math.round(big.height)} (${Math.round(100 * big.width * big.height / (vw * vh))}% of window)` : null;
    out.topbar_h = Math.round(document.querySelector(".topbar").getBoundingClientRect().height);
    out.bottombar_h = Math.round(document.querySelector(".bottombar").getBoundingClientRect().height);
    out.toasts = [...document.querySelectorAll(".toast")].map((t) => t.textContent.slice(0, 300));
    out.raw = [...document.querySelectorAll(".toast, .events .ev")].map((t) => t.textContent).filter((x) => /Traceback|File "|Error:|Exception/.test(x)).map((x) => x.slice(0, 300));
    out.status = document.getElementById("status").textContent;
    out.title = document.getElementById("scene").textContent.slice(0, 120);
    return out;
  });
}

async function firstLive(page) {
  // the first visible live control of the panel «Установка — меняется сразу»
  const info = await page.evaluate(() => {
    const ctl = [...document.querySelectorAll("#left details.lgroup .ctl")].find((c) => c.offsetParent && !c.querySelector(":disabled"));
    if (!ctl) return null;
    ctl.setAttribute("data-ux", "1");
    const lab = ctl.querySelector("label") ? ctl.querySelector("label").textContent : "";
    const sel = ctl.querySelector("select"), num = ctl.querySelector("input[type=number]"), cb = ctl.querySelector("input[type=checkbox]");
    return { label: lab, kind: sel ? "select" : num ? "number" : cb ? "bool" : "?", value: sel ? sel.value : num ? num.value : cb ? cb.checked : null,
             options: sel ? [...sel.options].map((o) => o.value) : null };
  });
  if (!info) return null;
  const nH = await page.evaluate(() => document.getElementById("world").options.length);
  const t0 = Date.now();
  if (info.kind === "select") { const v = info.options.find((o) => o !== info.value); await page.selectOption("[data-ux] select", v); info.to = v; }
  else if (info.kind === "number") { const v = String(Number(info.value) * 1.1 || 1); await page.fill("[data-ux] input[type=number]", v); await page.press("[data-ux] input[type=number]", "Enter"); info.to = v; }
  else if (info.kind === "bool") { await page.click("[data-ux] input[type=checkbox]"); info.to = !info.value; }
  await page.waitForFunction(() => document.getElementById("busy").style.display !== "none", null, { timeout: 1500 }).catch(() => {});
  await page.waitForFunction(() => document.getElementById("busy").style.display === "none", null, { timeout: 60000 }).catch(() => {});
  info.busy_s = (Date.now() - t0) / 1000;
  info.toasts = await page.$$eval(".toast", (ts) => ts.map((t) => t.textContent.slice(0, 200)));
  info.new_world = (await page.evaluate(() => document.getElementById("world").options.length)) !== nH;
  return info;
}

const b = await browser();
fs.mkdirSync("/pw/shots", { recursive: true });
const all = await get("/api/viz");
const want = process.argv.slice(2);
for (const v of all) {
  if (want.length && !want.includes(v.id)) continue;
  const presets = v.schema.presets.map((p) => p.id);
  const pick = [presets[0], presets[Math.min(presets.length - 1, Math.max(1, Math.floor(presets.length / 2)))]].filter((x, i, a) => x && a.indexOf(x) === i);
  for (const [pi, preset] of pick.entries()) {
    const res = { viz: v.id, preset };
    let id;
    try { id = await newRun(v.id, { preset, ...(SMALL[v.id] ? { params: SMALL[v.id] } : {}) }); }
    catch (e) { res.start_error = String(e).slice(0, 400); console.log(JSON.stringify(res)); fs.appendFileSync("/pw/out_use.jsonl", JSON.stringify(res) + "\n"); continue; }
    const ctx = await b.newContext({ viewport: { width: 1600, height: 1000 } });
    const page = await ctx.newPage();
    const logs = [];
    page.on("console", (m) => { if (m.type() === "error") logs.push(m.text().slice(0, 300)); });
    page.on("pageerror", (e) => logs.push("pageerror: " + String(e).slice(0, 300)));
    try {
      await page.goto(`${base}/run?id=${id}`);
      await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка/.test(document.getElementById("status").textContent), null, { timeout: 180000 });
      await play(page);
      await sleep(6000);
      res.m1600 = await metrics(page);
      // paused before the screenshots: under the host's load a page drawing every frame did not yield a screenshot in 30 s
      await post(`/api/runs/${id}/command`, { cmd: "pause" });
      await sleep(1500);
      await shot(page, `/pw/shots/use_${v.id}_${preset}_1600.jpg`, { timeout: 90000 });
      await page.setViewportSize({ width: 1280, height: 800 });
      await sleep(1500);
      res.m1280 = await metrics(page);
      await shot(page, `/pw/shots/use_${v.id}_${preset}_1280.jpg`, { timeout: 90000 });
      await post(`/api/runs/${id}/command`, { cmd: "play" });
      if (pi === 0) res.live = await firstLive(page);
      res.console = logs.slice(0, 6);
    } catch (e) { res.error = String(e).slice(0, 400); try { await shot(page, `/pw/shots/use_${v.id}_${preset}_fail.jpg`); } catch (e2) {} }
    console.log(JSON.stringify(res));
    fs.appendFileSync("/pw/out_use.jsonl", JSON.stringify(res) + "\n");
    await ctx.close();
    await post(`/api/runs/${id}/stop`, {});
  }
}
await b.close();
