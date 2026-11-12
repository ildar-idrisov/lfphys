// Review 2026-10-29, check k01: v09 in ordinary space (preset "lab"): the scene's box grows as the path is revealed
// (box messages). The craft (scene3d.setBody) is made once, sized by the box in force when it is first drawn. Opened at
// the end of the record (the craft made with the final box) and stepped back through a key frame, the craft keeps the
// final box's size; the view rebuilt from the record at the same cursor makes it with the box of that time.
import { writeFileSync } from "fs";
import { browser, dbg, open, post, scene, settle, sleep, waitRun } from "./k_common.mjs";

const out = [], errs = [];
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); out.push(s); console.log(s); };
const br = await browser();
const r = await post("/api/runs", { viz: "v09_thomas_3d", preset: "lab", params: { loop: "circle", rho: 2.0 }, seed: 3 });
log("run", r.id);
await waitRun(r.id, (m) => m.state === "running");
await post(`/api/runs/${r.id}/command`, { cmd: "speed", args: { value: 1e9 } });
await post(`/api/runs/${r.id}/command`, { cmd: "play" });
await sleep(20000);
await post(`/api/runs/${r.id}/command`, { cmd: "pause" });
await sleep(1500);
const page = await open(br, r.id, 5, errs);  // opened at the end: the craft is made with the final box
const craft = (s) => (s && s.layers.craft) ? { radius: s.layers.craft.radius, size: +s.size.toPrecision(6) } : null;
const nf = (await dbg(page)).frames;
log("frames", nf, "end:", craft(await scene(page)), await dbg(page));
for (const p of [0.005, 0.02, 0.05, 0.1, 0.2, 0.4]) {
  const i = Math.round(p * (nf - 1));
  await page.evaluate((i) => window.__lfPlayer.goTo(i), i);
  await settle(page);
  const d = await dbg(page), A = craft(await scene(page));
  await page.evaluate(() => window.__lfPlayer.rebuildFromRecord());
  await settle(page);
  const B = craft(await scene(page));
  log(JSON.stringify({ p, t: d.t, via: d.fromKey ? "key" : "?", dbg: d, key_frame: A, rebuilt: B,
                       same: JSON.stringify(A) === JSON.stringify(B) }));
  await page.evaluate(() => window.__lfPlayer.goTo(1e9));  // back to the end (the view fed forward)
  await settle(page);
}
log("errors", errs.slice(0, 10));
writeFileSync("out/k01_v09_body.txt", out.join("\n") + "\n");
await br.close();
