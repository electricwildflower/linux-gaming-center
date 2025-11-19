import tkinter as tk
from tkinter import ttk

class NetworkingFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="#282c34") # Set a background color for the frame

        label = ttk.Label(self, text="Networking Settings", font=("Arial", 20, "bold"), foreground="white", background="#282c34")
        label.pack(pady=20, padx=20)

        # Placeholder for networking options
        info_label = ttk.Label(self, text="Configure network settings for your gaming center app.",
                               foreground="white", background="#282c34", wraplength=400)
        info_label.pack(pady=10, padx=20)

    def on_show_frame(self):
        """Called when this frame is brought to the front."""
        print("Networking Settings Frame is now visible.")


