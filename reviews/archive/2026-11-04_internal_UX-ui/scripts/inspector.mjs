// U-edit: editing and removing objects in the browser while the world records (p01 «Солнце … Юпитер»): select a body
// in the list, change a field and Tab to the next one (does the focus survive the scene message that follows?),
// remove a body with ✕, change a position with Enter.
import { browser, newRun, openRun, play, sleep, post, shot } from "./common.mjs";
import fs from "fs";
const b = await browser();
const id = await newRun("p01_gravity", { preset: "inner" });
const { page, ctx } = await openRun(b, id);
await play(page);
await sleep(3000);
const out = {};
const rowOf = async (label) => page.evaluateHandle((l) => [...document.querySelectorAll(".pg-obj")].find((r) => r.querySelector(".grow").textContent === l), label);
// select the Earth
await (await rowOf("Земля")).asElement().click();
await sleep(800);
out.inspector_title = await page.evaluate(() => { const i = [...document.querySelectorAll(".panel")].find((p) => /Инспектор/.test(p.querySelector("h4").textContent)); return i ? i.querySelector(".ctl label").textContent + " " + i.querySelector(".ctl input").value : null; });
// the first number field (mass), type and Tab to the next (radius)
const inspector = await page.evaluateHandle(() => [...document.querySelectorAll(".panel")].find((p) => /Инспектор/.test(p.querySelector("h4").textContent)));
const nums = await inspector.$$("input[type=number]");
await nums[0].click({ clickCount: 3 });
await page.keyboard.type("2");
await page.keyboard.press("Tab");
const focusRight = await page.evaluate(() => ({ tag: document.activeElement.tagName, type: document.activeElement.type, label: (document.activeElement.closest(".ctl") || {}).textContent }));
await sleep(1500);
out.focus_after_tab_immediately = focusRight;
out.focus_after_scene_message = await page.evaluate(() => ({ tag: document.activeElement.tagName, type: document.activeElement.type, inInspector: !!document.activeElement.closest(".panel") && /Инспектор/.test(document.activeElement.closest(".panel").querySelector("h4").textContent) }));
await page.keyboard.type("5");
await sleep(300);
out.typed_5_went_to = await page.evaluate(() => ({ tag: document.activeElement.tagName, value: document.activeElement.value }));
out.events_tail = await page.$$eval(".events .ev", (es) => es.slice(-3).map((e) => e.textContent.slice(0, 120)));
// remove Mars while recording
const n0 = await page.$$eval(".pg-obj", (r) => r.length);
const mars = (await rowOf("Марс")).asElement();
const t0 = Date.now();
await (await mars.$("button[title^='Удалить']")).click();
await page.waitForFunction((n) => document.querySelectorAll(".pg-obj").length !== n, n0, { timeout: 30000 }).catch(() => {});
out.remove = { before: n0, after: await page.$$eval(".pg-obj", (r) => r.length), s: (Date.now() - t0) / 1000 };
// the scene list's scroll: a long scene (20 test bodies), scroll the list down, select the last one
for (let i = 0; i < 20; i++) await post(`/api/runs/${id}/command`, { cmd: "scene", args: { op: "add", type: "test", values: { x: 2 + 0.1 * i } } });
await sleep(2500);
const list = await page.$(".pg-list");
const lb = await list.boundingBox();
await page.mouse.move(lb.x + lb.width / 2, lb.y + lb.height / 2);
await page.mouse.wheel(0, 800); await sleep(400);
const st0 = await page.$eval(".pg-list", (e) => e.scrollTop);
const last = (await page.$$(".pg-obj")).at(-1);
await last.click();
await sleep(800);
out.list_scroll = { before_select: st0, after_select: await page.$eval(".pg-list", (e) => e.scrollTop), selected: await page.$eval(".pg-obj.sel .grow", (e) => e.textContent).catch(() => null) };
await post(`/api/runs/${id}/command`, { cmd: "pause" }); await sleep(800);
try { await shot(page, "/pw/shots/inspector_p01.jpg", { timeout: 90000 }); } catch (e) { out.shot_error = String(e).slice(0, 80); }
console.log(JSON.stringify(out));
fs.writeFileSync("/pw/out_inspector.json", JSON.stringify(out, null, 1));
await ctx.close(); await post(`/api/runs/${id}/stop`, {});
await b.close();
