// w01: every world in each language — a preset, recording, a live change, a refusal, an action, the help, every panel
// (Physics of this world, checks, events, instruments, about), for playgrounds the palette, the inspector and the
// carry-over; each step scanned (r_lib.scan) and photographed.
// usage: WORLDS=v01_light_travel,... LANGS=en,ru run_pw.sh w01_worlds.mjs
import { browser, newPage, post, get, del, sleep, startRun, waitPlayer, shot, scan, setLog, log, base, openPanel, SMALL } from "./r_lib.mjs";

const vizList = await get("/api/viz");
const WORLDS = (process.env.WORLDS || vizList.map((v) => v.id).join(",")).split(",").filter(Boolean);
const LANGS = (process.env.LANGS || "en,ru").split(",");
const HEAVY = new Set(["v08_wave_3d", "v09_thomas_3d", "v11_double_slit_2d", "v12_arrival_times_2d", "v13_hydrogen_3d", "v14_quarkonium_3d", "v15_kerr_shadow", "v17_mie_scattering", "p02_quantum", "p04_fluids"]);
setLog("w01_" + (process.env.TAG || WORLDS[0]));
const br = await browser();

const toastsInit = () => {
  window.__toasts = [];
  new MutationObserver((ms) => { for (const m of ms) for (const n of m.addedNodes) if (n.nodeType === 1 && n.classList && n.classList.contains("toast")) window.__toasts.push(n.textContent.replace(/^✕/, "")); })
    .observe(document, { childList: true, subtree: true });
};
const takeToasts = (p) => p.evaluate(() => { const a = window.__toasts || []; window.__toasts = []; return a; });

for (const viz of WORLDS) {
  const v = vizList.find((x) => x.id === viz);
  const pg = v.kind === "playground";
  for (const L of LANGS) {
    const tag = `${viz}_${L}`;
    const ctx = await br.newContext({ viewport: { width: Number(process.env.W || 1600), height: 1000 } });
    await ctx.addInitScript(toastsInit);
    const page = await newPage(ctx, tag);
    const presets = v.schema.presets || [];
    const preset = presets.length ? presets[0].id : null;
    const r = await startRun({ viz, seed: 3, params: SMALL[viz] || {}, ...(preset ? { preset } : {}) });
    if (!r.id) { log({ tag, startFailed: r }); await ctx.close(); continue; }
    const id = r.id;
    try {
      await page.goto(`${base}/run?id=${id}&lang=${L}`);
      await waitPlayer(page);
      await sleep(1000);
      // record 4 s
      await page.click("#rec"); await sleep(4000); await page.click("#rec"); await sleep(1500);
      await scan(page, L, `${tag} 1 after recording`);
      await shot(page, `w01_${tag}_1_run`);
      // a live change: the first number field of the set-up with a slider (value × 1.1 or +1), Enter
      const live = await page.evaluate(() => {
        const box = [...document.querySelectorAll("#left .panel")].find((p) => p.querySelector("input[type=range]"));
        if (!box) return null;
        const inp = [...box.querySelectorAll("input[type=number]")].find((e) => !e.disabled && e.offsetParent !== null);
        if (!inp) return null;
        inp.id = inp.id || "rv-live";
        const lab = inp.closest(".ctl, .field")?.querySelector("label")?.textContent;
        return { id: inp.id, value: inp.value, min: inp.min, max: inp.max, label: lab };
      });
      try {
      if (live) {
        const x = Number(live.value);
        const nv = x === 0 ? (Number(live.max) > 0 ? Math.min(1, Number(live.max)) : 1) : x * 1.1;
        await page.fill(`#${live.id}`, String(Number(nv.toPrecision(4)))); await page.press(`#${live.id}`, "Enter");
        await sleep(2500);
        log({ tag, live, newValue: nv, toasts: await takeToasts(page) });
        // a refusal: a value far outside
        await page.fill(`#${live.id}`, "-1e12"); await page.press(`#${live.id}`, "Enter");
        await sleep(2500);
        const errs = await page.evaluate(() => [...document.querySelectorAll(".ctl-err, .field-err")].map((e) => e.textContent).filter(Boolean));
        log({ tag, refusal: { errs, toasts: await takeToasts(page) } });
        await scan(page, L, `${tag} 2 after live change + refusal`);
        await shot(page, `w01_${tag}_2_refusal`);
      } else log({ tag, live: "no live number field" });
      } catch (e) { log({ tag, liveStepError: e.message.slice(0, 200) }); }
      // an action
      const act = await page.evaluate(() => { const p = [...document.querySelectorAll("#left .panel")].find((x) => /Actions|Действия/.test(x.querySelector("h4").textContent)); const b = p && [...p.querySelectorAll(".body button")].find((b) => !b.disabled); if (b) { b.click(); return b.textContent; } return null; });
      if (act) { await sleep(2500); log({ tag, action: act, toasts: await takeToasts(page) }); }
      // the help
      await page.click("#help"); await sleep(800);
      await scan(page, L, `${tag} 3 help`);
      const mh = await page.$(".modal > div");
      if (mh) { try { await mh.screenshot({ path: `/shots/w01_${tag}_3_help.png` }); } catch (e) { log({ tag, e: e.message }); } }
      await page.keyboard.press("Escape"); await sleep(300);
      // every panel open, sweep box and instrument groups open, the first quantity ticked
      await openPanel(page, /./);
      await page.evaluate(() => { for (const d of document.querySelectorAll("#right details, #left details")) d.open = true; });
      await sleep(600);
      await page.evaluate(() => { const cb = document.querySelector(".in-q input[type=checkbox]"); if (cb && !cb.checked) cb.click(); });
      await sleep(1200);
      // a click on the first event
      await page.evaluate(() => { const e = document.querySelector(".events .ev"); if (e) e.click(); });
      await sleep(1200);
      await scan(page, L, `${tag} 4 all panels`);
      for (const side of ["left", "right"]) {
        const panels = await page.$$(`#${side} .panel`);
        let k = 0;
        for (const p of panels) {
          const h = await p.evaluate((e) => e.querySelector("h4").textContent);
          try { await p.screenshot({ path: `/shots/w01_${tag}_4_${side}${String(k).padStart(2, "0")}.png` }); } catch (e) { /* hidden */ }
          log({ tag, panelShot: `w01_${tag}_4_${side}${String(k).padStart(2, "0")}.png`, h });
          k++;
        }
      }
      // back to the end
      await page.keyboard.press("End"); await sleep(800);
      if (pg) {
        // the palette: the first enabled type → the placement form → Place
        const ot = await page.evaluate(() => { const b = [...document.querySelectorAll(".pg-buttons button")].find((x) => !x.disabled); if (b) { b.click(); return b.textContent; } return null; });
        await sleep(800);
        if (ot) {
          await scan(page, L, `${tag} 5 placement form`);
          const pl = await page.$(".pg-place");
          if (pl) await pl.screenshot({ path: `/shots/w01_${tag}_5_place.png` });
          const placeTxt = await page.evaluate(() => document.querySelector(".pg-place .name")?.textContent);
          await page.evaluate(() => { const b = document.querySelector(".pg-place button.primary"); if (b && !b.disabled) b.click(); });
          await sleep(3000);
          log({ tag, palette: ot, placeHead: placeTxt, toasts: await takeToasts(page) });
        }
        // the inspector: the last object of the list
        const obj = await page.evaluate(() => { const rows = document.querySelectorAll(".pg-obj"); const r = rows[rows.length - 1]; if (r) { r.click(); return r.textContent; } return null; });
        await sleep(1200);
        if (obj) {
          const ins = await page.evaluate(() => {
            const p = [...document.querySelectorAll("#left .panel")].find((x) => x.querySelector(".pg-insp, input") && /Inspector|Инспектор/.test(x.querySelector("h4").textContent));
            if (!p) return null;
            const inp = [...p.querySelectorAll("input[type=number]")].find((e) => !e.disabled);
            if (inp) inp.id = "rv-insp";
            return { has: !!inp, value: inp && inp.value };
          });
          if (ins && ins.has) {
            const x = Number(ins.value);
            await page.fill("#rv-insp", String(x === 0 ? 0.5 : Number((x * 0.9).toPrecision(4)))); await page.press("#rv-insp", "Enter"); await sleep(2000);
            log({ tag, inspectorEdit: ins, toasts: await takeToasts(page) });
            await page.fill("#rv-insp", "1e30"); await page.press("#rv-insp", "Enter"); await sleep(2000);
            log({ tag, inspectorRefusal: { errs: await page.evaluate(() => [...document.querySelectorAll(".ctl-err, .field-err")].map((e) => e.textContent).filter(Boolean)), toasts: await takeToasts(page) } });
          }
          await scan(page, L, `${tag} 6 inspector`);
          const ip = await page.evaluateHandle(() => [...document.querySelectorAll("#left .panel")].find((x) => /Inspector|Инспектор/.test(x.querySelector("h4").textContent)));
          try { await ip.asElement().screenshot({ path: `/shots/w01_${tag}_6_inspector.png` }); } catch (e) { /* none */ }
          log({ tag, selected: obj });
        }
      }
      // the new world: the second scenario chosen (its note read); started for the light worlds; a playground carries
      // its scene over (no scenario)
      const nw = await page.evaluate((pg) => {
        const p = [...document.querySelectorAll("#left .panel")].find((x) => /New world|Новый мир/.test(x.querySelector("h4").textContent));
        if (!p) return null;
        if (p.classList.contains("closed")) p.querySelector("h4").click();
        const sel = p.querySelector(".body > div > .ctl select") || p.querySelector("select");
        let note = null;
        if (!pg && sel && sel.options.length > 2) { sel.value = sel.options[2].value; sel.dispatchEvent(new Event("change")); }
        note = p.querySelector(".help + .ctl + .help, .help:nth-of-type(2)")?.textContent;
        const opts = sel ? [...sel.options].map((o) => o.textContent) : [];
        return { opts, note, notes: [...p.querySelectorAll(".help")].map((h) => h.textContent.slice(0, 200)) };
      }, pg);
      log({ tag, newWorld: nw });
      await scan(page, L, `${tag} 7 new world form`);
      if (!HEAVY.has(viz) || pg) {
        await page.evaluate(() => { const p = [...document.querySelectorAll("#left .panel")].find((x) => /New world|Новый мир/.test(x.querySelector("h4").textContent)); const b = p && p.querySelector("button.primary"); if (b) b.click(); });
        await sleep(pg ? 12000 : 8000);
        log({ tag, newWorldStarted: true, toasts: await takeToasts(page), world: await page.evaluate(() => [...document.querySelectorAll("#world option")].map((o) => o.textContent)) });
        await scan(page, L, `${tag} 8 after new world`);
        await shot(page, `w01_${tag}_8_newworld`);
      }
      log({ tag, done: true });
    } catch (e) {
      log({ tag, error: e.message.slice(0, 400) });
      await shot(page, `w01_${tag}_error`);
    }
    await ctx.close();
    await post(`/api/runs/${id}/stop`);
    await sleep(1500);
    log({ tag, deleted: (await del(`/api/runs/${id}`)).status });
  }
}
await br.close();
