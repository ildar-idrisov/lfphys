"""R-E part F: S03's lab steps as the player computes them (instrument rounding, derived columns, fit, «Check against
the law» = |q - ref| <= 2 sigma), for the full tables and for every subset of rows a student could measure."""
import itertools, json, math, sys
import numpy as np
sys.path[:0] = ["/lf/lfphys", "/lf/visualizations", "/lf/visualizations/server"]
from lfphys.tools.stats import linear_fit
from s03_projectile.engine.shot import Shot, optimum_angle, G
from s03_projectile import viz

INS = viz.INSTRUMENTS
def reading(name, value):
    d = INS[name]["division"]
    dec = max(0, -int(math.floor(math.log10(d) + 1e-12)))
    return round(round(value / d) * d, dec), INS[name]["error"]

def check(res, q, ref, k=2.0):
    if q == "slope":
        v, s = res["params"][-1 if res["model"] != "line" else 1], res["sigma"][-1 if res["model"] != "line" else 1]
        if res["model"] == "line0": v, s = res["params"][0], res["sigma"][0]
    elif q == "vertex":
        v, s = res["vertex"], res["vertex_sigma"]
    return abs(v - ref) <= k * s, v, s, (v - ref) / s

out = {}
# ---------------- step A: heights ----------------
st = viz.STEPS[0]; pre = viz.SCHEMA.presets[st["preset"]]["params"]
obj, v0, air = pre["object"], pre["v0"], pre["air"]
print(f"== A heights: {obj} v0={v0} air={air} angle={pre['angle_deg']}")
hs = st["controls"][0]["values"]
rows = []
for h in hs:
    Sa, Sv = Shot(obj, h, v0, 0.0, air), Shot(obj, h, v0, 0.0, False)
    hr, he = reading("ruler", h); Lr, Le = reading("tape", Sa.L)
    rows.append(dict(h=h, L=Sa.L, Lvac=Sv.L, eff=1 - Sa.L / Sv.L, hr=hr, he=he, Lr=Lr, Le=Le,
                     x=math.sqrt(hr), sx=he / (2 * math.sqrt(hr))))
ref = viz.Simulation.lab_reference("heights", {**pre, **st["fixed"]}, {"h_m": hs})
print(" reference:", ref["value"], "|", ref["how"])
for r in rows[::4] + [rows[-1]]:
    print(f"  h={r['h']:.2f} L_air={r['L']:.6f} L_vac={r['Lvac']:.6f} air shortens by {100*r['eff']:.3f} % = {1e3*(r['Lvac']-r['L']):.3f} mm (tape error 0.5 mm, reading {r['Lr']})")
mx = max(rows, key=lambda r: r["Lvac"] - r["L"])
print(f"  largest shortening {1e3*(mx['Lvac']-mx['L']):.3f} mm at h={mx['h']} ({100*mx['eff']:.3f} %); relative to 0.5 mm: {(mx['Lvac']-mx['L'])/0.0005:.2f} x")
X = np.array([r["x"] for r in rows]); SX = np.array([r["sx"] for r in rows]); Y = np.array([r["Lr"] for r in rows])
for model in ("line0", "line"):
    f = linear_fit(X, Y, SX, 0.0005, model)
    ok, v, s, z = check(f, "slope", ref["value"])
    print(f" all 17 rows, {model}: k={v:.6f} ± {s:.6f} (chi2/dof {f['chi2_dof']:.3g}, scaled {f['scaled']}) vs {ref['value']:.6f}: z={z:+.2f} -> {'agrees' if ok else 'DOES NOT AGREE'}")
# the same without the declared ruler error (x exact): how strong is the air bias against the tape alone?
f = linear_fit(X, Y, 0.0, 0.0005, "line0"); ok, v, s, z = check(f, "slope", ref["value"])
print(f" (sx=0) line0: k={v:.6f} ± {s:.6f} chi2/dof {f['chi2_dof']:.3g} scaled {f['scaled']}: z={z:+.2f} -> {'agrees' if ok else 'DOES NOT AGREE'}")
fails = {"line0": 0, "line": 0}; tot = {"line0": 0, "line": 0}; worst = {"line0": 0, "line": 0}
idx = range(len(rows))
for n in range(2, len(rows) + 1):
    for sub in itertools.combinations(idx, n):
        sub = list(sub)
        for model in ("line0", "line"):
            if n <= (1 if model == "line0" else 2): continue
            f = linear_fit(X[sub], Y[sub], SX[sub], 0.0005, model)
            ok, v, s, z = check(f, "slope", ref["value"])
            tot[model] += 1; fails[model] += (not ok); worst[model] = max(worst[model], abs(z))
print(" every subset of rows:", {m: f"{fails[m]} of {tot[m]} do not agree, largest |z| {worst[m]:.2f}" for m in tot})

# ---------------- step B: angles ----------------
st = viz.STEPS[1]; pre = {**viz.SCHEMA.presets[st["preset"]]["params"], **st["fixed"]}
obj, v0, h, air = pre["object"], pre["v0"], pre["h_m"], pre["air"]
print(f"== B angles: {obj} v0={v0} h={h} air={air}")
ths = st["controls"][0]["values"]
ref = viz.Simulation.lab_reference("angles", pre, {"angle_deg": ths})
def table(air_):
    rr = []
    for th in ths:
        S = Shot(obj, h, v0, float(th), air_)
        tr, te = reading("protractor", th); Lr, Le = reading("tape", S.L)
        x = math.sin(2 * math.radians(tr)); sx = abs(2 * math.cos(2 * math.radians(tr)) * math.pi / 180) * te
        rr.append((x, sx, Lr, S.L))
    return np.array(rr)
for air_ in (False, True):
    A = table(air_)
    f = linear_fit(A[:, 0], A[:, 2], A[:, 1], 0.0005, "line0"); ok, v, s, z = check(f, "slope", ref["value"])
    print(f" air={air_}: all rows line0 slope={v:.6f} ± {s:.6f} chi2/dof {f['chi2_dof']:.3g} vs v0^2/g={ref['value']:.6f}: rel {100*(v/ref['value']-1):+.3f} %, z={z:+.2f} -> {'agrees' if ok else 'DOES NOT AGREE'}")
A = table(False)
fails = 0; tot = 0; worst = 0; worst_sub = None
for n in range(2, len(ths) + 1):
    for sub in itertools.combinations(range(len(ths)), n):
        sub = list(sub)
        f = linear_fit(A[sub, 0], A[sub, 2], A[sub, 1], 0.0005, "line0"); ok, v, s, z = check(f, "slope", ref["value"])
        tot += 1; fails += (not ok)
        if abs(z) > worst: worst, worst_sub = abs(z), [ths[i] for i in sub]
print(f" vacuum, every subset (line0): {fails} of {tot} do not agree; largest |z| {worst:.2f} at {worst_sub}")
fails = 0; tot = 0
for n in range(3, len(ths) + 1):
    for sub in itertools.combinations(range(len(ths)), n):
        sub = list(sub)
        f = linear_fit(A[sub, 0], A[sub, 2], A[sub, 1], 0.0005, "line"); ok, v, s, z = check(f, "slope", ref["value"])
        tot += 1; fails += (not ok)
print(f" vacuum, every subset (line): {fails} of {tot} do not agree")

# ---------------- step C: air ----------------
st = viz.STEPS[2]; pre = {**viz.SCHEMA.presets[st["preset"]]["params"], **st["fixed"]}
obj, v0, h = pre["object"], pre["v0"], pre["h_m"]
print(f"== C air: {obj} v0={v0} h={h}")
ths = st["controls"][0]["values"]
ref = viz.Simulation.lab_reference("air", pre, {"angle_deg": ths})
print(" reference:", ref["value"], "|", ref["how"])
# the true optimum to 1e-6 deg (golden section on the engine's range)
from scipy.optimize import minimize_scalar
m = minimize_scalar(lambda a: -Shot(obj, h, v0, a, True).L, bracket=(40, 42, 44), tol=1e-10)
print(f" true optimum (golden section): {m.x:.5f} deg, L={-m.fun:.6f}; reference's discretisation error {ref['value']-m.x:+.4f} deg")
C = []
for th in ths:
    S = Shot(obj, h, v0, float(th), True)
    tr, te = reading("protractor", th); Lr, Le = reading("tape", S.L)
    C.append((tr, te, Lr, S.L))
C = np.array(C)
f = linear_fit(C[:, 0], C[:, 2], C[:, 1], 0.0005, "quadratic"); ok, v, s, z = check(f, "vertex", ref["value"])
print(f" all 8 rows quadratic: vertex {v:.4f} ± {s:.4f} (unscaled σ {math.sqrt(np.array([0,-1/(2*f['params'][2]),f['params'][1]/(2*f['params'][2]**2)]) @ (np.array(f['cov'])/(f['chi2_dof'] if f['scaled'] else 1)) @ np.array([0,-1/(2*f['params'][2]),f['params'][1]/(2*f['params'][2]**2)])):.4f}), chi2/dof {f['chi2_dof']:.3g} scaled {f['scaled']}; vs ref {ref['value']}: z={z:+.2f} -> {'agrees' if ok else 'DOES NOT AGREE'}; vs true optimum z={(v-m.x)/s:+.2f}")
fails = []; tot = 0
for n in range(4, len(ths) + 1):
    for sub in itertools.combinations(range(len(ths)), n):
        sub = list(sub)
        f = linear_fit(C[sub, 0], C[sub, 2], C[sub, 1], 0.0005, "quadratic"); ok, v, s, z = check(f, "vertex", ref["value"])
        tot += 1
        if not ok: fails.append(([int(ths[i]) for i in sub], round(v, 3), round(s, 4), round(z, 1)))
print(f" every subset of >= 4 rows: {len(fails)} of {tot} do not agree")
for x in fails[:12]: print("   ", x)
# the parabola's bias with exact data (no rounding): the model error alone
f = linear_fit(C[:, 0], C[:, 3], 0.0, 1e-9, "quadratic")
print(f" exact ranges, 25-60 deg, unweighted-equivalent: vertex {f['vertex']:.4f} (model bias vs true optimum {f['vertex']-m.x:+.4f} deg)")
