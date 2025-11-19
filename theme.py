import json
import os
from pathlib import Path

class ThemeManager:
    """Centralized theme management for the Linux Gaming Center application."""
    
    def __init__(self, theme_name="cosmictwilight"):
        self.theme_name = theme_name
        self.theme_dir = Path("data") / "themes" / theme_name / "styles"
        self.config = self._load_theme_config()
    
    def _load_theme_config(self):
        """Load the main theme configuration."""
        config_file = self.theme_dir / "theme_config.json"
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Theme config file not found at {config_file}. Using defaults.")
            return self._get_default_config()
    
    def _get_default_config(self):
        """Return default theme configuration if config file is missing."""
        return {
            "colors": {
                "primary_background": "#1e1e1e",
                "secondary_background": "#2e2e2e",
                "accent_color": "#9a32cd",
                "text_primary": "#ffffff",
                "text_secondary": "#d4d4d4"
            },
            "fonts": {
                "primary_family": "Segoe UI",
                "base_size": 11
            }
        }
    
    def load_theme(self, frame_name):
        """Load theme for a specific frame, merging with base config."""
        frame_file = self.theme_dir / f"{frame_name}.json"
        
        # Start with base config
        theme = self.config.copy()
        
        # Load frame-specific overrides if they exist
        try:
            with open(frame_file, "r") as f:
                frame_theme = json.load(f)
                # Merge frame-specific theme with base config
                theme = self._merge_themes(theme, frame_theme)
        except FileNotFoundError:
            print(f"Info: No specific theme file for {frame_name}, using base theme.")
        
        return theme
    
    def _merge_themes(self, base_theme, frame_theme):
        """Recursively merge frame theme into base theme."""
        result = base_theme.copy()
        
        for key, value in frame_theme.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_themes(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_color(self, color_name):
        """Get a specific color from the theme."""
        return self.config.get("colors", {}).get(color_name, "#ffffff")
    
    def get_font(self, font_type="primary_family"):
        """Get a specific font from the theme."""
        return self.config.get("fonts", {}).get(font_type, "Segoe UI")
    
    def get_font_size(self, size_type="base_size"):
        """Get a specific font size from the theme."""
        return self.config.get("fonts", {}).get(size_type, 11)

# Global theme manager instance
_theme_manager = ThemeManager()

def load_theme(frame_name):
    """Legacy function for backward compatibility."""
    return _theme_manager.load_theme(frame_name)

def get_theme_manager():
    """Get the global theme manager instance."""
    return _theme_manager

