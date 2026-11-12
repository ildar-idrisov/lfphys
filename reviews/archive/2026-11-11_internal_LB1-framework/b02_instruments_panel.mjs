// b02: the «Приборы» panel as the owner uses it (Chromium, PRIVATE server; never 8479), fixture p97_osc.
// The owner complained before about views jumping back; here: does the panel keep focus, folded groups and the
// column's scroll when a quantity is ticked; does the sweep form keep what was typed when it is folded and opened
// again; does a running sweep's result block keep the column's scroll and its nodes; what the result says about the
// base moment and the sampling; what «Сейчас» says for an object's position.
// Run: docker run --rm --init --shm-size=2g --network host -v <scratch>/lbrf/pw:/pw -v <review>:/out -w /pw
//      mcr.microsoft.com/playwright:v1.58.2-jammy sh -c "cp /out/b02_instruments_panel.mjs /pw/ && node /pw/b02_instruments_panel.mjs 8601"
import { chromium } from "playwright";

const port = process.argv[2] || "8601";
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cmd = (id, c, a) => post(`/api/runs/${id}/command`, { cmd: c, args: a || {} });
const results = [];
const check = (name, ok, detail = {}) => { results.push({ name, ok: !!ok, ...detail }); console.log(JSON.stringify({ name, ok: !!ok, ...detail })); };

const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const r = await post("/api/runs", { viz: "p97_osc", preset: "two", seed: 5 });
const id = r.id;
for (let i = 0; i < 100 && (await get(`/api/runs/${id}`)).state !== "running"; i++) await sleep(200);
for (let i = 0; i < 8; i++) { await cmd(id, "scene", { op: "add", type: "osc", values: { x: 0.1 * i, v: 0.2 } }); await sleep(150); }
await cmd(id, "play"); await sleep(3000); await cmd(id, "pause"); await sleep(500);  // played: the estimate from stepped frames is ~1000x too high (c08)
const page = await br.newPage({ viewport: { width: 1280, height: 800 } });
const errs = [];
page.on("pageerror", (e) => errs.push(e.message));
await page.goto(`${base}/run?id=${id}`);
await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && document.querySelector(".in-panel") && document.querySelector(".in-panel").style.display !== "none", null, { timeout: 120000 });
await sleep(1500);
// the column that scrolls
const scroller = () => page.evaluate(() => {
  let e = document.querySelector(".in-panel");
  while (e && e !== document.body) { const s = getComputedStyle(e); if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight) return e.id || e.className; e = e.parentElement; }
  return null;
});
const scrollInfo = () => page.evaluate(() => {
  let e = document.querySelector(".in-panel");
  while (e && e !== document.body) { const s = getComputedStyle(e); if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight) return { top: e.scrollTop, h: e.scrollHeight }; e = e.parentElement; }
  return { top: document.scrollingElement.scrollTop, h: document.scrollingElement.scrollHeight };
});
const setScroll = (y) => page.evaluate((y) => {
  let e = document.querySelector(".in-panel");
  while (e && e !== document.body) { const s = getComputedStyle(e); if (/(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight) { e.scrollTop = y; return e.scrollTop; } e = e.parentElement; }
  document.scrollingElement.scrollTop = y; return document.scrollingElement.scrollTop;
}, y);
console.log(JSON.stringify({ scroller: await scroller() }));

// 1. fold the group «Мир», tick a quantity of «Осцилляторы» with the keyboard
await page.evaluate(() => { const g = [...document.querySelectorAll(".in-panel details.in-group")].find((d) => d.querySelector("summary").textContent === "Мир"); g.open = false; });
const boxes = await page.$$(".in-panel .in-group input[type=checkbox]");
const target = boxes[boxes.length - 2];
const title0 = await target.evaluate((b) => b.closest("label").title);
await target.focus();
await page.keyboard.press("Space");
await sleep(500);
const after1 = await page.evaluate(() => {
  const a = document.activeElement, g = [...document.querySelectorAll(".in-panel details.in-group")].find((d) => d.querySelector("summary").textContent === "Мир");
  return { active: a ? `${a.tagName}${a.closest("label") ? " " + a.closest("label").title : ""}` : null, worldOpen: g ? g.open : null };
});
check("ticking a quantity with the keyboard keeps the focus on it", after1.active === `INPUT ${title0}`, { before: title0, after: after1.active });
check("ticking a quantity keeps a folded group folded", after1.worldOpen === false, after1);

// 2. the column's scroll when a quantity is ticked with the mouse
await setScroll(10000);
const s0 = await scrollInfo();
const boxes2 = await page.$$(".in-panel .in-group input[type=checkbox]");
await boxes2[boxes2.length - 3].click();
await sleep(500);
const s1 = await scrollInfo();
check("ticking a quantity keeps the column's scroll", Math.abs(s1.top - s0.top) < 2, { before: s0, after: s1 });

// 3. the sweep form keeps what was typed when folded and opened again
await page.evaluate(() => { const d = document.querySelector(".in-sweep-box"); d.open = true; });
await sleep(1200);
await page.fill(".in-sweep input[placeholder^='например']", "1; 2; 3");
await page.evaluate(() => { const d = document.querySelector(".in-sweep-box"); d.open = false; });
await sleep(300);
await page.evaluate(() => { const d = document.querySelector(".in-sweep-box"); d.open = true; });
await sleep(1200);
const kept = await page.inputValue(".in-sweep input[placeholder^='например']");
check("the sweep form keeps the values typed after folding and opening it", kept === "1; 2; 3", { kept });

// 4. «Сейчас» for an object's position: the stored parameter or where the object is?
const opts = await page.$$eval(".in-sweep select:first-of-type option", (os) => os.map((o) => [o.value, o.textContent]));
const xKey = opts.find(([v]) => /^obj:o1:x$/.test(v));
await page.selectOption(".in-sweep select >> nth=0", xKey[0]);
await sleep(300);
const cur = await page.evaluate(() => [...document.querySelectorAll(".in-sweep .help")].map((e) => e.textContent).find((t) => t.startsWith("Сейчас")));
const where = await page.evaluate(() => { const m = window.lfInstruments.state(); return m; });
const ser = await get(`/api/runs/${id}/series?ids=o1.x`);
check("«Сейчас» for the position of o1 shows where it is (not the stored parameter)", cur && Math.abs(parseFloat(cur.replace("Сейчас: ", "").replace(",", ".")) - ser.values["o1.x"].at(-1)) < 1e-3,
  { shown: cur, position_now: ser.values["o1.x"].at(-1) });

// 5. a running sweep: the column's scroll and the result block's nodes across its polls; what the result says
await page.selectOption(".in-sweep select >> nth=0", "law:k");
const vals = Array.from({ length: 40 }, (_, i) => (1 + i * 2).toString()).join("; ");
await page.fill(".in-sweep input[placeholder^='например']", vals);
await page.fill(".in-sweep .ctl:has(label:text-matches('Сколько считать')) input", "300");
await page.selectOption(".in-sweep .ctl:has(label:text('Что взять')) select", "max");
await page.click(".in-sweep button:text('Оценить')");
await sleep(1500);
const estText = await page.textContent(".in-sweep .in-est");
console.log(JSON.stringify({ estimate: estText }));
await page.click(".in-sweep button:text('▶ Запустить свип')", { timeout: 5000 });
await sleep(1200);
await setScroll(10000);
const before = await scrollInfo();
await page.evaluate(() => { window.__t = document.querySelector(".in-sres table"); window.__cv = document.querySelector(".in-sres canvas"); });
await sleep(1500);  // two polls (700 ms)
const after = await scrollInfo();
const same = await page.evaluate(() => ({ table: window.__t === document.querySelector(".in-sres table"), canvas: window.__cv === document.querySelector(".in-sres canvas"),
  state: document.querySelector(".in-sres .in-sh") ? document.querySelector(".in-sres .in-sh").textContent : null }));
check("a running sweep keeps the column's scroll across its polls", Math.abs(after.top - before.top) < 2, { before, after, state: same.state });
check("a running sweep updates its table in place (the nodes kept)", same.table && same.canvas, same);
// wait for the end, then what the result states
let res = null;
for (let i = 0; i < 300; i++) { const l = await get(`/api/runs/${id}/sweeps`); res = l.at(-1); if (!res.active && !["starting", "running"].includes(res.state)) break; await sleep(500); }
await sleep(1500);
const head = await page.evaluate(() => [...document.querySelectorAll(".in-sres .help")].map((e) => e.textContent));
const csv = await (await fetch(`${base}/api/runs/${id}/sweeps/${res.n}?format=csv`)).text();
check("the result states the base moment", head.some((t) => /от t =/.test(t)), { head, estimate: estText });
check("the result states the sampling (how many readings a «максимум» is taken over)", head.some((t) => /замер/.test(t)), { head });
check("the CSV of the table states the base moment and the sampling", /t\s*=|замер|n_samples/.test(csv.split("\n")[0]), { first_line: csv.split("\n")[0] });
check("no page errors", !errs.length, { errs });
await page.screenshot({ path: "/out/b02_instruments_panel_end.png" });
await br.close();
const failed = results.filter((x) => !x.ok).length;
console.log(failed ? `${failed} failed` : "all passed");
