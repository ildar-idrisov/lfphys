// Review 2026-11-12 i18n-browser: shared helpers for the browser scripts (Playwright 1.58.2, Chromium swiftshader).
// Run through run_pw.sh against the private server lf-rv18b-srv (port 8652).
import { chromium } from "playwright";
import { appendFileSync, mkdirSync } from "node:fs";

export const port = process.env.PORT || "8652";
export const base = `http://127.0.0.1:${port}`;
export const SHOTS = "/shots";
export const LOGS = "/logs";
mkdirSync(SHOTS, { recursive: true });
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
export const get = async (u) => (await fetch(base + u)).json();
export const del = async (u) => fetch(base + u, { method: "DELETE" });

let LOGFILE = `${LOGS}/out.jsonl`;
export function setLog(name) { LOGFILE = `${LOGS}/${name}.jsonl`; }
export function log(o) { const s = JSON.stringify(o); console.log(s.slice(0, 600)); appendFileSync(LOGFILE, s + "\n"); }

export async function browser() {
  return chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
}

// a page that records page errors and console errors/warnings
export async function newPage(ctx, tag) {
  const page = await ctx.newPage();
  page.__errs = [];
  page.on("pageerror", (e) => { page.__errs.push(`pageerror: ${e.message}`.slice(0, 400)); log({ tag, pageerror: e.message.slice(0, 400) }); });
  page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") { const s = `${m.type()}: ${m.text()}`.slice(0, 400); page.__errs.push(s); log({ tag, console: s }); } });
  return page;
}

export const shot = async (page, name, full = false) => { try { await page.screenshot({ path: `${SHOTS}/${name}.png`, fullPage: full }); } catch (e) { log({ shotError: name, e: e.message }); } };

// scans what a viewer reads on the page (visible text nodes, titles, placeholders, options) for i18n defects
export async function scan(page, L, where) {
  const r = await page.evaluate((L) => {
    const CYR = /[Ѐ-ӿ]/;
    const vis = (e) => { if (!e) return false; const s = getComputedStyle(e); if (s.visibility === "hidden" || s.display === "none") return false; const rc = e.getBoundingClientRect(); return rc.width > 0 && rc.height > 0 && e.offsetParent !== null || s.position === "fixed"; };
    const path = (e) => { const p = []; let x = e; for (let i = 0; x && x.nodeType === 1 && i < 5; i++, x = x.parentElement) p.unshift(x.tagName.toLowerCase() + (x.id ? "#" + x.id : "") + (x.className && typeof x.className === "string" ? "." + x.className.trim().split(/\s+/).slice(0, 2).join(".") : "")); return p.join(">"); };
    const own = (e) => e.closest(".lang-switch");
    const items = [];
    const tw = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = tw.nextNode(); n; n = tw.nextNode()) {
      const s = n.nodeValue.replace(/\s+/g, " ").trim();
      if (!s) continue;
      const e = n.parentElement;
      if (!e || own(e) || e.closest("script,style") || !vis(e)) continue;
      items.push({ k: "text", s, at: path(e) });
    }
    for (const e of document.querySelectorAll("[title]")) if (!own(e) && vis(e)) items.push({ k: "title", s: e.getAttribute("title"), at: path(e) });
    for (const e of document.querySelectorAll("[placeholder]")) if (vis(e)) items.push({ k: "ph", s: e.getAttribute("placeholder"), at: path(e) });
    for (const sel of document.querySelectorAll("select")) if (vis(sel)) for (const o of sel.options) items.push({ k: "opt", s: o.textContent, at: path(sel) });
    for (const e of document.querySelectorAll("input[type=button],input[type=submit]")) if (vis(e)) items.push({ k: "val", s: e.value, at: path(e) });
    // canvas-drawn text cannot be read here; the screenshots are looked at
    const bad = [];
    for (const it of items) {
      const s = it.s || "";
      const why = [];
      if (/\[object Object\]/.test(s)) why.push("object");
      if (/\$t\b|"\$t"/.test(s)) why.push("raw$t");
      if (/\{[a-z_][a-z_0-9]*(:[^{}]*)?\}/i.test(s) && !/\{\s*"/.test(s)) why.push("placeholder");
      if (/\bundefined\b|\bNaN\b|\bnull\b/.test(s)) why.push("undef");
      if (L === "en" && CYR.test(s)) why.push("cyrillic-in-en");
      if (L === "ru" && !CYR.test(s)) {
        const words = (s.match(/\b[A-Za-z][a-z]{2,}\b/g) || []).filter((w) => !/^(lfphys|GPU|CPU|CSV|NIST|CODATA|LBM|FDTD|Bohm|Kerr|Mie|QCD|JSON|PDG|Verlet|Runge|Kutta|Lennard|Jones|Dirac|Boltzmann|Schwarzschild|Lorentz|Maxwell|Thomas|Wigner|Bell|CHSH|Navier|Stokes|Reynolds|Fresnel|Snell|Brewster|Laguerre|Gauss|Hermite|Planck|Coulomb|Newton|Einstein|Debye|Rydberg|Bohr|Hartree|Ångström|NumPy|SciPy|CuPy|three|max|min|exp|sin|cos|log|ln|arg|Re|Im|deg|rad|mod)$/i.test(w));
        if (words.length >= 2) why.push("latin-in-ru");
      }
      if (L === "ru") {
        // a decimal point between digits (not a version, an id, a date or a file name)
        const t2 = s.replace(/v?\d+\.\d+\.\d+(\.\d+)?/g, "").replace(/\b\d{8}-\d{6}\b/g, "").replace(/[\w-]+\.(png|json|csv|lfrec|lfscene|md|txt|html|js)\b/gi, "");
        if (/(^|[^\w.])\d+\.\d+(?![\w.]*\.\w)/.test(t2)) why.push("decimal-point-in-ru");
      }
      if (L === "en" && /(^|[^\d,])\d{1,3},\d{1,2}(?!\d)/.test(s) && !/\(\d+,\s?\d+\)|\[\d/.test(s)) why.push("decimal-comma-in-en?");
      if (/(^|[\s(\[=:;≈≤≥<>])-\d/.test(s) && it.k !== "ph") why.push("hyphen-minus");
      if (why.length) bad.push({ ...it, why });
    }
    // truncated / overflowing labels
    const over = [];
    for (const e of document.querySelectorAll("body *")) {
      if (!vis(e) || own(e) || e.closest(".lang-switch")) continue;
      if (["CANVAS", "SVG", "svg", "INPUT", "SELECT", "TEXTAREA", "HTML", "BODY", "path", "IMG"].includes(e.tagName)) continue;
      const txt = [...e.childNodes].filter((c) => c.nodeType === 3).map((c) => c.nodeValue).join("").trim();
      if (!txt) continue;
      const cs = getComputedStyle(e);
      const clipped = (e.scrollWidth > e.clientWidth + 1 && cs.overflowX !== "visible") || (e.scrollHeight > e.clientHeight + 2 && cs.overflowY === "hidden" && cs.whiteSpace !== "normal");
      const rc = e.getBoundingClientRect();
      const side = e.closest(".side, .panel, .modal, .card");
      let sticks = false;
      if (side) { const pr = side.getBoundingClientRect(); sticks = rc.right > pr.right + 2 && cs.position !== "fixed" && cs.position !== "absolute"; }
      if (clipped || sticks || rc.right > innerWidth + 2) over.push({ s: txt.slice(0, 80), at: path(e), clipped, sticks, offscreen: rc.right > innerWidth + 2, sw: e.scrollWidth, cw: e.clientWidth });
    }
    // select options wider than the select (a cut label)
    return { bad, over: over.slice(0, 40), n: items.length, docW: document.documentElement.scrollWidth, winW: innerWidth, lang: document.documentElement.lang };
  }, L);
  // log
  const errs = page.__errs.splice(0);
  log({ where, L, n: r.n, bad: r.bad.slice(0, 40), nbad: r.bad.length, over: r.over, hscroll: r.docW > r.winW + 2, lang: r.lang, errs });
  return r;
}

// a run started by the API, retried while the workers are busy
export async function startRun(body) {
  let r = null;
  for (let k = 0; k < 60; k++) {
    r = await post("/api/runs", body);
    if (r.id || !JSON.stringify(r.error || "").match(/busy|занят/)) break;
    await sleep(3000);
  }
  return r;
}

export const SMALL = {
  v08_wave_3d: { n: 128, zmax: 10.0 },
  v09_thomas_3d: { ngrid: 48 },
  v11_double_slit_2d: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 100, n_tracks: 10 },
  v12_arrival_times_2d: { grid: "coarse", n_bohm: 100, n_tracks: 10, L: 12.0, sigma_z: 2.0, sigma_x: 2.0 },
  v15_kerr_shadow: { res: "s" },
  v17_mie_scattering: { radius_um: 1.0, width: 0.05, n_lam: 8 },
};

export async function waitPlayer(page, ms = 240000) {
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !window.__lfPlayer.replaying(), null, { timeout: ms });
}

// opens every closed panel (h4 click) whose title matches
export async function openPanel(page, re) {
  return page.evaluate((src) => {
    const rx = new RegExp(src, "i"); const out = [];
    for (const p of document.querySelectorAll(".panel")) {
      const h = p.querySelector(":scope > h4"); if (!h) continue;
      if (rx.test(h.textContent)) { if (p.classList.contains("closed")) h.click(); out.push(h.textContent); }
    }
    return out;
  }, re.source || re);
}
