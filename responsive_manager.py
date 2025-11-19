"""
Responsive Design Manager for Linux Gaming Center
Handles scaling, layout, and responsive behavior across all screen sizes
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image
try:
    from PIL import ImageTk
except ImportError:
    # Fallback for systems where ImageTk is not available
    import tkinter as tk
    class ImageTk:
        @staticmethod
        def PhotoImage(image):
            return tk.PhotoImage()
import math


class ResponsiveManager:
    """Manages responsive design across the entire application."""
    
    def __init__(self, root_window):
        self.root = root_window
        self.screen_width = root_window.winfo_screenwidth()
        self.screen_height = root_window.winfo_screenheight()
        self.screen_dpi = root_window.winfo_fpixels('1i')
        
        # Current window dimensions (for windowed mode)
        self.window_width = self.screen_width
        self.window_height = self.screen_height
        
        # Calculate base scale factors - using 1280x720 as base resolution
        self.base_width = 1280
        self.base_height = 720
        self.base_dpi = 96
        
        # Calculate scale factors
        self.width_scale = self.screen_width / self.base_width
        self.height_scale = self.screen_height / self.base_height
        self.dpi_scale = self.screen_dpi / self.base_dpi
        
        # Use the most conservative scale to ensure everything fits
        self.scale = min(self.width_scale, self.height_scale, 1.5)  # Cap at 1.5x
        self.scale = max(self.scale, 0.6)  # Minimum 0.6x for very small screens
        
        # Callback for notifying frames of resize
        self.notify_frames_of_resize = None
        
        # Responsive breakpoints - adjusted for 1280x720 base
        self.breakpoints = {
            'xs': 640,    # Extra small (small laptops)
            'sm': 800,    # Small (tablets)
            'md': 1024,   # Medium (laptops)
            'lg': 1280,   # Large (base resolution)
            'xl': 1600,   # Extra large (desktops)
            'xxl': 1920   # Ultra wide
        }
        
        # Current breakpoint
        self.current_breakpoint = self.get_current_breakpoint()
        
        # Responsive dimensions
        self.dimensions = self.calculate_responsive_dimensions()
        
        # Bind to window events
        self.root.bind('<Configure>', self.on_window_configure)
        
    def get_current_breakpoint(self):
        """Get the current breakpoint based on screen width."""
        for breakpoint_name in ['xxl', 'xl', 'lg', 'md', 'sm', 'xs']:
            if self.screen_width >= self.breakpoints[breakpoint_name]:
                return breakpoint_name
        return 'xs'
    
    def calculate_responsive_dimensions(self):
        """Calculate responsive dimensions based on current screen size."""
        bp = self.current_breakpoint
        
        # Base dimensions (for xl breakpoint) - adjusted for 1280x720 base
        base_dims = {
            'button_width': 250,  # Proper media center button width like Emby/Jellyfin
            'button_height': 150, # 5:3 aspect ratio (250 * 0.6) - proper media center size
            'button_padding': 15, # Proper spacing between buttons
            'frame_padding': 15,  # Frame padding
            'image_padding': 0,   # No padding for full image coverage
            'font_size_base': 10, # Reduced from 11
            'font_size_large': 12, # Reduced from 14
            'font_size_small': 8,  # Reduced from 9
            'grid_spacing': 10,    # Proper grid spacing
            'menu_height': 35,     # Reduced from 40
            'logo_max_width': 300, # Reduced from 400
            'logo_max_height': 150, # Reduced from 200
            'progress_bar_height': 20,
            'recent_item_width': 120,  # Reduced from 160
            'recent_item_height': 110  # Reduced from 150
        }
        
        # Responsive multipliers based on breakpoint - optimized for 1280x720 base
        multipliers = {
            'xs': {'scale': 0.7, 'cols': 1, 'font_scale': 0.8},
            'sm': {'scale': 0.8, 'cols': 2, 'font_scale': 0.9},
            'md': {'scale': 0.9, 'cols': 3, 'font_scale': 0.95},
            'lg': {'scale': 1.0, 'cols': 4, 'font_scale': 1.0},
            'xl': {'scale': 1.1, 'cols': 4, 'font_scale': 1.0},
            'xxl': {'scale': 1.2, 'cols': 5, 'font_scale': 1.1}
        }
        
        mult = multipliers[bp]
        
        # Calculate responsive dimensions
        dims = {}
        for key, value in base_dims.items():
            if 'font' in key:
                dims[key] = int(value * mult['font_scale'] * self.scale)
            else:
                dims[key] = int(value * mult['scale'] * self.scale)
        
        # Add breakpoint-specific values
        dims['breakpoint'] = bp
        dims['max_columns'] = mult['cols']
        dims['scale_factor'] = self.scale
        
        return dims
    
    def update_window_size(self, width, height):
        """Update window dimensions and recalculate scaling."""
        self.window_width = width
        self.window_height = height
        
        # Update scale factors based on new window size
        self.width_scale = width / self.base_width
        self.height_scale = height / self.base_height
        
        # Recalculate scale
        self.scale = min(self.width_scale, self.height_scale, 1.5)
        self.scale = max(self.scale, 0.6)
        
        # Window resized
    
    def on_window_configure(self, event):
        """Handle window resize events."""
        if event.widget == self.root:
            # Update screen dimensions
            self.screen_width = self.root.winfo_width()
            self.screen_height = self.root.winfo_height()
            
            # Update breakpoint if changed
            new_breakpoint = self.get_current_breakpoint()
            if new_breakpoint != self.current_breakpoint:
                self.current_breakpoint = new_breakpoint
                self.dimensions = self.calculate_responsive_dimensions()
                
                # Notify all frames of the change (only if callback is set)
                if self.notify_frames_of_resize:
                    self.notify_frames_of_resize()
    
    def notify_frames_of_resize(self):
        """Notify all frames that they need to update their layout."""
        # This will be called by the main app to notify frames
        pass
    
    def get_dimension(self, key):
        """Get a responsive dimension value."""
        return self.dimensions.get(key, 0)
    
    def calculate_grid_layout(self, available_width, item_width=None):
        """Calculate optimal grid layout based on available width."""
        if available_width <= 0:
            return 1, 0
        
        if item_width is None:
            item_width = self.get_dimension('button_width')
        
        padding = self.get_dimension('button_padding')
        frame_padding = self.get_dimension('frame_padding')
        
        # Calculate how many items can fit
        min_item_width = item_width + padding
        max_columns = max(1, (available_width - 2 * frame_padding) // min_item_width)
        
        # Limit to maximum columns for current breakpoint
        max_columns = min(max_columns, self.get_dimension('max_columns'))
        
        # Calculate spacing
        total_content_width = max_columns * min_item_width - padding
        remaining_space = max(0, available_width - total_content_width - 2 * frame_padding)
        extra_padding = remaining_space // (max_columns + 1)
        
        return max_columns, extra_padding
    
    def resize_image_responsive(self, img, target_width, target_height, maintain_aspect=True):
        """Resize image responsively while maintaining aspect ratio."""
        if not maintain_aspect:
            return img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if target_ratio > img_ratio:
            # Image is taller than target, fit to height
            new_height = target_height
            new_width = int(img_ratio * new_height)
        else:
            # Image is wider than target, fit to width
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def get_font_size(self, size_type='base'):
        """Get responsive font size."""
        return self.get_dimension(f'font_size_{size_type}')
    
    def get_button_size(self):
        """Get responsive button dimensions."""
        return (
            self.get_dimension('button_width'),
            self.get_dimension('button_height')
        )
    
    def get_padding(self, padding_type='button'):
        """Get responsive padding."""
        return self.get_dimension(f'{padding_type}_padding')
    
    def is_mobile_size(self):
        """Check if current screen size is mobile-like."""
        return self.current_breakpoint in ['xs', 'sm']
    
    def is_desktop_size(self):
        """Check if current screen size is desktop-like."""
        return self.current_breakpoint in ['lg', 'xl', 'xxl']
    
    def get_logo_size(self, max_width=None, max_height=None):
        """Get responsive logo dimensions."""
        if max_width is None:
            max_width = self.get_dimension('logo_max_width')
        if max_height is None:
            max_height = self.get_dimension('logo_max_height')
        
        return max_width, max_height


class ResponsiveFrame(ttk.Frame):
    """Base frame class with responsive design capabilities."""
    
    def __init__(self, parent, controller, responsive_manager=None):
        super().__init__(parent)
        self.controller = controller
        self.responsive_manager = responsive_manager or getattr(controller, 'responsive_manager', None)
        
        if self.responsive_manager is None:
            # Create a default responsive manager if none provided
            self.responsive_manager = ResponsiveManager(parent.winfo_toplevel())
        
        # Responsive properties
        self.last_width = 0
        self.last_height = 0
        self.initial_load_complete = False
        
        # Bind resize events
        self.bind('<Configure>', self.on_frame_configure)
        
    def on_frame_configure(self, event):
        """Handle frame resize events."""
        if event.widget == self:
            current_width = self.winfo_width()
            current_height = self.winfo_height()
            
            # Only redraw if size actually changed
            if (current_width > 10 and current_height > 10 and 
                (current_width != self.last_width or current_height != self.last_height)):
                
                self.last_width = current_width
                self.last_height = current_height
                
                # Delay redraw to avoid excessive updates
                self.after(100, self.delayed_redraw)
    
    def delayed_redraw(self):
        """Delayed call to force redraw."""
        self.force_redraw()
    
    def force_redraw(self):
        """Force a complete redraw. Override in subclasses."""
        pass
    
    def get_responsive_dimension(self, key):
        """Get a responsive dimension value."""
        return self.responsive_manager.get_dimension(key)
    
    def calculate_grid_layout(self, available_width, item_width=None):
        """Calculate optimal grid layout."""
        return self.responsive_manager.calculate_grid_layout(available_width, item_width)
    
    def resize_image_responsive(self, img, target_width, target_height, maintain_aspect=True):
        """Resize image responsively."""
        return self.responsive_manager.resize_image_responsive(img, target_width, target_height, maintain_aspect)
