// Agent H (UX-params / UX-ui, v-worlds): the user's path in the catalogue — open a world's «Параметры…», change
// fields, «▶ Запустить» — and what the page shows: the run page (notices, events, checks) or the refusal on the form.
// usage: node forms.mjs <port> <cases.json> <out.json>
import { chromium } from "playwright";
import fs from "fs";
const base = `http://127.0.0.1:${process.argv[2]}`;
const cases = JSON.parse(fs.readFileSync(process.argv[3]));
const out = [];
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const c of cases) {
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const errs = [];
  page.on("pageerror", (e) => errs.push("pageerror: " + String(e.stack || e).slice(0, 300)));
  const rec = { name: c.name };
  try {
    await page.goto(base + "/");
    await page.waitForSelector(".card h3");
    const card = page.locator(".card", { has: page.locator("h3", { hasText: c.title }) }).first();
    if (c.preset) await card.locator("select").first().selectOption(c.preset);
    await card.getByRole("button", { name: "Параметры…" }).click();
    for (const [pid, val] of c.set || []) {
      const f = card.locator(`.field[data-pid="${pid}"]`);
      if (await f.locator("select").count()) await f.locator("select").selectOption(String(val));
      else if (typeof val === "boolean") await f.locator("input").setChecked(val);
      else { await f.locator("input").fill(String(val)); await f.locator("input").press("Tab"); }
      await page.waitForTimeout(150);
    }
    if (c.options) {  // the options a select offers now (option-level show_if)
      rec.options = {};
      for (const pid of c.options) {
        rec.options[pid] = await card.locator(`.field[data-pid="${pid}"] select option`).evaluateAll(
          (os) => os.filter((o) => !o.hidden && !o.disabled && o.style.display !== "none").map((o) => o.textContent));
      }
    }
    if (c.formShot) {
      await card.scrollIntoViewIfNeeded();
      await card.screenshot({ path: `shots/${c.name}_form.png` });
    }
    if (c.run !== false) {
      await card.getByRole("button", { name: "▶ Запустить" }).click();
      try { await page.waitForURL(/\/run\?id=/, { timeout: c.buildMs || 15000 }); } catch (e) { /* refused on the form */ }
      if (page.url().includes("/run?id=")) {
        rec.id = page.url().split("id=")[1];
        await page.waitForTimeout(c.wait || 6000);
        for (const [cmd, args, w] of c.cmds || []) {
          await page.evaluate(async ([id, cmd, args]) => fetch(`/api/runs/${id}/command`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cmd, args }) }), [rec.id, cmd, args]);
          await page.waitForTimeout(w || 2000);
        }
        rec.events = await page.evaluate(() => { const b = document.querySelector(".events"); return b ? b.innerText.slice(0, 2500) : null; });
        rec.checks = await page.evaluate(() => { const b = document.querySelector(".checks"); return b ? b.innerText.slice(0, 3000) : null; });
        rec.toasts = await page.$$eval(".toast", (xs) => xs.map((x) => x.textContent));
        await page.screenshot({ path: `shots/${c.name}.png` });
      } else {
        await card.scrollIntoViewIfNeeded();
        rec.refusal = await card.locator(".start-err").innerText();
        await card.screenshot({ path: `shots/${c.name}.png` });
      }
    }
  } catch (e) { rec.scriptError = String(e).slice(0, 400); }
  rec.pageErrors = errs;
  out.push(rec);
  fs.writeFileSync(process.argv[4], JSON.stringify(out, null, 1));
  console.log(JSON.stringify(rec).slice(0, 700));
  await page.close();
}
await browser.close();
