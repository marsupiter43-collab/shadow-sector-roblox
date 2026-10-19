import sys
import cv2
import numpy as np
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
import queue

class Signals(QObject):
    update_frame = pyqtSignal(np.ndarray, list, dict)

class ARWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.fused_targets = []
        self.telemetry = {}

    def set_data(self, frame: np.ndarray, fused_targets: list, telemetry: dict):
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        self.image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.fused_targets = fused_targets
        self.telemetry = telemetry
        self.update() # Trigger paintEvent

    def paintEvent(self, event):
        if self.image is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale image to widget size
        scaled_img = self.image.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        x_offset = (self.width() - scaled_img.width()) // 2
        y_offset = (self.height() - scaled_img.height()) // 2

        painter.drawImage(x_offset, y_offset, scaled_img)

        # We need scaling factors for AR elements
        scale_x = scaled_img.width() / self.image.width()
        scale_y = scaled_img.height() / self.image.height()

        # Draw AR Overlay
        for target in self.fused_targets:
            rt = target['radar_data']

            if target['is_visible'] and target['optical_bbox']:
                # Draw green/neutral brackets
                color = QColor(0, 255, 0)
                bx1, by1, bx2, by2 = target['optical_bbox']

                # Scale coordinates
                x1 = int(bx1 * scale_x) + x_offset
                y1 = int(by1 * scale_y) + y_offset
                x2 = int(bx2 * scale_x) + x_offset
                y2 = int(by2 * scale_y) + y_offset

                pen = QPen(color, 2)
                painter.setPen(pen)

                # Draw brackets (corners)
                L = 20
                # Top left
                painter.drawLine(x1, y1, x1+L, y1)
                painter.drawLine(x1, y1, x1, y1+L)
                # Top right
                painter.drawLine(x2, y1, x2-L, y1)
                painter.drawLine(x2, y1, x2, y1+L)
                # Bottom left
                painter.drawLine(x1, y2, x1+L, y2)
                painter.drawLine(x1, y2, x1, y2-L)
                # Bottom right
                painter.drawLine(x2, y2, x2-L, y2)
                painter.drawLine(x2, y2, x2, y2-L)

                # Distance text
                painter.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                dist_m = rt['y'] / 1000.0
                painter.drawText(x1, y1 - 10, f"{dist_m:.1f}m")

            else:
                # Occluded target: Draw red 3D wireframe and projected vector
                color = QColor(255, 0, 0)
                pen = QPen(color, 2)
                painter.setPen(pen)

                # If we have 3D wireframe points in radar_data
                wireframe = rt.get('wireframe', [])
                if len(wireframe) == 8:
                    # Scale points
                    pts = [(int(p[0] * scale_x) + x_offset, int(p[1] * scale_y) + y_offset) for p in wireframe]

                    # Draw bottom face
                    painter.drawLine(pts[0][0], pts[0][1], pts[1][0], pts[1][1])
                    painter.drawLine(pts[1][0], pts[1][1], pts[2][0], pts[2][1])
                    painter.drawLine(pts[2][0], pts[2][1], pts[3][0], pts[3][1])
                    painter.drawLine(pts[3][0], pts[3][1], pts[0][0], pts[0][1])

                    # Draw top face
                    painter.drawLine(pts[4][0], pts[4][1], pts[5][0], pts[5][1])
                    painter.drawLine(pts[5][0], pts[5][1], pts[6][0], pts[6][1])
                    painter.drawLine(pts[6][0], pts[6][1], pts[7][0], pts[7][1])
                    painter.drawLine(pts[7][0], pts[7][1], pts[4][0], pts[4][1])

                    # Draw pillars
                    painter.drawLine(pts[0][0], pts[0][1], pts[4][0], pts[4][1])
                    painter.drawLine(pts[1][0], pts[1][1], pts[5][0], pts[5][1])
                    painter.drawLine(pts[2][0], pts[2][1], pts[6][0], pts[6][1])
                    painter.drawLine(pts[3][0], pts[3][1], pts[7][0], pts[7][1])

                    # Distance text at center base
                    cx = (pts[2][0] + pts[3][0]) // 2
                    cy = (pts[2][1] + pts[3][1]) // 2
                    painter.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
                    dist_m = rt['y'] / 1000.0
                    painter.drawText(cx, cy + 20, f"{dist_m:.1f}m (OCCLUDED)")

        # Draw 360 Radar Widget in lower-left
        self.draw_tactical_radar(painter, x_offset, y_offset, scaled_img.height())

        # Draw Telemetry Bar
        self.draw_telemetry(painter)

    def draw_tactical_radar(self, painter, x_off, y_off, img_h):
        cx = 100
        cy = self.height() - 100
        r = 80

        # Background
        painter.setBrush(QColor(0, 20, 0, 150))
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        painter.drawEllipse(cx - r, cy - r, 2 * r, 2 * r)

        # Crosshairs
        painter.drawLine(cx - r, cy, cx + r, cy)
        painter.drawLine(cx, cy - r, cx, cy + r)

        # Draw targets on radar (top down view)
        max_range = 10000.0 # 10 meters max scale

        painter.setBrush(QColor(255, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        for target in self.fused_targets:
            rt = target['radar_data']
            x_m = rt['x']
            y_m = rt['y']

            # Scale to radar size
            rx = cx + int((x_m / max_range) * r)
            ry = cy - int((y_m / max_range) * r) # Y forward is -Y on screen

            if cx - r <= rx <= cx + r and cy - r <= ry <= cy + r:
                painter.drawEllipse(rx - 3, ry - 3, 6, 6)

    def draw_telemetry(self, painter):
        painter.setPen(QColor(0, 255, 0))
        painter.setFont(QFont("Consolas", 10))

        x = 10
        y = 20

        fps = self.telemetry.get('fps', 0.0)
        latency = self.telemetry.get('latency', 0.0)
        mode = self.telemetry.get('mode', 'NOMINAL')

        painter.drawText(x, y, f"SYS FPS: {fps:.1f}")
        painter.drawText(x, y + 15, f"LATENCY: {latency:.1f}ms")
        painter.drawText(x, y + 30, f"MODE: {mode}")

class MainWindow(QMainWindow):
    def __init__(self, data_queue: queue.Queue):
        super().__init__()
        self.setWindowTitle("NeuroVision Core HUD")
        self.resize(1280, 720)

        self.ar_widget = ARWidget(self)
        self.setCentralWidget(self.ar_widget)

        self.data_queue = data_queue
        self.signals = Signals()
        self.signals.update_frame.connect(self.ar_widget.set_data)

        # Timer to poll the queue
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_queue)
        self.timer.start(16) # ~60 FPS

    def poll_queue(self):
        try:
            # Get the latest item, drain the queue if multiple exist
            item = None
            while not self.data_queue.empty():
                item = self.data_queue.get_nowait()

            if item:
                frame, fused_targets, telemetry = item
                self.signals.update_frame.emit(frame, fused_targets, telemetry)
        except Exception as e:
            pass

def launch_gui(data_queue: queue.Queue):
    # This must run in the main thread of the process
    app = QApplication(sys.argv)
    window = MainWindow(data_queue)
    window.show()
    sys.exit(app.exec())
