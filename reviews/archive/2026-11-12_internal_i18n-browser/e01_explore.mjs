// e01: what the run page holds (panels, controls) for one demo and one playground, EN; screenshots
import { browser, newPage, post, get, sleep, startRun, waitPlayer, shot, setLog, log, base, openPanel } from "./r_lib.mjs";
setLog("e01_explore");
const br = await browser();
const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
for (const [viz, preset] of [["v02_double_slit", null], ["p01_gravity", "kerr_orbits"]]) {
  const r = await startRun({ viz, seed: 3, ...(preset ? { preset } : {}) });
  log({ viz, r });
  const page = await newPage(ctx, viz);
  await page.goto(`${base}/run?id=${r.id}&lang=en`);
  await waitPlayer(page);
  await sleep(1500);
  await openPanel(page, /./);
  await sleep(800);
  const dom = await page.evaluate(() => {
    const d = (box) => [...box.querySelectorAll(".panel")].map((p) => ({ h: p.querySelector("h4")?.textContent, ctrls: [...p.querySelectorAll("button, input, select, a, details > summary")].slice(0, 40).map((e) => `${e.tagName.toLowerCase()}${e.type ? "[" + e.type + "]" : ""}${e.className ? "." + e.className : ""}:${(e.textContent || e.value || e.title || "").trim().slice(0, 40)}`) }));
    return { left: d(document.getElementById("left")), right: d(document.getElementById("right")) };
  });
  log({ viz, dom });
  await shot(page, `e01_${viz}_en`, true);
  await post(`/api/runs/${r.id}/stop`);
  await page.close();
}
await br.close();
