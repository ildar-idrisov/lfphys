// Response LB1-p02-ux (p02): the visible fixes in a browser, against the PRIVATE server (port 8613).
// 1 (Q5/X5) a hard throw after the double slit's wall: clamped by the world and said, not refused;
// 2 (Q1) a drag of the AB electron across the lower slit while the wave is in it: refused, naming the tube;
//   then (Q1) a drag along the wall after it passed: taken as the magnetic translation;
// 3 (Q4) «Новый мир» into space with the scene carried: wall, tube, plane, detector and packet all in the 3-D scene.
import { log, OUT, post, get, sleep, cmd, record, waitFor, browser, newRun, openRun, scrWin, dragPath, toasts, idle, lastOf, shot, attachErrors } from "./b_lib.mjs";
const errs = [];
const b = await browser();
const page = await b.newPage({ viewport: { width: 1600, height: 1000 } });
attachErrors(page, errs);
const tAt = async (id) => (await record(id)).filter((m) => m.type === "frame").at(-1)?.t;
async function playUntil(id, t) {
  await cmd(id, "play");
  await waitFor(async () => ((await tAt(id)) || 0) >= t, 120000, 500);
  await cmd(id, "pause");
  await sleep(1500);
}
// 1
let id = await newRun("p02_quantum", "double_slit");
await openRun(page, id);
await playUntil(id, 1.25e-13);
let pe = await scrWin(page, "o4", 1);
log("1 electron", pe, "t", await tAt(id));
await page.mouse.click(pe[0], pe[1]); await sleep(500);
await dragPath(page, pe, [pe[0] + 70, pe[1] - 4], { n: 3, dtMs: 2, shift: true });
await idle(page); await sleep(2500);
let rec = await record(id);
log("1 events", lastOf(rec, "event", 3), "errors", lastOf(rec, "error", 2), "toasts", await toasts(page));
await shot(page, "fix1_throw_after_wall_clamped");
log('page errors', errs);
await b.close();
process.exit(0);
// 2
id = await newRun("p02_quantum", "aharonov_bohm");
await openRun(page, id);
await playUntil(id, 2.9e-14);
pe = await scrWin(page, "o4", 1);
const at = await page.evaluate(() => window.__lfManip.at("o4"));
const tgt = await page.evaluate(([p]) => {
  const W = [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean)[0];
  const h = W.helper(1), r = h.el.getBoundingClientRect(), [x, y] = h.toCanvas([p[0], p[1] + 6, 0]);
  return [r.left + x, r.top + y];
}, [at]);
log("2 electron", pe, at, "target", tgt, "t", await tAt(id));
await page.mouse.click(pe[0], pe[1]); await sleep(500);
await dragPath(page, pe, tgt, { n: 10, dtMs: 16 });
await idle(page); await sleep(1500);
rec = await record(id);
log("2 errors", lastOf(rec, "error", 1), "toasts", await toasts(page));
await shot(page, "fix2_ab_drag_across_slit_refused");
await playUntil(id, 1.15e-13);
pe = await scrWin(page, "o4", 1);
const at2 = await page.evaluate(() => window.__lfManip.at("o4"));
const tgt2 = await page.evaluate(([p]) => {
  const W = [...document.querySelectorAll(".s3d-windows")].map((e) => e.__slices).filter(Boolean)[0];
  const h = W.helper(1), r = h.el.getBoundingClientRect(), [x, y] = h.toCanvas([p[0], p[1] + 4, 0]);
  return [r.left + x, r.top + y];
}, [at2]);
await page.mouse.click(pe[0], pe[1]); await sleep(500);
await dragPath(page, pe, tgt2, { n: 10, dtMs: 16 });
await idle(page); await sleep(2000);
rec = await record(id);
log("2b events", lastOf(rec, "event", 2), "errors", lastOf(rec, "error", 1));
await shot(page, "fix2b_ab_drag_along_wall_taken");
// 3
const scene = { format: "lfscene", version: 1, objects: [
  { type: "slit_wall", label: "Стенка", values: { position: 0.0, thickness: 3.0, V: 3.0, n_slits: 2, width: 2.0, spacing: 8.0 } },
  { type: "flux", label: "Трубка", values: { x: 0.0, y: 0.0, flux: 0.5, radius: 1.0 } },
  { type: "plane", label: "Поток", values: { position: 8.0 } },
  { type: "detector", label: "Экран", values: { x: 15.0, sx: 3.0, edge: 3.0 } },
  { type: "packet", label: "Электрон", values: { x: -5.0, wavelength: 4.0, sx: 1.5, sy: 1.5 } }] };
const r3 = await post("/api/runs", { viz: "p02_quantum", params: { dim: "2d", n2: "128", size: 40.0, edges: "open", scene }, seed: 3 });
id = r3.id;
await waitFor(async () => (await get(`/api/runs/${id}`)).state === "running", 120000, 300);
await openRun(page, id);
await cmd(id, "new_world", { params: { dim: "3d", n3: "96", size: 40.0 }, carry: true });
await waitFor(async () => (await record(id)).some((m) => m.type === "notice" && m.carry), 180000, 1000);
await sleep(6000);
rec = await record(id);
log("3 notice", lastOf(rec, "notice", 1), "errors", lastOf(rec, "error", 1), "toasts", await toasts(page));
await shot(page, "fix3_carry_into_space");
log("page errors", errs);
await b.close();
