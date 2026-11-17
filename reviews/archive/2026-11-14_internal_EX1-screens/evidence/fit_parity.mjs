// the lab's fits on the S03 readings (and on the derived columns), exported for lfphys.tools.stats.linear_fit
import { readFileSync, writeFileSync } from "node:fs";
const { reading, rowOf } = await import("/lf/visualizations/player/js/lab.js");
const { fit } = await import("/lf/visualizations/player/js/fit.js");
const D = JSON.parse(readFileSync("/q/lab_points.json", "utf-8"));
const I = { tape: { division: 0.001, error: 0.0005 }, ruler: { division: 0.01, error: 0.005 }, protractor: { division: 1, error: 0.5 } };
const cases = [];
const add = (name, x, y, sx, sy, model) => { const r = fit(x, y, sx, sy, model); cases.push({ name, x, y, sx, sy, model, js: { params: r.params, sigma: r.sigma, chi2: r.chi2, scaled: r.scaled } }); };
const A = D.heights.rows.map((r) => rowOf([{ id: "h", from: "ruler" }, { id: "L", from: "tape" }, { id: "s", of: "h", op: "sqrt" }], { ruler: reading(I.ruler, r.v), tape: reading(I.tape, r.meas.range) }));
for (const m of ["line0", "line", "quadratic", "power"]) add(`A ${m}`, A.map((c) => c.s.v), A.map((c) => c.L.v), A.map((c) => c.s.e), A.map((c) => c.L.e), m);
add("A L(h) power", A.map((c) => c.h.v), A.map((c) => c.L.v), A.map((c) => c.h.e), A.map((c) => c.L.e), "power");
const B = D.angles.rows.map((r) => rowOf([{ id: "t", from: "protractor" }, { id: "L", from: "tape" }, { id: "s", of: "t", op: "sin2" }], { protractor: reading(I.protractor, r.v), tape: reading(I.tape, r.meas.range) }));
for (const m of ["line0", "line"]) add(`B ${m}`, B.map((c) => c.s.v), B.map((c) => c.L.v), B.map((c) => c.s.e), B.map((c) => c.L.e), m);
add("B L(θ) quadratic", B.map((c) => c.t.v), B.map((c) => c.L.v), B.map((c) => c.t.e), B.map((c) => c.L.e), "quadratic");
const C = D.air.rows.map((r) => rowOf([{ id: "t", from: "protractor" }, { id: "L", from: "tape" }], { protractor: reading(I.protractor, r.v), tape: reading(I.tape, r.meas.range) }));
add("C quadratic", C.map((c) => c.t.v), C.map((c) => c.L.v), C.map((c) => c.t.e), C.map((c) => c.L.e), "quadratic");
writeFileSync("/q/fit_cases.json", JSON.stringify(cases));
console.log(cases.length, "cases");
