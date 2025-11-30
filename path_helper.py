#!/usr/bin/env python3
"""
Linux Gaming Center - Path Helper Module
Provides centralized path management with support for custom storage locations
"""

from pathlib import Path
import json


def get_storage_config():
    """Load storage configuration from config file"""
    config_file = Path.home() / ".config" / "linux-gaming-center" / "storage_config.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            pass
    
    return {}


def get_main_base_path():
    """Get the main base path for linux-gaming-center data (where config files go)"""
    config = get_storage_config()
    custom_main = config.get("custom_main_location")
    
    if custom_main:
        custom_path = Path(custom_main)
        # Check if path already ends with linux-gaming-center (backward compatibility)
        if custom_path.name == "linux-gaming-center":
            return custom_path
        else:
            # Custom location provided - use linux-gaming-center subfolder
            return custom_path / "linux-gaming-center"
    else:
        # Default: use .config/linux-gaming-center
        return Path.home() / ".config" / "linux-gaming-center"


def get_data_base_path():
    """Get the base path for data (apps, emulators, etc.)"""
    config = get_storage_config()
    custom_main = config.get("custom_main_location")
    
    if custom_main:
        custom_path = Path(custom_main)
        # Check if path already ends with linux-gaming-center (backward compatibility)
        if custom_path.name == "linux-gaming-center":
            return custom_path / "data"
        else:
            # Custom location: data goes under linux-gaming-center/data/
            return custom_path / "linux-gaming-center" / "data"
    else:
        # Default: use .local/share/linux-gaming-center/data
        return Path.home() / ".local" / "share" / "linux-gaming-center" / "data"


def get_accounts_path():
    """Get the path for accounts directory"""
    config = get_storage_config()
    custom_accounts = config.get("custom_accounts_location")
    
    if custom_accounts:
        return Path(custom_accounts)
    elif config.get("custom_main_location"):
        custom_path = Path(config.get("custom_main_location"))
        # Check if path already ends with linux-gaming-center (backward compatibility)
        if custom_path.name == "linux-gaming-center":
            return custom_path / "accounts"
        else:
            # If custom main is set, accounts go under linux-gaming-center/accounts/
            return custom_path / "linux-gaming-center" / "accounts"
    else:
        # Default
        return Path.home() / ".config" / "linux-gaming-center" / "accounts"


def get_roms_path():
    """Get the path for ROMs directory"""
    config = get_storage_config()
    custom_roms = config.get("custom_roms_location")
    
    if custom_roms:
        return Path(custom_roms)
    elif config.get("custom_main_location"):
        custom_path = Path(config.get("custom_main_location"))
        # Check if path already ends with linux-gaming-center (backward compatibility)
        if custom_path.name == "linux-gaming-center":
            return custom_path / "roms"
        else:
            # If custom main is set, ROMs go under linux-gaming-center/roms/
            return custom_path / "linux-gaming-center" / "roms"
    else:
        # Default
        return Path.home() / ".local" / "share" / "linux-gaming-center" / "roms"


def get_bios_path():
    """Get the path for BIOS directory"""
    config = get_storage_config()
    custom_bios = config.get("custom_bios_location")
    
    if custom_bios:
        return Path(custom_bios)
    elif config.get("custom_main_location"):
        custom_path = Path(config.get("custom_main_location"))
        # Check if path already ends with linux-gaming-center (backward compatibility)
        if custom_path.name == "linux-gaming-center":
            return custom_path / "bios"
        else:
            # If custom main is set, BIOS goes under linux-gaming-center/bios/
            return custom_path / "linux-gaming-center" / "bios"
    else:
        # Default
        return Path.home() / ".local" / "share" / "linux-gaming-center" / "bios"


def get_config_file_path(filename):
    """Get path for a config file (like config.json, library_config.json, etc.)"""
    base_path = get_main_base_path()
    return base_path / filename


def get_user_account_dir(username):
    """Get the directory for a specific user account"""
    accounts_path = get_accounts_path()
    return accounts_path / username

