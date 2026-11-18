# SPDX-FileCopyrightText: 2026 Ildar Idrisov <idrisov.sci@gmail.com>
# SPDX-License-Identifier: LicenseRef-lfphys-Research-1.0
"""E03: S03's results with the engine's new forces, against the design's A.8 (2026-11-18).
Run in Docker with PYTHONPATH=/lf/lfphys; writes JSON to argv[1]."""
import json, math, sys
import numpy as np
from lfphys.core.mechanics import (Body, Medium, fly, Coriolis, history_bound, sideways, latitude_for_gravity,
                                   G_STANDARD, normal_gravity)
from lfphys.theories.models import drag_quadratic as dq, magnus as mg

g = G_STANDARD
AIR = Medium.air()
LAT = latitude_for_gravity(g)          # 45.4996: the WGS 84 normal gravity equals g_n
STEEL, BALL = Body(0.0329, 0.020, "steel20"), Body(0.058, 0.067, "ball67")
out = {"lat": LAT, "g_check": normal_gravity(LAT)}

def vec(v0, deg):
    a = math.radians(deg)
    return [v0 * math.cos(a), v0 * math.sin(a)] if deg not in (0.0, 0) else [float(v0), 0.0]

def L(body, h, v0, deg, forces=(), medium=None):
    return fly(body, [0.0, h], vec(v0, deg), forces=list(forces), medium=medium)

def const(body): return dq.QuadraticDrag.sphere(body.diameter)
def curve(body): return dq.CurveDrag.sphere(body.diameter)

# ---- part 1: the chute
W1 = 1.5 / 0.010   # rolling: omega = v0 / R, topspin
p1 = []
for k in range(17):
    h = round(0.20 + 0.05 * k, 2)
    Lv = 1.5 * math.sqrt(2 * h / g)
    fc = L(STEEL, h, 1.5, 0, [const(STEEL)])
    fk = L(STEEL, h, 1.5, 0, [curve(STEEL)])
    fm = L(STEEL, h, 1.5, 0, [curve(STEEL)], AIR)
    row = {"h": h, "L_vac": Lv, "air_const_mm": (fc.range - Lv) * 1e3, "curve_minus_const_mm": (fk.range - fc.range) * 1e3,
           "buoy_am_mm": (fm.range - fk.range) * 1e3, "air_no_spin_mm": (fm.range - Lv) * 1e3}
    for edge in ("central", "low", "high"):
        flift = L(STEEL, h, 1.5, 0, [curve(STEEL), mg.Magnus(0.020, W1, edge=edge)], AIR)
        fsd = L(STEEL, h, 1.5, 0, [mg.SpinDrag(0.020, W1, edge=edge)], AIR)
        fall = L(STEEL, h, 1.5, 0, [mg.SpinDrag(0.020, W1, edge=edge), mg.Magnus(0.020, W1, edge=edge)], AIR)
        row[f"magnus_{edge}_mm"] = (flift.range - fm.range) * 1e3
        row[f"spindrag_{edge}_mm"] = (fsd.range - fm.range) * 1e3
        row[f"air_all_{edge}_mm"] = (fall.range - Lv) * 1e3
        if edge == "central":
            fall_c = fall
            S = [mg.Magnus(0.020, W1).spin_ratio(t, fall.state(t)[1]) for t in (0.0, fall.t_end)]
            Re = fall.reynolds()[0]
            row["S_range"] = S
            row["Re_range"] = [float(Re.min()), float(Re.max())]
    # spin decay: a linear loss of 7 % of omega over the flight
    T_ = fall_c.t_end
    wdec = lambda t, T_=T_: W1 * (1 - 0.07 * min(t, T_) / T_)
    fdec = L(STEEL, h, 1.5, 0, [mg.SpinDrag(0.020, wdec), mg.Magnus(0.020, wdec)], AIR)
    row["spin_decay7_mm"] = (fdec.range - fall_c.range) * 1e3
    hb = history_bound(fall_c, n=2000)
    row["basset_mm"], row["basset_bound_mm"], row["basset_B_over_W"] = hb["dL"] * 1e3, hb["dL_bound"] * 1e3, hb["B_over_weight"]
    for az, name in ((90.0, "east"), (0.0, "north")):
        cor = Coriolis(STEEL.mass, LAT, az)
        fco = L(STEEL, h, 1.5, 0, [mg.SpinDrag(0.020, W1), mg.Magnus(0.020, W1), cor], AIR)
        row[f"cor_{name}_along_mm"] = (fco.range - fall_c.range) * 1e3
        row[f"cor_{name}_right_mm"] = sideways(fco, cor)["right"] * 1e3
    p1.append(row)
out["part1"] = p1

# ---- part 2: the launcher, steel, 5 m/s, no spin
p2 = []
for th in range(15, 76, 5):
    Lv = 25 / g * math.sin(2 * math.radians(th))
    fc = L(STEEL, 0.0, 5.0, th, [const(STEEL)])
    fk = L(STEEL, 0.0, 5.0, th, [curve(STEEL)])
    fm = L(STEEL, 0.0, 5.0, th, [curve(STEEL)], AIR)
    hb = history_bound(fm, n=2000)
    row = {"theta": th, "L_vac": Lv, "L_const": fc.range, "L_curve": fk.range, "L_full": fm.range,
           "air_const_mm": (fc.range - Lv) * 1e3, "curve_minus_const_mm": (fk.range - fc.range) * 1e3,
           "buoy_am_mm": (fm.range - fk.range) * 1e3, "basset_mm": hb["dL"] * 1e3, "basset_bound_mm": hb["dL_bound"] * 1e3,
           "basset_B_over_W": hb["B_over_weight"], "Re": [float(x) for x in (fm.reynolds()[0].min(), fm.reynolds()[0].max())]}
    for az, name in ((90.0, "east"), (0.0, "north")):
        cor = Coriolis(STEEL.mass, LAT, az)
        fco = L(STEEL, 0.0, 5.0, th, [curve(STEEL), cor], AIR)
        row[f"cor_{name}_along_mm"] = (fco.range - fm.range) * 1e3
        row[f"cor_{name}_right_mm"] = sideways(fco, cor)["right"] * 1e3
    p2.append(row)
out["part2"] = p2
x = np.sin(2 * np.radians([r["theta"] for r in p2]))
fits = {}
for key in ("L_const", "L_curve", "L_full"):
    y = np.array([r[key] for r in p2])
    A = np.vstack([x, np.ones_like(x)]).T
    s = 0.0005
    cov = np.linalg.inv(A.T @ A) * s * s
    a, b = np.linalg.lstsq(A, y, rcond=None)[0]
    r = y - (a * x + b)
    fits[key] = {"slope": float(a), "sigma": float(math.sqrt(cov[0, 0])), "b": float(b),
                 "miss_over_err": float((a - 25 / g) / math.sqrt(cov[0, 0])), "chi2_dof": float(np.sum(r * r) / s / s / (len(x) - 2))}
out["part2_fit"] = fits

# ---- part 3: the light ball, 20 m/s, no spin
def best(forces_fn, medium=None):
    best = None
    for k in range(380, 461):
        th = k / 10
        f = L(BALL, 0.0, 20.0, th, forces_fn(), medium)
        if best is None or f.range > best[1]:
            best = (th, f.range)
    return best
out["part3_opt"] = {"const": best(lambda: [const(BALL)]), "curve": best(lambda: [curve(BALL)]),
                    "full": best(lambda: [curve(BALL)], AIR)}
p3 = []
for th in range(20, 71, 5):
    fc = L(BALL, 0.0, 20.0, th, [const(BALL)])
    fk = L(BALL, 0.0, 20.0, th, [curve(BALL)])
    fm = L(BALL, 0.0, 20.0, th, [curve(BALL)], AIR)
    hb = history_bound(fm, n=2000)
    row = {"theta": th, "L_const": fc.range, "L_curve": fk.range, "L_full": fm.range,
           "curve_minus_const_m": fk.range - fc.range, "buoy_am_m": fm.range - fk.range,
           "basset_mm": hb["dL"] * 1e3, "basset_bound_mm": hb["dL_bound"] * 1e3, "basset_B_over_W": hb["B_over_weight"]}
    for az, name in ((90.0, "east"), (0.0, "north")):
        cor = Coriolis(BALL.mass, LAT, az)
        fco = L(BALL, 0.0, 20.0, th, [curve(BALL), cor], AIR)
        row[f"cor_{name}_along_mm"] = (fco.range - fm.range) * 1e3
        row[f"cor_{name}_right_mm"] = sideways(fco, cor)["right"] * 1e3
    p3.append(row)
out["part3"] = p3
th = out["part3_opt"]["full"][0]
fm = L(BALL, 0.0, 20.0, th, [curve(BALL)], AIR)
cor = Coriolis(BALL.mass, LAT, 90.0)
fco = L(BALL, 0.0, 20.0, th, [curve(BALL), cor], AIR)
out["part3_opt_coriolis"] = {"theta": th, "along_mm": (fco.range - fm.range) * 1e3, "right_mm": sideways(fco, cor)["right"] * 1e3}
# the optimum's shift by the Basset force (first order, by the bound): dL(theta) slope near the optimum is 0
# ---- Explore's longest throw: light ball 25 m/s, 45 deg, from 10 m
fm = L(BALL, 10.0, 25.0, 45.0, [curve(BALL)], AIR)
cor = Coriolis(BALL.mass, LAT, 90.0)
fco = L(BALL, 10.0, 25.0, 45.0, [curve(BALL), cor], AIR)
out["explore_longest"] = {"L": fm.range, "along_mm": (fco.range - fm.range) * 1e3, "right_mm": sideways(fco, cor)["right"] * 1e3}
json.dump(out, open(sys.argv[1], "w"), indent=1)

def rng(rows, key, f=1.0): 
    v = [r[key] * f for r in rows]; return f"{min(v):+.3f} .. {max(v):+.3f}"
print("lat", LAT, "g", out["g_check"])
print("P1 Re", p1[0]["Re_range"], p1[-1]["Re_range"], "S", p1[0]["S_range"], p1[-1]["S_range"])
for k in ("air_const_mm", "curve_minus_const_mm", "buoy_am_mm", "air_no_spin_mm", "magnus_central_mm", "magnus_low_mm", "magnus_high_mm",
          "spindrag_central_mm", "spindrag_low_mm", "spindrag_high_mm", "air_all_central_mm", "air_all_low_mm", "air_all_high_mm",
          "spin_decay7_mm", "basset_mm", "basset_bound_mm", "basset_B_over_W", "cor_east_along_mm", "cor_east_right_mm", "cor_north_along_mm", "cor_north_right_mm"):
    print("P1", k, rng(p1, k))
for e in ("central", "low", "high"):
    first = next((r["h"] for r in p1 if abs(r[f"air_all_{e}_mm"]) > 0.5), None)
    print("P1 first |air_all| > 0.5 mm:", e, first)
for k in ("air_const_mm", "curve_minus_const_mm", "buoy_am_mm", "basset_mm", "basset_bound_mm", "basset_B_over_W", "cor_east_along_mm", "cor_east_right_mm", "cor_north_right_mm"):
    print("P2", k, rng(p2, k))
print("P2 fit", json.dumps(fits))
print("P3 opt", out["part3_opt"])
for k in ("curve_minus_const_m", "buoy_am_m", "basset_mm", "basset_bound_mm", "basset_B_over_W", "cor_east_along_mm", "cor_east_right_mm", "cor_north_right_mm"):
    print("P3", k, rng(p3, k))
print("P3 opt coriolis", out["part3_opt_coriolis"])
print("Explore longest", out["explore_longest"])
