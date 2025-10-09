from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QComboBox, QFileDialog, QMessageBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF
import sys
import json


class GraphicObject:
    def __init__(self, kind, params, color=(0, 0, 0)):
        # kind: 'line', 'rect', 'circle'
        # params: for line: [x1,y1,x2,y2]
        # for rect: [x,y,w,h]
        # for circle: [cx,cy,r]
        self.kind = kind
        self.params = params
        self.color = color
        self.selected = False

    def to_dict(self):
        return {"kind": self.kind, "params": self.params, "color": self.color}

    @staticmethod
    def from_dict(d):
        return GraphicObject(d['kind'], d['params'], tuple(d.get('color', (0, 0, 0))))


class Canvas(QWidget):
    HANDLE_SIZE = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self.objects = []
        self.current_tool = 'select'  # or 'line','rect','circle'
        self.drawing = False
        self.start_pos = None
        self.temp_obj = None
        self.selected_obj = None
        self.dragging = False
        self.drag_offset = QPointF(0, 0)
        self.resizing = False
        self.resize_handle = None
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        for obj in self.objects:
            pen = QPen(QColor(*obj.color))
            pen.setWidth(2)
            painter.setPen(pen)
            if obj.kind == 'line':
                x1, y1, x2, y2 = obj.params
                painter.drawLine(x1, y1, x2, y2)
            elif obj.kind == 'rect':
                x, y, w, h = obj.params
                painter.drawRect(x, y, w, h)
            elif obj.kind == 'circle':
                cx, cy, r = obj.params
                painter.drawEllipse(QPointF(cx, cy), r, r)
            if obj.selected:
                self.draw_handles(painter, obj)
        # draw temp object
        if self.temp_obj:
            pen = QPen(QColor(*self.temp_obj.color))
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            obj = self.temp_obj
            if obj.kind == 'line':
                x1, y1, x2, y2 = obj.params
                painter.drawLine(x1, y1, x2, y2)
            elif obj.kind == 'rect':
                x, y, w, h = obj.params
                painter.drawRect(x, y, w, h)
            elif obj.kind == 'circle':
                cx, cy, r = obj.params
                painter.drawEllipse(QPointF(cx, cy), r, r)

    def draw_handles(self, painter, obj):
        painter.setBrush(QBrush(Qt.white))
        painter.setPen(QPen(Qt.black))
        if obj.kind == 'line':
            x1, y1, x2, y2 = obj.params
            for px, py in [(x1, y1), (x2, y2)]:
                painter.drawRect(px - 3, py - 3, 6, 6)
        elif obj.kind == 'rect':
            x, y, w, h = obj.params
            for px, py in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
                painter.drawRect(px - 3, py - 3, 6, 6)
        elif obj.kind == 'circle':
            cx, cy, r = obj.params
            painter.drawRect(cx + r - 3, cy - 3, 6, 6)

    def mousePressEvent(self, event):
        pos = event.position()
        x, y = pos.x(), pos.y()
        if event.button() == Qt.LeftButton:
            if self.current_tool == 'select':
                obj = self.find_object_at(x, y)
                if obj:
                    self.select_object(obj)
                    # check handles
                    handle = self.find_handle_at(obj, x, y)
                    if handle:
                        self.resizing = True
                        self.resize_handle = handle
                    else:
                        self.dragging = True
                        px = self.obj_pos(obj)
                        self.drag_offset = QPointF(x - px[0], y - px[1])
                else:
                    self.clear_selection()
            else:
                # start drawing
                self.drawing = True
                self.start_pos = (x, y)
                color = (0, 0, 0)
                if self.current_tool == 'line':
                    self.temp_obj = GraphicObject('line', [x, y, x, y], color)
                elif self.current_tool == 'rect':
                    self.temp_obj = GraphicObject('rect', [x, y, 0, 0], color)
                elif self.current_tool == 'circle':
                    self.temp_obj = GraphicObject('circle', [x, y, 0], color)
            self.update()

    def mouseMoveEvent(self, event):
        pos = event.position()
        x, y = pos.x(), pos.y()
        if self.drawing and self.temp_obj:
            if self.temp_obj.kind == 'line':
                self.temp_obj.params[2:] = [x, y]
            elif self.temp_obj.kind == 'rect':
                sx, sy = self.start_pos
                w, h = x - sx, y - sy
                self.temp_obj.params = [sx, sy, w, h]
            elif self.temp_obj.kind == 'circle':
                sx, sy = self.start_pos
                r = ((x - sx) ** 2 + (y - sy) ** 2) ** 0.5
                self.temp_obj.params = [sx, sy, r]
            self.update()
        elif self.dragging and self.selected_obj:
            # move object
            nx = x - self.drag_offset.x()
            ny = y - self.drag_offset.y()
            self.move_object_to(self.selected_obj, nx, ny)
            self.update()
        elif self.resizing and self.selected_obj:
            self.resize_object_with_handle(self.selected_obj, self.resize_handle, x, y)
            self.update()

    def mouseReleaseEvent(self, event):
        pos = event.position()
        x, y = pos.x(), pos.y()
        if self.drawing and self.temp_obj:
            # commit
            self.objects.append(self.temp_obj)
            self.temp_obj = None
            self.drawing = False
        self.dragging = False
        self.resizing = False
        self.resize_handle = None
        self.update()

    def find_object_at(self, x, y):
        # iterate reverse for topmost
        for obj in reversed(self.objects):
            if obj.kind == 'line':
                x1, y1, x2, y2 = obj.params
                # bounding box hit
                rect = QRectF(min(x1, x2)-5, min(y1, y2)-5, abs(x2-x1)+10, abs(y2-y1)+10) # TODO this will be very big 
                # if the line is skewed
                if rect.contains(x, y):
                    return obj
            elif obj.kind == 'rect':
                rx, ry, w, h = obj.params
                rect = QRectF(rx, ry, w, h)
                if rect.contains(x, y):
                    return obj
            elif obj.kind == 'circle':
                cx, cy, r = obj.params
                if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                    return obj
        return None

    def find_handle_at(self, obj, x, y):
        # return handle id or None
        s = 3
        if obj.kind == 'line':
            x1, y1, x2, y2 = obj.params
            if abs(x - x1) <= s and abs(y - y1) <= s:
                return ('line', 0)
            if abs(x - x2) <= s and abs(y - y2) <= s:
                return ('line', 1)
        elif obj.kind == 'rect':
            rx, ry, w, h = obj.params
            corners = [(rx, ry), (rx + w, ry), (rx, ry + h), (rx + w, ry + h)]
            for i, (px, py) in enumerate(corners):
                if abs(x - px) <= s and abs(y - py) <= s:
                    return ('rect', i)
        elif obj.kind == 'circle':
            cx, cy, r = obj.params
            hx, hy = cx + r, cy
            if abs(x - hx) <= s and abs(y - hy) <= s:
                return ('circle', 0)
        return None

    def select_object(self, obj):
        self.clear_selection()
        obj.selected = True
        self.selected_obj = obj

    def clear_selection(self):
        for o in self.objects:
            o.selected = False
        self.selected_obj = None

    def obj_pos(self, obj):
        # return top-left anchor for moving
        if obj.kind == 'line':
            x1, y1, x2, y2 = obj.params
            return (x1, y1)
        elif obj.kind == 'rect':
            x, y, w, h = obj.params
            return (x, y)
        elif obj.kind == 'circle':
            cx, cy, r = obj.params
            return (cx - r, cy - r)

    def move_object_to(self, obj, nx, ny):
        if obj.kind == 'line':
            x1, y1, x2, y2 = obj.params
            dx = nx - x1
            dy = ny - y1
            obj.params = [x1 + dx, y1 + dy, x2 + dx, y2 + dy]
        elif obj.kind == 'rect':
            x, y, w, h = obj.params
            obj.params = [nx, ny, w, h]
        elif obj.kind == 'circle':
            cx, cy, r = obj.params
            obj.params = [nx + r, ny + r, r]

    def resize_object_with_handle(self, obj, handle, x, y):
        kind, idx = handle
        if obj.kind == 'line' and kind == 'line':
            if idx == 0:
                obj.params[0:2] = [x, y]
            else:
                obj.params[2:4] = [x, y]
        elif obj.kind == 'rect' and kind == 'rect':
            rx, ry, w, h = obj.params
            corners = [(rx, ry), (rx + w, ry), (rx, ry + h), (rx + w, ry + h)]
            corners[idx] = (x, y)
            x0, y0 = corners[0]
            x1, y1 = corners[3]
            obj.params = [min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)]
        elif obj.kind == 'circle' and kind == 'circle':
            cx, cy, r = obj.params
            new_r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            obj.params[2] = new_r

    # text-based creation/updating
    def add_object_from_text(self, kind, params_text):
        try:
            parts = [float(p.strip()) for p in params_text.split(',') if p.strip()]
        except Exception:
            QMessageBox.warning(self, 'Params error', 'Invalid numeric parameters')
            return
        if kind == 'line' and len(parts) == 4:
            obj = GraphicObject('line', parts)
        elif kind == 'rect' and len(parts) == 4:
            obj = GraphicObject('rect', parts)
        elif kind == 'circle' and len(parts) == 3:
            obj = GraphicObject('circle', parts)
        else:
            QMessageBox.warning(self, 'Params error', 'Wrong number of params for kind')
            return
        self.objects.append(obj)
        self.update()

    def update_selected_from_text(self, params_text):
        if not self.selected_obj:
            QMessageBox.information(self, 'No selection', 'Select an object first')
            return
        try:
            parts = [float(p.strip()) for p in params_text.split(',') if p.strip()]
        except Exception:
            QMessageBox.warning(self, 'Params error', 'Invalid numeric parameters')
            return
        kind = self.selected_obj.kind
        if kind == 'line' and len(parts) == 4:
            self.selected_obj.params = parts
        elif kind == 'rect' and len(parts) == 4:
            self.selected_obj.params = parts
        elif kind == 'circle' and len(parts) == 3:
            self.selected_obj.params = parts
        else:
            QMessageBox.warning(self, 'Params error', 'Wrong number of params for selected kind')
            return
        self.update()

    def to_json(self):
        return json.dumps([o.to_dict() for o in self.objects], indent=2)

    def save_to_file(self, path):
        with open(path, 'w') as f:
            f.write(self.to_json())

    def load_from_file(self, path):
        with open(path, 'r') as f:
            arr = json.load(f)
        self.objects = [GraphicObject.from_dict(a) for a in arr]
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Primitives Editor - PySide6')
        self.canvas = Canvas()

        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        v = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        for t in ['select', 'line', 'rect', 'circle']:
            b = QPushButton(t.capitalize())
            b.setCheckable(True)
            if t == 'select':
                b.setChecked(True)
            b.clicked.connect(lambda checked, tt=t: self.set_tool(tt))
            toolbar.addWidget(b)
        v.addLayout(toolbar)

        # text params
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel('Kind:'))
        self.kind_combo = QComboBox()
        self.kind_combo.addItems(['line', 'rect', 'circle'])
        params_layout.addWidget(self.kind_combo)
        params_layout.addWidget(QLabel('Params:'))
        self.params_edit = QLineEdit()
        self.params_edit.setPlaceholderText('line: x1,y1,x2,y2  rect: x,y,w,h  circle: cx,cy,r')
        params_layout.addWidget(self.params_edit)
        add_btn = QPushButton('Add')
        add_btn.clicked.connect(self.add_from_text)
        params_layout.addWidget(add_btn)
        update_btn = QPushButton('Update selected')
        update_btn.clicked.connect(self.update_selected)
        params_layout.addWidget(update_btn)
        v.addLayout(params_layout)

        # save/load
        sl_layout = QHBoxLayout()
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(self.save_file)
        load_btn = QPushButton('Load')
        load_btn.clicked.connect(self.load_file)
        sl_layout.addWidget(save_btn)
        sl_layout.addWidget(load_btn)
        v.addLayout(sl_layout)

        v.addWidget(self.canvas)
        self.resize(900, 600)

    def set_tool(self, tool):
        self.canvas.current_tool = tool

    def add_from_text(self):
        kind = self.kind_combo.currentText()
        txt = self.params_edit.text()
        self.canvas.add_object_from_text(kind, txt)

    def update_selected(self):
        txt = self.params_edit.text()
        self.canvas.update_selected_from_text(txt)

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save JSON', filter='JSON Files (*.json)')
        if path:
            self.canvas.save_to_file(path)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open JSON', filter='JSON Files (*.json)')
        if path:
            self.canvas.load_from_file(path)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
