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
        self.setGeometry(100, 100, 500, 600)
        self.setup_ui()
        self.update_data_files_display()
        self.update_profile_menu()

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
        profile_label = QLabel("Model Profiles")
        profile_label.setStyleSheet("font-size: 10pt; margin-top: 10px;")
        main_layout.addWidget(profile_label)

        profile_layout = QHBoxLayout()
        create_profile_btn = self.styled_button("Create Model Profile", "#c4a7e7", "#9b6edc")
        create_profile_btn.clicked.connect(self.create_profile)
        profile_layout.addWidget(create_profile_btn)

        load_profile_btn = self.styled_button("Load Model Profile", "#fcae8a", "#d47b3f")
        load_profile_btn.clicked.connect(self.load_profile_menu)
        self.profile_dropdown = load_profile_btn 
        profile_layout.addWidget(load_profile_btn)

        delete_profile_btn = QPushButton("🗑")
        delete_profile_btn.setFixedSize(28, 28)
        delete_profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        delete_profile_btn.setToolTip("Delete a saved profile")
        delete_profile_btn.clicked.connect(self.delete_profile_menu)
        profile_layout.addWidget(delete_profile_btn)


        main_layout.addLayout(profile_layout)

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

    def create_profile(self):
        name, ok = QInputDialog.getText(self, "Profile Name", "Enter a name for the new profile:")
        if not ok or not name.strip():
            return
        profile_name = name.strip()
        folder = os.path.join(PROFILES_DIR, profile_name)
        os.makedirs(folder, exist_ok=True)

        files, _ = QFileDialog.getOpenFileNames(
            self, "Select files for the profile", "",
            "All Files (*.trail *.pml *.out *.isf *.txt)"
        )
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

        QMessageBox.information(self, "Success", f"Profile '{profile_name}' created!")
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
        reply = QMessageBox.question(
            self,
            "Delete Profile",
            f"Are you sure you want to delete the profile '{profile_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                def on_rm_error(func, path, exc_info):
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception as e:
                        print(f"Retry failed for {path}: {e}")

                target_folder = os.path.join(PROFILES_DIR, profile_name)

                # Attempt full deletion
                shutil.rmtree(target_folder, onerror=on_rm_error)

                # Double-check: if folder remains, remove it manually
                if os.path.exists(target_folder):
                    try:
                        os.rmdir(target_folder)
                    except Exception as e:
                        QMessageBox.warning(self, "Partial Delete",
                            f"Files deleted, but folder could not be removed:\n{target_folder}\nError: {e}")
                        return

                QMessageBox.information(self, "Deleted", f"Profile '{profile_name}' was fully deleted.")
                self.update_profile_menu()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete profile:\n{e}")


    def update_profile_menu(self):
        pass 


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
