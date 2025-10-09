from PySide6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSlider
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QColor

slider_style_sheet = """
    QSlider::groove:horizontal {
        height: 6px;               
        background: #ddd;
        border-radius: 3px;
    }

    QSlider::handle:horizontal {
        width: 6px;                
        height: 12px;             
        background: #888;
        margin: -3px 0;           
        border-radius: 2px;
    }
"""

class ColorPatch(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = QColor(0, 0, 0)
        self.setFixedSize(50, 50)

    def set_color(self, color: QColor):
        self.color = color
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.color)

class ColorPicker(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        rgb_layout = QVBoxLayout()
        rgb_layout.setSpacing(0)
        self.all_switches = {}

        self.color_preview = ColorPatch()
        rgb_layout.addWidget(self.color_preview)

        for color in ['R', 'G', 'B']:
            h = QHBoxLayout()
            h.setSpacing(5)
            label = QLabel(color)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            slider.setStyleSheet(slider_style_sheet)
            edit = QLineEdit("0")
            edit.setFixedWidth(35)
            slider.valueChanged.connect(lambda val, c=color: self.update_color(c, val))
            edit.textChanged.connect(lambda text, c=color: self.update_slider(c, text))
            h.addWidget(label)
            h.addWidget(slider)
            h.addWidget(edit)
            rgb_layout.addLayout(h)
            self.all_switches[color] = (slider, edit)

        main_layout.addLayout(rgb_layout)
        
        cmyk_layout = QVBoxLayout()
        cmyk_layout.setSpacing(0)
        for color in ['C', 'M', 'Y', "K"]:
            h = QHBoxLayout()
            h.setSpacing(5)
            label = QLabel(color)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setStyleSheet(slider_style_sheet)
            edit = QLineEdit("0")
            edit.setFixedWidth(35)
            slider.valueChanged.connect(lambda val, c=color: self.update_color(c, val))
            edit.textChanged.connect(lambda text, c=color: self.update_slider(c, text))
            h.addWidget(label)
            h.addWidget(slider)
            h.addWidget(edit)
            cmyk_layout.addLayout(h)
            self.all_switches[color] = (slider, edit)

        main_layout.addLayout(cmyk_layout)

    def update_color(self, c, val):
        slider, edit = self.all_switches[c]
        edit.setText(str(val))
        r = self.all_switches['R'][0].value()
        g = self.all_switches['G'][0].value()
        b = self.all_switches['B'][0].value()
        self.color_preview.set_color(QColor(r, g, b))

    def update_slider(self, c, text):
        if text.isdigit():  # more checks here
            val = int(text)
            slider, _ = self.all_switches[c]
            slider.setValue(val)