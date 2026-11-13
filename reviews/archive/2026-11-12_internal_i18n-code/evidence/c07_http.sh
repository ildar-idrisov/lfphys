#!/bin/bash
# the endpoint /api/i18n/<lang> and error bodies on the private server (port 8651)
B=http://127.0.0.1:8651
h() { echo "== $*"; curl -s -o /tmp/rv18c_body -D - "$@" | grep -i -E "^HTTP|etag|cache-control|content-length|content-type"; head -c 300 /tmp/rv18c_body; echo; }
h $B/api/i18n/ru
ET=$(curl -s -D - -o /dev/null $B/api/i18n/ru | grep -i etag | cut -d' ' -f2 | tr -d '\r')
echo "ETag=$ET"
h -H "If-None-Match: $ET" $B/api/i18n/ru
h -H "If-None-Match: W/$ET" $B/api/i18n/ru
h -H "If-None-Match: \"x\", $ET" $B/api/i18n/ru
h -H "If-None-Match: *" $B/api/i18n/ru
h -H "If-None-Match: $ET" $B/api/i18n/en
h -H "Accept-Encoding: gzip" $B/api/i18n/ru
h $B/api/i18n/en
h $B/api/i18n/RU
h $B/api/i18n/ru-RU
h "$B/api/i18n/%3Cscript%3E"
h -X HEAD $B/api/i18n/ru
echo "== sizes"; for l in en ru; do curl -s $B/api/i18n/$l | wc -c; done
echo "== error bodies"
h $B/api/runs/nope
h -X POST -H "Content-Type: application/json" -d '{"viz":"nope"}' $B/api/runs
h -X POST -H "Content-Type: application/json" -d 'not json' $B/api/runs
h -X POST -H "Content-Type: application/json" -d '{"viz":"v01_light_travel","params":{"nonexistent_param":1}}' $B/api/runs
h "$B/api/runs/nope/series?ids=x&format=csv&lang=ru"
