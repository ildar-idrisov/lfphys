import { chromium } from "playwright";
const base = "http://127.0.0.1:8501";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [], out = {};
const S = (page, f, a) => page.evaluate(f, a);
async function open(viz, preset, params = {}) {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
  page.on("pageerror", (e) => errs.push(`${viz}/${preset} pageerror: ${e.stack}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`${viz}/${preset} ${m.text()}`); });
  const r = await post("/api/runs", { viz, preset, params, seed: 3 });
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(6000);
  return [page, r.id];
}
const panelText = (page, re) => S(page, (src) => [...document.querySelectorAll(".panel")].map((p) => p.innerText).filter((t) => new RegExp(src).test(t)).map((t) => t.slice(0, 400)), re.source);
// v11: early (screen empty), end, then scrolled back
{
  const [page, id] = await open("v11_double_slit_2d", "narrow");
  await post(`/api/runs/${id}/command`, { cmd: "play", args: {} });
  await page.waitForTimeout(9000);
  await page.screenshot({ path: "b3r_v11_early.png", timeout: 120000 });
  out.v11_early = await panelText(page, /ЭКРАН/);
  await page.waitForTimeout(150000);
  await page.screenshot({ path: "b3r_v11_end.png", timeout: 120000 });
  out.v11_end = await panelText(page, /ЭКРАН|ОПЫТ/);
  out.v11_window = await S(page, () => { const c = document.querySelector(".slicewin .sw-canvas"); return [c.clientWidth, c.clientHeight, document.querySelector(".s3d-windows").clientWidth]; });
  await S(page, () => { const tl = document.getElementById("timeline"); tl.value = String(Math.round(Number(tl.max) * 0.45)); tl.dispatchEvent(new Event("input")); });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: "b3r_v11_back.png", timeout: 120000 });
  out.v11_back = await panelText(page, /ЭКРАН/);
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
// v10: city device panel; geometry mode readout
{
  const [page, id] = await open("v10_fast_observer", "city", { res: "s" });
  await post(`/api/runs/${id}/command`, { cmd: "play", args: {} });
  await page.waitForTimeout(8000);
  out.v10_dev = await panelText(page, /ГДЕ СЧИТАЛОСЬ/);
  await post(`/api/runs/${id}/command`, { cmd: "set", args: { values: { image: "geometry" } } });
  await page.waitForTimeout(5000);
  const c = page.locator(".imgwin .sw-canvas"); const b = await c.boundingBox();
  await page.mouse.move(b.x + b.width * 0.5, b.y + b.height * 0.45); await page.waitForTimeout(200);
  await page.mouse.move(b.x + b.width * 0.52, b.y + b.height * 0.45); await page.waitForTimeout(400);
  out.v10_readout = await S(page, () => document.querySelector(".imgwin .sw-readout").textContent);
  out.v10_window = await S(page, () => { const c = document.querySelector(".imgwin .sw-canvas"); return [c.clientWidth, c.clientHeight]; });
  await page.screenshot({ path: "b3r_v10_city_geometry.png", timeout: 120000 });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
console.log(JSON.stringify(out, null, 1));
console.log(errs.length ? errs.join("\n") : "no page errors");
await browser.close();
