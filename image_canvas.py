from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import Qt, QPoint, QEvent, Signal

from load_ppm_jpg import load_ppm
import numpy as np
from utils import create_ds_kernel

ds = [(-1,-1),(0,-1),(1,-1),(-1,0),(0,0),(1,0),(-1,1),(0,1),(1,1)]

class ImageCanvas(QWidget):
    hover_over_color = Signal(int, int, int)
    def __init__(self, parent=None):
        super().__init__()
        self.image = None
        self.modified_image = None
        self.scaled = None
        self.scale = 1.0
        self.offset = QPoint(0, 0)
        self.last_mouse_pos = None
        self.x = None
        self.y = None
        self.setMouseTracking(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.translate(self.offset)
        painter.scale(self.scale, self.scale)
        current_image = self.modified_image if self.modified_image else self.image
        if current_image:
            self.scaled = current_image.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.x = (self.width() - self.scaled.width()) / 2
            self.y = (self.height() - self.scaled.height()) / 2
            painter.drawImage(self.x, self.y, self.scaled)

    def load_from_file(self, path): 
        if path.lower().endswith(".ppm"):
            self.image = load_ppm(path)
        else:
            self.image = QImage(path)
        self.modified_image = None
        self.scale = 1.0
        self.offset = QPoint(0, 0)
        self.update()
        self.hover_over_color.emit(0, 0, 0)

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

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_mouse_pos:
            delta = event.pos() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.pos()
            self.update()
        if self.image:
            x = ((event.pos().x() - self.offset.x()) / self.scale) - self.x
            y = ((event.pos().y() - self.offset.y()) / self.scale) - self.y
            if x >= 0 and x < self.scaled.width() and y >= 0 and y < self.scaled.height():
                color = QColor(self.scaled.pixel(x, y))
                self.hover_over_color.emit(color.red(), color.green(), color.blue())

    def mouseReleaseEvent(self, event):
        self.last_mouse_pos = None

    def event(self, event):
        if event.type() == QEvent.NativeGesture:
            if event.gestureType() == Qt.ZoomNativeGesture:
                self.handle_zoom(event.value())
                return True  # prevent further handling
        return super().event(event)
    
    def handle_zoom(self, delta):
        factor = 1 + delta * 0.1
        self.scale *= factor
        self.update()

    def binarize(self, name, bin_threshold, black_percent):
        if self.image:
            if "percent black" in name:
                pass
            elif "mean iterative" in name:
                pass
            else:
                pass
            self.update()

    def perform_dilation(self, arr):
        out = np.zeros_like(arr, dtype=np.uint8)
        for y in range(arr.shape[0]):
            for x in range(arr.shape[1]):
                for dx, dy in ds:
                    nx = min(max(x+dx,0), arr.shape[1]-1)
                    ny = min(max(y+dy,0), arr.shape[0]-1)
                    if arr[ny, nx] == 255:
                        out[y, x] = 255
        return out
    
    def perform_erosion(self, arr):
        out = np.ones_like(arr, dtype=np.uint8) * 255
        for y in range(arr.shape[0]):
            for x in range(arr.shape[1]):
                for dx, dy in ds:
                    nx = min(max(x+dx,0), arr.shape[1]-1)
                    ny = min(max(y+dy,0), arr.shape[0]-1)
                    if arr[ny, nx] == 0:
                        out[y, x] = 0
        return out

    def perform_median_filter(self, arr):
        out = np.zeros_like(arr, dtype=np.uint8)
        
        for y in range(arr.shape[0]):
            for x in range(arr.shape[1]):
                all_neighbors = [[] for _ in range(arr.shape[2])]
                for dx, dy in ds:
                    nx = min(max(x+dx,0), arr.shape[1]-1)
                    ny = min(max(y+dy,0), arr.shape[0]-1)
                    for i in range(arr.shape[2]):
                        all_neighbors[i].append(arr[ny, nx, i])
                for i in range(arr.shape[2]):
                    all_neighbors[i] = sorted(all_neighbors[i])
                    out[y, x, i] = all_neighbors[i][4]

        return out

    def perform_sobel(self, arr):
        out = np.zeros_like(arr, dtype=np.uint8)
        kernel_gx = [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]
        kernel_gy = [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]
        ds_kernel_gx = create_ds_kernel(kernel_gx)
        ds_kernel_gy = create_ds_kernel(kernel_gy)
        for y in range(arr.shape[0]):
            for x in range(arr.shape[1]):
                acc_x = 0.0
                acc_y = 0.0
                for (mult_gx, dx, dy), (mult_gy, _, _) in zip(ds_kernel_gx, ds_kernel_gy):
                    nx = min(max(x+dx,0), arr.shape[1]-1)
                    ny = min(max(y+dy,0), arr.shape[0]-1)
                    acc_x += mult_gx * arr[ny, nx].astype(np.float64)
                    acc_y += mult_gy * arr[ny, nx].astype(np.float64)
                out[y, x] = np.clip(np.abs(acc_x) + np.abs(acc_y), 0, 255)

        return out
    
    def perform_matching(self, arr, kernel):
        out = np.zeros_like(arr, dtype=np.uint8)
        ds_kernel = create_ds_kernel(kernel)
        pad_up = len(kernel) // 2
        pad_down = pad_up - 1 if len(kernel) % 2 == 0 else pad_up
        pad_left = len(kernel) // 2
        pad_right = pad_left - 1 if len(kernel) % 2 == 0 else pad_left
        for y in range(pad_up, arr.shape[0] - pad_down):
            for x in range(pad_left, arr.shape[1] - pad_right):
                all_matches = []
                for expected_val, dx, dy in ds_kernel:
                    nx = x+dx
                    ny = y+dy
                    if arr[ny, nx] == expected_val * 255 or arr[ny, nx] == expected_val:
                        all_matches.append(True)
                    else:
                        all_matches.append(False)
                if all(all_matches):
                    out[y, x] = 255
        return out
    
    def read_image_bits(self):
        ptr = self.image.constBits()
        needs_swap = False
        bytes_per_pixel = 3
        real_bytes_per_pixel = 3

        if self.image.format() == QImage.Format_Grayscale8:
            bytes_per_pixel = 1
            real_bytes_per_pixel = 1
        elif self.image.format() != QImage.Format_RGB888:
            needs_swap = True
            bytes_per_pixel = 4
        
        arr = np.array(ptr, dtype=np.uint8).reshape(self.image.height(), self.image.bytesPerLine())

        arr = arr[:, :self.image.width() * bytes_per_pixel]
        arr = arr.reshape(self.image.height(), self.image.width(), bytes_per_pixel)[:, :, :real_bytes_per_pixel]
        if needs_swap:
            arr = arr[:, :, ::-1]

        return arr
    
    def histogram_filter(self, name):
        if self.image:
            arr = self.read_image_bits()
            arr = arr.astype(np.float32)
            if arr.shape[2] == 3:  # colorful
            # RGB to YCbCr
                y_channel = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
                cb_channel = -0.168736 * arr[:, :, 0] - 0.331264 * arr[:, :, 1] + 0.5 * arr[:, :, 2] + 128
                cr_channel = 0.5 * arr[:, :, 0] - 0.418688 * arr[:, :, 1] - 0.081312 * arr[:, :, 2] + 128
            else:
                y_channel = arr

            if "stretch" in name:
                y_min, y_max = y_channel.min(), y_channel.max()
                y_channel = (y_channel - y_min) / (y_max - y_min) * 255

            if arr.shape[2] == 3:  # colorful
                # YCbCr to RGB
                r_channel = y_channel + 1.402 * (cr_channel - 128)
                g_channel = y_channel - 0.344136 * (cb_channel - 128) - 0.714136 * (cr_channel - 128)
                b_channel = y_channel + 1.772 * (cb_channel - 128)
                
                new_image = np.stack([r_channel, g_channel, b_channel], axis=-1).clip(0, 255).astype(np.uint8)
                print(np.min(np.mean(new_image, axis=-1)))
                print(np.max(np.mean(new_image, axis=-1)))
                print(np.any(np.all(new_image > 252, axis=-1)))
                self.modified_image = QImage(new_image, new_image.shape[1], new_image.shape[0], new_image.shape[1] * 3, QImage.Format_RGB888).copy()
            else:
                new_image = y_channel.clip(0, 255).astype(np.uint8)
                self.modified_image = QImage(new_image, new_image.shape[1], new_image.shape[0], new_image.shape[1], QImage.Format_Grayscale8).copy()

            self.update()
        
    def filter(self, filter_type, kernel=None, bin_threshold=None):
        if self.image:
            arr = self.read_image_bits()
            bytes_per_pixel = arr.shape[2]
            end_format = QImage.Format_Grayscale8 if  bytes_per_pixel == 1 else  QImage.Format_RGB888
            
            if filter_type in {"dilation", "erosion", "close", "open", "HoM-thin", "HoM-thicken", "sobel"}:
                if arr.ndim == 3 and arr.shape[2] == 3: 
                    arr = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
                end_format = QImage.Format_Grayscale8

            if filter_type in {"dilation", "erosion", "close", "open", "HoM-thin", "HoM-thicken"}:
                arr = (arr > bin_threshold).astype(np.uint8) * 255
            
            if filter_type == "dilation":
                out = self.perform_dilation(arr)
            elif filter_type == "erosion":
                out = self.perform_erosion(arr)
            elif filter_type == "close":
                out = self.perform_dilation(arr)
                out = self.perform_erosion(out)
            elif filter_type == "open":
                out = self.perform_erosion(arr)
                out = self.perform_dilation(out)
            elif filter_type == "HoM-thin":
                out = self.perform_matching(arr, kernel)
                out = np.clip(arr - out, 0, 255)
            elif filter_type == "HoM-thicken":
                out = self.perform_matching(arr, kernel)
                out = np.clip(arr + out, 0, 255)
            elif filter_type == "median":
                out = self.perform_median_filter(arr)
            elif filter_type == "sobel":
                out = self.perform_sobel(arr)
            else:       
                if filter_type == "mean":
                    kernel = [[1/9] * 3 for _ in range(3)]
                elif filter_type ==  "sharpening":
                    kernel = [[0, -1, 0], [-1, 5, -1], [0, -1, 0]]
                elif filter_type == "gaussian":
                    kernel = [[1, 4, 7, 4, 1], [4, 16, 26, 16, 4], [7, 26, 41, 26, 7], [4, 16, 26, 16, 4], [1, 4, 7, 4, 1]]
                    kernel = [[el/273 for el in row] for row in kernel]

                out = np.zeros_like(arr, dtype=np.uint8)
                ds_kernel = create_ds_kernel(kernel)

                for y in range(arr.shape[0]):
                    for x in range(arr.shape[1]):
                        acc = np.zeros(bytes_per_pixel)
                        for mult, dx, dy in ds_kernel:
                            nx = min(max(x+dx,0), arr.shape[1]-1)
                            ny = min(max(y+dy,0), arr.shape[0]-1)
                            acc += mult * arr[ny, nx].astype(np.float64)
                        out[y, x] = np.clip(acc, 0, 255)

            self.modified_image = QImage(out.data, out.shape[1], out.shape[0], out.shape[1] * (out.shape[2] if out.ndim == 3 else 1), end_format).copy()
            self.update()
