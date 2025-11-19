# Linux Gaming Center

A comprehensive gaming center for Linux that provides a unified interface for managing and launching games, emulators, and applications.

## Features

- **Game Library Management**: Organize and launch your favorite games
- **Emulator Support**: Manage and configure various gaming emulators with dynamic frame generation
- **Open Source Games**: Discover and play open source games
- **Windows/Steam/Wine Integration**: Run Windows games through Wine
- **Application Management**: Launch and manage your favorite applications
- **User Profiles**: Multiple user accounts with personalized settings and admin support
- **Theme Support**: Customizable themes with unified styling system
- **Store Integration**: Download and install new games and applications
- **Path Management**: Flexible directory configuration with XDG compliance
- **Recent Items**: Track and quickly access recently played games and apps
- **Random Game**: Launch a random game from your library
- **Backup System**: Backup and restore your gaming library

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/linux-gaming-center.git
cd linux-gaming-center
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

## Requirements

- Python 3.8+
- tkinter (usually included with Python)
- PIL (Pillow) 11.3.0+
- pygame 2.6.1+
- requests 2.32.4+

## Configuration

The application follows XDG Base Directory Specification and stores data in:
- `~/.config/linux-gaming-center/` - Configuration files and user accounts
- `~/.local/share/linux-gaming-center/` - User data, game libraries, ROMs, and BIOS files

### Custom Path Configuration

You can configure custom directories for your data through the Directories settings in the application. This allows you to:
- Set a global custom root directory for all application data
- Override individual categories (ROMs, BIOS, themes, etc.) with custom paths
- Maintain XDG compliance while providing flexibility

## Architecture

The application is built with a modular architecture:

- **Main Application** (`main.py`): Core application controller and frame management
- **Path Manager** (`paths.py`): Centralized path management with XDG compliance
- **Theme System** (`theme.py`): Unified theming with frame-specific overrides
- **Base Frame** (`data/frames/base_frame.py`): Common functionality for all frames
- **Frame Modules**: Individual modules for different application sections
- **Utilities** (`utils.py`): Common utility functions
- **Configuration** (`config.py`): Application-wide configuration settings

## File Structure

```
linux-gaming-center/
├── main.py                 # Main application entry point
├── menu.py                 # Menu bar implementation
├── theme.py                # Theme management system
├── paths.py                # Path management with XDG compliance
├── config.py               # Application configuration
├── utils.py                # Utility functions
├── data/
│   ├── frames/             # UI frame modules
│   │   ├── base_frame.py   # Base frame class
│   │   ├── dashboard.py    # Main dashboard
│   │   ├── login.py        # User authentication
│   │   ├── emulators.py    # Emulator management
│   │   ├── open_source_gaming.py  # Open source games
│   │   ├── windows_steam_wine.py  # Windows/Steam/Wine games
│   │   ├── apps.py         # Application management
│   │   └── ...             # Other frame modules
│   ├── themes/             # Theme files
│   │   └── cosmictwilight/
│   │       ├── styles/     # Theme style definitions
│   │       └── images/     # Theme images
│   └── store/              # Store data
└── resources/              # Application resources
    └── emulator_mappings.json
```

## Development

### Code Style

The codebase follows Python best practices:
- Type hints where appropriate
- Comprehensive error handling
- Modular design with clear separation of concerns
- Consistent naming conventions (snake_case for files, PascalCase for classes)

### Adding New Features

1. Create new frame modules in `data/frames/`
2. Inherit from `BaseFrame` for common functionality
3. Add theme support through the unified theme system
4. Update the main application controller to register new frames

### Theme Development

Themes are defined in JSON files under `data/themes/[theme_name]/styles/`:
- `theme_config.json`: Base theme configuration
- `[frame_name].json`: Frame-specific theme overrides

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Version History

### v1.0.0 (Current)
- Complete refactoring and cleanup
- Unified theme system
- XDG-compliant path management
- Improved error handling
- Better code organization
- Enhanced user experience

## Support

For support, please open an issue on GitHub or contact the maintainer.