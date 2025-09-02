import sys
import os
import subprocess
import threading
import base64
import re
import shutil
import tempfile
import requests
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QTextEdit, 
                             QVBoxLayout, QHBoxLayout, QComboBox, QFileDialog, 
                             QProgressBar, QFrame, QGridLayout, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtGui import QFont, QPalette, QColor

import base64

def decode_base64_multiple(encoded, times=4):
    current = encoded
    for _ in range(times):
        current = base64.b64decode(current).decode("utf-8")
    return current

# Encoded usernames and passwords
encoded_usernames = [
    "test",
    "test"
]
encoded_passwords = [
    "test",
    "test"
]

usernames = [decode_base64_multiple(u, 4) for u in encoded_usernames]
passwords_list = [decode_base64_multiple(p, 4) for p in encoded_passwords]
passwords = {usernames[i]: passwords_list[i] for i in range(len(usernames))}

# Display names
account_display_list = ["Account 1", "Account 2"]

APP_ID = "824270"

def get_collection_items(collection_id):
    """
    Вытягивает все ID из Steam Workshop коллекции
    """
    collection_url = "https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/"
    collection_data = {
        "collectioncount": "1",
        "publishedfileids[0]": collection_id
    }
    try:
        collection_response = requests.post(collection_url, data=collection_data, timeout=10)
        if collection_response.status_code != 200:
            return []
        
        collection_json = collection_response.json()
        children = collection_json["response"]["collectiondetails"][0]["children"]
        item_ids = [child["publishedfileid"] for child in children]
        return item_ids
    except:
        return []

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal()

    def __init__(self, scenarios_dir, ids, selected_account, passwords):
        super().__init__()
        self.scenarios_dir = scenarios_dir
        self.ids = ids
        self.selected_account = selected_account
        self.passwords = passwords
        self.is_canceled = False
        self.current_process = None

    def run(self):
        if not self.scenarios_dir:
            self.log_signal.emit("❌ Error: Scenarios folder not set correctly.")
            return

        # Обрабатываем входные данные и извлекаем ID из коллекций
        all_ids = []
        for line in self.ids:
            line = line.strip()
            if not line:
                continue
            
            # Проверяем, является ли это коллекцией
            collection_match = re.search(r"steamcommunity\.com/sharedfiles/filedetails/\?id=(\d+)", line)
            if collection_match:
                collection_id = collection_match.group(1)
                self.log_signal.emit(f"🔍 Checking if {collection_id} is a collection...")
                
                # Пробуем получить элементы коллекции
                collection_items = get_collection_items(collection_id)
                if collection_items:
                    self.log_signal.emit(f"📦 Found collection with {len(collection_items)} items!")
                    all_ids.extend(collection_items)
                    continue
                else:
                    self.log_signal.emit(f"📄 Not a collection or single item: {collection_id}")
            
            # Если не коллекция, извлекаем обычный ID
            match = re.search(r"\b\d{8,10}\b", line)
            if match:
                all_ids.append(match.group(0))
            else:
                self.log_signal.emit(f"❌ Invalid ID: {line}")

        if not all_ids:
            self.log_signal.emit("❌ No valid IDs found!")
            return

        self.log_signal.emit(f"📋 Total items to download: {len(all_ids)}")
        
        # Скачиваем все ID
        for i, workshop_id in enumerate(all_ids):
            if self.is_canceled:
                self.log_signal.emit("❌ Download canceled!")
                break
            self.run_command(workshop_id)
            self.progress_signal.emit(int(((i + 1) / len(all_ids)) * 100))
        
        self.finished_signal.emit()

    def find_depot_downloader_mod(self):
        for root, dirs, files in os.walk(os.getcwd()):
            if "DepotDownloaderMod.exe" in files:
                return os.path.join(root, "DepotDownloaderMod.exe")
        return None

    def run_command(self, pubfileid):
        depot_exe = self.find_depot_downloader_mod()
        if not depot_exe:
            self.log_signal.emit("❌ DepotDownloaderMod.exe not found in current directory or subfolders")
            return

        password = self.passwords[self.selected_account]
        temp_dir = tempfile.mkdtemp(prefix="koovak_temp_")

        command = [
            depot_exe,
            "-app", APP_ID,
            "-pubfile", pubfileid,
            "-username", self.selected_account,
            "-password", password,
            "-dir", temp_dir
        ]

        self.log_signal.emit(f"🔄 Downloading {pubfileid}...")
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.current_process = process
        for _ in process.stdout:
            pass
        process.wait()
        self.current_process = None

        moved_files = 0
        for root_dir, _, files in os.walk(temp_dir):
            for file in files:
                if file.endswith(".sce"):
                    src = os.path.join(root_dir, file)
                    dst = os.path.join(self.scenarios_dir, file)
                    shutil.move(src, dst)
                    self.log_signal.emit(f"✅ Moved .sce file: {file}")
                    moved_files += 1

        if moved_files == 0:
            self.log_signal.emit(f"⚠️ No .sce files found in {pubfileid}")

        shutil.rmtree(temp_dir, ignore_errors=True)
        self.log_signal.emit(f"✅ Download of {pubfileid} completed\n")

class Downloader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Koovak's Map Downloader v2.0")
        self.setGeometry(100, 100, 800, 650)
        self.scenarios_dir = None
        self.worker = None
        self.settings = QSettings("Koovak", "MapDownloader")
        self.setup_style()
        self.initUI()
        self.load_saved_settings()

    def load_saved_settings(self):
        saved_folder = self.settings.value("game_root", None)
        if saved_folder:
            target = os.path.join(saved_folder, "FPSAimTrainer", "Saved", "SaveGames", "Scenarios")
            if os.path.isdir(target):
                self.scenarios_dir = target
                self.save_label.setText(f"✅ Target scenarios folder: {self.scenarios_dir}")
                self.save_label.setStyleSheet("color: #4CAF50;")
                self.printlog(f"✅ Loaded saved scenarios folder: {self.scenarios_dir}")
            else:
                self.printlog(f"⚠️ Saved game root not valid anymore: {saved_folder}")

    def setup_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
            QComboBox {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
                font-size: 12px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-top-color: white;
                border-width: 4px 4px 0px 4px;
            }
            QTextEdit {
                background-color: #404040;
                color: white;
                border: 1px solid #555555;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QProgressBar {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)

    def initUI(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # Title Section
        title_frame = QFrame()
        title_layout = QVBoxLayout()
        
        title = QLabel("🗺️ Koovak's Map Downloader")
        title_font = QFont("Segoe UI", 24, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #4CAF50; margin: 10px;")
        
        subtitle = QLabel("Download Workshop Maps for FPS Aim Trainer")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #cccccc; font-size: 14px; margin-bottom: 10px;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        title_frame.setLayout(title_layout)
        main_layout.addWidget(title_frame)

        # Configuration Section
        config_group = QGroupBox("Configuration")
        config_layout = QGridLayout()
        
        # Account selection
        account_label = QLabel("Account:")
        account_label.setStyleSheet("font-weight: bold;")
        self.account_combo = QComboBox()
        
        # Используем отображаемые имена
        for i, display_name in enumerate(account_display_list):
            self.account_combo.addItem(display_name, usernames[i])
        
        config_layout.addWidget(account_label, 0, 0)
        config_layout.addWidget(self.account_combo, 0, 1)

        # Game folder selection
        folder_label = QLabel("Game Folder:")
        folder_label.setStyleSheet("font-weight: bold;")
        self.save_button = QPushButton("📁 Select Game Root Folder")
        self.save_button.clicked.connect(self.select_game_root)
        self.save_label = QLabel("❌ Game root folder: Not set")
        self.save_label.setStyleSheet("color: #ff6b6b;")
        
        config_layout.addWidget(folder_label, 1, 0)
        config_layout.addWidget(self.save_button, 1, 1)
        config_layout.addWidget(self.save_label, 2, 0, 1, 2)
        
        config_group.setLayout(config_layout)
        main_layout.addWidget(config_group)

        # Input Section
        input_group = QGroupBox("Workshop Items & Collections")
        input_layout = QVBoxLayout()
        
        input_label = QLabel("Enter workshop links, IDs, or collection links (one per line):")
        input_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        
        self.id_text = QTextEdit()
        self.id_text.setPlaceholderText("Example:\nhttps://steamcommunity.com/sharedfiles/filedetails/?id=123456789\n987654321\n\n🔥 Collections are supported! Just paste collection links!")
        self.id_text.setMaximumHeight(100)
        
        input_layout.addWidget(input_label)
        input_layout.addWidget(self.id_text)
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)

        # Progress Section
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        progress_layout.addWidget(self.progress_bar)
        progress_group.setLayout(progress_layout)
        main_layout.addWidget(progress_group)

        # Console Section
        console_group = QGroupBox("Console Output")
        console_layout = QVBoxLayout()
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(200)
        self.console.append("📋 Ready to download maps...")
        
        console_layout.addWidget(self.console)
        console_group.setLayout(console_layout)
        main_layout.addWidget(console_group)

        # Download Button
        self.download_button = QPushButton("🚀 Start Download")
        self.set_download_button_style()
        self.download_button.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_button)

        self.setLayout(main_layout)

    def set_download_button_style(self):
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

    def set_cancel_button_style(self):
        self.download_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                font-size: 16px;
                font-weight: bold;
                padding: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
        """)

    def printlog(self, msg):
        self.console.append(msg)
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    def select_game_root(self):
        folder = QFileDialog.getExistingDirectory(self, "Select game root folder")
        if folder:
            target = os.path.join(folder, "FPSAimTrainer", "Saved", "SaveGames", "Scenarios")
            if os.path.isdir(target):
                self.scenarios_dir = target
                self.save_label.setText(f"✅ Target scenarios folder: {self.scenarios_dir}")
                self.save_label.setStyleSheet("color: #4CAF50;")
                self.printlog(f"✅ Target scenarios folder set to {self.scenarios_dir}")
                self.settings.setValue("game_root", folder)
            else:
                self.scenarios_dir = None
                self.save_label.setText("❌ Could not find Scenarios folder")
                self.save_label.setStyleSheet("color: #ff6b6b;")
                self.printlog(f"❌ Could not find Scenarios folder inside {folder}\\FPSAimTrainer\\Saved\\SaveGames")

    def start_download(self):
        if not self.scenarios_dir:
            QMessageBox.warning(self, "Error", "Please select a valid game root folder first!")
            return

        ids = self.id_text.toPlainText().splitlines()
        if not any(id.strip() for id in ids):
            QMessageBox.warning(self, "Error", "Please enter at least one workshop ID or link!")
            return

        # Получаем реальное имя аккаунта из комбобокса
        selected_account = self.account_combo.currentData()
        
        self.download_button.disconnect()
        self.download_button.clicked.connect(self.cancel_download)
        self.set_cancel_button_style()
        self.download_button.setText("❌ Cancel Download")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.worker = DownloadWorker(self.scenarios_dir, ids, selected_account, passwords)
        self.worker.log_signal.connect(self.printlog)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.download_finished)
        self.worker.start()

    def cancel_download(self):
        if self.worker:
            self.download_button.setEnabled(False)
            self.download_button.setText("❌ Canceling...")
            self.worker.is_canceled = True
            if self.worker.current_process:
                self.worker.current_process.terminate()
                self.printlog("⚠️ Terminating current download...")

    def download_finished(self):
        if self.worker.is_canceled:
            self.printlog("❌ Download canceled!")
            QMessageBox.information(self, "Canceled", "Download has been canceled!")
        else:
            self.printlog("🎉 All downloads completed!")
            QMessageBox.information(self, "Success", "All downloads completed successfully!")

        self.download_button.disconnect()
        self.download_button.clicked.connect(self.start_download)
        self.set_download_button_style()
        self.download_button.setText("🚀 Start Download")
        self.download_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.worker = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Downloader()
    window.show()

    sys.exit(app.exec_())
