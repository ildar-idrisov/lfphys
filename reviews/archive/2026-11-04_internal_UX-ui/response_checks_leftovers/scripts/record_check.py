"""What the keyframes variant's runs recorded: the live changes applied (events of kind action/set) or refused
(errors), and the `prepared` messages (v13, v14). Usage: record_check.py <run dir> ..."""
import sys
sys.path[:0] = ["/lf/visualizations/server"]
from lfviz import protocol
for d in sys.argv[1:]:
    data = open(d + "/stream.lfrec", "rb").read()
    prep, ev, err = 0, [], []
    for item in protocol.iter_stream(data, len(protocol.MAGIC)):
        msg = item[1] if isinstance(item, tuple) else item
        m = protocol.peek_meta(msg)
        if m.get("type") == "prepared":
            prep += 1
        elif m.get("type") == "event" and m.get("name") == "set":
            ev.append(m["text"][:150])
        elif m.get("type") == "error":
            err.append(m["text"][:150])
    print(d.split("/")[-1], {"prepared": prep, "set_events": ev, "errors": err})
