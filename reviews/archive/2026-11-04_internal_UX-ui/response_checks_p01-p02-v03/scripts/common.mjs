// Shared helpers for the UX-ui audit (private server only; never the shared one on 8479).
import { chromium } from "playwright";
export const port = process.env.PORT || "8573";
export const base = `http://127.0.0.1:${port}`;
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
export const post = async (u, b) => { const r = await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) }); return r.json(); };
export const get = async (u) => (await fetch(base + u)).json();
export async function browser() {
  return chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
}
export async function newRun(viz, body = {}) { const r = await post("/api/runs", { viz, ...body }); if (!r.id) throw new Error(JSON.stringify(r)); return r.id; }
export async function openRun(b, id, { w = 1600, h = 1000 } = {}) {
  const ctx = await b.newContext({ viewport: { width: w, height: h }, acceptDownloads: true });
  const page = await ctx.newPage();
  const logs = [];
  page.on("console", (m) => { if (m.type() === "error" || m.type() === "warning") logs.push(m.type() + ": " + m.text().slice(0, 400)); });
  page.on("pageerror", (e) => logs.push("pageerror: " + String(e).slice(0, 400)));
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка/.test(document.getElementById("status").textContent), null, { timeout: 120000 });
  return { page, ctx, logs };
}
export async function play(page) {
  const txt = await page.textContent("#rec");
  if (!/запись/.test(txt)) await page.click("#rec");
  await page.waitForFunction(() => /запись идёт/.test(document.getElementById("status").textContent), null, { timeout: 60000 });
}
export async function pause(page) {
  const txt = await page.textContent("#rec");
  if (/запись/.test(txt)) await page.click("#rec");
}
export async function toasts(page) { return page.$$eval(".toast", (ts) => ts.map((t) => t.textContent)); }
export async function shot(page, path, opts = {}) { await page.screenshot({ path, type: "jpeg", quality: 70, ...opts }); }
