#!/usr/bin/env python3
"""
Linux Gaming Center - Console/Computer Library View
Template for individual emulator library views
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import json
import os
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from path_helper import get_roms_path, get_bios_path

# Try to import PIL for image handling
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ConsoleLibraryFrame:
    def __init__(self, parent, theme, scaler, username=None, console_name=None, short_name=None, roms_dir=None, bios_dir=None, back_callback=None):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        self.username = username
        self.console_name = console_name or "Console"
        self.short_name = short_name or "console"
        if roms_dir:
            self.roms_dir = Path(roms_dir)
        else:
            base_roms = get_roms_path()
            self.roms_dir = base_roms / self.short_name
        if bios_dir:
            self.bios_dir = Path(bios_dir)
        else:
            base_bios = get_bios_path()
            self.bios_dir = base_bios / self.short_name
        self.back_callback = back_callback
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Top bar with title and buttons
        top_bar = tk.Frame(self.frame, bg=bg_color)
        top_bar.pack(fill=tk.X, padx=self.scaler.scale_padding(20), pady=self.scaler.scale_padding(20))
        
        # Back button (if callback provided)
        if self.back_callback:
            button_font = self.theme.get_font("button", scaler=self.scaler)
            back_button = tk.Button(
                top_bar,
                text="← Back to Emulators",
                font=button_font,
                command=self.go_back,
                bg=primary_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                borderwidth=0,
                padx=self.scaler.scale_padding(15),
                pady=self.scaler.scale_padding(10)
            )
            back_button.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(20)))
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            top_bar,
            text=self.console_name,
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(side=tk.LEFT)
        
        # Scrollable canvas for ROM grid
        canvas_frame = tk.Frame(self.frame, bg=bg_color)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=self.scaler.scale_padding(20), pady=(0, self.scaler.scale_padding(20)))
        
        # Create scrollable canvas
        self.canvas = tk.Canvas(canvas_frame, bg=bg_color, highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_scroll_region(event=None):
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=(0, 0, bbox[2], bbox[3] + 50))
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
        
        def configure_canvas(event):
            canvas_width = event.width
            if canvas_width > 0:
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            configure_scroll_region()
        
        self.canvas.bind("<Configure>", configure_canvas)
        
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Mousewheel scrolling
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        def scroll_up(e):
            if self.canvas.yview()[0] > 0.0:
                self.canvas.yview_scroll(-3, "units")
        
        def scroll_down(e):
            if self.canvas.yview()[1] < 1.0:
                self.canvas.yview_scroll(3, "units")
        
        self.canvas.bind("<Button-4>", scroll_up)
        self.canvas.bind("<Button-5>", scroll_down)
        self.scrollable_frame.bind("<Button-4>", scroll_up)
        self.scrollable_frame.bind("<Button-5>", scroll_down)
        
        # Load ROMs
        self.load_roms()
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        if event.delta:
            scroll_amount = int(-1 * (event.delta / 40))
            if scroll_amount < 0:
                if self.canvas.yview()[1] < 1.0:
                    self.canvas.yview_scroll(scroll_amount, "units")
            else:
                if self.canvas.yview()[0] > 0.0:
                    self.canvas.yview_scroll(scroll_amount, "units")
    
    def load_roms(self):
        """Load and display all files and directories in the ROMs folder"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Ensure ROMs directory exists
        self.roms_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all files and directories in the ROMs folder
        rom_items = []
        try:
            for item in self.roms_dir.iterdir():
                rom_items.append(item)
        except Exception as e:
            print(f"Error reading ROMs directory: {e}")
        
        # Sort items: directories first, then files, both alphabetically
        rom_items.sort(key=lambda x: (x.is_file(), x.name.lower()))
        
        if not rom_items:
            # Show empty state
            bg_color = self.theme.get_color("background", "#000000")
            text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
            
            empty_label = tk.Label(
                self.scrollable_frame,
                text=f"No ROMs found in:\n{self.roms_dir}\n\nAdd ROM files to this directory to see them here.",
                font=self.theme.get_font("body", scaler=self.scaler),
                bg=bg_color,
                fg=text_secondary,
                justify=tk.CENTER
            )
            empty_label.pack(pady=self.scaler.scale_padding(50))
            return
        
        # Display ROMs in grid
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        # Grid configuration
        items_per_row = 4
        button_width = self.scaler.scale_dimension(350)
        button_height = self.scaler.scale_dimension(200)
        button_padding = self.scaler.scale_padding(15)
        
        # Configure grid columns
        for col in range(items_per_row):
            self.scrollable_frame.grid_columnconfigure(col, weight=0, minsize=button_width + (button_padding * 2))
        
        for i, rom_item in enumerate(rom_items):
            row = i // items_per_row
            col = i % items_per_row
            
            # Create button frame
            button_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
            button_frame.grid(row=row, column=col, padx=button_padding, pady=button_padding)
            
            # Get display name
            if rom_item.is_dir():
                item_name = f"[DIR] {rom_item.name}"
            else:
                item_name = rom_item.name
            
            # Create button (placeholder - you can add ROM cover images later)
            button = tk.Button(
                button_frame,
                text=item_name,
                command=lambda ri=rom_item: self.run_rom(ri),
                bg=menu_bar_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                width=self.scaler.scale_dimension(20),
                height=self.scaler.scale_dimension(10),
                font=self.theme.get_font("body_small", scaler=self.scaler)
            )
            button.pack()
            
            # Item name label below button
            name_label = tk.Label(
                button_frame,
                text=item_name,
                font=self.theme.get_font("body_small", scaler=self.scaler),
                bg=bg_color,
                fg=text_color,
                wraplength=button_width
            )
            name_label.pack(pady=(self.scaler.scale_padding(5), 0))
        
        # Update canvas scroll region
        self.scrollable_frame.update_idletasks()
        self.canvas.update_idletasks()
        
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=(0, 0, bbox[2], bbox[3] + 50))
        else:
            canvas_width = self.canvas.winfo_width() or 800
            canvas_height = self.canvas.winfo_height() or 600
            self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        self.canvas.yview_moveto(0)
    
    def run_rom(self, rom_item):
        """Handle ROM file or directory click"""
        if rom_item.is_dir():
            messagebox.showinfo("Info", f"Directory: {rom_item.name}\n\nPath: {rom_item}\n\nDirectory browsing not yet implemented.")
        else:
            messagebox.showinfo("Info", f"ROM file: {rom_item.name}\n\nPath: {rom_item}\n\nROM launch functionality would be implemented here.")
    
    def show(self):
        """Show the frame"""
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.load_roms()
    
    def go_back(self):
        """Go back to emulators list"""
        if self.back_callback:
            self.back_callback()
    
    def hide(self):
        """Hide the frame"""
        self.frame.pack_forget()

