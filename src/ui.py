# ui.py
from PySide6 import QtWidgets, QtGui, QtCore
import sys, time, os
from queue import Empty
from pathlib import Path
import utils, settings
import json

logger = utils.get_logger("UIApp")

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings & Calibration")
        self.setMinimumWidth(560)
        layout = QtWidgets.QVBoxLayout(self)

        self.sliders = {}
        gcfg = settings.get().get("gestures", {})
        # per-gesture sliders: (label, key, min, max, step)
        items = [
            ("OK tip dist", "ok_tip_dist", 0.02, 0.12, 0.01),
            ("Folded threshold", "folded_thresh", 0.06, 0.20, 0.01),
            ("V tip separation", "v_tip_sep", 0.08, 0.30, 0.01),
            ("V extension thresh", "v_ext_thresh", 0.08, 0.30, 0.01),
            ("Fist folded thresh", "fist_folded", 0.04, 0.14, 0.01),
            ("Index vertical delta", "index_vert_delta", 0.01, 0.08, 0.005),
            ("Shaka thumb/pinky", "shaka_thumb_pinky", 0.06, 0.22, 0.01),
        ]
        for label, key, mn, mx, step in items:
            row = QtWidgets.QHBoxLayout()
            lab = QtWidgets.QLabel(label)
            s = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            s.setMinimum(int(mn*1000))
            s.setMaximum(int(mx*1000))
            s.setSingleStep(int(step*1000))
            val = float(settings.get_g(key, (mn+mx)/2))
            s.setValue(int(val*1000))
            vlabel = QtWidgets.QLabel(f"{val:.3f}")
            s.valueChanged.connect(lambda v, k=key, vl=vlabel: self._on_slider(v, k, vl))
            row.addWidget(lab)
            row.addWidget(s, stretch=1)
            row.addWidget(vlabel)
            layout.addLayout(row)
            self.sliders[key] = s

        # App Launcher Configuration
        app_group = QtWidgets.QGroupBox("Yo Gesture - Application Launcher")
        app_layout = QtWidgets.QVBoxLayout()
        app_row = QtWidgets.QHBoxLayout()
        self.app_path_label = QtWidgets.QLabel("No app configured")
        self.app_path_label.setWordWrap(True)
        self.app_browse_btn = QtWidgets.QPushButton("Browse...")
        self.app_browse_btn.clicked.connect(self._browse_app)
        app_row.addWidget(self.app_path_label, stretch=1)
        app_row.addWidget(self.app_browse_btn)
        app_layout.addLayout(app_row)
        app_group.setLayout(app_layout)
        layout.addWidget(app_group)
        
        # Load current app path
        import actions
        config = actions.load_app_config()
        app_path = config.get("app_path", "")
        if app_path:
            self.app_path_label.setText(f"App: {app_path}")
        else:
            self.app_path_label.setText("No app configured - Click Browse to select")
        
        # Calibration / Record
        h = QtWidgets.QHBoxLayout()
        self.cal_btn = QtWidgets.QPushButton("Calibration Mode")
        self.cal_btn.clicked.connect(self._calibrate)
        self.record_btn = QtWidgets.QPushButton("Record Sample")
        self.record_btn.clicked.connect(self._record_sample)
        h.addWidget(self.cal_btn)
        h.addWidget(self.record_btn)
        layout.addLayout(h)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.samples_dir = Path.cwd() / "gesture_samples"
        self.samples_dir.mkdir(parents=True, exist_ok=True)

    def _on_slider(self, value, key, vlabel):
        val = value / 1000.0
        vlabel.setText(f"{val:.3f}")
        settings.set_g(key, val)

    def _calibrate(self):
        QtWidgets.QMessageBox.information(self, "Calibration", "Calibration mode: follow on-screen instructions (not interactive in this basic mode).")
        # In a fuller implementation this would guide the user and compute thresholds.

    def _browse_app(self):
        """Browse for application to launch with Yo gesture"""
        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Application",
            "",
            "Executable Files (*.exe);;All Files (*.*)"
        )
        if file_path:
            import actions
            if actions.set_app_path(file_path):
                self.app_path_label.setText(f"App: {file_path}")
                QtWidgets.QMessageBox.information(self, "Success", f"Application configured:\n{file_path}")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to set application path")
    
    def _record_sample(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Record Gesture Sample", "Gesture name (ok/v/shaka/victory/fist/index_up/index_down):")
        if not ok or not name:
            return
        # We create a simple file that will be filled by processing thread if it supports sample capture (not implemented here)
        p = self.samples_dir / f"{name}_{int(time.time())}.json"
        p.write_text(json.dumps({"note": "manual sample placeholder", "time": time.time()}))
        QtWidgets.QMessageBox.information(self, "Recorded", f"Sample placeholder saved to {p}")

class UIApp:
    def __init__(self, preview_q=None, frame_q=None, event_q=None, stop_event=None, cfg=None):
        self.preview_q = preview_q
        self.frame_q = frame_q
        self.event_q = event_q
        self.stop_event = stop_event
        self.cfg = cfg or {}
        self.target_fps = int(self.cfg.get("target_fps", 30))

        self.app = QtWidgets.QApplication([])
        self.app.setStyle("Fusion")
        self.win = QtWidgets.QMainWindow()
        self.win.setWindowTitle("Swipe — Gesture Controller")
        self.win.resize(900, 600)  # Smaller default window size

        central = QtWidgets.QWidget()
        self.win.setCentralWidget(central)
        v = QtWidgets.QVBoxLayout(central)
        v.setContentsMargins(10, 10, 10, 10)

        # Top
        top = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("<b>Swipe</b>")
        label.setStyleSheet("font-size:22px;")
        top.addWidget(label)
        top.addStretch()
        self.last_action = QtWidgets.QLabel("")
        self.last_action.setStyleSheet("font-size:14px; color:#888;")
        top.addWidget(self.last_action)
        v.addLayout(top)

        # Preview
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setMinimumSize(800, 450)
        self.preview_label.setStyleSheet("background-color:#000; border-radius:8px;")
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
        v.addWidget(self.preview_label, stretch=1)

        # Toolbar
        tb = QtWidgets.QHBoxLayout()
        self.btn_settings = QtWidgets.QPushButton("⚙️ Settings")
        self.btn_screens = QtWidgets.QPushButton("📁 Screenshots")
        self.btn_help = QtWidgets.QPushButton("❓ Help")
        self.btn_quit = QtWidgets.QPushButton("Quit")
        tb.addWidget(self.btn_settings)
        tb.addWidget(self.btn_screens)
        tb.addWidget(self.btn_help)
        tb.addStretch()
        tb.addWidget(self.btn_quit)
        v.addLayout(tb)

        # Connect
        self.btn_settings.clicked.connect(self._open_settings)
        self.btn_screens.clicked.connect(self._open_screens)
        self.btn_help.clicked.connect(self._open_help)
        self.btn_quit.clicked.connect(self._quit)

        # Tray
        self._setup_tray()

        # Timer to poll preview queue
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._on_timer)
        self.timer.start(int(1000 / max(1, self.target_fps)))
        
        # Timer to check for events (screenshot notifications)
        self.event_timer = QtCore.QTimer()
        self.event_timer.timeout.connect(self._check_events)
        self.event_timer.start(100)  # Check every 100ms

        self.win.closeEvent = self._on_close

    def _setup_tray(self):
        icon = self.win.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        self.tray = QtWidgets.QSystemTrayIcon(icon)
        menu = QtWidgets.QMenu()
        menu.addAction("Show", self._show)
        menu.addAction("Quit", self._quit)
        self.tray.setContextMenu(menu)
        self.tray.show()

    def _show(self):
        self.win.showNormal()
        self.win.activateWindow()

    def _open_settings(self):
        dlg = SettingsDialog(self.win)
        dlg.exec()

    def _open_screens(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        folder = Path(self.cfg.get("screenshots_folder", str(Path.cwd() / "screenshots")))
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))


    def _open_help(self):
        QtWidgets.QMessageBox.information(self.win, "Help", 
            "Supported gestures:\n\n"
            "👌 OK - Play/Pause multimedia\n"
            "✌️ V - Close active window\n"
            "🤙 Shaka - Take screenshot\n"
            "✋ All 5 Fingers Up - Volume Up (10%)\n"
            "👇 All 4 Fingers Down - Volume Down (10%)\n"
            "🤘 Yo - Launch configured app\n\n"
            "Hold gesture for 0.5s to trigger action.\n"
            "Volume adjusts continuously while gesture is held.\n\n"
            "Configure app for Yo gesture in Settings.")

    def _quit(self):
        try:
            if self.stop_event:
                self.stop_event.set()
        except Exception:
            pass
        self.tray.hide()
        QtWidgets.QApplication.quit()

    def _on_close(self, e):
        e.ignore()
        self.win.hide()
        self.tray.showMessage("Swipe", "Minimized to tray. Right-click -> Quit to exit.", QtWidgets.QSystemTrayIcon.Information, 3000)

    def _on_timer(self):
        frame = None
        if self.preview_q:
            try:
                while True:
                    frame = self.preview_q.get_nowait()
            except Exception:
                pass
        if frame is not None:
            self._display(frame)
    
    def _check_events(self):
        """Check for events from processing thread (screenshot notifications)"""
        if self.event_q:
            try:
                while True:
                    event = self.event_q.get_nowait()
                    if event.get("name") == "screenshot" and "data" in event:
                        filepath = event["data"]
                        self._show_screenshot_notification(filepath)
            except Exception:
                pass
    
    def _show_screenshot_notification(self, filepath):
        """Show screenshot notification in the foreground window (not Swipe window)"""
        from pathlib import Path
        import threading
        
        filename = Path(filepath).name
        
        def show_notification():
            """Show notification in a separate thread to avoid blocking"""
            try:
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, x2, y2 = rect
                    window_width = x2 - x
                    window_height = y2 - y
                    
                    # Create a standalone notification window
                    notification_window = QtWidgets.QWidget()
                    notification_window.setWindowFlags(
                        QtCore.Qt.WindowStaysOnTopHint | 
                        QtCore.Qt.FramelessWindowHint |
                        QtCore.Qt.Tool |
                        QtCore.Qt.WindowDoesNotAcceptFocus
                    )
                    notification_window.setAttribute(QtCore.Qt.WA_ShowWithoutActivating)
                    notification_window.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)
                    
                    # Create label with notification
                    notification = QtWidgets.QLabel(f"📸 Screenshot saved:\n{filename}", notification_window)
                    notification.setStyleSheet("""
                        QLabel {
                            background-color: rgba(45, 45, 45, 250);
                            color: #00ff00;
                            padding: 15px;
                            border-radius: 8px;
                            font-size: 14px;
                            font-weight: bold;
                            border: 2px solid #00ff00;
                        }
                    """)
                    notification.setAlignment(QtCore.Qt.AlignCenter)
                    notification.setWordWrap(True)
                    
                    # Position in center of foreground window
                    notification.resize(300, 80)
                    notification_window.resize(300, 80)
                    notification_window.move(
                        x + (window_width // 2) - 150,
                        y + (window_height // 2) - 40
                    )
                    
                    notification_window.show()
                    notification_window.raise_()
                    
                    # Auto-hide after 2 seconds
                    def close_notification():
                        try:
                            notification_window.close()
                            notification_window.deleteLater()
                        except Exception:
                            pass
                    
                    QtCore.QTimer.singleShot(2000, close_notification)
                    return
            except Exception:
                pass
            
            # Fallback: use system tray notification
            try:
                self.tray.showMessage("Screenshot", f"Screenshot saved: {filename}", 
                                    QtWidgets.QSystemTrayIcon.Information, 2000)
            except Exception:
                pass
        
        # Run in main thread (Qt requires UI operations in main thread)
        QtCore.QTimer.singleShot(0, show_notification)

    def _display(self, frame):
        import cv2
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QtGui.QImage(rgb.data, w, h, 3*w, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(qimg)
        pix = pix.scaled(self.preview_label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.preview_label.setPixmap(pix)

    def run(self):
        self.win.show()
        sys.exit(self.app.exec())
