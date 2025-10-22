import json
import numpy as np
import copy
import math

from PySide6.QtWidgets import (
    QWidget, QMessageBox
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPolygonF, QKeyEvent
from PySide6.QtCore import Qt, QRectF, QPointF, Signal

def distance(point1, point2):
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


class PolygonsCanvas(QWidget):
    mode_changed = Signal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.current_mode = "create"
        self.polygons = []
        self.post_init()
        
    def post_init(self):
        self.new_one = []
        self.picked_index = None
        self.start_point_translate = None
        self.start_point_rotate_scale = None
        self.updated = None
        self.relative_point = None
        self.relative_point_proposal = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        painter.setBrush(QColor("skyblue"))
        painter.setPen(QColor("black"))
        for i, polygon in enumerate(self.polygons):
            if i == self.picked_index:
                continue
            curr_points = []
            for point in polygon:
                curr_points.append(QPointF(point[0], point[1]))
            painter.drawPolygon(QPolygonF(curr_points))
        
        if self.updated:
            curr_points = []
            for point in self.updated:
                curr_points.append(QPointF(point[0], point[1]))
            painter.drawPolygon(QPolygonF(curr_points))
        
        painter.setBrush(Qt.transparent)
        pen = QPen(QColor("black"))
        pen.setStyle(Qt.DashLine)
        painter.setPen(pen)

        if self.new_one:
            curr_points = []
            for point in self.new_one:
                curr_points.append(QPointF(point[0], point[1]))
            painter.drawPolygon(QPolygonF(curr_points))

        if self.relative_point_proposal:
            x, y = self.relative_point_proposal
            painter.setBrush(QColor("red"))
            painter.setPen(QColor("black"))
            radius = 5
            painter.drawEllipse(QPointF(x, y), radius, radius)
        if self.relative_point:
            x, y = self.relative_point
            painter.setBrush(QColor("black"))
            painter.setPen(QColor("black"))
            radius = 5
            painter.drawEllipse(QPointF(x, y), radius, radius)

    def setCurrentOption(self, opt):
        if opt != self.current_mode:
            self.mode_changed.emit(opt)
            self.current_mode = opt
            self.post_init()

    def mousePressEvent(self, event):
        pos = event.position()
        x, y = pos.x(), pos.y()
        if event.button() == Qt.LeftButton:
            if self.current_mode == "create":
                if self.new_one:
                    self.new_one[-1] = [x, y]
                    self.new_one.append([x, y])
                else:
                    self.new_one.append([x, y])
                    self.new_one.append([x, y])
            elif self.current_mode == "translate":
                self.picked_index = self.find_picked_index(x, y)
                if self.picked_index is not None:
                    self.start_point_translate = [x, y]
                    self.updated = copy.deepcopy(self.polygons[self.picked_index])
            else:
                if self.relative_point:
                    self.picked_index = self.find_picked_index(x, y)
                    if self.picked_index is not None:
                        self.start_point_rotate_scale = [x, y]
                        self.updated = copy.deepcopy(self.polygons[self.picked_index])
                else:
                    self.relative_point_proposal = [x, y]

        self.update()

    def find_picked_index(self, x, y):
        point_of_interest = QPointF(x, y)
        for i, existing_poligon in enumerate(self.polygons[::-1], 1):
            curr_points = []
            for point in existing_poligon:
                curr_points.append(QPointF(point[0], point[1]))
            polygon = QPolygonF(curr_points)
            if polygon.containsPoint(point_of_interest, Qt.WindingFill):
                return len(self.polygons)-i
        return None

    def mouseMoveEvent(self, event):
        pos = event.position()
        x, y = pos.x(), pos.y()
        if self.current_mode == "create" and self.new_one:
            self.new_one[-1] = [x, y]
        if self.current_mode == "translate" and self.start_point_translate:
            x_old, y_old = self.start_point_translate
            translate_matrix = np.array([[1, 0, x - x_old],
                                         [0, 1, y - y_old],
                                         [0, 0, 1]])
            for i, point in enumerate(self.polygons[self.picked_index]):
                point_homogenous = np.array(point + [1])
                new_point = translate_matrix @ point_homogenous
                self.updated[i] = [new_point[0], new_point[1]]
        if self.current_mode in {"rotate", "scale"} and self.start_point_rotate_scale:
            translate_negative = np.array([[1, 0, -self.relative_point[0]],
                                           [0, 1, -self.relative_point[1]],
                                           [0, 0, 1]])
            translate_positive = np.array([[1, 0, self.relative_point[0]],
                                           [0, 1, self.relative_point[1]],
                                           [0, 0, 1]])
            if self.current_mode == "rotate":
                v1 = np.array(self.start_point_rotate_scale) - np.array(self.relative_point)
                v2 = np.array([x, y]) - np.array(self.relative_point)
                angle = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
                cosine_theta = math.cos(angle)
                sine_theta = math.sin(angle)
                transform_rotate = np.array([[cosine_theta, -sine_theta, 0],
                                             [sine_theta, cosine_theta, 0],
                                             [0, 0, 1]])
                transform_total = translate_positive @ transform_rotate @ translate_negative
                for i, point in enumerate(self.polygons[self.picked_index]):
                    point_homogenous = np.array(point + [1])
                    new_point = transform_total @ point_homogenous
                    self.updated[i] = [new_point[0], new_point[1]]
            else:
                v1 = distance(self.start_point_rotate_scale, self.relative_point)
                v2 = distance([x, y], self.relative_point)
                if v1 == 0:
                    v1 = 0.000001
                scale = v2 / v1
                transform_scale = np.array([[scale, 0, 0],
                                            [0, scale, 0],
                                            [0, 0, 1]])
                transform_total = translate_positive @ transform_scale @ translate_negative
                for i, point in enumerate(self.polygons[self.picked_index]):
                    point_homogenous = np.array(point + [1])
                    new_point = transform_total @ point_homogenous
                    self.updated[i] = [new_point[0], new_point[1]]

        self.update()

    def mouseReleaseEvent(self, event):
        if self.current_mode in {"translate", "rotate", "scale"} and self.picked_index is not None:
            self.polygons[self.picked_index] = self.updated
            self.post_init()
        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        if self.current_mode == "create":
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if len(self.new_one) > 2:
                    self.polygons.append(self.new_one[:-1])
                self.post_init()
            if event.key() == Qt.Key_Escape:
                self.post_init()
        if self.current_mode in {"rotate", "scale"} and self.relative_point_proposal:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self.relative_point = self.relative_point_proposal
                self.relative_point_proposal = None
        self.update()
