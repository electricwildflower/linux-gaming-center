#!/usr/bin/env python3
"""
Linux Gaming Center - Dashboard Screen
"""

import tkinter as tk
from tkinter import Menu
from pathlib import Path
import json
import os
from path_helper import get_user_account_dir, get_config_file_path, get_data_base_path

# Try to import PIL for image handling (optional)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class DashboardScreen:
    def __init__(self, parent, on_logout, on_exit, theme, scaler):
        self.parent = parent
        self.on_logout = on_logout
        self.on_exit = on_exit
        self.theme = theme
        self.scaler = scaler
        self.username = None
        self.previous_username = None  # Track previous username to detect user change
        self.profile_image_path = None
        self.menu_bar_frame = None
        self.profile_menu = None
        self.admin_menu = None
        self.admin_button = None
        self.power_menu = None
        
        bg_color = self.theme.get_color("background", "#1A1A2E")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Menu bar frame (larger, scaled)
        menu_bar_color = self.theme.get_color("menu_bar", "#34495E")
        menu_bar_height = self.scaler.scale_dimension(70)
        self.menu_bar_frame = tk.Frame(self.frame, bg=menu_bar_color, height=menu_bar_height)
        self.menu_bar_frame.pack(fill=tk.X, side=tk.TOP)
        self.menu_bar_frame.pack_propagate(False)
        
        # Home button on the left (will be created, initially hidden on dashboard)
        self.home_button = None
        
        # Right side container for profile and power button (stored for reuse)
        self.right_container = tk.Frame(self.menu_bar_frame, bg=menu_bar_color)
        self.right_container.pack(side=tk.RIGHT, padx=self.scaler.scale_padding(15), pady=self.scaler.scale_padding(15))
        
        # Power button (will be created)
        self.power_button = None
        
        # Store button (will be created)
        self.store_button = None
        
        # Profile section (will be created when username is set)
        self.profile_container = None
        
        # Create scrollable content area
        # Create a canvas for scrolling (no visible scrollbar)
        self.scroll_canvas = tk.Canvas(self.frame, bg=bg_color, highlightthickness=0)
        self.scroll_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Content area for library buttons and frames (inside canvas)
        self.content_area = tk.Frame(self.scroll_canvas, bg=bg_color)
        self.scroll_canvas_window = self.scroll_canvas.create_window((0, 0), window=self.content_area, anchor="nw")
        
        # Configure scroll region
        def configure_scroll_region(event=None):
            self.scroll_canvas.update_idletasks()
            # Always set canvas window to full canvas size
            canvas_width = event.width if event else self.scroll_canvas.winfo_width()
            canvas_height = event.height if event else self.scroll_canvas.winfo_height()
            if canvas_width > 1 and canvas_height > 1:
                self.scroll_canvas.itemconfig(self.scroll_canvas_window, width=canvas_width, height=canvas_height)
            
            # For scroll region, check if we have a frame that needs scrolling or should fill
            bbox = self.scroll_canvas.bbox("all")
            if bbox:
                # If control panel is active, use full canvas size, otherwise use content bbox
                if hasattr(self, 'current_frame') and self.current_frame and hasattr(self.current_frame, '__class__'):
                    frame_class_name = self.current_frame.__class__.__name__
                    if frame_class_name == "ControlPanelFrame":
                        # Control panel: use full canvas size (no scrolling)
                        self.scroll_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
                    else:
                        # Other frames: use content bbox (allow scrolling)
                        self.scroll_canvas.configure(scrollregion=bbox)
                else:
                    # Default: use content bbox
                    self.scroll_canvas.configure(scrollregion=bbox)
        
        self.content_area.bind("<Configure>", configure_scroll_region)
        self.scroll_canvas.bind("<Configure>", configure_scroll_region)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            # Windows and Mac
            if event.delta:
                scroll_amount = int(-1 * (event.delta / 40))
                self.scroll_canvas.yview_scroll(scroll_amount, "units")
            return "break"
        
        # Linux mousewheel support
        def scroll_up(e):
            if self.scroll_canvas.yview()[0] > 0.0:
                self.scroll_canvas.yview_scroll(-3, "units")
        
        def scroll_down(e):
            if self.scroll_canvas.yview()[1] < 1.0:
                self.scroll_canvas.yview_scroll(3, "units")
        
        # Bind mousewheel events
        self.scroll_canvas.bind("<MouseWheel>", on_mousewheel)
        self.content_area.bind("<MouseWheel>", on_mousewheel)
        self.scroll_canvas.bind("<Button-4>", scroll_up)
        self.scroll_canvas.bind("<Button-5>", scroll_down)
        self.content_area.bind("<Button-4>", scroll_up)
        self.content_area.bind("<Button-5>", scroll_down)
        
        # Arrow key scrolling
        def on_arrow_key(event):
            if event.keysym == "Up":
                if self.scroll_canvas.yview()[0] > 0.0:
                    self.scroll_canvas.yview_scroll(-3, "units")
            elif event.keysym == "Down":
                if self.scroll_canvas.yview()[1] < 1.0:
                    self.scroll_canvas.yview_scroll(3, "units")
            elif event.keysym == "Page_Up":
                self.scroll_canvas.yview_scroll(-1, "page")
            elif event.keysym == "Page_Down":
                self.scroll_canvas.yview_scroll(1, "page")
            elif event.keysym == "Home":
                self.scroll_canvas.yview_moveto(0)
            elif event.keysym == "End":
                self.scroll_canvas.yview_moveto(1)
            return "break"
        
        # Bind arrow keys to the frame and canvas
        self.frame.bind("<KeyPress>", on_arrow_key)
        self.scroll_canvas.bind("<KeyPress>", on_arrow_key)
        self.content_area.bind("<KeyPress>", on_arrow_key)
        
        # Make sure the frame can receive focus for keyboard events
        self.frame.focus_set()
        self.scroll_canvas.focus_set()
        
        # Store reference to on_arrow_key for use in show/hide methods
        self.on_arrow_key = on_arrow_key
        
        # Library buttons container (initially visible)
        self.library_buttons_frame = tk.Frame(self.content_area, bg=bg_color)
        self.library_buttons_frame.pack(pady=self.scaler.scale_padding(30))
        
        # Create recently used sections in configured order
        self.create_recently_used_sections_in_order()
        
        # Frame container (where frame content will be displayed, initially hidden)
        self.frame_container = tk.Frame(self.content_area, bg=bg_color)
        # Don't pack initially - will be shown when a frame is loaded
        
        # Store frame container padding for reuse
        self.frame_padding = self.scaler.scale_padding(20)
        
        # Current frame instance
        self.current_frame = None
        
        # Create library buttons
        self.create_library_buttons()
    
    def create_home_button(self):
        """Create home button on the left side of menu bar"""
        if self.home_button:
            return  # Already created
        
        menu_bar_color = self.theme.get_color("menu_bar", "#34495E")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        
        # Get app root and load home icon
        from theme_manager import get_app_root
        app_root = get_app_root()
        home_image_path = app_root / "data" / "themes" / "cosmic-twilight" / "images" / "home.png"
        
        if home_image_path.exists() and PIL_AVAILABLE:
            try:
                image = Image.open(home_image_path)
                # Resize to fit menu bar (larger, scaled)
                icon_size = self.scaler.scale_dimension(40)
                image = image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.home_button = tk.Button(
                    self.menu_bar_frame,
                    image=photo,
                    command=self.go_home,
                    bg=menu_bar_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=0,
                    activebackground=self.theme.get_color("background_secondary", "#1A1A1A")
                )
                self.home_button.image = photo  # Keep reference
                # Don't pack initially - will be shown when needed
            except Exception as e:
                print(f"Error loading home icon: {e}")
                # Fallback to text button
                home_font = self.scaler.get_font("Arial", 14)
                self.home_button = tk.Button(
                    self.menu_bar_frame,
                    text="Home",
                    command=self.go_home,
                    bg=menu_bar_color,
                    fg=text_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=0,
                    font=home_font
                )
        else:
            # Fallback to text button if image not available
            home_font = self.scaler.get_font("Arial", 14)
            self.home_button = tk.Button(
                self.menu_bar_frame,
                text="Home",
                command=self.go_home,
                bg=menu_bar_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                borderwidth=0,
                highlightthickness=0,
                font=home_font
            )
    
    def show_home_button(self):
        """Show the home button"""
        if self.home_button:
            self.home_button.pack(side=tk.LEFT, padx=self.scaler.scale_padding(20), pady=self.scaler.scale_padding(15))
    
    def hide_home_button(self):
        """Hide the home button"""
        if self.home_button:
            self.home_button.pack_forget()
    
    def create_profile_section(self):
        """Create profile image and name dropdown on the right side"""
        if not self.username:
            return
        
        menu_bar_color = self.theme.get_color("menu_bar", "#34495E")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        button_small_font = self.theme.get_font("button_small", scaler=self.scaler)
        
        # Remove existing profile container if it exists
        if self.profile_container:
            self.profile_container.destroy()
        
        # Profile container
        self.profile_container = tk.Frame(self.right_container, bg=menu_bar_color)
        self.profile_container.pack(side=tk.LEFT, padx=(0, 10))
        
        # Profile image (larger, for menu bar, scaled)
        profile_image_label = None
        if self.profile_image_path and os.path.exists(self.profile_image_path) and PIL_AVAILABLE:
            try:
                image = Image.open(self.profile_image_path)
                # Resize to larger size for menu bar (scaled)
                profile_icon_size = self.scaler.scale_dimension(40)
                image = image.resize((profile_icon_size, profile_icon_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                profile_image_label = tk.Label(
                    self.profile_container,
                    image=photo,
                    bg=menu_bar_color,
                    cursor="hand2"
                )
                profile_image_label.image = photo  # Keep reference
                profile_image_label.bind("<Button-1>", lambda e: self.show_profile_menu())
                profile_image_label.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(8)))
            except Exception as e:
                print(f"Error loading profile image for menu: {e}")
        
        # Profile name button (acts as dropdown trigger)
        profile_name_button = tk.Button(
            self.profile_container,
            text=self.username,
            font=button_small_font,
            bg=menu_bar_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            activebackground=self.theme.get_color("background_secondary", "#1A1A1A"),
            command=self.show_profile_menu
        )
        profile_name_button.pack(side=tk.LEFT)
        
        # Create profile dropdown menu
        self.profile_menu = Menu(
            self.parent,
            tearoff=0,
            bg=self.theme.get_color("background_secondary", "#1A1A1A"),
            fg=text_color,
            activebackground=self.theme.get_color("primary", "#9D4EDD"),
            activeforeground=text_color,
            borderwidth=0,
            relief=tk.FLAT
        )
        self.profile_menu.add_command(label="Account settings", command=self.account_settings)
        
        # Create store button
        self.create_store_button()
    
    def create_store_button(self):
        """Create the store button in the menu bar"""
        menu_bar_color = self.theme.get_color("menu_bar", "#34495E")
        
        # Remove existing store button if it exists
        if self.store_button:
            self.store_button.destroy()
        
        # Store button container
        self.store_button = tk.Frame(self.right_container, bg=menu_bar_color)
        self.store_button.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(15)))
        
        # Try to load store icon
        store_icon_size = self.scaler.scale_dimension(32)
        store_icon_loaded = False
        
        from theme_manager import get_app_root
        app_root = get_app_root()
        store_icon_path = app_root / "data" / "themes" / "cosmic-twilight" / "images" / "appstore.png"
        
        if store_icon_path.exists() and PIL_AVAILABLE:
            try:
                image = Image.open(store_icon_path)
                image = image.resize((store_icon_size, store_icon_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                store_icon_label = tk.Label(
                    self.store_button,
                    image=photo,
                    bg=menu_bar_color,
                    cursor="hand2"
                )
                store_icon_label.image = photo  # Keep reference
                store_icon_label.bind("<Button-1>", lambda e: self.open_store())
                store_icon_label.pack(side=tk.LEFT)
                store_icon_loaded = True
            except Exception as e:
                print(f"Error loading store icon: {e}")
        
        # Fallback to text button if icon not loaded
        if not store_icon_loaded:
            text_color = self.theme.get_color("text_primary", "#FFFFFF")
            button_small_font = self.theme.get_font("button_small", scaler=self.scaler)
            store_text_btn = tk.Button(
                self.store_button,
                text="Store",
                font=button_small_font,
                bg=menu_bar_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                borderwidth=0,
                command=self.open_store
            )
            store_text_btn.pack(side=tk.LEFT)
    
    def open_store(self):
        """Open the store frame"""
        # Show home button (we're leaving dashboard)
        self.create_home_button()
        self.show_home_button()
        
        # Hide library buttons
        self.library_buttons_frame.pack_forget()
        
        # Hide recently used apps section
        if hasattr(self, 'recently_used_container'):
            self.recently_used_container.pack_forget()
        
        # Hide recently used open source games section
        if hasattr(self, 'recently_used_osg_container'):
            self.recently_used_osg_container.pack_forget()
        
        # Hide recently used Windows/Steam games section
        if hasattr(self, 'recently_used_ws_container'):
            self.recently_used_ws_container.pack_forget()
        
        # Hide current frame if exists
        if self.current_frame:
            self.current_frame.hide()
            self.current_frame = None
        
        # Clear the frame container
        for widget in self.frame_container.winfo_children():
            widget.destroy()
        
        # Show frame container
        self.frame_container.pack(fill=tk.BOTH, expand=True, padx=self.frame_padding, pady=self.frame_padding)
        
        try:
            # Import and create store frame
            from theme_manager import get_app_root
            import sys
            app_root = get_app_root()
            frames_dir = app_root / "data" / "frames"
            if str(frames_dir) not in sys.path:
                sys.path.insert(0, str(frames_dir))
            
            from store import StoreFrame
            
            self.current_frame = StoreFrame(
                self.frame_container,
                self.theme,
                self.scaler,
                self.username
            )
            
        except Exception as e:
            print(f"Error loading store: {e}")
            import traceback
            traceback.print_exc()
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load Store:\n{str(e)}")
    
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
    
    def create_admin_button(self):
        """Create Admin button with dropdown menu (only for admin users)"""
        if not self.is_admin():
            # Remove admin button if it exists and user is not admin
            if self.admin_button:
                self.admin_button.destroy()
                self.admin_button = None
                self.admin_menu = None
            return
        
        menu_bar_color = self.theme.get_color("menu_bar", "#34495E")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        button_small_font = self.theme.get_font("button_small", scaler=self.scaler)
        
        # Remove existing admin button if it exists
        if self.admin_button:
            self.admin_button.destroy()
        
        # Admin button
        self.admin_button = tk.Button(
            self.right_container,
            text="Admin",
            font=button_small_font,
            bg=menu_bar_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            activebackground=self.theme.get_color("background_secondary", "#1A1A1A"),
            command=self.show_admin_menu
        )
        # Pack between profile and power button (before power button)
        self.admin_button.pack(side=tk.RIGHT, padx=(0, self.scaler.scale_padding(10)))
        
        # Create admin dropdown menu
        menu_font = self.scaler.get_font("Arial", 12)
        self.admin_menu = Menu(
            self.parent,
            tearoff=0,
            bg=self.theme.get_color("background_secondary", "#1A1A1A"),
            fg=text_color,
            activebackground=self.theme.get_color("primary", "#9D4EDD"),
            activeforeground=text_color,
            borderwidth=0,
            relief=tk.FLAT,
            font=menu_font
        )
        self.admin_menu.add_command(label="Control Panel", command=self.open_control_panel)
    
    def show_admin_menu(self):
        """Show admin dropdown menu"""
        if self.admin_menu and self.admin_button:
            try:
                x = self.admin_button.winfo_rootx()
                y = self.admin_button.winfo_rooty() + self.admin_button.winfo_height()
                self.admin_menu.tk_popup(x, y)
            except Exception as e:
                print(f"Error showing admin menu: {e}")
    
    def open_control_panel(self):
        """Open the Control Panel frame"""
        # Hide library buttons and recently used sections
        self.library_buttons_frame.pack_forget()
        if hasattr(self, 'recently_used_container'):
            self.recently_used_container.pack_forget()
        if hasattr(self, 'recently_used_osg_container'):
            self.recently_used_osg_container.pack_forget()
        if hasattr(self, 'recently_used_ws_container'):
            self.recently_used_ws_container.pack_forget()
        
        # Show home button
        self.create_home_button()
        if self.home_button:
            self.home_button.pack(side=tk.LEFT, padx=self.scaler.scale_padding(15), pady=self.scaler.scale_padding(15))
        
        # Load control panel frame
        try:
            # Hide current frame if exists
            if self.current_frame:
                self.current_frame.hide()
            
            # Clear frame container to remove any lingering widgets
            for widget in self.frame_container.winfo_children():
                widget.destroy()
            
            # Add frames directory to path for imports
            import sys
            from theme_manager import get_app_root
            app_root = get_app_root()
            frames_dir = app_root / "data" / "frames"
            if str(frames_dir) not in sys.path:
                sys.path.insert(0, str(frames_dir))
            
            # Import and create control panel frame
            from controlpanel import ControlPanelFrame
            self.current_frame = ControlPanelFrame(self.frame_container, self.theme, self.scaler)
            self.current_frame.show()
            
            # Show frame container (no padding for control panel to fill entire window)
            self.frame_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
            
            # Force canvas window to fill full canvas height/width for control panel
            def update_canvas_for_control_panel():
                self.scroll_canvas.update_idletasks()
                canvas_width = self.scroll_canvas.winfo_width()
                canvas_height = self.scroll_canvas.winfo_height()
                if canvas_width > 1 and canvas_height > 1:
                    # Set canvas window to full canvas size
                    self.scroll_canvas.itemconfig(self.scroll_canvas_window, width=canvas_width, height=canvas_height)
                    # Set scroll region to match (no scrolling needed for control panel)
                    self.scroll_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
            
            # Update immediately and after a short delay
            update_canvas_for_control_panel()
            self.parent.after(100, update_canvas_for_control_panel)
            self.parent.after(300, update_canvas_for_control_panel)
        except Exception as e:
            print(f"Error loading control panel: {e}")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load Control Panel:\n{str(e)}")
    
    def create_power_button(self):
        """Create power button with dropdown menu"""
        menu_bar_color = self.theme.get_color("menu_bar", "#34495E")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        
        # Remove existing power button if it exists
        if self.power_button:
            self.power_button.destroy()
        
        # Get app root and load power icon
        from theme_manager import get_app_root
        app_root = get_app_root()
        power_image_path = app_root / "data" / "themes" / "cosmic-twilight" / "images" / "power.png"
        
        # Power button
        if power_image_path.exists() and PIL_AVAILABLE:
            try:
                image = Image.open(power_image_path)
                # Resize to fit menu bar (larger, scaled)
                icon_size = self.scaler.scale_dimension(40)
                image = image.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.power_button = tk.Button(
                    self.right_container,
                    image=photo,
                    command=self.show_power_menu,
                    bg=menu_bar_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=0,
                    activebackground=self.theme.get_color("background_secondary", "#1A1A1A")
                )
                self.power_button.image = photo  # Keep reference
                self.power_button.pack(side=tk.RIGHT)
            except Exception as e:
                print(f"Error loading power icon: {e}")
                # Fallback to text button
                power_font = self.scaler.get_font("Arial", 18)
                self.power_button = tk.Button(
                    self.right_container,
                    text="⚡",
                    font=power_font,
                    bg=menu_bar_color,
                    fg=text_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=0,
                    activebackground=self.theme.get_color("background_secondary", "#1A1A1A"),
                    command=self.show_power_menu
                )
                self.power_button.pack(side=tk.RIGHT)
        else:
            # Fallback to text button if image not available
            power_font = self.scaler.get_font("Arial", 18)
            self.power_button = tk.Button(
                self.right_container,
                text="⚡",
                font=power_font,
                bg=menu_bar_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                borderwidth=0,
                highlightthickness=0,
                activebackground=self.theme.get_color("background_secondary", "#1A1A1A"),
                command=self.show_power_menu
            )
            self.power_button.pack(side=tk.RIGHT)
        
        # Create power dropdown menu
        menu_font = self.scaler.get_font("Arial", 12)
        self.power_menu = Menu(
            self.parent,
            tearoff=0,
            bg=self.theme.get_color("background_secondary", "#1A1A1A"),
            fg=text_color,
            activebackground=self.theme.get_color("primary", "#9D4EDD"),
            activeforeground=text_color,
            borderwidth=0,
            relief=tk.FLAT,
            font=menu_font
        )
        self.power_menu.add_command(label="Logout", command=self.logout)
        self.power_menu.add_separator()
        self.power_menu.add_command(label="Exit app", command=self.exit_app)
    
    def show_profile_menu(self):
        """Show profile dropdown menu"""
        if self.profile_menu and self.profile_container:
            try:
                # Get position of profile container
                x = self.profile_container.winfo_rootx()
                y = self.profile_container.winfo_rooty() + self.profile_container.winfo_height()
                self.profile_menu.tk_popup(x, y)
            except Exception as e:
                print(f"Error showing profile menu: {e}")
    
    def show_power_menu(self):
        """Show power dropdown menu"""
        if self.power_menu and self.power_button:
            try:
                x = self.power_button.winfo_rootx()
                y = self.power_button.winfo_rooty() + self.power_button.winfo_height()
                self.power_menu.tk_popup(x, y)
            except Exception as e:
                print(f"Error showing power menu: {e}")
    
    def create_library_buttons(self):
        """Create library buttons in a grid row"""
        from theme_manager import get_app_root
        app_root = get_app_root()
        images_dir = app_root / "data" / "themes" / "cosmic-twilight" / "images"
        
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        
        # Library button configurations
        libraries = [
            {
                "name": "Apps",
                "image": "apps.jpg",
                "frame": "apps"
            },
            {
                "name": "Emulators",
                "image": "emulators.jpg",
                "frame": "emulators"
            },
            {
                "name": "Open Source Gaming",
                "image": "opensourcegaming.jpg",
                "frame": "opensourcegaming"
            },
            {
                "name": "Windows/Steam",
                "image": "windowssteam.jpg",
                "frame": "windowssteam"
            }
        ]
        
        for i, lib in enumerate(libraries):
            image_path = images_dir / lib["image"]
            
            # Create button frame
            button_frame = tk.Frame(self.library_buttons_frame, bg=menu_bar_color)
            button_frame.grid(row=0, column=i, padx=15, pady=10)
            
            # Load and display image (larger buttons)
            button = None
            if image_path.exists() and PIL_AVAILABLE:
                try:
                    image = Image.open(image_path)
                    # Resize to larger size (250x200 - wider)
                    image = image.resize((350, 200), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    button = tk.Button(
                        button_frame,
                        image=photo,
                        command=lambda f=lib["frame"]: self.load_frame(f),
                        bg=menu_bar_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        borderwidth=0,
                        highlightthickness=0,
                        activebackground=self.theme.get_color("background_secondary", "#1A1A1A")
                    )
                    button.image = photo  # Keep reference
                    button.pack()
                except Exception as e:
                    print(f"Error loading {lib['name']} image: {e}")
                    # Fallback to text button
                    button_font = self.theme.get_font("button_small", scaler=self.scaler)
                    button = tk.Button(
                        button_frame,
                        text=lib["name"],
                        command=lambda f=lib["frame"]: self.load_frame(f),
                        bg=menu_bar_color,
                        fg=text_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        borderwidth=0,
                        highlightthickness=0,
                        font=button_font,
                        padx=self.scaler.scale_padding(20),
                        pady=self.scaler.scale_padding(10)
                    )
                    button.pack()
            else:
                # Fallback to text button
                button_font = self.theme.get_font("button_small", scaler=self.scaler)
                button = tk.Button(
                    button_frame,
                    text=lib["name"],
                    command=lambda f=lib["frame"]: self.load_frame(f),
                    bg=menu_bar_color,
                    fg=text_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    borderwidth=0,
                    highlightthickness=0,
                    font=button_font,
                    padx=self.scaler.scale_padding(20),
                    pady=self.scaler.scale_padding(10)
                )
                button.pack()
    
    def create_recently_used_sections_in_order(self):
        """Create recently used sections in the configured order"""
        # Load order from config
        config_file = get_config_file_path("dashboard_config.json")
        order = ["apps", "opensourcegaming", "windowssteam"]  # Default order
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    order = config.get("recently_used_order", order)
            except:
                pass
        
        # Create sections in the specified order
        for section_key in order:
            if section_key == "apps":
                self.create_recently_used_section()
            elif section_key == "opensourcegaming":
                self.create_recently_used_opensourcegaming_section()
            elif section_key == "windowssteam":
                self.create_recently_used_windowssteam_section()
    
    def create_recently_used_section(self):
        """Create the Recently Used Apps section"""
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        
        # Section container
        recently_used_container = tk.Frame(self.content_area, bg=bg_color)
        recently_used_container.pack(fill=tk.X, padx=self.scaler.scale_padding(20), pady=(self.scaler.scale_padding(20), 0))
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            recently_used_container,
            text="Recently Used Apps",
            font=heading_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)))
        
        # Scrollable frame with left/right buttons
        scroll_container = tk.Frame(recently_used_container, bg=bg_color)
        scroll_container.pack(fill=tk.X)
        
        # Left scroll button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        left_button = tk.Button(
            scroll_container,
            text="◀",
            font=button_font,
            command=self.scroll_recently_used_left,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            width=self.scaler.scale_dimension(3),
            height=self.scaler.scale_dimension(2)
        )
        left_button.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(10)))
        
        # Canvas for horizontal scrolling
        self.recently_used_canvas = tk.Canvas(
            scroll_container,
            bg=bg_color,
            highlightthickness=0,
            height=self.scaler.scale_dimension(180)
        )
        self.recently_used_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollable frame inside canvas
        self.recently_used_frame = tk.Frame(self.recently_used_canvas, bg=bg_color)
        self.recently_used_canvas_window = self.recently_used_canvas.create_window(
            (0, 0), window=self.recently_used_frame, anchor="nw"
        )
        
        # Right scroll button
        right_button = tk.Button(
            scroll_container,
            text="▶",
            font=button_font,
            command=self.scroll_recently_used_right,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            width=self.scaler.scale_dimension(3),
            height=self.scaler.scale_dimension(2)
        )
        right_button.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(10), 0))
        
        # Configure canvas scroll region
        def configure_recent_canvas(event=None):
            self.recently_used_canvas.update_idletasks()
            bbox = self.recently_used_canvas.bbox("all")
            if bbox:
                # Set scrollregion for horizontal scrolling
                self.recently_used_canvas.configure(scrollregion=bbox)
            # Don't constrain width - let content determine width for horizontal scrolling
            # The canvas window should match content width, not canvas width
        
        self.recently_used_frame.bind("<Configure>", configure_recent_canvas)
        self.recently_used_canvas.bind("<Configure>", configure_recent_canvas)
        
        # Store reference
        self.recently_used_container = recently_used_container
    
    def scroll_recently_used_left(self):
        """Scroll recently used apps left"""
        self.recently_used_canvas.xview_scroll(-3, "units")
    
    def scroll_recently_used_right(self):
        """Scroll recently used apps right"""
        self.recently_used_canvas.xview_scroll(3, "units")
    
    def scroll_recently_used_osg_left(self):
        """Scroll recently used open source games left"""
        self.recently_used_osg_canvas.xview_scroll(-3, "units")
    
    def scroll_recently_used_osg_right(self):
        """Scroll recently used open source games right"""
        self.recently_used_osg_canvas.xview_scroll(3, "units")
    
    def create_recently_used_opensourcegaming_section(self):
        """Create the Recently Used Open Source Games section"""
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        
        # Section container
        recently_used_osg_container = tk.Frame(self.content_area, bg=bg_color)
        recently_used_osg_container.pack(fill=tk.X, padx=self.scaler.scale_padding(20), pady=(self.scaler.scale_padding(20), 0))
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            recently_used_osg_container,
            text="Recently Used Open Source Games",
            font=heading_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)))
        
        # Scrollable frame with left/right buttons
        scroll_container = tk.Frame(recently_used_osg_container, bg=bg_color)
        scroll_container.pack(fill=tk.X)
        
        # Left scroll button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        left_button = tk.Button(
            scroll_container,
            text="◀",
            font=button_font,
            command=self.scroll_recently_used_osg_left,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            width=self.scaler.scale_dimension(3),
            height=self.scaler.scale_dimension(2)
        )
        left_button.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(10)))
        
        # Canvas for horizontal scrolling
        self.recently_used_osg_canvas = tk.Canvas(
            scroll_container,
            bg=bg_color,
            highlightthickness=0,
            height=self.scaler.scale_dimension(180)
        )
        self.recently_used_osg_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollable frame inside canvas
        self.recently_used_osg_frame = tk.Frame(self.recently_used_osg_canvas, bg=bg_color)
        self.recently_used_osg_canvas_window = self.recently_used_osg_canvas.create_window(
            (0, 0), window=self.recently_used_osg_frame, anchor="nw"
        )
        
        # Right scroll button
        right_button = tk.Button(
            scroll_container,
            text="▶",
            font=button_font,
            command=self.scroll_recently_used_osg_right,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            width=self.scaler.scale_dimension(3),
            height=self.scaler.scale_dimension(2)
        )
        right_button.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(10), 0))
        
        # Configure canvas scroll region
        def configure_recent_osg_canvas(event=None):
            self.recently_used_osg_canvas.update_idletasks()
            bbox = self.recently_used_osg_canvas.bbox("all")
            if bbox:
                # Set scrollregion for horizontal scrolling
                self.recently_used_osg_canvas.configure(scrollregion=bbox)
        
        self.recently_used_osg_frame.bind("<Configure>", configure_recent_osg_canvas)
        self.recently_used_osg_canvas.bind("<Configure>", configure_recent_osg_canvas)
        
        # Store reference
        self.recently_used_osg_container = recently_used_osg_container
    
    def load_recently_used_opensourcegaming(self):
        """Load and display recently used open source games"""
        # Check if recently used section exists
        if not hasattr(self, 'recently_used_osg_frame'):
            return
        
        # Check if username is set
        if not self.username:
            return
        
        # Clear existing widgets
        for widget in self.recently_used_osg_frame.winfo_children():
            widget.destroy()
        
        # Load recently used games from user's account directory
        user_account_dir = get_user_account_dir(self.username)
        recently_used_file = user_account_dir / "recently_used_opensourcegaming.json"
        
        if not recently_used_file.exists():
            # File doesn't exist yet, that's okay - no games have been used
            return
        
        try:
            with open(recently_used_file, 'r') as f:
                recently_used = json.load(f)
        except Exception as e:
            print(f"Error loading recently used open source games: {e}")
            return
        
        if not recently_used:
            return
        
        # Display games in horizontal grid
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        # Button size for recently used (banner-like, rectangular)
        button_width = self.scaler.scale_dimension(300)  # Wider for banner look
        button_height = self.scaler.scale_dimension(150)  # Keep height smaller
        button_padding = self.scaler.scale_padding(10)
        
        for game in recently_used[:10]:  # Show max 10
            # Create button frame
            button_frame = tk.Frame(self.recently_used_osg_frame, bg=bg_color)
            button_frame.pack(side=tk.LEFT, padx=button_padding)
            
            # Load and display game image - resolve paths to handle custom locations
            image_path = Path(self.to_absolute_path(game.get("image", "")))
            game_name = game.get("name", "Unknown Game")
            sh_file = self.to_absolute_path(game.get("sh_file", ""))
            
            button = None
            if image_path.exists() and PIL_AVAILABLE:
                try:
                    image = Image.open(image_path)
                    image = image.resize((button_width, button_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    button = tk.Button(
                        button_frame,
                        image=photo,
                        command=lambda sf=sh_file, gn=game_name: self.run_recent_osg_game(sf, gn),
                        bg=menu_bar_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        borderwidth=0,
                        highlightthickness=0,
                        activebackground=self.theme.get_color("background_secondary", "#1A1A1A")
                    )
                    button.image = photo  # Keep reference
                    button.pack()
                except Exception as e:
                    print(f"Error loading recently used game image {image_path}: {e}")
                    # Fallback to text button
                    button = tk.Button(
                        button_frame,
                        text=game_name,
                        command=lambda sf=sh_file, gn=game_name: self.run_recent_osg_game(sf, gn),
                        bg=menu_bar_color,
                        fg=text_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        width=self.scaler.scale_dimension(15),
                        height=self.scaler.scale_dimension(10),
                        font=self.theme.get_font("body_small", scaler=self.scaler)
                    )
                    button.pack()
            else:
                # Fallback to text button
                button = tk.Button(
                    button_frame,
                    text=game_name,
                    command=lambda sf=sh_file, gn=game_name: self.run_recent_osg_game(sf, gn),
                    bg=menu_bar_color,
                    fg=text_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    width=self.scaler.scale_dimension(15),
                    height=self.scaler.scale_dimension(10),
                    font=self.theme.get_font("body_small", scaler=self.scaler)
                )
                button.pack()
        
        # Update canvas scroll region after loading games
        self.recently_used_osg_frame.update_idletasks()
        self.recently_used_osg_canvas.update_idletasks()
        bbox = self.recently_used_osg_canvas.bbox("all")
        if bbox:
            # Set scrollregion for horizontal scrolling
            self.recently_used_osg_canvas.configure(scrollregion=bbox)
        # Reset scroll position to start
        self.recently_used_osg_canvas.xview_moveto(0)
    
    def run_recent_osg_game(self, sh_file_path, game_name):
        """Run an open source game from recently used section"""
        import subprocess
        sh_path = Path(sh_file_path)
        
        if not sh_path.exists():
            from tkinter import messagebox
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
            
            # Update recently used (move to front) - use user's account directory
            if not self.username:
                return
            
            user_account_dir = get_user_account_dir(self.username)
            recently_used_file = user_account_dir / "recently_used_opensourcegaming.json"
            
            # Convert to relative path for comparison
            sh_file_relative = self.to_relative_path(sh_file_path)
            
            if recently_used_file.exists():
                with open(recently_used_file, 'r') as f:
                    recently_used = json.load(f)
                
                # Find game info before removing
                game_info = None
                for game in recently_used:
                    if game.get("sh_file") == sh_file_relative:
                        game_info = game.copy()
                        break
                
                # Remove if exists and add to front
                recently_used = [game for game in recently_used if game.get("sh_file") != sh_file_relative]
                
                if not game_info:
                    # Load from games.json
                    games_base_dir = get_data_base_path() / "opensourcegaming"
                    games_json = games_base_dir / "games.json"
                    if games_json.exists():
                        with open(games_json, 'r') as f:
                            games_data = json.load(f)
                            for game in games_data.get("games", []):
                                if game.get("sh_file") == sh_file_relative:
                                    game_info = game.copy()
                                    break
                
                if game_info:
                    from datetime import datetime
                    game_info["last_used"] = datetime.now().isoformat()
                    recently_used.insert(0, game_info)
                    recently_used = recently_used[:10]
                    
                    with open(recently_used_file, 'w') as f:
                        json.dump(recently_used, f, indent=2)
                    
                    # Reload display
                    self.load_recently_used_opensourcegaming()
                    
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to run game '{game_name}':\n{str(e)}")
            print(f"Error running game: {e}")
    
    def create_recently_used_windowssteam_section(self):
        """Create the Recently Used Windows/Steam Games section"""
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        
        # Section container
        recently_used_ws_container = tk.Frame(self.content_area, bg=bg_color)
        recently_used_ws_container.pack(fill=tk.X, padx=self.scaler.scale_padding(20), pady=(self.scaler.scale_padding(20), 0))
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            recently_used_ws_container,
            text="Recently Used Windows/Steam Games",
            font=heading_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)))
        
        # Scrollable frame with left/right buttons
        scroll_container = tk.Frame(recently_used_ws_container, bg=bg_color)
        scroll_container.pack(fill=tk.X)
        
        # Left scroll button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        left_button = tk.Button(
            scroll_container,
            text="◀",
            font=button_font,
            command=self.scroll_recently_used_ws_left,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            width=self.scaler.scale_dimension(3),
            height=self.scaler.scale_dimension(2)
        )
        left_button.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(10)))
        
        # Canvas for horizontal scrolling
        self.recently_used_ws_canvas = tk.Canvas(
            scroll_container,
            bg=bg_color,
            highlightthickness=0,
            height=self.scaler.scale_dimension(180)
        )
        self.recently_used_ws_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollable frame inside canvas
        self.recently_used_ws_frame = tk.Frame(self.recently_used_ws_canvas, bg=bg_color)
        self.recently_used_ws_canvas_window = self.recently_used_ws_canvas.create_window(
            (0, 0), window=self.recently_used_ws_frame, anchor="nw"
        )
        
        # Right scroll button
        right_button = tk.Button(
            scroll_container,
            text="▶",
            font=button_font,
            command=self.scroll_recently_used_ws_right,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            width=self.scaler.scale_dimension(3),
            height=self.scaler.scale_dimension(2)
        )
        right_button.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(10), 0))
        
        # Configure canvas scroll region
        def configure_recent_ws_canvas(event=None):
            self.recently_used_ws_canvas.update_idletasks()
            bbox = self.recently_used_ws_canvas.bbox("all")
            if bbox:
                # Set scrollregion for horizontal scrolling
                self.recently_used_ws_canvas.configure(scrollregion=bbox)
        
        self.recently_used_ws_frame.bind("<Configure>", configure_recent_ws_canvas)
        self.recently_used_ws_canvas.bind("<Configure>", configure_recent_ws_canvas)
        
        # Store reference
        self.recently_used_ws_container = recently_used_ws_container
    
    def scroll_recently_used_ws_left(self):
        """Scroll recently used Windows/Steam games left"""
        self.recently_used_ws_canvas.xview_scroll(-3, "units")
    
    def scroll_recently_used_ws_right(self):
        """Scroll recently used Windows/Steam games right"""
        self.recently_used_ws_canvas.xview_scroll(3, "units")
    
    def load_recently_used_windowssteam(self):
        """Load and display recently used Windows/Steam games"""
        # Check if recently used section exists
        if not hasattr(self, 'recently_used_ws_frame'):
            return
        
        # Check if username is set
        if not self.username:
            return
        
        # Clear existing widgets
        for widget in self.recently_used_ws_frame.winfo_children():
            widget.destroy()
        
        # Load recently used games from user's account directory
        user_account_dir = get_user_account_dir(self.username)
        recently_used_file = user_account_dir / "recently_used_windowssteam.json"
        
        if not recently_used_file.exists():
            # File doesn't exist yet, that's okay - no games have been used
            return
        
        try:
            with open(recently_used_file, 'r') as f:
                recently_used = json.load(f)
        except Exception as e:
            print(f"Error loading recently used Windows/Steam games: {e}")
            return
        
        if not recently_used:
            return
        
        # Display games in horizontal grid
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        # Button size for recently used (banner-like, rectangular)
        button_width = self.scaler.scale_dimension(300)  # Wider for banner look
        button_height = self.scaler.scale_dimension(150)  # Keep height smaller
        button_padding = self.scaler.scale_padding(10)
        
        for game in recently_used[:10]:  # Show max 10
            # Create button frame
            button_frame = tk.Frame(self.recently_used_ws_frame, bg=bg_color)
            button_frame.pack(side=tk.LEFT, padx=button_padding)
            
            # Load and display game image - resolve paths to handle custom locations
            image_path = Path(self.to_absolute_path(game.get("image", "")))
            game_name = game.get("name", "Unknown Game")
            sh_file = self.to_absolute_path(game.get("sh_file", ""))
            
            button = None
            if image_path.exists() and PIL_AVAILABLE:
                try:
                    image = Image.open(image_path)
                    image = image.resize((button_width, button_height), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    
                    button = tk.Button(
                        button_frame,
                        image=photo,
                        command=lambda sf=sh_file, gn=game_name: self.run_recent_ws_game(sf, gn),
                        bg=menu_bar_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        borderwidth=0,
                        highlightthickness=0,
                        activebackground=self.theme.get_color("background_secondary", "#1A1A1A")
                    )
                    button.image = photo  # Keep reference
                    button.pack()
                except Exception as e:
                    print(f"Error loading recently used game image {image_path}: {e}")
                    # Fallback to text button
                    button = tk.Button(
                        button_frame,
                        text=game_name,
                        command=lambda sf=sh_file, gn=game_name: self.run_recent_ws_game(sf, gn),
                        bg=menu_bar_color,
                        fg=text_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        width=self.scaler.scale_dimension(15),
                        height=self.scaler.scale_dimension(10),
                        font=self.theme.get_font("body_small", scaler=self.scaler)
                    )
                    button.pack()
            else:
                # Fallback to text button
                button = tk.Button(
                    button_frame,
                    text=game_name,
                    command=lambda sf=sh_file, gn=game_name: self.run_recent_ws_game(sf, gn),
                    bg=menu_bar_color,
                    fg=text_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    width=self.scaler.scale_dimension(15),
                    height=self.scaler.scale_dimension(10),
                    font=self.theme.get_font("body_small", scaler=self.scaler)
                )
                button.pack()
        
        # Update canvas scroll region after loading games
        self.recently_used_ws_frame.update_idletasks()
        self.recently_used_ws_canvas.update_idletasks()
        bbox = self.recently_used_ws_canvas.bbox("all")
        if bbox:
            # Set scrollregion for horizontal scrolling
            self.recently_used_ws_canvas.configure(scrollregion=bbox)
        # Reset scroll position to start
        self.recently_used_ws_canvas.xview_moveto(0)
    
    def run_recent_ws_game(self, sh_file_path, game_name):
        """Run a Windows/Steam game from recently used section"""
        import subprocess
        sh_path = Path(sh_file_path)
        
        if not sh_path.exists():
            from tkinter import messagebox
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
            
            # Update recently used (move to front) - use user's account directory
            if not self.username:
                return
            
            user_account_dir = get_user_account_dir(self.username)
            recently_used_file = user_account_dir / "recently_used_windowssteam.json"
            
            # Convert to relative path for comparison
            sh_file_relative = self.to_relative_path(sh_file_path)
            
            if recently_used_file.exists():
                with open(recently_used_file, 'r') as f:
                    recently_used = json.load(f)
                
                # Find game info before removing
                game_info = None
                for game in recently_used:
                    if game.get("sh_file") == sh_file_relative:
                        game_info = game.copy()
                        break
                
                # Remove if exists and add to front
                recently_used = [game for game in recently_used if game.get("sh_file") != sh_file_relative]
                
                if not game_info:
                    # Load from games.json
                    games_base_dir = get_data_base_path() / "windowssteam"
                    games_json = games_base_dir / "games.json"
                    if games_json.exists():
                        with open(games_json, 'r') as f:
                            games_data = json.load(f)
                            for game in games_data.get("games", []):
                                if game.get("sh_file") == sh_file_relative:
                                    game_info = game.copy()
                                    break
                
                if game_info:
                    from datetime import datetime
                    game_info["last_used"] = datetime.now().isoformat()
                    recently_used.insert(0, game_info)
                    recently_used = recently_used[:10]
                    
                    with open(recently_used_file, 'w') as f:
                        json.dump(recently_used, f, indent=2)
                    
                    # Reload display
                    self.load_recently_used_windowssteam()
                    
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to run game '{game_name}':\n{str(e)}")
            print(f"Error running game: {e}")
    
    def load_recently_used_apps(self):
        """Load and display recently used apps"""
        # Check if recently used section exists
        if not hasattr(self, 'recently_used_frame'):
            return
        
        # Check if username is set
        if not self.username:
            return
        
        # Clear existing widgets
        for widget in self.recently_used_frame.winfo_children():
            widget.destroy()
        
        # Load recently used apps from user's account directory
        user_account_dir = get_user_account_dir(self.username)
        recently_used_file = user_account_dir / "recently_used.json"
        
        if not recently_used_file.exists():
            # File doesn't exist yet, that's okay - no apps have been used
            return
        
        try:
            with open(recently_used_file, 'r') as f:
                recently_used = json.load(f)
        except Exception as e:
            print(f"Error loading recently used apps: {e}")
            return
        
        if not recently_used:
            return
        
        # Display apps in horizontal grid
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        # Button size for recently used (banner-like, rectangular)
        button_width = self.scaler.scale_dimension(300)  # Wider for banner look
        button_height = self.scaler.scale_dimension(150)  # Keep height smaller
        button_padding = self.scaler.scale_padding(10)
        
        for app in recently_used[:10]:  # Show max 10
            # Create button frame
            button_frame = tk.Frame(self.recently_used_frame, bg=bg_color)
            button_frame.pack(side=tk.LEFT, padx=button_padding)
            
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
                        command=lambda sf=sh_file, an=app_name: self.run_recent_app(sf, an),
                        bg=menu_bar_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        borderwidth=0,
                        highlightthickness=0,
                        activebackground=self.theme.get_color("background_secondary", "#1A1A1A")
                    )
                    button.image = photo  # Keep reference
                    button.pack()
                except Exception as e:
                    print(f"Error loading recently used app image {image_path}: {e}")
                    # Fallback to text button
                    button = tk.Button(
                        button_frame,
                        text=app_name,
                        command=lambda sf=sh_file, an=app_name: self.run_recent_app(sf, an),
                        bg=menu_bar_color,
                        fg=text_color,
                        cursor="hand2",
                        relief=tk.FLAT,
                        width=self.scaler.scale_dimension(15),
                        height=self.scaler.scale_dimension(10),
                        font=self.theme.get_font("body_small", scaler=self.scaler)
                    )
                    button.pack()
            else:
                # Fallback to text button
                button = tk.Button(
                    button_frame,
                    text=app_name,
                    command=lambda sf=sh_file, an=app_name: self.run_recent_app(sf, an),
                    bg=menu_bar_color,
                    fg=text_color,
                    cursor="hand2",
                    relief=tk.FLAT,
                    width=self.scaler.scale_dimension(15),
                    height=self.scaler.scale_dimension(10),
                    font=self.theme.get_font("body_small", scaler=self.scaler)
                )
                button.pack()
        
        # Update canvas scroll region after loading apps
        self.recently_used_frame.update_idletasks()
        self.recently_used_canvas.update_idletasks()
        bbox = self.recently_used_canvas.bbox("all")
        if bbox:
            # Set scrollregion for horizontal scrolling
            self.recently_used_canvas.configure(scrollregion=bbox)
        # Reset scroll position to start
        self.recently_used_canvas.xview_moveto(0)
    
    def run_recent_app(self, sh_file_path, app_name):
        """Run an app from recently used section"""
        import subprocess
        sh_path = Path(sh_file_path)
        
        if not sh_path.exists():
            from tkinter import messagebox
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
            
            # Update recently used (move to front) - use user's account directory
            if not self.username:
                return
            
            user_account_dir = get_user_account_dir(self.username)
            recently_used_file = user_account_dir / "recently_used.json"
            
            # Convert to relative path for comparison
            sh_file_relative = self.to_relative_path(sh_file_path)
            
            if recently_used_file.exists():
                with open(recently_used_file, 'r') as f:
                    recently_used = json.load(f)
                
                # Find app info before removing
                app_info = None
                for app in recently_used:
                    if app.get("sh_file") == sh_file_relative:
                        app_info = app.copy()
                        break
                
                # Remove if exists and add to front
                recently_used = [app for app in recently_used if app.get("sh_file") != sh_file_relative]
                
                if not app_info:
                    # Load from apps.json
                    apps_base_dir = get_data_base_path() / "apps"
                    apps_json = apps_base_dir / "apps.json"
                    if apps_json.exists():
                        with open(apps_json, 'r') as f:
                            apps_data = json.load(f)
                            for app in apps_data.get("apps", []):
                                if app.get("sh_file") == sh_file_relative:
                                    app_info = app.copy()
                                    break
                
                if app_info:
                    from datetime import datetime
                    app_info["last_used"] = datetime.now().isoformat()
                    recently_used.insert(0, app_info)
                    recently_used = recently_used[:10]
                    
                    with open(recently_used_file, 'w') as f:
                        json.dump(recently_used, f, indent=2)
                    
                    # Reload display
                    self.load_recently_used_apps()
                    
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to run app '{app_name}':\n{str(e)}")
            print(f"Error running app: {e}")
    
    def load_frame(self, frame_name):
        """Load and display a frame"""
        # Show home button (we're leaving dashboard)
        self.create_home_button()
        self.show_home_button()
        
        # Hide library buttons
        self.library_buttons_frame.pack_forget()
        
        # Hide recently used apps section
        if hasattr(self, 'recently_used_container'):
            self.recently_used_container.pack_forget()
        
        # Hide recently used open source games section
        if hasattr(self, 'recently_used_osg_container'):
            self.recently_used_osg_container.pack_forget()
        
        # Hide recently used Windows/Steam games section
        if hasattr(self, 'recently_used_ws_container'):
            self.recently_used_ws_container.pack_forget()
        
        # Hide current frame if exists
        if self.current_frame:
            self.current_frame.hide()
            self.current_frame = None
        
        # Clear frame container to remove any lingering widgets
        for widget in self.frame_container.winfo_children():
            widget.destroy()
        
        # Show frame container
        self.frame_container.pack(fill=tk.BOTH, expand=True, padx=self.frame_padding, pady=self.frame_padding)
        
        # Import and create the frame
        try:
            from theme_manager import get_app_root
            import sys
            import os
            
            app_root = get_app_root()
            frames_dir = app_root / "data" / "frames"
            
            # Add frames directory to path
            if str(frames_dir) not in sys.path:
                sys.path.insert(0, str(frames_dir))
            
            # Import the frame module
            if frame_name == "apps":
                from apps import AppsFrame
                self.current_frame = AppsFrame(self.frame_container, self.theme, self.scaler, self.username)
            elif frame_name == "emulators":
                from emulators import EmulatorsFrame
                self.current_frame = EmulatorsFrame(self.frame_container, self.theme, self.scaler, self.username)
            elif frame_name == "opensourcegaming":
                from opensourcegaming import OpenSourceGamingFrame
                self.current_frame = OpenSourceGamingFrame(self.frame_container, self.theme, self.scaler, self.username)
            elif frame_name == "windowssteam":
                from windowssteam import WindowsSteamFrame
                self.current_frame = WindowsSteamFrame(self.frame_container, self.theme, self.scaler, self.username)
            elif frame_name == "controlpanel":
                from controlpanel import ControlPanelFrame
                self.current_frame = ControlPanelFrame(self.frame_container, self.theme, self.scaler)
            
            if self.current_frame:
                self.current_frame.show()
        except Exception as e:
            print(f"Error loading frame {frame_name}: {e}")
    
    def go_home(self):
        """Navigate to dashboard/home"""
        # Hide home button (we're on dashboard now)
        self.hide_home_button()
        
        # Hide current frame if exists
        if self.current_frame:
            self.current_frame.hide()
            self.current_frame = None
        
        # Clear frame container to remove any lingering widgets
        for widget in self.frame_container.winfo_children():
            widget.destroy()
        
        # Hide frame container
        self.frame_container.pack_forget()
        
        # Ensure library buttons are at the top (pack them first to maintain order)
        if hasattr(self, 'library_buttons_frame'):
            self.library_buttons_frame.pack_forget()
            self.library_buttons_frame.pack(pady=self.scaler.scale_padding(30))
        
        # Hide and recreate recently used sections in the correct order
        if hasattr(self, 'recently_used_container'):
            self.recently_used_container.pack_forget()
            self.recently_used_container.destroy()
            self.recently_used_container = None
        if hasattr(self, 'recently_used_osg_container'):
            self.recently_used_osg_container.pack_forget()
            self.recently_used_osg_container.destroy()
            self.recently_used_osg_container = None
        if hasattr(self, 'recently_used_ws_container'):
            self.recently_used_ws_container.pack_forget()
            self.recently_used_ws_container.destroy()
            self.recently_used_ws_container = None
        
        # Recreate sections in the configured order
        self.create_recently_used_sections_in_order()
        
        # Reload the content for each section (sections are already created and packed in correct order)
        if hasattr(self, 'load_recently_used_apps'):
            self.load_recently_used_apps()
        if hasattr(self, 'load_recently_used_opensourcegaming'):
            self.load_recently_used_opensourcegaming()
        if hasattr(self, 'load_recently_used_windowssteam'):
            self.load_recently_used_windowssteam()
    
    def account_settings(self):
        """Open user account settings in main window"""
        if not self.username:
            return
        
        # Hide library buttons and recently used sections
        self.library_buttons_frame.pack_forget()
        if hasattr(self, 'recently_used_container'):
            self.recently_used_container.pack_forget()
        if hasattr(self, 'recently_used_osg_container'):
            self.recently_used_osg_container.pack_forget()
        if hasattr(self, 'recently_used_ws_container'):
            self.recently_used_ws_container.pack_forget()
        
        # Show home button
        self.create_home_button()
        if self.home_button:
            self.home_button.pack(side=tk.LEFT, padx=self.scaler.scale_padding(15), pady=self.scaler.scale_padding(15))
        
        # Load user account settings frame
        try:
            # Hide current frame if exists
            if self.current_frame:
                self.current_frame.hide()
            
            # Clear frame container to remove any lingering widgets
            for widget in self.frame_container.winfo_children():
                widget.destroy()
            
            # Add frames directory to path for imports
            import sys
            from theme_manager import get_app_root
            app_root = get_app_root()
            frames_dir = app_root / "data" / "frames"
            if str(frames_dir) not in sys.path:
                sys.path.insert(0, str(frames_dir))
            
            # Import and create user account settings frame
            from useraccountsettings import UserAccountSettingsFrame
            self.current_frame = UserAccountSettingsFrame(self.frame_container, self.theme, self.scaler, self.username, self)
            self.current_frame.show()
            
            # Show frame container
            self.frame_container.pack(fill=tk.BOTH, expand=True, padx=self.frame_padding, pady=self.frame_padding)
        except Exception as e:
            print(f"Error loading user account settings: {e}")
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to load Account Settings:\n{str(e)}")
        # TODO: Implement account settings screen
    
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
    
    def set_username(self, username):
        """Set the username and update the display"""
        # Check if this is a different user logging in
        is_new_user = (self.previous_username is not None and self.previous_username != username) or (self.previous_username is None and username is not None)
        
        self.previous_username = self.username  # Store previous username
        self.username = username
        
        # If a new user logged in, reset to home/dashboard view
        if is_new_user:
            self.go_home()
        
        # Try to load profile image
        self.load_profile_image()
        
        # Create profile section and power button in menu bar
        self.create_profile_section()
        self.create_power_button()
        self.create_admin_button()  # Create after power so it appears between profile and power
        
        # Load recently used apps when username is set
        self.load_recently_used_apps()
        # Load recently used open source games
        self.load_recently_used_opensourcegaming()
        # Load recently used Windows/Steam games
        self.load_recently_used_windowssteam()
        
        # Check if welcome popup should be shown
        self.check_and_show_welcome()
    
    def load_profile_image(self):
        """Load and display profile image if it exists"""
        if not self.username:
            return
        
        account_dir = get_user_account_dir(self.username)
        account_file = account_dir / "account.json"
        
        if account_file.exists():
            try:
                with open(account_file, 'r') as f:
                    account_data = json.load(f)
                
                profile_image_path = account_data.get('profile_image')
                
                # Check if stored path exists, if not try to find profile image in current account dir
                if profile_image_path and os.path.exists(profile_image_path):
                    self.profile_image_path = profile_image_path
                else:
                    # Look for profile image in the current account directory
                    # Profile images are named profile.{ext}
                    self.profile_image_path = None
                    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        potential_path = account_dir / f"profile{ext}"
                        if potential_path.exists():
                            self.profile_image_path = str(potential_path)
                            # Update the account data with the correct path
                            account_data['profile_image'] = str(potential_path)
                            with open(account_file, 'w') as f:
                                json.dump(account_data, f, indent=2)
                            break
            except Exception as e:
                print(f"Error loading account data: {e}")
    
    def check_and_show_welcome(self):
        """Check if welcome popup should be shown"""
        if not self.username:
            return
        
        account_dir = get_user_account_dir(self.username)
        account_file = account_dir / "account.json"
        
        if account_file.exists():
            try:
                with open(account_file, 'r') as f:
                    account_data = json.load(f)
                
                # Check if user has disabled welcome popup
                show_welcome = account_data.get('show_welcome_popup', True)
                
                if show_welcome:
                    self.show_welcome_popup()
            except Exception as e:
                print(f"Error checking welcome preference: {e}")
                # Show welcome by default if there's an error
                self.show_welcome_popup()
        else:
            # Show welcome if account file doesn't exist
            self.show_welcome_popup()
    
    def show_welcome_popup(self):
        """Show welcome popup for first-time users"""
        from welcome_popup import WelcomePopup
        welcome = WelcomePopup(
            self.parent,
            self.theme,
            self.scaler,
            self.username
        )
        welcome.show()
    
    def logout(self):
        """Handle logout"""
        # Reset to home before logging out
        self.go_home()
        self.username = None
        self.previous_username = None  # Clear previous username on logout
        self.profile_image_path = None
        self.on_logout()
    
    def exit_app(self):
        """Exit the application"""
        self.on_exit()
    
    def show(self):
        """Show the dashboard screen"""
        self.frame.pack(fill=tk.BOTH, expand=True)
        # Set focus for keyboard events
        self.frame.focus_set()
        if hasattr(self, 'scroll_canvas'):
            self.scroll_canvas.focus_set()
        # Load recently used apps when dashboard is shown
        if hasattr(self, 'recently_used_container'):
            self.load_recently_used_apps()
        # Load recently used open source games when dashboard is shown
        if hasattr(self, 'recently_used_osg_container'):
            self.load_recently_used_opensourcegaming()
        # Load recently used Windows/Steam games when dashboard is shown
        if hasattr(self, 'recently_used_ws_container'):
            self.load_recently_used_windowssteam()
        # Update scroll region after content loads
        if hasattr(self, 'scroll_canvas'):
            self.scroll_canvas.update_idletasks()
            bbox = self.scroll_canvas.bbox("all")
            if bbox:
                self.scroll_canvas.configure(scrollregion=bbox)
    
    def hide(self):
        """Hide the dashboard screen"""
        self.frame.pack_forget()
        # Unbind keyboard events from root window
        root = self.parent.winfo_toplevel()
        if hasattr(self, 'on_arrow_key'):
            try:
                root.unbind("<KeyPress>")
            except:
                pass
        # Unbind keyboard events from root window
        root = self.parent.winfo_toplevel()
        if hasattr(self, 'on_arrow_key'):
            try:
                root.unbind("<KeyPress>", self.on_arrow_key)
            except:
                pass
