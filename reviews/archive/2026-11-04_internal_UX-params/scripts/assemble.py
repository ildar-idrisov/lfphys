"""Fill the generated tables into REVIEW.md (placeholders SUMMARY_TABLE, KINDS_TABLE, SIGNATURES, FAILED_CHECKS)."""
import sys
review, frag = sys.argv[1], sys.argv[2]
s = open(review).read()
for key, fn in (("SUMMARY_TABLE", "summary_table.md"), ("KINDS_TABLE", "kinds_table.md"),
                ("SIGNATURES", "signatures.md"), ("FAILED_CHECKS", "failed_checks.md")):
    body = open(f"{frag}/{fn}").read().strip()
    if key not in s:
        print("missing placeholder", key)
    s = s.replace(key, body, 1)
s = s.replace("PENDING_FINDINGS\n\n", "").replace("PENDING_FINDINGS", "")
open(review, "w").write(s)
print("ok", len(s))
