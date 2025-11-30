#!/usr/bin/env python3
"""
Linux Gaming Center - Apps Frame
App library similar to Jellyfin's movie library
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
from pathlib import Path
import json
import os
import subprocess
import shutil
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from path_helper import get_data_base_path, get_user_account_dir, get_config_file_path

# Try to import PIL for image handling
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class AppsFrame:
    def __init__(self, parent, theme, scaler, username=None):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        self.username = username
        
        # Base directory for apps (shared across all users)
        data_base = get_data_base_path()
        self.apps_base_dir = data_base / "apps"
        self.apps_json_path = self.apps_base_dir / "apps.json"
        
        # Per-user recently used apps directory
        if username:
            self.user_account_dir = get_user_account_dir(username)
            self.user_account_dir.mkdir(parents=True, exist_ok=True)
            self.recently_used_file = self.user_account_dir / "recently_used.json"
        else:
            self.recently_used_file = None
        
        # Ensure base directory exists
        self.apps_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize apps.json if it doesn't exist
        if not self.apps_json_path.exists():
            self._init_apps_json()
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Top bar with Add App button
        top_bar = tk.Frame(self.frame, bg=bg_color)
        top_bar.pack(fill=tk.X, padx=self.scaler.scale_padding(20), pady=self.scaler.scale_padding(20))
        
        # Check if user is admin
        is_admin = self.is_admin()
        
        # Check if add button should be shown (admins always see it)
        show_add_button = True
        if not is_admin:
            config_file = get_config_file_path("library_config.json")
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    show_add_button = config.get("show_add_button_apps", True)
                except:
                    pass
        
        # Add App button (top left) - only show if enabled (or if admin)
        button_font = self.theme.get_font("button", scaler=self.scaler)
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        self.add_app_button = tk.Button(
            top_bar,
            text="+ Add App",
            font=button_font,
            command=self.show_add_app_popup,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            padx=self.scaler.scale_padding(20),
            pady=self.scaler.scale_padding(10)
        )
        if show_add_button:
            self.add_app_button.pack(side=tk.LEFT)
        else:
            self.add_app_button.pack_forget()
        
        # Sort dropdown (next to Add App button)
        label_font = self.theme.get_font("label", scaler=self.scaler)
        sort_label = tk.Label(
            top_bar,
            text="Sort:",
            font=label_font,
            bg=bg_color,
            fg=text_color
        )
        sort_label.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(20), self.scaler.scale_padding(5)))
        
        # Sort options
        self.sort_var = tk.StringVar(value="A to Z")
        sort_options = ["A to Z", "Z to A", "Newest added", "Oldest added"]
        
        # Create styled combobox
        input_bg = self.theme.get_color("input_background", "#1A1A1A")
        input_text = self.theme.get_color("input_text", "#FFFFFF")
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        sort_combobox = ttk.Combobox(
            top_bar,
            textvariable=self.sort_var,
            values=sort_options,
            state="readonly",
            font=body_font,
            width=15
        )
        sort_combobox.pack(side=tk.LEFT)
        sort_combobox.bind("<<ComboboxSelected>>", lambda e: self.load_apps())
        
        # Style the combobox
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TCombobox',
            fieldbackground=input_bg,
            background=input_bg,
            foreground=input_text,
            borderwidth=1,
            relief=tk.SOLID
        )
        style.map('TCombobox',
            fieldbackground=[('readonly', input_bg)],
            background=[('readonly', input_bg)],
            foreground=[('readonly', input_text)]
        )
        
        # Scrollable canvas for app grid (no scrollbar)
        canvas_frame = tk.Frame(self.frame, bg=bg_color)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=self.scaler.scale_padding(20), pady=(0, self.scaler.scale_padding(20)))
        
        # Create scrollable canvas
        self.canvas = tk.Canvas(canvas_frame, bg=bg_color, highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_scroll_region(event=None):
            # Update the scroll region
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                # Add padding to ensure we can scroll to the bottom
                self.canvas.configure(scrollregion=(0, 0, bbox[2], bbox[3] + 50))
            # Set scrollable frame width to match canvas for proper grid layout
            if event:
                canvas_width = event.width
                if canvas_width > 0:
                    # Set width to match canvas so grid can use full width
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            else:
                # Initial setup - get canvas width
                self.canvas.update_idletasks()
                canvas_width = self.canvas.winfo_width()
                if canvas_width > 1:  # Only if canvas has been rendered
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        def configure_canvas(event):
            # Update scrollable frame width to match canvas when canvas is resized
            canvas_width = event.width
            if canvas_width > 0:
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            # Update scroll region
            configure_scroll_region()
        
        self.canvas.bind("<Configure>", configure_canvas)
        
        # Configure grid columns - don't set weight, let content determine size
        # We'll configure columns dynamically when apps are loaded
        
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Improved mousewheel scrolling - bind to both canvas and scrollable_frame
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        # Linux mousewheel support with bounds checking
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
        
        # Also bind to frame for better coverage
        self.frame.bind("<MouseWheel>", self._on_mousewheel)
        self.frame.bind("<Button-4>", scroll_up)
        self.frame.bind("<Button-5>", scroll_down)
        
        # Current sort order
        self.current_sort = "A to Z"
        
        # Load and display apps
        self.load_apps()
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling with improved sensitivity"""
        # Windows and Mac
        if event.delta:
            # More sensitive scrolling
            scroll_amount = int(-1 * (event.delta / 40))
            # Check if we can scroll in that direction
            if scroll_amount < 0:  # Scrolling down
                # Check if we're at the bottom
                if self.canvas.yview()[1] < 1.0:
                    self.canvas.yview_scroll(scroll_amount, "units")
            else:  # Scrolling up
                # Check if we're at the top
                if self.canvas.yview()[0] > 0.0:
                    self.canvas.yview_scroll(scroll_amount, "units")
        # Linux (handled by Button-4/5 bindings)
    
    def _init_apps_json(self):
        """Initialize apps.json with empty list"""
        with open(self.apps_json_path, 'w') as f:
            json.dump({"apps": []}, f, indent=2)
    
    def to_relative_path(self, absolute_path):
        """Convert an absolute path to a relative path (relative to data base)"""
        if not absolute_path:
            return ""
        abs_path = Path(absolute_path)
        data_base = get_data_base_path()
        try:
            rel_path = abs_path.relative_to(data_base)
            return str(rel_path)
        except ValueError:
            return str(absolute_path)
    
    def to_absolute_path(self, stored_path):
        """Convert a stored path (relative or absolute) to an absolute path"""
        if not stored_path:
            return ""
        path = Path(stored_path)
        if path.is_absolute():
            if path.exists():
                return str(path)
            path_str = str(path)
            markers = ["/linux-gaming-center/data/", "linux-gaming-center/data/"]
            for marker in markers:
                if marker in path_str:
                    rel_part = path_str.split(marker)[-1]
                    data_base = get_data_base_path()
                    new_path = data_base / rel_part
                    if new_path.exists():
                        return str(new_path)
            return str(path)
        else:
            data_base = get_data_base_path()
            return str(data_base / path)
    
    def load_apps_json(self):
        """Load apps from apps.json"""
        try:
            with open(self.apps_json_path, 'r') as f:
                data = json.load(f)
                return data.get("apps", [])
        except Exception as e:
            print(f"Error loading apps.json: {e}")
            return []
    
    def save_apps_json(self, apps_list):
        """Save apps to apps.json"""
        try:
            with open(self.apps_json_path, 'w') as f:
                json.dump({"apps": apps_list}, f, indent=2)
        except Exception as e:
            print(f"Error saving apps.json: {e}")
            messagebox.showerror("Error", f"Failed to save app: {e}")
    
    def show_add_app_popup(self):
        """Show popup to add a new app"""
        popup = tk.Toplevel(self.parent)
        popup.title("Add New App")
        
        # Scale popup size
        popup_width = self.scaler.scale_dimension(500)
        popup_height = self.scaler.scale_dimension(400)
        popup.resizable(False, False)
        
        # Center on primary monitor
        popup.transient(self.parent)
        popup.grab_set()
        
        # Use the scaler instance we already have
        x, y = self.scaler.center_on_primary_monitor(popup_width, popup_height)
        popup.geometry(f'{popup_width}x{popup_height}+{x}+{y}')
        
        popup.update_idletasks()
        
        # Theme colors
        bg_color = self.theme.get_color("background_secondary", "#1A1A1A")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        input_bg = self.theme.get_color("input_background", "#1A1A1A")
        input_text = self.theme.get_color("input_text", "#FFFFFF")
        
        popup.configure(bg=bg_color)
        
        # Variables
        app_name_var = tk.StringVar()
        app_image_path_var = tk.StringVar()
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            popup,
            text="Add New App",
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=(self.scaler.scale_padding(20), self.scaler.scale_padding(20)))
        
        # Form frame
        form_frame = tk.Frame(popup, bg=bg_color)
        form_frame.pack(padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(10), fill=tk.BOTH, expand=True)
        
        # App name field
        label_font = self.theme.get_font("label", scaler=self.scaler)
        name_label = tk.Label(
            form_frame,
            text="App Name:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        name_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        body_font = self.theme.get_font("body", scaler=self.scaler)
        name_entry = tk.Entry(
            form_frame,
            textvariable=app_name_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1
        )
        name_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)), ipady=self.scaler.scale_padding(5))
        
        # Image selection
        image_label = tk.Label(
            form_frame,
            text="App Image:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        image_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        image_frame = tk.Frame(form_frame, bg=bg_color)
        image_frame.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        image_entry = tk.Entry(
            image_frame,
            textvariable=app_image_path_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1,
            state="readonly"
        )
        image_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=self.scaler.scale_padding(5))
        
        def browse_image():
            file_path = filedialog.askopenfilename(
                parent=popup,
                title="Select App Image",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                app_image_path_var.set(file_path)
        
        browse_button = tk.Button(
            image_frame,
            text="Browse",
            font=body_font,
            command=browse_image,
            bg=text_secondary,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(15),
            pady=self.scaler.scale_padding(5)
        )
        browse_button.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(10), 0))
        
        # Status label
        status_label = tk.Label(
            form_frame,
            text="",
            font=label_font,
            bg=bg_color,
            fg=self.theme.get_color("text_error", "#E74C3C")
        )
        status_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        def save_app():
            app_name = app_name_var.get().strip()
            image_path = app_image_path_var.get().strip()
            
            if not app_name:
                status_label.config(text="Please enter an app name")
                return
            
            if not image_path:
                status_label.config(text="Please select an app image")
                return
            
            # Create app directory structure
            app_safe_name = "".join(c for c in app_name if c.isalnum() or c in (' ', '-', '_')).strip()
            app_safe_name = app_safe_name.replace(' ', '_')
            app_dir = self.apps_base_dir / app_safe_name
            assets_dir = app_dir / "assets"
            run_dir = app_dir / "run"
            
            try:
                # Create directories
                assets_dir.mkdir(parents=True, exist_ok=True)
                run_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy image to assets folder
                image_ext = Path(image_path).suffix
                image_filename = f"app_image{image_ext}"
                dest_image_path = assets_dir / image_filename
                shutil.copy2(image_path, dest_image_path)
                
                # Create .sh file
                sh_filename = f"{app_safe_name}.sh"
                sh_file_path = run_dir / sh_filename
                
                # Create empty .sh file with a comment
                with open(sh_file_path, 'w') as f:
                    f.write(f"#!/bin/bash\n# Run script for {app_name}\n# Add your app launch commands below\n\n")
                
                # Make .sh file executable
                os.chmod(sh_file_path, 0o755)
                
                # Load existing apps
                apps_list = self.load_apps_json()
                
                # Add new app with timestamp - store relative paths for portability
                new_app = {
                    "name": app_name,
                    "image": self.to_relative_path(str(dest_image_path)),
                    "sh_file": self.to_relative_path(str(sh_file_path)),
                    "app_dir": self.to_relative_path(str(app_dir)),
                    "added_date": datetime.now().isoformat()
                }
                apps_list.append(new_app)
                
                # Save apps
                self.save_apps_json(apps_list)
                
                # Close popup and reload apps
                popup.destroy()
                self.load_apps()
                
                messagebox.showinfo("Success", f"App '{app_name}' added successfully!\n\nPlease edit the .sh file at:\n{sh_file_path}\n\nto add your app launch commands.")
                
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}")
                print(f"Error adding app: {e}")
        
        # Save button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        save_button = tk.Button(
            form_frame,
            text="Save",
            font=button_font,
            command=save_app,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(30),
            pady=self.scaler.scale_padding(10)
        )
        save_button.pack(pady=(self.scaler.scale_padding(10), 0))
    
    def sort_apps(self, apps_list, sort_order):
        """Sort apps based on the selected sort order"""
        if sort_order == "A to Z":
            return sorted(apps_list, key=lambda x: x.get("name", "").lower())
        elif sort_order == "Z to A":
            return sorted(apps_list, key=lambda x: x.get("name", "").lower(), reverse=True)
        elif sort_order == "Newest added":
            # Sort by added_date descending (newest first)
            # For apps without added_date, treat as very old
            return sorted(apps_list, key=lambda x: x.get("added_date", "1970-01-01"), reverse=True)
        elif sort_order == "Oldest added":
            # Sort by added_date ascending (oldest first)
            # For apps without added_date, treat as very old
            return sorted(apps_list, key=lambda x: x.get("added_date", "1970-01-01"))
        return apps_list
    
    def load_apps(self):
        """Load and display all apps in a grid"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Load apps from JSON
        apps = self.load_apps_json()
        
        # Sort apps based on current sort selection
        sort_order = self.sort_var.get() if hasattr(self, 'sort_var') else "A to Z"
        apps = self.sort_apps(apps, sort_order)
        
        if not apps:
            # Show empty state
            bg_color = self.theme.get_color("background", "#000000")
            text_color = self.theme.get_color("text_primary", "#FFFFFF")
            text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
            
            empty_label = tk.Label(
                self.scrollable_frame,
                text="No apps added yet.\nClick '+ Add App' to get started.",
                font=self.theme.get_font("body", scaler=self.scaler),
                bg=bg_color,
                fg=text_secondary,
                justify=tk.CENTER
            )
            empty_label.pack(pady=self.scaler.scale_padding(50))
            return
        
        # Display apps in grid
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        # Grid configuration
        items_per_row = 4
        button_width = self.scaler.scale_dimension(350)  # Wider, more rectangular
        button_height = self.scaler.scale_dimension(200)  # Keep height the same
        button_padding = self.scaler.scale_padding(15)
        
        # Configure grid columns for proper layout
        for col in range(items_per_row):
            self.scrollable_frame.grid_columnconfigure(col, weight=0, minsize=button_width + (button_padding * 2))
        
        for i, app in enumerate(apps):
            row = i // items_per_row
            col = i % items_per_row
            
            # Create button frame
            button_frame = tk.Frame(self.scrollable_frame, bg=bg_color)
            button_frame.grid(row=row, column=col, padx=button_padding, pady=button_padding)
            
            # Load and display app image - resolve paths to handle custom locations
            image_path = Path(self.to_absolute_path(app.get("image", "")))
            app_name = app.get("name", "Unknown App")
            sh_file = self.to_absolute_path(app.get("sh_file", ""))
            
            button = None
            if image_path.exists() and PIL_AVAILABLE:
                try:
                    image = Image.open(image_path)
                    image = image.resize((button_width, button_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    button = tk.Button(
                        button_frame,
                        image=photo,
                        command=lambda sf=sh_file, an=app_name: self.run_app(sf, an),
                        bg=menu_bar_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        borderwidth=0,
                        highlightthickness=0,
                        activebackground=self.theme.get_color("background_secondary", "#1A1A1A")
                    )
                    button.image = photo  # Keep reference
                    button.pack()
                    
                    # Add right-click context menu (prevent default button action on right-click)
                    def on_right_click(event):
                        # Stop event propagation
                        event.widget.focus_set()
                        # Capture event coordinates
                        x_root = event.x_root
                        y_root = event.y_root
                        # Create a copy of app data to avoid closure issues
                        app_data_copy = app.copy()
                        # Create a simple event-like object with coordinates
                        class MenuEvent:
                            def __init__(self, x, y):
                                self.x_root = x
                                self.y_root = y
                        menu_event = MenuEvent(x_root, y_root)
                        # Show menu immediately - no delay needed
                        self.show_app_context_menu(menu_event, app_data_copy)
                        return "break"  # Prevent default button action
                    
                    button.bind("<Button-3>", on_right_click)
                except Exception as e:
                    print(f"Error loading app image {image_path}: {e}")
                    # Fallback to text button
                    button = tk.Button(
                        button_frame,
                        text=app_name,
                        command=lambda sf=sh_file, an=app_name: self.run_app(sf, an),
                        bg=menu_bar_color,
                        fg=text_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        width=self.scaler.scale_dimension(20),
                        height=self.scaler.scale_dimension(10),
                        font=self.theme.get_font("body_small", scaler=self.scaler)
                    )
                    button.pack()
                    
                    # Add right-click context menu (prevent default button action on right-click)
                    def on_right_click(event):
                        # Stop event propagation
                        event.widget.focus_set()
                        # Capture event coordinates
                        x_root = event.x_root
                        y_root = event.y_root
                        app_data_copy = app.copy()
                        # Create a simple event-like object with coordinates
                        class MenuEvent:
                            def __init__(self, x, y):
                                self.x_root = x
                                self.y_root = y
                        menu_event = MenuEvent(x_root, y_root)
                        # Show menu immediately - no delay needed
                        self.show_app_context_menu(menu_event, app_data_copy)
                        return "break"
                    
                    button.bind("<Button-3>", on_right_click)
            else:
                # Fallback to text button
                button = tk.Button(
                    button_frame,
                    text=app_name,
                    command=lambda sf=sh_file, an=app_name: self.run_app(sf, an),
                    bg=menu_bar_color,
                    fg=text_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    width=self.scaler.scale_dimension(20),
                    height=self.scaler.scale_dimension(10),
                    font=self.theme.get_font("body_small", scaler=self.scaler)
                )
                button.pack()
                
                # Add right-click context menu (prevent default button action on right-click)
                def on_right_click(event):
                    event.widget.focus_set()  # Set focus to prevent button click
                    app_data_copy = app.copy()
                    self.show_app_context_menu(event, app_data_copy)
                    return "break"
                
                button.bind("<Button-3>", on_right_click)
            
            # App name label below button
            name_label = tk.Label(
                button_frame,
                text=app_name,
                font=self.theme.get_font("body_small", scaler=self.scaler),
                bg=bg_color,
                fg=text_color,
                wraplength=button_width
            )
            name_label.pack(pady=(self.scaler.scale_padding(5), 0))
        
        # Update canvas scroll region after loading apps
        # Force update to ensure all widgets are rendered
        self.scrollable_frame.update_idletasks()
        self.canvas.update_idletasks()
        
        # Get the bounding box of all items in the canvas
        bbox = self.canvas.bbox("all")
        if bbox:
            # Add some padding to ensure we can scroll to the bottom
            self.canvas.configure(scrollregion=(0, 0, bbox[2], bbox[3] + 50))
        else:
            # If no content, set a minimum scroll region
            canvas_width = self.canvas.winfo_width() or 800
            canvas_height = self.canvas.winfo_height() or 600
            self.canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
        
        # Ensure we start at the top
        self.canvas.yview_moveto(0)
    
    def run_app(self, sh_file_path, app_name):
        """Run the app's .sh file and track it as recently used"""
        sh_path = Path(sh_file_path)
        
        if not sh_path.exists():
            messagebox.showerror("Error", f"Script file not found:\n{sh_file_path}")
            return
        
        try:
            # Run the .sh file in the background
            subprocess.Popen(
                ["bash", str(sh_path)],
                cwd=sh_path.parent,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Track as recently used
            self.track_recently_used(sh_file_path, app_name)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run app '{app_name}':\n{str(e)}")
            print(f"Error running app: {e}")
    
    def track_recently_used(self, sh_file_path, app_name):
        """Track an app as recently used"""
        try:
            # Convert to relative path for storage and comparison
            sh_file_relative = self.to_relative_path(sh_file_path)
            
            # Find the app in the apps list to get its full info
            apps = self.load_apps_json()
            app_info = None
            for app in apps:
                # Compare relative paths
                if app.get("sh_file") == sh_file_relative:
                    app_info = app.copy()
                    break
            
            if not app_info:
                # Create minimal app info if not found - use relative paths
                app_info = {
                    "name": app_name,
                    "sh_file": sh_file_relative,
                    "image": ""
                }
            
            # Load recently used apps from user's account directory
            if not self.recently_used_file:
                return  # No username, can't track
            
            if self.recently_used_file.exists():
                with open(self.recently_used_file, 'r') as f:
                    recently_used = json.load(f)
            else:
                recently_used = []
            
            # Remove if already exists (to avoid duplicates) - compare relative paths
            recently_used = [app for app in recently_used if app.get("sh_file") != sh_file_relative]
            
            # Add timestamp
            app_info["last_used"] = datetime.now().isoformat()
            
            # Add to front
            recently_used.insert(0, app_info)
            
            # Keep only last 10
            recently_used = recently_used[:10]
            
            # Save to user's account directory
            with open(self.recently_used_file, 'w') as f:
                json.dump(recently_used, f, indent=2)
                
        except Exception as e:
            print(f"Error tracking recently used app: {e}")
    
    def show_app_context_menu(self, event, app_data):
        """Show context menu for an app"""
        # Create a copy of app_data to avoid closure issues
        app_data_copy = app_data.copy()
        
        menu = Menu(self.parent, tearoff=0)
        menu.configure(
            bg=self.theme.get_color("background_secondary", "#1A1A1A"),
            fg=self.theme.get_color("text_primary", "#FFFFFF"),
            activebackground=self.theme.get_color("primary", "#9D4EDD"),
            activeforeground=self.theme.get_color("text_primary", "#FFFFFF"),
            borderwidth=0,
            font=self.theme.get_font("body_small", scaler=self.scaler)
        )
        
        # Use separate functions to avoid immediate execution
        def edit_app():
            menu.destroy()
            self.show_edit_app_popup(app_data_copy)
        
        def configure_commands():
            menu.destroy()
            self.open_sh_file_for_editing(app_data_copy)
        
        def delete_app():
            menu.destroy()
            self.delete_app(app_data_copy)
        
        menu.add_command(label="Edit app", command=edit_app)
        menu.add_command(label="Configure commands", command=configure_commands)
        menu.add_command(label="Delete app", command=delete_app)
        
        try:
            # Show menu at cursor position with offset to prevent auto-selection
            # Get current mouse position to ensure menu appears correctly
            x = event.x_root
            y = event.y_root
            # Add offset to prevent menu from appearing directly under cursor
            # which can cause the first item to be auto-selected when button is released
            # Offset by several pixels to the right and down
            
            # Use update_idletasks to ensure everything is ready
            self.parent.update_idletasks()
            
            # Show the menu using tk_popup
            # This will keep the menu open until user selects an option or clicks outside
            menu.tk_popup(x + 10, y + 10)
            
            # Add a small delay before allowing any close operations
            # This prevents the menu from closing immediately after opening
            menu_just_opened = {"value": True}
            self.parent.after(100, lambda: menu_just_opened.update({"value": False}))
            
            # Add handler to close menu when clicking outside (only after initial delay)
            def setup_close_handler():
                root = self.parent.winfo_toplevel()
                
                def close_on_outside_click(event):
                    # Don't close if menu was just opened
                    if menu_just_opened.get("value", False):
                        return
                    
                    try:
                        if not menu.winfo_exists():
                            return
                        
                        # Get menu bounds
                        menu_x = menu.winfo_rootx()
                        menu_y = menu.winfo_rooty()
                        menu_w = menu.winfo_width()
                        menu_h = menu.winfo_height()
                        
                        # Get click position
                        click_x = event.x_root
                        click_y = event.y_root
                        
                        # Check if click is outside menu (only for left clicks)
                        if event.num == 1:  # Left click only
                            if (click_x < menu_x or click_x > menu_x + menu_w or
                                click_y < menu_y or click_y > menu_y + menu_h):
                                menu.destroy()
                                try:
                                    root.unbind("<Button-1>")
                                except:
                                    pass
                    except:
                        pass
                
                # Only bind left click, not right click
                root.bind("<Button-1>", close_on_outside_click, add="+")
                
                # Cleanup when menu is destroyed
                def cleanup():
                    try:
                        root.unbind("<Button-1>")
                    except:
                        pass
                
                menu.bind("<Unmap>", lambda e: cleanup())
            
            # Setup close handler after menu is displayed
            self.parent.after(150, setup_close_handler)
            
        except Exception as e:
            print(f"Error showing context menu: {e}")
            try:
                menu.destroy()
            except:
                pass
    
    def show_edit_app_popup(self, app_data):
        """Show popup to edit an app"""
        popup = tk.Toplevel(self.parent)
        popup.title("Edit App")
        
        # Scale popup size
        popup_width = self.scaler.scale_dimension(500)
        popup_height = self.scaler.scale_dimension(400)
        popup.resizable(False, False)
        
        # Center on primary monitor
        popup.transient(self.parent)
        popup.grab_set()
        
        # Use the scaler instance we already have
        x, y = self.scaler.center_on_primary_monitor(popup_width, popup_height)
        popup.geometry(f'{popup_width}x{popup_height}+{x}+{y}')
        
        popup.update_idletasks()
        
        # Theme colors
        bg_color = self.theme.get_color("background_secondary", "#1A1A1A")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        input_bg = self.theme.get_color("input_background", "#1A1A1A")
        input_text = self.theme.get_color("input_text", "#FFFFFF")
        
        popup.configure(bg=bg_color)
        
        # Variables - pre-fill with existing data (resolve paths for display)
        app_name_var = tk.StringVar(value=app_data.get("name", ""))
        app_image_path_var = tk.StringVar(value=self.to_absolute_path(app_data.get("image", "")))
        
        # Store original app data - resolve paths and keep original relative path for comparison
        original_app_dir = Path(self.to_absolute_path(app_data.get("app_dir", "")))
        original_sh_file_relative = app_data.get("sh_file", "")  # Keep the stored (relative) path for matching
        original_sh_file = self.to_absolute_path(original_sh_file_relative)
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            popup,
            text="Edit App",
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=(self.scaler.scale_padding(20), self.scaler.scale_padding(20)))
        
        # Form frame
        form_frame = tk.Frame(popup, bg=bg_color)
        form_frame.pack(padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(10), fill=tk.BOTH, expand=True)
        
        # App name field
        label_font = self.theme.get_font("label", scaler=self.scaler)
        name_label = tk.Label(
            form_frame,
            text="App Name:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        name_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        body_font = self.theme.get_font("body", scaler=self.scaler)
        name_entry = tk.Entry(
            form_frame,
            textvariable=app_name_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1
        )
        name_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)), ipady=self.scaler.scale_padding(5))
        
        # Image selection
        image_label = tk.Label(
            form_frame,
            text="App Image:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        image_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        image_frame = tk.Frame(form_frame, bg=bg_color)
        image_frame.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        image_entry = tk.Entry(
            image_frame,
            textvariable=app_image_path_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1,
            state="readonly"
        )
        image_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=self.scaler.scale_padding(5))
        
        def browse_image():
            file_path = filedialog.askopenfilename(
                parent=popup,
                title="Select App Image",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("All files", "*.*")
                ]
            )
            if file_path:
                app_image_path_var.set(file_path)
        
        browse_button = tk.Button(
            image_frame,
            text="Browse",
            font=body_font,
            command=browse_image,
            bg=text_secondary,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(15),
            pady=self.scaler.scale_padding(5)
        )
        browse_button.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(10), 0))
        
        # Status label
        status_label = tk.Label(
            form_frame,
            text="",
            font=label_font,
            bg=bg_color,
            fg=self.theme.get_color("text_error", "#E74C3C")
        )
        status_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        def save_changes():
            app_name = app_name_var.get().strip()
            image_path = app_image_path_var.get().strip()
            
            if not app_name:
                status_label.config(text="Please enter an app name")
                return
            
            try:
                # Load existing apps
                apps_list = self.load_apps_json()
                
                # Find and update the app - compare with the relative path
                app_found = False
                for app in apps_list:
                    if app.get("sh_file") == original_sh_file_relative:
                        # Update app name
                        app["name"] = app_name
                        
                        # Update image if changed
                        current_image_absolute = self.to_absolute_path(app.get("image", ""))
                        if image_path and image_path != current_image_absolute:
                            # Copy new image to assets folder
                            assets_dir = original_app_dir / "assets"
                            assets_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Delete old image
                            old_image_path = Path(current_image_absolute)
                            if old_image_path.exists():
                                try:
                                    old_image_path.unlink()
                                except:
                                    pass
                            
                            # Copy new image
                            image_ext = Path(image_path).suffix
                            image_filename = f"app_image{image_ext}"
                            dest_image_path = assets_dir / image_filename
                            shutil.copy2(image_path, dest_image_path)
                            # Store as relative path
                            app["image"] = self.to_relative_path(str(dest_image_path))
                        
                        app_found = True
                        break
                
                if not app_found:
                    status_label.config(text="App not found in library")
                    return
                
                # Save apps
                self.save_apps_json(apps_list)
                
                # Close popup and reload apps
                popup.destroy()
                self.load_apps()
                
                messagebox.showinfo("Success", f"App '{app_name}' updated successfully!")
                
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}")
                print(f"Error editing app: {e}")
        
        # Save button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        save_button = tk.Button(
            form_frame,
            text="Save Changes",
            font=button_font,
            command=save_changes,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(30),
            pady=self.scaler.scale_padding(10)
        )
        save_button.pack(pady=(self.scaler.scale_padding(10), 0))
    
    def is_admin(self):
        """Check if current user is an administrator"""
        if not self.username:
            return False
        
        account_dir = get_user_account_dir(self.username)
        account_file = account_dir / "account.json"
        
        if account_file.exists():
            try:
                with open(account_file, 'r') as f:
                    account_data = json.load(f)
                account_type = account_data.get("account_type", "basic")
                return account_type == "administrator"
            except Exception as e:
                print(f"Error checking admin status: {e}")
                return False
        return False
    
    def open_sh_file_for_editing(self, app_data):
        """Open the .sh file in the default text editor"""
        sh_file = self.to_absolute_path(app_data.get("sh_file", ""))
        sh_path = Path(sh_file)
        
        if not sh_path.exists():
            messagebox.showerror("Error", f"Script file not found:\n{sh_file}")
            return
        
        try:
            # Try to open with default editor
            # First try xdg-open (Linux)
            import platform
            if platform.system() == "Linux":
                # Suppress stderr to avoid editor warnings in terminal
                subprocess.Popen(["xdg-open", str(sh_path)], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", str(sh_path)], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            elif platform.system() == "Windows":
                os.startfile(str(sh_path))
            else:
                # Fallback: try common editors
                editors = ["gedit", "nano", "vim", "code", "kate"]
                opened = False
                for editor in editors:
                    try:
                        subprocess.Popen([editor, str(sh_path)], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                        opened = True
                        break
                    except:
                        continue
                if not opened:
                    messagebox.showerror("Error", "Could not find a text editor to open the file.\n\nPlease manually open:\n" + str(sh_path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{str(e)}\n\nPlease manually open:\n{sh_path}")
            print(f"Error opening file: {e}")
    
    def delete_app(self, app_data):
        """Delete an app from the library"""
        app_name = app_data.get("name", "Unknown App")
        # Get the relative path for comparison and resolve absolute for deletion
        sh_file_relative = app_data.get("sh_file", "")
        app_dir = Path(self.to_absolute_path(app_data.get("app_dir", "")))
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Delete App",
            f"Are you sure you want to delete '{app_name}'?\n\nThis will permanently delete:\n- The app directory\n- The app image\n- The app's .sh file\n\nThis action cannot be undone.",
            icon="warning"
        )
        
        if not result:
            return
        
        try:
            # Load apps list
            apps_list = self.load_apps_json()
            
            # Remove from apps list - compare with relative path
            apps_list = [app for app in apps_list if app.get("sh_file") != sh_file_relative]
            
            # Save updated apps list
            self.save_apps_json(apps_list)
            
            # Delete app directory and all contents
            if app_dir.exists() and app_dir.is_dir():
                shutil.rmtree(app_dir)
            
            # Remove from recently used (if exists in user's recently used)
            if self.recently_used_file and self.recently_used_file.exists():
                try:
                    with open(self.recently_used_file, 'r') as f:
                        recently_used = json.load(f)
                    recently_used = [app for app in recently_used if app.get("sh_file") != sh_file_relative]
                    with open(self.recently_used_file, 'w') as f:
                        json.dump(recently_used, f, indent=2)
                except:
                    pass  # Ignore errors with recently used
            
            # Reload apps display
            self.load_apps()
            
            messagebox.showinfo("Success", f"App '{app_name}' deleted successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete app:\n{str(e)}")
            print(f"Error deleting app: {e}")
    
    def show(self):
        """Show the frame"""
        self.frame.pack(fill=tk.BOTH, expand=True)
        # Reload apps when shown
        self.load_apps()
    
    def hide(self):
        """Hide the frame"""
        self.frame.pack_forget()
