import tkinter as tk
from tkinter import ttk

class DashboardConfigFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="#282c34") # Set a background color for the frame

        label = ttk.Label(self, text="Dashboard Configuration", font=("Arial", 20, "bold"), foreground="white", background="#282c34")
        label.pack(pady=20, padx=20)

        # Placeholder for dashboard layout and content options
        info_label = ttk.Label(self, text="Customize the main dashboard layout, visible libraries, and recently played sections.",
                               foreground="white", background="#282c34", wraplength=400)
        info_label.pack(pady=10, padx=20)

    def on_show_frame(self):
        """Called when this frame is brought to the front."""
        print("Dashboard Configuration Frame is now visible.")


