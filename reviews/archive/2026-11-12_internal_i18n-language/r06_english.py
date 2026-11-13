"""English msgid consistency: -ise/-ize pairs, disc/disk, 3-D/3D, space-time/spacetime, licence/license, and
the capitalisation of short labels. Run: python3 -I r06_english.py > r06_english.out"""
import os, re, sys
from collections import Counter, defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r00_load import load  # noqa: E402
E = load()
words = defaultdict(Counter)
for x in E:
    for w in re.findall(r"[A-Za-z][A-Za-z-]+", x["msgid"]):
        words[w.lower()][x["cat"]] += 1
print("1. -ise / -ize stems used both ways (sum over catalogues)")
for w in sorted(words):
    m = re.match(r"(.*)is(e|es|ed|ing|ation|ations|er|ers|able)$", w)
    if m:
        z = m.group(1) + "iz" + m.group(2)
        if z in words:
            print(f"  {w} {dict(words[w])}  |  {z} {dict(words[z])}")
print("\n2. variant pairs")
PAIRS = [("disc", "disk"), ("discs", "disks"), ("3-d", "3d"), ("2-d", "2d"), ("space-time", "spacetime"),
         ("licence", "license"), ("set-up", "setup"), ("analyse", "analyze"), ("modelled", "modeled"),
         ("centre", "center"), ("colour", "color"), ("colours", "colors"), ("grey", "gray"), ("per cent", "percent"),
         ("towards", "toward"), ("judgement", "judgment"), ("travelling", "traveling"), ("cancelled", "canceled"),
         ("labelled", "labeled"), ("metre", "meter"), ("metres", "meters"), ("behaviour", "behavior"),
         ("neighbouring", "neighboring"), ("normalised", "normalized"), ("polarisation", "polarization"),
         ("recognise", "recognize"), ("re-run", "rerun"), ("checkbox", "check box"), ("e.g.", "e. g."),
         ("non-relativistic", "nonrelativistic"), ("well-known", "well known"), ("wave function", "wavefunction"),
         ("wave packet", "wavepacket"), ("black hole", "black-hole"), ("time step", "timestep"), ("cross-section", "cross section"),
         ("post-newtonian", "postnewtonian"), ("x-ray", "x ray"), ("fine-structure", "fine structure"), ("data set", "dataset")]
for a, b in PAIRS:
    ca = Counter(); cb = Counter()
    for x in E:
        m = x["msgid"].lower()
        ca[x["cat"]] += len(re.findall(r"(?<![\w-])" + re.escape(a) + r"(?![\w-])", m))
        cb[x["cat"]] += len(re.findall(r"(?<![\w-])" + re.escape(b) + r"(?![\w-])", m))
    ta, tb = sum(ca.values()), sum(cb.values())
    if ta and tb:
        print(f"  {a}: {ta} {dict((k, v) for k, v in ca.items() if v)}\n  {b}: {tb} {dict((k, v) for k, v in cb.items() if v)}")
    elif ta or tb:
        print(f"  only {a if ta else b}: {ta or tb}")
print("\n3. short labels (1-5 words, no sentence punctuation): lowercase-initial vs uppercase-initial per catalogue")
for cat in sorted({x['cat'] for x in E}):
    lo = []; up = 0
    for x in E:
        if x["cat"] != cat: continue
        m = x["msgid"]
        if len(m.split()) > 5 or re.search(r"[.:;!?]$", m) or m.startswith("{"):
            continue
        c = re.search(r"[A-Za-z]", m)
        if not c or c.start() > 0: continue
        if m[0].islower(): lo.append(m)
        else: up += 1
    print(f"  {cat}: upper {up}, lower {len(lo)}: " + " | ".join(lo[:25]))
print("\n4. Title Case labels (2-6 words, every word capitalised) — the rest are sentence case")
for x in E:
    m = x["msgid"]
    ws = m.split()
    if 2 <= len(ws) <= 6 and all(w[0].isupper() for w in ws if w[0].isalpha() and w.lower() not in ("of", "the", "and", "a", "in", "on", "to", "for")) and sum(1 for w in ws if w[0].isalpha()) >= 2:
        if not re.search(r"[A-Z]{2}|[A-Z][a-z]+[–-][A-Z]", m) and not any(n in m for n in ("Bohm", "Kerr", "Bell", "Newton", "Schrö", "Kepler", "Doppler", "Mie", "Debye", "Thomas", "Wigner", "Lorentz", "Einstein", "Gauss", "Laguerre", "Bragg", "Snell", "Brewster", "Fresnel", "Planck", "Rayleigh", "Maxwell", "Boltzmann", "Lennard", "Poiseuille", "Kármán", "Couette", "Reynolds", "Mach", "Bohr", "Rydberg", "Coulomb", "Hermite", "Yoshida", "Verlet", "Born", "Kirchhoff", "Fraunhofer", "Fermi", "Dirac", "Pauli", "Heisenberg", "Hubble", "Friedmann", "Copenhagen", "Everett", "Schwarzschild", "Ghia", "DFG", "Gaussian", "Hilbert", "Andromeda", "Earth", "Sun", "Moon", "Mercury", "Jupiter", "Saturn", "Mars", "Venus")):
            print(f"  [{x['cat']}] {m}")
