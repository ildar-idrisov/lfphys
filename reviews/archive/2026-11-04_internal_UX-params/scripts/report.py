"""Markdown fragments for the review from res/*.jsonl: the per-world table and every distinct outcome with an example.

    python3 report.py res out_dir
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(__file__))
import analyze  # noqa: E402

res_dir, out_dir = sys.argv[1], sys.argv[2]
rs = analyze.load(res_dir)
table = defaultdict(Counter)
kinds = defaultdict(Counter)
sig = defaultdict(lambda: {"n": 0, "ex": [], "kinds": Counter()})
fchk = defaultdict(lambda: {"n": 0, "ex": []})
rows = []
for r in rs:
    prim, cls, notes = analyze.combo_classes(r)
    w = r["world"]
    table[w][prim] += 1
    table[w]["n"] += 1
    kinds[w][r["kind"]] += 1
    rows.append({"world": w, "cid": r["cid"], "kind": r["kind"], "desc": r["desc"], "preset": r.get("preset"),
                 "values": r.get("values"), "outcome": prim, "classes": sorted(cls), "notes": notes,
                 "events": [{k: e.get(k) for k in ("cls", "ux", "op", "exc_type", "proj", "inner", "text")}
                            for e in r.get("events", [])][:6],
                 "slow": r.get("slow"), "failed_checks": [c["id"] for c in r.get("failed_checks") or []],
                 "build_s": r.get("build_s"), "frame_max_s": r.get("frame_max_s"), "wall_s": r.get("wall_s")})
    for e in r.get("events", []):
        u = e.get("ux") or {"crash": "c", "hang": "d"}.get(e["cls"], "?")
        if u == "a":
            continue
        key = (w, u, e.get("exc_type") or "", e.get("proj") or e.get("inner") or "", analyze.norm(e["text"])[:160])
        s = sig[key]
        s["n"] += 1
        s["kinds"][r["kind"]] += 1
        if len(s["ex"]) < 1:
            s["ex"].append(f"#{r['cid']} {r['desc'][:90]} · {e.get('op')}")
    for s_ in r.get("slow") or []:
        key = (w, "d", "slow", s_["op"].split(" ")[0].split(":")[-1], "")
        s = sig[key]
        s["n"] += 1
        s["kinds"][r["kind"]] += 1
        if len(s["ex"]) < 1:
            s["ex"].append(f"#{r['cid']} {r['desc'][:90]} · {s_['op']} {s_['s']} s{' (killed)' if s_.get('killed') else ''}")
    for c in r.get("failed_checks") or []:
        k = (w, c["id"], r["kind"] in analyze.SHOW_CHECKS_KINDS)
        fchk[k]["n"] += 1
        if len(fchk[k]["ex"]) < 1:
            fchk[k]["ex"].append(f"#{r['cid']} {r['desc'][:80]}: {c.get('label', '')[:70]} = {c.get('value')!r} "
                                 f"(эталон {c.get('ref')!r})")

os.makedirs(out_dir, exist_ok=True)
L = ["| world | combinations | (a) ok | (b) clean refusal | (c) crash | (d) hang / slow | (e) wrong output | "
     "(f) raw / unclear refusal | (h) clean refusal never shown (P1) |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
tot = Counter()
for w in sorted(table):
    t = table[w]
    tot.update(t)
    L.append(f"| {w} | {t['n']} | {t['a']} | {t['b']} | {t['c']} | {t['d']} | {t['e']} | {t['f']} | {t['h']} |")
L.append(f"| **total** | **{tot['n']}** | **{tot['a']}** | **{tot['b']}** | **{tot['c']}** | **{tot['d']}** | "
         f"**{tot['e']}** | **{tot['f']}** | **{tot['h']}** |")
open(f"{out_dir}/summary_table.md", "w").write("\n".join(L) + "\n")
K = ["| world | " + " | ".join(["default", "single", "live", "pair", "pair_live", "all", "preset", "preset_live",
                                "preset_action", "preset_view", "view_extreme", "new_world", "palette", "palette_param",
                                "palette_edit", "preset_edit", "preset_remove", "preset_add", "random"]) + " |"]
K.append("|---|" + "---:|" * 19)
for w in sorted(kinds):
    k = kinds[w]
    K.append(f"| {w} | " + " | ".join(str(k.get(x, 0)) for x in ["default", "single", "live", "pair", "pair_live", "all",
                                                                  "preset", "preset_live", "preset_action",
                                                                  "preset_view", "view_extreme", "new_world", "palette",
                                                                  "palette_param", "palette_edit", "preset_edit",
                                                                  "preset_remove", "preset_add", "random"]) + " |")
open(f"{out_dir}/kinds_table.md", "w").write("\n".join(K) + "\n")
S = []
cur = None
for key, s in sorted(sig.items(), key=lambda kv: (kv[0][0], "cdefhb".find(kv[0][1]), -kv[1]["n"])):
    w, u, et, loc, text = key
    if w != cur:
        S.append(f"\n### {w}\n")
        cur = w
    S.append(f"- **({u})** ×{s['n']} {('`' + et + '`') if et else ''} {('`' + loc + '`') if loc else ''} "
             f"{('«' + text + '»') if text else ''} — e.g. {s['ex'][0]} ({dict(s['kinds'])})")
open(f"{out_dir}/signatures.md", "w").write("\n".join(S) + "\n")
C = []
cur = None
for (w, cid, dp), v in sorted(fchk.items()):
    if w != cur:
        C.append(f"\n### {w}\n")
        cur = w
    C.append(f"- `{cid}` {'**on a default or preset world**' if dp else ''} ×{v['n']}: {v['ex'][0]}")
open(f"{out_dir}/failed_checks.md", "w").write("\n".join(C) + "\n")
with open(f"{out_dir}/combinations.jsonl", "w") as f:
    for row in rows:
        f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
print(open(f"{out_dir}/summary_table.md").read())
