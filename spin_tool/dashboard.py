import sys
import shutil
import subprocess
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox, QFrame, QTextEdit
)
from PyQt6.QtCore import Qt

# === Constants ===
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
        self.setGeometry(100, 100, 450, 600)

        self.setup_ui()
        self.update_data_files_display()

    def setup_ui(self):
        self.setStyleSheet("font-family: Segoe UI, sans-serif; font-size: 11pt; background-color: #f9f9f9;")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Section label
        self.label = QLabel("Upload your .trail, .pml, .out and .isf files")
        self.label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #333; margin-top: 10px;")
        self.layout.addWidget(self.label)
        self.layout.addSpacing(10)

        self.layout.addWidget(self.make_line())

        self.file_display = QTextEdit()
        self.file_display.setReadOnly(True)
        self.file_display.setStyleSheet("background-color: #ffffff; border: 1px solid #ccc; padding: 6px;")
        self.layout.addWidget(self.file_display)

        buttons = [
            ("Upload Files", self.upload_files),
            ("Run Parser Module", lambda: self.run_script("parser_module.py")),
            ("Run Vizualizer Module", lambda: self.run_script("vizualizer_module.py")),
            ("Run Process Timeline", lambda: self.run_script("timeline_evolved.py")),
            ("Run MSC Maker", lambda: self.run_script("msc_maker.py")),
            ("Run Stats Overview", lambda: self.run_script("overview.py")),
            ("Run .out Viewer", lambda: self.run_script("OUT_viewer.py")),
            ("Why it Failed", lambda: self.run_script("why_it_failed.py")),
        ]

        for text, func in buttons:
            btn = self.styled_button(text)
            btn.clicked.connect(func)
            self.layout.addWidget(btn)

        self.layout.addSpacing(10)
        self.layout.addWidget(self.make_line())

        self.clear_button = self.styled_button("Clear Uploaded Data", "#e74c3c", "#c0392b")
        self.clear_button.clicked.connect(self.clear_data_and_output)
        self.layout.addWidget(self.clear_button)

    def styled_button(self, text, color="#f2d2b0", hover="#eac37c"):
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: black;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: {hover};
            }}
        """)
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

    def update_data_files_display(self):
        if not os.path.exists(DATA_DIR):
            self.file_display.setPlainText("No files in /data.")
            return

        files = [
            f for f in os.listdir(DATA_DIR)
            if os.path.splitext(f)[1].lower() in DATA_EXTENSIONS
        ]
        if files:
            self.file_display.setPlainText("\n".join(sorted(files)))
        else:
            self.file_display.setPlainText("No files selected.")

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
