// S03 worksheet: text EN/RU (teacher on), screenshot, PDF A4 page count
import { launch, startStatic, sleep, SITE, SRV, watchErrors } from "./lib.mjs";
await startStatic();
const br = await launch();
for (const [where, base] of [["site", SITE], ["srv", SRV]]) for (const lang of ["en", "ru"]) {
  const ctx = await br.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage(); const errs = []; watchErrors(page, errs);
  await page.goto(where === "site" ? `${base}/worksheet.html?demo=s03_projectile&lang=${lang}&teacher=1` : `${base}/worksheet?demo=s03_projectile&lang=${lang}&teacher=1`);
  await page.waitForSelector("body[data-ready='1']", { timeout: 30000 });
  await sleep(300);
  const txt = await page.$eval("#ws", (e) => e.innerText);
  if (where === "site") {
    console.log(`==== ${lang}\n${txt}\n`);
    await page.screenshot({ path: `/shots/ws_${lang}.png`, fullPage: true });
    await page.emulateMedia({ media: "print" });
    const pdf = await page.pdf({ path: `/shots/ws_${lang}.pdf`, format: "A4" });
    console.log(JSON.stringify({ lang, pdfBytes: pdf.length }));
  } else console.log(JSON.stringify({ where, lang, len: txt.length, errs }));
  console.log(JSON.stringify({ where, lang, errs }));
  await ctx.close();
}
await br.close(); process.exit(0);
