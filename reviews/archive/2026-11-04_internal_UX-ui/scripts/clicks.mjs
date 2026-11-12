// U-click: does a human click (button held ~150 ms) on a line of «События» work while the world records (the list is
// rebuilt every drawn frame), and does the folded «Прежние группы проверок» stay open once the owner opens it?
import { browser, newRun, openRun, play, sleep, shot, post } from "./common.mjs";
import fs from "fs";
const b = await browser();
const out = {};
{
  const id = await newRun("v04_orbits", { preset: "default" });
  const { page, ctx } = await openRun(b, id);
  await post(`/api/runs/${id}/command`, { cmd: "speed", args: { value: 0.1 } });
  await play(page);
  await sleep(6000);
  // count rebuilds of the events list per second
  out.events_rebuilds_per_s = await page.evaluate(() => new Promise((res) => {
    let n = 0; const box = document.querySelector(".events");
    const mo = new MutationObserver((ms) => { for (const m of ms) if (m.type === "childList" && m.target === box) n++; });
    mo.observe(box, { childList: true }); setTimeout(() => { mo.disconnect(); res(n / 2); }, 2000);
  }));
  const res = [];
  for (let k = 0; k < 6; k++) {
    await page.keyboard.press("End"); await sleep(400);
    const r = await page.evaluate(() => { const e = document.querySelector(".events .ev"); if (!e) return null; e.scrollIntoView({ block: "center" }); const b = e.getBoundingClientRect(); if (b.bottom > innerHeight || b.top < 0) return null; return { x: b.left + 40, y: b.top + b.height / 2, t: e.textContent.slice(0, 40) }; });
    if (!r) { res.push("no event line"); continue; }
    const before = await page.evaluate(() => window.__lfPlayer.t());
    await page.mouse.move(r.x, r.y); await page.mouse.down(); await sleep(150); await page.mouse.up();
    await sleep(500);
    const st = await page.textContent("#status");
    const after = await page.evaluate(() => window.__lfPlayer.t());
    res.push(/история/.test(st) ? "jumped" : `no jump (t ${before.toPrecision(4)} -> ${after.toPrecision(4)})`);
  }
  out.human_click_on_event = res;
  // the older check groups: five boosts make five more segments, each a check group
  await page.keyboard.press("End");
  for (let i = 0; i < 6; i++) {
    await post(`/api/runs/${id}/command`, { cmd: "action", args: { name: "boost", args: { dv: 0.02 } } });
    await sleep(2500);
  }
  await sleep(2000);
  const has = await page.evaluate(() => { const d = document.querySelector("details.older"); if (!d) return false; d.open = true; d.scrollIntoView(); return true; });
  out.older_present = has;
  if (has) {
    const s = [];
    for (let i = 0; i < 40; i++) { s.push(await page.evaluate(() => { const d = document.querySelector("details.older"); return d ? (d.open ? 1 : 0) : "-"; })); await sleep(250); }
    out.older_open_series = s.join("");
    const rs = await page.evaluate(() => { const d = document.querySelector("#right"); return d.scrollTop; });
    out.right_scrollTop_after = rs;
  }
  fs.writeFileSync("/pw/out_clicks.json", JSON.stringify(out, null, 1));
  try { await post(`/api/runs/${id}/command`, { cmd: "pause" }); await sleep(1000); await shot(page, "/pw/shots/clicks_v04.jpg", { timeout: 90000 }); } catch (e) { out.shot_error = String(e).slice(0, 100); }
  await ctx.close();
  await post(`/api/runs/${id}/stop`, {});
}
console.log(JSON.stringify(out));
fs.writeFileSync("/pw/out_clicks.json", JSON.stringify(out, null, 1));
await b.close();
