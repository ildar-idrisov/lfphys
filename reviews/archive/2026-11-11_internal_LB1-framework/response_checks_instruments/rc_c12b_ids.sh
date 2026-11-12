#!/bin/sh
# [response] rc_c12b = the reviewer's c12 against the processor's server (port 8611); the cancel route added.
# c12: ids in the series and sweep routes against the PRIVATE server (port 8611): path traversal, Unicode digits,
# a non-numeric world. Output in c12_ids.out.
RID=$(curl -s localhost:8611/api/runs | python3 -c "import json,sys; print([r['id'] for r in json.load(sys.stdin) if '-p97-' in r['id']][0])")
echo "run $RID"
for m in GET DELETE; do for n in "%C2%B2" "%D9%A1" "..%2F..%2Fx" "1"; do
  printf "%s /sweeps/%s -> " $m $n; curl -s -o /dev/null -w "%{http_code}\n" -X $m "localhost:8611/api/runs/$RID/sweeps/$n"
done; done
printf "GET /series?ids=E&world=..%%2F -> "; curl -s -w " %{http_code}\n" "localhost:8611/api/runs/$RID/series?ids=E&world=..%2F"
printf "GET /api/runs/..%%2F..%%2Fetc/series -> "; curl -s -o /dev/null -w "%{http_code}\n" "localhost:8611/api/runs/..%2F..%2Fetc/series?ids=E"
for n in "%C2%B2" "%D9%A1" "..%2F..%2Fx" "1"; do
  printf "POST /sweeps/%s/cancel -> " $n; curl -s -o /dev/null -w "%{http_code}\n" -X POST "localhost:8611/api/runs/$RID/sweeps/$n/cancel"
done
printf "POST /sweep with a list as the target id -> "; curl -s -w " %{http_code}\n" -X POST -H "Content-Type: application/json" -d '{"target":{"kind":"law","id":["k"]},"values":[1],"duration":1,"measure":"E"}' "localhost:8611/api/runs/$RID/sweep"
