"""Random parameter sets within each world's schema (min/max/options; log-uniform for log params), the world built and
stepped; every exception is put through lfviz.errors.owner_text as the runner does, and the owner's text is searched
for plain (untranslated) strings: those reach a Russian viewer in English. Usage: c14 <seed> <n> viz_id..."""
import os, queue, random, re, signal, sys, math, json
sys.path[:0] = ["/w/visualizations", "/w/visualizations/server", "/w/lfphys"]
os.environ.setdefault("LFVIZ_EXTRA", "/w/visualizations/tests/playgrounds:/w/visualizations/tests/instruments_worlds")
from lfviz import i18n, registry
from lfviz.errors import owner_text
from lfviz.i18n import is_t, render
from lfviz.sim import Runner
own = i18n._merge("ru")[0]
LAT = re.compile(r"[A-Za-z]{4,}")

def plain(x):
    """plain strings with English words inside an owner's text (not catalogue msgids)"""
    if is_t(x):
        out = []
        for v in (x.get("a") or {}).values():
            out += plain(v)
        return out
    if isinstance(x, str) and LAT.search(x) and x not in own:
        return [x]
    if isinstance(x, (list, tuple)):
        return [s for v in x for s in plain(v)]
    return []

class TO(Exception):
    pass
signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TO()))
seed, n = int(sys.argv[1]), int(sys.argv[2])
rnd = random.Random(seed)
found = {}
for vid in sys.argv[3:]:
    viz = registry.load(vid)
    sch = viz["schema"]
    presets = list(sch.presets) or [None]
    for i in range(n):
        vals = {}
        for p in sch.params:
            if p.hidden or rnd.random() < 0.5:
                continue
            if p.type == "select" and p.options:
                vals[p.id] = rnd.choice(p.options)[0]
            elif p.type == "bool":
                vals[p.id] = rnd.random() < 0.5
            elif p.type in ("float", "int") and p.min is not None and p.max is not None:
                lo, hi = float(p.min), float(p.max)
                r = rnd.random()
                v = lo if r < 0.2 else hi if r < 0.4 else (math.exp(rnd.uniform(math.log(lo), math.log(hi))) if p.log and lo > 0 else rnd.uniform(lo, hi))
                vals[p.id] = int(round(v)) if p.type == "int" else v
        preset = rnd.choice(presets)
        params, errs = sch.resolve(preset, vals)
        if errs:
            continue
        msgs = []
        signal.alarm(25)
        ctx = "build"
        try:
            sim = viz["simulation"](params, 1, lambda m, b=None: msgs.append(m))
            run = Runner(sim, lambda m, b=None: msgs.append(m), queue.Queue())
            run._start_world()
            ctx = "step"
            for _ in range(3):
                run.handle({"cmd": "step", "args": {}})
        except TO:
            pass
        except MemoryError:
            pass
        except Exception as e:
            text, detail = owner_text(e, ctx)
            pl = plain(text)
            if pl:
                key = (vid, type(e).__name__, pl[0][:80])
                if key not in found:
                    found[key] = {"preset": preset, "values": vals, "owner_en": render(text), "owner_ru": render(text, i18n.catalogue("ru"), "ru")}
                    print(json.dumps({"viz": vid, "exc": type(e).__name__, **found[key]}, ensure_ascii=False, default=str), flush=True)
        finally:
            signal.alarm(0)
        for m in msgs:
            if m.get("type") == "error":
                pl = plain(m.get("text"))
                if pl:
                    key = (vid, "error-msg", pl[0][:80])
                    if key not in found:
                        found[key] = 1
                        print(json.dumps({"viz": vid, "error_message_ru": render(m.get("text"), i18n.catalogue("ru"), "ru"), "preset": preset, "values": vals}, ensure_ascii=False, default=str), flush=True)
print("distinct plain-English owner texts:", len(found))
