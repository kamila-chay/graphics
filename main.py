import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QComboBox, QFileDialog, QButtonGroup, QTabWidget, QSlider, QLabel, QMessageBox, QTextEdit
)

from PySide6.QtCore import Qt

from color_picker import ColorPicker
from canvas import Canvas
from constants import slider_style_sheet
from utils import transform_text_to_kernel
from image_canvas import ImageCanvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Editor')
        self.drawing_canvas = Canvas()
        self.image_canvas = ImageCanvas()
        self.main_options_button_group = QButtonGroup(self)
        self.main_options_button_group.setExclusive(True)
        self.drawing_canvas.tool_changed.connect(self.update_button_state)

        tabs = QTabWidget()
        self.figures_tab = QWidget()
        self.init_figures_tab()
        self.images_tab = QWidget()
        self.init_images_tab()

        tabs.addTab(self.figures_tab, "Figures")
        tabs.addTab(self.images_tab, "Images")

        self.setCentralWidget(tabs)

    def init_figures_tab(self):
        v = QVBoxLayout(self.figures_tab)
        v.setContentsMargins(10, 2, 10, 2)
        v.setSpacing(3)

        # toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        for t in ['select', 'line', 'rect', 'circle']:
            b = QPushButton(t.capitalize())
            b.setCheckable(True)
            if t == 'select':
                b.setChecked(True)
            b.clicked.connect(lambda checked, tt=t: self.set_tool(tt))
            self.main_options_button_group.addButton(b)
            toolbar.addWidget(b)
        v.addLayout(toolbar)

        # text params
        params_layout = QHBoxLayout()
        basic_params_layout = QVBoxLayout()
        self.kind_combo = QComboBox()
        self.kind_combo.addItems(['line', 'rect', 'circle'])
        basic_params_layout.addWidget(self.kind_combo)
        self.params_edit = QLineEdit()
        self.params_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid gray;
                border-radius: 4px;
                padding: 0px;
            }
            QLineEdit:focus {
                border: none;
                outline: none;
            }
        """)
        self.params_edit.setPlaceholderText('param1, param2...')
        self.params_edit.editingFinished.connect(self.params_edit.clearFocus)
        basic_params_layout.addWidget(self.params_edit)

        # buttons
        confirm_buttons_layout = QHBoxLayout()
        confirm_buttons_layout.setSpacing(10)
        confirm_buttons_layout.setContentsMargins(0, 0, 0, 0)
        add_btn = QPushButton('Add')
        add_btn.clicked.connect(self.add_from_text)
        confirm_buttons_layout.addWidget(add_btn)
        update_btn = QPushButton('Update selected')
        update_btn.clicked.connect(self.update_selected)
        confirm_buttons_layout.addWidget(update_btn)
        basic_params_layout.addLayout(confirm_buttons_layout)

        params_layout.addLayout(basic_params_layout)

        # colors
        self.color_picker = ColorPicker()
        params_layout.addWidget(self.color_picker)

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

        v.addWidget(self.drawing_canvas, stretch=1)

        self.color_picker.color_changed.connect(self.drawing_canvas.set_drawing_color_for_new)
        self.resize(900, 600)

    def init_images_tab(self):
        v = QVBoxLayout(self.images_tab)
        v.setContentsMargins(10, 2, 10, 2)
        v.setSpacing(3)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_image_file)
        toolbar.addWidget(load_btn, stretch=True)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_image_file)
        toolbar.addWidget(save_btn, stretch=True)
        
        label = QLabel("Save as: ")
        toolbar.addWidget(label)

        self.format_combo = QComboBox()
        self.format_combo.addItems(['PPM3', 'PPM6', "JPEG"])
        self.format_combo.currentTextChanged.connect(self.handle_format_changes)
        toolbar.addWidget(self.format_combo)

        self.label_compression_level = QLabel("Compression quality: ")
        self.label_compression_level.setVisible(False)
        toolbar.addWidget(self.label_compression_level)

        self.text_compression_level = QLineEdit("80")
        self.text_compression_level.setReadOnly(True)
        self.text_compression_level.setVisible(False)
        self.text_compression_level.setFixedWidth(35)
        toolbar.addWidget(self.text_compression_level)

        self.jpeg_quality_slider = QSlider(Qt.Horizontal)
        self.jpeg_quality_slider.setRange(0, 100)
        self.jpeg_quality_slider.setStyleSheet(slider_style_sheet)
        self.jpeg_quality_slider.setValue(80)
        self.jpeg_quality_slider.setTickPosition(QSlider.TicksBelow)
        self.jpeg_quality_slider.setTickInterval(10)
        self.jpeg_quality_slider.valueChanged.connect(self.update_text_compression_level)
        self.jpeg_quality_slider.setVisible(False)
        toolbar.addWidget(self.jpeg_quality_slider)
        
        v.addLayout(toolbar)

        extra_tools = QHBoxLayout()
        extra_tools.setSpacing(10)

        self.linear_scaling_label = QLineEdit("1")
        self.linear_scaling_label.setReadOnly(True)
        self.linear_scaling_label.setFixedWidth(35)
        extra_tools.addWidget(self.linear_scaling_label)

        self.linear_scaling_slider = QSlider(Qt.Horizontal)
        self.linear_scaling_slider.setRange(1, 100) # 0.1 - 10.0
        self.linear_scaling_slider.setStyleSheet(slider_style_sheet)
        self.linear_scaling_slider.setValue(10)
        self.linear_scaling_slider.setTickPosition(QSlider.TicksBelow)
        self.linear_scaling_slider.setTickInterval(1)
        self.linear_scaling_slider.valueChanged.connect(self.update_linear_scaling_label)
        self.linear_scaling_slider.valueChanged.connect(self.image_canvas.handle_lin_scaling_updated)
        extra_tools.addWidget(self.linear_scaling_slider)

        self.hover_over_color_vals = QLabel("0, 0, 0")
        extra_tools.addWidget(self.hover_over_color_vals)

        v.addLayout(extra_tools)

        filters_toolbar = QHBoxLayout()
        filters_toolbar.setSpacing(10)

        self.filters_button_group = QButtonGroup(self)
        self.filters_button_group.setExclusive(True)

        for button_name in ["mean", "median", "sobel", "sharpening", "gaussian", "conv", "dilation", "erosion", "open", "close", "HoM-thin", "HoM-thicken"]:
            button = QPushButton(button_name)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, filter=button_name : self.filter(filter_type=filter))
            self.filters_button_group.addButton(button)
            filters_toolbar.addWidget(button)

        v.addLayout(filters_toolbar)

        filter_params_layout = QHBoxLayout()
        self.kernel_editor = QTextEdit("")
        self.kernel_editor.setPlaceholderText("Edit kernel where applicable...")
        self.binary_threshold = QSlider(Qt.Vertical)
        self.binary_threshold.setRange(0, 255)
        self.binary_threshold.setStyleSheet(slider_style_sheet)
        self.binary_threshold.setValue(127)
        self.binary_threshold.setTickInterval(5)
        filter_params_layout.addWidget(self.kernel_editor)
        filter_params_layout.addWidget(self.binary_threshold)

        v.addLayout(filter_params_layout)

        self.image_canvas.hover_over_color.connect(self.display_hover_over_color)
        v.addWidget(self.image_canvas, stretch=1)

    def set_tool(self, tool):
        self.drawing_canvas.current_tool = tool

    def add_from_text(self):
        kind = self.kind_combo.currentText()
        txt = self.params_edit.text()
        color_switches = self.color_picker.all_switches
        color_val = (color_switches["R"][0].value(), color_switches["G"][0].value(), color_switches["B"][0].value())
        self.drawing_canvas.add_object_from_text(kind, txt, color_val)
        self.params_edit.setText("")


    def update_selected(self):
        txt = self.params_edit.text()
        color_switches = self.color_picker.all_switches
        color_val = (color_switches["R"][0].value(), color_switches["G"][0].value(), color_switches["B"][0].value())
        self.drawing_canvas.update_selected_from_text(txt, color_val)
        self.params_edit.setText("")

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save JSON', filter='JSON Files (*.json)')
        if path:
            self.drawing_canvas.save_to_file(path)

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open JSON', filter='JSON Files (*.json)')
        if path:
            self.drawing_canvas.load_from_file(path)

    def load_image_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open image')
        if path:
            if path.lower().endswith((".jpg", ".jpeg", "ppm")):
                try:
                    self.image_canvas.load_from_file(path)
                    self.linear_scaling_slider.blockSignals(True)
                    self.linear_scaling_slider.setValue(10)
                    self.linear_scaling_slider.blockSignals(False)
                    self.linear_scaling_label.setText("1.0")
                except Exception as e:
                    QMessageBox.warning(self, "File error", f"Incorrect content of the file!")
            else:
                QMessageBox.warning(self, "File error", "Unsupported extension")

    def save_image_file(self):
        if not self.image_canvas.image:
            QMessageBox.warning(self, "Error", "Load a file first")
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                None,
                "Save Image As",
                "",
                "JPEG Files (*.jpg)"
            )
            if file_path:
                self.image_canvas.image.save(file_path, quality=self.jpeg_quality_slider.value())

    def handle_format_changes(self, curr_new_text):
        if curr_new_text in {"PPM3", "PPM6"}:
            self.label_compression_level.setVisible(False)
            self.text_compression_level.setVisible(False)
            self.jpeg_quality_slider.setVisible(False)
        else:
            self.label_compression_level.setVisible(True)
            self.text_compression_level.setVisible(True)
            self.jpeg_quality_slider.setVisible(True)

    def update_text_compression_level(self, new_value):
        self.text_compression_level.setText(str(new_value))

    def update_linear_scaling_label(self, new_value):
        self.linear_scaling_label.setText(str(round(new_value / 10, 1)))
    
    def update_button_state(self, tool):
        for b in self.main_options_button_group.buttons():
            b.setChecked(b.text().lower() == tool)

    def display_hover_over_color(self, r, g, b):
        self.hover_over_color_vals.setText(f"{r}, {g}, {b}")

    def filter(self, filter_type):
        binary_threshold_for_morphological = self.binary_threshold.value()
        if filter_type in {"HoM-thin", "HoM-thicken", "conv"}:
            if kernel := transform_text_to_kernel(self.kernel_editor.toPlainText()):
                self.image_canvas.filter(filter_type=filter_type, kernel=kernel, bin_threshold=binary_threshold_for_morphological)
            else:
                QMessageBox.warning(self, "Error", "Invalid kernel input. Double check the value")
        else:
            self.image_canvas.filter(filter_type=filter_type, bin_threshold=binary_threshold_for_morphological)
        # maybe also make sure the user selects a binarization level for morphological filters


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
