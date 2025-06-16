import os
import re
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea,
    QMainWindow, QPushButton
)
from PyQt6.QtCore import Qt

DATA_DIR = './data'  # Adjust if needed

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

    # Assertion violation
    m = re.search(r'spin: .*:(\d+), Error: assertion violated.*assert\((.*?)\)', text)
    if m:
        line, cond = m.groups()
        return {'type': 'assert', 'line': int(line), 'condition': cond.strip()}

    # Deadlock
    if "pan: deadlock detected" in text:
        return {'type': 'deadlock'}

    # Invalid end state
    if "invalid end state" in text:
        m = re.search(r'invalid end state \(at depth (\d+)\)', text)
        depth = int(m.group(1)) if m else None
        return {'type': 'invalid_end', 'depth': depth}

    # Unmatched send/receive
    if "unmatched receive" in text or "invalid read of message" in text:
        return {'type': 'unmatched_comm'}

    # Never claim
    if "never claim violated" in text:
        return {'type': 'never_claim'}

    return None

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

    for i, line in enumerate(sim_lines):
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

class ErrorViewer(QMainWindow):
    EXPLANATIONS = {
        'assert': ("An assertion failed during the simulation. This means that a condition "
                   "specified in the model was violated, indicating a potential bug or invalid state."),
        'deadlock': ("A deadlock was detected, meaning that the system reached a state where "
                     "no further progress is possible because processes are waiting indefinitely."),
        'invalid_end': ("The model reached an invalid end state, which may indicate unfinished processes "
                        "or unexpected termination. Depth indicates how deep in the state space this occurred."),
        'unmatched_comm': ("An unmatched send/receive error was found, suggesting that a message "
                          "was sent or expected but never properly received, leading to communication mismatch."),
        'never_claim': ("A 'never claim' violation was detected. This means a property specified to never "
                       "occur was actually violated, indicating a safety or liveness property failure.")
    }

    def __init__(self, error, sim_lines, causal_steps=None, line_number=None, condition=None):
        super().__init__()
        self.setWindowTitle("SPIN Error Viewer")
        self.setGeometry(100, 100, 900, 700)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        # Title Label
        err_title = {
            'assert': f"Assertion Failed: <code>{condition}</code> at Line {line_number}" if condition else "Assertion Failed",
            'deadlock': "🛑 Deadlock Detected",
            'invalid_end': f"⚠ Invalid End State (depth {error.get('depth', 'unknown')})",
            'unmatched_comm': "❗ Unmatched Send/Receive Detected",
            'never_claim': "⛔ Never Claim Violated"
        }

        title = QLabel(f"<h2>{err_title.get(error['type'], 'Unknown Error')}</h2>")
        if error['type'] == 'assert':
            title.setStyleSheet("color: red;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Explanation
        explanation = self.EXPLANATIONS.get(error['type'], "No explanation available for this error.")
        expl_label = QLabel(f"<b>Explanation:</b> {explanation}")
        expl_label.setWordWrap(True)
        layout.addWidget(expl_label)

        # If assertion error, show causal slice
        if error['type'] == 'assert' and causal_steps is not None:
            slice_label = QLabel("<b>Steps Leading to Error (Causal Slice):</b>")
            layout.addWidget(slice_label)

            steps_box = QTextEdit()
            steps_box.setReadOnly(True)
            steps_box.setFontFamily("Courier")
            for step in causal_steps:
                if 'assert' in step or 'FAIL' in step:
                    steps_box.append(f"<span style='color:red'><b>{step}</b></span>")
                else:
                    steps_box.append(step)
            layout.addWidget(steps_box)

        # Toggle button for full simulation trace
        self.toggle_button = QPushButton("Show Full Simulation Trace")
        layout.addWidget(self.toggle_button)

        self.sim_box = QTextEdit()
        self.sim_box.setReadOnly(True)
        self.sim_box.setFontFamily("Courier")
        # Highlight causal steps if available
        for step in sim_lines:
            if causal_steps and any(cs in step for cs in causal_steps):
                self.sim_box.append(f"<span style='background-color: #ffffaa'>{step}</span>")
            else:
                self.sim_box.append(step)
        self.sim_box.setVisible(False)
        layout.addWidget(self.sim_box)

        self.toggle_button.clicked.connect(self.toggle_trace)

    def toggle_trace(self):
        visible = self.sim_box.isVisible()
        self.sim_box.setVisible(not visible)
        if visible:
            self.toggle_button.setText("Show Full Simulation Trace")
        else:
            self.toggle_button.setText("Hide Full Simulation Trace")

def main():
    trail_file, txt_file, out_file = find_files()
    if not (trail_file and txt_file and out_file):
        app = QApplication(sys.argv)
        msg = QMainWindow()
        msg.setWindowTitle("Missing Files")
        label = QLabel("Could not find required .trail, .txt, or .out files in /data.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setCentralWidget(label)
        msg.resize(500, 200)
        msg.show()
        sys.exit(app.exec())

    error = parse_out(out_file)
    if not error:
        app = QApplication(sys.argv)
        msg = QMainWindow()
        msg.setWindowTitle("No Known Error Found")
        label = QLabel("No assertion, deadlock, or other known failure found in .out file.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        msg.setCentralWidget(label)
        msg.resize(500, 200)
        msg.show()
        sys.exit(app.exec())

    sim_lines = extract_simulation(txt_file)

    app = QApplication(sys.argv)

    if error['type'] == 'assert':
        variable, value, causal_steps = get_causal_slice(sim_lines, error['condition'])
        viewer = ErrorViewer(error, sim_lines, causal_steps, error['line'], error['condition'])
        viewer.show()
        sys.exit(app.exec())

    else:
        viewer = ErrorViewer(error, sim_lines)
        viewer.show()
        sys.exit(app.exec())

if __name__ == '__main__':
    main()
