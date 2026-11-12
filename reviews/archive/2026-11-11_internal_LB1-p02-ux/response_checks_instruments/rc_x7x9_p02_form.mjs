// [response] rc_x7x9: the sweep form of p02 (double slit, the plane) in Chromium on the processor's PRIVATE server
// (port given, never 8479). X9: «Что менять» names each unit once and does not offer the law hidden in the plane (n3).
// X7: the duration's unit and default follow the world (a femtosecond world: not «1 с»); after a start the estimate is
// asked anew. Prints one JSON line per check; a screenshot of the form goes to /pw/shots_p02.
import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
const port = process.argv[2] || "8611", base = `http://127.0.0.1:${port}`;
mkdirSync("/pw/shots_p02", { recursive: true });
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const check = (name, ok, info = {}) => console.log(JSON.stringify({ check: name, ok: !!ok, ...info }));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const { id } = await post("/api/runs", { viz: "p02_quantum", preset: "double_slit", seed: 3 });
for (let i = 0; i < 300 && (await get(`/api/runs/${id}`)).state !== "running"; i++) await sleep(200);
await post(`/api/runs/${id}/command`, { cmd: "play" }); await sleep(5000); await post(`/api/runs/${id}/command`, { cmd: "pause" }); await sleep(1500);
const page = await br.newPage({ viewport: { width: 1600, height: 1000 } });
const errs = []; page.on("pageerror", (e) => errs.push(e.message));
await page.goto(`${base}/run?id=${id}`);
await page.waitForFunction(() => window.__lfPlayer && document.querySelector(".in-panel") && document.querySelector(".in-panel").style.display !== "none", null, { timeout: 120000 });
await page.evaluate(() => { document.querySelector(".in-sweep-box").open = true; });
await page.waitForSelector(".in-sweep select", { timeout: 30000 }); await sleep(800);
const opts = await page.$$eval(".in-sweep select:first-of-type option", (os) => os.map((o) => [o.value, o.textContent]));
const viz = await get("/api/viz/p02_quantum");
const n3 = viz.schema.params.find((p) => p.id === "n3");
const doubled = opts.filter(([, t]) => { const m = /, ([^,]+)$/.exec(t); return m && t.slice(0, -m[0].length).includes(", " + m[1]); });
check("X9 no unit twice", doubled.length === 0, { doubled, sample: opts.slice(0, 8).map((o) => o[1]) });
check("X9 the law hidden in the plane (n3) not offered", !!(n3 && n3.show_if) && !opts.some(([v]) => v === "law:n3"), { n3_show_if: n3 && n3.show_if });
const ctl = page.locator(".in-sweep .ctl", { hasText: "Сколько считать" });
const lab = await ctl.textContent(), dv = await ctl.locator("input").inputValue();
const st = (await get(`/api/runs/${id}`));
check("X7 the duration in the world's scale", !/Сколько считать, с$/.test(lab.trim()) || Number(dv.replace(",", ".")) < 1e-3, { lab, dv, speed: st.speed });
await page.locator(".in-sweep-box").screenshot({ path: "/pw/shots_p02/p02_sweep_form.png" });
check("no page errors", !errs.length, { errs });
await br.close();
