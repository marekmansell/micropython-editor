from PyQt5.QtWidgets import (QMainWindow, QDesktopWidget, QTabWidget,
    QMessageBox, QSplitter, QTextEdit, QAction, qApp, QWidget,
    QGridLayout, QPushButton)
from PyQt5.QtGui import QCloseEvent, QIcon, QColor
from PyQt5.QtCore import QSize, Qt, QUrl
from PyQt5.Qsci import QsciScintilla
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from editor.resources import load_icon, list_themes, load_theme

def _center_window(window):
    """Moves the <window> object to the center of the Display"""
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())

class TextEdit(QsciScintilla):
    def __init__(self, file=None):
        super().__init__()
        self.setMarginLineNumbers(0, True)
        self.setMarginWidth(0, 45)
        self.setPaper(QColor("#272822"))
        self.setMarginsBackgroundColor(QColor("#373832"))
        self.setMarginsForegroundColor(QColor("grey"))
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)
        self.setBraceMatching(True)

class BlocklyWebPage(QWebEnginePage):
    def __init__(self):
        super().__init__()

    def javaScriptAlert(self, _x, msg):
        print(msg)

class BlocklyPane(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        l = QGridLayout(self)
        self.setLayout(l)
        # browser = QWebEngineView(self)
        # browser.resize(500,500)
        page = BlocklyWebPage()
        # browser.setPage(page)
        # browser.load(QUrl("http://www.google.sk/"))
        l.addWidget(page)


class EditorPane(QTabWidget):
    """Editor Pane Widget"""
    def __init__(self, parent):
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        # self.tabCloseRequested.connect(self.removeTab)
        # self.currentChanged.connect(self.change_tab)

        self.tabs = []
        self.add_tab()

    def add_tab(self, _x=None, name="untitled.py", file=None):
        # Create content o fnew tab
        tab = QWidget()
        tab.name = name
        tab.file = file
        tab.layout = QGridLayout() # Create Grid Layout
        tab.setLayout(tab.layout) # Apply Layout to Tab
        tab.entry = TextEdit(file)
        tab.layout.addWidget(tab.entry)

        tab_index = self.addTab(tab, name) # Add tab to EditorPane
        self.tabs.append(tab) # Store tab reference
        self.setCurrentIndex(tab_index)
 

class MainEditorWindow(QMainWindow):
    """Main PyQt window"""
    def __init__(self):
        super().__init__()
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
        self._toolbar_new.triggered.connect(self.editor_pane.add_tab)
        self._toolbar.addAction(self._toolbar_new)

        # Load
        self._toolbar_load = QAction(load_icon("load.png"), "Load", self)
        self._toolbar_load.triggered.connect(self.rm_storage_pane)
        self._toolbar.addAction(self._toolbar_load)

        # Save
        self._toolbar_save = QAction(load_icon("save.png"), "Save", self)
        self._toolbar_save.triggered.connect(self.add_blockly_pane)
        self._toolbar.addAction(self._toolbar_save)

        # Vertical Separator
        self._toolbar.addSeparator()

        # Run
        self._toolbar_run = QAction(load_icon("run.png"), "Run", self)
        self._toolbar_run.triggered.connect(self.rm_blockly_pane)
        self._toolbar.addAction(self._toolbar_run)

        # Flash
        self._toolbar_flash = QAction(load_icon("flash.png"), "Flash", self)
        # self._toolbar_flash.triggered.connect(self.close)
        self._toolbar.addAction(self._toolbar_flash)

        # REPL
        self._toolbar_repl = QAction(load_icon("repl.png"), "REPL", self)
        # self._toolbar_repl.triggered.connect(self.close)
        self._toolbar.addAction(self._toolbar_repl)

        # Storage
        self._toolbar_storage = QAction(load_icon("files.png"), "Storage", self)
        # self._toolbar_storage.triggered.connect(self.close)
        self._toolbar.addAction(self._toolbar_storage)

        # Blockly
        self._toolbar_blockly = QAction(load_icon("blockly.png"), "Blockly", self)
        # self._toolbar_blockly.triggered.connect(self.close)
        self._toolbar.addAction(self._toolbar_blockly)

        # Connect
        self._toolbar_connect = QAction(load_icon("device.png"), "Connect", self)
        # self._toolbar_connect.triggered.connect(self.close)
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
        self.repl_pane = QTextEdit(self.bottom_splitter)
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
            and chceck whether any files nees saving"""
        pass
        # reply = QMessageBox.question(
        #             self, 'Quit Program?', 'Do you really want to quit?',
        #             QMessageBox.Yes | QMessageBox.No)

        # if reply == QMessageBox.Yes:
        #     event.accept()
        # else:
        #     event.ignore()
