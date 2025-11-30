#!/usr/bin/env python3
"""
Linux Gaming Center - Storage Configs Panel
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import json
import os
import shutil
import sys
import subprocess


class StorageConfigsPanel:
    def __init__(self, parent, theme, scaler):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        input_bg = self.theme.get_color("input_background", "#1A1A1A")
        input_text = self.theme.get_color("input_text", "#FFFFFF")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        # Use grid to fill parent completely
        self.frame.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Configure frame to fill parent
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Config file for storage settings
        config_dir = Path.home() / ".config" / "linux-gaming-center"
        self.config_file = config_dir / "storage_config.json"
        config_dir.mkdir(parents=True, exist_ok=True)
        
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
            text="Storage Configs",
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=self.scaler.scale_padding(30))
        
        # Load current settings
        self.load_settings()
        
        # Create storage location sections
        self.create_storage_locations_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color, input_bg, input_text)
        
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
        """Load storage configuration settings"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        else:
            self.settings = {}
        
        # Set defaults if not present (use None to indicate default/not set)
        if "custom_main_location" not in self.settings:
            self.settings["custom_main_location"] = None
        if "custom_roms_location" not in self.settings:
            self.settings["custom_roms_location"] = None
        if "custom_accounts_location" not in self.settings:
            self.settings["custom_accounts_location"] = None
        if "custom_bios_location" not in self.settings:
            self.settings["custom_bios_location"] = None
    
    def save_settings(self):
        """Save storage configuration settings"""
        try:
            # Always ensure the config directory exists before saving
            # storage_config.json must always stay in ~/.config/linux-gaming-center
            config_dir = Path.home() / ".config" / "linux-gaming-center"
            config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving storage config: {e}")
    
    def get_current_main_path(self):
        """Get the current main path (either custom or default)"""
        custom_main = self.settings.get("custom_main_location")
        if custom_main:
            custom_path = Path(custom_main)
            if custom_path.name == "linux-gaming-center":
                return custom_path
            else:
                return custom_path / "linux-gaming-center"
        else:
            return Path.home() / ".config" / "linux-gaming-center"
    
    def get_current_data_path(self):
        """Get the current data path"""
        custom_main = self.settings.get("custom_main_location")
        if custom_main:
            custom_path = Path(custom_main)
            if custom_path.name == "linux-gaming-center":
                return custom_path / "data"
            else:
                return custom_path / "linux-gaming-center" / "data"
        else:
            return Path.home() / ".local" / "share" / "linux-gaming-center" / "data"
    
    def get_current_accounts_path(self):
        """Get the current accounts path"""
        custom_accounts = self.settings.get("custom_accounts_location")
        if custom_accounts:
            return Path(custom_accounts)
        elif self.settings.get("custom_main_location"):
            custom_path = Path(self.settings.get("custom_main_location"))
            if custom_path.name == "linux-gaming-center":
                return custom_path / "accounts"
            else:
                return custom_path / "linux-gaming-center" / "accounts"
        else:
            return Path.home() / ".config" / "linux-gaming-center" / "accounts"
    
    def get_current_roms_path(self):
        """Get the current ROMs path"""
        custom_roms = self.settings.get("custom_roms_location")
        if custom_roms:
            return Path(custom_roms)
        elif self.settings.get("custom_main_location"):
            custom_path = Path(self.settings.get("custom_main_location"))
            if custom_path.name == "linux-gaming-center":
                return custom_path / "roms"
            else:
                return custom_path / "linux-gaming-center" / "roms"
        else:
            return Path.home() / ".local" / "share" / "linux-gaming-center" / "roms"
    
    def get_current_bios_path(self):
        """Get the current BIOS path"""
        custom_bios = self.settings.get("custom_bios_location")
        if custom_bios:
            return Path(custom_bios)
        elif self.settings.get("custom_main_location"):
            custom_path = Path(self.settings.get("custom_main_location"))
            if custom_path.name == "linux-gaming-center":
                return custom_path / "bios"
            else:
                return custom_path / "linux-gaming-center" / "bios"
        else:
            return Path.home() / ".local" / "share" / "linux-gaming-center" / "bios"
    
    def show_migration_dialog(self, title, message, on_confirm):
        """Show a migration confirmation dialog"""
        bg_color = self.theme.get_color("background", "#1A1A2E")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#B0BEC5")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        
        # Create a toplevel dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title(title)
        dialog.configure(bg=bg_color)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the dialog - much larger size for better readability
        dialog_width = 900
        dialog_height = 650
        
        # Get root window position
        root = self.parent.winfo_toplevel()
        root_x = root.winfo_x()
        root_y = root.winfo_y()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        
        x = root_x + (root_width - dialog_width) // 2
        y = root_y + (root_height - dialog_height) // 2
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.resizable(False, False)
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            dialog,
            text=title,
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=(self.scaler.scale_padding(20), self.scaler.scale_padding(10)))
        
        # Message
        body_font = self.theme.get_font("body", scaler=self.scaler)
        message_label = tk.Label(
            dialog,
            text=message,
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            wraplength=850,
            justify=tk.LEFT
        )
        message_label.pack(padx=30, pady=20, fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = tk.Frame(dialog, bg=bg_color)
        button_frame.pack(pady=30)
        
        button_font = self.theme.get_font("button", scaler=self.scaler)
        
        def on_confirm_click():
            dialog.destroy()
            on_confirm()
        
        def on_cancel_click():
            dialog.destroy()
        
        # Confirm button
        confirm_button = tk.Button(
            button_frame,
            text="Confirm & Migrate",
            font=button_font,
            command=on_confirm_click,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=40,
            pady=20
        )
        confirm_button.pack(side=tk.LEFT, padx=20)
        
        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            font=button_font,
            command=on_cancel_click,
            bg=text_secondary,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=40,
            pady=20
        )
        cancel_button.pack(side=tk.LEFT, padx=20)
        
        # Wait for dialog to close
        dialog.wait_window()
    
    def show_manual_migration_dialog(self, title, message):
        """Show a dialog explaining manual migration is needed for BIOS/ROMs"""
        bg_color = self.theme.get_color("background", "#1A1A2E")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#B0BEC5")
        warning_color = self.theme.get_color("warning", "#FFA726")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        
        # Create a toplevel dialog
        dialog = tk.Toplevel(self.parent)
        dialog.title(title)
        dialog.configure(bg=bg_color)
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center the dialog - much larger size for better readability
        dialog_width = 950
        dialog_height = 700
        
        # Get root window position
        root = self.parent.winfo_toplevel()
        root_x = root.winfo_x()
        root_y = root.winfo_y()
        root_width = root.winfo_width()
        root_height = root.winfo_height()
        
        x = root_x + (root_width - dialog_width) // 2
        y = root_y + (root_height - dialog_height) // 2
        
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        dialog.resizable(False, False)
        
        result = {"confirmed": False}
        
        # Warning icon/title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            dialog,
            text="⚠️ " + title,
            font=heading_font,
            bg=bg_color,
            fg=warning_color
        )
        title_label.pack(pady=(self.scaler.scale_padding(20), self.scaler.scale_padding(10)))
        
        # Message
        body_font = self.theme.get_font("body", scaler=self.scaler)
        message_label = tk.Label(
            dialog,
            text=message,
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            wraplength=900,
            justify=tk.LEFT
        )
        message_label.pack(padx=30, pady=20, fill=tk.BOTH, expand=True)
        
        # Note about manual migration
        note_frame = tk.Frame(dialog, bg=bg_color)
        note_frame.pack(padx=30, pady=20, fill=tk.X)
        
        note_label = tk.Label(
            note_frame,
            text="📁 You will need to manually copy/move your files to the new location using your file manager.",
            font=body_font,
            bg=bg_color,
            fg=text_color,
            wraplength=900,
            justify=tk.LEFT
        )
        note_label.pack(fill=tk.X)
        
        # Button frame
        button_frame = tk.Frame(dialog, bg=bg_color)
        button_frame.pack(pady=30)
        
        button_font = self.theme.get_font("button", scaler=self.scaler)
        
        def on_confirm_click():
            result["confirmed"] = True
            dialog.destroy()
        
        def on_cancel_click():
            result["confirmed"] = False
            dialog.destroy()
        
        # Confirm button
        confirm_button = tk.Button(
            button_frame,
            text="I Understand, Update Path",
            font=button_font,
            command=on_confirm_click,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=40,
            pady=20
        )
        confirm_button.pack(side=tk.LEFT, padx=20)
        
        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            font=button_font,
            command=on_cancel_click,
            bg=text_secondary,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=40,
            pady=20
        )
        cancel_button.pack(side=tk.LEFT, padx=20)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return result["confirmed"]
    
    def migrate_directory(self, source, destination, exclude_dirs=None):
        """Migrate data from source to destination directory"""
        if exclude_dirs is None:
            exclude_dirs = []
        
        source = Path(source)
        destination = Path(destination)
        
        if not source.exists():
            return True  # Nothing to migrate
        
        try:
            # Create destination if it doesn't exist
            destination.mkdir(parents=True, exist_ok=True)
            
            # Copy all contents except excluded directories
            for item in source.iterdir():
                if item.name in exclude_dirs:
                    continue
                
                dest_item = destination / item.name
                
                if item.is_dir():
                    if dest_item.exists():
                        # Merge directories
                        self.migrate_directory(item, dest_item)
                    else:
                        shutil.copytree(item, dest_item)
                else:
                    shutil.copy2(item, dest_item)
            
            return True
        except Exception as e:
            print(f"Migration error: {e}")
            messagebox.showerror("Migration Error", f"Failed to migrate data:\n{str(e)}")
            return False
    
    def safely_delete_old_data(self, path, exclude_files=None, exclude_dirs=None, preserve_directory=False):
        """Safely delete old data after migration, preserving excluded files/dirs
        
        Args:
            path: The directory to clean up
            exclude_files: List of filenames to preserve
            exclude_dirs: List of directory names to preserve
            preserve_directory: If True, never delete the directory itself (only contents)
        """
        if exclude_files is None:
            exclude_files = []
        if exclude_dirs is None:
            exclude_dirs = []
        
        path = Path(path)
        
        if not path.exists():
            return True
        
        # Never delete the default config directory - storage_config.json must always live there
        default_config_dir = Path.home() / ".config" / "linux-gaming-center"
        if path == default_config_dir:
            preserve_directory = True
        
        try:
            # Delete contents of the directory, respecting exclusions
            for item in path.iterdir():
                if item.name in exclude_files or item.name in exclude_dirs:
                    continue
                
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            
            # If directory is now empty and we're allowed to delete it, remove it
            if not preserve_directory:
                remaining = list(path.iterdir())
                if not remaining:
                    path.rmdir()
            
            return True
        except Exception as e:
            print(f"Error deleting old data: {e}")
            # Don't show error to user - deletion failure is not critical
            return False
    
    def restart_application(self):
        """Restart the Linux Gaming Center application"""
        try:
            # Get the path to main.py
            from theme_manager import get_app_root
            app_root = get_app_root()
            main_script = app_root / "main.py"
            
            # Show restart message
            messagebox.showinfo(
                "Restart Required",
                "The application will now restart to apply the new storage location."
            )
            
            # Start a new instance of the application
            python_executable = sys.executable
            subprocess.Popen([python_executable, str(main_script)])
            
            # Exit the current instance
            root = self.parent.winfo_toplevel()
            root.quit()
            root.destroy()
            
        except Exception as e:
            print(f"Error restarting application: {e}")
            messagebox.showerror(
                "Restart Error",
                f"Failed to restart automatically. Please restart the application manually.\n\nError: {str(e)}"
            )
    
    def create_storage_locations_section(self, parent, bg_color, text_color, text_secondary, primary_color, input_bg, input_text):
        """Create section for custom storage locations"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Custom Storage Locations",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        description = tk.Label(
            section_frame,
            text="Set custom locations for storing Linux Gaming Center data. Leave empty to use default locations.",
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w",
            wraplength=self.scaler.scale_dimension(600)
        )
        description.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        # Main Linux-Gaming-Center location
        self.create_location_selector(
            section_frame,
            "Main Linux-Gaming-Center Location",
            "custom_main_location",
            "This location will contain a 'linux-gaming-center' folder with accounts, configs, and data (apps, emulators, etc.)",
            bg_color,
            text_color,
            text_secondary,
            primary_color,
            input_bg,
            input_text
        )
        
        # Accounts location
        self.create_location_selector(
            section_frame,
            "Accounts Location",
            "custom_accounts_location",
            "Custom location to store user accounts",
            bg_color,
            text_color,
            text_secondary,
            primary_color,
            input_bg,
            input_text
        )
        
        # ROMs location
        self.create_location_selector(
            section_frame,
            "ROMs Location",
            "custom_roms_location",
            "Custom location to store ROM files",
            bg_color,
            text_color,
            text_secondary,
            primary_color,
            input_bg,
            input_text
        )
        
        # BIOS location
        self.create_location_selector(
            section_frame,
            "BIOS Location",
            "custom_bios_location",
            "Custom location to store BIOS files",
            bg_color,
            text_color,
            text_secondary,
            primary_color,
            input_bg,
            input_text
        )
    
    def create_location_selector(self, parent, label_text, setting_key, description_text, bg_color, text_color, text_secondary, primary_color, input_bg, input_text):
        """Create a location selector with browse button"""
        selector_frame = tk.Frame(parent, bg=bg_color)
        selector_frame.pack(fill=tk.X, pady=self.scaler.scale_padding(15))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        # Label
        label = tk.Label(
            selector_frame,
            text=f"{label_text}:",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        # Description
        if description_text:
            desc_label = tk.Label(
                selector_frame,
                text=description_text,
                font=body_font,
                bg=bg_color,
                fg=text_secondary,
                anchor="w",
                wraplength=self.scaler.scale_dimension(600)
            )
            desc_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        # Path entry and browse button frame
        path_frame = tk.Frame(selector_frame, bg=bg_color)
        path_frame.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        # Path entry
        path_var = tk.StringVar(value=self.settings.get(setting_key, "") or "")
        path_entry = tk.Entry(
            path_frame,
            textvariable=path_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1,
            state="readonly"
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=self.scaler.scale_padding(5))
        
        def browse_location():
            """Browse for a directory"""
            directory = filedialog.askdirectory(
                parent=self.parent,
                title=f"Select {label_text}",
                initialdir=path_var.get() if path_var.get() else str(Path.home())
            )
            if directory:
                selected_path = Path(directory)
                
                # Handle different setting types
                if setting_key == "custom_main_location":
                    self.handle_main_location_change(selected_path, path_var, setting_key)
                elif setting_key == "custom_accounts_location":
                    self.handle_accounts_location_change(selected_path, path_var, setting_key)
                elif setting_key == "custom_roms_location":
                    self.handle_roms_location_change(selected_path, path_var, setting_key)
                elif setting_key == "custom_bios_location":
                    self.handle_bios_location_change(selected_path, path_var, setting_key)
        
        def clear_location():
            """Clear the custom location (use default)"""
            path_var.set("")
            self.settings[setting_key] = None
            self.save_settings()
        
        # Browse button
        browse_button = tk.Button(
            path_frame,
            text="Browse",
            font=body_font,
            command=browse_location,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(15),
            pady=self.scaler.scale_padding(5)
        )
        browse_button.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(10), 0))
        
        # Clear button (to reset to default)
        clear_button = tk.Button(
            path_frame,
            text="Clear",
            font=body_font,
            command=clear_location,
            bg=text_secondary,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(15),
            pady=self.scaler.scale_padding(5)
        )
        clear_button.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(5), 0))
        
        # Show default location info
        default_info = self.get_default_location_info(setting_key)
        if default_info:
            small_font = self.theme.get_font("body_small", scaler=self.scaler)
            default_label = tk.Label(
                selector_frame,
                text=f"Default: {default_info}",
                font=small_font,
                bg=bg_color,
                fg=text_secondary,
                anchor="w"
            )
            default_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
    
    def handle_main_location_change(self, selected_path, path_var, setting_key):
        """Handle changing the main storage location"""
        # Get current paths before change
        old_main_path = self.get_current_main_path()
        old_data_path = self.get_current_data_path()
        old_accounts_path = self.get_current_accounts_path()
        
        # New paths
        new_main_path = selected_path / "linux-gaming-center"
        
        message = (
            "Changing the main storage location will migrate your data to the new location.\n\n"
            "The following data will be migrated automatically:\n"
            "• User accounts\n"
            "• Configuration files\n"
            "• Apps data\n"
            "• Emulator settings\n"
            "• Open source gaming data\n"
            "• Windows/Steam data\n\n"
            "⚠️ IMPORTANT: BIOS and ROM folders will NOT be migrated automatically due to their "
            "potentially large size. You will need to manually move these folders to the new location.\n\n"
            "After migration, the old data will be safely deleted (except storage_config.json).\n\n"
            "The application will restart after migration completes."
        )
        
        def do_migration():
            try:
                # Create new directory structure
                new_main_path.mkdir(parents=True, exist_ok=True)
                (new_main_path / "accounts").mkdir(parents=True, exist_ok=True)
                (new_main_path / "data").mkdir(parents=True, exist_ok=True)
                (new_main_path / "data" / "apps").mkdir(parents=True, exist_ok=True)
                (new_main_path / "data" / "emulators").mkdir(parents=True, exist_ok=True)
                (new_main_path / "data" / "opensourcegaming").mkdir(parents=True, exist_ok=True)
                (new_main_path / "data" / "windowssteam").mkdir(parents=True, exist_ok=True)
                (new_main_path / "roms").mkdir(parents=True, exist_ok=True)
                (new_main_path / "bios").mkdir(parents=True, exist_ok=True)
                
                # Migrate main config files (excluding storage_config.json which stays in ~/.config)
                if old_main_path.exists():
                    for item in old_main_path.iterdir():
                        if item.name in ["accounts", "roms", "bios"]:
                            continue  # Handle separately
                        if item.name == "storage_config.json":
                            continue  # Keep storage config in default location
                        
                        dest_item = new_main_path / item.name
                        if item.is_dir():
                            if dest_item.exists():
                                self.migrate_directory(item, dest_item)
                            else:
                                shutil.copytree(item, dest_item)
                        else:
                            shutil.copy2(item, dest_item)
                
                # Migrate accounts (unless custom accounts location is set)
                if not self.settings.get("custom_accounts_location"):
                    if old_accounts_path.exists():
                        new_accounts_path = new_main_path / "accounts"
                        self.migrate_directory(old_accounts_path, new_accounts_path)
                
                # Migrate data directory
                if old_data_path.exists():
                    new_data_path = new_main_path / "data"
                    self.migrate_directory(old_data_path, new_data_path)
                
                # Update settings FIRST before deleting old data
                # This ensures storage_config.json exists before any deletion
                path_var.set(str(selected_path))
                self.settings[setting_key] = str(selected_path)
                self.save_settings()
                
                # Safely delete old data after successful migration
                # Keep storage_config.json in the default config location
                # preserve_directory=True ensures ~/.config/linux-gaming-center is never deleted
                if old_main_path.exists():
                    self.safely_delete_old_data(
                        old_main_path,
                        exclude_files=["storage_config.json"],
                        exclude_dirs=["roms", "bios"],  # Don't delete these - user may not have migrated yet
                        preserve_directory=True  # Never delete the config directory itself
                    )
                
                # Delete old data path if it's separate from main path
                if old_data_path.exists() and old_data_path != old_main_path / "data":
                    self.safely_delete_old_data(old_data_path)
                
                # Restart application
                self.restart_application()
                
            except Exception as e:
                messagebox.showerror("Migration Error", f"Failed to migrate data:\n{str(e)}")
        
        self.show_migration_dialog("Migrate Storage Location", message, do_migration)
    
    def handle_accounts_location_change(self, selected_path, path_var, setting_key):
        """Handle changing the accounts location"""
        old_accounts_path = self.get_current_accounts_path()
        
        message = (
            "Changing the accounts location will migrate all user account data to the new location.\n\n"
            "The following data will be migrated:\n"
            "• All user account profiles\n"
            "• Profile images\n"
            "• User preferences and settings\n"
            "• Recently used items\n\n"
            "After migration, the old accounts folder will be safely deleted.\n\n"
            "The application will restart after migration completes."
        )
        
        def do_migration():
            try:
                # Create new directory
                selected_path.mkdir(parents=True, exist_ok=True)
                
                # Migrate accounts
                if old_accounts_path.exists():
                    self.migrate_directory(old_accounts_path, selected_path)
                
                # Update settings FIRST before deleting old data
                path_var.set(str(selected_path))
                self.settings[setting_key] = str(selected_path)
                self.save_settings()
                
                # Safely delete old accounts folder after successful migration
                if old_accounts_path.exists():
                    self.safely_delete_old_data(old_accounts_path)
                
                # Restart application
                self.restart_application()
                
            except Exception as e:
                messagebox.showerror("Migration Error", f"Failed to migrate accounts:\n{str(e)}")
        
        self.show_migration_dialog("Migrate Accounts", message, do_migration)
    
    def handle_roms_location_change(self, selected_path, path_var, setting_key):
        """Handle changing the ROMs location - manual migration required"""
        old_roms_path = self.get_current_roms_path()
        
        message = (
            "You are changing the ROMs storage location.\n\n"
            "Due to the potentially large size of ROM files, automatic migration is NOT performed.\n\n"
            f"Current ROMs location:\n{old_roms_path}\n\n"
            f"New ROMs location:\n{selected_path}\n\n"
            "Please manually copy or move your ROM files from the old location to the new location "
            "using your file manager before or after changing this setting.\n\n"
            "The application will restart after updating the path."
        )
        
        confirmed = self.show_manual_migration_dialog("Manual ROM Migration Required", message)
        
        if confirmed:
            try:
                # Create new directory
                selected_path.mkdir(parents=True, exist_ok=True)
                
                # Update settings
                path_var.set(str(selected_path))
                self.settings[setting_key] = str(selected_path)
                self.save_settings()
                
                # Restart application
                self.restart_application()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update ROM location:\n{str(e)}")
    
    def handle_bios_location_change(self, selected_path, path_var, setting_key):
        """Handle changing the BIOS location - manual migration required"""
        old_bios_path = self.get_current_bios_path()
        
        message = (
            "You are changing the BIOS storage location.\n\n"
            "Due to the nature of BIOS files, automatic migration is NOT performed.\n\n"
            f"Current BIOS location:\n{old_bios_path}\n\n"
            f"New BIOS location:\n{selected_path}\n\n"
            "Please manually copy or move your BIOS files from the old location to the new location "
            "using your file manager before or after changing this setting.\n\n"
            "The application will restart after updating the path."
        )
        
        confirmed = self.show_manual_migration_dialog("Manual BIOS Migration Required", message)
        
        if confirmed:
            try:
                # Create new directory
                selected_path.mkdir(parents=True, exist_ok=True)
                
                # Update settings
                path_var.set(str(selected_path))
                self.settings[setting_key] = str(selected_path)
                self.save_settings()
                
                # Restart application
                self.restart_application()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update BIOS location:\n{str(e)}")
    
    def get_default_location_info(self, setting_key):
        """Get default location info for display"""
        defaults = {
            "custom_main_location": str(Path.home() / ".config" / "linux-gaming-center"),
            "custom_accounts_location": str(Path.home() / ".config" / "linux-gaming-center" / "accounts"),
            "custom_roms_location": str(Path.home() / ".local" / "share" / "linux-gaming-center" / "roms"),
            "custom_bios_location": str(Path.home() / ".local" / "share" / "linux-gaming-center" / "bios")
        }
        return defaults.get(setting_key, "")
    
    def destroy(self):
        """Destroy the panel"""
        self.frame.destroy()
