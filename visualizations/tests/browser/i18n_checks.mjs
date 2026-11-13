// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
// The interface's languages in a browser (owner, 2026-11-12: «для всего фронта сделай i18n переводы на русский и
// английский, по дефолту английский и переключением языка»; RULES.md «Languages and i18n»), for each language given:
//  - every page (catalogue, run, settings, legal) has the switch EN | RU in its top bar; English by default; a click on
//    the other language stores it (localStorage "lfviz.lang") and reloads the page in it; "?lang=" overrides;
//  - the catalogue and a run page of every visualization: in English no Cyrillic in the visible text, the tooltips and
//    the options of the lists; in Russian the framework's texts are the catalogue's translations (and the page is in
//    Cyrillic);
//  - screenshots of the catalogue and of one run page per language;
//  - (review i18n-code F7, i18n-browser F4) a "?lang=" link's language holds on the pages reached by its links, without
//    changing the stored choice; the switch ends it;
//  - (review i18n-browser F1, F2) a number typed with a decimal comma is applied as such (650,5 is 650.5, not 6505),
//    and the fields show numbers in the language's format;
//  - (review i18n-code F8) in Russian, no visible line with two or more English words (names, symbols and units aside;
//    the licence texts, labelled «на английском», aside).
//
// Run against a PRIVATE server (never the shared one on 8479), with Playwright's image:
//   docker run -d --name lf-i18c-srv --memory=6g -p 8641:8479 -v <repo>:/lf:ro -v <scratch>/runs:/lf/visualizations/runs \
//     -e LFPHYS_NO_GPU=1 -e LFVIZ_EXTRA=/lf/visualizations/tests/playgrounds:/lf/visualizations/tests/instruments_worlds \
//     -w /lf/visualizations lfphys-viz python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 3
//   docker run --rm --init --shm-size=2g --network host --memory=4g -v <a scratch dir with node_modules/playwright>:/pw \
//     -v <repo>/visualizations/tests/browser:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy \
//     sh -c "cp /t/*.mjs /pw/ && node /pw/i18n_checks.mjs 8641 [en,ru] [viz,...] [shots folder]"
// Prints one JSON line per check and "all passed" or the number failed (exit code 1).
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";

const port = process.argv[2] || "8641";
const LANGS = (process.argv[3] || "en,ru").split(",");
const base = `http://127.0.0.1:${port}`;
const SHOTS = process.argv[5] || "/pw/shots";
mkdirSync(SHOTS, { recursive: true });
const CYR = /[\u0400-\u04ff]/;  // i18n-ok: recognises Cyrillic
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = 0;
const check = (name, ok, info = {}) => { if (!ok) failed++; console.log(JSON.stringify({ check: name, ok: !!ok, ...info })); };

// worlds heavy at their defaults: small geometries (as keyframes.mjs)
const SMALL = {
  u38_wave_3d: { n: 128, zmax: 10.0 },
  r11_thomas_3d: { ngrid: 48 },
  r12_double_slit_2d: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 100, n_tracks: 10 },
  r13_arrival_times_2d: { grid: "coarse", n_bohm: 100, n_tracks: 10, L: 12.0, sigma_z: 2.0, sigma_x: 2.0 },
  u42_kerr_shadow: { res: "s" },
  u44_mie_scattering: { radius_um: 1.0, width: 0.05, n_lam: 8 },
};
const vizList = await get("/api/viz");
const WORLDS = (process.argv[4] || vizList.map((v) => v.id).join(",")).split(",").filter(Boolean);
const catalogue = {};
for (const L of LANGS) catalogue[L] = (await get(`/api/i18n/${L}`)).messages || {};
const tr = (L, msgid) => { const v = catalogue[L][msgid]; return typeof v === "string" ? v : msgid; };

// what a viewer reads on the page: the visible text, the tooltips, the options of the lists (the switch's own names
// excepted: each language is named in itself)
const readable = (page) => page.evaluate(() => {
  const own = new Set([...document.querySelectorAll(".lang-switch, .lang-switch *")]);
  const titles = [...document.querySelectorAll("[title]")].filter((e) => !own.has(e) && e.offsetParent !== null).map((e) => e.getAttribute("title"));
  const options = [...document.querySelectorAll("select")].filter((s) => s.offsetParent !== null).flatMap((s) => [...s.options].map((o) => o.textContent));
  const ph = [...document.querySelectorAll("input[placeholder]")].filter((e) => e.offsetParent !== null).map((e) => e.placeholder);
  return { text: document.body.innerText, titles, options, ph, lang: document.documentElement.lang, title: document.title };
});
// Latin words that are not English prose: symbols, units, proper names, code-ish tokens (review i18n-code, b01)
const OK = new Set("Bohm Kerr Mie Newton Einstein Schwarzschild Lorentz Thomas Bell CHSH Young Planck Debye Airy Fresnel Brewster Fabry Perot Kretschmann Cornell PDG EHT GeV MeV keV TeV GPU CPU CSV JSON Lennard Jones Maxwell Boltzmann Reynolds Mach Kármán Gauss Bonnet Faraday Landau Rydberg Bohr Sgr M87 FLRW Hubble ΛCDM Coulomb Verlet Langevin Berendsen Andersen Nosé Hoover Poiseuille Couette Stokes Navier LBM BGK TRT MRT Ladd Zou PML FDTD TFSF Yee Courant Tsirelson GHZ Peters Mathews Johannsen Penrose Doppler Terrell Wigner Hamilton Heisenberg Schrödinger Dirac Pauli Feynman Kirchhoff Huygens Snell Rayleigh Lorenz Laguerre Hermite Bessel Hankel Legendre Runge Kutta Crank Nicolson Lindblad Born Copenhagen Everett EGKLY Upsilon chi_c0 psi eta_c PubMed arXiv NIST CODATA Sun Earth Moon Mercury Venus Mars Jupiter Saturn lfphys lfviz Shift Ctrl Delete Enter Space".split(" "));
// words of English prose: lower-case Latin words of four letters or more, each once, outside identifiers (u31_light_travel,
// lfphys.core.gravity.orbits) and outside names (capitalised: citations such as «Gralla, Lupsasca & Marrone»), and not a
// mathematical function
const MATH = new Set(["arctg", "arcsin", "arccos", "arctan", "sinc", "sech", "cosh", "sinh", "tanh", "erfc"]);
const latinWords = (s) => [...new Set((s.replace(/[\w.-]*[_.][\w.-]*\w/g, " ").match(/(?<![\p{L}])[a-z][a-z'’-]{3,}/gu) || [])
  .filter((w) => !OK.has(w) && !MATH.has(w)))];
const englishLines = (r) => [...new Set([...r.text.split("\n"), ...r.titles, ...r.options, ...r.ph]
  .filter((s) => s && latinWords(s).length >= 2).map((s) => s.trim().slice(0, 140)))].slice(0, 8);
const cyrSamples = (r) => [r.title, ...r.text.split("\n"), ...r.titles, ...r.options, ...r.ph].filter((s) => s && CYR.test(s)).map((s) => s.slice(0, 120)).slice(0, 8);

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [];
const newPage = async (ctx) => {
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`.slice(0, 300)));
  return page;
};

// a number typed with a decimal comma into a live field is applied as that number, and the field shows it in the
// language's format (review i18n-browser F1, F2: «650,5» became 6505 in a field of type=number)
async function commaTyped(p, v, L) {
  // the review's case (u32's wavelength, 650,5) when the field takes it; else a positive field whose value shows in full
  const fl = v.schema.params.filter((q) => q.live && q.type === "float" && Number.isFinite(q.min) && Number.isFinite(q.max));
  let q = fl.find((x) => /lam/.test(x.id) && x.min <= 650.5 && x.max >= 650.5), whole = 650;
  if (!q) {
    q = fl.find((x) => x.min >= 0 && x.max - x.min > 4 && x.min + 0.37 * (x.max - x.min) < 1e5);
    whole = q ? Math.floor(q.min + 0.37 * (q.max - q.min)) : 0;
  }
  if (!q) { check(`${L} ${v.id}: a live number field to type into`, false); return; }
  const sel = `.ctl[data-pid="${q.id}"] input.num`;
  try {
    await p.waitForSelector(sel, { timeout: 30000 });
    const kind = await p.$eval(sel, (e) => e.type + "/" + e.inputMode);
    await p.fill(sel, `${whole},5`);
    await p.press(sel, "Enter");
    await sleep(2500);
    const got = await p.$eval(sel, (e) => ({ value: e.value, err: e.closest(".ctl").querySelector(".ctl-err")?.textContent || "" }));
    const want = L === "ru" ? `${whole},5` : `${whole}.5`;
    check(`${L} ${v.id}: “${whole},5” typed into “${q.id}” is applied as ${whole}.5`, kind === "text/decimal" && got.value.replace(/\s/g, "") === want && !got.err, { kind, ...got, want });
  } catch (e) { check(`${L} ${v.id}: typing a decimal comma`, false, { error: e.message }); }
}

// 1. the default, the switch on every page, the stored choice and the address's override
{
  const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await newPage(ctx);
  const { id } = await post("/api/runs", { viz: "p99_toy", preset: "two", seed: 1 });
  for (const [name, url] of [["catalogue", "/"], ["run", `/run?id=${id}`], ["settings", "/settings"], ["legal", "/legal"]]) {
    await page.goto(base + url);
    await page.waitForSelector(".topbar .lang-switch", { timeout: 60000 });
    const sw = await page.evaluate(() => ({ text: document.querySelector(".topbar .lang-switch").textContent, on: document.querySelector(".lang-switch a.on")?.dataset.lang, lang: document.documentElement.lang }));
    check(`${name}: the switch EN | RU in the top bar, English by default`, sw.text.replace(/\s/g, "") === "EN|RU" && sw.on === "en" && sw.lang === "en", sw);
  }
  await page.goto(base + "/");
  await page.waitForSelector(".lang-switch a[data-lang=ru]");
  await Promise.all([page.waitForNavigation(), page.click(".lang-switch a[data-lang=ru]")]);
  await page.waitForSelector(".lang-switch a.on[data-lang=ru]", { timeout: 30000 });
  // the start page (2026-11-13): its title in the top bar is a static text of the page
  const stored = await page.evaluate(() => ({ ls: localStorage.getItem("lfviz.lang"), lang: document.documentElement.lang, title: document.querySelector(".topbar a.title")?.textContent }));
  check("the switch stores the language and reloads the page in it", stored.ls === "ru" && stored.lang === "ru" && stored.title === tr("ru", "lfphys · physics computed, not drawn"), stored);
  await page.goto(base + "/settings");
  await page.waitForSelector(".lang-switch a.on");
  check("the stored language holds on the other pages", await page.evaluate(() => document.documentElement.lang) === "ru");
  await page.goto(base + "/?lang=en");
  await page.waitForSelector(".lang-switch a.on");
  check("?lang= overrides the stored language", await page.evaluate(() => document.documentElement.lang + localStorage.getItem("lfviz.lang")) === "enru");
  await post(`/api/runs/${id}/stop`);
  await ctx.close();
}

// 1b. a "?lang=" link's language holds on the next pages (review i18n-code F7, i18n-browser F4), the stored choice is
// not changed, and the switch ends it
{
  const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await newPage(ctx);
  const { id } = await post("/api/runs", { viz: "p99_toy", preset: "two", seed: 1 });
  const langOf = () => page.evaluate(() => ({ lang: document.documentElement.lang, ls: localStorage.getItem("lfviz.lang"), url: location.pathname + location.search }));
  await page.goto(base + "/?lang=ru");
  await page.waitForSelector(".lang-switch a.on");
  await Promise.all([page.waitForNavigation(), page.click('a[href="/settings"], a[href^="/settings?"]')]);
  await page.waitForSelector(".lang-switch a.on");
  const a = await langOf();
  check("?lang=ru → a link to the settings: still Russian, the stored choice untouched", a.lang === "ru" && a.ls === null, a);
  await page.goto(`${base}/run?id=${id}&lang=ru`);
  await page.waitForSelector(".lang-switch a.on");
  const back = await page.$('.topbar a[href="/"], .topbar a[href^="/?"]');
  if (back) {
    await Promise.all([page.waitForNavigation(), back.click()]);
    await page.waitForSelector(".lang-switch a.on");
  }
  const b = await langOf();
  check("a run page in ?lang=ru → its link to the catalogue: still Russian", !!back && b.lang === "ru", b);
  await Promise.all([page.waitForNavigation(), page.click(".lang-switch a[data-lang=en]")]);
  await page.waitForSelector(".lang-switch a.on[data-lang=en]");
  await page.goto(base + "/settings");
  await page.waitForSelector(".lang-switch a.on");
  const c = await langOf();
  check("the switch ends the link's language and stores the choice", c.lang === "en" && c.ls === "en", c);
  await post(`/api/runs/${id}/stop`);
  await ctx.close();
}

// 2. each language: the start page (the demonstrations of an audience and the laboratories: the old catalogue's two
// modes, 2026-11-13), the static pages, a run page of every world
for (const L of LANGS) {
  const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await newPage(ctx);
  const q = `?lang=${L}`;
  const judge = (name, r, extra = {}) => {
    if (L === "en") check(`${L} ${name}: no Cyrillic`, !cyrSamples(r).length && r.lang === "en", { cyrillic: cyrSamples(r), ...extra });
    else {
      check(`${L} ${name}: in the language`, r.lang === L && CYR.test(r.text), { lang: r.lang, ...extra });
      if (!/legal/.test(name)) check(`${L} ${name}: no English prose`, !englishLines(r).length, { english: englishLines(r) });
    }
  };
  for (const mode of ["demo", "playground"]) {
    await page.goto(`${base}/${q}${mode === "playground" ? "#labs" : "#university"}`);
    await page.waitForSelector(".card", { timeout: 60000 });
    await sleep(800);
    const r = await readable(page);
    judge(`catalogue (${mode})`, r);
    if (L !== "en") check(`${L} catalogue (${mode}): the framework's texts translated`, r.text.includes(tr(L, "‹ All audiences")) && r.text.includes(mode === "demo" ? tr(L, "▶ Compute live") : tr(L, "▶ Begin")), { back: tr(L, "‹ All audiences") });
    await page.screenshot({ path: `${SHOTS}/catalogue_${mode}_${L}.png` });
  }
  for (const url of ["/settings", "/legal"]) {
    await page.goto(base + url + q);
    await page.waitForSelector(".lang-switch a.on");
    await sleep(1500);
    judge(url.slice(1), await readable(page));
  }
  for (const viz of WORLDS) {
    const v = vizList.find((x) => x.id === viz);
    if (!v) { check(`${L} ${viz}: in the catalogue`, false); continue; }
    let r = null;
    for (let k = 0; k < 40; k++) {
      r = await post("/api/runs", { viz, seed: 3, params: SMALL[viz] || {}, ...(v.kind === "playground" && v.schema.presets.length ? { preset: v.schema.presets[0].id } : {}) });
      if (r.id || !JSON.stringify(r.error || "").includes("workers are busy")) break;
      await sleep(3000);
    }
    if (!r.id) { check(`${L} ${viz}: run started`, false, { r }); continue; }
    const id = r.id;
    const p = await newPage(ctx);
    try {
      await p.goto(`${base}/run?id=${id}&lang=${L}`);
      await p.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !window.__lfPlayer.replaying(), null, { timeout: 240000 });
      await post(`/api/runs/${id}/command`, { cmd: "play" });
      await sleep(3000);
      await post(`/api/runs/${id}/command`, { cmd: "pause" });
      await sleep(1500);
      const rr = await readable(p);
      judge(`run page ${viz}`, rr);
      if (L !== "en") check(`${L} run page ${viz}: the player's panels translated`, rr.text.toLowerCase().includes(tr(L, "Events").toLowerCase()) && rr.text.toLowerCase().includes(tr(L, "About the run").toLowerCase()), {});
      if (viz === WORLDS[0] || viz === "u32_double_slit") await p.screenshot({ path: `${SHOTS}/run_${viz}_${L}.png`, timeout: 120000 });
      if (viz === "u32_double_slit") await commaTyped(p, v, L);
    } catch (e) { check(`${L} run page ${viz}: opened`, false, { error: e.message }); }
    await p.close();
    await post(`/api/runs/${id}/stop`);
    await fetch(`${base}/api/runs/${id}`, { method: "DELETE" });
  }
  await ctx.close();
}
check("no page errors", !errs.length, { errs: errs.slice(0, 8) });
await br.close();
console.log(failed ? `FAILED: ${failed}` : "all passed");
process.exit(failed ? 1 : 0);
