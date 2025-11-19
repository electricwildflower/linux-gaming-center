"""
Controller Configuration Frame for Linux Gaming Center
Provides UI for configuring game controllers and button mappings.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import time
from pathlib import Path
from PIL import Image, ImageDraw
try:
    from PIL import ImageTk
except ImportError:
    # Fallback for systems where ImageTk is not available
    import tkinter as tk
    class ImageTk:
        @staticmethod
        def PhotoImage(image):
            return tk.PhotoImage()

from controller_manager import get_controller_manager, ControllerButton, NavigationAction
from theme import get_theme_manager

class ControllersConfigFrame(tk.Frame):
    """Frame for configuring game controllers"""
    
    def __init__(self, parent, controller, path_manager=None):
        super().__init__(parent)
        self.controller = controller
        self.path_manager = path_manager
        self.controller_manager = get_controller_manager(path_manager)
        
        # Theme setup
        self.theme_manager = get_theme_manager()
        self.theme = self.theme_manager.load_theme("controller_settings")
        colors = self.theme.get("colors", {})
        
        # Configure frame with cosmic twilight colors
        self.bg_color = "#1E1E1E"  # Black
        self.secondary_bg = "#2D2D2D"  # Dark grey
        self.accent_color = "#9a32cd"  # Purple
        self.text_color = "#ffffff"  # White
        self.text_secondary = "#d4d4d4"  # Light grey
        
        self.configure(bg=self.bg_color)
        
        # Controller data
        self.available_controllers = []
        self.selected_controller = None
        self.testing_input = False
        self.input_test_results = []
        
        self.create_widgets()
        self.refresh_controllers()
    
    def create_widgets(self):
        """Create the UI widgets"""
        # Main container with scrollbar
        main_container = tk.Frame(self, bg=self.bg_color)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title and controller image section
        title_frame = tk.Frame(main_container, bg=self.bg_color)
        title_frame.pack(fill="x", pady=(0, 20))
        
        # Title
        title_label = tk.Label(
            title_frame,
            text="CONTROLLER SETTINGS",
            font=("Impact", 24),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack(side="left")
        
        # Controller image
        try:
            if self.path_manager:
                controller_image_path = self.path_manager.get_path("themes") / "cosmictwilight" / "images" / "controller.png"
                if controller_image_path.exists():
                    # Load and resize controller image
                    controller_img = Image.open(controller_image_path)
                    controller_img = controller_img.resize((64, 64), Image.Resampling.LANCZOS)
                    self.controller_photo = ImageTk.PhotoImage(controller_img)
                    
                    controller_label = tk.Label(
                        title_frame,
                        image=self.controller_photo,
                        bg=self.bg_color
                    )
                    controller_label.pack(side="right", padx=(20, 0))
        except Exception as e:
            # Could not load controller image
            pass
        
        # Controller Detection Section
        self.create_detection_section(main_container)
        
        # Controller List Section
        self.create_controller_list_section(main_container)
        
        # Controller Configuration Section
        self.create_configuration_section(main_container)
        
        # Test Section
        self.create_test_section(main_container)
    
    def create_detection_section(self, parent):
        """Create controller detection section"""
        detection_frame = tk.LabelFrame(
            parent,
            text="Controller Detection",
            fg=self.text_color,
            bg=self.bg_color,
            font=("Arial", 12, "bold")
        )
        detection_frame.pack(fill="x", pady=(0, 20))
        
        # Detection info
        info_label = tk.Label(
            detection_frame,
            text="Scan for connected game controllers and configure their button mappings.",
            fg=self.text_secondary,
            bg=self.bg_color,
            wraplength=600
        )
        info_label.pack(pady=10, padx=10)
        
        # Scan button
        scan_button = tk.Button(
            detection_frame,
            text="Scan for Controllers",
            command=self.refresh_controllers,
            bg=self.accent_color,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        scan_button.pack(pady=10)
    
    def create_controller_list_section(self, parent):
        """Create controller list section"""
        list_frame = tk.LabelFrame(
            parent,
            text="Available Controllers",
            fg=self.text_color,
            bg=self.bg_color,
            font=("Arial", 12, "bold")
        )
        list_frame.pack(fill="x", pady=(0, 20))
        
        # Controller listbox with scrollbar
        list_container = tk.Frame(list_frame, bg=self.bg_color)
        list_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Listbox
        self.controller_listbox = tk.Listbox(
            list_container,
            bg=self.secondary_bg,
            fg=self.text_color,
            selectbackground=self.accent_color,
            font=("Arial", 10),
            height=6
        )
        self.controller_listbox.pack(side="left", fill="both", expand=True)
        self.controller_listbox.bind("<<ListboxSelect>>", self.on_controller_select)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_container, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        self.controller_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.controller_listbox.yview)
        
        # Controller actions
        actions_frame = tk.Frame(list_frame, bg=self.bg_color)
        actions_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        add_button = tk.Button(
            actions_frame,
            text="Add Controller",
            command=self.add_selected_controller,
            bg=self.accent_color,
            fg="white",
            font=("Arial", 9),
            padx=15,
            pady=3
        )
        add_button.pack(side="left", padx=(0, 10))
        
        remove_button = tk.Button(
            actions_frame,
            text="Remove Controller",
            command=self.remove_selected_controller,
            bg="#7d26cd",
            fg="white",
            font=("Arial", 9),
            padx=15,
            pady=3
        )
        remove_button.pack(side="left")
    
    def create_configuration_section(self, parent):
        """Create controller configuration section"""
        config_frame = tk.LabelFrame(
            parent,
            text="Controller Configuration",
            fg=self.text_color,
            bg=self.bg_color,
            font=("Arial", 12, "bold")
        )
        config_frame.pack(fill="x", pady=(0, 20))
        
        # Configuration content
        self.config_content = tk.Frame(config_frame, bg=self.bg_color)
        self.config_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Initially hide configuration
        self.config_content.pack_forget()
    
    def create_test_section(self, parent):
        """Create controller test section"""
        test_frame = tk.LabelFrame(
            parent,
            text="Controller Test",
            fg=self.text_color,
            bg=self.bg_color,
            font=("Arial", 12, "bold")
        )
        test_frame.pack(fill="x", pady=(0, 20))
        
        # Test info
        test_info = tk.Label(
            test_frame,
            text="Test your controller inputs to verify button mappings work correctly.",
            fg=self.text_secondary,
            bg=self.bg_color,
            wraplength=600
        )
        test_info.pack(pady=10, padx=10)
        
        # Test button
        self.test_button = tk.Button(
            test_frame,
            text="Start Input Test",
            command=self.start_input_test,
            bg=self.accent_color,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        self.test_button.pack(pady=10)
        
        # Test results
        self.test_results = tk.Text(
            test_frame,
            height=8,
            bg=self.secondary_bg,
            fg=self.text_color,
            font=("Courier", 9),
            wrap="word"
        )
        self.test_results.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def refresh_controllers(self):
        """Refresh the list of available controllers"""
        try:
            self.available_controllers = self.controller_manager.scan_for_controllers()
            self.update_controller_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan for controllers: {e}")
    
    def update_controller_list(self):
        """Update the controller listbox"""
        self.controller_listbox.delete(0, tk.END)
        
        for controller in self.available_controllers:
            # Check if controller is already configured
            is_configured = controller['id'] in self.controller_manager.controller_configs
            status = "✓ Configured" if is_configured else "○ Available"
            
            display_text = f"{controller['name']} ({status})"
            self.controller_listbox.insert(tk.END, display_text)
    
    def on_controller_select(self, event):
        """Handle controller selection"""
        selection = self.controller_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.available_controllers):
                self.selected_controller = self.available_controllers[index]
                self.show_controller_config()
    
    def add_selected_controller(self):
        """Add the selected controller to configuration"""
        if not self.selected_controller:
            messagebox.showwarning("Warning", "Please select a controller first.")
            return
        
        controller_id = self.selected_controller['id']
        controller_name = self.selected_controller['name']
        
        # Check if already configured
        if controller_id in self.controller_manager.controller_configs:
            messagebox.showinfo("Info", "This controller is already configured.")
            return
        
        # Add controller
        config = self.controller_manager.add_controller(controller_id, controller_name)
        self.update_controller_list()
        self.show_controller_config()
        
        messagebox.showinfo("Success", f"Controller '{controller_name}' added successfully!")
    
    def remove_selected_controller(self):
        """Remove the selected controller from configuration"""
        if not self.selected_controller:
            messagebox.showwarning("Warning", "Please select a controller first.")
            return
        
        controller_id = self.selected_controller['id']
        controller_name = self.selected_controller['name']
        
        if controller_id not in self.controller_manager.controller_configs:
            messagebox.showwarning("Warning", "This controller is not configured.")
            return
        
        # Confirm removal
        if messagebox.askyesno("Confirm", f"Remove controller '{controller_name}'?"):
            self.controller_manager.remove_controller(controller_id)
            self.update_controller_list()
            self.hide_controller_config()
            messagebox.showinfo("Success", "Controller removed successfully!")
    
    def show_controller_config(self):
        """Show controller configuration options"""
        if not self.selected_controller:
            return
        
        controller_id = self.selected_controller['id']
        
        # Clear existing config content
        for widget in self.config_content.winfo_children():
            widget.destroy()
        
        # Show configuration frame
        self.config_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Get or create controller config
        if controller_id in self.controller_manager.controller_configs:
            config = self.controller_manager.controller_configs[controller_id]
        else:
            return
        
        # Controller info
        info_frame = tk.Frame(self.config_content, bg=self.bg_color)
        info_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(
            info_frame,
            text=f"Configuring: {config.controller_name}",
            font=("Arial", 14, "bold"),
            fg=self.text_color,
            bg=self.bg_color
        ).pack(anchor="w")
        
        # Enable/Disable toggle
        enable_frame = tk.Frame(self.config_content, bg=self.bg_color)
        enable_frame.pack(fill="x", pady=(0, 20))
        
        self.enable_var = tk.BooleanVar(value=config.enabled)
        enable_check = tk.Checkbutton(
            enable_frame,
            text="Enable Controller",
            variable=self.enable_var,
            command=self.update_controller_enabled,
            fg=self.text_color,
            bg=self.bg_color,
            selectcolor=self.secondary_bg,
            font=("Arial", 10)
        )
        enable_check.pack(anchor="w")
        
        # Button mappings
        mappings_frame = tk.LabelFrame(
            self.config_content,
            text="Button Mappings",
            fg=self.text_color,
            bg=self.bg_color,
            font=("Arial", 10, "bold")
        )
        mappings_frame.pack(fill="x", pady=(0, 20))
        
        # Create mapping widgets
        self.mapping_vars = {}
        for button, action in config.button_mappings.items():
            mapping_row = tk.Frame(mappings_frame, bg=self.bg_color)
            mapping_row.pack(fill="x", padx=10, pady=5)
            
            tk.Label(
                mapping_row,
                text=f"{button}:",
                fg=self.text_color,
                bg=self.bg_color,
                width=15,
                anchor="w"
            ).pack(side="left")
            
            var = tk.StringVar(value=action)
            self.mapping_vars[button] = var
            
            action_combo = ttk.Combobox(
                mapping_row,
                textvariable=var,
                values=[action.value for action in NavigationAction],
                state="readonly",
                width=20
            )
            action_combo.pack(side="left", padx=(10, 0))
            action_combo.bind("<<ComboboxSelected>>", lambda e, btn=button: self.update_button_mapping(btn))
        
        # Save button
        save_button = tk.Button(
            self.config_content,
            text="Save Configuration",
            command=self.save_controller_config,
            bg=self.accent_color,
            fg="white",
            font=("Arial", 10, "bold"),
            padx=20,
            pady=5
        )
        save_button.pack(pady=10)
    
    def hide_controller_config(self):
        """Hide controller configuration"""
        self.config_content.pack_forget()
        self.selected_controller = None
    
    def update_controller_enabled(self):
        """Update controller enabled status"""
        if not self.selected_controller:
            return
        
        controller_id = self.selected_controller['id']
        enabled = self.enable_var.get()
        
        self.controller_manager.update_controller_config(
            controller_id,
            enabled=enabled
        )
    
    def update_button_mapping(self, button):
        """Update button mapping"""
        if not self.selected_controller:
            return
        
        controller_id = self.selected_controller['id']
        action = self.mapping_vars[button].get()
        
        # Update the mapping
        config = self.controller_manager.controller_configs[controller_id]
        config.button_mappings[button] = action
        
        self.controller_manager.save_controller_configs()
    
    def save_controller_config(self):
        """Save all controller configuration changes"""
        if not self.selected_controller:
            return
        
        controller_id = self.selected_controller['id']
        
        # Update all mappings
        config = self.controller_manager.controller_configs[controller_id]
        for button, var in self.mapping_vars.items():
            config.button_mappings[button] = var.get()
        
        # Save configuration
        self.controller_manager.save_controller_configs()
        messagebox.showinfo("Success", "Controller configuration saved!")
    
    def start_input_test(self):
        """Start controller input test"""
        if not self.selected_controller:
            messagebox.showwarning("Warning", "Please select a controller first.")
            return
        
        if self.testing_input:
            self.stop_input_test()
            return
        
        controller_id = self.selected_controller['id']
        
        # Clear previous results
        self.test_results.delete(1.0, tk.END)
        self.test_results.insert(tk.END, "Testing controller inputs... Press buttons, move sticks, or use D-pad.\n")
        self.test_results.insert(tk.END, "Test will run for 10 seconds.\n\n")
        
        # Start test in separate thread
        self.testing_input = True
        self.test_button.config(text="Stop Test", bg="#7d26cd")
        
        def run_test():
            try:
                inputs = self.controller_manager.test_controller_input(controller_id, 10.0)
                
                # Update UI in main thread
                self.after(0, self.display_test_results, inputs)
            except Exception as e:
                self.after(0, self.display_test_error, str(e))
        
        test_thread = threading.Thread(target=run_test, daemon=True)
        test_thread.start()
    
    def stop_input_test(self):
        """Stop controller input test"""
        self.testing_input = False
        self.test_button.config(text="Start Input Test", bg=self.accent_color)
    
    def display_test_results(self, inputs):
        """Display test results"""
        self.testing_input = False
        self.test_button.config(text="Start Input Test", bg=self.accent_color)
        
        if not inputs:
            self.test_results.insert(tk.END, "No inputs detected. Make sure your controller is connected and try again.\n")
            return
        
        self.test_results.insert(tk.END, f"Detected {len(inputs)} inputs:\n\n")
        
        for input_data in inputs:
            timestamp = f"{input_data['timestamp']:.2f}s"
            if input_data['type'] == 'button':
                self.test_results.insert(tk.END, f"[{timestamp}] Button {input_data['name']} pressed\n")
            elif input_data['type'] == 'hat':
                self.test_results.insert(tk.END, f"[{timestamp}] D-pad {input_data['direction']}\n")
            elif input_data['type'] == 'axis':
                self.test_results.insert(tk.END, f"[{timestamp}] Axis {input_data['axis']}: {input_data['value']:.2f}\n")
    
    def display_test_error(self, error):
        """Display test error"""
        self.testing_input = False
        self.test_button.config(text="Start Input Test", bg=self.accent_color)
        self.test_results.insert(tk.END, f"Error during test: {error}\n")
    
    def on_show_frame(self):
        """Called when this frame is shown"""
        # Set current user for controller manager
        if hasattr(self.controller, 'current_user') and self.controller.current_user:
            self.controller_manager.set_current_user(self.controller.current_user)
        
        # Refresh controllers
        self.refresh_controllers()
    
    def on_hide_frame(self):
        """Called when this frame is hidden"""
        if self.testing_input:
            self.stop_input_test()
