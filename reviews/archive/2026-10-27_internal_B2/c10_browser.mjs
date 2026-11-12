// B2 review, check 10: the pages in headless Chromium (WebGL by SwiftShader) against the reviewer's own server
// instance on port 8501 (engine mounted read-only, runs in this folder's runs/), started from engine/ with
//   docker run -d --rm --name b2rev-viz8501 --init --user "$(id -u):$(id -g)" -v "$PWD":/lf:ro \
//       -v "$PWD/reviews/2026-10-27_internal_B2/runs":/runs -p 8501:8501 -w /lf/visualizations light-funnel-viz \
//       python3 server/serve.py --host 0.0.0.0 --port 8501 --runs-dir /runs
// and stopped with `docker stop b2rev-viz8501`. This file, copied next to a node_modules with playwright@1.58.2, runs
// in mcr.microsoft.com/playwright:v1.58.2-jammy with --network host:
//   docker run --rm --init --shm-size=2g --network host --user "$(id -u):$(id -g)" -v <dir>:/w -v <out>:/o -w /w \
//       -e HOME=/tmp mcr.microsoft.com/playwright:v1.58.2-jammy node c10_browser.mjs /o
// (1) v09 thomas at t = 0, paused: what the panel «Манёвр и голономия» shows before the run's time moved (B2-2);
// (2) v09: a slice plane through two corners of the box (normal (1, -1, 0)): the outline drawn (B2-7);
// (3) v09 presets and v08 gauss: page errors after a full play.
import { chromium } from "playwright";
const OUT = process.argv[2] || ".";
const base = "http://127.0.0.1:8501";
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [], out = {};
async function open(viz, preset, wait = 8000, params) {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
  page.on("pageerror", (e) => errs.push(`${viz}/${preset} pageerror: ${e.stack}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`${viz}/${preset} ${m.text()}`); });
  const r = await post("/api/runs", { viz, preset, params, seed: 5 });
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(wait);
  return [page, r.id];
}
const cmd = (id, c, args) => post(`/api/runs/${id}/command`, { cmd: c, args });
const S = (page, f, a) => page.evaluate(f, a);

// (1) + (2)
{
  const [page, id] = await open("v09_thomas_3d", "thomas", 9000);
  out.t0_panel = await S(page, () => [...document.querySelectorAll(".panel")].map((p) => p.innerText).filter((t) => /голономия/i.test(t)).join("\n"));
  out.t0_runs = await (await fetch(`${base}/api/runs`)).json().then((rs) => rs.filter((r) => r.id === id).map((r) => ({ t: r.t ?? r.sim_t ?? r.time, state: r.state })));
  await page.screenshot({ path: `${OUT}/c10_v09_thomas_t0.png` });
  await cmd(id, "view", { op: "plane", id: 2, origin: [0, 0, 0], normal: [0.7071067811865476, -0.7071067811865476, 0] });
  await page.waitForTimeout(4000);
  out.diag_plane = await S(page, () => document.querySelector(".s3d-view").__scene3d.planes().map((P) => ({ id: P.id, n: P.n, poly: P.poly })));
  await page.screenshot({ path: `${OUT}/c10_v09_diagonal_plane.png` });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
// (3)
for (const preset of ["thomas", "triangle", "crown", "helix", "seam", "spin_flip", "lab"]) {
  const [page, id] = await open("v09_thomas_3d", preset, 7000);
  await cmd(id, "speed", { value: 1e12 }); await cmd(id, "play", {});
  await page.waitForTimeout(5000);
  out[`end_${preset}`] = await S(page, () => [...document.querySelectorAll(".panel")].map((p) => p.innerText).filter((t) => /голономия/i.test(t)).join("\n").slice(0, 600));
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
{
  const [page, id] = await open("v08_wave_3d", "gauss", 20000);
  await page.click("text=＋ Срез"); await page.waitForTimeout(6000);
  out.v08 = await S(page, () => document.querySelector(".s3d-view").__scene3d.planes().map((P) => ({ id: P.id, n: P.n.map((c) => +c.toFixed(3)), poly: P.poly.length })));
  await page.screenshot({ path: `${OUT}/c10_v08_gauss.png` });
  await post(`/api/runs/${id}/stop`, {}); await page.close();
}
console.log(JSON.stringify(out, null, 1));
console.log(errs.length ? errs.join("\n") : "no page errors");
await browser.close();
