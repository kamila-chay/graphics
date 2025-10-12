from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPainter
from PySide6.QtCore import Qt

from load_ppm_jpg import load_ppm

class ImageCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.image = None

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.image:
            scaled = self.image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (self.width() - scaled.width()) / 2
            y = (self.height() - scaled.height()) / 2
            painter.drawImage(x, y, scaled)

    def load_from_file(self, path): 
        if path.lower().endswith(".ppm"):
            self.image = load_ppm(path)
        else:
            self.image = QImage(path)
        self.update()