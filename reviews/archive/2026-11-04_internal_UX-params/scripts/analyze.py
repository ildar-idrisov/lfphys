"""Classify audit results (res/*.jsonl) into (a)-(f) and group distinct failures.

    python3 analyze.py [res_dir] [--world W] [--detail CLS] [--texts]
"""
import argparse
import glob
import json
import os
import re
from collections import Counter, defaultdict

CYR = re.compile(r"[А-Яа-яЁё]")
LIB_EXC = {"ZeroDivisionError", "IndexError", "KeyError", "TypeError", "AttributeError", "LinAlgError",
           "FloatingPointError", "OverflowError", "MemoryError", "AssertionError", "UnboundLocalError", "NameError",
           "RecursionError", "NotImplementedError", "StopIteration", "LinAlgWarning", "IntegrationWarning",
           "RuntimeWarning", "UFuncTypeError", "AxisError"}
RAW = re.compile(r"Traceback|\bnan\b|\binf\b|array\(|dtype|<class|object has no attribute|unsupported operand|"
                 r"out of bounds|division by zero|math domain error|index \d+|'NoneType'|could not convert|"
                 r"must be|expected|got an unexpected", re.I)
ORDER = "cdefhb"
SHOW_CHECKS_KINDS = ("default", "preset")


def norm(text):
    t = re.sub(r"[-+]?\d[\d.,]*(e[-+]?\d+)?", "#", text or "")
    t = re.sub(r"\s+", " ", t)
    return t[:220]


# manual review of refusal texts that read as Russian but are unclear, wrong or not reachable from the player
OVERRIDES = [
    # (regex on the text, class): "f" unclear / wrong advice / internal ids; "a" not reachable from the player
    (r"элемент '[a-z_]+' не подходит", "f"),                       # v02: internal ids of the elements
    (r"предпросмотр среза в этом мире не нужен", "a"),             # v13/v14: the player never sends a preview there
    (r"нечего менять на ходу|нельзя менять на ходу", "a"),         # the driver set a hidden control's parent
    (r"увеличьте dt|уменьшите dt", "f"),                           # p04: dt is not a parameter of the world
    (r"unknown parameter 'scene'", "a"),                           # v12: the driver sent a world parameter as live
]
OSC_WRONG_ADVICE = re.compile(r"слишком дорог для живого мира.*уменьшите ширину пакета, энергию или высоту потенциала")


def classify_refusal(e, values=None):
    """b: clean (Russian, raised on purpose by the project), f: raw / English, c: an internal exception."""
    text = e.get("text") or ""
    for rx, cls in OVERRIDES:
        if re.search(rx, text):
            return cls
    if OSC_WRONG_ADVICE.search(text) and (values or {}).get("scenario") == "oscillator":
        return "f"  # v03: the advice names parameters the oscillator scenario does not have
    body = re.sub(r"^(Изменение не применено|Действие \S+|Сцена|Просмотр|Новый мир не создан|Мир не создан|"
                  r"параметры): ", "", text)
    et = e.get("exc_type")
    if "Traceback" in text:
        return "c"
    if et in LIB_EXC:
        return "c"
    if et and not e.get("inner_in_proj", True) and et not in ("ValueError",):
        return "c"
    if et == "ValueError" and e.get("inner") and not e.get("inner_in_proj"):
        # raised inside numpy / scipy / lfphys? (lfphys is under /lf too: inner_in_proj then)
        return "c" if not CYR.search(body) else "f"
    if not CYR.search(body):
        return "f"
    if RAW.search(body):
        return "f"
    return "b"


def _set_values(r):
    out = {}
    for op in r.get("ops") or []:
        if op and op[0] == "set" and isinstance(op[1], dict):
            out.update(op[1])
    return out


def combo_classes(r):
    cls = set()
    notes = []
    for e in r.get("events", []):
        k = e["cls"]
        if k in ("crash",):
            cls.add("c")
        elif k == "hang":
            cls.add("d")
        elif k in ("refuse_start", "refuse_build", "refuse_cmd"):
            c = classify_refusal(e, {**(r.get("values") or {}), **_set_values(r)})
            if k == "refuse_build" and c == "b":
                c = "h"  # a clean reason the player never shows (the first world was not built: finding P1)
            e["ux"] = c
            cls.add(c)
        elif k == "ckpt_fail":
            cls.add("c")
            e["ux"] = "c"
        elif k == "audit_bug":
            cls.add("X")
    refusal_texts = {e.get("text") for e in r.get("events", [])}
    for er in r.get("errors") or []:
        if er["text"] in refusal_texts:
            continue
        if "Traceback" in er["text"]:
            if not any(e["cls"] == "crash" for e in r.get("events", [])):
                cls.add("c")
                r.setdefault("events", []).append({"cls": "crash", "op": "t=0 advance / emitted", "text": er["text"],
                                                   "ux": "c"})
        else:
            u = "f" if not CYR.search(er["text"]) or RAW.search(er["text"]) else "b"
            cls.add(u)
            r.setdefault("events", []).append({"cls": "world_error", "op": "?", "text": er["text"], "ux": u})
    for s in r.get("slow") or []:
        cls.add("d")
    st = r.get("stats") or {}
    if r.get("failed_checks"):
        if r.get("kind") in SHOW_CHECKS_KINDS:
            cls.add("e")
        else:
            notes.append("check fails")
    if r.get("nan_checks"):
        cls.add("e")
    if st.get("empty"):
        cls.add("e")
    nf = [x for x in st.get("nonfinite_meta") or [] if x["type"] in ("frame", "check", "header", "event", "live")]
    if nf:
        cls.add("e")
    prog = r.get("progress") or []
    if prog and all(p["dt"] == 0 for p in prog) and any(p["want"] > 0 for p in prog):
        cls.add("d")
        notes.append("world time did not advance")
    prim = next((c for c in ORDER if c in cls), "a")
    if "X" in cls and prim == "a":
        prim = "X"
    return prim, cls, notes


def load(res_dir, world=None):
    out = []
    for f in sorted(glob.glob(f"{res_dir}/*.jsonl")):
        w = os.path.basename(f)[:-6]
        if world and w != world:
            continue
        for line in open(f):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("res", nargs="?", default=os.path.join(os.path.dirname(__file__), "res"))
    ap.add_argument("--world")
    ap.add_argument("--detail", default="")
    ap.add_argument("--texts", action="store_true", help="distinct refusal texts per world with their class")
    ap.add_argument("--checks", action="store_true")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    rs = load(a.res, a.world)
    table = defaultdict(Counter)
    sig = defaultdict(lambda: {"n": 0, "examples": [], "worlds": Counter(), "kinds": Counter()})
    for r in rs:
        prim, cls, notes = combo_classes(r)
        r["_prim"], r["_cls"], r["_notes"] = prim, sorted(cls), notes
        table[r["world"]][prim] += 1
        table[r["world"]]["n"] += 1
        for e in r.get("events", []):
            u = e.get("ux") or {"crash": "c", "hang": "d"}.get(e["cls"], "?")
            if u in ("c", "d", "f") or (a.texts and u in ("b", "h")):
                key = (u, e.get("exc_type"), e.get("proj") or e.get("inner"), norm(e["text"]))
                s = sig[key]
                s["n"] += 1
                s["worlds"][r["world"]] += 1
                s["kinds"][r["kind"]] += 1
                if len(s["examples"]) < 3:
                    s["examples"].append({"world": r["world"], "cid": r["cid"], "desc": r["desc"], "op": e.get("op"),
                                          "text": e["text"][:600], "inner": e.get("inner")})
        for s_ in r.get("slow") or []:
            key = ("d", "slow", s_["op"].split(" ")[0].split(":")[0] if s_ else "", r["world"])
            s = sig[key]
            s["n"] += 1
            s["worlds"][r["world"]] += 1
            s["kinds"][r["kind"]] += 1
            if len(s["examples"]) < 3:
                s["examples"].append({"world": r["world"], "cid": r["cid"], "desc": r["desc"], "op": s_["op"],
                                      "text": f"{s_['s']} s{' killed' if s_.get('killed') else ''}"})
    print(f"{'world':<22} {'n':>5} " + " ".join(f"{c:>5}" for c in "abcdefhX"))
    tot = Counter()
    for w in sorted(table):
        t = table[w]
        tot.update(t)
        print(f"{w:<22} {t['n']:>5} " + " ".join(f"{t[c]:>5}" for c in "abcdefhX"))
    print(f"{'TOTAL':<22} {tot['n']:>5} " + " ".join(f"{tot[c]:>5}" for c in "abcdefhX"))
    print()
    for key, s in sorted(sig.items(), key=lambda kv: (kv[0][0], -kv[1]["n"])):
        if a.detail and key[0] not in a.detail:
            continue
        print(f"[{key[0]}] n={s['n']} {key[1]} @ {key[2]} worlds={dict(s['worlds'])} kinds={dict(s['kinds'])}")
        print(f"     {key[3]}")
        for ex in s["examples"][:2]:
            print(f"       e.g. {ex['world']} #{ex['cid']} {ex['desc'][:90]} | {ex['op']} | {ex['text'][:300]!r}")
    if a.checks:
        print("\n== failed checks (by world, kind)")
        fc = defaultdict(lambda: {"n": 0, "ex": []})
        for r in rs:
            for c in r.get("failed_checks") or []:
                k = (r["world"], c["id"], r["kind"] in SHOW_CHECKS_KINDS)
                fc[k]["n"] += 1
                if len(fc[k]["ex"]) < 2:
                    fc[k]["ex"].append((r["cid"], r["desc"][:70], c.get("value"), c.get("ref"), c.get("rel"),
                                        c.get("tol"), c.get("ok")))
        for k, v in sorted(fc.items()):
            print(f"  {k[0]} {k[1]} default/preset={k[2]} n={v['n']} {v['ex']}")
    if a.json:
        json.dump([{k: r.get(k) for k in ("world", "cid", "kind", "desc", "_prim", "_cls", "_notes")} for r in rs],
                  open(a.json, "w"), ensure_ascii=False, indent=0)


if __name__ == "__main__":
    main()
