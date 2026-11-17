import json, sys, time, threading
sys.path.insert(0, "/s/work"); from live2 import post, show  # noqa
U = "/api/atlas/u32_double_slit/explore/point"
res = {}
def one(i):
    res[i] = post(U, {"values": {"lam_nm": 410.0 + i}})
t0 = time.time()
th = [threading.Thread(target=one, args=(i,)) for i in range(8)]
for t in th: t.start(); time.sleep(0.05)
for t in th: t.join()
for i in range(8):
    st, h, body, dt = res[i]
    gz = body[:2] == bytes([31, 139])
    print(f"req {i}: {st} src={h.get('X-LF-Source')} after {dt:.1f}s", "" if gz else body[:120].decode())
print(f"total {time.time()-t0:.1f}s")
