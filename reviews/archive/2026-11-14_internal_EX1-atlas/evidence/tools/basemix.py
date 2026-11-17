import sys, glob, json
sys.path.insert(0, "/s/work"); from live2 import post, show  # noqa
sys.path.insert(0, "/lf/visualizations/server")
from lfviz import headless
r = show("live h=1.5 (server runs the edited code)", post("/api/atlas/s03_projectile/explore/point", {"values": {"h_m": 1.5}}))
msgs = headless.read_stream(r[2])
delta = msgs[0]
print("delta's keys:", sorted(delta[0]))
# the player's base on a server: the local atlas's base (/api/recordings -> index -> manifest -> base)
ix = json.load(open("/recs/s03_projectile/index.json"))
e = next(a for a in ix["atlases"] if a["id"] == "explore")
man = json.load(open("/recs/s03_projectile/" + e["file"]))
local_base = headless.read_stream(open("/recs/s03_projectile/atlas/explore/" + man["base"]["file"], "rb").read())[0]
server_base = headless.read_stream(open(glob.glob("/runs/atlas-live/s03_projectile/explore/base-*.lfpt.gz")[0], "rb").read())[0]
mh, _ = headless.merge_header(local_base, delta)
sh, _ = headless.merge_header(server_base, delta)
print("header the player shows (local atlas base): g =", mh["g"], " weight =", mh["weight"])
print("header the server computed with (its base): g =", sh["g"], " weight =", sh["weight"])
ev = [m for m, _b in msgs if m.get("type") == "event" and m.get("kind") in ("apex", "landing")]
print("events of the drawn flight:", [(m.get("kind"), round(m.get("t"), 6)) for m in ev][:3])
print("local atlas key in index:", e["key"], "| X-LF-Key:", r[1].get("X-LF-Key"))
