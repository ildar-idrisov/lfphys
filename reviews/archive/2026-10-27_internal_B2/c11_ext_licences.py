# B2 review, check 11: the installed licence metadata of the comparison-only packages in light-funnel-ext (P13),
# to compare with lfphys/sources/dependencies.md section 10.
# Run: docker run --rm -v "$PWD":/lf -w /lf light-funnel-ext:latest python3 reviews/2026-10-27_internal_B2/c11_ext_licences.py
import importlib.metadata as md

for p in ["rundec", "kerrgeopy", "tmm", "qutip", "astropy", "tqdm", "matplotlib", "pillow", "pyerfa",
          "astropy-iers-data", "contourpy", "cycler", "fonttools", "kiwisolver", "pyparsing", "python-dateutil",
          "PyYAML", "six", "tzdata"]:
    m = md.metadata(p)
    lic = m.get("License-Expression") or (m.get("License") or "")[:60].replace("\n", " ")
    cls = [c.split("::")[-1].strip() for c in (m.get_all("Classifier") or []) if c.startswith("License")]
    print(f"{p:18s} {md.version(p):24s} expr/license={lic!r} classifiers={cls}")
