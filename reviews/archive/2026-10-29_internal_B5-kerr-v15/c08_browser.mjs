// Review B5, check c08 (browser): v15 in the player.
// (A) M87 preset: the image's brightness on the approaching (alpha < 0) and receding side, from the data the window
//     holds and from the drawn canvas; screenshots in the four modes.
// (B) History: the image paused at ~25 % of its rows (the canvas sampled), scanned to the end, then the cursor moved
//     back to the paused frame: are the rows shown then drawn as they were (the brightness scale of the time shown) or
//     with a scale taken from rows computed later?
// (C) The 3-D views "Сверху" ("along the spin axis") and "От наблюдателя" of v15's header: screenshots, and where the
//     camera looks in physics coordinates (scene3d's P2T: physics (x, y, z) -> three (z, y, -x)).
// (D) The what-if preset, the edge-on preset and the world chi = 0.998, 81 deg (c06: `edge` fails): screenshots of
//     the screen and of the checks.
//
// Root: the reviewer's own server on port 8520 (engine mounted read-only at /lf, runs in a scratch folder); this script
// is copied next to a playwright node_modules folder and run there:
//   docker run --rm --init --network host --shm-size=2g --user "$(id -u):$(id -g)" -v <pw>:/pw -w /pw \
//     mcr.microsoft.com/playwright:v1.58.2-jammy node c08_browser.mjs > <review>/out/c08_browser.txt
// Screenshots land in <pw>/rev15_shots/ and are copied to <review>/out/.
import { chromium } from "playwright";
import fs from "node:fs";

const base = "http://127.0.0.1:8520";
const V = "v15_kerr_shadow";
fs.mkdirSync("rev15_shots", { recursive: true });
const post = async (u, b) => (await fetch(base + u, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b) })).json();
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const errs = [];
const log = (...a) => console.log(...a);
async function open(preset, params = {}, wait = 5000) {
  const page = await browser.newPage({ viewport: { width: 1700, height: 1000 } });
  page.on("pageerror", (e) => errs.push(`${preset} pageerror: ${e.message}`));
  page.on("console", (m) => { if (m.type() === "error") errs.push(`${preset} console: ${m.text()}`); });
  const r = await post("/api/runs", { viz: V, preset, params, seed: 3 });
  if (!r.id) { errs.push(`${preset} start: ${JSON.stringify(r)}`); return [page, null]; }
  await page.goto(base + "/run?id=" + r.id);
  await page.waitForTimeout(wait);
  return [page, r.id];
}
const cmd = (id, c, args = {}) => post(`/api/runs/${id}/command`, { cmd: c, args });
const S = (page, f, a) => page.evaluate(f, a);
const status = (page) => S(page, () => { const s = document.querySelector(".imgwin .sw-status"); return s ? s.textContent : ""; });
async function waitDone(page, ms = 40000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { const s = await status(page); if (s.startsWith("готово")) return s; await page.waitForTimeout(200); }
  return await status(page);
}
async function shot(page, sel, name) {
  try { await page.locator(sel).first().screenshot({ path: `rev15_shots/${name}.png`, timeout: 60000 }); } catch (e) { errs.push(`shot ${name}: ${e.message.slice(0, 100)}`); }
}
// the drawn colour of image pixel (i, j) from the window's canvas (centre of its drawn square)
const sample = (page, pts) => S(page, (pts) => {
  const w = document.querySelector(".imgwin").closest(".s3d-windows").__imagewin;
  const g = w.geometry(), cv = document.querySelector(".imgwin canvas"), ctx = cv.getContext("2d");
  const dpr = cv.width / cv.clientWidth;
  return pts.map(([i, j]) => {
    const x = Math.round((g.left + (i + 0.5) / g.W * g.pw) * dpr), y = Math.round((g.top + (j + 0.5) / g.H * g.ph) * dpr);
    return Array.from(ctx.getImageData(x, y, 1, 1).data.slice(0, 3));
  });
}, pts);

// (A) M87 preset
{
  const [page, id] = await open("m87");
  await cmd(id, "play");
  log("A: m87 status", await waitDone(page));
  await page.waitForTimeout(800);
  const st = await S(page, () => {
    const w = document.querySelector(".imgwin").closest(".s3d-windows").__imagewin, cur = w.current();
    const f = cur.fields, [H, W] = cur.meta.shape, n = (f.nmax + 1);
    let L = 0, R = 0, gl = 0, gr = 0, nl = 0, nr = 0;
    for (let j = 0; j < H; j++) for (let i = 0; i < W; i++) {
      const k = j * W + i; let s = 0; for (let m = 0; m < n; m++) s += f.I[m * W * H + k];
      if (i < W / 2) L += s; else R += s;
      const g0 = f.g[k]; if (g0 > 0 && f.r[k] <= 20) { if (i < W / 2) { gl += g0; nl++; } else { gr += g0; nr++; } }
    }
    return { W, H, sumI_left: L, sumI_right: R, mean_g0_left: gl / nl, mean_g0_right: gr / nr, camera: cur.meta.camera };
  });
  log("A: data", JSON.stringify(st));
  // drawn brightness by column halves
  const pts = []; for (let j = 0; j < st.H; j += 4) for (let i = 0; i < st.W; i += 4) pts.push([i, j]);
  const cols = await sample(page, pts);
  let dl = 0, dr = 0; pts.forEach(([i], k) => { const v = cols[k][0] + cols[k][1] + cols[k][2]; if (i < st.W / 2) dl += v; else dr += v; });
  log(`A: drawn brightness left ${dl} right ${dr} (ratio ${(dl / dr).toFixed(3)})`);
  await page.screenshot({ path: "rev15_shots/A_m87_page.png" });
  await shot(page, ".imgwin", "A_m87_seen");
  for (const mode of ["order", "redshift", "fate"]) {
    await S(page, (m) => { const s = [...document.querySelectorAll("select")].find((x) => [...x.options].some((o) => o.value === "redshift")); s.value = m; s.onchange(); }, mode);
    await page.waitForTimeout(600);
    await shot(page, ".imgwin", `A_m87_${mode}`);
    log(`A: mode ${mode} status «${await status(page)}» class ${await S(page, () => document.querySelector(".imgwin .sw-status span").className)}`);
  }
  // (C) the 3-D views
  for (const [label, name] of [["Изо", "iso"], ["Сверху", "top"], ["От наблюдателя", "beam"], ["Сбоку", "side"]]) {
    await page.locator(".s3d-tools button", { hasText: label }).first().click();
    await page.waitForTimeout(700);
    await shot(page, ".s3d-canvas", `C_view_${name}`);
  }
  log("C: scene3d camera directions (three.js): top [0.001, 1, 0] = physics +y; beam [-1, 0, 0] = physics -z; side [0, 0, 1] = physics -x; up = three +y = physics +y");
  await page.close();
}

// (B) history: live at ~25 % vs the cursor moved back to the same frame after the end
{
  const [page, id] = await open("m87");
  await cmd(id, "play");
  let rows = 0;
  const t0 = Date.now();
  while (Date.now() - t0 < 20000) {
    const s = await status(page); const m = s.match(/считается: (\d+) из (\d+)/);
    if (m && Number(m[1]) >= 0.25 * Number(m[2])) { rows = Number(m[1]); break; }
    await page.waitForTimeout(50);
  }
  await cmd(id, "pause");
  await page.waitForTimeout(1500);
  const s1 = await status(page); rows = Number((s1.match(/считается: (\d+)/) || [0, 0])[1]);
  const n1 = await S(page, () => window.__lfPlayer.frames()), t1 = await S(page, () => window.__lfPlayer.t());
  const W = 192, pts = []; for (let j = 2; j < rows - 2; j += 3) for (let i = 0; i < W; i += 3) pts.push([i, j]);
  const live = await sample(page, pts);
  await shot(page, ".imgwin", "B_live_paused");
  log(`B: paused at t = ${t1}, frames ${n1}, status «${s1}», sampled ${pts.length} pixels of rows < ${rows}`);
  await cmd(id, "play");
  log("B: end status", await waitDone(page));
  await page.waitForTimeout(1000);
  await cmd(id, "pause");
  await page.waitForTimeout(800);
  // the cursor back to the paused frame
  let idx = n1 - 1, tt = null;
  for (let k = 0; k < 40; k++) {
    await S(page, (i) => window.__lfPlayer.goTo(i), idx);
    await page.waitForTimeout(150);
    tt = await S(page, () => window.__lfPlayer.t());
    if (Math.abs(tt - t1) < 1e-9) break;
    idx += tt < t1 ? 1 : -1;
  }
  await page.waitForTimeout(1500);
  const s2 = await status(page);
  const back = await sample(page, pts);
  await shot(page, ".imgwin", "B_cursor_back");
  let diff = 0, maxd = 0, brighter = 0, dimmer = 0;
  pts.forEach((_, k) => {
    const d = Math.max(...[0, 1, 2].map((c) => Math.abs(live[k][c] - back[k][c])));
    if (d > 2) { diff++; const sl = live[k][0] + live[k][1] + live[k][2], sb = back[k][0] + back[k][1] + back[k][2]; if (sb > sl) brighter++; else dimmer++; }
    maxd = Math.max(maxd, d);
  });
  log(`B: cursor back at t = ${tt} (frame ${idx}), status «${s2}»: ${diff} of ${pts.length} sampled pixels drawn differently (max channel difference ${maxd}; brighter ${brighter}, dimmer ${dimmer})`);
  await page.close();
}

// (D) what-if, edge-on, the failing-edge world
for (const [preset, params, name] of [["whatif", {}, "D_whatif"], ["edge_on", {}, "D_edge_on"], [null, { chi: 0.998, incl: 81.0 }, "D_chi0998_81"]]) {
  const [page, id] = await open(preset, params);
  await cmd(id, "play");
  await page.waitForTimeout(6000);
  await page.screenshot({ path: `rev15_shots/${name}_page.png` });
  const txt = await S(page, () => document.getElementById("left").innerText);
  log(`D: ${name} left panel:\n${txt.split("\n").filter((l) => /Край тени|δ|EHT|кольцо|Тень на|GPU/.test(l)).slice(0, 14).join("\n")}`);
  await page.close();
}

log("errors:", JSON.stringify(errs));
await browser.close();
