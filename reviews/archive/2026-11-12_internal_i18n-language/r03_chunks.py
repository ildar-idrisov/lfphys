"""Split all Russian catalogue entries into reading chunks for the language read-through.

Run: python3 -I r03_chunks.py OUTDIR   (writes chunk_01.txt ... with numbered entries: [cat#i] msgid / -> ru)
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load  # noqa: E402

GROUPS = [
    ("01_engine_a", ["engine"], 0),
    ("02_engine_b", ["engine"], 1),
    ("03_framework", ["framework"], None),
    ("04_p01_p02", ["p01_gravity", "p02_quantum"], None),
    ("05_p03_p04", ["p03_molecules", "p04_fluids"], None),
    ("06_v01_v03", ["v01_light_travel", "v02_double_slit", "v03_quantum_1d"], None),
    ("07_v04_v07", ["v04_orbits", "v05_optics_bench", "v06_qcd", "v07_bell_test"], None),
    ("08_v08_v12", ["v08_wave_3d", "v09_thomas_3d", "v10_fast_observer", "v11_double_slit_2d", "v12_arrival_times_2d"], None),
    ("09_v13_v17", ["v13_hydrogen_3d", "v14_quarkonium_3d", "v15_kerr_shadow", "v16_optical_vortices", "v17_mie_scattering"], None),
]

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
E = load()
for name, cats, half in GROUPS:
    xs = [x for x in E if x["cat"] in cats]
    if half is not None:
        m = len(xs) // 2
        xs = xs[:m] if half == 0 else xs[m:]
    with open(os.path.join(out, f"chunk_{name}.txt"), "w", encoding="utf-8") as f:
        for i, x in enumerate(xs):
            ru = x["ru"] if not x["forms"] else json.dumps(x["forms"], ensure_ascii=False)
            f.write(f"[{x['cat']}] {x['msgid']}\n    -> {ru}\n")
    print(name, len(xs))
