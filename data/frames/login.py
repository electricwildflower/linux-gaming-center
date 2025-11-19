import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import hashlib
import shutil
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
import platform
from pathlib import Path # Import Path for modern path handling

from paths import PathManager # Import PathManager

# Determine if running on Linux for font adjustments
IS_LINUX = platform.system() == "Linux"

class StyledMessageBox:
    """
    A custom styled message box to replace tkinter's default messagebox,
    offering a gaming-inspired look and feel with custom colors and border.
    """
    @staticmethod
    def show_info(title, message, parent=None):
        """
        Displays an informational message box.

        Args:
            title (str): The title of the message box.
            message (str): The message to display.
            parent (tk.Widget, optional): The parent widget. Defaults to None.
        """
        root = tk.Toplevel(parent if parent else None)
        root.title(title)
        root.configure(bg="#0a0a12")  # Darker background

        # Remove window decorations (title bar) for a custom look
        root.overrideredirect(True)

        # Calculate position relative to parent window or screen center
        if parent:
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()

            # Center within parent window
            x = parent_x + (parent_width // 2) - 200  # 200 is half of default width
            y = parent_y + (parent_height // 2) - 100  # 100 is half of default height

            # Ensure it stays on screen
            x = max(0, min(x, parent.winfo_screenwidth() - 400))
            y = max(0, min(y, parent.winfo_screenheight() - 200))

            root.geometry(f"400x200+{x}+{y}")
        else:
            # Fallback to screen center if no parent
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            x = (screen_width // 2) - 200
            y = (screen_height // 2) - 100
            root.geometry(f"400x200+{x}+{y}")

        # Main frame with gaming-style border
        main_frame = tk.Frame(
            root,
            bg="#1a1a2e",  # Dark grey-blue for content area
            bd=0,
            highlightthickness=2,  # Border thickness
            highlightbackground="#9a32cd",  # Purple accent border
            highlightcolor="#9a32cd"
        )
        main_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # Title label with gaming font style
        title_label = tk.Label(
            main_frame,
            text=title,
            font=("Impact" if IS_LINUX else "Arial", 14, "bold"), # Use Impact if on Linux
            fg="#9a32cd",  # Purple accent color
            bg="#1a1a2e"
        )
        title_label.pack(pady=(15, 5))

        # Message label
        message_label = tk.Label(
            main_frame,
            text=message,
            font=("Arial", 11),
            fg="white",
            bg="#1a1a2e",
            wraplength=350
        )
        message_label.pack(pady=(0, 20))

        # Gaming-style OK button
        ok_button = tk.Button(
            main_frame,
            text="OK",
            command=root.destroy,
            bg="#9a32cd",  # Purple button background
            fg="white",
            activebackground="#7d26cd",  # Darker purple on click
            activeforeground="white",
            font=("Arial", 10, "bold"),
            bd=0,
            padx=20,
            pady=5,
            relief="flat",
            cursor="hand2"
        )
        ok_button.pack(pady=(0, 15))

        # Make the message box modal
        root.transient(parent if parent else None)
        try:
            root.grab_set()
        except tk.TclError:
            # If grab_set fails, continue without modal behavior
            pass
        root.wait_window(root)


class LoginFrame(tk.Frame):
    """
    The main login frame for the Linux Gaming Center application.
    It handles user profile selection, login, and account creation.
    """
    def __init__(self, parent, controller, path_manager: PathManager): # MODIFIED: Added path_manager argument
        """
        Initializes the LoginFrame.

        Args:
            parent (tk.Widget): The parent widget (root window).
            controller (object): The main application controller to manage frames.
            path_manager (PathManager): The PathManager instance for directory resolution.
        """
        super().__init__(parent)
        self.controller = controller
        self.path_manager = path_manager # STORED: path_manager instance

        # Define color scheme based on user's request
        self.styles = {
            "background_color": "#0a0a12",  # Darker background (almost black)
            "button_color": "#333344",      # Dark grey-blue for general buttons
            "button_text_color": "white",
            "accent_color": "#9a32cd",      # Vibrant purple for accents
            "secondary_color": "#1a1a2e",   # Dark grey for frames and input fields
            "text_color": "white"
        }

        # No longer needed for Steam-style login
        # self.profile_buttons = {}  # Stores references to profile buttons/labels
        # self.current_login_username = None
        # self.password_widgets = None  # To store password entry and login button

        self._configure_styles()
        self._create_widgets()
        # No longer loading profiles for Steam-style login
        # self._load_existing_profiles() # Load profiles on initialization (renamed from load_accounts)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Login.TFrame", background="#1e1e1e")
        style.configure("LoginTitle.TLabel", background="#1e1e1e", foreground="#BF5FFF", font=("Arial", 24, "bold"))
        style.configure("LoginSubtitle.TLabel", background="#1e1e1e", foreground="white", font=("Arial", 14))
        style.configure("Login.TButton",
                        background="#61afef",
                        foreground="white",
                        font=("Arial", 12, "bold"),
                        padding=10,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor="#61afef")
        style.map("Login.TButton",
                  background=[('active', '#5698d3'), ('pressed', '#467cb4')],
                  foreground=[('active', 'white'), ('pressed', 'white')])
        style.configure("Login.TLabel", background="#1e1e1e", foreground="white", font=("Arial", 12))
        style.configure("Login.TEntry", fieldbackground="#3e4451", foreground="white", insertbackground="white")

    def _create_widgets(self):
        """
        Creates all the widgets for the login screen with Steam-inspired design.
        """
        bg_color = self.styles["background_color"]
        button_color = self.styles["button_color"]
        accent_color = self.styles["accent_color"]
        secondary_color = self.styles["secondary_color"]
        text_color = self.styles["text_color"]

        self.configure(bg=bg_color)

        # Main container centered on screen
        main_container = tk.Frame(
            self,
            bg=bg_color,
            bd=0,
            highlightthickness=0
        )
        main_container.pack(expand=True, fill="both")

        # Center the login form
        center_frame = tk.Frame(main_container, bg=bg_color)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Logo section at top
        logo_frame = tk.Frame(center_frame, bg=bg_color)
        logo_frame.pack(pady=(0, 40))

        # Load and display the logo
        current_script_dir = Path(__file__).parent
        app_base_dir = current_script_dir.parent.parent
        logo_path = app_base_dir / "data" / "themes" / "cosmictwilight" / "images" / "linuxgamingcenter.png"

        try:
            logo_img = Image.open(logo_path)
            # Resize logo to be much bigger for login screen
            max_width = 800
            max_height = 400
            width, height = logo_img.size
            ratio = min(max_width/width, max_height/height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            logo_img = logo_img.resize((new_width, new_height), Image.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_img)

            logo_label = tk.Label(
                logo_frame,
                image=logo_photo,
                bg=bg_color
            )
            logo_label.image = logo_photo
            logo_label.pack()

        except Exception as e:
            # Error loading logo image
            # Fallback text logo
            logo_label = tk.Label(
                logo_frame,
                text="LINUX GAMING CENTER",
                font=("Impact" if IS_LINUX else "Arial", 48, "bold"),
                bg=bg_color,
                fg="white"
            )
            logo_label.pack()

        # Login form container
        login_form = tk.Frame(center_frame, bg=bg_color)
        login_form.pack()

        # Username field
        username_frame = tk.Frame(login_form, bg=bg_color)
        username_frame.pack(fill="x", pady=(0, 15))

        username_label = tk.Label(
            username_frame,
            text="SIGN IN WITH ACCOUNT NAME",
            font=("Arial", 11, "bold"),
            bg=bg_color,
            fg="white"
        )
        username_label.pack(anchor="w", pady=(0, 5))

        self.username_entry = tk.Entry(
            username_frame,
            width=35,
            font=("Arial", 12),
            bg=secondary_color,
            fg="white",
            insertbackground="white",
            bd=1,
            highlightthickness=1,
            highlightbackground="#555555",
            highlightcolor=accent_color,
            relief="flat"
        )
        self.username_entry.pack(fill="x")

        # Password field
        password_frame = tk.Frame(login_form, bg=bg_color)
        password_frame.pack(fill="x", pady=(0, 15))

        password_label = tk.Label(
            password_frame,
            text="PASSWORD",
            font=("Arial", 11, "bold"),
            bg=bg_color,
            fg="white"
        )
        password_label.pack(anchor="w", pady=(0, 5))

        self.password_entry = tk.Entry(
            password_frame,
            show="*",
            width=35,
            font=("Arial", 12),
            bg=secondary_color,
            fg="white",
            insertbackground="white",
            bd=1,
            highlightthickness=1,
            highlightbackground="#555555",
            highlightcolor=accent_color,
            relief="flat"
        )
        self.password_entry.pack(fill="x")

        # Remember me checkbox
        checkbox_frame = tk.Frame(login_form, bg=bg_color)
        checkbox_frame.pack(fill="x", pady=(0, 20))

        self.remember_var = tk.BooleanVar()
        self.remember_checkbox = tk.Checkbutton(
            checkbox_frame,
            text="Remember me",
            variable=self.remember_var,
            bg=bg_color,
            fg="white",
            selectcolor=secondary_color,
            activebackground=bg_color,
            activeforeground="white",
            font=("Arial", 11),
            bd=0,
            highlightthickness=0
        )
        self.remember_checkbox.pack(anchor="w")

        # Button container for sign in and exit buttons
        button_container = tk.Frame(login_form, bg=bg_color)
        button_container.pack(pady=(0, 30))

        # Sign in button
        signin_button = tk.Button(
            button_container,
            text="Sign in",
            command=self._handle_sign_in,
            bg=accent_color,
            fg="white",
            activebackground="#7d26cd",
            activeforeground="white",
            font=("Arial", 12, "bold"),
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            relief="flat",
            width=15
        )
        signin_button.pack(side=tk.LEFT, padx=(0, 15))

        # Exit button
        exit_button = tk.Button(
            button_container,
            text="Exit",
            command=self.controller.quit,
            bg=accent_color,
            fg="white",
            activebackground="#7d26cd",
            activeforeground="white",
            font=("Arial", 12, "bold"),
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            relief="flat",
            width=15
        )
        exit_button.pack(side=tk.LEFT)

        # Add hover effects for both buttons
        self._add_signin_button_hover_effect(signin_button)
        self._add_signin_button_hover_effect(exit_button)

        # Footer links
        footer_frame = tk.Frame(center_frame, bg=bg_color)
        footer_frame.pack(fill="x", pady=(20, 0))

        # Left side - Help link
        help_label = tk.Label(
            footer_frame,
            text="Help. I can't sign in",
            font=("Arial", 11),
            bg=bg_color,
            fg="white",
            cursor="hand2"
        )
        help_label.pack(side="left")

        # Right side - Create account
        account_frame = tk.Frame(footer_frame, bg=bg_color)
        account_frame.pack(side="right")

        account_text = tk.Label(
            account_frame,
            text="Don't have an account? ",
            font=("Arial", 11),
            bg=bg_color,
            fg="white"
        )
        account_text.pack(side="left")

        create_account_label = tk.Label(
            account_frame,
            text="Create a Free Account",
            font=("Arial", 11),
            bg=bg_color,
            fg="white",
            cursor="hand2"
        )
        create_account_label.pack(side="left")


        # Bind click events
        help_label.bind('<Button-1>', lambda e: self._show_help())
        create_account_label.bind('<Button-1>', lambda e: self._create_account_window())

        # Bind Enter key to sign in
        self.username_entry.bind("<Return>", lambda e: self._handle_sign_in())
        self.password_entry.bind("<Return>", lambda e: self._handle_sign_in())

        # Focus on username field
        self.username_entry.focus_set()

    def _handle_sign_in(self):
        """
        Handles the sign in process using username and password.
        """
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username:
            StyledMessageBox.show_info("Error", "Please enter your username.", self)
            return

        if not password:
            StyledMessageBox.show_info("Error", "Please enter your password.", self)
            return

        # Check if account exists by searching all user folders
        accounts_path = self.path_manager.get_path("accounts")
        user_folder = None
        account_file = None

        # Search for the account by checking all folders and matching the clean username
        if accounts_path.exists():
            for folder in accounts_path.iterdir():
                if folder.is_dir():
                    potential_account_file = folder / "account.json"
                    if potential_account_file.exists():
                        try:
                            with open(potential_account_file, 'r') as f:
                                account_data = json.load(f)
                                stored_username = account_data.get('username', '')
                                if stored_username == username:
                                    user_folder = folder
                                    account_file = potential_account_file
                                    break
                        except Exception:
                            continue

        if not user_folder or not account_file:
            StyledMessageBox.show_info("Error", f"Account '{username}' not found.", self)
            return

        try:
            with open(account_file, 'r') as f:
                account_data = json.load(f)
                stored_password_hash = account_data.get('password')
                is_first_login = account_data.get('first_login', False)

                if stored_password_hash and self._verify_password(password, stored_password_hash):
                    # Use the folder name for set_current_user (which may include (admin))
                    self.controller.set_current_user(user_folder.name)
                    # Schedule the menu refresh to happen after the current event loop iteration
                    if hasattr(self.controller, 'refresh_menu_elements'):
                        self.after(100, self.controller.refresh_menu_elements)
                    self.controller.show_frame("DashboardFrame")

                    # Mark first login as False after successful first login
                    if is_first_login:
                        account_data['first_login'] = False
                        with open(account_file, 'w') as f:
                            json.dump(account_data, f, indent=4)
                else:
                    StyledMessageBox.show_info("Error", "Invalid password.", self)
        except Exception as e:
            StyledMessageBox.show_info("Error", f"An error occurred during login: {e}", self)

    def _show_help(self):
        """
        Shows help information for sign in issues.
        """
        help_text = """Sign In Help:

1. Make sure you're using the correct username
2. Check that your password is correct
3. Ensure your account exists in the system

If you continue to have issues, please contact support.

You can also create a new account by clicking 
"Create a Free Account" below."""
        
        # Create a simple help window using Tkinter's built-in messagebox approach
        help_window = tk.Toplevel(self)
        help_window.title("Sign In Help")
        help_window.configure(bg="#0a0a12")
        help_window.resizable(False, False)

        # Position relative to parent window
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 250
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 150
        help_window.geometry(f"500x350+{x}+{y}")

        # Main container
        container = tk.Frame(help_window, bg="#0a0a12")
        container.pack(expand=True, fill="both", padx=20, pady=20)

        # Title
        title_label = tk.Label(
            container,
            text="Sign In Help",
            font=("Arial", 18, "bold"),
            fg="#9a32cd",
            bg="#0a0a12"
        )
        title_label.pack(pady=(0, 20))

        # Help text
        help_label = tk.Label(
            container,
            text=help_text,
            font=("Arial", 11),
            fg="white",
            bg="#0a0a12",
            justify="left",
            wraplength=450
        )
        help_label.pack(pady=(0, 30))

        # Close button - using a simpler approach
        close_button = tk.Button(
            container,
            text="Close",
            command=help_window.destroy,
            bg="#9a32cd",
            fg="white",
            activebackground="#7d26cd",
            activeforeground="white",
            font=("Arial", 14, "bold"),
            bd=0,
            padx=40,
            pady=15,
            relief="flat",
            cursor="hand2"
        )
        close_button.pack()

        # Add hover effect
        self._add_modern_button_hover_effect(close_button, "#9a32cd", "#7d26cd")

        # Make the window modal
        help_window.transient(self)
        try:
            help_window.grab_set()
        except tk.TclError:
            pass

    def _add_signin_button_hover_effect(self, button):
        """
        Adds a gradient-like hover effect to the sign in button.
        """
        def on_enter(e):
            button.config(bg="#7d26cd")
            button.config(cursor="hand2")

        def on_leave(e):
            button.config(bg=self.styles["accent_color"])

        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)

    def on_show_frame(self):
        """
        Called when this frame is brought to the front.
        Clears the login fields for a fresh login experience.
        """
        # Clear login fields
        if hasattr(self, 'username_entry'):
            self.username_entry.delete(0, tk.END)
        if hasattr(self, 'password_entry'):
            self.password_entry.delete(0, tk.END)
        if hasattr(self, 'remember_var'):
            self.remember_var.set(False)
        
        # Focus on username field
        if hasattr(self, 'username_entry'):
            self.username_entry.focus_set()

    def _clear_password_fields(self):
        """
        Destroys and clears any currently displayed password input widgets.
        """
        # This implementation assumes password fields are directly children of the LoginFrame
        # or within a specific container that can be identified and cleared.
        # The original code had a 'password_container' attribute.
        for widget in self.winfo_children():
            if hasattr(widget, "password_container") and widget.password_container:
                # Destroying existing password container
                widget.destroy()
                break
        self.password_widgets = None # Clear reference
        self.current_login_username = None
        # Password fields cleared


    def _load_existing_profiles(self):
        """
        Loads existing user profiles from the configured accounts directory
        and creates interactive profile buttons/icons for each.
        """
        # Clear existing profile buttons
        for widget in self.profile_buttons_frame.winfo_children():
            widget.destroy()
        self.profile_buttons = {}

        # MODIFIED: Use path_manager to get the accounts directory
        accounts_path = self.path_manager.get_path("accounts")
        
        # Create accounts directory if it doesn't exist
        if not accounts_path.exists(): # Use Path.exists()
            accounts_path.mkdir(parents=True) # Use Path.mkdir()
            return # No profiles to load yet

        account_folders = [
            d for d in accounts_path.iterdir() # Use Path.iterdir()
            if d.is_dir() # Use Path.is_dir()
        ]
        
        # Sort to ensure consistent order, especially for determining the "first" account
        account_folders.sort() 

        # Modern profile card size
        card_width = 180
        card_height = 220
        image_size = 120

        if not account_folders:
            # Modern empty state message
            empty_frame = tk.Frame(self.profile_buttons_frame, bg=self.styles["background_color"])
            empty_frame.pack(expand=True, fill="both")
            
            empty_label = tk.Label(
                empty_frame,
                text="No profiles found",
                font=("Arial", 16, "bold"),
                bg=self.styles["background_color"],
                fg="#888888"
            )
            empty_label.pack(pady=(50, 10))
            
            empty_subtitle = tk.Label(
                empty_frame,
                text="Click 'CREATE PROFILE' to get started",
                font=("Arial", 12),
                bg=self.styles["background_color"],
                fg="#666666"
            )
            empty_subtitle.pack()
            return

        # Create a modern grid layout for profile cards
        max_cards_per_row = 4
        current_row = 0
        current_col = 0

        for i, username_folder_path_obj in enumerate(account_folders):
            username_folder_name = username_folder_path_obj.name
            account_file = username_folder_path_obj / "account.json"
            
            if not account_file.is_file():
                # Error: Account file not found, skipping profile
                continue

            try:
                with open(account_file, 'r') as f:
                    account_data = json.load(f)
                    profile_image_filename = account_data.get('profile_image')
                    is_account_admin = account_data.get('is_admin', False)

                    original_username = username_folder_name.replace(" (admin)", "")
                    display_username = original_username
                    if is_account_admin:
                        display_username = f"{original_username} (admin)"

                    # Create modern profile card
                    profile_card = self._create_modern_profile_card(
                        username_folder_name, 
                        display_username, 
                        profile_image_filename, 
                        username_folder_path_obj,
                        card_width, 
                        card_height, 
                        image_size
                    )
                    
                    # Position in grid
                    profile_card.grid(
                        row=current_row, 
                        column=current_col, 
                        padx=15, 
                        pady=15, 
                        sticky="nsew"
                    )
                    
                    # Update grid position
                    current_col += 1
                    if current_col >= max_cards_per_row:
                        current_col = 0
                        current_row += 1

            except Exception as e:
                # Error loading profile
                pass

        # Configure grid weights for responsive layout
        for i in range(max_cards_per_row):
            self.profile_buttons_frame.grid_columnconfigure(i, weight=1)
        for i in range(current_row + 1):
            self.profile_buttons_frame.grid_rowconfigure(i, weight=1)

    def _create_modern_profile_card(self, username_folder_name, display_username, profile_image_filename, username_folder_path_obj, card_width, card_height, image_size):
        """
        Creates a modern profile card with gaming-inspired design.
        
        Args:
            username_folder_name (str): The folder name for the user
            display_username (str): The display name for the user
            profile_image_filename (str): The profile image filename
            username_folder_path_obj (Path): Path to the user folder
            card_width (int): Width of the profile card
            card_height (int): Height of the profile card
            image_size (int): Size of the profile image
            
        Returns:
            tk.Frame: The created profile card frame
        """
        # Main card container with modern styling
        card_frame = tk.Frame(
            self.profile_buttons_frame,
            bg=self.styles["secondary_color"],
            bd=0,
            highlightthickness=2,
            highlightbackground=self.styles["accent_color"],
            highlightcolor=self.styles["accent_color"],
            width=card_width,
            height=card_height
        )
        
        # Profile image container
        image_frame = tk.Frame(card_frame, bg=self.styles["secondary_color"])
        image_frame.pack(pady=(15, 10))
        
        if profile_image_filename:
            image_path = username_folder_path_obj / profile_image_filename
            try:
                img_pil = Image.open(image_path)
                img_pil = img_pil.resize((image_size, image_size), Image.LANCZOS)
                
                # Create circular mask
                mask = Image.new('L', (image_size, image_size), 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, image_size, image_size), fill=255)
                
                # Create circular border
                border_img = Image.new('RGBA', (image_size, image_size), (0, 0, 0, 0))
                border_draw = ImageDraw.Draw(border_img)
                border_draw.ellipse(
                    (0, 0, image_size, image_size),
                    outline=self.styles["accent_color"],
                    width=4
                )
                
                img_pil.putalpha(mask)
                final_img = Image.alpha_composite(border_img, img_pil)
                img_tk = ImageTk.PhotoImage(final_img)
                
                profile_image_label = tk.Label(
                    image_frame,
                    image=img_tk,
                    bg=self.styles["secondary_color"],
                    bd=0
                )
                profile_image_label.image = img_tk
                profile_image_label.pil_image = img_pil
                profile_image_label.pack()
                
                # Store reference for hover effects
                card_frame.profile_image_label = profile_image_label
                card_frame.original_image = img_tk
                
            except Exception as e:
                # Error loading image
                # Create fallback circular avatar
                self._create_fallback_avatar(image_frame, display_username, image_size)
        else:
            # Create fallback circular avatar
            self._create_fallback_avatar(image_frame, display_username, image_size)
        
        # Username label with modern styling
        username_label = tk.Label(
            card_frame,
            text=display_username.upper(),
            font=("Arial", 12, "bold"),
            bg=self.styles["secondary_color"],
            fg="white",
            wraplength=card_width - 20
        )
        username_label.pack(pady=(0, 10))
        
        # Admin badge if applicable
        if "(admin)" in display_username.lower():
            admin_badge = tk.Label(
                card_frame,
                text="ADMIN",
                font=("Arial", 8, "bold"),
                bg=self.styles["accent_color"],
                fg="white",
                padx=8,
                pady=2
            )
            admin_badge.pack(pady=(0, 10))
        
        # Store references for interaction
        card_frame.profile_username = username_folder_name
        card_frame.username_label = username_label
        
        # Bind click events to the entire card
        card_frame.bind('<Button-1>', lambda e, u=username_folder_name: self._show_login_fields(u))
        username_label.bind('<Button-1>', lambda e, u=username_folder_name: self._show_login_fields(u))
        if hasattr(card_frame, 'profile_image_label'):
            card_frame.profile_image_label.bind('<Button-1>', lambda e, u=username_folder_name: self._show_login_fields(u))
        
        # Add modern hover effects
        self._add_card_hover_effect(card_frame)
        
        # Store in profile buttons dictionary
        self.profile_buttons[username_folder_name] = card_frame
        
        return card_frame

    def _create_fallback_avatar(self, parent, display_username, size):
        """
        Creates a modern fallback avatar with the first letter of the username.
        
        Args:
            parent (tk.Widget): The parent widget
            display_username (str): The display username
            size (int): Size of the avatar
        """
        canvas = tk.Canvas(
            parent,
            width=size,
            height=size,
            bg=self.styles["secondary_color"],
            highlightthickness=0,
            bd=0
        )
        
        # Draw modern circular background with gradient effect
        canvas.create_oval(
            5, 5, size-5, size-5,
            fill=self.styles["button_color"],
            outline=self.styles["accent_color"],
            width=4
        )
        
        # Draw the first letter
        initial = display_username.split(' ')[0][0].upper()
        canvas.create_text(
            size // 2, size // 2,
            text=initial,
            fill="white",
            font=("Arial", 32, "bold")
        )
        
        canvas.pack()
        return canvas

    def _add_card_hover_effect(self, card_frame):
        """
        Adds modern hover effects to profile cards.
        
        Args:
            card_frame (tk.Frame): The profile card frame
        """
        original_bg = card_frame.cget("bg")
        original_highlight = card_frame.cget("highlightbackground")
        
        def on_enter(e):
            card_frame.config(bg=self.styles["accent_color"])
            card_frame.config(highlightbackground="#7d26cd")
            card_frame.config(cursor="hand2")
            
            # Update child widgets
            for child in card_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg=self.styles["accent_color"])
                elif isinstance(child, tk.Label):
                    child.config(bg=self.styles["accent_color"])
        
        def on_leave(e):
            card_frame.config(bg=original_bg)
            card_frame.config(highlightbackground=original_highlight)
            
            # Update child widgets
            for child in card_frame.winfo_children():
                if isinstance(child, tk.Frame):
                    child.config(bg=original_bg)
                elif isinstance(child, tk.Label):
                    child.config(bg=original_bg)
        
        card_frame.bind('<Enter>', on_enter)
        card_frame.bind('<Leave>', on_leave)

    def _create_circular_text_button(self, parent, username_folder_name, display_username):
        """
        Creates a circular button with the first letter of the username
        if no profile image is available.

        Args:
            parent (tk.Widget): The parent widget for the canvas.
            username_folder_name (str): The actual folder name (e.g., 'derek' or 'derek (admin)').
            display_username (str): The name to display (e.g., 'derek (admin)').
        """
        button_size = 100
        bg_color = self.styles["background_color"]
        button_color = self.styles["button_color"]
        accent_color = self.styles["accent_color"]

        canvas = tk.Canvas(
            parent,
            width=button_size,
            height=button_size,
            bg=bg_color,
            highlightthickness=0,
            bd=0
        )

        # Draw the circular background
        canvas.create_oval(
            5, 5, button_size-5, button_size-5,
            fill=button_color,
            outline=accent_color, # Purple outline
            width=2
        )

        # Draw the first letter of the username
        initial_to_display = display_username.split(' ')[0][0].upper() # Use first letter of the first word
        canvas.create_text(
            button_size // 2, button_size // 2,
            text=initial_to_display,
            fill="white",
            font=("Impact" if IS_LINUX else "Arial", 24)
        )

        canvas.bind('<Button-1>', lambda e, u=username_folder_name: self._show_login_fields(u))
        canvas.pack()
        canvas.profile_username = username_folder_name
        self.profile_buttons[username_folder_name] = canvas
        self._add_button_hover_effect_canvas(canvas, button_color, accent_color)

    def _add_button_hover_effect(self, button, hover_color):
        """
        Adds a hover effect to a standard Tkinter button.

        Args:
            button (tk.Button): The button to apply the effect to.
            hover_color (str): The background color on hover.
        """
        original_bg = button.cget("bg")

        def on_enter(e):
            button.config(bg=hover_color)
            button.config(cursor="hand2")

        def on_leave(e):
            button.config(bg=original_bg)

        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)

    def _add_modern_button_hover_effect(self, button, base_color, hover_color):
        """
        Adds a modern hover effect with smooth transitions to buttons.

        Args:
            button (tk.Button): The button to apply the effect to.
            base_color (str): The original background color.
            hover_color (str): The background color on hover.
        """
        def on_enter(e):
            button.config(bg=hover_color)
            button.config(cursor="hand2")

        def on_leave(e):
            button.config(bg=base_color)

        button.bind('<Enter>', on_enter)
        button.bind('<Leave>', on_leave)

    def _add_button_hover_effect_canvas(self, canvas, base_color, hover_color):
        """
        Adds a hover effect to a Tkinter Canvas (used for circular text buttons).

        Args:
            canvas (tk.Canvas): The canvas to apply the effect to.
            base_color (str): The original fill color of the circle.
            hover_color (str): The fill color on hover.
        """
        def on_enter(e):
            canvas.itemconfig(1, fill=hover_color) # Item 1 is the oval
            canvas.config(cursor="hand2")

        def on_leave(e):
            canvas.itemconfig(1, fill=base_color)

        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)

    def _add_profile_image_hover_effect_label(self, label, original_tk_image):
        """
        Adds a hover effect to a profile image label, showing a purple overlay.

        Args:
            label (tk.Label): The label displaying the profile image.
            original_tk_image (ImageTk.PhotoImage): The original PhotoImage object.
        """
        def on_enter(e):
            # Get the original PIL image from the label's stored attribute
            # Make a copy and convert to RGBA to ensure alpha channel for compositing
            current_pil_image = label.pil_image.copy().convert("RGBA")

            width, height = current_pil_image.size

            # Create a semi-transparent purple overlay
            overlay_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay_img)
            # Draw a semi-transparent purple circle on top
            draw.ellipse((0, 0, width, height), fill=(154, 50, 205, 100)) # Purple with 100 alpha

            # Create a circular mask for the current PIL image
            mask = Image.new('L', (width, height), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, width, height), fill=255)
            current_pil_image.putalpha(mask) # Apply mask to the current PIL image

            # Create a border image
            border_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            border_draw = ImageDraw.Draw(border_img)
            border_draw.ellipse(
                (0, 0, width, height),
                outline=self.styles["accent_color"],
                width=3
            )

            # Combine original image, overlay, and border
            combined_img = Image.alpha_composite(current_pil_image, overlay_img)
            final_img = Image.alpha_composite(border_img, combined_img)

            highlight_img = ImageTk.PhotoImage(final_img)
            label.config(image=highlight_img)
            label.highlight_image = highlight_img # Keep reference
            label.config(cursor="hand2")

        def on_leave(e):
            label.config(image=original_tk_image)

        label.bind('<Enter>', on_enter)
        label.bind('<Leave>', on_leave)

    def _show_login_fields(self, username):
        """
        Displays the password entry field and login button for the selected profile.

        Args:
            username (str): The username of the selected profile.
        """
        # Attempting to show login fields

        # Destroy any existing login container
        for widget in self.winfo_children():
            # Check if the widget is a frame and has the 'password_container' attribute
            if isinstance(widget, tk.Frame) and hasattr(widget, "password_container") and widget.password_container:
                # Destroying existing password container
                widget.destroy()
                break

        # Explicitly clear password_widgets references after destruction
        # This is crucial to prevent stale references after a widget is destroyed.
        self.password_widgets = None
        self.current_login_username = username

        try:
            # Creating new login fields
            
            # Modern login container with centered positioning
            login_container = tk.Frame(self, bg=self.styles["background_color"])
            login_container.pack(pady=20)
            login_container.password_container = True  # Mark this frame for easy destruction

            # Modern login card with enhanced styling
            login_card = tk.Frame(
                login_container,
                bg=self.styles["secondary_color"],
                bd=0,
                highlightthickness=3,
                highlightbackground=self.styles["accent_color"],
                highlightcolor=self.styles["accent_color"],
                relief="flat"
            )
            login_card.pack(pady=10, padx=20)

            # Header section
            header_frame = tk.Frame(login_card, bg=self.styles["secondary_color"])
            header_frame.pack(fill="x", pady=(20, 10), padx=20)

            # Profile icon (if available)
            profile_icon_frame = tk.Frame(header_frame, bg=self.styles["secondary_color"])
            profile_icon_frame.pack()

            # Try to get profile image for the login header
            try:
                accounts_path = self.path_manager.get_path("accounts")
                user_folder = accounts_path / username
                account_file = user_folder / "account.json"
                
                if account_file.exists():
                    with open(account_file, 'r') as f:
                        account_data = json.load(f)
                        profile_image_filename = account_data.get('profile_image')
                        
                        if profile_image_filename:
                            image_path = user_folder / profile_image_filename
                            try:
                                img_pil = Image.open(image_path)
                                img_pil = img_pil.resize((60, 60), Image.LANCZOS)
                                
                                # Create circular mask
                                mask = Image.new('L', (60, 60), 0)
                                draw = ImageDraw.Draw(mask)
                                draw.ellipse((0, 0, 60, 60), fill=255)
                                
                                # Create circular border
                                border_img = Image.new('RGBA', (60, 60), (0, 0, 0, 0))
                                border_draw = ImageDraw.Draw(border_img)
                                border_draw.ellipse(
                                    (0, 0, 60, 60),
                                    outline=self.styles["accent_color"],
                                    width=3
                                )
                                
                                img_pil.putalpha(mask)
                                final_img = Image.alpha_composite(border_img, img_pil)
                                img_tk = ImageTk.PhotoImage(final_img)
                                
                                profile_icon = tk.Label(
                                    profile_icon_frame,
                                    image=img_tk,
                                    bg=self.styles["secondary_color"],
                                    bd=0
                                )
                                profile_icon.image = img_tk
                                profile_icon.pack()
                                
                            except Exception as e:
                                # Error loading profile icon
                                # Create fallback icon
                                self._create_fallback_avatar(profile_icon_frame, username, 60)
                        else:
                            # Create fallback icon
                            self._create_fallback_avatar(profile_icon_frame, username, 60)
            except Exception as e:
                # Error creating profile icon
                # Create fallback icon
                self._create_fallback_avatar(profile_icon_frame, username, 60)

            # Username title
            username_title = tk.Label(
                header_frame,
                text=f"LOG IN AS {username.upper()}",
                font=("Arial", 14, "bold"),
                bg=self.styles["secondary_color"],
                fg="white"
            )
            username_title.pack(pady=(10, 0))

            # Input section
            input_frame = tk.Frame(login_card, bg=self.styles["secondary_color"])
            input_frame.pack(fill="x", pady=(10, 20), padx=20)

            # Password label
            password_label = tk.Label(
                input_frame,
                text="PASSWORD:",
                font=("Arial", 11, "bold"),
                bg=self.styles["secondary_color"],
                fg="#cccccc"
            )
            password_label.pack(anchor="w", pady=(0, 5))

            # Modern password entry
            self.password_entry = tk.Entry(
                input_frame,
                show="*",
                width=30,
                font=("Arial", 12),
                bg="#2a2a3e",
                fg="white",
                insertbackground="white",
                bd=0,
                highlightthickness=2,
                highlightbackground="#555577",
                highlightcolor=self.styles["accent_color"],
                relief="flat"
            )
            self.password_entry.pack(fill="x", pady=(0, 15))
            self.password_entry.focus_set()

            # Button section
            button_frame = tk.Frame(login_card, bg=self.styles["secondary_color"])
            button_frame.pack(fill="x", pady=(0, 20), padx=20)

            # Modern login button
            login_button = tk.Button(
                button_frame,
                text="LOGIN",
                command=self._login_existing_user,
                bg=self.styles["accent_color"],
                fg="white",
                activebackground="#7d26cd",
                activeforeground="white",
                font=("Arial", 12, "bold"),
                bd=0,
                padx=30,
                pady=10,
                cursor="hand2",
                relief="flat",
                width=15
            )
            login_button.pack()

            # Add modern hover effect
            self._add_modern_button_hover_effect(login_button, self.styles["accent_color"], "#7d26cd")
            
            self.password_widgets = (self.password_entry, login_button)

            # Bind <Return> key to login
            self.password_entry.bind("<Return>", lambda e: self._login_existing_user())
            # Modern login fields successfully created

        except Exception as e:
            # Error creating login fields
            StyledMessageBox.show_info("Error", f"Could not open login fields: {e}", self)
            # Clear password_widgets if an error occurs during creation
            self.password_widgets = None


    def _login_existing_user(self):
        """
        Authenticates the user with the entered password.
        If successful, redirects to the dashboard.
        """
        if not hasattr(self, "current_login_username") or not self.current_login_username:
            StyledMessageBox.show_info("Error", "No user selected. Please select a profile.", self)
            return

        username = self.current_login_username

        # Check if password_widgets exist and are still valid (not destroyed)
        if not self.password_widgets or not self.password_widgets[0].winfo_exists():
            StyledMessageBox.show_info("Error", "Password entry not found. Please select a profile again.", self)
            return

        password = self.password_widgets[0].get()

        if not password:
            StyledMessageBox.show_info("Error", "Please enter your password.", self)
            return

        # MODIFIED: Use path_manager to get the accounts directory
        accounts_path = self.path_manager.get_path("accounts")
        user_folder = accounts_path / username # Use Path object concatenation
        account_file = user_folder / "account.json" # Use Path object concatenation

        # Attempting to open account file for login
        if not account_file.exists(): # Use Path object's exists()
            # Account file does not exist
            StyledMessageBox.show_info("Error", "Account file not found.", self)
            return

        try:
            with open(account_file, 'r') as f:
                account_data = json.load(f)
                stored_password_hash = account_data.get('password')
                is_first_login = account_data.get('first_login', False)

                if stored_password_hash and self._verify_password(password, stored_password_hash):
                    self.controller.set_current_user(username)
                    # Schedule the menu refresh to happen after the current event loop iteration
                    if hasattr(self.controller, 'refresh_menu_elements'):
                        self.after(100, self.controller.refresh_menu_elements) # Added 100ms delay
                    self.controller.show_frame("DashboardFrame")

                    # Mark first login as False after successful first login
                    if is_first_login:
                        account_data['first_login'] = False
                        with open(account_file, 'w') as f:
                            json.dump(account_data, f, indent=4)
                else:
                    StyledMessageBox.show_info("Error", "Invalid password.", self)
        except FileNotFoundError: # This should ideally be caught by the account_file.exists() check above
            StyledMessageBox.show_info("Error", "Account file not found.", self)
        except json.JSONDecodeError:
            StyledMessageBox.show_info("Error", "Error reading account data. Account may be corrupted.", self)
        except Exception as e:
            StyledMessageBox.show_info("Error", f"An unexpected error occurred: {e}", self)


    def _create_account_window(self):
        """
        Opens a new Toplevel window for creating a new user account.
        """
        # Destroy any existing login container before opening the create account window
        for widget in self.winfo_children():
            # Check if the widget is a frame and has the 'password_container' attribute
            if isinstance(widget, tk.Frame) and hasattr(widget, "password_container") and widget.password_container:
                # Destroying existing password container before creating account
                widget.destroy()
                break
        self.password_widgets = None # Clear reference to destroyed widgets

        self.create_account_window = tk.Toplevel(self)
        self.create_account_window.title("Create New Profile")

        # Position relative to parent window for better UX
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 250
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 300
        self.create_account_window.geometry(f"500x600+{x}+{y}")

        bg_color = self.styles["background_color"]
        accent_color = self.styles["accent_color"]
        secondary_color = self.styles["secondary_color"]
        text_color = self.styles["text_color"]

        self.create_account_window.configure(bg=bg_color)

        # Main container
        main_container = tk.Frame(self.create_account_window, bg=bg_color)
        main_container.pack(expand=True, fill="both", padx=20, pady=20)

        # Header section
        header_frame = tk.Frame(main_container, bg=bg_color)
        header_frame.pack(fill="x", pady=(0, 20))

        # Title with modern styling
        title_label = tk.Label(
            header_frame,
            text="CREATE NEW PROFILE",
            font=("Arial", 20, "bold"),
            fg=accent_color,
            bg=bg_color
        )
        title_label.pack()

        # Subtitle
        subtitle_label = tk.Label(
            header_frame,
            text="Set up your gaming profile",
            font=("Arial", 12),
            fg="#cccccc",
            bg=bg_color
        )
        subtitle_label.pack(pady=(5, 0))

        # Main form card
        form_card = tk.Frame(
            main_container,
            bg=secondary_color,
            bd=0,
            highlightthickness=2,
            highlightbackground=accent_color,
            highlightcolor=accent_color
        )
        form_card.pack(fill="both", pady=(0, 20))

        # Form content
        form_content = tk.Frame(form_card, bg=secondary_color)
        form_content.pack(fill="both", padx=30, pady=30)

        field_font = ("Arial", 11)
        entry_bg = "#2a2a3e"
        label_fg = "#cccccc"

        # Username field
        username_frame = tk.Frame(form_content, bg=secondary_color)
        username_frame.pack(fill="x", pady=(0, 15))

        tk.Label(
            username_frame,
            text="USERNAME:",
            font=field_font,
            fg=label_fg,
            bg=secondary_color
        ).pack(anchor="w", pady=(0, 5))

        self.new_username = tk.StringVar()
        username_entry = tk.Entry(
            username_frame,
            textvariable=self.new_username,
            font=field_font,
            bg=entry_bg,
            fg=text_color,
            insertbackground=text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground="#555577",
            highlightcolor=accent_color,
            bd=0
        )
        username_entry.pack(fill="x", pady=(0, 5))

        # Password field
        password_frame = tk.Frame(form_content, bg=secondary_color)
        password_frame.pack(fill="x", pady=(0, 15))

        tk.Label(
            password_frame,
            text="PASSWORD:",
            font=field_font,
            fg=label_fg,
            bg=secondary_color
        ).pack(anchor="w", pady=(0, 5))

        self.new_password = tk.StringVar()
        password_entry = tk.Entry(
            password_frame,
            textvariable=self.new_password,
            show="*",
            font=field_font,
            bg=entry_bg,
            fg=text_color,
            insertbackground=text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground="#555577",
            highlightcolor=accent_color,
            bd=0
        )
        password_entry.pack(fill="x", pady=(0, 5))

        # Confirm Password field
        confirm_frame = tk.Frame(form_content, bg=secondary_color)
        confirm_frame.pack(fill="x", pady=(0, 15))

        tk.Label(
            confirm_frame,
            text="CONFIRM PASSWORD:",
            font=field_font,
            fg=label_fg,
            bg=secondary_color
        ).pack(anchor="w", pady=(0, 5))

        self.confirm_password = tk.StringVar()
        confirm_entry = tk.Entry(
            confirm_frame,
            textvariable=self.confirm_password,
            show="*",
            font=field_font,
            bg=entry_bg,
            fg=text_color,
            insertbackground=text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground="#555577",
            highlightcolor=accent_color,
            bd=0
        )
        confirm_entry.pack(fill="x", pady=(0, 5))

        # Profile Image selection
        image_frame = tk.Frame(form_content, bg=secondary_color)
        image_frame.pack(fill="x", pady=(0, 20))

        tk.Label(
            image_frame,
            text="PROFILE IMAGE:",
            font=field_font,
            fg=label_fg,
            bg=secondary_color
        ).pack(anchor="w", pady=(0, 5))

        # Image selection row
        image_selection_frame = tk.Frame(image_frame, bg=secondary_color)
        image_selection_frame.pack(fill="x")

        self.profile_image_path = tk.StringVar()
        image_entry = tk.Entry(
            image_selection_frame,
            textvariable=self.profile_image_path,
            state="readonly",
            font=field_font,
            bg=entry_bg,
            fg=text_color,
            relief="flat",
            highlightthickness=2,
            highlightbackground="#555577",
            highlightcolor=accent_color,
            bd=0
        )
        image_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))

        browse_button = tk.Button(
            image_selection_frame,
            text="BROWSE",
            command=self._browse_image,
            bg=accent_color,
            fg=text_color,
            activebackground="#7d26cd",
            activeforeground=text_color,
            font=("Arial", 10, "bold"),
            bd=0,
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        browse_button.pack(side=tk.RIGHT)
        self._add_modern_button_hover_effect(browse_button, accent_color, "#7d26cd")

        # Button section
        button_frame = tk.Frame(form_content, bg=secondary_color)
        button_frame.pack(fill="x", pady=(10, 0))

        # Create Account button
        create_button = tk.Button(
            button_frame,
            text="CREATE PROFILE",
            command=self._create_new_account,
            bg=accent_color,
            fg=text_color,
            activebackground="#7d26cd",
            activeforeground=text_color,
            font=("Arial", 12, "bold"),
            bd=0,
            padx=30,
            pady=12,
            relief="flat",
            cursor="hand2",
            width=20
        )
        create_button.pack()
        self._add_modern_button_hover_effect(create_button, accent_color, "#7d26cd")

        # Window settings
        self.create_account_window.resizable(False, False)
        self.create_account_window.transient(self)
        try:
            self.create_account_window.grab_set()
        except tk.TclError:
            # If grab_set fails, continue without modal behavior
            pass
        self.create_account_window.wait_window()

    def _browse_image(self):
        """
        Opens a file dialog to select a profile image.
        """
        file_path = filedialog.askopenfilename(
            title="Select Profile Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")],
            initialdir=str(Path.home()), # MODIFIED: Use Path.home() for initial directory
            parent=self.create_account_window # Make it modal to the creation window
        )
        if file_path:
            self.profile_image_path.set(file_path)

    def _create_new_account(self):
        """
        Validates input and creates a new user account.
        Saves user data and profile image to the new $HOME/.config location.
        """
        username = self.new_username.get().strip().lower()
        password = self.new_password.get()
        confirm_password = self.confirm_password.get()
        profile_image = self.profile_image_path.get()

        # Input validation
        if not username:
            StyledMessageBox.show_info("Error", "Username cannot be empty.", self.create_account_window)
            return
        if not password:
            StyledMessageBox.show_info("Error", "Password cannot be empty.", self.create_account_window)
            return
        if password != confirm_password:
            StyledMessageBox.show_info("Error", "Passwords do not match.", self.create_account_window)
            return
        if ' ' in username:
            StyledMessageBox.show_info("Error", "Username cannot contain spaces.", self.create_account_window)
            return

        # MODIFIED: Use path_manager to get the accounts directory
        accounts_base_path = self.path_manager.get_path("accounts")
        
        # Check if this is the very first account being created by checking if accounts_base_path is empty
        is_first_account = not accounts_base_path.exists() or not any(accounts_base_path.iterdir())

        user_folder_name = username
        if is_first_account:
            user_folder_name = f"{username} (admin)" # Append (admin) to the folder name

        user_folder_path = accounts_base_path / user_folder_name # Use Path object concatenation

        if user_folder_path.exists(): # Use Path object's exists()
            StyledMessageBox.show_info("Error", f"Username '{username}' already exists. Please choose a different one.", self.create_account_window)
            return

        try:
            user_folder_path.mkdir(parents=True, exist_ok=True) # Create user-specific directory
            hashed_password = self._hash_password(password)
            account_data = {
                'username': username, # Store clean username in JSON
                'password': hashed_password,
                'profile_image': Path(self.profile_image_path.get()).name if self.profile_image_path.get() else None, # Store only filename
                'is_admin': is_first_account, # Mark as admin in JSON
                'first_login': True
            }

            account_file = user_folder_path / "account.json" # Use Path object concatenation
            with open(account_file, 'w') as f:
                json.dump(account_data, f, indent=4) # Save account data

            if self.profile_image_path.get():
                dest_path = user_folder_path / Path(self.profile_image_path.get()).name # Use Path object concatenation
                shutil.copy(self.profile_image_path.get(), dest_path) # Copy profile image to user folder

            StyledMessageBox.show_info("Success", f"Account '{username}' created successfully!", self.create_account_window)
            
            # Refresh SwitchuserFrame profiles after new account creation
            if hasattr(self.controller, 'frames') and "SwitchuserFrame" in self.controller.frames:
                switchuser_frame = self.controller.frames["SwitchuserFrame"]
                if hasattr(switchuser_frame, 'load_profiles') and callable(switchuser_frame.load_profiles):
                    switchuser_frame.load_profiles()

            self.create_account_window.destroy() # Close creation window
        except Exception as e:
            StyledMessageBox.show_info("Creation Failed", f"An error occurred while creating account: {e}", self.create_account_window)
            # Error creating account
            import traceback
            traceback.print_exc()

    def _hash_password(self, password):
        """
        Hashes the given password using SHA256.

        Args:
            password (str): The plain text password.

        Returns:
            str: The SHA256 hashed password.
        """
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, password, stored_hash):
        """
        Verifies if the given password matches the stored hash.

        Args:
            password (str): The plain text password to verify.
            stored_hash (str): The hashed password stored in the account file.

        Returns:
            bool: True if passwords match, False otherwise.
        """
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash

    def get_user_profile_image_path(self, username_folder_name):
        """
        Returns the full path to the profile image for a given username (folder name).
        Assumes the profile image filename is stored in account.json.
        """
        # MODIFIED: Use path_manager to get the accounts directory
        accounts_dir = self.path_manager.get_path("accounts")
        user_folder = accounts_dir / username_folder_name # Use Path object concatenation
        account_file = user_folder / "account.json" # Use Path object concatenation

        if not account_file.exists(): # Use Path object's exists()
            # Error: Account file not found
            return None

        try:
            with open(account_file, 'r') as f:
                account_data = json.load(f)
                profile_image_filename = account_data.get('profile_image')
                if profile_image_filename:
                    return str(user_folder / profile_image_filename) # Return as string
                else:
                    return None # No profile image set for this user
        except Exception as e:
            # Error reading account data
            return None


if __name__ == "__main__":
    # This block is for testing the LoginFrame independently
    root = tk.Tk()
    root.title("Linux Gaming Center - Login")
    root.geometry("800x650") # Set initial window size

    # Create a dummy PathManager for testing purposes
    class MockPathManager:
        def __init__(self):
            # Define paths relative to a temporary test root
            self.test_root = Path.home() / ".test_linc_app_data"
            self.default_config_root = self.test_root / ".config" / "linux-gaming-center"
            self.default_data_root = self.test_root / ".local" / "share" / "linux-gaming-center"
            self._active_custom_root_path = None # Simulate no custom root initially
            self._individual_custom_paths = {}

            # Ensure default accounts path exists for testing
            (self.default_config_root / "accounts").mkdir(parents=True, exist_ok=True)
            (self.default_data_root / "user_data").mkdir(parents=True, exist_ok=True) # For profile images
            (self.default_data_root / "themes" / "cosmictwilight" / "images").mkdir(parents=True, exist_ok=True) # For logo

        def get_path(self, category: str) -> Path:
            if category == "accounts":
                if self._active_custom_root_path:
                    return self._active_custom_root_path / "config" / "linux-gaming-center" / "accounts"
                return self.default_config_root / "accounts"
            elif category == "data": # For user_data/profile_images
                 if self._active_custom_root_path:
                    return self._active_custom_root_path / "data" / "linux-gaming-center" / "user_data"
                 return self.default_data_root / "user_data"
            elif category == "themes": # For logo path
                if self._active_custom_root_path:
                    return self._active_custom_root_path / "data" / "linux-gaming-center" / "themes"
                return self.default_data_root / "themes"
            # Add other categories if needed for comprehensive testing
            return self.test_root / "mock_path" / category # Fallback for other categories

        def load_paths(self):
            # MockPathManager: load_paths called
            # In a real app, this would load from paths.json.
            # For testing, you could change _active_custom_root_path here if needed.
            # Example: self._active_custom_root_path = Path.home() / "Documents" / "CustomGamingCenter"
            pass

        def is_global_custom_path_active(self) -> bool:
            return self._active_custom_root_path is not None and self._active_custom_root_path.is_dir()

        def set_mock_global_custom_path(self, new_path: Path):
            self._active_custom_root_path = new_path
            # Ensure the structure exists in the mock custom path
            (new_path / "config" / "linux-gaming-center" / "accounts").mkdir(parents=True, exist_ok=True)
            (new_path / "data" / "linux-gaming-center" / "user_data").mkdir(parents=True, exist_ok=True)
            (new_path / "data" / "linux-gaming-center" / "themes" / "cosmictwilight" / "images").mkdir(parents=True, exist_ok=True)


    # Create a dummy controller for testing purposes
    class MockController:
        def __init__(self, root_win, path_manager): # MODIFIED: Accept path_manager
            self.current_user = None
            self.root_win = root_win
            self.frames = {} # Mock frames dictionary
            self.path_manager = path_manager # STORED: path_manager

            # Mock SwitchuserFrame for testing
            class MockSwitchuserFrame:
                def load_profiles(self):
                    # MockSwitchuserFrame: load_profiles called
                    pass
            self.frames["SwitchuserFrame"] = MockSwitchuserFrame()


        def set_current_user(self, username):
            self.current_user = username
            # Current user set

        def show_frame(self, frame_name):
            # Navigating to frame
            # In a real app, this would switch visible frames
            if frame_name == "DashboardFrame":
                # Simulate dashboard trying to get profile picture
                if self.current_user:
                    # Assuming login_frame is accessible via root_win or controller
                    # In a real app, controller might have a direct reference to LoginFrame
                    # or a utility function to get image path.
                    # For this mock, we'll assume login_frame is directly available.
                    mock_login_frame_instance = login_frame # Access the global login_frame for testing
                    profile_img_path = mock_login_frame_instance.get_user_profile_image_path(self.current_user)
                    if profile_img_path:
                        StyledMessageBox.show_info("Dashboard", f"Welcome to the Dashboard, {self.current_user}! Profile image path: {profile_img_path}", self.root_win)
                    else:
                        StyledMessageBox.show_info("Dashboard", f"Welcome to the Dashboard, {self.current_user}! No profile image found.", self.root_win)
                else:
                    StyledMessageBox.show_info("Dashboard", "Welcome to the Dashboard! (No user logged in)", self.root_win)
                # For testing, we might close the app or show a simple message
                # self.root_win.destroy()

        def refresh_menu_elements(self): # Renamed from refresh_profile_button to match menu.py
            # Dashboard profile button refreshed
            # In a real app, this would trigger the menu bar to update
            # For testing, we can simulate the update
            if hasattr(self.root_win, 'menu_frame') and hasattr(self.root_win.menu_frame, 'update_profile_display'):
                self.root_win.menu_frame.update_profile_display()

        def reload_path_manager_config(self): # MODIFIED: Added mock reload_path_manager_config
            # MockController: reload_path_manager_config called
            self.path_manager.load_paths() # Simulate reloading paths
            login_frame.refresh_accounts_display() # Trigger refresh in login frame

        def quit(self):
            self.root_win.destroy()

    mock_path_manager = MockPathManager() # Instantiate mock path manager
    controller = MockController(root, mock_path_manager) # Pass mock path manager to controller
    login_frame = LoginFrame(root, controller, mock_path_manager) # MODIFIED: Pass path_manager to LoginFrame
    login_frame.pack(expand=True, fill="both")

    # Clean up test directories from previous runs
    if mock_path_manager.test_root.exists():
        shutil.rmtree(mock_path_manager.test_root)
    mock_path_manager.test_root.mkdir(parents=True, exist_ok=True) # Recreate clean test root

    # Ensure the default accounts directory is set up for testing
    accounts_test_path = login_frame.path_manager.get_path("accounts")
    accounts_test_path.mkdir(parents=True, exist_ok=True) # Ensure it exists

    # This part simulates the menu being created and having the update_profile_display method
    # In your actual main.py, you would create the menu bar and assign its update method
    from menu import menu
    menu_bar_frame = menu(root, controller)
    menu_bar_frame.pack(side="top", fill="x")
    root.menu_frame = menu_bar_frame # Store reference for mock controller

    # Initial refresh of the menu after the app starts and a user might be implicitly logged in
    # (e.g., if you have a remember me feature, or just to initialize the "Guest" state correctly)
    if hasattr(controller, 'refresh_menu_elements'):
        controller.refresh_menu_elements()

    root.mainloop()

