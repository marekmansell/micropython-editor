import tkinter as tk

class Application(tk.Frame):
	def __init__(self, master):
		super().__init__(master)
		self.master = master
		master.title = "Hello"
		self.grid()
		self.text = tk.Text(master, height = 15)
		self.text.grid()

		self.text.insert(tk.END, ">>> \r\n>>> \r\n>>> ")
		

		self.text.bind("<Key>", self.key)
		self.stop = self.text.index("end-1c")

	def key(self, event):





root = tk.Tk()
app = Application(root)
app.mainloop()