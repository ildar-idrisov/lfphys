// Review B6-framework, browser checks of the playground's player (a PRIVATE server on port 8531, never 8479).
//   b1: p01 (preset "inner"): the trail points the 3-D scene holds, sampled every 3 s while the run plays, with the
//       record's segment count: at the first periodic checkpoint (60 s of play) rekey's reset empties every trail.
//   b2: the record panel at a cursor in the past: recording switched on then off; the page opened at the end, the cursor
//       moved back between the two; the panel's button and what a change of the window's minutes posts.
//   b3: p02 (preset "double_slit"): the renderer's memory while a live viewer watches (the window bounds the server's
//       record, not the tab).
// Server:
//   docker run -d --name lf-b6rf-srv --user $(id -u):$(id -g) -v <engine>:/lf:ro -v <review>/runs_browser:/lf/visualizations/runs \
//     -e LFPHYS_NO_GPU=1 -w /lf/visualizations -p 8531:8479 light-funnel-viz \
//     python3 server/serve.py --host 0.0.0.0 --port 8479 --max-workers 2
// Browser (the script next to a node_modules with playwright 1.58.2, copied to a scratch folder):
//   docker run --rm --init --shm-size=2g --network host --name lf-b6rf-pw -v <scratch with node_modules>:/pw \
//     -v <review>:/t:ro -w /pw mcr.microsoft.com/playwright:v1.58.2-jammy sh -c "cp /t/b01_browser.mjs /pw/ && node /pw/b01_browser.mjs 8531 [b1,b2,b3]"
import { chromium } from "playwright";
import { execSync } from "node:child_process";

const port = process.argv[2] || "8531";
const only = process.argv[3] ? process.argv[3].split(",") : ["b1", "b2", "b3"];
const base = `http://127.0.0.1:${port}`;
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
const get = async (u) => (await fetch(base + u)).json();
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const br = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });

async function open(id) {
  const page = await br.newPage({ viewport: { width: 1500, height: 950 } });
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message.slice(0, 200)));
  await page.goto(`${base}/run?id=${id}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка записи/.test(document.querySelector("#status").textContent || ""), null, { timeout: 120000 });
  return { page, errs };
}
const trailPts = (page) => page.evaluate(() => {
  const sc = document.querySelector(".s3d-view"), S = sc && sc.__scene3d && sc.__scene3d.state;
  if (!S) return -1;
  const L = S.layers.get("trails");
  if (!L) return 0;
  let n = 0;
  L.obj.traverse((o) => {
    const a = o.geometry && o.geometry.attributes.position; if (!a) return;
    const cnt = Number.isFinite(o.geometry.drawRange.count) ? Math.min(o.geometry.drawRange.count, a.count) : a.count;
    for (let i = 0; i < cnt; i++) if (Number.isFinite(a.array[3 * i])) n++;
  });
  return n;
});
const rendererRssMB = () => {
  try {
    const out = execSync("ps -eo rss,args").toString().split("\n").filter((l) => l.includes("--type=renderer"));
    return Math.round(out.reduce((s, l) => s + Number(l.trim().split(/\s+/)[0]), 0) / 1024);
  } catch (e) { return -1; }
};

if (only.includes("b1")) {
  const { id } = await post("/api/runs", { viz: "p01_gravity", preset: "inner", seed: 3 });
  const { page, errs } = await open(id);
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  const rows = [];
  for (let s = 0; s <= 84; s += 3) {
    const m = await get(`/api/runs/${id}`);
    rows.push({ s, segs: (m.buffer.segs || []).length, sim_t: Number(m.sim_t.toPrecision(4)), trail_points: await trailPts(page) });
    await sleep(3000);
  }
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  console.log(JSON.stringify({ b1: id, rows, errors: errs }));
  await page.close();
}

if (only.includes("b2")) {
  const { id } = await post("/api/runs", { viz: "p01_gravity", preset: "sun_earth", seed: 3 });
  await sleep(1500);
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  await sleep(3000); await post(`/api/runs/${id}/record`, { on: true });
  await sleep(3000); await post(`/api/runs/${id}/record`, { on: false });
  await sleep(3000); await post(`/api/runs/${id}/command`, { cmd: "pause" });
  await sleep(1500);
  const before = (await get(`/api/runs/${id}`)).buffer;
  const { page, errs } = await open(id);
  const label = () => page.evaluate(() => [...document.querySelectorAll("button")].map((b) => b.textContent).find((t) => /Сохраня/.test(t)) || null);
  const atEnd = await label();
  const nf = await page.evaluate(() => window.__lfPlayer.frames());
  await page.evaluate((i) => window.__lfPlayer.goTo(i), Math.round(0.5 * (nf - 1)));
  await sleep(800);
  const tMid = await page.evaluate(() => window.__lfPlayer.t());
  const atMid = await label();
  // the owner changes the window's minutes while looking at that moment
  await page.evaluate(() => {
    const inp = [...document.querySelectorAll("input[type=number]")].find((x) => /последних минут/.test(x.title));
    inp.value = "15"; inp.dispatchEvent(new Event("change"));
  });
  await sleep(1500);
  const after = (await get(`/api/runs/${id}`)).buffer;
  console.log(JSON.stringify({ b2: id, server_before: { recording: before.recording, window_s: before.window_s },
    button_at_end: atEnd, cursor_t: tMid, button_at_cursor: atMid,
    server_after_window_change: { recording: after.recording, window_s: after.window_s, protected: after.protected }, errors: errs }));
  await page.close();
}

if (only.includes("b3")) {
  const { id } = await post("/api/runs", { viz: "p02_quantum", preset: "double_slit", seed: 3 });
  const { page, errs } = await open(id);
  await post(`/api/runs/${id}/command`, { cmd: "play" });
  const rows = [];
  for (let s = 0; s <= 90; s += 15) {
    const m = await get(`/api/runs/${id}`);
    rows.push({ s, record_MB: Number((m.size / 1e6).toFixed(1)), renderer_rss_MB: rendererRssMB(), frames_kept: await page.evaluate(() => window.__lfPlayer.frames()) });
    await sleep(15000);
  }
  await post(`/api/runs/${id}/command`, { cmd: "pause" });
  console.log(JSON.stringify({ b3: id, rows, errors: errs }));
  await page.close();
}
await br.close();
