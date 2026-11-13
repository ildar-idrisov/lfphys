# prints a review log (logs/*.jsonl) compactly: the scans' findings and the other records
import json, sys
for f in sys.argv[1:]:
    for l in open(f):
        o = json.loads(l)
        if 'where' in o:
            print('##', o['where'], 'nbad', o['nbad'], 'over', len(o['over']), 'hscroll', o['hscroll'], 'errs', o['errs'][:3])
            for b in o['bad'][:15]: print('   ', b['why'], b['k'], repr(b['s'][:160]), b['at'][-70:])
            for b in o['over'][:10]: print('   OVER', json.dumps(b, ensure_ascii=False)[:250])
        elif 'panelShot' in o: continue
        else: print(json.dumps(o, ensure_ascii=False)[:900])
