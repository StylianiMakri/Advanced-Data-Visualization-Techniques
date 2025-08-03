import sys
import os
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QScrollArea, QGroupBox, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsTextItem,
    QGraphicsRectItem, QFrame, QSplitter
)
from PyQt6.QtGui import QBrush, QPen, QColor
from PyQt6.QtCore import Qt, QRectF


def parse_spin_output(file_path):
    data = {
        "Compilation Commands": [],
        "Settings Used": [],
        "Verification Checks": {},
        "Statespace Stats": {},
        "Memory Usage": {},
        "Unreached Code": [],
        "Elapsed Time": "",
        "Final Status": ""
    }
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('spin -a') or 'gcc' in line or './pan' in line:
                    data["Compilation Commands"].append(line.strip())

                if 'Partial Order Reduction' in line:
                    data["Settings Used"].append("Partial Order Reduction enabled")

                if 'never claim' in line:
                    data["Verification Checks"]["never_claim"] = '+' in line
                if 'assertion violations' in line:
                    data["Verification Checks"]["assertion_violations"] = '+' in line
                if 'non-progress cycles' in line:
                    data["Verification Checks"]["non_progress_cycles"] = '+' in line
                if 'invalid end states' in line:
                    data["Verification Checks"]["invalid_end_states"] = '+' in line

                if "State-vector" in line:
                    match = re.search(r'State-vector (\d+) byte, depth reached (\d+), errors: (\d+)', line)
                    if match:
                        data["Statespace Stats"]["state_vector_size"] = int(match.group(1))
                        data["Statespace Stats"]["depth_reached"] = int(match.group(2))
                        data["Statespace Stats"]["errors"] = int(match.group(3))
                if "states, stored" in line:
                    nums = list(map(int, re.findall(r'\d+', line)))
                    if len(nums) >= 2:
                        data["Statespace Stats"]["states_stored"] = nums[0]
                        data["Statespace Stats"]["states_visited"] = nums[1]
                if "states, matched" in line:
                    nums = re.findall(r'\d+', line)
                    if nums:
                        data["Statespace Stats"]["states_matched"] = int(nums[0])
                if "transitions" in line:
                    nums = re.findall(r'\d+', line)
                    if nums:
                        data["Statespace Stats"]["transitions"] = int(nums[0])
                if "atomic steps" in line:
                    nums = re.findall(r'\d+', line)
                    if nums:
                        data["Statespace Stats"]["atomic_steps"] = int(nums[0])
                if "hash conflicts" in line:
                    nums = re.findall(r'\d+', line)
                    if nums:
                        data["Statespace Stats"]["hash_conflicts"] = int(nums[0])

                if "memory used" in line or "memory usage" in line:
                    match = re.findall(r'([0-9\.]+)\s+memory used for ([^\(]+)', line)
                    for value, key in match:
                        data["Memory Usage"][key.strip()] = float(value)

                if "unreached in proctype" in line or "unreached in init" in line:
                    data["Unreached Code"].append(line.strip())

                if "elapsed time" in line:
                    match = re.search(r'elapsed time ([\d\.]+) seconds', line)
                    if match:
                        data["Elapsed Time"] = match.group(1) + " seconds"

                if "No errors found" in line or "errors found" in line:
                    data["Final Status"] = line.strip()
    except Exception as e:
        print(f"Error parsing file: {e}")

    return data


def find_out_file(directory):
    try:
        for filename in os.listdir(directory):
            if filename.endswith(".out"):
                return os.path.join(directory, filename)
    except FileNotFoundError:
        pass
    return None


class ExpandableSection(QGroupBox):
    def __init__(self, title, content_text):
        super().__init__()
        self.setTitle(title)
        self.setCheckable(True)
        self.setChecked(False)

        layout = QVBoxLayout()
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setPlainText(content_text)
        self.text_area.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.text_area.setMaximumHeight(150)

        layout.addWidget(self.text_area)
        self.setLayout(layout)

        self.toggled.connect(self.toggle_content)
        self.toggle_content(self.isChecked())

    def toggle_content(self, checked):
        self.text_area.setVisible(checked)


class SpinOutViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPIN .out File Viewer")
        self.resize(1000, 700)

        app.setStyleSheet("""
            QWidget {
                background-color: #f9f9fc;
                font-family: "Segoe UI";
                font-size: 10pt;
                color: #333;
            }

            QPushButton {
                background-color: #4285F4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }

            QPushButton#ClearButton {
                background-color: #DB4437;
            }

            QPushButton:hover {
                background-color: #357ae8;
            }

            QPushButton#ClearButton:hover {
                background-color: #c23321;
            }

            QGroupBox {
                border: 1px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background: transparent;
            }

            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 4px;
                background-color: #fff;
            }

            QLabel {
                font-weight: bold;
                margin: 10px 0 5px 0;
            }

            QScrollArea {
                border: none;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        btn_layout = QHBoxLayout()
        self.open_all_btn = QPushButton("Open All")
        self.open_all_btn.setObjectName("OpenAll")
        self.close_all_btn = QPushButton("Close All")
        self.close_all_btn.setObjectName("CloseAll")
        btn_layout.addWidget(self.open_all_btn)
        btn_layout.addWidget(self.close_all_btn)
        main_layout.addLayout(btn_layout)

        data_folder = os.path.join(os.getcwd(), "data")
        out_file = find_out_file(data_folder)

        if not out_file:
            msg = QLabel("No .out file found in the 'data' folder.")
            main_layout.addWidget(msg)
        else:
            parsed_data = parse_spin_output(out_file)
            self.sections = {}
            sections_data = {}

            sections_data["Compilation Commands"] = "\n".join(parsed_data["Compilation Commands"]) or "None"
            sections_data["Settings Used"] = "\n".join(parsed_data["Settings Used"]) or "None"

            if parsed_data["Verification Checks"]:
                checks_lines = []
                for k, v in parsed_data["Verification Checks"].items():
                    status = "Passed" if v else "Failed"
                    checks_lines.append(f"{k}: {status}")
                sections_data["Verification Checks"] = "\n".join(checks_lines)
            else:
                sections_data["Verification Checks"] = "None"

            if parsed_data["Statespace Stats"]:
                stats_lines = []
                for k, v in parsed_data["Statespace Stats"].items():
                    stats_lines.append(f"{k}: {v}")
                sections_data["Statespace Stats"] = "\n".join(stats_lines)
            else:
                sections_data["Statespace Stats"] = "None"

            if parsed_data["Memory Usage"]:
                mem_lines = []
                for k, v in parsed_data["Memory Usage"].items():
                    mem_lines.append(f"{k}: {v} units")
                sections_data["Memory Usage"] = "\n".join(mem_lines)
            else:
                sections_data["Memory Usage"] = "None"

            sections_data["Unreached Code"] = "\n".join(parsed_data["Unreached Code"]) or "None"
            sections_data["Elapsed Time"] = parsed_data["Elapsed Time"] or "Unknown"
            sections_data["Final Status"] = parsed_data["Final Status"] or "Unknown"

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content_widget = QWidget()
            content_layout = QVBoxLayout()

            for title, text in sections_data.items():
                section = ExpandableSection(title, text)
                self.sections[title] = section
                content_layout.addWidget(section)

            # ----- Charts Side-by-Side -----
            if parsed_data["Memory Usage"] or parsed_data["Statespace Stats"]:
                chart_layout = QHBoxLayout()

                if parsed_data["Memory Usage"]:
                    pie_view = QGraphicsView()
                    pie_scene = QGraphicsScene()
                    pie_view.setScene(pie_scene)
                    self.draw_piechart(pie_scene, parsed_data["Memory Usage"], 150, 150, 100)
                    chart_layout.addWidget(pie_view)

                if parsed_data["Statespace Stats"]:
                    bar_view = QGraphicsView()
                    bar_scene = QGraphicsScene()
                    bar_view.setScene(bar_scene)
                    self.draw_barchart(bar_scene, parsed_data["Statespace Stats"])
                    chart_layout.addWidget(bar_view)

                chart_container = QWidget()
                chart_container.setLayout(chart_layout)
                content_layout.addWidget(QLabel("Visualizations:"))
                content_layout.addWidget(chart_container)
            # -------------------------------

            content_widget.setLayout(content_layout)
            scroll.setWidget(content_widget)
            main_layout.addWidget(scroll)

            self.open_all_btn.clicked.connect(self.open_all)
            self.close_all_btn.clicked.connect(self.close_all)

        self.setLayout(main_layout)

    def open_all(self):
        for section in self.sections.values():
            section.setChecked(True)

    def close_all(self):
        for section in self.sections.values():
            section.setChecked(False)

    def draw_piechart(self, scene, memory_dict, center_x, center_y, radius):
        total = sum(memory_dict.values())
        if total == 0:
            return

        start_angle = 0
        colors = ["#c44", "#4c4", "#44c", "#cc4", "#4cc", "#c4c"]
        for i, (key, value) in enumerate(memory_dict.items()):
            angle_span = 360 * (value / total)
            slice_item = scene.addEllipse(
                QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2),
                QPen(Qt.GlobalColor.black),
                QBrush(QColor(colors[i % len(colors)]))
            )
            slice_item.setStartAngle(int(start_angle * 16))
            slice_item.setSpanAngle(int(angle_span * 16))

            label = QGraphicsTextItem(f"{key}: {value:.1f}")
            label.setPos(center_x + radius + 20, center_y - radius + i * 20)
            scene.addItem(label)

            start_angle += angle_span

    def draw_barchart(self, scene, stats, start_x=50, start_y=300, max_height=200):
        scene.clear()
        bar_width = 40
        spacing = 30
        max_value = max(stats.values()) if stats else 1
        scale = max_height / max_value if max_value != 0 else 1

        label_aliases = {
            "state_vector_size": "VecSize",
            "depth_reached": "Depth",
            "errors": "Errors",
            "states_stored": "Stored",
            "states_visited": "Visited",
            "states_matched": "Matched",
            "transitions": "Trans",
            "atomic_steps": "Atomic",
            "hash_conflicts": "Conflicts"
        }

        x = start_x
        for i, (label, value) in enumerate(stats.items()):
            height = value * scale
            rect = QGraphicsRectItem(x, start_y - height, bar_width, height)
            rect.setBrush(QBrush(QColor("#5a9")))
            rect.setPen(QPen(Qt.GlobalColor.black))
            scene.addItem(rect)

            short_label = label_aliases.get(label, label)
            label_item = QGraphicsTextItem(f"{short_label}\n{value}")
            label_item.setPos(x - 5, start_y + 5)
            label_item.setTextWidth(bar_width + 10)
            scene.addItem(label_item)

            x += bar_width + spacing


def main():
    global app
    app = QApplication(sys.argv)
    viewer = SpinOutViewer()
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
