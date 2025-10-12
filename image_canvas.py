from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import Qt

from load_ppm_jpg import load_ppm
import numpy as np

class ImageCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.image = None
        self.modified_image = None

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.modified_image:
            scaled = self.modified_image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) / 2
            y = (self.height() - scaled.height()) / 2
            painter.drawImage(x, y, scaled)
        elif self.image:
            scaled = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) / 2
            y = (self.height() - scaled.height()) / 2
            painter.drawImage(x, y, scaled)

    def load_from_file(self, path): 
        if path.lower().endswith(".ppm"):
            self.image = load_ppm(path)
        else:
            self.image = QImage(path)
        self.modified_image = None
        self.update()

    def handle_lin_scaling_updated(self, new_scaling_value):
        if self.image:
            self.modified_image = QImage(self.image.width(), self.image.height(), QImage.Format_RGB888)
            factor = new_scaling_value / 10
            for y in range(self.image.height()):
                for x in range(self.image.width()):
                    color = self.image.pixelColor(x, y)
                    r = min(int(color.red() * factor), 255)
                    g = min(int(color.green() * factor), 255)
                    b = min(int(color.blue() * factor), 255)
                    self.modified_image.setPixelColor(x, y, QColor(r, g, b))
            self.update()