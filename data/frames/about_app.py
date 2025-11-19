import tkinter as tk
from tkinter import ttk
from paths import PathManager
from theme import load_theme # Import the theme loader

class AboutAppFrame(tk.Frame):
    def __init__(self, parent, controller, path_manager: PathManager):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.path_manager = path_manager

        # --- THEME LOADING ---
        self.theme = load_theme("about_app")
        self.colors = self.theme.get("colors", {})
        self.fonts = self.theme.get("fonts", {})
        self.text_content = self.theme.get("text", {})
        # --- END THEME LOADING ---

        self._configure_layout()
        self._create_widgets()

    def _configure_layout(self):
        """ Configures the main grid layout to center content. """
        bg_color = self.colors.get("background", "#2c2c2c")
        self.configure(bg=bg_color)

        # Center the content vertically and horizontally
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _create_widgets(self):
        """ Creates and styles widgets based on the loaded theme. """
        bg_color = self.colors.get("background", "#2c2c2c")
        text_color = self.colors.get("text", "white")

        # Get font configurations from the theme
        title_font_config = self.fonts.get("title", {})
        body_font_config = self.fonts.get("body", {})

        # Create font tuples
        title_font = (
            title_font_config.get("family", "Arial"),
            title_font_config.get("size", 20),
            title_font_config.get("weight", "bold")
        )
        body_font = (
            body_font_config.get("family", "Arial"),
            body_font_config.get("size", 12)
        )

        # Main container to hold all the labels
        container = ttk.Frame(self, style="About.TFrame")
        container.grid(row=0, column=0)

        # Configure a custom style for the container frame
        style = ttk.Style(self)
        style.configure("About.TFrame", background=bg_color)

        # Get text from the theme
        title_text = self.text_content.get("title", "About This App")
        version_text = self.text_content.get("version", "Version: N/A")
        description_text = self.text_content.get("description", "")

        # Create and pack the labels
        title_label = ttk.Label(container, text=title_text, font=title_font, foreground=text_color, background=bg_color)
        title_label.pack(pady=(20, 10), padx=20)

        version_label = ttk.Label(container, text=version_text, font=body_font, foreground=text_color, background=bg_color)
        version_label.pack(pady=5, padx=20)

        description_label = ttk.Label(container, text=description_text, font=body_font, foreground=text_color, background=bg_color, wraplength=450, justify=tk.CENTER)
        description_label.pack(pady=10, padx=20)

    def on_show_frame(self):
        """Called when this frame is brought to the front."""
        # You could add logic here to refresh content if needed
        print("About App Frame is now visible.")

