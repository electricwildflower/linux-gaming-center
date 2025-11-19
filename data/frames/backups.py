import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
import datetime
from pathlib import Path
import tarfile # NEW: Import tarfile for creating tar.gz archives

from paths import PathManager, APP_NAME

class BackupsFrame(tk.Frame):
    def __init__(self, parent, controller, path_manager: PathManager):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        self.path_manager = path_manager

        self.configure(bg="#1E1E1E") # Consistent dark background
        self._configure_styles()

        self.canvas = tk.Canvas(self, bg="#1E1E1E", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollable_frame = ttk.Frame(self.canvas, style="Dark.TFrame")
        self.frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        self.setup_ui()

        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox(self.frame_id))

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Cosmic Twilight color scheme: black, dark grey, purple
        style.configure("Dark.TFrame", background="#2D2D2D")  # Dark grey
        style.configure("Accent.TButton",
                        background="#9a32cd",  # Purple
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="#9a32cd")
        style.map("Accent.TButton",
                  background=[('active', '#7d26cd'), ('pressed', '#6a1b9a')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        style.configure("Danger.TButton",
                        background="#9a32cd",  # Purple instead of red
                        foreground="white",
                        font=("Arial", 10, "bold"),
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="#9a32cd")
        style.map("Danger.TButton",
                  background=[('active', '#7d26cd'), ('pressed', '#6a1b9a')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        style.configure("Dark.TLabel", background="#2D2D2D", foreground="white")
        style.configure("SectionHeader.TLabel", background="#404040", foreground="white", font=("Arial", 12, "bold"), padding=5)
        style.configure("Title.TLabel", background="#1E1E1E", foreground="#9a32cd", font=("Arial", 20, "bold"))

    def _create_section_header(self, parent, text, bg_color):
        header_frame = ttk.Frame(parent, style="Dark.TFrame")
        header_frame.pack(pady=(15, 5), padx=20, fill="x")
        header_label = ttk.Label(header_frame, text=text, font=("Arial", 12, "bold"), foreground="white", background=bg_color, padding=5)
        header_label.pack(fill="x", expand=True)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.frame_id, width=event.width)
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox(self.frame_id))

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

    def setup_ui(self):
        label = ttk.Label(self.scrollable_frame, text="Backup & Restore", style="Title.TLabel")
        label.pack(pady=20, padx=20)

        # --- Backup & Restore Application Data Section ---
        self._create_section_header(self.scrollable_frame, "Backup & Restore Application Data", "#404040") # Dark grey header

        backup_restore_app_frame = ttk.Frame(self.scrollable_frame, style="Dark.TFrame", padding=10)
        backup_restore_app_frame.pack(pady=5, padx=20, fill="x", expand=True)

        backup_info_label = ttk.Label(backup_restore_app_frame, text="Backup your application's configuration and managed data (games, emulators, apps lists, images, scripts). ROMs and BIOS files are NOT included in this backup.",
                                     foreground="white", background="#2D2D2D", wraplength=550)
        backup_info_label.pack(pady=5, padx=5, anchor="w")

        backup_button = ttk.Button(backup_restore_app_frame, text="Backup App Data", command=self._backup_app_data, style="Accent.TButton")
        backup_button.pack(pady=10, padx=5, side="left")

        restore_button = ttk.Button(backup_restore_app_frame, text="Restore App Data", command=self._restore_app_data, style="Danger.TButton")
        restore_button.pack(pady=10, padx=5, side="left")

        # --- Backup BIOS Data Section ---
        self._create_section_header(self.scrollable_frame, "Backup BIOS Files", "#404040") # Dark grey header

        backup_bios_frame = ttk.Frame(self.scrollable_frame, style="Dark.TFrame", padding=10)
        backup_bios_frame.pack(pady=5, padx=20, fill="x", expand=True)

        bios_backup_info_label = ttk.Label(backup_bios_frame, text="Backup your custom BIOS files. This will create a separate archive containing only the files in your configured BIOS directory.",
                                          foreground="white", background="#2D2D2D", wraplength=550)
        bios_backup_info_label.pack(pady=5, padx=5, anchor="w")

        backup_bios_button = ttk.Button(backup_bios_frame, text="Backup BIOS Data", command=self._backup_bios_data, style="Accent.TButton")
        backup_bios_button.pack(pady=10, padx=5)


        # Add a button to go back to AdminPanel
        back_button = ttk.Button(self.scrollable_frame, text="< Back to Admin Panel",
                                 command=lambda: self.controller.show_frame("AdminPanelFrame"),
                                 style="Accent.TButton")
        back_button.pack(pady=20)


    def _get_app_managed_data_paths(self):
        """
        Returns a dictionary of source paths (Path objects) for all app-managed data
        that should be included in a backup, relative to their respective root.
        """
        data_to_backup = {}

        # 1. PathManager config file
        # Use a relative path for paths.json within the backup structure
        data_to_backup[self.path_manager.path_config_file] = Path("config") / "paths.json"

        # 2. Accounts and Settings (under config root)
        accounts_path = self.path_manager.get_path("accounts")
        # Use relative paths for backup staging
        if accounts_path.exists(): # Only include if the directory exists
            data_to_backup[accounts_path] = Path("config") / "accounts"

        settings_path = self.path_manager.get_path("settings")
        if settings_path.exists(): # Only include if the directory exists
            data_to_backup[settings_path] = Path("config") / "settings"

        # 3. Emulators data (under data root)
        emulator_data_base_path = self.path_manager.get_path("data") / "emulators"
        if emulator_data_base_path.exists(): # Only include if the directory exists
            data_to_backup[emulator_data_base_path] = Path("data") / "emulators"

        # 4. Open Source Games data (under data root)
        opensource_games_base_path = self.path_manager.get_path("data") / "games" / "opensourcegames"
        if opensource_games_base_path.exists(): # Only include if the directory exists
            data_to_backup[opensource_games_base_path] = Path("data") / "games" / "opensourcegames"

        # 5. Windows/Steam/Wine Games data (under data root)
        windows_steam_wine_base_path = self.path_manager.get_path("data") / "games" / "windowsandsteam"
        if windows_steam_wine_base_path.exists(): # Only include if the directory exists
            data_to_backup[windows_steam_wine_base_path] = Path("data") / "games" / "windowsandsteam"

        # 6. Apps data (under data root)
        apps_base_path = self.path_manager.get_path("data") / "apps"
        if apps_base_path.exists(): # Only include if the directory exists
            data_to_backup[apps_base_path] = Path("data") / "apps"

        # 7. Themes data (under data root) - NEWLY ADDED
        themes_base_path = self.path_manager.get_path("themes")
        if themes_base_path.exists(): # Only include if the directory exists
            data_to_backup[themes_base_path] = Path("data") / "themes"


        # Note: ROMs and BIOS directories themselves are not copied, only their paths are in paths.json
        # The user is responsible for backing up their actual game/bios files.

        return data_to_backup

    def _backup_app_data(self):
        """Handles the backup process for application data and configuration, creating a tar.gz archive."""
        backup_dir = filedialog.askdirectory(
            parent=self,
            title="Select a Destination Folder for Application Data Backup",
            initialdir=str(Path.home())
        )

        if not backup_dir:
            messagebox.showinfo("Backup Cancelled", "Application data backup cancelled.")
            return

        backup_dir_path = Path(backup_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name_prefix = f"{APP_NAME}_app_data_backup_{timestamp}" # More specific name
        full_archive_path_no_ext = backup_dir_path / archive_name_prefix
        full_archive_path_with_ext = f"{full_archive_path_no_ext}.tar.gz"

        # Create a temporary staging directory for the archive content
        temp_staging_dir = Path.home() / ".cache" / APP_NAME / f"backup_staging_{timestamp}"
        temp_staging_dir.mkdir(parents=True, exist_ok=True)
        # Created temporary staging directory

        try:
            data_to_backup = self._get_app_managed_data_paths()
            # Data sources identified

            for source_path, relative_dest in data_to_backup.items():
                dest_path = temp_staging_dir / relative_dest
                # Staging files
                if source_path.exists():
                    if source_path.is_dir():
                        shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                    elif source_path.is_file():
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path, dest_path)
                    else:
                        # Warning: Invalid source path type, skipping
                        pass
                else:
                    # Warning: Source path does not exist, skipping
                    pass

            # Create the tar.gz archive
            # Creating archive
            shutil.make_archive(str(full_archive_path_no_ext), 'gztar', root_dir=str(temp_staging_dir))
            # Archive created

            messagebox.showinfo("Backup Complete", f"Application data successfully backed up to:\n{full_archive_path_with_ext}")
            # Backup completed successfully

        except Exception as e:
            messagebox.showerror("Backup Error", f"An error occurred during backup: {e}")
            # Error occurred during backup
        finally:
            # Clean up the temporary staging directory
            if temp_staging_dir.exists():
                # Cleaning up temporary staging directory
                shutil.rmtree(temp_staging_dir)
            # App Data Backup process finished

    def _backup_bios_data(self):
        """Handles the backup process for BIOS files, creating a tar.gz archive."""
        bios_path = self.path_manager.get_path("bios")

        if not bios_path.exists() or not any(bios_path.iterdir()): # Check if directory exists and is not empty
            messagebox.showwarning("BIOS Backup Warning", f"The BIOS directory '{bios_path}' is empty or does not exist. There are no BIOS files to back up.")
            # Warning: BIOS directory empty or non-existent
            return

        backup_dir = filedialog.askdirectory(
            parent=self,
            title="Select a Destination Folder for BIOS Backup",
            initialdir=str(Path.home())
        )

        if not backup_dir:
            messagebox.showinfo("BIOS Backup Cancelled", "BIOS backup cancelled.")
            return

        backup_dir_path = Path(backup_dir)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name_prefix = f"{APP_NAME}_bios_backup_{timestamp}" # Specific name for BIOS backup
        full_archive_path_no_ext = backup_dir_path / archive_name_prefix
        full_archive_path_with_ext = f"{full_archive_path_no_ext}.tar.gz"

        # Create a temporary staging directory for the archive content
        temp_staging_dir = Path.home() / ".cache" / APP_NAME / f"bios_backup_staging_{timestamp}"
        temp_staging_dir.mkdir(parents=True, exist_ok=True)
        # Created temporary staging directory

        try:
            # Copy BIOS files to the staging directory
            # We want the contents of the bios_path directly in the root of the archive,
            # so copy into a subdirectory within temp_staging_dir
            staging_bios_content_dir = temp_staging_dir / "bios_content" # This will be the root inside the archive
            staging_bios_content_dir.mkdir(parents=True, exist_ok=True)
            
            # Staging BIOS files
            shutil.copytree(bios_path, staging_bios_content_dir, dirs_exist_ok=True)

            # Create the tar.gz archive from the staging directory
            # Creating archive
            # root_dir should be temp_staging_dir, and base_dir should be "bios_content" if we want that structure
            # Or, more simply, root_dir is the parent of bios_content, and base_dir is bios_content
            shutil.make_archive(str(full_archive_path_no_ext), 'gztar', root_dir=str(temp_staging_dir), base_dir="bios_content")
            # Archive created

            messagebox.showinfo("BIOS Backup Complete", f"BIOS files successfully backed up to:\n{full_archive_path_with_ext}")
            # Backup completed successfully

        except Exception as e:
            messagebox.showerror("BIOS Backup Error", f"An error occurred during BIOS backup: {e}")
            # Error occurred during BIOS backup
        finally:
            # Clean up the temporary staging directory
            if temp_staging_dir.exists():
                # Cleaning up temporary staging directory
                shutil.rmtree(temp_staging_dir)
            # BIOS Backup process finished


    def _restore_app_data(self):
        """Handles the restore process for application data and configuration from a tar.gz archive."""
        backup_archive_path_str = filedialog.askopenfilename(
            parent=self,
            title="Select the Backup Archive (.tar.gz) to Restore From",
            initialdir=str(Path.home()),
            filetypes=[("Tar GZ archives", "*.tar.gz"), ("All files", "*.*")]
        )

        if not backup_archive_path_str:
            messagebox.showinfo("Restore Cancelled", "Application data restore cancelled.")
            return

        backup_archive_path = Path(backup_archive_path_str)

        if not backup_archive_path.is_file() or not backup_archive_path.name.endswith(".tar.gz"):
            messagebox.showerror("Restore Error", "Please select a valid .tar.gz backup archive.")
            return

        # Create a temporary extraction directory
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_extract_dir = Path.home() / ".cache" / APP_NAME / f"restore_staging_{timestamp}"
        temp_extract_dir.mkdir(parents=True, exist_ok=True)
        # Created temporary extraction directory

        try:
            # Extract the archive
            # Extracting archive
            with tarfile.open(backup_archive_path, "r:gz") as tar:
                tar.extractall(path=temp_extract_dir)
            # Archive extracted successfully

            # Step 1: Restore paths.json FIRST from the extracted content
            backup_paths_file_in_temp = temp_extract_dir / "config" / "paths.json"
            if backup_paths_file_in_temp.is_file():
                # Restoring paths.json
                self.path_manager.path_config_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_paths_file_in_temp, self.path_manager.path_config_file)
                # paths.json restored successfully
                # Force PathManager to reload its configuration from the restored file
                self.controller.reload_path_manager_config()
            else:
                # Warning: No paths.json found in backup, current path settings will be retained
                messagebox.showwarning("Restore Warning", "No 'paths.json' found in the backup. Your current application directory settings will remain unchanged.")

            # Step 2: Restore other application-managed data based on the (potentially new) active paths
            data_to_restore_mapping = {
                Path("config") / "accounts": self.path_manager.get_path("accounts"),
                Path("config") / "settings": self.path_manager.get_path("settings"),
                Path("data") / "emulators": self.path_manager.get_path("data") / "emulators",
                Path("data") / "games" / "opensourcegames": self.path_manager.get_path("data") / "games" / "opensourcegames",
                Path("data") / "games" / "windowsandsteam": self.path_manager.get_path("data") / "games" / "windowsandsteam",
                Path("data") / "apps": self.path_manager.get_path("data") / "apps",
                Path("data") / "themes": self.path_manager.get_path("themes"), # NEW: Add themes to restore mapping
            }

            for relative_source_in_temp, destination_path in data_to_restore_mapping.items():
                source_path_in_temp = temp_extract_dir / relative_source_in_temp
                # Attempting to restore

                if source_path_in_temp.exists():
                    if source_path_in_temp.is_dir():
                        # Remove existing directory content before copying to ensure a clean restore
                        if destination_path.exists():
                            # Clearing existing directory
                            shutil.rmtree(destination_path)
                        destination_path.mkdir(parents=True, exist_ok=True) # Recreate empty directory
                        shutil.copytree(source_path_in_temp, destination_path, dirs_exist_ok=True) # Copy contents
                        # Restored directory
                    elif source_path_in_temp.is_file():
                        destination_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_path_in_temp, destination_path)
                        # Restored file
                else:
                    # Warning: Source path does not exist in backup, skipping
                    pass

            messagebox.showinfo("Restore Complete",
                                "Application data successfully restored.\n\nPlease restart the application for all changes to take full effect.")
            # Restore completed successfully

        except tarfile.ReadError as e:
            messagebox.showerror("Restore Error", f"Failed to read archive. It might be corrupted or not a valid .tar.gz file: {e}")
            # Error: Tarfile read error
        except Exception as e:
            messagebox.showerror("Restore Error", f"An error occurred during restore: {e}")
            # Error occurred during restore
        finally:
            # Clean up the temporary extraction directory
            if temp_extract_dir.exists():
                # Cleaning up temporary extraction directory
                shutil.rmtree(temp_extract_dir)
            # Restore process finished

    def on_show_frame(self):
        """Called when this frame is brought to the front."""
        # Backups Settings Frame is now visible

