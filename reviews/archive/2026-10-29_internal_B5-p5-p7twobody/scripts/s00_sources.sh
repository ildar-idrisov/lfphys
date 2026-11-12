#!/bin/sh
# Fetch the cited texts (arXiv PDFs and Steck's notes; no contact parameters or identifiers in the requests) into a
# fresh directory given as $1 (default ./dl), convert with pdftotext -layout, and extract the passages this review
# compares with the code. Output: out/00_quotes.txt (run from the review folder).
set -e
D=${1:-dl}
mkdir -p "$D"
for id in 1310.1528v3 1310.1528v6 gr-qc/9506022v1 1606.02744v1 0805.4002v1 quant-ph/9702007v1 1906.04478 1204.4325v3 \
          quant-ph/0612118v3 0810.5488v1; do
  f=$(echo $id | tr '/' '_')
  [ -s "$D/$f.pdf" ] || { curl -sL -A "Mozilla/5.0" -o "$D/$f.pdf" "https://arxiv.org/pdf/$id"; sleep 3; }
  pdftotext -layout "$D/$f.pdf" "$D/$f.txt"
done
[ -s "$D/steck.pdf" ] || curl -sL -A "Mozilla/5.0" -o "$D/steck.pdf" \
  https://atomoptics.uoregon.edu/~dsteck/teaching/quantum-optics/quantum-optics-notes.pdf
pdftotext -layout "$D/steck.pdf" "$D/steck.txt"
{
  echo "== Weisberg & Huang 2016 (arXiv:1606.02744v1): Table 2, Sec. 3.1, 4.1, 4.3, 5.1"
  sed -n 135p "$D/1606.02744v1.txt"; sed -n 262,278p "$D/1606.02744v1.txt"; sed -n 345,362p "$D/1606.02744v1.txt"
  sed -n 455,462p "$D/1606.02744v1.txt"; sed -n 515,560p "$D/1606.02744v1.txt"
  echo "== Blanchet 2014 (arXiv:1310.1528v3) Eqs. (219)-(220)"; sed -n 5628,5750p "$D/1310.1528v3.txt"
  echo "== Blanchet 2014 Eqs. (226)-(228), (232)"; sed -n 5930,5970p "$D/1310.1528v3.txt"; sed -n 6003,6013p "$D/1310.1528v3.txt"
  echo "== Blanchet 2014 Sec. 9.4 and Eqs. (322), (323)"; sed -n 8093,8100p "$D/1310.1528v3.txt"; sed -n 8128,8142p "$D/1310.1528v3.txt"; sed -n 8355,8372p "$D/1310.1528v3.txt"
  echo "== Blanchet 2014 Eqs. (346)-(351), (358)-(359)"; sed -n 9086,9112p "$D/1310.1528v3.txt"; sed -n 9160,9245p "$D/1310.1528v3.txt"; sed -n 9405,9425p "$D/1310.1528v3.txt"
  echo "== Blanchet 2024 (arXiv:1310.1528v6) Eqs. (358e), (359e)"; sed -n 9555,9572p "$D/1310.1528v6.txt"; sed -n 9688,9705p "$D/1310.1528v6.txt"
  echo "== Kidder 1995 (arXiv:gr-qc/9506022v1) Eqs. (2.2), (2.7), (2.9)"; sed -n 255,306p "$D/gr-qc_9506022v1.txt"; sed -n 410,478p "$D/gr-qc_9506022v1.txt"
  echo "== Steck rev. 0.16.11, (5.25)-(5.27), (5.127), (5.132)-(5.133), (5.556)"; sed -n 25p "$D/steck.txt"; sed -n 9005,9025p "$D/steck.txt"; sed -n 10290,10300p "$D/steck.txt"; sed -n 10330,10350p "$D/steck.txt"; sed -n 15045,15052p "$D/steck.txt"
  echo "== Bassi et al. 2013 (arXiv:1204.4325v3) Eqs. (19), (21), (22)"; sed -n 1257,1262p "$D/1204.4325v3.txt"; sed -n 1322,1352p "$D/1204.4325v3.txt"
  echo "== Hornberger (arXiv:quant-ph/0612118v3) Eqs. (5.170), (5.171)"; sed -n 2430,2442p "$D/quant-ph_0612118v3.txt"; sed -n 2493,2497p "$D/quant-ph_0612118v3.txt"
  echo "== Blanes et al. (arXiv:0810.5488v1) Eqs. (252)-(254)"; sed -n 5410,5426p "$D/0810.5488v1.txt"
  echo "== Manzano (arXiv:1906.04478) Eqs. (92), (93), (101)"; sed -n 1224,1240p "$D/1906.04478.txt"; sed -n 1410,1428p "$D/1906.04478.txt"
  echo "== Plenio & Knight (arXiv:quant-ph/9702007v1) Eqs. (30), (66), (67)"; sed -n 626,634p "$D/quant-ph_9702007v1.txt"; sed -n 1163,1180p "$D/quant-ph_9702007v1.txt"
} > out/00_quotes.txt
echo "written out/00_quotes.txt ($(wc -l < out/00_quotes.txt) lines)"
