

import sys
import shutil
import subprocess
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

# === Constants ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

DATA_EXTENSIONS = {".out", ".trail", ".pml", ".isf", ".txt"}
OUTPUT_EXTENSIONS = {".json", ".png"}


def delete_files_by_extension(folder, extensions):
    """Delete all files in a folder that match the given extensions."""
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
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 400, 350)

        self.setup_ui()
        self.update_data_files_display()

    def setup_ui(self):
        """Initialize and lay out all UI widgets."""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Upload your .trail, .pml, .out and .isf files")
        self.layout.addWidget(self.label)
        self.layout.addSpacing(10)

        self.layout.addWidget(self.make_line())

        self.data_files_label = QLabel("Current files in /data:")
        self.layout.addWidget(self.data_files_label)

        # Upload + Module Buttons
        buttons = [
            ("Upload Files", self.upload_files),
            ("Run Parser Module", lambda: self.run_script("parser_module.py")),
            ("Run Vizualizer Module", lambda: self.run_script("vizualizer_module.py")),
            ("Run Process Timeline Module", lambda: self.run_script("timeline_evolved.py")),
            ("Run MSC Maker Module", lambda: self.run_script("msc_maker.py")),
            ("Run Stats Overview Module", lambda: self.run_script("overview.py")),
            ("Run .out Viewer Module", lambda: self.run_script("OUT_viewer.py")),
            ("Why it Failed", lambda: self.run_script("why_it_failed.py")),
        ]

        for text, func in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(func)
            self.layout.addWidget(btn)

        self.layout.addSpacing(10)
        self.layout.addWidget(self.make_line())

        self.clear_button = QPushButton("Clear Uploaded Data")
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """
        )
        self.clear_button.clicked.connect(self.clear_data_and_output)
        self.layout.addWidget(self.clear_button)

    def make_line(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def upload_files(self):
        """Prompt user to upload files to /data directory."""
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
        """Update file list label to show files in /data."""
        if not os.path.exists(DATA_DIR):
            self.data_files_label.setText("No files in /data.")
            return

        files = [
            f for f in os.listdir(DATA_DIR)
            if os.path.splitext(f)[1].lower() in DATA_EXTENSIONS
        ]
        if files:
            self.data_files_label.setText("Uploaded Files :\n" + "\n".join(sorted(files)))
        else:
            self.data_files_label.setText("No files selected.")

    def clear_data_and_output(self):
        """Delete relevant files in data and output folders."""
        delete_files_by_extension(DATA_DIR, DATA_EXTENSIONS)
        delete_files_by_extension(OUTPUT_DIR, OUTPUT_EXTENSIONS)
        QMessageBox.information(self, "Cleared", "Data and output files cleared.")
        self.update_data_files_display()

    def run_script(self, script_name):
        """Launch an external Python script as a subprocess."""
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
