#!/usr/bin/env python3
"""
Linux Gaming Center - Library Configs Panel
"""

import tkinter as tk
from pathlib import Path
import json


class LibraryConfigsPanel:
    def __init__(self, parent, theme, scaler):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        # Use grid to fill parent completely
        self.frame.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Configure frame to fill parent
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Config file for library settings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from path_helper import get_config_file_path
        self.config_file = get_config_file_path("library_config.json")
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Scrollable canvas for content (no visible scrollbar)
        self.canvas = tk.Canvas(self.frame, bg=bg_color, highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_scroll_region(event=None):
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=bbox)
            # Update canvas window width to match canvas
            if event:
                canvas_width = event.width
                if canvas_width > 0:
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            else:
                self.canvas.update_idletasks()
                canvas_width = self.canvas.winfo_width()
                if canvas_width > 1:
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        self.canvas.bind("<Configure>", configure_scroll_region)
        
        # Use grid to fill entire frame
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            if event.delta:
                scroll_amount = int(-1 * (event.delta / 40))
                self.canvas.yview_scroll(scroll_amount, "units")
            return "break"
        
        def scroll_up(e):
            if self.canvas.yview()[0] > 0.0:
                self.canvas.yview_scroll(-3, "units")
        
        def scroll_down(e):
            if self.canvas.yview()[1] < 1.0:
                self.canvas.yview_scroll(3, "units")
        
        self.canvas.bind("<MouseWheel>", on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        self.canvas.bind("<Button-4>", scroll_up)
        self.canvas.bind("<Button-5>", scroll_down)
        self.scrollable_frame.bind("<Button-4>", scroll_up)
        self.scrollable_frame.bind("<Button-5>", scroll_down)
        
        # Arrow key scrolling
        def on_arrow_key(event):
            if event.keysym == "Up":
                if self.canvas.yview()[0] > 0.0:
                    self.canvas.yview_scroll(-3, "units")
            elif event.keysym == "Down":
                if self.canvas.yview()[1] < 1.0:
                    self.canvas.yview_scroll(3, "units")
            elif event.keysym == "Page_Up":
                self.canvas.yview_scroll(-1, "page")
            elif event.keysym == "Page_Down":
                self.canvas.yview_scroll(1, "page")
            elif event.keysym == "Home":
                self.canvas.yview_moveto(0)
            elif event.keysym == "End":
                self.canvas.yview_moveto(1)
            return "break"
        
        self.frame.bind("<KeyPress>", on_arrow_key)
        self.canvas.bind("<KeyPress>", on_arrow_key)
        self.scrollable_frame.bind("<KeyPress>", on_arrow_key)
        
        self.frame.focus_set()
        self.canvas.focus_set()
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            self.scrollable_frame,
            text="Library Configs",
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=self.scaler.scale_padding(30))
        
        # Load current settings
        self.load_settings()
        
        # Add Button Visibility Section
        self.create_add_button_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color)
        
        # Force initial canvas width update after a short delay
        def update_canvas_width():
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            if canvas_width > 1:
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
                bbox = self.canvas.bbox("all")
                if bbox:
                    self.canvas.configure(scrollregion=bbox)
        
        # Update canvas scroll region
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
        
        # Force update after delays
        self.parent.after(50, update_canvas_width)
        self.parent.after(200, update_canvas_width)
    
    def load_settings(self):
        """Load library configuration settings"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        else:
            self.settings = {}
        
        # Set defaults if not present
        if "show_add_button_apps" not in self.settings:
            self.settings["show_add_button_apps"] = True
        if "show_add_button_opensourcegaming" not in self.settings:
            self.settings["show_add_button_opensourcegaming"] = True
        if "show_add_button_windowssteam" not in self.settings:
            self.settings["show_add_button_windowssteam"] = True
        if "show_add_button_emulators" not in self.settings:
            self.settings["show_add_button_emulators"] = True
    
    def save_settings(self):
        """Save library configuration settings"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving library config: {e}")
    
    def create_add_button_section(self, parent, bg_color, text_color, text_secondary, primary_color):
        """Create section for controlling add button visibility"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Add Button Visibility",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        description = tk.Label(
            section_frame,
            text="Control whether users can see the 'Add' button in each library. When hidden, users cannot add new items.",
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w",
            wraplength=self.scaler.scale_dimension(600)
        )
        description.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        # Apps Library
        self.create_library_toggle(
            section_frame, 
            "Apps Library", 
            "show_add_button_apps",
            bg_color, 
            text_color, 
            text_secondary, 
            primary_color
        )
        
        # Open Source Gaming Library
        self.create_library_toggle(
            section_frame, 
            "Open Source Gaming Library", 
            "show_add_button_opensourcegaming",
            bg_color, 
            text_color, 
            text_secondary, 
            primary_color
        )
        
        # Windows & Steam Library
        self.create_library_toggle(
            section_frame, 
            "Windows & Steam Library", 
            "show_add_button_windowssteam",
            bg_color, 
            text_color, 
            text_secondary, 
            primary_color
        )
        
        # Emulators Library
        self.create_library_toggle(
            section_frame, 
            "Emulators Library", 
            "show_add_button_emulators",
            bg_color, 
            text_color, 
            text_secondary, 
            primary_color
        )
    
    def create_library_toggle(self, parent, library_name, setting_key, bg_color, text_color, text_secondary, primary_color):
        """Create a toggle for a specific library"""
        toggle_frame = tk.Frame(parent, bg=bg_color)
        toggle_frame.pack(fill=tk.X, pady=self.scaler.scale_padding(10))
        
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        label = tk.Label(
            toggle_frame,
            text=f"{library_name}:",
            font=body_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        var = tk.BooleanVar(value=self.settings.get(setting_key, True))
        
        def toggle_callback():
            self.settings[setting_key] = var.get()
            self.save_settings()
        
        toggle = tk.Checkbutton(
            toggle_frame,
            variable=var,
            command=toggle_callback,
            text="Show Add Button" if var.get() else "Hide Add Button",
            font=body_font,
            bg=bg_color,
            fg=text_color,
            selectcolor=primary_color,
            activebackground=bg_color,
            activeforeground=text_color,
            onvalue=True,
            offvalue=False
        )
        
        # Update text when toggled
        def update_text():
            toggle.config(text="Show Add Button" if var.get() else "Hide Add Button")
            toggle_callback()
        
        var.trace('w', lambda *args: update_text())
        toggle.pack(side=tk.RIGHT)
    
    def destroy(self):
        """Destroy the panel"""
        self.frame.destroy()
