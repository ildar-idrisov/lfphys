// Review LB1-p02-ux, Part B, tour b1: p02 as the owner uses it (double slit preset), 1600x1000.
// select / drag / throw / delete in the plane's window; live grid and window; a refusal; the event log; timings.
import { browser, newRun, openRun, shot, log, sleep, attachErrors, cmd, record, scrWin, scr3, dragPath, toasts, idle, lastOf, waitFor } from "./b_lib.mjs";

const W = Number(process.env.W || 1600), H = Number(process.env.H || 1000);
const tag = `${W}x${H}`;
const br = await browser();
const errs = [];
const id = await newRun("p02_quantum", "double_slit");
log(`b1 ${tag} run`, id);
const page = await br.newPage({ viewport: { width: W, height: H } });
attachErrors(page, errs);
await openRun(page, id);
// run it a little (the electron reaches the wall)
await cmd(id, "play");
await sleep(6000);
await cmd(id, "pause");
await sleep(1500);
await shot(page, `b1_${tag}_01_after_play`);
const rec0 = await record(id);
const tNow = rec0.filter((m) => m.type === "frame").at(-1)?.t;
log("b1 world time after 6 s play", tNow);

// 1. select the electron by a click in the plane's window
let pe = await scrWin(page, "o4", 1);
log("b1 electron in window", pe);
if (pe) {
  await page.mouse.click(pe[0], pe[1]);
  await sleep(600);
  const sel = await page.evaluate(() => ({ sel: window.__lfManip.selected(), insp: document.querySelector('input[title="Имя объекта"]')?.value }));
  log("b1 select", sel);
  await shot(page, `b1_${tag}_02_selected`);
}
// 2. drag the electron by ~ +60 px right, -80 px up
pe = await scrWin(page, "o4", 1);
if (pe) {
  const t0 = Date.now();
  const mid = await dragPath(page, pe, [pe[0] - 40, pe[1] - 90], { before: () => page.evaluate(() => window.__lfManip.text()) });
  await idle(page);
  const dt = Date.now() - t0;
  await sleep(800);
  log("b1 drag readout mid-gesture", mid, "ms to idle", dt, "toasts", await toasts(page));
  await shot(page, `b1_${tag}_03_dragged`);
  const rec = await record(id);
  log("b1 events after drag", lastOf(rec, "event", 3), "errors", lastOf(rec, "error", 2));
}
// 3. throw with Shift
pe = await scrWin(page, "o4", 1);
if (pe) {
  const mid = await dragPath(page, pe, [pe[0] + 120, pe[1] + 30], { n: 12, dtMs: 16, shift: true, before: () => page.evaluate(() => window.__lfManip.text()) });
  await idle(page);
  await sleep(800);
  log("b1 throw readout mid-gesture", mid, "toasts", await toasts(page));
  await shot(page, `b1_${tag}_04_thrown`);
  const rec = await record(id);
  log("b1 events after throw", lastOf(rec, "event", 3), "errors", lastOf(rec, "error", 2));
}
// 4. a hard throw: far beyond the grid's limit
pe = await scrWin(page, "o4", 1);
if (pe) {
  await page.fill(".pg-manip input[type=number]", "50");
  await page.press(".pg-manip input[type=number]", "Enter");
  const mid = await dragPath(page, pe, [pe[0] + 200, pe[1]], { n: 6, dtMs: 10, shift: true, before: () => page.evaluate(() => window.__lfManip.text()) });
  await idle(page);
  await sleep(800);
  log("b1 hard throw readout", mid, "toasts", await toasts(page));
  const rec = await record(id);
  log("b1 events after hard throw", lastOf(rec, "event", 3), "errors", lastOf(rec, "error", 2));
  await shot(page, `b1_${tag}_05_hard_throw`);
  await page.click(".pg-manip button:has-text('авто')").catch(() => {});
}
// 5. drag the wall along its axis; then the detector
for (const oid of ["o1", "o2"]) {
  const p = await scrWin(page, oid, 1);
  log("b1 object in window", oid, p);
  if (!p) continue;
  const t0 = Date.now();
  await dragPath(page, p, [p[0] + 50, p[1] + 20]);
  await idle(page);
  log(`b1 drag ${oid} ms`, Date.now() - t0, "toasts", await toasts(page));
  const rec = await record(id);
  log(`b1 events after ${oid} drag`, lastOf(rec, "event", 2), "errors", lastOf(rec, "error", 1));
}
await shot(page, `b1_${tag}_06_moved_wall_det`);
// 6. select the flux plane and press Delete
const pp = await scrWin(page, "o3", 1);
log("b1 plane in window", pp);
if (pp) {
  await page.mouse.click(pp[0], pp[1]);
  await sleep(400);
  log("b1 selected", await page.evaluate(() => window.__lfManip.selected()));
  await page.keyboard.press("Delete");
  await sleep(1500);
  const rec = await record(id);
  log("b1 after Delete", lastOf(rec, "event", 2), "errors", lastOf(rec, "error", 1), "objects", await page.evaluate(() => [...document.querySelectorAll(".pg-obj .pg-name, .pg-list .name")].map((e) => e.textContent)));
}
await shot(page, `b1_${tag}_07_deleted_plane`);
// 7. live grid: 256 -> 384; window 80 -> 100; 384 -> 192 (refused: wall edge); edges closed
const sel = page.locator("#left select").first();
for (const [what, act] of [
  ["n2 384", async () => { await sel.selectOption("384"); }],
  ["size 100", async () => { const i = page.locator("#left input[type=number], #left input[type=text]").first(); await i.fill("100"); await i.press("Enter"); }],
  ["n2 192", async () => { await sel.selectOption("192"); }],
  ["edges closed", async () => { await page.locator("#left select").nth(1).selectOption("closed"); }],
]) {
  const t0 = Date.now();
  const n0 = (await record(id)).length;
  await act();
  await waitFor(async () => (await record(id)).length > n0 + 1, 60000, 300);
  await sleep(1500);
  const rec = await record(id);
  log(`b1 live ${what}: ${Date.now() - t0} ms`, "events", lastOf(rec, "event", 1), "errors", lastOf(rec, "error", 1), "toasts", await toasts(page));
  await shot(page, `b1_${tag}_08_live_${what.replace(/ /g, "_")}`);
}
// 8. the event log as the owner reads it
const ev = await page.evaluate(() => document.querySelector("#right")?.innerText.split("СОБЫТИЯ")[1]?.slice(0, 4000));
log("b1 events panel:\n" + ev);
log("b1 page errors", errs);
await page.close();
await br.close();
