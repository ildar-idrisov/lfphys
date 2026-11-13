// In Russian, which visible texts of the catalogue and of a run page of each world are still English (Latin words of
// 4+ letters, symbols/formulas/units filtered out)? The repo's i18n_checks.mjs passes a Russian page as soon as it
// shows ANY Cyrillic. Also: does "?lang=ru" survive navigation to another page (no stored choice)?
// node b01_ru_english_leaks.mjs <port> [viz,...]
import { chromium } from "playwright";
const port = process.argv[2] || "8651";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const SMALL = {
  v08_wave_3d: { n: 128, zmax: 10.0 }, v09_thomas_3d: { ngrid: 48 },
  v11_double_slit_2d: { a: 1.5, d: 4.0, w: 1.0, L: 12.0, sigma_x: 3.0, sigma_z: 2.0, grid: "coarse", n_bohm: 100, n_tracks: 10 },
  v12_arrival_times_2d: { grid: "coarse", n_bohm: 100, n_tracks: 10, L: 12.0, sigma_z: 2.0, sigma_x: 2.0 },
  v15_kerr_shadow: { res: "s" }, v17_mie_scattering: { radius_um: 1.0, width: 0.05, n_lam: 8 },
};
// Latin words that are not English prose: symbols, units, proper names, code-ish tokens
const OK = new Set("Bohm Kerr Mie Newton Einstein Schwarzschild Lorentz Thomas Bell CHSH Young Planck Debye Airy Fresnel Brewster Fabry Perot Kretschmann Cornell PDG EHT GeV MeV keV TeV GPU CPU CSV JSON Lennard Jones Maxwell Boltzmann Reynolds Mach Kármán Gauss Bonnet Faraday Landau Rydberg Bohr Sgr M87 FLRW Hubble ΛCDM Coulomb Verlet Langevin Berendsen Andersen Nosé Hoover Poiseuille Couette Stokes Navier LBM BGK TRT MRT Ladd Zou PML FDTD TFSF Yee Courant Tsirelson GHZ Peters Mathews Johannsen Penrose Doppler Terrell Wigner Hamilton Heisenberg Schrödinger Dirac Pauli Feynman Kirchhoff Huygens Snell Rayleigh Lorenz Laguerre Hermite Bessel Hankel Legendre Runge Kutta Crank Nicolson Lindblad Born Copenhagen Everett EGKLY Upsilon chi_c0 psi eta_c PubMed arXiv NIST CODATA Sun Earth Moon Mercury Venus Mars Jupiter Saturn lfphys lfviz".split(" "));
const latinWords = (s) => (s.match(/[A-Za-z][A-Za-z'’-]{3,}/g) || []).filter((w) => !OK.has(w) && !/^[A-Z]{2,}\d*$/.test(w));
const readable = (page) => page.evaluate(() => {
  const own = new Set([...document.querySelectorAll(".lang-switch, .lang-switch *")]);
  const vis = (e) => e.offsetParent !== null;
  return {
    text: document.body.innerText.split("\n"),
    titles: [...document.querySelectorAll("[title]")].filter((e) => !own.has(e) && vis(e)).map((e) => e.getAttribute("title")),
    options: [...document.querySelectorAll("select")].filter(vis).flatMap((s) => [...s.options].map((o) => o.textContent)),
    lang: document.documentElement.lang,
  };
});
const leaks = (r) => [...new Set([...r.text, ...r.titles, ...r.options].filter((s) => s && latinWords(s).length >= 2).map((s) => s.trim().slice(0, 140)))];
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
// 1. ?lang=ru on one page, then a plain link (no stored choice)
{
  const ctx = await br.newContext();
  const page = await ctx.newPage();
  await page.goto(base + "/?lang=ru");
  await page.waitForSelector(".lang-switch a.on");
  const a = await page.evaluate(() => document.documentElement.lang);
  await page.goto(base + "/settings");
  await page.waitForSelector(".lang-switch a.on");
  const b = await page.evaluate(() => document.documentElement.lang);
  console.log(JSON.stringify({ check: "?lang=ru then another page without ?lang", first: a, next: b }));
  await ctx.close();
}
// 2. Russian pages: English leftovers
const vizList = await get("/api/viz");
const WORLDS = (process.argv[3] || vizList.map((v) => v.id).join(",")).split(",").filter(Boolean);
const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
await ctx.addInitScript(() => { try { localStorage.setItem("lfviz.lang", "ru"); } catch (e) {} });
const page = await ctx.newPage();
const errs = [];
page.on("pageerror", (e) => errs.push(String(e.message).slice(0, 200)));
for (const mode of ["demo", "playground"]) {
  await page.goto(`${base}/${mode === "playground" ? "#playground" : ""}`);
  await page.evaluate((m) => localStorage.setItem("lfviz.mode", m), mode);
  await page.reload();
  await page.waitForSelector(".card", { timeout: 60000 });
  await sleep(800);
  const r = await readable(page);
  console.log(JSON.stringify({ page: `catalogue ${mode}`, lang: r.lang, english: leaks(r) }));
}
for (const viz of WORLDS) {
  const { id } = await post("/api/runs", { viz, params: SMALL[viz] || {}, seed: 1 });
  if (!id) { console.log(JSON.stringify({ viz, error: "not started" })); continue; }
  await page.goto(`${base}/run?id=${id}`);
  try { await page.waitForFunction(() => document.querySelector("#title") && document.querySelector("#title").textContent.trim().length > 0, null, { timeout: 90000 }); } catch (e) {}
  await sleep(6000);
  const r = await readable(page);
  console.log(JSON.stringify({ page: viz, lang: r.lang, english: leaks(r) }));
  await post(`/api/runs/${id}/stop`);
}
console.log(JSON.stringify({ pageerrors: errs.slice(0, 10) }));
await br.close();
