import sys
import os
import random
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QFrame, QMessageBox,
    QSizePolicy, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QDoubleValidator, QMovie

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CUBE_GIF_PATH = os.path.join(SCRIPT_DIR, "assets", "gifs", "cube.gif")
SPOOKS_DIR = os.path.join(SCRIPT_DIR, "assets", "gifs", "spooks")


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MoveConverter(QGroupBox):
    def __init__(self, get_ratio):
        super().__init__("Movement Converter")
        self.get_ratio = get_ratio
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        intended_label = QLabel("Intended Movement / Movement Expended:")
        self.intended_input = QLineEdit()
        self.intended_input.setPlaceholderText("Enter value...")
        self.intended_input.setValidator(QDoubleValidator())

        actual_label = QLabel("Actual Movement:")
        self.actual_input = QLineEdit()
        self.actual_input.setPlaceholderText("Enter value...")
        self.actual_input.setValidator(QDoubleValidator())

        calc_btn = QPushButton("Calculate")
        calc_btn.clicked.connect(self._calculate)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear)

        btn_row = QHBoxLayout()
        btn_row.addWidget(calc_btn)
        btn_row.addWidget(clear_btn)

        layout.addWidget(intended_label)
        layout.addWidget(self.intended_input)
        layout.addWidget(actual_label)
        layout.addWidget(self.actual_input)
        layout.addLayout(btn_row)

    def _calculate(self):
        ratio = self.get_ratio()
        if ratio == 0:
            QMessageBox.warning(self, "Error", "Movement ratio is 0 — cannot calculate.")
            return

        intended_text = self.intended_input.text().strip()
        actual_text = self.actual_input.text().strip()

        both_filled = intended_text and actual_text
        neither_filled = not intended_text and not actual_text

        if neither_filled:
            QMessageBox.information(self, "Input needed", "Fill in one of the two boxes to calculate.")
            return
        if both_filled:
            QMessageBox.information(self, "Input needed", "Clear one box — only one should be filled.")
            return

        if intended_text:
            intended = float(intended_text)
            self.actual_input.setText(f"{round(intended * ratio, 1):g}")
        else:
            actual = float(actual_text)
            self.intended_input.setText(f"{round(actual / ratio, 1):g}")

    def _clear(self):
        self.intended_input.clear()
        self.actual_input.clear()


class RatioDirectSetter(QGroupBox):
    def __init__(self, set_ratio, get_ratio):
        super().__init__("GM Movement Ratio")
        self.set_ratio = set_ratio
        self.get_ratio = get_ratio
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.ratio_display = QLabel()
        self._refresh_display()
        self.ratio_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.ratio_display.setFont(font)

        input_label = QLabel("Set ratio directly:")
        self.ratio_input = QLineEdit()
        self.ratio_input.setPlaceholderText("Enter ratio...")
        self.ratio_input.setValidator(QDoubleValidator(0.0001, 99999.0, 6))

        set_btn = QPushButton("Set Ratio")
        set_btn.clicked.connect(self._apply)

        layout.addWidget(QLabel("Current Ratio:"))
        layout.addWidget(self.ratio_display)
        layout.addWidget(input_label)
        layout.addWidget(self.ratio_input)
        layout.addWidget(set_btn)

    def _apply(self):
        text = self.ratio_input.text().strip()
        if not text:
            QMessageBox.information(self, "Input needed", "Enter a ratio value.")
            return
        value = float(text)
        if value == 0:
            QMessageBox.warning(self, "Invalid", "Ratio cannot be zero.")
            return
        self.set_ratio(value)
        self.ratio_input.clear()

    def refresh(self):
        self._refresh_display()

    def _refresh_display(self):
        self.ratio_display.setText(f"{self.get_ratio():g}")


class RatioCalculator(QGroupBox):
    def __init__(self, set_ratio, ratio_display_widget):
        super().__init__("Ratio Setter Calculator")
        self.set_ratio = set_ratio
        self.ratio_display_widget = ratio_display_widget
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        wanted_label = QLabel("I wanted to move:")
        self.wanted_input = QLineEdit()
        self.wanted_input.setPlaceholderText("Enter value...")
        self.wanted_input.setValidator(QDoubleValidator(0.0001, 99999.0, 6))

        moved_label = QLabel("I moved:")
        self.moved_input = QLineEdit()
        self.moved_input.setPlaceholderText("Enter value...")
        self.moved_input.setValidator(QDoubleValidator(0.0001, 99999.0, 6))

        calc_btn = QPushButton("Calculate & Set Ratio")
        calc_btn.clicked.connect(self._calculate)

        layout.addWidget(wanted_label)
        layout.addWidget(self.wanted_input)
        layout.addWidget(moved_label)
        layout.addWidget(self.moved_input)
        layout.addWidget(calc_btn)

    def _calculate(self):
        wanted_text = self.wanted_input.text().strip()
        moved_text = self.moved_input.text().strip()

        if not wanted_text or not moved_text:
            QMessageBox.information(self, "Input needed", "Fill in both boxes.")
            return

        wanted = float(wanted_text)
        moved = float(moved_text)

        if wanted == 0:
            QMessageBox.warning(self, "Invalid", '"I wanted to move" cannot be zero.')
            return

        new_ratio = moved / wanted
        self.set_ratio(new_ratio)
        self.wanted_input.clear()
        self.moved_input.clear()


class CubeGifSection(QGroupBox):
    EASTER_EGG_DURATION_MS = 3000

    def __init__(self, primary_path, easter_egg_dir):
        super().__init__("The Cube")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = ClickableLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.label.setMinimumSize(1, 1)
        self.label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label.clicked.connect(self._trigger_easter_egg)

        self._primary = self._load_movie(primary_path)
        self._easter_eggs = self._load_easter_eggs(easter_egg_dir)
        self._active = None

        self._revert_timer = QTimer(self)
        self._revert_timer.setSingleShot(True)
        self._revert_timer.timeout.connect(self._revert_to_primary)

        if self._primary:
            self._set_active(self._primary)
        else:
            self.label.setText(f"(GIF not found: {primary_path})")

        layout.addWidget(self.label)

    def _load_movie(self, path):
        if not os.path.exists(path):
            return None
        movie = QMovie(path)
        if not movie.isValid():
            return None
        movie.jumpToFrame(0)
        return {"movie": movie, "size": movie.currentPixmap().size()}

    def _load_easter_eggs(self, directory):
        if not os.path.isdir(directory):
            return []
        entries = []
        for name in sorted(os.listdir(directory)):
            if name.lower().endswith(".gif"):
                entry = self._load_movie(os.path.join(directory, name))
                if entry:
                    entries.append(entry)
        return entries

    def _set_active(self, entry):
        if self._active and self._active is not entry:
            self._active["movie"].stop()
        self._active = entry
        self.label.setMovie(entry["movie"])
        entry["movie"].start()
        self._rescale_gif()

    def _trigger_easter_egg(self):
        if not self._easter_eggs:
            return
        if self._active is not None and self._active is not self._primary:
            return
        self._set_active(random.choice(self._easter_eggs))
        self._revert_timer.start(self.EASTER_EGG_DURATION_MS)

    def _revert_to_primary(self):
        if self._primary and self._active is not self._primary:
            self._set_active(self._primary)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale_gif()

    def _rescale_gif(self):
        if not self._active:
            return
        native = self._active["size"]
        if native.isEmpty():
            return
        target = native.scaled(
            self.label.size(), Qt.AspectRatioMode.KeepAspectRatio
        )
        if not target.isEmpty():
            self._active["movie"].setScaledSize(target)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.movement_ratio = 1.0
        self.setWindowTitle("The Great Movinator Unconfusinator")
        self.setMinimumSize(600, 500)
        self.resize(900, 700)
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.setCentralWidget(scroll)

        central = QWidget()
        scroll.setWidget(central)
        outer = QVBoxLayout(central)
        outer.setSpacing(12)
        outer.setContentsMargins(16, 16, 16, 16)

        title = QLabel("The Great Movinator Unconfusinator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        outer.addWidget(divider)

        self.ratio_setter = RatioDirectSetter(self._set_ratio, self._get_ratio)
        self.converter = MoveConverter(self._get_ratio)
        self.ratio_calc = RatioCalculator(self._set_ratio, self.ratio_setter)
        self.cube_section = CubeGifSection(CUBE_GIF_PATH, SPOOKS_DIR)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(self.converter,     0, 0)
        grid.addWidget(self.ratio_setter,  0, 1)
        grid.addWidget(self.cube_section,  1, 0)
        grid.addWidget(self.ratio_calc,    1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 0)
        grid.setRowStretch(1, 1)

        outer.addLayout(grid, stretch=1)

    def _get_ratio(self):
        return self.movement_ratio

    def _set_ratio(self, value):
        self.movement_ratio = value
        self.ratio_setter.refresh()


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
QScrollArea {
    border: none;
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
