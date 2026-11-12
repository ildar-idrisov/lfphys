# Shared set-up for the review scripts: paths inside the container (engine at /lf, read-only).
import sys

for p in ("/lf/lfphys", "/lf/visualizations", "/lf/visualizations/server", "/lf/visualizations/tests"):
    if p not in sys.path:
        sys.path.insert(0, p)
