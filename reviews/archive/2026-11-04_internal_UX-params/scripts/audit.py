"""UX audit of parameter combinations (review 2026-11-04_internal_UX-params).

Runs every combination of a world through the same code path the server's worker uses (schema.resolve -> Simulation
-> Runner._start_world -> frames / commands), each in a forked child with time budgets, and writes one JSON line per
combination: what the user would see (refusals, errors, failed checks, non-finite values, stalls).

    python3 audit.py WORLD [--workers 4] [--n-random 60] [--out /out/res] [--only KIND,...] [--limit N]

Run from /lf/visualizations inside the light-funnel-viz image with LFPHYS_NO_GPU=1 (CPU only).
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import multiprocessing as mp
import os
import random
import re
import signal
import sys
import time
import traceback

sys.path.insert(0, "/lf/visualizations/server")
sys.path.insert(0, "/lf/visualizations")
from lfviz import protocol, registry  # noqa: E402
from lfviz.sim import Runner  # noqa: E402
import queue  # noqa: E402

import numpy as np  # noqa: E402

registry.ensure_path()

BUILD_SLOW = 60.0   # s: a world that takes longer to build counts as a hang (d)
OP_SLOW = 30.0      # s: one frame / one command longer than this counts as a hang (d)
BUILD_KILL = 240.0  # s: the child is killed (the measured time is then "> BUILD_KILL")
OP_KILL = 120.0
COMBO_KILL = 600.0
FPS = 20.0

CYR = re.compile(r"[А-Яа-яЁё]")


# ---------------------------------------------------------------------------------------------------------------
# per-world configuration: interacting pairs, frames per op, budgets
# values: "min" | "max" | a literal; a pair is a dict of param -> value (applied together from the default)
WORLD = {
    "v01_light_travel": dict(F=8, n_random=50, pairs=[
        {"c_factor": "min", "scenario": "sun_earth", "se_distance_au": "max"},
        {"c_factor": "max", "scenario": "sun_earth", "se_distance_au": "min"},
        {"scenario": "sun_earth", "se_radius_km": "max", "se_distance_au": "min"},
        {"scenario": "sun_earth", "se_mass": "max", "se_radius_km": "min"},
        {"scenario": "sun_earth", "kinematics": "emission", "gravity": "newton"},
        {"scenario": "measure_c", "kinematics": "ether", "mc_v1": "max", "mc_v2": "min", "mc_v3": "max"},
        {"scenario": "measure_c", "kinematics": "emission", "mc_src_u": "max", "mc_v1": "min"},
        {"scenario": "measure_c", "mc_L0_km": "min", "mc_src_km": "max"},
        {"scenario": "measure_c", "mc_L0_km": "max", "mc_src_km": "min"},
        {"scenario": "measure_c", "mc_t_flash_ms": "max", "c_factor": "min"},
        {"scenario": "measure_c", "mc_orient": "y", "mc_sync": "lab", "kinematics": "ether", "mc_v2": "max"},
        {"scenario": "lensing", "ln_mass": "max", "ln_radius_km": "max"},
        {"scenario": "lensing", "ln_mass": "min", "ln_radius_km": "max"},
        {"scenario": "lensing", "ln_src_rs": "min", "ln_obs_rs": "min", "ln_src_y_rs": 0.0},
        {"scenario": "lensing", "ln_src_rs": "max", "ln_obs_rs": "max", "n_rays": "max"},
        {"scenario": "lensing", "ln_src_y_rs": "max", "ln_plane_hw_rs": "min"},
        {"scenario": "lensing", "gravity": "none", "kinematics": "emission"},
        {"scenario": "andromeda", "an_dist_mly": "max", "an_walk": "max", "an_event_days": "max"},
        {"scenario": "andromeda", "an_dist_mly": "min", "an_walk": "max", "an_event_days": "min"},
        {"scenario": "andromeda", "kinematics": "ether", "c_factor": "min"},
    ]),
    "v02_double_slit": dict(F=6, n_random=60, pairs=[
        {"species": "electron", "energy_by": "ekin", "ekin_ev": "min"},
        {"species": "electron", "energy_by": "ekin", "ekin_ev": "max"},
        {"species": "electron", "energy_by": "speed", "speed_ms": "max"},
        {"species": "c60", "energy_by": "speed", "speed_ms": "min"},
        {"species": "c60", "energy_by": "speed", "speed_ms": "max"},
        {"species": "photon", "energy_by": "speed"},
        {"species": "photon", "energy_by": "ekin", "ekin_ev": "max"},
        {"species": "photon", "energy_by": "freq", "freq_thz": "min"},
        {"species": "photon", "lam_nm": "max", "a_um": "min"},
        {"species": "photon", "lam_nm": "min", "a_um": "max", "d_um": "max"},
        {"species": "custom", "mass_u": "min", "energy_by": "speed", "speed_ms": "max"},
        {"species": "custom", "mass_u": "max", "energy_by": "speed", "speed_ms": "min", "charge_e": "max"},
        {"species": "custom", "spin_half": True, "spin_state": "up_x", "mass_u": "min"},
        {"a_um": "max", "d_um": "min"},
        {"a_um": 200.0, "d_um": 100.0},
        {"n_slits": "max", "d_um": "min"},
        {"n_slits": "max", "a_um": "max", "d_um": "max", "L2_m": "min"},
        {"n_slits": 1, "wp_mode": "qubit", "wp_slit": "max"},
        {"n_slits": 2, "wp_mode": "qubit", "wp_slit": 5},
        {"wp_mode": "qubit", "wp_read": "angle", "wp_read_angle": "max"},
        {"wp_mode": "microscope", "mic_lambda_nm": "min", "mic_record": "cone", "mic_cone_deg": "min"},
        {"wp_mode": "microscope", "species": "photon"},
        {"L2_m": "min", "screen_um": "max", "pixel_um": "max"},
        {"L2_m": "max", "screen_um": "min", "pixel_um": "min"},
        {"L1_m": "max", "src_width_um": "max"},
        {"L1_m": "min", "src_width_um": "max"},
        {"rate": "max", "dark_rate": "max"},
        {"rate": "min", "eff": 0.0},
        {"screen_model": "pec", "screen_t_um": "max", "a_um": "min"},
        {"screen_model": "pec", "species": "electron"},
        {"collapse": "grw", "grw_lambda": "max", "grw_rc_nm": "min", "species": "c60"},
        {"collapse": "grw", "grw_lambda": "max", "grw_rc_nm": "max"},
        {"collapse": "slit", "n_bohm": "max"},
        {"born_p": "min", "n_slits": "max"},
        {"born_p": "max", "dlam_rel": "max"},
        {"el1": "polarizer", "el2": "polarizer", "el1_angle": 0.0, "el2_angle": 90.0},
        {"el1": "block", "el2": "block"},
        {"el1": "filter", "species": "electron"},
        {"analyzer": "on", "pol_state": "unpol", "pol_degree": 0.0},
        {"pol_state": "custom", "pol_psi": "max", "pol_chi": "max"},
        {"ab_flux": "max", "species": "photon"},
        {"ab_flux": "max", "species": "electron", "energy_by": "ekin"},
        {"dlam_rel": "max", "src_width_um": "max", "n_bohm": "max"},
    ]),
    "v03_quantum_1d": dict(F=8, n_random=50, pairs=[
        {"energy": "min", "V0": "max", "width": "max"},
        {"energy": "max", "V0": "min", "width": "max"},
        {"energy": "max", "sigma": "min"},
        {"energy": "min", "sigma": "max"},
        {"width": "min", "edge": "max"},
        {"width": "max", "edge": "min"},
        {"scenario": "double", "gap": "min", "width": "max"},
        {"scenario": "double", "gap": "max", "width": "max", "sigma": "max"},
        {"scenario": "oscillator", "hw": "min", "x0": "max"},
        {"scenario": "oscillator", "hw": "max", "x0": "max", "energy": "max"},
        {"scenario": "well", "V0": "min", "width": "max"},
        {"scenario": "step", "V0": "max", "energy": "min"},
        {"interp": "bohm", "n_bohm": "max", "energy": "max"},
        {"interp": "everett", "n_bohm": "max", "scenario": "double"},
        {"scenario": "free", "energy": "max", "sigma": "max"},
    ]),
    "v04_orbits": dict(F=10, n_random=100, pairs=[
        {"mass_msun": "max", "radius_km": "max"},
        {"mass_msun": "min", "radius_km": "max"},
        {"mass_msun": "min", "radius_km": 5.0},
        {"radius_km": 1000.0, "r0": "min"},
        {"r0": "min", "speed": "max"},
        {"r0": "min", "speed": "min"},
        {"r0": "max", "speed": "max"},
        {"r0": "max", "speed": "min"},
        {"gravity": "newton", "speed": "max", "r0": "min"},
        {"gravity": "newton", "r0": "max", "mass_msun": "max"},
        {"angle": "max", "speed": "max"},
        {"angle": "min", "speed": "min"},
        {"angle": "max", "speed": 1.0, "r0": "min"},
        {"ghost": True, "gravity": "newton"},
        {"time_units": "geo", "r0": "max"},
    ]),
    "v05_optics_bench": dict(F=8, n_random=60, pairs=[
        {"theta_deg": "max", "structure": "tir", "tir_gap_nm": "max"},
        {"theta_deg": "max", "structure": "tir", "tir_gap_nm": "min"},
        {"n0": "max", "ns": "min", "theta_deg": "max"},
        {"n0": "max", "ns": "min", "theta_deg": 14.4775},
        {"n0": 1.5, "ns": 1.0, "theta_deg": 41.8103148958},
        {"n0": "max", "ns": "max"},
        {"structure": "bragg", "pairs": "max", "nH": "max", "nL": "min"},
        {"structure": "bragg", "nH": 1.45, "nL": 1.45},
        {"structure": "ar", "ar_n": "max", "lam0_nm": "min", "lam_nm": "max"},
        {"structure": "fp", "fp_d_nm": "max", "fp_n": "max", "lam_nm": "min"},
        {"structure": "metal", "metal_k": "max", "metal_d_nm": "max"},
        {"structure": "metal", "metal_k": "min", "metal_n": "min", "metal_d_nm": "min"},
        {"structure": "metal", "theta_deg": "max", "pol": "p"},
        {"rate": "max", "theta_deg": "min"},
        {"rate": "min"},
    ]),
    "v06_qcd": dict(F=10, n_random=60, pairs=[
        {"alpha_mz": "max", "mu": "min", "loops": "max"},
        {"alpha_mz": "max", "mu": "min", "loops": "min"},
        {"alpha_mz": "min", "mu": "max"},
        {"alpha_mz": "max", "sweep": "max"},
        {"system": "bottom", "m_q": "max", "kappa": "max"},
        {"system": "charm", "m_q": "min", "kappa": "min", "a_conf": "min"},
        {"kappa": "max", "a_conf": "max", "m_q": "max"},
        {"kappa": "min", "a_conf": "min"},
    ]),
    "v07_bell_test": dict(F=10, n_random=60, pairs=[
        {"L_m": "max", "rate": "max"},
        {"L_m": "min", "rate": "min"},
        {"switch": "random", "tau_ns": "min", "L_m": "max"},
        {"switch": "random", "tau_ns": "max", "L_m": "min"},
        {"pair": "spin", "spin_beta": "max", "L_m": "max"},
        {"pair": "spin", "spin_beta": "min", "rate": "max"},
        {"law": "lhv", "switch": "fixed"},
        {"a_deg": "max", "a2_deg": "max", "b_deg": "max", "b2_deg": "max"},
    ]),
    "v08_wave_3d": dict(F=3, n_random=12, workers=2, pairs=[
        {"n": "512", "zmax": "max", "lam": "min"},
        {"n": "128", "zmax": "max", "lam": "min"},
        {"n": "128", "zmax": "min", "lam": "max"},
        {"source": "double", "a": "max", "d": "min", "n": "128"},
        {"source": "double", "a": "max", "d": "max", "L": "max", "n": "128"},
        {"source": "gauss", "w": "max", "n": "128"},
        {"source": "gauss", "w": "min", "lam": "max", "n": "128"},
        {"source": "slit", "L": "max", "a": "max", "n": "128"},
        {"mode": "slices", "reduced": True, "source": "slit", "n": "128"},
        {"mode": "slices", "reduced": True, "source": "double", "zmax": "max"},
    ]),
    "v09_thomas_3d": dict(F=10, n_random=60, pairs=[
        {"rho": "max", "turns": "max", "accel_g": "min"},
        {"rho": "min", "turns": "max", "accel_g": "max"},
        {"loop": "polygon", "sides": "max", "rho": "max"},
        {"loop": "crown", "sides": "max", "chi": "max"},
        {"loop": "triangle", "alpha": "min", "rho": "max"},
        {"loop": "triangle", "alpha": "max", "rho": "max"},
        {"loop": "helix", "chi": "max", "turns": "max"},
        {"loop": "seam", "chi": "max", "rho": "max"},
        {"space": "lab", "rho": "max", "turns": "max"},
        {"field": "ratio", "eta_u": "max", "ngrid": "96"},
        {"nth": "min", "nph": "max"},
    ]),
    "v10_fast_observer": dict(F=5, n_random=50, pairs=[
        {"scene": "sky", "stars": "max", "sky_T": "min"},
        {"scene": "sky", "stars": "min", "sky_T": "max"},
        {"scene": "city", "stars": "max"},
        {"scene": "train", "beta": "max"},
        {"scene": "flyby", "beta": "max", "obs_beta": "max"},
        {"obs_beta": "max", "res": "l", "camera": "sky"},
        {"obs_beta": "max", "fov": "max", "pitch": "max"},
        {"fov": "min", "res": "l"},
        {"image": "delay", "exposure": "auto", "ev": "max"},
        {"image": "doppler", "obs_beta": "max", "ev": "min"},
    ]),
    "v11_double_slit_2d": dict(F=3, n_random=25, workers=4, pairs=[
        {"lam_pm": "min", "grid": "fine"},
        {"lam_pm": "max", "grid": "coarse"},
        {"a": "max", "d": "min"},
        {"a": "max", "d": "max", "w": "max", "L": "max"},
        {"L": "min", "sigma_z": "max"},
        {"sigma_x": "max", "sigma_y": "max", "sigma_z": "max"},
        {"sigma_x": "min", "sigma_y": "min", "sigma_z": "min"},
        {"n_bohm": "max", "n_tracks": "max"},
        {"mark": "spin", "particle": "c60"},
        {"mark": "detector", "V0": "min", "edge": "max"},
        {"particle": "c60", "lam_pm": "min"},
    ]),
    "v12_arrival_times_2d": dict(F=3, n_random=25, workers=4, pairs=[
        {"state": "train", "n_train": "max", "sep": "max"},
        {"state": "train", "n_train": "max", "sep": "min", "L": "min"},
        {"state": "backflow", "L": "max"},
        {"scene": "slits", "a": "max", "d": "min"},
        {"scene": "slits", "w": "max", "L": "min"},
        {"lam_pm": "min", "grid": "fine"},
        {"lam_pm": "max", "L": "max"},
        {"kappa": "max", "mu_w": "max", "mu_ms": "max"},
        {"kappa": "min", "mu_w": "min", "mu_ms": "min"},
        {"soft": True, "W0": "max"},
        {"soft": False, "kappa": "max"},
        {"n_bohm": "max", "n_tracks": "max"},
        {"sigma_x": "max", "sigma_y": "max", "sigma_z": "max"},
    ]),
    "v13_hydrogen_3d": dict(F=5, n_random=60, pairs=[
        {"n": 1, "l": 1},
        {"n": 2, "l": 1, "m": 2},
        {"n": 2, "l": 1, "m": -2},
        {"n": "max", "l": "max", "m": "max"},
        {"n": "max", "l": "max", "m": "min", "ng": "96"},
        {"n": "max", "l": 0, "m": 0},
        {"n": 3, "l": 2, "m": 2, "real": False},
        {"mode": "super", "n2": 1, "l2": 1},
        {"mode": "super", "n2": "max", "l2": "max", "m2": "max", "w2": "max"},
        {"mode": "super", "n2": 2, "l2": 1, "m2": 0, "n": 2, "l": 1, "m": 0},
        {"mode": "super", "w2": "min", "phase2": "max"},
        {"atom": "Ps", "n": "max", "l": "max"},
        {"atom": "He+", "n": "max", "l": 0},
    ]),
    "v14_quarkonium_3d": dict(F=5, n_random=60, pairs=[
        {"n": 1, "l": 2},
        {"l": 0, "m": 2},
        {"l": 1, "m": -2},
        {"n": "max", "l": "max", "m": "max"},
        {"system": "bottom", "n": "max", "l": "max", "ng": "96"},
        {"mode": "super", "n2": "max", "l2": "max", "m2": "max"},
        {"mode": "super", "n2": 1, "l2": 0, "m2": 2},
        {"mode": "super", "n2": 1, "l2": 0, "n": 1, "l": 0},
    ]),
    "v15_kerr_shadow": dict(F=5, n_random=60, pairs=[
        {"metric": "jp", "a13": "max", "chi": "max"},
        {"metric": "jp", "a13": "min", "chi": "max"},
        {"metric": "jp", "a22": "max", "a12": "max", "chi": "max"},
        {"metric": "jp", "a22": "min", "a12": "min", "chi": "max"},
        {"metric": "jp", "a22": "min", "a12": "min", "chi": "min"},
        {"chi": "max", "incl": "min", "res": "l"},
        {"chi": "max", "incl": 90.0, "emitter": "keplerian", "retro": True},
        {"chi": "min", "retro": True, "emitter": "keplerian"},
        {"half": "min", "n_rays": "max"},
        {"half": "max", "res": "l", "n_rays": "max"},
        {"target": "none", "chi": "max"},
    ]),
    "v16_optical_vortices": dict(F=5, n_random=50, workers=4, pairs=[
        {"l": "max", "p": "max", "w0": "min", "lam": "max"},
        {"l": "max", "p": "max", "w0": "max", "lam": "min"},
        {"l": "min", "p": "max", "w0": "max"},
        {"l": 0, "p": 0, "pol": "lin"},
        {"model": "paraxial", "w0": "min", "lam": "max"},
        {"model": "exact", "w0": "min", "lam": "max", "zspan": "max"},
        {"gen": "fork", "period": "min", "l": "max", "kind": "blazed"},
        {"gen": "fork", "period": "max", "l": "min", "w0": "max"},
        {"gen": "spp", "l": "max", "pol": "-1"},
        {"rot": "dove", "f_rot": "max", "l": "max"},
        {"rot": "disc", "f_rot": "max", "t_show": "min"},
        {"rot": "disc", "f_rot": "min", "t_show": "max"},
    ]),
    "v17_mie_scattering": dict(F=4, n_random=40, workers=4, pairs=[
        {"radius_um": "max", "n_lam": "32", "width": "max"},
        {"radius_um": "min", "n_lam": "8", "width": "max"},
        {"radius_um": "max", "width": "min"},
        {"index": "custom", "n_re": "min", "n_im": "max"},
        {"index": "custom", "n_re": "max", "n_im": "max", "radius_um": "max"},
        {"index": "custom", "n_re": 1.0, "n_im": 0.0, "n_medium": 1.0},
        {"index": "custom", "n_re": 1.2, "n_medium": "max"},
        {"index": "water", "t_c": "max", "n_medium": "max"},
        {"light": "mono", "lam_nm": "min", "radius_um": "max"},
        {"light": "mono", "lam_nm": "max", "radius_um": "min"},
    ]),
    "p01_gravity": dict(F=10, n_random=60, pairs=[
        {"laws": "pn", "m_total": "max"},
        {"laws": "pn", "m_total": "min"},
        {"laws": "kerr", "m_hole": "max", "spin": "max", "charge": "max"},
        {"laws": "kerr", "m_hole": "min", "spin": "min", "charge": "max"},
        {"laws": "kerr", "spin": "max", "charge": "max"},
    ]),
    "p02_quantum": dict(F=6, n_random=50, workers=4, pal_param_modes=["dim=2d"], pairs=[
        {"dim": "2d", "n2": "512", "size": "max"},
        {"dim": "2d", "n2": "128", "size": "min"},
        {"dim": "3d", "n3": "128", "size": "max"},
        {"dim": "3d", "n3": "48", "size": "min", "edges": "closed"},
    ]),
    "p03_molecules": dict(F=6, n_random=50, workers=4, pal_param_modes=["dim=2d,model=lj", "dim=2d,model=hard"],
                         pairs=[
        {"dim": "3d", "Lx": "max", "Ly": "max", "Lz": "max"},
        {"dim": "3d", "Lx": "min", "Ly": "min", "Lz": "min"},
        {"dim": "2d", "Lx": "min", "Ly": "max"},
        {"model": "lj", "cutoff": "max", "Lx": "min", "Ly": "min"},
        {"model": "lj", "cutoff": "max", "shift": "energy", "dt_fs": "max"},
        {"model": "hard", "boundary": "walls"},
        {"model": "wca", "dt_fs": "max", "boundary": "slab"},
    ]),
    "p04_fluids": dict(F=4, n_random=40, workers=4, pairs=[
        {"fluid": "custom", "nu": "max", "u_max": "max"},
        {"fluid": "custom", "nu": "min", "u_max": "max"},
        {"fluid": "custom", "nu": "min", "u_max": "min"},
        {"fluid": "custom", "rho": "min", "nu": "max"},
        {"Lx": "min", "Ly": "max", "nx": "1024"},
        {"Lx": "max", "Ly": "min", "nx": "128"},
        {"Lx": "max", "Ly": "max", "nx": "1024"},
        {"u_max": "max", "collision": "bgk"},
        {"u_max": "min", "dye_D": "max"},
        {"fluid": "air", "u_max": "max", "nx": "1024"},
    ]),
}


def num_extremes(p):
    out = []
    if p["min"] is not None:
        out.append(("min", p["min"]))
    if p["max"] is not None:
        out.append(("max", p["max"]))
    return out


def resolve_val(p, v):
    if v == "min":
        return p["min"]
    if v == "max":
        return p["max"]
    if p["type"] == "select":
        for o in p["options"]:
            if str(o["value"]) == str(v):
                return o["value"]
    return v


def make_visible(sch_by_id, base_params: dict, pid: str) -> dict:
    """Values of the controlling parameters that make ``pid`` shown (first allowed value, recursively)."""
    out = {}
    p = sch_by_id[pid]
    for k, allowed in (p.get("show_if") or {}).items():
        cur = {**base_params, **out}.get(k)
        if cur in allowed:
            continue
        out[k] = allowed[0]
        out.update(make_visible(sch_by_id, {**base_params, **out}, k))
    return out


def rand_value(rng: random.Random, p):
    t = p["type"]
    if t == "select":
        return rng.choice(p["options"])["value"]
    if t == "bool":
        return rng.random() < 0.5
    lo, hi = p["min"], p["max"]
    d = p["default"]
    if lo is None and hi is None:
        lo, hi = -abs(d or 1) * 100, abs(d or 1) * 100
    elif lo is None:
        lo = hi - abs(hi - (d if d is not None else 0)) * 100 - 1
    elif hi is None:
        hi = lo + abs((d if d is not None else lo) - lo) * 100 + 1
    r = rng.random()
    if r < 0.15:
        x = lo
    elif r < 0.30:
        x = hi
    elif p["log"] and lo > 0:
        x = 10 ** rng.uniform(math.log10(lo), math.log10(hi))
    else:
        x = rng.uniform(lo, hi)
    if t == "int":
        x = int(round(x))
    else:
        x = float(f"{x:.4g}")
        x = min(max(x, lo), hi)
    return x


def action_variants(a: dict):
    """Arg dicts for an action form: defaults, then each numeric arg at min / max, each option of a select."""
    args = a.get("args") or []
    base = {}
    for q in args:
        if q.get("type") == "select":
            opts = q.get("options") or []
            base[q["id"]] = q.get("default", opts[0]["value"] if opts else None)
        else:
            base[q["id"]] = q.get("default", 0)
    out = [("default", dict(base))]
    for q in args:
        if q.get("type") == "select":
            for o in q.get("options") or []:
                if o["value"] != base[q["id"]]:
                    out.append((f"{q['id']}={o['value']}", {**base, q["id"]: o["value"]}))
        elif q.get("type") in ("float", "int", "number", None):
            for nm in ("min", "max"):
                if q.get(nm) is not None:
                    out.append((f"{q['id']}={nm}", {**base, q["id"]: q[nm]}))
    return out


# ---------------------------------------------------------------------------------------------------------------
def gen_demo(vid, viz, info, cfg, n_random, seed=20261104):
    sch = viz["schema"].to_json()
    params = [p for p in sch["params"] if not p["hidden"]]
    by_id = {p["id"]: p for p in sch["params"]}
    defaults = viz["schema"].defaults()
    presets = [p["id"] for p in sch["presets"]]
    F = cfg.get("F", 8)
    live = [p for p in params if p["live"]]
    actions = info.get("actions") or []
    combos = []
    run_ops = [["frames", F], ["next_event"], ["frames", F]]

    def add(kind, desc, preset=None, values=None, ops=None):
        combos.append({"kind": kind, "desc": desc, "preset": preset, "values": values or {},
                       "ops": ops if ops is not None else copy.deepcopy(run_ops)})

    add("default", "defaults")
    # one parameter at a time from the default (made visible)
    for p in params:
        vis = make_visible(by_id, defaults, p["id"])
        if p["type"] in ("float", "int"):
            vals = num_extremes(p)
        elif p["type"] == "select":
            vals = [(str(o["value"]), o["value"]) for o in p["options"] if o["value"] != p["default"]]
        elif p["type"] == "bool":
            vals = [(str(not p["default"]), not p["default"])]
        else:
            vals = []
        for nm, v in vals:
            add("single", f"{p['id']}={nm}" + (f" (+{vis})" if vis else ""), values={**vis, p["id"]: v})
            if p["live"]:  # also changed while the world runs
                ops = [["frames", F]] + ([["set", vis]] if vis else []) + [["set", {p["id"]: v}], ["frames", F],
                                                                          ["next_event"], ["frames", F]]
                add("live", f"set {p['id']}={nm}" + (f" (+{vis})" if vis else ""), ops=ops)
    # pairs / groups of interacting extremes
    for pr in cfg.get("pairs", []):
        vals = {k: resolve_val(by_id[k], v) for k, v in pr.items()}
        add("pair", ", ".join(f"{k}={v}" for k, v in pr.items()), values=vals)
        lv = {k: v for k, v in vals.items() if by_id[k]["live"]}
        if lv and len(lv) == len(vals):
            add("pair_live", "set " + ", ".join(f"{k}={v}" for k, v in pr.items()),
                ops=[["frames", F], ["set", lv], ["frames", F], ["next_event"], ["frames", F]])
    # all shown numeric parameters at min, and at max
    for nm in ("min", "max"):
        vals = {p["id"]: p[nm] for p in params if p["type"] in ("float", "int") and p[nm] is not None}
        add("all", f"all numeric at {nm}", values=vals)
    # presets; each live change at its extremes from two presets (round robin), each action variant from one preset
    # and each preset with the default form of every action (the load of the shared host forbids the full product)
    for pr in presets:
        add("preset", f"preset {pr}", preset=pr,
            ops=[["frames", F], ["next_event"], ["frames", F], ["step", None], ["ckpt"]])
        if info.get("planes", {}).get("max", 0) > 0:
            add("preset_view", f"preset {pr}: slice planes", preset=pr, ops=VIEW_OPS(info, F))
        for ai in range(len(info.get("actions_by_preset", {}).get(pr, actions))):
            add("preset_action", f"preset {pr}: action #{ai} default", preset=pr,
                ops=[["frames", F], ["action_pick", ai, 0], ["frames", F], ["next_event"],
                     ["action_pick", ai, 0], ["frames", F]])
    k = 0
    for p in live:
        if not presets:
            break
        if p["type"] in ("float", "int"):
            vals = [v for _, v in num_extremes(p)]
        elif p["type"] == "select":
            vals = [o["value"] for o in p["options"]]
        else:
            vals = [True, False]
        for _ in range(2):
            pr = presets[k % len(presets)]
            k += 1
            pv = {**defaults, **viz["schema"].presets[pr].get("params", {})}
            vis = make_visible(by_id, pv, p["id"])
            ops = [["frames", max(2, F // 2)]] + ([["set", vis]] if vis else [])
            for v in vals:
                ops += [["set", {p["id"]: v}], ["frames", max(2, F // 2)]]
            ops += [["set", {p["id"]: pv.get(p["id"], p["default"])}], ["next_event"], ["frames", max(2, F // 2)]]
            add("preset_live", f"preset {pr}: set {p['id']} over {vals}", preset=pr, ops=ops)
    for pr in presets:  # every variant (extremes) of every action of each preset's own form
        for ai, a in enumerate(info.get("actions_by_preset", {}).get(pr, actions)):
            for j in range(1, len(action_variants(a))):
                add("preset_action", f"preset {pr}: action {a['name']} {action_variants(a)[j][0]}", preset=pr,
                    ops=[["frames", F], ["action_pick", ai, j], ["frames", F], ["next_event"],
                         ["action_pick", ai, j], ["frames", F]])
    if info.get("planes", {}).get("max", 0) > 0:
        add("view_extreme", "slice planes at the box's edge and outside", ops=VIEW_EXTREME(info, F))
    # new world from the running one (a world parameter changed in the player)
    for p in params:
        if p["live"] or p["type"] not in ("float", "int", "select"):
            continue
        vis = make_visible(by_id, defaults, p["id"])
        v = p["max"] if p["type"] != "select" else p["options"][-1]["value"]
        add("new_world", f"new_world {p['id']}={v}", ops=[["frames", F], ["new_world", {"params": {**vis, p["id"]: v}}],
                                                         ["frames", F]])
        break  # one is enough: the path is shared; world params are covered by "single"
    # random sample
    rng = random.Random(seed + sum(map(ord, vid)))
    for i in range(n_random):
        pr = rng.choice(presets) if presets and rng.random() < 0.3 else None
        base = {**defaults, **(viz["schema"].presets[pr].get("params", {}) if pr else {})}
        vals = {}
        for p in params:
            if rng.random() < 0.5:
                vals[p["id"]] = rand_value(rng, p)
        ops = [["frames", F]]
        if live:
            for _ in range(2):
                p = rng.choice(live)
                ops += [["set", {p["id"]: rand_value(rng, p)}], ["frames", max(2, F // 2)]]
        if actions:
            a = rng.choice(actions)
            ops += [["action_pick", rng.randrange(8), rng.randrange(8)], ["frames", max(2, F // 2)]]
        ops += [["next_event"], ["frames", max(2, F // 2)]]
        add("random", f"random #{i}", preset=pr, values=vals, ops=ops)
    return combos


def VIEW_OPS(info, F):
    c = info["planes"].get("center", [0, 0, 0])
    return [["frames", F], ["view", {"op": "plane", "id": 1, "normal": [0.3, 0.4, 0.866]}],
            ["view", {"op": "plane", "id": 3}], ["frames", F],
            ["view", {"op": "plane", "id": 2, "origin": c, "auto": True, "speed": 1.0}], ["frames", F],
            ["view", {"op": "preview", "id": 1, "origin": c, "normal": [0, 0.6, 0.8]}],
            ["view", {"op": "remove", "id": 2}], ["view", {"op": "reset"}], ["frames", F]]


def VIEW_EXTREME(info, F):
    c = info["planes"].get("center", [0, 0, 0])
    far = [x + 1e6 for x in c]
    return [["frames", F], ["view", {"op": "plane", "id": 1, "origin": far}], ["frames", F],
            ["view", {"op": "plane", "id": 1, "origin": c, "normal": [1, 1, 1]}],
            ["view", {"op": "plane", "id": 2, "origin": c, "normal": [0, 0, 1]}],
            ["view", {"op": "plane", "id": 3, "origin": c, "normal": [0, 0, 1]}], ["frames", F],
            ["view", {"op": "plane", "id": 2, "auto": True, "speed": 1e9}], ["frames", F],
            ["view", {"op": "remove", "id": 1}], ["view", {"op": "remove", "id": 2}],
            ["view", {"op": "remove", "id": 3}], ["frames", F], ["view", {"op": "reset"}], ["frames", F]]


# ---------------------------------------------------------------------------------------------------------------
def gen_playground(vid, viz, info, cfg, n_random, palettes, seed=20261104):
    """palettes: {mode_key: (laws dict, {type: ObjectType json})}"""
    sch = viz["schema"].to_json()
    params = [p for p in sch["params"] if not p["hidden"]]
    by_id = {p["id"]: p for p in sch["params"]}
    defaults = viz["schema"].defaults()
    presets = [p["id"] for p in sch["presets"]]
    F = cfg.get("F", 6)
    combos = []

    def add(kind, desc, preset=None, values=None, ops=None):
        combos.append({"kind": kind, "desc": desc, "preset": preset, "values": values or {},
                       "ops": ops if ops is not None else [["frames", F]]})

    add("default", "empty scene, defaults")
    for p in params:
        vis = make_visible(by_id, defaults, p["id"])
        if p["type"] in ("float", "int"):
            vals = num_extremes(p)
        elif p["type"] == "select":
            vals = [(str(o["value"]), o["value"]) for o in p["options"] if o["value"] != p["default"]]
        else:
            vals = []
        for nm, v in vals:
            add("single", f"{p['id']}={nm}" + (f" (+{vis})" if vis else ""), values={**vis, p["id"]: v})
    for pr in cfg.get("pairs", []):
        vals = {k: resolve_val(by_id[k], v) for k, v in pr.items()}
        add("pair", ", ".join(f"{k}={v}" for k, v in pr.items()), values=vals)
    # presets: run, then a law change starting a new world from the preset's scene? (the player keeps the scene only
    # through a file); edits of each preset object, removal, duplicate, export, clear
    for pr in presets:
        add("preset", f"preset {pr}", preset=pr,
            ops=[["frames", F], ["frames", F], ["step", None], ["scene", {"op": "export"}], ["ckpt"], ["frames", F]])
        add("preset_edit", f"preset {pr}: edit each object at extremes", preset=pr,
            ops=[["frames", F], ["edit_all_extremes", F]])
        add("preset_remove", f"preset {pr}: remove / duplicate each object while running", preset=pr,
            ops=[["frames", F], ["dup_remove_all", F], ["scene", {"op": "clear"}], ["frames", F]])
        add("preset_add", f"preset {pr}: add each palette type (defaults)", preset=pr,
            ops=[["frames", F], ["add_each_type", F]])
    # palette: per mode, each object type alone with defaults, then each parameter at its extremes
    sweep = cfg.get("pal_param_modes")
    for mk, (laws, pal) in palettes.items():
        for typ, ot in pal.items():
            ps = [q for q in ot["params"] if not q.get("hidden")]
            add("palette", f"[{mk}] add {typ} defaults", values=laws,
                ops=[["scene", {"op": "add", "type": typ, "values": {}}], ["frames", F], ["next_event"], ["frames", F]])
            qby = {q["id"]: q for q in ps}
            qdef = {q["id"]: q["default"] for q in ps}
            for q in ps:
                vis = make_visible(qby, qdef, q["id"])
                if q["type"] in ("float", "int"):
                    vals = num_extremes(q)
                elif q["type"] == "select":
                    vals = [(str(o["value"]), o["value"]) for o in q["options"] if o["value"] != q["default"]]
                elif q["type"] == "bool":
                    vals = [(str(not q["default"]), not q["default"])]
                else:
                    vals = []
                if sweep is not None and mk not in sweep:
                    continue
                for nm, v in vals:
                    add("palette_param", f"[{mk}] add {typ} {q['id']}={nm}", values=laws,
                        ops=[["scene", {"op": "add", "type": typ, "values": {**vis, q["id"]: v}}], ["frames", F]])
            # edit while running: add with defaults, then set every param to min then max
            add("palette_edit", f"[{mk}] {typ}: edit every param to min/max while running", values=laws,
                ops=[["scene", {"op": "add", "type": typ, "values": {}}], ["frames", F],
                     ["edit_all_extremes", max(2, F // 2)], ["dup_remove_all", max(2, F // 2)]])
    # random scenes of several objects, edits and removals while running
    rng = random.Random(seed + 7)
    for i in range(n_random):
        mk = rng.choice(list(palettes))
        laws, pal = palettes[mk]
        vals = dict(laws)
        for p in params:
            if p["id"] not in laws and rng.random() < 0.3:
                vals[p["id"]] = rand_value(rng, p)
        ops = []
        types = list(pal)
        for _ in range(rng.randint(2, 6)):
            typ = rng.choice(types)
            ps = [q for q in pal[typ]["params"] if not q.get("hidden")]
            v = {q["id"]: rand_value(rng, q) for q in ps if rng.random() < 0.4}
            ops.append(["scene", {"op": "add", "type": typ, "values": v}])
        ops += [["frames", F], ["random_edit", i], ["frames", F], ["random_edit", i + 1000], ["frames", F],
                ["random_remove", i], ["frames", F]]
        add("random", f"random scene #{i} [{mk}]", values=vals, ops=ops)
    return combos


# ---------------------------------------------------------------------------------------------------------------
def scan_nonfinite(obj, path="", out=None, limit=8):
    if out is None:
        out = []
    if len(out) >= limit:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            scan_nonfinite(v, f"{path}.{k}", out, limit)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj[:2000]):
            scan_nonfinite(v, f"{path}[{i}]", out, limit)
    elif isinstance(obj, (float, np.floating)):
        if not math.isfinite(float(obj)):
            out.append(f"{path}={obj}")
    elif isinstance(obj, np.ndarray) and obj.dtype.kind == "f" and obj.size:
        if not np.all(np.isfinite(obj)):
            out.append(f"{path}=array nonfinite")
    return out


def where_of(tb):
    """The innermost frame of the project's code and the innermost frame overall."""
    frames = traceback.extract_tb(tb)
    proj = [f for f in frames if f.filename.startswith("/lf/")]
    inner = frames[-1] if frames else None
    p = proj[-1] if proj else None
    return ({"proj": f"{p.filename.replace('/lf/', '')}:{p.lineno} ({p.name})" if p else None,
             "inner": f"{inner.filename.replace('/lf/', '')}:{inner.lineno} ({inner.name})" if inner else None,
             "inner_in_proj": bool(inner and inner.filename.startswith("/lf/"))})


def child(vid, combo, conn, pal_ctx):
    """Run one combination; send ticks and the result over ``conn``."""
    t_start = time.time()
    res = {"world": vid, **{k: combo[k] for k in ("cid", "kind", "desc", "preset", "values", "ops")},
           "events": [], "classes": []}
    stats = {"nonfinite_meta": [], "blob_nan": {}, "blob_inf": {}, "empty": [], "n_msgs": 0, "types": {}}
    checks = {}
    cur_actions = []
    errors_seen = []
    notices = []

    def tick(label):
        conn.send(("tick", label, time.time()))

    def ev(cls, op, text, exc=None, extra=None):
        d = {"cls": cls, "op": op, "text": (text or "")[:1500]}
        if exc is not None:
            d["exc_type"] = type(exc).__name__
            d.update(where_of(exc.__traceback__))
        if extra:
            d.update(extra)
        res["events"].append(d)

    viz = registry.load(vid)
    sch = viz["schema"]

    def emit(meta, blobs=None):
        stats["n_msgs"] += 1
        typ = meta.get("type")
        stats["types"][typ] = stats["types"].get(typ, 0) + 1
        nf = scan_nonfinite({k: v for k, v in meta.items() if k not in ("params",)}, typ)
        if nf and len(stats["nonfinite_meta"]) < 40:
            stats["nonfinite_meta"].append({"t": meta.get("t"), "type": typ, "where": nf[:4]})
        if blobs:
            for k, a in blobs.items():
                a = np.asarray(a)
                if a.dtype.kind == "f" and a.size:
                    nan = float(np.isnan(a).mean())
                    inf = int(np.isinf(a).sum())
                    key = f"{typ}.{k}"
                    if nan > stats["blob_nan"].get(key, 0):
                        stats["blob_nan"][key] = nan
                    if inf:
                        stats["blob_inf"][key] = stats["blob_inf"].get(key, 0) + inf
                    if typ in ("frame", "image", "wave", "volume", "cloud", "slice", "target") and nan == 1.0:
                        if len(stats["empty"]) < 10:
                            stats["empty"].append(f"{key} all NaN at t={meta.get('t')}")
        protocol.encode(meta, blobs)  # what the worker does: an unencodable message fails here
        if typ in ("header", "actions") and isinstance(meta.get("actions"), list):
            cur_actions[:] = meta["actions"]
        if typ == "check":
            checks[meta.get("id")] = {k: meta.get(k) for k in ("id", "label", "value", "ref", "rel", "tol", "ok",
                                                               "info", "note", "t")}
        elif typ == "error":
            errors_seen.append({"t": meta.get("t"), "text": str(meta.get("text"))[:2000]})
        elif typ == "notice":
            if len(notices) < 30:
                notices.append(str(meta.get("text"))[:400])

    # 1. the server's start: schema, scene form, the world, its header and t = 0
    tick("resolve")
    params, errs = sch.resolve(combo["preset"], combo["values"])
    if errs:
        ev("refuse_start", "start", "параметры: " + "; ".join(errs), extra={"stage": "resolve(400)"})
        res["final"] = "refused at start"
        return finish(res, stats, checks, errors_seen, notices, t_start, conn, None)
    if viz.get("kind") == "playground" and params.get("scene"):
        from lfviz.playground import check_scene
        try:
            check_scene(params["scene"], vid)
        except Exception as e:  # noqa: BLE001
            ev("refuse_start", "start", str(e), e, {"stage": "check_scene(400)"})
            return finish(res, stats, checks, errors_seen, notices, t_start, conn, None)
    tick("build")
    t0 = time.time()
    try:
        sim = viz["simulation"](params, 1, emit)
    except Exception as e:  # noqa: BLE001
        res["build_s"] = round(time.time() - t0, 2)
        ev("refuse_build", "build", f"Мир не создан: {e}", e, {"stage": "worker build"})
        return finish(res, stats, checks, errors_seen, notices, t_start, conn, None)

    def make_world(pr, values, sd):
        p, es = sch.resolve(pr, values or {})
        if es:
            raise ValueError("; ".join(es))
        return viz["simulation"](p, 1 if sd is None else int(sd), emit), {"preset": pr}

    q = queue.Queue()
    runner = Runner(sim, emit, q, fps=FPS, make_world=make_world, world_info={"preset": combo["preset"]})
    try:
        runner._start_world()
    except Exception as e:  # noqa: BLE001 - the worker would die here (outside the run loop's try)
        res["build_s"] = round(time.time() - t0, 2)
        ev("crash", "header", traceback.format_exc()[-1500:], e, {"stage": "header (worker dies)"})
        return finish(res, stats, checks, errors_seen, notices, t_start, conn, runner)
    res["build_s"] = round(time.time() - t0, 2)
    res["speed"] = runner.speed
    frame_times = []
    progress = []

    def handle(msg, label):
        """As Runner.run: a command; any exception escaping handle() is a traceback in the player."""
        try:
            runner.handle(msg)
        except Exception as e:  # noqa: BLE001
            ev("crash", label, traceback.format_exc()[-1500:], e, {"stage": "run loop (traceback shown)"})
            runner.playing = False
            return False
        return True

    def frames(n, label):
        runner.playing = True
        t_a = runner.sim.t
        for i in range(int(n)):
            tick(f"{label} frame {i}")
            a = time.time()
            try:
                runner._advance(runner.sim.t + runner.speed / FPS, budget=0.6 / FPS)
                runner._frame((time.time() - a) * 1e3)
            except Exception as e:  # noqa: BLE001
                ev("crash", label, traceback.format_exc()[-1500:], e, {"stage": "frame (traceback shown, paused)"})
                runner.playing = False
                return False
            frame_times.append(time.time() - a)
        runner.playing = False
        progress.append({"op": label, "dt": runner.sim.t - t_a, "want": runner.speed * n / FPS})
        return True

    # patch the world's command methods to learn the exception types behind refusals
    caught = {}

    def wrap(obj, name):
        f = getattr(obj, name, None)
        import inspect
        if f is None or not inspect.ismethod(f):  # v10 keeps its scene object in .scene: not a command method
            return

        def g(*a, **k):
            try:
                return f(*a, **k)
            except Exception as e:  # noqa: BLE001
                caught["last"] = (e, where_of(e.__traceback__), traceback.format_exc()[-1200:])
                raise
        setattr(obj, name, g)

    def patch():
        for nm in ("set_live", "action", "view", "scene"):
            wrap(runner.sim, nm)
    patch()
    orig_make = runner.make_world

    def mk(*a):
        try:
            return orig_make(*a)
        except Exception as e:  # noqa: BLE001
            caught["last"] = (e, where_of(e.__traceback__), traceback.format_exc()[-1200:])
            raise
    runner.make_world = mk

    def command(msg, label):
        tick(label)
        n_err = len(errors_seen)
        caught.pop("last", None)
        sim_before = runner.sim
        ok = handle(msg, label)
        if runner.sim is not sim_before:
            patch()
        if not ok:
            return
        for e in errors_seen[n_err:]:
            c = caught.get("last")
            extra = {"stage": "refused command"}
            if c:
                extra.update(c[1])
                extra["exc_type"] = type(c[0]).__name__
                extra["tb"] = c[2]
            ev("refuse_cmd", label, e["text"], extra=extra)

    rng = random.Random(combo.get("cid", 0))
    ok = True
    for i, op in enumerate(combo["ops"]):
        name = op[0]
        label = f"op{i}:{name}"
        if not ok:
            break
        tick(label)
        if name == "frames":
            ok = frames(op[1], label)
        elif name == "next_event":
            a = time.time()
            ok = handle({"cmd": "next_event"}, label)
            frame_times.append(time.time() - a)
            if ok:
                ok = frames(1, label + "+frame")
        elif name == "step":
            a = time.time()
            ok = handle({"cmd": "step", "args": {} if op[1] is None else {"dt": op[1]}}, label)
            frame_times.append(time.time() - a)
            if ok:
                ok = frames(1, label + "+frame")
        elif name == "set":
            command({"cmd": "set", "args": {"values": op[1]}}, label)
        elif name == "action":
            command({"cmd": "action", "args": {"name": op[1], "args": op[2]}}, label)
        elif name == "action_pick":  # an action of the form the player shows now (the world's own header)
            if cur_actions:
                a = cur_actions[op[1] % len(cur_actions)]
                vs = action_variants(a)
                nm, args = vs[op[2] % len(vs)]
                res.setdefault("picked", []).append(f"{a['name']} {nm}")
                command({"cmd": "action", "args": {"name": a["name"], "args": args}}, f"{label} {a['name']} {nm}")
        elif name == "view":
            command({"cmd": "view", "args": op[1]}, label)
        elif name == "scene":
            command({"cmd": "scene", "args": op[1]}, label)
        elif name == "new_world":
            command({"cmd": "new_world", "args": op[1]}, label)
        elif name == "ckpt":
            try:
                from lfviz import checkpoint as C
                a = time.time()
                data = C.dumps(runner.checkpoint_state(), emit)
                st = C.loads(data, emit)
                res["ckpt"] = {"bytes": len(data), "s": round(time.time() - a, 2)}
            except Exception as e:  # noqa: BLE001
                ev("ckpt_fail", label, f"{type(e).__name__}: {e}"[:500], e)
        elif name in ("edit_all_extremes", "dup_remove_all", "add_each_type", "random_edit", "random_remove"):
            ok = playground_op(runner, name, op[1], label, command, frames, rng, pal_ctx)
    res["t_end"] = runner.sim.t
    res["frame_max_s"] = round(max(frame_times), 3) if frame_times else None
    res["frames_n"] = len(frame_times)
    res["progress"] = progress
    return finish(res, stats, checks, errors_seen, notices, t_start, conn, runner)


def playground_op(runner, name, arg, label, command, frames, rng, pal_ctx):
    sim = runner.sim
    pal = {k: ot.to_json() for k, ot in sim.PALETTE.items()}
    objs = list(sim.objects.values())
    F = arg if isinstance(arg, int) else 3
    if name == "edit_all_extremes":
        for o in objs:
            ps = [q for q in pal[o["type"]]["params"] if not q.get("hidden")]
            for q in ps:
                if q["type"] in ("float", "int"):
                    vals = [v for _, v in num_extremes(q)]
                elif q["type"] == "select":
                    vals = [x["value"] for x in q["options"]]
                elif q["type"] == "bool":
                    vals = [True, False]
                else:
                    continue
                for v in vals:
                    if o["id"] not in runner.sim.objects:
                        break
                    command({"cmd": "scene", "args": {"op": "set", "id": o["id"], "values": {q["id"]: v}}},
                            f"{label} set {o['type']}.{q['id']}={v}")
                    if not frames(1, f"{label} after {o['type']}.{q['id']}={v}"):
                        return False
                if o["id"] in runner.sim.objects:  # back to the object's value
                    command({"cmd": "scene", "args": {"op": "set", "id": o["id"],
                                                      "values": {q["id"]: o["values"][q["id"]]}}},
                            f"{label} reset {o['type']}.{q['id']}")
        return frames(F, label + " end")
    if name == "dup_remove_all":
        for o in objs:
            command({"cmd": "scene", "args": {"op": "duplicate", "id": o["id"]}}, f"{label} dup {o['type']}")
            if not frames(1, f"{label} after dup {o['type']}"):
                return False
            command({"cmd": "scene", "args": {"op": "remove", "id": o["id"]}}, f"{label} remove {o['type']}")
            if not frames(1, f"{label} after remove {o['type']}"):
                return False
        return frames(F, label + " end")
    if name == "add_each_type":
        for typ in pal:
            command({"cmd": "scene", "args": {"op": "add", "type": typ, "values": {}}}, f"{label} add {typ}")
            if not frames(1, f"{label} after add {typ}"):
                return False
        return frames(F, label + " end")
    if name == "random_edit":
        if not objs:
            return True
        o = rng.choice(objs)
        ps = [q for q in pal[o["type"]]["params"] if not q.get("hidden")]
        if not ps:
            return True
        q = rng.choice(ps)
        v = rand_value(rng, q)
        command({"cmd": "scene", "args": {"op": "set", "id": o["id"], "values": {q["id"]: v}}},
                f"{label} set {o['type']}.{q['id']}={v}")
        return True
    if name == "random_remove":
        if not objs:
            return True
        o = rng.choice(objs)
        command({"cmd": "scene", "args": {"op": "remove", "id": o["id"]}}, f"{label} remove {o['type']}")
        return True
    return True


def failed_check(c):
    if c.get("info"):
        return False
    if c.get("ok") is True or c.get("ok") is False:
        return c["ok"] is False
    rel, ref = c.get("rel"), c.get("ref")
    if ref is None or rel is None:
        return False
    try:
        return abs(float(rel)) > max(float(c.get("tol") or 1e-9), 1e-12)
    except (TypeError, ValueError):
        return False


def finish(res, stats, checks, errors_seen, notices, t_start, conn, runner):
    res["wall_s"] = round(time.time() - t_start, 2)
    res["stats"] = stats
    res["errors"] = errors_seen[:30]
    res["notices"] = notices[:30]
    fc = [c for c in checks.values() if failed_check(c)]
    res["failed_checks"] = fc[:20]
    res["checks_n"] = len(checks)
    nan_checks = [c for c in checks.values() if any(isinstance(c.get(k), float) and not math.isfinite(c[k])
                                                   for k in ("value", "ref", "rel"))]
    res["nan_checks"] = nan_checks[:10]
    conn.send(("done", json.loads(json.dumps(res, default=str))))
    conn.close()


# ---------------------------------------------------------------------------------------------------------------
def palettes_for(vid, viz):
    """Palettes of a playground per mode of its laws."""
    sch = viz["schema"]
    modes = {
        "p01_gravity": [{"laws": "newton"}, {"laws": "pn"}, {"laws": "kerr"}],
        "p02_quantum": [{"dim": "2d"}, {"dim": "3d"}],
        "p03_molecules": [{"dim": d, "model": m} for d in ("2d", "3d") for m in ("lj", "wca", "hard")],
        "p04_fluids": [{}],
    }[vid]
    out = {}
    for laws in modes:
        p, errs = sch.resolve(None, laws)
        sim = viz["simulation"](p, 1, lambda m, b=None: None)
        key = ",".join(f"{k}={v}" for k, v in laws.items()) or "default"
        out[key] = (laws, {k: ot.to_json() for k, ot in sim.PALETTE.items()})
    return out


def world_info(vid, viz):
    sch = viz["schema"]
    p, _ = sch.resolve(None, {})
    msgs = []
    sim = viz["simulation"](p, 1, lambda m, b=None: msgs.append(m))
    h, _ = sim.header()
    sc = h.get("scene3d") or {}
    out = {"actions": h.get("actions") or [], "planes": sc.get("planes") or {}, "actions_by_preset": {}}
    if out["actions"]:
        for pr in sch.presets:
            pp, _ = sch.resolve(pr, {})
            try:
                hh, _ = viz["simulation"](pp, 1, lambda m, b=None: None).header()
                out["actions_by_preset"][pr] = hh.get("actions") or []
            except Exception:  # noqa: BLE001
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("world")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--n-random", type=int, default=None)
    ap.add_argument("--out", default="/out/res")
    ap.add_argument("--only", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cids", default="", help="only these combination ids (comma separated)")
    a = ap.parse_args()
    vid = a.world
    viz = registry.load(vid)
    cfg = WORLD.get(vid, {})
    n_random = a.n_random if a.n_random is not None else cfg.get("n_random", 40)
    W = a.workers or cfg.get("workers", 5)
    if vid.startswith("p"):
        pals = palettes_for(vid, viz)
        info = {"actions": [], "planes": {}}
        combos = gen_playground(vid, viz, info, cfg, n_random, pals)
    else:
        info = world_info(vid, viz) if vid != "v08_wave_3d" else {"actions": [], "planes": {
            "max": 3, "center": [0.0, 0.0, 15.0]}}
        pals = None
        combos = gen_demo(vid, viz, info, cfg, n_random)
    for i, c in enumerate(combos):
        c["cid"] = i
    if a.cids:
        keep = {int(x) for x in a.cids.split(",")}
        combos = [c for c in combos if c["cid"] in keep]
    if a.only:
        kinds = set(a.only.split(","))
        combos = [c for c in combos if c["kind"] in kinds]
    if a.limit:
        combos = combos[:a.limit]
    if a.list:
        from collections import Counter
        print(len(combos), Counter(c["kind"] for c in combos))
        return
    os.makedirs(a.out, exist_ok=True)
    path = f"{a.out}/{vid}.jsonl"
    done = set()
    if os.path.exists(path):
        for line in open(path):
            try:
                done.add(json.loads(line)["cid"])
            except Exception:  # noqa: BLE001
                pass
    todo = [c for c in combos if c["cid"] not in done]
    print(f"{vid}: {len(combos)} combinations, {len(todo)} to run, {W} workers", flush=True)
    ctx = mp.get_context("fork")
    out = open(path, "a")
    active = {}
    from multiprocessing.connection import wait
    t_all = time.time()
    n_done = 0
    while todo or active:
        while todo and len(active) < W:
            c = todo.pop(0)
            r, w = ctx.Pipe(duplex=False)
            p = ctx.Process(target=_child_entry, args=(vid, c, w, None))
            p.start()
            w.close()
            now = time.time()
            active[r] = {"p": p, "c": c, "start": now, "tick": now, "label": "start", "slow": []}
        ready = wait(list(active), timeout=0.5)
        for r in ready:
            st = active[r]
            try:
                msg = r.recv()
            except (EOFError, OSError):
                st["p"].join(5)
                res = {"world": vid, **{k: st["c"][k] for k in ("cid", "kind", "desc", "preset", "values", "ops")},
                       "events": [{"cls": "crash", "op": st["label"], "text":
                                   f"worker process died (exit code {st['p'].exitcode})"}],
                       "wall_s": round(time.time() - st["start"], 2)}
                res["slow"] = st["slow"]
                out.write(json.dumps(res, ensure_ascii=False) + "\n")
                out.flush()
                del active[r]
                n_done += 1
                continue
            if msg[0] == "tick":
                now = time.time()
                el = now - st["tick"]
                lim = BUILD_SLOW if st["label"] == "build" else OP_SLOW
                if el > lim:
                    st["slow"].append({"op": st["label"], "s": round(el, 1)})
                st["tick"], st["label"] = now, msg[1]
            elif msg[0] == "done":
                res = msg[1]
                el = time.time() - st["tick"]
                lim = BUILD_SLOW if st["label"] == "build" else OP_SLOW
                if el > lim:
                    st["slow"].append({"op": st["label"], "s": round(el, 1)})
                res["slow"] = st["slow"]
                out.write(json.dumps(res, ensure_ascii=False) + "\n")
                out.flush()
                st["p"].join(10)
                del active[r]
                n_done += 1
        now = time.time()
        for r, st in list(active.items()):
            el = now - st["tick"]
            kill = BUILD_KILL if st["label"] == "build" else OP_KILL
            if el > kill or now - st["start"] > COMBO_KILL:
                try:
                    os.kill(st["p"].pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                st["p"].join(5)
                res = {"world": vid, **{k: st["c"][k] for k in ("cid", "kind", "desc", "preset", "values", "ops")},
                       "events": [{"cls": "hang", "op": st["label"],
                                   "text": f"no progress for {el:.0f} s in {st['label']} (killed; combination "
                                           f"{now - st['start']:.0f} s)"}],
                       "wall_s": round(now - st["start"], 2)}
                res["slow"] = st["slow"] + [{"op": st["label"], "s": round(el, 1), "killed": True}]
                out.write(json.dumps(res, ensure_ascii=False) + "\n")
                out.flush()
                del active[r]
                n_done += 1
        if n_done and n_done % 50 == 0 and n_done != globals().get("_last_print"):
            globals()["_last_print"] = n_done
            print(f"  {n_done} done, {len(todo)} left, {time.time() - t_all:.0f} s", flush=True)
    print(f"{vid}: finished in {time.time() - t_all:.0f} s", flush=True)


MEM_LIMIT_GB = float(os.environ.get("AUDIT_MEM_GB", "8"))  # per child: an allocation beyond it is a MemoryError, not
# a host-wide OOM (a v02 combination took 31 GB and triggered the kernel's OOM killer on 2026-11-04 before this limit)


def _child_entry(vid, combo, conn, pal_ctx):
    try:
        import resource
        lim = int(MEM_LIMIT_GB * 2**30)
        resource.setrlimit(resource.RLIMIT_AS, (lim, lim))
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        child(vid, combo, conn, pal_ctx)
    except Exception:  # noqa: BLE001 - a bug of this script, not of the world
        try:
            conn.send(("done", {"world": vid, "cid": combo["cid"], "kind": combo["kind"], "desc": combo["desc"],
                                "preset": combo["preset"], "values": combo["values"], "ops": combo["ops"],
                                "events": [{"cls": "audit_bug", "op": "?", "text": traceback.format_exc()[-1500:]}]}))
        except Exception:  # noqa: BLE001
            pass


if __name__ == "__main__":
    main()
