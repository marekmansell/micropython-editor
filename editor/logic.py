from pathlib import Path
import os
from editor.boards import Board
from PyQt5.QtCore import QIODevice
from time import sleep


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
            self.main_window.top_splitter.setSizes([100,0])
        else:
            self._enter_blockly_mode()
            self.main_window.blockly_pane.setVisible(True)
            self.main_window.top_splitter.setSizes([100,100])

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

    def connect(self, port="/dev/ttyUSB0", board="ESP8266"):

        self.port = port
        # open the serial port
        self.board = Board(port=port, board=board, repl_pane=self.main_window.repl_pane)
        self.main_window.repl_pane.board = self.board

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
        self.main_window.get_current_tab().text_field.clear()
        self.main_window.get_current_tab().text_field.insert(code)