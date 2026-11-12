// Agent H: open a recorded run and show the panel holding a given text (scrolled into view), with a screenshot.
// usage: node stats.mjs <port> <run id> <text> <shot name>
import { chromium } from "playwright";
const [port, id, text, name] = process.argv.slice(2);
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
await page.goto(`http://127.0.0.1:${port}/run?id=${id}`);
await page.waitForTimeout(7000);
const loc = page.getByText(text, { exact: false }).first();
const found = await loc.count();
let shown = null;
if (found) {
  await loc.scrollIntoViewIfNeeded();
  shown = await loc.evaluate((e) => (e.closest("section, details, .panel, div") || e).innerText.slice(0, 600));
}
await page.screenshot({ path: `shots/${name}.png` });
console.log(JSON.stringify({ found, shown }));
await browser.close();
