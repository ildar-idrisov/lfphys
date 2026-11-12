// The look of a world's 3-D view before ("orig") and after ("new") the processing, on the same paused state: the view as
// opened, and the same camera with the slice planes hidden (the volume alone). For the review's A1, A2, A5, A10.
// usage: node look_ab.mjs <port> <orig|new> <viz> <preset|-> <tag> [playMs] [outDir] [paramsJSON]
import fs from "node:fs";
import { launch, startRun, openPage, shot, diag, settle, sleep } from "./lib.mjs";
const [port, variant, viz, preset, tag, playMsS, outDirA, paramsJ] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;
const out = `${outDirA || "/pw/out"}/${tag}_${variant}`;
fs.mkdirSync(out, { recursive: true });
const body = {}; if (preset && preset !== "-") body.preset = preset; if (paramsJ && paramsJ !== "-") body.params = JSON.parse(paramsJ);
const errs = [], res = { viz, preset, tag, variant };
const br = await launch();
try {
  const id = await startRun(base, viz, body);
  const page = await openPage(br, base, id, { errs, playMs: +(playMsS || 6000), variant });
  await fetch(`${base}/api/runs/${id}/command`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ cmd: "pause" }) });
  await sleep(1200); await settle(page);
  res.diag = await diag(page);
  await shot(page, `${out}/a_opened.jpg`);
  res.look = await page.evaluate(() => { const a = document.querySelector(".s3d-view").__scene3d; for (const P of a.planes()) a.setPlaneVisible(P.id, false); return a.volumeLook ? a.volumeLook() : null; });
  await settle(page);
  await shot(page, `${out}/b_no_planes.jpg`);
  await page.close();
} catch (e) { res.failed = String(e && e.stack || e).slice(0, 600); }
res.errors = errs.slice(0, 6);
await br.close();
fs.writeFileSync(`${out}/look.json`, JSON.stringify(res, null, 1));
console.log(JSON.stringify({ tag, variant, failed: res.failed, errors: res.errors, corners: res.diag && res.diag.cornersInside, look: res.look }));
