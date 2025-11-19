import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
from pathlib import Path
from paths import PathManager
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from artwork_scraper import ArtworkScraper

class RomsFrame(tk.Frame):
    def __init__(self, parent, controller, path_manager: PathManager):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.path_manager = path_manager
        self.configure(bg="#282c34")
        
        # Initialize artwork scraper
        self.artwork_scraper = ArtworkScraper(self.path_manager)
        self.artwork_scraper.add_progress_callback(self._on_scraper_progress)
        self.artwork_scraper.add_completion_callback(self._on_scraper_completion)
        
        # Load emulators data
        self.emulators_data = []
        self.load_emulators()
        
        # UI variables
        self.console_vars = {}  # Dictionary to store checkbox variables
        self.boxart_var = tk.BooleanVar(value=True)
        self.banner_var = tk.BooleanVar(value=True)
        self.fanart_var = tk.BooleanVar(value=False)
        self.screenshot_var = tk.BooleanVar(value=False)
        self.titlescreen_var = tk.BooleanVar(value=False)
        self.clearlogo_var = tk.BooleanVar(value=False)
        self.api_source_var = tk.StringVar(value="TheGamesDB")  # Default to TheGamesDB
        
        # Credential variables
        self.thegamesdb_apikey_var = tk.StringVar(value="1")
        self.screenscraper_username_var = tk.StringVar(value="")
        self.screenscraper_password_var = tk.StringVar(value="")
        self.screenscraper_devid_var = tk.StringVar(value="")
        
        # Load saved settings
        self.load_scraper_settings()
        
        # Setup UI
        self.setup_ui()

    def load_emulators(self):
        """Load emulators from JSON file"""
        DATA_FILE = self.path_manager.get_path("data") / "emulators" / "emulators.json"
        if not DATA_FILE.exists():
            self.emulators_data = []
            return

        try:
            with open(DATA_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    self.emulators_data = []
                else:
                    self.emulators_data = json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading emulators: {e}")
            self.emulators_data = []
    
    def load_scraper_settings(self):
        """Load scraper settings from config file"""
        config_file = self.path_manager.get_path("data") / "scraper_settings.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    content = f.read().strip()
                    if content:
                        settings = json.loads(content)
                        # Load API key (strip whitespace)
                        if "thegamesdb_apikey" in settings:
                            apikey = str(settings["thegamesdb_apikey"]).strip() if settings["thegamesdb_apikey"] else "1"
                            print(f"DEBUG: Loading API key from settings (length: {len(apikey)})")
                            self.thegamesdb_apikey_var.set(apikey)
                            # Also set it on the scraper immediately
                            self.artwork_scraper.set_thegamesdb_apikey(apikey)
                        else:
                            print("DEBUG: No API key found in settings, using default '1'")
                        # Load ScreenScraper credentials (strip whitespace)
                        if "screenscraper_username" in settings:
                            username = str(settings["screenscraper_username"]).strip() if settings["screenscraper_username"] else ""
                            self.screenscraper_username_var.set(username)
                        if "screenscraper_password" in settings:
                            password = str(settings["screenscraper_password"]).strip() if settings["screenscraper_password"] else ""
                            self.screenscraper_password_var.set(password)
                        if "screenscraper_devid" in settings:
                            devid = str(settings["screenscraper_devid"]).strip() if settings["screenscraper_devid"] else ""
                            self.screenscraper_devid_var.set(devid)
                        # Load API source
                        if "api_source" in settings:
                            self.api_source_var.set(settings["api_source"])
                        # Load artwork type preferences (optional)
                        if "boxart_enabled" in settings:
                            self.boxart_var.set(settings["boxart_enabled"])
                        if "banner_enabled" in settings:
                            self.banner_var.set(settings["banner_enabled"])
                        if "fanart_enabled" in settings:
                            self.fanart_var.set(settings["fanart_enabled"])
                        if "screenshot_enabled" in settings:
                            self.screenshot_var.set(settings["screenshot_enabled"])
                        if "titlescreen_enabled" in settings:
                            self.titlescreen_var.set(settings["titlescreen_enabled"])
                        if "clearlogo_enabled" in settings:
                            self.clearlogo_var.set(settings["clearlogo_enabled"])
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error loading scraper settings: {e}")
    
    def save_scraper_settings(self):
        """Save scraper settings to config file"""
        config_file = self.path_manager.get_path("data") / "scraper_settings.json"
        try:
            # Strip whitespace from API key when saving
            apikey = self.thegamesdb_apikey_var.get().strip() if self.thegamesdb_apikey_var.get() else "1"
            settings = {
                "thegamesdb_apikey": apikey,
                "screenscraper_username": self.screenscraper_username_var.get(),
                "screenscraper_password": self.screenscraper_password_var.get(),
                "screenscraper_devid": self.screenscraper_devid_var.get(),
                "api_source": self.api_source_var.get(),
                "boxart_enabled": self.boxart_var.get(),
                "banner_enabled": self.banner_var.get(),
                "fanart_enabled": self.fanart_var.get(),
                "screenshot_enabled": self.screenshot_var.get(),
                "titlescreen_enabled": self.titlescreen_var.get(),
                "clearlogo_enabled": self.clearlogo_var.get()
            }
            # Ensure directory exists
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, "w") as f:
                json.dump(settings, f, indent=4)
            # Also update the scraper's API key immediately after saving
            if apikey:
                self.artwork_scraper.set_thegamesdb_apikey(apikey)
        except Exception as e:
            print(f"Error saving scraper settings: {e}")

    def setup_ui(self):
        """Setup the UI components"""
        # Title
        title_label = ttk.Label(
            self,
            text="ROM Artwork Scraper",
            font=("Arial", 24, "bold"),
            foreground="white",
            background="#282c34"
        )
        title_label.pack(pady=(20, 10), padx=20)

        # Description
        desc_label = ttk.Label(
            self,
            text="Select consoles and configure artwork types to scrape artwork for your ROMs.",
            foreground="white",
            background="#282c34",
            wraplength=600
        )
        desc_label.pack(pady=(0, 20), padx=20)

        # Main container
        main_container = tk.Frame(self, bg="#282c34")
        main_container.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel - Console selection
        left_panel = tk.Frame(main_container, bg="#282c34")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        console_label = ttk.Label(
            left_panel,
            text="Select Consoles:",
            font=("Arial", 14, "bold"),
            foreground="white",
            background="#282c34"
        )
        console_label.pack(anchor="w", pady=(0, 10))

        # Scrollable frame for consoles
        canvas = tk.Canvas(left_panel, bg="#1e1e1e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e1e1e")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Populate console checkboxes
        if self.emulators_data:
            for emulator in self.emulators_data:
                full_name = emulator.get("full_name", "Unknown")
                short_name = emulator.get("short_name", "")
                var = tk.BooleanVar(value=False)
                self.console_vars[short_name] = {
                    "var": var,
                    "full_name": full_name
                }

                checkbox = tk.Checkbutton(
                    scrollable_frame,
                    text=full_name,
                    variable=var,
                    bg="#1e1e1e",
                    fg="white",
                    selectcolor="#282c34",
                    activebackground="#1e1e1e",
                    activeforeground="white",
                    font=("Arial", 11),
                    anchor="w",
                    padx=10,
                    pady=5
                )
                checkbox.pack(fill="x", padx=5, pady=2)
        else:
            no_consoles_label = ttk.Label(
                scrollable_frame,
                text="No emulators found. Add emulators first.",
                foreground="gray",
                background="#1e1e1e"
            )
            no_consoles_label.pack(pady=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Right panel - Configuration and controls
        right_panel = tk.Frame(main_container, bg="#282c34", width=300)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)

        # API source selection
        api_label = ttk.Label(
            right_panel,
            text="API Source:",
            font=("Arial", 14, "bold"),
            foreground="white",
            background="#282c34"
        )
        api_label.pack(anchor="w", pady=(0, 10))
        
        api_frame = tk.Frame(right_panel, bg="#1e1e1e")
        api_frame.pack(fill="x", pady=(0, 20))
        
        api_dropdown = ttk.Combobox(
            api_frame,
            textvariable=self.api_source_var,
            values=("TheGamesDB", "ScreenScraper"),
            state="readonly",
            font=("Arial", 11),
            width=20
        )
        api_dropdown.set("TheGamesDB")
        api_dropdown.pack(fill="x", padx=10, pady=5)
        api_dropdown.bind("<<ComboboxSelected>>", self._on_api_source_changed)
        
        # Credentials frame - will show/hide based on API selection
        self.credentials_frame = tk.Frame(right_panel, bg="#282c34")
        self.credentials_frame.pack(fill="x", pady=(0, 20))
        
        # TheGamesDB credentials
        self.thegamesdb_creds_frame = tk.Frame(self.credentials_frame, bg="#1e1e1e")
        
        tgdb_label = ttk.Label(
            self.thegamesdb_creds_frame,
            text="API Key:",
            font=("Arial", 10),
            foreground="white",
            background="#1e1e1e"
        )
        tgdb_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        tgdb_key_entry = tk.Entry(
            self.thegamesdb_creds_frame,
            textvariable=self.thegamesdb_apikey_var,
            bg="#282c34",
            fg="white",
            insertbackground="white",
            font=("Arial", 10),
            width=30
        )
        tgdb_key_entry.pack(fill="x", padx=10, pady=(0, 5))
        # Save API key when user leaves the field
        tgdb_key_entry.bind("<FocusOut>", lambda e: self.save_scraper_settings())
        
        tgdb_help_label = ttk.Label(
            self.thegamesdb_creds_frame,
            text="Get your API key from:\nhttps://api.thegamesdb.net/key.php",
            font=("Arial", 8),
            foreground="gray",
            background="#1e1e1e",
            justify="left"
        )
        tgdb_help_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # ScreenScraper credentials
        self.screenscraper_creds_frame = tk.Frame(self.credentials_frame, bg="#1e1e1e")
        
        ss_user_label = ttk.Label(
            self.screenscraper_creds_frame,
            text="Username:",
            font=("Arial", 10),
            foreground="white",
            background="#1e1e1e"
        )
        ss_user_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        ss_user_entry = tk.Entry(
            self.screenscraper_creds_frame,
            textvariable=self.screenscraper_username_var,
            bg="#282c34",
            fg="white",
            insertbackground="white",
            font=("Arial", 10),
            width=30
        )
        ss_user_entry.pack(fill="x", padx=10, pady=(0, 5))
        
        ss_pass_label = ttk.Label(
            self.screenscraper_creds_frame,
            text="Password:",
            font=("Arial", 10),
            foreground="white",
            background="#1e1e1e"
        )
        ss_pass_label.pack(anchor="w", padx=10, pady=(5, 5))
        
        ss_pass_entry = tk.Entry(
            self.screenscraper_creds_frame,
            textvariable=self.screenscraper_password_var,
            bg="#282c34",
            fg="white",
            insertbackground="white",
            font=("Arial", 10),
            width=30,
            show="*"
        )
        ss_pass_entry.pack(fill="x", padx=10, pady=(0, 5))
        
        ss_devid_label = ttk.Label(
            self.screenscraper_creds_frame,
            text="Dev ID (Optional):",
            font=("Arial", 10),
            foreground="white",
            background="#1e1e1e"
        )
        ss_devid_label.pack(anchor="w", padx=10, pady=(5, 5))
        
        ss_devid_entry = tk.Entry(
            self.screenscraper_creds_frame,
            textvariable=self.screenscraper_devid_var,
            bg="#282c34",
            fg="white",
            insertbackground="white",
            font=("Arial", 10),
            width=30
        )
        ss_devid_entry.pack(fill="x", padx=10, pady=(0, 5))
        
        ss_help_label = ttk.Label(
            self.screenscraper_creds_frame,
            text="Register at:\nhttps://www.screenscraper.fr/webapi2.php",
            font=("Arial", 8),
            foreground="gray",
            background="#1e1e1e",
            justify="left"
        )
        ss_help_label.pack(anchor="w", padx=10, pady=(0, 10))
        
        # Show TheGamesDB credentials by default
        self._on_api_source_changed()
        
        # Artwork type selection
        artwork_label = ttk.Label(
            right_panel,
            text="Artwork Types:",
            font=("Arial", 14, "bold"),
            foreground="white",
            background="#282c34"
        )
        artwork_label.pack(anchor="w", pady=(0, 10))

        artwork_frame = tk.Frame(right_panel, bg="#1e1e1e")
        artwork_frame.pack(fill="x", pady=(0, 20))

        boxart_check = tk.Checkbutton(
            artwork_frame,
            text="Box Art (Covers)",
            variable=self.boxart_var,
            bg="#1e1e1e",
            fg="white",
            selectcolor="#282c34",
            activebackground="#1e1e1e",
            activeforeground="white",
            font=("Arial", 11),
            anchor="w",
            padx=10,
            pady=5
        )
        boxart_check.pack(fill="x")

        banner_check = tk.Checkbutton(
            artwork_frame,
            text="Banners",
            variable=self.banner_var,
            bg="#1e1e1e",
            fg="white",
            selectcolor="#282c34",
            activebackground="#1e1e1e",
            activeforeground="white",
            font=("Arial", 11),
            anchor="w",
            padx=10,
            pady=5
        )
        banner_check.pack(fill="x")

        fanart_check = tk.Checkbutton(
            artwork_frame,
            text="Fan Art",
            variable=self.fanart_var,
            bg="#1e1e1e",
            fg="white",
            selectcolor="#282c34",
            activebackground="#1e1e1e",
            activeforeground="white",
            font=("Arial", 11),
            anchor="w",
            padx=10,
            pady=5
        )
        fanart_check.pack(fill="x")

        screenshot_check = tk.Checkbutton(
            artwork_frame,
            text="Screenshots",
            variable=self.screenshot_var,
            bg="#1e1e1e",
            fg="white",
            selectcolor="#282c34",
            activebackground="#1e1e1e",
            activeforeground="white",
            font=("Arial", 11),
            anchor="w",
            padx=10,
            pady=5
        )
        screenshot_check.pack(fill="x")

        titlescreen_check = tk.Checkbutton(
            artwork_frame,
            text="Title Screens",
            variable=self.titlescreen_var,
            bg="#1e1e1e",
            fg="white",
            selectcolor="#282c34",
            activebackground="#1e1e1e",
            activeforeground="white",
            font=("Arial", 11),
            anchor="w",
            padx=10,
            pady=5
        )
        titlescreen_check.pack(fill="x")

        clearlogo_check = tk.Checkbutton(
            artwork_frame,
            text="Clear Logos",
            variable=self.clearlogo_var,
            bg="#1e1e1e",
            fg="white",
            selectcolor="#282c34",
            activebackground="#1e1e1e",
            activeforeground="white",
            font=("Arial", 11),
            anchor="w",
            padx=10,
            pady=5
        )
        clearlogo_check.pack(fill="x")

        # Select/Unselect all buttons
        button_frame = tk.Frame(right_panel, bg="#282c34")
        button_frame.pack(fill="x", pady=(0, 20))

        select_all_btn = tk.Button(
            button_frame,
            text="Select All",
            command=self.select_all_consoles,
            bg="#4a5568",
            fg="white",
            activebackground="#5a6578",
            activeforeground="white",
            font=("Arial", 10),
            relief="flat",
            padx=10,
            pady=5
        )
        select_all_btn.pack(fill="x", pady=(0, 5))

        unselect_all_btn = tk.Button(
            button_frame,
            text="Unselect All",
            command=self.unselect_all_consoles,
            bg="#4a5568",
            fg="white",
            activebackground="#5a6578",
            activeforeground="white",
            font=("Arial", 10),
            relief="flat",
            padx=10,
            pady=5
        )
        unselect_all_btn.pack(fill="x")

        # Scrape button
        self.scrape_btn = tk.Button(
            right_panel,
            text="Scrape Artwork",
            command=self.start_scraping,
            bg="#48bb78",
            fg="white",
            activebackground="#38a169",
            activeforeground="white",
            font=("Arial", 12, "bold"),
            relief="flat",
            padx=20,
            pady=10
        )
        self.scrape_btn.pack(fill="x", pady=(0, 10))

        # Cancel button (initially disabled)
        self.cancel_btn = tk.Button(
            right_panel,
            text="Cancel",
            command=self.cancel_scraping,
            bg="#f56565",
            fg="white",
            activebackground="#e53e3e",
            activeforeground="white",
            font=("Arial", 11),
            relief="flat",
            padx=20,
            pady=10,
            state="disabled"
        )
        self.cancel_btn.pack(fill="x", pady=(0, 20))

        # Progress display
        progress_frame = tk.Frame(right_panel, bg="#1e1e1e")
        progress_frame.pack(fill="both", expand=True)

        progress_label = ttk.Label(
            progress_frame,
            text="Progress:",
            font=("Arial", 11, "bold"),
            foreground="white",
            background="#1e1e1e"
        )
        progress_label.pack(anchor="w", padx=10, pady=(10, 5))

        self.progress_text = tk.Text(
            progress_frame,
            bg="#282c34",
            fg="white",
            font=("Arial", 9),
            wrap="word",
            height=10,
            relief="flat",
            padx=10,
            pady=5
        )
        # Configure text tags for success/error messages
        self.progress_text.tag_config("success", foreground="#48bb78")
        self.progress_text.tag_config("error", foreground="#f56565")
        self.progress_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Scrollbar for progress text
        progress_scrollbar = ttk.Scrollbar(
            progress_frame,
            orient="vertical",
            command=self.progress_text.yview
        )
        self.progress_text.configure(yscrollcommand=progress_scrollbar.set)
        progress_scrollbar.pack(side="right", fill="y")

    def select_all_consoles(self):
        """Select all console checkboxes"""
        for data in self.console_vars.values():
            data["var"].set(True)

    def unselect_all_consoles(self):
        """Unselect all console checkboxes"""
        for data in self.console_vars.values():
            data["var"].set(False)
    
    def _on_api_source_changed(self, event=None):
        """Called when API source dropdown changes - show/hide credential fields"""
        # Hide all credential frames
        self.thegamesdb_creds_frame.pack_forget()
        self.screenscraper_creds_frame.pack_forget()
        
        # Show appropriate credential frame based on selection
        api_source = self.api_source_var.get()
        if api_source == "TheGamesDB":
            self.thegamesdb_creds_frame.pack(fill="x", pady=(0, 10))
        elif api_source == "ScreenScraper":
            self.screenscraper_creds_frame.pack(fill="x", pady=(0, 10))
        
        # Save settings when API source changes
        self.save_scraper_settings()

    def start_scraping(self):
        """Start the artwork scraping process"""
        # Check if at least one console is selected
        selected_emulators = []
        for short_name, data in self.console_vars.items():
            if data["var"].get():
                # Find the full emulator data to include rom_directory if available
                emulator_data = None
                for emulator in self.emulators_data:
                    if emulator.get("short_name") == short_name:
                        emulator_data = emulator
                        break
                
                selected_emulator = {
                    "short_name": short_name,
                    "full_name": data["full_name"]
                }
                
                # Include rom_directory if it exists in emulator data
                if emulator_data and "rom_directory" in emulator_data:
                    selected_emulator["rom_directory"] = emulator_data["rom_directory"]
                
                selected_emulators.append(selected_emulator)

        if not selected_emulators:
            messagebox.showwarning(
                "No Selection",
                "Please select at least one console to scrape artwork for."
            )
            return

        # Check if at least one artwork type is selected
        if not (self.boxart_var.get() or self.banner_var.get() or self.fanart_var.get() or 
                self.screenshot_var.get() or self.titlescreen_var.get() or self.clearlogo_var.get()):
            messagebox.showwarning(
                "No Artwork Type",
                "Please select at least one artwork type to scrape."
            )
            return

        # Check if already scraping
        if self.artwork_scraper.is_scraping():
            messagebox.showinfo(
                "Already Scraping",
                "Artwork scraping is already in progress."
            )
            return

        # Clear progress text
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.insert(tk.END, "Starting artwork scraping...\n")
        self.progress_text.see(tk.END)

        # Disable scrape button, enable cancel button
        self.scrape_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")

        # Start scraping in background thread
        def scrape_worker():
            try:
                print(f"DEBUG: Starting scrape for {len(selected_emulators)} emulator(s)")
                for em in selected_emulators:
                    print(f"  - {em.get('full_name')} (short: {em.get('short_name')})")
                
                # Get selected API source
                api_source = self.api_source_var.get()
                api_source_lower = api_source.lower()
                self.artwork_scraper.set_api_source(api_source_lower)
                
                # Set credentials based on selected API
                if api_source == "TheGamesDB":
                    # Get API key from UI variable
                    raw_apikey = self.thegamesdb_apikey_var.get() if self.thegamesdb_apikey_var.get() else ""
                    apikey = str(raw_apikey).strip() if raw_apikey else ""
                    raw_length = len(raw_apikey) if raw_apikey else 0
                    raw_preview = repr(raw_apikey[:20]) if raw_apikey else "''"
                    print(f"DEBUG: Raw API key from UI (length: {raw_length}): {raw_preview}...")
                    
                    if not apikey:
                        apikey = "1"  # Default public key
                        print("DEBUG: API key is empty, using default '1'")
                    
                    # Clean the key thoroughly
                    apikey = apikey.strip()
                    print(f"DEBUG: Setting API key on scraper (length: {len(apikey)}): {apikey[:10]}...{apikey[-5:] if len(apikey) > 15 else apikey}")
                    
                    # Set on scraper
                    self.artwork_scraper.set_thegamesdb_apikey(apikey)
                    
                    # Update the StringVar with the cleaned key
                    self.thegamesdb_apikey_var.set(apikey)
                    
                    # Verify it was set correctly
                    verify_key = self.artwork_scraper.thegamesdb_apikey if hasattr(self.artwork_scraper, 'thegamesdb_apikey') else "N/A"
                    print(f"DEBUG: Verified scraper API key (length: {len(verify_key) if verify_key != 'N/A' else 0}): {verify_key[:10] if verify_key != 'N/A' else 'N/A'}...{verify_key[-5:] if verify_key != 'N/A' and len(verify_key) > 15 else ''}")
                elif api_source == "ScreenScraper":
                    username = self.screenscraper_username_var.get().strip()
                    password = self.screenscraper_password_var.get().strip()
                    devid = self.screenscraper_devid_var.get().strip()
                    self.artwork_scraper.set_screenscraper_credentials(username, password, devid)
                    print(f"DEBUG: Using ScreenScraper credentials (username: {username}, devid: {devid})")
                
                # Save settings before scraping
                self.save_scraper_settings()
                
                self.artwork_scraper.scrape_multiple_emulators(
                    selected_emulators,
                    download_boxart=self.boxart_var.get(),
                    download_banner=self.banner_var.get(),
                    download_fanart=self.fanart_var.get(),
                    download_screenshot=self.screenshot_var.get(),
                    download_titlescreen=self.titlescreen_var.get(),
                    download_clearlogo=self.clearlogo_var.get()
                )
            except Exception as e:
                import traceback
                error_msg = f"ERROR in scrape_worker: {e}\n{traceback.format_exc()}"
                print(error_msg)
                self.progress_text.insert(tk.END, f"\n\nFATAL ERROR:\n{error_msg}\n")
                self.progress_text.see(tk.END)
                self._on_scraper_completion(False, f"Scraping failed with error: {e}")

        thread = threading.Thread(target=scrape_worker, daemon=True)
        thread.start()
        print("DEBUG: Scrape thread started")

    def cancel_scraping(self):
        """Cancel the ongoing scraping operation"""
        if self.artwork_scraper.is_scraping():
            self.artwork_scraper.cancel_scraping()
            self.progress_text.insert(tk.END, "\nScraping cancelled by user.\n")
            self.progress_text.see(tk.END)
            self._on_scraper_completion(False, "Scraping cancelled.")

    def _on_scraper_progress(self, message: str, current: int, total: int):
        """Handle progress updates from scraper"""
        def update_ui():
            if total > 0:
                progress_msg = f"[{current}/{total}] {message}\n"
            else:
                progress_msg = f"{message}\n"
            self.progress_text.insert(tk.END, progress_msg)
            # Force the text widget to update and scroll to bottom
            self.progress_text.see(tk.END)
            # Force immediate update of the display
            self.progress_text.update_idletasks()
            self.update_idletasks()

        # Schedule UI update on main thread - use 1ms delay to ensure it processes
        self.after(1, update_ui)

    def _on_scraper_completion(self, success: bool, message: str):
        """Handle completion callback from scraper"""
        def update_ui():
            if success:
                self.progress_text.insert(tk.END, f"\n✓ {message}\n", "success")
            else:
                self.progress_text.insert(tk.END, f"\n✗ {message}\n", "error")
            self.progress_text.see(tk.END)

            # Re-enable scrape button, disable cancel button
            self.scrape_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")

            # Show completion message
            if success:
                messagebox.showinfo("Scraping Complete", message)
            else:
                messagebox.showerror("Scraping Error", message)

            self.update_idletasks()

        # Schedule UI update on main thread
        self.after(0, update_ui)

    def on_show_frame(self):
        """Called when this frame is brought to the front"""
        # Reload emulators data in case it changed
        self.load_emulators()
        
        # Clear and rebuild console checkboxes
        self.console_vars.clear()
        
        # Find the scrollable frame and repopulate
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        for canvas in child.winfo_children():
                            if isinstance(canvas, tk.Canvas):
                                # Find scrollable_frame
                                canvas_children = canvas.winfo_children()
                                if canvas_children:
                                    scrollable_frame = canvas_children[0]
                                    # Clear existing checkboxes
                                    for widget in scrollable_frame.winfo_children():
                                        widget.destroy()
                                    
                                    # Repopulate
                                    if self.emulators_data:
                                        for emulator in self.emulators_data:
                                            full_name = emulator.get("full_name", "Unknown")
                                            short_name = emulator.get("short_name", "")
                                            var = tk.BooleanVar(value=False)
                                            self.console_vars[short_name] = {
                                                "var": var,
                                                "full_name": full_name
                                            }

                                            checkbox = tk.Checkbutton(
                                                scrollable_frame,
                                                text=full_name,
                                                variable=var,
                                                bg="#1e1e1e",
                                                fg="white",
                                                selectcolor="#282c34",
                                                activebackground="#1e1e1e",
                                                activeforeground="white",
                                                font=("Arial", 11),
                                                anchor="w",
                                                padx=10,
                                                pady=5
                                            )
                                            checkbox.pack(fill="x", padx=5, pady=2)
                                    else:
                                        no_consoles_label = ttk.Label(
                                            scrollable_frame,
                                            text="No emulators found. Add emulators first.",
                                            foreground="gray",
                                            background="#1e1e1e"
                                        )
                                        no_consoles_label.pack(pady=20)
                                    break


