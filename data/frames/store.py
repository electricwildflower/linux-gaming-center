#!/usr/bin/env python3
"""
Linux Gaming Center - Store Frame
Application store for downloading games and apps
"""

import tkinter as tk
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class StoreFrame:
    def __init__(self, parent, theme, scaler, username=None):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        self.username = username
        self.current_tab = None
        self.tab_buttons = {}
        self.tab_content_frame = None
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        input_bg = self.theme.get_color("input_background", "#1A1A1A")
        input_text = self.theme.get_color("input_text", "#FFFFFF")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure frame grid
        self.frame.grid_rowconfigure(0, weight=0)  # Search bar row
        self.frame.grid_rowconfigure(1, weight=0)  # Tabs row
        self.frame.grid_rowconfigure(2, weight=1)  # Content row (expandable)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # ===== Search Bar Section =====
        search_frame = tk.Frame(self.frame, bg=bg_color)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(self.scaler.scale_padding(20), self.scaler.scale_padding(15)))
        
        # Center the search bar
        search_frame.grid_columnconfigure(0, weight=1)
        search_frame.grid_columnconfigure(1, weight=0)
        search_frame.grid_columnconfigure(2, weight=1)
        
        # Search container (centered)
        search_container = tk.Frame(search_frame, bg=bg_color)
        search_container.grid(row=0, column=1)
        
        # Search entry
        body_font = self.theme.get_font("body", scaler=self.scaler)
        search_width = self.scaler.scale_dimension(40)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_container,
            textvariable=self.search_var,
            font=body_font,
            width=search_width,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.FLAT,
            highlightthickness=2,
            highlightbackground=menu_bar_color,
            highlightcolor=primary_color
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(10)), ipady=self.scaler.scale_padding(8))
        self.search_entry.insert(0, "Search the store...")
        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<Return>", self._on_search)
        
        # Search button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        search_button = tk.Button(
            search_container,
            text="Search",
            font=button_font,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(20),
            pady=self.scaler.scale_padding(8),
            command=self._on_search
        )
        search_button.pack(side=tk.LEFT)
        
        # ===== Tabs Section =====
        tabs_frame = tk.Frame(self.frame, bg=bg_color)
        tabs_frame.grid(row=1, column=0, sticky="ew", pady=(0, self.scaler.scale_padding(15)))
        
        # Center the tabs
        tabs_frame.grid_columnconfigure(0, weight=1)
        tabs_frame.grid_columnconfigure(1, weight=0)
        tabs_frame.grid_columnconfigure(2, weight=1)
        
        # Tabs container (centered)
        tabs_container = tk.Frame(tabs_frame, bg=bg_color)
        tabs_container.grid(row=0, column=1)
        
        # Tab definitions
        tabs = [
            ("opensourcegames", "Open Source Games"),
            ("emulators", "Emulators"),
            ("apps", "Apps"),
            ("plugins", "Plugins"),
            ("other", "Other")
        ]
        
        # Create tab buttons
        for tab_id, tab_label in tabs:
            btn = tk.Button(
                tabs_container,
                text=tab_label,
                font=button_font,
                bg=menu_bar_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                padx=self.scaler.scale_padding(20),
                pady=self.scaler.scale_padding(10),
                command=lambda t=tab_id: self.switch_tab(t)
            )
            btn.pack(side=tk.LEFT, padx=self.scaler.scale_padding(5))
            self.tab_buttons[tab_id] = btn
        
        # ===== Content Section =====
        content_frame = tk.Frame(self.frame, bg=bg_color)
        content_frame.grid(row=2, column=0, sticky="nsew", padx=self.scaler.scale_padding(20))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)
        
        # Tab content container
        self.tab_content_frame = tk.Frame(content_frame, bg=bg_color)
        self.tab_content_frame.grid(row=0, column=0, sticky="nsew")
        self.tab_content_frame.grid_rowconfigure(0, weight=1)
        self.tab_content_frame.grid_columnconfigure(0, weight=1)
        
        # Load default tab
        self.switch_tab("opensourcegames")
    
    def _on_search_focus_in(self, event):
        """Handle search entry focus in"""
        if self.search_var.get() == "Search the store...":
            self.search_entry.delete(0, tk.END)
            text_color = self.theme.get_color("input_text", "#FFFFFF")
            self.search_entry.config(fg=text_color)
    
    def _on_search_focus_out(self, event):
        """Handle search entry focus out"""
        if not self.search_var.get():
            text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
            self.search_entry.insert(0, "Search the store...")
            self.search_entry.config(fg=text_secondary)
    
    def _on_search(self, event=None):
        """Handle search"""
        search_term = self.search_var.get()
        if search_term and search_term != "Search the store...":
            print(f"Searching for: {search_term}")
            # TODO: Implement search functionality
    
    def switch_tab(self, tab_id):
        """Switch to a different tab"""
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        # Update tab button styles
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.config(bg=primary_color)
            else:
                btn.config(bg=menu_bar_color)
        
        # Clear current content
        for widget in self.tab_content_frame.winfo_children():
            widget.destroy()
        
        self.current_tab = tab_id
        
        # Load tab content
        if tab_id == "opensourcegames":
            self._load_opensourcegames_tab()
        elif tab_id == "emulators":
            self._load_emulators_tab()
        elif tab_id == "apps":
            self._load_apps_tab()
        elif tab_id == "plugins":
            self._load_plugins_tab()
        elif tab_id == "other":
            self._load_other_tab()
    
    def _create_placeholder_content(self, title, description):
        """Create placeholder content for a tab"""
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        
        # Center container
        center_frame = tk.Frame(self.tab_content_frame, bg=bg_color)
        center_frame.place(relx=0.5, rely=0.4, anchor=tk.CENTER)
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            center_frame,
            text=title,
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=(0, self.scaler.scale_padding(15)))
        
        # Description
        body_font = self.theme.get_font("body", scaler=self.scaler)
        desc_label = tk.Label(
            center_frame,
            text=description,
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            justify=tk.CENTER
        )
        desc_label.pack()
    
    def _load_opensourcegames_tab(self):
        """Load Open Source Games tab content"""
        self._create_placeholder_content(
            "Open Source Games",
            "Browse and download free, open source games.\n\nContent coming soon..."
        )
    
    def _load_emulators_tab(self):
        """Load Emulators tab content"""
        self._create_placeholder_content(
            "Emulators",
            "Download emulators for various gaming platforms.\n\nContent coming soon..."
        )
    
    def _load_apps_tab(self):
        """Load Apps tab content"""
        self._create_placeholder_content(
            "Apps",
            "Discover useful applications for gaming.\n\nContent coming soon..."
        )
    
    def _load_plugins_tab(self):
        """Load Plugins tab content"""
        self._create_placeholder_content(
            "Plugins",
            "Extend Linux Gaming Center with plugins.\n\nContent coming soon..."
        )
    
    def _load_other_tab(self):
        """Load Other tab content"""
        self._create_placeholder_content(
            "Other",
            "Miscellaneous downloads and resources.\n\nContent coming soon..."
        )
    
    def show(self):
        """Show the frame"""
        self.frame.pack(fill=tk.BOTH, expand=True)
    
    def hide(self):
        """Hide the frame"""
        self.frame.pack_forget()
    
    def destroy(self):
        """Destroy the frame"""
        self.frame.destroy()
