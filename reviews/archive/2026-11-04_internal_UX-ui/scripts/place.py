"""Placement audit (UX-ui): every palette object of p01-p04, placed the way a user would, through the runner's
`scene` command (what the player sends). Records the message the user would see (the runner's `error` text) and the
outcome. Run in the light-funnel-viz image with /lf mounted read-only:
  docker run --rm --name lf-uxb-place -v <engine>:/lf:ro -v <aui>:/aui -e LFPHYS_NO_GPU=1 -w /lf/visualizations \
    light-funnel-viz python3 /aui/py/place.py [section ...]
Prints JSON lines; writes /aui/out/place.jsonl."""
import json, math, os, signal, sys, time, traceback
sys.path[:0] = ["/lf/visualizations", "/lf/visualizations/server", "/lf/lfphys", "/lf"]
from tests.harness import Harness

class Hang(BaseException):
    pass

def _alarm(*a):
    raise Hang()

signal.signal(signal.SIGALRM, _alarm)
OUT = open("/aui/out/place.jsonl", "a")

def rec(**kw):
    line = json.dumps(kw, ensure_ascii=False, default=str)
    print(line, flush=True)
    OUT.write(line + "\n"); OUT.flush()

def cmd(h, args, limit=30):
    """The player's scene command; returns (outcome, user message, seconds)."""
    n0 = len(h.msgs)
    n_obj0 = len(h.sim.objects)
    t0 = time.time()
    signal.alarm(limit)
    try:
        h.runner.handle({"cmd": "scene", "args": args})
        hung = False
    except Hang:
        hung = True
    finally:
        signal.alarm(0)
    dt = time.time() - t0
    new = h.msgs[n0:]
    errs = [m["text"] for m, _ in new if m.get("type") == "error"]
    evs = [m["text"] for m, _ in new if m.get("type") == "event" and m.get("kind") == "scene"]
    if hung:
        return "HANG>%ds" % limit, "", dt, len(h.sim.objects) - n_obj0
    if errs:
        return "refused", errs[0], dt, len(h.sim.objects) - n_obj0
    return ("ok" if evs else "nothing"), (evs[0] if evs else ""), dt, len(h.sim.objects) - n_obj0

def run_frames(h, n=3, limit=60):
    """Advance as the runner's loop would at the default speed; any exception is what the user would see raw."""
    sp = h.runner.speed
    t0 = time.time()
    signal.alarm(limit)
    try:
        for _ in range(n):
            h.runner._advance(h.sim.t + sp / h.runner.fps, budget=None)
            h.runner._frame(0.0)
        return "ok", "", time.time() - t0
    except Hang:
        return "HANG>%ds" % limit, "", time.time() - t0
    except Exception as e:
        tb = traceback.format_exc()
        return "EXC", tb.strip().splitlines()[-1][:300], time.time() - t0
    finally:
        signal.alarm(0)

def palette(h):
    hd = [m for m, _ in h.msgs if m.get("type") == "header"][-1]
    return hd["playground"]["palette"], hd

VARIANTS = {
    "p01_gravity": [("newton", {"laws": "newton"}), ("pn", {"laws": "pn"}), ("kerr", {"laws": "kerr"})],
    "p02_quantum": [("2d", {"dim": "2d", "n2": "128"}), ("3d", {"dim": "3d", "n3": "48"})],
    "p03_molecules": [("2d-lj", {"dim": "2d", "model": "lj"}), ("2d-hard", {"dim": "2d", "model": "hard"}),
                      ("3d-lj", {"dim": "3d", "model": "lj"}), ("2d-walls", {"dim": "2d", "model": "lj", "boundary": "walls"})],
    "p04_fluids": [("dfg", {"fluid": "dfg", "nx": "256"})],
}
# a preset to try "add with defaults into a typical scene"
PRESET = {"p01_gravity": {"newton": "inner", "pn": "pn_inspiral", "kerr": "kerr_orbits"},
          "p02_quantum": {"2d": "double_slit", "3d": "ball_3d"},
          "p03_molecules": {"2d-lj": "maxwell", "2d-hard": "hard_disks", "3d-lj": "liquid_vapour", "2d-walls": "piston"},
          "p04_fluids": {"dfg": "cylinder_re20"}}

def fresh(viz, params, preset=None):
    if preset:
        return Harness(viz, preset=preset)
    return Harness(viz, params=dict(params))

def main(sections):
    for viz in sections:
        for vname, params in VARIANTS[viz]:
            try:
                h = fresh(viz, params)
            except Exception as e:
                rec(viz=viz, variant=vname, op="world", outcome="EXC", msg=str(e)); continue
            pal, hd = palette(h)
            box = (hd.get("scene3d") or {}).get("box")
            rec(viz=viz, variant=vname, op="world", outcome="ok", box=box, types=[p["type"] for p in pal])
            for ot in pal:
                typ = ot["type"]
                # A: defaults into an empty world, then advance
                h = fresh(viz, params)
                o, msg, dt, dn = cmd(h, {"op": "add", "type": typ, "values": {}})
                rec(viz=viz, variant=vname, type=typ, op="add_default_empty", outcome=o, msg=msg, s=round(dt, 2), dn=dn)
                if o == "ok":
                    fo, fmsg, fdt = run_frames(h)
                    rec(viz=viz, variant=vname, type=typ, op="advance_after_add", outcome=fo, msg=fmsg, s=round(fdt, 2),
                        n_obj=len(h.sim.objects))
                    # B: the same again (a second click on the palette button)
                    o2, msg2, dt2, dn2 = cmd(h, {"op": "add", "type": typ, "values": {}})
                    rec(viz=viz, variant=vname, type=typ, op="add_default_twice", outcome=o2, msg=msg2, s=round(dt2, 2), dn=dn2)
                    if o2 == "ok":
                        fo, fmsg, fdt = run_frames(h)
                        rec(viz=viz, variant=vname, type=typ, op="advance_after_twice", outcome=fo, msg=fmsg, s=round(fdt, 2),
                            n_obj=len(h.sim.objects))
                    # G: edit each numeric parameter, then duplicate, then remove
                    oid = next((k for k, v in h.sim.objects.items() if v["type"] == typ), None)
                    if oid:
                        for p in ot["params"]:
                            if p.get("hidden") or p["type"] not in ("float", "int"):
                                continue
                            d = p["default"]
                            lo, hi = p.get("min"), p.get("max")
                            new = d * 1.5 if d not in (0, None) else (0.5 * (hi or 1.0) if (hi or 0) < 10 else 1.0)
                            if p["type"] == "int":
                                new = int(round(new)) if int(round(new)) != d else d + 1
                            if hi is not None:
                                new = min(new, hi)
                            if lo is not None:
                                new = max(new, lo)
                            if new == d:
                                continue
                            o3, m3, dt3, _ = cmd(h, {"op": "set", "id": oid, "values": {p["id"]: new}})
                            rec(viz=viz, variant=vname, type=typ, op="set", param=p["id"], value=new, outcome=o3, msg=m3, s=round(dt3, 2))
                        for p in ot["params"]:
                            if p["type"] == "select" and not p.get("hidden"):
                                for opt in p["options"][1:]:
                                    o3, m3, dt3, _ = cmd(h, {"op": "set", "id": oid, "values": {p["id"]: opt["value"]}})
                                    rec(viz=viz, variant=vname, type=typ, op="set", param=p["id"], value=opt["value"], outcome=o3, msg=m3, s=round(dt3, 2))
                        fo, fmsg, fdt = run_frames(h)
                        rec(viz=viz, variant=vname, type=typ, op="advance_after_edits", outcome=fo, msg=fmsg, s=round(fdt, 2))
                        if oid in h.sim.objects:
                            o4, m4, dt4, dn4 = cmd(h, {"op": "duplicate", "id": oid})
                            rec(viz=viz, variant=vname, type=typ, op="duplicate", outcome=o4, msg=m4, s=round(dt4, 2), dn=dn4)
                            o5, m5, dt5, dn5 = cmd(h, {"op": "remove", "id": oid})
                            rec(viz=viz, variant=vname, type=typ, op="remove", outcome=o5, msg=m5, s=round(dt5, 2), dn=dn5)
                # C: defaults into the typical preset scene
                pr = PRESET[viz].get(vname)
                if pr:
                    try:
                        hp = fresh(viz, params, preset=pr)
                        run_frames(hp, 2)
                        o6, m6, dt6, dn6 = cmd(hp, {"op": "add", "type": typ, "values": {}})
                        rec(viz=viz, variant=vname, type=typ, op="add_default_in_preset:" + pr, outcome=o6, msg=m6, s=round(dt6, 2), dn=dn6)
                        if o6 == "ok":
                            fo, fmsg, fdt = run_frames(hp)
                            rec(viz=viz, variant=vname, type=typ, op="advance_in_preset", outcome=fo, msg=fmsg, s=round(fdt, 2))
                    except Exception as e:
                        rec(viz=viz, variant=vname, type=typ, op="preset_world:" + pr, outcome="EXC", msg=str(e)[:200])
                # E/F: each numeric parameter at its max and at its min (others default), into an empty world
                for p in ot["params"]:
                    if p.get("hidden") or p["type"] not in ("float", "int"):
                        continue
                    for which in ("max", "min"):
                        v = p.get(which)
                        if v is None:
                            continue
                        hx = fresh(viz, params)
                        o7, m7, dt7, dn7 = cmd(hx, {"op": "add", "type": typ, "values": {p["id"]: v}}, limit=40)
                        r = dict(viz=viz, variant=vname, type=typ, op="add_" + which, param=p["id"], value=v, outcome=o7, msg=m7, s=round(dt7, 2), dn=dn7)
                        if o7 == "ok":
                            fo, fmsg, fdt = run_frames(hx, 2, limit=40)
                            r.update(adv=fo, adv_msg=fmsg, adv_s=round(fdt, 2))
                        rec(**r)

if __name__ == "__main__":
    os.makedirs("/aui/out", exist_ok=True)
    main(sys.argv[1:] or list(VARIANTS))
