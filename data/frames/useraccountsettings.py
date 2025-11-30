#!/usr/bin/env python3
"""
Linux Gaming Center - User Account Settings Frame
User-facing account settings (separate from admin account settings)
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from pathlib import Path
import json
import hashlib
import shutil
import os
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from path_helper import get_user_account_dir, get_accounts_path

# Try to import PIL for image handling
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class UserAccountSettingsFrame:
    def __init__(self, parent, theme, scaler, username=None, dashboard=None):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        self.username = username
        self.dashboard = dashboard  # Reference to dashboard for updating profile
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        input_bg = self.theme.get_color("input_background", "#1A1A1A")
        input_text = self.theme.get_color("input_text", "#FFFFFF")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Account directory
        if username:
            self.account_dir = get_user_account_dir(username)
            self.account_file = self.account_dir / "account.json"
        else:
            self.account_dir = None
            self.account_file = None
        
        # Scrollable canvas for content (no visible scrollbar)
        self.canvas = tk.Canvas(self.frame, bg=bg_color, highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_scroll_region(event=None):
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=bbox)
            # Update canvas window width to match canvas
            if event:
                canvas_width = event.width
                if canvas_width > 0:
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            else:
                self.canvas.update_idletasks()
                canvas_width = self.canvas.winfo_width()
                if canvas_width > 1:
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        self.canvas.bind("<Configure>", configure_scroll_region)
        
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            if event.delta:
                scroll_amount = int(-1 * (event.delta / 120))
                self.canvas.yview_scroll(scroll_amount, "units")
            return "break"
        
        def scroll_up(e):
            self.canvas.yview_scroll(-3, "units")
            return "break"
        
        def scroll_down(e):
            self.canvas.yview_scroll(3, "units")
            return "break"
        
        # Store scroll functions for binding to child widgets
        self._on_mousewheel = on_mousewheel
        self._scroll_up = scroll_up
        self._scroll_down = scroll_down
        
        # Bind to canvas and scrollable frame
        self.canvas.bind("<MouseWheel>", on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        self.canvas.bind("<Button-4>", scroll_up)
        self.canvas.bind("<Button-5>", scroll_down)
        self.scrollable_frame.bind("<Button-4>", scroll_up)
        self.scrollable_frame.bind("<Button-5>", scroll_down)
        
        # Bind mouse wheel to the main frame as well
        self.frame.bind("<MouseWheel>", on_mousewheel)
        self.frame.bind("<Button-4>", scroll_up)
        self.frame.bind("<Button-5>", scroll_down)
        
        # Arrow key scrolling
        def on_arrow_key(event):
            if event.keysym == "Up":
                if self.canvas.yview()[0] > 0.0:
                    self.canvas.yview_scroll(-3, "units")
            elif event.keysym == "Down":
                if self.canvas.yview()[1] < 1.0:
                    self.canvas.yview_scroll(3, "units")
            elif event.keysym == "Page_Up":
                self.canvas.yview_scroll(-1, "page")
            elif event.keysym == "Page_Down":
                self.canvas.yview_scroll(1, "page")
            elif event.keysym == "Home":
                self.canvas.yview_moveto(0)
            elif event.keysym == "End":
                self.canvas.yview_moveto(1)
            return "break"
        
        self.frame.bind("<KeyPress>", on_arrow_key)
        self.canvas.bind("<KeyPress>", on_arrow_key)
        self.scrollable_frame.bind("<KeyPress>", on_arrow_key)
        
        self.frame.focus_set()
        self.canvas.focus_set()
        
        # Title
        heading_font = self.theme.get_font("heading", scaler=self.scaler)
        title_label = tk.Label(
            self.scrollable_frame,
            text="Account Settings",
            font=heading_font,
            bg=bg_color,
            fg=text_color
        )
        title_label.pack(pady=self.scaler.scale_padding(30))
        
        # 1. Change Username Section
        self.create_change_username_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color, input_bg, input_text)
        
        # 2. Change Password Section
        self.create_change_password_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color, input_bg, input_text)
        
        # 3. Change Profile Picture Section
        self.create_change_profile_picture_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color)
        
        # Update canvas scroll region
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
        
        # Bind scroll events to all child widgets
        self.bind_scroll_to_children(self.scrollable_frame)
    
    def bind_scroll_to_children(self, widget):
        """Recursively bind scroll events to all child widgets"""
        # Bind mouse wheel events
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        widget.bind("<Button-4>", self._scroll_up, add="+")
        widget.bind("<Button-5>", self._scroll_down, add="+")
        
        # Recursively bind to all children
        for child in widget.winfo_children():
            self.bind_scroll_to_children(child)
    
    def create_change_username_section(self, parent, bg_color, text_color, text_secondary, primary_color, input_bg, input_text):
        """Create section for changing username"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        button_font = self.theme.get_font("button", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Change Username",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        form_frame = tk.Frame(section_frame, bg=bg_color)
        form_frame.pack(fill=tk.X)
        
        current_username_label = tk.Label(
            form_frame,
            text=f"Current username: {self.username}",
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        current_username_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        new_username_label = tk.Label(
            form_frame,
            text="New Username:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        new_username_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        new_username_var = tk.StringVar()
        new_username_entry = tk.Entry(
            form_frame,
            textvariable=new_username_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1
        )
        new_username_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(5))
        
        status_label = tk.Label(
            form_frame,
            text="",
            font=label_font,
            bg=bg_color,
            fg=self.theme.get_color("text_error", "#E74C3C")
        )
        status_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        def save_username():
            new_username = new_username_var.get().strip()
            
            if not new_username:
                status_label.config(text="Please enter a new username", fg=self.theme.get_color("text_error", "#E74C3C"))
                return
            
            if new_username == self.username:
                status_label.config(text="New username must be different from current username", fg=self.theme.get_color("text_error", "#E74C3C"))
                return
            
            # Check if new username already exists
            new_account_dir = get_user_account_dir(new_username)
            if new_account_dir.exists():
                status_label.config(text="Username already exists", fg=self.theme.get_color("text_error", "#E74C3C"))
                return
            
            try:
                # Load current account data
                if not self.account_file or not self.account_file.exists():
                    status_label.config(text="Account file not found", fg=self.theme.get_color("text_error", "#E74C3C"))
                    return
                
                with open(self.account_file, 'r') as f:
                    account_data = json.load(f)
                
                # Create new account directory
                new_account_dir.mkdir(parents=True, exist_ok=True)
                
                # Update username in account data
                account_data["username"] = new_username
                
                # Copy profile image if exists
                if "profile_image" in account_data:
                    old_profile_path = Path(account_data["profile_image"])
                    if old_profile_path.exists():
                        image_ext = old_profile_path.suffix
                        new_profile_path = new_account_dir / f"profile{image_ext}"
                        shutil.copy2(old_profile_path, new_profile_path)
                        account_data["profile_image"] = str(new_profile_path)
                
                # Save account data to new location
                new_account_file = new_account_dir / "account.json"
                with open(new_account_file, 'w') as f:
                    json.dump(account_data, f, indent=2)
                
                # Copy all files from old directory to new directory
                if self.account_dir.exists():
                    for item in self.account_dir.iterdir():
                        if item.name != "account.json":  # Already handled
                            if item.is_file():
                                shutil.copy2(item, new_account_dir / item.name)
                            elif item.is_dir():
                                shutil.copytree(item, new_account_dir / item.name, dirs_exist_ok=True)
                
                # Delete old account directory
                if self.account_dir.exists():
                    shutil.rmtree(self.account_dir)
                
                # Update username
                self.username = new_username
                self.account_dir = new_account_dir
                self.account_file = new_account_file
                
                # Update dashboard username and profile
                if self.dashboard:
                    self.dashboard.set_username(new_username)
                
                messagebox.showinfo("Success", f"Username changed to '{new_username}'. Please log out and log back in for changes to take full effect.")
                
                # Clear form
                new_username_var.set("")
                status_label.config(text="")
                current_username_label.config(text=f"Current username: {self.username}")
                
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}", fg=self.theme.get_color("text_error", "#E74C3C"))
                print(f"Error changing username: {e}")
        
        save_btn = tk.Button(
            form_frame,
            text="Change Username",
            font=button_font,
            command=save_username,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(20),
            pady=self.scaler.scale_padding(8)
        )
        save_btn.pack(pady=(self.scaler.scale_padding(10), 0))
    
    def create_change_password_section(self, parent, bg_color, text_color, text_secondary, primary_color, input_bg, input_text):
        """Create section for changing password"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        button_font = self.theme.get_font("button", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Change Password",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        form_frame = tk.Frame(section_frame, bg=bg_color)
        form_frame.pack(fill=tk.X)
        
        # Current password
        current_pass_label = tk.Label(
            form_frame,
            text="Current Password:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        current_pass_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        current_pass_var = tk.StringVar()
        current_pass_entry = tk.Entry(
            form_frame,
            textvariable=current_pass_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            show="*",
            relief=tk.SOLID,
            borderwidth=1
        )
        current_pass_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(5))
        
        # New password
        new_pass_label = tk.Label(
            form_frame,
            text="New Password:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        new_pass_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        new_pass_var = tk.StringVar()
        new_pass_entry = tk.Entry(
            form_frame,
            textvariable=new_pass_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            show="*",
            relief=tk.SOLID,
            borderwidth=1
        )
        new_pass_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(5))
        
        # Confirm new password
        confirm_pass_label = tk.Label(
            form_frame,
            text="Confirm New Password:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        confirm_pass_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        confirm_pass_var = tk.StringVar()
        confirm_pass_entry = tk.Entry(
            form_frame,
            textvariable=confirm_pass_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            show="*",
            relief=tk.SOLID,
            borderwidth=1
        )
        confirm_pass_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(5))
        
        status_label = tk.Label(
            form_frame,
            text="",
            font=label_font,
            bg=bg_color,
            fg=self.theme.get_color("text_error", "#E74C3C")
        )
        status_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        def save_password():
            current_pass = current_pass_var.get()
            new_pass = new_pass_var.get()
            confirm_pass = confirm_pass_var.get()
            
            if not current_pass:
                status_label.config(text="Please enter your current password", fg=self.theme.get_color("text_error", "#E74C3C"))
                return
            
            if not new_pass:
                status_label.config(text="Please enter a new password", fg=self.theme.get_color("text_error", "#E74C3C"))
                return
            
            if new_pass != confirm_pass:
                status_label.config(text="New passwords do not match", fg=self.theme.get_color("text_error", "#E74C3C"))
                return
            
            try:
                # Load account data
                if not self.account_file or not self.account_file.exists():
                    status_label.config(text="Account file not found", fg=self.theme.get_color("text_error", "#E74C3C"))
                    return
                
                with open(self.account_file, 'r') as f:
                    account_data = json.load(f)
                
                # Verify current password
                current_pass_hash = hashlib.sha256(current_pass.encode()).hexdigest()
                if account_data.get('password_hash') != current_pass_hash:
                    status_label.config(text="Current password is incorrect", fg=self.theme.get_color("text_error", "#E74C3C"))
                    return
                
                # Update password
                new_pass_hash = hashlib.sha256(new_pass.encode()).hexdigest()
                account_data['password_hash'] = new_pass_hash
                
                # Save account data
                with open(self.account_file, 'w') as f:
                    json.dump(account_data, f, indent=2)
                
                messagebox.showinfo("Success", "Password changed successfully!")
                
                # Clear form
                current_pass_var.set("")
                new_pass_var.set("")
                confirm_pass_var.set("")
                status_label.config(text="")
                
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}", fg=self.theme.get_color("text_error", "#E74C3C"))
                print(f"Error changing password: {e}")
        
        save_btn = tk.Button(
            form_frame,
            text="Change Password",
            font=button_font,
            command=save_password,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(20),
            pady=self.scaler.scale_padding(8)
        )
        save_btn.pack(pady=(self.scaler.scale_padding(10), 0))
    
    def create_change_profile_picture_section(self, parent, bg_color, text_color, text_secondary, primary_color):
        """Create section for changing profile picture"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        button_font = self.theme.get_font("button", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Change Profile Picture",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        form_frame = tk.Frame(section_frame, bg=bg_color)
        form_frame.pack(fill=tk.X)
        
        # Current profile picture display
        current_picture_frame = tk.Frame(form_frame, bg=bg_color)
        current_picture_frame.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)))
        
        current_picture_label = tk.Label(
            current_picture_frame,
            text="Current Profile Picture:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        current_picture_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        # Load and display current profile picture
        self.current_profile_image_label = None
        if self.account_file and self.account_file.exists():
            try:
                with open(self.account_file, 'r') as f:
                    account_data = json.load(f)
                profile_image_path = account_data.get('profile_image')
                
                # Check if stored path exists, if not try to find profile image in current account dir
                if not profile_image_path or not os.path.exists(profile_image_path):
                    # Look for profile image in the current account directory
                    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                        potential_path = self.account_dir / f"profile{ext}"
                        if potential_path.exists():
                            profile_image_path = str(potential_path)
                            # Update the account data with the correct path
                            account_data['profile_image'] = profile_image_path
                            with open(self.account_file, 'w') as f:
                                json.dump(account_data, f, indent=2)
                            break
                
                if profile_image_path and os.path.exists(profile_image_path) and PIL_AVAILABLE:
                    try:
                        image = Image.open(profile_image_path)
                        # Resize for display
                        display_size = self.scaler.scale_dimension(100)
                        image = image.resize((display_size, display_size), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        
                        self.current_profile_image_label = tk.Label(
                            current_picture_frame,
                            image=photo,
                            bg=bg_color
                        )
                        self.current_profile_image_label.image = photo  # Keep reference
                        self.current_profile_image_label.pack(pady=(0, self.scaler.scale_padding(10)))
                    except Exception as e:
                        print(f"Error loading current profile image: {e}")
            except:
                pass
        
        if not self.current_profile_image_label:
            no_image_label = tk.Label(
                current_picture_frame,
                text="No profile picture set",
                font=body_font,
                bg=bg_color,
                fg=text_secondary
            )
            no_image_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        # New profile picture selection
        self.new_profile_image_path = None
        
        image_selection_frame = tk.Frame(form_frame, bg=bg_color)
        image_selection_frame.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)))
        
        browse_btn = tk.Button(
            image_selection_frame,
            text="Browse for Image",
            font=button_font,
            command=self.browse_profile_image,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(20),
            pady=self.scaler.scale_padding(8)
        )
        browse_btn.pack(side=tk.LEFT)
        
        self.selected_image_label = tk.Label(
            image_selection_frame,
            text="No image selected",
            font=body_font,
            bg=bg_color,
            fg=text_secondary
        )
        self.selected_image_label.pack(side=tk.LEFT, padx=(self.scaler.scale_padding(15), 0))
        
        status_label = tk.Label(
            form_frame,
            text="",
            font=label_font,
            bg=bg_color,
            fg=self.theme.get_color("text_error", "#E74C3C")
        )
        status_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        def save_profile_picture():
            if not self.new_profile_image_path:
                status_label.config(text="Please select a new profile picture", fg=self.theme.get_color("text_error", "#E74C3C"))
                return
            
            try:
                # Load account data
                if not self.account_file or not self.account_file.exists():
                    status_label.config(text="Account file not found", fg=self.theme.get_color("text_error", "#E74C3C"))
                    return
                
                with open(self.account_file, 'r') as f:
                    account_data = json.load(f)
                
                # Delete old profile image if exists
                if "profile_image" in account_data:
                    old_profile_path = Path(account_data["profile_image"])
                    if old_profile_path.exists() and old_profile_path.parent == self.account_dir:
                        try:
                            old_profile_path.unlink()
                        except:
                            pass
                
                # Copy new image to account directory
                image_ext = os.path.splitext(self.new_profile_image_path)[1]
                new_profile_path = self.account_dir / f"profile{image_ext}"
                shutil.copy2(self.new_profile_image_path, new_profile_path)
                
                # Update account data
                account_data["profile_image"] = str(new_profile_path)
                
                # Save account data
                with open(self.account_file, 'w') as f:
                    json.dump(account_data, f, indent=2)
                
                messagebox.showinfo("Success", "Profile picture updated successfully!")
                
                # Update dashboard profile image
                if self.dashboard:
                    self.dashboard.load_profile_image()
                    self.dashboard.create_profile_section()
                
                # Clear selection
                self.new_profile_image_path = None
                self.selected_image_label.config(text="No image selected", fg=text_secondary)
                status_label.config(text="")
                
                # Reload current profile picture display
                if self.current_profile_image_label:
                    self.current_profile_image_label.destroy()
                
                if PIL_AVAILABLE:
                    try:
                        image = Image.open(new_profile_path)
                        display_size = self.scaler.scale_dimension(100)
                        image = image.resize((display_size, display_size), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(image)
                        
                        self.current_profile_image_label = tk.Label(
                            current_picture_frame,
                            image=photo,
                            bg=bg_color
                        )
                        self.current_profile_image_label.image = photo
                        self.current_profile_image_label.pack(pady=(0, self.scaler.scale_padding(10)))
                    except Exception as e:
                        print(f"Error loading new profile image: {e}")
                
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}", fg=self.theme.get_color("text_error", "#E74C3C"))
                print(f"Error changing profile picture: {e}")
        
        save_btn = tk.Button(
            form_frame,
            text="Save Profile Picture",
            font=button_font,
            command=save_profile_picture,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(20),
            pady=self.scaler.scale_padding(8)
        )
        save_btn.pack(pady=(self.scaler.scale_padding(10), 0))
    
    def browse_profile_image(self):
        """Browse for a new profile image"""
        file_path = filedialog.askopenfilename(
            parent=self.parent,
            title="Select Profile Picture",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.new_profile_image_path = file_path
            self.selected_image_label.config(text=os.path.basename(file_path), fg=self.theme.get_color("text_primary", "#FFFFFF"))
    
    def show(self):
        """Show the frame"""
        self.frame.pack(fill=tk.BOTH, expand=True)
    
    def hide(self):
        """Hide the frame"""
        self.frame.pack_forget()
    
    def destroy(self):
        """Destroy the panel"""
        self.frame.destroy()
