import re
import os
import sys
import serial_manager
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QVBoxLayout, QApplication, QLabel,
    QLineEdit, QComboBox, QGridLayout, QGroupBox, QHBoxLayout,
    QMessageBox, QAction, QActionGroup, QFileDialog, QDialog, QMenu,
    QDesktopWidget, QTextEdit
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import QSettings, Qt, QThread, pyqtSignal

VERSION_NUM = "0.1.0"

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 720

ABOUT_TEXT = f"""
             Recite Cable Tester GUI. Copyright Beaded Streams, 2019.
             v{VERSION_NUM}
             """


class ReciteGui(QMainWindow):
    test_version_signal = pyqtSignal()
    read_cables_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.sm = serial_manager.SerialManager()
        self.serial_thread = QThread()
        self.sm.moveToThread(self.serial_thread)
        self.serial_thread.start()

        self.test_version_signal.connect(self.sm.check_version)
        self.read_cables_signal.connect(self.sm.read_cables)
        self.sm.version_check_signal.connect(self.version_check)
        self.sm.port_unavailable_signal.connect(self.port_unavailable)
        self.sm.serial_error_signal.connect(self.serial_error)
        self.sm.cable_values_signal.connect(self.display_cables)
        self.sm.no_sensors_signal.connect(self.no_sensors)

        self.port_name = None

        self.system_font = QApplication.font().family()
        self.label_font = QFont(self.system_font, 14)
        self.sensor_font = QFont(self.system_font, 12)

        self.quit = QAction("Quit/退出；結束", self)
        self.quit.setShortcut("Ctrl+Q")
        self.quit.setStatusTip("Exit Program/退出；結束")
        self.quit.triggered.connect(self.close)

        self.about_tu = QAction("About Test Utility", self)
        self.about_tu.setShortcut("Ctrl+U")
        self.about_tu.setStatusTip("About Program")
        self.about_tu.triggered.connect(self.about_program)

        self.aboutqt = QAction("About Qt", self)
        self.aboutqt.setShortcut("Ctrl+I")
        self.aboutqt.setStatusTip("About Qt")
        self.aboutqt.triggered.connect(self.about_qt)

        # Create menubar
        self.menubar = self.menuBar()
        self.file_menu = self.menubar.addMenu("&File/文件")
        self.file_menu.addAction(self.quit)

        self.serial_menu = self.menubar.addMenu("&Serial/串行端口")
        self.serial_menu.installEventFilter(self)
        self.ports_menu = QMenu("&Ports/串行端口", self)
        self.serial_menu.addMenu(self.ports_menu)
        self.ports_menu.aboutToShow.connect(self.populate_ports)
        self.ports_group = QActionGroup(self)
        self.ports_group.triggered.connect(self.connect_port)

        self.help_menu = self.menubar.addMenu("&Help/帮助")
        self.help_menu.addAction(self.about_tu)
        self.help_menu.addAction(self.aboutqt)

        self.center()

        self.initUI()

    # Get logo path
    def resource_path(self, relative_path):
         if hasattr(sys, '_MEIPASS'):
             return os.path.join(sys._MEIPASS, relative_path)
         return os.path.join(os.path.abspath("."), relative_path)

    def initUI(self):
        RIGHT_SPACING = 350
        LINE_EDIT_WIDTH = 200
        self.central_widget = QWidget()

        self.start_btn = QPushButton("Start Cable Test / 开始测试")
        self.start_btn.setFixedWidth(350)
        self.start_btn.setAutoDefault(True)
        self.start_btn.setFont(self.label_font)
        self.start_btn.clicked.connect(self.start)

        self.logo_img = QPixmap(self.resource_path("h_logo.png"))
        self.logo_img = self.logo_img.scaledToWidth(600)
        self.logo = QLabel()
        self.logo.setPixmap(self.logo_img)

        hbox_logo = QHBoxLayout()
        hbox_logo.addStretch()
        hbox_logo.addWidget(self.logo)
        hbox_logo.addStretch()

        hbox_start_btn = QHBoxLayout()
        hbox_start_btn.addStretch()
        hbox_start_btn.addWidget(self.start_btn)
        hbox_start_btn.addStretch()

        vbox = QVBoxLayout()
        vbox.addStretch()
        vbox.addLayout(hbox_logo)
        vbox.addSpacing(100)
        vbox.addLayout(hbox_start_btn)
        vbox.addStretch()

        self.central_widget.setLayout(vbox)
        self.setCentralWidget(self.central_widget)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setWindowTitle("BeadedStream Cable Test Utility")

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def about_program(self):
        QMessageBox.about(self, "About TestUtility", ABOUT_TEXT)

    def about_qt(self):
        QMessageBox.aboutQt(self, "About Qt")

    def populate_ports(self):
        ports = serial_manager.SerialManager.scan_ports()
        self.ports_menu.clear()

        if not ports:
            self.ports_menu.addAction("None/无连接")
            self.sm.close_port()

        for port in ports:
            port_description = str(port)[:-6]
            action = self.ports_menu.addAction(port_description)
            self.port_name = port_description[0:4]
            if self.sm.is_connected(self.port_name):
                action.setCheckable(True)
                action.setChecked(True)
            self.ports_group.addAction(action)

    def connect_port(self, action):
        p = "COM[0-9]+"
        self.port_name = re.search(p, action.text()).group()
        if (self.sm.is_connected(self.port_name)):
            action.setChecked

        self.sm.open_port(self.port_name)

    def port_unavailable(self):
        QMessageBox.warning(self, "Warning", "Port unavailable!\n"
                            "没有串行端口")

    def serial_error(self):
        QMessageBox.warning(self, "Serial Error/串行端口错误", "Serial error! "
                            "Please try the operation again.\n"
                            "串行端口错误")
        self.setup_page2()

    def closeEvent(self, event):
        event.accept()

        quit_msg = "Are you sure you want to exit the program?"
        confirmation = QMessageBox.question(self, 'Message',
                                            quit_msg, QMessageBox.Yes,
                                            QMessageBox.No)

        if confirmation == QMessageBox.Yes:
            self.serial_thread.quit()
            self.serial_thread.wait()
            event.accept()
        else:
            event.ignore()

    def start(self):
        if not self.sm.is_connected(self.port_name):
            QMessageBox.warning(self, "Warning", "No serial port selected!\n"
                                 "未选串行端口")
        else:
            self.test_version_signal.emit()
    
    def version_check(self, result):
        if result:
            self.setup_page2()
        else:
            QMessageBox.warning(self, "Serial Error/串行端口错误", "No communication. "
                "Please make sure the Recite is powered and the cables are "
                "properly connected to computer.")

    def setup_page2(self):
        central_widget = QWidget()

        self.lbl = QLabel("Read sensors/读传感器")
        self.lbl.setFont(self.label_font)

        self.read_cables_btn = QPushButton("Read sensors/读传感器")
        self.read_cables_btn.clicked.connect(self.test_cables)

        self.hbox = QHBoxLayout()
        self.hbox.addWidget(self.lbl)
        self.hbox.addWidget(self.read_cables_btn)

        self.sensors = QLineEdit()
        self.sensors.setReadOnly(True)
        self.sensors.setFont(self.sensor_font)

        self.box1 = QTextEdit()
        self.box1.setReadOnly(True)
        self.box1.setFont(self.sensor_font)
        self.box2 = QTextEdit()
        self.box2.setReadOnly(True)
        self.box2.setFont(self.sensor_font)
        self.box3 = QTextEdit()
        self.box3.setReadOnly(True)
        self.box3.setFont(self.sensor_font)
        self.box4 = QTextEdit()
        self.box4.setReadOnly(True)
        self.box4.setFont(self.sensor_font)

        self.grid = QGridLayout()
        self.grid.setVerticalSpacing(10)
        self.grid.setHorizontalSpacing(15)

        self.grid.addLayout(self.hbox, 0, 0)
        self.grid.addWidget(self.sensors, 0, 1, 1, 2)
        self.grid.addWidget(self.box1, 1, 0, 8, 1)
        self.grid.addWidget(self.box2, 1, 1, 8, 1)
        self.grid.addWidget(self.box3, 1, 2, 8, 1)
        self.grid.addWidget(self.box4, 0, 3, 9, 1)

        central_widget.setLayout(self.grid)

        self.setCentralWidget(central_widget)

    def test_cables(self):
        self.lbl.setText("Reading.../读取...")
        self.read_cables_btn.setEnabled(False)
        self.sensors.clear()
        self.box1.clear()
        self.box2.clear()
        self.box3.clear()
        self.box4.clear()
        self.read_cables_signal.emit()

    def display_cables(self, boards_list, sensor_num, temps_dict):

        self.lbl.setText("Finished./完毕")
        self.read_cables_btn.setEnabled(True)
        self.sensors.setText(f"{sensor_num} sensors found")

        failed_sensors = self.check_cable_temps(temps_dict)

        # Display 30 boards each in first three box
        # remaining boards in the last one. There should be no more than 125
        # sensors. 
        boxes = [self.box1, self.box2, self.box3, self.box4]
        box_capacities = [30, 30, 30, 35]
        boards_list.reverse()

        box_num = 0
        list_num = 1
        temp = None

        while len(boards_list):
            for i in range(0, box_capacities[box_num]):
                try:
                    sensor_id = boards_list.pop()
                except IndexError:
                    break

                # Trim it to six bytes to match the ids from the temps
                sensor_id_temp = sensor_id[3:-3]

                if sensor_id_temp in failed_sensors:
                    temp = failed_sensors[sensor_id_temp]
                    sensor_text = (f" {list_num}) {sensor_id} FAILED {temp}")
                    boxes[box_num].setTextColor(Qt.red)
                else:
                    sensor_text = f" {list_num}) {sensor_id}"
                    boxes[box_num].setTextColor(Qt.black)

                # Add a blank line every ten sensors
                if not list_num % 10:
                    sensor_text += "\n"

                boxes[box_num].append(sensor_text)
                list_num += 1

            box_num += 1

    def check_cable_temps(self, temps):
        failed = {}
        for sensor, temp in temps.items():
            if temp > 75.0:
                failed[sensor] = temp
        return failed

    def no_sensors(self):
        self.setup_page2()
        self.sensors.setText("0 sensors found")