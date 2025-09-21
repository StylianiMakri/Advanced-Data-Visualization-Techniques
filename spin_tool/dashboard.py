from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QMessageBox, QFrame, QTextEdit, QGroupBox,
    QSizePolicy, QInputDialog, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6 import QtCore
import os
import shutil
import subprocess
import sys
import json
import stat

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
PROFILES_DIR = os.path.join(BASE_DIR, 'profiles')

DATA_EXTENSIONS = {".out", ".trail", ".pml", ".isf", ".txt"}
OUTPUT_EXTENSIONS = {".json", ".png"}

os.makedirs(PROFILES_DIR, exist_ok=True)


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
        self.setGeometry(100, 100, 540, 680)
        self.setup_ui()
        self.update_data_files_display()
        self.update_profile_menu()

    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f4f6f9;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 10.5pt;
                color: #2e3a59;
            }
            QLabel {
                font-weight: 600;
            }
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #dcdfe6;
                border-radius: 6px;
                padding: 8px;
            }
        """)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addWidget(self.section_label("File Operations"))
        file_ops = self.card_frame()
        file_layout = QHBoxLayout(file_ops)
        upload_btn = self.styled_button("Upload Files", "#3A7AFE", "#2C5DC1")
        upload_btn.clicked.connect(self.upload_files)
        file_layout.addWidget(upload_btn)

        clear_btn = self.styled_button("Clear Files", "#d9534f", "#c9302c")
        clear_btn.clicked.connect(self.clear_data_and_output)
        file_layout.addWidget(clear_btn)
        main_layout.addWidget(file_ops)

        main_layout.addWidget(self.section_label("Model Profiles"))
        profile_frame = self.card_frame()
        profile_layout = QHBoxLayout(profile_frame)

        create_profile_btn = self.styled_button("Create Model Profile")
        create_profile_btn.clicked.connect(self.create_profile)
        profile_layout.addWidget(create_profile_btn)

        load_profile_btn = self.styled_button("Load Model Profile")
        load_profile_btn.clicked.connect(self.load_profile_menu)
        self.profile_dropdown = load_profile_btn
        profile_layout.addWidget(load_profile_btn)

        delete_profile_btn = self.styled_button("Delete Profile", "#e0e0e0", "#cccccc")
        delete_profile_btn.setFixedWidth(130)
        delete_profile_btn.clicked.connect(self.delete_profile_menu)
        profile_layout.addWidget(delete_profile_btn)

        main_layout.addWidget(profile_frame)

        main_layout.addWidget(self.section_label("Run Parser"))
        parser_frame = self.card_frame()
        parser_layout = QVBoxLayout(parser_frame)
        parser_btn = self.styled_button("Run Parser Module", large=True)
        parser_btn.clicked.connect(self.run_parsers)
        parser_layout.addWidget(parser_btn)
        main_layout.addWidget(parser_frame)

        main_layout.addWidget(self.section_label("Analysis Modules"))
        module_frame = self.card_frame()
        module_layout = QVBoxLayout(module_frame)
        rows = [
            [("Visualizer", "vizualizer_module.py"), ("Timeline", "timeline_evolved.py")],
            [("3D State Graph", "3D_statespace_module.py"), ("Why it Failed", "why_it_failed.py")],
            [("Overview", "OUT_viewer.py")]
        ]
        for row in rows:
            row_layout = QHBoxLayout()
            for label, script in row:
                btn = self.styled_button(label)
                btn.clicked.connect(lambda _, s=script: self.run_script(s))
                row_layout.addWidget(btn)
            module_layout.addLayout(row_layout)
        main_layout.addWidget(module_frame)

        main_layout.addWidget(self.section_label("Files in /data:"))
        self.file_display = QTextEdit()
        self.file_display.setReadOnly(True)
        self.file_display.setFixedHeight(150)
        main_layout.addWidget(self.file_display)

    def styled_button(self, text, color="#3A7AFE", hover="#2C5DC1", large=False):
        font_size = "11pt" if large else "10pt"
        padding = "10px" if large else "6px"
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                font-weight: 500;
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

    def section_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 11.5pt; font-weight: bold; margin-top: 10px;")
        return label

    def card_frame(self):
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e6ed;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        return frame

    def upload_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "All Files (*.trail *.pml *.out *.isf *.txt)")
        if not files:
            return
        os.makedirs(DATA_DIR, exist_ok=True)
        for file in files:
            try:
                shutil.copy(file, DATA_DIR)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not copy file: {e}")
        QMessageBox.information(self, "Success", "Files uploaded to /data")
        self.update_data_files_display()

    def clear_data_and_output(self):
        delete_files_by_extension(DATA_DIR, DATA_EXTENSIONS)
        delete_files_by_extension(OUTPUT_DIR, OUTPUT_EXTENSIONS)
        QMessageBox.information(self, "Cleared", "Data and output files cleared.")
        self.update_data_files_display()

    def update_data_files_display(self):
        if not os.path.exists(DATA_DIR):
            self.file_display.setPlainText("No files in /data.")
            return
        files = [f for f in os.listdir(DATA_DIR) if os.path.splitext(f)[1].lower() in DATA_EXTENSIONS]
        self.file_display.setPlainText("\n".join(sorted(files)) if files else "No files selected.")

    def run_parsers(self):
        try:
            self.run_script("parser_module.py")
            self.run_script("parser_sim.py")
        except Exception as e:
            QMessageBox.critical(self, "Parser Error", str(e))

    def run_script(self, script_name):
        try:
            subprocess.Popen([sys.executable, script_name])
            #QMessageBox.information(self, "Running", f"{script_name} launched.")
        except Exception as e:
            QMessageBox.critical(self, "Execution Failed", f"Could not launch {script_name}:\n{e}")

    def create_profile(self):
        name, ok = QInputDialog.getText(self, "Profile Name", "Enter profile name:")
        if not ok or not name.strip():
            return
        profile_name = name.strip()
        folder = os.path.join(PROFILES_DIR, profile_name)
        os.makedirs(folder, exist_ok=True)

        files, _ = QFileDialog.getOpenFileNames(self, "Select files for profile", "", "All Files (*.trail *.pml *.out *.isf *.txt)")
        if not files:
            return

        file_mapping = {}
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in DATA_EXTENSIONS:
                dst = os.path.join(folder, os.path.basename(f))
                try:
                    shutil.copy(f, dst)
                    file_mapping[ext] = os.path.basename(f)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to copy {f}: {e}")

        with open(os.path.join(folder, "profile.json"), "w") as f:
            json.dump({"name": profile_name, "files": file_mapping}, f, indent=2)

        QMessageBox.information(self, "Success", f"Profile '{profile_name}' created.")
        self.update_profile_menu()

    def load_profile_menu(self):
        menu = QMenu()
        for profile in sorted(os.listdir(PROFILES_DIR)):
            profile_path = os.path.join(PROFILES_DIR, profile, "profile.json")
            if os.path.isfile(profile_path):
                action = menu.addAction(profile)
                action.triggered.connect(lambda _, p=profile: self.load_profile(p))
        menu.exec(self.profile_dropdown.mapToGlobal(QtCore.QPoint(0, self.profile_dropdown.height())))

    def load_profile(self, profile_name):
        profile_folder = os.path.join(PROFILES_DIR, profile_name)
        metadata_path = os.path.join(profile_folder, "profile.json")
        if not os.path.exists(metadata_path):
            QMessageBox.critical(self, "Error", f"Profile '{profile_name}' has no metadata.")
            return

        delete_files_by_extension(DATA_DIR, DATA_EXTENSIONS)

        for f in os.listdir(profile_folder):
            if f == "profile.json":
                continue
            shutil.copy(os.path.join(profile_folder, f), os.path.join(DATA_DIR, f))

        QMessageBox.information(self, "Loaded", f"Profile '{profile_name}' loaded into /data.")
        self.update_data_files_display()

    def delete_profile_menu(self):
        menu = QMenu()
        for profile in sorted(os.listdir(PROFILES_DIR)):
            profile_path = os.path.join(PROFILES_DIR, profile, "profile.json")
            if os.path.isfile(profile_path):
                action = menu.addAction(profile)
                action.triggered.connect(lambda _, p=profile: self.confirm_delete_profile(p))
        menu.exec(self.sender().mapToGlobal(QtCore.QPoint(0, self.sender().height())))

    def confirm_delete_profile(self, profile_name):
        reply = QMessageBox.question(self, "Delete Profile", f"Delete profile '{profile_name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                def on_rm_error(func, path, exc_info):
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception as e:
                        print(f"Retry failed for {path}: {e}")

                shutil.rmtree(os.path.join(PROFILES_DIR, profile_name), onerror=on_rm_error)
                self.update_profile_menu()
                QMessageBox.information(self, "Deleted", f"Profile '{profile_name}' deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete profile:\n{e}")

    def update_profile_menu(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
