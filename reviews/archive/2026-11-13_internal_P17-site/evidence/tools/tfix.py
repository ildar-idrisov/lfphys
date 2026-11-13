import os, sys, tempfile, importlib.util, pathlib
os.environ["LFVIZ_EXTRA"] = "/lf/visualizations/tests/site_worlds"
sys.path.insert(0, "/lf/visualizations/server")
def site(n):
    spec = importlib.util.spec_from_file_location("lfsite_" + n, f"/lf/visualizations/site/{n}.py"); m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m); return m
rec, build, check = site("record"), site("build"), site("check")
d = pathlib.Path(tempfile.mkdtemp())
for v in ("u98_site_toy", "r98_site_probe"):
    rec.record_world(v, d / "rec")
build.build(d / "rec", d / "site", "/lfphys/")
r = check.check(d / "site", "/lfphys/", allow_missing=True)
print("FAILS", r.fails)
