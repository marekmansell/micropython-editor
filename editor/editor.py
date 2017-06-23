import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QSplashScreen, QMessageBox, QDesktopWidget, qApp, QAction
from PyQt5.QtGui import QPixmap, QIcon
# from PyQt5.


def center_widget(widget):
    qr = widget.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    widget.move(qr.topLeft())

class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):




        exitAction = QAction(QIcon('editor/a.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)




        self.setMinimumSize(800, 400)
        center_widget(self)
        self.setWindowTitle('Icon')
        self.setWindowIcon(QIcon('editor/a.png'))
        self.statusBar()

        self.show()

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', "Are you sure to quit?",
                                     QMessageBox.Yes or QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()



def run():
    print("running!")
    app = QApplication(sys.argv)
    splash = QSplashScreen(QPixmap('editor/a.png'))
    splash.show()
    editor_window = EditorWindow()
    splash.finish(editor_window)
    sys.exit(app.exec_())
