import tkinter as tk
import serial
from time import sleep, time
from threading import Thread
from PIL import Image, ImageTk


# GUI CLASSES:

class EditArea:
    """
        TextField creates the following widgets:
            self.text_area = tk.Text (Main Text Editor Area)
            self.y_scrollbar = tk.Scrollbar (Vertical Text Editor Scrollbar)
            self.x_scrollbar = tk.Scrollbar (Horizontal Text Editor Scrollbar)
            self.line_numbers = tk.Canvas (SideBar with line numbers)

        Example usage:
            edit_area = EditArea(master)
            edit_area.line_numbers.grid(row=1, column=0, sticky=tk.N+tk.S)
            edit_area.y_scrollbar.grid(row=1, column=2, sticky=tk.N+tk.S)
            edit_area.x_scrollbar.grid(row=2, column=1, sticky=tk.W+tk.E)
            edit_area.text_area.grid(row=1, column=1)
    """
    def __init__(self, master, **kwargs):

        self.text_area = tk.Text(master, **kwargs)

        self.master = master

        self.y_scrollbar = tk.Scrollbar(master)
        self.y_scrollbar.config(command=self.text_area.yview)
        self.x_scrollbar = tk.Scrollbar(master)
        self.x_scrollbar.config(command=self.text_area.xview, orient=tk.HORIZONTAL)

        self.line_numbers = tk.Canvas(master, width=28)

        self.text_area.config(
            bg="black",  # background color
            fg="green",  # default text color
            wrap=tk.NONE,  # allows lines to be infinitely long
            yscrollcommand=self.y_scrollbar.set,
            xscrollcommand=self.x_scrollbar.set,
            font="{fixedsys} 12",
            insertbackground="white",  # cursor color
        )

        self.last_line_number = None
        self._update_line_numbers()

        self.text_area.bind("<Tab>", self._tab_event)
        self.text_area.bind("<Shift-ISO_Left_Tab>", self._shift_tab_event)
        self.text_area.bind("<Control-a>", self._control_a_event)
        self.text_area.bind("<Control-A>", self._control_a_event)

    def _update_line_numbers(self):
        line = self.text_area.index('@0,0')
        if (self.last_line_number != line) or (self.last_line_number is None):
            self.line_numbers.delete("all")

            while True:
                dline = self.text_area.dlineinfo(line)
                if dline is None:
                    break
                y = dline[1]
                linenum = str(line).split(".")[0]
                self.line_numbers.create_text(2, y, anchor="nw", text=linenum)
                line = self.text_area.index("%s+1line" % line)

            self.last_line_number = line

        self.master.after(60, self._update_line_numbers)

    def _tab_event(self, event):
        self.text_area.insert(tk.INSERT, " " * 4)
        return 'break'

    def _shift_tab_event(self, event):
        return 'break'

    def _control_a_event(self, event):
        self.text_area.tag_add("sel", "1.0", "end")
        return 'break'


class ReplArea:
    def __init__(self, master, userial):
        self.repl_history = tk.Text(master)
        self.repl_scrollbar = tk.Scrollbar(master)
        self.repl_scrollbar.config(command=self.repl_history.yview)
        self.repl_entry = tk.Entry(master)

        self.repl_history.config(
            height=7,
            state=tk.DISABLED,
            yscrollcommand=self.repl_scrollbar.set
        )

        self.repl_entry.insert(0, "print(\"This is the MicroPython REPL. Press Enter!\")")

        self.repl_entry.bind("<Return>", self._return_event)
        self.repl_entry.bind("<Tab>", self._insert_tab)

    def _return_event(self, event):
        self.repl_history.config(state=tk.NORMAL)
        self.repl_history.insert(tk.END, self.repl_entry.get() + "\n")
        self.repl_history.see(tk.END)
        self.repl_history.config(state=tk.DISABLED)
        self.repl_history.mark_set(tk.INSERT, 1.0)
        self.repl_entry.delete(0, tk.END)

    def _insert_tab(self, event):
        self.repl_entry.insert(tk.INSERT, " " * 4)
        return 'break'


class Toolbar(tk.Frame):
    def __init__(self, master):
        super().__init__(master, borderwidth=2, relief='raised')

        # Load all the images first as PNGs and use ImageTk to convert
        # them to usable Tkinter images.
        img_upload = Image.open('load.png')
        img_upload = img_upload.resize((50, 50), Image.ANTIALIAS)
        self.tk_img_upload = ImageTk.PhotoImage(img_upload)

        # Set up all the buttons for use on the toolbars.
        self.upload_button = tk.Button(master, image=self.tk_img_upload, command=self._upload_event)

    def _upload_event(self):
        # self.upload_button.flash()
        print("Upload Code")


class Application(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        root.title("MicroPython Editor")
        self.grid()

        userial = None

        self.edit_area = EditArea(self)
        self.edit_area.line_numbers.grid(row=1, column=0, sticky=tk.N+tk.S)
        self.edit_area.y_scrollbar.grid(row=1, column=2, sticky=tk.N+tk.S)
        self.edit_area.x_scrollbar.grid(row=2, column=1, sticky=tk.W+tk.E)
        self.edit_area.text_area.grid(row=1, column=1)

        self.repl = ReplArea(self, userial)
        self.repl.repl_history.grid(row=3, column=1, sticky=tk.W+tk.E)
        self.repl.repl_entry.grid(row=4, column=1, sticky=tk.W+tk.E)
        self.repl.repl_scrollbar.grid(row=3, column=2, sticky=tk.N+tk.S)

        self.tool_bar = Toolbar(self)
        self.tool_bar.upload_button.grid(row=0, column=1, sticky=tk.W)


root = tk.Tk()
app = Application(root)
app.mainloop()


# def listener():
#   # sleep(.5)
#   # ser.write("import machine\n\r".encode())
#   # sleep(.5)
#   # ser.write("pin = machine.Pin(2, machine.Pin.OUT)\n\r".encode())
#   # sleep(.5)
#   # ser.write("pin.value(0)\n\r".encode())
#   while True:
#       out = input()
#       out += "\r"
#       out = out.encode()
#       ser.write(out)


# ser = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=.2)
# ser.flushInput()
# Thread(target=listener).start()


# while True:
#   a = []
#   while not ser.inWaiting():
#       sleep(.01)

#   while ser.inWaiting():
#       a.append(ser.read(1))
#   # if a != [b"\n\r"]:
#   print(b"".join(a).decode(), end="")

#   # [print(ser.read(1).decode(), end="") for x in range(ser.inWaiting())]
