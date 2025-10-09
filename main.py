import sys

from PySide6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QComboBox, QFileDialog, QButtonGroup
)

from color_picker import ColorPicker
from canvas import Canvas

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Editor')
        self.canvas = Canvas()
        self.main_options_button_group = QButtonGroup(self)
        self.main_options_button_group.setExclusive(True)
        self.canvas.tool_changed.connect(self.update_button_state)

        self.init_ui()

    def init_ui(self):
        # main
        central = QWidget()
        self.setCentralWidget(central)
        v = QVBoxLayout(central)
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
        params_layout.addLayout(basic_params_layout)

        # colors
        self.color_picker = ColorPicker()
        params_layout.addWidget(self.color_picker)

        # buttons
        confirm_buttons_layout = QVBoxLayout()
        confirm_buttons_layout.setSpacing(10)
        add_btn = QPushButton('Add')
        add_btn.clicked.connect(self.add_from_text)
        confirm_buttons_layout.addWidget(add_btn)
        update_btn = QPushButton('Update selected')
        update_btn.clicked.connect(self.update_selected)
        confirm_buttons_layout.addWidget(update_btn)
        params_layout.addLayout(confirm_buttons_layout)
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
    
    def update_button_state(self, tool):
        for b in self.main_options_button_group.buttons():
            b.setChecked(b.text().lower() == tool)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
