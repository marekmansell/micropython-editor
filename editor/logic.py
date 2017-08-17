from pathlib import Path
import os
from editor.boards import Board, BOARDS
from PyQt5.QtCore import QIODevice
from time import sleep
from serial.tools.list_ports import comports

class EditorLogic:
    """All MicroPython Editor Actions are processed here"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.load_save_path = str(Path.home())
        self.board = None

    def toggle_blockly_pane(self):
        current_state = self.main_window.blockly_pane.isVisible()
        if current_state:
            self._exit_blockly_mode()
            self.main_window.blockly_pane.setVisible(False)
            self.main_window.top_splitter.setSizes([800,0])
        else:
            self._enter_blockly_mode()
            self.main_window.blockly_pane.setVisible(True)
            self.main_window.top_splitter.setSizes([250,550])
            self.main_window.blockly_pane.blockly_browser.page().runJavaScript("autoUpdate();")

    def toggle_storage_pane(self):
        self.main_window.repl_pane.hide()
        if self.board:
            current_state = self.main_window.storage_pane.isVisible()
            self.main_window.storage_pane.setVisible(not current_state)

    def toggle_repl_pane(self):
        self.main_window.storage_pane.hide()
        if self.board:
            current_state = self.main_window.repl_pane.isVisible()
            self.main_window.repl_pane.setVisible(not current_state)

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

    def connect(self, port, board):

        self.port = port
        # open the serial port
        if self.board:
            self.board.close()
        self.board = Board(port=port, board=board, repl_pane=self.main_window.repl_pane,
            icon_update=self.main_window.update_device_icon)
        self.main_window.repl_pane.board = self.board
        self.main_window.update_device_icon(connected=True)

    def run_tab(self):
        if self.board is None:
            return
        tab = self.main_window.get_current_tab()
        if tab is None:
            return
        self.board.run(bytes(tab.text_field.text().strip(), 'utf8'))

    def stop(self):
        if self.board:
            self.board.stop()

    def reset(self):
        if self.board:
            self.board.reset()

    def _exit_blockly_mode(self):
        self.main_window.editor_pane.unlock()

    def _enter_blockly_mode(self):
        self.main_window.new_tab()
        self.main_window.editor_pane.lock()

    def blockly_update(self, code):
        code = code.replace("&quot;","\"")
        code = code.replace("&amp;","&")
        self.main_window.get_current_tab().text_field.clear()
        self.main_window.get_current_tab().text_field.insert(code)

    def flash(self):
        repeats = 3
        tab = self.main_window.get_current_tab()
        if tab is None:
            return
        data = bytes(tab.text_field.text().strip(), 'utf8')
        self.board.flash("main.py", data)
        print("Starting consistency check of uploaded file...")
        written_file = self.board.get("main.py").replace(b'\r', b'').strip(b'\x04')
        if written_file == data:
            print("Successfully uploaded!")
        else:
            print("Uploaded is corrupted")

    def get(self, filename):
        self.board.get(filename)

    def get_comports(self):
        ports = list(comports()) # get all serial devices
        return [dev.device for dev in ports if "USB" in dev.hwid] # return a list of their names (COMx or dev/ttyUSBx)

    def get_board_types(self):
        return BOARDS