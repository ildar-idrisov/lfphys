// R-P probe: the built site under /lfphys/, used by hand (390 and 1280 px, the language of LFVIZ_LANG): every request
// stays under the sub-path; the start page's screen buttons; Explore/Lab/Watch used; the worksheet and the help.
import { chromium } from "playwright";
const ROOT = process.argv[2] || "http://127.0.0.1:8702/lfphys/";
const LANG = process.env.LFVIZ_LANG || "en";
const SH = process.env.SHOTS || "/pw/shots_site";
const PREFIX = new URL(ROOT).pathname, ORIGIN = new URL(ROOT).origin;
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const settle = (page, ms = 300) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
for (const [W, H] of [[390, 844], [1280, 800]]) {
  const ctx = await br.newContext({ viewport: { width: W, height: H } });
  const outside = [], bad = [], errs = [], all = new Set();
  ctx.on("request", (r) => { const u = new URL(r.url()); if (u.protocol.startsWith("http")) { all.add(u.pathname.replace(/p\d+\.[0-9a-f]+\.lfpt\.gz$/, "p*.lfpt.gz")); if (u.origin !== ORIGIN || !u.pathname.startsWith(PREFIX)) outside.push(r.url()); } });
  ctx.on("response", (r) => { if (r.status() >= 400) bad.push(`${r.status()} ${r.url()}`); });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 160)));
  page.on("popup", (p) => p.on("pageerror", (e) => errs.push("popup: " + e.message.slice(0, 160))));
  // the start page: the school card's buttons
  await page.goto(`${ROOT}?lang=${LANG}#school/s03_projectile`);
  await page.waitForSelector("#card-s03_projectile a.st-screen", { timeout: 30000 });
  const btns = await page.$$eval("#card-s03_projectile a.st-screen, #card-s03_projectile button", (a) => a.map((b) => ({ t: b.textContent, href: b.getAttribute("href"), off: b.classList.contains("disabled") })));
  out(`${W} start: s03 card's buttons`, { btns });
  for (const sc of ["watch", "explore", "lab"]) {
    await page.goto(`${ROOT}?lang=${LANG}#school/s03_projectile`);
    await page.waitForSelector(`#card-s03_projectile a.st-screen[data-screen="${sc}"]`);
    await Promise.all([page.waitForURL(/run\.html\?demo=/), page.click(`#card-s03_projectile a.st-screen[data-screen="${sc}"]`)]);
    const ok = await page.waitForSelector(`.dm-tab[data-screen="${sc}"][aria-selected="true"]`, { timeout: 30000 }).then(() => true, () => false);
    out(`${W} start → ${sc}`, { ok, url: page.url().replace(ORIGIN, "") });
  }
  // Explore: pick, launch, overlays, drawer
  await page.goto(`${ROOT}run.html?demo=s03_projectile&screen=explore&lang=${LANG}`);
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 30000 });
  out(`${W} site explore: no «Compute live», no «Another sample»`, { live: await page.locator(".dm-live").count(), sliders: await page.evaluate(() => [...document.querySelectorAll(".dm-slider")].map((s) => `${s.min}..${s.max}/${s.step}`)) });
  for (const k of [2, 5, 8]) { await page.locator('.dm-ctl[data-param="angle_deg"] .dm-detent').nth(k).click(); await sleep(300); await page.locator(".dm-play").click(); await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 30000 }); }
  await page.locator('.dm-ctl[data-param="air"] button[data-value="true"]').click(); await sleep(500);
  await page.locator(".dm-play").click(); await page.waitForFunction(() => !window.__lfExplore.explore.state.playing, null, { timeout: 30000 });
  if (W < 1000) { await page.locator(".dm-menu > summary").click(); await page.locator(".dm-menu-box button").first().click(); } else await page.locator(".dm-how").click();
  await settle(page);
  await page.screenshot({ path: `${SH}/rp_site_explore_drawer_${LANG}_${W}.png` });
  const dr = await page.locator(".dm-drawer-body").innerText();
  out(`${W} site explore drawer`, { head: dr.split("\n").filter(Boolean).slice(0, 6), passport: dr.split("\n").filter(Boolean).slice(-14) });
  await page.keyboard.press("Escape");
  // help
  await page.keyboard.press("?"); await settle(page);
  const help = await page.evaluate(() => [...document.querySelectorAll(".modal a, dialog a, .modal-box a")].map((a) => a.href));
  out(`${W} help's links`, { help });
  await page.keyboard.press("Escape");
  // Lab: three parts, measure in each
  await page.locator('.dm-tab[data-screen="lab"]').click();
  await page.waitForFunction(() => window.__lfLab && window.__lfLab.step() && window.__lfLab.step().cur, null, { timeout: 30000 });
  for (const k of [0, 1, 2]) {
    await page.locator(".dm-steps button").nth(k).click();
    await page.waitForFunction((k) => window.__lfLab.state.k === k && window.__lfLab.step() && window.__lfLab.step().cur, k, { timeout: 30000 });
    await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-timeline"); s.value = s.max; s.dispatchEvent(new Event("input")); });
    await settle(page, 100);
    await page.locator(".dm-measure").click(); await settle(page, 100);
    out(`${W} lab part ${k + 1}: measured`, { msg: await page.locator(".dm-msg").innerText(), row: await page.locator(".dm-table tbody tr").last().innerText().catch(() => "") });
    await page.screenshot({ path: `${SH}/rp_site_lab${k + 1}_${LANG}_${W}.png`, fullPage: true });
  }
  // the worksheet link (opens a new tab)
  const [ws] = await Promise.all([ctx.waitForEvent("page"), page.locator(".dm-ws a").click()]);
  await ws.waitForFunction(() => document.body.dataset.ready === "1", null, { timeout: 30000 });
  out(`${W} worksheet from the lab card`, { url: ws.url().replace(ORIGIN, "") });
  await ws.close();
  // Watch: play a moment, a chapter, the «More recordings» select (u32)
  await page.goto(`${ROOT}run.html?demo=u32_double_slit&screen=watch&lang=${LANG}`);
  await page.waitForFunction(() => window.__lfWatch && window.__lfWatch.state.story, null, { timeout: 60000 });
  await page.locator(".dm-tick").nth(3).click({ force: true }); await settle(page);
  const sel = page.locator("select.dm-more");
  const opts = await sel.locator("option").allInnerTexts();
  await sel.selectOption({ index: 1 });
  await page.waitForFunction(() => window.__lfWatch.state.rec && window.__lfWatch.state.rec.id !== "story" && window.__lfWatch.state.story, null, { timeout: 60000 });
  out(`${W} u32 watch: More recordings`, { opts, now: await page.evaluate(() => window.__lfWatch.state.rec.id), caption: await page.evaluate(() => window.__lfWatch.caption()).then((s) => s.slice(0, 60)) });
  await page.screenshot({ path: `${SH}/rp_site_u32_watch_${LANG}_${W}.png` });
  // u32 explore: a control changed, the drawer (standard: the table)
  await page.locator('.dm-tab[data-screen="explore"]').click();
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 60000 });
  await page.locator('.dm-ctl[data-param="lam_nm"] .dm-detent').nth(0).click(); await sleep(1500);
  if (W < 1000) { await page.locator(".dm-menu > summary").click(); await page.locator(".dm-menu-box button").first().click(); } else await page.locator(".dm-how").click();
  await settle(page);
  const dr2 = await page.locator(".dm-drawer-body").innerText();
  out(`${W} u32 explore drawer`, { lines: dr2.split("\n").filter(Boolean).slice(0, 12), folds: await page.$$eval(".dm-drawer-body summary", (a) => a.map((s) => s.textContent)) });
  await page.screenshot({ path: `${SH}/rp_site_u32_drawer_${LANG}_${W}.png` });
  await page.keyboard.press("Escape");
  // back to the start page
  await page.locator(".dm-back").click(); await page.waitForURL(/lfphys\/(index\.html)?(\?|#|$)/, { timeout: 30000 });
  out(`${W} back link`, { url: page.url().replace(ORIGIN, "") });
  await sleep(500);
  out(`${W} requests`, { outside, bad: bad.filter((b) => !b.endsWith("/favicon.ico")), errs, n: all.size, paths: [...all].filter((p) => !p.includes("/static/") && !p.includes("/viz/")).slice(0, 60) });
  await ctx.close();
}
await br.close();
