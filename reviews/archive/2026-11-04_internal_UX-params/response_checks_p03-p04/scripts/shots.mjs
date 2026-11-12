// Before/after screenshots for the p03/p04 processing of reviews UX-ui and UX-params (private servers only).
// Usage: PORT=<port> TAG=<before|after> node shots.mjs [case,...]
import { chromium } from "playwright";
import fs from "fs";
const port = process.env.PORT, tag = process.env.TAG;
const base = `http://127.0.0.1:${port}`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const post = async (u, b) => { const r = await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) }); try { return await r.json(); } catch (e) { return { status: r.status }; } };
const cmd = (id, c, args) => post(`/api/runs/${id}/command`, { cmd: c, args });
const before = tag === "before";
const CASES = {
  hard_atom: { viz: "p03_molecules", body: { params: before ? { model: "hard" } : { dynamics: "hard" } },
               steps: async (id) => { await cmd(id, "scene", { op: "add", type: "atom", values: {} }); await cmd(id, "play", {}); await sleep(5000); } },
  p03_wall_piston: { viz: "p03_molecules", body: {},
                     steps: async (id) => { await cmd(id, "scene", { op: "add", type: "gas", values: {} }); await sleep(800);
                                            await cmd(id, "scene", { op: "add", type: "wall", values: {} }); await sleep(800);
                                            await cmd(id, "scene", { op: "add", type: "piston", values: {} }); await cmd(id, "play", {}); await sleep(5000); } },
  p03_hot_gas: { viz: "p03_molecules", body: {},
                 steps: async (id) => { await cmd(id, "scene", { op: "add", type: "gas", values: { T: 100000 } }); await cmd(id, "play", {}); await sleep(6000); } },
  p03_live: { viz: "p03_molecules", body: { preset: "maxwell" },
              steps: async (id) => { await cmd(id, "play", {}); await sleep(1500); await cmd(id, "set", { values: { model: "wca", dt_fs: 5 } }); await sleep(3000); } },
  p04_gravity: { viz: "p04_fluids", body: {},
                 steps: async (id) => { await cmd(id, "scene", { op: "add", type: "gravity", values: {} }); await cmd(id, "play", {}); await sleep(4000); } },
  p04_cyl_1280: { viz: "p04_fluids", body: { preset: "cylinder_re20" }, w: 1280, h: 800,
                  steps: async (id) => { await cmd(id, "play", {}); await sleep(8000); } },
  p04_water: { viz: "p04_fluids", body: { params: { fluid: "water" } },
               steps: async (id) => { for (const t of ["inlet", "outlet", "disk", "dye_source"]) { await cmd(id, "scene", { op: "add", type: t, values: {} }); await sleep(500); }
                                      await cmd(id, "play", {}); await sleep(8000); } },
  p04_probe_body: { viz: "p04_fluids", body: { preset: "cylinder_re20" },
                    steps: async (id) => { await cmd(id, "scene", { op: "add", type: "probe", values: { x: 0.6, y: 0.2 } }); await sleep(800);
                                           const p = await (await fetch(`${base}/api/runs/${id}`)).json();
                                           await cmd(id, "play", {}); await sleep(1500);
                                           // the probe is the last object: o5 in the preset (4 objects)
                                           await cmd(id, "scene", { op: "set", id: "o5", values: { x: 0.2, y: 0.2 } }); await sleep(4000); } },
  p04_live: { viz: "p04_fluids", body: { preset: "cylinder_re20" },
              steps: async (id) => { await cmd(id, "play", {}); await sleep(2000); await cmd(id, "set", { values: { nu: 0.002, collision: "bgk" } }); await sleep(3000); } },
};
const b = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
fs.mkdirSync("/pw/shots", { recursive: true });
const only = process.argv[2] ? process.argv[2].split(",") : Object.keys(CASES);
for (const name of only) {
  const c = CASES[name];
  if (!before || !name.endsWith("_live")) {
    const r = await post("/api/runs", { viz: c.viz, ...c.body });
    const out = { case: name, tag, start: r };
    const ctx = await b.newContext({ viewport: { width: c.w || 1600, height: c.h || 1000 } });
    const page = await ctx.newPage();
    if (r.id) {
      await page.goto(`${base}/run?id=${r.id}`);
      await page.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0, null, { timeout: 60000 }).catch(() => { out.no_frames = true; });
      await sleep(1500);
      await c.steps(r.id);
      out.toasts = await page.$$eval(".toast", (ts) => ts.map((t) => t.textContent.slice(0, 400)));
      out.events = await page.$$eval(".events div", (ds) => ds.slice(-6).map((d) => d.textContent.slice(0, 300))).catch(() => []);
      out.status = await page.textContent("#status").catch(() => "");
      await page.screenshot({ path: `/pw/shots/${tag}_${name}.jpg`, type: "jpeg", quality: 70 });
      await post(`/api/runs/${r.id}/stop`, {});
    } else {
      await page.goto(`${base}/`);
      await sleep(1500);
      await page.screenshot({ path: `/pw/shots/${tag}_${name}.jpg`, type: "jpeg", quality: 70 });
    }
    console.log(JSON.stringify(out));
    fs.appendFileSync(`/pw/shots_${tag}.jsonl`, JSON.stringify(out) + "\n");
    await ctx.close();
  }
}
await b.close();
