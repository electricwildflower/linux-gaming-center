import tkinter as tk
from tkinter import ttk
from paths import PathManager # Import PathManager

class ThemesFrame(tk.Frame):
    def __init__(self, parent, controller, path_manager: PathManager): # ADDED: path_manager argument
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.path_manager = path_manager # STORED: path_manager as an instance variable
        self.configure(bg="#282c34") # Set a background color for the frame

        label = ttk.Label(self, text="Themes Settings", font=("Arial", 20, "bold"), foreground="white", background="#282c34")
        label.pack(pady=20, padx=20)

        # Placeholder for networking options
        info_label = ttk.Label(self, text="Configure Themes settings for your gaming center app.",
                               foreground="white", background="#282c34", wraplength=400)
        info_label.pack(pady=10, padx=20)

    def on_show_frame(self):
        """Called when this frame is brought to the front."""
        print("Themes Settings Frame is now visible.")
        # Example of using path_manager (you can expand this as needed)
        # themes_path = self.path_manager.get_path("themes")
        # print(f"Current themes path: {themes_path}")


