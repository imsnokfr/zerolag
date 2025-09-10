# ZeroLag macOS Installation Guide

## System Requirements

- **Operating System**: macOS 10.15 (Catalina) or later
- **Architecture**: Intel x64 or Apple Silicon (M1/M2)
- **Python**: 3.8 or later
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 100MB free space
- **Permissions**: Accessibility permissions required for input monitoring

## Installation Methods

### Method 1: Homebrew Installation (Recommended)

#### Step 1: Install Homebrew
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to PATH (for Apple Silicon Macs)
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

#### Step 2: Install Python and Dependencies
```bash
# Install Python
brew install python@3.11

# Install PyQt5
brew install pyqt@5

# Install additional dependencies
brew install python-tk
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

### Method 2: Direct Python Installation

#### Step 1: Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Choose Python 3.8 or later
3. Run the installer package
4. Verify installation:
   ```bash
   python3 --version
   pip3 --version
   ```

#### Step 2: Install Dependencies
```bash
# Install PyQt5
pip3 install PyQt5

# Install additional packages
pip3 install pynput psutil
```

### Method 3: Anaconda/Miniconda

#### Step 1: Install Anaconda
Download from [anaconda.com](https://www.anaconda.com/download)

#### Step 2: Create Environment
```bash
# Create conda environment
conda create -n zerolag python=3.9

# Activate environment
conda activate zerolag
```

#### Step 3: Install Dependencies
```bash
# Install packages
conda install pyqt
pip install pynput psutil
```

## macOS-Specific Configuration

### Accessibility Permissions

ZeroLag requires accessibility permissions to monitor input:

#### Step 1: Grant Accessibility Permissions
1. Open **System Preferences** (or **System Settings** on macOS 13+)
2. Go to **Security & Privacy** > **Privacy**
3. Select **Accessibility** from the left sidebar
4. Click the **lock icon** and enter your password
5. Click **"+"** and add:
   - **Terminal** (if running from Terminal)
   - **Python** (if running Python directly)
   - **ZeroLag** (if running as an app)

#### Step 2: Grant Input Monitoring Permissions
1. In **Security & Privacy** > **Privacy**
2. Select **Input Monitoring** from the left sidebar
3. Add the same applications as above

#### Step 3: Grant Screen Recording Permissions (Optional)
1. In **Security & Privacy** > **Privacy**
2. Select **Screen Recording** from the left sidebar
3. Add applications if needed for advanced features

### System Tray Configuration

#### macOS System Tray Support
- ZeroLag's system tray works with most macOS versions
- May require additional configuration on some systems
- Check if system tray icon appears in menu bar

#### Troubleshooting System Tray
```bash
# Check if system tray is available
python3 -c "from PyQt5.QtWidgets import QSystemTrayIcon; print(QSystemTrayIcon.isSystemTrayAvailable())"

# If False, try running with different Python version
# or check macOS version compatibility
```

## Troubleshooting

### Common Issues

#### "Permission denied" errors
- Ensure accessibility permissions are granted
- Check input monitoring permissions
- Try running from different terminal/application

#### "Module not found" errors
```bash
# Update pip
python3 -m pip install --upgrade pip

# Reinstall packages
pip3 install --upgrade PyQt5 pynput psutil

# Check Python path
echo $PYTHONPATH
```

#### GUI not displaying
```bash
# Check PyQt5 installation
python3 -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"

# Check for missing frameworks
otool -L /usr/local/lib/python3.9/site-packages/PyQt5/QtCore.so
```

#### Input not working
- Verify accessibility permissions
- Check input monitoring permissions
- Try running from different application
- Restart macOS after granting permissions

### Performance Issues

#### High CPU usage
```bash
# Check system load
top -l 1

# Check for background processes
ps aux | grep zerolag

# Monitor resource usage
python3 -c "import psutil; print(psutil.cpu_percent())"
```

#### Memory issues
```bash
# Check memory usage
vm_stat

# Check for memory leaks
ps aux | grep zerolag
```

### macOS Version Issues

#### macOS 13+ (Ventura) Issues
- Some permission dialogs may look different
- Check **System Settings** instead of **System Preferences**
- Ensure all permissions are granted

#### macOS 12 (Monterey) Issues
- May require additional security permissions
- Check **Security & Privacy** settings
- Verify input monitoring permissions

#### macOS 11 (Big Sur) Issues
- Some PyQt5 features may be limited
- Check Python version compatibility
- Update to latest PyQt5 version

## macOS-Specific Features

### Limited Features on macOS
- **DPI Emulation**: Not available (macOS handles this natively)
- **Polling Rate Control**: Limited by macOS input system
- **Global Hotkeys**: Requires accessibility permissions
- **Input Optimization**: Limited by macOS security model

### Available Features
- ✅ Basic input handling
- ✅ GUI interface
- ✅ System tray integration
- ✅ Profile management
- ✅ Performance monitoring
- ✅ Mouse and keyboard optimization (with permissions)

### Apple Silicon Compatibility

#### M1/M2 Macs
- ZeroLag works on Apple Silicon Macs
- May require Rosetta 2 for some dependencies
- Performance may vary compared to Intel Macs

#### Intel Macs
- Full compatibility expected
- All features should work as designed
- No special configuration required

## Security Considerations

### Input Monitoring
- ZeroLag monitors keyboard and mouse input
- Requires explicit user permission
- Data is processed locally
- No network transmission

### Privacy
- All processing happens locally
- No data is sent to external servers
- Input data is not stored permanently

### System Integrity
- ZeroLag does not modify system files
- All changes are user-configurable
- Can be completely removed without system impact

## Performance Optimization

### macOS Settings
1. **Energy Saver**: Set to "High Performance" if available
2. **Background App Refresh**: Disable unnecessary apps
3. **Login Items**: Remove unused startup items
4. **Spotlight**: Exclude ZeroLag directory if needed

### ZeroLag Settings
1. **Polling Rate**: Adjust based on macOS capabilities
2. **Profile Management**: Use appropriate profiles
3. **Performance Monitoring**: Monitor resource usage
4. **Input Settings**: Optimize for your input devices

## Package Management

### Creating .app Bundle
```bash
# Install py2app
pip3 install py2app

# Create setup.py
cat > setup.py << EOF
from setuptools import setup

APP = ['run_gui.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': 'ZeroLag',
        'CFBundleDisplayName': 'ZeroLag',
        'CFBundleIdentifier': 'com.zerolag.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
EOF

# Build app
python3 setup.py py2app

# The app will be in dist/ZeroLag.app
```

### Creating .dmg Installer
```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "ZeroLag" \
  --volicon "icon.icns" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --icon "ZeroLag.app" 175 120 \
  --hide-extension "ZeroLag.app" \
  --app-drop-link 425 120 \
  "ZeroLag.dmg" \
  "dist/"
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
- **VS Code**: Install Python extension and macOS-specific tools
- **PyCharm**: Configure Python interpreter and macOS environment
- **Sublime Text**: Install Python package and macOS tools
- **Vim/Neovim**: Configure Python support and macOS integration

## Uninstallation

### Remove Python Packages
```bash
pip3 uninstall pynput psutil PyQt5
```

### Remove Homebrew Packages
```bash
# If installed via Homebrew
brew uninstall pyqt@5 python@3.11
```

### Remove ZeroLag Files
```bash
# Remove installation directory
rm -rf ~/zerolag

# Remove configuration files
rm -rf ~/Library/Application\ Support/ZeroLag
rm -rf ~/Library/Preferences/com.zerolag.plist
```

### Remove Permissions
1. Open **System Preferences** > **Security & Privacy** > **Privacy**
2. Remove ZeroLag from **Accessibility** list
3. Remove ZeroLag from **Input Monitoring** list
4. Remove ZeroLag from **Screen Recording** list (if added)

## Support

### Getting Help
- Check this installation guide
- Review troubleshooting section
- Test with minimal configuration
- Report issues with macOS version details

### System Information
When reporting issues, include:
- macOS version (`sw_vers`)
- Python version
- Installed packages list
- Error messages
- System specifications

### Log Files
ZeroLag creates log files in:
- `~/Library/Application Support/ZeroLag/logs/`
- Check for error messages
- Include relevant log entries when reporting issues

## Known Limitations

### macOS Security Model
- Input monitoring requires explicit user permission
- Some features may be limited by macOS security policies
- Global hotkeys may not work in all applications

### Performance Considerations
- macOS input system may limit optimization capabilities
- Some features may use more CPU than on Windows
- Battery impact may be higher on laptops

### Compatibility Issues
- Some PyQt5 features may not work on all macOS versions
- Apple Silicon compatibility may vary
- System tray support depends on macOS version

## Conclusion

ZeroLag works on macOS with some limitations due to the security model and input system. Follow this guide for the best installation experience. Some features may require additional configuration or may not be available due to macOS security restrictions.
