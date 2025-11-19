import os
import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable

# Try to import PIL for image pre-loading
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

# Common ROM extensions - centralized definition
COMMON_ROM_EXTENSIONS = {
    '.nes', '.snes', '.gb', '.bin', '.chd', '.cue', '.gba', '.gen', '.md', '.n64', '.ps1', '.iso',
    '.zip', '.7z', '.rar', '.j64', '.jag', '.rom', '.abs', '.cof', '.prg'
}

class ROMCacheManager:
    """
    Manages ROM scanning and caching to prevent UI blocking.
    Scans ROMs in background threads and provides cached results.
    """
    
    def __init__(self, path_manager):
        self.path_manager = path_manager
        self.cache_file = self.path_manager.get_path("data") / "rom_cache.json"
        self.cache = {}
        self.scanning = False
        self.scan_progress = 0
        self.scan_total = 0
        self.scan_current_emulator = ""
        self.progress_callbacks = []
        self.completion_callbacks = []
        self.frame_notification_callbacks = []
        self._lock = threading.Lock()
        
        # Image cache: stores PIL Images (not PhotoImage) for all ROMs
        # Key: (emulator_short_name, rom_path) -> PIL Image
        self.image_cache = {}  # Shared image cache accessible by all frames
        self.image_loading = False
        self.image_progress = 0
        self.image_total = 0
        
        # Load existing cache if available
        self.load_cache()
    
    def add_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Add a callback for progress updates: callback(progress, total, current_emulator)"""
        self.progress_callbacks.append(callback)
    
    def add_completion_callback(self, callback: Callable[[], None]):
        """Add a callback for when scanning is complete"""
        self.completion_callbacks.append(callback)
    
    def add_frame_notification_callback(self, callback: Callable[[], None]):
        """Add a callback to notify frames when scanning is complete"""
        self.frame_notification_callbacks.append(callback)
    
    def load_cache(self):
        """Load ROM cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self.cache = json.load(f)
                # Loaded ROM cache
            except Exception as e:
                # Error loading ROM cache
                self.cache = {}
        else:
            self.cache = {}
    
    def save_cache(self):
        """Save ROM cache to disk"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            # Saved ROM cache
        except Exception as e:
            # Error saving ROM cache
            pass
    
    def get_emulator_roms(self, emulator_short_name: str) -> List[Dict]:
        """Get cached ROMs for a specific emulator"""
        with self._lock:
            return self.cache.get(emulator_short_name, {}).get('roms', [])
    
    def get_all_roms(self) -> List[Dict]:
        """Get all cached ROMs from all emulators"""
        all_roms = []
        with self._lock:
            for emulator_data in self.cache.values():
                all_roms.extend(emulator_data.get('roms', []))
        return all_roms
    
    def is_scanning(self) -> bool:
        """Check if ROM scanning is currently in progress"""
        return self.scanning
    
    def get_scan_progress(self) -> tuple:
        """Get current scan progress: (current, total, current_emulator)"""
        return (self.scan_progress, self.scan_total, self.scan_current_emulator)
    
    def scan_emulator_roms(self, emulator_data: Dict) -> List[Dict]:
        """Scan ROMs for a single emulator from all possible locations"""
        full_emulator_name = emulator_data.get("full_name", "Unknown Emulator")
        short_emulator_name = emulator_data.get("short_name", "")
        run_script_path = Path(emulator_data.get("run_script_path", ""))
        
        roms = []
        
        if not run_script_path.exists():
            # Warning: Run script not found
            return roms
        
        # Get all possible ROM directories for this emulator
        rom_directories = self._get_all_rom_directories(short_emulator_name)
        
        # Scanning ROMs
        
        for rom_directory in rom_directories:
            if not rom_directory.exists() or not rom_directory.is_dir():
                # Warning: ROM directory not found
                continue
            
            try:
                for root, _, files in os.walk(rom_directory):
                    for filename in files:
                        if any(filename.lower().endswith(ext) for ext in COMMON_ROM_EXTENSIONS):
                            full_rom_path = Path(root) / filename
                            roms.append({
                                "rom_path": str(full_rom_path),
                                "display_name": filename,
                                "emulator_name": full_emulator_name,
                                "emulator_short_name": short_emulator_name,
                                "run_script_path": str(run_script_path)
                            })
            except Exception as e:
                # Error: Failed to scan ROMs
                pass
        
        return roms
    
    def _get_all_rom_directories(self, emulator_short_name: str) -> List[Path]:
        """Get all possible ROM directories for an emulator (default + custom locations)"""
        directories = []
        
        # 1. Default ROM directory
        default_rom_dir = self.path_manager.get_path("roms") / emulator_short_name
        directories.append(default_rom_dir)
        
        # 2. Check if there's a global custom root with ROMs
        if self.path_manager.is_global_custom_path_active():
            global_root = self.path_manager.get_active_root_path()
            custom_rom_dir = global_root / "linux-gaming-center" / "roms" / emulator_short_name
            if custom_rom_dir != default_rom_dir:  # Avoid duplicates
                directories.append(custom_rom_dir)
        
        # 3. Check for individual custom ROM path
        individual_rom_path = self.path_manager.get_individual_custom_path("roms")
        if individual_rom_path:
            individual_rom_dir = individual_rom_path / emulator_short_name
            if individual_rom_dir not in directories:  # Avoid duplicates
                directories.append(individual_rom_dir)
        
        # 4. Also check if there are any other custom locations we might have missed
        # This could be expanded in the future for additional path sources
        
        return directories
    
    def start_background_scan(self, emulators_data: List[Dict]):
        """Start background ROM scanning"""
        if self.scanning:
            # ROM scan already in progress
            return
        
        # Starting background scan
        self.scanning = True
        self.scan_progress = 0
        self.scan_total = len(emulators_data)
        
        # Check if we have a valid cache for all emulators
        cached_emulators = set(self.cache.keys())
        emulator_short_names = {emulator.get("short_name") for emulator in emulators_data}
        
        if cached_emulators.issuperset(emulator_short_names):
            # Valid cache found for all emulators, doing quick validation scan
            # We have cache for all emulators, do a quick validation
            self._do_quick_validation_scan(emulators_data)
            return
        
        def scan_worker():
            try:
                # Starting background ROM scan
                
                for i, emulator_data in enumerate(emulators_data):
                    if not self.scanning:  # Check if scan was cancelled
                        break
                    
                    short_name = emulator_data.get("short_name", "")
                    full_name = emulator_data.get("full_name", "Unknown Emulator")
                    
                    self.scan_current_emulator = full_name
                    self.scan_progress = i
                    
                    # Notify progress callbacks
                    for callback in self.progress_callbacks:
                        try:
                            callback(self.scan_progress, self.scan_total, self.scan_current_emulator)
                        except Exception as e:
                            # Error in progress callback
                            pass
                    
                    # Scan ROMs for this emulator
                    roms = self.scan_emulator_roms(emulator_data)
                    
                    # Update cache
                    with self._lock:
                        self.cache[short_name] = {
                            'emulator_data': emulator_data,
                            'roms': roms,
                            'last_scan': time.time()
                        }
                    
                    # Scanned ROMs
                    
                    # Small delay to prevent overwhelming the system
                    time.sleep(0.1)
                
                # Final progress update
                self.scan_progress = self.scan_total
                self.scan_current_emulator = "Complete"
                
                for callback in self.progress_callbacks:
                    try:
                        callback(self.scan_progress, self.scan_total, self.scan_current_emulator)
                    except Exception as e:
                        # Error in progress callback
                        pass
                
                # Save cache
                self.save_cache()
                
                # Background ROM scan complete
                
                # Now pre-load all images for all scanned ROMs
                # This happens before completion callbacks are fired
                self._preload_all_images(emulators_data)
                
            except Exception as e:
                # Error during background ROM scan
                pass
            finally:
                # Background scan completed
                self.scanning = False
                
                # Only notify completion after images are loaded
                # Wait for image loading to complete
                while self.image_loading:
                    time.sleep(0.1)
                
                # Notify completion callbacks
                # Calling completion callbacks
                for callback in self.completion_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        # Error in completion callback
                        pass
                
                # Notify frame callbacks
                # Calling frame notification callbacks
                for callback in self.frame_notification_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        # Error in frame notification callback
                        pass
        
        # Start the background thread
        scan_thread = threading.Thread(target=scan_worker, daemon=True)
        scan_thread.start()
    
    def _do_quick_validation_scan(self, emulators_data: List[Dict]):
        """Do a quick validation scan when cache exists"""
        def validation_worker():
            try:
                # Starting quick validation scan
                
                for i, emulator_data in enumerate(emulators_data):
                    short_name = emulator_data.get("short_name", "")
                    full_name = emulator_data.get("full_name", "Unknown Emulator")
                    
                    self.scan_current_emulator = f"Validating {full_name}"
                    self.scan_progress = i
                    
                    # Notify progress callbacks
                    for callback in self.progress_callbacks:
                        try:
                            callback(self.scan_progress, self.scan_total, self.scan_current_emulator)
                        except Exception as e:
                            # Error in progress callback
                            pass
                    
                    # Small delay to show progress
                    time.sleep(0.5)
                
                # Final progress update
                self.scan_progress = self.scan_total
                self.scan_current_emulator = "Cache validation complete"
                
                for callback in self.progress_callbacks:
                    try:
                        callback(self.scan_progress, self.scan_total, self.scan_current_emulator)
                    except Exception as e:
                        # Error in progress callback
                        pass
                
                # Quick validation scan complete
                
                # Now pre-load all images for all cached ROMs
                # This happens before completion callbacks are fired
                self._preload_all_images(emulators_data)
                
            except Exception as e:
                # Error during quick validation scan
                pass
            finally:
                # Validation scan completed
                self.scanning = False
                
                # Only notify completion after images are loaded
                # Wait for image loading to complete
                while self.image_loading:
                    time.sleep(0.1)
                
                # Notify completion callbacks
                # Calling completion callbacks
                for callback in self.completion_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        # Error in completion callback
                        pass
                
                # Notify frame callbacks
                # Calling frame notification callbacks
                for callback in self.frame_notification_callbacks:
                    try:
                        callback()
                    except Exception as e:
                        # Error in frame notification callback
                        pass
        
        # Start the validation thread
        validation_thread = threading.Thread(target=validation_worker, daemon=True)
        validation_thread.start()
    
    def invalidate_emulator_cache(self, emulator_short_name: str):
        """Invalidate cache for a specific emulator"""
        with self._lock:
            if emulator_short_name in self.cache:
                del self.cache[emulator_short_name]
                self.save_cache()
    
    def invalidate_all_cache(self):
        """Invalidate entire cache"""
        with self._lock:
            self.cache.clear()
            if self.cache_file.exists():
                self.cache_file.unlink()
    
    def force_full_rescan(self):
        """Force a full rescan by clearing the cache"""
        # Forcing full rescan by clearing cache
        self.invalidate_all_cache()
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            total_roms = sum(len(data.get('roms', [])) for data in self.cache.values())
            return {
                'emulators_cached': len(self.cache),
                'total_roms': total_roms,
                'cache_file_size': self.cache_file.stat().st_size if self.cache_file.exists() else 0
            }
    
    def _preload_all_images(self, emulators_data: List[Dict]):
        """Pre-load all PIL Images for all ROMs during startup"""
        if not PIL_AVAILABLE:
            return
        
        self.image_loading = True
        total_roms = 0
        all_roms = []
        
        # Collect all ROMs from all emulators
        with self._lock:
            for emulator_data in emulators_data:
                short_name = emulator_data.get("short_name", "")
                if short_name in self.cache:
                    roms = self.cache[short_name].get('roms', [])
                    for rom_info in roms:
                        all_roms.append((short_name, rom_info))
                        total_roms += 1
        
        self.image_total = total_roms
        self.image_progress = 0
        
        if total_roms == 0:
            self.image_loading = False
            return
        
        # Update progress: "Loading images: 0/total"
        for callback in self.progress_callbacks:
            try:
                callback(self.scan_total, self.scan_total, f"Loading images: 0/{total_roms}")
            except Exception:
                pass
        
        # Pre-load images for each ROM
        loaded_count = 0
        for short_name, rom_info in all_roms:
            rom_path = rom_info.get("rom_path", "")
            if not rom_path:
                continue
            
            # Get box2dfront directory for this emulator
            rom_dirs = self._get_all_rom_directories(short_name)
            box2dfront_dir = None
            for rom_dir in rom_dirs:
                media_dir = rom_dir / "media" / "box2dfront"
                if media_dir.exists():
                    box2dfront_dir = media_dir
                    break
            if not box2dfront_dir and rom_dirs:
                box2dfront_dir = rom_dirs[0] / "media" / "box2dfront"
            
            if not box2dfront_dir or not box2dfront_dir.exists():
                self.image_progress += 1
                continue
            
            # Get ROM name without extension
            rom_name = Path(rom_path).stem
            
            # Look for boxart image
            boxart_path = None
            for ext in ['.jpg', '.jpeg', '.png']:
                potential_path = box2dfront_dir / f"{rom_name}{ext}"
                if potential_path.exists():
                    boxart_path = potential_path
                    break
            
            if boxart_path:
                try:
                    # Load and resize image (target size: 150x200 for buttons)
                    target_width = 150
                    target_height = 200
                    
                    img = Image.open(boxart_path)
                    
                    if img.width > 0 and img.height > 0 and target_width > 0 and target_height > 0:
                        # Convert to RGB if necessary
                        if img.mode not in ('RGB', 'RGBA'):
                            img = img.convert('RGB')
                        
                        # Resize to target dimensions
                        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                        
                        if img.width > 0 and img.height > 0:
                            # Store PIL Image in cache (not PhotoImage - no X11 resource)
                            cache_key = (short_name, rom_path)
                            self.image_cache[cache_key] = img
                            loaded_count += 1
                except Exception:
                    # Skip images that fail to load
                    pass
            
            self.image_progress += 1
            
            # Update progress every 50 images
            if self.image_progress % 50 == 0 or self.image_progress == total_roms:
                for callback in self.progress_callbacks:
                    try:
                        callback(self.scan_total, self.scan_total, 
                               f"Loading images: {self.image_progress}/{total_roms}")
                    except Exception:
                        pass
        
        self.image_loading = False
        
        # Final progress update - mark as complete
        for callback in self.progress_callbacks:
            try:
                callback(self.scan_total, self.scan_total, 
                       f"Loaded {loaded_count} images - Ready!")
            except Exception:
                pass
    
    def get_image_cache(self, emulator_short_name: str, rom_path: str) -> Optional:
        """Get pre-loaded PIL Image from cache"""
        if not PIL_AVAILABLE:
            return None
        cache_key = (emulator_short_name, rom_path)
        return self.image_cache.get(cache_key)
