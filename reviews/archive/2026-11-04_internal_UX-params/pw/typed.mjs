// The user's path for a typed number outside the schema's range: the catalogue's form and the live control.
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8563";
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const out = [];
async function toasts(page) { return page.$$eval(".toast", (xs) => xs.map((x) => x.textContent)); }
async function catalogue(title, label, value, name) {
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  await page.goto(base + "/"); await page.waitForTimeout(1500);
  const card = page.locator(".card", { has: page.locator("h3", { hasText: title }) }).first();
  await card.locator("button", { hasText: "Параметры" }).click();
  await page.waitForTimeout(300);
  const row = card.locator(".field", { has: page.locator("label", { hasText: label }) }).first();
  const inp = row.locator("input");
  await inp.fill(String(value));
  await inp.dispatchEvent("change");
  await card.locator("button", { hasText: "Запустить" }).click();
  await page.waitForTimeout(2500);
  const rec = { name, path: "catalogue form", url: page.url(), toasts: await toasts(page) };
  await page.screenshot({ path: `shots/${name}.png` });
  out.push(rec); console.log(JSON.stringify(rec));
  await page.close();
}
async function live(viz, label, value, name) {
  const r = await (await fetch(base + "/api/runs", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ viz, seed: 1 }) })).json();
  const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
  await page.goto(base + "/run?id=" + r.id); await page.waitForTimeout(5000);
  const ctl = page.locator(".ctl", { has: page.locator("label", { hasText: label }) }).first();
  const inp = ctl.locator("input[type=number]");
  await inp.fill(String(value));
  await inp.press("Enter");
  let seen = new Set();
  for (let i = 0; i < 10; i++) { for (const t of await toasts(page)) seen.add(t); await page.waitForTimeout(300); }
  const rec = { name, path: "live control", id: r.id, toasts: [...seen], after: await inp.inputValue() };
  await page.screenshot({ path: `shots/${name}.png` });
  out.push(rec); console.log(JSON.stringify(rec));
  await page.close();
  await fetch(base + `/api/runs/${r.id}/stop`, { method: "POST" });
}
await catalogue("Оптический стол", "Длина волны λ", 2000, "P2_catalogue_typed_above_max");
await catalogue("Оптический стол", "Длина волны λ", "", "P2_catalogue_field_cleared");
await live("v05_optics_bench", "Длина волны λ", 2000, "P2_live_typed_above_max");
fs.writeFileSync("typed_out.json", JSON.stringify(out, null, 1));
await browser.close();
