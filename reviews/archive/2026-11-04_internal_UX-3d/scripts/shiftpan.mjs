// Shift + left drag (pan on a touchpad without a right button) and the wheel's step, in p04 (a light scene)
import { launch, startRun, openPage, drag, wheel, settle } from "./lib.mjs";
const base = "http://127.0.0.1:" + process.argv[2];
const br = await launch(); const res = {};
try {
  const id = await startRun(base, "p04_fluids", { preset: "cylinder_re20" });
  const page = await openPage(br, base, id, { playMs: 3000 });
  const cam = () => page.evaluate(() => { const a = document.querySelector(".s3d-view").__scene3d; return { pos: a.__camera.position.toArray().map((v) => +v.toFixed(3)), target: a.__orbit.target.toArray().map((v) => +v.toFixed(3)), dist: +a.__camera.position.distanceTo(a.__orbit.target).toFixed(4) }; });
  res.start = await cam();
  await drag(page, 120, 60, { modifiers: ["Shift"] }); res.shiftDrag = await cam();
  await page.keyboard.press("f"); await settle(page, 200);
  res.reset = await cam();
  await wheel(page, -100, 1); res.oneNotchIn = await cam();
  res.notchRatio = +(res.oneNotchIn.dist / res.reset.dist).toFixed(4);
  await page.close();
} catch (e) { res.failed = String(e).slice(0, 300); }
await br.close();
console.log(JSON.stringify(res));
