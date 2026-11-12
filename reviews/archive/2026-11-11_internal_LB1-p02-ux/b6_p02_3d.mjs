// Review LB1-p02-ux, Part B, tour b6: p02 in space (ball_3d preset) at 1280x800 — a drag and a throw of the packet in
// the 3-D view, the grid 64 -> 96 -> 64 live (timing), «Новый мир» into the plane with the scene carried, dark theme.
import { browser, newRun, openRun, shot, log, sleep, attachErrors, cmd, record, scrWin, scr3, dragPath, toasts, idle, lastOf, waitFor, camera } from "./b_lib.mjs";

const W = Number(process.env.W || 1280), H = Number(process.env.H || 800);
const tag = `${W}x${H}`;
const br = await browser();
const errs = [];
const id = await newRun("p02_quantum", "ball_3d");
log(`b6 ${tag} run`, id);
const page = await br.newPage({ viewport: { width: W, height: H } });
attachErrors(page, errs);
await openRun(page, id);
await cmd(id, "play"); await sleep(6000); await cmd(id, "pause"); await sleep(2000);
await shot(page, `b6_${tag}_01`);
const objs = await page.evaluate(() => window.__lfManip.objects());
log("b6 objects", objs.map((o) => `${o.id}:${o.type}`));
const pk = objs.find((o) => o.type === "packet");
let p = await scr3(page, pk.id);
log("b6 packet on screen (3-D)", p);
if (p) {
  await page.mouse.click(p[0], p[1]); await sleep(400);
  const cam0 = await camera(page);
  let n0 = (await record(id)).length, t0 = Date.now();
  const mid = await dragPath(page, p, [p[0] - 50, p[1] + 30], { before: () => page.evaluate(() => window.__lfManip.text()) });
  await idle(page); await sleep(800);
  let rec = (await record(id)).slice(n0);
  log(`b6 drag: ${Date.now() - t0} ms, readout`, mid, "events", rec.filter((m) => m.type === "event").map((m) => m.text), "errors", rec.filter((m) => m.type === "error").map((m) => m.text),
    "camera moved", JSON.stringify(cam0) !== JSON.stringify(await camera(page)), "selected", await page.evaluate(() => window.__lfManip.selected()));
  await shot(page, `b6_${tag}_02_dragged`);
  p = await scr3(page, pk.id);
  n0 = (await record(id)).length; t0 = Date.now();
  const midT = await dragPath(page, p, [p[0] + 70, p[1]], { n: 12, dtMs: 16, shift: true, before: () => page.evaluate(() => window.__lfManip.text()) });
  await idle(page); await sleep(800);
  rec = (await record(id)).slice(n0);
  log(`b6 throw: ${Date.now() - t0} ms, readout`, midT, "events", rec.filter((m) => m.type === "event").map((m) => m.text), "errors", rec.filter((m) => m.type === "error").map((m) => m.text));
  await shot(page, `b6_${tag}_03_thrown`);
}
// live grid 64 -> 96 -> 64
for (const v of ["96", "64"]) {
  const sel = page.locator("#left select").filter({ has: page.locator("option[value='96']") }).first();
  const n0 = (await record(id)).length, t0 = Date.now();
  await sel.selectOption(v);
  await waitFor(async () => (await record(id)).slice(n0).some((m) => m.type === "event" || m.type === "error"), 120000, 300);
  const rec = (await record(id)).slice(n0);
  log(`b6 n3 -> ${v}: ${Date.now() - t0} ms`, "events", rec.filter((m) => m.type === "event").map((m) => m.text), "errors", rec.filter((m) => m.type === "error").map((m) => m.text));
  await sleep(1500);
}
await shot(page, `b6_${tag}_04_regridded`);
// into the plane, scene carried
const head = page.locator("text=Новый мир: законы и начальные условия").first();
await head.scrollIntoViewIfNeeded(); await head.click(); await sleep(600);
await page.locator("select").filter({ has: page.locator("option[value='2d']") }).first().selectOption("2d");
const n0 = (await record(id)).length, t0 = Date.now();
await page.locator("button", { hasText: "Начать новый мир" }).click();
await waitFor(async () => (await record(id)).slice(n0).some((m) => m.type === "header"), 120000, 400);
await sleep(4000);
const rec = (await record(id)).slice(n0);
log(`b6 into the plane: ${Date.now() - t0} ms; notices`, rec.filter((m) => m.type === "notice").map((m) => m.text), "errors", rec.filter((m) => m.type === "error").map((m) => m.text));
await shot(page, `b6_${tag}_05_plane_world`);
await page.keyboard.press("t"); await sleep(800);
await shot(page, `b6_${tag}_06_plane_dark`);
log("b6 page errors", errs);
await page.close();
await br.close();
