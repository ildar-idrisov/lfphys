import sys
sys.path.insert(0, "/lf/visualizations/server"); sys.path.insert(0, "/lf/visualizations")
from lfviz import registry
registry.ensure_path()
for w in ("v01_light_travel", "v02_double_slit", "v06_qcd", "v07_bell_test", "v08_wave_3d", "v13_hydrogen_3d", "v14_quarkonium_3d", "v15_kerr_shadow", "v16_optical_vortices", "v17_mie_scattering"):
    viz = registry.load(w)
    print("==", w)
    for p in viz["schema"].params:
        if p.type in ("float", "int") and not p.hidden:
            print(f"   {p.id:14s} [{p.type}] {p.label!r} unit={p.unit!r}")
