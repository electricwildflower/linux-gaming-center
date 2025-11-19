import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path

from paths import PathManager, APP_NAME

class DirectoriesFrame(tk.Frame):
    """
    A Tkinter frame for configuring application directory settings.
    Allows users to set a custom root directory for all application data
    or specify separate locations for individual categories.
    """
    def __init__(self, parent, controller, path_manager: PathManager):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.path_manager = path_manager

        self.configure(bg="#1E1E1E")

        self._configure_styles()

        self.canvas = tk.Canvas(self, bg="#1E1E1E", highlightthickness=0)
        # Removed the vertical scrollbar and its configuration
        # self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        # self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame = ttk.Frame(self.canvas, style="Dark.TFrame")

        # REMOVED: This bind as _on_canvas_configure will handle scrollregion updates
        # self.scrollable_frame.bind(
        #     "<Configure>",
        #     lambda e: self.canvas.configure(
        #         scrollregion=self.canvas.bbox("all")
        #     )
        # )

        # Store the ID of the window item created in the canvas
        self.frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Pack the canvas (removed scrollbar packing)
        # self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Bind the canvas's configure event to resize the inner frame
        # This ensures the scrollable_frame fills the width of the canvas
        self.canvas.bind("<Configure>", self._on_canvas_configure) # This needs to be AFTER canvas.pack

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)


        label = ttk.Label(self.scrollable_frame, text="Directories Settings", font=("Arial", 20, "bold"), foreground="#BF5FFF", background="#1E1E1E")
        label.pack(pady=20, padx=20)

        info_label = ttk.Label(self.scrollable_frame, text="Configure custom directories for your gaming center app's data. You can set a single custom location for everything, or specify separate locations for individual categories.",
                               foreground="white", background="#1E1E1E", wraplength=600)
        info_label.pack(pady=10, padx=20)

        self.status_message_var = tk.StringVar()
        self.status_message_label = ttk.Label(self.scrollable_frame, textvariable=self.status_message_var, foreground="#BF5FFF", background="#1E1E1E", wraplength=600)
        self.status_message_label.pack(pady=5, padx=20)

        # --- Global Custom Local Path Section ---
        self._create_section_header(self.scrollable_frame, "Global Local Data Location (All-in-One)", "#8A2BE2")

        global_path_frame = ttk.Frame(self.scrollable_frame, style="Dark.TFrame", padding=10)
        global_path_frame.pack(pady=5, padx=20, fill="x", expand=True)

        ttk.Label(global_path_frame, text="Current Global Root:", foreground="white", background="#1E1E1E", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))
        self.global_path_var = tk.StringVar()
        self.global_path_label = ttk.Label(global_path_frame, textvariable=self.global_path_var, foreground="white", background="#1E1E1E", wraplength=450, anchor="w")
        self.global_path_label.pack(side="left", fill="x", expand=True)

        global_buttons_frame = ttk.Frame(self.scrollable_frame, style="Dark.TFrame")
        global_buttons_frame.pack(pady=5, padx=20, fill="x")

        choose_global_dir_button = ttk.Button(global_buttons_frame, text="Set Global Local Location", command=self._choose_new_global_location, style="Accent.TButton")
        choose_global_dir_button.pack(side="left", padx=5)

        reset_global_button = ttk.Button(global_buttons_frame, text="Reset All to Default", command=self._reset_all_to_default, style="Reset.TButton")
        reset_global_button.pack(side="left", padx=5)

        # --- Individual Custom Path Sections ---
        self._create_section_header(self.scrollable_frame, "Individual Data Locations (Overrides)", "#9932CC")

        self.individual_path_vars = {}
        self.individual_categories = self.path_manager.all_managed_categories

        for category in sorted(self.individual_categories):
            self._create_individual_path_entry(self.scrollable_frame, category)

        self._update_all_path_displays()

        # Ensure scrollregion is set after all content is packed
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox(self.frame_id))


    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Dark.TFrame", background="#282828")
        style.configure("Accent.TButton",
                        background="#BF5FFF",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="#BF5FFF")
        style.map("Accent.TButton",
                  background=[('active', '#A020F0'), ('pressed', '#7B00B0')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        style.configure("Reset.TButton",
                        background="#505050",
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="#707070")
        style.map("Reset.TButton",
                  background=[('active', '#606060'), ('pressed', '#404040')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        style.configure("Dark.TLabel", background="#282828", foreground="white")

        style.configure("SectionHeader.TLabel", background="#363636", foreground="white", font=("Arial", 12, "bold"), padding=5)

    def _create_section_header(self, parent, text, bg_color):
        header_frame = ttk.Frame(parent, style="Dark.TFrame")
        header_frame.pack(pady=(15, 5), padx=20, fill="x")
        header_label = ttk.Label(header_frame, text=text, font=("Arial", 12, "bold"), foreground="white", background=bg_color, padding=5)
        header_label.pack(fill="x", expand=True)

    def _create_individual_path_entry(self, parent, category):
        frame = ttk.Frame(parent, style="Dark.TFrame", padding=10)
        frame.pack(pady=5, padx=20, fill="x", expand=True)

        ttk.Label(frame, text=f"{category.replace('_', ' ').title()} Path:", foreground="white", background="#1E1E1E", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 5))

        path_var = tk.StringVar()
        self.individual_path_vars[category] = path_var
        path_label = ttk.Label(frame, textvariable=path_var, foreground="white", background="#1E1E1E", wraplength=400, anchor="w")
        path_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        buttons_frame = ttk.Frame(frame, style="Dark.TFrame")
        buttons_frame.pack(side="right")

        choose_button = ttk.Button(buttons_frame, text="Choose", command=lambda c=category: self._choose_individual_location(c), style="Accent.TButton")
        choose_button.pack(side="left", padx=2)

        reset_button = ttk.Button(buttons_frame, text="Reset", command=lambda c=category: self._reset_individual_location(c), style="Reset.TButton")
        reset_button.pack(side="left", padx=2)

    def _update_all_path_displays(self):
        active_global_root = self.path_manager.get_active_root_path()
        global_status = "Local Custom" if self.path_manager.is_global_custom_path_active() else "Default"
        self.global_path_var.set(f"{active_global_root} ({global_status})")

        for category in self.individual_categories:
            path = self.path_manager.get_path(category)
            individual_custom_intended = self.path_manager.get_individual_custom_path(category)

            if individual_custom_intended:
                status = "Individual Custom (Active)"
            elif self.path_manager.is_global_custom_path_active():
                status = "Global Custom (Active)"
            else:
                status = "Default"

            self.individual_path_vars[category].set(f"{path} ({status})")

        self.status_message_var.set("")

    def _on_canvas_configure(self, event):
        """
        Adjusts the width of the scrollable_frame to match the canvas's width
        when the canvas is resized and updates the scrollregion.
        """
        self.canvas.itemconfig(self.frame_id, width=event.width)
        # Ensure that content is fully laid out before calculating scrollregion
        self.canvas.update_idletasks()
        # Set scrollregion specifically to the bounding box of the inner frame
        self.canvas.configure(scrollregion=self.canvas.bbox(self.frame_id))


    def _choose_new_global_location(self):
        selected_directory = filedialog.askdirectory(
            parent=self,
            title="Select New Global Local Root Directory for Linux Gaming Center Data",
            initialdir=str(Path.home())
        )

        if selected_directory:
            self.status_message_var.set(f"Attempting to set new global local location: {selected_directory}...")
            self.update_idletasks()

            success = self.path_manager.set_custom_root_path(selected_directory)

            if success:
                self.status_message_var.set(f"Successfully set new global local location and created folder structure in: {selected_directory}")
                self._update_all_path_displays()
                messagebox.showinfo("Success",
                                    f"A new global folder structure has been created under:\n{Path(selected_directory) / APP_NAME}/\n\n"
                                    "No existing data was moved. You will need to manually move your files to the new location.\n\n"
                                    "Please restart the application for all changes to take full effect.")
                # NEW: Notify the controller to reload PathManager config
                self.controller.reload_path_manager_config()
            else:
                self.status_message_var.set("Failed to set new global local location or create folder structure. Check console for details.")
                messagebox.showerror("Error", "Failed to set new global local location or create folder structure. Please check permissions or select a different directory.")
        else:
            self.status_message_var.set("Global local location selection cancelled.")

    def _reset_all_to_default(self):
        if messagebox.askyesno("Confirm Reset All", "Are you sure you want to reset ALL data locations to default?\n\nThis will clear all custom path settings (global and individual). Data currently in custom locations will NOT be moved back to default paths. You will need to manually move it if desired."):
            self.status_message_var.set("Resetting all paths to default...")
            self.update_idletasks()

            success = self.path_manager.reset_to_default_paths()
            if success:
                self.status_message_var.set("Successfully reset all paths to default.")
                self._update_all_path_displays()
                messagebox.showinfo("Success", "All application data locations have been reset to default.\n\nPlease restart the application for all changes to take full effect.")
                # NEW: Notify the controller to reload PathManager config
                self.controller.reload_path_manager_config()
            else:
                self.status_message_var.set("Failed to reset all paths to default. Check console for details.")
                messagebox.showerror("Error", "Failed to reset all paths to default.")

    def _choose_individual_location(self, category):
        old_custom_path_intended = self.path_manager.get_individual_custom_path(category)

        selected_directory = filedialog.askdirectory(
            parent=self,
            title=f"Select New Location for {category.replace('_', ' ').title()}",
            initialdir=str(self.path_manager.get_path(category))
        )

        if selected_directory:
            self.status_message_var.set(f"Attempting to set custom location for {category}: {selected_directory}...")
            self.update_idletasks()

            success = self.path_manager.set_custom_path_for_category(category, selected_directory)

            if success:
                self.status_message_var.set(f"Successfully set custom location for {category} to: {selected_directory}")
                self._update_all_path_displays()

                message_parts = [
                    f"The location for {category.replace('_', ' ').title()} has been successfully updated.",
                    f"A new folder structure has been created under:\n{Path(selected_directory) / APP_NAME / category}/",
                    "No existing ROMs or data were moved. You will need to manually move your files to the new location."
                ]

                if old_custom_path_intended and Path(old_custom_path_intended) != Path(selected_directory) / APP_NAME / category:
                    message_parts.append(f"\nThe previous custom location ({old_custom_path_intended}) is no longer in use. You may manually delete any old custom locations if you are changing from one custom location to another.")

                message_parts.append("\nPlease restart the application for changes to take full effect.")

                messagebox.showinfo("Success", "\n\n".join(message_parts))
                # NEW: Notify the controller to reload PathManager config
                self.controller.reload_path_manager_config()
            else:
                self.status_message_var.set(f"Failed to set custom location for {category}. Check console for details.")
                messagebox.showerror("Error", f"Failed to set custom location for {category}. Please check permissions or select a different directory.")
        else:
            self.status_message_var.set(f"Location selection for {category} cancelled.")

    def _reset_individual_location(self, category):
        if messagebox.askyesno("Confirm Reset Category", f"Are you sure you want to reset the location for {category.replace('_', ' ').title()} to its default/global path?\n\nData currently in the custom location will NOT be moved back."):
            self.status_message_var.set(f"Resetting location for {category}...")
            self.update_idletasks()

            success = self.path_manager.reset_path_for_category(category)
            if success:
                self.status_message_var.set(f"Successfully reset location for {category}.")
                self._update_all_path_displays()
                messagebox.showinfo("Success", f"The location for {category.replace('_', ' ').title()} has been reset.\\n\\nPlease restart the application for changes to take full effect.")
                # NEW: Notify the controller to reload PathManager config
                self.controller.reload_path_manager_config()
            else:
                self.status_message_var.set(f"Failed to reset location for {category}. Check console for details.")
                messagebox.showerror("Error", f"Failed to reset location for {category}.")

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def on_show_frame(self):
        print("Directory Settings Frame is now visible.")
        self._update_all_path_displays()
        self.status_message_var.set("")

