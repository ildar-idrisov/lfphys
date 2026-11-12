// Review 2026-10-29 (record checkpoints, key frames): shared helpers of the browser checks k01..k06.
// Run each check against a PRIVATE server (never the shared one on :8479), e.g.:
//   docker run --rm --init --shm-size=2g --network host --name lf-rev-pw -v <scratchpad>/pw/node_modules:/pw/node_modules:ro \
//     -v <this folder>:/pw/rev -w /pw/rev mcr.microsoft.com/playwright:v1.58.2-jammy node k01_v09_body.mjs 8510
import { chromium } from "playwright";

export const port = process.argv[2] || "8510";
export const base = `http://127.0.0.1:${port}`;
export const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
export const get = async (u) => (await fetch(base + u)).json();
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export async function browser() {
  return chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--js-flags=--expose-gc"] });
}
export const settle = (page) => page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(r, 400)))));

// open a run's page and wait until its record is loaded and drawn once (history_end, then a rebuild of the view)
export async function open(br, id, keyEvery = 5, errs = []) {
  const page = await br.newPage({ viewport: { width: 1600, height: 1000 } });
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`console: ${m.text()}`.slice(0, 300)); });
  await page.goto(`${base}/run?id=${id}&key_every=${keyEvery}`);
  await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && document.querySelector("#status")
    && !/загрузка записи/.test(document.querySelector("#status").textContent || ""), null, { timeout: 180000 });
  await settle(page);
  return page;
}

// wait for a run's state from the REST API
export async function waitRun(id, pred, timeout = 120000) {
  const t0 = Date.now();
  for (;;) {
    const m = await get(`/api/runs/${id}`);
    if (pred(m)) return m;
    if (Date.now() - t0 > timeout) throw new Error(`timeout waiting for run ${id}: ${JSON.stringify(m).slice(0, 300)}`);
    await sleep(500);
  }
}

// the 3-D scene's state as numbers (layers' geometry and transforms, planes with/without their image, slice windows)
export async function scene(page) {
  return page.evaluate(() => {
    const sc = document.querySelector(".s3d-view");
    if (!sc || !sc.__scene3d) return null;
    const S = sc.__scene3d.state;
    const layers = {};
    for (const L of S.layers.values()) {
      let acc = 0, n = 0, radius = null;
      L.obj.traverse((o) => {
        if (o.geometry && o.geometry.parameters && o.geometry.parameters.radius && radius === null) radius = o.geometry.parameters.radius;
        if (!o.geometry) return;
        const g = o.geometry, cnt = Number.isFinite(g.drawRange.count) ? g.drawRange.count : Infinity;
        for (const name of ["position", "color"]) {
          const a = g.attributes[name]; if (!a) continue;
          const m = Math.min(a.array.length, cnt === Infinity ? a.array.length : cnt * a.itemSize);
          for (let i = 0; i < m; i++) { const v = a.array[i]; if (Number.isFinite(v)) acc += v * ((i % 97) + 1); }
          n += m;
        }
      });
      layers[L.id] = { kind: L.kind, n, acc: +acc.toPrecision(8), radius, children: L.obj.children.length };
    }
    const planes = {};
    for (const [id, P] of S.planes) planes[id] = { hasImage: !!P.data, origin: P.meta && P.meta.origin };
    const wins = [...document.querySelectorAll(".slicewin")].map((w) => {
      const c = w.querySelector("canvas.sw-canvas");
      let sum = 0;
      try { const d = c.getContext("2d").getImageData(0, 0, c.width, c.height).data; for (let i = 0; i < d.length; i += 4) sum += d[i] + 2 * d[i + 1] + 3 * d[i + 2]; } catch (e) { sum = -1; }
      return { id: (w.querySelector(".sw-chip") || {}).textContent, text: (w.innerText || "").slice(0, 80).replace(/\s+/g, " "), pix: sum };
    });
    return { size: S.size, box: S.box, layers, planes, wins };
  });
}

export const panelsText = (page) => page.evaluate(() => [...document.querySelectorAll(".panel")].map((p) => (p.innerText || "").replace(/\s+/g, " ").slice(0, 400)));
export const dbg = (page) => page.evaluate(() => ({ ...window.__lfPlayer.dbg, keys: window.__lfPlayer.keys(), t: window.__lfPlayer.t(), frames: window.__lfPlayer.frames() }));
