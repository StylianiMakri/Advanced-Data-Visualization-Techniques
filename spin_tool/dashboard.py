from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox, QFrame, QTextEdit, QGroupBox, QSizePolicy
)
from PyQt6.QtCore import Qt
import os
import shutil
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

DATA_EXTENSIONS = {".out", ".trail", ".pml", ".isf", ".txt"}
OUTPUT_EXTENSIONS = {".json", ".png"}


def delete_files_by_extension(folder, extensions):
    if not os.path.exists(folder):
        return
    for f in os.listdir(folder):
        if os.path.splitext(f)[1].lower() in extensions:
            try:
                os.remove(os.path.join(folder, f))
            except Exception as e:
                QMessageBox.warning(None, "Warning", f"Could not delete {f}: {e}")


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SPIN Tool Dashboard")
        self.setGeometry(100, 100, 500, 600)
        self.setup_ui()
        self.update_data_files_display()

    def setup_ui(self):
        self.setStyleSheet("font-family: Segoe UI, sans-serif; font-size: 10pt; background-color: #f9f9f9;")
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(QLabel("File Operations"))
        file_layout = QHBoxLayout()
        upload_btn = self.styled_button("Upload Files", "#7dcb5b", "#368a3f")
        upload_btn.clicked.connect(self.upload_files)
        file_layout.addWidget(upload_btn)

        clear_btn = self.styled_button("Clear Files", "#e74c3c", "#c0392b")
        clear_btn.clicked.connect(self.clear_data_and_output)
        file_layout.addWidget(clear_btn)
        main_layout.addLayout(file_layout)
        main_layout.addWidget(self.make_line())

        parser_label = QLabel("Run Parser")
        parser_label.setStyleSheet("font-size: 10pt; margin-top: 10px;")
        main_layout.addWidget(parser_label)

        parser_btn = self.styled_button("Run Parser Module", "#8ad5e6", "#369095", large=True)
        parser_btn.clicked.connect(self.run_parsers)
        main_layout.addWidget(parser_btn)

        main_layout.addWidget(self.make_line())

        module_group = QGroupBox("Analysis Modules")
        module_layout = QVBoxLayout()
        rows = [
            [("Visualizer", "vizualizer_module.py"), ("Timeline", "timeline_evolved.py")],
            [("MSC Maker", "msc_maker_80.py"), ("Overview", "overview.py")],
            [("Out Viewer", "OUT_viewer.py"), ("Why it Failed", "why_it_failed.py")]
        ]
        for row in rows:
            row_layout = QHBoxLayout()
            for label, script in row:
                btn = self.styled_button(label)
                btn.clicked.connect(lambda _, s=script: self.run_script(s))
                row_layout.addWidget(btn)
            module_layout.addLayout(row_layout)
        module_group.setLayout(module_layout)
        main_layout.addWidget(module_group)
        main_layout.addWidget(self.make_line())

        main_layout.addWidget(QLabel("Files in /data:"))
        self.file_display = QTextEdit()
        self.file_display.setReadOnly(True)
        self.file_display.setFixedHeight(150)
        self.file_display.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; padding: 6px;")
        main_layout.addWidget(self.file_display)

    def styled_button(self, text, color="#fea94e", hover="#b96f20", large=False):
        font_size = "13pt" if large else "11pt"
        padding = "12px" if large else "8px"
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: black;
                font-weight: bold;
                font-size: {font_size};
                border: none;
                border-radius: 6px;
                padding: {padding};
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return btn

    def make_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select .trail, .pml, .isf and .out files", "",
            "All Files (*.trail *.pml *.out *.isf *.txt)"
        )
        if not files:
            return

        os.makedirs(DATA_DIR, exist_ok=True)
        for file in files:
            try:
                shutil.copy(file, DATA_DIR)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not copy file: {e}")

        QMessageBox.information(self, "Success", "Files uploaded to 'data' folder")
        self.update_data_files_display()

    def run_parsers(self):
        try:
            self.run_script("parser_module.py")
            self.run_script("parser_msc.py")
        except Exception as e:
            print(f"Error running parsers: {e}")


    def update_data_files_display(self):
        if not os.path.exists(DATA_DIR):
            self.file_display.setPlainText("No files in /data.")
            return

        files = [
            f for f in os.listdir(DATA_DIR)
            if os.path.splitext(f)[1].lower() in DATA_EXTENSIONS
        ]
        self.file_display.setPlainText("\n".join(sorted(files)) if files else "No files selected.")

    def clear_data_and_output(self):
        delete_files_by_extension(DATA_DIR, DATA_EXTENSIONS)
        delete_files_by_extension(OUTPUT_DIR, OUTPUT_EXTENSIONS)
        QMessageBox.information(self, "Cleared", "Data and output files cleared.")
        self.update_data_files_display()

    def run_script(self, script_name):
        try:
            subprocess.Popen([sys.executable, script_name])
            QMessageBox.information(self, "Success", f"{script_name} launched successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {script_name}:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
