// review P, e5: the start page and the recording mode on the static site under /lfphys/
import { chromium } from "playwright";
const root = process.argv[2] || "http://127.0.0.1:8682";
const base = root + "/lfphys/";
const L = (k, v) => console.log(JSON.stringify({ k, v }));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const watch = (page, bag) => {
  page.on("pageerror", (e) => bag.errs.push(e.message.slice(0, 200)));
  page.on("console", (m) => { if (m.type() === "error") bag.errs.push("console: " + m.text().slice(0, 200)); });
  page.on("request", (r) => { const u = r.url(); if (!u.startsWith(base) && !u.startsWith("data:") && !u.startsWith("blob:")) bag.out.push(u); });
  page.on("response", (r) => { if (r.status() >= 400) bag.bad.push(`${r.status()} ${r.url()}`); });
};
for (const lang of ["en", "ru"]) {
  for (const w of [1280, 390]) {
    const ctx = await br.newContext({ viewport: { width: w, height: 900 } });
    for (const hash of ["", "school", "university", "research", "labs"]) {
      const page = await ctx.newPage();
      const bag = { errs: [], out: [], bad: [] };
      watch(page, bag);
      await page.goto(`${base}?lang=${lang}` + (hash ? `#${hash}` : ""));
      await page.waitForSelector(hash ? ".st-head" : ".st-tiles", { timeout: 60000 });
      await sleep(1500);
      const o = await page.evaluate(() => ({ sw: document.scrollingElement.scrollWidth, w: innerWidth, title: document.title,
        links: [...document.querySelectorAll("a[href]")].map((a) => a.getAttribute("href")).filter((h) => !h.startsWith("#") && !h.startsWith("http")).slice(0, 40),
        topbar: document.querySelector(".topbar").innerText.replace(/\n/g, " | "),
        buttons: [...document.querySelectorAll(".st-card button, .st-card a.button")].map((b) => b.textContent).slice(0, 6),
        offCards: document.querySelectorAll(".card.off").length,
        noRec: [...document.querySelectorAll(".st-card")].filter((c) => !c.querySelector("a.button")).map((c) => c.id) }));
      L(`site ${lang} ${w} ${hash || "home"}`, { ...o, ...bag });
      await page.screenshot({ path: `/shots/e5_site_${hash || "home"}_${lang}_${w}.png`, fullPage: true });
      await page.close();
    }
    await ctx.close();
  }
}
// click a recording from the university page; the back link; the old link; help on the site
const ctx = await br.newContext({ viewport: { width: 1280, height: 860 } });
{
  const page = await ctx.newPage();
  const bag = { errs: [], out: [], bad: [] };
  watch(page, bag);
  await page.goto(`${base}?lang=ru#university`);
  await page.waitForSelector(".st-card");
  await Promise.all([page.waitForURL(/run\.html\?rec=/), page.click("#card-u34_orbits a.button")]);
  await page.waitForFunction(() => window.__lfPlayer && !window.__lfPlayer.replaying() && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
  await sleep(2500);
  const s = await page.evaluate(() => ({ url: location.href, title: document.title, badge: document.getElementById("recbadge")?.textContent,
    back: document.querySelector('.topbar a[data-page=""]')?.getAttribute("href"), legal: document.querySelector('.topbar a[data-page="legal"]')?.getAttribute("href"),
    gear: !!document.querySelector('.topbar a[data-page="settings"]'), live: !!document.querySelector(".rec-note button"), note: document.querySelector(".rec-note")?.innerText,
    dl: [...document.querySelectorAll("a[download]")].map((a) => a.getAttribute("href")) }));
  L("site rec from card", { ...s, ...bag });
  await page.screenshot({ path: `/shots/e5_site_rec_u34_ru.png` });
  await page.click('.topbar a[data-page=""]');
  await sleep(2000);
  L("site back link", await page.evaluate(() => ({ url: location.href, focus: document.querySelector(".card.focus")?.id, lang: document.documentElement.lang })));
  await page.goto(`${base}run.html?rec=u34_orbits/mercury&lang=en`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 120000 });
  await page.keyboard.press("?");
  await sleep(500);
  L("site help on recording", (await page.evaluate(() => document.body.innerText)).slice(-1800));
  await page.close();
}
for (const q of ["run.html?rec=v04_orbits/mercury", "run.html?rec=v02_double_slit/young", "run.html?rec=u32_double_slit/nope", "run.html?id=20261111-170830-v04-2ca9", "run?rec=u34_orbits/mercury", "run.html"]) {
  const page = await ctx.newPage();
  const bag = { errs: [], out: [], bad: [] };
  watch(page, bag);
  await page.goto(base + q + (q.includes("?") ? "&" : "?") + "lang=en");
  await sleep(7000);
  L("site link " + q, { frames: await page.evaluate(() => window.__lfPlayer?.frames()), body: (await page.evaluate(() => document.body.innerText)).slice(0, 300), ...bag });
  await page.screenshot({ path: `/shots/e5_site_link_${q.replace(/[^\w]+/g, "_")}.png` });
  await page.close();
}
await br.close();
