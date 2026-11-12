"""The numbers of the processing's before/after runs, as a Markdown summary (SUMMARY.md).

    python3 summarize.py <outputs folder> > SUMMARY.md

Reads final/*/tour.json (tour_ab.mjs), final/probe_*/probe.json (probe_ab.mjs), final/perf_*/perf.json (perf_ab.mjs),
lookF/*/look.json (look_ab.mjs)."""
import argparse
import glob
import json
import os
import statistics


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src")
    a = ap.parse_args()
    out = ["# Before/after numbers of the processing (software GL, private server; compare ratios only)", ""]
    # tours
    rows = {}
    for p in sorted(glob.glob(os.path.join(a.src, "final", "*", "tour.json"))):
        d = load(p)
        st = d.get("steps", {}).get("default", {})
        rows.setdefault(d["tag"], {})[d["variant"]] = {
            "corners": st.get("cornersInside"), "canvas": st.get("canvas"), "ms": (d.get("perf") or {}).get("msPerRender"),
            "draws": (d.get("fps") or {}).get("drawsPerSec"), "raf": (d.get("fps") or {}).get("rafFps"),
            "tri": (d.get("perf") or {}).get("triangles"), "err": d.get("errors") or d.get("failed")}
    out += ["## Tours (`tour_ab.mjs`): box corners on screen as opened, a full frame, frames while turning", "",
            "| tour | corners before → after | ms per frame before → after | scene frames/s while turning before → after | triangles before → after | errors |",
            "|---|---|---|---|---|---|"]
    for t, v in rows.items():
        o, n = v.get("orig", {}), v.get("new", {})
        out.append(f"| {t} | {o.get('corners')} → {n.get('corners')} | {o.get('ms')} → {n.get('ms')} | {o.get('draws')} → {n.get('draws')} | {o.get('tri')} → {n.get('tri')} | {o.get('err') or ''} {n.get('err') or ''} |")
    # perf
    perf = {}
    for p in sorted(glob.glob(os.path.join(a.src, "final", "perf_*", "perf.json"))):
        d = load(p)
        tag = d["tag"].rsplit("_r", 1)[0]
        perf.setdefault(tag, {}).setdefault(d["variant"], []).append(d)
    out += ["", "## Performance (`perf_ab.mjs`, each world twice, orig and new interleaved)", "",
            "| world | full frame, ms (runs) before | after | scene frames/s while turning before | after | script share playing before | after |",
            "|---|---|---|---|---|---|---|"]
    for t, v in perf.items():
        def col(var, f):
            xs = [f(d) for d in v.get(var, []) if f(d) is not None]
            return " / ".join(str(x) for x in xs) if xs else "—"
        out.append(f"| {t} | {col('orig', lambda d: (d.get('perf') or {}).get('msPerRender'))} | {col('new', lambda d: (d.get('perf') or {}).get('msPerRender'))} | "
                   f"{col('orig', lambda d: (d.get('rotate') or {}).get('drawsPerSec'))} | {col('new', lambda d: (d.get('rotate') or {}).get('drawsPerSec'))} | "
                   f"{col('orig', lambda d: (d.get('play') or {}).get('scriptShare'))} | {col('new', lambda d: (d.get('play') or {}).get('scriptShare'))} |")
    # probes
    out += ["", "## Probes (`probe_ab.mjs`)", ""]
    for p in sorted(glob.glob(os.path.join(a.src, "final", "probe_*", "probe.json"))):
        d = load(p)
        d.pop("samples", None); d.pop("geo", None)
        out.append(f"- `{d['case']}` {d['variant']}: `{json.dumps(d, ensure_ascii=False)[:700]}`")
    # looks
    out += ["", "## Volume looks (`look_ab.mjs`): the start look (τ after, the old density before), corners as opened", ""]
    for p in sorted(glob.glob(os.path.join(a.src, "lookF", "*", "look.json"))):
        d = load(p)
        out.append(f"- {os.path.basename(os.path.dirname(os.path.dirname(p)))}/{d['tag']} {d['variant']}: look {d.get('look')}, corners {(d.get('diag') or {}).get('cornersInside')}, errors {d.get('errors')}")
    print("\n".join(out))


if __name__ == "__main__":
    main()
