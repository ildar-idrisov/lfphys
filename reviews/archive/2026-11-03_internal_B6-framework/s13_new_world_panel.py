# Review B6-framework, script s13: the player's panel «Новый мир» (player.js renderWorldPanel) sends, without a preset,
# params = {...header.params, ...live, ...form values of every non-live parameter}; the hidden "scene" is a non-live
# parameter, so the current world's INITIAL scene goes along. Here the same body is resolved and built as the worker
# does (make_world) for p01 when the owner switches the laws from Newton to the post-Newtonian binary.
# Usage: see s01; python3 /out/s13_new_world_panel.py
from lfviz import registry

viz = registry.load("p01_gravity")
header_params, errs = viz["schema"].resolve("sun_earth", {})
body = {**header_params, "laws": "pn"}  # what the panel sends after the laws' select is changed
p, errs = viz["schema"].resolve(None, body)
print("schema errors:", errs, "| scene objects carried over:", [o["type"] for o in p["scene"]["objects"]])
try:
    viz["simulation"](p, 1, lambda m, b=None: None)
    print("new world built")
except Exception as e:  # noqa: BLE001
    print("new world refused:", type(e).__name__, e)
