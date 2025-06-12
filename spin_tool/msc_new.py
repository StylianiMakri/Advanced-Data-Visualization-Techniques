import json
import os
from graphviz import Digraph


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_ispin_msc(proc_map_raw, events_raw):
    # Normalize keys to strings
    proc_map = {str(k): v for k, v in proc_map_raw.items()}
    events = []

    for evt in events_raw:
        evt_copy = evt.copy()
        if "pid" in evt_copy:
            evt_copy["pid"] = str(evt_copy["pid"])
        if "from" in evt_copy:
            evt_copy["from"] = str(evt_copy["from"])
        if "to" in evt_copy:
            evt_copy["to"] = str(evt_copy["to"])
        events.append(evt_copy)

    dot = Digraph(engine='dot')
    dot.attr(rankdir='TB', fontsize='10')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='white', fontsize='10', fontname='Arial')

    # Display names for process headers
    display_names = {
        pid: (f"{pname}:{pid}" if pname == "calc" else pname)
        for pid, pname in proc_map.items()
    }

    # Header nodes (process names)
    for pid, name in display_names.items():
        dot.node(f"header_{pid}", name, shape='plaintext', fontsize='11', fontname='Arial')

    # Force processes to appear left to right
    sorted_pids = sorted(proc_map.keys(), key=lambda x: int(x))
    with dot.subgraph() as s:
        s.attr(rank='same')
        for pid in sorted_pids:
            s.node(f"header_{pid}")
        for i in range(len(sorted_pids) - 1):
            s.edge(f"header_{sorted_pids[i]}", f"header_{sorted_pids[i+1]}", style='invis')

    timeline_nodes = {pid: [] for pid in proc_map}
    send_events = []
    recv_events = []
    terminations = set()
    assertion_violation = None

    for i, evt in enumerate(events):
        etype = evt["type"]
        eid = f"evt_{i}"

        if etype == "create":
            src, dst, label = evt["from"], evt["to"], evt["label"]
            dot.edge(f"header_{src}", f"header_{dst}", label=label, style="dashed", fontsize="9")
            continue

        if etype == "terminate":
            terminations.add(evt["pid"])
            continue

        if etype == "assertion":
            assertion_violation = (evt["pid"], i)
            continue

        if etype == "action":
            pid, label = evt["pid"], evt["label"]
            dot.node(eid, label=label)

            # Timeline per process
            tl = timeline_nodes[pid]
            if not tl:
                dot.edge(f"header_{pid}", eid, style="solid", arrowhead="none")
            else:
                dot.edge(tl[-1], eid, style="solid", arrowhead="none")
            tl.append(eid)

            if label.startswith("f!"):
                chan, val = label[2:].split(",", 1)
                send_events.append((pid, i, eid, chan.strip(), val.strip()))
            elif label.startswith("f?"):
                chan, val = label[2:].split(",", 1)
                recv_events.append((pid, i, eid, chan.strip(), val.strip()))

    # Match sends to receives
    used_receives = set()
    for s_pid, s_index, s_node, s_chan, s_val in send_events:
        for r_pid, r_index, r_node, r_chan, r_val in recv_events:
            if r_node in used_receives:
                continue
            if s_chan == r_chan and s_val == r_val:
                dot.edge(s_node, r_node, label=f"{s_chan},{s_val}", fontsize="8", color="blue")
                used_receives.add(r_node)
                break

    # Assertion failure
    if assertion_violation:
        pid, idx = assertion_violation
        assert_node = f"evt_{idx}"
        dot.node(assert_node, "assertion failed", shape="box", style="filled", fillcolor="red", fontcolor="white")

    # Terminations
    for pid in terminations:
        tl = timeline_nodes.get(pid)
        if tl:
            last = tl[-1]
            tnode = f"term_{pid}"
            dot.node(tnode, "(terminated)", shape="plaintext", fontcolor="gray")
            dot.edge(last, tnode, style="dotted", arrowhead="none")

    return dot


def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_path, "output", "msc_data.json")
    out_path = os.path.join(base_path, "output", "msc_output")

    data = load_json(json_path)
    graph = build_ispin_msc(data["processes"], data["events"])
    graph.render(filename=out_path, format='png', cleanup=True)
    print(f"MSC generated: {out_path}.png")


if __name__ == '__main__':
    main()
