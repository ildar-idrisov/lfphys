// Extra cases of fw_ui.mjs (U9 cancel, U4 placement, U1 repeats and v04's plane); imported by fw_ui.mjs.
export function extraCases({ newRun, page, openRun, play, pauseRec, shot, post, sleep, SIZES }) {
  return {
    // U9: the busy indicator and its cancel on a slow scene change (p02 double slit)
    async u9_cancel() {
      const r = await newRun("p02_quantum", { preset: "double_slit" });
      const p = await page(1600, 1000);
      await openRun(p, r.id);
      await play(p); await sleep(1500);
      const n0 = await p.$$eval(".pg-obj", (x) => x.length);
      await p.evaluate(() => { window.__busySeen = []; new MutationObserver(() => { const b = document.getElementById("busy"); if (b.style.display !== "none") window.__busySeen.push(b.textContent); }).observe(document.getElementById("busy"), { childList: true, subtree: true, attributes: true }); });
      const btn = await p.evaluateHandle(() => [...document.querySelectorAll(".pg-buttons button")].find((x) => /Барьер/.test(x.textContent)));
      await btn.click(); await sleep(600);
      const out = { form: await p.evaluate(() => (document.querySelector(".pg-place") || {}).textContent || null) };
      await shot(p, "u4_place_form_p02_1600");
      await (await p.$(".pg-place button.primary")).click();
      await sleep(2500);
      out.busy_text = await p.evaluate(() => { const b = document.getElementById("busy"); return b.style.display !== "none" ? b.textContent : null; });
      out.palette_disabled_while_busy = await p.$$eval(".pg-buttons button", (bs) => bs.every((b) => b.disabled));
      await shot(p, "u9_busy_p02_1600");
      const cancel = await p.$("#busy button.cancel");
      out.cancel_offered = !!cancel;
      if (cancel) {
        await cancel.click();
        await p.waitForFunction(() => [...document.querySelectorAll(".events .ev")].some((e) => /Отменено/.test(e.textContent)), null, { timeout: 180000 }).catch(() => {});
        await sleep(2000);
        out.after_cancel = { objects: await p.$$eval(".pg-obj", (x) => x.length), objects_before: n0, status: await p.textContent("#status"),
                             notice: await p.$$eval(".events .ev", (es) => es.map((e) => e.textContent).filter((t) => /Отменено/.test(t)).slice(-1)[0] || null),
                             busy: await p.evaluate(() => document.getElementById("busy").style.display !== "none") };
        await shot(p, "u9_after_cancel_p02_1600");
      }
      out.busy_seen = await p.evaluate(() => [...new Set(window.__busySeen)].slice(0, 6));
      out.logs = p.logs;
      await p.ctx.close();
      await post(`/api/runs/${r.id}/stop`);
      return out;
    },
    // U4: the pre-placement form with a point clicked in the 3-D scene (p01)
    async u4_place() {
      const r = await newRun("p01_gravity", { preset: "sun_earth" });
      const out = {};
      for (const [w, h] of SIZES) {
        const p = await page(w, h);
        await openRun(p, r.id);
        const btn = await p.evaluateHandle(() => [...document.querySelectorAll(".pg-buttons button")].find((x) => /Пробное/.test(x.textContent)));
        await btn.click(); await sleep(500);
        const pick = await p.$(".pg-place button:has-text('Указать')");
        out[`pick_button_${w}`] = !!pick;
        if (pick) {
          await pick.click(); await sleep(300);
          const v = await p.$eval(".s3d-view", (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width * 0.62, y: r.top + r.height * 0.45 }; });
          await p.mouse.click(v.x, v.y); await sleep(500);
          out[`point_${w}`] = await p.evaluate(() => (document.querySelector(".pg-place .muted") || {}).textContent || null);
          out[`fields_${w}`] = await p.$$eval(".pg-place .ctl", (cs) => cs.slice(0, 3).map((c) => c.textContent.slice(0, 30) + "=" + (c.querySelector("input") || {}).value));
          // the clicked point drawn back: where scene3d puts it on the screen (should be where we clicked)
          out[`reprojected_${w}`] = await p.evaluate(({ x, y }) => { const api = document.querySelector(".s3d-view").__scene3d; const f = [...document.querySelectorAll(".pg-place .ctl input[type=number]")].slice(0, 3).map((i) => Number(i.value)); const q = api.screenOf(f); return { clicked: [Math.round(x), Math.round(y)], back: q.map(Math.round), xyz: f }; }, v);
        }
        await shot(p, `u4_place_form_p01_${w}`);
        if (w === 1600) {
          const n0 = await p.$$eval(".pg-obj", (x) => x.length);
          await (await p.$(".pg-place button.primary")).click();
          await p.waitForFunction((n) => document.querySelectorAll(".pg-obj").length > n, n0, { timeout: 60000 }).catch(() => {});
          await sleep(800);
          out.placed = { objects: [n0, await p.$$eval(".pg-obj", (x) => x.length)], last_event: await p.$$eval(".events .ev", (es) => es.slice(-1).map((e) => e.textContent)[0]) };
          const last = (await p.$$(".pg-obj")).at(-1); if (last) await last.click(); await sleep(600);
          out.placed.inspector = await p.evaluate(() => { const i = [...document.querySelectorAll(".panel")].find((x) => /Инспектор/.test(x.querySelector("h4").textContent)); return [...i.querySelectorAll(".ctl")].slice(1, 4).map((c) => c.textContent.slice(0, 24) + "=" + (c.querySelector("input") || {}).value); });
          await shot(p, "u4_placed_p01_1600");
        }
        await p.ctx.close();
      }
      await post(`/api/runs/${r.id}/stop`);
      return out;
    },
    // U1: a playground's segment starts repeat the box; the zoom is kept (p01 «inner», segments every 6 s here)
    async u1_repeat() {
      const r = await newRun("p01_gravity", { preset: "inner" });
      const p = await page(1600, 1000);
      await openRun(p, r.id);
      await play(p); await sleep(3000);
      const zoom = () => p.evaluate(() => { const api = document.querySelector(".s3d-view").__scene3d; const a = api.screenOf([0, 0, 0]), q = api.screenOf([1, 0, 0]); return +Math.hypot(q[0] - a[0], q[1] - a[1]).toFixed(2); });
      const z0 = await zoom();
      const v = await p.$eval(".s3d-view", (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
      await p.mouse.move(v.x, v.y); for (let i = 0; i < 4; i++) { await p.mouse.wheel(0, -300); await sleep(150); }
      await sleep(800);
      const z1 = await zoom(), series = [];
      for (let i = 0; i < 20; i++) { await sleep(1000); series.push(await zoom()); }
      const out = { zoom_before: z0, zoom_after_wheel: z1, zoom_series: series, repeats_dropped: await p.evaluate(() => window.__lfPlayer.dbg.repeats) };
      await shot(p, "u1_repeat_p01_1600");
      await p.ctx.close();
      await post(`/api/runs/${r.id}/stop`);
      return out;
    },
    // U1: v04's plane after a wheel zoom, steps back along the timeline and back to the end (Plane.fit counted)
    async u1_v04() {
      const r = await newRun("v04_orbits", { preset: "default" });
      const p = await page(1600, 1000);
      await openRun(p, r.id);
      await play(p); await sleep(5000); await pauseRec(p);
      await p.evaluate(async () => { const m = await import("/static/js/canvas.js"); const f = m.Plane.prototype.fit; window.__fits = 0; m.Plane.prototype.fit = function (...a) { window.__fits++; return f.apply(this, a); }; });
      const cv = await p.$eval("#center canvas", (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
      await p.mouse.move(cv.x, cv.y); for (let i = 0; i < 5; i++) { await p.mouse.wheel(0, -200); await sleep(100); }
      await sleep(500);
      await p.keyboard.press("Home"); await sleep(1200); await p.keyboard.press("End"); await sleep(1200);
      const tl = await p.$("#timeline"); const b = await tl.boundingBox();
      await p.mouse.click(b.x + b.width * 0.3, b.y + b.height / 2); await sleep(1000);
      await p.keyboard.press("End"); await sleep(1000);
      const out = { fits_after_wheel_and_scrub: await p.evaluate(() => window.__fits) };
      await shot(p, "u1_v04_after_scrub_1600");
      await p.ctx.close();
      await post(`/api/runs/${r.id}/stop`);
      return out;
    },

    // U9: a slow command (a new v08 world: tens of seconds on the CPU) is shown with what it does and its seconds, and
    // ✕ cancels it: the world goes back to just before it (the old world goes on)
    async u9_cancel_v08() {
      const r = await newRun("v08_wave_3d", { params: { n: 128, zmax: 10.0 } });
      const p = await page(1600, 1000);
      await p.goto(`http://127.0.0.1:${process.env.PORT || "8572"}/run?id=${r.id}`);
      const out = {};
      // the first world's build is shown too
      await sleep(2500);
      out.busy_build = await p.evaluate(() => { const b = document.getElementById("busy"); return b.style.display !== "none" ? b.textContent : null; });
      await p.waitForFunction(() => window.__lfPlayer && window.__lfPlayer.frames() > 0 && !/загрузка/.test(document.getElementById("status").textContent), null, { timeout: 400000 });
      await sleep(1500);
      await post(`/api/runs/${r.id}/command`, { cmd: "new_world", args: { params: { n: 128, zmax: 20.0 } } });
      await p.waitForSelector("#busy button.cancel", { timeout: 60000 }).catch(() => {});
      await sleep(3000);
      out.busy_text = await p.evaluate(() => { const b = document.getElementById("busy"); return b.style.display !== "none" ? b.textContent : null; });
      await shot(p, "u9_busy_v08_1600");
      const cancel = await p.$("#busy button.cancel");
      out.cancel_offered = !!cancel;
      if (cancel) {
        await cancel.click();
        await p.waitForFunction(() => [...document.querySelectorAll(".events .ev")].some((e) => /Отменено/.test(e.textContent)), null, { timeout: 400000 }).catch(() => {});
        await p.waitForFunction(() => !/восстанавливается/.test(document.getElementById("status").textContent), null, { timeout: 400000 }).catch(() => {});
        await sleep(2000);
        out.after_cancel = { status: await p.textContent("#status"), worlds: await p.$$eval("#world option", (o) => o.length),
                             notice: await p.$$eval(".events .ev", (es) => es.map((e) => e.textContent).filter((t) => /Отменено/.test(t)).slice(-1)[0] || null),
                             busy: await p.evaluate(() => document.getElementById("busy").style.display !== "none") };
        const meta = await (await fetch(`http://127.0.0.1:${process.env.PORT || "8572"}/api/runs/${r.id}`)).json();
        out.after_cancel.passport = { state: meta.state, worlds: (meta.worlds || []).length, resumes: (meta.resumes || []).map((x) => x.from) };
        await shot(p, "u9_after_cancel_v08_1600");
      }
      out.logs = p.logs;
      await p.ctx.close();
      await post(`/api/runs/${r.id}/stop`);
      return out;
    },
    // UX-3d A6 (the playground's part): «◎ Центрировать» and «👁 Следить» on the selected object (p01: the Earth)
    async a6_center_follow() {
      const r = await newRun("p01_gravity", { preset: "sun_earth" });
      const p = await page(1600, 1000);
      await openRun(p, r.id);
      await play(p); await sleep(1500);
      const cam = () => p.evaluate(() => { const c = document.querySelector(".s3d-view").__scene3d.cameraState(); return { t: c.target.map((x) => +x.toFixed(4)), r: +Math.hypot(c.target[0], c.target[1]).toFixed(4), d: +Math.hypot(c.pos[0] - c.target[0], c.pos[1] - c.target[1], c.pos[2] - c.target[2]).toFixed(3) }; });
      const followOn = () => p.evaluate(() => { const b = document.querySelector(".pg-cam button.toggle"); return b ? b.classList.contains("on") : null; });
      const out = { cam0: await cam() };
      const earth = await p.evaluateHandle(() => [...document.querySelectorAll(".pg-obj")].find((x) => /Земля/.test(x.textContent)));
      await earth.asElement().click(); await sleep(600);
      await (await p.$(".pg-cam button:has-text('Центрировать')")).click(); await sleep(400);
      out.after_center = await cam();
      await (await p.$(".pg-cam button.toggle")).click(); await sleep(300);
      out.follow_on = await followOn();
      const series = [];
      for (let i = 0; i < 6; i++) { await sleep(700); series.push(await cam()); }
      out.following = series;
      out.eye_shown = await p.evaluate(() => [...document.querySelectorAll(".pg-eye")].filter((e) => e.style.display !== "none").length);
      await shot(p, "a6_follow_p01_1600");
      // a wheel zoom keeps following
      const v = await p.$eval(".s3d-canvas", (e) => { const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; });
      await p.mouse.move(v.x, v.y); await p.mouse.wheel(0, -200); await sleep(800);
      out.after_zoom = { on: await followOn(), cam: await cam() };
      // a rotation by hand stops it
      await p.mouse.move(v.x, v.y); await p.mouse.down(); await p.mouse.move(v.x + 80, v.y + 30, { steps: 6 }); await p.mouse.up(); await sleep(800);
      out.after_rotate = { on: await followOn(), toasts: await p.$$eval(".toast", (ts) => ts.map((t) => t.textContent)).catch(() => []) };
      // following again, then the object removed: it stops
      await (await p.$(".pg-cam button.toggle")).click(); await sleep(500);
      out.on_again = await followOn();
      await (await earth.asElement().$("button[title^='Удалить']")).click(); await sleep(2500);
      out.after_remove = { eye_shown: await p.evaluate(() => [...document.querySelectorAll(".pg-eye")].filter((e) => e.style.display !== "none").length), toggle: await followOn() };
      await pauseRec(p);
      await p.ctx.close();
      await post(`/api/runs/${r.id}/stop`);
      return out;
    },
  };
}
