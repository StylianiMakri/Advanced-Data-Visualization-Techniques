import os
import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QMainWindow, QPushButton, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QWheelEvent, QPainter

DATA_JSON = './output/parsed_data.json'
DATA_DIR = './data'


def load_parsed_json(json_path):
    if not os.path.exists(json_path):
        return None, None
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data.get('trail', []), data.get('errors', [])


def extract_simulation(txt_path):
    """Exactly your original simulation extraction logic"""
    with open(txt_path, 'r') as f:
        lines = f.readlines()
    in_sim = False
    sim_lines = []
    for line in lines:
        if '===start Sim===' in line:
            in_sim = True
            continue
        elif '===end Sim===' in line:
            break
        elif in_sim:
            sim_lines.append(line.rstrip('\n'))
    return sim_lines


class TimelineWidget(QGraphicsView):
    def __init__(self, transitions, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.draw_timeline(transitions)

    def draw_timeline(self, transitions):
        self.scene.clear()
        y_map = {}
        y_spacing = 50
        dot_radius = 4

        # Map proc_id to y positions
        for t in transitions:
            proc = t['proc_id']
            if proc not in y_map:
                y_map[proc] = len(y_map)

        max_step = max((t['step'] for t in transitions), default=0)
        max_x = max_step * 20 + 100
        max_y = len(y_map) * y_spacing

        # Vertical grid lines
        for step in range(0, max_step + 1, 5):
            x = step * 20
            line = self.scene.addLine(x, -20, x, max_y, QPen(QColor("#dddddd")))
            line.setZValue(-1)

        # Horizontal process lines
        for _, y_index in y_map.items():
            y = y_index * y_spacing
            line = self.scene.addLine(-80, y, max_x, y, QPen(QColor("#ddddddd6")))
            line.setZValue(-1)

        # Draw timeline dots
        for idx, t in enumerate(transitions, start=1):
            step = t['step']
            proc = t['proc_id']
            x = step * 20
            y = y_map[proc] * y_spacing

            is_last = idx == len(transitions)
            color = QColor("red") if is_last else QColor("blue")

            dot = QGraphicsEllipseItem(QRectF(x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2))
            dot.setBrush(QBrush(color))
            dot.setPen(QPen(Qt.GlobalColor.black))
            self.scene.addItem(dot)

            label = QGraphicsTextItem(str(idx))
            label.setDefaultTextColor(Qt.GlobalColor.darkGray)
            label.setPos(x - 5, y - 20)
            self.scene.addItem(label)

        # Process labels
        for proc, idx in y_map.items():
            label = QGraphicsTextItem(f"proc {proc}")
            label.setDefaultTextColor(Qt.GlobalColor.black)
            label.setPos(-70, idx * y_spacing - 6)
            self.scene.addItem(label)

        self.scene.setSceneRect(-80, -30, max_x + 150, max_y + 60)

    def wheelEvent(self, event: QWheelEvent):
        zoom = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(zoom, 1)


class ErrorViewer(QMainWindow):
    EXPLANATIONS = {
        'assertion violated': "An assertion in the model was violated, indicating a serious correctness problem.",
        'deadlock': "The system reached a deadlock where no process could proceed.",
        'invalid end state': "The model ended in a state where not all processes were properly terminated.",
        'unmatched_comm': "A send or receive had no matching partner, showing a communication issue.",
        'never_claim': "A never claim property was violated, breaking a specified safety/liveness condition."
    }

    def __init__(self, errors, trail, sim_lines):
        super().__init__()
        self.setWindowTitle("SPIN Error Viewer")
        self.setGeometry(100, 100, 900, 700)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setCentralWidget(central)

        title_font = QFont("Arial", 11, QFont.Weight.Bold)
        expl_font = QFont("Arial", 9)

        # Display errors
        for error in errors:
            err_type = error.get('type', 'unknown')
            msg = error.get('message', '')
            depth = error.get('depth')

            title_text = {
                'assertion violated': f"❗ Assertion Failed: {msg}",
                'deadlock': "❗ Deadlock Detected",
                'invalid end state': f"❗ Invalid End State (depth {depth or '?'})",
                'unmatched_comm': "❗ Unmatched Communication Detected",
                'never_claim': "❗ Never Claim Violated"
            }.get(err_type, msg)

            title = QLabel(title_text)
            title.setFont(title_font)
            title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            title.setStyleSheet("margin:0px; padding:0px; line-height:90%;")
            layout.addWidget(title)

            expl = self.EXPLANATIONS.get(err_type, "Unknown error.")
            expl_label = QLabel(expl)
            expl_label.setFont(expl_font)
            expl_label.setWordWrap(True)
            expl_label.setStyleSheet("margin:0px; padding:0px; line-height:90%; color: #444;")
            layout.addWidget(expl_label)

        # Timeline
        timeline = TimelineWidget(trail)
        timeline.setMinimumHeight(200)
        layout.addWidget(timeline)

        # Simulation trace
        self.toggle_button = QPushButton("Show Full Simulation Trace")
        self.toggle_button.setStyleSheet("margin:4px; padding:4px;")
        layout.addWidget(self.toggle_button)

        self.sim_box = QTextEdit()
        self.sim_box.setReadOnly(True)
        self.sim_box.setFontFamily("Courier")
        self.sim_box.setFontPointSize(9)
        self.sim_box.setVisible(False)
        self.sim_box.setStyleSheet("margin:0px; padding:2px;")
        layout.addWidget(self.sim_box)

        self.sim_lines = sim_lines

        self.toggle_button.clicked.connect(self.toggle_trace)

    def toggle_trace(self):
        visible = self.sim_box.isVisible()
        if not visible:
            self.sim_box.clear()
            self.sim_box.append("\n".join(self.sim_lines))
        self.sim_box.setVisible(not visible)
        self.toggle_button.setText(
            "Hide Full Simulation Trace" if not visible else "Show Full Simulation Trace"
        )


def main():
    trail, errors = load_parsed_json(DATA_JSON)

    # Find txt file for simulation extraction
    txt_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.txt')]
    if txt_files:
        txt_path = os.path.join(DATA_DIR, txt_files[0])
        sim_lines = extract_simulation(txt_path)
    else:
        sim_lines = []

    app = QApplication(sys.argv)

    if not trail or not errors:
        win = QMainWindow()
        win.setWindowTitle("Missing Data")
        lbl = QLabel(f"Could not load data from {DATA_JSON}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        win.setCentralWidget(lbl)
        win.resize(500, 200)
        win.show()
        sys.exit(app.exec())

    win = ErrorViewer(errors, trail, sim_lines)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
