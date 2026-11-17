// R-P probe: keyboard and accessibility on the screens (server on the given port)
import { chromium } from "playwright";
const port = process.argv[2] || "8702", base = `http://127.0.0.1:${port}`;
const LANG = process.env.LFVIZ_LANG || "en";
const out = (k, v) => console.log(JSON.stringify({ k, ...v }));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const settle = (page, ms = 300) => page.evaluate((m) => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, m)))), ms);
for (const [W, H] of [[1280, 800], [390, 844]]) {
  const ctx = await br.newContext({ viewport: { width: W, height: H } });
  const page = await ctx.newPage();
  await page.goto(`${base}/run?demo=s03_projectile&screen=explore&lang=${LANG}`);
  await page.waitForFunction(() => window.__lfExplore && window.__lfExplore.explore && window.__lfExplore.explore.point(), null, { timeout: 30000 });
  await settle(page);
  const X = "window.__lfExplore.explore";
  // 1. arrows on a focused control slider
  const sl = page.locator('.dm-screen:not([hidden]) .dm-ctl[data-param="angle_deg"] .dm-slider');
  await sl.focus();
  const before = await page.evaluate(`({ v: ${X}.values().angle_deg, input: document.activeElement.value, clock: ${X}.state.clock, launched: ${X}.state.cur.launchedAt })`);
  await page.keyboard.press("ArrowRight"); await settle(page, 600);
  await page.keyboard.press("ArrowRight"); await settle(page, 600);
  const after = await page.evaluate(`({ v: ${X}.values().angle_deg, input: document.activeElement.value, clock: ${X}.state.clock, launched: ${X}.state.cur.launchedAt, active: document.activeElement.className })`);
  out(`${W} arrow keys on the focused angle slider`, { before, after });
  // 2. Space on a focused toggle button (air: off/on)
  const airOn = page.locator('.dm-screen:not([hidden]) .dm-ctl[data-param="air"] button[data-value="true"]');
  await airOn.focus();
  const a0 = await page.evaluate(`({ air: ${X}.values().air, playing: ${X}.state.playing, launched: ${X}.state.cur.launchedAt })`);
  await page.keyboard.press("Space"); await settle(page, 600);
  const a1 = await page.evaluate(`({ air: ${X}.values().air, playing: ${X}.state.playing, launched: ${X}.state.cur.launchedAt })`);
  await page.keyboard.press("Enter"); await settle(page, 800);
  const a2 = await page.evaluate(`({ air: ${X}.values().air })`);
  out(`${W} Space then Enter on the focused «on» button of Air`, { before: a0, afterSpace: a1, afterEnter: a2 });
  // 3. the tab order and the focus ring of the first 30 stops
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  await page.locator("body").click({ position: { x: 2, y: 2 } }).catch(() => {});
  const stops = [];
  for (let i = 0; i < 34; i++) {
    await page.keyboard.press("Tab");
    stops.push(await page.evaluate(() => { const e = document.activeElement; if (!e) return null; const cs = getComputedStyle(e);
      const r = e.getBoundingClientRect();
      return `${e.tagName.toLowerCase()}${e.className ? "." + String(e.className).split(" ")[0] : ""}[${(e.getAttribute("aria-label") || e.textContent || e.title || "").trim().slice(0, 18)}] ring:${cs.outlineStyle !== "none" && cs.outlineWidth !== "0px" ? "y" : (cs.boxShadow !== "none" ? "shadow" : "N")} vis:${r.width > 0 && r.bottom > 0 && r.top < innerHeight ? "y" : "N"}`; }));
  }
  out(`${W} tab stops`, { stops });
  // 4. buttons' accessible names: icon-only text
  const names = await page.evaluate(() => [...document.querySelectorAll("#demo button, #demo summary, #demo a, #demo input")].filter((e) => e.offsetParent !== null).map((e) => ({
    tag: e.tagName.toLowerCase(), cls: String(e.className).split(" ")[0], text: (e.textContent || "").trim().slice(0, 14), aria: e.getAttribute("aria-label"), title: (e.title || "").slice(0, 30) }))
    .filter((x) => !x.aria && (/^[\s▶⟲◀▷✕◐?☰❚✎◎⤓]+$/u.test(x.text) || (x.tag === "input" && x.cls !== "dm-slider" && !x.text))));
  out(`${W} controls named only by a symbol (no aria-label)`, { n: names.length, names });
  // 5. touch targets (design §3.9: ≥ 44 × 44 px)
  const small = await page.evaluate(() => [...document.querySelectorAll(".dm-screen:not([hidden]) button, .dm-screen:not([hidden]) input, .dm-top button, .dm-top summary, .dm-top a")]
    .filter((e) => e.offsetParent !== null).map((e) => { const r = e.getBoundingClientRect(); return { c: String(e.className).split(" ")[0] || e.tagName.toLowerCase(), t: (e.textContent || e.type || "").trim().slice(0, 8), w: Math.round(r.width), h: Math.round(r.height) }; })
    .filter((x) => x.w < 44 || x.h < 44));
  const thumb = await page.evaluate(() => { const s = document.querySelector(".dm-screen:not([hidden]) .dm-slider"); return s ? getComputedStyle(s).height : null; });
  out(`${W} targets under 44 px`, { n: small.length, sample: small.slice(0, 30), sliderHeight: thumb });
  // 6. the tab list's semantics
  const tabs = await page.evaluate(() => [...document.querySelectorAll(".dm-tab")].map((b) => ({ role: b.getAttribute("role"), sel: b.getAttribute("aria-selected"), controls: b.getAttribute("aria-controls"), tabindex: b.tabIndex })));
  const panels = await page.evaluate(() => [...document.querySelectorAll(".dm-screen")].map((s) => s.getAttribute("role")));
  out(`${W} tabs`, { tabs, panels, lang: await page.evaluate(() => document.documentElement.lang) });
  // 7. keyboard on the tab list: Right arrow from the focused tab
  await page.locator('.dm-tab[data-screen="watch"]').focus();
  await page.keyboard.press("Enter"); await settle(page, 800);
  out(`${W} Enter on the Watch tab`, { screen: new URL(page.url()).searchParams.get("screen") });
  await page.locator('.dm-tab[data-screen="explore"]').focus();
  await page.keyboard.press("Space"); await settle(page, 800);
  out(`${W} Space on the Explore tab`, { screen: new URL(page.url()).searchParams.get("screen") });
  await ctx.close();
}
await br.close();
