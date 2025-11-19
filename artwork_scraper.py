import os
import json
import re
import requests
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Callable, Tuple
from urllib.parse import quote

# Mapping of short emulator names to TheGamesDB platform IDs
# Based on TheGamesDB API v2: https://api.thegamesdb.net/v2/Platforms/ByPlatformID
PLATFORM_MAPPING = {
    "nes": 25,           # Nintendo Entertainment System
    "snes": 6,           # Super Nintendo Entertainment System
    "n64": 4,            # Nintendo 64
    "gb": 5,             # Game Boy
    "gbc": 41,           # Game Boy Color
    "gba": 24,           # Game Boy Advance
    "nds": 20,           # Nintendo DS
    "wii": 11,           # Nintendo Wii
    "wiiu": 38,          # Nintendo Wii U
    "Switch": 41,        # Nintendo Switch (using Wii U ID as placeholder)
    "ps1": 7,            # Sony Playstation
    "ps2": 8,            # Sony Playstation 2
    "ps3": 9,            # Sony Playstation 3
    "ps4": 130,          # Sony Playstation 4
    "ps5": 167,          # Sony Playstation 5
    "megadrive": 1,      # Sega Mega Drive / Genesis
    "mastersystem": 2,   # Sega Master System
    "gamegear": 35,      # Sega Game Gear
    "32x": 19,           # Sega 32X
    "atari2600": 26,     # Atari 2600
    "atari5200": 40,     # Atari 5200
    "atari7800": 28,     # Atari 7800
    "tg16": 31,          # NEC PC Engine / TurboGrafx-16
    "xbox": 12,          # Microsoft Xbox
    "xbox360": 32,       # Microsoft Xbox 360
}

# Mapping of short emulator names to ScreenScraper platform IDs
# Based on ScreenScraper API: https://www.screenscraper.fr/webapi2.php
SCREENSCRAPER_PLATFORM_MAPPING = {
    "nes": 3,            # Nintendo Entertainment System
    "snes": 1,           # Super Nintendo Entertainment System
    "n64": 4,            # Nintendo 64
    "gb": 9,             # Game Boy
    "gbc": 10,           # Game Boy Color
    "gba": 12,           # Game Boy Advance
    "nds": 15,           # Nintendo DS
    "wii": 145,          # Nintendo Wii
    "wiiu": 162,         # Nintendo Wii U
    "Switch": 283,       # Nintendo Switch
    "ps1": 7,            # Sony Playstation
    "ps2": 8,            # Sony Playstation 2
    "ps3": 9,            # Sony Playstation 3
    "ps4": 46,           # Sony Playstation 4
    "ps5": 307,          # Sony Playstation 5
    "megadrive": 1,      # Sega Mega Drive / Genesis
    "mastersystem": 2,   # Sega Master System
    "gamegear": 21,      # Sega Game Gear
    "32x": 19,           # Sega 32X
    "atari2600": 26,     # Atari 2600
    "atari5200": 40,     # Atari 5200
    "atari7800": 28,     # Atari 7800
    "tg16": 31,          # NEC PC Engine / TurboGrafx-16
    "xbox": 32,          # Microsoft Xbox
    "xbox360": 78,       # Microsoft Xbox 360
    "c64": 64,           # Commodore 64
}

# Common ROM extensions
COMMON_ROM_EXTENSIONS = {
    '.nes', '.snes', '.gb', '.bin', '.chd', '.cue', '.gba', '.gen', '.md', '.n64', '.ps1', '.iso',
    '.zip', '.7z', '.rar', '.j64', '.jag', '.rom', '.abs', '.cof', '.prg', '.gbc', '.nds', '.ps2', '.ps3'
}

class ArtworkScraper:
    """
    Scrapes game artwork (covers, banners, screenshots) from TheGamesDB API or ScreenScraper API
    and saves them to the artwork folder for each console.
    """
    
    def __init__(self, path_manager, api_source: str = "thegamesdb"):
        """
        Initialize the artwork scraper.
        
        Args:
            path_manager: PathManager instance
            api_source: API source to use - "thegamesdb" or "screenscraper"
        """
        self.path_manager = path_manager
        self.api_source = api_source.lower()  # "thegamesdb" or "screenscraper"
        # TheGamesDB API base URL (v2.0 API uses /v1.1/ endpoints)
        self.base_url = "https://api.thegamesdb.net"
        # ScreenScraper API
        self.screenscraper_url = "https://www.screenscraper.fr/api2"
        self.scraping = False
        self.progress_callbacks = []
        self.completion_callbacks = []
        self._lock = threading.Lock()
        
        # TheGamesDB API key
        self.thegamesdb_apikey = "1"  # Default public key
        
        # ScreenScraper credentials (can be set later via set_screenscraper_credentials)
        self.screenscraper_username = ""
        self.screenscraper_password = ""
        self.screenscraper_devid = ""
        
    def add_progress_callback(self, callback: Callable[[str, int, int], None]):
        """Add a callback for progress updates: callback(message, current, total)"""
        self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[[bool, str], None]):
        """Add a callback for when scraping is complete: callback(success, message)"""
        self.completion_callbacks.append(callback)
    
    def _notify_progress(self, message: str, current: int = 0, total: int = 0):
        """Notify all progress callbacks"""
        for callback in self.progress_callbacks:
            try:
                callback(message, current, total)
            except Exception as e:
                print(f"Error in progress callback: {e}")
    
    def _notify_completion(self, success: bool, message: str):
        """Notify all completion callbacks"""
        for callback in self.completion_callbacks:
            try:
                callback(success, message)
            except Exception as e:
                print(f"Error in completion callback: {e}")
    
    def set_api_source(self, api_source: str):
        """Set the API source to use: 'thegamesdb' or 'screenscraper'"""
        self.api_source = api_source.lower()
    
    def set_thegamesdb_apikey(self, apikey: str):
        """Set TheGamesDB API key"""
        if apikey:
            # Strip whitespace and ensure it's a string
            cleaned_key = str(apikey).strip()
            self.thegamesdb_apikey = cleaned_key if cleaned_key else "1"
        else:
            self.thegamesdb_apikey = "1"
    
    def set_screenscraper_credentials(self, username: str, password: str, devid: str = ""):
        """Set ScreenScraper API credentials"""
        self.screenscraper_username = username.strip() if username else ""
        self.screenscraper_password = password.strip() if password else ""
        self.screenscraper_devid = devid.strip() if devid else ""
    
    def _get_rom_name_from_file(self, rom_path: Path) -> str:
        """
        Extract game name from ROM filename by removing extension and cleaning up.
        """
        filename = rom_path.stem  # Get filename without extension
        # Remove common suffixes and clean up
        name = re.sub(r'\([^)]*\)', '', filename)  # Remove text in parentheses
        name = re.sub(r'\[[^\]]*\]', '', name)  # Remove text in brackets
        name = name.strip()
        # Remove extra spaces
        name = re.sub(r'\s+', ' ', name)
        return name
    
    def _search_game(self, game_name: str, platform_id: int, emulator_short_name: str = "") -> Optional[Dict]:
        """
        Search for a game on the configured API (TheGamesDB or ScreenScraper).
        Returns the first matching game data or None.
        """
        if self.api_source == "screenscraper":
            return self._search_game_screenscraper(game_name, platform_id, emulator_short_name)
        else:
            return self._search_game_thegamesdb_v2(game_name, platform_id)
    
    def _fetch_artwork_for_game(self, game_id, artwork_type: str = "boxart") -> Optional[Dict]:
        """
        Fetch artwork (boxart, banner, or fanart) for a specific game ID using TheGamesDB v2 API.
        Returns artwork data or None.
        
        Args:
            game_id: The game ID
            artwork_type: Type of artwork to fetch - "boxart", "banner", or "fanart"
        """
        try:
            # Try v1 endpoint first (v1.1 might not have ByGameID)
            url = f"{self.base_url}/v1/Games/ByGameID"
            params = {
                "apikey": self.thegamesdb_apikey,
                "id": game_id,
                "include": artwork_type,
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # TheGamesDB API uses "include" not "included"
                    include = data.get("include", {})
                    
                    if include:
                        artwork_info = include.get(artwork_type, {})
                        
                        # Structure: include.{artwork_type}.data[game_id] = [list of items]
                        if isinstance(artwork_info, dict):
                            artwork_data = artwork_info.get("data", {})
                            
                            if artwork_data:
                                game_id_str = str(game_id)
                                game_id_int = int(game_id) if game_id and str(game_id).isdigit() else None
                                
                                # Try to get artwork for this game ID
                                if isinstance(artwork_data, dict):
                                    artwork_list = None
                                    if game_id_str in artwork_data:
                                        artwork_list = artwork_data[game_id_str]
                                    elif game_id_int and game_id_int in artwork_data:
                                        artwork_list = artwork_data[game_id_int]
                                    
                                    if artwork_list:
                                        # artwork_list is a list of items
                                        if isinstance(artwork_list, list) and len(artwork_list) > 0:
                                            # For boxart, look for "front", otherwise use first item
                                            for item in artwork_list:
                                                if isinstance(item, dict):
                                                    if artwork_type == "boxart":
                                                        side = item.get("side", "")
                                                        if side == "front":
                                                            item["base_url"] = artwork_info.get("base_url", {})
                                                            return item
                                                    else:
                                                        # For banner/fanart, use first item
                                                        item["base_url"] = artwork_info.get("base_url", {})
                                                        return item
                                            # If no "front" found for boxart, or fallback
                                            first_item = artwork_list[0]
                                            if isinstance(first_item, dict):
                                                first_item["base_url"] = artwork_info.get("base_url", {})
                                            return first_item
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
                        
                except ValueError:
                    pass
                except Exception:
                    pass
            else:
                pass
        except Exception:
            pass
        
        return None
    
    def check_thegamesdb_rate_limit(self) -> Optional[Dict]:
        """
        Check TheGamesDB API rate limit by making a test API call.
        Returns dict with rate limit info or None if check failed.
        {
            "remaining": int,
            "limit_reached": bool,
            "refresh_days": int,
            "refresh_hours": int,
            "error": str
        }
        """
        if self.api_source != "thegamesdb":
            return None
            
        try:
            # Make a minimal API call to check rate limit
            # Use a simple platform query or a known game ID
            url = f"{self.base_url}/v1.1/Games/ByGameName"
            api_key_clean = str(self.thegamesdb_apikey).strip() if self.thegamesdb_apikey else "1"
            api_key_clean = ''.join(c for c in api_key_clean if c.isprintable())
            
            params = {
                "apikey": api_key_clean,
                "name": "Test",  # Minimal search
                "filter[platform]": 6,  # SNES as a test platform
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    remaining = data.get("remaining_monthly_allowance", None)
                    if remaining is not None:
                        return {
                            "remaining": remaining,
                            "limit_reached": remaining == 0,
                            "refresh_days": 0,
                            "refresh_hours": 0,
                            "error": None
                        }
                except (ValueError, KeyError):
                    pass
            else:
                # Check response for rate limit info even if status is not 200
                try:
                    data = response.json()
                    remaining = data.get("remaining_monthly_allowance", None)
                    refresh_timer = data.get("allowance_refresh_timer", None)
                    
                    if remaining is not None:
                        days = 0
                        hours = 0
                        if refresh_timer:
                            days = refresh_timer // 86400
                            hours = (refresh_timer % 86400) // 3600
                        
                        return {
                            "remaining": remaining,
                            "limit_reached": remaining == 0,
                            "refresh_days": days,
                            "refresh_hours": hours,
                            "error": data.get("status", "Rate limit check failed")
                        }
                except (ValueError, KeyError):
                    pass
                    
        except Exception as e:
            return None
            
        return None
    
    def _search_game_thegamesdb_v2(self, game_name: str, platform_id: int) -> Optional[Dict]:
        """
        Search for a game on TheGamesDB API v2.0.
        Returns the first matching game data or None.
        """
        try:
            # Clean game name for search
            search_name = game_name.strip()
            search_name = re.sub(r',\s*The$', '', search_name, flags=re.IGNORECASE)
            search_name = search_name.strip()
            
            # TheGamesDB API v2.0 endpoint format
            # Uses /v1.1/Games/ByGameName endpoint
            # Note: Requires a valid API key from api.thegamesdb.net
            url = f"{self.base_url}/v1.1/Games/ByGameName"
            
            # Debug: Check API key value
            # Make sure we use the actual stored key, not a stripped copy
            api_key_debug = str(self.thegamesdb_apikey).strip() if self.thegamesdb_apikey else "1"
            # Remove any non-printable characters or whitespace
            api_key_debug = ''.join(c for c in api_key_debug if c.isprintable())
            
            
            params = {
                "apikey": api_key_debug,  # Use stored API key (cleaned)
                "name": search_name,
                "filter[platform]": platform_id,  # Use filter[platform] format, not platform
                "include": "boxart,banner,fanart,screenshot,titlescreen,clearlogo,platform",  # Include all artwork types
                "fields": "publishers,genres,overview,rating"
            }
            
            # Debug: Show what we're sending
            
            response = requests.get(url, params=params, timeout=10)
            
            # Debug: Check response status
            
            try:
                data = response.json()
            except ValueError:
                # Not valid JSON - return None
                return None
            
            # Handle v2 response structure
            if isinstance(data, dict):
                # Check for error status/code field
                status_code = data.get("code") or data.get("status")
                error_msg = data.get("status", "") or data.get("message", "")
                
                # Debug: Show what we're checking
                
                # Check for rate limiting (remaining_monthly_allowance = 0)
                remaining_allowance = data.get("remaining_monthly_allowance", None)
                if remaining_allowance is not None:
                    if remaining_allowance == 0:
                        error_msg = "❌ Monthly API rate limit reached (0 requests remaining)"
                        self._notify_progress(error_msg, 0, 0)
                        self._notify_progress("Your API key has exhausted its monthly quota. Please wait for the allowance to refresh.", 0, 0)
                        refresh_timer = data.get("allowance_refresh_timer", None)
                        if refresh_timer:
                            # Convert seconds to days/hours
                            days = refresh_timer // 86400
                            hours = (refresh_timer % 86400) // 3600
                            refresh_msg = f"Allowance refreshes in approximately {days} days and {hours} hours"
                            self._notify_progress(refresh_msg, 0, 0)
                        return None
                
                # Check for authentication/authorization errors (401, 403, etc.)
                if status_code == 401 or status_code == 403 or (isinstance(status_code, int) and status_code >= 400) or "API key" in str(error_msg).lower() or "invalid" in str(error_msg).lower():
                    pass
                    
                    # If it's a 403 with "Invalid API key", check if it's actually rate limiting
                    if status_code == 403 and "invalid" in str(error_msg).lower():
                        if remaining_allowance == 0:
                            pass
                        else:
                            pass
                    
                    return None
                
                # Check for success
                if status_code == 200 or status_code == "Success" or response.status_code == 200:
                    games_data = data.get("data", {})
                    if isinstance(games_data, dict):
                        games = games_data.get("games", [])
                    elif isinstance(games_data, list):
                        games = games_data
                    else:
                        games = []
                    
                    if games and len(games) > 0:
                        game = games[0]
                        game_id = game.get("id")
                        
                        # TheGamesDB v2.0 returns artwork in "include" section
                        # Structure: include.{boxart|banner|fanart}.data[game_id] = [list of items]
                        include = data.get("include", {})
                        
                        # Extract all artwork types from include section
                        boxart_data = None
                        banner_data = None
                        fanart_data = None
                        screenshot_data = None
                        titlescreen_data = None
                        clearlogo_data = None
                        
                        if include:
                            game_id_str = str(game_id)
                            game_id_int = int(game_id) if game_id and str(game_id).isdigit() else None
                            
                            # Extract boxart
                            boxart_info = include.get("boxart", {})
                            if boxart_info and isinstance(boxart_info, dict):
                                boxart_data_dict = boxart_info.get("data", {})
                                if boxart_data_dict:
                                    boxart_list = None
                                    if game_id_str in boxart_data_dict:
                                        boxart_list = boxart_data_dict[game_id_str]
                                    elif game_id_int and game_id_int in boxart_data_dict:
                                        boxart_list = boxart_data_dict[game_id_int]
                                    
                                    if boxart_list and isinstance(boxart_list, list) and len(boxart_list) > 0:
                                        for item in boxart_list:
                                            if isinstance(item, dict) and item.get("side") == "front":
                                                item["base_url"] = boxart_info.get("base_url", {})
                                                boxart_data = item
                                                break
                                        if not boxart_data:
                                            first_item = boxart_list[0]
                                            if isinstance(first_item, dict):
                                                first_item["base_url"] = boxart_info.get("base_url", {})
                                            boxart_data = first_item
                            
                            # Extract banner
                            banner_info = include.get("banner", {})
                            if banner_info and isinstance(banner_info, dict):
                                banner_data_dict = banner_info.get("data", {})
                                if banner_data_dict:
                                    banner_list = None
                                    if game_id_str in banner_data_dict:
                                        banner_list = banner_data_dict[game_id_str]
                                    elif game_id_int and game_id_int in banner_data_dict:
                                        banner_list = banner_data_dict[game_id_int]
                                    
                                    if banner_list and isinstance(banner_list, list) and len(banner_list) > 0:
                                        first_banner = banner_list[0]
                                        if isinstance(first_banner, dict):
                                            first_banner["base_url"] = banner_info.get("base_url", {})
                                        banner_data = first_banner
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass
                            
                            # Extract fanart
                            fanart_info = include.get("fanart", {})
                            if fanart_info and isinstance(fanart_info, dict):
                                fanart_data_dict = fanart_info.get("data", {})
                                if fanart_data_dict:
                                    fanart_list = None
                                    if game_id_str in fanart_data_dict:
                                        fanart_list = fanart_data_dict[game_id_str]
                                    elif game_id_int and game_id_int in fanart_data_dict:
                                        fanart_list = fanart_data_dict[game_id_int]
                                    
                                    if fanart_list and isinstance(fanart_list, list) and len(fanart_list) > 0:
                                        first_fanart = fanart_list[0]
                                        if isinstance(first_fanart, dict):
                                            first_fanart["base_url"] = fanart_info.get("base_url", {})
                                        fanart_data = first_fanart
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass
                            
                            # Extract screenshots
                            screenshot_info = include.get("screenshot", {})
                            if screenshot_info and isinstance(screenshot_info, dict):
                                screenshot_data_dict = screenshot_info.get("data", {})
                                if screenshot_data_dict:
                                    screenshot_list = None
                                    if game_id_str in screenshot_data_dict:
                                        screenshot_list = screenshot_data_dict[game_id_str]
                                    elif game_id_int and game_id_int in screenshot_data_dict:
                                        screenshot_list = screenshot_data_dict[game_id_int]
                                    
                                    if screenshot_list and isinstance(screenshot_list, list) and len(screenshot_list) > 0:
                                        # Use first screenshot
                                        first_screenshot = screenshot_list[0]
                                        if isinstance(first_screenshot, dict):
                                            first_screenshot["base_url"] = screenshot_info.get("base_url", {})
                                        screenshot_data = first_screenshot
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass
                            
                            # Extract titlescreens
                            titlescreen_info = include.get("titlescreen", {})
                            if titlescreen_info and isinstance(titlescreen_info, dict):
                                titlescreen_data_dict = titlescreen_info.get("data", {})
                                if titlescreen_data_dict:
                                    titlescreen_list = None
                                    if game_id_str in titlescreen_data_dict:
                                        titlescreen_list = titlescreen_data_dict[game_id_str]
                                    elif game_id_int and game_id_int in titlescreen_data_dict:
                                        titlescreen_list = titlescreen_data_dict[game_id_int]
                                    
                                    if titlescreen_list and isinstance(titlescreen_list, list) and len(titlescreen_list) > 0:
                                        first_titlescreen = titlescreen_list[0]
                                        if isinstance(first_titlescreen, dict):
                                            first_titlescreen["base_url"] = titlescreen_info.get("base_url", {})
                                        titlescreen_data = first_titlescreen
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass
                            
                            # Extract clearlogos
                            clearlogo_info = include.get("clearlogo", {})
                            if clearlogo_info and isinstance(clearlogo_info, dict):
                                clearlogo_data_dict = clearlogo_info.get("data", {})
                                if clearlogo_data_dict:
                                    clearlogo_list = None
                                    if game_id_str in clearlogo_data_dict:
                                        clearlogo_list = clearlogo_data_dict[game_id_str]
                                    elif game_id_int and game_id_int in clearlogo_data_dict:
                                        clearlogo_list = clearlogo_data_dict[game_id_int]
                                    
                                    if clearlogo_list and isinstance(clearlogo_list, list) and len(clearlogo_list) > 0:
                                        first_clearlogo = clearlogo_list[0]
                                        if isinstance(first_clearlogo, dict):
                                            first_clearlogo["base_url"] = clearlogo_info.get("base_url", {})
                                        clearlogo_data = first_clearlogo
                                    else:
                                        pass
                                else:
                                    pass
                            else:
                                pass
                        
                        # If artwork not found in include section, try to fetch separately
                        if not boxart_data:
                            boxart_data = self._fetch_artwork_for_game(game_id, "boxart")
                        
                        if not banner_data:
                            banner_data = self._fetch_artwork_for_game(game_id, "banner")
                        
                        if not fanart_data:
                            fanart_data = self._fetch_artwork_for_game(game_id, "fanart")
                        
                        if not screenshot_data:
                            screenshot_data = self._fetch_artwork_for_game(game_id, "screenshot")
                        
                        if not titlescreen_data:
                            titlescreen_data = self._fetch_artwork_for_game(game_id, "titlescreen")
                        
                        if not clearlogo_data:
                            clearlogo_data = self._fetch_artwork_for_game(game_id, "clearlogo")
                        
                        if boxart_data:
                            game["boxart"] = boxart_data
                        
                        if banner_data:
                            game["banner"] = banner_data
                        
                        if fanart_data:
                            game["fanart"] = fanart_data
                        
                        if screenshot_data:
                            game["screenshot"] = screenshot_data
                        
                        if titlescreen_data:
                            game["titlescreen"] = titlescreen_data
                        
                        if clearlogo_data:
                            game["clearlogo"] = clearlogo_data
                        
                        # Debug: show what artwork data we have
                        
                        return game
                    else:
                        # No games found in results
                        pass
                else:
                    # Check for error message
                    if "API key" in error_msg:
                        pass
                    else:
                        pass
            
            return None
            
        except Exception as e:
            return None
    
    def _search_game_screenscraper(self, game_name: str, platform_id: int, emulator_short_name: str = "") -> Optional[Dict]:
        """
        Search for a game on ScreenScraper API.
        Returns game data or None.
        """
        try:
            # Get ScreenScraper platform ID
            screenscraper_platform_id = SCREENSCRAPER_PLATFORM_MAPPING.get(emulator_short_name.lower())
            if not screenscraper_platform_id:
                return None
            
            # Clean game name
            search_name = game_name.strip()
            search_name = re.sub(r',\s*The$', '', search_name, flags=re.IGNORECASE)
            search_name = search_name.strip()
            
            # ScreenScraper API endpoint: jeuRecherche.php
            # Format: https://www.screenscraper.fr/api2/jeuRecherche.php
            url = f"{self.screenscraper_url}/jeuRecherche.php"
            params = {
                "devid": self.screenscraper_devid if self.screenscraper_devid else "linux-gaming-center",
                "devpassword": "",  # Optional
                "softname": "linux-gaming-center",
                "output": "json",
                "recherche": search_name,
                "systemeid": screenscraper_platform_id,
            }
            
            # Add credentials if provided
            if self.screenscraper_username and self.screenscraper_password:
                params["ssid"] = self.screenscraper_username
                params["sspassword"] = self.screenscraper_password
            
            response = requests.get(url, params=params, timeout=10)
            
            # Check response status
            if response.status_code != 200:
                response.raise_for_status()
            
            # Get response text to check for errors
            response_text = response.text.strip()
            
            # Check for login error in French
            if "Erreur de login" in response_text or "identifiants développeur" in response_text:
                return None
            
            try:
                data = response.json()
                
                # ScreenScraper response structure: {"response": {"jeux": [{...}]}}
                if isinstance(data, dict):
                    response_data = data.get("response", {})
                    if isinstance(response_data, dict):
                        jeux = response_data.get("jeux", [])
                        if jeux and len(jeux) > 0:
                            game = jeux[0]
                            return game
                    # Check for error in response
                    if "erreur" in response_data:
                        error_msg = response_data.get("erreur", {}).get("message", "Unknown error")
                        return None
            except ValueError:
                # Not valid JSON - show actual response
                return None
            
            return None
            
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                pass
            return None
        except Exception as e:
            return None
    
    def _search_game_v1(self, game_name: str, platform_id: int) -> Optional[Dict]:
        """
        Fallback to TheGamesDB v1 API if v2 fails.
        v1 API returns XML format.
        """
        try:
            # TheGamesDB v1 API
            url = "https://thegamesdb.net/api/GetGamesList.php"
            
            # Map platform_id to v1 platform name
            platform_map = {
                6: "snes", 8: "ps2", 25: "nes", 4: "n64",
                5: "gb", 41: "gbc", 24: "gba", 20: "nds",
                11: "wii", 38: "wiiu", 1: "genesis", 2: "mastersystem",
                7: "psx", 9: "ps3", 1: "genesis", 32: "xbox360", 12: "xbox"
            }
            platform_name = platform_map.get(platform_id, "")
            
            # Clean game name - try multiple variations
            search_name = game_name.strip()
            search_name = re.sub(r',\s*The$', '', search_name, flags=re.IGNORECASE).strip()
            
            # Try without platform first (broader search)
            params = {
                "name": search_name,
            }
            if platform_name:
                params["platform"] = platform_name
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Check if response indicates deprecation
            response_text = response.text.strip()
            
            # Debug: print first 500 chars of response to see what we get
            
            if "update your programs" in response_text.lower() or len(response_text) < 50:
                # TheGamesDB v1 might be deprecated - games won't be found
                # This is expected behavior - not all games will have artwork available
                return None
            
            # Parse XML response
            try:
                root = ET.fromstring(response_text)
            except ET.ParseError as e:
                return None
            
            # Check if we got results
            games = root.findall(".//Game")
            if not games:
                # Try searching without platform to get better results
                if platform_name:
                    params_no_platform = {"name": search_name}
                    response2 = requests.get(url, params=params_no_platform, timeout=10)
                    response2.raise_for_status()
                    response2_text = response2.text.strip()
                    if len(response2_text) > 50 and "update" not in response2_text.lower():
                        try:
                            root2 = ET.fromstring(response2_text)
                            games = root2.findall(".//Game")
                            # Filter by platform if we found games
                            if games and platform_name:
                                filtered_games = []
                                for game in games:
                                    game_platform = game.findtext(".//Platform", "")
                                    if platform_name.lower() in game_platform.lower():
                                        filtered_games.append(game)
                                if filtered_games:
                                    games = filtered_games
                        except:
                            pass
                
                if not games:
                    return None
            
            # Return first game as dict format compatible with v2
            game = games[0]
            game_id = game.findtext("id", "")
            game_title = game.findtext("GameTitle", search_name)
            release_date = game.findtext("ReleaseDate", "")
            
            # Get boxart
            boxart = game.find(".//boxart")
            boxart_url = None
            if boxart is not None:
                # v1 API boxart format: <boxart side="front" width="500" height="500">filename.jpg</boxart>
                boxart_text = boxart.text
                if boxart_text:
                    # v1 CDN URL structure
                    boxart_url = f"https://thegamesdb.net/banners/{boxart_text}"
            
            # Get fanart
            fanart = game.find(".//fanart")
            fanart_url = None
            if fanart is not None:
                original = fanart.find(".//original")
                if original is not None and original.text:
                    fanart_url = f"https://thegamesdb.net/banners/{original.text}"
            
            # Get banner
            banner = game.findtext(".//banner", "")
            banner_url = None
            if banner:
                banner_url = f"https://thegamesdb.net/banners/{banner}"
            
            # Return in v2-compatible format
            result = {
                "id": game_id,
                "game_title": game_title,
                "release_date": release_date,
                "boxart": boxart_url if boxart_url else {},
                "fanart": fanart_url if fanart_url else {},
                "banner": banner_url if banner_url else ""
            }
            
            return result
            
        except ET.ParseError as e:
            return None
        except Exception as e:
            # Only log unexpected errors
            if "404" not in str(e) and "update" not in str(e).lower():
                pass
            return None
    
    def _get_artwork_url(self, game_data: Dict, artwork_type: str = "boxart") -> Optional[str]:
        """
        Get artwork URL from game data.
        artwork_type can be: "boxart", "fanart", "banner"
        Handles TheGamesDB v1/v2 API formats and ScreenScraper API format.
        """
        try:
            # Handle ScreenScraper API format
            if self.api_source == "screenscraper":
                return self._get_artwork_url_screenscraper(game_data, artwork_type)
            
            # TheGamesDB API formats
            base_url = "https://cdn.thegamesdb.net/images/"
            
            if artwork_type == "boxart":
                boxart = game_data.get("boxart", {})
                
                # v1 API format: direct URL string
                if isinstance(boxart, str):
                    if boxart.startswith("http"):
                        return boxart
                    if boxart.startswith("/"):
                        return f"https://thegamesdb.net{boxart}"  # v1 uses thegamesdb.net
                    return f"https://thegamesdb.net/banners/{boxart}"  # v1 format
                
                # v2 API format: might be a list
                elif isinstance(boxart, list) and len(boxart) > 0:
                    # Array structure: [{"filename": "...", "side": "front"}]
                    for item in boxart:
                        if isinstance(item, dict):
                            filename = item.get("filename")
                            side = item.get("side", "")
                            if filename and (side == "front" or not side):
                                if filename.startswith("http"):
                                    return filename
                                url = f"{base_url}original/{filename}"
                                return url
                
                # v2 API format: nested dict
                elif isinstance(boxart, dict):
                    # TheGamesDB v2.0 structure: {"filename": "path", "side": "front", "base_url": {"original": "..."}}
                    filename = boxart.get("filename")
                    base_url_info = boxart.get("base_url", {})
                    
                    if filename:
                        # Construct URL from filename using base_url
                        if filename.startswith("http"):
                            return filename
                        
                        # Use base_url.original if available, otherwise fallback
                        if base_url_info and isinstance(base_url_info, dict):
                            original_base = base_url_info.get("original", "")
                            if original_base:
                                url = f"{original_base}{filename}"
                                return url
                        
                        # Fallback to default base URL construction
                        if filename.startswith("/"):
                            return f"https://cdn.thegamesdb.net{filename}"
                        return f"{base_url}original/{filename}"
                    
                    # Legacy: Check for nested structure: {"original": {"front": "path"}}
                    original = boxart.get("original", {})
                    if isinstance(original, dict):
                        front = original.get("front", "") or original.get("", "")
                        if front:
                            if front.startswith("http"):
                                return front
                            if front.startswith("/"):
                                return f"https://cdn.thegamesdb.net{front}"
                            return f"{base_url}original/{front}"
                    elif isinstance(original, str):
                        if original.startswith("http"):
                            return original
                        if original.startswith("/"):
                            return f"https://cdn.thegamesdb.net{original}"
                        return f"{base_url}original/{original}"
            
            elif artwork_type == "banner":
                banner = game_data.get("banner", {})
                
                # Debug logging for banners
                
                # v1 API: direct URL string
                if isinstance(banner, str):
                    if banner.startswith("http"):
                        return banner
                    if banner.startswith("/"):
                        return f"https://thegamesdb.net{banner}"  # v1
                    return f"https://thegamesdb.net/banners/{banner}"  # v1 format
                
                # v2 API format: might be a list
                elif isinstance(banner, list) and len(banner) > 0:
                    first_banner = banner[0]
                    if isinstance(first_banner, dict):
                        filename = first_banner.get("filename")
                        base_url_info = first_banner.get("base_url", {})
                        if filename:
                            if filename.startswith("http"):
                                return filename
                            if base_url_info and isinstance(base_url_info, dict):
                                original_base = base_url_info.get("original", "")
                                if original_base:
                                    url = f"{original_base}{filename}"
                                    return url
                            if filename.startswith("/"):
                                return f"https://cdn.thegamesdb.net{filename}"
                            url = f"{base_url}banner/{filename}"
                            return url
                
                # v2 API format: dict with filename
                elif isinstance(banner, dict):
                    filename = banner.get("filename")
                    base_url_info = banner.get("base_url", {})
                    
                    if filename:
                        if filename.startswith("http"):
                            return filename
                        
                        # Use base_url.original if available
                        if base_url_info and isinstance(base_url_info, dict):
                            original_base = base_url_info.get("original", "")
                            if original_base:
                                url = f"{original_base}{filename}"
                                return url
                        
                        # Fallback
                        if filename.startswith("/"):
                            url = f"https://cdn.thegamesdb.net{filename}"
                            return url
                        url = f"{base_url}banner/{filename}"
                        return url
                    else:
                        # Legacy format
                        banner_path = banner.get("", "") or banner.get("original", "")
                        if banner_path:
                            if banner_path.startswith("http"):
                                return banner_path
                            if banner_path.startswith("/"):
                                return f"https://cdn.thegamesdb.net{banner_path}"
                            return f"{base_url}banner/{banner_path}"
            
            elif artwork_type == "fanart":
                fanart = game_data.get("fanart", {})
                
                # Debug logging for fanart
                
                # v1 API format: direct URL string
                if isinstance(fanart, str):
                    if fanart.startswith("http"):
                        return fanart
                    if fanart.startswith("/"):
                        return f"https://thegamesdb.net{fanart}"  # v1
                    return f"https://thegamesdb.net/banners/{fanart}"  # v1 format
                
                # v2 API format: might be a list
                elif isinstance(fanart, list) and len(fanart) > 0:
                    first_fanart = fanart[0]
                    if isinstance(first_fanart, dict):
                        filename = first_fanart.get("filename")
                        base_url_info = first_fanart.get("base_url", {})
                        if filename:
                            if filename.startswith("http"):
                                return filename
                            if base_url_info and isinstance(base_url_info, dict):
                                original_base = base_url_info.get("original", "")
                                if original_base:
                                    url = f"{original_base}{filename}"
                                    return url
                            if filename.startswith("/"):
                                return f"https://cdn.thegamesdb.net{filename}"
                            url = f"{base_url}fanart/original/{filename}"
                            return url
                
                # v2 API format: dict with filename
                elif isinstance(fanart, dict):
                    filename = fanart.get("filename")
                    base_url_info = fanart.get("base_url", {})
                    
                    if filename:
                        if filename.startswith("http"):
                            return filename
                        
                        # Use base_url.original if available
                        if base_url_info and isinstance(base_url_info, dict):
                            original_base = base_url_info.get("original", "")
                            if original_base:
                                url = f"{original_base}{filename}"
                                return url
                        
                        # Fallback
                        if filename.startswith("/"):
                            url = f"https://cdn.thegamesdb.net{filename}"
                            return url
                        url = f"{base_url}fanart/original/{filename}"
                        return url
                    else:
                        # Legacy format
                        original = fanart.get("original", {})
                        if isinstance(original, dict):
                            orig_path = original.get("", "") or original.get("original", "")
                            if orig_path:
                                if orig_path.startswith("http"):
                                    return orig_path
                                if orig_path.startswith("/"):
                                    return f"https://cdn.thegamesdb.net{orig_path}"
                                return f"{base_url}fanart/original/{orig_path}"
                        elif isinstance(original, str):
                            if original.startswith("http"):
                                return original
                            if original.startswith("/"):
                                return f"https://cdn.thegamesdb.net{original}"
                            return f"{base_url}fanart/original/{original}"
            
            elif artwork_type == "screenshot":
                screenshot = game_data.get("screenshot", {})
                
                # Debug logging for screenshots
                
                # v1 API format: direct URL string
                if isinstance(screenshot, str):
                    if screenshot.startswith("http"):
                        return screenshot
                    if screenshot.startswith("/"):
                        return f"https://thegamesdb.net{screenshot}"  # v1
                    return f"https://thegamesdb.net/banners/{screenshot}"  # v1 format
                
                # v2 API format: might be a list
                elif isinstance(screenshot, list) and len(screenshot) > 0:
                    first_screenshot = screenshot[0]
                    if isinstance(first_screenshot, dict):
                        filename = first_screenshot.get("filename")
                        base_url_info = first_screenshot.get("base_url", {})
                        if filename:
                            if filename.startswith("http"):
                                return filename
                            if base_url_info and isinstance(base_url_info, dict):
                                original_base = base_url_info.get("original", "")
                                if original_base:
                                    url = f"{original_base}{filename}"
                                    return url
                            if filename.startswith("/"):
                                return f"https://cdn.thegamesdb.net{filename}"
                            url = f"{base_url}screenshot/{filename}"
                            return url
                
                # v2 API format: dict with filename
                elif isinstance(screenshot, dict):
                    filename = screenshot.get("filename")
                    base_url_info = screenshot.get("base_url", {})
                    
                    if filename:
                        if filename.startswith("http"):
                            return filename
                        
                        # Use base_url.original if available
                        if base_url_info and isinstance(base_url_info, dict):
                            original_base = base_url_info.get("original", "")
                            if original_base:
                                url = f"{original_base}{filename}"
                                return url
                        
                        # Fallback
                        if filename.startswith("/"):
                            url = f"https://cdn.thegamesdb.net{filename}"
                            return url
                        url = f"{base_url}screenshot/{filename}"
                        return url
            
            elif artwork_type == "titlescreen":
                titlescreen = game_data.get("titlescreen", {})
                
                # Debug logging for titlescreens
                
                # v1 API format: direct URL string
                if isinstance(titlescreen, str):
                    if titlescreen.startswith("http"):
                        return titlescreen
                    if titlescreen.startswith("/"):
                        return f"https://thegamesdb.net{titlescreen}"
                    return f"https://thegamesdb.net/banners/{titlescreen}"
                
                # v2 API format: might be a list
                elif isinstance(titlescreen, list) and len(titlescreen) > 0:
                    first_titlescreen = titlescreen[0]
                    if isinstance(first_titlescreen, dict):
                        filename = first_titlescreen.get("filename")
                        base_url_info = first_titlescreen.get("base_url", {})
                        if filename:
                            if filename.startswith("http"):
                                return filename
                            if base_url_info and isinstance(base_url_info, dict):
                                original_base = base_url_info.get("original", "")
                                if original_base:
                                    url = f"{original_base}{filename}"
                                    return url
                            if filename.startswith("/"):
                                return f"https://cdn.thegamesdb.net{filename}"
                            url = f"{base_url}titlescreen/{filename}"
                            return url
                
                # v2 API format: dict with filename
                elif isinstance(titlescreen, dict):
                    filename = titlescreen.get("filename")
                    base_url_info = titlescreen.get("base_url", {})
                    
                    if filename:
                        if filename.startswith("http"):
                            return filename
                        
                        if base_url_info and isinstance(base_url_info, dict):
                            original_base = base_url_info.get("original", "")
                            if original_base:
                                url = f"{original_base}{filename}"
                                return url
                        
                        if filename.startswith("/"):
                            url = f"https://cdn.thegamesdb.net{filename}"
                            return url
                        url = f"{base_url}titlescreen/{filename}"
                        return url
            
            elif artwork_type == "clearlogo":
                clearlogo = game_data.get("clearlogo", {})
                
                # Debug logging for clearlogos
                
                # v1 API format: direct URL string
                if isinstance(clearlogo, str):
                    if clearlogo.startswith("http"):
                        return clearlogo
                    if clearlogo.startswith("/"):
                        return f"https://thegamesdb.net{clearlogo}"
                    return f"https://thegamesdb.net/banners/{clearlogo}"
                
                # v2 API format: might be a list
                elif isinstance(clearlogo, list) and len(clearlogo) > 0:
                    first_clearlogo = clearlogo[0]
                    if isinstance(first_clearlogo, dict):
                        filename = first_clearlogo.get("filename")
                        base_url_info = first_clearlogo.get("base_url", {})
                        if filename:
                            if filename.startswith("http"):
                                return filename
                            if base_url_info and isinstance(base_url_info, dict):
                                original_base = base_url_info.get("original", "")
                                if original_base:
                                    url = f"{original_base}{filename}"
                                    return url
                            if filename.startswith("/"):
                                return f"https://cdn.thegamesdb.net{filename}"
                            url = f"{base_url}clearlogo/{filename}"
                            return url
                
                # v2 API format: dict with filename
                elif isinstance(clearlogo, dict):
                    filename = clearlogo.get("filename")
                    base_url_info = clearlogo.get("base_url", {})
                    
                    if filename:
                        if filename.startswith("http"):
                            return filename
                        
                        if base_url_info and isinstance(base_url_info, dict):
                            original_base = base_url_info.get("original", "")
                            if original_base:
                                url = f"{original_base}{filename}"
                                return url
                        
                        if filename.startswith("/"):
                            url = f"https://cdn.thegamesdb.net{filename}"
                            return url
                        url = f"{base_url}clearlogo/{filename}"
                        return url
            
            return None
        except Exception as e:
            print(f"Error getting artwork URL: {e}")
            return None
    
    def _get_artwork_url_screenscraper(self, game_data: Dict, artwork_type: str = "boxart") -> Optional[str]:
        """
        Get artwork URL from ScreenScraper game data.
        ScreenScraper API response structure:
        {
            "medias": {
                "box-2D": [{"url": "..."}],
                "banner-2D": [{"url": "..."}],
                "fanart": [{"url": "..."}]
            }
        }
        """
        try:
            medias = game_data.get("medias", {})
            if not medias:
                return None
            
            if artwork_type == "boxart":
                # Try different boxart keys
                boxart_list = medias.get("box-2D", []) or medias.get("box-3D", []) or medias.get("box-text", [])
                if boxart_list and len(boxart_list) > 0:
                    url = boxart_list[0].get("url", "")
                    if url:
                        # ScreenScraper URLs are relative, need to prepend base URL
                        if not url.startswith("http"):
                            return f"https://www.screenscraper.fr{url}"
                        return url
            
            elif artwork_type == "banner":
                banner_list = medias.get("banner-2D", []) or medias.get("banner", [])
                if banner_list and len(banner_list) > 0:
                    url = banner_list[0].get("url", "")
                    if url:
                        if not url.startswith("http"):
                            return f"https://www.screenscraper.fr{url}"
                        return url
            
            elif artwork_type == "fanart":
                fanart_list = medias.get("fanart", []) or medias.get("fanart-2D", [])
                if fanart_list and len(fanart_list) > 0:
                    url = fanart_list[0].get("url", "")
                    if url:
                        if not url.startswith("http"):
                            return f"https://www.screenscraper.fr{url}"
                        return url
            
            elif artwork_type == "screenshot":
                # ScreenScraper uses various screenshot keys
                screenshot_list = medias.get("ss", []) or medias.get("screenmarquee", []) or medias.get("sstitle", [])
                if screenshot_list and len(screenshot_list) > 0:
                    url = screenshot_list[0].get("url", "")
                    if url:
                        if not url.startswith("http"):
                            return f"https://www.screenscraper.fr{url}"
                        return url
            
            return None
        except Exception as e:
            print(f"Error getting ScreenScraper artwork URL: {e}")
            return None
    
    def _download_image(self, url: str, save_path: Path) -> bool:
        """
        Download an image from URL and save it to the specified path.
        """
        try:
            response = requests.get(url, timeout=15, stream=True)
            response.raise_for_status()
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
            return False
    
    def _get_all_rom_directories(self, emulator_short_name: str, stored_rom_directory: Optional[str] = None) -> List[Path]:
        """Get all possible ROM directories for an emulator (default + custom locations)
        
        This matches the logic from ROMCacheManager to ensure consistency.
        
        Args:
            emulator_short_name: Short name of the emulator
            stored_rom_directory: Optional stored rom_directory path from emulator data
        """
        directories = []
        
        # 1. Default ROM directory (same as ROMCacheManager)
        default_rom_dir = self.path_manager.get_path("roms") / emulator_short_name
        directories.append(default_rom_dir)
        
        # 2. Check if there's a global custom root with ROMs (same as ROMCacheManager)
        if self.path_manager.is_global_custom_path_active():
            global_root = self.path_manager.get_active_root_path()
            custom_rom_dir = global_root / "linux-gaming-center" / "roms" / emulator_short_name
            if custom_rom_dir != default_rom_dir:  # Avoid duplicates
                directories.append(custom_rom_dir)
        
        # 3. Check for individual custom ROM path (same as ROMCacheManager)
        individual_rom_path = self.path_manager.get_individual_custom_path("roms")
        if individual_rom_path:
            individual_rom_dir = individual_rom_path / emulator_short_name
            if individual_rom_dir not in directories:  # Avoid duplicates
                directories.append(individual_rom_dir)
        
        # 4. If stored_rom_directory exists and is different, add it as well
        # This handles cases where the path was stored but might not match current path_manager resolution
        if stored_rom_directory:
            stored_dir = Path(stored_rom_directory)
            # Only add if it's not already in the list and it's a valid directory
            if stored_dir not in directories:
                # Check if any existing directory resolves to the same path
                stored_resolved = stored_dir.resolve() if stored_dir.exists() else None
                is_duplicate = False
                if stored_resolved:
                    for existing_dir in directories:
                        if existing_dir.exists():
                            if existing_dir.resolve() == stored_resolved:
                                is_duplicate = True
                                break
                
                if not is_duplicate and stored_dir.exists() and stored_dir.is_dir():
                    directories.append(stored_dir)
        
        return directories
    
    def _scan_roms_for_emulator(self, emulator_short_name: str, stored_rom_directory: Optional[str] = None) -> Tuple[List[Path], List[str]]:
        """
        Scan all ROM directories for an emulator and return list of ROM file paths and diagnostic messages.
        Returns: (roms_list, diagnostic_messages)
        """
        roms = []
        messages = []
        
        rom_directories = self._get_all_rom_directories(emulator_short_name, stored_rom_directory)
        
        messages.append(f"Checking {len(rom_directories)} ROM directory(ies) for '{emulator_short_name}'...")
        if stored_rom_directory:
            messages.append(f"  Stored ROM directory: {stored_rom_directory}")
        default_path = self.path_manager.get_path('roms') / emulator_short_name
        messages.append(f"  Default path from path_manager: {default_path}")
        messages.append(f"  Default path exists: {default_path.exists()}")
        if self.path_manager.is_global_custom_path_active():
            global_root = self.path_manager.get_active_root_path()
            messages.append(f"  Global custom root: {global_root}")
        individual_rom_path = self.path_manager.get_individual_custom_path("roms")
        if individual_rom_path:
            messages.append(f"  Individual custom ROM path: {individual_rom_path}")
        
        for idx, rom_directory in enumerate(rom_directories, 1):
            messages.append(f"\n[{idx}/{len(rom_directories)}] Checking: {rom_directory}")
            messages.append(f"  Absolute path: {rom_directory.resolve() if rom_directory.exists() else 'N/A (does not exist)'}")
            
            if not rom_directory.exists():
                messages.append(f"  ⚠ Directory does not exist!")
                continue
            
            if not rom_directory.is_dir():
                messages.append(f"  ⚠ Path is not a directory!")
                continue
            
            messages.append(f"  ✓ Directory exists, scanning...")
            
            try:
                files_found = 0
                roms_found_in_dir = 0
                file_extensions_seen = set()
                
                for root, _, files in os.walk(rom_directory):
                    # Skip artwork folder
                    if Path(root).name == "artwork":
                        continue
                    
                    files_found += len(files)
                    
                    for filename in files:
                        # Track all file extensions we see
                        file_ext = Path(filename).suffix.lower()
                        if file_ext:
                            file_extensions_seen.add(file_ext)
                        
                        # Check if file has a ROM extension
                        file_lower = filename.lower()
                        matching_ext = None
                        for ext in COMMON_ROM_EXTENSIONS:
                            if file_lower.endswith(ext):
                                matching_ext = ext
                                break
                        
                        if matching_ext:
                            full_rom_path = Path(root) / filename
                            roms.append(full_rom_path)
                            roms_found_in_dir += 1
                
                messages.append(f"  Found {files_found} total file(s), {roms_found_in_dir} ROM file(s)")
                
                if files_found > 0:
                    messages.append(f"  File extensions found: {', '.join(sorted(file_extensions_seen)) if file_extensions_seen else 'none'}")
                
                if roms_found_in_dir == 0 and files_found > 0:
                    messages.append(f"  ℹ Files found but none match ROM extensions!")
                    messages.append(f"  Supported extensions: {', '.join(sorted(COMMON_ROM_EXTENSIONS))}")
                elif files_found == 0:
                    messages.append(f"  ℹ Directory is empty (no files found)")
                    
            except Exception as e:
                import traceback
                error_msg = f"  ✗ Error scanning directory: {e}"
                messages.append(error_msg)
                messages.append(f"  Traceback: {traceback.format_exc()}")
        
        if not roms:
            messages.append(f"\n❌ No ROM files found for {emulator_short_name}")
            messages.append(f"   Supported extensions: {', '.join(sorted(COMMON_ROM_EXTENSIONS))}")
        else:
            messages.append(f"\n✓ Found {len(roms)} ROM file(s) total")
        return roms, messages
    
    def scrape_emulator_artwork(self, emulator_short_name: str, emulator_full_name: str,
                               download_boxart: bool = True, download_banner: bool = True,
                               download_fanart: bool = False, download_screenshot: bool = False,
                               download_titlescreen: bool = False, download_clearlogo: bool = False,
                               stored_rom_directory: Optional[str] = None,
                               skip_scraping_check: bool = False) -> Dict:
        """
        Scrape artwork for all ROMs in an emulator's directory.
        
        Args:
            skip_scraping_check: If True, skip the scraping flag check (used when called from scrape_multiple_emulators)
        
        Returns a dictionary with statistics:
        {
            "total_roms": int,
            "scraped": int,
            "failed": int,
            "skipped": int
        }
        """
        # Only check scraping flag if not called from scrape_multiple_emulators
        if not skip_scraping_check:
            if self.scraping:
                return {"error": "Scraping already in progress"}
            
            with self._lock:
                if self.scraping:
                    return {"error": "Scraping already in progress"}
                self.scraping = True
        
        
        try:
            platform_id = PLATFORM_MAPPING.get(emulator_short_name.lower())
            if not platform_id:
                if not skip_scraping_check:
                    self.scraping = False
                return {
                    "error": f"Platform mapping not found for '{emulator_short_name}'. Platform not supported."
                }
            
            # Check API rate limit before starting to scrape (only for TheGamesDB)
            if self.api_source == "thegamesdb":
                self._notify_progress("Checking API rate limit...", 0, 0)
                rate_limit_info = self.check_thegamesdb_rate_limit()
                
                if rate_limit_info and rate_limit_info.get("limit_reached", False):
                    # Rate limit reached - stop before attempting to scrape
                    remaining = rate_limit_info.get("remaining", 0)
                    days = rate_limit_info.get("refresh_days", 0)
                    hours = rate_limit_info.get("refresh_hours", 0)
                    
                    error_msg = f"❌ Monthly API rate limit reached ({remaining} requests remaining)"
                    self._notify_progress(error_msg, 0, 0)
                    
                    quota_msg = "Your TheGamesDB API key has exhausted its monthly quota. Please wait for the allowance to refresh before scraping again."
                    self._notify_progress(quota_msg, 0, 0)
                    
                    if days > 0 or hours > 0:
                        refresh_msg = f"⏰ Allowance refreshes in approximately {days} day(s) and {hours} hour(s)"
                        self._notify_progress(refresh_msg, 0, 0)
                    
                    
                    if not skip_scraping_check:
                        self.scraping = False
                    
                    return {
                        "total_roms": 0,
                        "scraped": 0,
                        "failed": 0,
                        "skipped": 0,
                        "error": "Rate limit reached",
                        "rate_limit_info": {
                            "remaining": remaining,
                            "refresh_days": days,
                            "refresh_hours": hours
                        }
                    }
                elif rate_limit_info:
                    # Rate limit check succeeded - show remaining requests
                    remaining = rate_limit_info.get("remaining", 0)
                    if remaining > 0:
                        self._notify_progress(f"✓ API rate limit check: {remaining} requests remaining this month", 0, 0)
            
            # Get artwork directories (create artwork folder in all ROM directories)
            rom_directories = self._get_all_rom_directories(emulator_short_name, stored_rom_directory)
            if not rom_directories:
                if not skip_scraping_check:
                    self.scraping = False
                return {"error": "No ROM directories found for this emulator"}
            
            # Create media folder structure in all ROM directories
            media_dirs = []
            box2dfront_dirs = []
            screenshot_dirs = []
            steamgrid_dirs = []
            for rom_dir in rom_directories:
                media_dir = rom_dir / "media"
                box2dfront_dir = media_dir / "box2dfront"
                screenshot_dir = media_dir / "screenshot"
                steamgrid_dir = media_dir / "steamgrid"
                
                for directory in [media_dir, box2dfront_dir, screenshot_dir, steamgrid_dir]:
                    directory.mkdir(parents=True, exist_ok=True)
                
                media_dirs.append(media_dir)
                box2dfront_dirs.append(box2dfront_dir)
                screenshot_dirs.append(screenshot_dir)
                steamgrid_dirs.append(steamgrid_dir)
            
            # Use the first directories for saving (all ROM directories are scanned for ROMs)
            box2dfront_dir = box2dfront_dirs[0]
            screenshot_dir = screenshot_dirs[0]
            steamgrid_dir = steamgrid_dirs[0]
            
            # Scan ROMs
            import time
            self._notify_progress(f"Scanning ROMs for {emulator_full_name}...", 0, 0)
            time.sleep(0.1)
            
            roms, scan_messages = self._scan_roms_for_emulator(emulator_short_name, stored_rom_directory)
            
            # Report diagnostic messages - send each one with a small delay to ensure UI updates
            for msg in scan_messages:
                self._notify_progress(msg, 0, 0)
                time.sleep(0.05)  # Delay to allow UI to process messages
            
            if not roms:
                self.scraping = False
                error_details = "\n".join(scan_messages)
                return {
                    "total_roms": 0,
                    "scraped": 0,
                    "failed": 0,
                    "skipped": 0,
                    "error": "No ROMs found",
                    "details": error_details
                }
            
            total_roms = len(roms)
            scraped = 0
            failed = 0
            skipped = 0
            
            # Scrape artwork for each ROM
            for i, rom_path in enumerate(roms):
                if not self.scraping:  # Allow cancellation
                    break
                
                rom_name = self._get_rom_name_from_file(rom_path)
                self._notify_progress(
                    f"Scraping artwork for '{rom_name}'... ({i+1}/{total_roms})",
                    i + 1,
                    total_roms
                )
                
                # Search for game
                game_data = self._search_game(rom_name, platform_id, emulator_short_name)
                
                if not game_data:
                    failed += 1
                    continue
                
                # Get game title - handle both TheGamesDB and ScreenScraper formats
                if self.api_source == "screenscraper":
                    # ScreenScraper format: {"noms": [{"text": "Game Name"}]}
                    noms = game_data.get("noms", [])
                    game_title = noms[0].get("text", rom_name) if noms else rom_name
                else:
                    # TheGamesDB format
                    game_title = game_data.get("game_title", rom_name)
                # Clean game title for filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '', game_title)
                safe_title = safe_title[:100]  # Limit length
                
                success_count = 0
                
                # Download boxart to media/box2dfront/
                if download_boxart:
                    boxart_url = self._get_artwork_url(game_data, "boxart")
                    if boxart_url:
                        # Use ROM name as filename (stem = name without extension)
                        # Match ROM filename exactly: "3 Ninjas Kick Back (USA).zip" -> "3 Ninjas Kick Back (USA).jpg"
                        rom_name_clean = Path(rom_path).stem
                        boxart_path = box2dfront_dir / f"{rom_name_clean}.jpg"
                        # Try with .png if .jpg doesn't work
                        if boxart_path.exists():
                            # Check if we have .png instead
                            png_path = box2dfront_dir / f"{rom_name_clean}.png"
                            if png_path.exists():
                                boxart_path = png_path
                                success_count += 1
                            else:
                                success_count += 1  # Already exists
                        else:
                            if self._download_image(boxart_url, boxart_path):
                                success_count += 1
                            else:
                                if boxart_path.exists():
                                    boxart_path.unlink()  # Remove failed download
                
                # Download banner to media/steamgrid/ (banner-style images)
                if download_banner:
                    banner_url = self._get_artwork_url(game_data, "banner")
                    if banner_url:
                        rom_name_clean = Path(rom_path).stem
                        banner_path = steamgrid_dir / f"{rom_name_clean}.jpg"
                        if not banner_path.exists():  # Skip if already exists
                            if self._download_image(banner_url, banner_path):
                                success_count += 1
                            else:
                                if banner_path.exists():
                                    banner_path.unlink()
                        else:
                            success_count += 1
                
                # Download fanart to media/steamgrid/ (banner-style images)
                if download_fanart:
                    fanart_url = self._get_artwork_url(game_data, "fanart")
                    if fanart_url:
                        rom_name_clean = Path(rom_path).stem
                        fanart_path = steamgrid_dir / f"{rom_name_clean}_fanart.jpg"
                        if not fanart_path.exists():  # Skip if already exists
                            if self._download_image(fanart_url, fanart_path):
                                success_count += 1
                            else:
                                if fanart_path.exists():
                                    fanart_path.unlink()
                        else:
                            success_count += 1
                
                # Download screenshot to media/screenshot/
                if download_screenshot:
                    screenshot_url = self._get_artwork_url(game_data, "screenshot")
                    if screenshot_url:
                        rom_name_clean = Path(rom_path).stem
                        screenshot_path = screenshot_dir / f"{rom_name_clean}.jpg"
                        if not screenshot_path.exists():  # Skip if already exists
                            if self._download_image(screenshot_url, screenshot_path):
                                success_count += 1
                            else:
                                if screenshot_path.exists():
                                    screenshot_path.unlink()
                        else:
                            success_count += 1
                
                # Download titlescreen to media/screenshot/
                if download_titlescreen:
                    titlescreen_url = self._get_artwork_url(game_data, "titlescreen")
                    if titlescreen_url:
                        rom_name_clean = Path(rom_path).stem
                        titlescreen_path = screenshot_dir / f"{rom_name_clean}_titlescreen.jpg"
                        if not titlescreen_path.exists():  # Skip if already exists
                            if self._download_image(titlescreen_url, titlescreen_path):
                                success_count += 1
                            else:
                                if titlescreen_path.exists():
                                    titlescreen_path.unlink()
                        else:
                            success_count += 1
                
                # Download clearlogo to media/box2dfront/ (clearlogo can be used as boxart alternative)
                if download_clearlogo:
                    clearlogo_url = self._get_artwork_url(game_data, "clearlogo")
                    if clearlogo_url:
                        rom_name_clean = Path(rom_path).stem
                        clearlogo_path = box2dfront_dir / f"{rom_name_clean}_clearlogo.png"
                        if not clearlogo_path.exists():  # Skip if already exists
                            if self._download_image(clearlogo_url, clearlogo_path):
                                success_count += 1
                            else:
                                if clearlogo_path.exists():
                                    clearlogo_path.unlink()
                        else:
                            success_count += 1
                
                if success_count > 0:
                    scraped += 1
                else:
                    skipped += 1
            
            result = {
                "total_roms": total_roms,
                "scraped": scraped,
                "failed": failed,
                "skipped": skipped
            }
            
            # Only reset scraping flag if we're managing it ourselves
            if not skip_scraping_check:
                self.scraping = False
            return result
            
        except Exception as e:
            # Only reset scraping flag if we're managing it ourselves
            if not skip_scraping_check:
                self.scraping = False
            return {"error": f"Error during scraping: {str(e)}"}
        finally:
            # Only reset scraping flag if we're managing it ourselves
            if not skip_scraping_check:
                self.scraping = False
    
    def scrape_multiple_emulators(self, emulators: List[Dict],
                                  download_boxart: bool = True,
                                  download_banner: bool = True,
                                  download_fanart: bool = False,
                                  download_screenshot: bool = False,
                                  download_titlescreen: bool = False,
                                  download_clearlogo: bool = False):
        """
        Scrape artwork for multiple emulators in a background thread.
        emulators should be a list of dicts with 'short_name' and 'full_name' keys.
        """
        if self.scraping:
            self._notify_completion(False, "Scraping already in progress")
            return
        
        # Set scraping flag to True when starting
        with self._lock:
            if self.scraping:
                self._notify_completion(False, "Scraping already in progress")
                return
            self.scraping = True
        
        def scrape_worker():
            try:
                total_emulators = len(emulators)
                overall_results = {
                    "total_emulators": total_emulators,
                    "results": []
                }
                
                # Check API rate limit BEFORE starting to scrape any emulators (only for TheGamesDB)
                if self.api_source == "thegamesdb":
                    self._notify_progress("Checking API rate limit...", 0, 0)
                    rate_limit_info = self.check_thegamesdb_rate_limit()
                    
                    if rate_limit_info and rate_limit_info.get("limit_reached", False):
                        # Rate limit reached - stop before attempting to scrape
                        remaining = rate_limit_info.get("remaining", 0)
                        days = rate_limit_info.get("refresh_days", 0)
                        hours = rate_limit_info.get("refresh_hours", 0)
                        
                        self._notify_progress(f"\n{'='*60}", 0, 0)
                        self._notify_progress("❌ RATE LIMIT REACHED", 0, 0)
                        self._notify_progress(f"{'='*60}\n", 0, 0)
                        self._notify_progress(f"Monthly API rate limit reached ({remaining} requests remaining)", 0, 0)
                        self._notify_progress("Your TheGamesDB API key has exhausted its monthly quota.", 0, 0)
                        
                        if days > 0 or hours > 0:
                            refresh_msg = f"⏰ Allowance refreshes in approximately {days} day(s) and {hours} hour(s)"
                            self._notify_progress(refresh_msg, 0, 0)
                        
                        self._notify_progress("\nPlease wait for your quota to refresh before trying again.", 0, 0)
                        self._notify_completion(False, "Scraping cancelled: Monthly API rate limit reached")
                        return
                    elif rate_limit_info:
                        # Rate limit check succeeded - show remaining requests
                        remaining = rate_limit_info.get("remaining", 0)
                        if remaining > 0:
                            self._notify_progress(f"✓ API rate limit check: {remaining} requests remaining this month", 0, 0)
                        else:
                            # This shouldn't happen, but handle it just in case
                            self._notify_progress("⚠️ API rate limit check completed, but remaining requests is 0", 0, 0)
                
                for i, emulator in enumerate(emulators):
                    if not self.scraping:  # Allow cancellation
                        break
                    
                    short_name = emulator.get("short_name", "")
                    full_name = emulator.get("full_name", "Unknown Emulator")
                    stored_rom_dir = emulator.get("rom_directory")
                    
                    try:
                        self._notify_progress(
                            f"Scraping artwork for {full_name}... ({i+1}/{total_emulators})",
                            i + 1,
                            total_emulators
                        )
                    except Exception as e:
                        # Error in progress callback is logged silently
                        pass
                    
                    # Get stored rom_directory if available
                    try:
                        result = self.scrape_emulator_artwork(
                            short_name,
                            full_name,
                            download_boxart,
                            download_banner,
                            download_fanart,
                            download_screenshot,
                            download_titlescreen,
                            download_clearlogo,
                            stored_rom_directory=stored_rom_dir,
                            skip_scraping_check=True  # Skip check since we're already in scrape_multiple_emulators
                        )
                    except Exception as e:
                        import traceback
                        result = {"error": str(e), "traceback": traceback.format_exc()}
                    
                    result["emulator"] = full_name
                    overall_results["results"].append(result)
                    
                    # Check if rate limit was reached - stop processing further emulators
                    if "error" in result and result.get("error") == "Rate limit reached":
                        rate_limit_info = result.get("rate_limit_info", {})
                        days = rate_limit_info.get("refresh_days", 0)
                        hours = rate_limit_info.get("refresh_hours", 0)
                        
                        # Show rate limit message and stop
                        self._notify_progress(f"\n{'='*60}", 0, 0)
                        self._notify_progress("⚠️ RATE LIMIT REACHED - Stopping scraping", 0, 0)
                        self._notify_progress(f"{'='*60}\n", 0, 0)
                        
                        if days > 0 or hours > 0:
                            refresh_msg = f"Please wait {days} day(s) and {hours} hour(s) before scraping again."
                            self._notify_progress(refresh_msg, 0, 0)
                        
                        break  # Stop processing remaining emulators
                    
                    # If there's an error or details, show them in progress
                    if "error" in result:
                        # Add a separator before error details
                        self._notify_progress(f"\n--- Error for {full_name} ---", 0, 0)
                        error_msg = f"Error: {result.get('error', 'Unknown error')}"
                        self._notify_progress(error_msg, 0, 0)
                        if "details" in result:
                            # Send each detail line separately so they all appear in the UI
                            details_lines = result["details"].split('\n')
                            for detail_line in details_lines:
                                if detail_line.strip():  # Only send non-empty lines
                                    self._notify_progress(detail_line, 0, 0)
                                    import time
                                    time.sleep(0.005)  # Small delay to ensure UI updates
                        self._notify_progress("--- End of error details ---\n", 0, 0)
                
                # Check if rate limit was reached in any result
                rate_limit_reached = any(
                    r.get("error") == "Rate limit reached" for r in overall_results["results"]
                )
                
                if rate_limit_reached:
                    # Rate limit was reached - show final message
                    self._notify_progress(f"\n{'='*60}", 0, 0)
                    self._notify_progress("SCRAPING STOPPED DUE TO RATE LIMIT", 0, 0)
                    self._notify_progress(f"{'='*60}\n", 0, 0)
                    self._notify_progress("Your TheGamesDB API key has exhausted its monthly quota.", 0, 0)
                    
                    # Get rate limit info from the first result that has it
                    for r in overall_results["results"]:
                        if r.get("error") == "Rate limit reached" and "rate_limit_info" in r:
                            rate_info = r["rate_limit_info"]
                            days = rate_info.get("refresh_days", 0)
                            hours = rate_info.get("refresh_hours", 0)
                            if days > 0 or hours > 0:
                                refresh_msg = f"Allowance refreshes in {days} day(s) and {hours} hour(s)."
                                self._notify_progress(refresh_msg, 0, 0)
                            break
                    
                    self._notify_progress("\nPlease wait for your quota to refresh before trying again.", 0, 0)
                    self._notify_completion(False, "Scraping stopped: Monthly API rate limit reached")
                    return
                
                # Create summary message
                total_roms = sum(r.get("total_roms", 0) for r in overall_results["results"])
                total_scraped = sum(r.get("scraped", 0) for r in overall_results["results"])
                total_failed = sum(r.get("failed", 0) for r in overall_results["results"])
                
                if total_roms == 0:
                    import time
                    time.sleep(0.2)  # Ensure all diagnostic messages are displayed first
                    
                    # Send a separator before the summary
                    self._notify_progress("\n" + "="*60, 0, 0)
                    self._notify_progress("SUMMARY", 0, 0)
                    self._notify_progress("="*60, 0, 0)
                    time.sleep(0.1)
                    
                    message = f"No ROMs found in any of the selected emulator directories.\n\n"
                    message += "Please check:\n"
                    message += "1. ROM files exist in the console's ROM directory\n"
                    message += "2. Files have supported extensions (.nes, .snes, .ps2, etc.)\n"
                    message += "3. The ROM directory path is correct"
                    
                    # Send summary message to progress window as well (split into lines)
                    for line in message.split('\n'):
                        if line.strip():
                            self._notify_progress(line, 0, 0)
                            time.sleep(0.05)
                    
                    # Include details from results if available
                    error_details = []
                    for r in overall_results["results"]:
                        if "details" in r:
                            error_details.append(f"{r.get('emulator', 'Unknown')}:\n{r['details']}")
                    if error_details:
                        detail_msg = "\n\nDetailed scan results:\n" + "\n\n".join(error_details)
                        # Send each line of details to progress window
                        for detail_line in detail_msg.split('\n'):
                            if detail_line.strip():
                                self._notify_progress(detail_line, 0, 0)
                                time.sleep(0.02)
                        message += detail_msg
                    
                    time.sleep(0.3)  # Final delay to ensure all messages are displayed
                    self._notify_completion(False, message)
                else:
                    message = f"Scraping complete! Processed {total_roms} ROMs across {total_emulators} emulator(s). "
                    message += f"Successfully scraped: {total_scraped}, Failed: {total_failed}"
                    
                    self._notify_completion(True, message)
                
            except Exception as e:
                import traceback
                error_details = f"Error during scraping: {str(e)}\n{traceback.format_exc()}"
                self._notify_completion(False, f"Error during scraping: {str(e)}")
            finally:
                # Always reset scraping flag when worker completes
                with self._lock:
                    self.scraping = False
        
        thread = threading.Thread(target=scrape_worker, daemon=True)
        thread.start()
    
    def cancel_scraping(self):
        """Cancel ongoing scraping operation"""
        self.scraping = False
    
    def is_scraping(self) -> bool:
        """Check if scraping is currently in progress"""
        return self.scraping

