// the S03 lab's «Check against the law» on the computed points, as lab.js does it (reading → rowOf → fit → quantity → agrees)
import { readFileSync } from "node:fs";
const { reading, rowOf } = await import("/lf/visualizations/player/js/lab.js");
const { fit, quantity, agrees } = await import("/lf/visualizations/player/js/fit.js");
const D = JSON.parse(readFileSync("/q/lab_points.json", "utf-8"));
const I = { tape: { division: 0.001, error: 0.0005 }, tape_grey: { division: 0.001, error: 0.0005 }, ruler: { division: 0.01, error: 0.005 }, protractor: { division: 1, error: 0.5 } };
const steps = {
  heights: { cols: [{ id: "h", from: "ruler" }, { id: "L", from: "tape" }, { id: "sqrt_h", of: "h", op: "sqrt" }], x: "sqrt_h", y: "L", model: "line0", q: "slope", ref: "k_horizontal", read: (r) => ({ ruler: reading(I.ruler, r.v), tape: reading(I.tape, r.meas.range) }) },
  angles: { cols: [{ id: "theta", from: "protractor" }, { id: "L", from: "tape" }, { id: "sin2", of: "theta", op: "sin2" }], x: "sin2", y: "L", model: "line0", q: "slope", ref: "v2_over_g", read: (r) => ({ protractor: reading(I.protractor, r.v), tape: reading(I.tape, r.meas.range) }) },
  air: { cols: [{ id: "theta", from: "protractor" }, { id: "L", from: "tape" }, { id: "L_vac", from: "tape_grey" }], x: "theta", y: "L", model: "quadratic", q: "vertex", ref: "theta_max_air", read: (r) => ({ protractor: reading(I.protractor, r.v), tape: reading(I.tape, r.meas.range), tape_grey: reading(I.tape_grey, r.meas.range_vacuum) }) },
};
function run(step, sel = () => true, rep = 1, opts = {}) {
  const S = steps[step], d = D[step];
  const rows = [];
  for (const r of d.rows.filter(sel)) for (let k = 0; k < rep; k++) rows.push(rowOf(S.cols, S.read(r)));
  const x = opts.x || S.x, y = opts.y || S.y, model = opts.model || S.model;
  const pts = rows.map((c) => [c[x], c[y]]);
  const res = fit(pts.map((p) => p[0].v), pts.map((p) => p[1].v), pts.map((p) => p[0].e), pts.map((p) => p[1].e), model);
  const q = quantity(res, S.q), ref = d.references[S.ref].value;
  const a = q ? agrees(q.value, q.sigma, ref) : null;
  return { step, n: rows.length, model, q: q && +q.value.toPrecision(7), sigma: q && +q.sigma.toPrecision(3), ref: +ref.toPrecision(7), dev_sigma: q && +((q.value - ref) / q.sigma).toFixed(2), chi2dof: +(res.chi2 / res.dof).toPrecision(3), scaled: res.scaled, verdict: a ? (a.agrees ? "✓" : "✗") : "no quantity" };
}
const out = [];
out.push(run("heights"));
out.push(run("heights", () => true, 5));
out.push(run("heights", () => true, 20));
out.push(run("heights", (r) => [0.2, 0.4, 0.6, 0.8, 1.0].includes(r.v)));
out.push(run("heights", (r) => [0.2, 0.4, 0.6, 0.8, 1.0].includes(r.v), 10));
out.push(run("heights", () => true, 1, { model: "line" }));
out.push(run("heights", () => true, 1, { x: "h" }));  // the student plots L against h: compared with k anyway
out.push(run("angles"));
out.push(run("angles", () => true, 10));
out.push(run("angles", (r) => r.v <= 45));
out.push(run("air"));
out.push(run("air", () => true, 5));
out.push(run("air", (r) => r.v >= 35 && r.v <= 50));
out.push(run("air", (r) => r.v >= 30 && r.v <= 55));
out.push(run("air", (r) => r.v <= 45));
out.push(run("air", () => true, 1, { y: "L_vac" }));  // the grey ball's parabola vertex vs the air reference
for (const o of out) console.log(JSON.stringify(o));
// the grey ball (vacuum) vertex compared to 45° (what the worksheet's answer says), done by hand
{
  const d = D.air; const rows = d.rows.map((r) => rowOf(steps.air.cols, steps.air.read(r)));
  const res = fit(rows.map((c) => c.theta.v), rows.map((c) => c.L_vac.v), rows.map((c) => c.theta.e), rows.map((c) => c.L_vac.e), "quadratic");
  console.log(JSON.stringify({ grey_vertex: res.params.xv, sigma: res.sigma.xv, dev_from_45_sigma: (res.params.xv - 45) / res.sigma.xv, chi2dof: res.chi2 / res.dof }));
}
