"""Dynamic scan beyond test_i18n's: every world, ALL presets (not the first two), 12 steps, plus the 'set' of every live
parameter to its min/max. Collects (1) msgids of T objects missing from the ru catalogue (own entries), (2) PLAIN
strings with Latin words in user-facing fields that the ru catalogue lacks (the tests see only T objects), (3) refusals /
failures whose owner text is not a T (plain English). Usage: python c04_dynamic_scan.py [viz_id ...]"""
import json, os, queue, re, signal, sys, traceback
sys.path[:0] = ["/w/visualizations", "/w/visualizations/server", "/w/lfphys", "/w/visualizations/tests"]
os.environ.setdefault("LFVIZ_EXTRA", "/w/visualizations/tests/playgrounds:/w/visualizations/tests/instruments_worlds")
from lfviz import i18n, registry
from lfviz.i18n import is_t, msgids, text_of
from lfviz.sim import Runner
import i18n_tools as tools

own = i18n._merge("ru")[0]
KEYS = {"label", "unit", "units", "help", "group", "title", "summary", "purpose", "note", "notes", "text", "name", "hint",
        "legend", "xlabel", "ylabel", "axis", "caption", "what", "message", "energy_unit", "time_unit", "description",
        "kind_label", "status", "short"}
LAT = re.compile(r"[A-Za-z]{3,}")


def plain_strings(x, path=""):
    out = []
    if is_t(x):
        for k, v in (x.get("a") or {}).items():
            if isinstance(v, str) and LAT.search(v) and v not in own:
                out.append((path + "/$t-arg:" + k, v))
            elif isinstance(v, (dict, list)):
                out += plain_strings(v, path + "/a." + k)
        return out
    if isinstance(x, dict):
        for k, v in x.items():
            if isinstance(v, str):
                if k in KEYS and LAT.search(v) and v not in own:
                    out.append((path + "/" + k, v))
            else:
                out += plain_strings(v, path + "/" + str(k))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            if isinstance(v, str) and path.rsplit("/", 1)[-1] in KEYS and LAT.search(v) and v not in own:
                out.append((path, v))
            else:
                out += plain_strings(v, path + "[]")
    return out


class Timeout(Exception):
    pass


def alarm(*_):
    raise Timeout()


signal.signal(signal.SIGALRM, alarm)
SMALL = {"v08_wave_3d": {"n": 128, "zmax": 10.0}, "v09_thomas_3d": {"ngrid": 48},
         "v11_double_slit_2d": {"a": 1.5, "d": 4.0, "w": 1.0, "L": 12.0, "sigma_x": 3.0, "sigma_z": 2.0, "grid": "coarse",
                                "n_bohm": 100, "n_tracks": 10},
         "v12_arrival_times_2d": {"grid": "coarse", "n_bohm": 100, "n_tracks": 10, "L": 12.0, "sigma_z": 2.0, "sigma_x": 2.0},
         "v17_mie_scattering": {"radius_um": 1.0, "width": 0.05, "n_lam": 8}}
ids = sys.argv[1:] or registry.viz_ids()
report = {}
for vid in ids:
    R = {"missing_T": set(), "plain": {}, "plain_refusals": [], "errors": []}
    try:
        viz = registry.load(vid)
        desc = registry.describe(viz)
        R["missing_T"] |= {m for m in msgids(desc) if tools.needs_translation(m) and m not in own}
        for p, v in plain_strings(desc, "describe"):
            R["plain"].setdefault(v, p)
        sch = viz["schema"]
        presets = list(sch.presets) or [None]
        for preset in presets:
            signal.alarm(90)
            try:
                params, errors = sch.resolve(preset, SMALL.get(vid, {}))
                if errors:
                    continue
                msgs = []
                emit = lambda meta, blobs=None: msgs.append(meta)
                sim = viz["simulation"](params, 3, emit)
                run = Runner(sim, emit, queue.Queue())
                run._start_world()
                for _ in range(12):
                    run.handle({"cmd": "step", "args": {}})
                for p in sch.params:
                    if not p.live or p.type not in ("float", "int"):
                        continue
                    for v in (p.min, p.max):
                        if v is None:
                            continue
                        n0 = len(msgs)
                        run.handle({"cmd": "set", "args": {p.id: v}})
                        run.handle({"cmd": "step", "args": {}})
                for m in msgs:
                    R["missing_T"] |= {x for x in msgids(m) if tools.needs_translation(x) and x not in own}
                    for path, v in plain_strings(m, m.get("type", "?")):
                        R["plain"].setdefault(v, f"{preset}:{path}")
                    for k in ("text", "error", "message", "reason"):
                        v = m.get(k)
                        if isinstance(v, str) and LAT.search(v) and v not in own:
                            R["plain_refusals"].append(f"{preset}: {m.get('type')}.{k}: {v[:200]}")
            except Timeout:
                R["errors"].append(f"{preset}: timeout")
            except Exception as e:
                R["errors"].append(f"{preset}: {type(e).__name__}: {str(e)[:200]}")
            finally:
                signal.alarm(0)
    except Exception as e:
        R["errors"].append(f"load: {type(e).__name__}: {e}")
    R["missing_T"] = sorted(R["missing_T"])
    report[vid] = R
    print(vid, "missing_T", len(R["missing_T"]), "plain", len(R["plain"]), "plain_refusals", len(R["plain_refusals"]),
          "errors", len(R["errors"]), flush=True)
json.dump(report, open(os.environ.get("OUT", "/dev/stdout"), "w"), ensure_ascii=False, indent=1, default=str)
