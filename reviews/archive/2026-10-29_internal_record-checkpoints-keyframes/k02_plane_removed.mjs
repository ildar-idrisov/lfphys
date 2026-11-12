// Review 2026-10-29, check k02 (v09 in velocity space: its time runs, unlike v08's stationary wave, whose record
// stays at t = 0): a slice plane that existed at a key frame and was removed after it. The environment's
// key frame keeps the latest message per object; the plane's slice message is the same before and after the removal,
// so env3d.restore does not set it again, while setting the planes again makes the plane (and its window) anew,
// empty. The view brought back through the key frame shows plane 2 without its slice; the view rebuilt from the record
// at the same cursor shows it with its slice.
import { writeFileSync } from "fs";
import { browser, dbg, get, open, post, scene, settle, sleep, waitRun } from "./k_common.mjs";

const out = [], errs = [];
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); out.push(s); console.log(s); };
const br = await browser();
const r = await post("/api/runs", { viz: "v09_thomas_3d", params: { ngrid: 48 }, seed: 3 });
const id = r.id;
log("run", id);
await waitRun(id, (m) => m.state === "running");
const cmd = (c, a) => post(`/api/runs/${id}/command`, { cmd: c, args: a || {} });
const simT = async () => (await get(`/api/runs/${id}`)).sim_t;
await cmd("play");
await sleep(2000);
const center = [0, 0, 0];
await cmd("view", { op: "plane", id: 2, origin: center, normal: [1, 0, 0] });
await sleep(2500);
const tAdd = await simT();
for (let k = 0; k < 6; k++) { await cmd("view", { op: "plane", id: 1, origin: [0, 0, -0.3 + 0.1 * k], normal: [0, 0, 1] }); await sleep(1500); }
const tRemove = await simT();
await cmd("view", { op: "remove", id: 2 });
await sleep(2000);
for (let k = 0; k < 6; k++) { await cmd("view", { op: "plane", id: 1, origin: [0, 0, 0.3 - 0.1 * k], normal: [0, 0, 1] }); await sleep(1500); }
await cmd("pause");
await sleep(1500);
log("t_add", tAdd, "t_remove", tRemove);

const page = await open(br, id, 2, errs);
const nf = (await dbg(page)).frames;
const tAt = (i) => page.evaluate((i) => { window.__lfPlayer.goTo(i); return window.__lfPlayer.t(); }, i);
let lo = 0, hi = nf - 1;
const target = (tAdd + tRemove) / 2;
while (lo < hi) { const mid = (lo + hi) >> 1; if ((await tAt(mid)) < target) lo = mid + 1; else hi = mid; }
log("frames", nf, "cursor frame", lo, "t", await tAt(lo));
await page.evaluate(() => window.__lfPlayer.goTo(1e9));
await settle(page);
const summary = (s) => s && { planes: s.planes, wins: s.wins.map((w) => ({ id: w.id, pix: w.pix, text: w.text.slice(0, 40) })) };
log("at the end:", JSON.stringify(summary(await scene(page))));
await page.evaluate((i) => window.__lfPlayer.goTo(i), lo);
await settle(page);
const d = await dbg(page);
const A = summary(await scene(page));
await page.evaluate(() => window.__lfPlayer.rebuildFromRecord());
await settle(page);
const B = summary(await scene(page));
log(JSON.stringify({ t: d.t, how: d, key_frame: A, rebuilt: B, same: JSON.stringify(A) === JSON.stringify(B) }, null, 0));
log("errors", errs.slice(0, 10));
writeFileSync("out/k02_plane_removed.txt", out.join("\n") + "\n");
await br.close();
