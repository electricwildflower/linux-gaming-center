import tkinter as tk
from tkinter import ttk

# Import the new configuration section frames
from data.frames.display import DisplayFrame
from data.frames.plugins_config import PluginsConfigFrame
from data.frames.dashboard_config import DashboardConfigFrame
# ControllersConfigFrame removed - moved to user account settings
from data.frames.appsettings_config import AppSettingsConfigFrame
from data.frames.networking import NetworkingFrame
from data.frames.accounts import AccountsFrame
from data.frames.roms import RomsFrame
from data.frames.backups import BackupsFrame # Already imported
from data.frames.bios import BiosFrame
from data.frames.directories_frame import DirectoriesFrame # Already imported
from data.frames.themes import ThemesFrame
from data.frames.libraries_config import LibrariesConfigFrame
from data.frames.about_app import AboutAppFrame

from paths import PathManager # Ensure PathManager is imported if needed for type hinting

class AdminPanelFrame(tk.Frame):
    def __init__(self, parent, controller, path_manager: PathManager): # ADDED: path_manager argument with type hint
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.path_manager = path_manager # STORED: path_manager as an instance variable
        self.configure(bg="#1e1e1e") # Dark background for the main config dashboard

        # Configure grid for two columns: menu on left, content on right
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Menu column, fixed width
        self.grid_columnconfigure(1, weight=1) # Content column, expands

        # --- Left Menu Panel ---
        self.menu_panel = tk.Frame(self, bg="#282c34", width=200) # Darker background for menu
        self.menu_panel.pack_propagate(False) # Prevent menu_panel from resizing to its contents
        self.menu_panel.grid(row=0, column=0, sticky="nsew")

        # Title for the menu
        menu_title = ttk.Label(self.menu_panel, text="Configuration", font=("Arial", 14, "bold"),
                                 foreground="white", background="#282c34", anchor="w")
        menu_title.pack(pady=(20, 10), padx=15, fill="x")

        # --- Content Area (Right Panel) ---
        self.content_panel = tk.Frame(self, bg="#1e1e1e") # Main content area background
        self.content_panel.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # ADDED: Configure the content_panel's internal grid to expand
        self.content_panel.grid_rowconfigure(0, weight=1)
        self.content_panel.grid_columnconfigure(0, weight=1)

        # Dictionary to hold the instances of sub-frames
        self.frames = {}
        self.current_sub_frame = None

        # Define the menu items and their corresponding frame classes
        self.menu_items = {
            "Display": DisplayFrame,
            "Plugins": PluginsConfigFrame,
            "Dashboard": DashboardConfigFrame,
            "App Settings": AppSettingsConfigFrame,
            "Backups": BackupsFrame, # This frame will need path_manager
            "Networking": NetworkingFrame,
            "Accounts": AccountsFrame, # This frame might need path_manager for account files
            "Roms": RomsFrame, # This frame will need path_manager
            "Bios": BiosFrame, # This frame will need path_manager
            "Directories": DirectoriesFrame, # This frame already gets path_manager
            "Themes": ThemesFrame, # This frame might need path_manager for theme files
            "Libraries": LibrariesConfigFrame,
            "About App": AboutAppFrame,
        }

        # Create and pack menu buttons
        for text, FrameClass in self.menu_items.items():
            # Instantiate each sub-frame and store it
            # MODIFIED: Pass path_manager to frames that need it
            # AppSettingsConfigFrame and AboutAppFrame also needs path_manager now
            if text in ["Directories", "Backups", "Accounts", "Roms", "Bios", "Themes", "App Settings", "About App"]: # ADDED "About App"
                frame_instance = FrameClass(self.content_panel, self.controller, self.path_manager)
            else:
                frame_instance = FrameClass(self.content_panel, self.controller)

            frame_instance.grid(row=0, column=0, sticky="nsew") # Place all in the same grid cell
            frame_instance.grid_remove() # Hide them initially
            self.frames[text] = frame_instance

            # Create button for menu
            button = tk.Button(
                self.menu_panel,
                text=text,
                command=lambda t=text: self.show_section(t),
                font=("Arial", 10),
                bg="#282c34", # Button background
                fg="white", # Text color
                activebackground="#4a4f59", # Hover background
                activeforeground="white",
                relief="flat",
                anchor="w",
                padx=15,
                pady=10,
                bd=0,
                highlightthickness=0
            )
            button.pack(fill="x", pady=2, padx=10)
            button.bind("<Enter>", lambda e, b=button: b.config(bg="#3e4451")) # Hover effect
            button.bind("<Leave>", lambda e, b=button: b.config(bg="#282c34")) # Leave effect

        # Show the first section by default
        if self.menu_items:
            first_item_text = list(self.menu_items.keys())[0]
            self.show_section(first_item_text)

    def show_section(self, section_name):
        """
        Hides the current sub-frame and shows the selected one.
        """
        if self.current_sub_frame:
            self.current_sub_frame.grid_remove() # Hide previous frame

        new_sub_frame = self.frames.get(section_name)
        if new_sub_frame:
            new_sub_frame.grid() # Show the new frame
            self.current_sub_frame = new_sub_frame
            # Call on_show_frame if it exists on the sub-frame
            if hasattr(new_sub_frame, 'on_show_frame') and callable(new_sub_frame.on_show_frame):
                new_sub_frame.on_show_frame()
            elif hasattr(new_sub_frame, 'on_visibility_change') and callable(new_sub_frame.on_visibility_change):
                new_sub_frame.on_visibility_change(event=None) # Pass dummy event

    def on_show_frame(self):
        """
        This method will be called when the AdminPanelFrame itself is brought to the front.
        It ensures the correct sub-section is displayed.
        """
        print("Admin Panel Frame is now visible.")
        # Ensure the currently active sub-frame is visible when the dashboard is shown
        if self.current_sub_frame:
            self.current_sub_frame.grid()
            if hasattr(self.current_sub_frame, 'on_show_frame') and callable(self.current_sub_frame.on_show_frame):
                self.current_sub_frame.on_show_frame()
            elif hasattr(self.current_sub_frame, 'on_visibility_change') and callable(self.current_sub_frame.on_visibility_change):
                self.current_sub_frame.on_visibility_change(event=None)

    def on_visibility_change(self, event=None):
        """
        This method can be used if you need to react to actual visibility events,
        though on_show_frame is often sufficient for initial display.
        """
        if self.winfo_ismapped():
            self.on_show_frame()
        else:
            print("Admin Panel Frame is now hidden.")

