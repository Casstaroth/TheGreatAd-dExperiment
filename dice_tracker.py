import sys
import json
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QFrame, QMessageBox, QFileDialog,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


FACES = ("top", "front", "bottom", "back", "left", "right")


class DiceState:
    def __init__(self):
        self.faces = {name: "" for name in FACES}

    def rotate_forward(self):
        # Top tilts toward the front: top -> front -> bottom -> back -> top
        t, f, bo, ba = self.faces["top"], self.faces["front"], self.faces["bottom"], self.faces["back"]
        self.faces["front"] = t
        self.faces["bottom"] = f
        self.faces["back"] = bo
        self.faces["top"] = ba

    def rotate_backward(self):
        # Top tilts away: top -> back -> bottom -> front -> top
        t, f, bo, ba = self.faces["top"], self.faces["front"], self.faces["bottom"], self.faces["back"]
        self.faces["back"] = t
        self.faces["bottom"] = ba
        self.faces["front"] = bo
        self.faces["top"] = f

    def rotate_right(self):
        # Top tilts to the right: top -> right -> bottom -> left -> top
        t, r, bo, l = self.faces["top"], self.faces["right"], self.faces["bottom"], self.faces["left"]
        self.faces["right"] = t
        self.faces["bottom"] = r
        self.faces["left"] = bo
        self.faces["top"] = l

    def rotate_left(self):
        # Top tilts to the left: top -> left -> bottom -> right -> top
        t, r, bo, l = self.faces["top"], self.faces["right"], self.faces["bottom"], self.faces["left"]
        self.faces["left"] = t
        self.faces["bottom"] = l
        self.faces["right"] = bo
        self.faces["top"] = r

    def to_dict(self):
        return dict(self.faces)

    def load_dict(self, data):
        for name in FACES:
            value = data.get(name, "")
            self.faces[name] = "" if value is None else str(value)


class FaceWidget(QGroupBox):
    def __init__(self, label, on_change):
        super().__init__(label.upper())
        self._on_change = on_change
        self._face_name = label
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(120, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 18, 8, 8)

        self.input = QLineEdit()
        self.input.setPlaceholderText("(blank)")
        self.input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.input.setFont(font)
        self.input.textEdited.connect(self._handle_edit)

        layout.addWidget(self.input)

    def _handle_edit(self, text):
        self._on_change(self._face_name, text)

    def set_value(self, text):
        if self.input.text() != text:
            self.input.blockSignals(True)
            self.input.setText(text)
            self.input.blockSignals(False)


class DiceView(QGroupBox):
    """Cross-layout view of the unfolded cube."""

    def __init__(self, state, on_face_changed):
        super().__init__("Dice Faces")
        self.state = state
        self.on_face_changed = on_face_changed

        grid = QGridLayout(self)
        grid.setSpacing(8)

        self.face_widgets = {name: FaceWidget(name, self._face_edited) for name in FACES}

        # Cross layout:
        #   .    Top    .     .
        # Left Front Right Back
        #   .   Bottom  .     .
        grid.addWidget(self.face_widgets["top"],    0, 1)
        grid.addWidget(self.face_widgets["left"],   1, 0)
        grid.addWidget(self.face_widgets["front"],  1, 1)
        grid.addWidget(self.face_widgets["right"],  1, 2)
        grid.addWidget(self.face_widgets["back"],   1, 3)
        grid.addWidget(self.face_widgets["bottom"], 2, 1)

        for col in range(4):
            grid.setColumnStretch(col, 1)
        for row in range(3):
            grid.setRowStretch(row, 1)

        self.refresh()

    def _face_edited(self, name, text):
        self.state.faces[name] = text
        self.on_face_changed()

    def refresh(self):
        for name, widget in self.face_widgets.items():
            widget.set_value(self.state.faces[name])


class RotationControls(QGroupBox):
    def __init__(self, state, on_rotated):
        super().__init__("Rotation")
        self.state = state
        self.on_rotated = on_rotated

        layout = QGridLayout(self)
        layout.setSpacing(8)

        self.btn_forward = QPushButton("↑ Forward\n(top → front)")
        self.btn_backward = QPushButton("↓ Backward\n(top → back)")
        self.btn_left = QPushButton("← Left\n(top → left)")
        self.btn_right = QPushButton("→ Right\n(top → right)")

        self.btn_forward.clicked.connect(self._do(state.rotate_forward))
        self.btn_backward.clicked.connect(self._do(state.rotate_backward))
        self.btn_left.clicked.connect(self._do(state.rotate_left))
        self.btn_right.clicked.connect(self._do(state.rotate_right))

        for btn in (self.btn_forward, self.btn_backward, self.btn_left, self.btn_right):
            btn.setMinimumHeight(50)

        # D-pad layout
        layout.addWidget(self.btn_forward,  0, 1)
        layout.addWidget(self.btn_left,     1, 0)
        layout.addWidget(self.btn_right,    1, 2)
        layout.addWidget(self.btn_backward, 2, 1)

        for col in range(3):
            layout.setColumnStretch(col, 1)

    def _do(self, action):
        def handler():
            action()
            self.on_rotated()
        return handler


class FileControls(QGroupBox):
    def __init__(self, state, on_loaded):
        super().__init__("Save / Load")
        self.state = state
        self.on_loaded = on_loaded

        layout = QHBoxLayout(self)
        layout.setSpacing(8)

        save_btn = QPushButton("Save…")
        load_btn = QPushButton("Load…")
        clear_btn = QPushButton("Clear All")

        save_btn.clicked.connect(self._save)
        load_btn.clicked.connect(self._load)
        clear_btn.clicked.connect(self._clear)

        layout.addWidget(save_btn)
        layout.addWidget(load_btn)
        layout.addWidget(clear_btn)

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Dice State", "dice.json", "JSON files (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.state.to_dict(), f, indent=2)
        except OSError as e:
            QMessageBox.warning(self, "Save failed", str(e))

    def _load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Dice State", "", "JSON files (*.json);;All files (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            QMessageBox.warning(self, "Load failed", str(e))
            return
        if not isinstance(data, dict):
            QMessageBox.warning(self, "Load failed", "File does not contain a dice state.")
            return
        self.state.load_dict(data)
        self.on_loaded()

    def _clear(self):
        confirm = QMessageBox.question(
            self, "Clear all faces", "Reset every face to blank?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        for name in FACES:
            self.state.faces[name] = ""
        self.on_loaded()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = DiceState()
        self.setWindowTitle("Dice Position Tracker")
        self.setMinimumSize(700, 500)
        self.resize(900, 600)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setSpacing(12)
        outer.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Dice Position Tracker")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(divider)

        self.dice_view = DiceView(self.state, self._noop)
        self.rotation = RotationControls(self.state, self._after_rotation)
        self.file_controls = FileControls(self.state, self._after_load)

        outer.addWidget(self.dice_view, stretch=3)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        bottom.addWidget(self.rotation, stretch=2)
        bottom.addWidget(self.file_controls, stretch=1)
        outer.addLayout(bottom, stretch=1)

    def _noop(self):
        pass

    def _after_rotation(self):
        self.dice_view.refresh()

    def _after_load(self):
        self.dice_view.refresh()


DARK_STYLESHEET = """
QWidget {
    background-color: #151515;
    color: #ffffff;
}
QGroupBox {
    border: 1px solid #ffffff;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 8px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #ffffff;
}
QLineEdit {
    background-color: #151515;
    color: #ffffff;
    border: 1px solid #ffffff;
    border-radius: 3px;
    padding: 4px;
    selection-background-color: #444444;
}
QPushButton {
    background-color: #151515;
    color: #ffffff;
    border: 1px solid #ffffff;
    border-radius: 3px;
    padding: 6px 12px;
}
QPushButton:hover {
    background-color: #2a2a2a;
}
QPushButton:pressed {
    background-color: #3a3a3a;
}
QFrame[frameShape="4"] {
    color: #ffffff;
    background-color: #ffffff;
}
QMessageBox {
    background-color: #151515;
    color: #ffffff;
}
"""


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
