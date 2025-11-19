"""
Base frame class for Linux Gaming Center application.
Provides common functionality for all frame types.
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
from pathlib import Path
from theme import get_theme_manager


class BaseFrame(ttk.Frame):
    """Base class for all application frames."""
    
    def __init__(self, parent, controller, path_manager=None):
        super().__init__(parent)
        self.controller = controller
        self.path_manager = path_manager
        self.theme_manager = get_theme_manager()
        self.theme = self.load_theme()
        
        # Get responsive manager from controller
        self.responsive_manager = getattr(controller, 'responsive_manager', None)
        
        # Common properties
        self.icons = []
        self.widgets = []
        self.last_width = 0
        self.initial_load_complete = False
        self.current_menu = None
        
        # Scaling setup - use responsive manager if available
        if self.responsive_manager:
            self.scale = self.responsive_manager.scale
            self.BUTTON_WIDTH = self.responsive_manager.get_dimension('button_width')
            self.BUTTON_HEIGHT = self.responsive_manager.get_dimension('button_height')
            self.BUTTON_PADDING = self.responsive_manager.get_dimension('button_padding')
            self.FRAME_PADDING = self.responsive_manager.get_dimension('frame_padding')
            self.IMAGE_PADDING = self.responsive_manager.get_dimension('image_padding')
        else:
            # Fallback to original scaling
            self.screen_width = self.winfo_screenwidth()
            self.scale = self.screen_width / 1920
            self.scale = max(0.8, min(self.scale, 1.25))
            
            # Common dimensions
            self.BUTTON_WIDTH = int(200 * self.scale)
            self.BUTTON_HEIGHT = int(150 * self.scale)
            self.BUTTON_PADDING = int(20 * self.scale)
            self.FRAME_PADDING = int(20 * self.scale)
            self.IMAGE_PADDING = int(10 * self.scale)
        
        # Bind common events
        self.bind("<Visibility>", self.on_visibility_change)
        if hasattr(controller, 'bind'):
            self.controller.bind("<Configure>", self.on_main_window_configure)
    
    def load_theme(self):
        """Load theme for this frame. Override in subclasses for specific themes."""
        return self.theme_manager.load_theme(self.__class__.__name__.lower().replace('frame', ''))
    
    def configure_style(self):
        """Configure ttk styles based on theme. Override in subclasses."""
        style = ttk.Style()
        colors = self.theme.get("colors", {})
        fonts = self.theme.get("fonts", {})
        
        bg = colors.get("primary_background", "#1e1e1e")
        fg = colors.get("text_primary", "#ffffff")
        font_family = fonts.get("primary_family", "Segoe UI")
        
        # Use responsive font size if available
        if self.responsive_manager:
            font_size = self.responsive_manager.get_font_size('base')
        else:
            font_size = int(fonts.get("base_size", 11) * self.scale)
        
        # Base frame style
        frame_style = f"{self.__class__.__name__}.TFrame"
        style.configure(frame_style, background=bg)
        
        # Label style
        label_style = f"{self.__class__.__name__}.TLabel"
        style.configure(label_style, background=bg, foreground=fg, 
                       font=(font_family, font_size), anchor="center")
        
        # Button style
        button_style = f"{self.__class__.__name__}.TButton"
        style.configure(button_style, background=bg, foreground=fg,
                       font=(font_family, font_size + 1), padding=6)
        
        # Combobox style
        combobox_style = f"{self.__class__.__name__}.TCombobox"
        style.configure(combobox_style, background=bg, foreground=fg,
                       font=(font_family, font_size))
        
        # Sort label style
        sort_label_style = f"{self.__class__.__name__}.SortLabel.TLabel"
        style.configure(sort_label_style, background=bg, foreground=fg,
                       font=(font_family, font_size), anchor="w")
    
    def setup_ui(self):
        """Setup the UI. Override in subclasses."""
        pass
    
    def load_data(self):
        """Load data for this frame. Override in subclasses."""
        pass
    
    def on_visibility_change(self, event=None):
        """Handle frame becoming visible."""
        current_width = self.winfo_width()
        if current_width > 0 and current_width != self.last_width:
            self.last_width = current_width
            self.after(100, self.delayed_redraw)
    
    def on_main_window_configure(self, event=None):
        """Handle the main window's resize event."""
        current_width = self.winfo_width()
        if current_width > 0 and current_width != self.last_width:
            self.last_width = current_width
            self.after(100, self.delayed_redraw)
    
    def delayed_redraw(self):
        """Delayed call to force redraw."""
        self.force_redraw()
    
    def force_redraw(self):
        """Force a complete redraw. Override in subclasses."""
        try:
            # Update responsive dimensions if available
            if self.responsive_manager:
                # Recalculate dimensions based on current window size
                current_width = self.winfo_width()
                current_height = self.winfo_height()
                
                if current_width > 1 and current_height > 1:
                    # Update the responsive manager with current dimensions
                    self.responsive_manager.update_window_size(current_width, current_height)
            
            # Force update of all child widgets
            self.update_idletasks()
            self.update()
            
            # Call any custom redraw logic
            if hasattr(self, 'on_resize'):
                self.on_resize()
                
        except Exception as e:
            print(f"Error in force_redraw: {e}")
    
    def perform_initial_redraw(self):
        """Perform initial redraw after a delay."""
        self.initial_load_complete = True
        self.force_redraw()
    
    def bind_mousewheel_events(self, canvas):
        """Bind mouse wheel events for cross-platform compatibility."""
        canvas.bind_all("<MouseWheel>", lambda e: self.on_mousewheel(e, canvas))
        canvas.bind_all("<Button-4>", lambda e: self.on_mousewheel_scroll(-1, canvas))
        canvas.bind_all("<Button-5>", lambda e: self.on_mousewheel_scroll(1, canvas))
        canvas.bind("<Enter>", lambda e: canvas.focus_set())
    
    def on_mousewheel(self, event, canvas):
        """Handle mouse wheel scrolling on Windows/Mac."""
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_mousewheel_scroll(self, direction, canvas):
        """Handle mouse wheel scrolling on Linux."""
        canvas.yview_scroll(direction, "units")
    
    def resize_image_to_fit(self, img, target_width, target_height):
        """Resize image maintaining aspect ratio to fit within target dimensions."""
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if target_ratio > img_ratio:
            new_height = target_height
            new_width = int(img_ratio * new_height)
        else:
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def calculate_grid_layout(self, available_width):
        """Calculate optimal grid layout based on available width."""
        if available_width <= 0:
            return 1, 0
        
        # Use responsive manager if available
        if self.responsive_manager:
            return self.responsive_manager.calculate_grid_layout(available_width, self.BUTTON_WIDTH)
        else:
            # Fallback to original calculation
            min_item_width = self.BUTTON_WIDTH + self.BUTTON_PADDING
            max_columns = max(1, (available_width - 2 * self.FRAME_PADDING) // min_item_width)
            
            total_content_width = max_columns * min_item_width - self.BUTTON_PADDING
            remaining_space = max(0, available_width - total_content_width - 2 * self.FRAME_PADDING)
            extra_padding = remaining_space // (max_columns + 1)
            
            return max_columns, extra_padding
    
    def show_context_menu(self, event, index, menu_items):
        """Show a context menu with the given items."""
        if self.current_menu:
            self.current_menu.unpost()
        
        colors = self.theme.get("colors", {})
        bg = colors.get("primary_background", "#1e1e1e")
        fg = colors.get("text_primary", "#ffffff")
        
        menu = tk.Menu(self, tearoff=0, bg=bg, fg=fg)
        
        for label, command in menu_items:
            if label == "---":
                menu.add_separator()
            else:
                menu.add_command(label=label, command=command)
        
        self.current_menu = menu
        menu.tk_popup(event.x_root, event.y_root)
        
        if hasattr(self.controller, 'bind'):
            self.controller.bind("<Button-1>", self.close_context_menu, add="+")
    
    def close_context_menu(self, event=None):
        """Close the context menu if it's open."""
        if hasattr(self, "current_menu") and self.current_menu:
            self.current_menu.destroy()
            self.current_menu = None
        if hasattr(self.controller, 'unbind'):
            self.controller.unbind("<Button-1>")
    
    def on_show_frame(self):
        """Called when the frame is shown. Override in subclasses."""
        pass
    
    def on_visibility_change(self, event=None):
        """Handle frame becoming visible."""
        current_width = self.winfo_width()
        if current_width > 0 and current_width != self.last_width:
            self.last_width = current_width
            self.after(100, self.delayed_redraw)
