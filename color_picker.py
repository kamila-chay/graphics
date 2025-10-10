from PySide6.QtWidgets import (
     QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSlider
)
from PySide6.QtCore import Qt, Signal
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

cmyk_set = ["C", "M", "Y", "K"]
rgb_set = ["R", "G", "B"]

def rgb_to_cmyk(r, g, b):
    r_norm, g_norm, b_norm = r/255, g/255, b/255
    k = 1 - max(r_norm, g_norm, b_norm)
    
    if k < 1:
        c = (1 - r_norm - k) / (1 - k)
        m = (1 - g_norm - k) / (1 - k)
        y = (1 - b_norm - k) / (1 - k)
    else:
        c = 0
        m = 0
        y = 0
    
    c = round(100 * c)
    m = round(100 * m)
    y = round(100 * y)
    k = round(100 * k)
    return c, m, y, k

def cmyk_to_rgb(c, m, y, k):
    c = c / 100
    m = m / 100
    y = y / 100
    k = k / 100
    r = round(255 * (1 - c) * (1 - k))
    g = round(255 * (1 - m) * (1 - k))
    b = round(255 * (1 - y) * (1 - k))
    return r, g, b

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
    color_changed = Signal(QColor)
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout(self)
        rgb_layout = QVBoxLayout()
        rgb_layout.setSpacing(0)
        self.all_switches = {}

        self.color_preview = ColorPatch()

        for color in rgb_set:
            h = QHBoxLayout()
            h.setSpacing(0)
            label = QLabel(color)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 255)
            slider.setStyleSheet(slider_style_sheet)
            edit = QLineEdit("0")
            edit.setFixedWidth(35)
            slider.valueChanged.connect(lambda val, c=color: self.handle_slider_updated(c, val))
            edit.textChanged.connect(lambda text, c=color: self.handle_text_updated(c, text))
            h.addWidget(label)
            h.addWidget(slider)
            h.addWidget(edit)
            rgb_layout.addLayout(h)
            self.all_switches[color] = (slider, edit)

        main_layout.addLayout(rgb_layout)
        
        cmyk_layout = QVBoxLayout()
        cmyk_layout.setSpacing(0)
        for color in cmyk_set:
            h = QHBoxLayout()
            h.setSpacing(5)
            label = QLabel(color)
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 100)
            slider.setStyleSheet(slider_style_sheet)
            edit = QLineEdit("0")
            edit.setFixedWidth(35)
            slider.valueChanged.connect(lambda val, c=color: self.handle_slider_updated(c, val))
            edit.textChanged.connect(lambda text, c=color: self.handle_text_updated(c, text))
            h.addWidget(label)
            h.addWidget(slider)
            h.addWidget(edit)
            cmyk_layout.addLayout(h)
            self.all_switches[color] = (slider, edit)

        main_layout.addLayout(cmyk_layout)
        main_layout.addWidget(self.color_preview)

    def update_the_other_system(self, current):
        if current in rgb_set:
            fields_to_change = cmyk_set
            r = self.all_switches['R'][0].value()
            g = self.all_switches['G'][0].value()
            b = self.all_switches['B'][0].value()
            values_to_assign = rgb_to_cmyk(r, g, b)
            for field, value in zip(fields_to_change, values_to_assign):
                slider, edit = self.all_switches[field]
                slider.blockSignals(True)
                edit.blockSignals(True)
                slider.setValue(value)
                edit.setText(str(value))
                slider.blockSignals(False)
                edit.blockSignals(False)
        if current in cmyk_set:
            fields_to_change = rgb_set
            c = self.all_switches['C'][0].value()
            m = self.all_switches['M'][0].value()
            y = self.all_switches['Y'][0].value()
            k = self.all_switches['K'][0].value()
            values_to_assign = cmyk_to_rgb(c, m, y, k)
            for field, value in zip(fields_to_change, values_to_assign):
                slider, edit = self.all_switches[field]
                slider.blockSignals(True)
                edit.blockSignals(True)
                slider.setValue(value)
                edit.setText(str(value))
                slider.blockSignals(False)
                edit.blockSignals(False)

    def update_preview(self):
        r = self.all_switches['R'][0].value()
        g = self.all_switches['G'][0].value()
        b = self.all_switches['B'][0].value()
        color = QColor(r, g, b)
        self.color_preview.set_color(color)
        self.color_changed.emit(color)

    def handle_slider_updated(self, c, val):
        slider, edit = self.all_switches[c]
        edit.blockSignals(True)
        edit.setText(str(val))
        edit.blockSignals(False)

        self.update_the_other_system(c)
        self.update_preview()


    def handle_text_updated(self, c, text):
        if text.isdigit() and (((val := int(text)) <= 100 and c in cmyk_set) or (val <= 255 and c in rgb_set)):
            slider, _ = self.all_switches[c]
            slider.blockSignals(True)
            slider.setValue(val)
            slider.blockSignals(False)

            self.update_the_other_system(c)
            self.update_preview()