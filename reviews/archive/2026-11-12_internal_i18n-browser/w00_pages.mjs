// w00: the catalogue (both modes, a card's parameter form, the help), the settings page, the legal page, in each
// language; the language switch (stored, ?lang= wins, a switch in the middle of a recording keeps the run)
import { browser, newPage, post, get, del, sleep, startRun, waitPlayer, shot, scan, setLog, log, base } from "./r_lib.mjs";
setLog("w00_pages");
const br = await browser();
for (const W of [1600, 1280]) {
  for (const L of ["en", "ru"]) {
    const ctx = await br.newContext({ viewport: { width: W, height: 1000 } });
    const page = await newPage(ctx, `pages_${L}_${W}`);
    for (const mode of ["demo", "playground"]) {
      await page.goto(`${base}/?lang=${L}`);
      await page.evaluate((m) => localStorage.setItem("lfviz.mode", m), mode);
      await page.reload();
      await page.waitForSelector(".card", { timeout: 60000 });
      await sleep(2500);
      await scan(page, L, `catalogue ${mode} ${W}`);
      await shot(page, `w00_catalogue_${mode}_${L}_${W}`, true);
      if (W === 1600) {
        // every card's parameter form ("Parameters…" / "Laws…") opened
        await page.evaluate(() => { for (const b of document.querySelectorAll(".card .row button:not(.primary)")) if (/Parameters|Laws|Параметр|Закон/.test(b.textContent)) b.click(); });
        await sleep(800);
        await scan(page, L, `catalogue ${mode} forms open`);
        await shot(page, `w00_catalogue_${mode}_forms_${L}`, true);
        // every scenario of every card: its note
        const notes = await page.evaluate(() => {
          const out = [];
          for (const c of document.querySelectorAll(".card")) {
            const s = c.querySelector(".row select"); if (!s) continue;
            for (const o of s.options) { s.value = o.value; s.dispatchEvent(new Event("change")); out.push({ card: c.querySelector("h3").textContent, opt: o.textContent, note: s.closest(".row").nextElementSibling?.textContent }); }
          }
          return out;
        });
        log({ L, mode, scenarioNotes: notes });
      }
    }
    if (W === 1600) {
      await page.click("#help"); await sleep(600);
      await scan(page, L, "catalogue help");
      const m = await page.$(".modal > div"); if (m) await m.screenshot({ path: `/shots/w00_catalogue_help_${L}.png` });
      await page.keyboard.press("Escape");
      for (const u of ["settings", "legal"]) {
        await page.goto(`${base}/${u}?lang=${L}`);
        await page.waitForSelector(".lang-switch a.on"); await sleep(2500);
        await scan(page, L, u);
        await shot(page, `w00_${u}_${L}`, true);
        // every details element open on the legal page
        if (u === "legal") { await page.evaluate(() => { for (const d of document.querySelectorAll("details")) d.open = true; }); await sleep(500); await scan(page, L, "legal open"); await shot(page, `w00_legal_open_${L}`, true); }
      }
    }
    await ctx.close();
  }
}

// the language switch
{
  const ctx = await br.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await newPage(ctx, "switch");
  await page.goto(`${base}/`);
  await page.waitForSelector(".lang-switch a.on");
  log({ check: "default", lang: await page.evaluate(() => document.documentElement.lang) });
  await Promise.all([page.waitForNavigation(), page.click(".lang-switch a[data-lang=ru]")]);
  await page.waitForSelector(".lang-switch a.on");
  log({ check: "after RU click", lang: await page.evaluate(() => document.documentElement.lang), ls: await page.evaluate(() => localStorage.getItem("lfviz.lang")) });
  await page.goto(`${base}/settings`); await page.waitForSelector(".lang-switch a.on");
  log({ check: "stored on settings", lang: await page.evaluate(() => document.documentElement.lang) });
  await page.goto(`${base}/legal?lang=en`); await page.waitForSelector(".lang-switch a.on");
  log({ check: "?lang=en over stored ru", lang: await page.evaluate(() => document.documentElement.lang), ls: await page.evaluate(() => localStorage.getItem("lfviz.lang")) });
  // ?lang=en then the switch to RU on that page: the address loses ?lang
  await Promise.all([page.waitForNavigation(), page.click(".lang-switch a[data-lang=ru]")]);
  await page.waitForSelector(".lang-switch a.on");
  log({ check: "switch on a ?lang page", url: page.url(), lang: await page.evaluate(() => document.documentElement.lang) });
  // an unknown ?lang
  await page.goto(`${base}/?lang=de`); await page.waitForSelector(".lang-switch a.on");
  log({ check: "?lang=de", lang: await page.evaluate(() => document.documentElement.lang) });
  // links inside a ?lang page keep the language? (catalogue → run → settings)
  await page.evaluate(() => localStorage.setItem("lfviz.lang", "en"));
  await page.goto(`${base}/?lang=ru`); await page.waitForSelector(".card", { timeout: 60000 });
  const hrefs = await page.evaluate(() => [...document.querySelectorAll(".topbar a")].map((a) => a.getAttribute("href")));
  await page.click(".topbar a[href='/settings']"); await page.waitForSelector(".lang-switch a.on");
  log({ check: "?lang=ru then a link to settings (stored en)", hrefs, url: page.url(), lang: await page.evaluate(() => document.documentElement.lang) });
  await shot(page, "w00_switch_settings_after_link");

  // the switch in the middle of a recording
  await page.evaluate(() => localStorage.setItem("lfviz.lang", "en"));
  const r = await startRun({ viz: "v04_orbits", seed: 3 });
  await page.goto(`${base}/run?id=${r.id}`);
  await waitPlayer(page);
  await page.click("#rec"); await sleep(4000);
  const before = await page.evaluate(() => ({ frames: window.__lfPlayer.frames(), time: document.getElementById("time").textContent }));
  const runBefore = (await get("/api/runs")).find((x) => x.id === r.id);
  await shot(page, "w00_switch_midrun_before_en");
  await Promise.all([page.waitForNavigation(), page.click(".lang-switch a[data-lang=ru]")]);
  await waitPlayer(page);
  await sleep(4000);
  const after = await page.evaluate(() => ({ frames: window.__lfPlayer.frames(), time: document.getElementById("time").textContent, rec: document.getElementById("rec").className, status: document.getElementById("status").textContent }));
  const runAfter = (await get("/api/runs")).find((x) => x.id === r.id);
  log({ check: "switch mid-recording", url: page.url(), before, after, playingBefore: runBefore.playing, playingAfter: runAfter.playing, simBefore: runBefore.sim_t, simAfter: runAfter.sim_t, worlds: runAfter.n_worlds });
  await shot(page, "w00_switch_midrun_after_ru");
  await scan(page, "ru", "run page after switch mid-run");
  await post(`/api/runs/${r.id}/stop`); await sleep(500); await del(`/api/runs/${r.id}`);
  await ctx.close();
}
await br.close();
