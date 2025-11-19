import json
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import datetime
from PIL import Image
try:
    from PIL import ImageTk
except ImportError:
    # Fallback for systems where ImageTk is not available
    import tkinter as tk
    class ImageTk:
        @staticmethod
        def PhotoImage(image):
            return tk.PhotoImage()
import shlex # Import shlex for safe command parsing
import importlib.util # For dynamic module loading
from .emulator_template_generator import generate_emulator_frame_file
import random # NEW: Import random for selecting a random ROM
from pathlib import Path # <-- NEW: Import Path from pathlib
from typing import List # Import List for type hints

# Import the PathManager
from paths import PathManager # <-- NEW: Import PathManager

# REMOVED: Old hardcoded BASE_DATA_DIR, USER_ROMS_BASE_DIR, USER_BIOS_BASE_DIR, etc.
# These will now be obtained dynamically from PathManager.

class EmulatorsFrame(ttk.Frame):
    def __init__(self, parent, controller, path_manager):
        super().__init__(parent)

        self.controller = controller
        # NEW: Get the path_manager instance from the controller
        self.path_manager = path_manager
        self.rom_cache_manager = None  # Will be set by main.py

        self.icons = []
        self.emulators_data = []
        self.emulator_widgets = []
        self.emulator_mappings = self.load_emulator_mappings()

        # Scaling setup
        self.screen_width = self.winfo_screenwidth()
        self.scale = self.screen_width / 1920
        self.scale = max(0.8, min(self.scale, 1.25))

        # Scaled dimensions
        self.BUTTON_WIDTH = int(200 * self.scale)
        self.BUTTON_HEIGHT = int(150 * self.scale)
        self.BUTTON_PADDING = int(20 * self.scale)
        self.FRAME_PADDING = int(20 * self.scale)
        self.IMAGE_PADDING = int(10 * self.scale)

        self.theme = self.controller.get_theme_for_emulators_frame()

        self.configure_style()

        self.last_width = 0
        self.initial_load_complete = False
        self.current_menu = None

        self["style"] = "Emulator.TFrame"
        self.bind("<Visibility>", self.on_visibility_change)
        self.controller.bind("<Configure>", self.on_main_window_configure)

        self.setup_ui()
        self.load_emulators()
        self.after(200, self.perform_initial_redraw)

        # Removed: self.controller.frames["EmulatorsFrame"] = self
        # This assignment should happen in main.py's load_all_frames,
        # where all frames are registered.

        print("INFO: EmulatorsFrame initialized. Remember to call load_all_dynamic_emulator_frames_at_startup() from your main Controller.")

    def set_rom_cache_manager(self, rom_cache_manager):
        """Set the ROM cache manager instance"""
        self.rom_cache_manager = rom_cache_manager


    def load_emulator_mappings(self):
        """Loads the emulator long_name to short_name mappings from a JSON file."""
        # MODIFIED: Use the hardcoded path for resources_dir as specified by the user
        resources_dir = Path("/opt/linux-gaming-center/resources")
        EMULATOR_MAPPINGS_FILE = resources_dir / "emulator_mappings.json"

        if not EMULATOR_MAPPINGS_FILE.exists():
            messagebox.showerror("Error", f"Emulator mappings file not found: {EMULATOR_MAPPINGS_FILE}\n"
                                          "Please create it with the format: {'Full Name': 'short_name'}")
            return {}
        try:
            with open(EMULATOR_MAPPINGS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            messagebox.showerror("Error", f"Malformed JSON in {EMULATOR_MAPPINGS_FILE}: {e}\n"
                                          "Please check the file format.")
            return {}
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred loading {EMULATOR_MAPPINGS_FILE}: {e}")
            return {}

    def get_short_name(self, long_name):
        """Retrieves the short name for a given long name from the mappings."""
        return self.emulator_mappings.get(long_name, long_name.lower().replace(' ', '_'))

    def get_long_name_from_short(self, short_name):
        """Retrieves the long name for a given short name from the mappings."""
        for long, short in self.emulator_mappings.items():
            if short == short_name:
                return long
        return short_name


    def setup_ui(self):
        controls_frame = ttk.Frame(self, style="Emulator.TFrame")
        controls_frame.pack(fill="x", padx=10, pady=10)

        add_button = ttk.Button(
            controls_frame,
            text="Add Emulator",
            style="Emulator.TButton",
            command=self.open_add_emulator_dialog,
        )
        add_button.pack(side="left", padx=(0, 5))

        sort_label = ttk.Label(controls_frame, text="Sort by:", style="SortLabel.TLabel")
        sort_label.pack(side="left", padx=(5, 5))

        sort_options = ["A to Z", "Z to A", "Date Added"]
        self.sort_var = tk.StringVar(self)
        self.sort_var.set(sort_options[2])

        sort_dropdown = ttk.Combobox(
            controls_frame,
            textvariable=self.sort_var,
            values=sort_options,
            state="readonly",
            style="Sort.TCombobox",
        )
        sort_dropdown.pack(side="left", padx=(5, 0))
        sort_dropdown.bind("<<ComboboxSelected>>", self.sort_emulators)

        # All ROMs button
        all_roms_button = ttk.Button(
            controls_frame,
            text="All ROMs",
            style="Emulator.TButton", # Reusing existing button style
            command=lambda: self.controller.show_frame("AllRomsFrame") # Command to show the new frame
        )
        all_roms_button.pack(side="left", padx=(15, 0)) # Add some padding to separate it

        # NEW: Random Game button
        random_game_button = ttk.Button(
            controls_frame,
            text="Random Game",
            style="Emulator.TButton",
            command=self.launch_random_rom # Call the new method
        )
        random_game_button.pack(side="left", padx=(5, 0)) # Add some padding

        self.canvas = tk.Canvas(
            self,
            bg=self.theme.get("background", "#1e1e1e"),
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.grid_frame = ttk.Frame(self.canvas, style="Emulator.TFrame")
        self.grid_frame_id = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.bind_mousewheel_events()

    def open_edit_emulator_dialog(self, index):
        """Open dialog to edit the selected emulator."""
        emulator_info = self.emulators_data[index]
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Emulator: {emulator_info.get('full_name', 'Unknown Emulator')}")
        dialog.configure(bg=self.theme.get("background", "#1e1e1e"))

        dialog.transient(self)
        dialog.grab_set()

        def themed_label(master, text, row, col=0, sticky="w", padx=5, pady=5):
            label = ttk.Label(master, text=text, style="Emulator.TLabel")
            label.grid(row=row, column=col, sticky=sticky, padx=padx, pady=pady)
            return label

        def themed_entry(master, var=None, row=0, col=1, columnspan=1, sticky="ew", padx=5, pady=5):
            entry = ttk.Entry(master, textvariable=var) if var else ttk.Entry(master)
            entry.grid(row=row, column=col, columnspan=columnspan, sticky="ew", padx=5, pady=5)
            return entry

        dialog.columnconfigure(1, weight=1)

        try:
            # --- Name (now read-only, showing full name) ---
            themed_label(dialog, "Emulator Name:", 0)
            name_display_label = ttk.Label(
                dialog,
                text=emulator_info.get("full_name", ""),
                style="Emulator.TLabel",
                anchor="w"
            )
            name_display_label.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

            short_name = emulator_info.get("short_name", "")

            # --- Image ---
            themed_label(dialog, "Current Image:", 1)
            current_image_label = ttk.Label(
                dialog,
                text=os.path.basename(emulator_info.get("image", "No Image Selected")),
                style="Emulator.TLabel",
            )
            current_image_label.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

            themed_label(dialog, "Select New Image:", 2)
            new_image_path_var = tk.StringVar()
            new_image_entry = themed_entry(dialog, new_image_path_var, row=2)
            ttk.Button(
                dialog,
                text="Browse",
                style="Emulator.TButton",
                command=lambda: self.browse_image(new_image_path_var),
            ).grid(row=2, column=2, padx=5)

            # --- ROM Directory Info (Display Only) ---
            themed_label(dialog, "ROMs Directory (Default):", 3)
            rom_dir_display_label = ttk.Label(
                dialog,
                # MODIFIED: Use path_manager to get the current ROM directory
                text=self.path_manager.get_path("roms") / short_name, # Display the actual path being used
                style="Emulator.TLabel",
                wraplength=400,
                justify="left"
            )
            rom_dir_display_label.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

            # --- BIOS Directory Info (Display Only) ---
            themed_label(dialog, "BIOS Directory (Default):", 4)
            bios_dir_display_label = ttk.Label(
                dialog,
                # MODIFIED: Use path_manager to get the current BIOS directory
                text=self.path_manager.get_path("bios") / short_name, # Display the actual path being used
                style="Emulator.TLabel",
                wraplength=400,
                justify="left"
            )
            bios_dir_display_label.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5, pady=5)


            # --- Emulator Run Command Edit Button ---
            themed_label(dialog, "Emulator Run Command:", 5)
            ttk.Button(
                dialog,
                text="Edit",
                style="Emulator.TButton",
                command=lambda: self.open_script_for_editing(emulator_info.get("run_script_path")),
            ).grid(row=5, column=1, sticky="ew", padx=5, pady=5)

            # --- Emulator Config Command Edit Button ---
            themed_label(dialog, "Emulator Config Command:", 6)
            ttk.Button(
                dialog,
                text="Edit",
                style="Emulator.TButton",
                command=lambda: self.open_script_for_editing(emulator_info.get("config_script_path")),
            ).grid(row=6, column=1, sticky="ew", padx=5, pady=5)


            # --- Save Changes Button ---
            def save_changes():
                new_image_path = new_image_path_var.get()

                old_image_path = emulator_info["image"]

                emulator_folder_name = short_name

                # MODIFIED: Use path_manager for EMULATOR_RUN_SCRIPT_DIR
                EMULATOR_RUN_SCRIPT_DIR = self.path_manager.get_path("data") / "emulators" / "run"
                new_run_sh_filename = f"{emulator_folder_name}.sh"
                new_config_sh_filename = f"{emulator_folder_name}_config.sh"

                new_run_sh_path = EMULATOR_RUN_SCRIPT_DIR / emulator_folder_name / new_run_sh_filename
                new_config_sh_path = EMULATOR_RUN_SCRIPT_DIR / emulator_folder_name / new_config_sh_filename

                # MODIFIED: Use path_manager for EMULATOR_LIBRARIES_DIR
                EMULATOR_LIBRARIES_DIR = self.path_manager.get_path("data") / "emulators" / "custom_frames"
                new_emulator_py_filename = f"{emulator_folder_name}_emulator.py"
                new_emulator_py_path = EMULATOR_LIBRARIES_DIR / new_emulator_py_filename

                # Handle new image upload
                if new_image_path:
                    # MODIFIED: Use path_manager for IMAGE_DIR
                    IMAGE_DIR = self.path_manager.get_path("data") / "emulators" / "assets"
                    os.makedirs(IMAGE_DIR, exist_ok=True)
                    _ , ext = os.path.splitext(new_image_path)
                    new_image_filepath = IMAGE_DIR / f"{short_name}{ext}"
                    try:
                        shutil.copy(new_image_path, new_image_filepath) # Corrected: use new_image_path, not image_path
                        emulator_info["image"] = str(new_image_filepath) # Store as string
                        if old_image_path and os.path.exists(old_image_path) and old_image_path != str(new_image_filepath):
                            os.remove(old_image_path)
                    except Exception as e:
                        messagebox.showerror("Error", f"Error updating image: {e}")
                        return
                elif not emulator_info["image"]:
                    # MODIFIED: Use path_manager for IMAGE_DIR
                    IMAGE_DIR = self.path_manager.get_path("data") / "emulators" / "assets"
                    default_image_found = False
                    for ext in [".png", ".jpg", ".jpeg", ".gif"]:
                        potential_default_path = IMAGE_DIR / f"{short_name}{ext}"
                        if potential_default_path.exists():
                            emulator_info["image"] = str(potential_default_path)
                            default_image_found = True
                            break
                    if not default_image_found:
                        emulator_info["image"] = ""


                try:
                    # MODIFIED: Use path_manager for rom_directory and bios_directory
                    rom_directory = self.path_manager.get_path("roms") / short_name
                    bios_directory = self.path_manager.get_path("bios") / short_name
                    generate_emulator_frame_file(
                        str(new_emulator_py_path), # Pass as string
                        emulator_info["full_name"],
                        short_name,
                        str(new_run_sh_path), # Pass as string
                        str(rom_directory), # Pass as string
                        str(bios_directory) # Pass as string
                    )
                    emulator_info["emulator_py_path"] = str(new_emulator_py_path) # Store as string

                except Exception as e:
                    messagebox.showerror("Error", f"Error updating emulator files: {e}")
                    return

                # Save updated data to JSON
                # MODIFIED: Use path_manager for DATA_FILE
                DATA_FILE = self.path_manager.get_path("data") / "emulators" / "emulators.json"
                try:
                    with open(DATA_FILE, "w") as f:
                        json.dump(self.emulators_data, f, indent=4)

                    base_name = str(new_emulator_py_path).replace('_emulator.py', '') # Convert to string for replace
                    class_name_parts = [part.capitalize() for part in os.path.basename(base_name).split('_')]
                    dynamic_frame_class_name = "".join(class_name_parts) + "EmulatorFrame"

                    if self.controller.register_dynamic_frame(str(new_emulator_py_path), dynamic_frame_class_name): # Pass as string
                        print(f"Successfully updated and registered frame: {dynamic_frame_class_name}")
                    else:
                        print(f"Warning: Could not register updated frame: {dynamic_frame_class_name}")

                    dialog.destroy()
                    self.after(50, self.sort_emulators)

                except Exception as e:
                    messagebox.showerror("Error", f"Error saving emulator data: {e}")

            ttk.Button(
                dialog, text="Save Changes", style="Emulator.TButton", command=save_changes
            ).grid(row=7, column=0, columnspan=3, pady=10)

            dialog.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while opening the edit dialog: {e}")
            import traceback
            traceback.print_exc()
            dialog.destroy()

        dialog.wait_window()

    def browse_image(self, path_var):
        """Select image file."""
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")]
        )
        if file_path:
            path_var.set(file_path)

    def browse_directory(self, path_var):
        """Opens a directory selection dialog and sets the path_var."""
        directory_path = filedialog.askdirectory(title="Select ROMs Directory")
        if directory_path:
            path_var.set(directory_path)

    def perform_initial_redraw(self):
        """Perform initial redraw after a delay."""
        self.initial_load_complete = True
        self.force_redraw()

    def on_main_window_configure(self, event=None):
        """Handle the main window's resize event."""
        current_width = self.winfo_width()
        if current_width > 0 and current_width != self.last_width:
            self.last_width = current_width
            self.after(100, self.delayed_redraw)

    def on_visibility_change(self, event=None):
        """Handle frame becoming visible"""
        current_width = self.winfo_width()
        if current_width > 0 and current_width != self.last_width:
            self.last_width = current_width
            self.after(100, self.delayed_redraw)

    def delayed_redraw(self):
        """Delayed call to force redraw."""
        self.force_redraw()

    def force_redraw(self):
        """Force a complete redraw of the grid"""
        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 0:
            return

        self.canvas.config(width=canvas_width)

        for button_frame in self.emulator_widgets:
            button_frame.destroy()
        self.emulator_widgets = []
        self.icons = []

        if hasattr(self, "grid_frame"):
            self.grid_frame.destroy()

        self.grid_frame = ttk.Frame(self.canvas, style="Emulator.TFrame")
        self.grid_frame_id = self.canvas.create_window(
            (0, 0), window=self.grid_frame, anchor="nw"
        )

        for entry in self.emulators_data:
            self.add_emulator_icon(entry)

        self.redraw_grid()

        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        self.update()
        self.update_idletasks()

    def get_theme_for_emulators_frame(self):
        """Load theme settings for EmulatorsFrame from JSON file."""
        # MODIFIED: Use path_manager to get themes directory
        theme_file = self.path_manager.get_path("themes") / "cosmictwilight" / "styles" / "emulators.json"
        if theme_file.exists(): # Use .exists() for Path objects
            with open(theme_file, "r") as f:
                return json.load(f)
        return {
            "background": "#1e1e1e",
            "text_color": "#ffffff",
            "font_family": "Segoe UI",
            "font_size": 11,
        }

    def configure_style(self):
        """Configure ttk styles based on theme."""
        style = ttk.Style()
        bg = self.theme.get("background", "#1e1e1e")
        fg = self.theme.get("text_color", "#ffffff")
        font_family = self.theme.get("font_family", "Segoe UI")
        font_size = int(self.theme.get("font_size", 11) * self.scale)

        style.configure("Emulator.TFrame", background=bg)
        style.configure(
            "Emulator.TLabel",
            background=bg,
            foreground=fg,
            font=(font_family, font_size),
            anchor="center",
        )
        style.configure(
            "Emulator.TButton",
            background=bg,
            foreground=fg,
            font=(font_family, font_size + 1),
            padding=6,
        )
        style.configure(
            "Sort.TCombobox",
            background=bg,
            foreground=fg,
            font=(font_family, font_size),
        )
        style.configure(
            "SortLabel.TLabel",
            background=bg,
            foreground=fg,
            font=(font_family, font_size),
            anchor="w",
        )

    def bind_mousewheel_events(self):
        """Bind mouse wheel events for cross-platform compatibility"""
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.on_mousewheel_scroll(-1))
        self.canvas.bind_all("<Button-5>", lambda e: self.on_mousewheel_scroll(1))
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling on Windows/Mac"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_scroll(self, direction):
        """Handle mouse wheel scrolling on Linux"""
        self.canvas.yview_scroll(direction, "units")

    def on_canvas_resize(self, event):
        """Handle canvas resize events"""
        if event.width <= 0:
            return

        self.last_width = event.width
        self.canvas.config(width=event.width)
        self.canvas.itemconfig(self.grid_frame_id, width=event.width)
        self.after(50, self.redraw_grid)

    def calculate_grid_layout(self, available_width):
        """Calculate optimal grid layout based on available width"""
        if available_width <= 0:
            return 1, 0

        min_item_width = self.BUTTON_WIDTH + self.BUTTON_PADDING
        max_columns = max(1, (available_width - 2 * self.FRAME_PADDING) // min_item_width)

        total_content_width = max_columns * min_item_width - self.BUTTON_PADDING
        remaining_space = max(
            0, available_width - total_content_width - 2 * self.FRAME_PADDING
        )
        extra_padding = remaining_space // (max_columns + 1)

        return max_columns, extra_padding

    def redraw_grid(self):
        """Reorganize buttons in a grid based on current width"""
        if not self.emulator_widgets:
            return

        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 0:
            return

        for widget in self.grid_frame.winfo_children():
            widget.grid_forget()

        columns, extra_padding = self.calculate_grid_layout(canvas_width)

        for idx, button_frame in enumerate(self.emulator_widgets):
            row = idx // columns
            col = idx % columns

            left_pad = (
                self.FRAME_PADDING + extra_padding
                if col == 0
                else self.BUTTON_PADDING // 2 + extra_padding
            )
            right_pad = (
                self.FRAME_PADDING + extra_padding
                if col == columns - 1
                else self.BUTTON_PADDING // 2 + extra_padding
            )

            button_frame.grid(
                row=row,
                column=col,
                padx=(left_pad, right_pad),
                pady=int(10 * self.scale),
                sticky="nsew"
            )

        for col in range(columns):
            self.grid_frame.columnconfigure(col, weight=1, uniform="emulator_cols")

        rows = (len(self.emulator_widgets) + columns - 1) // columns
        total_height = rows * (self.BUTTON_HEIGHT + int(10 * self.scale))
        self.grid_frame.config(height=total_height)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.update_idletasks()

    def _read_sh_script_file(self, script_path):
        """
        Helper function to read the content of a .sh script file.
        Returns an empty string if the file doesn't exist or an error occurs.
        """
        if not script_path or not os.path.exists(script_path):
            return ""
        try:
            with open(script_path, "r") as f:
                lines = f.readlines()
                if lines and lines[0].strip().startswith("#!/"):
                    return "".join(lines[1:]).strip()
                return "".join(lines).strip()
        except Exception as e:
            print(f"Error reading script file {script_path}: {e}")
            return ""

    def _write_sh_script_file(self, script_path, command_content, add_rom_arg=False):
        """
        Helper function to create a .sh script file with the provided command content.
        Makes the script executable.
        """
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        try:
            with open(script_path, "w") as f:
                f.write(f"#!/bin/bash\n")
                if add_rom_arg:
                    if "$1" not in command_content:
                        f.write(f"{command_content} \"$1\"\n")
                    else:
                        f.write(f"{command_content}\n")
                else:
                    f.write(f"{command_content}\n")
            os.chmod(script_path, 0o755)
            print(f"Created executable script: {script_path}")
        except Exception as e:
            raise Exception(f"Failed to create executable script {script_path}: {e}")

    def create_emulator_py_file(self, file_path, full_emulator_name, short_emulator_name, run_script_path, rom_directory, bios_directory):
        """
        Creates a Python file for the new emulator's library,
        including logic to list and launch ROMs using the .sh script.
        This now delegates to the external generate_emulator_frame_file function.
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        generate_emulator_frame_file(file_path, full_emulator_name, short_emulator_name, run_script_path, rom_directory, bios_directory)


    def open_add_emulator_dialog(self):
        """Create dialog for adding new emulator"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Emulator")
        dialog.configure(bg=self.theme.get("background", "#1e1e1e"))

        def themed_label(master, text, row):
            label = ttk.Label(master, text=text, style="Emulator.TLabel")
            label.grid(row=row, column=0, sticky="w", padx=5, pady=5)
            return label

        def themed_entry(master, var=None, row=0, col=1, columnspan=1):
            entry = ttk.Entry(master, textvariable=var) if var else ttk.Entry(master)
            entry.grid(
                row=row, column=col, columnspan=columnspan, sticky="ew", padx=5, pady=5
            )
            return entry

        dialog.columnconfigure(1, weight=1)

        # 1. Emulator name drop down list
        themed_label(dialog, "Emulator Name:", 0)
        emulator_names = list(self.emulator_mappings.keys())
        if not emulator_names:
            messagebox.showwarning("No Emulators Defined",
                                   f"No emulator mappings found. Please add entries to your emulator_mappings.json file (located in {self.path_manager.get_path('data_root') / 'resources'}) before adding an emulator.")
            dialog.destroy()
            return

        name_var = tk.StringVar(self)
        name_dropdown = ttk.Combobox(
            dialog,
            textvariable=name_var,
            values=emulator_names,
            state="readonly",
            style="Sort.TCombobox",
        )
        name_dropdown.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)

        # 2. Reintroduce image selection (row adjusted to 1)
        themed_label(dialog, "Select Image (Optional):", 1)
        image_path_var = tk.StringVar()
        image_entry = themed_entry(dialog, image_path_var, row=1)
        ttk.Button(
            dialog,
            text="Browse",
            style="Emulator.TButton",
            command=lambda: self.browse_image(image_path_var),
        ).grid(row=1, column=2, padx=5)

        # 3 & 4. Informative text for .sh files and default ROMs/BIOS directories
        info_label_text_var = tk.StringVar()
        info_label = ttk.Label(
            dialog,
            textvariable=info_label_text_var,
            style="Emulator.TLabel",
            wraplength=400,
            justify="left"
        )
        # Row adjusted to 2 as the ROMs directory selection was removed
        info_label.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky="w")

        def update_info_label(*args):
            selected_full_name = name_var.get()
            if selected_full_name:
                short_name = self.get_short_name(selected_full_name)

                # MODIFIED: Use path_manager for all these paths
                roms_default_path_example = self.path_manager.get_path("roms") / short_name
                bios_default_path_example = self.path_manager.get_path("bios") / short_name
                emulator_run_script_dir = self.path_manager.get_path("data") / "emulators" / "run"
                run_script_path_example = emulator_run_script_dir / short_name / f"{short_name}.sh"

                info_label_text_var.set(
                    f"ROMs should be placed in:\n"
                    f"'{roms_default_path_example}'\n\n"
                    f"BIOS files should be placed in:\n"
                    f"'{bios_default_path_example}'\n\n"
                    f"Please add run commands for '{selected_full_name}' under:\n"
                    f"'{run_script_path_example}'\n"
                    "Ensure these directories exist or create them as needed."
                )
            else:
                info_label_text_var.set(
                    "Select an emulator from the dropdown to see its expected paths and directories."
                )

        name_var.trace_add("write", update_info_label)
        update_info_label()

        def save():
            full_name = name_var.get().strip()
            image_path = image_path_var.get().strip()

            if not full_name:
                messagebox.showerror("Error", "Please select an emulator name.")
                return

            short_name = self.get_short_name(full_name)
            if not short_name:
                messagebox.showerror("Error", f"Could not find short name mapping for '{full_name}'. Please check emulator_mappings.json.")
                return

            for emulator in self.emulators_data:
                if emulator.get("short_name") == short_name:
                    messagebox.showerror("Error", f"An emulator with the short name '{short_name}' (Full Name: '{full_name}') already exists.")
                    return

            run_command = f"# Add your ROM launch command here. Use $1 for ROM path.\n# Example: retroarch --fullscreen -L \"/usr/lib/libretro/ps2_libretro.so\" \"$1\""
            config_command = f"# Add your emulator configuration command here.\n# Example: retroarch"

            print(f"Debug - Full Name: {full_name}")
            print(f"Debug - Short Name: {short_name}")
            print(f"Debug - Run Command (default): {run_command}")
            print(f"Debug - Config Command (default): {config_command}")

            try:
                # MODIFIED: Use path_manager for all base directories
                IMAGE_DIR = self.path_manager.get_path("data") / "emulators" / "assets"
                EMULATOR_LIBRARIES_DIR = self.path_manager.get_path("data") / "emulators" / "custom_frames"
                ROMS_DATA_DIR = self.path_manager.get_path("data") / "emulators" / "rom_data"
                USER_BIOS_BASE_DIR = self.path_manager.get_path("bios") # This is the base BIOS dir

                os.makedirs(IMAGE_DIR, exist_ok=True)
                os.makedirs(EMULATOR_LIBRARIES_DIR, exist_ok=True)
                os.makedirs(ROMS_DATA_DIR, exist_ok=True)
                # Ensure the base BIOS directory exists
                os.makedirs(USER_BIOS_BASE_DIR, exist_ok=True)
                print("Debug - Core directories created/verified")

                # MODIFIED: Use path_manager for rom_directory and bios_directory
                rom_directory = self.path_manager.get_path("roms") / short_name
                bios_directory = self.path_manager.get_path("bios") / short_name

                print(f"Debug - Defaulting ROM directory to: {rom_directory}")
                print(f"Debug - Defaulting BIOS directory to: {bios_directory}")

                if not rom_directory.exists(): # Use .exists() for Path objects
                    rom_directory.mkdir(parents=True, exist_ok=True) # Use .mkdir() for Path objects
                    print(f"Debug - Created ROMs directory: {rom_directory}")
                else:
                    print(f"Debug - ROMs directory already exists: {rom_directory}")

                # Create media folder structure inside roms directory
                media_directory = rom_directory / "media"
                box2dfront_directory = media_directory / "box2dfront"
                manual_directory = media_directory / "manual"
                screenshot_directory = media_directory / "screenshot"
                steamgrid_directory = media_directory / "steamgrid"
                
                for directory in [media_directory, box2dfront_directory, manual_directory, screenshot_directory, steamgrid_directory]:
                    if not directory.exists():
                        directory.mkdir(parents=True, exist_ok=True)
                        print(f"Debug - Created directory: {directory}")
                    else:
                        print(f"Debug - Directory already exists: {directory}")

                if not bios_directory.exists(): # Use .exists() for Path objects
                    bios_directory.mkdir(parents=True, exist_ok=True) # Use .mkdir() for Path objects
                    print(f"Debug - Created BIOS directory: {bios_directory}")
                else:
                    print(f"Debug - BIOS directory already exists: {bios_directory}")


                new_image_filepath_for_json = ""
                if image_path:
                    _, ext = os.path.splitext(image_path)
                    new_image_filename = f"{short_name}{ext}"
                    destination_image_path = IMAGE_DIR / new_image_filename # Use Path object concatenation
                    try:
                        shutil.copy(image_path, destination_image_path)
                        new_image_filepath_for_json = str(destination_image_path) # Store as string
                        print(f"Debug - Copied user-selected image to: {destination_image_path}")
                    except Exception as e:
                        messagebox.showwarning("Image Copy Error", f"Could not copy selected image: {e}\nProceeding without image.")
                        for ext_check in [".png", ".jpg", ".jpeg", ".gif"]:
                            potential_default_path = IMAGE_DIR / f"{short_name}{ext_check}" # Use Path object concatenation
                            if potential_default_path.exists():
                                new_image_filepath_for_json = str(potential_default_path)
                                break
                else:
                    for ext_check in [".png", ".jpg", ".jpeg", ".gif"]:
                        potential_default_path = IMAGE_DIR / f"{short_name}{ext_check}" # Use Path object concatenation
                        if potential_default_path.exists():
                            new_image_filepath_for_json = str(potential_default_path)
                            break

                print(f"Debug - Final image path for JSON: {new_image_filepath_for_json}")

                emulator_folder_name = short_name
                # MODIFIED: Use path_manager for EMULATOR_RUN_SCRIPT_DIR
                EMULATOR_RUN_SCRIPT_DIR = self.path_manager.get_path("data") / "emulators" / "run"
                emulator_scripts_sub_dir = EMULATOR_RUN_SCRIPT_DIR / emulator_folder_name # Use Path object concatenation
                os.makedirs(emulator_scripts_sub_dir, exist_ok=True)
                print(f"Debug - Emulator scripts directory created: {emulator_scripts_sub_dir}")

                run_script_filename = f"{short_name}.sh"
                run_script_path = emulator_scripts_sub_dir / run_script_filename # Use Path object concatenation

                config_script_filename = f"{short_name}_config.sh"
                config_script_path = emulator_scripts_sub_dir / config_script_filename # Use Path object concatenation

                emulator_py_filename = f"{short_name}_emulator.py"
                emulator_py_path = EMULATOR_LIBRARIES_DIR / emulator_py_filename # Use Path object concatenation

                class_name_parts = [part.capitalize() for part in short_name.split('_')]
                dynamic_frame_class_name = "".join(class_name_parts) + "EmulatorFrame"

                self._write_sh_script_file(str(run_script_path), run_command, add_rom_arg=True) # Pass as string
                print(f"Debug - Run script created: {run_script_path}")
                self._write_sh_script_file(str(config_script_path), config_command, add_rom_arg=False) # Pass as string
                print(f"Debug - Config script created: {config_script_path}")

                # Call the external generator function
                generate_emulator_frame_file(
                    str(emulator_py_path), # Pass as string
                    full_name,
                    short_name,
                    str(run_script_path), # Pass as string
                    str(rom_directory), # Pass as string
                    str(bios_directory) # Pass as string
                )
                print(f"Debug - Python file created: {emulator_py_path}")

                new_entry = {
                    "full_name": full_name,
                    "short_name": short_name,
                    "image": new_image_filepath_for_json,
                    "rom_directory": str(rom_directory), # Store as string
                    "bios_directory": str(bios_directory), # Store as string
                    "emulator_py_path": str(emulator_py_path), # Store as string
                    "run_script_path": str(run_script_path), # Store as string
                    "config_script_path": str(config_script_path) # Store as string
                }

                self.emulators_data.append(new_entry)
                # MODIFIED: Use path_manager for DATA_FILE
                DATA_FILE = self.path_manager.get_path("data") / "emulators" / "emulators.json"
                with open(DATA_FILE, "w") as f:
                    json.dump(self.emulators_data, f, indent=4)
                print("Debug - Data saved to emulators.json")

                if self.controller.register_dynamic_frame(str(emulator_py_path), dynamic_frame_class_name): # Pass as string
                    print(f"Debug - Successfully registered new frame: {dynamic_frame_class_name}.")
                else:
                    print(f"Debug - Warning: Could not register new frame: {dynamic_frame_class_name}.")

                # Invalidate ROM cache for this emulator (will need rescan)
                if self.rom_cache_manager:
                    self.rom_cache_manager.invalidate_emulator_cache(short_name)

                dialog.destroy()
                self.after(50, self.sort_emulators)
                
                # Return to EmulatorsFrame after creation
                self.controller.show_frame("EmulatorsFrame")
            except Exception as e:
                print(f"Debug - Full error traceback:")
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Error creating emulator: {str(e)}")

        ttk.Button(dialog, text="Save", style="Emulator.TButton", command=save).grid(
            row=3, column=0, columnspan=3, pady=10
        )

    def load_emulators(self):
        """
        Load emulators from JSON file and apply initial sorting.
        Handles cases where the JSON file is missing or malformed.
        """
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "emulators" / "emulators.json"
        if not DATA_FILE.exists(): # Use .exists() for Path objects
            print(f"Info: {DATA_FILE} not found. Initializing with empty emulator data.")
            self.emulators_data = []
            return

        try:
            with open(DATA_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    print(f"Info: {DATA_FILE} is empty. Initializing with empty emulator data.")
                    self.emulators_data = []
                else:
                    self.emulators_data = json.loads(content)
            self.sort_emulators()
        except json.JSONDecodeError as e:
            print(f"Error: Malformed JSON in {DATA_FILE}: {e}. Initializing with empty emulator data.")
            print("Please check or delete the 'emulators.json' file if this error persists.")
            self.emulators_data = []
        except Exception as e:
            print(f"An unexpected error occurred while loading {DATA_FILE}: {e}. Initializing with empty emulator data.")
            self.emulators_data = []

    def load_all_dynamic_emulator_frames_at_startup(self):
        """
        Loads and registers all dynamic emulator frames found in emulators.json
        with the main controller at application startup.
        This method should be called once by the main Controller.
        """
        print("INFO: Attempting to load all dynamic emulator frames at startup.")
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "emulators" / "emulators.json"
        if not DATA_FILE.exists(): # Use .exists() for Path objects
            print(f"INFO: No {DATA_FILE} found at startup. No dynamic emulators to load.")
            return

        try:
            with open(DATA_FILE, "r") as f:
                emulators_config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"ERROR: Could not load emulators.json at startup ({e}). Skipping dynamic frame loading.")
            return

        for emulator_entry in emulators_config:
            emulator_py_path = emulator_entry.get("emulator_py_path")
            short_name = emulator_entry.get("short_name")

            if not emulator_py_path or not short_name:
                print(f"WARNING: Skipping malformed emulator entry (missing path or short_name): {emulator_entry}")
                continue

            class_name_parts = [part.capitalize() for part in short_name.split('_')]
            dynamic_frame_class_name = "".join(class_name_parts) + "EmulatorFrame"

            # MODIFIED: Check for existence using Path object
            if Path(emulator_py_path).exists():
                print(f"INFO: Registering dynamic frame: {dynamic_frame_class_name} from {emulator_py_path}")
                if self.controller.register_dynamic_frame(emulator_py_path, dynamic_frame_class_name):
                    print(f"INFO: Successfully re-registered {dynamic_frame_class_name}.")
                else:
                    print(f"WARNING: Failed to re-register {dynamic_frame_class_name}.")
            else:
                print(f"WARNING: Emulator Python file not found at {emulator_py_path} for {dynamic_frame_class_name}. Skipping registration.")


    def get_all_roms_with_emulator_info(self):
        """
        Gets all ROMs from the cache manager instead of scanning directories.
        Falls back to scanning if cache is not available.
        """
        if self.rom_cache_manager and not self.rom_cache_manager.is_scanning():
            # Use cached data
            all_roms = self.rom_cache_manager.get_all_roms()
            print(f"Retrieved {len(all_roms)} ROMs from cache")
            return all_roms
        else:
            # Fallback to scanning if cache is not available or still scanning
            print("ROM cache not available, falling back to directory scanning")
            return self._scan_all_roms_with_emulator_info()

    def _scan_all_roms_with_emulator_info(self):
        """
        Legacy method that scans all configured emulator ROM directories.
        This is now only used as a fallback when cache is not available.
        """
        all_roms_info = []
        for emulator_data in self.emulators_data:
            full_emulator_name = emulator_data.get("full_name", "Unknown Emulator")
            short_emulator_name = emulator_data.get("short_name", "")
            run_script_path = Path(emulator_data.get("run_script_path")) # Convert to Path object

            if not run_script_path or not run_script_path.exists(): # Use .exists() for Path objects
                print(f"WARNING: Run script not found for {full_emulator_name}: {run_script_path}")
                continue

            # Get all possible ROM directories for this emulator
            rom_directories = self._get_all_rom_directories(short_emulator_name)
            
            for rom_directory in rom_directories:
                if not rom_directory.exists() or not rom_directory.is_dir():
                    continue

                try:
                    for root, _, files in os.walk(rom_directory):
                        for filename in files:
                            if any(filename.lower().endswith(ext) for ext in COMMON_ROM_EXTENSIONS):
                                full_rom_path = Path(root) / filename # Use Path object concatenation
                                all_roms_info.append({
                                    "rom_path": str(full_rom_path), # Store as string in dict
                                    "display_name": filename,
                                    "emulator_name": full_emulator_name,
                                    "run_script_path": str(run_script_path) # Store as string in dict
                                })
                except Exception as e:
                    print(f"ERROR: Failed to scan ROMs in {rom_directory} for {full_emulator_name}: {e}")
        return all_roms_info
    
    def _get_all_rom_directories(self, emulator_short_name: str) -> List[Path]:
        """Get all possible ROM directories for an emulator (default + custom locations)"""
        from pathlib import Path
        directories = []
        
        # 1. Default ROM directory
        default_rom_dir = self.path_manager.get_path("roms") / emulator_short_name
        directories.append(default_rom_dir)
        
        # 2. Check if there's a global custom root with ROMs
        if self.path_manager.is_global_custom_path_active():
            global_root = self.path_manager.get_active_root_path()
            custom_rom_dir = global_root / "linux-gaming-center" / "roms" / emulator_short_name
            if custom_rom_dir != default_rom_dir:  # Avoid duplicates
                directories.append(custom_rom_dir)
        
        # 3. Check for individual custom ROM path
        individual_rom_path = self.path_manager.get_individual_custom_path("roms")
        if individual_rom_path:
            individual_rom_dir = individual_rom_path / emulator_short_name
            if individual_rom_dir not in directories:  # Avoid duplicates
                directories.append(individual_rom_dir)
        
        return directories

    def launch_random_rom(self):
        """
        Picks a random ROM from all configured emulator directories and launches it.
        """
        all_roms = self.get_all_roms_with_emulator_info()
        if not all_roms:
            messagebox.showinfo("No ROMs Found", "No ROMs were found across all configured emulator directories.")
            return

        random_rom_info = random.choice(all_roms)

        rom_path = random_rom_info["rom_path"]
        run_script_path = random_rom_info["run_script_path"]
        emulator_name = random_rom_info["emulator_name"]
        display_name = random_rom_info["display_name"]

        print(f"Attempting to launch random ROM: {display_name} via {emulator_name} using script: {run_script_path}")

        try:
            subprocess.Popen([run_script_path, rom_path])

            # Update last_played for this specific ROM in its emulator's history file
            # This requires access to the _update_rom_last_played_history method,
            # which is currently in AllRomsFrame. We need to make it accessible.
            # For now, we'll call it directly if AllRomsFrame exists and has the method.
            if "AllRomsFrame" in self.controller.frames and \
               hasattr(self.controller.frames["AllRomsFrame"], "_update_rom_last_played_history"):
                self.controller.frames["AllRomsFrame"]._update_rom_last_played_history(rom_path, emulator_name)
            else:
                print("WARNING: AllRomsFrame not available or missing _update_rom_last_played_history. ROM history not updated.")

            # Notify dashboard to update recently played ROMs
            if "DashboardFrame" in self.controller.frames and self.controller.frames["DashboardFrame"]:
                self.controller.frames["DashboardFrame"].update_dashboard()

        except FileNotFoundError:
            print(f"Could not find the script executable at: {run_script_path}")
            messagebox.showerror("Error", f"Could not find the script executable at: {run_script_path}")
        except PermissionError:
            print(f"Permission denied to execute script: {run_script_path}")
            messagebox.showerror("Permission Denied", f"Permission denied to execute script: {run_script_path}.\\nMake sure it's executable (chmod +x).")
        except Exception as e:
            print(f"An error occurred while launching '{display_name}' via {emulator_name} script:\\n{e}")
            messagebox.showerror("Launch Error", f"An error occurred while launching '{display_name}' via {emulator_name} script:\\n{e}")


    def sort_emulators(self, event=None):
        """Sort the emulators data and redraw the grid based on the selected option."""
        selected_sort = self.sort_var.get()

        if selected_sort == "A to Z":
            self.emulators_data.sort(key=lambda item: item["full_name"].lower())
        elif selected_sort == "Z to A":
            self.emulators_data.sort(key=lambda item: item["full_name"].lower(), reverse=True)
        elif selected_sort == "Date Added":
            pass

        for widget in self.emulator_widgets:
            widget.destroy()
        self.emulator_widgets = []
        self.icons = []
        for entry in self.emulators_data:
            self.add_emulator_icon(entry)
        self.force_redraw()

    def show_context_menu(self, event, index):
        if self.current_menu:
            self.current_menu.unpost()

        menu = tk.Menu(self, tearoff=0, bg=self.theme.get("background", "#1e1e1e"), fg=self.theme.get("text_color", "#ffffff"))
        menu.add_command(label="Edit Emulator", command=lambda: self.open_edit_emulator_dialog(index))
        menu.add_command(label="Configure Emulator", command=lambda: self.configure_emulator(self.emulators_data[index]))
        menu.add_separator()
        menu.add_command(label="Delete Emulator", command=lambda: self.delete_emulator(index))

        self.current_menu = menu
        menu.tk_popup(event.x_root, event.y_root)

        self.controller.bind("<Button-1>", self.close_context_menu, add="+")

    def on_menu_dismiss(self):
        """Handle menu being dismissed"""
        if hasattr(self, "current_menu") and self.current_menu:
            self.current_menu.destroy()
            self.current_menu = None
        self.controller.unbind("<Button-1>")

    def close_context_menu(self, event=None):
        """Close the context menu if it's open"""
        if hasattr(self, "current_menu") and self.current_menu:
            self.current_menu.destroy()
            self.current_menu = None
        self.controller.unbind("<Button-1>")

    def configure_emulator(self, emulator_info):
        """
        Launches the emulator for configuration using its dedicated configuration command.
        """
        config_script_path = emulator_info.get("config_script_path")

        if not config_script_path or not os.path.exists(config_script_path):
            messagebox.showwarning("Missing Configuration Script",
                                   f"The configuration script for '{emulator_info['full_name']}' is not found. "
                                   "Please edit the emulator and ensure the Config Command is set correctly.")
            return

        print(f"Attempting to configure emulator: {emulator_info['full_name']} using script: '{config_script_path}'")

        try:
            subprocess.Popen([config_script_path])
        except FileNotFoundError:
            print(f"Could not find the script executable at: '{config_script_path}'")
            messagebox.showerror("Error", f"Could not find the script executable at: '{config_script_path}'. "
                                 "Please ensure the script exists and has execute permissions.")
        except PermissionError:
            print(f"Permission denied to execute script: '{config_script_path}'")
            messagebox.showerror("Permission Denied", f"Permission denied to execute script: '{config_script_path}'. "
                                 "Make sure the script has appropriate permissions (e.g., chmod +x).")
        except Exception as e:
            print(f"An error occurred while launching {emulator_info['full_name']} for configuration:\n{e}")
            messagebox.showerror("Launch Error", f"An error occurred while launching {emulator_info['full_name']} for configuration:\n{e}")

    def open_script_for_editing(self, script_path):
        """
        Opens the specified shell script file in a graphical text editor.
        Tries gedit first, then falls back to xdg-open.
        """
        if not script_path or not os.path.exists(script_path):
            messagebox.showwarning("File Not Found", f"Script file not found: {script_path}")
            return

        try:
            subprocess.Popen(['gedit', script_path])
            print(f"Opened {script_path} with gedit.")
        except FileNotFoundError:
            try:
                subprocess.Popen(['xdg-open', script_path])
                print(f"Opened {script_path} with xdg-open (gedit not found).")
            except FileNotFoundError:
                messagebox.showerror("Error", "Could not find 'gedit' or 'xdg-open'. Please ensure one is installed and in your PATH, or configure a default editor.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open script '{os.path.basename(script_path)}' with xdg-open: {e}")
                print(f"Error opening script {script_path} with xdg-open: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open script '{os.path.basename(script_path)}' with gedit: {e}")
            print(f"Error opening script {script_path} with gedit: {e}")


    def delete_emulator(self, index):
        emulator = self.emulators_data[index]
        confirm = messagebox.askyesno("Delete Emulator", f"Are you sure you want to delete '{emulator['full_name']}'?")
        if not confirm:
            return

        # MODIFIED: Use path_manager for IMAGE_DIR
        IMAGE_DIR = self.path_manager.get_path("data") / "emulators" / "assets"
        if "image" in emulator and Path(emulator["image"]).exists(): # Use Path for exists check
            is_derived_image = False
            short_name = emulator.get('short_name')
            if short_name:
                for ext in [".png", ".jpg", ".jpeg", ".gif"]:
                    if Path(emulator["image"]) == IMAGE_DIR / f"{short_name}{ext}": # Compare Path objects
                        is_derived_image = True
                        break

            if not is_derived_image:
                try:
                    os.remove(emulator["image"])
                    print(f"Removed custom image: {emulator['image']}")
                except Exception as e:
                    print(f"Failed to remove custom image: {e}")


        if "emulator_py_path" in emulator and Path(emulator["emulator_py_path"]).exists(): # Use Path for exists check
            try:
                os.remove(emulator["emulator_py_path"])
                print(f"Removed emulator Python file: {emulator['emulator_py_path']}")
            except Exception as e:
                print(f"Failed to remove emulator Python file: {e}")

        emulator_folder_name = emulator['short_name']
        # MODIFIED: Use path_manager for EMULATOR_RUN_SCRIPT_DIR
        EMULATOR_RUN_SCRIPT_DIR = self.path_manager.get_path("data") / "emulators" / "run"
        emulator_scripts_sub_dir = EMULATOR_RUN_SCRIPT_DIR / emulator_folder_name # Use Path object concatenation

        run_sh_path = emulator_scripts_sub_dir / f"{emulator_folder_name}.sh" # Use Path object concatenation
        config_sh_path = emulator_scripts_sub_dir / f"{emulator_folder_name}_config.sh" # Use Path object concatenation

        if run_sh_path.exists(): # Use .exists() for Path objects
            try:
                os.remove(run_sh_path)
                print(f"Removed emulator run shell script: {run_sh_path}")
            except Exception as e:
                print(f"Failed to remove emulator run shell script: {e}")

        if config_sh_path.exists(): # Use .exists() for Path objects
            try:
                os.remove(config_sh_path)
                print(f"Removed emulator config shell script: {config_sh_path}")
            except Exception as e:
                print(f"Failed to remove emulator config shell script: {e}")

        if emulator_scripts_sub_dir.exists() and not os.listdir(emulator_scripts_sub_dir): # Use .exists() for Path objects
            try:
                os.rmdir(emulator_scripts_sub_dir)
                print(f"Removed empty emulator script directory: {emulator_scripts_sub_dir}")
            except OSError as e:
                print(f"Could not remove directory {emulator_scripts_sub_dir}: {e}")

        # MODIFIED: Use path_manager for ROMS_DATA_DIR
        ROMS_DATA_DIR = self.path_manager.get_path("data") / "emulators" / "rom_data"
        rom_data_file = ROMS_DATA_DIR / f"{emulator_folder_name}_roms.json" # Use Path object concatenation
        if rom_data_file.exists(): # Use .exists() for Path objects
            try:
                os.remove(rom_data_file)
                print(f"Removed ROM play history file: {rom_data_file}")
            except Exception as e:
                print(f"Failed to remove ROM play history file: {e}")

        # MODIFIED: Use path_manager for USER_BIOS_BASE_DIR
        USER_BIOS_BASE_DIR = self.path_manager.get_path("bios")
        bios_directory = USER_BIOS_BASE_DIR / emulator_folder_name # Use Path object concatenation
        if bios_directory.exists() and bios_directory.is_dir() and not os.listdir(bios_directory): # Use .exists() and .is_dir() for Path objects
            try:
                os.rmdir(bios_directory)
                print(f"Removed empty BIOS directory: {bios_directory}")
            except OSError as e:
                print(f"Could not remove BIOS directory {bios_directory}: {e}")

        # Invalidate ROM cache for this emulator before deleting
        if self.rom_cache_manager:
            self.rom_cache_manager.invalidate_emulator_cache(emulator['short_name'])

        del self.emulators_data[index]
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "emulators" / "emulators.json"
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.emulators_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save updated data: {e}")
            return

        self.force_redraw()

    def add_emulator_icon(self, entry):
        """Add emulator button to the grid"""
        emulator_display_name = entry.get("full_name", entry.get("name", "Unknown Emulator"))

        try:
            image_path = entry.get("image")
            photo = None

            if image_path and Path(image_path).exists(): # Use Path for exists check
                img = Image.open(image_path)
                img = self.resize_image_to_fit(
                    img,
                    self.BUTTON_WIDTH - self.IMAGE_PADDING * 2,
                    self.BUTTON_HEIGHT - self.IMAGE_PADDING * 2,
                )
                photo = ImageTk.PhotoImage(img)
                self.icons.append(photo)
            else:
                print(f"No image found for '{emulator_display_name}' at '{image_path if image_path else 'N/A'}'. Displaying text.")

            button_frame = ttk.Frame(self.grid_frame, style="Emulator.TFrame")

            if photo:
                img_label = ttk.Label(button_frame, image=photo, style="Emulator.TLabel")
                img_label.image = photo
            else:
                img_label = ttk.Label(
                    button_frame,
                    text=emulator_display_name,
                    style="Emulator.TLabel",
                    wraplength=self.BUTTON_WIDTH - self.IMAGE_PADDING * 2,
                    justify="center"
                )

            img_label.pack(pady=(0, 0), fill="both", expand=True)

            short_name = entry.get('short_name')
            if not short_name:
                print(f"Error: Missing short_name for emulator entry: {entry}. Cannot create dynamic frame class name.")
                return

            class_name_parts = [part.capitalize() for part in short_name.split('_')]
            emulator_frame_class_name = "".join(class_name_parts) + "EmulatorFrame"

            button_frame.bind(
                "<Button-1>", lambda e, frame_name=emulator_frame_class_name: self.controller.show_frame(frame_name)
            )
            img_label.bind(
                "<Button-1>", lambda e, frame_name=emulator_frame_class_name: self.controller.show_frame(frame_name)
            )

            index = len(self.emulator_widgets)
            img_label.bind(
                "<Button-3>",
                lambda event, idx=index: self.show_context_menu(event, idx),
            )

            self.emulator_widgets.append(button_frame)
        except Exception as e:
            print(f"Error loading emulator icon for entry {emulator_display_name}: {e}")
            import traceback
            traceback.print_exc()

    def resize_image_to_fit(self, img, target_width, target_height):
        """Resize image maintaining aspect ratio to fit within target dimensions"""
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height

        if target_ratio > img_ratio:
            new_height = target_height
            new_width = int(img_ratio * new_height)
        else:
            new_width = target_width
            new_height = int(new_width / img_ratio)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def run_emulator(self, emulator_py_path):
        """Show the emulator's dedicated Python file frame and update last_played."""
        pass

    def save_emulators(self):
        """Save the emulators data to the JSON file."""
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "emulators" / "emulators.json"
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.emulators_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save emulator data: {e}")

    def get_recently_played_emulators(self, num_items=15):
        """
        Retrieves recently played ROMs by querying each registered emulator frame.
        Combines and sorts them by last_played timestamp.
        """
        all_recent_roms = []
        for frame_name, frame_instance in self.controller.frames.items():
            if frame_name.endswith("EmulatorFrame") and hasattr(frame_instance, 'get_recently_played_roms'):
                roms_from_emulator = frame_instance.get_recently_played_roms(num_items=num_items)
                all_recent_roms.extend(roms_from_emulator)

        all_recent_roms.sort(key=lambda x: x["last_played"], reverse=True)

        return all_recent_roms[:num_items]

