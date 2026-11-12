// G1 response check (U4, U7, U12, U18 in the browser): palette adds through the pre-placement form, the toasts, the live
// law, a disabled palette button with its reason.
import { base, browser, newRun, sleep, post, openRun, toasts } from "./common.mjs";
import fs from "fs";
const b = await browser();
const out = {};
async function clickPalette(page, re) {
  const bs = await page.$$("button");
  for (const x of bs) if (re.test(await x.textContent()) && /＋/.test(await x.textContent())) { await x.click(); return true; }
  return false;
}
async function placeNow(page) {
  await sleep(500);
  return page.evaluate(() => {
    const g = [...document.querySelectorAll("button")].find((x) => /Поставить/.test(x.textContent) && !x.disabled);
    if (g) { g.click(); return true; }
    return false;
  });
}
{ // p01 inner: a star and a hole from the palette, then the collisions law changed live
  const id = await newRun("p01_gravity", { preset: "inner" });
  const { page, ctx, logs } = await openRun(b, id);
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  await sleep(2000);
  const r = {};
  r.star_click = await clickPalette(page, /Звезда/);
  r.star_place = await placeNow(page);
  await sleep(2500);
  r.toasts1 = await toasts(page);
  await page.screenshot({ path: "/pw/shots/after_p01_palette_star.jpg", type: "jpeg", quality: 70 });
  r.hole_click = await clickPalette(page, /Чёрная дыра/);
  r.hole_place = await placeNow(page);
  await sleep(2500);
  r.toasts2 = await toasts(page);
  r.live = await page.evaluate(() => {
    const sels = [...document.querySelectorAll("select")];
    const sel = sels.find((s) => [...s.options].some((o) => /проходят друг сквозь друга/.test(o.textContent)));
    if (!sel) return "no control";
    sel.value = "pass";
    sel.dispatchEvent(new Event("input", { bubbles: true }));
    sel.dispatchEvent(new Event("change", { bubbles: true }));
    return sel.value;
  });
  await sleep(2500);
  r.events = await page.$$eval(".events .ev", (ts) => ts.map((t) => t.textContent.slice(0, 220)).slice(-8));
  await page.screenshot({ path: "/pw/shots/after_p01_live_collisions.jpg", type: "jpeg", quality: 70 });
  r.logs = logs.slice(0, 5);
  out.p01 = r;
  await ctx.close(); await post(`/api/runs/${id}/stop`, {});
}
{ // p02 double slit: a particle from the palette lands upstream of the wall
  const id = await newRun("p02_quantum", { preset: "double_slit" });
  const { page, ctx, logs } = await openRun(b, id);
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  await sleep(2000);
  const r = {};
  const t0 = Date.now();
  r.click = await clickPalette(page, /Частица/);
  r.place = await placeNow(page);
  try {
    await page.waitForFunction(() => /Частица \(волновой пакет\) 2/.test(document.body.innerText), null, { timeout: 60000 });
    r.listed_s = (Date.now() - t0) / 1000;
  } catch (e) { r.listed_s = null; }
  await sleep(1500);
  r.toasts = await toasts(page);
  await page.screenshot({ path: "/pw/shots/after_p02_palette_packet.jpg", type: "jpeg", quality: 70 });
  r.logs = logs.slice(0, 5);
  out.p02_slit = r;
  await ctx.close(); await post(`/api/runs/${id}/stop`, {});
}
{ // p02 cyclotron: the field button disabled with its reason
  const id = await newRun("p02_quantum", { preset: "cyclotron" });
  const { page, ctx } = await openRun(b, id);
  await sleep(1500);
  out.p02_cyc = await page.evaluate(() => [...document.querySelectorAll("button")]
    .filter((x) => /Магнитное поле|Стенка со щелями/.test(x.textContent))
    .map((x) => ({ t: x.textContent, disabled: x.disabled, title: x.title })));
  await ctx.close(); await post(`/api/runs/${id}/stop`, {});
}
console.log(JSON.stringify(out, null, 1));
fs.writeFileSync("/pw/out_pgui.json", JSON.stringify(out, null, 1));
await b.close();
