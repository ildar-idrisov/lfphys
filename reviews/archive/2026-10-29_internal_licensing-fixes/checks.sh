#!/bin/sh
# Read-only consistency checks behind REVIEW.md (review of commit 9462d8b). Run from engine/:
#   sh reviews/2026-10-29_internal_licensing-fixes/checks.sh > reviews/2026-10-29_internal_licensing-fixes/checks.out
# Changes nothing; needs only POSIX sh, cmp, grep.
set -u
echo "== 1. copies of the licence files in lfphys/ and visualizations/ against the root"
for f in LICENSE.md CLA.md COMMERCIAL.md CONTRIBUTING.md PUBLICATIONS.md LICENSE-DOCS.txt NOTICE CITATION.cff; do
  for d in lfphys visualizations; do
    if cmp -s "$f" "$d/$f"; then echo "same  $d/$f"; else echo "DIFF  $d/$f"; fi
  done
done
echo
echo "== 2. PolyForm / Required Notice outside review folders and run records"
grep -rIn -i 'polyform\|required notice' --exclude-dir=reviews --exclude-dir=runs --exclude-dir=.pytest_cache . | cut -c1-160
echo
echo "== 3. source files (py/js/mjs/html/css) without an SPDX licence line (vendor excluded)"
grep -rIL 'SPDX-License-Identifier' --include=*.py --include=*.js --include=*.mjs --include=*.html --include=*.css \
  --exclude-dir=reviews --exclude-dir=runs --exclude-dir=vendor --exclude-dir=.pytest_cache . || true
echo "(none listed above = every file carries one)"
echo
echo "== 4. the citation condition: where 'substantially' is kept and where summaries drop it"
grep -n 'substantially' LICENSE.md PUBLICATIONS.md NOTICE CITATION.cff lfphys/README.md README.md | cut -c1-160
grep -n 'обязательна' visualizations/README.md visualizations/player/legal.html visualizations/player/index.html
grep -n 'publications must cite' README.md | cut -c1-160
echo
echo "== 5. the CLA's definition of Licensor (who receives the CLA grants)"
grep -n 'assigns or licenses' CLA.md
echo
echo "== 6. versions a citing user can see"
grep -n '^version' CITATION.cff lfphys/CITATION.cff visualizations/CITATION.cff
grep -n '__version__ =' lfphys/lfphys/__init__.py visualizations/server/lfviz/__init__.py
grep -n '"version": "' visualizations/v01_light_travel/viz.py
echo
echo "== 7. where the in-player help text lives (code or documentation?)"
echo "viz.py files with in-player help strings: $(grep -l '"help":' visualizations/v*/viz.py | wc -l)"
grep -n 'описания, справка, рисунки' visualizations/README.md
echo
echo "== 8. 'every source file starts with' the owner's copyright line"
grep -n 'starts with the lines' -A3 CONTRIBUTING.md
echo
echo "== 9. affirmative accuracy wording next to the disclaimer"
grep -n "accuracy is the one stated\|computed exactly\|provably contains" lfphys/README.md | cut -c1-160
