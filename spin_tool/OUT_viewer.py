import sys
import os
import re
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit,
    QPushButton, QScrollArea, QGroupBox, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt

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
        self.text_area.setMaximumHeight(150)  # Limit height

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
        self.resize(800, 600)

        main_layout = QVBoxLayout()

        # Buttons for open all / close all
        btn_layout = QHBoxLayout()
        self.open_all_btn = QPushButton("Open All")
        self.close_all_btn = QPushButton("Close All")
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

            # Prepare display texts per section
            self.sections = {}

            sections_data = {}

            # Compilation Commands
            sections_data["Compilation Commands"] = "\n".join(parsed_data["Compilation Commands"]) or "None"

            # Settings Used
            sections_data["Settings Used"] = "\n".join(parsed_data["Settings Used"]) or "None"

            # Verification Checks
            if parsed_data["Verification Checks"]:
                checks_lines = []
                for k, v in parsed_data["Verification Checks"].items():
                    status = "Passed" if v else "Failed"
                    checks_lines.append(f"{k}: {status}")
                sections_data["Verification Checks"] = "\n".join(checks_lines)
            else:
                sections_data["Verification Checks"] = "None"

            # Statespace Stats
            if parsed_data["Statespace Stats"]:
                stats_lines = []
                for k, v in parsed_data["Statespace Stats"].items():
                    stats_lines.append(f"{k}: {v}")
                sections_data["Statespace Stats"] = "\n".join(stats_lines)
            else:
                sections_data["Statespace Stats"] = "None"

            # Memory Usage
            if parsed_data["Memory Usage"]:
                mem_lines = []
                for k, v in parsed_data["Memory Usage"].items():
                    mem_lines.append(f"{k}: {v} units")
                sections_data["Memory Usage"] = "\n".join(mem_lines)
            else:
                sections_data["Memory Usage"] = "None"

            # Unreached Code
            sections_data["Unreached Code"] = "\n".join(parsed_data["Unreached Code"]) or "None"

            # Elapsed Time
            sections_data["Elapsed Time"] = parsed_data["Elapsed Time"] or "Unknown"

            # Final Status
            sections_data["Final Status"] = parsed_data["Final Status"] or "Unknown"

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content_widget = QWidget()
            content_layout = QVBoxLayout()

            for title, text in sections_data.items():
                section = ExpandableSection(title, text)
                self.sections[title] = section
                content_layout.addWidget(section)

            content_widget.setLayout(content_layout)
            scroll.setWidget(content_widget)
            main_layout.addWidget(scroll)

            # Connect buttons
            self.open_all_btn.clicked.connect(self.open_all)
            self.close_all_btn.clicked.connect(self.close_all)

        self.setLayout(main_layout)

    def open_all(self):
        for section in self.sections.values():
            section.setChecked(True)

    def close_all(self):
        for section in self.sections.values():
            section.setChecked(False)

def main():
    app = QApplication(sys.argv)
    viewer = SpinOutViewer()
    viewer.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
