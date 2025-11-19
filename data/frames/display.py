import tkinter as tk
from tkinter import ttk

class DisplayFrame(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.configure(bg="#282c34") # Set a background color for the frame

        label = ttk.Label(self, text="Display Settings", font=("Arial", 20, "bold"), foreground="white", background="#282c34")
        label.pack(pady=20, padx=20)

        # Placeholder for display configuration options
        info_label = ttk.Label(self, text="Manage fullscreen, window toggles, and other display preferences here.",
                               foreground="white", background="#282c34", wraplength=400)
        info_label.pack(pady=10, padx=20)

        # Fullscreen toggle button
        self.toggle_button = tk.Button(
            self,
            text="Toggle Windowed/Fullscreen",
            font=("Arial", 12),
            bg="#61afef", # Example button background
            fg="white",   # Example text color
            activebackground="#5698d3",
            activeforeground="white",
            command=self.controller.toggle_fullscreen
        )
        self.toggle_button.pack(pady=20)


    def on_show_frame(self):
        """Called when this frame is brought to the front."""
        # Display Settings Frame is now visible
