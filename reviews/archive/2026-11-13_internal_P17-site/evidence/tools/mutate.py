import json, shutil, subprocess, sys, hashlib, pathlib
src = pathlib.Path("/site"); 
def fresh(name):
    d = pathlib.Path("/tmp") / name
    shutil.copytree(src, d); return d
def reman(d):
    m = json.loads((d / "site-manifest.json").read_text())
    files = {}
    for f in sorted(d.rglob("*")):
        if f.is_file() and f.name != "site-manifest.json":
            files[f.relative_to(d).as_posix()] = {"bytes": f.stat().st_size, "sha256": hashlib.sha256(f.read_bytes()).hexdigest()}
    m["files"] = files; (d / "site-manifest.json").write_text(json.dumps(m))
def run(d, label):
    r = subprocess.run([sys.executable, "site/check.py", str(d), "--base", "/lfphys/"], capture_output=True, text=True)
    fails = [l for l in r.stdout.splitlines() if l.startswith("FAIL")]
    print(f"{label}: exit {r.returncode}; {fails[:2]}")
d = fresh("a"); (d / "static/js/start.js").write_text((d / "static/js/start.js").read_text() + '\nfetch("/api/viz");\nlocation.href = "/run?id=x";\n'); reman(d); run(d, "absolute /api and /run in static/js/start.js (manifest rebuilt)")
d = fresh("b"); shutil.rmtree(d / "viz/u34_orbits"); reman(d); run(d, "viz/u34_orbits/ (the view module) missing, manifest rebuilt")
d = fresh("c"); (d / "images/u34_orbits.jpg").unlink(); reman(d); run(d, "images/u34_orbits.jpg missing while api/viz.json names its picture (manifest rebuilt)")
d = fresh("e"); (d / "static/vendor/three-0.185.1/OrbitControls.js").unlink(); reman(d); run(d, "static/vendor/.../OrbitControls.js missing (manifest rebuilt)")
d = fresh("f"); idx = json.loads((d / "recordings/u34_orbits/index.json").read_text()); idx["recordings"].append(dict(idx["recordings"][0], id="extra")); (d / "recordings/u34_orbits/index.json").write_text(json.dumps(idx)); reman(d); run(d, "an extra index entry the registry does not know")
d = fresh("g"); (d / "static/locales/ru.json").unlink(); reman(d); run(d, "static/locales/ru.json missing")
