# ZeroLag Linux Installation Guide

## System Requirements

- **Operating System**: Ubuntu 18.04+, Debian 10+, Fedora 32+, Arch Linux, or similar
- **Architecture**: 64-bit (x64) or 32-bit (x86)
- **Python**: 3.8 or later
- **Display Server**: X11 or Wayland
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 100MB free space
- **Permissions**: May require root privileges for input monitoring

## Distribution-Specific Installation

### Ubuntu/Debian

#### Step 1: Update System
```bash
sudo apt update
sudo apt upgrade
```

#### Step 2: Install Python and Dependencies
```bash
# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install PyQt5 and system dependencies
sudo apt install python3-pyqt5 python3-pyqt5.qtwidgets python3-pyqt5.qtcore python3-pyqt5.qtgui

# Install additional dependencies
sudo apt install python3-dev libx11-dev libxtst-dev libxrandr-dev libxinerama-dev libxcursor-dev libxi-dev
```

#### Step 3: Install Python Packages
```bash
# Install required packages
pip3 install pynput psutil

# Optional: Install development dependencies
pip3 install pytest pytest-qt
```

#### Step 4: Download and Run ZeroLag
```bash
# Clone repository
git clone https://github.com/imsnokfr/zerolag.git
cd zerolag

# Run ZeroLag
python3 run_gui.py
```

### Fedora/RHEL/CentOS

#### Step 1: Update System
```bash
sudo dnf update
```

#### Step 2: Install Python and Dependencies
```bash
# Install Python and pip
sudo dnf install python3 python3-pip python3-venv

# Install PyQt5 and system dependencies
sudo dnf install python3-qt5 python3-qt5-devel

# Install additional dependencies
sudo dnf install python3-devel libX11-devel libXtst-devel libXrandr-devel libXinerama-devel libXcursor-devel libXi-devel
```

#### Step 3: Install Python Packages
```bash
pip3 install pynput psutil
```

### Arch Linux

#### Step 1: Update System
```bash
sudo pacman -Syu
```

#### Step 2: Install Python and Dependencies
```bash
# Install Python and pip
sudo pacman -S python python-pip python-virtualenv

# Install PyQt5 and system dependencies
sudo pacman -S python-pyqt5

# Install additional dependencies
sudo pacman -S libx11 libxtst libxrandr libxinerama libxcursor libxi
```

#### Step 3: Install Python Packages
```bash
pip install pynput psutil
```

### openSUSE

#### Step 1: Update System
```bash
sudo zypper update
```

#### Step 2: Install Python and Dependencies
```bash
# Install Python and pip
sudo zypper install python3 python3-pip python3-virtualenv

# Install PyQt5 and system dependencies
sudo zypper install python3-qt5 python3-qt5-devel

# Install additional dependencies
sudo zypper install python3-devel libX11-devel libXtst-devel libXrandr-devel libXinerama-devel libXcursor-devel libXi-devel
```

## Linux-Specific Configuration

### Input Device Permissions

#### Method 1: Add User to Input Group
```bash
# Add current user to input group
sudo usermod -a -G input $USER

# Log out and log back in for changes to take effect
```

#### Method 2: Set Input Device Permissions
```bash
# Find input devices
ls /dev/input/

# Set permissions (temporary)
sudo chmod 666 /dev/input/event*

# Make permanent (add to udev rules)
sudo nano /etc/udev/rules.d/99-input-permissions.rules
```

Add the following content:
```
# Allow input device access
KERNEL=="event*", MODE="0666"
KERNEL=="mouse*", MODE="0666"
KERNEL=="js*", MODE="0666"
```

Then reload udev rules:
```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Display Server Configuration

#### X11 Configuration
For X11 users, ensure proper input handling:
```bash
# Check if X11 is running
echo $XDG_SESSION_TYPE

# If using X11, ensure input permissions
xinput list
```

#### Wayland Configuration
For Wayland users, some features may be limited:
```bash
# Check if Wayland is running
echo $XDG_SESSION_TYPE

# For Wayland, may need to switch to X11 for full functionality
# Check your display manager settings
```

### System Tray Configuration

#### Desktop Environment Support
ZeroLag's system tray works with most desktop environments:

- **GNOME**: Requires extension for system tray
- **KDE**: Native support
- **XFCE**: Native support
- **LXDE**: Native support
- **MATE**: Native support

#### GNOME System Tray Extension
```bash
# Install GNOME Shell extension for system tray
# Use GNOME Extensions app or install via browser
# Search for "TopIcons Plus" or "AppIndicator Support"
```

## Troubleshooting

### Common Issues

#### "Permission denied" for input devices
```bash
# Check current permissions
ls -la /dev/input/

# Add user to input group
sudo usermod -a -G input $USER

# Log out and back in
```

#### "Module not found" errors
```bash
# Update pip
python3 -m pip install --upgrade pip

# Reinstall packages
pip3 install --upgrade pynput psutil

# Check Python path
echo $PYTHONPATH
```

#### GUI not displaying
```bash
# Check display server
echo $DISPLAY

# Test PyQt5 installation
python3 -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"

# Check for missing libraries
ldd /usr/lib/python3/dist-packages/PyQt5/QtCore.so
```

#### Input not working
```bash
# Check input device permissions
ls -la /dev/input/

# Test with root privileges (temporary)
sudo python3 run_gui.py

# Check for conflicting input handlers
ps aux | grep -i input
```

### Performance Issues

#### High CPU usage
```bash
# Check system load
top
htop

# Check for background processes
ps aux | grep zerolag

# Monitor resource usage
python3 -c "import psutil; print(psutil.cpu_percent())"
```

#### Memory issues
```bash
# Check memory usage
free -h

# Check for memory leaks
ps aux --sort=-%mem | head

# Monitor ZeroLag memory usage
ps aux | grep zerolag
```

### Desktop Environment Issues

#### GNOME Issues
```bash
# Install system tray extension
# Use GNOME Extensions website or app

# Check GNOME version
gnome-shell --version

# Restart GNOME Shell
Alt+F2, type 'r', press Enter
```

#### KDE Issues
```bash
# Check KDE version
plasmashell --version

# Restart Plasma
killall plasmashell && plasmashell &
```

#### XFCE Issues
```bash
# Check XFCE version
xfce4-panel --version

# Restart panel
xfce4-panel -r
```

## Linux-Specific Features

### Limited Features on Linux
- **DPI Emulation**: Not available (handled by display server)
- **Polling Rate Control**: Limited by kernel and hardware
- **Global Hotkeys**: Depends on window manager
- **Input Optimization**: May require root privileges

### Available Features
- ✅ Basic input handling
- ✅ GUI interface
- ✅ System tray integration
- ✅ Profile management
- ✅ Performance monitoring
- ✅ Mouse and keyboard optimization

### Window Manager Compatibility

#### Full Support
- **KDE Plasma**: Full system tray and hotkey support
- **XFCE**: Full system tray support
- **MATE**: Full system tray support
- **LXDE**: Full system tray support

#### Partial Support
- **GNOME**: Requires extensions for system tray
- **Cinnamon**: Good system tray support
- **Budgie**: Limited system tray support

#### Limited Support
- **i3**: No system tray, limited hotkey support
- **Awesome**: No system tray, limited hotkey support
- **Openbox**: No system tray, limited hotkey support

## Security Considerations

### Input Monitoring
- ZeroLag monitors keyboard and mouse input
- Requires appropriate permissions
- Data is processed locally
- No network transmission

### Root Privileges
- Some features may require root access
- Only run as root when necessary
- Consider using sudo for specific operations

### File Permissions
```bash
# Set appropriate permissions
chmod 755 run_gui.py
chmod 644 *.py

# Secure configuration files
chmod 600 config.json
```

## Performance Optimization

### System Optimization
```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups

# Optimize for gaming
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### ZeroLag Optimization
1. **Polling Rate**: Adjust based on hardware capabilities
2. **Profile Management**: Use appropriate profiles for different games
3. **Performance Monitoring**: Monitor resource usage
4. **Input Settings**: Optimize for your input devices

## Package Management

### Creating Package
```bash
# Create setup.py
cat > setup.py << EOF
from setuptools import setup, find_packages

setup(
    name="zerolag",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "pynput>=1.7.0",
        "psutil>=5.8.0",
    ],
    entry_points={
        "console_scripts": [
            "zerolag=src.gui.main_window:main",
        ],
    },
)
EOF

# Install in development mode
pip3 install -e .
```

### Creating .deb Package (Ubuntu/Debian)
```bash
# Install build tools
sudo apt install python3-stdeb

# Create package
python3 setup.py --command-packages=stdeb.command bdist_deb

# Install package
sudo dpkg -i deb_dist/zerolag_1.0.0-1_all.deb
```

### Creating .rpm Package (Fedora/RHEL)
```bash
# Install build tools
sudo dnf install python3-setuptools-rpm

# Create package
python3 setup.py bdist_rpm

# Install package
sudo rpm -i dist/zerolag-1.0.0-1.noarch.rpm
```

## Development Setup

### For Developers
```bash
# Clone repository
git clone https://github.com/imsnokfr/zerolag.git
cd zerolag

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run GUI
python run_gui.py
```

### IDE Configuration
- **VS Code**: Install Python extension and Linux-specific tools
- **PyCharm**: Configure Python interpreter and Linux environment
- **Sublime Text**: Install Python package and Linux tools
- **Vim/Neovim**: Configure Python support and Linux integration

## Uninstallation

### Remove Python Packages
```bash
pip3 uninstall pynput psutil
```

### Remove System Dependencies
```bash
# Ubuntu/Debian
sudo apt remove python3-pyqt5

# Fedora
sudo dnf remove python3-qt5

# Arch Linux
sudo pacman -R python-pyqt5
```

### Remove ZeroLag Files
```bash
# Remove installation directory
rm -rf ~/zerolag

# Remove configuration files
rm -rf ~/.config/zerolag
rm -rf ~/.local/share/zerolag
```

### Restore Input Permissions
```bash
# Remove from input group
sudo gpasswd -d $USER input

# Restore default permissions
sudo chmod 644 /dev/input/event*
```

## Support

### Getting Help
- Check this installation guide
- Review troubleshooting section
- Test with minimal configuration
- Report issues with distribution details

### System Information
When reporting issues, include:
- Distribution and version
- Desktop environment
- Python version
- Installed packages list
- Error messages
- System specifications

### Log Files
ZeroLag creates log files in:
- `~/.config/zerolag/logs/`
- Check for error messages
- Include relevant log entries when reporting issues

## Conclusion

ZeroLag works on most Linux distributions with some limitations compared to Windows. Follow this guide for the best installation experience. Some features may require additional configuration or may not be available due to Linux security model and display server limitations.
