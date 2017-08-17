from serial import Serial
from time import sleep, time
from threading import Thread, RLock
from queue import Queue
from PyQt5.QtCore import pyqtSignal, QObject
import textwrap

BUFFER_SIZE = 32

BOARDS = ["ESP8266", "ESP32", "STM32", "MicroBit"]

class BoardError(BaseException):
    pass

class MicroBit:
    def __init__(self):
        pass


class ESP8266:
    def __init__(self):
        pass


class ESP32:
    def __init__(self):
        pass


class Board(QObject):
    receive_signal = pyqtSignal(bytes)
    def __init__(self, port, board, repl_pane, icon_update):
        super().__init__()
        self.serial = Serial(port, baudrate=115200, timeout=.2)
        self.serial.flushInput()
        self._input_queue = Queue()
        self.repl_pane = repl_pane
        self.icon_update = icon_update
        self.send(b'\r\x03\x03') # ctrl-C twice: interrupt any running program
        self._clear_repl() # clear the text
        self.running = True
        self.receive_signal.connect(self._on_serial_read)
        self.serial_thread = Thread(target=self._serial_listener)
        self.serial_thread.start()

    def _serial_listener(self):
        try:
            while self.running:
                if self.serial.in_waiting:
                    msg = self.serial.read(1)
                    self._input_queue.put(msg)
                    self.receive_signal.emit(msg)
                else:
                    sleep(.01)
        except:
            self.icon_update(connected=False)
            if self.serial:
                self.serial.close()

    def _on_serial_read(self, msg):
        if self.repl_pane:
            self.repl_pane.process_bytes(msg)

    def _clear_repl(self):
        if self.repl_pane:
            self.repl_pane.clear()

    def _input_queue_reset(self):
        while not self._input_queue.empty():
            _ = self._input_queue.get()

    def run(self, command):
        self.enter_raw_repl()
        self.exec_(command)
        self.exit_raw_repl()


    def send(self, msg):
        if not type(msg) is bytes:
            msg = bytes(msg, 'utf-8')
        self.serial.write(msg)

    def stop(self):
        self.send(b'\r\x03\x03') # ctrl-C twice: interrupt any running program

    def reset(self):
        self.send(b'\r\x02') # ctrl-B: enter friendly REPL
        self.send(b'\r\x03\x03') # ctrl-C twice: interrupt any running program
        self.send(b'\x04') # ctrl-D: soft reset

    def close(self):
        self.running = False
        self.serial_thread.join()
        if self.serial:
            self.serial.close()
        self.serial = None
        print("Closed Properly")

    def _read_until(self, data, timeout=10):
        start_t = time()
        input_stream = b""
        while time() < (start_t + timeout):
            if not self._input_queue.empty():
                input_stream += self._input_queue.get()
            if input_stream.endswith(data):
                break
        return input_stream

    def flash(self, filename, data):
        written_bytes = 0
        total_size = len(data)
        self.enter_raw_repl()
        self.exec_("f = open('{0}', 'wb')".format(filename))
        size = len(data)
        # Loop through and write a buffer size chunk of data at a time.
        for i in range(0, size, BUFFER_SIZE):
            chunk_size = min(BUFFER_SIZE, size-i)
            chunk = repr(data[i:i+chunk_size])
            # Make sure to send explicit byte strings (handles python 2 compatibility).
            if not chunk.startswith('b'):
                chunk = 'b' + chunk
            self.exec_("f.write({0})".format(chunk))
            written_bytes += BUFFER_SIZE
            print("{} bytes written of {}".format(written_bytes, total_size))
        self.exec_('f.close()')
        self.exit_raw_repl()

    def enter_raw_repl(self):
        self.send(b'\r\x03\x03') # ctrl-C twice: interrupt any running program

        self.send(b'\r\x01') # ctrl-A: enter raw REPL

        self.send(b'\x04') # ctrl-D: soft reset
        #   Add a small delay and send Ctrl-C twice after soft reboot to ensure
        #   any main program loop in main.py is interrupted.
        sleep(0.5)
        self.send(b'\x03\x03')

    def exit_raw_repl(self):
        self.send(b'\r\x02') # ctrl-B: enter friendly REPL

    def exec_(self, command):
        if isinstance(command, bytes):
            command_bytes = command
        else:
            command_bytes = bytes(command, encoding='utf8')

        # write command
        for i in range(0, len(command_bytes), 256):
            self.send(command_bytes[i:min(i + 256, len(command_bytes))])
            sleep(0.1)
        self.send(b'\x04')

        data = self._read_until(b"OK")
        if not data.endswith(b"OK"):
            raise BoardError("Could not exec command")

    def get(self, filename):
        """Retrieve the contents of the specified file and return its contents
        as a byte string.
        """
        # Open the file and read it a few bytes at a time and print out the
        # raw bytes.  Be careful not to overload the UART buffer so only write
        # a few bytes at a time, and don't use print since it adds newlines and
        # expects string data.
        command = """
            import sys
            with open('{0}', 'rb') as infile:
                while True:
                    result = infile.read({1})
                    if result == b'':
                        break
                    len = sys.stdout.write(result)
        """.format(filename, BUFFER_SIZE)
        self.enter_raw_repl()
        self._input_queue_reset()
        self.exec_(textwrap.dedent(command))
        self.exit_raw_repl()

        data = self._read_until(b'\x04')
        if not data.endswith(b'\x04'):
            print(data)
            raise BoardError("Could not read file")
        return data
