// G1 response check (U3/P30): p02 «Двухщелевой опыт» recording in the browser; a scene change sent as the palette does
// (command scene add) and the time until the page lists the new object; before (PORT 8577: the tree before) and after.
import { base, browser, newRun, sleep, post, openRun } from "./common.mjs";
import fs from "fs";
const tag = process.argv[2] || "after";
const b = await browser();
const id = await newRun("p02_quantum", { preset: "double_slit" });
const { page, ctx, logs } = await openRun(b, id);
await post(`/api/runs/${id}/command`, { cmd: "play" });
await sleep(3000);
const out = [];
for (const [lab, type, values] of [["Ящик Т1", "box", { x: 20, y: 20 }], ["Детектор Т2", "detector", { x: 20, y: -20 }],
                                   ["Метка Т3", "marker", { x: 2, y: 5 }], ["Плоскость Т4", "plane", { position: 20 }],
                                   ["Шар Т5", "ball", { x: -10, y: 25, radius: 3 }]]) {
  const t0 = Date.now();
  await post(`/api/runs/${id}/command`, { cmd: "scene", args: { op: "add", type, values, label: lab } });
  let ok = false;
  try { await page.waitForFunction((l) => document.body.innerText.includes(l), lab, { timeout: 120000 }); ok = true; } catch (e) { /* timeout */ }
  out.push({ tag, change: `add ${type}`, s: (Date.now() - t0) / 1000, ok });
  console.log(JSON.stringify(out[out.length - 1]));
  await sleep(1000);
}
await page.screenshot({ path: `/pw/shots/${tag}_p02_after_adds.jpg`, type: "jpeg", quality: 70 });
fs.writeFileSync(`/pw/out_p02lat_${tag}.json`, JSON.stringify({ out, logs }, null, 1));
await ctx.close(); await post(`/api/runs/${id}/stop`, {});
await b.close();
