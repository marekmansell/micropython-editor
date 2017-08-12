from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QTabWidget,
    QMessageBox, QSplitter, QTextEdit, QAction, qApp, QWidget,
    QGridLayout, QPushButton, QFileDialog, QMenu, QApplication)
from PyQt5.QtGui import (QCloseEvent, QIcon, QColor, QTextCursor, QKeySequence,
    QCursor)
from PyQt5.QtCore import QSize, Qt, QUrl, QIODevice
from PyQt5.Qsci import QsciScintilla
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtSerialPort import QSerialPort
from editor.resources import load_icon, list_themes, load_theme
from editor.logic import EditorLogic
import os
import platform
import re

def _center_window(window):
    """Moves the <window> object to the center of the Display"""
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())

class TextEdit(QsciScintilla):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setMarginLineNumbers(0, True)
        self.setMarginWidth(0, 45)
        self.setPaper(QColor("#272822"))
        self.setMarginsBackgroundColor(QColor("#373832"))
        self.setMarginsForegroundColor(QColor("grey"))
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)
        self.setBraceMatching(True)
        self.textChanged.connect(self._text_changged)

    def _text_changged(self):
        self.parent.setModified(True)

class BlocklyWebPage(QWebEnginePage):
    """Extends QWebEngineView event handling"""
    def __init__(self):
        super().__init__()

    def javaScriptAlert(self, _x, msg):
        """Overwrites JavaScript Alert handling"""
        print(msg)

class REPLPane(QTextEdit):
    """
    REPL = Read, Evaluate, Print, Loop.
    This widget represents a REPL client connected to a BBC micro:bit running
    MicroPython.
    The device MUST be flashed with MicroPython for this to work.
    """

    def __init__(self, parent, serial):
        super().__init__(parent)
        self.serial = serial
        self.setAcceptRichText(False)
        self.setReadOnly(False)
        self.setUndoRedoEnabled(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.context_menu)

    def paste(self):
        """
        Grabs clipboard contents then sends down the serial port.
        """
        clipboard = QApplication.clipboard()
        if clipboard and clipboard.text():
            self.serial.write(bytes(clipboard.text(), 'utf8'))

    def context_menu(self):
        """"
        Creates custom context menu with just copy and paste.
        """
        menu = QMenu(self)
        if platform.system() == 'Darwin':
            copy_keys = QKeySequence(Qt.CTRL + Qt.Key_C)
            paste_keys = QKeySequence(Qt.CTRL + Qt.Key_V)
        else:
            copy_keys = QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_C)
            paste_keys = QKeySequence(Qt.CTRL + Qt.SHIFT + Qt.Key_V)

        menu.addAction("Copy", self.copy, copy_keys)
        menu.addAction("Paste", self.paste, paste_keys)
        menu.exec_(QCursor.pos())

    def cursor_to_end(self):
        """
        Moves the cursor to the very end of the available text.
        """
        tc = self.textCursor()
        tc.movePosition(QTextCursor.End)
        self.setTextCursor(tc)

    def on_serial_read(self):
        """
        Called when the application gets data from the connected device.
        """
        self.process_bytes(bytes(self.serial.readAll()))

    def keyPressEvent(self, data):
        """
        Called when the user types something in the REPL.
        Correctly encodes it and sends it to the connected device.
        """
        key = data.key()
        msg = bytes(data.text(), 'utf8')
        if key == Qt.Key_Backspace:
            msg = b'\b'
        elif key == Qt.Key_Up:
            msg = b'\x1B[A'
        elif key == Qt.Key_Down:
            msg = b'\x1B[B'
        elif key == Qt.Key_Right:
            msg = b'\x1B[C'
        elif key == Qt.Key_Left:
            msg = b'\x1B[D'
        elif key == Qt.Key_Home:
            msg = b'\x1B[H'
        elif key == Qt.Key_End:
            msg = b'\x1B[F'
        elif (platform.system() == 'Darwin' and
                data.modifiers() == Qt.MetaModifier) or \
             (platform.system() != 'Darwin' and
                data.modifiers() == Qt.ControlModifier):
            # Handle the Control key. On OSX/macOS/Darwin (python calls this
            # platform Darwin), this is handled by Qt.MetaModifier. Other
            # platforms (Linux, Windows) call this Qt.ControlModifier. Go
            # figure. See http://doc.qt.io/qt-5/qt.html#KeyboardModifier-enum
            if Qt.Key_A <= key <= Qt.Key_Z:
                # The microbit treats an input of \x01 as Ctrl+A, etc.
                msg = bytes([1 + key - Qt.Key_A])
        elif (data.modifiers() == Qt.ControlModifier | Qt.ShiftModifier) or \
                (platform.system() == 'Darwin' and
                    data.modifiers() == Qt.ControlModifier):
            # Command-key on Mac, Ctrl-Shift on Win/Lin
            if key == Qt.Key_C:
                self.copy()
                msg = b''
            elif key == Qt.Key_V:
                self.paste()
                msg = b''
        self.serial.write(msg)

    def process_bytes(self, data):
        """
        Given some incoming bytes of data, work out how to handle / display
        them in the REPL widget.
        """
        tc = self.textCursor()
        # The text cursor must be on the last line of the document. If it isn't
        # then move it there.
        while tc.movePosition(QTextCursor.Down):
            pass
        i = 0
        while i < len(data):
            if data[i] == 8:  # \b
                tc.movePosition(QTextCursor.Left)
                self.setTextCursor(tc)
            elif data[i] == 13:  # \r
                pass
            elif data[i] == 27 and data[i + 1] == 91:  # VT100 cursor: <Esc>[
                i += 2  # move index to after the [
                m = re.search(r'(?P<count>[\d]*)(?P<action>[ABCDK])',
                              data[i:].decode('utf-8'))

                # move to (almost) after control seq (will ++ at end of loop)
                i += m.end() - 1

                if m.group("count") == '':
                    count = 1
                else:
                    count = int(m.group("count"))

                if m.group("action") == "A":  # up
                    tc.movePosition(QTextCursor.Up, n=count)
                    self.setTextCursor(tc)
                elif m.group("action") == "B":  # down
                    tc.movePosition(QTextCursor.Down, n=count)
                    self.setTextCursor(tc)
                elif m.group("action") == "C":  # right
                    tc.movePosition(QTextCursor.Right, n=count)
                    self.setTextCursor(tc)
                elif m.group("action") == "D":  # left
                    tc.movePosition(QTextCursor.Left, n=count)
                    self.setTextCursor(tc)
                elif m.group("action") == "K":  # delete things
                    if m.group("count") == "":  # delete to end of line
                        tc.movePosition(QTextCursor.EndOfLine,
                                        mode=QTextCursor.KeepAnchor)
                        tc.removeSelectedText()
                        self.setTextCursor(tc)
            elif data[i] == 10:  # \n
                tc.movePosition(QTextCursor.End)
                self.setTextCursor(tc)
                self.insertPlainText(chr(data[i]))
            else:
                tc.deleteChar()
                self.setTextCursor(tc)
                self.insertPlainText(chr(data[i]))
            i += 1
        self.ensureCursorVisible()

    def clear(self):
        """
        Clears the text of the REPL.
        """
        self.setText('')


class BlocklyPane(QWidget):
    """Creates a pane with Blockly opened in QWebEngineView Widget"""
    def __init__(self, parent):
        super().__init__(parent)
        # Create Grid Layout for BlocklyPane Widget
        self.blockly_layout = QGridLayout(self)
        self.setLayout(self.blockly_layout)

        # Create Blockly Browser Widget
        self.blockly_browser = QWebEngineView(self)

        # BlocklyWebPage overwrites JavaScript Alert handling (generated code)
        self.page = BlocklyWebPage()
        self.blockly_browser.setPage(self.page)

        # url = 'file://' + os.path.abspath(os.path.join('blockly','index.htm'))
        url = QUrl('http://marekmansell.sk/test/blockly/')
        self.blockly_browser.load(url) # Load Website
        self.blockly_layout.addWidget(self.blockly_browser) # Display Browser


class Tab(QWidget):
    """Tab with QsciScintilla TextEntry"""
    def __init__(self, parent, path):
        super().__init__()
        self.parent = parent
        self.path = path
        self.layout = QGridLayout() # Create Grid Layout
        self.setLayout(self.layout) # Apply Layout to Tab
        self.text_field = TextEdit(self)
        self.layout.addWidget(self.text_field)

        if path:
            self.title = os.path.basename(path)
        else:
            self.title = "untitled.py"

    def setModified(self, modified):
        if modified:
            text = self.title + "*"
        else:
            text = self.title

        self.parent.setTabText(self.id, text)
    

class EditorPane(QTabWidget):
    """Editor Pane Widget"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.remove_tab)

        self.create_new_tab()

    def remove_tab(self, id):
        self.removeTab(id)
        if self.count() == 0:
            self.create_new_tab()

    def create_new_tab(self, path=None, content=None):
        tab = Tab(self, path) 
        tab.id = self.addTab(tab, tab.title) # Add tab to EditorPane

        if content:
            tab.text_field.insert(content)
            tab.setModified(False)

        self.setCurrentIndex(tab.id)


class MainEditorWindow(QMainWindow):
    """Main PyQt window"""
    def __init__(self):
        super().__init__()
        self.logic = EditorLogic(self)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("MicroPython Editor")
        self.setWindowIcon(load_icon("icon.ico"))
        self.resize(800, 800)
        _center_window(self)
        self._init_central_widget()
        self._init_menubar()
        self._init_toolbar()
        self.set_theme()
        self.statusBar().showMessage("MicroPython Editor")
        self.show()

    def set_theme(self, theme_id=0):
        self.setStyleSheet(load_theme(theme_id))

    def _init_menubar(self):
        """Creates a menubar for the Main Window"""

        # Menubar
        self._menubar = self.menuBar()

        # File
        self._menubar_file = self._menubar.addMenu("File")

        # File -> New
        self._menubar_file_newFile = QAction("New File", self)
        self._menubar_file.addAction(self._menubar_file_newFile)

        # File -> Quit
        self._menubar_file_quit = QAction("Quit", self)
        self._menubar_file.addAction(self._menubar_file_quit)
        self._menubar_file_quit.triggered.connect(self.close)

        # View
        self._menubar_view = self._menubar.addMenu("View")

        # REPL (checkable)
        self._menubar_view_repl = QAction("REPL", self, checkable=True)
        self._menubar_view.addAction(self._menubar_view_repl)

        # Storage (checkable)
        self._menubar_view_storage = QAction("Storage", self, checkable=True)
        self._menubar_view.addAction(self._menubar_view_storage)

        # Blockly (checkable)
        self._menubar_view_blockly = QAction("Blockly", self, checkable=True)
        self._menubar_view.addAction(self._menubar_view_blockly)

    def _init_toolbar(self):
        self._toolbar = self.addToolBar("Toolbar")
        self._toolbar.setIconSize(QSize(45, 40))
        self._toolbar.setToolButtonStyle(3)
        self._toolbar.setMovable(False)

        # New
        self._toolbar_new = QAction(load_icon("new.png"), "New", self)
        self._toolbar_new.triggered.connect(self.new_tab)
        self._toolbar.addAction(self._toolbar_new)

        # Load
        self._toolbar_load = QAction(load_icon("load.png"), "Load", self)
        self._toolbar_load.triggered.connect(self.logic.load)
        self._toolbar.addAction(self._toolbar_load)

        # Save
        self._toolbar_save = QAction(load_icon("save.png"), "Save", self)
        self._toolbar_save.triggered.connect(self.logic.save)
        self._toolbar.addAction(self._toolbar_save)

        # Vertical Separator
        self._toolbar.addSeparator()

        # Run
        self._toolbar_run = QAction(load_icon("run.png"), "Run", self)
        self._toolbar_run.triggered.connect(self.logic.run_tab)
        self._toolbar.addAction(self._toolbar_run)

        # Stop
        self._toolbar_stop = QAction(load_icon("stop.png"), "Stop", self)
        self._toolbar_stop.triggered.connect(self.logic.stop)
        self._toolbar.addAction(self._toolbar_stop)

        # Reset
        self._toolbar_reset = QAction(load_icon("reset.png"), "Reset", self)
        self._toolbar_reset.triggered.connect(self.logic.reset)
        self._toolbar.addAction(self._toolbar_reset)

        # Flash
        self._toolbar_flash = QAction(load_icon("flash.png"), "Flash", self)
        # self._toolbar_flash.triggered.connect(self.close)
        self._toolbar.addAction(self._toolbar_flash)

        # Vertical Separator
        self._toolbar.addSeparator()
        
        # REPL
        self._toolbar_repl = QAction(load_icon("repl.png"), "REPL", self)
        self._toolbar_repl.triggered.connect(self.logic.toggle_repl_pane)
        self._toolbar.addAction(self._toolbar_repl)

        # Storage
        self._toolbar_storage = QAction(load_icon("storage.png"), "Storage", self)
        self._toolbar_storage.triggered.connect(self.logic.toggle_storage_pane)
        self._toolbar.addAction(self._toolbar_storage)

        # Blockly
        self._toolbar_blockly = QAction(load_icon("blockly.png"), "Blockly", self)
        self._toolbar_blockly.triggered.connect(self.logic.toggle_blockly_pane)
        self._toolbar.addAction(self._toolbar_blockly)

        # Connect
        self._toolbar_connect = QAction(load_icon("device.png"), "Connect", self)
        self._toolbar_connect.triggered.connect(self.logic.connect)
        self._toolbar.addAction(self._toolbar_connect)

        # Vertical Separator
        self._toolbar.addSeparator()

        # Check
        self._toolbar_check = QAction(load_icon("check.png"), "Check", self)
        # self._toolbar_check.triggered.connect(self.close)
        self._toolbar.addAction(self._toolbar_check)

        # Help
        self._toolbar_help = QAction(load_icon("help.png"), "Help", self)
        # self._toolbar_help.triggered.connect(self.close)
        self._toolbar.addAction(self._toolbar_help)

        # Exit
        self._toolbar_exit = QAction(load_icon("quit.png"), "Exit", self)
        self._toolbar_exit.triggered.connect(self.close)
        self._toolbar.addAction(self._toolbar_exit)

    def _init_central_widget(self):
    
        # Create a central widget with Grid layout
        central_widget = QWidget(self)
        self.central_grid = QGridLayout()
        central_widget.setLayout(self.central_grid)
        self.setCentralWidget(central_widget) # Place widget in QMainWindow

        # Create Horizontal and Vertical Splitter
        self.top_splitter = QSplitter(Qt.Horizontal)
        self.bottom_splitter = QSplitter(Qt.Vertical)

        # These are the widgets in the central widget
        # repl, blockly & storage are created when needed
        self.repl_pane = None
        self.editor_pane = EditorPane(self.top_splitter)
        self.blockly_pane = None
        self.storage_pane = None

        # Add Splitters to central grid
        self.central_grid.addWidget(self.top_splitter)
        self.central_grid.addWidget(self.bottom_splitter)
        
        # Place top_splitter as top widget of bottom_splitter
        self.bottom_splitter.addWidget(self.top_splitter)

    def add_repl_pane(self):
        self.repl_pane = REPLPane(self.bottom_splitter, self.logic.serial)
        self.bottom_splitter.addWidget(self.repl_pane)

    def add_blockly_pane(self):
        self.blockly_pane = BlocklyPane(self.top_splitter)
        self.top_splitter.addWidget(self.blockly_pane)

    def add_storage_pane(self):
        self.storage_pane = QTextEdit(self.bottom_splitter)
        self.bottom_splitter.addWidget(self.storage_pane)

    def rm_repl_pane(self):
        self.repl_pane.setParent(None)
        self.repl_pane.deleteLater()
        self.repl_pane = None

    def rm_blockly_pane(self):
        self.blockly_pane.setParent(None)
        self.blockly_pane.deleteLater()
        self.blockly_pane = None

    def rm_storage_pane(self):
        self.storage_pane.setParent(None)
        self.storage_pane.deleteLater()
        self.storage_pane = None

    def closeEvent(self, event):
        """Called when user wants to close the App
        and chceck whether any files nees saving
        """
        pass
        # reply = QMessageBox.question(
        #             self, 'Quit Program?', 'Do you really want to quit?',
        #             QMessageBox.Yes | QMessageBox.No)

        # if reply == QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()

    def get_load_path(self, path):
        path, _ = QFileDialog.getOpenFileName(self, 'Open File', path, '*.py')
        return path

    def new_tab(self, path=None, content=None):
        self.editor_pane.create_new_tab(path=path, content=content)

    def get_current_tab(self):
        return self.editor_pane.currentWidget()

    def get_save_path(self, path):
        path, _ = QFileDialog.getSaveFileName(self, 'Save file', path)
        return path