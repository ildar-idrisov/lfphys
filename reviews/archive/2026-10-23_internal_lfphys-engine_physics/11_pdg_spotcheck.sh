#!/bin/sh
# 11: independent spot-check of the PDG 2024 numbers in lfphys/lfphys/core/data.py: anonymous download of the PDG 2024
# summary tables (no e-mail, no identifiers), pdftotext, grep of the "Mass m = ..." lines. Runs on the host (needs curl
# and pdftotext); the PDFs go to a temporary directory given as $1 (default: a new mktemp dir).
# Usage: sh 11_pdg_spotcheck.sh [workdir]
[ "$1" = "--help" ] && { sed -n 2,5p "$0"; exit 0; }
D=${1:-$(mktemp -d)}
mkdir -p "$D"
for u in https://pdg.lbl.gov/2024/tables/rpp2024-sum-quarks.pdf https://pdg.lbl.gov/2024/tables/rpp2024-sum-gauge-higgs-bosons.pdf https://pdg.lbl.gov/2024/tables/rpp2024-sum-mesons.pdf; do
  f="$D/$(basename $u)"; [ -s "$f" ] || curl -s -L -A "Mozilla/5.0" -o "$f" "$u"; pdftotext -layout "$f" "${f%.pdf}.txt"
done
echo "--- quarks (PDG 2024) ---"; grep -h "m c =\|m b =\|direct measurements\|from cross-section measurements) m = 162" "$D/rpp2024-sum-quarks.txt"
echo "--- Z (PDG 2024) ---"; grep -h "Mass m = 91" "$D/rpp2024-sum-gauge-higgs-bosons.txt"
echo "--- quarkonia (PDG 2024) ---"
for v in 2984 3096 3414 3510 3525 3556 3637 3686 9398 9460 9859 9892 9899 9912 10023 10355; do
  grep -h "Mass m = $v" "$D/rpp2024-sum-mesons.txt" | head -1
done
