// The review's probes (scripts/probe.mjs, copied and changed for its processing): the same cases, run with the code
// before the processing ("orig") or after it ("new") in the same environment (lib.mjs of this folder). Changed: the
// variant argument; twoplanes recolours the planes through the uniforms of either version; boxjump also records the
// camera after a step back in the history (env3d restores the header's box); labels (A9) and dblclick (A6) added.
// usage: node probe_ab.mjs <port> <case> <orig|new> [outDir]
import fs from "node:fs";
import { launch, startRun, openPage, shot, settle, sleep, mk } from "./lib.mjs";

const [port, which, variant, outA] = process.argv.slice(2);
const base = `http://127.0.0.1:${port}`;
const out = `${outA || "/pw/out"}/probe_${which}_${variant}`;
fs.mkdirSync(out, { recursive: true });
const { post } = mk(base);
const res = { case: which, variant };
const errs = [];
const br = await launch();

// pixel (r, g, b) of the 3-D canvas at a physics point (the drawing buffer is preserved)
const pixelAt = (page, p) => page.evaluate((p) => {
  const api = document.querySelector(".s3d-view").__scene3d; api.render();
  const c = api.__renderer.domElement, r = c.getBoundingClientRect(), [sx, sy] = api.screenOf(p);
  const gl = api.__renderer.getContext(), px = new Uint8Array(4);
  const x = Math.round((sx - r.left) * c.width / r.width), y = Math.round(c.height - (sy - r.top) * c.height / r.height);
  gl.readPixels(x, y, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
  return [px[0], px[1], px[2]];
}, p);

const cmd = (id, c, args) => post(`/api/runs/${id}/command`, { cmd: c, args });

try {
  if (which === "volsphere") {
    // v13 2pz: two opaque probe spheres placed with the cloud's densest point between them: one IN FRONT of it, one
    // BEHIND it (on rays offset sideways so that both are seen through the lobe). The cloud's density is raised with
    // its own slider (as a user can) so that the lobe is clearly visible
    const id = await startRun(base, "v13_hydrogen_3d", { preset: "2pz" });
    const page = await openPage(br, base, id, { errs, playMs: 6000, variant });
    await sleep(2000); await settle(page);
    const geo = await page.evaluate(() => {
      const api = document.querySelector(".s3d-view").__scene3d; api.view("iso");
      for (const P of api.planes()) api.setPlaneVisible(P.id, false);  // the cloud alone
      api.setVolumeLook({ density: 0.05 * Math.pow(10, 80 / 33) }, true);  // the density slider at 80 %
      const cam = api.__camera, S = api.state, T2P = (v) => [-v.z, v.y, v.x], P2T = (p) => [p[2], p[1], -p[0]];
      // the densest point of the volume (the lobe)
      const [nz, nx, ny] = S.vol.dims, d = S.vol.data, [lo, hi] = S.box; let best = -1, bi = 0;
      for (let i = 0; i < d.length; i++) if (d[i] > best) { best = d[i]; bi = i; }
      const iz = Math.floor(bi / (nx * ny)), ix = Math.floor((bi % (nx * ny)) / ny), iy = bi % ny;
      const pk = [lo[0] + (hi[0] - lo[0]) * ix / (nx - 1), lo[1] + (hi[1] - lo[1]) * iy / (ny - 1), lo[2] + (hi[2] - lo[2]) * iz / (nz - 1)];
      // the lobe's peak and its mirror image through the nucleus (the other lobe): the BACK sphere sits right behind
      // one lobe's peak on the line of sight, the FRONT sphere right in front of the other lobe's peak
      const c = cam.position.clone(), V = c.constructor;
      const pkT = new V(...P2T(pk)), pk2T = new V(...P2T(pk.map((q) => -q)));
      const size = S.size, r = 0.03 * size;
      const back = pkT.clone().addScaledVector(pkT.clone().sub(c).normalize(), 0.15 * size);
      const front = pk2T.clone().addScaledVector(pk2T.clone().sub(c).normalize(), -0.15 * size);
      return { peak: pk, front: T2P(front), back: T2P(back), r, box: S.box, frontVal: api.sampleVolume(T2P(front)), backVal: api.sampleVolume(T2P(back)) };
    });
    res.geo = geo;
    await settle(page);
    await shot(page, `${out}/a_cloud_only.jpg`);
    res.cloudAtFront = await pixelAt(page, geo.front);
    res.cloudAtBack = await pixelAt(page, geo.back);
    await page.evaluate((g) => {
      const api = document.querySelector(".s3d-view").__scene3d;
      api.setSpheres("probe", new Float32Array([...g.front, ...g.back]), new Float32Array([g.r, g.r]), new Float32Array([0.2, 1, 0.3, 0.2, 1, 0.3]), { label: "probe", minFrac: 0 });
    }, geo);
    await settle(page);
    await shot(page, `${out}/b_cloud_with_spheres.jpg`);
    res.withFront = await pixelAt(page, geo.front);
    res.withBack = await pixelAt(page, geo.back);
    await page.evaluate(() => { const api = document.querySelector(".s3d-view").__scene3d; api.setLayerVisible("cloud", false); });
    await settle(page);
    res.sphereAloneFront = await pixelAt(page, geo.front);
    res.sphereAloneBack = await pixelAt(page, geo.back);
    await shot(page, `${out}/c_spheres_only.jpg`);
    await page.close();
  } else if (which === "planevol") {
    // v13 2pz: the default slice plane against the cloud: plane on / off, from iso and from above
    const id = await startRun(base, "v13_hydrogen_3d", { preset: "2pz" });
    const page = await openPage(br, base, id, { errs, playMs: 6000, variant });
    await sleep(3000); await settle(page);
    res.planes = await page.evaluate(() => document.querySelector(".s3d-view").__scene3d.planes().map((P) => ({ id: P.id, label: (P.meta || {}).label, data: !!P.data })));
    await shot(page, `${out}/a_plane_on.jpg`);
    await page.evaluate(() => { const api = document.querySelector(".s3d-view").__scene3d; for (const P of api.planes()) api.setPlaneVisible(P.id, false); });
    await settle(page);
    await shot(page, `${out}/b_plane_off.jpg`);
    await page.close();
  } else if (which === "twoplanes") {
    // v13 1s with planes 1 (default) and 2 (x = 0, added like «＋ Срез»): which plane is drawn where they cross.
    // A/B: the planes recoloured flat (plane 1 red, plane 2 green, opaque) with the CURRENT depth settings, then with
    // depthWrite on (the proposed fix)
    const id = await startRun(base, "v13_hydrogen_3d", { preset: "1s" });
    const page = await openPage(br, base, id, { errs, playMs: 3000, variant });
    await cmd(id, "view", { op: "plane", id: 2, origin: [0, 0, 0], normal: [1, 0, 0] });
    await sleep(6000); await settle(page);
    res.planes = await page.evaluate(() => document.querySelector(".s3d-view").__scene3d.planes().map((P) => ({ id: P.id, label: (P.meta || {}).label, n: P.n })));
    await shot(page, `${out}/a_as_shown.jpg`);
    for (const dw of [false, true]) {
      await page.evaluate((dw) => {
        const api = document.querySelector(".s3d-view").__scene3d;
        api.setLayerVisible("cloud", false);
        const cols = { 1: [1, 0, 0], 2: [0, 1, 0], 3: [0, 0, 1] };
        for (const P of api.planes()) {
          P.mat.uniforms.uMode.value = 2;
          if (P.mat.uniforms.uDim) { P.mat.uniforms.uColor.value.setRGB(...cols[P.id]); P.mat.uniforms.uDim.value = 1 / 0.3; }  // the new opaque planes
          else { P.mat.uniforms.uColor.value.setRGB(...cols[P.id].map((c) => c / 0.35)); P.mat.uniforms.uOpacity.value = 1 / 0.35; P.mat.depthWrite = dw; P.mat.needsUpdate = true; }
        }
        api.view("iso");
      }, dw);
      await settle(page);
      await shot(page, `${out}/${dw ? "c_depthwrite_on" : "b_current"}.jpg`);
      // which colour wins at points of plane 2 in front of / behind plane 1 (plane 1 is y = 0 or z = 0; plane 2 x = 0)
      res[dw ? "fix" : "current"] = await page.evaluate(() => {
        const api = document.querySelector(".s3d-view").__scene3d, S = api.state, [lo, hi] = S.box, s = 0.3 * (hi[0] - lo[0]);
        const P1 = api.planes().find((p) => p.id === 1), n1 = P1.n;
        // two points on plane 2 (x = 0) on both sides of plane 1, inside the box
        const pts = [[0, s * n1[1], s * n1[2]], [0, -s * n1[1], -s * n1[2]]].map((p) => [p[0] + 0.0, p[1] + (n1[2] ? s * 0.5 : 0), p[2] + (n1[1] ? s * 0.5 : 0)]);
        const cam = api.__camera.position, T2P = (v) => [-v.z, v.y, v.x], c = T2P(cam);
        api.render();
        const gl = api.__renderer.getContext(), cv = api.__renderer.domElement, r = cv.getBoundingClientRect();
        return pts.map((p) => {
          const [sx, sy] = api.screenOf(p), px = new Uint8Array(4);
          gl.readPixels(Math.round((sx - r.left) * cv.width / r.width), Math.round(cv.height - (sy - r.top) * cv.height / r.height), 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px);
          // is plane 2's point on the camera's side of plane 1 (then plane 2 must win there)?
          const side = (p[0] * n1[0] + p[1] * n1[1] + p[2] * n1[2]) * (c[0] * n1[0] + c[1] * n1[1] + c[2] * n1[2]) > 0;
          return { p, plane2InFront: side, rgb: [px[0], px[1], px[2]] };
        });
      });
    }
    await page.close();
  } else if (which === "volcost") {
    // the ray-marched volume's share of a frame: v13 1s at a 1600 x 1000 page, cloud on / off, at pixel ratio 1 and 2
    // (a HiDPI laptop), and with 64 instead of 160 steps (software GL: ratios only)
    const id = await startRun(base, "v13_hydrogen_3d", { preset: "1s" });
    const page = await openPage(br, base, id, { errs, playMs: 4000, variant });
    await sleep(1500); await settle(page);
    res.cost = await page.evaluate(() => {
      const api = document.querySelector(".s3d-view").__scene3d, R = api.__renderer, gl = R.getContext();
      const time = (n = 4) => { api.render(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));
        const t0 = performance.now(); for (let i = 0; i < n; i++) api.render(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); return +((performance.now() - t0) / n).toFixed(1); };
      const out = {};
      const vol = api.layers().find((L) => L.kind === "volume");
      for (const pr of [1, 2]) {
        R.setPixelRatio(pr); const c = R.domElement; R.setSize(c.clientWidth, c.clientHeight, false);
        out[`px${pr}`] = [c.width, c.height];
        out[`on_pr${pr}`] = time();
        api.state.volMat.uniforms.uSteps.value = 64; out[`on64_pr${pr}`] = time(); api.state.volMat.uniforms.uSteps.value = 160;
        vol.obj.visible = false; out[`off_pr${pr}`] = time(); vol.obj.visible = true;
      }
      R.setPixelRatio(1); const c = R.domElement; R.setSize(c.clientWidth, c.clientHeight, false);
      return out;
    });
    await page.close();
  } else if (which === "zfight") {
    // v08 double: the light volume seen against the back face of the screen (z = 0, the box's own face): the target
    // and the slice hidden, the camera behind the screen looking back at it through the light
    const id = await startRun(base, "v08_wave_3d", { preset: "double" });
    const page = await openPage(br, base, id, { errs, playMs: 8000, variant });
    await sleep(2000); await settle(page);
    await page.evaluate(() => {
      const api = document.querySelector(".s3d-view").__scene3d;
      api.setLayerVisible("target", false); for (const P of api.planes()) api.setPlaneVisible(P.id, false);
      const o = api.__orbit, cam = api.__camera, S = api.state, [lo, hi] = S.box;
      const P2T = (p) => [p[2], p[1], -p[0]];
      const t = P2T([0, 0, 0.5 * hi[2]]); o.target.set(...t);
      const c = P2T([0.35 * hi[0], 0.25 * hi[1], 1.6 * hi[2]]); cam.position.set(...c); o.update();
    });
    await settle(page);
    await shot(page, `${out}/a_through_light.jpg`);
    await page.evaluate(() => { const api = document.querySelector(".s3d-view").__scene3d; api.setLayerVisible("screen", false); });
    await settle(page);
    await shot(page, `${out}/b_screen_hidden.jpg`);
    await page.evaluate(() => { const api = document.querySelector(".s3d-view").__scene3d; api.setLayerVisible("screen", true); api.setLayerVisible("light", false); });
    await settle(page);
    await shot(page, `${out}/c_light_hidden.jpg`);
    await page.close();
  } else if (which === "boxjump") {
    // p01 «inner» (Newton, bodies going out): the user turns and zooms the view, then the run widens its box: does the
    // camera stay where the user put it?
    const id = await startRun(base, "p01_gravity", { preset: "pythagorean" });
    const page = await openPage(br, base, id, { errs, playMs: 1500, variant });
    await settle(page);
    const { drag, wheel } = await import("./lib.mjs");
    await drag(page, 260, -120); await wheel(page, -100, 8);
    page.on("crash", () => { res.crashed = true; });
    const withTimeout = (pr, ms) => Promise.race([pr, new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms))]);
    const cam = () => withTimeout(page.evaluate(() => { const a = document.querySelector(".s3d-view").__scene3d; return { pos: a.__camera.position.toArray().map((v) => +v.toFixed(3)), target: a.__orbit.target.toArray().map((v) => +v.toFixed(3)), dist: +a.__camera.position.distanceTo(a.__orbit.target).toFixed(3), box: JSON.stringify(a.state.box), lastView: a.state.lastView }; }), 20000);
    res.before = await cam();
    console.error("before", JSON.stringify(res.before));
    await shot(page, `${out}/a_user_view.jpg`);
    const t0 = Date.now(); res.samples = [];
    while (Date.now() - t0 < 90000) {
      await sleep(1000);
      let c; try { c = await cam(); } catch (e) { res.sampleError = String(e); break; }
      res.samples.push(c);
      if (c.box !== res.before.box) break;
    }
    res.after = res.samples[res.samples.length - 1];
    await settle(page);
    await shot(page, `${out}/b_after_box_grew.jpg`);
    // the player's history: back to the first frames (the header's box restored), the camera then
    await page.evaluate(() => window.__lfPlayer.goTo(Math.round(0.02 * (window.__lfPlayer.frames() - 1))));
    await sleep(1500); await settle(page);
    res.afterScrub = await cam();
    await shot(page, `${out}/c_after_scrub.jpg`);
    await page.close();
  } else if (which === "theme") {
    // the 3-D view in the light (default) and the dark theme: v09 thomas (planes, labels, the legend panel)
    const id = await startRun(base, "v09_thomas_3d", { preset: "thomas" });
    const page = await openPage(br, base, id, { errs, playMs: 4000, variant });
    await sleep(1500); await settle(page);
    await shot(page, `${out}/a_light.jpg`, { full: true });
    await page.evaluate(() => { document.documentElement.setAttribute("data-theme", "dark"); });
    await settle(page);
    await shot(page, `${out}/b_dark.jpg`, { full: true });
    await page.close();
  } else if (which === "faint") {
    // v13 1s, the cloud alone (slice hidden): its default look, and the density slider at the top
    const id = await startRun(base, "v13_hydrogen_3d", { preset: "1s" });
    const page = await openPage(br, base, id, { errs, playMs: 4000, variant });
    await sleep(1500); await settle(page);
    res.look = await page.evaluate(() => { const api = document.querySelector(".s3d-view").__scene3d; api.view("iso"); for (const P of api.planes()) api.setPlaneVisible(P.id, false);
      const S = api.state; const d = S.volBox.mx.clone().sub(S.volBox.mn).length(); return { look: api.volumeLook(), diag: d, dt: d / 160 }; });
    await settle(page);
    await shot(page, `${out}/a_default_look.jpg`);
    await page.evaluate(() => { document.querySelector(".s3d-view").__scene3d.setVolumeLook({ density: 0.05 * Math.pow(10, 100 / 33) }, true); });
    await settle(page);
    await shot(page, `${out}/b_slider_max.jpg`);
    await page.close();
  } else if (which === "layerspanel") {
    // while a world plays, how often is the panel «Слои сцены» rebuilt (its inputs replaced)? p01 (trails) and p02 3-D
    // (a volume with its density slider)
    res.worlds = {};
    for (const [viz, preset] of [["p01_gravity", "sun_earth"], ["p02_quantum", "ball_3d"], ["v16_optical_vortices", "lg3"]]) {
      const id = await startRun(base, viz, { preset });
      const page = await openPage(br, base, id, { errs, playMs: 3000, variant });
      const r = await page.evaluate(() => new Promise((done) => {
        // the layers panel: the element that holds the layer checkboxes
        const cb = [...document.querySelectorAll("label.s3d-layer input[type=checkbox]")][0];
        const box = cb ? cb.closest("label").parentElement.parentElement : null;
        if (!box) { done({ error: "no layers panel" }); return; }
        let muts = 0; const first = box.querySelector("input");
        const mo = new MutationObserver((l) => { muts += l.filter((m) => m.type === "childList").length; });
        mo.observe(box, { childList: true, subtree: true });
        const t0 = performance.now();
        setTimeout(() => { mo.disconnect(); done({ secs: (performance.now() - t0) / 1000, childListMutations: muts, firstInputReplaced: !first.isConnected, hasRange: !!box.querySelector("input[type=range]") }); }, 10000);
      }));
      res.worlds[viz] = r;
      await page.close();
    }
  } else if (which === "flat") {
    // p03 maxwell: atoms as drawn (MeshBasicMaterial) and the same instances with a lit material (A/B)
    const id = await startRun(base, "p03_molecules", { preset: "liquid_vapour" });
    const page = await openPage(br, base, id, { errs, playMs: 8000, variant });
    await sleep(2000); await settle(page);
    await post(`/api/runs/${id}/command`, { cmd: "pause" });
    await sleep(800); await settle(page);
    await shot(page, `${out}/a_basic.jpg`);
    res.layers = await page.evaluate(() => document.querySelector(".s3d-view").__scene3d.layers().map((L) => [L.id, L.kind]));
    // B: the same instances with a lit material of the same library, lit by the scene's own lights; the view's
    // render() replaces only matrices and colours, so the material stays (the run is paused)
    // (the new code draws the atoms lit already: its "b" is the view as drawn)
    if (variant === "orig") await page.evaluate(async () => {
      const THREE = await import("three");
      const api = document.querySelector(".s3d-view").__scene3d;
      for (const L of api.layers().filter((q) => q.kind === "spheres")) L.obj.material = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.5, metalness: 0.0 });
      api.requestRender();
    });
    await settle(page);
    await shot(page, `${out}/b_lit.jpg`);
    // zoomed crops of both (the same camera)
    await page.evaluate(() => { const o = document.querySelector(".s3d-view").__scene3d.__orbit; o.object.position.lerp(o.target, 0.55); o.update(); });
    await settle(page);
    await shot(page, `${out}/d_lit_zoom.jpg`);
    if (variant === "orig") await page.evaluate(async () => {
      const THREE = await import("three");
      const api = document.querySelector(".s3d-view").__scene3d;
      for (const L of api.layers().filter((q) => q.kind === "spheres")) L.obj.material = new THREE.MeshBasicMaterial({ color: 0xffffff });
      api.requestRender();
    });
    await settle(page);
    await shot(page, `${out}/c_basic_zoom.jpg`);
    await page.close();
  }
} catch (e) { res.failed = String(e && e.stack || e).slice(0, 800); }
res.errors = errs.slice(0, 8);
await br.close();
fs.writeFileSync(`${out}/probe.json`, JSON.stringify(res, null, 1));
console.log(JSON.stringify(res));
