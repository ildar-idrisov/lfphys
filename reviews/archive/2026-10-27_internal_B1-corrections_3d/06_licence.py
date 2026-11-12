# Review of the B1 corrections (reviewer's script). The vendored three.js r185.1 against the published npm package:
# the tarball from the npm registry (no contact or identifying parameters), its sha512 against the registry's
# "integrity", the five vendored files byte for byte, the licence, the publication date recorded in vendor/README.md,
# the NOTICE lines, and the absence of other third-party files under player/. Downloads go to a temporary folder.
import argparse
import base64
import hashlib
import io
import json
import tarfile
import urllib.request
from pathlib import Path

argparse.ArgumentParser(description=__doc__).parse_args()
ENGINE = Path("/lf")
VEND = ENGINE / "visualizations/player/vendor/three-0.185.1"
lines = []


def out(s):
    print(s)
    lines.append(s)


meta = json.load(urllib.request.urlopen("https://registry.npmjs.org/three", timeout=60))
ver = meta["versions"]["0.185.1"]
out(f"registry: three 0.185.1 published {meta['time']['0.185.1']}, license {ver.get('license')}")
tgz = urllib.request.urlopen(ver["dist"]["tarball"], timeout=120).read()
integ = "sha512-" + base64.b64encode(hashlib.sha512(tgz).digest()).decode()
out(f"tarball {len(tgz)} bytes; sha512 equals the registry's integrity: {integ == ver['dist']['integrity']}")
files = {"three.module.min.js": "package/build/three.module.min.js", "three.core.min.js": "package/build/three.core.min.js",
         "OrbitControls.js": "package/examples/jsm/controls/OrbitControls.js",
         "TransformControls.js": "package/examples/jsm/controls/TransformControls.js", "LICENSE": "package/LICENSE"}
with tarfile.open(fileobj=io.BytesIO(tgz)) as tf:
    for name, member in files.items():
        npm = tf.extractfile(member).read()
        ours = (VEND / name).read_bytes()
        out(f"  {name:<22} identical to the package: {npm == ours}  sha256 {hashlib.sha256(ours).hexdigest()}")
extra = sorted(p.name for p in VEND.iterdir() if p.name not in files)
out(f"files in the vendor folder not from the list: {extra}")
out(f"LICENSE first line: {(VEND / 'LICENSE').read_text().splitlines()[0]}")
readme = (ENGINE / "visualizations/player/vendor/README.md").read_text()
out(f"vendor/README.md records 'published 2026-07-01': {'published 2026-07-01' in readme}")
for notice in ("NOTICE", "visualizations/NOTICE"):
    out(f"{notice} names three.js r185.1 MIT: {'three.js r185.1' in (ENGINE / notice).read_text()}")
# third-party markers in the player's own code (not vendor/)
own = [p for p in (ENGINE / "visualizations/player").rglob("*") if p.is_file() and "vendor" not in p.parts]
marks = [str(p.relative_to(ENGINE)) for p in own if p.suffix in (".js", ".css", ".html")
         and any(m in p.read_text(errors="ignore") for m in ("@license", "Copyright (c)", "MIT License", "three.js authors"))]
out(f"third-party licence markers in the player's own files: {marks}")
Path("out/06_licence.txt").write_text("\n".join(lines) + "\n")
