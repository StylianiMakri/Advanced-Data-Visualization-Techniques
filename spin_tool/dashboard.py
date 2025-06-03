import sys
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dashboard")
        self.setGeometry(100, 100, 400, 350)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Upload your .trail, .pml, .out and .isf files")
        self.layout.addWidget(self.label)

        self.upload_button = QPushButton("Upload Files")
        self.upload_button.clicked.connect(self.upload_files)
        self.layout.addWidget(self.upload_button)

        self.run_parser_button = QPushButton("Run Parser Module")
        self.run_parser_button.clicked.connect(self.run_parser)
        self.layout.addWidget(self.run_parser_button)

        self.run_visualizer_button = QPushButton("Run Vizualizer Module")
        self.run_visualizer_button.clicked.connect(self.run_visualizer)
        self.layout.addWidget(self.run_visualizer_button)

        self.sequence_btn = QPushButton("Run Process Timeline Module")
        self.sequence_btn.clicked.connect(self.run_sequence)
        self.layout.addWidget(self.sequence_btn)

        self.msc_maker_button = QPushButton("Run MSC Maker Module")
        self.msc_maker_button.clicked.connect(self.run_msc_maker)
        self.layout.addWidget(self.msc_maker_button)

        self.overview_btn = QPushButton("Run Overview Module")
        self.overview_btn.clicked.connect(self.run_overview)
        self.layout.addWidget(self.overview_btn)

        self.OUT_btn = QPushButton("Run .out viewer Module")
        self.OUT_btn.clicked.connect(self.run_OUT)
        self.layout.addWidget(self.OUT_btn)

        

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select .trail, .pml, and .out files",
            "", "All Files (*.trail *.pml *.out *.isf)"
        )
        if not files:
            return
        
        os.makedirs(DATA_DIR, exist_ok=True)
        for file in files:
            try:
                shutil.copy(file, DATA_DIR)
                print(f"Copied: {file} to {DATA_DIR}")  # Add debug print
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not copy file: {e}")
        QMessageBox.information(self, "Success", "Files uploaded to 'data folder'")

    def run_parser(self):
        self.run_script("parser_module.py")

    def run_overview(self):
        self.run_script("overview.py")

    def run_OUT(self):
        self.run_script("OUT_viewer.py")

    def run_visualizer(self):
        self.run_script("vizualizer_module_3.py")

    def run_sequence(self):
        self.run_script("sequence_module.py")

    def run_msc_maker(self):
        script_name = "msc_maker.py"
        try:
            subprocess.Popen([sys.executable, script_name])
            QMessageBox.information(self, "Success", f"{script_name} launched successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch {script_name}:\n{e}")

    def run_script(self, script_name):
        try:
            result = subprocess.run(
                [sys.executable, script_name],
                check=True,
                capture_output=True,
                text=True
            )
            QMessageBox.information(self, "Success", f"{script_name} ran successfully!")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"{script_name} failed:\n{e.stderr}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
