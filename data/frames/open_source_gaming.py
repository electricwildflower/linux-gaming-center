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
from pathlib import Path # NEW: Import Path for consistency

# NEW: Import the PathManager
from paths import PathManager

# REMOVED: Old hardcoded BASE_DATA_DIR, DATA_FILE, IMAGE_DIR, SCRIPT_DIR, THEME_FILE
# These will now be obtained dynamically from PathManager.

BUTTON_WIDTH = 200
BUTTON_HEIGHT = 150
BUTTON_PADDING = 20
FRAME_PADDING = 20
IMAGE_PADDING = 10


class OpenSourceGamingFrame(ttk.Frame):
    def __init__(self, parent, controller, path_manager):
        super().__init__(parent)

        self.controller = controller
        # NEW: Get the path_manager instance from the controller
        self.path_manager = path_manager

        self.icons = []
        self.games_data = []
        self.game_widgets = []
        self.theme = self.load_theme() # load_theme will now use path_manager
        self.configure_style()

        self.last_width = 0
        self.initial_load_complete = False
        self.current_menu = None

        self["style"] = "Game.TFrame"
        self.bind("<Visibility>", self.on_visibility_change)

        self.controller.bind("<Configure>", self.on_main_window_configure)

        self.setup_ui()
        self.load_games() # load_games will now use path_manager
        self.after(200, self.perform_initial_redraw)

    def setup_ui(self):
        controls_frame = ttk.Frame(self, style="Game.TFrame")
        controls_frame.pack(fill="x", padx=10, pady=10)

        add_button = ttk.Button(
            controls_frame,
            text="Add Game",
            style="Game.TButton",
            command=self.open_add_game_dialog,
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
        sort_dropdown.bind("<<ComboboxSelected>>", self.sort_games)

        self.canvas = tk.Canvas(
            self,
            bg=self.theme.get("background", "#1e1e1e"),
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.grid_frame = ttk.Frame(self.canvas, style="Game.TFrame")
        self.grid_frame_id = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.bind_mousewheel_events()

    def on_canvas_resize(self, event):
        """Update canvas and grid width on resize."""
        self.last_width = event.width
        self.canvas.itemconfig(self.grid_frame_id, width=event.width)
        self.after(100, self.redraw_grid)

    def open_edit_game_dialog(self, index):
        """Open dialog to edit the selected game."""
        game_info = self.games_data[index]
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Game: {game_info['name']}")
        dialog.configure(bg=self.theme.get("background", "#1e1e1e"))

        def themed_label(master, text, row, col=0, sticky="w", padx=5, pady=5):
            label = ttk.Label(master, text=text, style="Game.TLabel")
            label.grid(row=row, column=col, sticky=sticky, padx=padx, pady=pady)
            return label

        def themed_entry(master, var=None, row=0, col=1, columnspan=1, sticky="ew", padx=5, pady=5):
            entry = ttk.Entry(master, textvariable=var) if var else ttk.Entry(master)
            entry.grid(row=row, column=col, columnspan=columnspan, sticky="ew", padx=5, pady=5)
            return entry

        dialog.columnconfigure(1, weight=1)

        # --- Name ---
        themed_label(dialog, "Game Name:", 0)
        name_var = tk.StringVar(value=game_info["name"])
        name_entry = themed_entry(dialog, name_var, row=0)

        # --- Image ---
        themed_label(dialog, "Current Image:", 1)
        current_image_label = ttk.Label(
            dialog,
            text=os.path.basename(game_info["image"]),
            style="Game.TLabel",
        )
        current_image_label.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        themed_label(dialog, "Select New Image:", 2)
        new_image_path_var = tk.StringVar()
        new_image_entry = themed_entry(dialog, new_image_path_var, row=2)
        ttk.Button(
            dialog,
            text="Browse",
            style="Game.TButton",
            command=lambda: self.browse_image(new_image_path_var),
        ).grid(row=2, column=2, padx=5)

        # --- Run Command Edit Button ---
        themed_label(dialog, "Run Command:", 3)
        ttk.Button(
            dialog,
            text="Edit",
            style="Game.TButton",
            command=lambda: self.open_script_for_editing(game_info.get("exec")),
        ).grid(row=3, column=1, sticky="ew", padx=5, pady=5)


        # --- Save Changes Button ---
        def save_changes():
            new_name = name_var.get().strip()
            new_image_path = new_image_path_var.get()

            if not new_name:
                messagebox.showerror("Error", "Game Name is required.")
                return

            old_name = game_info["name"]
            old_image_path = game_info["image"]
            old_exec_path = game_info["exec"]

            game_info["name"] = new_name

            # Handle new image upload
            if new_image_path:
                # MODIFIED: Use path_manager for IMAGE_DIR
                IMAGE_DIR = self.path_manager.get_path("data") / "games" / "opensourcegames" / "assets"
                os.makedirs(IMAGE_DIR, exist_ok=True)
                new_image_filename = os.path.basename(new_image_path)
                new_image_filepath = IMAGE_DIR / new_image_filename # Use Path object concatenation
                try:
                    shutil.copy(new_image_path, new_image_filepath)
                    game_info["image"] = str(new_image_filepath) # Store as string
                    if Path(old_image_path).exists() and Path(old_image_path) != new_image_filepath: # Use Path for comparison
                        os.remove(old_image_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Error updating image: {e}")
                    return

            # Rename script file if name changed
            # MODIFIED: Use path_manager for SCRIPT_DIR
            SCRIPT_DIR = self.path_manager.get_path("data") / "games" / "opensourcegames" / "run"
            new_exec_filename = f"{new_name.lower().replace(' ', '_')}.sh"
            new_exec_path = SCRIPT_DIR / new_exec_filename # Use Path object concatenation

            if Path(old_exec_path) != new_exec_path: # Use Path for comparison
                try:
                    if Path(old_exec_path).exists(): # Use Path for exists check
                        shutil.move(old_exec_path, new_exec_path)
                    game_info["exec"] = str(new_exec_path) # Store as string
                except Exception as e:
                    messagebox.showerror("Error", f"Error renaming run script: {e}")
                    return

            # Save updated data to JSON
            # MODIFIED: Use path_manager for DATA_FILE
            DATA_FILE = self.path_manager.get_path("data") / "games" / "opensourcegames" / "opensourcegames.json"
            try:
                with open(DATA_FILE, "w") as f:
                    json.dump(self.games_data, f, indent=4)
                self.force_redraw()  # Redraw to update the UI
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Error saving game data: {e}")

        ttk.Button(
            dialog, text="Save Changes", style="Game.TButton", command=save_changes
        ).grid(row=4, column=0, columnspan=3, pady=10) # Adjusted row for new button

        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.wait_window()

    def browse_image(self, path_var):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")]
        )
        if file_path:
            path_var.set(file_path)

    def load_run_command(self, script_path):
        """Load the run command from the game's .sh script."""
        # This method is no longer directly used for displaying in GUI,
        # but might be useful for internal logic if needed.
        # MODIFIED: Use Path object for exists check
        if not Path(script_path).exists():
            print(f"Warning: Script not found at {script_path}")
            return ""
        try:
            with open(script_path, "r") as f:
                lines = f.readlines()
                # Assuming the run command is on the second line (after #!/bin/bash)
                if len(lines) > 1:
                    return lines[1].strip()
        except FileNotFoundError:
            print(f"Warning: Script not found at {script_path}")
        except Exception as e:
            print(f"Error reading script {script_path}: {e}")
        return ""

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
            self.after(100, self.delayed_redraw)  # Small delay to ensure proper sizing

    def delayed_redraw(self):
        """Delayed call to force redraw."""
        self.force_redraw()

    def force_redraw(self):
        """Force a complete redraw of the grid"""
        canvas_width = self.canvas.winfo_width()  # Get the current width of the frame
        self.canvas.config(width=canvas_width)  # Update canvas width

        # Clear the game widgets list and destroy them
        for button_frame in self.game_widgets:
            button_frame.destroy()
        self.game_widgets = []
        self.icons = []  # Also clear icons

        # Destroy the old grid frame if it exists
        if hasattr(self, "grid_frame"):
            self.grid_frame.destroy()

        # Create a new grid frame
        self.grid_frame = ttk.Frame(self.canvas, style="Game.TFrame")
        self.grid_frame_id = self.canvas.create_window(
            (0, 0), window=self.grid_frame, anchor="nw"
        )

        # Re-add the game icons to populate the new grid frame
        for entry in self.games_data:  # Use the already loaded data
            self.add_game_icon(entry)

        self.redraw_grid()

        # Reset the scrollregion after redrawing
        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        self.update()
        self.update_idletasks()

    def load_theme(self):
        """Load theme settings from JSON file"""
        # MODIFIED: Use path_manager to get the themes directory
        theme_file_path = self.path_manager.get_path("themes") / "cosmictwilight" / "styles" / "opensourcegames.json"
        if theme_file_path.exists(): # Use Path object's exists()
            with open(theme_file_path, "r") as f:
                return json.load(f)
        return {
            "background": "#1e1e1e",
            "text_color": "#ffffff",
            "font_family": "Segoe UI",
            "font_size": 11,
        }

    def configure_style(self):
        """Configure ttk styles based on theme"""
        style = ttk.Style()
        bg = self.theme.get("background", "#1e1e1e")
        fg = self.theme.get("text_color", "#ffffff")
        font_family = self.theme.get("font_family", "Segoe UI")
        font_size = self.theme.get("font_size", 11)

        style.configure("Game.TFrame", background=bg)
        style.configure(
            "Game.TLabel",
            background=bg,
            foreground=fg,
            font=(font_family, font_size),
            anchor="center",
        )
        style.configure(
            "Game.TButton",
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

    # setup_ui method is duplicated, keeping the one above as it's more complete.
    # The one below will be removed.

    # def setup_ui(self):
    #     """Set up the user interface"""
    #     # Create a frame for the controls (add button and sort dropdown)
    #     controls_frame = ttk.Frame(self, style="Game.TFrame")
    #     controls_frame.pack(fill="x", padx=10, pady=10)

    #     # Add game button in controls frame
    #     add_button = ttk.Button(
    #         controls_frame,
    #         text="Add Game",
    #         style="Game.TButton",
    #         command=self.open_add_game_dialog,
    #     )
    #     add_button.pack(side="left", padx=(0, 5))

    #     # Label for the sort dropdown
    #     sort_label = ttk.Label(controls_frame, text="Sort by:", style="SortLabel.TLabel")
    #     sort_label.pack(side="left", padx=(5, 5))

    #     # Sort options
    #     sort_options = ["A to Z", "Z to A", "Date Added"]
    #     self.sort_var = tk.StringVar(self)
    #     self.sort_var.set(sort_options[2])  # Default to "Date Added"

    #     # Dropdown for sorting
    #     sort_dropdown = ttk.Combobox(
    #         controls_frame,
    #         textvariable=self.sort_var,
    #         values=sort_options,
    #         state="readonly",
    #         style="Sort.TCombobox",
    #     )
    #     sort_dropdown.pack(side="left", padx=(5, 0))
    #     sort_dropdown.bind("<<ComboboxSelected>>", self.sort_games)

    #     self.canvas = tk.Canvas(
    #         self,
    #         bg=self.theme.get("background", "#1e1e1e"),
    #         highlightthickness=0
    #     )
    #     self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    #     self.grid_frame = ttk.Frame(self.canvas, style="Game.TFrame")
    #     self.grid_frame_id = self.canvas.create_window(
    #         (0, 0), window=self.grid_frame, anchor="nw"
    #     )

    #     # Configure mouse wheel scrolling
    #     self.canvas.bind("<Configure>", self.on_canvas_resize)
    #     self.bind_mousewheel_events()


    def bind_mousewheel_events(self):
        """Bind mouse wheel events for cross-platform compatibility"""
        # Windows and MacOS
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        # Linux
        self.canvas.bind_all("<Button-4>", lambda e: self.on_mousewheel_scroll(-1))
        self.canvas.bind_all("<Button-5>", lambda e: self.on_mousewheel_scroll(1))

        # Set focus when mouse enters canvas
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling on Windows/Mac"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_scroll(self, direction):
        """Handle mouse wheel scrolling on Linux"""
        self.canvas.yview_scroll(direction, "units")

    def on_canvas_resize(self, event):
        """Handle canvas resize events"""
        self.last_width = event.width
        self.canvas.config(width=event.width)
        self.canvas.itemconfig(self.grid_frame_id, width=event.width)
        self.after(50, self.redraw_grid)  # Small delay to ensure proper sizing

    def calculate_grid_layout(self, available_width):
        """Calculate optimal grid layout based on available width"""
        if available_width <= 0:
            return 1, 0

        min_item_width = BUTTON_WIDTH + BUTTON_PADDING
        max_columns = max(1, (available_width - 2 * FRAME_PADDING) // min_item_width)

        total_content_width = max_columns * min_item_width - BUTTON_PADDING
        remaining_space = max(
            0, available_width - total_content_width - 2 * FRAME_PADDING
        )
        extra_padding = remaining_space // (max_columns + 1)

        return max_columns, extra_padding

    def redraw_grid(self):
        """Reorganize buttons in a grid based on current width"""
        if not self.game_widgets:
            return

        canvas_width = self.canvas.winfo_width()  # Use the canvas's width
        if canvas_width <= 0:
            return

        # Clear current grid
        for widget in self.grid_frame.winfo_children():
            widget.grid_forget()

        # Calculate optimal layout
        columns, extra_padding = self.calculate_grid_layout(canvas_width)

        # Place buttons in grid
        for idx, button_frame in enumerate(self.game_widgets):
            row = idx // columns
            col = idx % columns

            left_pad = (
                FRAME_PADDING + extra_padding
                if col == 0
                else BUTTON_PADDING // 2 + extra_padding
            )
            right_pad = (
                FRAME_PADDING + extra_padding
                if col == columns - 1
                else BUTTON_PADDING // 2 + extra_padding
            )

            button_frame.grid(
                row=row, column=col, padx=(left_pad, right_pad), pady=10, sticky="nsew"
            )

        # Configure grid weights
        for col in range(columns):
            self.grid_frame.columnconfigure(col, weight=1, uniform="game_cols")

        # Update the grid frame's size request
        rows = (len(self.game_widgets) + columns - 1) // columns
        total_height = rows * (BUTTON_HEIGHT + 20)  # 20 for padding
        self.grid_frame.config(height=total_height)

        # Update the scroll region
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

        # Force immediate update
        self.update_idletasks()

    def open_add_game_dialog(self):
        """Create dialog for adding new game"""
        dialog = tk.Toplevel(self)
        dialog.title("Add Game")
        dialog.configure(bg=self.theme.get("background", "#1e1e1e"))

        def themed_label(master, text, row):
            label = ttk.Label(master, text=text, style="Game.TLabel")
            label.grid(row=row, column=0, sticky="w", padx=5, pady=5)
            return label

        def themed_entry(master, var=None, row=0, col=1, colspan=1):
            entry = ttk.Entry(master, textvariable=var) if var else ttk.Entry(master)
            entry.grid(
                row=row, column=col, columnspan=colspan, sticky="ew", padx=5, pady=5
            )
            return entry

        dialog.columnconfigure(1, weight=1)

        themed_label(dialog, "Game Name:", 0)
        name_entry = themed_entry(dialog, row=0)

        themed_label(dialog, "Select Image:", 1)
        image_path_var = tk.StringVar()
        image_entry = themed_entry(dialog, image_path_var, row=1)
        ttk.Button(
            dialog,
            text="Browse",
            style="Game.TButton",
            command=lambda: self.browse_image(image_path_var),
        ).grid(row=1, column=2, padx=5)

        # --- Informative Text for .sh files ---
        # MODIFIED: Use path_manager for the example path
        SCRIPT_DIR_EXAMPLE = self.path_manager.get_path("data") / "games" / "opensourcegames" / "run"
        info_label = ttk.Label(
            dialog,
            text=f"Please add run commands for games under:\n{SCRIPT_DIR_EXAMPLE}",
            style="Game.TLabel",
            wraplength=300, # Adjust as needed
            justify="left"
        )
        info_label.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky="w")


        def save():
            name = name_entry.get().strip()
            image_path = image_path_var.get()

            # Default placeholder command for new games
            run_command = "#!/bin/bash\n# Add your game launch command here.\n# Example: /usr/bin/steam steam://rungameid/12345"

            if not name or not image_path:
                messagebox.showerror("Error", "Game Name and Image are required.")
                return

            # MODIFIED: Use path_manager for IMAGE_DIR and SCRIPT_DIR
            IMAGE_DIR = self.path_manager.get_path("data") / "games" / "opensourcegames" / "assets"
            SCRIPT_DIR = self.path_manager.get_path("data") / "games" / "opensourcegames" / "run"

            os.makedirs(IMAGE_DIR, exist_ok=True)
            os.makedirs(SCRIPT_DIR, exist_ok=True)

            new_image_path = IMAGE_DIR / os.path.basename(image_path) # Use Path object concatenation
            shutil.copy(image_path, new_image_path)

            script_filename = f"{name.lower().replace(' ', '_')}.sh"
            script_path = SCRIPT_DIR / script_filename # Use Path object concatenation
            with open(script_path, "w") as script_file:
                script_file.write(f"{run_command}\n") # Write the placeholder content
            os.chmod(script_path, 0o755)

            new_entry = {"name": name, "image": str(new_image_path), "exec": str(script_path)} # Store as strings

            # Load existing data
            # MODIFIED: Use path_manager for DATA_FILE
            DATA_FILE = self.path_manager.get_path("data") / "games" / "opensourcegames" / "opensourcegames.json"
            if DATA_FILE.exists(): # Use Path object's exists()
                with open(DATA_FILE, "r") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                    else:
                        data = []
            else:
                data = []

            # Add new entry
            data.append(new_entry)

            # Save the data
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

            # Update the internal data and UI
            self.games_data = data  # Update the local data
            self.sort_games()  # Apply the current sorting
            dialog.destroy()

        ttk.Button(dialog, text="Save", style="Game.TButton", command=save).grid(
            row=3, column=0, columnspan=3, pady=10 # Adjusted row for new info label
        )

        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.wait_window()

    def browse_image(self, var):
        """Open file dialog to select image"""
        path = filedialog.askopenfilename(
            title="Select Game Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")],
        )
        if path:
            var.set(path)

    def open_script_for_editing(self, script_path):
        """
        Opens the specified shell script file in the default text editor.
        Tries gedit first, then falls back to xdg-open.
        """
        # MODIFIED: Use Path object for exists check
        if not script_path or not Path(script_path).exists():
            messagebox.showwarning("File Not Found", f"Script file not found: {script_path}")
            return

        try:
            # Try to open with gedit, a common graphical text editor
            subprocess.Popen(['gedit', script_path])
            print(f"Opened {script_path} with gedit.")
        except FileNotFoundError:
            # If gedit is not found, fall back to xdg-open
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

    def load_games(self):
        """Load games from JSON file and apply initial sorting"""
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "games" / "opensourcegames" / "opensourcegames.json"
        if not DATA_FILE.exists(): # Use Path object's exists()
            print(f"Info: {DATA_FILE} not found. Initializing with empty game data.")
            self.games_data = []
            return
        try:
            with open(DATA_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    print(f"Info: {DATA_FILE} is empty. Initializing with empty game data.")
                    self.games_data = []
                else:
                    self.games_data = json.loads(content)
            self.sort_games()  # Apply initial sorting
        except json.JSONDecodeError as e:
            print(f"Error: Malformed JSON in {DATA_FILE}: {e}. Initializing with empty game data.")
            print("Please check or delete the 'opensourcegames.json' file if this error persists.")
            self.games_data = []
        except Exception as e:
            print(f"An unexpected error occurred while loading {DATA_FILE}: {e}. Initializing with empty game data.")
            self.games_data = []

    def sort_games(self, event=None):
        """Sort the games data and redraw the grid based on the selected option."""
        selected_sort = self.sort_var.get()

        if selected_sort == "A to Z":
            self.games_data.sort(key=lambda item: item["name"].lower())
        elif selected_sort == "Z to A":
            self.games_data.sort(key=lambda item: item["name"].lower(), reverse=True)
        elif selected_sort == "Date Added":
            # For "Date Added", we'll rely on the order in which they are loaded
            # from the JSON file, assuming that's the order they were added.
            # If you need a more precise "Date Added" feature, you'd need to
            # add a timestamp to your game data when a game is added.
            pass  # Keep the current order

        # After sorting, clear existing widgets and re-add them
        for widget in self.game_widgets:
            widget.destroy()
        self.game_widgets = []
        self.icons = []
        for entry in self.games_data:
            self.add_game_icon(entry)
        self.force_redraw()

    def show_context_menu(self, event, index):
        if self.current_menu:
            self.current_menu.unpost()

        menu = tk.Menu(self, tearoff=0, bg=self.theme.get("background", "#1e1e1e"), fg=self.theme.get("text_color", "#ffffff"))
        menu.add_command(label="Edit Game", command=lambda: self.open_edit_game_dialog(index))
        menu.add_separator()
        menu.add_command(label="Delete Game", command=lambda: self.delete_game(index))

        self.current_menu = menu
        menu.tk_popup(event.x_root, event.y_root)

        # Bind to root window click to close menu
        self.controller.bind("<Button-1>", self.close_context_menu, add="+")

    def on_menu_dismiss(self):
        """Handle menu being dismissed"""
        if hasattr(self, "current_menu") and self.current_menu:
            self.current_menu.destroy()
            self.current_menu = None
        # Unbind the root window click handler
        self.controller.unbind("<Button-1>")

    def close_context_menu(self, event=None):
        """Close the context menu if it's open"""
        if hasattr(self, "current_menu") and self.current_menu:
            self.current_menu.destroy()
            self.current_menu = None
        # Unbind the root window click handler
        self.controller.unbind("<Button-1>")

    def edit_game(self, index):
        """Open the edit game dialog for the selected game."""
        self.open_edit_game_dialog(index)

    def delete_game(self, index):
        game = self.games_data[index]
        confirm = messagebox.askyesno("Delete Game", f"Are you sure you want to delete '{game['name']}'?")
        if not confirm:
            return

        # Remove image file
        # MODIFIED: Use Path object for exists check
        if Path(game["image"]).exists():
            try:
                os.remove(game["image"])
            except Exception as e:
                print(f"Failed to remove image: {e}")

        # Remove .sh script
        # MODIFIED: Use Path object for exists check
        if Path(game["exec"]).exists():
            try:
                os.remove(game["exec"])
            except Exception as e:
                print(f"Failed to remove exec script: {e}")

        # Remove from data and save
        del self.games_data[index]
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "games" / "opensourcegames" / "opensourcegames.json"
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.games_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save updated data: {e}")
            return

        self.force_redraw()

    def add_game_icon(self, entry):
        """Add game button to the grid"""
        try:
            # Load and resize image to fit button (with padding)
            # MODIFIED: Use Path object for exists check
            if not Path(entry["image"]).exists():
                print(f"Warning: Image file not found for game '{entry['name']}' at '{entry['image']}'. Skipping image loading.")
                # Optionally, use a placeholder image or just display text
                img = Image.new('RGB', (BUTTON_WIDTH - IMAGE_PADDING * 2, BUTTON_HEIGHT - IMAGE_PADDING * 2 - 30), color = 'grey')
                photo = ImageTk.PhotoImage(img)
            else:
                img = Image.open(entry["image"])
                img = self.resize_image_to_fit(
                    img,
                    BUTTON_WIDTH - IMAGE_PADDING * 2,
                    BUTTON_HEIGHT - IMAGE_PADDING * 2 - 30,
                )
                photo = ImageTk.PhotoImage(img)

            self.icons.append(photo)

            # Create a frame to hold button image and label
            button_frame = ttk.Frame(self.grid_frame, style="Game.TFrame")

            # Create image label
            img_label = ttk.Label(button_frame, image=photo, style="Game.TLabel")
            img_label.pack(pady=(0, 5))

            # Create text label
            text_label = ttk.Label(
                button_frame,
                text=entry["name"],
                style="Game.TLabel",
                wraplength=BUTTON_WIDTH - 10,
                justify="center",
            )
            text_label.pack()

            # Make the whole frame clickable for running
            button_frame.bind(
                "<Button-1>", lambda e, path=entry["exec"]: self.run_game(path)
            )
            img_label.bind(
                "<Button-1>", lambda e, path=entry["exec"]: self.run_game(path)
            )
            text_label.bind(
                "<Button-1>", lambda e, path=entry["exec"]: self.run_game(path)
            )

            # Bind right-click to show context menu on image and text
            index = len(self.game_widgets)
            img_label.bind(
                "<Button-3>",
                lambda event, idx=index: self.show_context_menu(event, idx),
            )
            text_label.bind(
                "<Button-3>",
                lambda event, idx=index: self.show_context_menu(event, idx),
            )

            self.game_widgets.append(button_frame)
            # No immediate redraw here, will be done after loading
        except Exception as e:
            print(f"Error loading game icon: {e}")
            import traceback
            traceback.print_exc()


    def resize_image_to_fit(self, img, target_width, target_height):
        """Resize image maintaining aspect ratio to fit within target dimensions"""
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height

        if target_ratio > img_ratio:
            # Fit to height
            new_height = target_height
            new_width = int(img_ratio * new_height)
        else:
            # Fit to width
            new_width = target_width
            new_height = int(new_width / img_ratio)

        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def save_games(self):
        """Save the current games data to the JSON file."""
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "games" / "opensourcegames" / "opensourcegames.json"
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.games_data, f, indent=4)
        except Exception as e:
            print(f"Error saving games data: {e}")
            messagebox.showerror("Error", f"Failed to save game data: {e}")

    def run_game(self, script_path):
        """Execute the game script and update last_played."""
        try:
            # Update last_played timestamp before running
            for game in self.games_data:
                if game["exec"] == script_path:
                    game["last_played"] = datetime.datetime.now().isoformat()
                    break

            # Save the updated data before running the game
            self.save_games()

            # Run the game
            if os.name == 'nt':  # Windows
                os.startfile(script_path)
            else:  # Linux/Mac
                subprocess.Popen(['sh', script_path])

            # After running the game, notify the dashboard to update its "Recently Played Games" section
            if "DashboardFrame" in self.controller.frames and self.controller.frames["DashboardFrame"]:
                self.controller.frames["DashboardFrame"].update_dashboard()
            else:
                print("WARNING: DashboardFrame not found in controller.frames. Cannot update recently played games on dashboard.")

        except FileNotFoundError:
            messagebox.showerror("Error", f"Game script not found: {script_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run game: {e}")

    def get_recently_played_games(self, num_items=15):
        """Get a list of recently played games, sorted by last_played.
        Returns game data including name, image, and exec path.
        """
        # Filter out games without last_played and convert string timestamps to datetime objects
        played_games = []
        for game in self.games_data:
            if "last_played" in game:
                try:
                    # Create a copy to avoid modifying original data
                    game_copy = game.copy()
                    game_copy["last_played_dt"] = datetime.datetime.fromisoformat(game["last_played"])
                    played_games.append(game_copy)
                except ValueError:
                    continue

        # Sort by datetime objects
        played_games.sort(key=lambda x: x["last_played_dt"], reverse=True)

        # Return the original game data (without the temporary datetime field)
        # Include 'image' and 'exec' paths for dashboard display and functionality
        return [
            dict(name=g["name"], last_played=g["last_played"], image=g["image"], exec=g["exec"])
            for g in played_games[:num_items]
        ]

    def get_recently_added_games(self, num_items=15):
        """Placeholder: Get a list of recently added games.
        Currently returns an empty list. Implement actual logic here.
        """
        # You would typically add a 'date_added' timestamp to your game data
        # when a game is first added, and then sort by that timestamp.
        # For now, it just returns an empty list to prevent errors.
        return []

