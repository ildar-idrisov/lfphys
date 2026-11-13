// w05b: in Russian, «Длина волны, нм» of v02 typed as 650,5 (decimal comma): what the world applies
import { browser, newPage, post, del, sleep, startRun, waitPlayer, shot, setLog, log, base } from "./r_lib.mjs";
setLog("w05b_comma_applied");
const br = await browser();
const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 }, locale: "ru-RU" });
const page = await newPage(ctx, "comma_v02");
const r = await startRun({ viz: "v02_double_slit", seed: 3 });
await page.goto(`${base}/run?id=${r.id}&lang=ru`);
await waitPlayer(page); await sleep(1500);
const lab = await page.evaluate(() => { const i = [...document.querySelectorAll("#left input[type=number]")].find((e) => e.value === "632.8"); i.id = "rv-lam"; return i.closest("div").parentElement.textContent.slice(0, 60); });
await page.click("#rv-lam", { clickCount: 3 });
await page.keyboard.type("650,5");
await page.keyboard.press("Enter");
await sleep(4000);
const after = await page.evaluate(() => ({ field: document.getElementById("rv-lam")?.value, errs: [...document.querySelectorAll(".ctl-err, .field-err")].map((e) => e.textContent).filter(Boolean),
  events: [...document.querySelectorAll(".events .ev")].slice(0, 4).map((e) => e.textContent.slice(0, 160)), topbar: document.getElementById("scene").textContent }));
log({ lab, after });
await shot(page, "w05b_comma_applied_v02_ru");
await ctx.close();
await post(`/api/runs/${r.id}/stop`); await sleep(1500); await del(`/api/runs/${r.id}`);
await br.close();
