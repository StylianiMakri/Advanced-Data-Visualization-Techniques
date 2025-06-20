import os
import json
import sys

from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QGraphicsTextItem, QGraphicsRectItem
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath
from PyQt6.QtCore import Qt, QPointF

def load_events_from_output():
    output_dir = "output"
    json_files = [f for f in os.listdir(output_dir) if f.endswith("_events.json")]
    if len(json_files) != 1:
        raise ValueError(f"Expected exactly one *_events.json in {output_dir}, found {len(json_files)}")
    json_path = os.path.join(output_dir, json_files[0])
    with open(json_path, 'r') as f:
        return json.load(f)

def draw_arrow(scene, start_point, end_point, color=Qt.GlobalColor.black):
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

def normalize_label(label):
    """Extract channel and message type ignoring payload"""
    if '!' in label:
        chan, content = label.split('!', 1)
    elif '?' in label:
        chan, content = label.split('?', 1)
    else:
        return None, None
    msg_type = content.split(',', 1)[0].strip()
    return chan.strip(), msg_type

def draw_msc():
    app = QApplication(sys.argv)
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setWindowTitle("SPIN-style Message Sequence Chart")
    view.resize(1000, 600)

    spacing_x = 160
    top_y = 50
    rect_width = 110
    rect_height = 25
    y_step = 35

    events = load_events_from_output()

    # Get unique processes in order
    processes = list(dict.fromkeys(proc for proc, _ in events))

    process_positions = {}
    # Assign x positions, giving empty "" processes a default column at x=spacing_x
    for i, proc in enumerate(processes):
        x = spacing_x * (i + 1) if proc else spacing_x // 2
        process_positions[proc] = x
        scene.addLine(x, top_y, x, top_y + 1000, QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine))
        label = QGraphicsTextItem(proc if proc else "(init)")
        label.setPos(x - 35, top_y - 30)
        scene.addItem(label)

    # Define channel equivalences for matching sends and receives on different channel names
    channel_equiv = {
        '4': 'me',
        'me': '4',
        # Add more if needed
    }

    pending_sends = {}

    for step, (proc, label) in enumerate(events):
        y = top_y + step * y_step
        x = process_positions.get(proc, spacing_x // 2)  # default x for unknown process

        rect = QGraphicsRectItem(x - rect_width / 2, y, rect_width, rect_height)
        rect.setBrush(QBrush(QColor("pink")))
        scene.addItem(rect)

        text = QGraphicsTextItem(label)
        text.setDefaultTextColor(Qt.GlobalColor.black)
        text.setPos(x - rect_width / 2 + 5, y + 3)
        scene.addItem(text)

        chan, msg_type = normalize_label(label)
        if chan is None or msg_type is None:
            continue

        if '!' in label:
            key = (chan, msg_type)
            pending_sends.setdefault(key, []).append((proc, step))

        elif '?' in label:
            key = (chan, msg_type)
            matched_send = None

            # Try exact match first
            if key in pending_sends and pending_sends[key]:
                matched_send = pending_sends[key].pop(0)
            else:
                # Try equivalent channel matching
                equiv_chan = channel_equiv.get(chan)
                if equiv_chan:
                    equiv_key = (equiv_chan, msg_type)
                    if equiv_key in pending_sends and pending_sends[equiv_key]:
                        matched_send = pending_sends[equiv_key].pop(0)

            if matched_send:
                send_proc, send_step = matched_send
                x1 = process_positions.get(send_proc, spacing_x // 2) + rect_width / 2
                y1 = top_y + send_step * y_step + rect_height / 2
                x2 = x - rect_width / 2
                y2 = y + rect_height / 2
                draw_arrow(scene, (x1, y1), (x2, y2))

    final_y = top_y + len(events) * y_step + 20
    scene.addLine(spacing_x // 2, final_y, spacing_x * (len(processes) + 1), final_y,
                  QPen(QColor("red"), 2, Qt.PenStyle.DashLine))

    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    draw_msc()
