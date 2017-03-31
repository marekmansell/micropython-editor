import tkinter as tk
from tkinter import ttk
import serial
from time import sleep, time
import threading 
from PIL import Image, ImageTk
import logging
import queue
import os
import subprocess
from pygments import lex
from pygments.lexers import PythonLexer


logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )

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
            # bg="black",  # background color
            # fg="green",  # default text color
            wrap=tk.NONE,  # allows lines to be infinitely long
            yscrollcommand=self.y_scrollbar.set,
            xscrollcommand=self.x_scrollbar.set,
            font="{fixedsys} 12",
            # insertbackground="white",  # cursor color
        )

        self.last_line_number = None
        self._update_line_numbers()

        self.text_area.bind("<Tab>", self._tab_event)
        self.text_area.bind("<Shift-ISO_Left_Tab>", self._shift_tab_event)
        self.text_area.bind("<Control-a>", self._control_a_event)
        self.text_area.bind("<Control-A>", self._control_a_event)
        self.text_area.bind("<Key>", self._key_event)

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

    def _key_event(self, event):
        textPad = self.text_area
        textPad.tag_configure("Token.Comment", foreground="#b21111")
        textPad.mark_set("range_start", "1.0")
        data = textPad.get("1.0", "end-1c")
        for token, content in lex(data, PythonLexer()):
            textPad.mark_set("range_end", "range_start + %dc" % len(content))
            textPad.tag_add(str(token), "range_start", "range_end")
            textPad.mark_set("range_start", "range_end")


class ReplArea:
    def __init__(self, master, u_serial):
        self.repl_history = tk.Text(master)
        self.repl_scrollbar = tk.Scrollbar(master)
        self.repl_scrollbar.config(command=self.repl_history.yview)
        # self.repl_entry = tk.Entry(master)
        self.repl_stop = self.repl_history.index("end")
        self.send_queue = queue.Queue()

        self.repl_history.config(
            height=15,
            yscrollcommand=self.repl_scrollbar.set,
            # background="black",
            # foreground="yellow",
            # insertbackground="white",  # cursor color
        )

        # self.repl_entry.insert(0, "print(\"This is the MicroPython REPL. Press Enter!\")")

        self.repl_history.bind("<Return>", self._return_event)
        self.repl_history.bind("<Tab>", self._insert_tab)
        self.repl_history.bind("<Key>", self._key_event)
        self.repl_history.bind("<Control-a>", self._ctrl_a_event)
        self.repl_history.bind("<Control-A>", self._ctrl_a_event)
        self.repl_history.bind("<Control-b>", self._ctrl_b_event)
        self.repl_history.bind("<Control-B>", self._ctrl_b_event)
        self.repl_history.bind("<Control-c>", self._ctrl_c_event)
        self.repl_history.bind("<Control-C>", self._ctrl_c_event)
        self.repl_history.bind("<Control-d>", self._ctrl_d_event)
        self.repl_history.bind("<Control-D>", self._ctrl_d_event)
        self.repl_history.bind("<Control-e>", self._ctrl_e_event)
        self.repl_history.bind("<Control-E>", self._ctrl_e_event)

        self.serial_thread = SerialThread(self, u_serial)

    def _return_event(self, event):
        to_send = self.repl_history.get(self.repl_stop, tk.END).rstrip()
        to_send += "\r"
        to_send = to_send.encode()
        event.widget.delete(self.repl_stop, tk.END)
        self.send_queue.put(to_send)
        return "break"

    def _insert_tab(self, event):
        self.repl_history.insert(tk.INSERT, " " * 4)
        return 'break'

    def _key_event(self, event):
        if event.keysym == "Left" and self.repl_history.compare(self.repl_history.index(tk.INSERT), '==', self.repl_stop):
            return "break"
        if event.keysym == "BackSpace" and self.repl_history.compare(self.repl_history.index(tk.INSERT), '==', self.repl_stop):
            return "break"
        if event.keysym == "Up":
            return "break"
        if self.repl_history.compare(self.repl_history.index(tk.INSERT), '<', self.repl_stop):
            self.repl_history.mark_set("insert", self.repl_stop)
            return "break"

    def _ctrl_a_event(self, event):
        self.send_queue.put(chr(1).encode())
        return "break"

    def _ctrl_b_event(self, event):
        self.send_queue.put(chr(2).encode())
        return "break"

    def _ctrl_c_event(self, event):
        self.send_queue.put(chr(3).encode())
        return "break"

    def _ctrl_d_event(self, event):
        self.send_queue.put(chr(4).encode())
        return "break"

    def _ctrl_e_event(self, event):
        self.send_queue.put(chr(5).encode())
        return "break"


class Toolbar(tk.Frame):
    def __init__(self, master, u_serial, edit_area, repl_area):
        super().__init__(master, borderwidth=2, relief='raised')
        self.u_serial = u_serial
        self.edit_area = edit_area
        self.repl_area = repl_area

        # Load all the images first as PNGs and use ImageTk to convert
        # them to usable Tkinter images.
        img_upload = Image.open('load.png')
        img_upload = img_upload.resize((50, 50), Image.ANTIALIAS)
        self.tk_img_upload = ImageTk.PhotoImage(img_upload)

        # Set up all the buttons for use on the toolbars.
        self.upload_button = tk.Button(master, image=self.tk_img_upload, command=self._upload_event)

    def _upload_event(self):
        # self.upload_button.flash()
        self.u_serial.run(self.edit_area.text_area.get(1.0, tk.END).encode())
        print("Upload Code")


class uSerial:
    def __init__(self, port, **args):
        self.serial = serial.Serial(port, **args)
        self.serial.flushInput()

    def read(self, num):
        return self.serial.read(num)
        
    def inWaiting(self):
        return self.serial.inWaiting()

    def write(self,msg):
        self.serial.write(msg)

    def is_open(self):
        return self.serial.is_open

    def close(self):
        self.serial.close()

    def run(self, command):
        self.enter_raw_repl()
        self.exec(command)
        self.exit_raw_repl()

    def run_file(self, filename):
        with open(filename, 'rb') as f:
            pyfile = f.read()
        self.run(pyfile)

    def enter_raw_repl(self):
        self.serial.write(b'\r\x03\x03') # ctrl-C twice: interrupt any running program

        # # flush input (without relying on serial.flushInput())
        # n = self.serial.inWaiting()
        # while n > 0:
        #     self.serial.read(n)
        #     n = self.serial.inWaiting()

        self.serial.write(b'\r\x01') # ctrl-A: enter raw REPL
        sleep(.1)
        self.serial.write(b'\x04') # ctrl-D: soft reset
        sleep(.5)

    def exit_raw_repl(self):
        self.serial.write(b'\r\x02') # ctrl-B: enter friendly REPL

    def exec(self, command):
        command_bytes = command.rstrip() + b"\n\r"

        # write command
        for i in range(0, len(command_bytes), 256):
            self.serial.write(command_bytes[i:min(i + 256, len(command_bytes))])
            sleep(0.01)
        self.serial.write(b'\x04')
        print("Sending", command.decode())


class SerialThread(threading.Thread):

    def __init__(self, repl_area, u_serial):
        super().__init__()
        self.name = "SerialThread"
        self.repl_area = repl_area
        self.u_serial = u_serial
        self.start()

    def run(self):
        logging.info('SerialThread Started')
        
        if self.u_serial.is_open():
            logging.info("Serial opened")
        else:
            logging.critical("Serial could not be open")
            return

        sleep(.2)
        self.u_serial.write(chr(4).encode())
        
        while True:
            incoming_bytes = []
            if not self.repl_area.send_queue.empty():
                message = self.repl_area.send_queue.get()
                print("Sending: ", message)
                self.u_serial.write(message)
            if self.u_serial.inWaiting():
                while self.u_serial.inWaiting():
                    incoming_bytes.append(self.u_serial.read(1))
                print("Receiving: ", end=" ")
                for index, byte in enumerate(incoming_bytes):
                    if ord(byte) < 128:
                        incoming_bytes[index] = byte.decode()
                        print(ord(byte), end=" ")
                    else:
                        incoming_bytes[index] = "$"
                print("")

                incoming_message = "".join(incoming_bytes).replace("\r", "")
                self.repl_area.repl_history.insert(tk.END, incoming_message)
                self.repl_area.repl_history.see(tk.END)
                self.repl_area.repl_history.mark_set(tk.INSERT, tk.END)
                # if self.text_color == "grey":
                #     self.repl_area.repl_history.tag_add("grey", self.repl_area.repl_stop, tk.END)
                #     self.repl_area.repl_history.tag_config("grey", foreground="grey")
                self.repl_area.repl_stop = self.repl_area.repl_history.index("end-1c")
            else:
                sleep(.01)

        return


class Application(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        root.title("MicroPython Editor")
        self.grid()

        print(self._get_usb_devices())

        self.u_serial = uSerial("/dev/ttyUSB0", baudrate=115200, timeout=.2)

        self.edit_area = EditArea(self)
        self.edit_area.line_numbers.grid(row=1, column=0, sticky=tk.N+tk.S)
        self.edit_area.y_scrollbar.grid(row=1, column=2, sticky=tk.N+tk.S)
        self.edit_area.x_scrollbar.grid(row=2, column=1, sticky=tk.W+tk.E)
        self.edit_area.text_area.grid(row=1, column=1)

        self.repl = ReplArea(self, self.u_serial)
        self.repl.repl_history.grid(row=3, column=1, sticky=tk.W+tk.E)
        self.repl.repl_scrollbar.grid(row=3, column=2, sticky=tk.N+tk.S)

        self.tool_bar = Toolbar(self, self.u_serial, self.edit_area, self.repl)
        self.tool_bar.upload_button.grid(row=0, column=1, sticky=tk.W)

        # n = ttk.Notebook(self)
        # f1 = ttk.Frame(n)   # first page, which would get widgets gridded into it
        # f2 = ttk.Frame(n)   # second page
        # n.add(f1, text='One')
        # n.add(f2, text='Two')
        # k1 = tk.Text(f1)
        # k2 = tk.Text(f2)
        # n.grid()
        # k1.grid()
        # k2.grid()

    def _get_usb_devices(self):
        serial_devices = subprocess.check_output("ls /dev/serial/by-path/; exit 0", stderr=subprocess.STDOUT, shell=True)
        serial_devices = serial_devices.decode().strip().split("\n")
        serial_devices = [x.strip() for x in serial_devices]
        serial_devices = [os.path.realpath(os.path.join("/dev/serial/by-path/", x)) for x in serial_devices]
        return serial_devices


def run():
    root = tk.Tk()
    app = Application(root)
    app.mainloop()

if __name__ == "__main__":
    run()