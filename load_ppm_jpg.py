from PySide6.QtGui import QImage, QColor
import numpy as np

def load_ppm(path):
    with open(path, "rb") as f:
        magic_num = f.readline().strip()
        if magic_num not in [b'P3', b'P6']:
            raise ValueError("Not a valid PPM file")
        meta_data = []
        temp = b''
        while len(meta_data) < 3:
            next_char = f.read(1)
            if next_char == b'#':
                if len(temp) > 0:
                    meta_data.append(int(temp))
                    temp = b''
                f.readline()
            elif next_char.isspace():
                if len(temp) > 0:
                    meta_data.append(int(temp))
                    temp = b''
                    if magic_num == b'P6' and len(meta_data) == 3 and next_char != b'\n':
                        f.readline()
            else:
                temp += next_char
        actual_values = []
        if magic_num == b'P3':
            for line in f:
                line = line.split(b'#')[0]
                actual_values.extend(line.split())
            actual_values = np.array(list(map(int, actual_values)), dtype=np.uint16)
        else:
            actual_values = np.array(list(f.read()), dtype=np.uint16)

        width, height, maxval = meta_data
        actual_values = actual_values if maxval == 255 else (actual_values / maxval) * 255
        actual_values = actual_values.astype(np.uint8)
        image = QImage(actual_values.tobytes(), width, height, 3 * width, QImage.Format_RGB888)
        return image.copy()
        