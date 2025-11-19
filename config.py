"""
Configuration settings for Linux Gaming Center application.
"""

import os
from pathlib import Path

# Application Information
APP_NAME = "linux-gaming-center"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Electricwildflower"
APP_DESCRIPTION = "A comprehensive gaming center for Linux"

# Default Paths
DEFAULT_CONFIG_DIR = Path.home() / ".config" / APP_NAME
DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / APP_NAME

# Theme Configuration
DEFAULT_THEME = "cosmictwilight"
THEME_DIR = Path("data") / "themes"

# File Extensions
ROM_EXTENSIONS = {
    '.nes', '.smc', '.sfc', '.gb', '.gbc', '.gba', '.nds', '.3ds',
    '.iso', '.bin', '.cue', '.img', '.mdf', '.mds', '.nrg', '.ccd',
    '.pce', '.sgx', '.sms', '.gg', '.md', '.gen', '.smd', '.32x',
    '.a26', '.a78', '.lynx', '.ws', '.wsc', '.ngp', '.ngc', '.vb',
    '.chd', '.gdi', '.elf', '.dol', '.wad', '.rvz', '.wbfs', '.ciso'
}

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}

# UI Configuration
DEFAULT_WINDOW_SIZE = (1920, 1080)
MIN_WINDOW_SIZE = (800, 600)
DEFAULT_BUTTON_SIZE = (200, 150)
DEFAULT_ICON_SIZE = (64, 64)

# Scaling Configuration
BASE_SCREEN_WIDTH = 1920
MIN_SCALE = 0.8
MAX_SCALE = 1.25

# Performance Configuration
MAX_RECENT_ITEMS = 15
MAX_THUMBNAIL_SIZE = (256, 256)
CACHE_SIZE_LIMIT = 100  # MB

# Network Configuration
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "linux_gaming_center.log"

# Security Configuration
MAX_PASSWORD_LENGTH = 128
MIN_PASSWORD_LENGTH = 8
PASSWORD_HASH_ALGORITHM = "sha256"

# Development Configuration
DEBUG_MODE = os.getenv("LGC_DEBUG", "false").lower() == "true"
DEVELOPMENT_MODE = os.getenv("LGC_DEV", "false").lower() == "true"

# Platform-specific Configuration
IS_LINUX = os.name == "posix"
IS_WINDOWS = os.name == "nt"
IS_MACOS = os.name == "posix" and os.uname().sysname == "Darwin"

# Default Applications
DEFAULT_TEXT_EDITOR = "gedit" if IS_LINUX else "notepad" if IS_WINDOWS else "TextEdit"
DEFAULT_FILE_MANAGER = "nautilus" if IS_LINUX else "explorer" if IS_WINDOWS else "Finder"

# Emulator Configuration
DEFAULT_EMULATOR_MAPPINGS = {
    "Nintendo Entertainment System": "nes",
    "Super Nintendo Entertainment System": "snes",
    "Nintendo 64": "n64",
    "Game Boy": "gb",
    "Game Boy Color": "gbc",
    "Game Boy Advance": "gba",
    "Nintendo DS": "nds",
    "Nintendo 3DS": "3ds",
    "PlayStation": "psx",
    "PlayStation 2": "ps2",
    "PlayStation Portable": "psp",
    "Sega Genesis": "genesis",
    "Sega Dreamcast": "dreamcast",
    "Sega Saturn": "saturn",
    "Atari 2600": "atari2600",
    "Arcade": "arcade"
}

# Store Configuration
STORE_API_URL = "https://api.linuxgamingcenter.com"  # Placeholder
STORE_CACHE_DURATION = 3600  # 1 hour in seconds

# Backup Configuration
BACKUP_RETENTION_DAYS = 30
MAX_BACKUP_SIZE = 1024  # MB

# Update Configuration
UPDATE_CHECK_INTERVAL = 86400  # 24 hours in seconds
AUTO_UPDATE_ENABLED = False

def get_config_value(key: str, default=None):
    """
    Get a configuration value, checking environment variables first.
    
    Args:
        key: Configuration key
        default: Default value if not found
        
    Returns:
        Configuration value
    """
    env_key = f"LGC_{key.upper()}"
    return os.getenv(env_key, default)

def is_development_mode():
    """Check if the application is running in development mode."""
    return DEVELOPMENT_MODE or DEBUG_MODE

def get_log_level():
    """Get the current log level."""
    return get_config_value("LOG_LEVEL", LOG_LEVEL)

def get_cache_size_limit():
    """Get the cache size limit in MB."""
    return int(get_config_value("CACHE_SIZE_LIMIT", CACHE_SIZE_LIMIT))
