// w03: the pages' titles in each language; whether ?lang= follows the links (catalogue → run, run → settings);
// the run page at 1280 px in Russian (an old record and a fresh run of v02 and p03), with every panel open
import { browser, newPage, post, get, del, sleep, startRun, waitPlayer, shot, scan, setLog, log, base, openPanel } from "./r_lib.mjs";
setLog("w03_misc");
const br = await browser();
const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
const page = await newPage(ctx, "misc");
const old = (await get("/api/runs")).find((r) => r.id.includes("-v02-"));
for (const L of ["en", "ru"]) {
  for (const u of ["/", "/settings", "/legal", `/run?id=${old.id}`]) {
    await page.goto(`${base}${u}${u.includes("?") ? "&" : "?"}lang=${L}`);
    await page.waitForSelector(".lang-switch a.on"); await sleep(2500);
    log({ L, u, title: await page.title() });
  }
}
// ?lang=ru with English stored: the catalogue's link to a run, the run's ⚙ link
await page.evaluate(() => localStorage.setItem("lfviz.lang", "en"));
await page.goto(`${base}/?lang=ru`); await page.waitForSelector("#runs a", { timeout: 60000 });
const href = await page.evaluate((id) => document.querySelector(`#runs a[href*='${id}']`)?.getAttribute("href"), old.id);
await page.click(`#runs a[href*='${old.id}']`);
await page.waitForSelector(".lang-switch a.on");
log({ check: "catalogue ?lang=ru → run link", href, url: page.url(), lang: await page.evaluate(() => document.documentElement.lang) });
await shot(page, "w03_lang_lost_on_run_link");
await page.goto(`${base}/run?id=${old.id}&lang=ru`); await page.waitForSelector(".lang-switch a.on");
const back = await page.evaluate(() => document.querySelector(".topbar a[href='/']") ? "/" : null);
await page.click(".topbar a[href='/']"); await page.waitForSelector(".card", { timeout: 60000 });
log({ check: "run ?lang=ru → ← Catalogue", back, url: page.url(), lang: await page.evaluate(() => document.documentElement.lang) });
await page.evaluate(() => localStorage.removeItem("lfviz.lang"));
await ctx.close();

// 1280 px, Russian
const c2 = await br.newContext({ viewport: { width: 1280, height: 800 } });
for (const viz of ["v02_double_slit", "p03_molecules", "v07_bell_test", "p04_fluids"]) {
  const v = (await get("/api/viz")).find((x) => x.id === viz);
  const r = await startRun({ viz, seed: 3, ...(v.schema.presets.length ? { preset: v.schema.presets[0].id } : {}) });
  for (const L of ["ru", "en"]) {
    const p = await newPage(c2, `${viz}_1280_${L}`);
    await p.goto(`${base}/run?id=${r.id}&lang=${L}`);
    await waitPlayer(p);
    await p.click("#rec"); await sleep(4000); await p.click("#rec"); await sleep(1500);
    await scan(p, L, `${viz} 1280 ${L}`);
    await shot(p, `w03_${viz}_1280_${L}`);
    await openPanel(p, /./);
    await p.evaluate(() => { for (const d of document.querySelectorAll("#right details, #left details")) d.open = true; });
    await sleep(800);
    await scan(p, L, `${viz} 1280 ${L} panels`);
    let k = 0;
    for (const pn of await p.$$("#left .panel, #right .panel")) { try { await pn.screenshot({ path: `/shots/w03_${viz}_1280_${L}_p${String(k).padStart(2, "0")}.png` }); } catch (e) { /* hidden */ } k++; }
    await p.close();
  }
  await post(`/api/runs/${r.id}/stop`); await sleep(1500); await del(`/api/runs/${r.id}`);
}
await c2.close();
await br.close();
