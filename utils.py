"""
Utility functions for Linux Gaming Center application.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


def safe_json_load(file_path: Path, default: Any = None) -> Any:
    """
    Safely load JSON from a file with error handling.
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if loading fails
        
    Returns:
        Loaded JSON data or default value
    """
    try:
        if not file_path.exists():
            return default
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return default


def safe_json_save(file_path: Path, data: Any, create_dirs: bool = True) -> bool:
    """
    Safely save data to a JSON file with error handling.
    
    Args:
        file_path: Path to save the JSON file
        data: Data to save
        create_dirs: Whether to create parent directories if they don't exist
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except (IOError, TypeError) as e:
        print(f"Error saving JSON to {file_path}: {e}")
        return False


def safe_execute_command(command: str, cwd: Optional[Path] = None) -> bool:
    """
    Safely execute a shell command with error handling.
    
    Args:
        command: Command to execute
        cwd: Working directory for the command
        
    Returns:
        True if successful, False otherwise
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        print(f"Error executing command '{command}': {e}")
        return False


def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB, or 0.0 if file doesn't exist
    """
    try:
        if file_path.exists() and file_path.is_file():
            return file_path.stat().st_size / (1024 * 1024)
    except OSError:
        pass
    return 0.0


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Characters that are not allowed in filenames on most systems
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "unnamed"
    
    return filename


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False


def get_relative_path(base_path: Path, target_path: Path) -> str:
    """
    Get relative path from base to target.
    
    Args:
        base_path: Base path
        target_path: Target path
        
    Returns:
        Relative path string
    """
    try:
        return str(target_path.relative_to(base_path))
    except ValueError:
        return str(target_path)


def is_image_file(file_path: Path) -> bool:
    """
    Check if a file is an image based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file appears to be an image
    """
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp'}
    return file_path.suffix.lower() in image_extensions


def is_video_file(file_path: Path) -> bool:
    """
    Check if a file is a video based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file appears to be a video
    """
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    return file_path.suffix.lower() in video_extensions


def is_audio_file(file_path: Path) -> bool:
    """
    Check if a file is an audio file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file appears to be an audio file
    """
    audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}
    return file_path.suffix.lower() in audio_extensions


def get_file_type_category(file_path: Path) -> str:
    """
    Get the category of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Category string ('image', 'video', 'audio', 'document', 'archive', 'other')
    """
    if is_image_file(file_path):
        return 'image'
    elif is_video_file(file_path):
        return 'video'
    elif is_audio_file(file_path):
        return 'audio'
    elif file_path.suffix.lower() in {'.pdf', '.doc', '.docx', '.txt', '.rtf'}:
        return 'document'
    elif file_path.suffix.lower() in {'.zip', '.rar', '.7z', '.tar', '.gz'}:
        return 'archive'
    else:
        return 'other'
