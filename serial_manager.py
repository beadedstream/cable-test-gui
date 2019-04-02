import re
import time
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class SerialManager(QObject):
    port_unavailable_signal = pyqtSignal()
    version_check_signal = pyqtSignal(bool)
    serial_error_signal = pyqtSignal()
    cable_values_signal = pyqtSignal(list, int, dict)
    no_sensors_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ser = serial.Serial(port=None, baudrate=115200,
                    parity=serial.PARITY_NONE,
                    bytesize=serial.EIGHTBITS,
                    stopbits=serial.STOPBITS_ONE, timeout=40)
        self.end = b"\r\n>"

    def scan_ports():
        return serial.tools.list_ports.comports()

    def is_connected(self, port):
        return self.ser.port == port and self.ser.is_open

    def open_port(self, port):
        try:
            self.ser.close()
            self.ser.port = port
            self.ser.open()
        except serial.serialutil.SerialException:
            self.port_unavailable_signal.emit()

    def flush_buffers(self):
        self.ser.write("\r\n".encode())
        time.sleep(0.5)
        self.ser.read(self.ser.in_waiting)

    def close_port(self):
        self.ser.close()

    @pyqtSlot()
    def check_version(self):
        command = "version"
        p = "SDI12/RS485 BRIDGE MAIN APP [0-9]+\.[0-9]+[a-z]"
        if self.ser.is_open:
            try:
                self.flush_buffers()
                # Send individual chars and wait for echo back,
                # because half-duplex with no control flow.
                for c in command:
                    self.ser.write(c.encode())
                    self.ser.flush()
                    time.sleep(0.05)
                    self.ser.read(self.ser.in_waiting)

                self.ser.write(b"\r\n")
                self.ser.flush()
                time.sleep(0.1)
                try:
                    response = self.ser.read_until(self.end).decode()
                except UnicodeDecodeError:
                    self.serial_error_signal.emit()
                    return

                # Ensure version matches format, otherwise emit error signal.
                if re.search(p, response):
                    self.version_check_signal.emit(True)
                else:
                    self.version_check_signal.emit(False)
                    return

            except serial.serialutil.SerialException:
                self.port_unavailable_signal.emit()
        else:
            self.port_unavailable_signal.emit()

    @pyqtSlot()
    def read_cables(self):
        ids_cmd = "tac-get-info v\r\n"
        temps_cmd = "temps\r\n"
        temps_dict = {}

        p1 = r"((?:[0-9a-fA-F][0-9a-fA-F][ \t]+){8})"
        p2 = r"([0-9]+) sensors"
        p3 = r"((?:[0-9a-fA-F][0-9a-fA-F][ \t]+){6})(temp =\s+[0-9]+\.[0-9]+ C)"
        p4 = r"[0-9]+\.[0-9]+"

        if self.ser.is_open:
            try:
                self.ser.flush()

                self.flush_buffers()

                for c in ids_cmd:
                    self.ser.write(c.encode())
                    self.ser.flush()
                    time.sleep(0.05)
                    self.ser.read(self.ser.in_waiting)
                    
                try:
                    response = self.ser.read_until(self.end).decode()
                except UnicodeDecodeError:
                    self.serial_error_signal.emit()
                    return

                # Check for 0 sensors read response, don't match on 
                # 10, 20, 30, etc sensors so use re.match to get beginning of
                # string.
                if re.match("0 sensors", response.strip()):
                    self.no_sensors_signal.emit()
                    return
                else:
                    boards = re.findall(p1, response)

                try:
                    sensor_num = int(re.search(p2, response).group(1))
                except (IndexError, AttributeError) as err:
                    self.serial_error_signal.emit()
                    return

                # Remove extra spaces
                for b, board in enumerate(boards):
                    board = board.strip().replace("  ", " ")
                    boards[b] = board

                self.ser.flush()
                self.flush_buffers()

                for c in temps_cmd:
                    self.ser.write(c.encode())
                    self.ser.flush()
                    time.sleep(0.05)
                    self.ser.read(self.ser.in_waiting)

                try:
                    response = self.ser.read_until(self.end).decode()
                except UnicodeDecodeError:
                    self.serial_error_signal.emit()
                    return

                matches = re.findall(p3, response)

                if matches:
                    for match in matches:
                        board_id = match[0].strip()

                        t = re.search(p4, match[1]).group()

                        if t:
                            temp = float(t)
                        else:
                            self.serial_error_signal.emit()
                            return

                        temps_dict[board_id] = temp

                    self.cable_values_signal.emit(boards, sensor_num,
                                                  temps_dict)
                else:
                    self.no_temps_signal.emit()
                    return

            except serial.serialutil.SerialException:
                self.port_unavailable_signal.emit()

        else:
            self.port_unavailable_signal.emit()

