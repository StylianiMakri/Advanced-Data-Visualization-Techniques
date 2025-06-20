import json
import os
import sys
from PyQt6.QtWidgets import QApplication, QLabel, QScrollArea, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap
from graphviz import Digraph


def load_msc_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    proc_names = data.get('processes', {})
    events = data.get('events', [])
    proc_names = {int(k): v for k, v in proc_names.items()}
    return proc_names, events


def build_msc_graph(proc_names, events):
    dot = Digraph(engine='dot')
    dot.attr(rankdir='TB', fontsize='10')  # Top to bottom layout
    dot.attr('node', shape='rectangle', style='filled', fillcolor='lightgray', fontsize='10', fontname='Arial', fixedsize='false')

    for pid, pname in sorted(proc_names.items()):
        label = f"{pid}: {pname}"
        dot.node(f"proc_{pid}_head", label)

    for pid in proc_names.keys():
        dot.node(f"proc_{pid}_line", label='', shape='point', width='0.01', height='0.01', style='invis')

    with dot.subgraph() as s:
        s.attr(rank='same')
        for pid in proc_names.keys():
            s.node(f"proc_{pid}_head")
            s.node(f"proc_{pid}_line")

    last_event_node = {}

    event_count = 0
    for evt in events:
        event_count += 1
        if evt['type'] == 'create':
            src = evt['from'] 
            dst = evt['to']   
            label = evt['label'] 

            dot.edge(f"proc_{src}_line", f"proc_{dst}_head", label=label, style='dashed', fontsize='8')

        elif evt['type'] == 'action':
            pid = evt['pid']
            action = evt['label'] 

            node_id = f"evt_{pid}_{event_count}"
            dot.node(node_id, label=action, shape='box', style='rounded,filled', fillcolor='white', fontsize='9', fontname='Arial')

            if pid in last_event_node:
                dot.edge(last_event_node[pid], node_id, style='solid', arrowhead='none')
            else:
                dot.edge(f"proc_{pid}_head", node_id, style='solid', arrowhead='none')

            last_event_node[pid] = node_id

    for pid in proc_names.keys():
        start = f"proc_{pid}_head"
        end = last_event_node.get(pid, start)
        if start != end:
            dot.edge(start, end, style='dotted', arrowhead='none')

    return dot


class MscWindow(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Custom MSC Viewer")
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        label = QLabel()
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        scroll.setWidget(label)
        layout.addWidget(scroll)
        self.setLayout(layout)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, 'output')
    json_path = os.path.join(output_dir, 'msc_data.json')

    if not os.path.exists(json_path):
        print(f"No MSC JSON file found at {json_path}")
        return

    proc_names, events = load_msc_json(json_path)
    graph = build_msc_graph(proc_names, events)

    output_image = os.path.join(output_dir, 'msc_output')
    graph.render(filename=output_image, format='png', cleanup=True)

    app = QApplication(sys.argv)
    viewer = MscWindow(output_image)
    viewer.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
