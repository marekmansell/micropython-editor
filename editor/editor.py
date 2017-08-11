import os
import sys
from PyQt5.QtWidgets import QApplication
from editor.gui import MainEditorWindow

def run():
	app = QApplication(sys.argv)
	main_editor_window = MainEditorWindow()
	sys.exit(app.exec_())