#!/usr/bin/env python3
"""
Linux Gaming Center - Main Application Entry Point
"""

import tkinter as tk
from pathlib import Path
import os
import sys

# Get absolute path to app root directory (linux-gaming-center)
APP_ROOT = Path(__file__).parent.absolute()

# Add the app root to the path so we can import our modules
sys.path.insert(0, str(APP_ROOT))

# Initialize theme manager and load default theme
from theme_manager import get_theme_manager
theme = get_theme_manager()

from screen_scaler import init_scaler
from login import LoginScreen, CreateAccountScreen, has_any_accounts
from dashboard import DashboardScreen


class LinuxGamingCenter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Linux Gaming Center")
        
        # Get theme manager
        self.theme = get_theme_manager()
        
        # Set background color from theme
        bg_color = self.theme.get_color("background", "#1A1A2E")
        self.root.configure(bg=bg_color)
        
        # Position window on primary monitor (0, 0) before making fullscreen
        # This ensures it opens on the primary monitor in multi-monitor setups
        primary_width = self.root.winfo_screenwidth()
        primary_height = self.root.winfo_screenheight()
        self.root.geometry(f"{primary_width}x{primary_height}+0+0")
        self.root.update_idletasks()
        
        # Initialize screen scaler (must be done after positioning)
        self.scaler = init_scaler(self.root)
        
        # Make window fullscreen (will stay on primary monitor)
        self.root.attributes('-fullscreen', True)
        
        # Set up escape key to exit fullscreen (optional)
        self.root.bind('<Escape>', self.toggle_fullscreen)
        self.root.bind('<F11>', self.toggle_fullscreen)
        
        # Get screen dimensions for centering (primary monitor)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Current user session
        self.current_user = None
        
        # Container frame for all screens
        self.container = tk.Frame(self.root, bg=bg_color)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Dictionary to store screen instances
        self.screens = {}
        
        # Initialize screens
        self.init_screens()
        
        # Check if any accounts exist - if not, show account creation screen
        if has_any_accounts():
            self.show_screen('login')
        else:
            # No accounts exist, show account creation screen
            self.show_screen('create_account')
    
    def init_screens(self):
        """Initialize all application screens"""
        self.screens['login'] = LoginScreen(
            self.container,
            self.on_login_success,
            self.show_create_account,
            self.exit_app,
            self.theme,
            self.scaler
        )
        self.screens['create_account'] = CreateAccountScreen(
            self.container,
            self.on_account_created,
            self.show_login,
            self.exit_app,
            self.theme,
            self.scaler
        )
        self.screens['dashboard'] = DashboardScreen(
            self.container,
            self.logout,
            self.exit_app,
            self.theme,
            self.scaler
        )
    
    def show_screen(self, screen_name):
        """Show a specific screen"""
        # Hide all screens
        for screen in self.screens.values():
            screen.hide()
        
        # Show the requested screen
        if screen_name in self.screens:
            self.screens[screen_name].show()
    
    def on_login_success(self, username):
        """Handle successful login"""
        self.current_user = username
        self.screens['dashboard'].set_username(username)
        self.show_screen('dashboard')
    
    def show_create_account(self):
        """Show account creation screen"""
        self.show_screen('create_account')
    
    def show_login(self):
        """Show login screen"""
        self.show_screen('login')
    
    def on_account_created(self, username):
        """Handle account creation - return to login screen"""
        self.show_screen('login')
        # Optionally show a message that account was created
        if hasattr(self.screens['login'], 'show_account_created_message'):
            self.screens['login'].show_account_created_message(username)
    
    def logout(self):
        """Handle logout - return to login screen"""
        self.current_user = None
        self.show_screen('login')
    
    def toggle_fullscreen(self, event=None):
        """Toggle fullscreen mode"""
        self.root.attributes('-fullscreen', 
                            not self.root.attributes('-fullscreen'))
    
    def exit_app(self):
        """Exit the application"""
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = LinuxGamingCenter()
    app.run()
