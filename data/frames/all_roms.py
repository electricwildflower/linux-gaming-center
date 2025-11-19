import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import json
import datetime

# Define a set of common ROM extensions. This should be consistent across the app.
# Duplicated here for self-containment of the generated frame, but ideally
# this would be imported from a central config/constants file if available.
COMMON_ROM_EXTENSIONS = {
    '.nes', '.snes', '.gb', '.bin', '.chd', '.cue','.gba', '.gen', '.md', '.n64', '.ps1', '.iso',
    '.zip', '.7z', '.rar'
}

# Path to the main data file for emulators (to update last_played for ROMs)
# This path needs to be correct for the generated file's context
EMULATORS_DATA_FILE = os.path.join(os.path.expanduser("~/.local/share/linux-gaming-center/data/emulators"), "emulators.json").replace(os.sep, '/')
ROMS_DATA_DIR = os.path.expanduser("~/.local/share/linux-gaming-center/data/emulators/rom_data").replace(os.sep, '/')


class AllRomsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.all_roms_data = [] # Stores consolidated ROM info
        self.rom_cache_manager = None  # Will be set by main.py

        self.setup_ui()
        self.bind("<Visibility>", self.on_visibility_change) # Bind for when frame becomes visible

    def set_rom_cache_manager(self, rom_cache_manager):
        """Set the ROM cache manager instance"""
        self.rom_cache_manager = rom_cache_manager

    def setup_ui(self):
        main_frame = ttk.Frame(self, style="AllRomsFrame.TFrame")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Back button
        style = ttk.Style(self)
        style.configure("AllRomsFrame.BackButton.TButton",
                        background="#333344", # Dark grey
                        foreground="#9a32cd", # Purple
                        font=("Arial", 10, "bold"),
                        padding=5)

        back_button = ttk.Button(
            main_frame,
            text="< Back to Emulators",
            command=lambda: self.controller.show_frame("EmulatorsFrame"),
            style="AllRomsFrame.BackButton.TButton"
        )
        back_button.pack(anchor="nw", padx=0, pady=0)

        # Title - MODIFIED TO USE STYLE
        ttk.Label(
            main_frame,
            text="ALL AVAILABLE ROMS",
            font=("Impact", 24),
            style="AllRomsFrame.Title.TLabel" # Use the defined style
        ).pack(pady=(10, 20))

        # Listbox for ROMs
        roms_list_frame = ttk.Frame(main_frame, style="AllRomsFrame.TFrame")
        roms_list_frame.pack(fill="both", expand=True)

        self.rom_listbox = tk.Listbox(
            roms_list_frame,
            selectmode="browse",
            bg="#333333", # Dark background
            fg="white", # White text
            font=("Arial", 12),
            selectbackground="purple", # Highlight color
            selectforeground="white",
            exportselection=False,
            bd=0,
            highlightthickness=0
        )
        self.rom_listbox.pack(side="left", fill="both", expand=True)

        # Removed the scrollbar widget and its configuration from here.
        # scrollbar = ttk.Scrollbar(roms_list_frame, orient="vertical", command=self.rom_listbox.yview, style="EmulatorFrame.Scrollbar")
        # scrollbar.pack(side="right", fill="y")
        # self.rom_listbox.config(yscrollcommand=scrollbar.set)

        self.rom_listbox.bind("<Double-1>", self.on_rom_double_click)
        # NEW: Bind mouse wheel events for scrolling
        self.rom_listbox.bind("<MouseWheel>", self.on_mousewheel)
        self.rom_listbox.bind("<Button-4>", lambda e: self.on_mousewheel_scroll(-1)) # For Linux
        self.rom_listbox.bind("<Button-5>", lambda e: self.on_mousewheel_scroll(1))  # For Linux
        self.rom_listbox.bind("<Enter>", lambda e: self.rom_listbox.focus_set()) # Ensure listbox has focus for scrolling

    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling on Windows/Mac."""
        self.rom_listbox.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_scroll(self, direction):
        """Handle mouse wheel scrolling on Linux."""
        self.rom_listbox.yview_scroll(direction, "units")

    def on_visibility_change(self, event=None):
        """Called when this frame becomes visible."""
        if self.winfo_ismapped():
            self.load_all_roms()

    def load_all_roms(self):
        """
        Loads all ROMs from cache or EmulatorsFrame.
        """
        self.rom_listbox.delete(0, tk.END) # Clear existing list

        # Try to get ROMs from cache first
        if self.rom_cache_manager and not self.rom_cache_manager.is_scanning():
            self.all_roms_data = self.rom_cache_manager.get_all_roms()
            print(f"Retrieved {len(self.all_roms_data)} ROMs from cache for AllRomsFrame")
        else:
            # Fallback to EmulatorsFrame method
            if "EmulatorsFrame" in self.controller.frames and \
               hasattr(self.controller.frames["EmulatorsFrame"], "get_all_roms_with_emulator_info"):
                
                self.all_roms_data = self.controller.frames["EmulatorsFrame"].get_all_roms_with_emulator_info()
                print(f"Retrieved {len(self.all_roms_data)} ROMs from EmulatorsFrame for AllRomsFrame")
            else:
                messagebox.showerror("Error", "EmulatorsFrame not initialized or missing 'get_all_roms_with_emulator_info' method.")
                self.rom_listbox.insert(tk.END, "Error: Could not load ROMs. Emulators data not available.")
                return
        
        # Sort ROMs alphabetically by display name
        self.all_roms_data.sort(key=lambda x: x["display_name"].lower())

        if not self.all_roms_data:
            self.rom_listbox.insert(tk.END, "No ROMs found across all configured emulator directories.")
            return

        for rom_info in self.all_roms_data:
            # Display ROM name and its associated emulator
            self.rom_listbox.insert(tk.END, f"{rom_info['display_name']} ({rom_info['emulator_name']})")

    def on_rom_double_click(self, event):
        """Handles double-clicking a ROM in the listbox."""
        selected_index_tuple = self.rom_listbox.curselection()
        if not selected_index_tuple:
            return

        selected_index = selected_index_tuple[0]
        if selected_index < 0 or selected_index >= len(self.all_roms_data):
            # This can happen if the listbox contains the "No ROMs found" message
            return

        rom_info = self.all_roms_data[selected_index]
        self.launch_rom(rom_info)

    def launch_rom(self, rom_info):
        """
        Launches the specified ROM using its associated emulator's run script.
        Updates the ROM's last_played history.
        """
        rom_path = rom_info["rom_path"]
        run_script_path = rom_info["run_script_path"]
        emulator_name = rom_info["emulator_name"]
        display_name = rom_info["display_name"]

        if not os.path.exists(rom_path):
            messagebox.showerror("File Not Found", f"ROM file not found: {rom_path}")
            self.load_all_roms() # Refresh list in case file was deleted
            return
        
        if not os.path.exists(run_script_path):
            messagebox.showerror("Script Not Found", f"Emulator launch script not found for {emulator_name}: {run_script_path}")
            return

        print(f"Attempting to launch {display_name} via {emulator_name} using script: {run_script_path}")

        try:
            subprocess.Popen([run_script_path, rom_path])

            # Update last_played for this specific ROM in its emulator's history file
            self._update_rom_last_played_history(rom_path, rom_info["emulator_name"])

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

    def _update_rom_last_played_history(self, rom_path, emulator_full_name):
        """
        Updates the last_played timestamp for a specific ROM in its emulator's
        rom_data.json file. This requires finding the correct short_name first.
        """
        # First, find the short_name for the emulator from the full_emulator_name
        short_emulator_name = None
        for emulator_data in self.controller.frames["EmulatorsFrame"].emulators_data:
            if emulator_data.get("full_name") == emulator_full_name:
                short_emulator_name = emulator_data.get("short_name")
                break
        
        if not short_emulator_name:
            print(f"WARNING: Could not find short name for emulator '{emulator_full_name}'. Cannot update ROM history.")
            return

        rom_data_file = os.path.join(ROMS_DATA_DIR, f"{short_emulator_name}_roms.json")

        rom_play_history = {}
        if os.path.exists(rom_data_file):
            try:
                with open(rom_data_file, "r") as f:
                    rom_play_history = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Malformed JSON in ROM data file: {rom_data_file}. Starting with empty history.")
                rom_play_history = {} 
        
        rom_play_history[rom_path] = datetime.datetime.now().isoformat()
        
        os.makedirs(ROMS_DATA_DIR, exist_ok=True)
        try:
            with open(rom_data_file, "w") as f:
                json.dump(rom_play_history, f, indent=4)
        except Exception as e:
            print(f"Error saving ROM play history to {rom_data_file}: {e}")


