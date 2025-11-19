# frames/settings.py
import tkinter as tk
from tkinter import ttk
import json
import os

class SettingsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.parent = parent
        
        # Load styles from JSON
        try:
            with open("data/themes/cosmictwilight/styles/settings.json", "r") as f:
                self.style = json.load(f)
        except FileNotFoundError:
            # Fallback styles if JSON missing
            self.style = {
                "background": "#1a1a1a",
                "button": {
                    "font": ("Segoe UI", 12),
                    "background": "#2d2d2d",
                    "foreground": "white",
                    "activebackground": "#3d3d3d",
                    "activeforeground": "white"
                }
            }

        # Configure main frame
        self.configure(style="Settings.TFrame")
        ttk.Style().configure("Settings.TFrame", background=self.style.get("background", "#1a1a1a"))
        
        # Make the frame expand to fill its container
        self.grid_rowconfigure(0, weight=1)  # Row 0 will expand vertically
        self.grid_rowconfigure(1, weight=1)  # Row 1 will expand (for centering)
        self.grid_rowconfigure(2, weight=1)  # Row 2 will expand (for centering)
        self.grid_columnconfigure(0, weight=1)  # Column 0 will expand horizontally

        # Create a container frame for centering the button
        self.center_frame = ttk.Frame(self, style="Settings.TFrame")
        self.center_frame.grid(row=1, column=0, sticky="nsew")  # Place in the middle row

        # Configure the center_frame to center its contents
        self.center_frame.grid_rowconfigure(0, weight=1)
        self.center_frame.grid_rowconfigure(1, weight=0)  # Button row (no expansion)
        self.center_frame.grid_rowconfigure(2, weight=1)
        self.center_frame.grid_columnconfigure(0, weight=1)
        self.center_frame.grid_columnconfigure(1, weight=0)  # Button column (no expansion)
        self.center_frame.grid_columnconfigure(2, weight=1)

        # Fullscreen toggle button (now centered)
        button_style = self.style.get("button", {})
        self.toggle_button = tk.Button(
            self.center_frame,
            text="Toggle Windowed/Fullscreen",
            font=tuple(button_style.get("font", ("Segoe UI", 12))),
            bg=button_style.get("background", "#2d2d2d"),
            fg=button_style.get("foreground", "white"),
            activebackground=button_style.get("activebackground", "#3d3d3d"),
            activeforeground=button_style.get("activeforeground", "white"),
            command=self.controller.toggle_fullscreen
        )
        self.toggle_button.grid(row=1, column=1, pady=20)  # Place in the center cell
