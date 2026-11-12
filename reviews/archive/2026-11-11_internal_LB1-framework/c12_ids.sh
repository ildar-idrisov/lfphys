#!/bin/sh
# c12: ids in the series and sweep routes against the PRIVATE server (port 8601): path traversal, Unicode digits,
# a non-numeric world. Output in c12_ids.out.
RID=$(curl -s localhost:8601/api/runs | python3 -c "import json,sys; print([r['id'] for r in json.load(sys.stdin) if '-p97-' in r['id']][0])")
echo "run $RID"
for m in GET DELETE; do for n in "%C2%B2" "%D9%A1" "..%2F..%2Fx" "1"; do
  printf "%s /sweeps/%s -> " $m $n; curl -s -o /dev/null -w "%{http_code}\n" -X $m "localhost:8601/api/runs/$RID/sweeps/$n"
done; done
printf "GET /series?ids=E&world=..%%2F -> "; curl -s -w " %{http_code}\n" "localhost:8601/api/runs/$RID/series?ids=E&world=..%2F"
printf "GET /api/runs/..%%2F..%%2Fetc/series -> "; curl -s -o /dev/null -w "%{http_code}\n" "localhost:8601/api/runs/..%2F..%2Fetc/series?ids=E"
