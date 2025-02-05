from PyQt5 import QtWidgets
from gui import ezUARTApp
import qdarktheme  # Import the theme

if __name__ == "__main__":
    qdarktheme.enable_hi_dpi()
    app = QtWidgets.QApplication([])
    window = ezUARTApp()
    window.show()
    app.exec()
    