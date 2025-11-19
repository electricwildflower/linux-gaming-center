import tkinter as tk
from tkinter import ttk, BooleanVar, Checkbutton, messagebox
from PIL import Image, ImageDraw
try:
    from PIL import ImageTk
except ImportError:
    # Fallback for systems where ImageTk is not available
    import tkinter as tk
    class ImageTk:
        @staticmethod
        def PhotoImage(image):
            # Simple fallback - this won't work perfectly but prevents crashes
            return tk.PhotoImage()
import json
import os
import datetime
from pathlib import Path
from theme import get_theme_manager

class DashboardFrame(ttk.Frame):
    def __init__(self, parent, controller, shown_welcome_users):
        super().__init__(parent)
        self.controller = controller
        self.current_user_id = None
        self.shown_welcome_users = shown_welcome_users  # Track which users saw the welcome popup in this session
        
        # Get responsive manager from controller
        self.responsive_manager = getattr(controller, 'responsive_manager', None)
        
        # Initialize theme manager
        self.theme_manager = get_theme_manager()
        self.theme = self.theme_manager.load_theme("dashboard")
        
        # Get colors from theme
        colors = self.theme.get("colors", {})
        self.bg_color = colors.get("primary_background", "#1a1a1a")
        self.configure(style="Dashboard.TFrame")

        style = ttk.Style()
        style.configure("Dashboard.TFrame", background=self.bg_color)
        style.configure("DashboardInner.TFrame", background=self.bg_color)
        
        # Style for individual recent item frames - background for the frame itself
        # This frame will now primarily hold the image button and a separate text label below it.
        style.configure("RecentItem.TFrame", background=self.bg_color) # Use background color for the container frame
        
        # Style for the image label (which acts as the clickable button)
        button_bg = colors.get("secondary_background", "#2e2e2e")
        style.configure("RecentItemImage.TLabel", background=button_bg,
                        relief="solid", borderwidth=0) # Add border to the image label to make it look like a button
        
        # Style for the text label below the image button
        text_color = colors.get("text_secondary", "#d4d4d4")
        style.configure("RecentItemText.TLabel", background=self.bg_color, # Text label background matches dashboard
                        foreground=text_color, 
                        font=("Arial", 9), anchor="center")
        
        # Style for the main library buttons. The text will now be removed from these.
        # The LibraryButton.TFrame will be the clickable container, and LibraryButton.TLabel will style the image.
        style.configure("LibraryButton.TFrame", background=button_bg,
                        relief="solid", borderwidth=0) # Added border for consistency and visual button feel
        style.configure("LibraryButton.TLabel", background=button_bg)

        # Reduced font size and padding for scroll buttons
        style.configure("ScrollButton.TButton", font=("Arial", 10, "bold"), foreground=text_color, background=button_bg, padding=[5, 5]) # Increased padding for better visibility
        style.map("ScrollButton.TButton",
            background=[('active', '#8e44ad')] # Highlight on hover
        )

        # --- Frame to hold the 4 library buttons ---
        self.button_frame = tk.Frame(self, bg=self.bg_color)
        self.button_frame.pack(pady=(0, 10))
        self.button_frame.grid_columnconfigure(tuple(range(4)), weight=1)

        # --- Define initial button sizes from theme ---
        self.button_width = self.theme.get("button_width", 250)
        self.button_height = self.theme.get("button_height", 150)

        # --- Get icon paths and labels from the theme ---
        icon_paths = self.theme.get("button_icons", [])
        button_labels = self.theme.get("button_labels", [])

        # --- Frame name mapping to match button labels correctly ---
        self.frame_name_mapping = {
            "Open Source Gaming": "OpenSourceGamingFrame",
            "Emulators": "EmulatorsFrame",
            "Windows/Steam/Wine": "SteamFrame",
            "Apps": "AppsFrame"
        }

        self.buttons = []

        # --- Loop to create each button ---
        for i in range(len(button_labels)):
            text = button_labels[i]
            icon_path = icon_paths[i]
            frame_name = self.frame_name_mapping.get(text, "")

            # --- Create a frame for each library button to hold the image ---
            # This frame will act as the clickable button
            library_button_container = ttk.Frame(self.button_frame, style="LibraryButton.TFrame")
            library_button_container.grid(row=0, column=i, padx=8, pady=10, sticky="n")
            library_button_container.grid_propagate(False) # Prevent children from resizing the frame

            # Create an image label inside the container
            # This image label will now fill the entire container as there's no text label
            img_label = ttk.Label(library_button_container, style="LibraryButton.TLabel")
            img_label.pack(side="top", fill="both", expand=True) 

            # Store the container, image label, and other info (text label is removed)
            # The 'text' variable is still kept in the tuple for debugging/logging purposes if needed
            self.buttons.append((library_button_container, img_label, text, icon_path, frame_name))
            
            # Bind click events to open the library
            def create_library_callback(frame_name):
                def library_callback(event):
                    print(f"Library button clicked: {text} -> {frame_name}")
                    if frame_name and hasattr(self.controller, 'show_frame'):
                        self.controller.show_frame(frame_name)
                    else:
                        print(f"Error: Cannot navigate to frame '{frame_name}'")
                return library_callback
            
            # Bind click events to both the container and image label
            library_callback = create_library_callback(frame_name)
            library_button_container.bind("<Button-1>", library_callback)
            img_label.bind("<Button-1>", library_callback)
            
            # Add hover effects to show buttons are clickable
            def on_enter(event):
                library_button_container.config(cursor="hand2")
                img_label.config(cursor="hand2")
            
            def on_leave(event):
                library_button_container.config(cursor="")
                img_label.config(cursor="")
            
            library_button_container.bind("<Enter>", on_enter)
            library_button_container.bind("<Leave>", on_leave)
            img_label.bind("<Enter>", on_enter)
            img_label.bind("<Leave>", on_leave)

        # --- Bind window resizing event to update button sizes and images ---
        self.bind("<Configure>", self.on_resize)

        # --- CRITICAL FIX: Call on_resize immediately after setting up buttons ---
        self.update_idletasks()
        self.on_resize(None)

        # --- Recently Played/Added Sections Container Frame ---
        self.recent_sections_frame = ttk.Frame(self, style="DashboardInner.TFrame")
        self.recent_sections_frame.pack(pady=(10, 10), padx=10, fill="x")
        self.recent_sections_frame.grid_columnconfigure(0, weight=1)


        # --- Recently Played Games Section ---
        # Header frame for title and scroll buttons
        self.recent_games_header_frame = ttk.Frame(self.recent_sections_frame, style="DashboardInner.TFrame")
        self.recent_games_header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.recent_games_header_frame.grid_columnconfigure(0, weight=1) # Label takes most space

        ttk.Label(self.recent_games_header_frame, text="Recently Played Games", style="Dashboard.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        
        # Left scroll button for games header
        self.scroll_left_header_button_games = ttk.Button(
            self.recent_games_header_frame,
            text="◀",
            style="ScrollButton.TButton",
            command=self.scroll_recent_games_left,
            width=3
        )
        self.scroll_left_header_button_games.grid(row=0, column=1, padx=(0, 5), sticky="e")

        # Right scroll button for games header
        self.scroll_right_header_button_games = ttk.Button(
            self.recent_games_header_frame,
            text="▶",
            style="ScrollButton.TButton",
            command=self.scroll_recent_games_right,
            width=3
        )
        self.scroll_right_header_button_games.grid(row=0, column=2, padx=(5, 0), sticky="e")

        # Canvas for horizontal scrolling of recently played games
        self.recently_played_games_canvas = tk.Canvas(
            self.recent_sections_frame,
            bg=self.bg_color,
            highlightthickness=0,
            height=150 # Fixed height for the row of game buttons (includes image and text)
        )
        self.recently_played_games_canvas.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.recently_played_games_frame = ttk.Frame(self.recently_played_games_canvas, style="DashboardInner.TFrame")
        self.recently_played_games_frame_id = self.recently_played_games_canvas.create_window(
            (0, 0), window=self.recently_played_games_frame, anchor="nw"
        )
        
        # Bind canvas resize to update scroll region and inner frame width
        self.recently_played_games_frame.bind(
            "<Configure>",
            lambda e: self.recently_played_games_canvas.configure(
                scrollregion=self.recently_played_games_canvas.bbox("all")
            )
        )
        self.recently_played_games_canvas.bind("<Configure>", self.on_recent_games_canvas_resize)
        self.bind_mousewheel_events_recent_games() # Bind mousewheel specifically to this canvas

        self.recently_played_game_widgets = [] # To store the frames for each game
        self.recently_played_game_icons = [] # To store PhotoImage references


        # --- Recently Added Games Section (No horizontal scroll buttons requested for this) ---
        ttk.Label(self.recent_sections_frame, text="Recently Added Games", style="Dashboard.TLabel").grid(
            row=2, column=0, padx=10, pady=(10, 5), sticky="w"
        )
        self.recently_added_games_buttons = [] # This section still uses simple buttons
        added_games_inner_frame = ttk.Frame(self.recent_sections_frame, style="DashboardInner.TFrame")
        added_games_inner_frame.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        for i in range(15):
            button = ttk.Button(added_games_inner_frame, text="", width=10, style="DashboardButton.TButton")  # Adjust width as needed
            button.grid(row=0, column=i, padx=5, pady=5)
            self.recently_added_games_buttons.append(button)

        # --- Recently Used Apps Section ---
        # Header frame for title and scroll buttons
        self.recent_apps_header_frame = ttk.Frame(self.recent_sections_frame, style="DashboardInner.TFrame")
        self.recent_apps_header_frame.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.recent_apps_header_frame.grid_columnconfigure(0, weight=1) # Label takes most space

        ttk.Label(self.recent_apps_header_frame, text="Recently Used Apps", style="Dashboard.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        
        # Left scroll button for apps header
        self.scroll_left_header_button_apps = ttk.Button(
            self.recent_apps_header_frame,
            text="◀",
            style="ScrollButton.TButton",
            command=self.scroll_recent_apps_left,
            width=3
        )
        self.scroll_left_header_button_apps.grid(row=0, column=1, padx=(0, 5), sticky="e")

        # Right scroll button for apps header
        self.scroll_right_header_button_apps = ttk.Button(
            self.recent_apps_header_frame,
            text="▶",
            style="ScrollButton.TButton",
            command=self.scroll_recent_apps_right,
            width=3
        )
        self.scroll_right_header_button_apps.grid(row=0, column=2, padx=(5, 0), sticky="e")

        # Canvas for horizontal scrolling of recently used apps
        self.recently_used_apps_canvas = tk.Canvas(
            self.recent_sections_frame,
            bg=self.bg_color,
            highlightthickness=0,
            height=150 # Fixed height for the row of app buttons (includes image and text)
        )
        self.recently_used_apps_canvas.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.recently_used_apps_frame = ttk.Frame(self.recently_used_apps_canvas, style="DashboardInner.TFrame")
        self.recently_used_apps_frame_id = self.recently_used_apps_canvas.create_window(
            (0, 0), window=self.recently_used_apps_frame, anchor="nw"
        )

        # Bind canvas resize for apps
        self.recently_used_apps_frame.bind(
            "<Configure>",
            lambda e: self.recently_used_apps_canvas.configure(
                scrollregion=self.recently_used_apps_canvas.bbox("all")
            )
        )
        self.recently_used_apps_canvas.bind("<Configure>", self.on_recent_apps_canvas_resize)
        self.bind_mousewheel_events_recent_apps()

        self.recently_used_app_widgets = []
        self.recently_used_app_icons = []

        # --- Recently Played ROMs Section ---
        # Header frame for title and scroll buttons
        self.recent_roms_header_frame = ttk.Frame(self.recent_sections_frame, style="DashboardInner.TFrame")
        self.recent_roms_header_frame.grid(row=6, column=0, padx=10, pady=(10, 5), sticky="ew")
        self.recent_roms_header_frame.grid_columnconfigure(0, weight=1) # Label takes most space

        ttk.Label(self.recent_roms_header_frame, text="Recently Played ROMs", style="Dashboard.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        
        # Left scroll button for ROMs header
        self.scroll_left_header_button_roms = ttk.Button(
            self.recent_roms_header_frame,
            text="◀",
            style="ScrollButton.TButton",
            command=self.scroll_recent_roms_left,
            width=3
        )
        self.scroll_left_header_button_roms.grid(row=0, column=1, padx=(0, 5), sticky="e")

        # Right scroll button for ROMs header
        self.scroll_right_header_button_roms = ttk.Button(
            self.recent_roms_header_frame,
            text="▶",
            style="ScrollButton.TButton",
            command=self.scroll_recent_roms_right,
            width=3
        )
        self.scroll_right_header_button_roms.grid(row=0, column=2, padx=(5, 0), sticky="e")

        # Canvas for horizontal scrolling of recently played ROMs
        self.recently_played_roms_canvas = tk.Canvas(
            self.recent_sections_frame,
            bg=self.bg_color,
            highlightthickness=0,
            height=150 # Fixed height for the row of ROM buttons
        )
        self.recently_played_roms_canvas.grid(row=7, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.recently_played_roms_frame = ttk.Frame(self.recently_played_roms_canvas, style="DashboardInner.TFrame")
        self.recently_played_roms_frame_id = self.recently_played_roms_canvas.create_window(
            (0, 0), window=self.recently_played_roms_frame, anchor="nw"
        )

        # Bind canvas resize for ROMs
        self.recently_played_roms_frame.bind(
            "<Configure>",
            lambda e: self.recently_played_roms_canvas.configure(
                scrollregion=self.recently_played_roms_canvas.bbox("all")
            )
        )
        self.recently_played_roms_canvas.bind("<Configure>", self.on_recent_roms_canvas_resize)
        self.bind_mousewheel_events_recent_roms()

        self.recently_played_rom_widgets = []
        self.recently_played_rom_icons = [] # No icons needed for ROMs directly as per requirement, but keeping the list for consistency

    def on_show_frame(self):
        """Called when the dashboard frame is shown."""
        self.current_user_id = self.controller.current_user
        if not self.current_user_id:
            print("Error: current_user_id is not set when DashboardFrame is shown.")
            return

        if self.current_user_id in self.shown_welcome_users:
            return

        user_preferences = self.load_user_preferences(self.current_user_id)
        show_welcome_preference = user_preferences.get("show_welcome_message", True)

        account_data = self._load_account_data(self.current_user_id)
        is_first_login = account_data.get("first_login", False)

        if is_first_login or show_welcome_preference:
            self.show_welcome_dialog(self.current_user_id, is_first_login)
            self.shown_welcome_users.add(self.current_user_id)

        if is_first_login:
            self._update_first_login_status(self.current_user_id, False)
        
        self.update_dashboard()

    def _load_account_data(self, user_id):
        """Load user's account data from account.json."""
        # Use PathManager if available, otherwise fallback to hardcoded path
        if hasattr(self.controller, 'path_manager'):
            accounts_path = self.controller.path_manager.get_path("accounts")
            account_file = accounts_path / user_id / "account.json"
        else:
            account_file = Path("data") / "accounts" / user_id / "account.json"
        
        try:
            with open(account_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Account file not found for user {user_id}")
            return {}
        except json.JSONDecodeError:
            print(f"Error: Could not decode account JSON for user {user_id}")
            return {}

    def _update_first_login_status(self, user_id, status):
        """Update the 'first_login' status in the user's account.json."""
        # Use PathManager if available, otherwise fallback to hardcoded path
        if hasattr(self.controller, 'path_manager'):
            accounts_path = self.controller.path_manager.get_path("accounts")
            account_file = accounts_path / user_id / "account.json"
        else:
            account_file = Path("data") / "accounts" / user_id / "account.json"
        
        try:
            with open(account_file, "r+") as f:
                account_data = json.load(f)
                account_data["first_login"] = status
                f.seek(0)
                json.dump(account_data, f, indent=4)
                f.truncate()
        except FileNotFoundError:
            print(f"Error: Account file not found for user {user_id}")
        except json.JSONDecodeError:
            print(f"Error: Could not decode account JSON for user {user_id}")
        except Exception as e:
            print(f"Error updating first_login status: {e}")

    def load_user_preferences(self, user_id):
        """Load user preferences from account.json."""
        # Use PathManager if available, otherwise fallback to hardcoded path
        if hasattr(self.controller, 'path_manager'):
            accounts_path = self.controller.path_manager.get_path("accounts")
            account_file = accounts_path / user_id / "account.json"
        else:
            account_file = Path("data") / "accounts" / user_id / "account.json"
        
        try:
            with open(account_file, "r") as f:
                account_data = json.load(f)
                return {"show_welcome_message": account_data.get("show_welcome_message", True)}
        except FileNotFoundError:
            print(f"Error: Account file not found for user {user_id}")
            return {"show_welcome_message": True}
        except json.JSONDecodeError:
            print(f"Error: Could not decode account JSON for user {user_id}")
            return {"show_welcome_message": True}

    def save_user_preference(self, user_id, key, value):
        """Save user preference to account.json."""
        # Use PathManager if available, otherwise fallback to hardcoded path
        if hasattr(self.controller, 'path_manager'):
            accounts_path = self.controller.path_manager.get_path("accounts")
            account_file = accounts_path / user_id / "account.json"
        else:
            account_file = Path("data") / "accounts" / user_id / "account.json"
        
        try:
            with open(account_file, "r+") as f:
                account_data = json.load(f)
                account_data[key] = value
                f.seek(0)
                json.dump(account_data, f, indent=4)
                f.truncate()
        except FileNotFoundError:
            print(f"Error: Account file not found for user {user_id}")
        except json.JSONDecodeError:
            print(f"Error: Could not decode account JSON for user {user_id}")
        except Exception as e:
            print(f"Error saving user preference: {e}")

    def show_welcome_dialog(self, user_id, is_first_login):
        """Display the welcome dialog with a purple, black, and grey look with a logo."""
        dialog = tk.Toplevel(self)
        dialog.title("Welcome to the App!")
        dialog.configure(bg="#1a1a1a")

        dialog_width = 900
        dialog_height = 600
        dialog.geometry(f"{dialog_width}x{dialog_height}")

        style = ttk.Style()
        dialog_bg = "#2e2e2e"
        text_color = "#d4d4d4"
        accent_color = "#8e44ad"

        style.configure("Welcome.TLabel", background=dialog_bg, foreground=text_color, font=("Arial", 12), anchor='w')
        style.configure("Welcome.TCheckbutton", background=dialog_bg, foreground=text_color, font=("Arial", 10))
        style.configure("Welcome.TFrame", background=dialog_bg)
        style.configure("WelcomeButton.TButton", background=accent_color, foreground="black", font=("Arial", 10, "bold"))

        main_frame = ttk.Frame(dialog, style="Welcome.TFrame", padding=(20, 20))
        main_frame.pack(fill="both", expand=True)

        # Use app installation directory for theme files
        if hasattr(self.controller, 'app_installation_dir'):
            logo_path = self.controller.app_installation_dir / "data" / "themes" / "cosmictwilight" / "images" / "linuxgamingcenterdialogue.png"
        else:
            logo_path = Path("data") / "themes" / "cosmictwilight" / "images" / "linuxgamingcenterdialogue.png"
        
        try:
            logo_img = Image.open(logo_path)
            logo_size = int(dialog_height * 0.4)
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(main_frame, image=self.logo_photo, style="Welcome.TLabel", background=dialog_bg)
            logo_label.grid(row=0, column=1, rowspan=2, padx=(120, 0), sticky='nse')
        except FileNotFoundError:
            print(f"Error: Logo image not found at {logo_path}")
            logo_label = ttk.Label(main_frame, text="Logo Not Found", style="Welcome.TLabel", background=dialog_bg)
            logo_label.grid(row=0, column=1, padx=(20, 0), sticky='ne')

        welcome_text = "Welcome to Linux Gaming Center!\n\n"
        if is_first_login:
            welcome_text += "Get ready to explore a powerful hub for all your gaming adventures on Linux! Whether you're into open-source classics, retro emulators, modern PC titles or even your favourite apps, we've got you covered.:\n\n"
        welcome_text += "- Browse and launch your favorite games, emulators & apps from a sleek, customizable library.\n\n"
        welcome_text += "- Install and manage emulators, open-source games, Steam/Wine titles and your favourite Linux/media apps.\n\n"
        welcome_text += "- Access the Store to discover new games, apps, emulators and community plugins (coming soon!)!\n\n"
        welcome_text += "- Visit the menu bar to configure your controllers and other such settings!\n\n"
        welcome_text += "- VERSION 1.0 BETA! \n\n"
        welcome_text += "- Python 3.0!\n\n"
        welcome_text += "- Electricwildflower creation!\n\n"

        message_label = ttk.Label(main_frame, text=welcome_text, style="Welcome.TLabel", wraplength=dialog_width * 0.5)
        message_label.grid(row=0, column=0, sticky='nwsw', pady=(0, 10))

        control_frame = ttk.Frame(main_frame, style="Welcome.TFrame")
        control_frame.grid(row=1, column=0, sticky='sw', pady=(10, 0))

        self.show_welcome_var = tk.BooleanVar()
        user_preferences = self.load_user_preferences(user_id)
        self.show_welcome_var.set(not user_preferences.get("show_welcome_message", True))
        dont_show_again_check = ttk.Checkbutton(
            control_frame,
            text="Don't show this message again",
            variable=self.show_welcome_var,
            style="Welcome.TCheckbutton"
        )
        dont_show_again_check.pack(side="left", padx=(0, 10))

        close_button = ttk.Button(
            control_frame,
            text="Close",
            command=self._on_close_welcome_dialog(dialog, user_id),
            style="WelcomeButton.TButton"
        )
        close_button.pack(side="left")

        dialog.protocol("WM_DELETE_WINDOW", self._on_close_welcome_dialog(dialog, user_id))

        dialog.transient(self.controller)
        dialog.grab_set()
        dialog.wait_window(dialog)

    def _on_close_welcome_dialog(self, dialog, user_id):
        """Handler for when the welcome dialog is closed."""
        def close_handler():
            self.save_user_preference(user_id, "show_welcome_message", not self.show_welcome_var.get())
            dialog.destroy()
        return close_handler

    def force_redraw(self):
        """Force a complete redraw of the dashboard."""
        try:
            if self.winfo_width() < 10:
                return

            window_width = self.winfo_width()
            
            # Use responsive manager if available
            if self.responsive_manager:
                # Get base dimensions from responsive manager (250x150)
                base_button_width = self.responsive_manager.get_dimension('button_width')
                base_button_height = self.responsive_manager.get_dimension('button_height')
                padding = self.responsive_manager.get_dimension('button_padding')
                
                # Use the base dimensions directly (250x150) and apply scaling
                scale = self.responsive_manager.scale
                button_width = int(base_button_width * scale)
                button_height = int(base_button_height * scale)
                
            else:
                # Fallback to fixed dimensions
                button_width = 250
                button_height = 150

            # Image will now take up the full height of the button container
            image_height = button_height 

            # Update the tuple unpacking to match the new structure (no text_label)
            for idx, (container_frame, img_label, text, icon_path, frame_name) in enumerate(self.buttons):
                self._update_button_layout(idx, container_frame, img_label, text, icon_path, frame_name, 
                                         button_width, button_height, image_height, window_width)
            
            # Update recent items layout
            self._update_recent_items_layout(window_width)
            
            # Force update
            self.update_idletasks()
            self.update()
            
        except Exception as e:
            print(f"Error in dashboard force_redraw: {e}")

    def on_resize(self, event=None):
        """Handle resize events."""
        # Call force_redraw with a small delay to prevent excessive updates
        self.after(50, self.force_redraw)
    
    def _update_button_layout(self, idx, container_frame, img_label, text, icon_path, frame_name, 
                            button_width, button_height, image_height, window_width):
        """Update the layout of a single button."""
        try:
            # Configure the container frame size
            container_frame.config(width=button_width, height=button_height)

            # Load and resize image to cover the entire button area (like CSS object-fit: cover)
            if os.path.exists(icon_path):
                icon_img = Image.open(icon_path)
                # Ensure we have the exact button dimensions
                icon_img = self.resize_image_cover(icon_img, button_width, button_height)
                photo = ImageTk.PhotoImage(icon_img)
                img_label.config(image=photo)
                img_label.image = photo
                # Ensure the image label fills the container
                img_label.pack(side="top", fill="both", expand=True)
            else:
                # Create a placeholder image if the icon is not found
                placeholder_img = Image.new('RGB', (button_width, button_height), color='grey')
                d = ImageDraw.Draw(placeholder_img)
                d.text((10, button_height // 2 - 5), "No Icon", fill=(255, 255, 255))
                photo = ImageTk.PhotoImage(placeholder_img)
                img_label.config(image=photo)
                img_label.image = photo
                # Ensure the image label fills the container
                img_label.pack(side="top", fill="both", expand=True)

        except Exception as e:
            print(f"Error updating button layout {idx} ({text}): {e}")
    
    def _update_recent_items_layout(self, window_width):
        """Update the layout of recent items."""
        try:
            # Update recent items if they exist
            if hasattr(self, 'recent_items_frame') and self.recent_items_frame:
                # Recalculate layout for recent items
                self.load_recently_played_apps()
        except Exception as e:
            print(f"Error updating recent items layout: {e}")

    def resize_image_cover(self, img, target_width, target_height):
        """Resize image to cover target dimensions while maintaining aspect ratio (like CSS object-fit: cover)."""
        if target_width <= 0 or target_height <= 0:
            return img # Return original if target dimensions are invalid

        img_ratio = img.width / img.height
        target_ratio = target_width / target_height

        # Calculate scale factor to cover the entire target area
        if target_ratio > img_ratio:
            # Target is wider, so match width and scale height (may crop height)
            scale_factor = target_width / img.width
        else:
            # Target is taller, so match height and scale width (may crop width)
            scale_factor = target_height / img.height

        # Calculate new dimensions
        new_width = int(img.width * scale_factor)
        new_height = int(img.height * scale_factor)

        # Resize the image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Calculate crop box to center the image
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height

        # Ensure crop box coordinates are valid
        left = max(0, left)
        top = max(0, top)
        right = min(new_width, right)
        bottom = min(new_height, bottom)

        # Crop the image to target dimensions
        if right - left > 0 and bottom - top > 0:
            img = img.crop((left, top, right, bottom))
        else:
            # Fallback: create a solid color image
            img = Image.new('RGB', (target_width, target_height), color='#2e2e2e')
        
        return img

    def load_recent_data(self):
        self.load_recently_played_games()
        self.load_recently_added_games()
        self.load_recently_played_apps()
        self.load_recently_played_roms()

    def load_recently_played_games(self):
        for widget in self.recently_played_game_widgets:
            widget.destroy()
        self.recently_played_game_widgets = []
        self.recently_played_game_icons = []

        all_recent_games = []

        open_source_gaming_frame = None
        if "OpenSourceGamingFrame" in self.controller.frames and self.controller.frames["OpenSourceGamingFrame"]:
            open_source_gaming_frame = self.controller.frames["OpenSourceGamingFrame"]
            if hasattr(open_source_gaming_frame, 'get_recently_played_games'):
                open_source_recent_games = open_source_gaming_frame.get_recently_played_games(num_items=15)
                for game in open_source_recent_games:
                    game['source_frame'] = 'OpenSourceGamingFrame'
                all_recent_games.extend(open_source_recent_games)
        windows_steam_wine_frame = None
        if "SteamFrame" in self.controller.frames and self.controller.frames["SteamFrame"]:
            windows_steam_wine_frame = self.controller.frames["SteamFrame"]
            if hasattr(windows_steam_wine_frame, 'get_recently_played_games'):
                windows_steam_recent_games = windows_steam_wine_frame.get_recently_played_games(num_items=15)
                for game in windows_steam_recent_games:
                    game['source_frame'] = 'SteamFrame'
                all_recent_games.extend(windows_steam_recent_games)

        for game in all_recent_games:
            if "last_played" in game and isinstance(game["last_played"], str):
                try:
                    game["last_played_dt"] = datetime.datetime.fromisoformat(game["last_played"])
                except ValueError:
                    game["last_played_dt"] = datetime.datetime.min
            else:
                game["last_played_dt"] = datetime.datetime.min

        all_recent_games.sort(key=lambda x: x["last_played_dt"], reverse=True)
        
        final_recent_games = all_recent_games[:15]

        # Define target dimensions for the recent game buttons
        RECENT_ITEM_BUTTON_WIDTH = 160 # This is the width of the entire item (image + text)
        RECENT_ITEM_BUTTON_HEIGHT = 150 # Increased height to accommodate image and text
        IMAGE_ONLY_HEIGHT = 110 # Height for the image part (the clickable area)
        TEXT_DISPLAY_HEIGHT = 40 # Height for the text part below the image

        if not final_recent_games:
            # Ensure the frame is still sized correctly even if empty
            self.recently_played_games_canvas.itemconfig(
                self.recently_played_games_frame_id,
                width=self.recently_played_games_canvas.winfo_width()
            )
            self.recently_played_games_canvas.config(scrollregion=self.recently_played_games_canvas.bbox("all"))
            return

        for i, game in enumerate(final_recent_games):
            try:
                # Create a container frame for the image button and the text label below it
                item_container_frame = ttk.Frame(self.recently_played_games_frame, style="RecentItem.TFrame")
                item_container_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
                item_container_frame.grid_propagate(False)
                item_container_frame.config(width=RECENT_ITEM_BUTTON_WIDTH, height=RECENT_ITEM_BUTTON_HEIGHT)

                # Create the image label (which acts as the button)
                image_button_label = ttk.Label(item_container_frame, style="RecentItemImage.TLabel")
                image_button_label.pack(side="top", fill="both", expand=False, ipady=0) # Image fills top part, fixed height

                # Load and resize image to fill and crop the image_button_label area
                image_path = game.get("image")
                if not image_path or not os.path.exists(image_path):
                    print(f"WARNING: Image not found for game: {game.get('name', 'Unknown')}, path: {image_path}. Using placeholder.")
                    img = Image.new('RGB', (RECENT_ITEM_BUTTON_WIDTH, IMAGE_ONLY_HEIGHT), color = 'grey')
                    d = ImageDraw.Draw(img)
                    d.text((10, IMAGE_ONLY_HEIGHT // 2 - 5), "No Image", fill=(255,255,255))
                else:
                    img = Image.open(image_path)
                
                # Resize image to fill and crop for the image display height
                img = self.resize_image_to_fill_and_crop(img, RECENT_ITEM_BUTTON_WIDTH, IMAGE_ONLY_HEIGHT)
                photo = ImageTk.PhotoImage(img)
                self.recently_played_game_icons.append(photo) # Keep reference

                image_button_label.config(image=photo)

                # Create the text label below the image button
                text_label = ttk.Label(
                    item_container_frame,
                    text=game["name"],
                    style="RecentItemText.TLabel", # Use new style for text below image
                    wraplength=RECENT_ITEM_BUTTON_WIDTH - 10,
                    justify="center"
                )
                text_label.pack(side="bottom", fill="x", pady=(2, 2)) # Text fills bottom part

                def run_game_callback(event, item_data=game):
                    
                    if item_data.get('source_frame') == 'OpenSourceGamingFrame' and open_source_gaming_frame:
                        open_source_gaming_frame.run_game(item_data["exec"])
                    elif item_data.get('source_frame') == 'SteamFrame' and windows_steam_wine_frame:
                        windows_steam_wine_frame.run_game(item_data["exec"])
                    else:
                        messagebox.showerror("Launch Error", f"Could not determine origin frame for game: {item_data['name']}")
                    self.update_dashboard()

                # Bind click events to both the image label and the text label
                image_button_label.bind("<Button-1>", run_game_callback)
                text_label.bind("<Button-1>", run_game_callback)
                item_container_frame.bind("<Button-1>", run_game_callback) # Also bind to the container frame

                self.recently_played_game_widgets.append(item_container_frame)

            except Exception as e:
                print(f"Error loading recently played game icon for {game.get('name', 'Unknown')}: {e}")

        total_content_width = len(final_recent_games) * (RECENT_ITEM_BUTTON_WIDTH + 10) # 10 for padx on each side
        
        self.recently_played_games_canvas.itemconfig(
            self.recently_played_games_frame_id,
            width=total_content_width if total_content_width > self.recently_played_games_canvas.winfo_width() else self.recently_played_games_canvas.winfo_width()
        )
        self.recently_played_games_canvas.update_idletasks()
        self.recently_played_games_canvas.config(
            scrollregion=self.recently_played_games_canvas.bbox("all")
        )
    
    def on_recent_games_canvas_resize(self, event):
        """Update the inner frame width when the canvas resizes."""
        inner_frame_width = self.recently_played_games_frame.winfo_reqwidth()
        canvas_width = self.recently_played_games_canvas.winfo_width()
        
        self.recently_played_games_canvas.itemconfig(
            self.recently_played_games_frame_id, 
            width=max(inner_frame_width, canvas_width)
        )
        self.recently_played_games_canvas.config(scrollregion=self.recently_played_games_canvas.bbox("all"))

    def scroll_recent_games_left(self):
        """Scroll the recently played games canvas to the left."""
        self.recently_played_games_canvas.xview_scroll(-1, "units")

    def scroll_recent_games_right(self):
        """Scroll the recently played games canvas to the right."""
        self.recently_played_games_canvas.xview_scroll(1, "units")

    def bind_mousewheel_events_recent_games(self):
        """Bind mouse wheel events for the recently played games canvas."""
        # Bind directly to the canvas, not bind_all
        self.recently_played_games_canvas.bind("<MouseWheel>", self.on_mousewheel_recent_games)
        self.recently_played_games_canvas.bind("<Button-4>", lambda e: self.on_mousewheel_recent_games_scroll(-1))
        self.recently_played_games_canvas.bind("<Button-5>", lambda e: self.on_mousewheel_recent_games_scroll(1))
        self.recently_played_games_canvas.bind("<Enter>", lambda e: self.recently_played_games_canvas.focus_set())
        self.recently_played_games_canvas.bind("<Leave>", lambda e: self.focus_set()) # Remove focus when mouse leaves

    def on_mousewheel_recent_games(self, event):
        """Handle mouse wheel scrolling for the recently played games canvas on Windows/Mac."""
        self.recently_played_games_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_recent_games_scroll(self, direction):
        """Handle mouse wheel scrolling for the recently played games canvas on Linux."""
        self.recently_played_games_canvas.xview_scroll(direction, "units")

    def load_recently_added_games(self):
        # Placeholder for recently added games logic
        # This section remains unchanged as per user request
        if "OpenSourceGamingFrame" in self.controller.frames and self.controller.frames["OpenSourceGamingFrame"]:
            open_source_gaming_frame = self.controller.frames["OpenSourceGamingFrame"]
            if hasattr(open_source_gaming_frame, 'get_recently_added_games'):
                recent_added_games = open_source_gaming_frame.get_recently_added_games()
                for i, game in enumerate(recent_added_games):
                    if i < 15:
                        self.recently_added_games_buttons[i].config(text=game.get("name", ""))
                    else:
                        break
                for i in range(len(recent_added_games), 15):
                    self.recently_added_games_buttons[i].config(text="")
            else:
                print("Open Source Gaming Frame does not have get_recently_added_games method.")
        else:
            print("Open Source Gaming Frame not loaded in controller yet.")

    def load_recently_played_apps(self):
        for widget in self.recently_used_app_widgets:
            widget.destroy()
        self.recently_used_app_widgets = []
        self.recently_used_app_icons = []

        recent_apps = []
        apps_frame = None
        if "AppsFrame" in self.controller.frames and self.controller.frames["AppsFrame"]:
            apps_frame = self.controller.frames["AppsFrame"]
            if hasattr(apps_frame, 'get_recently_played_apps'):
                recent_apps = apps_frame.get_recently_played_apps(num_items=15)

        for app in recent_apps:
            if "last_played" in app and isinstance(app["last_played"], str):
                try:
                    app["last_played_dt"] = datetime.datetime.fromisoformat(app["last_played"])
                except ValueError:
                    app["last_played_dt"] = datetime.datetime.min
            else:
                app["last_played_dt"] = datetime.datetime.min
        
        recent_apps.sort(key=lambda x: x["last_played_dt"], reverse=True)

        RECENT_ITEM_BUTTON_WIDTH = 160
        RECENT_ITEM_BUTTON_HEIGHT = 150 # Increased height to accommodate image and text
        IMAGE_ONLY_HEIGHT = 110 # Height for the image part (the clickable area)
        TEXT_DISPLAY_HEIGHT = 40 # Height for the text part below the image

        if not recent_apps:
            self.recently_used_apps_canvas.itemconfig(
                self.recently_used_apps_frame_id,
                width=self.recently_used_apps_canvas.winfo_width()
            )
            self.recently_used_apps_canvas.config(scrollregion=self.recently_used_apps_canvas.bbox("all"))
            return

        for i, app in enumerate(recent_apps):
            try:
                # Create a container frame for the image button and the text label below it
                item_container_frame = ttk.Frame(self.recently_used_apps_frame, style="RecentItem.TFrame")
                item_container_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
                item_container_frame.grid_propagate(False)
                item_container_frame.config(width=RECENT_ITEM_BUTTON_WIDTH, height=RECENT_ITEM_BUTTON_HEIGHT)

                # Create the image label (which acts as the button)
                image_button_label = ttk.Label(item_container_frame, style="RecentItemImage.TLabel")
                image_button_label.pack(side="top", fill="both", expand=False, ipady=0) # Image fills top part, fixed height

                image_path = app.get("image")
                if not image_path or not os.path.exists(image_path):
                    print(f"WARNING: Image not found for app: {app.get('name', 'Unknown')}, path: {image_path}. Using placeholder.")
                    img = Image.new('RGB', (RECENT_ITEM_BUTTON_WIDTH, IMAGE_ONLY_HEIGHT), color = 'grey')
                    d = ImageDraw.Draw(img)
                    d.text((10, IMAGE_ONLY_HEIGHT // 2 - 5), "No Image", fill=(255,255,255))
                else:
                    img = Image.open(image_path)
                
                # Resize image to fill and crop for the image display height
                img = self.resize_image_to_fill_and_crop(img, RECENT_ITEM_BUTTON_WIDTH, IMAGE_ONLY_HEIGHT)
                photo = ImageTk.PhotoImage(img)
                self.recently_used_app_icons.append(photo) # Keep reference

                image_button_label.config(image=photo)

                # Create the text label below the image button
                text_label = ttk.Label(
                    item_container_frame,
                    text=app["name"],
                    style="RecentItemText.TLabel", # Use new style for text below image
                    wraplength=RECENT_ITEM_BUTTON_WIDTH - 10,
                    justify="center"
                )
                text_label.pack(side="bottom", fill="x", pady=(2, 2)) # Text fills bottom part

                def run_app_callback(event, item_data=app):
                    if apps_frame:
                        apps_frame.run_app(item_data["exec"])
                    else:
                        messagebox.showerror("Launch Error", f"AppsFrame not available to run app: {item_data['name']}")
                    self.update_dashboard()

                # Bind click events to both the image label and the text label
                image_button_label.bind("<Button-1>", run_app_callback)
                text_label.bind("<Button-1>", run_app_callback)
                item_container_frame.bind("<Button-1>", run_app_callback) # Also bind to the container frame

                self.recently_used_app_widgets.append(item_container_frame)

            except Exception as e:
                print(f"Error loading recently used app icon for {app.get('name', 'Unknown')}: {e}")

        total_content_width = len(recent_apps) * (RECENT_ITEM_BUTTON_WIDTH + 10)
        self.recently_used_apps_canvas.itemconfig(
            self.recently_used_apps_frame_id,
            width=total_content_width if total_content_width > self.recently_used_apps_canvas.winfo_width() else self.recently_used_apps_canvas.winfo_width()
        )
        self.recently_used_apps_canvas.update_idletasks()
        self.recently_used_apps_canvas.config(
            scrollregion=self.recently_used_apps_canvas.bbox("all")
        )

    def on_recent_apps_canvas_resize(self, event):
        """Update the inner frame width when the apps canvas resizes."""
        inner_frame_width = self.recently_used_apps_frame.winfo_reqwidth()
        canvas_width = self.recently_used_apps_canvas.winfo_width()
        
        self.recently_used_apps_canvas.itemconfig(
            self.recently_used_apps_frame_id, 
            width=max(inner_frame_width, canvas_width)
        )
        self.recently_used_apps_canvas.config(scrollregion=self.recently_used_apps_canvas.bbox("all"))

    def scroll_recent_apps_left(self):
        """Scroll the recently used apps canvas to the left."""
        self.recently_used_apps_canvas.xview_scroll(-1, "units")

    def scroll_recent_apps_right(self):
        """Scroll the recently used apps canvas to the right."""
        self.recently_used_apps_canvas.xview_scroll(1, "units")

    def bind_mousewheel_events_recent_apps(self):
        """Bind mouse wheel events for the recently used apps canvas."""
        self.recently_used_apps_canvas.bind("<MouseWheel>", self.on_mousewheel_recent_apps)
        self.recently_used_apps_canvas.bind("<Button-4>", lambda e: self.on_mousewheel_recent_apps_scroll(-1))
        self.recently_used_apps_canvas.bind("<Button-5>", lambda e: self.on_mousewheel_recent_apps_scroll(1))
        self.recently_used_apps_canvas.bind("<Enter>", lambda e: self.recently_used_apps_canvas.focus_set())
        self.recently_used_apps_canvas.bind("<Leave>", lambda e: self.focus_set())

    def on_mousewheel_recent_apps(self, event):
        """Handle mouse wheel scrolling for the recently used apps canvas on Windows/Mac."""
        self.recently_used_apps_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_recent_apps_scroll(self, direction):
        """Handle mouse wheel scrolling for the recently used apps canvas on Linux."""
        self.recently_used_apps_canvas.xview_scroll(direction, "units")


    def load_recently_played_roms(self):
        for widget in self.recently_played_rom_widgets:
            widget.destroy()
        self.recently_played_rom_widgets = []
        self.recently_played_rom_icons = []

        emulators_frame = None
        all_recent_roms = []

        if "EmulatorsFrame" in self.controller.frames and self.controller.frames["EmulatorsFrame"]:
            emulators_frame = self.controller.frames["EmulatorsFrame"]
            if hasattr(emulators_frame, 'get_recently_played_emulators'):
                all_recent_roms = emulators_frame.get_recently_played_emulators(num_items=15)

        for rom_data in all_recent_roms:
            if "last_played" in rom_data and isinstance(rom_data["last_played"], str):
                try:
                    rom_data["last_played"] = datetime.datetime.fromisoformat(rom_data["last_played"])
                except ValueError:
                    rom_data["last_played"] = datetime.datetime.min

        all_recent_roms.sort(key=lambda x: x["last_played"], reverse=True)

        RECENT_ITEM_BUTTON_WIDTH = 160
        RECENT_ITEM_BUTTON_HEIGHT = 110
        # No image for ROMs, so text will fill the whole button area

        if not all_recent_roms:
            self.recently_played_roms_canvas.itemconfig(
                self.recently_played_roms_frame_id,
                width=self.recently_played_roms_canvas.winfo_width()
            )
            self.recently_played_roms_canvas.config(scrollregion=self.recently_played_roms_canvas.bbox("all"))
            return

        for i, rom_data in enumerate(all_recent_roms):
            try:
                rom_frame = ttk.Frame(self.recently_played_roms_frame, style="RecentItem.TFrame", relief="solid", borderwidth=0)
                rom_frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
                rom_frame.grid_propagate(False)
                rom_frame.config(width=RECENT_ITEM_BUTTON_WIDTH, height=RECENT_ITEM_BUTTON_HEIGHT)

                # For ROMs, the text label will fill the entire frame since there's no image
                text_label = ttk.Label(
                    rom_frame,
                    text=rom_data["name"],
                    style="RecentItemText.TLabel", # Changed to RecentItemText.TLabel for consistency
                    wraplength=RECENT_ITEM_BUTTON_WIDTH - 10,
                    justify="center"
                )
                text_label.pack(expand=True, fill="both", pady=(5, 5))

                def run_rom_callback(event, rom_info=rom_data):
                    target_emulator_frame = self.controller.frames.get(rom_info['emulator_frame_name'])
                    if target_emulator_frame and hasattr(target_emulator_frame, 'launch_selected_rom'):
                        target_emulator_frame.launch_selected_rom(rom_info['rom_path'])
                    else:
                        messagebox.showerror("Launch Error", f"Could not find emulator '{rom_info['emulator_name']}' or its launch method to run '{rom_info['name']}'.")
                    self.update_dashboard()

                rom_frame.bind("<Button-1>", run_rom_callback)
                text_label.bind("<Button-1>", run_rom_callback)

                self.recently_played_rom_widgets.append(rom_frame)

            except Exception as e:
                print(f"Error loading recently played ROM button for {rom_data.get('name', 'Unknown')}: {e}")

        total_content_width = len(all_recent_roms) * (RECENT_ITEM_BUTTON_WIDTH + 10)
        self.recently_played_roms_canvas.itemconfig(
            self.recently_played_roms_frame_id,
            width=total_content_width if total_content_width > self.recently_played_roms_canvas.winfo_width() else self.recently_played_roms_canvas.winfo_width()
        )
        self.recently_played_roms_canvas.update_idletasks()
        self.recently_played_roms_canvas.config(
            scrollregion=self.recently_played_roms_canvas.bbox("all")
        )

    def on_recent_roms_canvas_resize(self, event):
        """Update the inner frame width when the ROMs canvas resizes."""
        inner_frame_width = self.recently_played_roms_frame.winfo_reqwidth()
        canvas_width = self.recently_played_roms_canvas.winfo_width()
        
        self.recently_played_roms_canvas.itemconfig(
            self.recently_played_roms_frame_id, 
            width=max(inner_frame_width, canvas_width)
        )
        self.recently_played_roms_canvas.config(scrollregion=self.recently_played_roms_canvas.bbox("all"))

    def scroll_recent_roms_left(self):
        """Scroll the recently played ROMs canvas to the left."""
        self.recently_played_roms_canvas.xview_scroll(-1, "units")

    def scroll_recent_roms_right(self):
        """Scroll the recently played ROMs canvas to the right."""
        self.recently_played_roms_canvas.xview_scroll(1, "units")

    def bind_mousewheel_events_recent_roms(self):
        """Bind mouse wheel events for the recently played ROMs canvas."""
        self.recently_played_roms_canvas.bind("<MouseWheel>", self.on_mousewheel_recent_roms)
        self.recently_played_roms_canvas.bind("<Button-4>", lambda e: self.on_mousewheel_recent_roms_scroll(-1))
        self.recently_played_roms_canvas.bind("<Button-5>", lambda e: self.on_mousewheel_recent_roms_scroll(1))
        self.recently_played_roms_canvas.bind("<Enter>", lambda e: self.recently_played_roms_canvas.focus_set())
        self.recently_played_roms_canvas.bind("<Leave>", lambda e: self.focus_set())

    def on_mousewheel_recent_roms(self, event):
        """Handle mouse wheel scrolling for the recently played ROMs canvas on Windows/Mac."""
        self.recently_played_roms_canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_recent_roms_scroll(self, direction):
        """Handle mouse wheel scrolling for the recently played ROMs canvas on Linux."""
        self.recently_played_roms_canvas.xview_scroll(direction, "units")

    def update_dashboard(self):
        """Call this method to refresh the recently played/added data."""
        self.load_recent_data()
    
    # Controller Navigation Methods
    def controller_navigate_up(self):
        """Handle controller up navigation on dashboard"""
        # Focus on library buttons or scroll up in recent items
        if hasattr(self, 'library_buttons') and self.library_buttons:
            # Focus first library button
            self.library_buttons[0].focus_set()
    
    def controller_navigate_down(self):
        """Handle controller down navigation on dashboard"""
        # Focus on recent items or scroll down
        if hasattr(self, 'library_buttons') and self.library_buttons:
            # Focus last library button
            self.library_buttons[-1].focus_set()
    
    def controller_navigate_left(self):
        """Handle controller left navigation on dashboard"""
        # Scroll left in recent items or focus previous library button
        current_focus = self.focus_get()
        if hasattr(self, 'library_buttons') and current_focus in self.library_buttons:
            current_index = self.library_buttons.index(current_focus)
            if current_index > 0:
                self.library_buttons[current_index - 1].focus_set()
        elif hasattr(self, 'scroll_recent_roms_left'):
            self.scroll_recent_roms_left()
    
    def controller_navigate_right(self):
        """Handle controller right navigation on dashboard"""
        # Scroll right in recent items or focus next library button
        current_focus = self.focus_get()
        if hasattr(self, 'library_buttons') and current_focus in self.library_buttons:
            current_index = self.library_buttons.index(current_focus)
            if current_index < len(self.library_buttons) - 1:
                self.library_buttons[current_index + 1].focus_set()
        elif hasattr(self, 'scroll_recent_roms_right'):
            self.scroll_recent_roms_right()
    
    def controller_select(self):
        """Handle controller select action on dashboard"""
        # Activate the currently focused library button
        current_focus = self.focus_get()
        if hasattr(self, 'library_buttons') and current_focus in self.library_buttons:
            # Simulate button click
            current_focus.invoke()
    
    def controller_back(self):
        """Handle controller back action on dashboard"""
        # Go to login or show menu
        if hasattr(self.controller, 'show_frame'):
            self.controller.show_frame("LoginFrame")
    
    def controller_menu(self):
        """Handle controller menu action on dashboard"""
        # Show profile dropdown
        if hasattr(self.controller, 'menu_bar') and hasattr(self.controller.menu_bar, 'show_profile_dropdown'):
            self.controller.menu_bar.show_profile_dropdown()
    
    def controller_home(self):
        """Handle controller home action on dashboard"""
        # Already on dashboard, just refresh
        self.refresh_user()

