import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QTextBrowser
from PyQt5.QtCore import Qt, QThread, pyqtSignal

# Define the dependencies folder path
dep_path = os.path.join(os.getcwd(), "dependencies")
adb_path = os.path.join(dep_path, "adb.exe")
scrcpy_path = os.path.join(dep_path, "scrcpy.exe")

# Background Thread to Run scrcpy and Monitor Process
class ScrcpyThread(QThread):
    scrcpy_closed = pyqtSignal()

    def run(self):
        try:
            scrcpy_process = subprocess.Popen([scrcpy_path])
            scrcpy_process.wait()  # Wait until scrcpy is closed
            self.scrcpy_closed.emit()  # Emit signal when scrcpy exits
        except Exception as e:
            print(f"Error starting scrcpy: {e}")

# Main Application Window
class ScreenMirrorApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("AndroidMirror")
        self.setGeometry(100, 100, 400, 300)

        # UI Elements
        self.debug_label = QLabel("⚠️ You must enable USB debugging on your device!", self)
        self.debug_label.setAlignment(Qt.AlignCenter)

        self.label = QLabel("🔌 Connect your device via USB", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.device_info = QTextBrowser(self)
        self.device_info.setPlaceholderText("Device info will appear here...")

        self.start_button = QPushButton("Start Screen Mirror", self)
        self.start_button.setEnabled(False)  # Initially disabled
        self.start_button.clicked.connect(self.start_screen_mirror)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.debug_label)
        layout.addWidget(self.label)
        layout.addWidget(self.device_info)
        layout.addWidget(self.start_button)
        self.setLayout(layout)

        # Check for connected devices
        self.update_device_info()

    def update_device_info(self):
        try:
            # Check if ADB recognizes any devices
            result = subprocess.run([adb_path, "devices"], capture_output=True, text=True)
            lines = result.stdout.strip().split("\n")

            if len(lines) <= 1 or "device" not in lines[1]:  # No device connected
                self.device_info.setText("No device detected. Please connect your Android device via USB.")
                return

            # Fetch device properties
            model = subprocess.run([adb_path, "shell", "getprop", "ro.product.model"], capture_output=True, text=True).stdout.strip()
            brand = subprocess.run([adb_path, "shell", "getprop", "ro.product.brand"], capture_output=True, text=True).stdout.strip()
            android_version = subprocess.run([adb_path, "shell", "getprop", "ro.build.version.release"], capture_output=True, text=True).stdout.strip()
            serial = lines[1].split("\t")[0]  # Get device serial number

            # Display device info
            info = f"Device: {model}\nBrand: {brand}\nAndroid Version: {android_version}\nSerial: {serial}"
            self.device_info.setText(info)
            self.start_button.setEnabled(True)  # Enable button if a device is found

        except Exception as e:
            self.device_info.setText(f"Error detecting device: {e}")

    def start_screen_mirror(self):
        self.start_button.setEnabled(False)  # Disable while running
        self.scrcpy_thread = ScrcpyThread()
        self.scrcpy_thread.scrcpy_closed.connect(self.on_scrcpy_closed)
        self.scrcpy_thread.start()

    def on_scrcpy_closed(self):
        self.start_button.setEnabled(True)  # Re-enable button when scrcpy closes

# Run the Application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenMirrorApp()
    window.show()
    sys.exit(app.exec_())
