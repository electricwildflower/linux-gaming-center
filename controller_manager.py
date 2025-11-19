"""
Controller Manager for Linux Gaming Center
Handles game controller detection, configuration, and navigation support.
"""

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    # Warning: pygame not available. Controller support will be limited.

import json
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

class ControllerButton(Enum):
    """Standard controller button mappings"""
    A = 0
    B = 1
    X = 2
    Y = 3
    LEFT_BUMPER = 4
    RIGHT_BUMPER = 5
    BACK = 6
    START = 7
    LEFT_STICK = 8
    RIGHT_STICK = 9
    DPAD_UP = 10
    DPAD_DOWN = 11
    DPAD_LEFT = 12
    DPAD_RIGHT = 13
    GUIDE = 14

class NavigationAction(Enum):
    """Navigation actions for the application"""
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    SELECT = "select"
    BACK = "back"
    MENU = "menu"
    HOME = "home"

@dataclass
class ControllerConfig:
    """Configuration for a specific controller"""
    controller_id: int
    controller_name: str
    enabled: bool = True
    button_mappings: Dict[str, str] = None  # button -> action mapping
    deadzone: float = 0.1
    sensitivity: float = 1.0
    
    def __post_init__(self):
        if self.button_mappings is None:
            self.button_mappings = self.get_default_mappings()
    
    def get_default_mappings(self) -> Dict[str, str]:
        """Get default button mappings"""
        return {
            "A": NavigationAction.SELECT.value,
            "B": NavigationAction.BACK.value,
            "X": NavigationAction.MENU.value,
            "Y": NavigationAction.HOME.value,
            "DPAD_UP": NavigationAction.UP.value,
            "DPAD_DOWN": NavigationAction.DOWN.value,
            "DPAD_LEFT": NavigationAction.LEFT.value,
            "DPAD_RIGHT": NavigationAction.RIGHT.value,
            "START": NavigationAction.MENU.value,
            "BACK": NavigationAction.BACK.value,
            "GUIDE": NavigationAction.HOME.value
        }

class ControllerManager:
    """Main controller management class"""
    
    def __init__(self, path_manager=None):
        self.path_manager = path_manager
        self.controllers: Dict[int, Any] = {}
        self.controller_configs: Dict[int, ControllerConfig] = {}
        self.navigation_callbacks: Dict[str, Callable] = {}
        self.is_running = False
        self.scan_thread = None
        self.current_user = None
        
        # Initialize pygame if available
        if PYGAME_AVAILABLE:
            try:
                # Initialize pygame with specific modules to avoid video system issues
                pygame.mixer.quit()  # Quit mixer to avoid conflicts
                pygame.init()
                pygame.joystick.init()
                # Controller support enabled - pygame initialized successfully
            except Exception as e:
                # Warning: pygame initialization failed
                # Controller support disabled - pygame not available
                pass
        else:
            # Controller support disabled - pygame not available
            pass
        
        # Load existing configurations
        self.load_controller_configs()
    
    def set_current_user(self, username: str):
        """Set the current user for controller profile loading"""
        self.current_user = username
        self.load_controller_configs()
    
    def get_controller_config_path(self) -> Path:
        """Get the path for controller configuration file"""
        if self.path_manager and self.current_user:
            accounts_path = self.path_manager.get_path("accounts")
            return accounts_path / self.current_user / "controller_config.json"
        else:
            # Fallback to default location
            return Path.home() / ".config" / "linux-gaming-center" / "controller_config.json"
    
    def load_controller_configs(self):
        """Load controller configurations from file"""
        config_path = self.get_controller_config_path()
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    for config_data in data.get('controllers', []):
                        config = ControllerConfig(**config_data)
                        self.controller_configs[config.controller_id] = config
            except Exception as e:
                # Error loading controller configs
                pass
    
    def save_controller_configs(self):
        """Save controller configurations to file"""
        config_path = self.get_controller_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            data = {
                'controllers': [asdict(config) for config in self.controller_configs.values()]
            }
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            # Error saving controller configs
            pass
    
    def scan_for_controllers(self) -> List[Dict[str, Any]]:
        """Scan for connected controllers and return their info"""
        if not PYGAME_AVAILABLE:
            return []
        
        pygame.joystick.quit()
        pygame.joystick.init()
        
        controllers = []
        for i in range(pygame.joystick.get_count()):
            joystick = pygame.joystick.Joystick(i)
            joystick.init()
            
            controller_info = {
                'id': i,
                'name': joystick.get_name(),
                'num_axes': joystick.get_numaxes(),
                'num_buttons': joystick.get_numbuttons(),
                'num_hats': joystick.get_numhats(),
                'guid': joystick.get_guid() if hasattr(joystick, 'get_guid') else f"controller_{i}"
            }
            controllers.append(controller_info)
        
        return controllers
    
    def add_controller(self, controller_id: int, controller_name: str) -> ControllerConfig:
        """Add a new controller configuration"""
        config = ControllerConfig(
            controller_id=controller_id,
            controller_name=controller_name
        )
        self.controller_configs[controller_id] = config
        self.save_controller_configs()
        return config
    
    def remove_controller(self, controller_id: int):
        """Remove a controller configuration"""
        if controller_id in self.controller_configs:
            del self.controller_configs[controller_id]
            self.save_controller_configs()
    
    def update_controller_config(self, controller_id: int, **kwargs):
        """Update controller configuration"""
        if controller_id in self.controller_configs:
            config = self.controller_configs[controller_id]
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            self.save_controller_configs()
    
    def register_navigation_callback(self, action: str, callback: Callable):
        """Register a callback for navigation actions"""
        self.navigation_callbacks[action] = callback
    
    def unregister_navigation_callback(self, action: str):
        """Unregister a navigation callback"""
        if action in self.navigation_callbacks:
            del self.navigation_callbacks[action]
    
    def start_controller_monitoring(self):
        """Start monitoring controllers for input"""
        if not PYGAME_AVAILABLE:
            # Controller monitoring disabled - pygame not available
            return
            
        if self.is_running:
            return
        
        self.is_running = True
        self.scan_thread = threading.Thread(target=self._monitor_controllers, daemon=True)
        self.scan_thread.start()
    
    def stop_controller_monitoring(self):
        """Stop monitoring controllers"""
        self.is_running = False
        if self.scan_thread:
            self.scan_thread.join(timeout=1.0)
    
    def _monitor_controllers(self):
        """Monitor controllers for input in a separate thread"""
        if not PYGAME_AVAILABLE:
            return
            
        clock = pygame.time.Clock()
        
        while self.is_running:
            try:
                # Process pygame events
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        self._handle_button_press(event.joy, event.button)
                    elif event.type == pygame.JOYHATMOTION:
                        self._handle_hat_motion(event.joy, event.hat, event.value)
                    elif event.type == pygame.JOYAXISMOTION:
                        self._handle_axis_motion(event.joy, event.axis, event.value)
                
                clock.tick(60)  # 60 FPS
            except Exception as e:
                # Error in controller monitoring
                time.sleep(0.1)
    
    def _handle_button_press(self, controller_id: int, button: int):
        """Handle button press events"""
        if controller_id not in self.controller_configs:
            return
        
        config = self.controller_configs[controller_id]
        if not config.enabled:
            return
        
        # Map button number to button name
        button_name = self._get_button_name(button)
        if button_name in config.button_mappings:
            action = config.button_mappings[button_name]
            self._trigger_navigation_action(action)
    
    def _handle_hat_motion(self, controller_id: int, hat: int, value: tuple):
        """Handle D-pad/hat motion events"""
        if controller_id not in self.controller_configs:
            return
        
        config = self.controller_configs[controller_id]
        if not config.enabled:
            return
        
        # Map hat value to direction
        direction = self._get_hat_direction(value)
        if direction and direction in config.button_mappings:
            action = config.button_mappings[direction]
            self._trigger_navigation_action(action)
    
    def _handle_axis_motion(self, controller_id: int, axis: int, value: float):
        """Handle analog stick motion events"""
        if controller_id not in self.controller_configs:
            return
        
        config = self.controller_configs[controller_id]
        if not config.enabled:
            return
        
        # Apply deadzone
        if abs(value) < config.deadzone:
            return
        
        # Map axis to direction (simplified - could be enhanced)
        if axis == 0:  # Left stick X
            if value > 0:
                self._trigger_navigation_action("right")
            else:
                self._trigger_navigation_action("left")
        elif axis == 1:  # Left stick Y
            if value > 0:
                self._trigger_navigation_action("down")
            else:
                self._trigger_navigation_action("up")
    
    def _get_button_name(self, button: int) -> str:
        """Map button number to button name"""
        button_map = {
            0: "A", 1: "B", 2: "X", 3: "Y",
            4: "LEFT_BUMPER", 5: "RIGHT_BUMPER",
            6: "BACK", 7: "START",
            8: "LEFT_STICK", 9: "RIGHT_STICK",
            10: "GUIDE"
        }
        return button_map.get(button, f"BUTTON_{button}")
    
    def _get_hat_direction(self, value: tuple) -> Optional[str]:
        """Map hat value to direction name"""
        x, y = value
        if y == 1:
            return "DPAD_UP"
        elif y == -1:
            return "DPAD_DOWN"
        elif x == -1:
            return "DPAD_LEFT"
        elif x == 1:
            return "DPAD_RIGHT"
        return None
    
    def _trigger_navigation_action(self, action: str):
        """Trigger a navigation action callback"""
        if action in self.navigation_callbacks:
            try:
                self.navigation_callbacks[action]()
            except Exception as e:
                # Error in navigation callback
                pass
    
    def get_controller_info(self, controller_id: int) -> Optional[Dict[str, Any]]:
        """Get information about a specific controller"""
        if not PYGAME_AVAILABLE:
            return None
            
        if controller_id < pygame.joystick.get_count():
            joystick = pygame.joystick.Joystick(controller_id)
            return {
                'id': controller_id,
                'name': joystick.get_name(),
                'num_axes': joystick.get_numaxes(),
                'num_buttons': joystick.get_numbuttons(),
                'num_hats': joystick.get_numhats(),
                'connected': True
            }
        return None
    
    def test_controller_input(self, controller_id: int, duration: float = 5.0) -> List[Dict[str, Any]]:
        """Test controller input for a specified duration"""
        if not PYGAME_AVAILABLE:
            return []
            
        if controller_id >= pygame.joystick.get_count():
            return []
        
        joystick = pygame.joystick.Joystick(controller_id)
        joystick.init()
        
        inputs = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.joy == controller_id:
                    inputs.append({
                        'type': 'button',
                        'button': event.button,
                        'name': self._get_button_name(event.button),
                        'timestamp': time.time() - start_time
                    })
                elif event.type == pygame.JOYHATMOTION and event.joy == controller_id:
                    direction = self._get_hat_direction(event.value)
                    if direction:
                        inputs.append({
                            'type': 'hat',
                            'direction': direction,
                            'value': event.value,
                            'timestamp': time.time() - start_time
                        })
                elif event.type == pygame.JOYAXISMOTION and event.joy == controller_id:
                    if abs(event.value) > 0.1:  # Deadzone
                        inputs.append({
                            'type': 'axis',
                            'axis': event.axis,
                            'value': event.value,
                            'timestamp': time.time() - start_time
                        })
        
        return inputs
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_controller_monitoring()
        if PYGAME_AVAILABLE:
            try:
                pygame.joystick.quit()
                pygame.quit()
            except Exception as e:
                # Warning: pygame cleanup failed
                pass

# Global controller manager instance
_controller_manager = None

def get_controller_manager(path_manager=None) -> ControllerManager:
    """Get the global controller manager instance"""
    global _controller_manager
    if _controller_manager is None:
        _controller_manager = ControllerManager(path_manager)
    return _controller_manager
