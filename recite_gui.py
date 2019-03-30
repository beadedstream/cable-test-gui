import sys
import views
import serial_manager
from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication([])
    app.setStyle("fusion")
    window = views.ReciteGui()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()