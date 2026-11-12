#!/bin/bash
# Quotation checks of lfphys/sources/verification_2026-11-03_p15_3.md against the texts (arXiv PDFs, pdftotext
# -layout). Usage: v01_sources.sh <empty download directory outside the project>. Neutral user agent, no contact
# parameter. Output: v01_sources.out
D=${1:?download directory}
mkdir -p "$D"
for id in quant-ph/0611067 1204.4325 0805.4002 quant-ph/9702007 2209.00480 cond-mat/0506691; do
  n=$(echo $id | tr '/' '_'); mkdir -p "$D/$n"
  [ -s "$D/$n/paper.pdf" ] || curl -sL -A "Mozilla/5.0 (research reader)" -o "$D/$n/paper.pdf" "https://arxiv.org/pdf/$id"
  [ -s "$D/$n/paper.txt" ] || pdftotext -layout "$D/$n/paper.pdf" "$D/$n/paper.txt"
done
echo "== [JS] quant-ph/0611067 eq. (22), (24)"; grep -n "4k∆t\|Gaussian-weighted" "$D/quant-ph_0611067/paper.txt" | head -8
echo "== [B] 1204.4325 eqs. (17), (18), (22)"; grep -n "(πrC2 )3/4\|kLn (x)ψt (x1 , x2 , . . . xN )k2\|λGRW \[1 − e\|Poissonian process" "$D/1204.4325/paper.txt" | head
echo "== [CDM] 0805.4002 eqs. (4), (8), (10), (11); publication"; grep -n "C Cm .  *(4)\|δpm = δt\|with a probability δpm\|probability 1 − δp\|Published in AIP" "$D/0805.4002/paper.txt" | head
echo "== [PK] quant-ph/9702007 eqs. (30), (66), (67)"; grep -n "e−i Hef f t/h̄\|just the delay function\|P0 (t) = hψA\|I1 (τ ) ≡" "$D/quant-ph_9702007/paper.txt" | head
echo "== [PDAC] 2209.00480 p. 1"; grep -n "relative phase φAB = qΦB\|infinitely long and thin solenoid" "$D/2209.00480/paper.txt" | head
echo "== [PCM] cond-mat/0506691 flux unit"; grep -n "Φ0 = 2πh̄/|e|" "$D/cond-mat_0506691/paper.txt" | head
