import tkinter as tk
from tkinter import ttk, font, messagebox
import os
import json
import requests # Keep requests for potential future use or if other parts of the app rely on it, though not directly used in this simplified StoreFrame.

class StoreFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configure the main frame style
        self.configure(style="Store.TFrame")

        # Create the content frame that will hold the "Coming Soon" message
        # Padding is removed as it's not strictly necessary for a single centered label
        self.content_frame = ttk.Frame(self, style="Content.TFrame")
        self.content_frame.pack(fill="both", expand=True)

        # Create the "Coming Soon" label
        # Use a custom style "ComingSoon.TLabel" for specific formatting
        self.coming_soon_label = ttk.Label(
            self.content_frame,
            text="Coming Soon!",
            style="ComingSoon.TLabel"
        )
        # Pack the label to be centered within the content_frame
        # 'anchor="center"' centers it horizontally and vertically
        self.coming_soon_label.pack(expand=True, anchor="center")

        # Load and apply styles for the simplified frame
        # We'll define the "ComingSoon.TLabel" style in apply_styles
        self.load_styles() # Still needed to get general background colors if defined in store.json
        self.apply_styles()

    def load_styles(self):
        """
        Loads styles from the store.json file.
        This method is kept to potentially retrieve background colors
        or other general theme settings from the original style file,
        even if most specific widget styles are no longer used.
        """
        self.style_path = os.path.join("data", "themes", "cosmictwilight", "styles", "store.json")
        try:
            with open(self.style_path, 'r') as f:
                self.styles = json.load(f)
        except Exception as e:
            print(f"Style load error: {e}. Using default styles.")
            self.styles = {} # Fallback to empty dict if file not found or error

    def apply_styles(self):
        """
        Applies styles to the StoreFrame and its children.
        This method is significantly simplified to only style the main frames
        and the new "Coming Soon!" label.
        """
        style = ttk.Style(self)

        # Configure general frame styles
        # Use a default background if not found in self.styles
        background_color = self.styles.get("background", "#2e2e2e") # A dark grey default

        style.configure("Store.TFrame", background=background_color)
        style.configure("Content.TFrame", background=background_color)

        # Configure the "Coming Soon!" label style
        # Set a large font size, yellow foreground, and transparent background
        style.configure(
            "ComingSoon.TLabel",
            font=("Arial", 72, "bold"), # Huge font size
            foreground="yellow",       # Yellow text color
            background=background_color, # Match content frame background
            justify="center"           # Ensure text is centered
        )

    # All other methods (show_category, _toggle_experimental_warning,
    # load_initial_items, update_search_results, on_items_frame_configure,
    # on_items_canvas_resize, calculate_grid_layout, redraw_grid,
    # _on_mousewheel, download_item) are removed as they are no longer needed
    # for a "Coming Soon!" display.
