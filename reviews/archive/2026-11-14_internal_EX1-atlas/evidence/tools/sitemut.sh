#!/bin/bash
# inside the container: /lf repo (ro), /s scratch
set -u
SRC=/lf/visualizations/recordings
W=/s/work/sitemut; rm -rf $W; mkdir -p $W
run() {  # name
  local n=$1
  python3 site/build.py --recordings $W/$n/rec --out $W/$n/site --base /lfphys/ > $W/$n/build.out 2>&1; echo "build exit $?" >> $W/$n/build.out
  python3 site/check.py $W/$n/site --base /lfphys/ > $W/$n/check.out 2>&1; echo "check exit $?" >> $W/$n/check.out
  echo "=== $n"; grep -E "^(FAIL|WARN)" $W/$n/build.out | grep -i atlas | head -3; grep -E "^FAIL" $W/$n/check.out | head -6; tail -2 $W/$n/check.out
}
mk() { mkdir -p $W/$1; cp -a $SRC $W/$1/rec; }
py() { python3 -c "$1"; }
mk clean; run clean
mk failedchecks; py "
import json,glob
f=glob.glob('$W/failedchecks/rec/s03_projectile/atlas/explore/atlas.*.json')[0]; m=json.load(open(f)); m['checks']['failed']=1; open(f,'w').write(json.dumps(m))"; run failedchecks
mk stale; py "
import json
f='$W/stale/rec/u32_double_slit/index.json'; ix=json.load(open(f)); ix['atlases'][0]['key']='0'*16; open(f,'w').write(json.dumps(ix))"; run stale
mk nofolder; rm -rf $W/nofolder/rec/s03_projectile/atlas/lab.air; run nofolder
mk noentry; py "
import json
f='$W/noentry/rec/s03_projectile/index.json'; ix=json.load(open(f)); ix['atlases']=[a for a in ix['atlases'] if a['id']!='lab.angles']; open(f,'w').write(json.dumps(ix))"; run noentry
mk nopoint; rm -f $W/nopoint/rec/s03_projectile/atlas/explore/p500.*; run nopoint
