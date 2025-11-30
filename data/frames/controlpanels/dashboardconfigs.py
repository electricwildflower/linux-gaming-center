#!/usr/bin/env python3
"""
Linux Gaming Center - Dashboard Configs Panel
"""

import tkinter as tk
from pathlib import Path
import json


class DashboardConfigsPanel:
    def __init__(self, parent, theme, scaler):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        # Use grid to fill parent completely
        self.frame.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Configure frame to fill parent
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Config file for dashboard settings
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from path_helper import get_config_file_path
        self.config_file = get_config_file_path("dashboard_config.json")
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
            text="Dashboard Configs",
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=self.scaler.scale_padding(30))
        
        # Load current settings
        self.load_settings()
        
        # Add Recently Used Sections Order Section
        self.create_recently_used_order_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color, menu_bar_color)
        
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
        """Load dashboard configuration settings"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        else:
            self.settings = {}
        
        # Set defaults if not present
        if "recently_used_order" not in self.settings:
            self.settings["recently_used_order"] = [
                "apps",
                "opensourcegaming",
                "windowssteam"
            ]
    
    def save_settings(self):
        """Save dashboard configuration settings"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving dashboard config: {e}")
    
    def create_recently_used_order_section(self, parent, bg_color, text_color, text_secondary, primary_color, menu_bar_color):
        """Create section for reordering recently used sections"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Recently Used Sections Order",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        description = tk.Label(
            section_frame,
            text="Drag and drop items to reorder the recently used sections on the dashboard. Changes take effect after refreshing the dashboard.",
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w",
            wraplength=self.scaler.scale_dimension(600)
        )
        description.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        # Section names mapping
        self.section_names = {
            "apps": "Recently Used Apps",
            "opensourcegaming": "Recently Used Open Source Games",
            "windowssteam": "Recently Used Windows/Steam Games"
        }
        
        # List container for draggable items
        list_container = tk.Frame(section_frame, bg=bg_color)
        list_container.pack(fill=tk.BOTH, expand=True, pady=(0, self.scaler.scale_padding(20)))
        
        # Create draggable list
        self.create_draggable_list(list_container, bg_color, text_color, menu_bar_color, primary_color)
    
    def create_draggable_list(self, parent, bg_color, text_color, menu_bar_color, primary_color):
        """Create a draggable list of sections"""
        # Container frame for the list
        list_frame = tk.Frame(parent, bg=bg_color, relief=tk.SOLID, borderwidth=1)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=self.scaler.scale_padding(10), pady=self.scaler.scale_padding(10))
        
        # Store list items
        self.list_items = []
        self.drag_start_index = None
        self.drag_item = None
        
        # Create items based on current order
        current_order = self.settings.get("recently_used_order", ["apps", "opensourcegaming", "windowssteam"])
        
        for section_key in current_order:
            if section_key in self.section_names:
                self.add_list_item(list_frame, section_key, bg_color, text_color, menu_bar_color, primary_color)
    
    def add_list_item(self, parent, section_key, bg_color, text_color, menu_bar_color, primary_color):
        """Add a draggable item to the list"""
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        item_frame = tk.Frame(parent, bg=menu_bar_color, relief=tk.RAISED, borderwidth=1)
        item_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(5), pady=self.scaler.scale_padding(3))
        
        # Drag handle (left side)
        handle_label = tk.Label(
            item_frame,
            text="☰",
            font=body_font,
            bg=menu_bar_color,
            fg=text_color,
            cursor="hand2",
            width=3
        )
        handle_label.pack(side=tk.LEFT, padx=self.scaler.scale_padding(5))
        
        # Section name
        name_label = tk.Label(
            item_frame,
            text=self.section_names[section_key],
            font=body_font,
            bg=menu_bar_color,
            fg=text_color,
            anchor="w"
        )
        name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=self.scaler.scale_padding(10))
        
        # Store section key in the frame
        item_frame.section_key = section_key
        
        # Bind mouse events for dragging
        def on_button_press(event):
            self.drag_start_index = None
            self.drag_item = item_frame
            # Find the index of this item
            for i, item in enumerate(self.list_items):
                if item == item_frame:
                    self.drag_start_index = i
                    break
            # Visual feedback - highlight the item being dragged
            item_frame.config(bg=primary_color)
            handle_label.config(bg=primary_color)
            name_label.config(bg=primary_color)
            # Change cursor
            handle_label.config(cursor="hand2")
            name_label.config(cursor="hand2")
            # Store initial y position
            item_frame.drag_start_y = event.y_root
        
        def on_button_release(event):
            if self.drag_item and self.drag_start_index is not None and self.drag_item == item_frame:
                # Find drop position based on mouse position
                drop_y = event.y_root
                drop_index = None
                
                # Check each item to find where to drop
                for i, item in enumerate(self.list_items):
                    if item == item_frame:
                        continue
                    item_y = item.winfo_rooty()
                    item_height = item.winfo_height()
                    item_center = item_y + item_height / 2
                    
                    if drop_y < item_center:
                        drop_index = i
                        break
                
                if drop_index is None:
                    drop_index = len(self.list_items)
                
                # Only move if position changed
                if drop_index != self.drag_start_index:
                    # Remove from old position
                    self.list_items.pop(self.drag_start_index)
                    # Insert at new position (adjust if needed)
                    if drop_index > self.drag_start_index:
                        drop_index -= 1
                    self.list_items.insert(drop_index, item_frame)
                    
                    # Reorder in parent
                    for item in self.list_items:
                        item.pack_forget()
                    for item in self.list_items:
                        item.pack(fill=tk.X, padx=self.scaler.scale_padding(5), pady=self.scaler.scale_padding(3))
                    
                    # Update settings
                    self.update_order_from_list()
            
            # Reset visual feedback
            if self.drag_item == item_frame:
                item_frame.config(bg=menu_bar_color)
                handle_label.config(bg=menu_bar_color)
                name_label.config(bg=menu_bar_color)
            
            self.drag_item = None
            self.drag_start_index = None
        
        def on_motion(event):
            if self.drag_item and self.drag_start_index is not None and self.drag_item == item_frame:
                # Visual feedback - keep highlighted
                item_frame.config(bg=primary_color)
                handle_label.config(bg=primary_color)
                name_label.config(bg=primary_color)
        
        def on_leave(event):
            # Only reset if not currently dragging this item
            if self.drag_item != item_frame:
                item_frame.config(bg=menu_bar_color)
                handle_label.config(bg=menu_bar_color)
                name_label.config(bg=menu_bar_color)
        
        # Bind events to both handle and name label
        handle_label.bind("<Button-1>", on_button_press)
        handle_label.bind("<B1-Motion>", on_motion)
        handle_label.bind("<ButtonRelease-1>", on_button_release)
        handle_label.bind("<Leave>", on_leave)
        
        name_label.bind("<Button-1>", on_button_press)
        name_label.bind("<B1-Motion>", on_motion)
        name_label.bind("<ButtonRelease-1>", on_button_release)
        name_label.bind("<Leave>", on_leave)
        
        item_frame.bind("<Button-1>", on_button_press)
        item_frame.bind("<B1-Motion>", on_motion)
        item_frame.bind("<ButtonRelease-1>", on_button_release)
        item_frame.bind("<Leave>", on_leave)
        
        # Add to list
        self.list_items.append(item_frame)
    
    def update_order_from_list(self):
        """Update settings with current list order"""
        new_order = []
        for item in self.list_items:
            if hasattr(item, 'section_key'):
                new_order.append(item.section_key)
        
        self.settings["recently_used_order"] = new_order
        self.save_settings()
    
    def destroy(self):
        """Destroy the panel"""
        self.frame.destroy()
