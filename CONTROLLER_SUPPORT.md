# Controller Support for Linux Gaming Center

Linux Gaming Center now includes comprehensive game controller support, allowing users to navigate the application and control games using their favorite game controllers.

## Features

- **Controller Detection**: Automatically scan for connected game controllers
- **Button Mapping**: Customize button mappings for navigation and control
- **Per-User Profiles**: Each user can have their own controller configurations
- **Real-time Testing**: Test controller inputs to verify configurations
- **Universal Navigation**: Use controllers to navigate throughout the application
- **Multiple Controller Support**: Configure and use multiple controllers simultaneously

## Installation

### Automatic Installation
Run the provided installation script:
```bash
./install_controller_support.sh
```

### Manual Installation
Install pygame using your system's package manager:

**Ubuntu/Debian:**
```bash
sudo apt install python3-pygame
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-pygame
```

**Arch Linux:**
```bash
sudo pacman -S python-pygame
```

**Using pip:**
```bash
pip3 install pygame
```

## Configuration

### Setting Up Controllers

1. **Start Linux Gaming Center** and log in to your account
2. **Navigate to Account Settings** from the profile menu
3. **Click "Open Controller Settings"** in the Controller Settings section
4. **Scan for Controllers** by clicking "Scan for Controllers"
5. **Add Controllers** by selecting a detected controller and clicking "Add Controller"
6. **Configure Button Mappings** for each controller
7. **Test Your Configuration** using the built-in input test

### Default Button Mappings

| Button | Action | Description |
|--------|--------|-------------|
| A Button | Select | Activate focused item |
| B Button | Back | Go back or cancel |
| X Button | Menu | Open context menu |
| Y Button | Home | Go to dashboard |
| D-Pad | Navigation | Move focus up/down/left/right |
| Start | Menu | Open main menu |
| Back/Select | Back | Go back |
| Guide/Home | Home | Go to dashboard |

### Customizing Mappings

You can customize button mappings for each controller:

1. Select a configured controller from the list
2. Modify the button mappings in the "Button Mappings" section
3. Choose from available actions:
   - **up**: Navigate up
   - **down**: Navigate down
   - **left**: Navigate left
   - **right**: Navigate right
   - **select**: Activate/select item
   - **back**: Go back
   - **menu**: Open menu
   - **home**: Go to dashboard

## Navigation

### Dashboard Navigation
- Use D-pad or left stick to navigate between library buttons
- Press A button to select a library
- Press B button to go back to login
- Press Y button to refresh dashboard

### General Navigation
- **D-pad/Left Stick**: Navigate between UI elements
- **A Button**: Activate focused element
- **B Button**: Go back or cancel
- **X Button**: Open context menu
- **Y Button**: Go to dashboard
- **Start Button**: Open main menu
- **Guide Button**: Go to dashboard

## Supported Controllers

The controller system supports most standard game controllers including:

- **Xbox Controllers** (Xbox 360, Xbox One, Xbox Series)
- **PlayStation Controllers** (PS3, PS4, PS5)
- **Nintendo Controllers** (Switch Pro Controller, Joy-Cons)
- **Generic USB Controllers**
- **Bluetooth Controllers**

## Troubleshooting

### Controller Not Detected
1. Ensure the controller is properly connected (USB or Bluetooth)
2. Check that pygame is installed correctly
3. Try running the application with elevated permissions
4. Verify the controller works in other applications

### Buttons Not Responding
1. Check button mappings in Controller Settings
2. Ensure the controller is enabled
3. Test controller inputs using the built-in test feature
4. Verify the controller is properly configured

### Navigation Issues
1. Check that controller monitoring is enabled
2. Verify button mappings are correct
3. Try restarting the application
4. Check for conflicting input devices

## Technical Details

### File Locations
- **Controller Configurations**: `~/.config/linux-gaming-center/accounts/[username]/controller_config.json`
- **Global Configuration**: `~/.config/linux-gaming-center/controller_config.json`

### Configuration Format
```json
{
  "controllers": [
    {
      "controller_id": 0,
      "controller_name": "Xbox 360 Controller",
      "enabled": true,
      "button_mappings": {
        "A": "select",
        "B": "back",
        "X": "menu",
        "Y": "home",
        "DPAD_UP": "up",
        "DPAD_DOWN": "down",
        "DPAD_LEFT": "left",
        "DPAD_RIGHT": "right"
      },
      "deadzone": 0.1,
      "sensitivity": 1.0
    }
  ]
}
```

### API Reference

The controller system provides several classes and methods:

- **ControllerManager**: Main controller management class
- **ControllerConfig**: Configuration data structure
- **NavigationAction**: Available navigation actions
- **ControllerButton**: Standard button mappings

## Development

### Adding Controller Support to New Frames

To add controller navigation support to a new frame, implement these methods:

```python
def controller_navigate_up(self):
    """Handle controller up navigation"""
    pass

def controller_navigate_down(self):
    """Handle controller down navigation"""
    pass

def controller_navigate_left(self):
    """Handle controller left navigation"""
    pass

def controller_navigate_right(self):
    """Handle controller right navigation"""
    pass

def controller_select(self):
    """Handle controller select action"""
    pass

def controller_back(self):
    """Handle controller back action"""
    pass

def controller_menu(self):
    """Handle controller menu action"""
    pass

def controller_home(self):
    """Handle controller home action"""
    pass
```

### Registering Navigation Callbacks

```python
from controller_manager import get_controller_manager, NavigationAction

controller_manager = get_controller_manager()

# Register custom navigation callback
controller_manager.register_navigation_callback(
    NavigationAction.SELECT.value,
    my_custom_select_function
)
```

## Contributing

To contribute to controller support:

1. Test with various controller types
2. Report bugs and compatibility issues
3. Suggest new features and improvements
4. Submit pull requests with enhancements

## License

Controller support is part of Linux Gaming Center and follows the same license terms.
