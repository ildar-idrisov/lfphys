# all distinct scan findings across logs (module names and versions excluded), with the first place seen
import json, sys, re
seen = {}
for f in sys.argv[1:]:
    for l in open(f):
        o = json.loads(l)
        if 'where' not in o: continue
        for b in o['bad']:
            s = b['s']
            if re.fullmatch(r'lfphys(\.\w+)+|[\w.]+\.(arb|geodesics|transfer|raytrace)', s) or re.search(r'\(версия \d|· версия \d', s): continue
            key = (tuple(b['why']), s[:150])
            if key not in seen: seen[key] = (o['where'], b['at'][-60:], b['k'])
for (why, s), (w, at, k) in seen.items():
    print(why, k, '|', w, '|', repr(s), '|', at)
