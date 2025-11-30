#!/usr/bin/env python3
"""
Linux Gaming Center - Account Settings Panel
"""

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import json
import hashlib
import shutil


class AccountSettingsPanel:
    def __init__(self, parent, theme, scaler):
        self.parent = parent
        self.theme = theme
        self.scaler = scaler
        
        bg_color = self.theme.get_color("background", "#000000")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        input_bg = self.theme.get_color("input_background", "#1A1A1A")
        input_text = self.theme.get_color("input_text", "#FFFFFF")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        menu_bar_color = self.theme.get_color("menu_bar", "#2D2D2D")
        
        self.frame = tk.Frame(parent, bg=bg_color)
        # Use grid to fill parent completely
        self.frame.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        # Configure frame to fill parent
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Accounts directory
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from path_helper import get_accounts_path, get_config_file_path
        self.accounts_dir = get_accounts_path()
        self.config_file = get_config_file_path("config.json")
        
        # Scrollable canvas for content (no visible scrollbar) - fills entire frame
        self.canvas = tk.Canvas(self.frame, bg=bg_color, highlightthickness=0)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        def configure_scroll_region(event=None):
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            if bbox:
                self.canvas.configure(scrollregion=bbox)
            # Always update canvas window width to match canvas
            canvas_width = event.width if event else self.canvas.winfo_width()
            if canvas_width > 1:
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
            # Also update on initial load
            if not event:
                self.canvas.update_idletasks()
                canvas_width = self.canvas.winfo_width()
                if canvas_width > 1:
                    self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        self.canvas.bind("<Configure>", configure_scroll_region)
        
        # Force initial canvas width update after a short delay
        def update_canvas_width():
            self.canvas.update_idletasks()
            canvas_width = self.canvas.winfo_width()
            if canvas_width > 1:
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
                bbox = self.canvas.bbox("all")
                if bbox:
                    self.canvas.configure(scrollregion=bbox)
        
        self.parent.after(50, update_canvas_width)
        self.parent.after(200, update_canvas_width)
        
        # Use grid to fill entire frame
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            # Windows and Mac
            if event.delta:
                scroll_amount = int(-1 * (event.delta / 40))
                self.canvas.yview_scroll(scroll_amount, "units")
            return "break"
        
        # Linux mousewheel support
        def scroll_up(e):
            if self.canvas.yview()[0] > 0.0:
                self.canvas.yview_scroll(-3, "units")
        
        def scroll_down(e):
            if self.canvas.yview()[1] < 1.0:
                self.canvas.yview_scroll(3, "units")
        
        # Bind mousewheel events
        self.canvas.bind("<MouseWheel>", on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", on_mousewheel)
        self.canvas.bind("<Button-4>", scroll_up)
        self.canvas.bind("<Button-5>", scroll_down)
        self.scrollable_frame.bind("<Button-4>", scroll_up)
        self.scrollable_frame.bind("<Button-5>", scroll_down)
        
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
        
        # Bind arrow keys
        self.frame.bind("<KeyPress>", on_arrow_key)
        self.canvas.bind("<KeyPress>", on_arrow_key)
        self.scrollable_frame.bind("<KeyPress>", on_arrow_key)
        
        # Make sure the frame can receive focus for keyboard events
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
        title_label.pack(pady=self.scaler.scale_padding(20))
        
        # 1. Account Creation Toggle
        self.create_account_creation_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color)
        
        # 2. Accounts List
        self.create_accounts_list_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color, menu_bar_color, input_bg, input_text)
        
        # 3. Create Account Section
        self.create_new_account_section(self.scrollable_frame, bg_color, text_color, text_secondary, primary_color, input_bg, input_text)
        
        # Update canvas scroll region
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)
    
    def create_account_creation_section(self, parent, bg_color, text_color, text_secondary, primary_color):
        """Create section for toggling account creation"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(20), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Account Creation",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        toggle_frame = tk.Frame(section_frame, bg=bg_color)
        toggle_frame.pack(fill=tk.X)
        
        description = tk.Label(
            toggle_frame,
            text="Allow account creation on login screen:",
            font=body_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        description.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.account_creation_var = tk.BooleanVar(value=self.get_account_creation_enabled())
        toggle_btn = tk.Checkbutton(
            toggle_frame,
            variable=self.account_creation_var,
            command=self.toggle_account_creation,
            bg=bg_color,
            fg=text_color,
            selectcolor=primary_color,
            activebackground=bg_color,
            activeforeground=text_color,
            font=body_font
        )
        toggle_btn.pack(side=tk.RIGHT)
    
    def get_account_creation_enabled(self):
        """Check if account creation is enabled"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                return config.get("allow_account_creation", True)  # Default to True
            except:
                return True
        return True
    
    def toggle_account_creation(self):
        """Toggle account creation setting"""
        try:
            config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            config["allow_account_creation"] = self.account_creation_var.get()
            
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update setting: {str(e)}")
    
    def create_accounts_list_section(self, parent, bg_color, text_color, text_secondary, primary_color, menu_bar_color, input_bg, input_text):
        """Create section for listing and managing accounts"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.BOTH, expand=True, padx=self.scaler.scale_padding(20), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Manage Accounts",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        # Accounts list container
        list_container = tk.Frame(section_frame, bg=bg_color)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        button_font = self.theme.get_font("button", scaler=self.scaler)
        refresh_btn = tk.Button(
            list_container,
            text="Refresh List",
            font=button_font,
            command=lambda: self.refresh_accounts_list(list_container, bg_color, text_color, text_secondary, primary_color, menu_bar_color, input_bg, input_text),
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(15),
            pady=self.scaler.scale_padding(8)
        )
        refresh_btn.pack(anchor="w", pady=(0, self.scaler.scale_padding(10)))
        
        # Accounts list frame
        self.accounts_list_frame = tk.Frame(list_container, bg=bg_color)
        self.accounts_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Load accounts initially
        self.refresh_accounts_list(list_container, bg_color, text_color, text_secondary, primary_color, menu_bar_color, input_bg, input_text)
    
    def refresh_accounts_list(self, parent, bg_color, text_color, text_secondary, primary_color, menu_bar_color, input_bg, input_text):
        """Refresh the accounts list"""
        # Clear existing accounts
        for widget in self.accounts_list_frame.winfo_children():
            widget.destroy()
        
        if not self.accounts_dir.exists():
            no_accounts = tk.Label(
                self.accounts_list_frame,
                text="No accounts found",
                font=self.theme.get_font("body", scaler=self.scaler),
                bg=bg_color,
                fg=text_secondary
            )
            no_accounts.pack(pady=self.scaler.scale_padding(20))
            return
        
        # Get all accounts
        accounts = []
        for account_dir in self.accounts_dir.iterdir():
            if account_dir.is_dir():
                account_file = account_dir / "account.json"
                if account_file.exists():
                    try:
                        with open(account_file, 'r') as f:
                            account_data = json.load(f)
                        accounts.append({
                            "username": account_data.get("username", account_dir.name),
                            "account_type": account_data.get("account_type", "basic"),
                            "locked": account_data.get("locked", False),
                            "account_dir": account_dir,
                            "account_file": account_file
                        })
                    except:
                        pass
        
        if not accounts:
            no_accounts = tk.Label(
                self.accounts_list_frame,
                text="No accounts found",
                font=self.theme.get_font("body", scaler=self.scaler),
                bg=bg_color,
                fg=text_secondary
            )
            no_accounts.pack(pady=self.scaler.scale_padding(20))
            return
        
        # Display each account
        body_font = self.theme.get_font("body", scaler=self.scaler)
        button_font = self.theme.get_font("button_small", scaler=self.scaler)
        
        for account in accounts:
            account_frame = tk.Frame(self.accounts_list_frame, bg=menu_bar_color, relief=tk.FLAT, borderwidth=1)
            account_frame.pack(fill=tk.X, pady=self.scaler.scale_padding(5), padx=self.scaler.scale_padding(5))
            
            # Account info
            info_frame = tk.Frame(account_frame, bg=menu_bar_color)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=self.scaler.scale_padding(10), pady=self.scaler.scale_padding(10))
            
            username_label = tk.Label(
                info_frame,
                text=f"Username: {account['username']}",
                font=body_font,
                bg=menu_bar_color,
                fg=text_color,
                anchor="w"
            )
            username_label.pack(fill=tk.X)
            
            type_label = tk.Label(
                info_frame,
                text=f"Type: {account['account_type'].capitalize()}",
                font=body_font,
                bg=menu_bar_color,
                fg=text_secondary,
                anchor="w"
            )
            type_label.pack(fill=tk.X)
            
            status_text = "Locked" if account['locked'] else "Unlocked"
            status_color = self.theme.get_color("text_error", "#E74C3C") if account['locked'] else self.theme.get_color("text_success", "#4CAF50")
            status_label = tk.Label(
                info_frame,
                text=f"Status: {status_text}",
                font=body_font,
                bg=menu_bar_color,
                fg=status_color,
                anchor="w"
            )
            status_label.pack(fill=tk.X)
            
            # Buttons frame
            buttons_frame = tk.Frame(account_frame, bg=menu_bar_color)
            buttons_frame.pack(side=tk.RIGHT, padx=self.scaler.scale_padding(10), pady=self.scaler.scale_padding(10))
            
            # Change Password button
            change_pass_btn = tk.Button(
                buttons_frame,
                text="Change Password",
                font=button_font,
                command=lambda acc=account: self.change_password(acc),
                bg=primary_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                padx=self.scaler.scale_padding(10),
                pady=self.scaler.scale_padding(5)
            )
            change_pass_btn.pack(side=tk.LEFT, padx=self.scaler.scale_padding(3))
            
            # Lock/Unlock button
            lock_text = "Unlock" if account['locked'] else "Lock"
            lock_btn = tk.Button(
                buttons_frame,
                text=lock_text,
                font=button_font,
                command=lambda acc=account: self.toggle_lock_account(acc),
                bg=primary_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                padx=self.scaler.scale_padding(10),
                pady=self.scaler.scale_padding(5)
            )
            lock_btn.pack(side=tk.LEFT, padx=self.scaler.scale_padding(3))
            
            # Change Admin Status button
            admin_text = "Remove Admin" if account['account_type'] == "administrator" else "Make Admin"
            admin_btn = tk.Button(
                buttons_frame,
                text=admin_text,
                font=button_font,
                command=lambda acc=account: self.toggle_admin_status(acc),
                bg=primary_color,
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                padx=self.scaler.scale_padding(10),
                pady=self.scaler.scale_padding(5)
            )
            admin_btn.pack(side=tk.LEFT, padx=self.scaler.scale_padding(3))
            
            # Delete button
            delete_btn = tk.Button(
                buttons_frame,
                text="Delete",
                font=button_font,
                command=lambda acc=account: self.delete_account(acc),
                bg=self.theme.get_color("text_error", "#E74C3C"),
                fg=text_color,
                cursor="hand2",
                relief=tk.FLAT,
                padx=self.scaler.scale_padding(10),
                pady=self.scaler.scale_padding(5)
            )
            delete_btn.pack(side=tk.LEFT, padx=self.scaler.scale_padding(3))
    
    def change_password(self, account):
        """Change account password"""
        popup = tk.Toplevel(self.parent)
        popup.title("Change Password")
        popup.transient(self.parent)
        popup.grab_set()
        
        bg_color = self.theme.get_color("background_secondary", "#1A1A1A")
        text_color = self.theme.get_color("text_primary", "#FFFFFF")
        text_secondary = self.theme.get_color("text_secondary", "#E0E0E0")
        input_bg = self.theme.get_color("input_background", "#1A1A1A")
        input_text = self.theme.get_color("input_text", "#FFFFFF")
        primary_color = self.theme.get_color("primary", "#9D4EDD")
        
        popup.configure(bg=bg_color)
        popup_width = self.scaler.scale_dimension(400)
        popup_height = self.scaler.scale_dimension(300)
        x, y = self.scaler.center_on_primary_monitor(popup_width, popup_height)
        popup.geometry(f'{popup_width}x{popup_height}+{x}+{y}')
        popup.resizable(False, False)
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        button_font = self.theme.get_font("button", scaler=self.scaler)
        
        title = tk.Label(
            popup,
            text=f"Change Password for {account['username']}",
            font=label_font,
            bg=bg_color,
            fg=text_color
        )
        title.pack(pady=self.scaler.scale_padding(20))
        
        form_frame = tk.Frame(popup, bg=bg_color)
        form_frame.pack(padx=self.scaler.scale_padding(30), pady=self.scaler.scale_padding(10), fill=tk.BOTH, expand=True)
        
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
        
        # Confirm password
        confirm_pass_label = tk.Label(
            form_frame,
            text="Confirm Password:",
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
        confirm_pass_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)), ipady=self.scaler.scale_padding(5))
        
        status_label = tk.Label(
            form_frame,
            text="",
            font=label_font,
            bg=bg_color,
            fg=self.theme.get_color("text_error", "#E74C3C")
        )
        status_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        def save_password():
            new_pass = new_pass_var.get()
            confirm_pass = confirm_pass_var.get()
            
            if not new_pass:
                status_label.config(text="Please enter a password")
                return
            
            if new_pass != confirm_pass:
                status_label.config(text="Passwords do not match")
                return
            
            try:
                # Load account data
                with open(account['account_file'], 'r') as f:
                    account_data = json.load(f)
                
                # Update password
                password_hash = hashlib.sha256(new_pass.encode()).hexdigest()
                account_data['password_hash'] = password_hash
                
                # Save account data
                with open(account['account_file'], 'w') as f:
                    json.dump(account_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Password changed for {account['username']}")
                popup.destroy()
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}")
        
        save_btn = tk.Button(
            form_frame,
            text="Save",
            font=button_font,
            command=save_password,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(30),
            pady=self.scaler.scale_padding(10)
        )
        save_btn.pack(pady=(self.scaler.scale_padding(10), 0))
    
    def toggle_lock_account(self, account):
        """Lock or unlock an account"""
        action = "unlock" if account['locked'] else "lock"
        confirm = messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to {action} account '{account['username']}'?"
        )
        
        if not confirm:
            return
        
        try:
            # Load account data
            with open(account['account_file'], 'r') as f:
                account_data = json.load(f)
            
            # Toggle lock status
            account_data['locked'] = not account['locked']
            
            # Save account data
            with open(account['account_file'], 'w') as f:
                json.dump(account_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Account '{account['username']}' has been {action}ed")
            
            # Refresh accounts list
            self.refresh_accounts_list(
                self.accounts_list_frame.master,
                self.theme.get_color("background", "#000000"),
                self.theme.get_color("text_primary", "#FFFFFF"),
                self.theme.get_color("text_secondary", "#E0E0E0"),
                self.theme.get_color("primary", "#9D4EDD"),
                self.theme.get_color("menu_bar", "#2D2D2D"),
                self.theme.get_color("input_background", "#1A1A1A"),
                self.theme.get_color("input_text", "#FFFFFF")
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to {action} account: {str(e)}")
    
    def toggle_admin_status(self, account):
        """Toggle admin status of an account"""
        action = "remove admin from" if account['account_type'] == "administrator" else "make admin"
        confirm = messagebox.askyesno(
            "Confirm",
            f"Are you sure you want to {action} '{account['username']}'?"
        )
        
        if not confirm:
            return
        
        try:
            # Load account data
            with open(account['account_file'], 'r') as f:
                account_data = json.load(f)
            
            # Toggle admin status
            if account['account_type'] == "administrator":
                account_data['account_type'] = "basic"
            else:
                account_data['account_type'] = "administrator"
            
            # Save account data
            with open(account['account_file'], 'w') as f:
                json.dump(account_data, f, indent=2)
            
            messagebox.showinfo("Success", f"Account '{account['username']}' admin status updated")
            
            # Refresh accounts list
            self.refresh_accounts_list(
                self.accounts_list_frame.master,
                self.theme.get_color("background", "#000000"),
                self.theme.get_color("text_primary", "#FFFFFF"),
                self.theme.get_color("text_secondary", "#E0E0E0"),
                self.theme.get_color("primary", "#9D4EDD"),
                self.theme.get_color("menu_bar", "#2D2D2D"),
                self.theme.get_color("input_background", "#1A1A1A"),
                self.theme.get_color("input_text", "#FFFFFF")
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update admin status: {str(e)}")
    
    def delete_account(self, account):
        """Delete an account"""
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete account '{account['username']}'?\n\nThis will permanently delete all account data and cannot be undone.",
            icon="warning"
        )
        
        if not confirm:
            return
        
        try:
            # Delete account directory
            if account['account_dir'].exists():
                shutil.rmtree(account['account_dir'])
            
            messagebox.showinfo("Success", f"Account '{account['username']}' has been deleted")
            
            # Refresh accounts list
            self.refresh_accounts_list(
                self.accounts_list_frame.master,
                self.theme.get_color("background", "#000000"),
                self.theme.get_color("text_primary", "#FFFFFF"),
                self.theme.get_color("text_secondary", "#E0E0E0"),
                self.theme.get_color("primary", "#9D4EDD"),
                self.theme.get_color("menu_bar", "#2D2D2D"),
                self.theme.get_color("input_background", "#1A1A1A"),
                self.theme.get_color("input_text", "#FFFFFF")
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete account: {str(e)}")
    
    def create_new_account_section(self, parent, bg_color, text_color, text_secondary, primary_color, input_bg, input_text):
        """Create section for creating new accounts"""
        section_frame = tk.Frame(parent, bg=bg_color)
        section_frame.pack(fill=tk.X, padx=self.scaler.scale_padding(20), pady=self.scaler.scale_padding(20))
        
        label_font = self.theme.get_font("label", scaler=self.scaler)
        body_font = self.theme.get_font("body", scaler=self.scaler)
        button_font = self.theme.get_font("button", scaler=self.scaler)
        
        title = tk.Label(
            section_frame,
            text="Create New Account",
            font=label_font,
            bg=bg_color,
            fg=text_color,
            anchor="w"
        )
        title.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(10)))
        
        form_frame = tk.Frame(section_frame, bg=bg_color)
        form_frame.pack(fill=tk.X)
        
        # Username
        username_label = tk.Label(
            form_frame,
            text="Username:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        username_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        username_var = tk.StringVar()
        username_entry = tk.Entry(
            form_frame,
            textvariable=username_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            relief=tk.SOLID,
            borderwidth=1
        )
        username_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(5))
        
        # Password
        password_label = tk.Label(
            form_frame,
            text="Password:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        password_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        password_var = tk.StringVar()
        password_entry = tk.Entry(
            form_frame,
            textvariable=password_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            show="*",
            relief=tk.SOLID,
            borderwidth=1
        )
        password_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(5))
        
        # Confirm Password
        confirm_password_label = tk.Label(
            form_frame,
            text="Confirm Password:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        confirm_password_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        confirm_password_var = tk.StringVar()
        confirm_password_entry = tk.Entry(
            form_frame,
            textvariable=confirm_password_var,
            font=body_font,
            bg=input_bg,
            fg=input_text,
            insertbackground=input_text,
            show="*",
            relief=tk.SOLID,
            borderwidth=1
        )
        confirm_password_entry.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(15)), ipady=self.scaler.scale_padding(5))
        
        # Account Type
        account_type_label = tk.Label(
            form_frame,
            text="Account Type:",
            font=label_font,
            bg=bg_color,
            fg=text_secondary,
            anchor="w"
        )
        account_type_label.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(5)))
        
        account_type_var = tk.StringVar(value="basic")
        account_type_frame = tk.Frame(form_frame, bg=bg_color)
        account_type_frame.pack(fill=tk.X, pady=(0, self.scaler.scale_padding(20)))
        
        basic_radio = tk.Radiobutton(
            account_type_frame,
            text="Basic",
            variable=account_type_var,
            value="basic",
            font=body_font,
            bg=bg_color,
            fg=text_color,
            selectcolor=primary_color,
            activebackground=bg_color,
            activeforeground=text_color
        )
        basic_radio.pack(side=tk.LEFT, padx=(0, self.scaler.scale_padding(20)))
        
        admin_radio = tk.Radiobutton(
            account_type_frame,
            text="Administrator",
            variable=account_type_var,
            value="administrator",
            font=body_font,
            bg=bg_color,
            fg=text_color,
            selectcolor=primary_color,
            activebackground=bg_color,
            activeforeground=text_color
        )
        admin_radio.pack(side=tk.LEFT)
        
        status_label = tk.Label(
            form_frame,
            text="",
            font=label_font,
            bg=bg_color,
            fg=self.theme.get_color("text_error", "#E74C3C")
        )
        status_label.pack(pady=(0, self.scaler.scale_padding(10)))
        
        def create_account():
            username = username_var.get().strip()
            password = password_var.get()
            confirm_password = confirm_password_var.get()
            account_type = account_type_var.get()
            
            if not username:
                status_label.config(text="Please enter a username")
                return
            
            if not password:
                status_label.config(text="Please enter a password")
                return
            
            if password != confirm_password:
                status_label.config(text="Passwords do not match")
                return
            
            # Check if account already exists
            account_dir = self.accounts_dir / username
            if account_dir.exists():
                status_label.config(text="Username already exists")
                return
            
            try:
                # Create account directory
                account_dir.mkdir(parents=True, exist_ok=True)
                
                # Hash password
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                
                # Save account data
                account_data = {
                    "username": username,
                    "password_hash": password_hash,
                    "account_type": account_type,
                    "locked": False
                }
                
                account_file = account_dir / "account.json"
                with open(account_file, 'w') as f:
                    json.dump(account_data, f, indent=2)
                
                messagebox.showinfo("Success", f"Account '{username}' created successfully!")
                
                # Clear form
                username_var.set("")
                password_var.set("")
                confirm_password_var.set("")
                account_type_var.set("basic")
                status_label.config(text="")
                
                # Refresh accounts list
                self.refresh_accounts_list(
                    self.accounts_list_frame.master,
                    self.theme.get_color("background", "#000000"),
                    self.theme.get_color("text_primary", "#FFFFFF"),
                    self.theme.get_color("text_secondary", "#E0E0E0"),
                    self.theme.get_color("primary", "#9D4EDD"),
                    self.theme.get_color("menu_bar", "#2D2D2D"),
                    self.theme.get_color("input_background", "#1A1A1A"),
                    self.theme.get_color("input_text", "#FFFFFF")
                )
            except Exception as e:
                status_label.config(text=f"Error: {str(e)}")
        
        create_btn = tk.Button(
            form_frame,
            text="Create Account",
            font=button_font,
            command=create_account,
            bg=primary_color,
            fg=text_color,
            cursor="hand2",
            relief=tk.FLAT,
            padx=self.scaler.scale_padding(30),
            pady=self.scaler.scale_padding(10)
        )
        create_btn.pack(pady=(self.scaler.scale_padding(10), 0))
    
    def destroy(self):
        """Destroy the panel"""
        self.frame.destroy()
