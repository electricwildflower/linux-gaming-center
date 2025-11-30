#!/usr/bin/env python3
"""
Linux Gaming Center - Emulator Settings Panel
"""

import tkinter as tk
from pathlib import Path
import json


class EmulatorSettingsPanel:
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
        
        # Config file for emulator settings
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
            text="Emulator Settings",
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=self.scaler.scale_padding(30))
        
        # Load current settings
        self.load_settings()
        
        # Add Right-Click Menu Visibility Section
        self.create_right_click_menu_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color)
        
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
        """Load emulator configuration settings"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        else:
            self.settings = {}
        
        # Set defaults if not present
        if "show_emulator_context_menu" not in self.settings:
            self.settings["show_emulator_context_menu"] = True  # Default: show to everyone
    
    def save_settings(self):
        """Save emulator configuration settings"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving emulator settings: {e}")
    
    def create_right_click_menu_section(self, parent, bg_color, text_color, text_secondary, primary_color):
        """Create section for controlling right-click menu visibility"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Right-Click Menu Visibility",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        description = tk.Label(
            section_frame,
            text="Control whether non-admin users can see the right-click context menu on emulator buttons. When unchecked, only administrators will see the context menu.",
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w",
            wraplength=self.scaler.scale_dimension(600)
        )
        description.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        # Right-click menu visibility toggle
        toggle_frame = tk.Frame(section_frame, bg=bg_color)
        toggle_frame.pack(fill=tk.X, pady=self.scaler.scale_padding(10))
        
        label = tk.Label(
            toggle_frame,
            text="Show right-click menu to non-admin users:",
            font=body_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        var = tk.BooleanVar(value=self.settings.get("show_emulator_context_menu", True))
        
        def toggle_callback():
            self.settings["show_emulator_context_menu"] = var.get()
            self.save_settings()
        
        toggle = tk.Checkbutton(
            toggle_frame,
            variable=var,
            command=toggle_callback,
            text="Enabled" if var.get() else "Disabled",
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
            toggle.config(text="Enabled" if var.get() else "Disabled")
            toggle_callback()
        
        var.trace('w', lambda *args: update_text())
        toggle.pack(side=tk.RIGHT)
    
    def destroy(self):
        """Destroy the panel"""
        self.frame.destroy()

