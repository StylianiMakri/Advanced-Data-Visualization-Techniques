import sys
import os
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QVBoxLayout, QWidget
)
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtCore import Qt, QRectF


def parse_spin_output(file_path):
    data = {
        "statespace": {
            "states_stored": 0,
            "states_visited": 0,
            "states_matched": 0,
            "transitions": 0,
            "depth_reached": 0,
            "errors": 0,
            "hash_conflicts": 0
        },
        "memory_usage": {}
    }

    with open(file_path, 'r') as file:
        for line in file:
            if "State-vector" in line:
                match = re.search(r'State-vector (\d+) byte, depth reached (\d+), errors: (\d+)', line)
                if match:
                    data["statespace"]["depth_reached"] = int(match.group(2))
                    data["statespace"]["errors"] = int(match.group(3))

            if "states, stored" in line:
                numbers = re.findall(r'\d+', line)
                if len(numbers) >= 2:
                    data["statespace"]["states_stored"] = int(numbers[0])
                    data["statespace"]["states_visited"] = int(numbers[1])

            if "states, matched" in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    data["statespace"]["states_matched"] = int(numbers[0])

            if "transitions" in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    data["statespace"]["transitions"] = int(numbers[0])

            if "hash conflicts" in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    data["statespace"]["hash_conflicts"] = int(numbers[0])

            if "memory used" in line or "memory usage" in line:
                match = re.findall(r'([0-9\.]+)\s+memory used for ([^\(]+)', line)
                for value, key in match:
                    data["memory_usage"][key.strip()] = float(value)

    return data


class StatsViewer(QMainWindow):
    def __init__(self, data):
        super().__init__()
        self.setWindowTitle("SPIN Statistics Viewer")
        self.setGeometry(100, 100, 800, 400)

        layout = QVBoxLayout()
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)

        self.draw_barchart(data["statespace"], start_y=0)
        if data["memory_usage"]:
            self.draw_piechart(data["memory_usage"], center_x=550, center_y=150, radius=80)

    def draw_barchart(self, stats, start_y):
        bar_width = 30
        spacing = 20
        x = 50
        max_value = max(stats.values()) or 1
        scale = 200 / max_value

        for i, (label, value) in enumerate(stats.items()):
            height = value * scale
            bar = QGraphicsRectItem(x, 300 - height, bar_width, height)
            bar.setBrush(QBrush(QColor("#5a9")))
            bar.setPen(QPen(Qt.GlobalColor.black))
            self.scene.addItem(bar)

            txt = QGraphicsTextItem(f"{label}\n{value}")
            txt.setPos(x - 10, 310)
            txt.setTextWidth(50)
            self.scene.addItem(txt)

            x += bar_width + spacing

    def draw_piechart(self, memory_dict, center_x, center_y, radius):
        total = sum(memory_dict.values())
        if total == 0:
            return

        start_angle = 0
        colors = ["#c44", "#4c4", "#44c", "#cc4", "#4cc", "#c4c"]
        for i, (key, value) in enumerate(memory_dict.items()):
            angle_span = 360 * (value / total)
            slice_item = self.scene.addEllipse(
                QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2),
                QPen(Qt.GlobalColor.black),
                QBrush(QColor(colors[i % len(colors)]))
            )
            slice_item.setStartAngle(int(start_angle * 16))
            slice_item.setSpanAngle(int(angle_span * 16))

            label = QGraphicsTextItem(f"{key}: {value:.1f}")
            label.setPos(center_x + radius + 10, center_y - radius + i * 20)
            self.scene.addItem(label)

            start_angle += angle_span


def main():
    data_folder = os.path.join(os.getcwd(), "data")
    out_files = [f for f in os.listdir(data_folder) if f.endswith(".out")]

    if not out_files:
        print("No .out file found in /data.")
        return

    path = os.path.join(data_folder, out_files[0])
    data = parse_spin_output(path)

    app = QApplication(sys.argv)
    viewer = StatsViewer(data)
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
