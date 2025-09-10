# ZeroLag Cross-Platform Compatibility Guide

## Overview

ZeroLag is designed to work across multiple operating systems, with full support for Windows and partial support for macOS and Linux. This document outlines the compatibility status, requirements, and known limitations for each platform.

## Platform Support Matrix

| Feature | Windows 10/11 | macOS | Linux |
|---------|---------------|-------|-------|
| **Core Functionality** | ✅ Full | ⚠️ Partial | ⚠️ Partial |
| **GUI (PyQt5)** | ✅ Full | ✅ Full | ✅ Full |
| **Input Handling** | ✅ Full | ⚠️ Limited | ⚠️ Limited |
| **System Tray** | ✅ Full | ✅ Full | ✅ Full |
| **Hotkeys** | ✅ Full | ⚠️ Limited | ⚠️ Limited |
| **DPI Emulation** | ✅ Full | ❌ Not Available | ❌ Not Available |
| **Polling Rate** | ✅ Full | ⚠️ Limited | ⚠️ Limited |
| **Performance Monitoring** | ✅ Full | ✅ Full | ✅ Full |

## Windows Compatibility

### Supported Versions
- **Windows 10** (Build 1903 or later)
- **Windows 11** (All versions)

### Requirements
- Python 3.8 or later
- PyQt5 5.15 or later
- pynput library
- pywin32 (for Windows-specific features)

### Features Available
- ✅ Full input optimization
- ✅ DPI emulation and scaling
- ✅ High-frequency polling (up to 8000Hz)
- ✅ System tray integration
- ✅ Global hotkeys
- ✅ Performance monitoring
- ✅ Profile management
- ✅ Emergency stop functionality

### Installation
```bash
# Install Python dependencies
pip install PyQt5 pynput pywin32 psutil

# Run ZeroLag
python run_gui.py
```

### Known Issues
- Some Windows versions may require administrator privileges for certain input optimizations
- Windows Defender may flag the application as potentially unwanted software due to input monitoring

## macOS Compatibility

### Supported Versions
- **macOS 10.15** (Catalina) or later
- **macOS 11+** (Big Sur, Monterey, Ventura, Sonoma)

### Requirements
- Python 3.8 or later
- PyQt5 5.15 or later
- pynput library
- Accessibility permissions (required for input monitoring)

### Features Available
- ✅ Basic input handling
- ✅ GUI interface
- ✅ System tray integration
- ✅ Profile management
- ✅ Performance monitoring
- ⚠️ Limited hotkey support (requires accessibility permissions)
- ❌ No DPI emulation (macOS handles this natively)
- ❌ Limited polling rate control

### Installation
```bash
# Install Python dependencies
pip install PyQt5 pynput psutil

# Grant accessibility permissions in System Preferences
# System Preferences > Security & Privacy > Privacy > Accessibility

# Run ZeroLag
python run_gui.py
```

### Known Issues
- Requires accessibility permissions for input monitoring
- Some input optimizations may not work due to macOS security restrictions
- Global hotkeys may not work in all applications

## Linux Compatibility

### Supported Distributions
- **Ubuntu** 18.04 or later
- **Debian** 10 or later
- **Fedora** 32 or later
- **Arch Linux** (latest)
- **openSUSE** 15.2 or later

### Requirements
- Python 3.8 or later
- PyQt5 5.15 or later
- pynput library
- X11 or Wayland display server
- Appropriate input device permissions

### Features Available
- ✅ Basic input handling
- ✅ GUI interface
- ✅ System tray integration
- ✅ Profile management
- ✅ Performance monitoring
- ⚠️ Limited hotkey support (depends on window manager)
- ❌ No DPI emulation (handled by display server)
- ❌ Limited polling rate control

### Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pyqt5 python3-pip
pip install pynput psutil

# Fedora
sudo dnf install python3-PyQt5 python3-pip
pip install pynput psutil

# Arch Linux
sudo pacman -S python-pyqt5 python-pip
pip install pynput psutil

# Run ZeroLag
python run_gui.py
```

### Known Issues
- May require running as root for certain input optimizations
- Hotkey support varies by window manager
- Some input features may not work in Wayland sessions

## Platform-Specific Considerations

### Input Handling Differences

#### Windows
- Full access to low-level input APIs
- Complete control over polling rates
- Native DPI scaling support
- Global hotkey support

#### macOS
- Limited by accessibility permissions
- Input handling through Quartz Event Services
- No direct polling rate control
- Hotkeys require accessibility permissions

#### Linux
- Input handling through X11/Wayland
- May require root privileges
- Polling rate control limited by kernel
- Hotkey support depends on window manager

### GUI Differences

All platforms use PyQt5, so the GUI should be consistent across platforms. However:

- **Font rendering** may vary between platforms
- **System tray icons** may look different
- **Window decorations** follow platform conventions
- **Keyboard shortcuts** may conflict with platform shortcuts

### Performance Considerations

#### Windows
- Optimized for Windows input stack
- Low CPU usage (<1% typical)
- Memory usage <50MB

#### macOS
- May use more CPU due to permission checks
- Memory usage similar to Windows
- Battery impact minimal

#### Linux
- Performance varies by distribution
- May require more CPU for input processing
- Memory usage similar to other platforms

## Troubleshooting

### Common Issues

#### "Permission Denied" Errors
- **Windows**: Run as administrator
- **macOS**: Grant accessibility permissions
- **Linux**: Run with sudo or add user to input group

#### "Module Not Found" Errors
- Ensure all dependencies are installed
- Check Python version compatibility
- Verify virtual environment activation

#### GUI Not Displaying
- Check display server (X11/Wayland on Linux)
- Verify PyQt5 installation
- Check for missing system libraries

#### Input Not Working
- **Windows**: Check antivirus software
- **macOS**: Verify accessibility permissions
- **Linux**: Check input device permissions

### Platform-Specific Solutions

#### Windows
```bash
# Run as administrator
# Disable Windows Defender real-time protection temporarily
# Add ZeroLag to Windows Defender exclusions
```

#### macOS
```bash
# Grant accessibility permissions:
# System Preferences > Security & Privacy > Privacy > Accessibility
# Add Python or Terminal to the list

# For global hotkeys:
# System Preferences > Security & Privacy > Privacy > Input Monitoring
```

#### Linux
```bash
# Add user to input group
sudo usermod -a -G input $USER

# For Wayland users, try X11 session
# Check window manager hotkey support
```

## Development Notes

### Testing Requirements
- Test on multiple Windows versions (10, 11)
- Test on different macOS versions
- Test on various Linux distributions
- Verify GUI consistency across platforms
- Test input handling on different hardware

### Platform Detection
```python
import platform

system = platform.system()
if system == "Windows":
    # Windows-specific code
elif system == "Darwin":
    # macOS-specific code
elif system == "Linux":
    # Linux-specific code
```

### Conditional Imports
```python
try:
    import win32api
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

try:
    from PyQt5.QtWidgets import QSystemTrayIcon
    SYSTEM_TRAY_AVAILABLE = QSystemTrayIcon.isSystemTrayAvailable()
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False
```

## Future Platform Support

### Planned Improvements
- Enhanced macOS compatibility
- Better Linux distribution support
- Wayland compatibility improvements
- Mobile platform support (Android/iOS)

### Community Contributions
- Platform-specific optimizations
- Additional distribution packages
- Documentation improvements
- Bug reports and fixes

## Support

For platform-specific issues:
- Check this compatibility guide
- Review platform-specific installation instructions
- Test with minimal configuration
- Report issues with platform details

## Version History

- **v1.0.0**: Initial cross-platform support
- **v1.1.0**: Enhanced Windows compatibility
- **v1.2.0**: Improved macOS support
- **v1.3.0**: Better Linux compatibility
