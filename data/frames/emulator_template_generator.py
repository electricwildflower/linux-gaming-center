import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import json
import datetime
from pathlib import Path # Import Path for consistency and future use in generated code

# This file contains the logic to generate the content of a dynamic emulator frame.

def generate_emulator_frame_file(file_path, full_emulator_name, short_emulator_name, run_script_path, rom_directory, bios_directory):
    """
    Generates the content for a dynamic emulator Python file and writes it to the specified path.
    This function encapsulates the large f-string that defines the emulator's UI and logic.
    """
    # Derive the class name (should match what's used in register_dynamic_frame)
    class_name_parts = [part.capitalize() for part in short_emulator_name.split('_')]
    dynamic_frame_class_name = "".join(class_name_parts) + "EmulatorFrame"

    # Escape quotes and backslashes for safe inclusion in the f-string
    full_emulator_name_escaped = full_emulator_name.replace('"', '\\"').replace('\\', '\\\\\\\\')
    run_script_path_escaped = run_script_path.replace(os.sep, '/').replace('"', '\\"').replace('\\', '\\\\\\\\')
    rom_directory_escaped = rom_directory.replace(os.sep, '/').replace('"', '\\"').replace('\\', '\\\\\\\\')
    bios_directory_escaped = bios_directory.replace(os.sep, '/').replace('"', '\\"').replace('\\', '\\\\\\\\')

    # Content for the new .py file using f-string
    # We now pass the path_manager instance to the generated frame's __init__
    # And use it to get the ROMS_DATA_DIR and EMULATORS_DATA_FILE dynamically.
    file_content = f'''
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import json
import datetime
import re
from pathlib import Path # NEW: Import Path in the generated file
from paths import PathManager # NEW: Import PathManager in the generated file

# Try to import PIL/Pillow for image handling, but don't crash if it's not available
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("WARNING: PIL/Pillow not available. Boxart images will not be displayed.")

# Define a set of common ROM extensions. You can expand this.
ROM_EXTENSIONS = {{
    '.nes', '.snes', '.gb', '.bin', '.chd', '.cue','.gba', '.gen', '.md', '.n64', '.ps1', '.iso',
    '.zip', '.7z', '.rar' '.j64', '.jag', '.rom', '.abs', '.cof', '.bin', '.prg'
}}

class {dynamic_frame_class_name}(ttk.Frame):
    # MODIFIED: Added path_manager to the __init__ signature
    def __init__(self, parent, controller, path_manager):
        super().__init__(parent)
        self.controller = controller
        self.path_manager = path_manager # NEW: Store path_manager in the generated class
        self.rom_cache_manager = None  # Will be set by main.py

        self.emulator_name = "{full_emulator_name_escaped}" # Store the full name for display
        self.short_emulator_name = "{short_emulator_name}" # Store the short name for file operations
        self.run_script_path = r"{run_script_path_escaped}" # Path to the .sh script for running ROMs
        self.rom_directory = r"{rom_directory_escaped}"
        self.bios_directory = r"{bios_directory_escaped}" # Store bios directory

        # MODIFIED: Get ROMS_DATA_DIR and EMULATORS_DATA_FILE dynamically using path_manager
        # This path is for the JSON file storing ROM play history within the dynamic emulator frame
        self.ROMS_DATA_DIR = self.path_manager.get_path("data") / "emulators" / "rom_data"
        self.EMULATORS_DATA_FILE = self.path_manager.get_path("data") / "emulators" / "emulators.json"

        self.rom_data_file = self.ROMS_DATA_DIR / f"{{self.short_emulator_name}}_roms.json" # Use short_name for ROM data file

        # Grid UI components
        self.roms = [] # Stores full paths of ROMs found in the directory
        self.filtered_roms = [] # Stores filtered ROMs based on search
        self.rom_buttons = [] # Stores button widgets
        self.rom_images = {{}} # Stores PhotoImage objects (X11 resources) - limited cache (50 max)
        self.rom_pil_cache = {{}} # Stores PIL Image objects (no X11 resources) - all images pre-loaded
        self.box2dfront_directory = None # Path to media/box2dfront/ directory
        self.search_var = tk.StringVar()
        # Don't set up trace yet - wait until UI is ready
        
        # Grid layout settings
        self.columns = 6  # Number of columns in the grid
        self.button_width = max(100, 150)  # Ensure minimum valid width
        self.button_height = max(100, 200)  # Ensure minimum valid height
        self.button_padding = 10
        
        self.rom_play_history = self.load_rom_play_history() # Stores last_played for each ROM

        try:
            self.setup_ui()
            
            # Set up search trace after UI is ready
            self.search_var.trace("w", lambda *args: self.filter_roms())
            
            # Delay ROM loading to ensure UI is fully initialized
            self.after(100, self.load_roms)

            self.bind("<Visibility>", self.on_visibility_change)
        except Exception as e:
            print(f"ERROR: Failed to initialize {{self.emulator_name}} frame: {{e}}")
            import traceback
            traceback.print_exc()
            # Create a minimal error frame so the app doesn't crash
            error_label = tk.Label(self, text=f"Error loading {{self.emulator_name}} library:\\n{{e}}", 
                                 fg="red", bg="#1e1e1e", font=("Arial", 12), justify="left")
            error_label.pack(fill="both", expand=True, padx=20, pady=20)

    def set_rom_cache_manager(self, rom_cache_manager):
        """Set the ROM cache manager instance"""
        self.rom_cache_manager = rom_cache_manager

    def setup_ui(self):
        main_frame = ttk.Frame(self, style="EmulatorFrame.TFrame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Define button styles matching theme
        style = ttk.Style(self)
        style.theme_use("clam")
        
        # Back button style (purple theme)
        style.configure("EmulatorFrame.BackButton.TButton",
                        background="#9a32cd",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        padding=8,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="#9a32cd")
        style.map("EmulatorFrame.BackButton.TButton",
                  background=[('active', '#7d26cd'), ('pressed', '#6a1b9a')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        
        # Rescan button style (blue theme)
        style.configure("EmulatorFrame.RescanButton.TButton",
                        background="#61afef",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        padding=8,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="#61afef")
        style.map("EmulatorFrame.RescanButton.TButton",
                  background=[('active', '#5698d3'), ('pressed', '#467cb4')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        # Button frame for back and rescan buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(anchor="nw", padx=0, pady=10, fill="x")
        
        # Back button
        back_button = ttk.Button(
            button_frame,
            text="< Back to Emulators",
            command=lambda: self.controller.show_frame("EmulatorsFrame"),
            style="EmulatorFrame.BackButton.TButton"
        )
        back_button.pack(side="left", padx=0, pady=0)
        
        # Rescan ROMs button
        rescan_button = ttk.Button(
            button_frame,
            text="Rescan ROMs",
            command=self.rescan_roms,
            style="EmulatorFrame.RescanButton.TButton"
        )
        rescan_button.pack(side="left", padx=(10, 0), pady=0)

        # Search box at top center (centered, not too wide)
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill="x", pady=(10, 20))
        
        # Center the search entry
        search_container = ttk.Frame(search_frame)
        search_container.pack(expand=True)
        
        self.search_entry = ttk.Entry(search_container, textvariable=self.search_var, font=("Arial", 12), width=30)
        self.search_entry.pack()
        
        # Main content frame with grid and letter index
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True)
        
        # Canvas for ROM grid (no scrollbar - use mousewheel only)
        canvas_frame = ttk.Frame(content_frame)
        canvas_frame.pack(side="left", fill="both", expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#1e1e1e", highlightthickness=0)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        def update_scroll_region(e):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self._on_canvas_configure()
        
        self.scrollable_frame.bind("<Configure>", update_scroll_region)
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Setup mousewheel bindings after canvas is created
        self.after(50, self._setup_mousewheel_binding)
        
        # Letter/Number index on the right
        index_frame = ttk.Frame(content_frame)
        index_frame.pack(side="right", fill="y", padx=(10, 0))
        
        index_label = ttk.Label(index_frame, text="Index", font=("Arial", 10, "bold"))
        index_label.pack(pady=(0, 5))
        
        self.index_buttons = []
        # Numbers 0-9
        for i in range(0, 10):
            btn = tk.Button(index_frame, text=str(i), width=3, height=1,
                          bg="#2d2d2d", fg="white", font=("Arial", 10),
                          relief="flat", borderwidth=0,
                          command=lambda num=i: self.scroll_to_letter(str(num)))
            btn.pack(pady=2)
            self.index_buttons.append(btn)
        
        # # symbol
        btn = tk.Button(index_frame, text="#", width=3, height=1,
                      bg="#2d2d2d", fg="white", font=("Arial", 10),
                      relief="flat", borderwidth=0,
                      command=lambda: self.scroll_to_letter("#"))
        btn.pack(pady=2)
        self.index_buttons.append(btn)
        
        # Letters A-Z
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            btn = tk.Button(index_frame, text=letter, width=3, height=1,
                          bg="#2d2d2d", fg="white", font=("Arial", 10),
                          relief="flat", borderwidth=0,
                          command=lambda l=letter: self.scroll_to_letter(l))
            btn.pack(pady=2)
            self.index_buttons.append(btn)
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass
    
    def _on_mousewheel_scroll(self, direction):
        """Handle mousewheel scrolling on Linux"""
        try:
            self.canvas.yview_scroll(direction, "units")
        except Exception:
            pass
    
    def _setup_mousewheel_binding(self):
        """Setup mousewheel bindings after canvas is fully created"""
        def bind_mousewheel(event):
            try:
                self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
                self.canvas.bind_all("<Button-4>", lambda e: self._on_mousewheel_scroll(-1))
                self.canvas.bind_all("<Button-5>", lambda e: self._on_mousewheel_scroll(1))
            except Exception:
                pass
        
        def unbind_mousewheel(event):
            try:
                self.canvas.unbind_all("<MouseWheel>")
                self.canvas.unbind_all("<Button-4>")
                self.canvas.unbind_all("<Button-5>")
            except Exception:
                pass
        
        try:
            self.canvas.bind("<Enter>", bind_mousewheel)
            self.canvas.bind("<Leave>", unbind_mousewheel)
        except Exception:
            pass
    
    def _on_canvas_configure(self, event=None):
        """Called when canvas is resized - update visible images"""
        self._update_visible_images()
    
    def _on_canvas_scroll(self, event=None):
        """Called when canvas is scrolled - update visible images after a delay"""
        # Debounce: update visible images after scrolling stops
        if hasattr(self, '_scroll_update_job'):
            self.after_cancel(self._scroll_update_job)
        self._scroll_update_job = self.after(200, self._update_visible_images)
    
    def _update_visible_images(self):
        """Update PhotoImage objects for currently visible buttons only"""
        if not hasattr(self, 'scrollable_frame') or not hasattr(self, 'canvas'):
            return
        
        try:
            # Get scroll position and canvas dimensions
            scroll_top = self.canvas.canvasy(0)
            canvas_height = self.canvas.winfo_height()
            if canvas_height < 1:
                canvas_height = 600  # Default
            
            scroll_bottom = scroll_top + canvas_height
            
            # Calculate which rows are visible (with buffer)
            row_height = self.button_height + (self.button_padding * 2)
            if row_height < 1:
                row_height = 200  # Default
            visible_start_row = max(0, int((scroll_top - 200) // row_height))  # -200 buffer
            visible_end_row = int((scroll_bottom + 200) // row_height) + 2  # +200 buffer
            
            # Limit to prevent X11 exhaustion - only keep 50 PhotoImage objects max
            MAX_PHOTOIMAGES = 50
            
            # Remove PhotoImage objects for buttons that are far out of view
            # This frees X11 resources
            widgets_far_away = []
            for widget in self.scrollable_frame.winfo_children():
                if hasattr(widget, 'rom_path') and hasattr(widget, 'row'):
                    row = widget.row
                    if widget.rom_path in self.rom_images:
                        # Button has PhotoImage - check if it's still in visible range
                        if row < visible_start_row - 5 or row > visible_end_row + 5:
                            # Button is far out of view - remove PhotoImage
                            widgets_far_away.append(widget)
            
            # Remove PhotoImage for far-away buttons
            for widget in widgets_far_away:
                if hasattr(widget, 'image'):
                    widget.image = None  # Release reference
                    widget.config(image="", text=os.path.basename(widget.rom_path)[:30])
                if widget.rom_path in self.rom_images:
                    del self.rom_images[widget.rom_path]
            
            # Count current PhotoImages after cleanup
            current_photo_count = len(self.rom_images)
            
            # Find buttons in visible range that need PhotoImage
            buttons_to_update = []
            for widget in self.scrollable_frame.winfo_children():
                if hasattr(widget, 'rom_path') and hasattr(widget, 'row') and hasattr(widget, 'has_pil_image'):
                    row = widget.row
                    # Check if button is in visible range and has PIL image available
                    if visible_start_row <= row <= visible_end_row:
                        if widget.has_pil_image and widget.rom_path not in self.rom_images:
                            buttons_to_update.append((widget, widget.rom_path))
            
            # Update buttons up to the limit (only for visible ones)
            for widget, rom_path in buttons_to_update[:MAX_PHOTOIMAGES - current_photo_count]:
                if current_photo_count >= MAX_PHOTOIMAGES:
                    break
                try:
                    img = self._load_boxart_image(rom_path)
                    if img:
                        # Update button with image
                        widget.config(image=img, text="")
                        widget.image = img  # Keep reference
                        current_photo_count += 1
                except Exception:
                    pass
        except Exception:
            pass

    def on_visibility_change(self, event=None):
        """Called when frame visibility changes"""
        if self.winfo_ismapped():
            self.update_emulator_last_played() # Update emulator's last played time
            self.load_roms() # Reload ROMs to ensure list is fresh
    
    def rescan_roms(self):
        """Rescan ROMs for this emulator and update the display"""
        if not self.rom_cache_manager:
            return
        
        # Get emulator data from controller's emulators data
        emulator_data = None
        if hasattr(self.controller, 'frames') and "EmulatorsFrame" in self.controller.frames:
            emulators_frame = self.controller.frames["EmulatorsFrame"]
            if hasattr(emulators_frame, 'emulators_data'):
                for emulator in emulators_frame.emulators_data:
                    if emulator.get("short_name") == self.short_emulator_name:
                        emulator_data = emulator
                        break
        
        if not emulator_data:
            # Could not find emulator data
            return
        
        # Invalidate cache for this emulator
        self.rom_cache_manager.invalidate_emulator_cache(self.short_emulator_name)
        
        # Scan ROMs for this emulator
        roms = self.rom_cache_manager.scan_emulator_roms(emulator_data)
        
        # Update cache
        import time
        with self.rom_cache_manager._lock:
            self.rom_cache_manager.cache[self.short_emulator_name] = {{
                'emulator_data': emulator_data,
                'roms': roms,
                'last_scan': time.time()
            }}
        self.rom_cache_manager.save_cache()
        
        # Reload ROMs display
        self.load_roms()

    def update_emulator_last_played(self):
        """Updates the last_played timestamp for this specific emulator in the main emulators.json."""
        try:
            # MODIFIED: Use self.EMULATORS_DATA_FILE (which uses path_manager)
            with open(self.EMULATORS_DATA_FILE, "r+") as f:
                emulators_data = json.load(f)
                found = False
                for emulator in emulators_data:
                    # Use short_emulator_name to find the entry for updating last_played
                    if emulator.get("short_name") == self.short_emulator_name:
                        emulator["last_played"] = datetime.datetime.now().isoformat()
                        found = True
                        break
                if found:
                    f.seek(0)
                    json.dump(emulators_data, f, indent=4)
                    f.truncate()
                else:
                    print(f"Emulator '{{self.short_emulator_name}}' not found in {{self.EMULATORS_DATA_FILE}} for last_played update.")
        except FileNotFoundError:
            print(f"Error: {{self.EMULATORS_DATA_FILE}} not found. Cannot update emulator last_played.")
        except json.JSONDecodeError:
            print(f"Error: Malformed JSON in {{self.EMULATORS_DATA_FILE}}. Starting with empty history.")
        except Exception as e:
            print(f"An unexpected error occurred while updating emulator last_played: {{e}}")


    def load_rom_play_history(self):
        """Loads the ROM play history for this emulator from its specific JSON file."""
        # MODIFIED: Use Path object for .exists() check
        if self.rom_data_file.exists():
            try:
                with open(self.rom_data_file, "r") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Malformed JSON in ROM data file: {{self.rom_data_file}}. Starting with empty history.")
                return {{}}
        return {{}}

    def save_rom_play_history(self):
        """Saves the ROM play history for this emulator to its specific JSON file."""
        # MODIFIED: Use self.ROMS_DATA_DIR (which uses path_manager) and Path methods
        self.ROMS_DATA_DIR.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.rom_data_file, "w") as f:
                json.dump(self.rom_play_history, f, indent=4)
        except Exception as e:
            print(f"Error saving ROM play history to {{self.rom_data_file}}: {{e}}")


    def load_roms(self):
        """Loads ROM files from cache or directory and populates the grid."""
        try:
            self.roms = []
            
            # Find box2dfront directory - check all possible ROM directories for media/box2dfront/
            self.box2dfront_directory = None
            rom_dirs = self._get_all_rom_directories()
            for rom_dir in rom_dirs:
                media_dir = rom_dir / "media" / "box2dfront"
                if media_dir.exists():
                    self.box2dfront_directory = media_dir
                    break
            # If no box2dfront directory found, use the first ROM directory
            if not self.box2dfront_directory and rom_dirs:
                self.box2dfront_directory = rom_dirs[0] / "media" / "box2dfront"
            
            # Try to get ROMs from cache (don't wait for scanning to finish - use what's available)
            if self.rom_cache_manager:
                # Check cache even if scanning is in progress (use partial cache)
                cached_roms = self.rom_cache_manager.get_emulator_roms(self.short_emulator_name)
                if cached_roms:
                    print(f"Loaded {{len(cached_roms)}} ROMs from cache for {{self.emulator_name}}")
                    for rom_info in cached_roms:
                        self.roms.append(rom_info["rom_path"])
                    
                    # Sort by base filename for consistent display
                    self.roms.sort(key=os.path.basename)
                    
                    # Load pre-cached PIL images from ROM cache manager
                    # (Images were pre-loaded during app startup)
                    self._preload_all_pil_images()
                    
                    # Display ROMs in grid - only if UI is ready
                    if hasattr(self, 'scrollable_frame'):
                        self.filter_roms()
                else:
                    # No cached ROMs yet - check if scanning is in progress
                    if self.rom_cache_manager.is_scanning():
                        # Scanning in progress - show message and retry
                        print(f"Scanning in progress for {{self.emulator_name}}...")
                        if hasattr(self, 'scrollable_frame'):
                            self._show_scanning_message()
                        # Retry loading ROMs after a short delay
                        self.after(500, self.load_roms)
                    else:
                        # No cached ROMs and not scanning - show message to user
                        print(f"No cached ROMs found for {{self.emulator_name}}")
                        if hasattr(self, 'scrollable_frame'):
                            self._show_cache_needed_message()
            else:
                # No cache manager - show cache needed message
                print(f"ROM cache not available for {{self.emulator_name}}")
                if hasattr(self, 'scrollable_frame'):
                    self._show_cache_needed_message()
        except Exception as e:
            print(f"Error loading ROMs for {{self.emulator_name}}: {{e}}")
            import traceback
            traceback.print_exc()
            # Still show empty grid instead of crashing
            self.filtered_roms = []
            if hasattr(self, 'scrollable_frame'):
                self._show_cache_needed_message()
    
    def _show_cache_needed_message(self):
        """Show message that ROMs need to be cached"""
        # Clear existing buttons
        for button in self.rom_buttons:
            try:
                button.destroy()
            except Exception:
                pass
        self.rom_buttons = []
        
        # Clear scrollable frame - destroy all widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Use grid for consistency with _update_grid
        # Show message using grid layout
        message_frame = tk.Frame(self.scrollable_frame, bg="#2d2d2d")
        message_frame.grid(row=0, column=0, sticky="nsew", padx=50, pady=100)
        
        # Configure grid weights for centering
        self.scrollable_frame.rowconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(0, weight=1)
        
        message_label = tk.Label(
            message_frame,
            text="ROMs need to be cached for loading",
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Arial", 16, "bold"),
            justify="center"
        )
        message_label.grid(row=0, column=0, pady=20)
        
        instruction_label = tk.Label(
            message_frame,
            text="Please either restart the app or press the 'Rescan ROMs' button\\nto scan the ROM directory and cache all ROMs and images.",
            bg="#2d2d2d",
            fg="#888888",
            font=("Arial", 12),
            justify="center"
        )
        instruction_label.grid(row=1, column=0, pady=10)
    
    def _show_scanning_message(self):
        """Show message that ROMs are being scanned"""
        # Clear existing buttons
        for button in self.rom_buttons:
            try:
                button.destroy()
            except Exception:
                pass
        self.rom_buttons = []
        
        # Clear scrollable frame - destroy all widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Use grid for consistency with _update_grid
        # Show message using grid layout
        message_frame = tk.Frame(self.scrollable_frame, bg="#2d2d2d")
        message_frame.grid(row=0, column=0, sticky="nsew", padx=50, pady=100)
        
        # Configure grid weights for centering
        self.scrollable_frame.rowconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(0, weight=1)
        
        message_label = tk.Label(
            message_frame,
            text="Scanning ROMs...",
            bg="#2d2d2d",
            fg="#ffffff",
            font=("Arial", 16, "bold"),
            justify="center"
        )
        message_label.grid(row=0, column=0, pady=20)
        
        instruction_label = tk.Label(
            message_frame,
            text="Please wait while ROMs are being scanned and cached.",
            bg="#2d2d2d",
            fg="#888888",
            font=("Arial", 12),
            justify="center"
        )
        instruction_label.grid(row=1, column=0, pady=10)
    
    def on_rom_scan_complete(self):
        """Called when ROM scanning is complete for all emulators"""
        # Reload ROMs from cache now that scanning is complete
        self.load_roms()
    
    def _get_all_rom_directories(self):
        """Get all possible ROM directories for this emulator"""
        directories = []
        
        # 1. Default ROM directory
        default_rom_dir = self.path_manager.get_path("roms") / self.short_emulator_name
        directories.append(default_rom_dir)
        
        # 2. Check if there's a global custom root with ROMs
        if self.path_manager.is_global_custom_path_active():
            global_root = self.path_manager.get_active_root_path()
            custom_rom_dir = global_root / "linux-gaming-center" / "roms" / self.short_emulator_name
            if custom_rom_dir != default_rom_dir:
                directories.append(custom_rom_dir)
        
        # 3. Check for individual custom ROM path
        individual_rom_path = self.path_manager.get_individual_custom_path("roms")
        if individual_rom_path:
            individual_rom_dir = individual_rom_path / self.short_emulator_name
            if individual_rom_dir not in directories:
                directories.append(individual_rom_dir)
        
        return directories
    
    def _get_boxart_path(self, rom_path):
        """Get the boxart file path for a ROM if it exists in media/box2dfront/
        
        Matches ROM filename (without extension) to image filename (without extension).
        Example: ROM "Aladdin (USA).zip" -> boxart "Aladdin (USA).png"
        """
        if not PIL_AVAILABLE:
            return None
        
        # Get ROM name without extension (stem)
        rom_name = Path(rom_path).stem
        
        # Ensure box2dfront_directory is set
        if not self.box2dfront_directory:
            rom_dirs = self._get_all_rom_directories()
            for rom_dir in rom_dirs:
                media_dir = rom_dir / "media" / "box2dfront"
                if media_dir.exists():
                    self.box2dfront_directory = media_dir
                    break
            # If still not found, use the first ROM directory
            if not self.box2dfront_directory and rom_dirs:
                self.box2dfront_directory = rom_dirs[0] / "media" / "box2dfront"
        
        # Check media/box2dfront/ directory
        if self.box2dfront_directory and self.box2dfront_directory.exists():
            # Look for boxart files - try .jpg, .png first
            # Files are named after the ROM stem (without extension), e.g. "Aladdin (USA).png"
            for ext in ['.jpg', '.jpeg', '.png']:
                boxart_path = self.box2dfront_directory / f"{{rom_name}}{{ext}}"
                if boxart_path.exists():
                    return boxart_path
        
        return None
    
    def _preload_all_pil_images(self):
        """Load PIL Images from ROM cache manager's pre-loaded image cache.
        Images are already pre-loaded during app startup, just copy them to local cache."""
        if not PIL_AVAILABLE or not self.rom_cache_manager:
            return
        
        # Copy pre-loaded images from ROM cache manager to local cache
        loaded_count = 0
        for rom_path in self.roms:
            # Get pre-loaded PIL Image from ROM cache manager
            pil_img = self.rom_cache_manager.get_image_cache(self.short_emulator_name, rom_path)
            if pil_img:
                # Store in local cache
                self.rom_pil_cache[rom_path] = pil_img
                loaded_count += 1
        
        if loaded_count > 0:
            print(f"Loaded {{loaded_count}} pre-cached boxart images for {{self.emulator_name}}")
    
    def _load_boxart_image(self, rom_path):
        """Load PhotoImage from cached PIL Image, creating it on-demand.
        Only creates PhotoImage (X11 resource) when needed for display."""
        # Check if PhotoImage already exists (X11 resource)
        if rom_path in self.rom_images:
            return self.rom_images[rom_path]
        
        # Check if PIL is available
        if not PIL_AVAILABLE:
            return None
        
        # Check if we have a cached PIL Image
        if rom_path not in self.rom_pil_cache:
            # Try to load PIL Image on-demand (shouldn't happen if preload worked)
            boxart_path = self._get_boxart_path(rom_path)
            if not boxart_path:
                return None
            
            try:
                target_width = max(1, self.button_width - 20)
                target_height = max(1, self.button_height - 40)
                
                img = Image.open(boxart_path)
                if img.width <= 0 or img.height <= 0 or target_width <= 0 or target_height <= 0:
                    return None
                
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                
                img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                if img.width <= 0 or img.height <= 0:
                    return None
                
                self.rom_pil_cache[rom_path] = img
            except Exception:
                return None
        
        # Get cached PIL Image
        pil_img = self.rom_pil_cache[rom_path]
        
        try:
            # Limit PhotoImage cache size to prevent X11 resource exhaustion (50 max)
            MAX_PHOTOIMAGES = 50
            if len(self.rom_images) >= MAX_PHOTOIMAGES:
                # Remove first (oldest) entry
                oldest_rom = next(iter(self.rom_images))
                del self.rom_images[oldest_rom]
            
            # Create PhotoImage from cached PIL Image (this creates X11 pixmap)
            photo = ImageTk.PhotoImage(pil_img)
            
            if photo is None:
                return None
            
            # Store PhotoImage (X11 resource)
            self.rom_images[rom_path] = photo
            return photo
        except Exception as e:
            # Failed to create PhotoImage - may be X11 resource limit
            return None
    
    def filter_roms(self):
        """Filter ROMs based on search query and update grid"""
        # Check if UI is ready
        if not hasattr(self, 'scrollable_frame'):
            return
        
        try:
            search_query = self.search_var.get().lower().strip()
            
            if search_query:
                self.filtered_roms = [rom for rom in self.roms 
                                    if search_query in os.path.basename(rom).lower()]
            else:
                self.filtered_roms = self.roms.copy()
            
            self._update_grid()
        except Exception as e:
            print(f"Error filtering ROMs: {{e}}")
            import traceback
            traceback.print_exc()
    
    def _update_grid(self):
        """Update the grid display with current filtered ROMs"""
        # Check if UI is ready
        if not hasattr(self, 'scrollable_frame'):
            return
        
        try:
            # Clear existing buttons
            for button in self.rom_buttons:
                try:
                    button.destroy()
                except Exception:
                    pass
            self.rom_buttons = []
            
            # Clear scrollable frame - destroy all widgets to avoid geometry manager conflicts
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()
            
            if not self.filtered_roms:
                no_roms_label = ttk.Label(self.scrollable_frame, 
                                         text="No ROMs found",
                                         font=("Arial", 14))
                no_roms_label.grid(row=0, column=0, columnspan=self.columns, pady=50)
                return
            
            # Calculate target dimensions for image buttons
            target_width = max(1, self.button_width - 20)
            target_height = max(1, self.button_height - 40)
            
            # Calculate columns based on canvas width
            canvas_width = self.canvas.winfo_width()
            if canvas_width < 1:
                canvas_width = 800  # Default width
            self.columns = max(1, (canvas_width - 40) // (self.button_width + self.button_padding * 2))
            
            # Enable boxart images but use virtual scrolling
            # Only create PhotoImage objects for visible buttons to prevent X11 exhaustion
            ENABLE_IMAGES = True
            
            # Display ALL ROMs (no limit) - let them wrap and scroll with mousewheel
            roms_to_display = self.filtered_roms
            
            # Create grid of buttons (all ROMs, wrapping across screen)
            # DO NOT create PhotoImage objects here - create them on-demand when visible
            # This prevents X11 resource exhaustion for large ROM collections
            row = 0
            col = 0
            
            for idx, rom_path in enumerate(roms_to_display):
                rom_name = os.path.basename(rom_path)
                display_name = rom_name[:30] + "..." if len(rom_name) > 30 else rom_name
                
                # Create button WITHOUT PhotoImage first (will be loaded on-demand when visible)
                # Check if we have a pre-loaded PIL Image (from cache manager)
                has_image = False
                if ENABLE_IMAGES and self.rom_cache_manager:
                    try:
                        # Check if PIL Image is pre-loaded (no X11 resource)
                        pil_img = self.rom_cache_manager.get_image_cache(self.short_emulator_name, rom_path)
                        if pil_img:
                            has_image = True
                    except Exception:
                        pass
                
                # For now, create button with text only - image will be added when visible
                img = None
                
                if img:
                    # Button with boxart image ONLY (no text, no border)
                    try:
                        btn = tk.Button(self.scrollable_frame,
                                      image=img,
                                      bg="#1e1e1e",
                                      activebackground="#2d2d2d",
                                      relief="flat",
                                      borderwidth=0,
                                      padx=5,
                                      pady=5,
                                      command=lambda rp=rom_path: self.launch_selected_rom(rp))
                        # Keep reference to image to prevent garbage collection
                        btn.image = img
                        self.rom_buttons.append(btn)
                    except Exception as e:
                        # Fallback to text-only button if image fails
                        img = None
                
                if not img:
                    # Button with text only (no boxart found, or image loading disabled, no border)
                    btn = tk.Button(self.scrollable_frame,
                                  text=display_name,
                                  bg="#2d2d2d",
                                  fg="white",
                                  activebackground="#3d3d3d",
                                  activeforeground="white",
                                  font=("Arial", 10),
                                  wraplength=max(50, self.button_width - 10),
                                  relief="flat",
                                  borderwidth=0,
                                  padx=10,
                                  pady=10,
                                  command=lambda rp=rom_path: self.launch_selected_rom(rp))
                    self.rom_buttons.append(btn)
                
                # Grid the button (will wrap to next row automatically)
                btn.grid(row=row, column=col,
                        padx=self.button_padding,
                        pady=self.button_padding,
                        sticky="nsew")
                
                # Store button info for lazy image loading on scroll
                btn.rom_path = rom_path
                btn.row = row
                btn.col = col
                btn.has_pil_image = has_image  # Track if PIL image exists (not yet PhotoImage)
                
                col += 1
                if col >= self.columns:
                    col = 0
                    row += 1
            
            # Configure grid weights for responsiveness - buttons span across screen
            self.scrollable_frame.columnconfigure(tuple(range(self.columns)), weight=1, uniform="rom_buttons")
            
            # Update canvas scroll region after grid is populated
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            # Update visible images after grid is created (loads PhotoImage for visible buttons only)
            self.after(100, self._update_visible_images)
        except Exception as e:
            print(f"Error updating grid: {{e}}")
            import traceback
            traceback.print_exc()
    
    def scroll_to_letter(self, letter):
        """Scroll to the first ROM starting with the given letter/number"""
        if not self.filtered_roms or not self.rom_buttons:
            return
        
        try:
            # Find first ROM starting with letter
            target_index = None
            for i, rom_path in enumerate(self.filtered_roms):
                rom_name = os.path.basename(rom_path)
                first_char = rom_name[0].upper() if rom_name else ""
                
                # Handle numbers (0-9) and # symbol
                if letter == "#":
                    if first_char.isdigit():
                        target_index = i
                        break
                # Handle numbers 0-9
                elif letter.isdigit() and first_char == letter:
                    target_index = i
                    break
                # Handle letters A-Z
                elif letter.isalpha() and first_char == letter.upper():
                    target_index = i
                    break
            
            if target_index is not None and target_index < len(self.rom_buttons):
                # Get the button
                button = self.rom_buttons[target_index]
                # Update canvas to ensure button is positioned
                self.canvas.update_idletasks()
                self.scrollable_frame.update_idletasks()
                
                # Get button grid position
                grid_info = button.grid_info()
                row = grid_info.get("row", 0)
                # Get total height of scrollable frame
                frame_height = self.scrollable_frame.winfo_reqheight()
                
                if frame_height > 0:
                    # Calculate scroll position (0.0 to 1.0) based on row
                    # Estimate button position based on row number
                    button_y = row * (self.button_height + self.button_padding * 2)
                    # Get canvas visible height
                    canvas_height = self.canvas.winfo_height()
                    # Calculate scroll position to show button near top
                    scroll_pos = max(0.0, min(1.0, button_y / max(1, frame_height - canvas_height)))
                    self.canvas.yview_moveto(scroll_pos)
        except Exception as e:
            print(f"Error scrolling to letter {{letter}}: {{e}}")
            import traceback
            traceback.print_exc()

    def _load_roms_from_directory(self):
        """Legacy method to load ROMs by scanning directory"""
        # MODIFIED: Use Path object for .is_dir() check
        if not Path(self.rom_directory).is_dir():
            messagebox.showwarning("Invalid Directory", f"ROM directory '{{self.rom_directory}}' does not exist or is not a directory.")
            return

        try:
            for root, _, files in os.walk(self.rom_directory):
                for filename in files:
                    if any(filename.lower().endswith(ext) for ext in ROM_EXTENSIONS):
                        full_rom_path = Path(root) / filename # MODIFIED: Use Path for concatenation
                        self.roms.append(str(full_rom_path)) # Store as string
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load ROMs from '{{self.rom_directory}}': {{e}}")

    def launch_selected_rom(self, rom_path=None):
        """Launches the selected ROM using the associated .sh script, or a specified rom_path."""
        if rom_path is None:
            messagebox.showwarning("No ROM Selected", "Please select a ROM to launch.")
            return

        # MODIFIED: Use Path object for .exists() check
        if not Path(rom_path).exists():
            messagebox.showerror("File Not Found", f"ROM file not found: {{rom_path}}")
            self.load_roms() # Refresh list in case file was deleted
            return

        # MODIFIED: Use Path object for .exists() check
        if not Path(self.run_script_path).exists():
            messagebox.showerror("Script Not Found", f"Emulator launch script not found: {{self.run_script_path}}")
            return

        print(f"Attempting to launch {{os.path.basename(rom_path)}} using script: {{self.run_script_path}}")

        try:
            subprocess.Popen([self.run_script_path, rom_path])

            self.rom_play_history[rom_path] = datetime.datetime.now().isoformat()
            self.save_rom_play_history()

            if "DashboardFrame" in self.controller.frames and self.controller.frames["DashboardFrame"]:
                self.controller.frames["DashboardFrame"].update_dashboard()

        except FileNotFoundError:
            print(f"Could not find the script executable at: {{self.run_script_path}}")
            messagebox.showerror("Error", f"Could not find the script executable at: {{self.run_script_path}}")
        except PermissionError:
            print(f"Permission denied to execute script: {{self.run_script_path}}")
            messagebox.showerror("Permission Denied", f"Permission denied to execute script: {{self.run_script_path}}.\\nMake sure it's executable (chmod +x).")
        except Exception as e:
            print(f"An error occurred while launching '{{os.path.basename(rom_path)}}' via script:\\n{{e}}")
            messagebox.showerror("Launch Error", f"An error occurred while launching '{{os.path.basename(rom_path)}}' via script:\\n{{e}}")


    def get_recently_played_roms(self, num_items=5):
        """
        Returns a list of recently played ROMs for this specific emulator.
        Each item includes 'name' (ROM filename), 'last_played', 'emulator_name', and 'rom_path'.
        """
        recent_roms = []
        for rom_path, last_played_str in self.rom_play_history.items():
            try:
                last_played_dt = datetime.datetime.fromisoformat(last_played_str)
                recent_roms.append({{
                    "name": os.path.basename(rom_path),
                    "last_played": last_played_dt,
                    "emulator_name": self.emulator_name,
                    "rom_path": rom_path,
                    "emulator_frame_name": self.__class__.__name__
                }})
            except ValueError:
                continue

        recent_roms.sort(key=lambda x: x["last_played"], reverse=True)
        return recent_roms[:num_items]
'''

    with open(file_path, "w") as f:
        f.write(file_content)

