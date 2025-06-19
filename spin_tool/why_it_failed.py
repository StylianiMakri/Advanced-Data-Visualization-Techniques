import os
import re
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QMainWindow, QPushButton, QGraphicsView, QGraphicsScene,
    QGraphicsEllipseItem, QGraphicsTextItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QFont, QPen, QBrush, QColor, QWheelEvent, QPainter

DATA_DIR = './data'


def find_files():
    trail = txt = out = None
    for f in os.listdir(DATA_DIR):
        if f.endswith('.trail') and not trail:
            trail = os.path.join(DATA_DIR, f)
        elif f.endswith('.txt') and not txt:
            txt = os.path.join(DATA_DIR, f)
        elif f.endswith('.out') and not out:
            out = os.path.join(DATA_DIR, f)
    return trail, txt, out


def parse_out(out_path):
    with open(out_path, 'r') as f:
        text = f.read()

    errors = []

    m = re.search(r'pan:\d+:\s+assertion violated \((.*?)\)', text)
    if m:
        condition = m.group(1).strip()
        errors.append({'type': 'assert', 'line': None, 'condition': condition})

    if "pan: deadlock detected" in text:
        errors.append({'type': 'deadlock'})

    if "invalid end state" in text:
        m = re.search(r'invalid end state \(at depth (\d+)\)', text)
        depth = int(m.group(1)) if m else None
        errors.append({'type': 'invalid_end', 'depth': depth})

    if "unmatched receive" in text or "invalid read of message" in text:
        errors.append({'type': 'unmatched_comm'})

    if "never claim violated" in text:
        errors.append({'type': 'never_claim'})

    return errors


def extract_simulation(txt_path):
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


def parse_trail(trail_path):
    transitions = []
    with open(trail_path, 'r') as f:
        for line in f:
            parts = line.strip().split(':')
            if len(parts) != 3 or any(int(p) < 0 for p in parts):
                continue
            step, proc, action = map(int, parts)
            transitions.append((step, proc, action))
    return transitions


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

        for _, proc, _ in transitions:
            if proc not in y_map:
                y_map[proc] = len(y_map)

        max_step = max((step for step, _, _ in transitions), default=0)
        max_x = max_step * 20 + 100
        max_y = (len(y_map)) * y_spacing

        # Grid: Vertical step lines
        for step in range(0, max_step + 1, 5):  # every 5 steps
            x = step * 20
            line = self.scene.addLine(x, -20, x, max_y, QPen(QColor("#dddddd")))
            line.setZValue(-1)  # behind everything

        # Grid: Horizontal process lines
        for _, y_index in y_map.items():
            y = y_index * y_spacing
            line = self.scene.addLine(-80, y, max_x, y, QPen(QColor("#dddddd")))
            line.setZValue(-1)

        # Draw timeline points
        for step, proc, action in transitions:
            x = step * 20
            y = y_map[proc] * y_spacing

            dot = QGraphicsEllipseItem(QRectF(x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2))
            dot.setBrush(QBrush(QColor("blue")))
            dot.setPen(QPen(Qt.GlobalColor.black))
            self.scene.addItem(dot)

            label = QGraphicsTextItem(str(action))
            label.setDefaultTextColor(Qt.GlobalColor.darkGray)
            label.setPos(x - 5, y - 20)
            self.scene.addItem(label)

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
        'assert': "An assertion in the model was violated, indicating a serious correctness problem.",
        'deadlock': "The system reached a deadlock where no process could proceed.",
        'invalid_end': "The model ended in a state where not all processes were properly terminated.",
        'unmatched_comm': "A send or receive had no matching partner, showing a communication issue.",
        'never_claim': "A never claim property was violated, breaking a specified safety/liveness condition."
    }

    def __init__(self, errors, sim_lines, transitions):
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

        for error in errors:
            err_title = {
                'assert': f"❗ Assertion Failed: {error.get('condition', 'unknown')}",
                'deadlock': "🛑 Deadlock Detected",
                'invalid_end': f"⚠ Invalid End State (depth {error.get('depth', '?')})",
                'unmatched_comm': "❗ Unmatched Communication Detected",
                'never_claim': "⛔ Never Claim Violated"
            }
            title = QLabel(err_title.get(error['type'], 'Unknown Error'))
            title.setFont(title_font)
            title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
            title.setStyleSheet("margin:0px; padding:0px; line-height:90%;")
            layout.addWidget(title)

            expl = self.EXPLANATIONS.get(error['type'], "Unknown error.")
            expl_label = QLabel(expl)
            expl_label.setFont(expl_font)
            expl_label.setWordWrap(True)
            expl_label.setStyleSheet("margin:0px; padding:0px; line-height:90%; color: #444;")
            layout.addWidget(expl_label)

        timeline = TimelineWidget(transitions)
        timeline.setMinimumHeight(200)
        layout.addWidget(timeline)

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

        self.toggle_button.clicked.connect(lambda: self.toggle_trace(sim_lines))

    def toggle_trace(self, sim_lines):
        visible = self.sim_box.isVisible()
        if not visible:
            self.sim_box.clear()
            self.sim_box.append("\n".join(sim_lines))
        self.sim_box.setVisible(not visible)
        self.toggle_button.setText(
            "Hide Full Simulation Trace" if not visible else "Show Full Simulation Trace"
        )


def main():
    trail_file, txt_file, out_file = find_files()
    app = QApplication(sys.argv)

    if not all([trail_file, txt_file, out_file]):
        win = QMainWindow()
        win.setWindowTitle("Missing Files")
        lbl = QLabel("Required .trail, .txt, or .out files not found in /data.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        win.setCentralWidget(lbl)
        win.resize(500, 200)
        win.show()
        sys.exit(app.exec())

    errors = parse_out(out_file)
    if not errors:
        win = QMainWindow()
        win.setWindowTitle("No Known Error")
        lbl = QLabel("No error (assertion, deadlock, etc.) found in .out file.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        win.setCentralWidget(lbl)
        win.resize(500, 200)
        win.show()
        sys.exit(app.exec())

    sim_lines = extract_simulation(txt_file)
    transitions = parse_trail(trail_file)

    win = ErrorViewer(errors, sim_lines, transitions)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
