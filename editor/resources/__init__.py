import os
import sys
from PyQt5.QtGui import QIcon

_styles = ["day.css", "night.css", "black.css", "green"]

def get_file_content(file):
    if hasattr(sys, "_MEIPASS"):
        full_path = os.path.join(sys._MEIPASS, "editor", "resources", file)
    else:
        full_path = os.path.join("editor", "resources", file)
    with open(full_path, "r") as f:
        content = f.read()
    return content

def load_icon(file):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "editor", "resources", file)
    return QIcon(os.path.join("editor", "resources", "img", file))

def list_themes():
    return ["Day", "Night", "Black", "Green"]

def load_theme(id):
    file = _styles[id]
    return get_file_content(os.path.join("themes", file))

