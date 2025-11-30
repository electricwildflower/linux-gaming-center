#!/usr/bin/env python3
"""
Linux Gaming Center - Screen Scaling Utility
Handles dynamic scaling of UI elements based on screen size
"""

import tkinter as tk


class ScreenScaler:
    """Handles dynamic scaling based on screen resolution"""
    
    # Reference resolution (1920x1080 - Full HD)
    REFERENCE_WIDTH = 1920
    REFERENCE_HEIGHT = 1080
    
    def __init__(self, root):
        self.root = root
        # Get primary monitor dimensions (the monitor where the root window is)
        # For multi-monitor setups, we use the root window's screen dimensions
        # which correspond to the monitor it's displayed on
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Get the root window's position to determine primary monitor
        # The primary monitor is typically at (0, 0) or where the root window is
        self.root_x = 0
        self.root_y = 0
        
        # Calculate scaling factors
        self.scale_x = self.screen_width / self.REFERENCE_WIDTH
        self.scale_y = self.screen_height / self.REFERENCE_HEIGHT
        
        # Use the smaller scale to maintain aspect ratio
        self.scale = min(self.scale_x, self.scale_y)
        
        # Clamp scale to reasonable bounds (0.5 to 2.0)
        self.scale = max(0.5, min(2.0, self.scale))
    
    def get_primary_monitor_position(self):
        """Get the position of the primary monitor (where the main window is)"""
        # Update root window position
        self.root.update_idletasks()
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        
        # In multi-monitor setups, the primary monitor is typically at (0, 0)
        # If the root window is at (0, 0) or negative, use (0, 0) as primary
        # Otherwise, use the root window's position
        if root_x <= 0 and root_y <= 0:
            return (0, 0)
        return (root_x, root_y)
    
    def center_on_primary_monitor(self, window_width, window_height):
        """Calculate x, y position to center a window on the primary monitor"""
        # Get primary monitor position (typically 0, 0)
        primary_x, primary_y = self.get_primary_monitor_position()
        
        # Calculate center position relative to primary monitor
        # Use the screen dimensions which should be the primary monitor's dimensions
        x = primary_x + (self.screen_width // 2) - (window_width // 2)
        y = primary_y + (self.screen_height // 2) - (window_height // 2)
        
        # Ensure window stays within primary monitor bounds (0 to screen_width/height)
        x = max(primary_x, min(x, primary_x + self.screen_width - window_width))
        y = max(primary_y, min(y, primary_y + self.screen_height - window_height))
        
        return (x, y)
    
    def scale_font_size(self, base_size):
        """Scale a font size based on screen size"""
        return int(base_size * self.scale)
    
    def scale_dimension(self, base_dimension):
        """Scale a dimension (width/height) based on screen size"""
        return int(base_dimension * self.scale)
    
    def scale_padding(self, base_padding):
        """Scale padding/spacing based on screen size"""
        return int(base_padding * self.scale)
    
    def get_font(self, family, base_size, style=""):
        """Get a scaled font tuple"""
        scaled_size = self.scale_font_size(base_size)
        if style:
            return (family, scaled_size, style)
        return (family, scaled_size)
    
    def get_screen_info(self):
        """Get screen information"""
        return {
            "width": self.screen_width,
            "height": self.screen_height,
            "scale": self.scale,
            "scale_x": self.scale_x,
            "scale_y": self.scale_y
        }


# Global scaler instance
_scaler = None


def get_scaler(root=None):
    """Get the global screen scaler instance"""
    global _scaler
    if _scaler is None and root is not None:
        _scaler = ScreenScaler(root)
    return _scaler


def init_scaler(root):
    """Initialize the screen scaler"""
    global _scaler
    _scaler = ScreenScaler(root)
    return _scaler

