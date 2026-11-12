// U-place (UI): every palette button of a playground preset clicked as the owner would, while the world records:
// the objects in the list before, 2.5 s and 6 s after; the toasts shown; the button's state. Usage: node palette.mjs [case]
import { browser, openRun, newRun, play, sleep, shot, post } from "./common.mjs";
import fs from "fs";
const CASES = {
  p01_inner: ["p01_gravity", { preset: "inner" }],
  p01_kerr: ["p01_gravity", { preset: "kerr_orbits" }],
  p01_pn: ["p01_gravity", { preset: "pn_inspiral" }],
  p02_slit: ["p02_quantum", { preset: "double_slit" }],
  p03_maxwell: ["p03_molecules", { preset: "maxwell" }],
  p03_piston: ["p03_molecules", { preset: "piston" }],
  p04_cyl: ["p04_fluids", { preset: "cylinder_re20", params: { nx: "256" } }],
};
const b = await browser();
fs.mkdirSync("/pw/shots", { recursive: true });
const clearToasts = (page) => page.evaluate(() => { for (const t of [...document.querySelectorAll(".toast")]) t.parentNode.removeChild(t); });
for (const name of (process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(CASES))) {
  const [viz, body] = CASES[name];
  const id = await newRun(viz, body);
  const { page, ctx, logs } = await openRun(b, id, { w: 1600, h: 1000 });
  await play(page);
  await sleep(2500);
  const buttons = await page.$$eval(".pg-buttons button", (bs) => bs.map((x) => ({ text: x.textContent, disabled: x.disabled, title: x.title })));
  const rows = [];
  for (let i = 0; i < buttons.length; i++) {
    const before = await page.$$eval(".pg-obj .grow", (xs) => xs.map((x) => x.textContent));
    await clearToasts(page);
    const btn = (await page.$$(".pg-buttons button"))[i];
    const dis = await btn.isDisabled();
    const t0 = Date.now();
    if (!dis) await btn.click();
    // the object appears when the run answers: wait for the list to change or a toast, up to 30 s
    await page.waitForFunction((n) => document.querySelectorAll(".pg-obj").length !== n || document.querySelector(".toast"), before.length, { timeout: 30000 }).catch(() => {});
    const answered = (Date.now() - t0) / 1000;
    await sleep(2500);
    const mid = await page.$$eval(".pg-obj .grow", (xs) => xs.map((x) => x.textContent));
    const toast = await page.$$eval(".toast", (ts) => ts.map((t) => t.textContent));
    if (toast.length && !fs.existsSync(`/pw/shots/palette_${name}_toast.jpg`)) await shot(page, `/pw/shots/palette_${name}_toast.jpg`);
    await sleep(3500);
    const after = await page.$$eval(".pg-obj .grow", (xs) => xs.map((x) => x.textContent));
    const status = await page.textContent("#status");
    rows.push({ button: buttons[i].text, disabled: dis, title: buttons[i].title, answered_s: answered, n_before: before.length, n_2s: mid.length, n_6s: after.length,
                added: mid.filter((x) => !before.includes(x)), vanished_by_6s: before.concat(mid).filter((x) => !after.includes(x)), toast, status });
  }
  await shot(page, `/pw/shots/palette_${name}_end.jpg`);
  const r = { case: name, run: id, rows, console: logs.slice(0, 8) };
  console.log(JSON.stringify(r));
  fs.appendFileSync("/pw/out_palette.jsonl", JSON.stringify(r) + "\n");
  await ctx.close();
  await post(`/api/runs/${id}/stop`, {});
}
await b.close();
