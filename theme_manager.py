#!/usr/bin/env python3
"""
Linux Gaming Center - Theme Manager
Handles loading and managing themes for the application
"""

import json
import os
from pathlib import Path


class ThemeManager:
    """Manages application themes"""
    
    def __init__(self):
        # Get the absolute path to the app root directory (linux-gaming-center)
        self.app_root = Path(__file__).parent.absolute()
        self.themes_dir = self.app_root / "data" / "themes"
        self.current_theme = None
        self.theme_data = {}
    
    def get_app_root(self):
        """Get the absolute path to the app root directory"""
        return self.app_root
    
    def get_themes_dir(self):
        """Get the absolute path to the themes directory"""
        return self.themes_dir
    
    def load_theme(self, theme_name="cosmic-twilight"):
        """Load a theme by name"""
        theme_dir = self.themes_dir / theme_name
        
        if not theme_dir.exists():
            raise FileNotFoundError(f"Theme '{theme_name}' not found in {self.themes_dir}")
        
        theme_file = theme_dir / "theme.json"
        
        if not theme_file.exists():
            raise FileNotFoundError(f"Theme file not found: {theme_file}")
        
        try:
            with open(theme_file, 'r') as f:
                self.theme_data = json.load(f)
            
            self.current_theme = theme_name
            return self.theme_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid theme JSON file: {e}")
        except Exception as e:
            raise Exception(f"Error loading theme: {e}")
    
    def get(self, key, default=None):
        """Get a theme value by key (supports dot notation like 'colors.primary')"""
        keys = key.split('.')
        value = self.theme_data
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value if value is not None else default
    
    def get_color(self, color_key, default="#000000"):
        """Get a color value from the theme"""
        return self.get(f"colors.{color_key}", default)
    
    def get_font(self, font_key, default=("Arial", 12), scaler=None):
        """Get a font tuple from the theme, optionally scaled"""
        font_data = self.get(f"fonts.{font_key}", None)
        if font_data:
            family = font_data.get("family", default[0])
            size = font_data.get("size", default[1] if len(default) > 1 else 12)
            style = font_data.get("style", "")
            
            # Apply scaling if scaler is provided
            if scaler:
                size = scaler.scale_font_size(size)
            
            # Build font tuple based on style
            if style and style.lower() in ["bold", "italic", "underline"]:
                return (family, size, style.lower())
            else:
                return (family, size)
        # Apply scaling to default if provided
        if scaler and isinstance(default, tuple) and len(default) > 1:
            scaled_default = (default[0], scaler.scale_font_size(default[1]))
            if len(default) > 2:
                return (*scaled_default, default[2])
            return scaled_default
        return default
    
    def list_themes(self):
        """List all available themes"""
        if not self.themes_dir.exists():
            return []
        
        themes = []
        for item in self.themes_dir.iterdir():
            if item.is_dir():
                theme_file = item / "theme.json"
                if theme_file.exists():
                    themes.append(item.name)
        
        return themes


# Global theme manager instance
_theme_manager = None


def get_theme_manager():
    """Get the global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
        # Load default theme
        try:
            _theme_manager.load_theme("cosmic-twilight")
        except Exception as e:
            print(f"Warning: Could not load default theme: {e}")
    return _theme_manager


def get_app_root():
    """Get the absolute path to the app root directory"""
    return get_theme_manager().get_app_root()

