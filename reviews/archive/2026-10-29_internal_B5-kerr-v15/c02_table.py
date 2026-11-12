# Review B5: tabulate c02's output (worst relative r_n error by distance d from the critical curve and order n).
# Run on the host: python3 c02_table.py out/c02_hard_rays.txt
import re
import sys

txt = open(sys.argv[1]).read().split("\n")
cur = None
worst = {}
for l in txt:
    m = re.match(r"\[graze d=([^ ]+) ang=([^\]]+)\]: chi=([^ ]+) th=([^ ]+)", l)
    if m:
        cur = (m.group(3), m.group(4), m.group(1))
        continue
    if l.startswith("["):
        cur = None
    m = re.search(r"n=(\d): r_n=([^ ]+) +tau_n err ([^ ]+) rel;  r_n err ([^ ]+) M \(([^ ]+) rel\)", l)
    if m and cur:
        k = (cur[2], int(m.group(1)))
        worst[k] = max(worst.get(k, 0), float(m.group(5)))
ds = sorted(set(k[0] for k in worst), key=lambda s: (s[0] == "-", abs(float(s))))
print("worst relative r_n error over chi / theta_o / direction, by d (rows) and n (columns)")
for d in ds:
    print(f"{d:>7} " + " ".join(f"n{n}:{worst.get((d, n), float('nan')):.1e}" for n in range(9)))
