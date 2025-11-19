import os
import tkinter as tk
# pygame import removed - not used in main.py
from tkinter import ttk
import importlib.util
import sys
import json
import threading
from pathlib import Path # Import Path

from paths import PathManager
from controller_manager import get_controller_manager
from rom_cache_manager import ROMCacheManager
from responsive_manager import ResponsiveManager

from data.frames.dashboard import DashboardFrame
from data.frames.open_source_gaming import OpenSourceGamingFrame
from data.frames.emulators import EmulatorsFrame
from data.frames.login import LoginFrame
from data.frames.loading import LoadingFrame
from data.frames.windows_steam_wine import WindowsSteamWineFrame
from data.frames.apps import AppsFrame
from data.frames.accounts import AccountsFrame
from data.frames.accountsettings import AccountSettingsFrame
from data.frames.userpreferences import UserPreferencesFrame
from data.frames.store import StoreFrame
from data.frames.adminpanel import AdminPanelFrame
from data.frames.all_roms import AllRomsFrame
from data.frames.directories_frame import DirectoriesFrame
from data.frames.backups import BackupsFrame # Import BackupsFrame
from data.frames.bios import BiosFrame # Import BiosFrame
from data.frames.roms import RomsFrame # Import RomsFrame
from data.frames.themes import ThemesFrame # Import ThemesFrame
from menu import menu

APP_NAME = "linux-gaming-center"

def on_button_hover(event):
    event.widget.config(bg="#3b3f46")

def on_button_leave(event):
    event.widget.config(bg="#1b2838")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Linux Gaming Center")
        
        # Initialize responsive manager first
        self.responsive_manager = ResponsiveManager(self)
        
        self.attributes("-alpha", 1.0)
        
        # Window state tracking
        self.is_fullscreen = True
        self.windowed_size = None

        # Determine the application's base installation directory
        # This assumes main.py is in the root of the installation (e.g., /opt/linux-gaming-center/)
        self.app_installation_dir = Path(os.path.dirname(os.path.abspath(__file__)))

        self.path_manager = PathManager()
        self.EMULATOR_LIBRARIES_DIR = self.path_manager.get_path("data") / "emulators" / "custom_frames"
        self.EMULATOR_LIBRARIES_DIR.mkdir(parents=True, exist_ok=True)
        # Emulator Libraries Directory initialized
        
        # Initialize ROM cache manager
        self.rom_cache_manager = ROMCacheManager(self.path_manager)

        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.apply_base_styles()
        self.apply_emulator_frame_styles()

        self.container = tk.Frame(self, bg="black")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.menu_bar = menu(self, self)
        self.menu_bar.pack_forget()
        self.menu_bar.pack(in_=self, side="top", fill="x", before=self.container)

        self.frames = {}
        self.current_frame = None
        self.current_user = None
        self.current_frame_name = None
        self.shown_welcome_users = set()
        
        # Initialize controller manager
        self.controller_manager = get_controller_manager(self.path_manager)
        self.setup_controller_navigation()

        self.frames["LoadingFrame"] = LoadingFrame(self.container, self)
        self.frames["LoadingFrame"].grid(row=0, column=0, sticky="nsew")
        self.show_frame("LoadingFrame")

        # Set up ROM cache manager callbacks
        self.rom_cache_manager.add_progress_callback(self.frames["LoadingFrame"].update_progress)
        self.rom_cache_manager.add_completion_callback(self.on_rom_scan_complete)
        self.rom_cache_manager.add_frame_notification_callback(self.notify_frames_scan_complete)
        
        # Set up responsive manager callbacks
        self.responsive_manager.notify_frames_of_resize = self.notify_frames_of_resize
        
        # Bind keyboard shortcuts for window mode switching
        self.bind('<F11>', self.toggle_fullscreen)
        self.bind('<Escape>', self.exit_fullscreen)
        self.bind('<Control-w>', self.toggle_fullscreen)
        
        # Bind window resize events for responsive design
        self.bind('<Configure>', self.on_window_configure)

        # Set up window mode after window is fully initialized
        self.after(100, self.setup_window_mode)
        
        # Start ROM scanning IMMEDIATELY - don't wait for frames to load
        # This ensures loading screen shows progress from the start
        self.after(200, self.start_initial_rom_scanning)
        
        # Load frames in parallel (doesn't block ROM scanning)
        self.after(500, self.load_all_frames)

        # Bind custom event to show overlay
        self.bind("<<ShowOverlayMenu>>", lambda event: show_overlay_menu_tk(self))

    # --- Style Configuration Methods ---
    def apply_base_styles(self, theme_data=None): # Added theme_data parameter
        """
        Loads and applies general theme styles for static frames and common widgets.
        This includes styles used by the main EmulatorsFrame.
        """
        style = ttk.Style()

        # Use path_manager to get the correct themes directory
        theme_file_path = self.path_manager.get_path("themes") / "cosmictwilight" / "styles" / "emulators.json"
        theme = {}
        if theme_file_path.exists():
            try:
                with open(theme_file_path, "r") as f:
                    theme = json.load(f)
            except json.JSONDecodeError as e:
                # Error loading theme
                pass
            except Exception as e:
                # Unexpected error loading theme
                pass

        # If theme_data is provided, use it, otherwise use the loaded theme
        current_theme = theme_data if theme_data is not None else theme

        bg = current_theme.get("background", "#1e1e1e")
        fg = current_theme.get("text_color", "#ffffff")
        font_family = current_theme.get("font_family", "Segoe UI")
        font_size = int(current_theme.get("font_size", 11) * (self.winfo_screenwidth() / 1920)) # Example scaling

        # Apply general styles
        style.configure("TFrame", background=bg) # Default frame style
        style.configure("TLabel", background=bg, foreground=fg, font=(font_family, font_size))
        style.configure("TButton", background=bg, foreground=fg, font=(font_family, font_size + 1), padding=6)
        style.configure("TCombobox", background=bg, foreground=fg, font=(font_family, font_size))
        style.configure("Treeview", background="#3e4451", foreground="#ffffff", fieldbackground="#3e4451")
        style.map("Treeview", background=[('selected', '#5698d3')])
        style.configure("Treeview.Heading", background="#3e4451", foreground="#ffffff", font=(font_family, font_size, "bold"))
        style.configure("TScrollbar", background="#61afef", troughcolor="#282c34") # General scrollbar

        # Apply styles specific to EmulatorsFrame (which uses "Emulator.*" styles)
        style.configure("Emulator.TFrame", background=bg)
        style.configure("Emulator.TLabel", background=bg, foreground=fg, font=(font_family, font_size), anchor="center")
        style.configure("Emulator.TButton", background=bg, foreground=fg, font=(font_family, font_size + 1), padding=6)
        style.configure("Sort.TCombobox", background=bg, foreground=fg, font=(font_family, font_size))
        style.configure("SortLabel.TLabel", background=bg, foreground=fg, font=(font_family, font_size), anchor="w")

        # NEW: Styles for AllRomsFrame
        style.configure("AllRomsFrame.TFrame", background="#282c34")
        style.configure("AllRomsFrame.TLabel", background="#282c34", foreground="#ffffff", font=("Arial", 12))
        # NEW: Style for the title label in AllRomsFrame
        style.configure("AllRomsFrame.Title.TLabel",
                                 background="#282c34",
                                 foreground="#9a32cd",
                                 font=("Impact", 24))


    def apply_emulator_frame_styles(self):
        """
        Applies the specific ttk styles required by the dynamically generated
        emulator frames (e.g., NintendoNesEmulatorFrame, Snes9xEmulatorFrame).
        These were previously defined within each generated .py file.
        """
        style = ttk.Style()
        # These are the styles that were in the generated .py files' configure_style method
        style.configure("EmulatorFrame.TFrame", background="#282c34")  # Dark background
        style.configure("EmulatorFrame.TLabel", background="#282c34", foreground="#ffffff", font=("Arial", 12))
        style.configure("EmulatorFrame.TButton", background="#61afef", foreground="#ffffff", font=("Arial", 10, "bold"), padding=5)
        style.configure("EmulatorFrame.Treeview", background="#3e4451", foreground="#ffffff", fieldbackground="#3e4451")
        style.map("EmulatorFrame.Treeview", background=[('selected', '#5698d3')])
        style.configure("EmulatorFrame.Treeview.Heading", background="#3e4451", foreground="#ffffff", font=("Arial", 10, "bold"))

        # Configure the Scrollbar style
        style.configure("EmulatorFrame.Scrollbar", background="#61afef", troughcolor="#282c34")

        # --- CRITICAL NEW ADDITION: Explicitly define the layout for the custom scrollbar style ---
        # The Ttk Scrollbar has internal "elements" like 'trough', 'thumb', 'uparrow', 'downarrow'.
        # We need to tell Ttk how these elements are laid out for
        # 'EmulatorFrame.Scrollbar' when it's vertical.
        style.layout("EmulatorFrame.Scrollbar", [
            ('Vertical.Scrollbar.trough', {
                'children': [
                    ('Vertical.Scrollbar.thumb', {'expand': '1', 'sticky': 'nswe'}),
                    ('Vertical.Scrollbar.uparrow', {'side': 'top', 'sticky': ''}),
                    ('Vertical.Scrollbar.downarrow', {'side': 'bottom', 'sticky': ''})
                ],
                'sticky': 'ns'
            })
        ])

    # This method is now used by EmulatorsFrame to get its theme data.
    # It's here because the Controller is the central point for theme management.
    def get_theme_for_emulators_frame(self):
        """Provides theme settings specifically for the EmulatorsFrame."""
        # Use path_manager to get the correct themes directory
        theme_file_path = self.path_manager.get_path("themes") / "cosmictwilight" / "styles" / "emulators.json"
        if theme_file_path.exists():
            with open(theme_file_path, "r") as f:
                return json.load(f)
        return {
            "background": "#1e1e1e",
            "text_color": "#ffffff",
            "font_family": "Segoe UI",
            "font_size": 11,
        }

    def load_all_frames(self):
        frame_classes = {
            "LoginFrame": LoginFrame,
            "DashboardFrame": DashboardFrame,
            "OpenSourceGamingFrame": OpenSourceGamingFrame,
            "EmulatorsFrame": EmulatorsFrame,
            "SteamFrame": WindowsSteamWineFrame,
            "AppsFrame": AppsFrame,
            "AccountsFrame": AccountsFrame,
            "AccountSettingsFrame": AccountSettingsFrame,
            "UserPreferencesFrame": UserPreferencesFrame,
            "StoreFrame": StoreFrame,
            "AdminPanelFrame": AdminPanelFrame,
            "AllRomsFrame": AllRomsFrame,
            "DirectoriesFrame": DirectoriesFrame,
            "BackupsFrame": BackupsFrame,
            "BiosFrame": BiosFrame, # Added BiosFrame
            "RomsFrame": RomsFrame, # Added RomsFrame
            "ThemesFrame": ThemesFrame, # Added ThemesFrame
        }

        for name, FrameClass in frame_classes.items():
            try:
                # Pass the path_manager to frames that need it
                if name == "DashboardFrame":
                    frame = FrameClass(self.container, self, self.shown_welcome_users)
                    # Add path_manager to DashboardFrame for account data access
                    frame.path_manager = self.path_manager
                # MODIFIED: Explicitly list all frames that require path_manager
                elif name in (
                    "LoginFrame",
                    "DirectoriesFrame",
                    "AdminPanelFrame",
                    "EmulatorsFrame",
                    "OpenSourceGamingFrame",
                    "SteamFrame",
                    "AppsFrame",
                    "BackupsFrame",
                    "AccountsFrame",
                    "BiosFrame",
                    "RomsFrame",
                    "ThemesFrame",
                    "AccountSettingsFrame",
                    "UserPreferencesFrame"
                ):
                    frame = FrameClass(self.container, self, self.path_manager)
                    # Add ROM cache manager to frames that need it
                    if hasattr(frame, 'set_rom_cache_manager'):
                        frame.set_rom_cache_manager(self.rom_cache_manager)
                else:
                    frame = FrameClass(self.container, self)

                frame.grid(row=0, column=0, sticky="nsew") # Apply grid to ALL frames
                self.frames[name] = frame # Add to frames

                if name not in ("LoadingFrame", "LoginFrame"):
                    frame.grid_remove()  # Hide all frames except the initial ones
            except Exception as e:
                # Failed to load frame
                pass

        # After all static frames are initialized and registered,
        # then call the dynamic loading for EmulatorsFrame
        if "EmulatorsFrame" in self.frames:
            self.frames["EmulatorsFrame"].load_all_dynamic_emulator_frames_at_startup()
            
            # ROM scanning is already started in start_initial_rom_scanning
            # Just ensure emulators are available for scanning

        # Don't fade out loading until ROM scanning is complete
        # Transition happens in on_rom_scan_complete()

    def start_initial_rom_scanning(self):
        """Start ROM scanning immediately when app starts - before frames load"""
        # Load emulator data directly from file (don't wait for frames)
        emulators_file = self.path_manager.get_path("data") / "emulators" / "emulators.json"
        
        if emulators_file.exists():
            try:
                with open(emulators_file, 'r') as f:
                    emulators_data = json.load(f)
                
                if emulators_data:
                    # Update loading screen to show we're starting
                    if "LoadingFrame" in self.frames:
                        self.frames["LoadingFrame"].update_progress(0, len(emulators_data), "Starting ROM scan...")
                    
                    # Start background ROM scanning immediately
                    self.rom_cache_manager.start_background_scan(emulators_data)
                    return
            except Exception:
                pass
        
        # No emulators found or error loading - mark as complete
        self.on_rom_scan_complete()

    def start_rom_scanning(self):
        """Start background ROM scanning"""
        if "EmulatorsFrame" in self.frames:
            emulators_data = self.frames["EmulatorsFrame"].emulators_data
            if emulators_data:
                # Starting ROM scan
                # Update loading screen to show we're starting
                self.frames["LoadingFrame"].update_progress(0, len(emulators_data), "Starting ROM scan...")
                self.rom_cache_manager.start_background_scan(emulators_data)
            else:
                # No emulators found, skipping ROM scan
                self.on_rom_scan_complete()
        else:
            # EmulatorsFrame not available, skipping ROM scan
            self.on_rom_scan_complete()

    def on_rom_scan_complete(self):
        """Called when ROM scanning and image loading are complete"""
        # Check if images are still loading - wait until complete
        if self.rom_cache_manager.image_loading:
            # Continue waiting for image loading to complete
            self.after(100, self.on_rom_scan_complete)
            return
        
        # Verify ROM scanning is also complete
        if self.rom_cache_manager.scanning:
            # Still scanning ROMs, wait
            self.after(100, self.on_rom_scan_complete)
            return
        
        # ROM scanning and image loading complete - show completion message
        self.frames["LoadingFrame"].update_progress(100, 100, "Loading complete!")
        self.frames["LoadingFrame"].hide_progress()
        
        # Wait a moment to show completion, then transition to login screen
        self.after(1500, self.transition_to_login)
    
    def transition_to_login(self):
        """Transition from loading screen to login screen after everything is loaded"""
        # All ROMs and images are pre-loaded, safe to show login screen
        # Hide loading frame and show login frame
        if "LoadingFrame" in self.frames:
            self.frames["LoadingFrame"].grid_remove()
        if "LoginFrame" in self.frames:
            self.show_frame("LoginFrame")
    
    def notify_frames_scan_complete(self):
        """Notify all emulator frames that ROM scanning is complete"""
        # Notifying all emulator frames that ROM scanning is complete
        for frame_name, frame in self.frames.items():
            if hasattr(frame, 'on_rom_scan_complete'):
                try:
                    frame.on_rom_scan_complete()
                except Exception as e:
                    # Error notifying frame
                    pass

    def register_dynamic_frame(self, full_file_path, dynamic_frame_class_name):
        """
        Dynamically loads a single Python file, instantiates its Frame class,
        and adds it to self.frames. This version is used *after* initial startup
        (e.g., when adding a new emulator through the UI).
        """
        module_name = os.path.basename(full_file_path)[:-3]

        if dynamic_frame_class_name in self.frames:
            # Dynamic frame already registered, reloading if necessary
            old_frame = self.frames.pop(dynamic_frame_class_name, None)
            if old_frame:
                old_frame.destroy()
                # Destroyed old instance

        try:
            # Always remove from sys.modules to ensure a fresh import, especially if file was modified
            if f"dynamic_emulators.{module_name}" in sys.modules:
                del sys.modules[f"dynamic_emulators.{module_name}"]

            spec = importlib.util.spec_from_file_location(
                f"dynamic_emulators.{module_name}",
                full_file_path
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Force Tkinter to process pending events, including style updates
            self.update_idletasks() # Crucial line for dynamic UI additions
            self.apply_emulator_frame_styles() # Re-apply just in case, though it should be redundant here

            if hasattr(module, dynamic_frame_class_name):
                FrameClass = getattr(module, dynamic_frame_class_name)

                # Dynamically loaded emulator frames also need the path_manager
                # to correctly locate ROMs, BIOS, etc.
                frame_instance = FrameClass(self.container, self, self.path_manager)
                # Add ROM cache manager to dynamic frames
                if hasattr(frame_instance, 'set_rom_cache_manager'):
                    frame_instance.set_rom_cache_manager(self.rom_cache_manager)
                frame_instance.grid(row=0, column=0, sticky="nsew")
                frame_instance.grid_remove()  # Hide it initially

                self.frames[dynamic_frame_class_name] = frame_instance
                # Successfully registered dynamic frame
                return True
            else:
                # Warning: Class not found
                return False
        except Exception as e:
            # Error loading dynamic emulator frame
            return False

    def reload_path_manager_config(self):
        """
        Reloads the PathManager's configuration from disk and
        triggers relevant frames to refresh their data based on new paths.
        """
        self.path_manager.load_paths() # This will re-read paths.json

        # Trigger relevant frames to refresh their data/UI based on potentially new paths
        # This is crucial for changes in DirectoriesFrame to take effect immediately.

        # LoginFrame needs to re-scan for accounts
        if "LoginFrame" in self.frames and self.frames["LoginFrame"].winfo_ismapped():
            if hasattr(self.frames["LoginFrame"], 'refresh_accounts_display') and callable(self.frames["LoginFrame"].refresh_accounts_display):
                self.frames["LoginFrame"].refresh_accounts_display()

        # DashboardFrame needs to update recently played lists
        if "DashboardFrame" in self.frames and self.frames["DashboardFrame"].winfo_ismapped():
            self.frames["DashboardFrame"].update_dashboard()

        # EmulatorsFrame needs to reload its list of emulators and potentially ROMs
        if "EmulatorsFrame" in self.frames:
            # Re-register dynamic frames in case their paths changed (though less common)
            self.frames["EmulatorsFrame"].load_all_dynamic_emulator_frames_at_startup()
            # Force a reload of the main emulators list and redraw
            self.frames["EmulatorsFrame"].load_emulators()
            self.frames["EmulatorsFrame"].force_redraw()

        # OpenSourceGamingFrame needs to reload its games
        if "OpenSourceGamingFrame" in self.frames and self.frames["OpenSourceGamingFrame"].winfo_ismapped():
            self.frames["OpenSourceGamingFrame"].load_games()
            self.frames["OpenSourceGamingFrame"].force_redraw()

        # AppsFrame needs to reload its apps
        if "AppsFrame" in self.frames and self.frames["AppsFrame"].winfo_ismapped():
            self.frames["AppsFrame"].load_apps()
            self.frames["AppsFrame"].force_redraw()


        # WindowsSteamWineFrame (SteamFrame) needs to reload its games
        if "SteamFrame" in self.frames and self.frames["SteamFrame"].winfo_ismapped():
            self.frames["SteamFrame"].load_games()
            self.frames["SteamFrame"].force_redraw()

        # AllRomsFrame might need to rescan if ROM paths changed
        if "AllRomsFrame" in self.frames and self.frames["AllRomsFrame"].winfo_ismapped():
            self.frames["AllRomsFrame"].load_all_roms()
            self.frames["AllRomsFrame"].force_redraw()

        # DirectoriesFrame itself needs to update its display
        if "DirectoriesFrame" in self.frames and self.frames["DirectoriesFrame"].winfo_ismapped():
            self.frames["DirectoriesFrame"]._update_all_path_displays()

        # BackupsFrame doesn't hold data that needs reloading, but it's good to include
        # for completeness if future features require it.
        if "BackupsFrame" in self.frames and self.frames["BackupsFrame"].winfo_ismapped():
            pass # No specific refresh method needed here yet

        # AccountsFrame, BiosFrame, RomsFrame, ThemesFrame, AccountSettingsFrame, UserPreferencesFrame
        # also need to be refreshed if visible
        for frame_name in ["AccountsFrame", "BiosFrame", "RomsFrame", "ThemesFrame", "AccountSettingsFrame", "UserPreferencesFrame", "AdminPanelFrame"]:
            if frame_name in self.frames and self.frames[frame_name].winfo_ismapped():
                if hasattr(self.frames[frame_name], 'on_show_frame') and callable(self.frames[frame_name].on_show_frame):
                    self.frames[frame_name].on_show_frame()
                elif hasattr(self.frames[frame_name], 'on_visibility_change') and callable(self.frames[frame_name].on_visibility_change):
                    self.frames[frame_name].on_visibility_change(event=None)

    def fade_out_loading(self):
        loading_frame = self.frames.get("LoadingFrame")
        login_frame = self.frames.get("LoginFrame")
        if loading_frame and login_frame:
            # Only transition to login if user is not already logged in
            if not hasattr(self, 'current_user') or not self.current_user:
                login_frame.grid()  # Make the login frame visible immediately
                login_frame.tkraise() # Bring the login frame to the front
                self.current_frame = login_frame # Update the current frame
                self.current_frame_name = "LoginFrame" # Set current frame name

            # Remove the loading frame regardless
            self.after(1000, lambda: loading_frame.grid_remove())

    def show_frame(self, name):
        """
        Shows the specified frame and handles menu bar visibility.
        Also calls an 'on_show_frame' method if the new frame has one.
        """
        new_frame = self.frames.get(name)
        if new_frame:
            if self.current_frame:
                self.current_frame.grid_remove() # Hide the previous frame

            new_frame.grid() # Show the new frame
            self.current_frame = new_frame
            self.current_frame_name = name

            # Show or hide menu bar properly
            if name in ("LoginFrame", "LoadingFrame", "SwitchuserFrame"): # Keep SwitchuserFrame here
                self.menu_bar.pack_forget()
            else:
                self.menu_bar.pack_forget()
                self.menu_bar.pack(in_=self, side="top", fill="x", before=self.container)

            # Update home button visibility
            if hasattr(self, "update_home_button_visibility"):
                self.update_home_button_visibility()
            elif hasattr(self.menu_bar, "update_home_button_visibility"):
                self.menu_bar.update_home_button_visibility()

            # --- IMPORTANT: Call on_show_frame or on_visibility_change ---
            # This ensures the frame can refresh its content or layout when shown.
            # Call 'on_visibility_change' if it exists, otherwise 'on_show_frame', then 'force_redraw'.
            if hasattr(new_frame, 'on_visibility_change') and callable(new_frame.on_visibility_change):
                new_frame.on_visibility_change(event=None) # Pass a dummy event as it's often bound to <Visibility>
            elif hasattr(new_frame, 'on_show_frame') and callable(new_frame.on_show_frame):
                new_frame.on_show_frame()
            elif hasattr(new_frame, 'force_redraw') and callable(new_frame.force_redraw):
                new_frame.force_redraw()

        else:
            # Error: Frame not found
            # This error means the frame wasn't loaded at startup or registered dynamically.
            # For dynamic emulator frames, this should ideally not happen if register_dynamic_frame
            # is called correctly after creation.
            pass

    def toggle_fullscreen(self):
        is_fullscreen = self.attributes("-fullscreen")
        self.attributes("-fullscreen", not is_fullscreen)
    
    def setup_controller_navigation(self):
        """Setup controller navigation callbacks"""
        from controller_manager import NavigationAction
        
        # Register navigation callbacks
        self.controller_manager.register_navigation_callback(
            NavigationAction.UP.value, 
            self.controller_navigate_up
        )
        self.controller_manager.register_navigation_callback(
            NavigationAction.DOWN.value, 
            self.controller_navigate_down
        )
        self.controller_manager.register_navigation_callback(
            NavigationAction.LEFT.value, 
            self.controller_navigate_left
        )
        self.controller_manager.register_navigation_callback(
            NavigationAction.RIGHT.value, 
            self.controller_navigate_right
        )
        self.controller_manager.register_navigation_callback(
            NavigationAction.SELECT.value, 
            self.controller_select
        )
        self.controller_manager.register_navigation_callback(
            NavigationAction.BACK.value, 
            self.controller_back
        )
        self.controller_manager.register_navigation_callback(
            NavigationAction.MENU.value, 
            self.controller_menu
        )
        self.controller_manager.register_navigation_callback(
            NavigationAction.HOME.value, 
            self.controller_home
        )
        
        # Start controller monitoring
        self.controller_manager.start_controller_monitoring()
    
    def controller_navigate_up(self):
        """Handle controller up navigation"""
        if hasattr(self.current_frame, 'controller_navigate_up'):
            self.current_frame.controller_navigate_up()
        else:
            # Default behavior - focus previous widget
            self.focus_previous_widget()
    
    def controller_navigate_down(self):
        """Handle controller down navigation"""
        if hasattr(self.current_frame, 'controller_navigate_down'):
            self.current_frame.controller_navigate_down()
        else:
            # Default behavior - focus next widget
            self.focus_next_widget()
    
    def controller_navigate_left(self):
        """Handle controller left navigation"""
        if hasattr(self.current_frame, 'controller_navigate_left'):
            self.current_frame.controller_navigate_left()
        else:
            # Default behavior - focus previous widget
            self.focus_previous_widget()
    
    def controller_navigate_right(self):
        """Handle controller right navigation"""
        if hasattr(self.current_frame, 'controller_navigate_right'):
            self.current_frame.controller_navigate_right()
        else:
            # Default behavior - focus next widget
            self.focus_next_widget()
    
    def controller_select(self):
        """Handle controller select action"""
        if hasattr(self.current_frame, 'controller_select'):
            self.current_frame.controller_select()
        else:
            # Default behavior - activate focused widget
            focused = self.focus_get()
            if focused:
                focused.invoke() if hasattr(focused, 'invoke') else None
    
    def controller_back(self):
        """Handle controller back action"""
        if hasattr(self.current_frame, 'controller_back'):
            self.current_frame.controller_back()
        else:
            # Default behavior - go to dashboard
            self.show_frame("DashboardFrame")
    
    def controller_menu(self):
        """Handle controller menu action"""
        if hasattr(self.current_frame, 'controller_menu'):
            self.current_frame.controller_menu()
        else:
            # Default behavior - show menu
            if hasattr(self, 'menu_bar') and hasattr(self.menu_bar, 'show_profile_dropdown'):
                self.menu_bar.show_profile_dropdown()
    
    def controller_home(self):
        """Handle controller home action"""
        if hasattr(self.current_frame, 'controller_home'):
            self.current_frame.controller_home()
        else:
            # Default behavior - go to dashboard
            self.show_frame("DashboardFrame")
    
    def focus_next_widget(self):
        """Focus the next focusable widget"""
        current = self.focus_get()
        if current:
            # Try to find next widget
            widgets = []
            self._collect_focusable_widgets(self, widgets)
            try:
                current_index = widgets.index(current)
                next_index = (current_index + 1) % len(widgets)
                widgets[next_index].focus_set()
            except (ValueError, IndexError):
                pass
    
    def focus_previous_widget(self):
        """Focus the previous focusable widget"""
        current = self.focus_get()
        if current:
            # Try to find previous widget
            widgets = []
            self._collect_focusable_widgets(self, widgets)
            try:
                current_index = widgets.index(current)
                prev_index = (current_index - 1) % len(widgets)
                widgets[prev_index].focus_set()
            except (ValueError, IndexError):
                pass
    
    def _collect_focusable_widgets(self, widget, widgets_list):
        """Recursively collect focusable widgets"""
        if hasattr(widget, 'focus_set') and widget.winfo_viewable():
            widgets_list.append(widget)
        for child in widget.winfo_children():
            self._collect_focusable_widgets(child, widgets_list)

    def set_current_user(self, username):
        self.current_user = username
        # Current user set
        
        # Update controller manager with current user
        if hasattr(self, 'controller_manager'):
            self.controller_manager.set_current_user(username)
        
        # Load user's fullscreen preference
        self.load_user_fullscreen_preference()
        
        # The menu bar refresh is now handled by the LoginFrame/SwitchuserFrame
        # after a slight delay to ensure current_user is propagated.
        # So, we remove the direct call here to avoid double-triggering or race conditions.
        # if hasattr(self, 'menu_bar') and hasattr(self.menu_bar, 'refresh_menu_elements'):
        #    self.menu_bar.refresh_menu_elements()
    
    def load_user_fullscreen_preference(self):
        """Load user's fullscreen preference from their account.json file."""
        if not self.current_user:
            return
            
        try:
            account_file = self.path_manager.get_path("accounts") / self.current_user / "account.json"
            if account_file.exists():
                with open(account_file, 'r') as f:
                    account_data = json.load(f)
                
                # Check if user has a fullscreen preference set (only apply if user has made a choice)
                if 'prefer_fullscreen' in account_data:
                    prefer_fullscreen = account_data['prefer_fullscreen']
                    # Loading fullscreen preference
                    
                    # Apply the preference if it's different from current state
                    if prefer_fullscreen and not self.is_fullscreen:
                        self.after(1000, self.enter_fullscreen)  # Delay to ensure window is ready
                    elif not prefer_fullscreen and self.is_fullscreen:
                        self.after(1000, self.exit_fullscreen)  # Delay to ensure window is ready
                else:
                    # User hasn't set a preference yet, keep current fullscreen state
                    # No fullscreen preference set, keeping current state
                    pass
        except Exception as e:
            # Error loading fullscreen preference
            pass
    
    def save_user_fullscreen_preference(self, prefer_fullscreen):
        """Save user's fullscreen preference to their account.json file."""
        if not self.current_user:
            return
            
        try:
            account_file = self.path_manager.get_path("accounts") / self.current_user / "account.json"
            
            # Load existing account data
            account_data = {}
            if account_file.exists():
                with open(account_file, 'r') as f:
                    account_data = json.load(f)
            
            # Update the fullscreen preference
            account_data['prefer_fullscreen'] = prefer_fullscreen
            
            # Save back to file
            with open(account_file, 'w') as f:
                json.dump(account_data, f, indent=4)
            
            # Saved fullscreen preference
        except Exception as e:
            # Error saving fullscreen preference
            pass
    
    def setup_window_mode(self):
        """Setup initial window mode - start in fullscreen by default."""
        # Always start in fullscreen mode initially
        self.start_fullscreen()
    
    def setup_proper_windowed_mode(self):
        """Setup proper windowed mode with 1280x720 base resolution and multi-monitor support."""
        # Get primary monitor dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Base resolution as requested
        base_width = 1280
        base_height = 720
        
        # Use base resolution, but ensure it fits on the screen
        window_width = min(base_width, screen_width - 100)
        window_height = min(base_height, screen_height - 100)
        
        # If screen is too small, scale down proportionally
        if window_width < base_width or window_height < base_height:
            scale = min(window_width / base_width, window_height / base_height)
            window_width = int(base_width * scale)
            window_height = int(base_height * scale)
        
        # Center the window on the primary monitor
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set the geometry
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Store the windowed size for future reference
        self.windowed_size = (window_width, window_height)
        
        # Set reasonable minimum and maximum sizes
        self.minsize(800, 450)  # Minimum 16:9 aspect ratio
        self.maxsize(screen_width - 50, screen_height - 50)
        
        # Enable window resizing
        self.resizable(True, True)
        
        # Windowed mode set
    
    def _ensure_primary_monitor(self):
        """Ensure the window is positioned on the primary monitor."""
        try:
            # Get primary monitor dimensions
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            # Get current window position
            current_x = self.winfo_x()
            current_y = self.winfo_y()
            current_width = self.winfo_width()
            current_height = self.winfo_height()
            
            # Check if window is outside primary monitor bounds
            # Also check if window is partially off-screen
            if (current_x < 0 or current_x >= screen_width or 
                current_y < 0 or current_y >= screen_height or
                current_x + current_width > screen_width or
                current_y + current_height > screen_height):
                
                # Use default windowed size
                window_width = min(1280, screen_width - 100)
                window_height = min(720, screen_height - 100)
                
                # Center on primary monitor
                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2
                
                # Ensure position is within bounds
                x = max(0, min(x, screen_width - window_width))
                y = max(0, min(y, screen_height - window_height))
                
                self.geometry(f"{window_width}x{window_height}+{x}+{y}")
                # Positioned window on primary monitor
                
        except Exception as e:
            # Error ensuring primary monitor
            pass
    
    def start_fullscreen(self):
        """Start the application in fullscreen mode."""
        self.attributes("-fullscreen", True)
        self.is_fullscreen = True
        # Don't use overrideredirect on Linux - it causes display issues
    
    def start_windowed(self):
        """Start the application in windowed mode."""
        self.attributes("-fullscreen", False)
        self.is_fullscreen = False
        
        # Ensure we're on the primary monitor
        self._ensure_primary_monitor()
        
        self.setup_proper_windowed_mode()
    
    def toggle_fullscreen(self, event=None):
        """Toggle between fullscreen and windowed mode."""
        if self.is_fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()
    
    def enter_fullscreen(self, event=None):
        """Enter fullscreen mode."""
        if not self.is_fullscreen:
            # Save current windowed size
            self.windowed_size = (self.winfo_width(), self.winfo_height())
            
            # Ensure we're on primary monitor before going fullscreen
            self._ensure_primary_monitor()
            
            # Use standard fullscreen mode (works better on Linux)
            self.attributes("-fullscreen", True)
            self.is_fullscreen = True
            
            # Save user's fullscreen preference
            self.save_user_fullscreen_preference(True)
            
            # Force update and delay notification to ensure proper rendering
            self.update_idletasks()
            self.after(200, self.notify_frames_of_resize)
    
    def exit_fullscreen(self, event=None):
        """Exit fullscreen mode."""
        if self.is_fullscreen:
            self.attributes("-fullscreen", False)
            self.is_fullscreen = False
            self.state('normal')
            
            # Force update before repositioning
            self.update_idletasks()
            
            # Ensure we're on the primary monitor
            self._ensure_primary_monitor()
            
            # Save user's fullscreen preference
            self.save_user_fullscreen_preference(False)
            
            # Set proper windowed size and position
            self.setup_proper_windowed_mode()
            
            # Force update and delay notification to ensure proper rendering
            self.update_idletasks()
            self.after(100, self.notify_frames_of_resize)
    
    def on_window_configure(self, event):
        """Handle window resize events for responsive design."""
        # Only handle main window resize events, not child widget events
        if event.widget == self:
            # Update responsive manager with new window size
            if hasattr(self, 'responsive_manager'):
                self.responsive_manager.update_window_size(event.width, event.height)
            
            # Notify all frames of the resize with a small delay to prevent excessive updates
            self.after_idle(self.notify_frames_of_resize)
    
    def notify_frames_of_resize(self, event=None):
        """Notify all frames that they need to update their layout."""
        for frame_name, frame in self.frames.items():
            if hasattr(frame, 'force_redraw'):
                frame.force_redraw()
            elif hasattr(frame, 'on_visibility_change'):
                # Check if the method requires an event parameter
                import inspect
                try:
                    sig = inspect.signature(frame.on_visibility_change)
                    # Check if there are parameters beyond 'self' (like 'event')
                    param_names = list(sig.parameters.keys())
                    if len(param_names) > 1:  # More than just 'self'
                        frame.on_visibility_change(event)
                    else:
                        frame.on_visibility_change()
                except (ValueError, TypeError):
                    # If signature inspection fails, try calling with event
                    try:
                        frame.on_visibility_change(event)
                    except TypeError:
                        # If that fails, try without event
                        try:
                            frame.on_visibility_change()
                        except Exception:
                            pass

if __name__ == "__main__":
    app = App()
    app.mainloop()

