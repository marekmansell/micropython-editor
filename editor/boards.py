from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtCore import QIODevice
from time import sleep


class MicroBit:
    def __init__(self):
        pass


class ESP8266:
    def __init__(self):
        pass


class ESP32:
    def __init__(self):
        pass


class Board:
    def __init__(self, port, board, repl_pane):
        self.serial = QSerialPort()
        self.serial.setPortName("/dev/ttyUSB0")
        self.repl_pane = repl_pane
        if self.serial.open(QIODevice.ReadWrite):
            self.serial.setBaudRate(115200)
            self.serial.readyRead.connect(self._on_serial_read)
            self.serial.write(b'\x03') # Send a Control-C
            self._clear_repl() # clear the text
        else:
            raise IOError("Cannot connect to device on port {}".format(port))

    def _on_serial_read(self):
        if self.repl_pane:
            self.repl_pane.process_bytes(bytes(self.serial.readAll()))

    def _clear_repl(self):
        if self.repl_pane:
            self.repl_pane.clear()

    def run(self, command):
        self._enter_raw_repl()
        self._exec(command)
        self._exit_raw_repl()

    def _enter_raw_repl(self):
        print("ss")
        self.serial.write(b'\r\x03\x03') # ctrl-C twice: interrupt any running program
        self.serial.flush()

        self.serial.clear()

        self.serial.write(b'\r\x01') # ctrl-A: enter raw REPL
        sleep(.1)
        self.serial.write(b'\x04') # ctrl-D: soft reset
        sleep(.5)

    def _exit_raw_repl(self):
        self.serial.write(b'\r\x02') # ctrl-B: enter friendly REPL

    def _exec(self, command):
        command_bytes = command + b"\n\r"
        print(command)

        # write command
        for i in range(0, len(command_bytes), 256):
            self.serial.write(command_bytes[i:min(i + 256, len(command_bytes))])
            sleep(0.01)
        self.serial.write(b'\x04')
        self.serial.flush()

    def send(self, msg):
        self.serial.write(msg)

    def stop(self):
        self.serial.write(b'\r\x03\x03') # ctrl-C twice: interrupt any running program

    def reset(self):
        self._exit_raw_repl()
        self.stop()
        self.serial.write(b'\x04') # ctrl-D: soft reset