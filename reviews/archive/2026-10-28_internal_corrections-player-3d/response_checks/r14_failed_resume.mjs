// Response to the C1 review, check for C1-14 in the page: a suspended v04 run whose record's header was given a parameter
// the code does not know (as after a rename; done with the server stopped, then restarted). ⏺ → the rebuild fails →
// what the player and the catalogue show; the header restored (server stopped again) → ⏺ resumes.
// Usage: RUN=<id> PHASE=fail|retry node r14_failed_resume.mjs (own server 127.0.0.1:8501). Output: out/r14_failed_resume.txt
import { chromium } from "playwright";
import fs from "fs";
const base = "http://127.0.0.1:8501", run = process.env.RUN, phase = process.env.PHASE || "fail";
const OUT = process.env.OUT || "/pw/c1proc_out";
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--disable-accelerated-2d-canvas"] });
const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });
await page.goto(`${base}/run?id=${run}`);
await page.waitForTimeout(4000);
const ui = () => page.evaluate(() => ({ rec: document.getElementById("rec").textContent, recDisabled: document.getElementById("rec").disabled,
  status: document.getElementById("status").textContent, statusTitle: document.getElementById("status").title.slice(0, 160),
  busy: document.getElementById("busy").style.display !== "none" ? document.getElementById("busy").textContent : "" }));
const lines = [`[${phase}] before ⏺: ${JSON.stringify(await ui())}`];
await page.click("#rec");
await page.waitForTimeout(phase === "fail" ? 6000 : 20000);
lines.push(`[${phase}] after ⏺: ${JSON.stringify(await ui())}`);
const cat = await browser.newPage();
await cat.goto(base + "/");
await cat.waitForTimeout(2500);
lines.push(`[${phase}] catalogue row: ${await cat.evaluate((id) => { const tr = [...document.querySelectorAll("tr")].find((r) => r.textContent.includes(id)); return tr ? tr.children[0].textContent : "(none)"; }, run)}`);
if (phase === "retry") { await page.click("#rec"); await page.waitForTimeout(1000); }
fs.appendFileSync(`${OUT}/r14_failed_resume.txt`, lines.join("\n") + "\n");
console.log(lines.join("\n"));
await browser.close();
