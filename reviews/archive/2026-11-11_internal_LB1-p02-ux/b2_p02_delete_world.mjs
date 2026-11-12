// Review LB1-p02-ux, Part B, tour b2: p02 — Delete of a selected object in the plane's window, the edges closed live,
// «Новый мир» of the other dimension with «перенести сцену» from the panel (what the form offers, what is carried),
// a drag in the 3-D view of the space world, and back to the plane.
import { browser, newRun, openRun, shot, log, sleep, attachErrors, cmd, record, scrWin, scr3, dragPath, toasts, idle, lastOf, waitFor } from "./b_lib.mjs";

const W = Number(process.env.W || 1600), H = Number(process.env.H || 1000);
const tag = `${W}x${H}`;
const br = await browser();
const errs = [];
const id = await newRun("p02_quantum", "double_slit");
log(`b2 ${tag} run`, id);
const page = await br.newPage({ viewport: { width: W, height: H } });
attachErrors(page, errs);
await openRun(page, id);
await cmd(id, "play"); await sleep(4000); await cmd(id, "pause"); await sleep(1500);

// 1. Delete: select the detector by a click in the window, press Delete
const removes = async () => (await record(id)).filter((m) => m.type === "command" && m.cmd === "scene" && m.args.op === "remove").length;
const view = async () => (await record(id)).filter((m) => m.type === "command" && m.cmd === "view").length;
const pd = await scrWin(page, "o2", 1);
await page.mouse.click(pd[0], pd[1]);
await sleep(500);
const st = await page.evaluate(() => ({ sel: window.__lfManip.selected(), sliceSel: document.querySelector(".s3d-view")?.__scene3d?.state?.selected ?? null,
  win1: document.querySelector(".s3d-windows")?.innerText?.slice(0, 80) }));
const r0 = await removes(), v0 = await view();
await page.keyboard.press("Delete");
await sleep(2000);
log("b2 Delete after selecting the detector in the window:", st, "scene removes +", (await removes()) - r0, "view commands +", (await view()) - v0,
  "toasts", await toasts(page), "errors", lastOf(await record(id), "error", 1));
await shot(page, `b2_${tag}_01_delete`);
// the same after a click on empty space of the window first (deselect the slice?), then select, then Delete
await page.mouse.click(pd[0] - 300, pd[1] - 300); await sleep(300);
await page.mouse.click(pd[0], pd[1]); await sleep(500);
const r1 = await removes();
await page.keyboard.press("Delete"); await sleep(2000);
log("b2 Delete, second try:", "selected", await page.evaluate(() => window.__lfManip.selected()), "scene removes +", (await removes()) - r1, "toasts", await toasts(page));

// 2. the edges closed live
const edgesSel = page.locator("#left select").filter({ has: page.locator("option[value=closed]") }).first();
await edgesSel.selectOption("closed");
await sleep(3000);
log("b2 edges closed:", lastOf(await record(id), "event", 1), "errors", lastOf(await record(id), "error", 1));

// 3. «Новый мир»: open the panel, look at its form, choose the space, carry the scene
const panelHead = page.locator("text=Новый мир: законы и начальные условия").first();
await panelHead.scrollIntoViewIfNeeded();
await panelHead.click();
await sleep(800);
const form = await page.evaluate(() => {
  const box = [...document.querySelectorAll("details, .panel")].find((d) => /Новый мир/.test(d.innerText || ""));
  return box ? box.innerText.slice(0, 1500) : null;
});
log("b2 new-world panel text:\n" + form);
await shot(page, `b2_${tag}_02_new_world_form`);
const dimSel = page.locator("select").filter({ has: page.locator("option[value='3d']") }).first();
await dimSel.selectOption("3d");
await sleep(500);
await shot(page, `b2_${tag}_03_new_world_3d_chosen`);
const t0 = Date.now();
await page.locator("button", { hasText: "Начать новый мир" }).click();
await waitFor(async () => (await record(id)).filter((m) => m.type === "header").length >= 2, 120000, 500);
await sleep(4000);
log(`b2 new 3-D world after ${Date.now() - t0} ms; notices`, lastOf(await record(id), "notice", 3), "errors", lastOf(await record(id), "error", 2), "toasts", await toasts(page));
await shot(page, `b2_${tag}_04_3d_world`);
const live = await page.evaluate(() => document.querySelector("#left").innerText.slice(0, 600));
log("b2 3-D world live laws:\n" + live);

// 4. set the 3-D grid finer and the window smaller live, then add a packet from the palette, drag it in the 3-D view
const n3 = page.locator("#left select").filter({ has: page.locator("option[value='96']") }).first();
await n3.selectOption("96"); await sleep(4000);
log("b2 3-D n3 96:", lastOf(await record(id), "event", 1), "errors", lastOf(await record(id), "error", 1));
const size = page.locator("#left input").first();
await size.fill("40"); await size.press("Enter"); await sleep(5000);
log("b2 3-D size 40:", lastOf(await record(id), "event", 1), "errors", lastOf(await record(id), "error", 1));
await shot(page, `b2_${tag}_05_3d_regridded`);
log("b2 page errors", errs);
await page.close();
await br.close();
