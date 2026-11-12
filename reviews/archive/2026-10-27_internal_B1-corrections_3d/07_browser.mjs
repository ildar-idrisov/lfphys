// Review of the B1 corrections (reviewer's script): the player's 3-D environment in headless Chromium (WebGL by
// SwiftShader) against the reviewer's own server instance (port 8498, engine read-only, runs in ./runs).
// Each step logs numbers to out/07_browser.txt and saves a screenshot to out/07*.png. Every run it starts is stopped.
import { createRequire } from "module";
import fs from "fs";
const require = createRequire("/pw/node_modules/x.js");
const { chromium } = require("playwright");

const BASE = "http://127.0.0.1:8498";
const OUT = "/rev/out";
const LOG = `${OUT}/07_browser.txt`;
fs.writeFileSync(LOG, "");
const log = (...a) => { const s = a.map((x) => (typeof x === "string" ? x : JSON.stringify(x))).join(" "); console.log(s); fs.appendFileSync(LOG, s + "\n"); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function api(path, body, method) {
  const r = await fetch(BASE + path, { method: method || (body ? "POST" : "GET"), headers: { "content-type": "application/json" }, body: body ? JSON.stringify(body) : undefined });
  return r.json();
}
const started = [];

async function scene(page) {
  return page.evaluate(() => {
    const s = document.querySelector(".s3d-view").__scene3d;
    const r = (a) => (a ? a.map((x) => Math.round(x * 1e4) / 1e4) : a);
    return {
      layers: s.layers().map((L) => ({ id: L.id, label: L.label, visible: L.visible, objVisible: L.obj.visible, kind: L.kind })),
      planes: s.planes().map((P) => ({ id: P.id, origin: r(P.origin), n: r(P.n), u: r(P.u), v: r(P.v), visible: P.visible,
        hl: P.mat.uniforms.uHighlight.value, op: P.mat.uniforms.uOpacity.value, mode: P.mat.uniforms.uMode.value,
        meta: P.data ? { s: r(P.data.meta.s), tt: r(P.data.meta.tt), origin: r(P.data.meta.origin), label: P.data.meta.label,
          route_label: P.data.meta.route_label, verify: P.data.meta.verify, window_est: P.data.meta.window_est, t: P.data.meta.t } : null })),
      selected: s.state.selected, highlighted: s.state.highlighted,
    };
  });
}
async function waitFor(page, fn, arg, ms = 60000) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) { if (await page.evaluate(fn, arg)) return true; await sleep(250); }
  return false;
}
const planeReady = (id) => { const s = document.querySelector(".s3d-view")?.__scene3d; const P = s && s.planes().find((q) => q.id === id); return !!(P && P.data && P.data.meta && !document.querySelector(".slicewin .sw-status .warn")); };

async function openRun(browser, body, tag) {
  const { id } = await api("/api/runs", body);
  started.push(id);
  const page = await browser.newPage({ viewport: { width: 1680, height: 1000 } });
  const errors = [];
  page.on("pageerror", (e) => errors.push("pageerror: " + e.message));
  page.on("console", (m) => { if (m.type() === "error") errors.push("console: " + m.text()); });
  const counts = {};
  page.on("websocket", (ws) => ws.on("framereceived", (f) => {
    try {
      const b = Buffer.isBuffer(f.payload) ? f.payload : Buffer.from(f.payload);
      const n = b.readUInt32LE(0);
      const meta = JSON.parse(b.subarray(4, 4 + n).toString("utf8"));
      counts[meta.type] = (counts[meta.type] || 0) + 1;
      if (meta.type === "error") errors.push("run error: " + String(meta.text).slice(0, 200));
    } catch (e) { /* text frames */ }
  }));
  await page.goto(`${BASE}/run?id=${id}`);
  await page.waitForSelector(".s3d-view", { timeout: 60000 });
  const ok = await waitFor(page, planeReady, 1, 90000);
  log(`[${tag}] run ${id} ${JSON.stringify(body)}: first slice ready ${ok}`);
  return { id, page, errors, counts };
}

const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
try {
  // ---------------------------------------------------------------------------------------------------------------
  const { id, page, errors, counts } = await openRun(browser, { viz: "v08_wave_3d", preset: "double" }, "double");
  await sleep(1500);
  let S0 = await scene(page);
  log("(1) layers:", S0.layers.map((L) => `${L.id}:${L.kind}:${L.visible}`));
  log("    planes:", S0.planes.map((P) => ({ id: P.id, origin: P.origin, n: P.n, label: P.meta && P.meta.label, verify: P.meta && P.meta.verify })));
  log("    top bar:", await page.textContent("#physics"));
  await page.screenshot({ path: `${OUT}/07a_initial.png` });

  // (2) fixed while the world plays
  const before = JSON.stringify(S0.planes.map((P) => [P.origin, P.n, P.meta && P.meta.t]));
  const c0 = { ...counts };
  await page.click("#play");
  await sleep(6000);
  await page.click("#play");
  const S1 = await scene(page);
  const after = JSON.stringify(S1.planes.map((P) => [P.origin, P.n, P.meta && P.meta.t]));
  log(`(2) 6 s of play: planes unchanged ${before === after}; slice messages during play ${(counts.slice || 0) - (c0.slice || 0)}, planes messages ${(counts.planes || 0) - (c0.planes || 0)}, frames ${(counts.frame || 0) - (c0.frame || 0)}`);
  log("    time shown:", await page.textContent("#time"));

  // (3) add two planes: middle, perpendicular
  const addBtn = page.locator("button", { hasText: "＋ Срез" });
  await addBtn.click();
  await waitFor(page, planeReady, 2);
  await addBtn.click();
  await waitFor(page, planeReady, 3);
  await sleep(800);
  const S2 = await scene(page);
  const N = S2.planes.map((P) => P.n);
  const dots = [[0, 1], [0, 2], [1, 2]].map(([a, b]) => Math.abs(N[a][0] * N[b][0] + N[a][1] * N[b][1] + N[a][2] * N[b][2]).toFixed(3));
  log("(3) planes after two '+ Срез':", S2.planes.map((P) => ({ id: P.id, origin: P.origin, n: P.n, label: P.meta && P.meta.label })), "|n_i.n_j|:", dots,
    "windows:", await page.locator(".slicewin").count(), "add button disabled:", await addBtn.isDisabled());
  await page.screenshot({ path: `${OUT}/07b_three_planes.png` });

  // (4) pointing at a window highlights its plane
  await page.locator(".slicewin").nth(1).hover();
  await sleep(300);
  const S3 = await scene(page);
  log("(4) hover window 2: highlight", S3.planes.map((P) => [P.id, P.hl, P.op]));
  await page.screenshot({ path: `${OUT}/07c_hover_window2.png` });
  await page.mouse.move(5, 500);

  // (5) the add-plane rule when plane 1 is turned first: is the next plane perpendicular?
  // (done later on a fresh run; here: remove 2 and 3, turn plane 1 by parameters, add again)

  // (6) select plane 1 by its window, then move it by parameters: centre x = 5 for plane 3 (transverse)
  await page.locator(".slicewin").nth(2).click();
  await sleep(300);
  const inputs = page.locator(".panel:has(h4:text('Срез: положение и наклон')) input[type=number]");
  log("(6) selected:", (await scene(page)).selected, "panel inputs:", await inputs.count());
  await inputs.nth(0).fill("5");
  await inputs.nth(0).dispatchEvent("change");
  await sleep(500);
  await waitFor(page, planeReady, 3);
  await sleep(800);
  const S4 = await scene(page);
  const p3 = S4.planes.find((P) => P.id === 3);
  log("    plane 3 after centre x = 5:", { origin: p3.meta.origin, s: p3.meta.s, tt: p3.meta.tt, label: p3.meta.label },
    "-> window's horizontal axis is labelled 'x, мкм' with ticks from s0 =", p3.meta.s[0], "to s1 =", p3.meta.s[1],
    "; the true x of those points:", (p3.meta.origin[0] + p3.meta.s[0]).toFixed(3), "to", (p3.meta.origin[0] + p3.meta.s[1]).toFixed(3));
  await page.locator(".slicewin").nth(2).screenshot({ path: `${OUT}/07e_window3_after_x5.png` });
  // the readout under the cursor at the window's left edge
  const g = await page.locator(".slicewin").nth(2).locator("canvas").boundingBox();
  await page.mouse.move(g.x + 46, g.y + g.height / 2);
  await sleep(200);
  log("    readout at the left edge of window 3:", await page.locator(".slicewin").nth(2).locator(".sw-readout").textContent());

  // (7) turn plane 2 by parameters: theta 45, phi 30
  await page.locator(".slicewin").nth(1).click();
  await sleep(300);
  await inputs.nth(3).fill("45");
  await inputs.nth(4).fill("30");
  await inputs.nth(4).dispatchEvent("change");
  await sleep(500);
  await waitFor(page, planeReady, 2, 120000);
  await sleep(800);
  const S5 = await scene(page);
  const p2 = S5.planes.find((P) => P.id === 2);
  log("(7) plane 2 at theta 45, phi 30:", { n: p2.n, u: p2.u, v: p2.v, label: p2.meta.label, route: p2.meta.route_label, verify: p2.meta.verify });
  log("    window 2 status:", await page.locator(".slicewin").nth(1).locator(".sw-status").textContent());
  await page.screenshot({ path: `${OUT}/07f_tilted_plane2.png` });

  // (8) drag plane 1 by its gizmo (translate along the normal)
  await page.locator(".slicewin").nth(0).click();
  await sleep(300);
  const o1 = S5.planes.find((P) => P.id === 1);
  let moved = false;
  for (const dist of [1.2, 2.0, 3.0, 4.5]) {
    const a = await page.evaluate(({ o, n, d }) => { const s = document.querySelector(".s3d-view").__scene3d; return [s.screenOf(o), s.screenOf([o[0] + d * n[0], o[1] + d * n[1], o[2] + d * n[2]]), s.screenOf([o[0] + 3 * d * n[0], o[1] + 3 * d * n[1], o[2] + 3 * d * n[2]])]; }, { o: o1.origin, n: o1.n, d: dist });
    await page.mouse.move(a[1][0], a[1][1]);
    await page.mouse.down();
    for (let k = 1; k <= 10; k++) await page.mouse.move(a[1][0] + (a[2][0] - a[1][0]) * k / 10, a[1][1] + (a[2][1] - a[1][1]) * k / 10);
    await page.mouse.up();
    await sleep(1500);
    await waitFor(page, planeReady, 1, 60000);
    const P = (await scene(page)).planes.find((q) => q.id === 1);
    if (JSON.stringify(P.meta.origin) !== JSON.stringify(o1.meta.origin)) {
      log(`(8) gizmo drag from ${dist} along the normal: plane 1 origin ${JSON.stringify(o1.meta.origin)} -> ${JSON.stringify(P.meta.origin)}, normal ${JSON.stringify(P.n)}, label ${P.meta.label}, verify ${JSON.stringify(P.meta.verify)}`);
      moved = true;
      break;
    }
  }
  if (!moved) log("(8) gizmo drag: the plane did not move with the tried handle positions");
  await page.screenshot({ path: `${OUT}/07d_after_drag.png` });

  // (9) every element switched off on its own
  const boxes = page.locator(".panel:has(h4:text('Слои сцены')) input[type=checkbox]");
  const nb = await boxes.count();
  const res = [];
  for (let i = 0; i < nb; i++) {
    await boxes.nth(i).uncheck();
    await sleep(150);
    const S = await scene(page);
    res.push([S.layers.filter((L) => !L.objVisible).map((L) => L.id).join("+"), S.planes.filter((P) => !P.visible).map((P) => "plane" + P.id).join("+")]);
    if (i < nb - 1) { await boxes.nth(i).check(); await sleep(100); }
  }
  log(`(9) ${nb} layer checkboxes; each one alone switched off ->`, res);
  await page.screenshot({ path: `${OUT}/07g_last_layer_off.png` });
  await boxes.nth(nb - 1).check();
  // the light alone off
  const lightIdx = (await scene(page)).layers.findIndex((L) => L.id === "light");
  if (lightIdx >= 0) { await boxes.nth(lightIdx).uncheck(); await sleep(300); await page.screenshot({ path: `${OUT}/07g_light_off.png` }); await boxes.nth(lightIdx).check(); }
  // the energy current on
  const fluxIdx = (await scene(page)).layers.findIndex((L) => L.id === "flux");
  if (fluxIdx >= 0) { await boxes.nth(fluxIdx).check(); await boxes.nth(lightIdx).uncheck(); await sleep(400); await page.screenshot({ path: `${OUT}/07h_flux_on_light_off.png` }); await boxes.nth(lightIdx).check(); }

  // (10) remove plane 3 by its window's cross; then the add rule after turning plane 1
  await page.locator(".slicewin").nth(2).locator("button", { hasText: "✕" }).click();
  await sleep(1500);
  await page.locator(".slicewin").nth(1).locator("button", { hasText: "✕" }).click();
  await sleep(1500);
  log("(10) after removing 3 and 2: planes", (await scene(page)).planes.map((P) => P.id), "windows", await page.locator(".slicewin").count());
  await page.locator(".slicewin").nth(0).click();
  await sleep(300);
  await inputs.nth(3).fill("90");
  await inputs.nth(4).fill("300");
  await inputs.nth(4).dispatchEvent("change");
  await sleep(500);
  await waitFor(page, planeReady, 1, 120000);
  await addBtn.click();
  await waitFor(page, planeReady, 2, 120000);
  await addBtn.click();
  await waitFor(page, planeReady, 3, 120000);
  await sleep(800);
  const S6 = await scene(page);
  const M = S6.planes.map((P) => P.n);
  log("    plane 1 turned to theta 90, phi 300; then two '+ Срез':", S6.planes.map((P) => ({ id: P.id, n: P.n })),
    "|n_i.n_j|:", [[0, 1], [0, 2], [1, 2]].map(([a, b]) => Math.abs(M[a][0] * M[b][0] + M[a][1] * M[b][1] + M[a][2] * M[b][2]).toFixed(3)));
  await page.screenshot({ path: `${OUT}/07i_add_after_turn.png` });

  // (11) a new world; the previous world from the record is read-only
  await api(`/api/runs/${id}/command`, { cmd: "new_world", args: { preset: "circle" } });
  await sleep(1000);
  await waitFor(page, () => document.querySelector("#world") && document.querySelector("#world").options.length > 1, null, 60000);
  await waitFor(page, planeReady, 1, 90000);
  const Sw = await scene(page);
  log("(11) new world (circle): planes", Sw.planes.map((P) => ({ id: P.id, origin: P.origin, n: P.n })));
  await page.selectOption("#world", "0");
  await sleep(1500);
  const disabled = await page.evaluate(() => [...document.querySelectorAll(".panel input, .panel button")].filter((e) => e.closest(".panel").querySelector("h4").textContent.startsWith("Срез")).map((e) => e.disabled));
  await page.locator(".slicewin").nth(0).click();
  await sleep(300);
  log("    world 1 from the record: planes", (await scene(page)).planes.map((P) => P.id), "plane panel controls disabled:", disabled.length ? disabled.every(Boolean) : "panel empty",
    "add disabled:", await addBtn.isDisabled(), "banner:", (await page.textContent(".banner").catch(() => "")) || "");
  await page.screenshot({ path: `${OUT}/07j_archived_world.png` });
  await page.selectOption("#world", "1");
  await sleep(1500);
  await page.screenshot({ path: `${OUT}/07k_circle_world.png` });
  log("    page errors:", errors);
  log("    message counts:", counts);
  await api(`/api/runs/${id}/stop`, {});

  // ---------------------------------------------------------------------------------------------------------------
  const r2 = await openRun(browser, { viz: "v08_wave_3d", preset: "double_slices" }, "double_slices");
  await sleep(1500);
  log("(12) slices only, reduced model: top bar", await r2.page.textContent("#physics"));
  log("     window 1 status:", await r2.page.locator(".slicewin").nth(0).locator(".sw-status").textContent());
  const SR = await scene(r2.page);
  log("     layers:", SR.layers.map((L) => L.id), "planes:", SR.planes.map((P) => ({ id: P.id, label: P.meta && P.meta.label, route: P.meta && P.meta.route_label })));
  await r2.page.screenshot({ path: `${OUT}/07l_slices_only.png` });
  await r2.page.locator(".slicewin").nth(0).locator("button", { hasText: "✕" }).click();
  await sleep(1500);
  log("     after removing the reduced plane: top bar", JSON.stringify(await r2.page.textContent("#physics")));
  const runs = await api("/api/runs");
  const me = runs.find ? runs.find((r) => r.id === r2.id) : (runs.runs || []).find((r) => r.id === r2.id);
  log("     run list entry approximations:", me && me.approximations);
  log("     page errors:", r2.errors);
  await api(`/api/runs/${r2.id}/stop`, {});
} catch (e) {
  log("FAILED:", String(e && e.stack || e));
} finally {
  for (const id of started) { try { await api(`/api/runs/${id}/stop`, {}); } catch (e) { /* stopped */ } }
  await browser.close();
  log("runs stopped:", started);
}
