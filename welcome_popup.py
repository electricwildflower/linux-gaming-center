#!/usr/bin/env python3
"""
Linux Gaming Center - Welcome Popup
Displays a welcome message for first-time users
"""

import tkinter as tk
from pathlib import Path
import json

# Try to import PIL for image handling
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from theme_manager import get_app_root
from path_helper import get_user_account_dir


class WelcomePopup:
    """Welcome popup window for first-time users"""
    
    def __init__(self, parent, theme, scaler, username, on_close_callback=None):
        """
        Initialize the welcome popup
        
        Args:
            parent: Parent Tkinter window
            theme: Theme manager instance
            scaler: Screen scaler instance
            username: Username to display in welcome message
            on_close_callback: Optional callback function called when popup closes
        """
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        self.username = username
        self.on_close_callback = on_close_callback
        self.popup = None
        self.dont_show_var = None
    
    def show(self):
        """Show the welcome popup"""
        self.popup = tk.Toplevel(self.parent)
        self.popup.title("Welcome to Linux Gaming Center")
        
        # Scale popup size (larger base dimensions for better visibility)
        popup_width = self.scaler.scale_dimension(900)
        popup_height = self.scaler.scale_dimension(650)
        self.popup.resizable(False, False)
        
        # Center the popup on primary monitor (where main window is)
        self.popup.transient(self.parent)
        self.popup.grab_set()
        
        # Use scaler to center on primary monitor with our calculated dimensions
        x, y = self.scaler.center_on_primary_monitor(popup_width, popup_height)
        self.popup.geometry(f'{popup_width}x{popup_height}+{x}+{y}')
        
        # Update to ensure geometry is applied
        self.popup.update_idletasks()
        
        # Theme colors
        bg_color = self.theme.get_color("background_secondary", "#1A1A1A")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        purple_color = self.theme.get_color("primary", "#9D4EDD")
        
        self.popup.configure(bg=bg_color)
        
        # Welcome title with username
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        welcome_text = f"Welcome {self.username} to Linux Gaming Center" if self.username else "Welcome to Linux Gaming Center"
        title_label = tk.Label(
            self.popup,
            text=welcome_text,
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=(self.scaler.scale_padding(30), self.scaler.scale_padding(30)))
        
        # Content frame for bullet points and logo
        content_frame = tk.Frame(self.popup, bg=bg_color)
        content_frame.pack(pady=(0, self.scaler.scale_padding(30)), padx=self.scaler.scale_padding(30), fill=tk.BOTH, expand=True)
        
        # Left side - Bullet point list
        left_frame = tk.Frame(content_frame, bg=bg_color)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, self.scaler.scale_padding(20)))
        
        body_font = self.theme.get_font("body", scaler=self.scaler)
        bullet_points = [
            "Play your favourite open source games",
            "Play your favourite emulators & Roms",
            "Open your favourite apps and Windows Games",
            "Visit settings for configurations",
            "Choose custom themes and locations to store your data",
            "Visit the store for plugins and apps"
        ]
        
        for point in bullet_points:
            bullet_label = tk.Label(
                left_frame,
                text=f"• {point}",
                font=body_font,
                bg=bg_color,
                fg=text_secondary,
                anchor="w",
                justify=tk.LEFT
            )
            bullet_label.pack(anchor="w", pady=(0, self.scaler.scale_padding(10)))
        
        # Right side - Logo image
        right_frame = tk.Frame(content_frame, bg=bg_color)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        app_root = get_app_root()
        logo_path = app_root / "data" / "themes" / "cosmic-twilight" / "images" / "linuxgamingcenterdialogue.png"
        
        if logo_path.exists() and PIL_AVAILABLE:
            try:
                logo_image = Image.open(logo_path)
                # Resize logo to fit nicely (keeping aspect ratio, scaled - larger for bigger popup)
                max_width = self.scaler.scale_dimension(400)
                max_height = self.scaler.scale_dimension(400)
                logo_image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                logo_photo = ImageTk.PhotoImage(logo_image)
                
                logo_label = tk.Label(
                    right_frame,
                    image=logo_photo,
                    bg=bg_color
                )
                logo_label.image = logo_photo  # Keep reference
                logo_label.pack(anchor=tk.CENTER)
            except Exception as e:
                print(f"Error loading welcome logo: {e}")
        
        # Checkbox frame
        checkbox_frame = tk.Frame(self.popup, bg=bg_color)
        checkbox_frame.pack(pady=(0, self.scaler.scale_padding(30)))
        
        self.dont_show_var = tk.BooleanVar()
        checkbox_font = self.theme.get_font("body_small", scaler=self.scaler)
        checkbox = tk.Checkbutton(
            checkbox_frame,
            text="Don't show this message again",
            font=checkbox_font,
            bg=bg_color,
            fg=text_secondary,
            selectcolor=bg_color,
            activebackground=bg_color,
            activeforeground=text_secondary,
            variable=self.dont_show_var,
            cursor="hand2",
            highlightthickness=0,
            highlightbackground=bg_color,
            highlightcolor=bg_color
        )
        checkbox.pack()
        
        # Close button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        close_button = tk.Button(
            self.popup,
            text="Close",
            font=button_font,
            width=self.scaler.scale_dimension(15),
            height=self.scaler.scale_dimension(2),
            command=self.close,
            bg=purple_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0
        )
        close_button.pack(pady=(0, self.scaler.scale_padding(30)))
    
    def close(self):
        """Close welcome popup and save preference"""
        if self.popup:
            dont_show_again = self.dont_show_var.get() if self.dont_show_var else False
            self.popup.destroy()
            
            if dont_show_again and self.username:
                # Save preference to account file
                account_dir = get_user_account_dir(self.username)
                account_file = account_dir / "account.json"
                
                if account_file.exists():
                    try:
                        with open(account_file, 'r') as f:
                            account_data = json.load(f)
                        
                        account_data['show_welcome_popup'] = False
                        
                        with open(account_file, 'w') as f:
                            json.dump(account_data, f, indent=2)
                    except Exception as e:
                        print(f"Error saving welcome preference: {e}")
            
            # Call callback if provided
            if self.on_close_callback:
                self.on_close_callback()



