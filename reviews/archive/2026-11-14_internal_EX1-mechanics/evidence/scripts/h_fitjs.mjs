// R-E part H: fit.js against lfphys.tools.stats.linear_fit on the exported cases, and fit.js's own behaviour
import { readFileSync } from "node:fs";
const { fit, agrees, quantity } = await import("/lf/visualizations/player/js/fit.js");
const cases = JSON.parse(readFileSync("/out/g_fit_cases.json", "utf8"));
let worst = { p: 0, s: 0, v: 0, name: "" };
const rel = (a, b) => Math.abs(a - b) / Math.max(Math.abs(b), 1e-300);
for (const c of cases) {
  const r = fit(c.x, c.y, c.sx, c.sy, c.model);
  const names = r.names;
  let pj = names.map((n) => r.params[n]), sj = names.map((n) => r.sigma[n]);
  let pp = c.params, sp = c.sigma;
  if (c.model === "power") { pp = [c.A, c.params[1]]; sp = [c.A_sigma, c.sigma[1]]; }
  const dp = Math.max(...pj.map((v, i) => rel(v, pp[i]))), ds = Math.max(...sj.map((v, i) => rel(v, sp[i])));
  let dv = 0;
  if (c.model === "quadratic") dv = Math.max(rel(r.params.xv, c.vertex), rel(r.sigma.xv, c.vertex_sigma));
  if (dp > worst.p) worst.p = dp; if (ds > worst.s) worst.s = ds; if (dv > worst.v) { worst.v = dv; worst.name = c.name; }
}
console.log(`fit.js vs linear_fit on ${cases.length} cases: largest relative difference params ${worst.p.toExponential(1)}, sigma ${worst.s.toExponential(1)}, vertex/vertex sigma ${worst.v.toExponential(1)} (${worst.name})`);
// singular design
for (const [x, y, m] of [[[2, 2, 2, 2], [1, 1.1, 0.9, 1.05], "line"], [[30, 30, 30, 40], [1, 1.1, 0.9, 1.05], "quadratic"]]) {
  try { const r = fit(x, y, x.map(() => 0.5), y.map(() => 0.05), m); console.log("singular", m, "->", JSON.stringify(r.params)); }
  catch (e) { console.log("singular", m, "-> throws", e.why, e.message); }
}
// a negative error and a NaN reading
const r1 = fit([1, 2, 3, 4], [2, 4.1, 5.9, 8.2], [0, 0, 0, 0], [-0.1, 0.1, 0.1, 0.1], "line0");
console.log("negative sy taken as |sy|:", r1.params.b.toFixed(6), r1.sigma.b.toExponential(3));
const r2 = fit([1, 2, NaN, 4], [2, 4.1, 5.9, 8.2], null, [0.1, 0.1, 0.1, 0.1], "line0");
console.log("NaN row dropped: n =", r2.n);
// agrees() with refSigma unused by lab.js; the verdict at k = 2
console.log("agrees(0.6769, 0.000654, 0.677401):", JSON.stringify(agrees(0.676871, 0.000654, 0.6774011336276813)));
