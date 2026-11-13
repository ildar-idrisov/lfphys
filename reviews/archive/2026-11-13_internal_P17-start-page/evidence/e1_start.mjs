// review P, e1: the start page on the server: screenshots EN/RU 1280/390, keyboard focus, contrast, titles, continue strip
import { chromium } from "playwright";
import { writeFileSync } from "node:fs";
const base = process.argv[2] || "http://127.0.0.1:8682";
const OUT = "/shots";
const log = [];
const L = (k, v) => { log.push({ k, v }); console.log(JSON.stringify({ k, v })); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch();

for (const lang of ["en", "ru"]) {
  for (const w of [1280, 390]) {
    const ctx = await br.newContext({ viewport: { width: w, height: 900 } });
    for (const hash of ["", "school", "university", "research", "labs"]) {
      const page = await ctx.newPage();
      const errs = [];
      page.on("pageerror", (e) => errs.push(e.message));
      page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") errs.push("console: " + m.text().slice(0, 200)); });
      await page.goto(`${base}/?lang=${lang}` + (hash ? `#${hash}` : ""));
      await page.waitForSelector(hash ? ".st-head" : ".st-tiles", { timeout: 60000 });
      await sleep(3800);
      const o = await page.evaluate(() => ({ sw: document.scrollingElement.scrollWidth, w: innerWidth, title: document.title,
        h: document.scrollingElement.scrollHeight,
        wide: [...document.querySelectorAll("body *")].filter((e) => e.getBoundingClientRect().right > innerWidth + 1).slice(0, 5).map((e) => e.tagName + "." + e.className) }));
      L(`${lang} ${w} ${hash || "home"}`, { ...o, errs });
      await page.screenshot({ path: `${OUT}/e1_${hash || "home"}_${lang}_${w}.png`, fullPage: true });
      await page.close();
    }
    await ctx.close();
  }
}

// keyboard: tab through the home, record focused elements and whether a focus indicator is visible
{
  const ctx = await br.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(`${base}/?lang=en`);
  await page.waitForSelector(".st-tiles");
  await sleep(500);
  const seq = [];
  for (let i = 0; i < 16; i++) {
    await page.keyboard.press("Tab");
    seq.push(await page.evaluate(() => {
      const e = document.activeElement; const cs = getComputedStyle(e);
      return { tag: e.tagName, id: e.id, cls: e.className, text: (e.textContent || "").trim().slice(0, 30), outline: cs.outlineStyle + " " + cs.outlineWidth + " " + cs.outlineColor,
        border: cs.borderLeftWidth + " " + cs.borderLeftColor + " / top " + cs.borderTopColor };
    }));
  }
  L("tab order home", seq);
  // focus on the university tile: screenshot
  await page.focus("#tile-university");
  await page.keyboard.press("Shift+Tab"); await page.keyboard.press("Tab");
  await page.locator(".st-tiles").screenshot({ path: `${OUT}/e1_focus_tile_en.png` });
  // the audience page: chips
  await page.goto(`${base}/?lang=en#university`);
  await page.waitForSelector(".st-chips");
  await sleep(400);
  const seq2 = [];
  for (let i = 0; i < 10; i++) {
    await page.keyboard.press("Tab");
    seq2.push(await page.evaluate(() => { const e = document.activeElement; const cs = getComputedStyle(e);
      return { tag: e.tagName, text: (e.textContent || "").trim().slice(0, 30), pressed: e.getAttribute("aria-pressed"), outline: cs.outlineStyle + " " + cs.outlineWidth }; }));
  }
  L("tab order university", seq2);
  await page.locator(".st-filters").screenshot({ path: `${OUT}/e1_focus_chip_en.png` });
  // the disabled recording link: focusable? role?
  const dis = await page.$$eval("a.button.disabled", (a) => a.map((e) => ({ text: e.textContent, tabindex: e.tabIndex, href: e.getAttribute("href"), aria: e.getAttribute("aria-disabled"), role: e.getAttribute("role") })));
  L("disabled rec buttons", dis);
  const recbtn = await page.$$eval(".st-card a.button:not(.disabled)", (a) => a.slice(0, 3).map((e) => ({ text: e.textContent, tabindex: e.tabIndex, role: e.getAttribute("role") })));
  L("rec buttons", recbtn);
  // search: does typing scroll the page? focus kept?
  await page.evaluate(() => window.scrollTo(0, 600));
  await page.fill(".st-search", "");
  await page.type(".st-search", "slit", { delay: 50 });
  await sleep(300);
  L("search keeps focus/scroll", await page.evaluate(() => ({ focus: document.activeElement.className, val: document.activeElement.value, y: scrollY, cards: document.querySelectorAll(".st-card").length })));
  await ctx.close();
}

// contrast of the greyed lab tile and cards (static-like look cannot be produced on the server: compute from the tile CSS)
{
  const ctx = await br.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(`${base}/?lang=en`);
  await page.waitForSelector(".st-tiles");
  const c = await page.evaluate(() => {
    const parse = (s) => s.match(/[\d.]+/g).map(Number);
    const lum = ([r, g, b]) => { const f = (x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const ratio = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
    const cs = getComputedStyle(document.documentElement);
    const v = (n) => { const d = document.createElement("div"); d.style.color = `var(${n})`; document.body.append(d); const r = parse(getComputedStyle(d).color); d.remove(); return r; };
    const muted = v("--muted"), panel = v("--panel"), bg = v("--bg"), ink = v("--ink"), accent = v("--accent");
    const mix = (a, b, k) => a.map((x, i) => x * k + b[i] * (1 - k));
    const gray = (c) => { const y = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; return [y, y, y]; };
    // the greyed tile: grayscale(1) then opacity .72 over the page background
    const offText = mix(gray(muted), bg, 0.72), offPanel = mix(gray(panel), bg, 0.72), offInk = mix(gray(ink), bg, 0.72);
    const aud = (n) => v(n);
    const out = { muted_on_panel: ratio(muted, panel), muted_on_bg: ratio(muted, bg), off_muted: ratio(offText, offPanel), off_ink: ratio(offInk, offPanel) };
    for (const a of ["--aud-school", "--aud-university", "--aud-research", "--aud-labs"]) {
      const d = document.createElement("div"); d.className = "start"; d.style.color = `var(${a})`; document.body.append(d); const col = parse(getComputedStyle(d).color); d.remove();
      out[a + "_on_panel"] = ratio(col, panel);
    }
    out.white_on_accent = ratio([255, 255, 255], accent);
    out.disabled_btn = ratio(mix(ink, panel, 0.45), panel);
    return out;
  });
  L("contrast light", c);
  await ctx.close();
}
writeFileSync(`${OUT}/e1_log.json`, JSON.stringify(log, null, 1));
await br.close();
