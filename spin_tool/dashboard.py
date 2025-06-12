import sys
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox, QHBoxLayout, QTextEdit, QSizePolicy, QFrame
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
        self.layout.addSpacing(10) 
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)

        self.data_files_label = QLabel("Current files in /data:")
        self.layout.addWidget(self.data_files_label)
        self.update_data_files_display()

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

        self.layout.addSpacing(10) 
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self.layout.addWidget(line)

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
        """)
        self.clear_button.clicked.connect(self.clear_data_and_output)
        self.layout.addWidget(self.clear_button)


        
    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select .trail, .pml, .isf and .out files",
            "", "All Files (*.trail *.pml *.out *.isf)"
        )
        if not files:
            return
        
        os.makedirs(DATA_DIR, exist_ok=True)
        for file in files:
            try:
                shutil.copy(file, DATA_DIR)
                print(f"Copied: {file} to {DATA_DIR}") 
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not copy file: {e}")
        QMessageBox.information(self, "Success", "Files uploaded to 'data folder'")

        self.update_data_files_display()

    def update_data_files_display(self):
        if not os.path.exists(DATA_DIR):
            self.data_files_label.setText("No files in /data.")
            return
        
        valid_extensions = {".out", ".trail", ".pml", ".isf"}

        files = [       
            f for f in os.listdir(DATA_DIR)
            if os.path.splitext(f)[1].lower() in valid_extensions 
        ]
        if files:
            self.data_files_label.setText("Uploaded Files :\n" + "\n".join(sorted(files)))
        else:
            self.data_files_label.setText("No files selected.")

    def clear_data_and_output(self):
        data_extensions = {".out", ".trail", ".pml", ".isf", ".txt"}
        output_extensions = {".json", ".png"}

        if os.path.exists(DATA_DIR):
            for f in os.listdir(DATA_DIR):
                if os.path.splitext(f)[1].lower() in data_extensions:
                    try:
                        os.remove(os.path.join(DATA_DIR, f))
                    except Exception as e:
                        QMessageBox.warning(self, "Warning", f"Could not delete {f}: {e}")

        OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
        if os.path.exists(OUTPUT_DIR):
            for f in os.listdir(OUTPUT_DIR):
                if os.path.splitext(f)[1].lower() in output_extensions:
                    try:
                        os.remove(os.path.join(OUTPUT_DIR, f))
                    except Exception as e:
                        QMessageBox.warning(self, "Warning", f"Could not delete {f}: {e}")

        QMessageBox.information(self, "Cleared", "Data and output files cleared.")
        self.update_data_files_display()



    def run_parser(self):
        self.run_script("parser_module.py")

    def run_overview(self):
        self.run_script("overview.py")

    def run_OUT(self):
        self.run_script("OUT_viewer.py")

    def run_visualizer(self):
        self.run_script("vizualizer_module_3.py")

    def run_sequence(self):
        self.run_script("timeline_evolved.py")

    def run_msc_maker(self):
        self.run_script("msc_maker.py")

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
