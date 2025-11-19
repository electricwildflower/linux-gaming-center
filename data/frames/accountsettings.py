# frames/accountsettings.py
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import shutil
import hashlib
from PIL import Image, ImageDraw
try:
    from PIL import ImageTk
except ImportError:
    # Fallback for systems where ImageTk is not available
    import tkinter as tk
    class ImageTk:
        @staticmethod
        def PhotoImage(image):
            return tk.PhotoImage()
from pathlib import Path # Import Path for modern path handling

from paths import PathManager # Import PathManager

class AccountSettingsFrame(tk.Frame):
    def __init__(self, parent, controller, path_manager: PathManager): # MODIFIED: Add path_manager argument
        super().__init__(parent)
        self.controller = controller
        self.path_manager = path_manager # STORED: path_manager instance
        self.account_data = None
        self.profile_image = None
        
        # Configure frame
        self.configure(bg="#0a0a12")
        
        # Main container
        container = tk.Frame(self, bg="#0a0a12")
        container.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Title
        tk.Label(
            container,
            text="ACCOUNT SETTINGS",
            font=("Impact", 24),
            fg="#9a32cd",
            bg="#0a0a12"
        ).pack(pady=(0, 20))
        
        # Profile Picture Section
        self.profile_frame = tk.LabelFrame(
            container,
            text="PROFILE PICTURE",
            fg="white",
            bg="#1a1a2e",
            font=("Arial", 12, "bold")
        )
        self.profile_frame.pack(fill="x", pady=10)
        
        # Profile image display
        self.profile_label = tk.Label(self.profile_frame, bg="#1a1a2e")
        self.profile_label.pack(pady=10)
        
        # Change photo button
        tk.Button(
            self.profile_frame,
            text="CHANGE PROFILE PHOTO",
            command=self.change_profile_photo,
            bg="#333344",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat"
        ).pack(pady=10)
        
        # Username Section
        self.username_frame = tk.LabelFrame(
            container,
            text="USERNAME",
            fg="white",
            bg="#1a1a2e",
            font=("Arial", 12, "bold")
        )
        self.username_frame.pack(fill="x", pady=10)
        
        # Current username display
        tk.Label(
            self.username_frame,
            text="Current:",
            fg="white",
            bg="#1a1a2e"
        ).pack()
        
        self.current_username_label = tk.Label(
            self.username_frame,
            text="",
            fg="#9a32cd",
            bg="#1a1a2e",
            font=("Arial", 12, "bold")
        )
        self.current_username_label.pack()
        
        # New username entry
        tk.Label(
            self.username_frame,
            text="New Username:",
            fg="white",
            bg="#1a1a2e"
        ).pack(pady=(10, 0))
        
        self.new_username_entry = tk.Entry(self.username_frame, bg="#2a2a3e", fg="white")
        self.new_username_entry.pack(fill="x", padx=10, pady=5)
        
        # Change username button
        tk.Button(
            self.username_frame,
            text="CHANGE USERNAME",
            command=self.change_username,
            bg="#333344",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat"
        ).pack(pady=10)
        
        # Password Section
        self.password_frame = tk.LabelFrame(
            container,
            text="PASSWORD",
            fg="white",
            bg="#1a1a2e",
            font=("Arial", 12, "bold")
        )
        self.password_frame.pack(fill="x", pady=10)
        
        # Current password
        tk.Label(
            self.password_frame,
            text="Current Password:",
            fg="white",
            bg="#1a1a2e"
        ).pack()
        
        self.current_password_entry = tk.Entry(
            self.password_frame,
            show="*",
            bg="#2a2a3e",
            fg="white"
        )
        self.current_password_entry.pack(fill="x", padx=10, pady=5)
        
        # New password
        tk.Label(
            self.password_frame,
            text="New Password:",
            fg="white",
            bg="#1a1a2e"
        ).pack()
        
        self.new_password_entry = tk.Entry(
            self.password_frame,
            show="*",
            bg="#2a2a3e",
            fg="white"
        )
        self.new_password_entry.pack(fill="x", padx=10, pady=5)
        
        # Confirm password
        tk.Label(
            self.password_frame,
            text="Confirm Password:",
            fg="white",
            bg="#1a1a2e"
        ).pack()
        
        self.confirm_password_entry = tk.Entry(
            self.password_frame,
            show="*",
            bg="#2a2a3e",
            fg="white"
        )
        self.confirm_password_entry.pack(fill="x", padx=10, pady=5)
        
        # Change password button
        tk.Button(
            self.password_frame,
            text="CHANGE PASSWORD",
            command=self.change_password,
            bg="#333344",
            fg="white",
            font=("Arial", 10, "bold"),
            relief="flat"
        ).pack(pady=10)
        

    def on_show_frame(self):
        """
        Called when this frame is brought to the front.
        Refreshes user data and display.
        """
        self.refresh_user()

    def refresh_user(self):
        """Refresh with current user from controller"""
        if hasattr(self.controller, 'current_user') and self.controller.current_user:
            self.load_account_data(self.controller.current_user)
            self.update_display()
        else:
            self.current_username_label.config(text="Not logged in")
            self.show_default_profile()
    
    def load_account_data(self, username):
        """Load account data from JSON file"""
        if not username:
            self.account_data = None # Ensure account_data is cleared if no user
            return
            
        # MODIFIED: Use path_manager to get the accounts directory
        accounts_base_dir = self.path_manager.get_path("accounts")
        account_dir = accounts_base_dir / username # Use Path object concatenation
        json_path = account_dir / "account.json" # Use Path object concatenation
        
        # Initialize default account data if file doesn't exist
        if not json_path.exists(): # MODIFIED: Use Path.exists()
            self.account_data = {
                "username": username,
                "password": "", # This should ideally be hashed if it's a new account
                "profile_image": None,
                "first_login": False
            }
            # Optionally, save this initial data if it's truly a new account being set up here
            # For existing accounts, this path means the account.json is missing/corrupt
            return
            
        try:
            with open(json_path, "r") as f:
                self.account_data = json.load(f)
            # Ensure username in JSON matches folder name (important after rename)
            if self.account_data.get("username") != username:
                self.account_data["username"] = username
                # Don't save here, save_account_data will handle it after full changes
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load account data for {username}: {e}")
            self.account_data = { # Fallback to default if loading fails
                "username": username,
                "password": "",
                "profile_image": None,
                "first_login": False
            }
    
    def update_display(self):
        """Update the UI with current account data"""
        if not self.account_data: # Check if account_data is loaded
            self.current_username_label.config(text="Not logged in")
            self.show_default_profile()
            return
        
        # Update username display
        self.current_username_label.config(text=self.account_data.get("username", "Unknown User"))
        
        # Load and display profile picture
        self.load_profile_picture()
    
    def load_profile_picture(self):
        """Load and display the profile picture"""
        if not self.account_data:
            self.show_default_profile()
            return
            
        # MODIFIED: Use path_manager to get the accounts directory
        accounts_base_dir = self.path_manager.get_path("accounts")
        account_dir = accounts_base_dir / self.account_data.get("username") # Use username from account_data
        profile_image_name = self.account_data.get("profile_image")
        
        if not profile_image_name:
            self.show_default_profile()
            return
            
        image_path = account_dir / profile_image_name # Use Path object concatenation

        if not image_path.exists(): # MODIFIED: Use Path.exists()
            print(f"Profile image not found at expected path: {image_path}. Showing default.")
            self.show_default_profile()
            return
            
        try:
            # Load and resize image
            img = Image.open(image_path)
            img = img.resize((150, 150), Image.LANCZOS)
            
            # Convert to PhotoImage and keep reference
            self.profile_image = ImageTk.PhotoImage(img)
            self.profile_label.config(image=self.profile_image)
        except Exception as e:
            print(f"Error loading profile image from {image_path}: {e}")
            self.show_default_profile()
    
    def show_default_profile(self):
        """Show default profile picture"""
        # Create a simple colored circle
        img = Image.new('RGB', (150, 150), "#1a1a2e")
        draw = ImageDraw.Draw(img)
        draw.ellipse((10, 10, 140, 140), fill="#9a32cd")
        
        # Add initial if username exists
        current_display_username = self.account_data.get("username") if self.account_data else "Guest"
        if current_display_username and current_display_username != "Guest":
            try:
                # Calculate font size based on image size for better scaling
                font_size = 60
                # Use a Tkinter font object for text drawing to ensure it's available
                from tkinter import font as tkFont
                fnt = tkFont.Font(family="Arial", size=font_size, weight="bold")
                
                # Get text bounding box to center it
                text_width = fnt.measure(current_display_username[0].upper())
                text_height = fnt.metrics('linespace') # Get line height for vertical centering
                
                x = (150 - text_width) / 2
                y = (150 - text_height) / 2
                
                draw.text((x, y), current_display_username[0].upper(), 
                         fill="white", font=fnt) # Use font object here
            except Exception as e:
                print(f"Error drawing default profile initial: {e}")
        
        self.profile_image = ImageTk.PhotoImage(img)
        self.profile_label.config(image=self.profile_image)
    
    def change_profile_photo(self):
        """Handle changing profile photo"""
        if not hasattr(self.controller, 'current_user') or not self.controller.current_user:
            messagebox.showerror("Error", "Please login first")
            return
        
        # Ensure account data is loaded
        if not self.account_data or self.account_data.get("username") != self.controller.current_user:
            self.load_account_data(self.controller.current_user)
            if not self.account_data:
                messagebox.showerror("Error", "Failed to load account data")
                return

        file_path = filedialog.askopenfilename(
            title="Select Profile Photo",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        
        if not file_path:
            return
            
        try:
            # MODIFIED: Use path_manager to get the accounts directory
            accounts_base_dir = self.path_manager.get_path("accounts")
            account_dir = accounts_base_dir / self.controller.current_user # Use Path object concatenation
            account_dir.mkdir(parents=True, exist_ok=True) # MODIFIED: Use Path.mkdir()
            
            # Remove old photo if exists
            if self.account_data.get("profile_image"):
                old_photo_name = self.account_data["profile_image"]
                old_path = account_dir / old_photo_name # Use Path object concatenation
                if old_path.exists(): # MODIFIED: Use Path.exists()
                    old_path.unlink() # MODIFIED: Use Path.unlink() to remove file
            
            # Copy new photo
            filename = Path(file_path).name # MODIFIED: Use Path.name
            new_path = account_dir / filename # Use Path object concatenation
            shutil.copy(file_path, new_path)
            
            # Update account data
            self.account_data["profile_image"] = filename
            
            # Ensure we have required fields (defensive programming)
            if "password" not in self.account_data: self.account_data["password"] = ""
            if "first_login" not in self.account_data: self.account_data["first_login"] = False
            if "username" not in self.account_data: self.account_data["username"] = self.controller.current_user # Ensure username is present

            if self.save_account_data():
                self.load_profile_picture()
                # Refresh all relevant UI components
                if hasattr(self.controller, 'refresh_menu_elements'):
                    self.controller.refresh_menu_elements() # Refresh menu bar
                # The login_frame and switchuser_frame references might be indirect.
                # It's safer to call a method on the controller that then calls the frame's method.
                if hasattr(self.controller, 'frames') and "LoginFrame" in self.controller.frames:
                    self.controller.frames["LoginFrame"]._load_existing_profiles() # Refresh login screen profiles
                if hasattr(self.controller, 'frames') and "SwitchuserFrame" in self.controller.frames:
                    self.controller.frames["SwitchuserFrame"].load_profiles() # Refresh switch user profiles
                
                messagebox.showinfo("Success", "Profile photo updated!")
            else:
                messagebox.showerror("Error", "Failed to save profile photo")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update photo: {str(e)}")
    
    def change_username(self):
        """Handle username change"""
        if not hasattr(self.controller, 'current_user') or not self.controller.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        old_username = self.controller.current_user
        new_username = self.new_username_entry.get().strip()
        
        if not new_username:
            messagebox.showerror("Error", "Please enter a new username")
            return
            
        if new_username == old_username:
            messagebox.showerror("Error", "New username same as current")
            return
            
        # Check if new username already exists as a directory
        # MODIFIED: Use path_manager to get the accounts directory
        accounts_base_dir = self.path_manager.get_path("accounts")
        old_account_dir = accounts_base_dir / old_username # Use Path object concatenation
        new_account_dir = accounts_base_dir / new_username # Use Path object concatenation
        
        if new_account_dir.exists(): # MODIFIED: Use Path.exists()
            messagebox.showerror("Error", "Username already exists. Please choose a different one.")
            return
        
        if not old_account_dir.exists(): # MODIFIED: Use Path.exists()
            messagebox.showerror("Error", f"Old account directory not found for {old_username}.")
            return

        try:
            # Step 1: Rename the directory
            old_account_dir.rename(new_account_dir) # MODIFIED: Use Path.rename()
            print(f"Renamed directory from {old_account_dir} to {new_account_dir}")
            
            # Step 2: Update account.json with new username
            json_path = new_account_dir / "account.json" # Use Path object concatenation
            if json_path.exists(): # MODIFIED: Use Path.exists()
                with open(json_path, "r") as f:
                    account_data = json.load(f)
                account_data["username"] = new_username
                with open(json_path, "w") as f:
                    json.dump(account_data, f, indent=4)
                print(f"Updated account.json in {new_account_dir} with new username.")
            else:
                messagebox.showwarning("Warning", "account.json not found in new directory. Creating a new one.")
                self.account_data["username"] = new_username # Ensure internal data is consistent
                self.save_account_data() # Create new account.json if missing

            # Step 3: Update controller's current_user
            self.controller.set_current_user(new_username)
            print(f"Controller's current user updated to {new_username}.")

            # Step 4: Update UI elements in AccountSettingsFrame
            self.current_username_label.config(text=new_username)
            self.new_username_entry.delete(0, tk.END)
            
            # Step 5: Reload account data with the new username
            self.load_account_data(new_username)
            self.update_display() # Refresh profile picture and other displays

            # Step 6: Trigger refresh in other relevant frames
            if hasattr(self.controller, 'refresh_menu_elements'):
                self.controller.refresh_menu_elements() # Refresh menu bar
            # MODIFIED: Use controller.frames for accessing other frames
            if hasattr(self.controller, 'frames') and "LoginFrame" in self.controller.frames:
                self.controller.frames["LoginFrame"]._load_existing_profiles() # Refresh login screen profiles
            if hasattr(self.controller, 'frames') and "SwitchuserFrame" in self.controller.frames:
                self.controller.frames["SwitchuserFrame"].load_profiles() # Refresh switch user profiles
            # You might need to refresh other frames that display the username/profile picture
            # e.g., dashboard_frame if it shows the current user's name/pic
            if hasattr(self.controller, 'frames') and "DashboardFrame" in self.controller.frames and \
               hasattr(self.controller.frames["DashboardFrame"], 'refresh_user'):
                self.controller.frames["DashboardFrame"].refresh_user()
            
            messagebox.showinfo("Success", "Username changed successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to change username: {e}")
            # Attempt to revert directory name if an error occurred after renaming
            if new_account_dir.exists() and not old_account_dir.exists(): # MODIFIED: Use Path.exists()
                try:
                    new_account_dir.rename(old_account_dir) # MODIFIED: Use Path.rename()
                    print(f"Reverted directory rename due to error: {new_account_dir} -> {old_account_dir}")
                except Exception as revert_e:
                    print(f"Failed to revert directory rename: {revert_e}")
            # Revert controller's current_user if it was changed
            self.controller.set_current_user(old_username)
            self.refresh_user() # Refresh UI to old username
    
    def change_password(self):
        """Handle password change"""
        if not hasattr(self.controller, 'current_user') or not self.controller.current_user:
            messagebox.showerror("Error", "Please login first")
            return
            
        # Ensure account data is loaded
        if not self.account_data or self.account_data.get("username") != self.controller.current_user:
            self.load_account_data(self.controller.current_user)
            if not self.account_data:
                messagebox.showerror("Error", "Failed to load account data")
                return

        current = self.current_password_entry.get()
        new = self.new_password_entry.get()
        confirm = self.confirm_password_entry.get()
        
        if not current or not new or not confirm:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        # Verify current password
        if not self.verify_password(current):
            messagebox.showerror("Error", "Current password incorrect")
            return
            
        if new != confirm:
            messagebox.showerror("Error", "New passwords don't match")
            return
            
        # Update password
        self.account_data["password"] = hashlib.sha256(new.encode()).hexdigest()
        
        # Ensure all required fields exist before saving (defensive programming)
        if "username" not in self.account_data: self.account_data["username"] = self.controller.current_user
        if "profile_image" not in self.account_data: self.account_data["profile_image"] = None
        if "first_login" not in self.account_data: self.account_data["first_login"] = False
            
        if self.save_account_data():
            self.current_password_entry.delete(0, tk.END)
            self.new_password_entry.delete(0, tk.END)
            self.confirm_password_entry.delete(0, tk.END)
            messagebox.showinfo("Success", "Password changed successfully!")
        else:
            messagebox.showerror("Error", "Failed to save new password")
    
    def verify_password(self, password):
        """Verify password matches stored hash"""
        stored_hash = self.account_data.get("password")
        if not stored_hash:
            return False
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash
    
    def save_account_data(self):
        """Save account data to JSON file"""
        if not hasattr(self.controller, 'current_user') or not self.controller.current_user:
            messagebox.showerror("Error", "No current user to save data for.")
            return False
            
        # MODIFIED: Use path_manager to get the accounts directory
        accounts_base_dir = self.path_manager.get_path("accounts")
        account_dir = accounts_base_dir / self.controller.current_user # Use Path object concatenation
        account_dir.mkdir(parents=True, exist_ok=True) # MODIFIED: Use Path.mkdir()
        json_path = account_dir / "account.json" # Use Path object concatenation
        
        try:
            with open(json_path, "w") as f:
                json.dump(self.account_data, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save data: {e}")
            return False

if __name__ == "__main__":
    # This block is for testing the AccountSettingsFrame independently
    root = tk.Tk()
    root.title("Account Settings Test")
    root.geometry("800x600")

    # Create a dummy PathManager for testing purposes
    class MockPathManager:
        def __init__(self):
            self.test_root = Path.home() / ".test_linc_app_data_accountsettings"
            self.accounts_path = self.test_root / ".config" / "linux-gaming-center" / "accounts"
            self.accounts_path.mkdir(parents=True, exist_ok=True)

        def get_path(self, category: str) -> Path:
            if category == "accounts":
                return self.accounts_path
            return self.test_root / "mock_path" / category

        def load_paths(self):
            print("MockPathManager: load_paths called (simulating reload)")

        def is_global_custom_path_active(self) -> bool:
            return False

    # Create a dummy controller for testing purposes
    class MockController:
        def __init__(self, root_win, path_manager):
            self.root_win = root_win
            self.current_user = "test_user" # Simulate a logged-in user
            self.path_manager = path_manager # Store path_manager
            self.frames = { # Mock frames for inter-frame communication
                "LoginFrame": type("LoginFrame", (object,), {"_load_existing_profiles": lambda: print("Mock LoginFrame profiles loaded")})(),
                "SwitchuserFrame": type("SwitchuserFrame", (object,), {"load_profiles": lambda: print("Mock SwitchuserFrame profiles loaded")})(),
                "DashboardFrame": type("DashboardFrame", (object,), {"refresh_user": lambda: print("Mock DashboardFrame refreshed")})(),
            }

        def set_current_user(self, username):
            self.current_user = username
            print(f"MockController: Current user set to: {username}")

        def refresh_menu_elements(self):
            print("MockController: refresh_menu_elements called.")

        def show_frame(self, frame_name):
            print(f"MockController: show_frame called for {frame_name}.")

        def quit(self):
            self.root_win.destroy()

    mock_path_manager = MockPathManager()
    controller = MockController(root, mock_path_manager)

    # Clean up test directories from previous runs
    if mock_path_manager.test_root.exists():
        shutil.rmtree(mock_path_manager.test_root)
    mock_path_manager.test_root.mkdir(parents=True, exist_ok=True) # Recreate clean test root
    mock_path_manager.accounts_path.mkdir(parents=True, exist_ok=True) # Ensure accounts path exists

    # Create a dummy account for testing
    test_user_dir = mock_path_manager.accounts_path / controller.current_user
    test_user_dir.mkdir(exist_ok=True)
    test_account_data = {
        "username": controller.current_user,
        "password": hashlib.sha256("password123".encode()).hexdigest(),
        "profile_image": None,
        "is_admin": False,
        "first_login": False
    }
    with open(test_user_dir / "account.json", "w") as f:
        json.dump(test_account_data, f, indent=4)

    # Create a dummy profile image for testing
    dummy_image_path = test_user_dir / "dummy_profile.png"
    Image.new('RGB', (150, 150), color = 'red').save(dummy_image_path)
    test_account_data["profile_image"] = "dummy_profile.png"
    with open(test_user_dir / "account.json", "w") as f:
        json.dump(test_account_data, f, indent=4)


    account_settings_frame = AccountSettingsFrame(root, controller, mock_path_manager)
    account_settings_frame.pack(expand=True, fill="both")

    # Manually call on_show_frame to simulate navigation
    account_settings_frame.on_show_frame()

    root.mainloop()

    # Clean up after test
    if mock_path_manager.test_root.exists():
        shutil.rmtree(mock_path_manager.test_root)

