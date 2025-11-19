import tkinter as tk
from PIL import Image, ImageDraw, ImageFont
try:
    from PIL import ImageTk
except ImportError:
    # Fallback for systems where ImageTk is not available
    import tkinter as tk
    class ImageTk:
        @staticmethod
        def PhotoImage(image):
            return tk.PhotoImage()
from theme import get_theme_manager
import os
import json
import subprocess
import platform
from pathlib import Path

def menu(parent_window, controller):
    theme_manager = get_theme_manager()
    theme = theme_manager.load_theme("menubar")

    # --- Scaling Helpers ---
    screen_width = parent_window.winfo_screenwidth()
    scale = screen_width / 1920  # Base width
    def scale_px(value):
        return int(min(max(value * scale, value * 0.7), value * 1.2))  # Clamp between 70% and 120%

    def scale_image(path, w, h):
        try:
            img = Image.open(path).resize((w, h), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except FileNotFoundError:
            print(f"Error: {path} not found!")
            return None

    # --- Scaled Dimensions ---
    menu_height = scale_px(50)
    home_size = scale_px(35)
    store_size = scale_px(50)
    profile_btn_width = scale_px(180)
    profile_btn_height = scale_px(40)
    profile_img_size = scale_px(32)
    dropdown_width = scale_px(200) # Width for both dropdowns

    # --- Menu Bar Frame ---
    colors = theme.get("colors", {})
    menu_bg = colors.get("menu_background", "#505050")
    menu_frame = tk.Frame(parent_window, bg=menu_bg, height=menu_height)
    menu_frame.pack_propagate(False)
    menu_frame.columnconfigure(2, weight=1)
    menu_frame.columnconfigure(3, weight=0)
    menu_frame.columnconfigure(4, weight=0) # Column for store button
    menu_frame.columnconfigure(5, weight=0) # Column for profile button (new position)
    menu_frame.columnconfigure(6, weight=0) # Column for power button (new position)

    # --- Home Button ---
    icons = theme.get("icons", {})
    home_img = scale_image(icons.get("home", ""), home_size, home_size)
    home_btn = tk.Label(menu_frame, image=home_img, bg=menu_bg, cursor="hand2", bd=0)
    home_btn.image = home_img
    home_btn.grid(row=0, column=1, padx=(5, 10))

    def go_home(event=None):
        controller.show_frame("DashboardFrame")
    home_btn.bind("<Button-1>", go_home)
    hover_bg = colors.get("menu_hover", "#444444")
    home_btn.bind("<Enter>", lambda e: home_btn.config(bg=hover_bg))
    home_btn.bind("<Leave>", lambda e: home_btn.config(bg=menu_bg))

    # --- Store Button ---
    # MODIFIED: Use controller.app_installation_dir to get the path for appstore.png
    store_icon_path = controller.app_installation_dir / "data" / "themes" / "cosmictwilight" / "images" / "appstore.png"
    store_img = scale_image(store_icon_path, store_size, store_size)
    store_btn = None # Initialize store_btn to None
    if store_img:
        store_btn = tk.Label(menu_frame, image=store_img, bg=menu_bg, cursor="hand2", bd=0)
        store_btn.image = store_img
        # Column remains 4
        store_btn.grid(row=0, column=4, padx=15, sticky="e")

        def open_store(event=None):
            controller.show_frame("StoreFrame")
        store_btn.bind("<Button-1>", open_store)
        store_btn.bind("<Enter>", lambda e: store_btn.config(bg=hover_bg))
        store_btn.bind("<Leave>", lambda e: store_btn.config(bg=menu_bg))

    # --- Profile Dropdown Menu ---
    dropdown_bg = colors.get("dropdown_background", "#3a3a3a")
    profile_dropdown = tk.Frame(
        parent_window,
        bg=dropdown_bg,
        bd=1,
        relief="solid",
        highlightthickness=0
    )

    def toggle_profile_dropdown(event=None):
        if profile_dropdown.winfo_ismapped():
            profile_dropdown.place_forget()
        else:
            x = profile_btn.winfo_rootx() - parent_window.winfo_rootx()
            y = menu_frame.winfo_rooty() - parent_window.winfo_rooty() + menu_frame.winfo_height()
            profile_dropdown.place(
                x=x - dropdown_width + profile_btn.winfo_width(),
                y=y,
                width=dropdown_width
            )
            profile_dropdown.lift()
        # Ensure other dropdowns are hidden
        hide_power_dropdown()

    def hide_profile_dropdown(event=None):
        profile_dropdown.place_forget()

    # Profile Dropdown buttons
    def add_profile_dropdown_button(text, command):
        text_color = colors.get("text_primary", "white")
        btn = tk.Button(
            profile_dropdown,
            text=text,
            bg=dropdown_bg,
            fg=text_color,
            activebackground="#9a32cd",
            activeforeground="white",
            relief="flat",
            anchor="w",
            padx=15,
            pady=8,
            font=("Arial", 10),
            highlightthickness=0,
            bd=0,
            command=lambda: [hide_profile_dropdown(), command()]
        )
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda e: btn.config(bg="#9a32cd"))
        btn.bind("<Leave>", lambda e: btn.config(bg=dropdown_bg))
        return btn

    # --- Power Dropdown Menu ---
    power_dropdown = tk.Frame(
        parent_window,
        bg=dropdown_bg,
        bd=1,
        relief="solid",
        highlightthickness=0
    )

    def toggle_power_dropdown(event=None):
        if power_dropdown.winfo_ismapped():
            power_dropdown.place_forget()
        else:
            # Position relative to the power_btn
            x = power_btn.winfo_rootx() - parent_window.winfo_rootx()
            y = menu_frame.winfo_rooty() - parent_window.winfo_rooty() + menu_frame.winfo_height()
            power_dropdown.place(
                x=x - dropdown_width + power_btn.winfo_width(),
                y=y,
                width=dropdown_width
            )
            power_dropdown.lift()
        # Ensure other dropdowns are hidden
        hide_profile_dropdown()

    def hide_power_dropdown(event=None):
        power_dropdown.place_forget()

    # Power Dropdown buttons
    def add_power_dropdown_button(text, command):
        btn = tk.Button(
            power_dropdown,
            text=text,
            bg=dropdown_bg,
            fg="white",
            activebackground="#9a32cd",
            activeforeground="white",
            relief="flat",
            anchor="w",
            padx=15,
            pady=8,
            font=("Arial", 10),
            highlightthickness=0,
            bd=0,
            command=lambda: [hide_power_dropdown(), command()]
        )
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda e: btn.config(bg="#9a32cd"))
        btn.bind("<Leave>", lambda e: btn.config(bg=dropdown_bg))
        return btn


    # --- Profile Button ---
    def create_profile_button():
        profile_btn_frame = tk.Frame(
            menu_frame,
            bg=menu_bg,
            width=profile_btn_width,
            height=profile_btn_height,
            cursor="hand2"
        )
        # Changed column to 5 for profile button
        profile_btn_frame.grid(row=0, column=5, padx=(15, 5), sticky="e") # Adjusted padx
        profile_btn_frame.pack_propagate(False)
        profile_btn_frame.bind("<Button-1>", toggle_profile_dropdown) # Bind to profile dropdown

        profile_img_label = tk.Label(
            profile_btn_frame,
            bg=menu_bg,
            bd=0
        )
        profile_img_label.pack(side="left", padx=(5, 8))
        profile_img_label.bind("<Button-1>", toggle_profile_dropdown)

        username_label = tk.Label(
            profile_btn_frame,
            text="", # Initialize with empty text
            fg="white",
            bg=menu_bg,
            font=("Arial", 10, "bold"),
            anchor="w"
        )
        username_label.pack(side="left", fill="x", expand=True)
        username_label.bind("<Button-1>", toggle_profile_dropdown)

        # This function will be called to load/update the profile image and username
        def load_profile_image_and_name():
            # Force Tkinter to process pending events to ensure controller.current_user is updated
            parent_window.update_idletasks()

            username = getattr(controller, 'current_user', "Guest")
            
            # Extract the clean username for display if it includes "(admin)"
            display_username = username.replace(" (admin)", "")
            capitalized_display_username = display_username.capitalize()
            
            # If the user is an admin, append (Admin) to the displayed name
            # This relies on the current_user being set to 'username (admin)' for admin users
            if " (admin)" in username:
                capitalized_display_username = f"{capitalized_display_username} (Admin)"

            username_label.config(text=capitalized_display_username)

            # Define font for PIL ImageDraw
            try:
                # MODIFIED: Use controller.app_installation_dir for fonts
                font_path = controller.app_installation_dir / "data" / "themes" / "cosmictwilight" / "fonts" / "Impact.ttf"
                if not font_path.exists(): # MODIFIED: Use Path.exists()
                    # Fallback to a system font if Impact.ttf is not found
                    if platform.system() == "Linux":
                        # Prioritize a common bold font on Linux
                        if Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf").exists():
                            font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
                        elif Path("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf").exists():
                            font_path = Path("/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf")
                        else:
                            font_path = None # No suitable TrueType font found
                    elif platform.system() == "Windows":
                        font_path = Path("C:/Windows/Fonts/arialbd.ttf") # Common Windows font
                    else:
                        font_path = None # No specific fallback for other OS

                if font_path and font_path.exists(): # MODIFIED: Use Path.exists()
                    font_for_pil = ImageFont.truetype(str(font_path), profile_img_size // 2) # MODIFIED: Convert Path to str
                else:
                    # Fallback to default PIL font if no TrueType font can be loaded
                    font_for_pil = ImageFont.load_default()
                    print("Warning: Could not load TrueType font for profile avatar, using default.")
            except Exception as e:
                print(f"Error loading font for PIL: {e}. Using default PIL font.")
                font_for_pil = ImageFont.load_default()


            if hasattr(controller, 'current_user') and controller.current_user:
                # MODIFIED: Use controller.path_manager to get the accounts directory
                accounts_path = controller.path_manager.get_path("accounts")
                account_dir = accounts_path / controller.current_user # Use Path object concatenation
                json_path = account_dir / "account.json" # Use Path object concatenation

                if json_path.exists(): # MODIFIED: Use Path.exists()
                    try:
                        with open(json_path, "r") as f:
                            account_data = json.load(f)
                        profile_image_filename = account_data.get('profile_image')

                        if profile_image_filename:
                            img_path = account_dir / profile_image_filename # Use Path object concatenation
                            if img_path.exists(): # MODIFIED: Use Path.exists()
                                img = Image.open(img_path)
                                img = img.resize((profile_img_size, profile_img_size), Image.LANCZOS)

                                mask = Image.new('L', (profile_img_size, profile_img_size), 0)
                                draw = ImageDraw.Draw(mask)
                                draw.ellipse((0, 0, profile_img_size, profile_img_size), fill=255)

                                img.putalpha(mask)
                                photo = ImageTk.PhotoImage(img)
                                profile_img_label.config(image=photo)
                                profile_img_label.image = photo
                                return # Image loaded, exit function
                    except Exception as e:
                        print(f"Error loading profile image: {e}")

            # Fallback to default avatar if no image or error
            img = Image.new('RGBA', (profile_img_size, profile_img_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((0, 0, profile_img_size, profile_img_size), fill="#9a32cd")

            # Use the clean username for the initial if available, otherwise "G" for Guest
            initial_for_avatar = display_username[0].upper() if display_username else "G"

            draw.text(
                (profile_img_size//2, profile_img_size//2),
                initial_for_avatar,
                fill="white",
                font=font_for_pil, # Use the loaded PIL font object
                anchor="mm"
            )

            photo = ImageTk.PhotoImage(img)
            profile_img_label.config(image=photo)
            profile_img_label.image = photo

        # Initial call to set the profile image and name
        load_profile_image_and_name()

        def on_enter(e):
            profile_btn_frame.config(bg=hover_bg)
            profile_img_label.config(bg=hover_bg)
            username_label.config(bg=hover_bg)

        def on_leave(e):
            profile_btn_frame.config(bg=menu_bg)
            profile_img_label.config(bg=menu_bg)
            username_label.config(bg=menu_bg)

        profile_btn_frame.bind("<Enter>", on_enter)
        profile_btn_frame.bind("<Leave>", on_leave)
        profile_img_label.bind("<Enter>", on_enter)
        profile_img_label.bind("<Leave>", on_leave)
        username_label.bind("<Enter>", on_enter)
        username_label.bind("<Leave>", on_leave)

        # Store the update function on the frame for external calls
        profile_btn_frame.update_profile_display = load_profile_image_and_name
        return profile_btn_frame

    profile_btn = create_profile_button()

    # --- New Power Button ---
    def create_power_button():
        power_btn_frame = tk.Frame(
            menu_frame,
            bg=menu_bg,
            width=scale_px(40), # Fixed width for power button
            height=profile_btn_height,
            cursor="hand2"
        )
        # Changed column to 6 for power button
        power_btn_frame.grid(row=0, column=6, padx=(5, 15), sticky="e") # Adjusted padx
        power_btn_frame.pack_propagate(False)
        power_btn_frame.bind("<Button-1>", toggle_power_dropdown)

        power_label = tk.Label(
            power_btn_frame,
            text="\u23FB", # Unicode power symbol
            font=("Arial", 18, "bold"),
            fg="white",
            bg=menu_bg,
            bd=0
        )
        power_label.pack(expand=True)
        power_label.bind("<Button-1>", toggle_power_dropdown)

        def on_enter(e):
            power_btn_frame.config(bg=hover_bg)
            power_label.config(bg=hover_bg)

        def on_leave(e):
            power_btn_frame.config(bg=menu_bg)
            power_label.config(bg=menu_bg)

        power_btn_frame.bind("<Enter>", on_enter)
        power_btn_frame.bind("<Leave>", on_leave)
        power_label.bind("<Enter>", on_enter)
        power_label.bind("<Leave>", on_leave)

        return power_btn_frame

    power_btn = create_power_button()


    # --- System Command Functions ---
    def reboot_os():
        """Reboots the operating system using pkexec for graphical password prompt."""
        try:
            subprocess.run(["pkexec", "/sbin/reboot"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error rebooting OS: {e}")
            show_message_dialog("Error", "Failed to reboot OS. Authorization denied or pkexec issue.", "red")
        except FileNotFoundError:
            print("Error: 'pkexec' command not found. Is it installed and in your PATH?")
            show_message_dialog("Error", "'pkexec' command not found. Please install PolicyKit.", "red")

    def shutdown_os():
        """Shuts down the operating system using pkexec for graphical password prompt."""
        try:
            subprocess.run(["pkexec", "/sbin/shutdown", "-h", "now"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error shutting down OS: {e}")
            show_message_dialog("Error", "Failed to shut down OS. Authorization denied or pkexec issue.", "red")
        except FileNotFoundError:
            print("Error: 'pkexec' command not found. Is it installed and in your PATH?")
            show_message_dialog("Error", "'pkexec' command not found. Please install PolicyKit.", "red")

    # --- Custom Message/Confirmation Dialog ---
    def show_message_dialog(title, message, color="white", on_yes=None):
        """
        Displays a custom message or confirmation dialog.
        If on_yes is provided, it acts as a confirmation dialog.
        """
        dialog = tk.Toplevel(parent_window)
        dialog.title(title)
        dialog.transient(parent_window)
        dialog.grab_set() # Make it modal
        dialog.resizable(False, False)

        # Center the dialog
        parent_x = parent_window.winfo_x()
        parent_y = parent_window.winfo_y()
        parent_width = parent_window.winfo_width()
        parent_height = parent_window.winfo_height()

        dialog_width = 300
        dialog_height = 150
        x = parent_x + (parent_width // 2) - (dialog_width // 2)
        y = parent_y + (parent_height // 2) - (dialog_height // 2)
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        dialog.config(bg=dropdown_bg) # Use dropdown background for dialog

        message_label = tk.Label(
            dialog,
            text=message,
            fg=color,
            bg=dropdown_bg,
            font=("Arial", 10),
            wraplength=dialog_width - 20 # Wrap text
        )
        message_label.pack(pady=20, padx=10)

        button_frame = tk.Frame(dialog, bg=dropdown_bg)
        button_frame.pack(pady=10)

        if on_yes: # Confirmation dialog
            yes_button = tk.Button(
                button_frame,
                text="Yes",
                command=lambda: [dialog.destroy(), on_yes()],
                bg="#9a32cd",
                fg="white",
                relief="flat",
                font=("Arial", 10, "bold")
            )
            yes_button.pack(side="left", padx=10)

            no_button = tk.Button(
                button_frame,
                text="No",
                command=dialog.destroy,
                bg="#555555",
                fg="white",
                relief="flat",
                font=("Arial", 10, "bold")
            )
            no_button.pack(side="right", padx=10)
        else: # Simple message dialog
            ok_button = tk.Button(
                button_frame,
                text="OK",
                command=dialog.destroy,
                bg="#9a32cd",
                fg="white",
                relief="flat",
                font=("Arial", 10, "bold")
            )
            ok_button.pack(padx=10)

        dialog.wait_window(dialog) # Wait until dialog is closed

    # Build dropdown structure for Profile Dropdown
    for widget in profile_dropdown.winfo_children(): # Clear existing buttons before rebuilding
        widget.destroy()
    add_profile_dropdown_button("Account Settings", lambda: controller.show_frame("AccountSettingsFrame"))
    add_profile_dropdown_button("User Preferences", lambda: controller.show_frame("UserPreferencesFrame"))
    add_profile_dropdown_button("Admin Panel", lambda: controller.show_frame("AdminPanelFrame"))

    # Function to handle signing out
    def sign_out_user():
        controller.set_current_user("Guest") # Set current user to Guest
        controller.show_frame("LoginFrame") # Navigate to LoginFrame
        # No need to explicitly refresh SwitchuserFrame here, as LoginFrame's _load_existing_profiles()
        # and the subsequent navigation will handle it.

    # Build dropdown structure for Power Dropdown
    for widget in power_dropdown.winfo_children(): # Clear existing buttons before rebuilding
        widget.destroy()
    add_power_dropdown_button("Reboot OS", lambda: show_message_dialog(
        "Confirm Reboot", "Are you sure you want to reboot the OS? (Requires sudo)", "yellow", reboot_os
    ))
    add_power_dropdown_button("Shutdown OS", lambda: show_message_dialog(
        "Confirm Shutdown", "Are you sure you want to shut down the OS? (Requires sudo)", "red", shutdown_os
    ))
    add_power_dropdown_button("Sign Out", sign_out_user) # Renamed and moved
    add_power_dropdown_button("Exit App", parent_window.quit)


    def on_global_click(event):
        widget = event.widget
        if profile_dropdown.winfo_ismapped() or power_dropdown.winfo_ismapped():
            is_child_of_profile = False
            is_child_of_power = False
            current = widget
            while current:
                if current == profile_dropdown or current == profile_btn:
                    is_child_of_profile = True
                if current == power_dropdown or current == power_btn:
                    is_child_of_power = True
                if is_child_of_profile and is_child_of_power: # Both are true, means it's a click within either dropdown/button
                    break
                current = current.master

            if not is_child_of_profile:
                hide_profile_dropdown()
            if not is_child_of_power:
                hide_power_dropdown()

    parent_window.bind("<Button-1>", on_global_click, add="+")

    def update_home_button_visibility():
        if getattr(controller, "current_frame_name", "") == "DashboardFrame":
            home_btn.grid_remove()
        else:
            if not home_btn.winfo_ismapped():
                home_btn.grid(row=0, column=1, padx=(5, 10))

    controller.update_home_button_visibility = update_home_button_visibility

    def refresh_menu_elements(): # Renamed from refresh_profile_button
        nonlocal profile_btn, power_btn, store_btn # Include power_btn and store_btn in nonlocal

        # Recreate profile button
        profile_btn.destroy()
        profile_btn = create_profile_button()
        profile_btn.update_profile_display() # Call the new update function

        # Recreate power button
        power_btn.destroy()
        power_btn = create_power_button()

        # Recreate store button if it exists
        if store_btn:
            store_btn.destroy()
            # MODIFIED: Use controller.app_installation_dir for store icon path
            store_icon_path = controller.app_installation_dir / "data" / "themes" / "cosmictwilight" / "images" / "appstore.png"
            store_img = scale_image(store_icon_path, store_size, store_size)
            if store_img:
                store_btn = tk.Label(menu_frame, image=store_img, bg=menu_bg, cursor="hand2", bd=0)
                store_btn.image = store_img
                store_btn.grid(row=0, column=4, padx=15, sticky="e") # Re-grid in correct column
                store_btn.bind("<Button-1>", open_store)
                store_btn.bind("<Enter>", lambda e: store_btn.config(bg=hover_bg))
                store_btn.bind("<Leave>", lambda e: store_btn.config(bg=menu_bg))


        # Rebuild profile dropdown (ensure "Switch User" is removed)
        for widget in profile_dropdown.winfo_children():
            widget.destroy()
        add_profile_dropdown_button("Account Settings", lambda: controller.show_frame("AccountSettingsFrame"))
        add_profile_dropdown_button("User Preferences", lambda: controller.show_frame("UserPreferencesFrame"))
        add_profile_dropdown_button("Admin Panel", lambda: controller.show_frame("AdminPanelFrame"))

        # Rebuild power dropdown (ensure "Sign Out" is added)
        for widget in power_dropdown.winfo_children():
            widget.destroy()
        add_power_dropdown_button("Reboot OS", lambda: show_message_dialog(
            "Confirm Reboot", "Are you sure you want to reboot the OS? (Requires sudo)", "yellow", reboot_os
        ))
        add_power_dropdown_button("Shutdown OS", lambda: show_message_dialog(
            "Confirm Shutdown", "Are you sure you want to shut down the OS? (Requires sudo)", "red", shutdown_os
        ))
        add_power_dropdown_button("Sign Out", sign_out_user) # Renamed and moved
        add_power_dropdown_button("Exit App", parent_window.quit)

    controller.refresh_menu_elements = refresh_menu_elements # Update controller reference

    return menu_frame

