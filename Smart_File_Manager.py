import os
import shutil
import json
from pathlib import Path

from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QThread, Signal, QPropertyAnimation
from PySide6.QtGui import QFont

SESSION_FILE = "last_session.json"
AUTO_SELECT_EXTS = {".dat", ".mat", ".zip", ".xmp", ".log"}


def get_extensions(folder_path):
    return sorted({
        Path(f).suffix
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and Path(f).suffix
    })


def handle_duplicate(dst):
    if not os.path.exists(dst):
        return dst

    reply = QMessageBox.question(
        None,
        "Duplicate File",
        f"File already exists:\n{os.path.basename(dst)}\n\nReplace?",
        QMessageBox.Yes | QMessageBox.No
    )
    return dst if reply == QMessageBox.Yes else None


class Worker(QThread):
    finished = Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app

    def run(self):
        self.app.execute_logic()
        self.finished.emit()


class FileRenameApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart File Manager")
        self.resize(900, 700)

        self.source_folder = ""
        self.extension_vars = {}
        self.file_widgets = []

        self.create_zip_var = True
        self.operation_var = "copy"

        self.init_ui()
        self.apply_dark_theme()  # ✅ updated styles
        self.fade_in()

        self.load_last_session()

    # ✅ ONLY UPDATED THIS PART
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2f;
                color: #ffffff;
                font-size: 13px;
            }

            QPushButton {
                background-color: #3a3f5c;
                border-radius: 6px;
                padding: 6px;
            }

            QPushButton:hover {
                background-color: #50577a;
            }

            QLineEdit, QTextEdit, QComboBox {
                background-color: #2a2f4a;
                border: 1px solid #444;
                padding: 5px;
                border-radius: 5px;
            }

            /* 🔥 FIX: CHECKBOX VISIBILITY */
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #aaa;
                border-radius: 3px;
                background: #2a2f4a;
            }

            QCheckBox::indicator:checked {
                background-color: #4da6ff;
                border: 2px solid #4da6ff;
            }

            /* 🔥 FIX: RADIO BUTTON VISIBILITY */
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 2px solid #aaa;
                background: #2a2f4a;
            }

            QRadioButton::indicator:checked {
                background-color: #4da6ff;
                border: 2px solid #4da6ff;
            }
        """)

    def fade_in(self):
        self.setWindowOpacity(0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(800)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        self.layout = QVBoxLayout(container)

        scroll.setWidget(container)
        self.setCentralWidget(scroll)

        self.layout.addWidget(QLabel("Enter Rename Names"))
        self.names_text = QTextEdit()
        self.layout.addWidget(self.names_text)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Session")
        save_btn.clicked.connect(self.save_session)
        load_btn = QPushButton("Load Session")
        load_btn.clicked.connect(self.load_session)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(load_btn)
        self.layout.addLayout(btn_layout)

        self.dest_entry = self.create_path_input("Destination Folder")

        self.new_folder_entry = QLineEdit()
        self.layout.addWidget(QLabel("New Folder Name"))
        self.layout.addWidget(self.new_folder_entry)

        self.zip_files_dest_entry = self.create_path_input("Model Files Destination")
        self.created_zip_dest_entry = self.create_path_input("Result Files Destination")

        self.source_entry = self.create_path_input("Source Folder", self.browse_source)

        detect_btn = QPushButton("Detect Extensions")
        detect_btn.clicked.connect(self.detect_extensions)
        self.layout.addWidget(detect_btn)

        self.extensions_layout = QHBoxLayout()
        self.layout.addLayout(self.extensions_layout)

        load_files_btn = QPushButton("Load Files")
        load_files_btn.clicked.connect(self.load_files)
        self.layout.addWidget(load_files_btn)

        self.files_layout = QVBoxLayout()
        self.layout.addLayout(self.files_layout)

        op_layout = QHBoxLayout()
        copy_radio = QRadioButton("Copy")
        move_radio = QRadioButton("Move")
        copy_radio.setChecked(True)

        copy_radio.toggled.connect(lambda: setattr(self, "operation_var", "copy"))
        move_radio.toggled.connect(lambda: setattr(self, "operation_var", "move"))

        op_layout.addWidget(copy_radio)
        op_layout.addWidget(move_radio)
        self.layout.addLayout(op_layout)

        self.zip_checkbox = QCheckBox("Create ZIP file")
        self.zip_checkbox.setChecked(True)
        self.layout.addWidget(self.zip_checkbox)

        self.exec_btn = QPushButton("Execute")
        self.exec_btn.clicked.connect(self.run_thread)
        self.layout.addWidget(self.exec_btn)

    def run_thread(self):
        self.exec_btn.setEnabled(False)
        self.worker = Worker(self)
        self.worker.finished.connect(self.on_done)
        self.worker.start()

    def on_done(self):
        self.exec_btn.setEnabled(True)
        QMessageBox.information(self, "Success", "All outputs saved to their respective destinations.")

    def create_path_input(self, label, browse_func=None):
        self.layout.addWidget(QLabel(label))
        layout = QHBoxLayout()
        entry = QLineEdit()
        btn = QPushButton("Browse")

        if browse_func:
            btn.clicked.connect(browse_func)
        else:
            btn.clicked.connect(lambda: self.browse_generic(entry))

        layout.addWidget(entry)
        layout.addWidget(btn)
        self.layout.addLayout(layout)
        return entry

    def browse_generic(self, entry):
        path = QFileDialog.getExistingDirectory(self)
        if path:
            entry.setText(path)
            self.save_last_session()

    def browse_source(self):
        path = QFileDialog.getExistingDirectory(self)
        if path:
            self.source_entry.setText(path)
            self.source_folder = path

    def detect_extensions(self):
        for i in reversed(range(self.extensions_layout.count())):
            self.extensions_layout.itemAt(i).widget().deleteLater()

        self.extension_vars.clear()

        for ext in get_extensions(self.source_folder):
            cb = QCheckBox(ext)
            cb.setChecked(ext.lower() in AUTO_SELECT_EXTS)
            self.extensions_layout.addWidget(cb)
            self.extension_vars[ext] = cb

    def load_files(self):
        for i in reversed(range(self.files_layout.count())):
            self.files_layout.itemAt(i).widget().deleteLater()

        self.file_widgets.clear()

        names = [n.strip() for n in self.names_text.toPlainText().splitlines() if n.strip()]
        selected_exts = [e for e, cb in self.extension_vars.items() if cb.isChecked()]

        for f in os.listdir(self.source_folder):
            if Path(f).suffix not in selected_exts:
                continue

            row = QHBoxLayout()
            row.setSpacing(1)
            row.setContentsMargins(0, 0, 0, 0)

            inc = QCheckBox()
            inc.setChecked(True)

            file_label = QLabel(f)

            keep = QCheckBox("Keep original")
            folder_only = QCheckBox("Folder only")

            combo = QComboBox()
            combo.addItems(names)

            row.addWidget(inc)
            row.addWidget(file_label)
            row.addWidget(combo)
            row.addWidget(folder_only)
            row.addWidget(keep)

            container = QWidget()
            container.setLayout(row)

            self.files_layout.addWidget(container)
            self.file_widgets.append((f, inc, keep, folder_only, combo))

    def execute_logic(self):
        normal_dest = os.path.join(self.dest_entry.text(), self.new_folder_entry.text())
        zip_files_dest = self.zip_files_dest_entry.text()
        created_zip_dest = self.created_zip_dest_entry.text()

        os.makedirs(normal_dest, exist_ok=True)
        os.makedirs(zip_files_dest, exist_ok=True)
        os.makedirs(created_zip_dest, exist_ok=True)

        for f, inc, keep, folder_only, rename in self.file_widgets:
            if not inc.isChecked():
                continue

            ext = Path(f).suffix

            if keep.isChecked():
                final_name = f
            elif folder_only.isChecked():
                final_name = f"{self.new_folder_entry.text()}{ext}"
            else:
                final_name = f"{self.new_folder_entry.text()}_{rename.currentText()}{ext}"

            src = os.path.join(self.source_folder, f)
            dst = os.path.join(zip_files_dest if ext == ".zip" else normal_dest, final_name)

            dst = handle_duplicate(dst)
            if dst is None:
                continue

            if self.operation_var == "move":
                shutil.move(src, dst)
            else:
                shutil.copy2(src, dst)

        if self.zip_checkbox.isChecked():
            zip_path = os.path.join(created_zip_dest, self.new_folder_entry.text() + ".zip")
            zip_path = handle_duplicate(zip_path)

            if zip_path:
                shutil.make_archive(
                    zip_path.replace(".zip", ""),
                    "zip",
                    self.dest_entry.text(),
                    self.new_folder_entry.text()
                )

    def save_session(self):
        names = [n.strip() for n in self.names_text.toPlainText().splitlines() if n.strip()]
        if not names:
            QMessageBox.warning(self, "Warning", "No rename names to save.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save Session", "", "JSON files (*.json)")
        if path:
            json.dump({"rename_names": names}, open(path, "w"), indent=4)

    def load_session(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Session", "", "JSON files (*.json)")
        if path:
            names = json.load(open(path)).get("rename_names", [])
            self.names_text.setPlainText("\n".join(names))

    def save_last_session(self):
        json.dump({
            "dest_folder": self.dest_entry.text(),
            "zip_files_dest": self.zip_files_dest_entry.text(),
            "created_zip_dest": self.created_zip_dest_entry.text()
        }, open(SESSION_FILE, "w"))

    def load_last_session(self):
        if os.path.exists(SESSION_FILE):
            data = json.load(open(SESSION_FILE))
            self.dest_entry.setText(data.get("dest_folder", ""))
            self.zip_files_dest_entry.setText(data.get("zip_files_dest", ""))
            self.created_zip_dest_entry.setText(data.get("created_zip_dest", ""))


if __name__ == "__main__":
    app = QApplication([])
    win = FileRenameApp()
    win.show()
    app.exec()