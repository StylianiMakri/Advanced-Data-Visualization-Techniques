import os
import re
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QMainWindow, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

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


def get_causal_slice(sim_lines, error_condition):
    causal_steps = []
    m_var = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)', error_condition)
    variable = m_var.group(1) if m_var else None
    last_value = None

    for line in sim_lines:
        if variable and re.search(rf'\b{variable}\b\s*=', line):
            causal_steps.append(line)
            val_match = re.search(r'=\s*(\S+)', line)
            if val_match:
                last_value = val_match.group(1)
        elif variable and re.search(rf'\b{variable}\b\s+from\b', line):
            causal_steps.append(line)
        elif 'assert' in line or 'FAIL' in line:
            causal_steps.append(line)

    return variable, last_value, causal_steps


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


class TimelineCanvas(FigureCanvas):
    def __init__(self, transitions, parent=None, width=6, height=3, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)
        self.draw_timeline(transitions)

    def draw_timeline(self, transitions):
        self.axes.clear()
        y_labels = {}
        y_pos = 0

        for _, proc, _ in transitions:
            if proc not in y_labels:
                y_labels[proc] = y_pos
                y_pos += 1

        for step, proc, action in transitions:
            self.axes.plot(step, y_labels[proc], 'o', color='blue')
            self.axes.text(step, y_labels[proc] + 0.1, f'{action}', fontsize=8, ha='center')

        self.axes.set_yticks(list(y_labels.values()))
        self.axes.set_yticklabels([f'proc {p}' for p in y_labels.keys()])
        self.axes.set_xlabel("Step")
        self.axes.set_title("Execution Timeline")
        self.axes.grid(True)
        self.figure.tight_layout()
        self.draw()


from PyQt6.QtGui import QFont

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
        self.setGeometry(100, 100, 1000, 800)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(1)             # less spacing between widgets
        layout.setContentsMargins(2, 2, 2, 2)  # reduce margins
        self.setCentralWidget(central)

        title_font = QFont()
        title_font.setPointSize(14)      # smaller title font
        title_font.setBold(True)

        expl_font = QFont()
        expl_font.setPointSize(10)        # smaller explanation font

        for error in errors:
            err_title = {
                'assert': f"❗ Assertion Failed at Line {error.get('line', 'none')}: <code>{error.get('condition', 'none')}</code>",
                'deadlock': "🛑 Deadlock Detected",
                'invalid_end': f"⚠ Invalid End State (depth {error.get('depth', '?')})",
                'unmatched_comm': "❗ Unmatched Communication Detected",
                'never_claim': "⛔ Never Claim Violated"
            }
            title = QLabel(err_title.get(error['type'], 'Unknown Error'))
            title.setFont(title_font)
            title.setTextFormat(Qt.TextFormat.PlainText)  # remove html tags like <h3>
            title.setAlignment(Qt.AlignmentFlag.AlignLeft)
            title.setContentsMargins(0,0,0,0)
            title.setContentsMargins(0,0,0,0)
            layout.addWidget(title)

            expl = self.EXPLANATIONS.get(error['type'], "Unknown error.")
            expl_label = QLabel(f"Explanation: {expl}")
            expl_label.setFont(expl_font)
            expl_label.setWordWrap(True)
            expl_label.setContentsMargins(0, 0, 0, 1)  # small bottom margin
            expl_label.setStyleSheet("margin-top: 1px;")
            layout.addWidget(expl_label)

            layout.setSpacing(1)

        # Timeline
        canvas = TimelineCanvas(transitions, width=8, height=3)
        layout.addWidget(canvas)

        # Show full simulation button
        self.toggle_button = QPushButton("Show Full Simulation Trace")
        layout.addWidget(self.toggle_button)

        self.sim_box = QTextEdit()
        self.sim_box.setReadOnly(True)
        self.sim_box.setFontFamily("Courier")
        self.sim_box.setVisible(False)
        layout.addWidget(self.sim_box)

        self.toggle_button.clicked.connect(lambda: self.toggle_trace(sim_lines))

    def toggle_trace(self, sim_lines):
        visible = self.sim_box.isVisible()
        if not visible:
            self.sim_box.clear()
            for line in sim_lines:
                self.sim_box.append(line)
        self.sim_box.setVisible(not visible)
        self.toggle_button.setText("Hide Full Simulation Trace" if not visible else "Show Full Simulation Trace")



def main():
    trail_file, txt_file, out_file = find_files()
    if not all([trail_file, txt_file, out_file]):
        app = QApplication(sys.argv)
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
        app = QApplication(sys.argv)
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

    app = QApplication(sys.argv)
    win = ErrorViewer(errors, sim_lines, transitions)
    win.show()
    sys.exit(app.exec())



if __name__ == '__main__':
    main()
