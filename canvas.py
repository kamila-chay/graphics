import json

from PySide6.QtWidgets import (
    QWidget, QMessageBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt, QRectF, QPointF, Signal

from graphical_object import GraphicalObject
from constants import grab_def_offset

class Canvas(QWidget):
    tool_changed = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.objects = []
        self.current_tool = 'select'
        self.drawing = False
        self.start_pos = None
        self.temp_obj = None
        self.temp_obj_color = None
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
                painter.drawRect(px - grab_def_offset, py - grab_def_offset, grab_def_offset * 2, grab_def_offset * 2)
        elif obj.kind == 'rect':
            x, y, w, h = obj.params
            for px, py in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
                painter.drawRect(px - grab_def_offset, py - grab_def_offset, grab_def_offset * 2, grab_def_offset * 2)
        elif obj.kind == 'circle':
            cx, cy, r = obj.params
            painter.drawRect(cx + r - grab_def_offset, cy - grab_def_offset, grab_def_offset * 2, grab_def_offset * 2)

    def mousePressEvent(self, event):
        pos = event.position()
        x, y = pos.x(), pos.y()
        if event.button() == Qt.LeftButton:
            if self.current_tool == 'select':
                obj = self.find_object_at(x, y)
                if obj:
                    self.select_object(obj)
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
                self.drawing = True
                self.start_pos = (x, y)
                color = self.temp_obj_color.getRgb()[:3]
                if self.current_tool == 'line':
                    self.temp_obj = GraphicalObject('line', [x, y, x, y], color)
                elif self.current_tool == 'rect':
                    self.temp_obj = GraphicalObject('rect', [x, y, 0, 0], color)
                elif self.current_tool == 'circle':
                    self.temp_obj = GraphicalObject('circle', [x, y, 0], color)
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
            self.start_pos = None
        self.dragging = False
        self.drag_offset = None
        self.resizing = False
        self.resize_handle = None
        self.set_tool("select")
        self.update()

    def find_object_at(self, x, y):
        # iterate reverse for topmost
        for obj in reversed(self.objects):
            if obj.kind == 'line':
                x1, y1, x2, y2 = obj.params
                rect = QRectF(min(x1, x2)-grab_def_offset * 2, min(y1, y2)-grab_def_offset * 2, abs(x2-x1)+grab_def_offset * 4, abs(y2-y1)+grab_def_offset * 4)
                if rect.contains(x, y):
                    return obj
            elif obj.kind == 'rect':
                rx, ry, w, h = obj.params
                rect = QRectF(rx - grab_def_offset, ry - grab_def_offset, w + grab_def_offset * 2, h + grab_def_offset * 2)
                if rect.contains(x, y):
                    return obj
            elif obj.kind == 'circle':
                cx, cy, r = obj.params
                if (x - cx) ** 2 + (y - cy) ** 2 <= (r + grab_def_offset) ** 2:
                    return obj
        return None

    def find_handle_at(self, obj, x, y):
        if obj.kind == 'line':
            x1, y1, x2, y2 = obj.params
            if abs(x - x1) <= grab_def_offset and abs(y - y1) <= grab_def_offset:
                return ('line', 0)
            if abs(x - x2) <= grab_def_offset and abs(y - y2) <= grab_def_offset:
                return ('line', 1)
        elif obj.kind == 'rect':
            rx, ry, w, h = obj.params
            corners = [(rx, ry), (rx + w, ry), (rx, ry + h), (rx + w, ry + h)]
            for i, (px, py) in enumerate(corners):
                if abs(x - px) <= grab_def_offset and abs(y - py) <= grab_def_offset:
                    return ('rect', i)
        elif obj.kind == 'circle':
            cx, cy, r = obj.params
            hx, hy = cx + r, cy
            if abs(x - hx) <= grab_def_offset and abs(y - hy) <= grab_def_offset:
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
            if idx == 0 or idx == 3:
                x0, y0 = corners[0]
                x1, y1 = corners[3]
            else:
                x0, y0 = corners[1]
                x1, y1 = corners[2]
            obj.params = [min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0)]
        elif obj.kind == 'circle' and kind == 'circle':
            cx, cy, r = obj.params
            new_r = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            obj.params[2] = new_r

    def add_object_from_text(self, kind, params_text, color):
        try:
            parts = [float(p.strip()) for p in params_text.split(',') if p.strip()]
        except Exception:
            QMessageBox.warning(self, 'Params error', 'Invalid numeric parameters')
            return
        if kind == 'line' and len(parts) == 4:
            obj = GraphicalObject('line', parts, color)
        elif kind == 'rect' and len(parts) == 4:
            obj = GraphicalObject('rect', parts, color)
        elif kind == 'circle' and len(parts) == 3:
            obj = GraphicalObject('circle', parts, color)
        else:
            QMessageBox.warning(self, 'Params error', 'Wrong number of params for kind')
            return
        self.objects.append(obj)
        self.update()

    def update_selected_from_text(self, params_text, color):
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
            self.selected_obj.color = color
        elif kind == 'rect' and len(parts) == 4:
            self.selected_obj.params = parts
            self.selected_obj.color = color
        elif kind == 'circle' and len(parts) == 3:
            self.selected_obj.params = parts
            self.selected_obj.color = color
        elif len(parts) == 0 and self.selected_obj.color != color:
            self.selected_obj.color = color
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
        self.objects = [GraphicalObject.from_dict(a) for a in arr]
        self.update()

    def set_tool(self, tool):
        self.current_tool = tool
        self.tool_changed.emit(tool)

    def set_drawing_color_for_new(self, color):
        self.temp_obj_color = color