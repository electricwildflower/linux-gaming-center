import os
import json
import shutil
from pathlib import Path

# Define the application name for directory creation
APP_NAME = "linux-gaming-center"

class PathManager:
    """
    Manages all application-specific file paths, allowing for:
    1. A global custom root directory for all data.
    2. Individual custom directories for specific categories (roms, bios, etc.)
       which override the global setting for that category.
    It falls back to default locations if custom paths are unavailable or invalid.
    """

    def __init__(self):
        """
        Initializes the PathManager, setting up default paths and attempting
        to load any previously saved custom root path and individual paths.
        """
        # Define default root directories based on XDG Base Directory Specification
        self.default_config_root = Path.home() / ".config" / APP_NAME
        self.default_data_root = Path.home() / ".local" / "share" / APP_NAME

        # Define subdirectories relative to their respective roots
        # Note: 'accounts' is under config, others under data
        self.config_subdirs = ["accounts"] # Removed "settings" as it's not in use
        self.data_subdirs = ["bios", "roms", "themes", "data"]
        # All managed categories, regardless of their default config/data split
        self.all_managed_categories = self.config_subdirs + self.data_subdirs

        # Path to the configuration file that stores all path settings
        self.path_config_file = self.default_config_root / "paths.json"

        # Initialize active paths
        self._active_custom_root_path = None
        self._individual_custom_paths = {} # Stores Path objects for individual overrides

        self._ensure_base_dirs()
        self.load_paths() # Load saved paths after ensuring base directories

    def _ensure_base_dirs(self):
        """Ensures the default configuration and data root directories exist."""
        try:
            self.default_config_root.mkdir(parents=True, exist_ok=True)
            self.default_data_root.mkdir(parents=True, exist_ok=True)

            # Also ensure default subdirectories under default_data_root exist
            for subdir in self.data_subdirs:
                (self.default_data_root / subdir).mkdir(parents=True, exist_ok=True)

            # And default subdirectories under default_config_root exist
            for subdir in self.config_subdirs:
                (self.default_config_root / subdir).mkdir(parents=True, exist_ok=True)

        except OSError as e:
            print(f"ERROR (PathManager): Failed to create base directories: {e}")
            # Handle this gracefully in a GUI app, e.g., show an error message
            # messagebox.showerror("Directory Error", f"Failed to create essential directories: {e}")
            # sys.exit(1) # Or some other error handling
        except Exception as e:
            print(f"ERROR (PathManager): An unexpected error occurred during directory setup: {e}")


    def load_paths(self):
        """Loads custom path settings from the configuration file."""
        if self.path_config_file.exists():
            try:
                with open(self.path_config_file, "r") as f:
                    content = f.read().strip()
                    if content:
                        settings = json.loads(content)
                        global_root = settings.get("global_custom_root")
                        if global_root:
                            self._active_custom_root_path = Path(global_root)
                        else:
                            self._active_custom_root_path = None

                        individual_paths_dict = settings.get("individual_custom_paths", {})
                        self._individual_custom_paths = {k: Path(v) for k, v in individual_paths_dict.items()}
                    else:
                        self._active_custom_root_path = None
                        self._individual_custom_paths = {}
            except json.JSONDecodeError as e:
                print(f"ERROR (PathManager): Malformed JSON in {self.path_config_file}: {e}. Resetting paths.")
                self._active_custom_root_path = None
                self._individual_custom_paths = {}
                # Optionally, delete the corrupted file here
                # self.path_config_file.unlink(missing_ok=True)
            except Exception as e:
                print(f"ERROR (PathManager): An unexpected error occurred loading {self.path_config_file}: {e}. Resetting paths.")
                self._active_custom_root_path = None
                self._individual_custom_paths = {}
        else:
            # Ensure an empty paths.json is created if it doesn't exist and we're starting fresh
            self.save_paths() # This will create an empty paths.json if it's missing initially

    def save_paths(self):
        """Saves the current custom path settings to the configuration file."""
        settings = {
            "global_custom_root": str(self._active_custom_root_path) if self._active_custom_root_path else None,
            "individual_custom_paths": {k: str(v) for k, v in self._individual_custom_paths.items()}
        }
        try:
            # Ensure the parent directory for paths.json exists
            self.path_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path_config_file, "w") as f:
                json.dump(settings, f, indent=4)
            print(f"INFO (PathManager): Path settings successfully saved to {self.path_config_file}")
        except Exception as e:
            print(f"ERROR (PathManager): Failed to save path settings to {self.path_config_file}: {e}")

    def get_path(self, category: str) -> Path:
        """
        Returns the active path for a given category.
        Prioritizes individual custom path, then global custom root, then default.
        """
        if category not in self.all_managed_categories:
            print(f"WARNING (PathManager): Category '{category}' is not a managed category. Returning default data root.")
            # Fallback for unmanaged categories, might need to be adjusted based on usage
            return self.default_data_root / category

        # 1. Check for individual custom path
        if category in self._individual_custom_paths and self._individual_custom_paths[category].is_dir():
            path = self._individual_custom_paths[category]
            path.mkdir(parents=True, exist_ok=True) # Ensure it exists when accessed
            return path

        # 2. Check for global custom root path
        if self._active_custom_root_path and self._active_custom_root_path.is_dir():
            # MODIFIED: All categories directly under APP_NAME within the global custom root
            path = self._active_custom_root_path / APP_NAME / category
            path.mkdir(parents=True, exist_ok=True) # Ensure it exists when accessed
            return path

        # 3. Fallback to default path
        if category in self.config_subdirs:
            path = self.default_config_root / category
        else:
            path = self.default_data_root / category
        
        # Ensure the default path exists when accessed
        path.mkdir(parents=True, exist_ok=True) # Ensure it exists when accessed
        return path

    def set_custom_root_path(self, path_str: str) -> bool:
        """
        Sets a new global custom root path for all application data.
        Creates the necessary category subdirectories directly under APP_NAME
        within the new root.
        """
        new_root = Path(path_str)
        if not new_root.is_dir():
            print(f"ERROR (PathManager): Custom root path '{new_root}' is not a valid directory.")
            return False

        # The base directory for all app data under the new root
        app_base_root = new_root / APP_NAME

        try:
            app_base_root.mkdir(parents=True, exist_ok=True)

            # Create all managed category subdirectories directly under app_base_root
            for subdir in self.all_managed_categories: # MODIFIED: Iterate through all_managed_categories
                (app_base_root / subdir).mkdir(parents=True, exist_ok=True)

            self._active_custom_root_path = new_root # Store the user-selected root
            self._individual_custom_paths = {} # Clear individual overrides when global is set
            self.save_paths()
            print(f"INFO (PathManager): Global custom root set to: {self._active_custom_root_path}")
            return True
        except OSError as e:
            print(f"ERROR (PathManager): Failed to create subdirectories under {new_root}: {e}")
            return False

    def reset_to_default_paths(self) -> bool:
        """Resets all paths to their default XDG locations."""
        self._active_custom_root_path = None
        self._individual_custom_paths = {}
        self.save_paths()
        print("INFO (PathManager): All paths reset to default.")
        return True

    def set_custom_path_for_category(self, category: str, path_str: str) -> bool:
        """
        Sets a custom path for a specific category, overriding the global setting.
        Creates the necessary directory structure (APP_NAME/category) if it doesn't exist.
        """
        if category not in self.all_managed_categories:
            print(f"ERROR (PathManager): Cannot set custom path for unmanaged category: {category}")
            return False

        new_base_path = Path(path_str)
        if not new_base_path.is_dir():
            print(f"ERROR (PathManager): Custom base path for '{category}' is not a valid directory: {new_base_path}")
            return False

        # The final path should be new_base_path / APP_NAME / category
        final_path_for_category = new_base_path / APP_NAME / category
        try:
            final_path_for_category.mkdir(parents=True, exist_ok=True)
            self._individual_custom_paths[category] = final_path_for_category
            self.save_paths()
            print(f"INFO (PathManager): Individual custom path for '{category}' set to: {final_path_for_category}")
            return True
        except OSError as e:
            print(f"ERROR (PathManager): Failed to create directory for '{category}' at {final_path_for_category}: {e}")
            return False


    def reset_path_for_category(self, category: str) -> bool:
        """Resets the custom path for a specific category to use the global/default setting."""
        if category in self._individual_custom_paths:
            del self._individual_custom_paths[category]
            self.save_paths()
            print(f"INFO (PathManager): Individual custom path for '{category}' reset.")
            return True
        print(f"INFO (PathManager): No individual custom path to reset for '{category}'.")
        return False

    def is_global_custom_path_active(self) -> bool:
        """Checks if a global custom root path is currently active."""
        return self._active_custom_root_path is not None and self._active_custom_root_path.is_dir()

    def get_active_root_path(self) -> Path:
        """
        Returns the currently active root path (global custom or default data root).
        For global custom, returns the user-selected root, not the nested APP_NAME folder.
        """
        if self.is_global_custom_path_active():
            return self._active_custom_root_path
        return self.default_data_root # For display, default to data root as a general reference

    def get_individual_custom_path(self, category: str) -> Path | None:
        """Returns the individual custom path for a category if set, otherwise None."""
        path = self._individual_custom_paths.get(category)
        if path and path.is_dir():
            return path
        return None

