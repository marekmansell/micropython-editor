from pathlib import Path
import os
from editor.boards import ESP8266, MicroBit, ESP32
from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtCore import QIODevice
from time import sleep


class EditorLogic:
    """All MicroPython Editor Actions are processed here"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.load_save_path = str(Path.home())
        self.serial = None

    def toggle_blockly_pane(self):
        if self.main_window.blockly_pane:
            self.main_window.rm_blockly_pane()
        else:
            self.main_window.add_blockly_pane()

    def toggle_storage_pane(self):
        if self.main_window.storage_pane:
            self.main_window.rm_storage_pane()
        elif self.serial:
            if self.main_window.repl_pane:
                self.main_window.rm_repl_pane()
            self.main_window.add_storage_pane()

    def toggle_repl_pane(self):
        if self.main_window.repl_pane:
            self.main_window.rm_repl_pane()
        elif self.serial:
            if self.main_window.storage_pane:
                self.main_window.rm_storage_pane()
            self.main_window.add_repl_pane()

    def load(self):
        path = self.main_window.get_load_path(self.load_save_path)
        self.load_save_path = str(Path(path).parent)
        with open(path, 'r') as file:
            content = file.read()
        self.main_window.new_tab(path=path, content=content)

    def save(self):
        tab = self.main_window.get_current_tab()
        if tab is None:
            return
        if tab.path is None:
            tab.path = self.main_window.get_save_path(self.load_save_path)
        if tab.path:
            self.load_save_path = str(Path(tab.path).parent)
            if not os.path.basename(tab.path).endswith('.py'):
                tab.path += '.py'
            with open(tab.path, "w") as f:
                f.write(tab.text_field.text())
            tab.title = os.path.basename(tab.path)
            tab.setModified(False)
        else:
            tab.path = None

    def connect(self, port="/dev/ttyUSB0"):
        self.port = port
        # open the serial port
        self.serial = QSerialPort()
        self.serial.setPortName("/dev/ttyUSB0")
        if self.serial.open(QIODevice.ReadWrite):
            self.serial.setBaudRate(115200)
            self.serial.readyRead.connect(self._on_serial_read)
            self._clear_repl() # clear the text
            self.serial.write(b'\x03') # Send a Control-C
        else:
            raise IOError("Cannot connect to device on port {}".format(port))

    def _on_serial_read(self):
        if self.main_window.repl_pane:
            self.main_window.repl_pane.on_serial_read()

    def _clear_repl(self):
        if self.main_window.repl_pane:
            self.main_window.repl_pane.clear()

    def run(self, command):
        self.enter_raw_repl()
        self.exec_(command)
        self.exit_raw_repl()

    def run_tab(self):
        tab = self.main_window.get_current_tab()
        if tab is None:
            return
        self.run(tab.text_field.text().strip())

    def enter_raw_repl(self):
        print("ss")
        self.serial.write(b'\r\x03\x03') # ctrl-C twice: interrupt any running program
        self.serial.flush()

        self.serial.clear()

        self.serial.write(b'\r\x01') # ctrl-A: enter raw REPL
        sleep(.1)
        self.serial.write(b'\x04') # ctrl-D: soft reset
        sleep(.5)

    def exit_raw_repl(self):
        self.serial.write(b'\r\x02') # ctrl-B: enter friendly REPL

    def exec_(self, command):
        command_bytes = command.encode() + "\n\r".encode()

        # write command
        for i in range(0, len(command_bytes), 256):
            self.serial.write(command_bytes[i:min(i + 256, len(command_bytes))])
            sleep(0.01)
        self.serial.write(b'\x04')
        self.serial.flush()

    def stop(self):
        pass

    def reset(self):
        pass
