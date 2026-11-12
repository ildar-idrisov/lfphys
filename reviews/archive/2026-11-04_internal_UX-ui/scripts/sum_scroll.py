import sys, json
for l in open(sys.argv[1]):
    if not l.startswith('{'):
        continue
    d = json.loads(l)
    print('CASE', d['case'], d.get('error', ''))
    for size, r in d.items():
        if size in ('case', 'error'):
            continue
        if not isinstance(r, dict):
            print(' ', size, r); continue
        for sel, v in r.items():
            if isinstance(v, dict) and 'after_wheel' in v:
                print(' ', size, sel, 'wheel', v['after_wheel'], 'min', v['min'], 'final', v['final'], 'resets', v['resets'],
                      'removed', [(x['el'], x['scrollTop']) for x in v['removed']][:3],
                      'logs', sorted(set(x['kind'] + ' ' + x['el'] + ' ' + x['stack'][:100] for x in v['log'])))
            else:
                print(' ', size, sel, v)
