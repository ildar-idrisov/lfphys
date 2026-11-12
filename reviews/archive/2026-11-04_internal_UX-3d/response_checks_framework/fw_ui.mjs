// Browser checks of the framework/player findings (UX-ui U1 list, U4, U9, U10, U13, U14, U16, U17, U20-U24; UX-params
// P1, P2, P4). The same script before and after the fixes: node fw_ui.mjs <prefix> [case,...]
// Private server only (PORT, default 8572). Screenshots to /pw/shots/<prefix>_<case>_<w>.jpg, results to
// /pw/out_<prefix>.json (one entry per case).
import { chromium } from "playwright";
import fs from "fs";
import { extraCases } from "./cases_extra.mjs";

const prefix = process.argv[2] || "before";
const only = (process.argv[3] || "").split(",").filter(Boolean);
const port = process.env.PORT || "8572";
const base = `http://127.0.0.1:${port}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const post = async (u, b) => { const r = await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) }); return r.json(); };
const get = async (u) => (await fetch(base + u)).json();
const SIZES = [[1600, 1000], [1280, 800]];
fs.mkdirSync("/pw/shots", { recursive: true });
const outFile = `/pw/out_${prefix}.json`;
const OUT = fs.existsSync(outFile) ? JSON.parse(fs.readFileSync(outFile, "utf8")) : {};
const save = () => fs.writeFileSync(outFile, JSON.stringify(OUT, null, 1));

const b = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
async function page(w, h) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, acceptDownloads: true });
  const p = await ctx.newPage();
  p.logs = [];
  p.on("console", (m) => { if (m.type() === "error") p.logs.push("console: " + m.text().slice(0, 300)); });
  p.on("pageerror", (e) => p.logs.push("pageerror: " + String(e).slice(0, 300)));
  p.ctx = ctx;
  return p;
}
async function newRun(viz, body = {}) { const r = await post("/api/runs", { viz, ...body }); return r; }
async function openRun(p, id, wait = true) {
  await p.goto(`${base}/run?id=${id}`);
  if (wait) await p.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка/.test(document.getElementById("status").textContent), null, { timeout: 180000 });
}
async function play(p) {
  const txt = await p.textContent("#rec");
  if (!/запись/.test(txt)) await p.click("#rec");
  await p.waitForFunction(() => /запись идёт/.test(document.getElementById("status").textContent), null, { timeout: 120000 });
}
async function pauseRec(p) { const txt = await p.textContent("#rec"); if (/запись/.test(txt)) await p.click("#rec"); await sleep(600); }
const toasts = (p) => p.$$eval(".toast", (ts) => ts.map((t) => t.textContent));
const shot = (p, name) => p.screenshot({ path: `/pw/shots/${prefix}_${name}.jpg`, type: "jpeg", quality: 72, timeout: 120000 }).catch((e) => console.error("shot", name, String(e).slice(0, 100)));
const panelBody = (p, re) => p.evaluateHandle((s) => { const r = new RegExp(s); const P = [...document.querySelectorAll(".panel")].find((x) => r.test(x.querySelector("h4").textContent)); return P || null; }, re);

const CASES = {
  // P1: a world refused at its start (v13 «Суперпозиция» from the defaults)
  async p1_v13_super() {
    const r = await newRun("v04_orbits", { params: { radius_km: 1000, r0: 2.1 } });
    const out = { start: r };
    if (!r.id) return out;
    const p = await page(1600, 1000);
    await openRun(p, r.id, false);
    await sleep(12000);
    out.status = await p.textContent("#status");
    out.toasts = await toasts(p);
    out.events = await p.$$eval(".events .ev, .events .muted", (es) => es.map((e) => e.textContent.slice(0, 200)));
    out.passport_state = (await get(`/api/runs/${r.id}`)).state;
    await shot(p, "p1_refused_start_1600");
    out.logs = p.logs;
    await p.ctx.close();
    // the catalogue's run list
    const c = await page(1600, 1000);
    await c.goto(base + "/"); await sleep(3000);
    out.catalogue_row = await c.evaluate((id) => { const a = [...document.querySelectorAll("table.runs a")].find((x) => x.href.includes(id)); return a ? a.closest("tr").textContent.slice(0, 300) : null; }, r.id);
    await c.ctx.close();
    return out;
  },
  // P1 (2) + P2: the catalogue's start form: a refused combination, a typed value above its maximum, an emptied field
  async p2_catalogue() {
    const out = {};
    for (const [w, h] of SIZES) {
      const c = await page(w, h);
      await c.goto(base + "/"); await c.waitForSelector(".card"); await sleep(800);
      const card = await c.evaluateHandle(() => [...document.querySelectorAll(".card")].find((x) => x.textContent.includes("v05_optics_bench")));
      const btn = await card.$("button:has-text('Параметры')");
      await btn.click(); await sleep(400);
      const inp = await card.$('.field[data-pid="lam_nm"] input');
      await inp.click({ clickCount: 3 }); await c.keyboard.type("2000"); await c.keyboard.press("Tab"); await sleep(300);
      const run = await card.$("button:has-text('Запустить')");
      const url0 = c.url();
      await run.click(); await sleep(2500);
      out[`above_max_${w}`] = { url_changed: c.url() !== url0, toasts: await toasts(c), inline: await card.evaluate((x) => [...x.querySelectorAll(".start-err, .field-err")].map((e) => e.textContent).filter(Boolean)) };
      await shot(c, `p2_catalogue_above_${w}`);
      if (c.url() !== url0) { await c.ctx.close(); continue; }
      await inp.click({ clickCount: 3 }); await c.keyboard.press("Backspace"); await c.keyboard.press("Tab"); await sleep(300);
      out[`emptied_${w}`] = { value_after: await inp.evaluate((e) => e.value), inline: await card.evaluate((x) => [...x.querySelectorAll(".start-err, .field-err")].map((e) => e.textContent).filter(Boolean)) };
      await shot(c, `p2_catalogue_empty_${w}`);
      await c.ctx.close();
    }
    // a combination the world refuses when it is built (v04: the start inside the body): does the form say why?
    try {
      const c = await page(1600, 1000);
      await c.goto(base + "/"); await c.waitForSelector(".card"); await sleep(800);
      const card = await c.evaluateHandle(() => [...document.querySelectorAll(".card")].find((x) => x.textContent.includes("v04_orbits")));
      await (await card.$("button:has-text('Параметры')")).click(); await sleep(400);
      for (const [pid, val] of [["radius_km", "1000"], ["r0", "2.1"]]) {
        const inp = await card.$(`.field[data-pid="${pid}"] input`);
        await inp.click({ clickCount: 3 }); await c.keyboard.type(val); await c.keyboard.press("Tab");
      }
      const url0 = c.url();
      await (await card.$("button:has-text('Запустить')")).click();
      await sleep(9000);
      out.refused_start = { url_changed: c.url() !== url0, url: c.url(), toasts: await toasts(c), inline: await card.evaluate((x) => [...x.querySelectorAll(".start-err")].map((e) => e.textContent).filter(Boolean)) };
      await card.evaluate((x) => x.scrollIntoView());
      await shot(c, "p2_catalogue_refused_start");
      await c.ctx.close();
    } catch (e) { out.refused_start = { failed: String(e).slice(0, 200) }; }
    return out;
  },
  // P2: a live control typed above its maximum
  async p2_live() {
    const r = await newRun("v05_optics_bench", { preset: "brewster" });
    const p = await page(1600, 1000);
    await openRun(p, r.id);
    const inp = await p.evaluateHandle(() => [...document.querySelectorAll("#left .ctl")].find((x) => /Длина волны/.test(x.textContent)).querySelector("input[type=number]"));
    await inp.click({ clickCount: 3 }); await p.keyboard.type("2000"); await p.keyboard.press("Enter");
    await sleep(2500);
    const out = { toasts: await toasts(p), value: await inp.evaluate((e) => e.value), inline: await p.evaluate(() => [...document.querySelectorAll("#left .ctl-err")].map((e) => e.textContent).filter(Boolean)) };
    await shot(p, "p2_live_1600");
    await p.ctx.close();
    await post(`/api/runs/${r.id}/stop`);
    return out;
  },
  // U9 (+U3 visible part): a palette click in p02's double slit while recording
  async u9_p02() {
    const r = await newRun("p02_quantum", { preset: "double_slit" });
    const p = await page(1600, 1000);
    await openRun(p, r.id);
    await play(p); await sleep(2000);
    const n0 = await p.$$eval(".pg-obj", (x) => x.length);
    const btn = await p.evaluateHandle(() => [...document.querySelectorAll(".pg-buttons button")].find((x) => /Барьер/.test(x.textContent)));
    const t0 = Date.now();
    await btn.click();
    await sleep(1500);
    const out = { busy_after_1_5s: await p.evaluate(() => { const b = document.getElementById("busy"); return b && b.style.display !== "none" ? b.textContent : null; }), status: await p.textContent("#status"),
      form: await p.evaluate(() => !!document.querySelector(".pg-place")) };
    await shot(p, "u9_p02_busy_1600");
    // if a placement form opened, confirm it
    const go = await p.$(".pg-place button.primary");
    if (go) { await go.click(); await sleep(1500); out.busy_after_place = await p.evaluate(() => { const b = document.getElementById("busy"); return b && b.style.display !== "none" ? b.textContent : null; }); await shot(p, "u9_p02_busy_after_place_1600"); }
    await p.waitForFunction((n) => document.querySelectorAll(".pg-obj").length !== n, n0, { timeout: 120000 }).catch(() => {});
    out.added_after_s = (Date.now() - t0) / 1000;
    out.busy_end = await p.evaluate(() => { const b = document.getElementById("busy"); return b && b.style.display !== "none" ? b.textContent : null; });
    out.logs = p.logs;
    await p.ctx.close();
    await post(`/api/runs/${r.id}/stop`);
    return out;
  },
  // U16, U20: v04 and v07 at both sizes (checks panel width, bars, canvas share)
  async u16_u20() {
    const out = {};
    for (const [viz, preset] of [["v04_orbits", "default"], ["v07_bell_test", "spin_lhv"], ["p02_quantum", "double_slit"], ["p04_fluids", null]]) {
      const r = await newRun(viz, preset ? { preset } : {});
      for (const [w, h] of SIZES) {
        const p = await page(w, h);
        await openRun(p, r.id);
        if (w === 1600) { await play(p); await sleep(viz === "v04_orbits" ? 5000 : 3000); await pauseRec(p); }
        await sleep(1200);
        out[`${viz}_${w}`] = await p.evaluate(() => {
          const R = document.getElementById("right"), top = document.querySelector(".topbar"), bot = document.querySelector(".bottombar");
          const cv = [...document.querySelectorAll("#center canvas")].map((c) => c.getBoundingClientRect()).sort((a, b) => b.width * b.height - a.width * a.height)[0];
          const tick = document.querySelector("#speedticks span");
          return { right_scroll: [R.scrollWidth, R.clientWidth], top_h: top.getBoundingClientRect().height, bottom_h: bot.getBoundingClientRect().height,
                   canvas: cv ? [Math.round(cv.width), Math.round(cv.height), +(cv.width * cv.height / innerWidth / innerHeight).toFixed(3)] : null,
                   tick_font: tick ? getComputedStyle(tick).fontSize : null,
                   checks_h: document.querySelector(".checks") ? Math.round(document.querySelector(".checks").getBoundingClientRect().height) : null };
        });
        await shot(p, `u20_${viz}_${w}`);
        if (w === 1280) {  // both side columns folded (⇤ ⇥): the centre takes the room
          await p.click("#fold-left"); await p.click("#fold-right"); await sleep(1200);
          out[`${viz}_${w}_folded`] = await p.evaluate(() => {
            const cv = [...document.querySelectorAll("#center canvas")].map((c) => c.getBoundingClientRect()).sort((a, b) => b.width * b.height - a.width * a.height)[0];
            return { canvas: cv ? [Math.round(cv.width), Math.round(cv.height), +(cv.width * cv.height / innerWidth / innerHeight).toFixed(3)] : null,
                     top_h: document.querySelector(".topbar").getBoundingClientRect().height };
          });
          await shot(p, `u20_${viz}_${w}_folded`);
        }
        await p.ctx.close();
      }
      await post(`/api/runs/${r.id}/stop`);
    }
    return out;
  },
  // U14, U17: «События» rebuilt every frame; «Прежние группы проверок» closing itself (v04 with boosts)
  async u14_u17() {
    const r = await newRun("v04_orbits", { preset: "default" });
    const p = await page(1600, 1000);
    await openRun(p, r.id);
    await post(`/api/runs/${r.id}/command`, { cmd: "speed", args: { value: 0.1 } });
    await play(p); await sleep(4000);
    const out = {};
    out.events_rebuilds_per_s = await p.evaluate(() => new Promise((res) => {
      let n = 0; const box = document.querySelector(".events");
      const mo = new MutationObserver((ms) => { for (const m of ms) if (m.type === "childList" && m.target === box) n++; });
      mo.observe(box, { childList: true }); setTimeout(() => { mo.disconnect(); res(n / 2); }, 2000);
    }));
    const res = [];
    for (let k = 0; k < 4; k++) {
      await p.keyboard.press("End"); await sleep(400);
      const q = await p.evaluate(() => { const e = document.querySelector(".events .ev"); if (!e) return null; e.scrollIntoView({ block: "center" }); const b = e.getBoundingClientRect(); return { x: b.left + 40, y: b.top + b.height / 2 }; });
      if (!q) { res.push("no line"); continue; }
      await p.mouse.move(q.x, q.y); await p.mouse.down(); await sleep(150); await p.mouse.up(); await sleep(500);
      res.push(/история/.test(await p.textContent("#status")) ? "jumped" : "no jump");
    }
    out.human_click_on_event = res;
    await p.keyboard.press("End");
    for (let i = 0; i < 6; i++) { await post(`/api/runs/${r.id}/command`, { cmd: "action", args: { name: "boost", args: { dv: 0.02 } } }); await sleep(2000); }
    await sleep(1500);
    const has = await p.evaluate(() => { const d = document.querySelector("details.older"); if (!d) return false; d.open = true; return true; });
    out.older_present = has;
    if (has) { const s = []; for (let i = 0; i < 16; i++) { s.push(await p.evaluate(() => { const d = document.querySelector("details.older"); return d ? (d.open ? 1 : 0) : "-"; })); await sleep(250); } out.older_open_series = s.join(""); }
    await shot(p, "u14_u17_v04_1600");
    await p.ctx.close();
    await post(`/api/runs/${r.id}/stop`);
    return out;
  },
  // U1 (object list), U10 (inspector focus), U21 (slice tools), U23 (left column), U4 (palette places with defaults)
  async u1_u10_u21_u23() {
    const r = await newRun("p01_gravity", { preset: "inner" });
    const out = {};
    for (const [w, h] of SIZES) {
      const p = await page(w, h);
      await openRun(p, r.id);
      out[`left_panels_${w}`] = await p.$$eval("#left .panel", (ps) => ps.map((x) => (x.classList.contains("closed") ? "▸ " : "▾ ") + x.querySelector("h4").textContent.slice(0, 40)));
      out[`tools_${w}`] = await p.$$eval(".s3d-tools button, .s3d-tools select", (bs) => bs.filter((x) => x.offsetParent).map((x) => x.textContent.slice(0, 20)));
      out[`hint_${w}`] = await p.$eval(".s3d-hint", (x) => x.textContent.slice(0, 200)).catch(() => null);
      await shot(p, `u21_u23_p01_${w}`);
      if (w === 1600) {
        await play(p); await sleep(1500);
        const rowOf = (label) => p.evaluateHandle((l) => [...document.querySelectorAll(".pg-obj")].find((x) => x.textContent.includes(l)), label);
        await (await rowOf("Земля")).asElement().click(); await sleep(800);
        const insp = await panelBody(p, "Инспектор");
        const nums = await insp.$$("input[type=number]");
        await nums[0].click({ clickCount: 3 }); await p.keyboard.type("2"); await p.keyboard.press("Tab");
        out.focus_after_tab = await p.evaluate(() => ({ tag: document.activeElement.tagName, type: document.activeElement.type, label: ((document.activeElement.closest(".ctl") || {}).textContent || "").slice(0, 40) }));
        await sleep(2500);
        out.focus_after_scene_msg = await p.evaluate(() => ({ tag: document.activeElement.tagName, type: document.activeElement.type, label: ((document.activeElement.closest(".ctl") || {}).textContent || "").slice(0, 40) }));
        for (let i = 0; i < 20; i++) await post(`/api/runs/${r.id}/command`, { cmd: "scene", args: { op: "add", type: "test", values: { x: 2 + 0.1 * i } } });
        await sleep(4000);
        const list = await p.$(".pg-list");
        const lb = await list.boundingBox();
        await p.mouse.move(lb.x + lb.width / 2, lb.y + lb.height / 2); await p.mouse.wheel(0, 900); await sleep(500);
        const st0 = await p.$eval(".pg-list", (e) => e.scrollTop);
        const last = (await p.$$(".pg-obj")).at(-1);
        await last.click(); await sleep(1500);
        out.list_scroll = { before_select: st0, after_select: await p.$eval(".pg-list", (e) => e.scrollTop) };
        // a scene change while the list is scrolled (another body added)
        await post(`/api/runs/${r.id}/command`, { cmd: "scene", args: { op: "add", type: "test", values: { x: 5 } } }); await sleep(2500);
        out.list_scroll.after_scene_change = await p.$eval(".pg-list", (e) => e.scrollTop);
        // U4: a palette button
        const btn = await p.evaluateHandle(() => [...document.querySelectorAll(".pg-buttons button")].find((x) => /Звезда/.test(x.textContent)));
        const n0 = await p.$$eval(".pg-obj", (x) => x.length);
        await btn.click(); await sleep(2500);
        out.palette_click = { form: await p.evaluate(() => (document.querySelector(".pg-place") || {}).textContent || null), objects_before: n0, objects_after: await p.$$eval(".pg-obj", (x) => x.length), toasts: await toasts(p) };
        await shot(p, "u4_palette_p01_1600");
        await pauseRec(p);
      }
      await p.ctx.close();
    }
    await post(`/api/runs/${r.id}/stop`);
    return out;
  },
  // P4 / U6: a palette action that breaks the world (p03 hard disks + atom): what the owner reads
  async p4_trace() {
    const r = await newRun("p03_molecules", { params: { model: "hard" } });
    const out = { start: r };
    if (!r.id) return out;
    const p = await page(1600, 1000);
    await openRun(p, r.id);
    await post(`/api/runs/${r.id}/command`, { cmd: "scene", args: { op: "add", type: "atom", values: {} } });
    await sleep(2000);
    await play(p).catch(() => {});
    await sleep(4000);
    out.toasts = await toasts(p);
    out.status = await p.textContent("#status");
    out.events = await p.$$eval(".events .ev", (es) => es.slice(-3).map((e) => e.textContent.slice(0, 300)));
    await shot(p, "p4_trace_p03_1600");
    await p.ctx.close();
    await post(`/api/runs/${r.id}/stop`);
    return out;
  },
};

Object.assign(CASES, extraCases({ newRun, page, openRun, play, pauseRec, shot, post, sleep, SIZES }));
for (const [name, fn] of Object.entries(CASES)) {
  if (only.length && !only.includes(name)) continue;
  const t0 = Date.now();
  try { OUT[name] = await fn(); } catch (e) { OUT[name] = { failed: String(e).slice(0, 400) }; }
  OUT[name].secs = Math.round((Date.now() - t0) / 1000);
  console.log(name, JSON.stringify(OUT[name]).slice(0, 1500));
  save();
}
await b.close();
