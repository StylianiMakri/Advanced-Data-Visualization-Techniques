#hi

import sys
import json
import csv
import re
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QLabel,
    QLineEdit, QPushButton, QHBoxLayout, QHeaderView, QTextEdit, QMessageBox, QFileDialog, QListWidget, QSplitter
)
from PyQt6.QtGui import QColor, QFont, QAction
from PyQt6.QtCore import Qt

DATA_DIR = "data"

class StepDetailDialog(QMessageBox):
    def __init__(self, step):
        super().__init__()
        self.setWindowTitle(f"Details for Step {step.get('step', '')}")
        text = "\n".join(f"{k}: {v}" for k, v in step.items())
        self.setText(text)
        self.setStandardButtons(QMessageBox.StandardButton.Ok)


class SpinVisualizer(QWidget):
    def __init__(self, parsed_data):
        super().__init__()
        self.setWindowTitle("SPIN Execution Timeline Visualizer")
        self.resize(1000, 700)

        self.data = parsed_data
        self.trail = self.data.get("trail", [])
        self.errors_raw = self.data.get("errors", [])
        self.load_pml_lines()


        # Parse errors into dict with optional step info
        self.errors = []
        for err in self.errors_raw:
            # If error is string, try to parse step number
            if isinstance(err, str):
                step = None
                match = re.search(r"step\s*(\d+)", err, re.IGNORECASE)
                if match:
                    step = int(match.group(1))
                self.errors.append({"message": err, "step": step})
            elif isinstance(err, dict):
                self.errors.append(err)
            else:
                self.errors.append({"message": str(err), "step": None})

        layout = QVBoxLayout()

        # Search bar and export buttons
        search_layout = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter by any text in Step, Process, Line, or Action")
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)

        # Export buttons
        self.export_csv_btn = QPushButton("Export CSV")
        self.export_csv_btn.clicked.connect(self.export_csv)
        self.export_html_btn = QPushButton("Export HTML")
        self.export_html_btn.clicked.connect(self.export_html)
        search_layout.addWidget(self.export_csv_btn)
        search_layout.addWidget(self.export_html_btn)

        layout.addLayout(search_layout)

        # Splitter to separate timeline table and errors/context
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Timeline Table
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Step", "Process", "Line", "Action", "Code"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.cellDoubleClicked.connect(self.show_step_details)

        splitter.addWidget(self.table)

        # Bottom widget for errors and context
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout()

        # Error list widget
        self.error_list = QListWidget()
        self.error_list.setMaximumHeight(150)
        error_label = QLabel("Errors Detected:")
        error_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        error_label.setStyleSheet("color: red;")
        bottom_layout.addWidget(error_label)
        bottom_layout.addWidget(self.error_list)

        # Error message display
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setStyleSheet("background: #ffeeee; color: darkred; font-family: Consolas;")
        self.error_text.setFixedHeight(100)
        bottom_layout.addWidget(self.error_text)

        bottom_widget.setLayout(bottom_layout)
        splitter.addWidget(bottom_widget)

        layout.addWidget(splitter, stretch=1)
        self.setLayout(layout)

        self.load_data()
        self.populate_error_list()

        self.error_list.currentItemChanged.connect(self.on_error_selected)

    def load_data(self):
        self.table.setRowCount(len(self.trail))

        colors = [
            QColor("#FFDDC1"),
            QColor("#C1FFD7"),
            QColor("#C1D4FF"),
            QColor("#FFD1DC"),
            QColor("#E6E6FA"),
            QColor("#FFFACD"),
            QColor("#D1FFD6"),
        ]

        for row, step in enumerate(self.trail):
            self.table.setItem(row, 0, QTableWidgetItem(str(step.get("step", ""))))
            proc_name = f'{step.get("proc_name", "")} (#{step.get("proc_id", "")})'
            proc_item = QTableWidgetItem(proc_name)
            color = colors[step.get("proc_id", 0) % len(colors)]
            proc_item.setBackground(color)
            self.table.setItem(row, 1, proc_item)

            self.table.setItem(row, 2, QTableWidgetItem(str(step.get("line", ""))))
            self.table.setItem(row, 3, QTableWidgetItem(step.get("action", "")))
            pml_line = self.get_pml_line(step.get("line", 0))
            self.table.setItem(row, 4, QTableWidgetItem(pml_line))

        # Populate error text with all errors
        if self.errors:
            # Show combined raw messages
            error_messages = [err["message"] for err in self.errors]
            self.error_text.setPlainText("\n".join(error_messages))
        else:
            self.error_text.setPlainText("No errors detected.")

    def find_pml_file(self):
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".pml"):
             return os.path.join(DATA_DIR, filename)
        return None
    
    def load_pml_lines(self):
        pml_path = self.find_pml_file()
        if not pml_path:
            print("No .pml file found in data directory.")
            self.pml_lines = []
            return
        try:
            with open(pml_path, "r") as f:
                self.pml_lines = f.readlines()
            print(f"Loaded {len(self.pml_lines)} lines from {pml_path}")
        except Exception as e:
            print(f"Failed to read .pml file: {e}")
            self.pml_lines = []

    def get_pml_line(self, line_number):
        if 1 <= line_number <= len(self.pml_lines):
            return self.pml_lines[line_number - 1].strip()
        return "[Invalid line number]"


    def filter_table(self):
        filter_text = self.search_input.text().lower()

        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and filter_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def show_step_details(self, row, column):
        step_num_item = self.table.item(row, 0)
        if not step_num_item:
            return
        try:
            step_num = int(step_num_item.text())
        except ValueError:
            return
        step = next((s for s in self.trail if s.get("step") == step_num), None)
        if step:
            dlg = StepDetailDialog(step)
            dlg.exec()

    def export_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Step", "Process", "Line", "Action"])
                for step in self.trail:
                    proc_name = f'{step.get("proc_name", "")} (#{step.get("proc_id", "")})'
                    writer.writerow([
                        step.get("step", ""),
                        proc_name,
                        step.get("line", ""),
                        step.get("action", "")
                    ])
            QMessageBox.information(self, "Export CSV", f"CSV exported successfully to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export CSV", f"Failed to export CSV:\n{e}")

    def export_html(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save HTML", "", "HTML Files (*.html *.htm)")
        if not path:
            return
        try:
            html = """
            <html><head><meta charset="UTF-8"><style>
            table {border-collapse: collapse; width: 100%;}
            th, td {border: 1px solid #999; padding: 0.5em; text-align: left;}
            th {background-color: #eee;}
            </style></head><body>
            <h2>SPIN Execution Timeline</h2>
            <table>
            <thead><tr><th>Step</th><th>Process</th><th>Line</th><th>Action</th></tr></thead>
            <tbody>
            """
            for step in self.trail:
                proc_name = f'{step.get("proc_name", "")} (#{step.get("proc_id", "")})'
                html += f"<tr><td>{step.get('step','')}</td><td>{proc_name}</td><td>{step.get('line','')}</td><td>{step.get('action','')}</td></tr>"
            html += """
            </tbody></table>
            <h3>Errors Detected:</h3>
            <pre style="color:red;">""" + "\n".join(err["message"].replace("<","&lt;").replace(">","&gt;") for err in self.errors) + "</pre>" + """
            </body></html>
            """
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            QMessageBox.information(self, "Export HTML", f"HTML exported successfully to:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "Export HTML", f"Failed to export HTML:\n{e}")

    def populate_error_list(self):
        self.error_list.clear()
        for err in self.errors:
            step_info = f"Step {err['step']}" if err['step'] is not None else "No step info"
            item_text = f"{step_info}: {err['message'][:80]}{'...' if len(err['message']) > 80 else ''}"
            self.error_list.addItem(item_text)

    def on_error_selected(self, current, previous):
        if current is None:
            self.error_text.clear()
            return
        idx = self.error_list.currentRow()
        err = self.errors[idx]
        self.error_text.setPlainText(err["message"])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    try:
        with open("output/parsed_data.json") as f:
            data = json.load(f)
    except Exception as e:
        data = {"trail": [], "errors": [f"Error loading data: {e}"]}

    window = SpinVisualizer(data)
    window.show()
    sys.exit(app.exec())