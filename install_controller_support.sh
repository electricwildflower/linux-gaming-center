#!/bin/bash

# Linux Gaming Center - Controller Support Installation Script
# This script installs pygame for controller support

echo "Linux Gaming Center - Controller Support Installation"
echo "=================================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root. It will use sudo when needed."
    exit 1
fi

# Detect package manager and install pygame
if command -v apt &> /dev/null; then
    echo "Detected apt package manager. Installing pygame..."
    sudo apt update
    sudo apt install -y python3-pygame
elif command -v yum &> /dev/null; then
    echo "Detected yum package manager. Installing pygame..."
    sudo yum install -y python3-pygame
elif command -v dnf &> /dev/null; then
    echo "Detected dnf package manager. Installing pygame..."
    sudo dnf install -y python3-pygame
elif command -v pacman &> /dev/null; then
    echo "Detected pacman package manager. Installing pygame..."
    sudo pacman -S python-pygame
elif command -v zypper &> /dev/null; then
    echo "Detected zypper package manager. Installing pygame..."
    sudo zypper install python3-pygame
else
    echo "No supported package manager found. Please install pygame manually:"
    echo "  pip3 install pygame"
    echo "  or"
    echo "  python3 -m pip install pygame"
    exit 1
fi

# Verify installation
echo "Verifying pygame installation..."
python3 -c "import pygame; print('pygame version:', pygame.version.ver); print('Controller support enabled!')"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Controller support successfully installed!"
    echo "You can now use game controllers with Linux Gaming Center."
    echo ""
    echo "To configure controllers:"
    echo "1. Start Linux Gaming Center"
    echo "2. Go to Account Settings"
    echo "3. Click 'Open Controller Settings'"
    echo "4. Scan for and configure your controllers"
else
    echo ""
    echo "❌ Installation failed. Please try installing pygame manually:"
    echo "  pip3 install pygame"
fi
