#!/usr/bin/env python3
"""
Linux Gaming Center - Login Screen
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import json
import hashlib
import shutil
import os
from path_helper import get_accounts_path, get_config_file_path, get_user_account_dir

# Try to import PIL for image handling (optional)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def has_any_accounts():
    """Check if any accounts exist in the accounts directory"""
    accounts_dir = get_accounts_path()
    
    if not accounts_dir.exists():
        return False
    
    # Check if there are any subdirectories (accounts)
    try:
        subdirs = [d for d in accounts_dir.iterdir() if d.is_dir()]
        return len(subdirs) > 0
    except Exception:
        return False


class LoginScreen:
    def __init__(self, parent, on_login_success, on_create_account, on_exit, theme, scaler):
        self.parent = parent
        self.on_login_success = on_login_success
        self.on_create_account = on_create_account
        self.on_exit = on_exit
        self.theme = theme
        self.scaler = scaler
        
        # Steam-like colors
        bg_color = self.theme.get_color("background", "#1A1A2E")
        panel_bg = self.theme.get_color("background_secondary", "#16213E")  # Darker panel
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#B0BEC5")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Main container for centering
        main_container = tk.Frame(self.frame, bg=bg_color)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Login panel (Steam-style centered box)
        login_panel = tk.Frame(main_container, bg=panel_bg, relief=tk.FLAT)
        login_panel.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        login_panel.config(borderwidth=0, highlightthickness=0)
        
        # Title/Logo area (with extra top padding to avoid X button)
        from theme_manager import get_app_root
        app_root = get_app_root()
        logo_path = app_root / "data" / "themes" / "cosmic-twilight" / "images" / "linuxgamingcenter.png"
        
        title_label = None
        if logo_path.exists() and PIL_AVAILABLE:
            try:
                logo_image = Image.open(logo_path)
                # Resize logo to reasonable size (keeping aspect ratio)
                # Calculate size to fit nicely in the login panel (scaled)
                max_width = self.scaler.scale_dimension(600)
                max_height = self.scaler.scale_dimension(150)
                logo_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_image)
                
                title_label = tk.Label(
                    login_panel,
                    image=logo_photo,
                    bg=panel_bg
                )
                title_label.image = logo_photo  # Keep reference
                title_label.pack(pady=(50, 10))
            except Exception as e:
                print(f"Error loading logo: {e}")
                # Fallback to text
                title_font = self.theme.get_font("heading", scaler=self.scaler)
                title_label = tk.Label(
                    login_panel,
                    text="Linux Gaming Center",
                    font=title_font,
                    bg=panel_bg,
                    fg=text_color
                )
                title_label.pack(pady=(self.scaler.scale_padding(50), self.scaler.scale_padding(10)))
        else:
            # Fallback to text if image not available
            title_font = self.theme.get_font("heading", scaler=self.scaler)
            title_label = tk.Label(
                login_panel,
                text="Linux Gaming Center",
                font=title_font,
                bg=panel_bg,
                fg=text_color
            )
            title_label.pack(pady=(self.scaler.scale_padding(50), self.scaler.scale_padding(10)))
        
        subtitle_font = self.theme.get_font("body_small", scaler=self.scaler)
        subtitle_label = tk.Label(
            login_panel,
            text="Sign in to your account",
            font=subtitle_font,
            bg=panel_bg,
            fg=text_secondary
        )
        subtitle_label.pack(pady=(0, self.scaler.scale_padding(40)))
        
        # Form container
        form_frame = tk.Frame(login_panel, bg=panel_bg)
        form_frame.pack(padx=self.scaler.scale_padding(40), pady=self.scaler.scale_padding(20))
        
        # Username field
        label_font = self.theme.get_font("body_small", scaler=self.scaler)
        username_label = tk.Label(
            form_frame,
            text="Username",
            font=label_font,
            bg=panel_bg,
            fg=text_secondary,
            anchor="w"
        )
        username_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        input_bg = self.theme.get_color("input_background", "#FFFFFF")
        input_text = self.theme.get_color("input_text", "#000000")
        input_border = self.theme.get_color("input_border", "#B0BEC5")
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        self.username_entry = tk.Entry(
            form_frame,
            font=body_font,
            width=self.scaler.scale_dimension(30),
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=input_border,
            highlightcolor=self.theme.get_color("primary", "#4CAF50")
        )
        self.username_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)), ipady=self.scaler.scale_padding(8))
        
        # Password field
        password_label = tk.Label(
            form_frame,
            text="Password",
            font=label_font,
            bg=panel_bg,
            fg=text_secondary,
            anchor="w"
        )
        password_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        self.password_entry = tk.Entry(
            form_frame,
            font=body_font,
            width=self.scaler.scale_dimension(30),
            show="*",
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=input_border,
            highlightcolor=self.theme.get_color("primary", "#4CAF50")
        )
        self.password_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(8))
        
        # Remember me checkbox (Steam-style)
        checkbox_frame = tk.Frame(form_frame, bg=panel_bg)
        checkbox_frame.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(25)))
        
        self.remember_var = tk.BooleanVar()
        remember_checkbox = tk.Checkbutton(
            checkbox_frame,
            text="Remember me",
            font=label_font,
            bg=panel_bg,
            fg=text_secondary,
            selectcolor=panel_bg,
            activebackground=panel_bg,
            activeforeground=text_secondary,
            variable=self.remember_var,
            cursor="hand2",
            highlightthickness=0,
            highlightbackground=panel_bg,
            highlightcolor=panel_bg
        )
        remember_checkbox.pack(side=tk.LEFT)
        
        # Status label (for errors)
        error_color = self.theme.get_color("text_error", "#E74C3C")
        self.status_label = tk.Label(
            form_frame,
            text="",
            font=label_font,
            bg=panel_bg,
            fg=error_color,
            wraplength=self.scaler.scale_dimension(300)
        )
        self.status_label.pack(pady=(0, self.scaler.scale_padding(20)))
        
        # Login button (large, prominent)
        button_font = self.theme.get_font("button", scaler=self.scaler)
        primary_color = self.theme.get_color("primary", "#4CAF50")
        login_button = tk.Button(
            form_frame,
            text="Sign In",
            font=button_font,
            width=self.scaler.scale_dimension(30),
            height=self.scaler.scale_dimension(2),
            command=self.login,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            activebackground=self.theme.get_color("primary_hover", "#45a049")
        )
        login_button.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(5))
        
        # Divider line
        divider = tk.Frame(form_frame, bg=self.theme.get_color("border", "#34495E"), height=1)
        divider.pack(fill=tk.X, pady=(self.scaler.scale_padding(10), self.scaler.scale_padding(15)))
        
        # Create account link (Steam-style, less prominent) - only show if enabled
        self.create_frame = tk.Frame(form_frame, bg=panel_bg)
        self.create_frame.pack(fill=tk.X)
        
        self.create_label = tk.Label(
            self.create_frame,
            text="Don't have an account?",
            font=label_font,
            bg=panel_bg,
            fg=text_secondary
        )
        self.create_label.pack(side=tk.LEFT)
        
        self.create_link = tk.Label(
            self.create_frame,
            text="Create Account",
            font=label_font,
            bg=panel_bg,
            fg=self.theme.get_color("secondary", "#2196F3"),
            cursor="hand2"
        )
        self.create_link.pack(side=tk.LEFT, padx=(5, 0))
        self.create_link.bind("<Button-1>", lambda e: self.create_account())
        
        # Check if account creation is enabled
        self.update_account_creation_visibility()
        
        # Exit button (small, top-right corner) - purple
        purple_color = self.theme.get_color("primary", "#9D4EDD")
        exit_font = self.scaler.get_font("Arial", 16)
        exit_button = tk.Button(
            login_panel,
            text="✕",
            font=exit_font,
            command=self.exit_app,
            bg=panel_bg,
            fg=purple_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            activebackground=self.theme.get_color("primary_hover", "#7B2CBF"),
            activeforeground=text_color,
            width=self.scaler.scale_dimension(3),
            height=self.scaler.scale_dimension(1)
        )
        exit_button.place(relx=1.0, rely=0.0, anchor="ne", x=-self.scaler.scale_padding(10), y=self.scaler.scale_padding(10))
        
        # Bind Enter key to login
        self.password_entry.bind('<Return>', lambda e: self.login())
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
    
    def login(self):
        """Handle login attempt"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        error_color = self.theme.get_color("text_error", "#E74C3C")
        
        if not username or not password:
            self.status_label.config(text="Please enter both username and password", fg=error_color)
            return
        
        if self.verify_credentials(username, password):
            self.status_label.config(text="", fg=error_color)
            self.on_login_success(username)
        else:
            self.status_label.config(text="Invalid username or password", fg=error_color)
            self.password_entry.delete(0, tk.END)
    
    def verify_credentials(self, username, password):
        """Verify username and password"""
        account_dir = get_user_account_dir(username)
        
        if not account_dir.exists():
            return False
        
        account_file = account_dir / "account.json"
        if not account_file.exists():
            return False
        
        try:
            with open(account_file, 'r') as f:
                account_data = json.load(f)
            
            # Check if account is locked
            if account_data.get('locked', False):
                self.status_label.config(text="This account is locked by admin", fg=self.theme.get_color("text_error", "#E74C3C"))
                return False
            
            # Hash the provided password and compare
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            return account_data.get('password_hash') == password_hash
        except Exception as e:
            print(f"Error verifying credentials: {e}")
            return False
    
    def create_account(self):
        """Open create account screen"""
        self.on_create_account()
    
    def exit_app(self):
        """Exit the application"""
        self.on_exit()
    
    def show_account_created_message(self, username):
        """Show message that account was created"""
        success_color = self.theme.get_color("text_success", "#4CAF50")
        self.status_label.config(
            text=f"Account '{username}' created successfully! Please login.",
            fg=success_color
        )
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
    
    def get_account_creation_enabled(self):
        """Check if account creation is enabled"""
        config_file = get_config_file_path("config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                return config.get("allow_account_creation", True)  # Default to True
            except:
                return True
        return True
    
    def update_account_creation_visibility(self):
        """Update visibility of account creation link based on setting"""
        if hasattr(self, 'create_frame'):
            if self.get_account_creation_enabled():
                self.create_frame.pack(fill=tk.X)
            else:
                self.create_frame.pack_forget()
    
    def show(self):
        """Show the login screen"""
        self.frame.pack(fill=tk.BOTH, expand=True)
        # Update account creation visibility when shown
        self.update_account_creation_visibility()
        self.username_entry.focus()
        # Clear status message
        error_color = self.theme.get_color("text_error", "#E74C3C")
        self.status_label.config(text="", fg=error_color)
    
    def hide(self):
        """Hide the login screen"""
        self.frame.pack_forget()
        error_color = self.theme.get_color("text_error", "#E74C3C")
        self.status_label.config(text="", fg=error_color)


class CreateAccountScreen:
    def __init__(self, parent, on_account_created, on_cancel, on_exit, theme, scaler):
        self.parent = parent
        self.on_account_created = on_account_created
        self.on_cancel = on_cancel
        self.on_exit = on_exit
        self.theme = theme
        self.scaler = scaler
        self.profile_image_path = None
        
        bg_color = self.theme.get_color("background", "#1A1A2E")
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Center content
        self.center_frame = tk.Frame(self.frame, bg=bg_color)
        self.center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Check if this is the first account
        self.is_first_account = not has_any_accounts()
        
        # Create UI
        self.create_ui()
    
    def create_ui(self):
        """Create the UI elements"""
        bg_color = self.theme.get_color("background", "#1A1A2E")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        input_bg = self.theme.get_color("input_background", "#FFFFFF")
        input_text = self.theme.get_color("input_text", "#000000")
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            self.center_frame,
            text="Create New Account",
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        # Account type notice label (will be updated dynamically)
        notice_font = self.theme.get_font("notice", scaler=self.scaler)
        accent_color = self.theme.get_color("accent", "#FF9800")
        self.account_type_notice = tk.Label(
            self.center_frame,
            text="",
            font=notice_font,
            bg=bg_color,
            fg=accent_color
        )
        self.account_type_notice.pack(pady=(0, self.scaler.scale_padding(30)))
        self.update_account_type_notice()
        
        # Username field
        label_font = self.theme.get_font("label", scaler=self.scaler)
        username_label = tk.Label(
            self.center_frame,
            text="Username:",
            font=label_font,
            bg=bg_color,
            fg=text_color
        )
        username_label.pack(pady=(0, self.scaler.scale_padding(5)))
        
        self.username_entry = tk.Entry(
            self.center_frame,
            font=label_font,
            width=self.scaler.scale_dimension(25),
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text
        )
        self.username_entry.pack(pady=(0, self.scaler.scale_padding(20)))
        
        # Password field
        password_label = tk.Label(
            self.center_frame,
            text="Password:",
            font=label_font,
            bg=bg_color,
            fg=text_color
        )
        password_label.pack(pady=(0, self.scaler.scale_padding(5)))
        
        self.password_entry = tk.Entry(
            self.center_frame,
            font=label_font,
            width=self.scaler.scale_dimension(25),
            show="*",
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text
        )
        self.password_entry.pack(pady=(0, self.scaler.scale_padding(20)))
        
        # Confirm Password field
        confirm_password_label = tk.Label(
            self.center_frame,
            text="Confirm Password:",
            font=label_font,
            bg=bg_color,
            fg=text_color
        )
        confirm_password_label.pack(pady=(0, self.scaler.scale_padding(5)))
        
        self.confirm_password_entry = tk.Entry(
            self.center_frame,
            font=label_font,
            width=self.scaler.scale_dimension(25),
            show="*",
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text
        )
        self.confirm_password_entry.pack(pady=(0, self.scaler.scale_padding(20)))
        
        # Profile Image section
        profile_label = tk.Label(
            self.center_frame,
            text="Profile Image:",
            font=label_font,
            bg=bg_color,
            fg=text_color
        )
        profile_label.pack(pady=(0, self.scaler.scale_padding(5)))
        
        profile_frame = tk.Frame(self.center_frame, bg=bg_color)
        profile_frame.pack(pady=(0, self.scaler.scale_padding(20)))
        
        muted_color = self.theme.get_color("text_muted", "#757575")
        body_small_font = self.theme.get_font("body_small", scaler=self.scaler)
        self.profile_image_label = tk.Label(
            profile_frame,
            text="No image selected",
            font=body_small_font,
            bg=bg_color,
            fg=muted_color
        )
        self.profile_image_label.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(10)))
        
        browse_button = tk.Button(
            profile_frame,
            text="Browse",
            font=body_small_font,
            command=self.browse_image,
            bg=muted_color,
            fg=text_color
        )
        browse_button.pack(side=tk.LEFT)
        
        # Create button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        primary_color = self.theme.get_color("primary", "#4CAF50")
        create_button = tk.Button(
            self.center_frame,
            text="Create Account",
            font=button_font,
            width=self.scaler.scale_dimension(20),
            height=self.scaler.scale_dimension(2),
            command=self.create_account,
            bg=primary_color,
            fg=text_color,
            cursor="hand2"
        )
        create_button.pack(pady=(self.scaler.scale_padding(20), self.scaler.scale_padding(15)))
        
        # Cancel button - only show if not creating first account
        self.cancel_button = tk.Button(
            self.center_frame,
            text="Cancel",
            font=button_font,
            width=self.scaler.scale_dimension(20),
            height=self.scaler.scale_dimension(2),
            command=self.cancel,
            bg=muted_color,
            fg=text_color,
            cursor="hand2"
        )
        
        # Hide cancel button if this is the first account (required)
        if not self.is_first_account:
            self.cancel_button.pack()
        
        # Status label
        error_color = self.theme.get_color("text_error", "#E74C3C")
        self.status_label = tk.Label(
            self.center_frame,
            text="",
            font=body_small_font,
            bg=bg_color,
            fg=error_color
        )
        self.status_label.pack(pady=(self.scaler.scale_padding(20), 0))
        
        # Exit button - only show for first account creation
        if self.is_first_account:
            exit_frame = tk.Frame(self.center_frame, bg=bg_color)
            exit_frame.pack(pady=(self.scaler.scale_padding(30), 0))
            
            exit_label = tk.Label(
                exit_frame,
                text="Don't want to create an account?",
                font=body_small_font,
                bg=bg_color,
                fg=text_color
            )
            exit_label.pack()
            
            exit_button = tk.Button(
                exit_frame,
                text="✕ Exit Application",
                font=button_font,
                command=self.exit_app,
                bg=error_color,
                fg="#FFFFFF",
                cursor="hand2",
                relief=tk.FLAT,
                padx=self.scaler.scale_padding(15),
                pady=self.scaler.scale_padding(5)
            )
            exit_button.pack(pady=(self.scaler.scale_padding(10), 0))
        
        # Focus on username entry
        self.username_entry.focus()
    
    def browse_image(self):
        """Browse for profile image"""
        # Get the root window to ensure dialog opens on primary monitor
        root_window = self.parent.winfo_toplevel()
        file_path = filedialog.askopenfilename(
            parent=root_window,  # Explicitly set parent to ensure dialog on primary monitor
            title="Select Profile Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.profile_image_path = file_path
            filename = os.path.basename(file_path)
            text_color = self.theme.get_color("text_dark", "#000000")
            self.profile_image_label.config(text=filename, fg=text_color)
    
    def create_account(self):
        """Create the account"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        error_color = self.theme.get_color("text_error", "#E74C3C")
        
        # Validation
        if not username:
            self.status_label.config(text="Please enter a username", fg=error_color)
            return
        
        if not password:
            self.status_label.config(text="Please enter a password", fg=error_color)
            return
        
        if password != confirm_password:
            self.status_label.config(text="Passwords do not match", fg=error_color)
            return
        
        if len(password) < 4:
            self.status_label.config(text="Password must be at least 4 characters", fg=error_color)
            return
        
        # Check if account already exists
        account_dir = get_user_account_dir(username)
        if account_dir.exists():
            self.status_label.config(text="Username already exists", fg=error_color)
            return
        
        try:
            # Check if this is the first account (administrator) or a basic account
            is_first_account = not has_any_accounts()
            account_type = "administrator" if is_first_account else "basic"
            
            # Create account directory
            account_dir.mkdir(parents=True, exist_ok=True)
            
            # Hash password
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Copy profile image if selected
            profile_image_path = None
            if self.profile_image_path:
                image_ext = os.path.splitext(self.profile_image_path)[1]
                profile_image_dest = account_dir / f"profile{image_ext}"
                shutil.copy2(self.profile_image_path, profile_image_dest)
                profile_image_path = str(profile_image_dest)
            
            # Save account data
            account_data = {
                "username": username,
                "password_hash": password_hash,
                "account_type": account_type
            }
            
            if profile_image_path:
                account_data["profile_image"] = profile_image_path
            
            account_file = account_dir / "account.json"
            with open(account_file, 'w') as f:
                json.dump(account_data, f, indent=2)
            
            # Clear fields
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.confirm_password_entry.delete(0, tk.END)
            self.profile_image_path = None
            muted_color = self.theme.get_color("text_muted", "#757575")
            self.profile_image_label.config(text="No image selected", fg=muted_color)
            
            # Show success message and return to login
            success_color = self.theme.get_color("text_success", "#4CAF50")
            self.status_label.config(
                text=f"Account '{username}' created successfully!",
                fg=success_color
            )
            self.frame.after(1500, lambda: self.on_account_created(username))
            
        except Exception as e:
            error_color = self.theme.get_color("text_error", "#E74C3C")
            self.status_label.config(text=f"Error: {str(e)}", fg=error_color)
    
    def exit_app(self):
        """Exit the application without creating an account"""
        if self.on_exit:
            self.on_exit()
    
    def cancel(self):
        """Cancel account creation and return to login"""
        self.on_cancel()
    
    def update_account_type_notice(self):
        """Update the account type notice label"""
        bg_color = self.theme.get_color("background", "#1A1A2E")
        notice_font = self.theme.get_font("notice", scaler=self.scaler)
        notice_small_font = self.theme.get_font("notice_small", scaler=self.scaler)
        accent_color = self.theme.get_color("accent", "#FF9800")
        muted_color = self.theme.get_color("text_muted", "#757575")
        
        if self.is_first_account:
            self.account_type_notice.config(
                text="This will be the Administrator account",
                font=notice_font,
                bg=bg_color,
                fg=accent_color
            )
        else:
            self.account_type_notice.config(
                text="This will be a Basic account",
                font=notice_small_font,
                bg=bg_color,
                fg=muted_color
            )
    
    def show(self):
        """Show the create account screen"""
        # Re-check if this is the first account (in case accounts were created)
        self.is_first_account = not has_any_accounts()
        
        # Update account type notice
        self.update_account_type_notice()
        
        # Update cancel button visibility based on whether it's the first account
        if self.is_first_account:
            # Hide cancel button for first account
            self.cancel_button.pack_forget()
        else:
            # Show cancel button for subsequent accounts
            self.cancel_button.pack()
        
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.username_entry.focus()
        error_color = self.theme.get_color("text_error", "#E74C3C")
        self.status_label.config(text="", fg=error_color)
    
    def hide(self):
        """Hide the create account screen"""
        self.frame.pack_forget()
        # Clear fields when hiding
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        self.confirm_password_entry.delete(0, tk.END)
        self.profile_image_path = None
        muted_color = self.theme.get_color("text_muted", "#757575")
        error_color = self.theme.get_color("text_error", "#E74C3C")
        self.profile_image_label.config(text="No image selected", fg=muted_color)
        self.status_label.config(text="", fg=error_color)
