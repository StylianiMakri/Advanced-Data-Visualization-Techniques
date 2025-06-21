import os
import json
import sys
from collections import defaultdict

from PyQt6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsTextItem,
    QGraphicsRectItem, QVBoxLayout, QPushButton, QWidget, QFileDialog
)
from PyQt6.QtGui import QPen, QBrush, QColor, QPainterPath, QImage, QPainter
from PyQt6.QtCore import Qt, QPointF, QRectF

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

    dx, dy = x2 - x1, y2 - y1
    length = (dx ** 2 + dy ** 2) ** 0.5
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
    if '!' in label:
        chan, content = label.split('!', 1)
    elif '?' in label:
        chan, content = label.split('?', 1)
    else:
        return None, None
    msg_type = content.split(',', 1)[0].strip()
    return chan.strip(), msg_type

class MSCViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPIN-style Message Sequence Chart")
        self.resize(1300, 750)

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        self.save_button = QPushButton("Save as PNG")
        self.save_button.clicked.connect(self.save_png)
        layout.addWidget(self.save_button)

        self.draw_msc()

    def save_png(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save PNG", "msc_chart.png", "PNG Files (*.png)")
        if file_path:
            rect = self.scene.itemsBoundingRect()
            image = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.white)

            painter = QPainter(image)
            self.scene.render(painter, target=QRectF(image.rect()), source=rect)
            painter.end()
            image.save(file_path)

    def draw_msc(self):
        spacing_x = 160
        top_y = 50
        rect_width = 110
        rect_height = 25
        y_step = 35

        events = load_events_from_output()
        processes = list(dict.fromkeys(proc for proc, _ in events))
        process_positions = {}

        for i, proc in enumerate(processes):
            x = spacing_x * (i + 1)
            process_positions[proc] = x
            self.scene.addLine(x, top_y, x, top_y + 1000, QPen(Qt.GlobalColor.black, 1, Qt.PenStyle.DashLine))
            label = QGraphicsTextItem(proc if proc else "(init)")
            label.setPos(x - 35, top_y - 30)
            self.scene.addItem(label)

        send_buffer = defaultdict(list)
        canonical_channels = {}

        def get_canonical_channel(chan):
            return canonical_channels.get(chan, chan)

        for step, (proc, label) in enumerate(events):
            y = top_y + step * y_step
            x = process_positions.get(proc, spacing_x // 2)

            rect = QGraphicsRectItem(x - rect_width / 2, y, rect_width, rect_height)
            rect.setBrush(QBrush(QColor("pink")))
            self.scene.addItem(rect)

            text = QGraphicsTextItem(label)
            text.setDefaultTextColor(Qt.GlobalColor.black)
            text.setPos(x - rect_width / 2 + 5, y + 3)
            self.scene.addItem(text)

            chan, msg_type = normalize_label(label)
            if not chan or not msg_type:
                continue

            canon_chan = get_canonical_channel(chan)

            if '!' in label:
                key = (canon_chan, msg_type)
                send_buffer[key].append((proc, step, chan))
                canonical_channels[chan] = canon_chan

            elif '?' in label:
                key = (canon_chan, msg_type)
                matched = None

                if send_buffer[key]:
                    matched = send_buffer[key].pop(0)
                    canonical_channels[chan] = canon_chan
                else:
                    for (alt_chan, alt_type), queue in send_buffer.items():
                        if alt_type == msg_type and queue:
                            matched = queue.pop(0)
                            canonical_channels[chan] = alt_chan
                            break

                if matched:
                    send_proc, send_step, send_chan = matched
                    x1 = process_positions[send_proc] + rect_width / 2
                    y1 = top_y + send_step * y_step + rect_height / 2
                    x2 = x - rect_width / 2
                    y2 = y + rect_height / 2
                    draw_arrow(self.scene, (x1, y1), (x2, y2), QColor("blue"))
                else:
                    print(f"[!] No send match found for receive: {label} at step {step}")

        final_y = top_y + len(events) * y_step + 20
        self.scene.addLine(spacing_x // 2, final_y, spacing_x * (len(processes) + 1), final_y,
                           QPen(QColor("red"), 2, Qt.PenStyle.DashLine))

def main():
    app = QApplication(sys.argv)
    viewer = MSCViewer()
    viewer.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
