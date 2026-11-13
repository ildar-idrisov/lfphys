import { chromium } from "playwright";
const br = await chromium.launch();
const ctx = await br.newContext({ locale: "ru-RU", extraHTTPHeaders: { "Accept-Language": "ru-RU,ru;q=0.9" } });
const p = await ctx.newPage();
await p.goto(process.argv[2] + "run.html?rec=u32_double_slit/young");
await p.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 60000 });
console.log(JSON.stringify(await p.evaluate(() => ({ lang: document.documentElement.lang, nav: navigator.language, head: document.body.innerText.slice(0, 120) }))));
await br.close();
