import os
import json

from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsRectItem
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath
from PyQt6.QtCore import Qt, QPointF
import sys

def load_events_from_output():
    output_dir = "output"
    json_files = [f for f in os.listdir(output_dir) if f.endswith("_events.json")]
    if len(json_files) != 1:
        raise ValueError(f"Expected exactly one *_events.json in {output_dir}, found {len(json_files)}")
    json_path = os.path.join(output_dir, json_files[0])
    with open(json_path, 'r') as f:
        return json.load(f)

# Load events from JSON file
events = load_events_from_output()
print("Loaded events:")
for e in events:
    print(e)


# Dynamically determine unique processes in order of appearance
processes = list(dict.fromkeys(proc for proc, _ in events))


def draw_arrow(scene, start_point, end_point, color=Qt.GlobalColor.blue):
    x1, y1 = start_point
    x2, y2 = end_point
    pen = QPen(color, 2)
    scene.addLine(x1, y1, x2, y2, pen)

    # Draw arrowhead
    dx, dy = x2 - x1, y2 - y1
    length = (dx**2 + dy**2) ** 0.5
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    perp_x, perp_y = -uy, ux
    arrow_size = 6
    p1 = QPointF(x2, y2)
    p2 = QPointF(x2 - ux * 15 + perp_x * arrow_size, y2 - uy * 15 + perp_y * arrow_size)
    p3 = QPointF(x2 - ux * 15 - perp_x * arrow_size, y2 - uy * 15 - perp_y * arrow_size)

    path = QPainterPath()
    path.moveTo(p1)
    path.lineTo(p2)
    path.lineTo(p3)
    path.closeSubpath()
    scene.addPath(path, pen, QBrush(color))


def draw_msc():
    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setWindowTitle("SPIN-style Message Sequence Chart")
    view.resize(1000, 600)

    spacing_x = 160
    top_y = 50
    process_positions = {}
    rect_width = 110
    rect_height = 25

    # Draw lifelines and process labels
    for i, proc in enumerate(processes):
        x = spacing_x * (i + 1)
        process_positions[proc] = x
        scene.addLine(x, top_y, x, top_y + 1000, QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine))
        label = QGraphicsTextItem(proc)
        label.setPos(x - 35, top_y - 30)
        scene.addItem(label)

    # Draw events and arrows
    y_step = 35
    for step, (proc, label) in enumerate(events):
        y = top_y + step * y_step
        x = process_positions[proc]

        # Yellow box
        rect = QGraphicsRectItem(x - rect_width / 2, y, rect_width, rect_height)
        rect.setBrush(QBrush(QColor("yellow")))
        scene.addItem(rect)

        text = QGraphicsTextItem(label)
        text.setDefaultTextColor(Qt.GlobalColor.black)
        text.setPos(x - rect_width / 2 + 5, y + 3)
        scene.addItem(text)

        # If it is a receive (?...), try to draw arrow from matching send
        if '?' in label:
            chan_recv, payload_recv = label.split('?')
            # recv payload splits into type and value
            if ',' in payload_recv:
                msg_type_recv, _ = payload_recv.split(',', 1)
            else:
                msg_type_recv = payload_recv

            for prev_step in range(step - 1, -1, -1):
                prev_proc, prev_label = events[prev_step]
                if '!' in prev_label:
                    chan_send, payload_send = prev_label.split('!')
                    if ',' in payload_send:
                        msg_type_send, _ = payload_send.split(',', 1)
                    else:
                        msg_type_send = payload_send

                    if chan_send == chan_recv and msg_type_send == msg_type_recv:
                        print(f"Match found: from {prev_proc} at step {prev_step} to {proc} at step {step}")
                        x1 = process_positions[prev_proc] + rect_width / 2
                        y1 = top_y + prev_step * y_step + rect_height / 2
                        x2 = process_positions[proc] - rect_width / 2
                        y2 = y + rect_height / 2
                        draw_arrow(scene, (x1, y1), (x2, y2))
                        break



    # Final red dashed line
    final_y = top_y + len(events) * y_step + 20
    scene.addLine(spacing_x, final_y, spacing_x * (len(processes) + 1), final_y,
                  QPen(QColor("red"), 2, Qt.PenStyle.DashLine))

    view.show()
    sys.exit(app.exec())

draw_msc()
