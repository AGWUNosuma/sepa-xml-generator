from PySide6.QtWidgets import QApplication
import sys
from .ui.main_window import MainWindow

def main() -> int:
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
