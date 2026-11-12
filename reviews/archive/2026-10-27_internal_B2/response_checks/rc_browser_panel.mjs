// SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
// Response check: the v09 result panel at t = 0 and at the closure (found while processing: the result block was passed as a third argument of panel() and lost).
import { chromium } from "playwright";
const base = "http://127.0.0.1:8499";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
const errs = []; page.on("pageerror", (e) => errs.push(e.stack));
const r = await post("/api/runs", { viz: "v09_thomas_3d", preset: "thomas", seed: 3 });
await page.goto(base + "/run?id=" + r.id); await page.waitForTimeout(7000);
const panelText = () => page.evaluate(() => [...document.querySelectorAll("*")].filter((e) => e.children.length < 40 && /Манёвр и голономия/i.test(e.firstChild?.textContent || "")).map((e) => e.parentElement.textContent.slice(0, 600)));
console.log("T0:", JSON.stringify(await page.evaluate(() => { const h = [...document.querySelectorAll(".panel h4")].find((x) => /Манёвр и голономия/i.test(x.textContent)); return h ? h.parentElement.textContent.slice(0, 700) : "no panel"; })));
await post(`/api/runs/${r.id}/command`, { cmd: "speed", args: { value: 1e12 } }); await post(`/api/runs/${r.id}/command`, { cmd: "play", args: {} });
await page.waitForTimeout(5000);
console.log("END:", JSON.stringify(await page.evaluate(() => { const h = [...document.querySelectorAll(".panel h4")].find((x) => /Манёвр и голономия/i.test(x.textContent)); return h ? h.parentElement.textContent.slice(0, 900) : "no panel"; })));
console.log(errs.length ? errs.join("\n") : "no page errors");
await post(`/api/runs/${r.id}/stop`, {}); await browser.close();
