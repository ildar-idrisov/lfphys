// Review 2026-10-29, check k07: v07 differed in k06 also between two rebuilds from the record (p = 0.05): which part of
// the page differs, and is it the key frame or the view itself? Same cursor: (A) through a key frame, (B) rebuilt from the
// record, (C) rebuilt again; the canvases' and panels' fingerprints of each.
//   node k07_v07_probe.mjs <port> <run id>
import { createHash } from "crypto";
import { writeFileSync } from "fs";
import { browser, dbg, open, settle } from "./k_common.mjs";

const id = process.argv[3];
const out = [];
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); out.push(s); console.log(s); };
const br = await browser();
const page = await open(br, id, 3, []);
const fp = async () => {
  const parts = [];
  for (const hdl of await page.$$("canvas")) {
    const info = await hdl.evaluate((c) => ({ w: c.width, h: c.height, vis: !!c.offsetParent, cls: c.className, parent: c.parentElement && c.parentElement.className }));
    if (!info.vis || !info.w) continue;
    try { parts.push(`${info.parent}/${info.w}x${info.h}:` + createHash("sha1").update(await hdl.screenshot()).digest("hex").slice(0, 10)); } catch (e) { parts.push("err"); }
  }
  const panels = await page.evaluate(() => [...document.querySelectorAll(".panel")].map((p) => (p.innerText || "").replace(/\s+/g, " ").slice(0, 200)));
  return { canvases: parts, panels };
};
const nf = (await dbg(page)).frames;
for (const p of [0.3, 0.05]) {
  await page.evaluate((i) => window.__lfPlayer.goTo(i), Math.round(p * (nf - 1)));
  await settle(page);
  const d = await dbg(page);
  const A = await fp();
  await page.evaluate(() => window.__lfPlayer.rebuildFromRecord()); await settle(page);
  const B = await fp();
  await page.evaluate(() => window.__lfPlayer.rebuildFromRecord()); await settle(page);
  const C = await fp();
  const cmp = (X, Y) => ({ canvases: X.canvases.map((x, k) => x === Y.canvases[k]), panels: X.panels.map((x, k) => (x === Y.panels[k] ? true : [x, Y.panels[k]])) });
  log(JSON.stringify({ p, t: d.t, how: d, A_vs_B: cmp(A, B), B_vs_C: cmp(B, C) }));
  await page.evaluate(() => window.__lfPlayer.goTo(1e9)); await settle(page);
}
writeFileSync("out/k07_v07_probe.txt", out.join("\n") + "\n");
await br.close();
