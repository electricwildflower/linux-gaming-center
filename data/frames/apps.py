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

BUTTON_WIDTH = 200
BUTTON_HEIGHT = 150
BUTTON_PADDING = 20
FRAME_PADDING = 20
IMAGE_PADDING = 10


class AppsFrame(ttk.Frame):
    def __init__(self, parent, controller, path_manager):
        super().__init__(parent)

        self.controller = controller
        # NEW: Get the path_manager instance from the controller
        self.path_manager = path_manager

        self.icons = []
        self.apps_data = []
        self.app_widgets = []
        self.theme = self.load_theme() # load_theme will now use path_manager
        self.configure_style()

        self.last_width = 0
        self.initial_load_complete = False
        self.current_menu = None

        self["style"] = "App.TFrame"
        self.bind("<Visibility>", self.on_visibility_change)

        self.controller.bind("<Configure>", self.on_main_window_configure)

        self.setup_ui()
        self.load_apps() # load_apps will now use path_manager
        self.after(200, self.perform_initial_redraw)

    def setup_ui(self):
        controls_frame = ttk.Frame(self, style="App.TFrame")
        controls_frame.pack(fill="x", padx=10, pady=10)

        add_button = ttk.Button(
            controls_frame,
            text="Add App",
            style="App.TButton",
            command=self.open_add_app_dialog,
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
        sort_dropdown.bind("<<ComboboxSelected>>", self.sort_apps)

        self.canvas = tk.Canvas(
            self,
            bg=self.theme.get("background", "#1e1e1e"),
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.grid_frame = ttk.Frame(self.canvas, style="App.TFrame")
        self.grid_frame_id = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")

        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.bind_mousewheel_events()

    def on_canvas_resize(self, event):
        """Update canvas and grid width on resize."""
        self.last_width = event.width
        self.canvas.itemconfig(self.grid_frame_id, width=event.width)
        self.after(100, self.redraw_grid)

    def open_edit_app_dialog(self, index):
        """Open dialog to edit the selected app."""
        app_info = self.apps_data[index]
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit App: {app_info['name']}")
        dialog.configure(bg=self.theme.get("background", "#1e1e1e"))

        dialog.transient(self) # Make dialog modal
        dialog.grab_set()     # Grab all input events

        def themed_label(master, text, row, col=0, sticky="w", padx=5, pady=5):
            label = ttk.Label(master, text=text, style="App.TLabel")
            label.grid(row=row, column=col, sticky=sticky, padx=padx, pady=pady)
            return label

        def themed_entry(master, var=None, row=0, col=1, columnspan=1, sticky="ew", padx=5, pady=5):
            entry = ttk.Entry(master, textvariable=var) if var else ttk.Entry(master)
            entry.grid(row=row, column=col, columnspan=columnspan, sticky=sticky, padx=padx, pady=5)
            return entry

        dialog.columnconfigure(1, weight=1) # Column for entries/buttons to expand

        try:
            # --- Name ---
            themed_label(dialog, "App Name:", 0)
            name_var = tk.StringVar(value=app_info["name"])
            name_entry = themed_entry(dialog, name_var, row=0)

            # --- Image ---
            themed_label(dialog, "Current Image:", 1)
            current_image_label = ttk.Label(
                dialog,
                text=os.path.basename(app_info.get("image", "No Image Selected")),
                style="App.TLabel",
            )
            current_image_label.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

            themed_label(dialog, "Select New Image:", 2)
            new_image_path_var = tk.StringVar()
            new_image_entry = themed_entry(dialog, new_image_path_var, row=2)
            ttk.Button(
                dialog,
                text="Browse",
                style="App.TButton",
                command=lambda: self.browse_image(new_image_path_var),
            ).grid(row=2, column=2, padx=5)

            # --- Run Command Edit Button ---
            themed_label(dialog, "Run Command:", 3)
            ttk.Button(
                dialog,
                text="Edit",
                style="App.TButton",
                command=lambda: self.open_script_for_editing(app_info.get("exec")),
            ).grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)


            # --- Save Changes Button ---
            def save_changes():
                new_name = name_var.get().strip()
                new_image_path = new_image_path_var.get()

                if not new_name:
                    messagebox.showerror("Error", "App Name is required.")
                    return

                old_name = app_info["name"]
                old_image_path = app_info.get("image")
                old_exec_path = app_info["exec"]

                app_info["name"] = new_name

                # Handle new image upload
                if new_image_path:
                    # MODIFIED: Use path_manager for IMAGE_DIR
                    IMAGE_DIR = self.path_manager.get_path("data") / "apps" / "assets"
                    os.makedirs(IMAGE_DIR, exist_ok=True)
                    new_image_filename = os.path.basename(new_image_path)
                    new_image_filepath = IMAGE_DIR / new_image_filename # Use Path object concatenation
                    try:
                        shutil.copy(new_image_path, new_image_filepath)
                        app_info["image"] = str(new_image_filepath) # Store as string
                        if old_image_path and Path(old_image_path).exists() and Path(old_image_path) != new_image_filepath: # Use Path for comparison
                            os.remove(old_image_path)
                    except Exception as e:
                        messagebox.showerror("Error", f"Error updating image: {e}")
                        return

                # Rename script file if name changed
                # MODIFIED: Use path_manager for SCRIPT_DIR
                SCRIPT_DIR = self.path_manager.get_path("data") / "apps" / "run"
                new_exec_filename = f"{new_name.lower().replace(' ', '_')}.sh"
                new_exec_path = SCRIPT_DIR / new_exec_filename # Use Path object concatenation

                if Path(old_exec_path) != new_exec_path: # Use Path for comparison
                    try:
                        if Path(old_exec_path).exists(): # Use Path for exists check
                            shutil.move(old_exec_path, new_exec_path)
                        app_info["exec"] = str(new_exec_path) # Store as string
                    except Exception as e:
                        messagebox.showerror("Error", f"Error renaming run script: {e}")
                        return

                # Save updated data to JSON
                # MODIFIED: Use path_manager for DATA_FILE
                DATA_FILE = self.path_manager.get_path("data") / "apps" / "apps.json"
                try:
                    with open(DATA_FILE, "w") as f:
                        json.dump(self.apps_data, f, indent=4)
                    self.force_redraw()
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"Error saving app data: {e}")

            ttk.Button(
                dialog, text="Save Changes", style="App.TButton", command=save_changes
            ).grid(row=4, column=0, columnspan=3, pady=10) # Adjusted row for new button

            dialog.update_idletasks() # Ensure widgets are rendered and size calculated
            x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
            y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            dialog.wait_window()

        except Exception as e:
            # Catch any error during dialog creation and display it
            messagebox.showerror("Error", f"An error occurred while opening the edit dialog: {e}")
            import traceback
            traceback.print_exc() # Print full traceback to console for debugging
            dialog.destroy() # Close the potentially broken dialog


    def browse_image(self, path_var):
        file_path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")]
        )
        if file_path:
            path_var.set(file_path)

    def open_script_for_editing(self, script_path):
        """
        Opens the specified shell script file in a graphical text editor.
        Tries gedit first, then falls back to xdg-open.
        """
        # MODIFIED: Use Path object for exists check
        if not script_path or not Path(script_path).exists():
            messagebox.showwarning("File Not Found", f"Script file not found: {script_path}")
            print(f"DEBUG: Script file does not exist at: {script_path}")
            return

        print(f"DEBUG: Attempting to open script: {script_path}")
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
                print("ERROR: Neither 'gedit' nor 'xdg-open' found in PATH.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open script '{os.path.basename(script_path)}' with xdg-open: {e}")
                print(f"ERROR: Failed to open script {script_path} with xdg-open: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open script '{os.path.basename(script_path)}' with gedit: {e}")
            print(f"ERROR: Failed to open script {script_path} with gedit: {e}")


    def load_run_command(self, script_path):
        """Load the run command from the app's .sh script."""
        # This method is no longer directly used for displaying in GUI,
        # but might be useful for internal logic if needed.
        # MODIFIED: Use Path object for exists check
        if not Path(script_path).exists():
            print(f"Warning: Script not found at {script_path}")
            return ""
        try:
            with open(script_path, "r") as f:
                lines = f.readlines()
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
        try:
            if not self.winfo_exists():
                return
            current_width = self.winfo_width()
            if current_width > 0 and current_width != self.last_width:
                self.last_width = current_width
                self.after(100, self.delayed_redraw)
        except tk.TclError:
            # Widget has been destroyed, ignore
            pass

    def on_visibility_change(self, event=None):
        """Handle frame becoming visible"""
        try:
            if not self.winfo_exists():
                return
            current_width = self.winfo_width()
            if current_width > 0 and current_width != self.last_width:
                self.last_width = current_width
                self.after(100, self.delayed_redraw)
        except tk.TclError:
            # Widget has been destroyed, ignore
            pass

    def delayed_redraw(self):
        """Delayed call to force redraw."""
        self.force_redraw()

    def force_redraw(self):
        """Force a complete redraw of the grid"""
        canvas_width = self.winfo_width()
        self.canvas.config(width=canvas_width)

        for button_frame in self.app_widgets:
            button_frame.destroy()
        self.app_widgets = []
        self.icons = []

        if hasattr(self, "grid_frame"):
            self.grid_frame.destroy()

        self.grid_frame = ttk.Frame(self.canvas, style="App.TFrame")
        self.grid_frame_id = self.canvas.create_window(
            (0, 0), window=self.grid_frame, anchor="nw"
        )

        for entry in self.apps_data:
            self.add_app_icon(entry)

        self.redraw_grid()

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
        theme_file_path = self.path_manager.get_path("themes") / "cosmictwilight" / "styles" / "apps.json"
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

        style.configure("App.TFrame", background=bg)
        style.configure(
            "App.TLabel",
            background=bg,
            foreground=fg,
            font=(font_family, font_size),
            anchor="center",
        )
        style.configure(
            "App.TButton",
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
        if not self.app_widgets:
            return

        canvas_width = self.canvas.winfo_width()
        if canvas_width <= 0:
            return

        for widget in self.grid_frame.winfo_children():
            widget.grid_forget()

        columns, extra_padding = self.calculate_grid_layout(canvas_width)

        for idx, button_frame in enumerate(self.app_widgets):
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

        for col in range(columns):
            self.grid_frame.columnconfigure(col, weight=1, uniform="app_cols")

        rows = (len(self.app_widgets) + columns - 1) // columns
        total_height = rows * (BUTTON_HEIGHT + 20)
        self.grid_frame.config(height=total_height)
        
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.update_idletasks()

    def open_add_app_dialog(self):
        """Create dialog for adding new app"""
        dialog = tk.Toplevel(self)
        dialog.title("Add App")
        dialog.configure(bg=self.theme.get("background", "#1e1e1e"))

        dialog.transient(self) # Make dialog modal
        dialog.grab_set()     # Grab all input events

        def themed_label(master, text, row):
            label = ttk.Label(master, text=text, style="App.TLabel")
            label.grid(row=row, column=0, sticky="w", padx=5, pady=5)
            return label

        def themed_entry(master, var=None, row=0, col=1, columnspan=1): # Corrected: 'colspan' to 'columnspan'
            entry = ttk.Entry(master, textvariable=var) if var else ttk.Entry(master)
            entry.grid(
                row=row, column=col, columnspan=columnspan, sticky="ew", padx=5, pady=5
            )
            return entry

        dialog.columnconfigure(1, weight=1)

        themed_label(dialog, "App Name:", 0)
        name_entry = themed_entry(dialog, row=0)

        themed_label(dialog, "Select Image:", 1)
        image_path_var = tk.StringVar()
        image_entry = themed_entry(dialog, image_path_var, row=1)
        ttk.Button(
            dialog,
            text="Browse",
            style="App.TButton",
            command=lambda: self.browse_image(image_path_var),
        ).grid(row=1, column=2, padx=5)

        # --- Informative Text for .sh files ---
        # MODIFIED: Use path_manager for the example path
        SCRIPT_DIR_EXAMPLE = self.path_manager.get_path("data") / "apps" / "run"
        info_label = ttk.Label(
            dialog,
            text=f"Please add run commands for apps under:\n{SCRIPT_DIR_EXAMPLE}",
            style="App.TLabel",
            wraplength=300, # Adjust as needed
            justify="left"
        )
        info_label.grid(row=2, column=0, columnspan=3, padx=5, pady=10, sticky="w")


        def save():
            name = name_entry.get().strip()
            image_path = image_path_var.get()
            
            # Default placeholder command for new apps
            run_command = "#!/bin/bash\n# Add your app launch command here.\n# Example: /usr/bin/firefox"

            if not name or not image_path:
                messagebox.showerror("Error", "App Name and Image are required.")
                return

            # MODIFIED: Use path_manager for IMAGE_DIR and SCRIPT_DIR
            IMAGE_DIR = self.path_manager.get_path("data") / "apps" / "assets"
            SCRIPT_DIR = self.path_manager.get_path("data") / "apps" / "run"

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
            DATA_FILE = self.path_manager.get_path("data") / "apps" / "apps.json"
            if DATA_FILE.exists(): # Use Path object's exists()
                with open(DATA_FILE, "r") as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
                    else:
                        data = []
            else:
                data = []

            data.append(new_entry)

            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)

            self.apps_data = data
            self.sort_apps()
            dialog.destroy()

        ttk.Button(dialog, text="Save", style="App.TButton", command=save).grid(
            row=3, column=0, columnspan=3, pady=10 # Adjusted row for new info label
        )

        dialog.update_idletasks() # Ensure widgets are rendered and size calculated
        x = self.winfo_x() + (self.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.wait_window()

    def load_apps(self):
        """Load apps from JSON file and apply initial sorting"""
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "apps" / "apps.json"
        if not DATA_FILE.exists(): # Use Path object's exists()
            print(f"Info: {DATA_FILE} not found. Initializing with empty app data.")
            self.apps_data = []
            return
        try:
            with open(DATA_FILE, "r") as f:
                content = f.read().strip()
                if not content:
                    print(f"Info: {DATA_FILE} is empty. Initializing with empty app data.")
                    self.apps_data = []
                else:
                    self.apps_data = json.loads(content)
            self.sort_apps()
        except json.JSONDecodeError as e:
            print(f"Error: Malformed JSON in {DATA_FILE}: {e}. Initializing with empty app data.")
            print("Please check or delete the 'apps.json' file if this error persists.")
            self.apps_data = []
        except Exception as e:
            print(f"An unexpected error occurred while loading {DATA_FILE}: {e}. Initializing with empty app data.")
            self.apps_data = []

    def sort_apps(self, event=None):
        """Sort the apps data and redraw the grid based on the selected option."""
        selected_sort = self.sort_var.get()

        if selected_sort == "A to Z":
            self.apps_data.sort(key=lambda item: item["name"].lower())
        elif selected_sort == "Z to A":
            self.apps_data.sort(key=lambda item: item["name"].lower(), reverse=True)
        elif selected_sort == "Date Added":
            pass

        for widget in self.app_widgets:
            widget.destroy()
        self.app_widgets = []
        self.icons = []
        for entry in self.apps_data:
            self.add_app_icon(entry)
        self.force_redraw()

    def show_context_menu(self, event, index):
        if self.current_menu:
            self.current_menu.unpost()

        menu = tk.Menu(self, tearoff=0, bg=self.theme.get("background", "#1e1e1e"), fg=self.theme.get("text_color", "#ffffff"))
        menu.add_command(label="Edit App", command=lambda: self.open_edit_app_dialog(index))
        menu.add_separator()
        menu.add_command(label="Delete App", command=lambda: self.delete_app(index))

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

    def delete_app(self, index):
        app = self.apps_data[index]
        confirm = messagebox.askyesno("Delete App", f"Are you sure you want to delete '{app['name']}'?")
        if not confirm:
            return

        # MODIFIED: Use Path object for exists check
        if Path(app["image"]).exists():
            try:
                os.remove(app["image"])
            except Exception as e:
                print(f"Failed to remove image: {e}")

        # MODIFIED: Use Path object for exists check
        if Path(app["exec"]).exists():
            try:
                os.remove(app["exec"])
            except Exception as e:
                print(f"Failed to remove exec script: {e}")

        del self.apps_data[index]
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "apps" / "apps.json"
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.apps_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save updated data: {e}")
            return

        self.force_redraw()

    def add_app_icon(self, entry):
        """Add app button to the grid"""
        try:
            # MODIFIED: Use Path object for exists check
            if not Path(entry["image"]).exists():
                print(f"Warning: Image file not found for app '{entry['name']}' at '{entry['image']}'. Skipping image loading.")
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

            button_frame = ttk.Frame(self.grid_frame, style="App.TFrame")

            img_label = ttk.Label(button_frame, image=photo, style="App.TLabel")
            img_label.pack(pady=(0, 5))

            text_label = ttk.Label(
                button_frame,
                text=entry["name"],
                style="App.TLabel",
                wraplength=BUTTON_WIDTH - 10,
                justify="center",
            )
            text_label.pack()

            button_frame.bind(
                "<Button-1>", lambda e, path=entry["exec"]: self.run_app(path)
            )
            img_label.bind(
                "<Button-1>", lambda e, path=entry["exec"]: self.run_app(path)
            )
            text_label.bind(
                "<Button-1>", lambda e, path=entry["exec"]: self.run_app(path)
            )

            index = len(self.app_widgets)
            img_label.bind(
                "<Button-3>",
                lambda event, idx=index: self.show_context_menu(event, idx),
            )
            text_label.bind(
                "<Button-3>",
                lambda event, idx=index: self.show_context_menu(event, idx),
            )

            self.app_widgets.append(button_frame)
        except Exception as e:
            print(f"Error loading app icon: {e}")
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

    def run_app(self, script_path):
        """Execute the app script and update last_played."""
        try:
            if os.name == 'nt':
                subprocess.Popen(['cmd.exe', '/C', script_path], shell=True) # Use cmd.exe /C for Windows .bat/.exe
            else:
                subprocess.Popen(['sh', script_path])

        except FileNotFoundError:
            messagebox.showerror("Error", f"Script not found: {script_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error running script: {e}")
        finally:
            for app in self.apps_data:
                if app["exec"] == script_path:
                    app["last_played"] = datetime.datetime.now().isoformat()
                    self.save_apps()
                    break
            # Notify dashboard to update recently played apps
            if "DashboardFrame" in self.controller.frames and self.controller.frames["DashboardFrame"]:
                self.controller.frames["DashboardFrame"].update_dashboard()
            else:
                print("WARNING: DashboardFrame not found in controller.frames. Cannot update recently played apps on dashboard.")


    def save_apps(self):
        """Save the apps data to the JSON file."""
        # MODIFIED: Use path_manager for DATA_FILE
        DATA_FILE = self.path_manager.get_path("data") / "apps" / "apps.json"
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.apps_data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save app data: {e}")

    def get_recently_played_apps(self, num_items=15):
        """Get a list of recently played apps, sorted by last_played.
        Returns app data including name, image, and exec path.
        """
        played_apps = []
        for app in self.apps_data:
            if "last_played" in app:
                try:
                    app_copy = app.copy()
                    app_copy["last_played_dt"] = datetime.datetime.fromisoformat(app["last_played"])
                    played_apps.append(app_copy)
                except ValueError:
                    continue
        
        played_apps.sort(
            key=lambda x: x["last_played_dt"], reverse=True
        )
        # MODIFIED: Ensure SCRIPT_DIR is retrieved via path_manager for this return
        SCRIPT_DIR_FOR_RETURN = self.path_manager.get_path("data") / "apps" / "run"
        return [
            dict(name=a["name"], last_played=a["last_played"], image=a.get("image"), exec=a["exec"], script_dir=str(SCRIPT_DIR_FOR_RETURN)) # Store as string
            for a in played_apps[:num_items]
        ]

