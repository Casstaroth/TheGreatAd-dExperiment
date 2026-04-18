import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QDoubleValidator, QMovie

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CUBE_GIF_PATH = os.path.join(SCRIPT_DIR, "assets", "gifs", "cube.gif")


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
    def __init__(self, gif_path):
        super().__init__("The Cube")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            if self.movie.isValid():
                self.label.setMovie(self.movie)
                self.movie.start()
            else:
                self.label.setText("(Could not load cube.gif)")
        else:
            self.label.setText(f"(GIF not found: {gif_path})")

        layout.addWidget(self.label)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.movement_ratio = 1.0
        self.setWindowTitle("The Great Movinator Unconfusinator")
        self.setMinimumWidth(420)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel("The Great Movinator Unconfusinator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(divider)

        self.ratio_setter = RatioDirectSetter(self._set_ratio, self._get_ratio)

        self.converter = MoveConverter(self._get_ratio)

        self.ratio_calc = RatioCalculator(self._set_ratio, self.ratio_setter)

        self.cube_section = CubeGifSection(CUBE_GIF_PATH)

        layout.addWidget(self.ratio_setter)
        layout.addWidget(self.converter)
        layout.addWidget(self.ratio_calc)
        layout.addWidget(self.cube_section)

    def _get_ratio(self):
        return self.movement_ratio

    def _set_ratio(self, value):
        self.movement_ratio = value
        self.ratio_setter.refresh()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
