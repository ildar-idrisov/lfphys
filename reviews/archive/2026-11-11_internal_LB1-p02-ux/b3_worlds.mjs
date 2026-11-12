// Review LB1-p02-ux, Part B, tour b3: p01, p03, p04 as the owner uses them (the user's view only; their engines are
// reviewed by others): a preset played, the live laws of LB1 changed from the panel or the inspector, an object
// selected / dragged / thrown / deleted in the 3-D view (or the window), with what the page says and how long it takes.
// WORLDS env: comma list among p01k, p01pn, p03, p04 (default all).
import { browser, newRun, openRun, shot, log, sleep, attachErrors, cmd, record, scrWin, scr3, dragPath, toasts, idle, lastOf, waitFor, camera } from "./b_lib.mjs";

const W = Number(process.env.W || 1600), H = Number(process.env.H || 1000);
const tag = `${W}x${H}`;
const want = (process.env.WORLDS || "p01k,p01pn,p03,p04").split(",");
const br = await browser();

async function findCtl(page, label) {
  // the last visible control whose label starts with the text (the inspector comes after the live laws)
  const ok = await page.evaluate((label) => {
    document.querySelectorAll("[data-rv]").forEach((e) => e.removeAttribute("data-rv"));
    const ctls = [...document.querySelectorAll("#left .ctl")].filter((c) => (c.querySelector("label")?.textContent || "").trim().startsWith(label)
      && c.querySelector("input, select"));
    const c = ctls.at(-1);
    if (!c) return false;
    c.scrollIntoView({ block: "center" });
    c.querySelector("input, select").setAttribute("data-rv", "1");
    return true;
  }, label);
  return ok ? page.locator("[data-rv='1']") : null;
}
async function liveSet(page, id, label, value) {
  const inp = await findCtl(page, label);
  if (!inp) { log(`  live «${label}»: control not found`); return; }
  const t0 = Date.now(), n0 = (await record(id)).length;
  const tagName = await inp.evaluate((e) => e.tagName);
  if (tagName === "SELECT") await inp.selectOption(String(value));
  else { await inp.fill(String(value)); await inp.press("Enter"); }
  await waitFor(async () => (await record(id)).slice(n0).some((m) => m.type === "event" || m.type === "error" || m.type === "notice"), 90000, 300);
  const dt = Date.now() - t0;
  await sleep(800);
  const rec = (await record(id)).slice(n0);
  log(`  live «${label}» = ${value}: ${dt} ms;`, "events", rec.filter((m) => m.type === "event").map((m) => m.text).slice(-2),
    "errors", rec.filter((m) => m.type === "error").map((m) => m.text), "notices", rec.filter((m) => m.type === "notice").map((m) => m.text));
}
async function inspSet(page, id, oid, label, value) {
  const p = await scr3(page, oid) || await scrWin(page, oid, 1);
  if (p) { await page.mouse.click(p[0], p[1]); await sleep(500); }
  else { const row = page.locator(".pg-row, .pg-list > div", { hasText: "" }); }
  const sel = await page.evaluate(() => window.__lfManip.selected());
  if (!p) { await page.locator("#left .pg-row, #left div", { hasText: "" }).first(); }
  const inp = await findCtl(page, label);
  if (!inp) { log(`  inspector «${label}» (selected ${sel}): control not found`); return; }
  const t0 = Date.now(), n0 = (await record(id)).length;
  await inp.fill(String(value)); await inp.press("Enter");
  await waitFor(async () => (await record(id)).slice(n0).some((m) => m.type === "event" || m.type === "error"), 90000, 300);
  const dt = Date.now() - t0;
  await sleep(800);
  const rec = (await record(id)).slice(n0);
  log(`  inspector «${label}» of ${sel} = ${value}: ${dt} ms;`, "events", rec.filter((m) => m.type === "event").map((m) => m.text).slice(-3),
    "errors", rec.filter((m) => m.type === "error").map((m) => m.text));
}
async function manipulate(page, id, oid, name) {
  let p = await scr3(page, oid);
  let where = "3-D";
  if (!p) { p = await scrWin(page, oid, 1); where = "window"; }
  log(`  ${name}: ${oid} at screen`, p, where);
  if (!p) return;
  await page.mouse.click(p[0], p[1]); await sleep(400);
  const sel = await page.evaluate(() => window.__lfManip.selected());
  const cam0 = await camera(page).catch(() => null);
  let n0 = (await record(id)).length, t0 = Date.now();
  const mid = await dragPath(page, p, [p[0] + 60, p[1] - 40], { before: () => page.evaluate(() => window.__lfManip.text()) });
  await idle(page); await sleep(800);
  let rec = (await record(id)).slice(n0);
  const cam1 = await camera(page).catch(() => null);
  log(`  drag (selected ${sel}): ${Date.now() - t0} ms; readout`, mid, "events", rec.filter((m) => m.type === "event").map((m) => m.text).slice(-2),
    "errors", rec.filter((m) => m.type === "error").map((m) => m.text), "camera moved", JSON.stringify(cam0) !== JSON.stringify(cam1),
    "selected after", await page.evaluate(() => window.__lfManip.selected()));
  p = await scr3(page, oid) || await scrWin(page, oid, 1);
  if (p) {
    n0 = (await record(id)).length; t0 = Date.now();
    const midT = await dragPath(page, p, [p[0] + 90, p[1] + 20], { n: 12, dtMs: 16, shift: true, before: () => page.evaluate(() => window.__lfManip.text()) });
    await idle(page); await sleep(800);
    rec = (await record(id)).slice(n0);
    log(`  throw: ${Date.now() - t0} ms; readout`, midT, "events", rec.filter((m) => m.type === "event").map((m) => m.text).slice(-2),
      "errors", rec.filter((m) => m.type === "error").map((m) => m.text));
  }
  await shot(page, `b3_${name}_${tag}_manip`);
}
async function del(page, id, oid, name) {
  const p = await scr3(page, oid) || await scrWin(page, oid, 1);
  if (!p) { log(`  delete ${oid}: not on screen`); return; }
  await page.mouse.click(p[0], p[1]); await sleep(400);
  const sel = await page.evaluate(() => window.__lfManip.selected());
  const n0 = (await record(id)).length;
  await page.keyboard.press("Delete"); await sleep(2500);
  const rec = (await record(id)).slice(n0);
  log(`  Delete (selected ${sel}):`, "scene removes", rec.filter((m) => m.type === "command" && m.cmd === "scene" && m.args.op === "remove").length,
    "view commands", rec.filter((m) => m.type === "command" && m.cmd === "view").length, "errors", rec.filter((m) => m.type === "error").map((m) => m.text), "toasts", await toasts(page));
}

const cfg = {
  p01k: { viz: "p01_gravity", preset: "kerr_orbits", run: async (page, id, objs) => {
    const hole = objs.find((o) => o.type === "kn_hole"), body = objs.find((o) => o.type === "body");
    if (hole) { await inspSet(page, id, hole.id, "Масса M", 20); await inspSet(page, id, hole.id, "Спин a/M", 0.5); await inspSet(page, id, hole.id, "Заряд", 0.3); }
    if (body) await manipulate(page, id, body.id, "p01k");
    const obs = objs.find((o) => o.type === "observer");
    if (obs) await del(page, id, obs.id, "p01k");
  } },
  p01pn: { viz: "p01_gravity", preset: "pn_inspiral", run: async (page, id, objs) => {
    const bin = objs.find((o) => /binary|pn/.test(o.type)) || objs[0];
    log("  p01pn objects", objs.map((o) => `${o.id}:${o.type}`));
    if (bin) await inspSet(page, id, bin.id, "Полная масса", 40);
  } },
  p03: { viz: "p03_molecules", preset: "maxwell", run: async (page, id, objs) => {
    log("  p03 objects", objs.map((o) => `${o.id}:${o.type}`));
    await liveSet(page, id, "Динамика", "hard");
    await liveSet(page, id, "Динамика", "forces");
    await liveSet(page, id, "Как менять размер ящика", "wall");
    await liveSet(page, id, "Размер ящика по y", 14);
    await liveSet(page, id, "Как менять размер ящика", "affine");
    await liveSet(page, id, "Размер ящика по x", 11);
    const g = objs.find((o) => ["gas", "atom", "crystal", "molecule", "probe"].includes(o.type));
    if (g) await manipulate(page, id, g.id, "p03");
    const pr = objs.find((o) => o.type === "probe");
    if (pr) await del(page, id, pr.id, "p03");
  } },
  p04: { viz: "p04_fluids", preset: "cylinder_re20", run: async (page, id, objs) => {
    log("  p04 objects", objs.map((o) => `${o.id}:${o.type}`));
    await liveSet(page, id, "Узлов сетки по x", 330);
    await liveSet(page, id, "Наибольшая ожидаемая скорость", 0.3);
    await liveSet(page, id, "Длина области по x", 2.5);
    const c = objs.find((o) => o.type === "disk");
    if (c) await manipulate(page, id, c.id, "p04");
  } },
};

for (const k of want) {
  const c = cfg[k];
  const errs = [];
  const id = await newRun(c.viz, c.preset);
  log(`b3 ${k} ${tag} run`, id);
  if (!id) continue;
  const page = await br.newPage({ viewport: { width: W, height: H } });
  attachErrors(page, errs);
  try {
    await openRun(page, id);
    await cmd(id, "play"); await sleep(5000); await cmd(id, "pause"); await sleep(2000);
    await shot(page, `b3_${k}_${tag}_01`);
    const live = await page.evaluate(() => document.querySelector("#left").innerText.slice(0, 1200));
    log(`  ${k} left column:\n` + live);
    const objs = await page.evaluate(() => window.__lfManip.objects());
    await c.run(page, id, objs);
    await shot(page, `b3_${k}_${tag}_02_end`);
    await page.keyboard.press("t"); await sleep(800);
    await shot(page, `b3_${k}_${tag}_03_dark`);
  } catch (e) { log(`  ${k} FAILED`, e.message.slice(0, 400)); await shot(page, `b3_${k}_${tag}_fail`); }
  log(`  ${k} page errors`, errs);
  await page.close();
}
await br.close();
