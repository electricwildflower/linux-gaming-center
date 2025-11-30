#!/usr/bin/env python3
"""
Linux Gaming Center - Control Panel Frame
Admin control panel for system management
"""

import tkinter as tk
from pathlib import Path
import sys


class ControlPanelFrame:
    def __init__(self, parent, theme, scaler):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        self.current_panel = None
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        # Main frame that fills entire parent - use grid for full control
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.grid(row=0, column=0, sticky="nsew")
        # Configure parent to allow frame to expand
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Use grid for better control over layout
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=0)  # Sidebar fixed width
        self.frame.grid_columnconfigure(1, weight=1)  # Content area expands
        
        # Vertical menu sidebar (left side, full height of window)
        sidebar_width = self.scaler.scale_dimension(250)
        sidebar = tk.Frame(self.frame, bg=menu_bar_color, width=sidebar_width)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_rowconfigure(0, weight=0)  # Title row (fixed)
        sidebar.grid_rowconfigure(1, weight=1)  # Menu container expands
        sidebar.grid_columnconfigure(0, weight=1)  # Full width
        
        # Content area (right side) - where panels will be displayed (fills entire right side)
        self.content_area = tk.Frame(self.frame, bg=bg_color)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        # Configure content area to fill and expand
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        # Sidebar title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        sidebar_title = tk.Label(
            sidebar,
            text="Control Panel",
            font=heading_font,
            bg=menu_bar_color,
            fg=text_color,
            anchor="w"
        )
        sidebar_title.grid(row=0, column=0, sticky="ew", padx=self.scaler.scale_padding(15), pady=(self.scaler.scale_padding(20), self.scaler.scale_padding(30)))
        
        # Menu items container (fills remaining vertical space)
        menu_container = tk.Frame(sidebar, bg=menu_bar_color)
        menu_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_columnconfigure(0, weight=1)
        
        # Sidebar menu items (vertical menu)
        button_font = self.theme.get_font("button", scaler=self.scaler)
        menu_items = [
            ("Account Settings", "accountsettings"),
            ("Controller settings", "controllersettings"),
            ("Dashboard configs", "dashboardconfigs"),
            ("Display Settings", "displaysettings"),
            ("Emulator Settings", "emulatorsettings"),
            ("General Settings", "generalsettings"),
            ("Library configs", "libraryconfigs"),
            ("Rom Settings", "romsettings"),
            ("Storage configs", "storageconfigs"),
            ("Theme Settings", "themesettings")
        ]
        
        self.menu_buttons = {}
        for idx, (item_text, item_key) in enumerate(menu_items):
            btn = tk.Button(
                menu_container,
                text=item_text,
                font=button_font,
                bg=menu_bar_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                borderwidth=0,
                anchor="w",
                padx=self.scaler.scale_padding(15),
                pady=self.scaler.scale_padding(10),
                activebackground=self.theme.get_color("primary", "#9D4EDD"),
                activeforeground=text_color,
                command=lambda k=item_key: self.load_panel(k)
            )
            btn.pack(fill=tk.X, padx=self.scaler.scale_padding(10), pady=self.scaler.scale_padding(5))
            self.menu_buttons[item_key] = btn
        
        # Load default panel (Account Settings)
        self.load_panel("accountsettings")
    
    def load_panel(self, panel_key):
        """Load a panel based on the key"""
        # Highlight the selected menu button
        for key, btn in self.menu_buttons.items():
            if key == panel_key:
                btn.config(bg=self.theme.get_color("primary", "#9D4EDD"))
            else:
                btn.config(bg=self.theme.get_color("menu_bar", "#2D2D2D"))
        
        # Clear current panel
        if self.current_panel:
            self.current_panel.destroy()
        
        # Add frames directory to path for imports
        from theme_manager import get_app_root
        app_root = get_app_root()
        panels_dir = app_root / "data" / "frames" / "controlpanels"
        if str(panels_dir) not in sys.path:
            sys.path.insert(0, str(panels_dir))
        
        try:
            # Map panel keys to their module and class names
            panel_map = {
                "accountsettings": ("accountsettings", "AccountSettingsPanel"),
                "dashboardconfigs": ("dashboardconfigs", "DashboardConfigsPanel"),
                "libraryconfigs": ("libraryconfigs", "LibraryConfigsPanel"),
                "emulatorsettings": ("emulatorsettings", "EmulatorSettingsPanel"),
                "romsettings": ("romsettings", "RomSettingsPanel"),
                "themesettings": ("themesettings", "ThemeSettingsPanel"),
                "generalsettings": ("generalsettings", "GeneralSettingsPanel"),
                "displaysettings": ("displaysettings", "DisplaySettingsPanel"),
                "controllersettings": ("controllersettings", "ControllerSettingsPanel"),
                "storageconfigs": ("storageconfigs", "StorageConfigsPanel")
            }
            
            module_name, class_name = panel_map.get(panel_key, ("accountsettings", "AccountSettingsPanel"))
            
            # Dynamically import the panel module
            module = __import__(module_name)
            panel_class = getattr(module, class_name)
            
            # Create and display the panel
            self.current_panel = panel_class(self.content_area, self.theme, self.scaler)
            # Ensure panel fills content area
            if hasattr(self.current_panel, 'frame'):
                self.current_panel.frame.grid(row=0, column=0, sticky="nsew")
                self.content_area.grid_rowconfigure(0, weight=1)
                self.content_area.grid_columnconfigure(0, weight=1)
            
            # Update canvas if panel has one (for account settings and other scrollable panels)
            def update_panel_canvas():
                if hasattr(self.current_panel, 'canvas') and hasattr(self.current_panel, 'canvas_window'):
                    self.current_panel.canvas.update_idletasks()
                    canvas_width = self.current_panel.canvas.winfo_width()
                    if canvas_width > 1:
                        self.current_panel.canvas.itemconfig(self.current_panel.canvas_window, width=canvas_width)
                        bbox = self.current_panel.canvas.bbox("all")
                        if bbox:
                            self.current_panel.canvas.configure(scrollregion=bbox)
                    # Also trigger configure event to ensure proper sizing
                    self.current_panel.canvas.event_generate("<Configure>", width=canvas_width)
            
            # Update after panel is created (multiple delays to ensure it works)
            self.parent.after(50, update_panel_canvas)
            self.parent.after(150, update_panel_canvas)
            self.parent.after(300, update_panel_canvas)
                
        except Exception as e:
            print(f"Error loading panel {panel_key}: {e}")
            import traceback
            traceback.print_exc()
            # Show error message
            error_label = tk.Label(
                self.content_area,
                text=f"Error loading {panel_key}:\n{str(e)}",
                bg=self.theme.get_color("background", "#000000"),
                fg=self.theme.get_color("text_error", "#E74C3C"),
                font=self.theme.get_font("body", scaler=self.scaler)
            )
            error_label.pack(pady=self.scaler.scale_padding(50))
            self.current_panel = error_label
    
    def show(self):
        """Show the frame"""
        # Frame is already placed with grid in __init__, just ensure it's visible
        self.frame.grid(row=0, column=0, sticky="nsew")
    
    def hide(self):
        """Hide the frame"""
        self.frame.grid_remove()
