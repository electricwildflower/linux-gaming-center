import tkinter as tk
from tkinter import ttk
import os
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

class LoadingFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#1e1e1e")  # Use your main app's background color
        self.controller = controller
        
        # Get responsive manager from controller
        self.responsive_manager = getattr(controller, 'responsive_manager', None)

        self.logo_label = None  # Declare as instance variables
        self.loading_label = None
        self.progress_bar = None
        self.progress_label = None
        self.status_label = None

        self.create_widgets()
        self.bind("<Configure>", self.on_resize)  # Bind the resize event

    def create_widgets(self):
        """Creates the widgets for the frame."""
        # Use PathManager if available, otherwise fallback to hardcoded path
        if hasattr(self.controller, 'path_manager'):
            themes_path = self.controller.path_manager.get_path("themes")
            logo_path = themes_path / "cosmictwilight" / "images" / "linuxgamingcenter.png"
        else:
            logo_path = Path("data") / "themes" / "cosmictwilight" / "images" / "linuxgamingcenter.png"

        try:
            logo_image_original = Image.open(logo_path)
            # Initial size, will be updated on resize
            self.logo_image_original = logo_image_original
            self.logo_image = ImageTk.PhotoImage(logo_image_original)
            self.logo_label = tk.Label(self, image=self.logo_image, bg="#1e1e1e")
            self.logo_label.pack(expand=True)
        except FileNotFoundError:
            self.logo_label = tk.Label(self, text="Linux Gaming Center", font=("Arial", 36), bg="#1e1e1e", fg="white")
            self.logo_label.pack(expand=True)

        # Loading text
        self.loading_label = tk.Label(self, text="Loading Linux Gaming Center...", font=("Arial", 14, "bold"), bg="#1e1e1e", fg="white")
        self.loading_label.pack(pady=20)
        
        # Progress label showing current/total
        self.progress_label = tk.Label(self, text="Initializing...", font=("Arial", 11), bg="#1e1e1e", fg="#ffffff")
        self.progress_label.pack(pady=10)
        
        # Status label showing current emulator being scanned
        self.status_label = tk.Label(self, text="Please wait while we load all ROMs and artwork...", font=("Arial", 9), bg="#1e1e1e", fg="#888888")
        self.status_label.pack(pady=5)
        
        # Create a frame to hold the progress bar at the bottom
        self.progress_frame = tk.Frame(self, bg="#1e1e1e")
        self.progress_frame.pack(side="bottom", fill="x", pady=20)
        
        # Custom progress bar using canvas - black bar that fills with purple
        progress_height = 30
        if self.responsive_manager:
            progress_height = max(30, self.responsive_manager.get_dimension('progress_bar_height'))
        
        self.progress_canvas = tk.Canvas(
            self.progress_frame, 
            height=progress_height, 
            bg="#000000",  # Black background
            highlightthickness=2,
            highlightbackground="#9a32cd",  # Purple border
            relief="flat"
        )
        self.progress_canvas.pack(fill="x", padx=50, pady=10)
        
        # Percentage label below progress bar
        self.percent_label = tk.Label(self.progress_frame, text="0%", font=("Arial", 10, "bold"), bg="#1e1e1e", fg="#9a32cd")
        self.percent_label.pack(pady=(5, 0))
        
        # Initialize progress variables
        self.progress_width = 0
        self.progress_percent = 0

    def on_resize(self, event):
        """Handles resizing of the frame."""
        width = event.width
        height = event.height

        # Use responsive manager if available
        if self.responsive_manager:
            logo_max_width, logo_max_height = self.responsive_manager.get_logo_size()
            # Scale based on window size
            logo_max_width = min(logo_max_width, int(width * 0.8))
            logo_max_height = min(logo_max_height, int(height * 0.6))
        else:
            # Fallback to original calculation
            logo_max_width = int(width * 0.8)  # 80% of window width
            logo_max_height = int(height * 0.6) # 60% of window height
        
        max_size = (logo_max_width, logo_max_height)

        if hasattr(self, 'logo_image_original'): #check if logo_image_original exists
            logo_image_resized = self.logo_image_original.copy()  # Create a copy to avoid modifying the original
            logo_image_resized.thumbnail(max_size, Image.LANCZOS)  # Use LANCZOS for high-quality resizing
            self.logo_image = ImageTk.PhotoImage(logo_image_resized)
            self.logo_label.config(image=self.logo_image)  # Update the label's image
        else:
            #update font size
            if width > 800:
                font_size = 36
            elif width > 600:
                font_size = 24
            else:
                font_size = 18
            self.logo_label.config(font=("Arial", font_size))

        #update loading label font size using responsive manager
        if self.responsive_manager:
            loading_font_size = self.responsive_manager.get_font_size('base')
        else:
            # Fallback to original calculation
            if width > 800:
                loading_font_size = 12
            elif width > 600:
                loading_font_size = 10
            else:
                loading_font_size = 8
        self.loading_label.config(font=("Arial", loading_font_size))
        
        # Redraw the progress bar when window is resized
        self.after(10, self._draw_progress_bar)

    def update_progress(self, current, total, current_emulator):
        """Update the progress bar and labels
        
        Args:
            current: Current progress (emulators scanned, images loaded, etc.)
            total: Total items (emulators, images, etc.)
            current_emulator: Status message describing what's being loaded
        """
        # Parse status message to determine phase
        if "Loading images" in current_emulator:
            # Image loading phase - parse progress from message like "Loading images: 100/1746"
            try:
                if ":" in current_emulator:
                    parts = current_emulator.split(":")
                    if len(parts) > 1:
                        progress_str = parts[1].strip()  # " 100/1746"
                        if "/" in progress_str:
                            img_current, img_total = progress_str.split("/")
                            img_current = int(img_current.strip())
                            img_total = int(img_total.strip())
                            # Calculate percentage: assume ROM scanning was 50% of total, images are 50%
                            # So images start at 50% and go to 100%
                            self.progress_percent = 50 + (img_current / img_total * 50) if img_total > 0 else 50
                            self.progress_label.config(text=f"Loading artwork: {img_current}/{img_total} images")
                            self.status_label.config(text="Preparing image cache...")
            except (ValueError, AttributeError):
                # Fallback if parsing fails
                self.progress_percent = min(100, (current / total * 100) if total > 0 else 0)
                self.progress_label.config(text=current_emulator)
                self.status_label.config(text="")
        elif "Loaded" in current_emulator and "images" in current_emulator:
            # Images complete
            self.progress_percent = 100
            self.progress_label.config(text="Loading complete!")
            self.status_label.config(text=current_emulator)
        elif total > 0:
            # ROM scanning phase - this is first 50% of progress
            self.progress_percent = (current / total * 50) if total > 0 else 0
            self.progress_label.config(text=f"Scanning ROMs: {current}/{total} emulators")
            self.status_label.config(text=f"Current: {current_emulator}")
        else:
            self.progress_percent = 0
            self.progress_label.config(text="Preparing to load ROMs and artwork...")
            self.status_label.config(text="")
        
        # Update the custom progress bar
        self._draw_progress_bar()
        
        # Force update of the display
        self.update_idletasks()
    
    def _draw_progress_bar(self):
        """Draw the custom progress bar on the canvas"""
        # Clear the canvas
        self.progress_canvas.delete("all")
        
        # Get canvas dimensions
        canvas_width = self.progress_canvas.winfo_width()
        canvas_height = self.progress_canvas.winfo_height()
        
        # Only draw if canvas has been rendered (has dimensions)
        if canvas_width > 1 and canvas_height > 1:
            # Calculate the width of the purple fill
            fill_width = (self.progress_percent / 100) * canvas_width
            
            # Draw the purple progress fill from left to right
            if fill_width > 0:
                self.progress_canvas.create_rectangle(
                    0, 0, fill_width, canvas_height,
                    fill="#9a32cd",  # Purple color
                    outline=""
                )
            
            # Update percentage label
            self.percent_label.config(text=f"{int(self.progress_percent)}%")
    
    def hide_progress(self):
        """Hide progress elements when scanning is complete"""
        self.progress_frame.pack_forget()
        self.progress_label.pack_forget()
        self.status_label.pack_forget()
        self.loading_label.config(text="Loading complete!")
    
    def on_show(self):
        """This method can be empty for the loading screen, or you could start an animation here."""
        pass

