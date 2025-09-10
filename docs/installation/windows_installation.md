# ZeroLag Windows Installation Guide

## System Requirements

- **Operating System**: Windows 10 (Build 1903 or later) or Windows 11
- **Architecture**: 64-bit (x64)
- **Python**: 3.8 or later
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 100MB free space
- **Permissions**: Administrator privileges recommended for full functionality

## Installation Methods

### Method 1: Direct Python Installation (Recommended)

#### Step 1: Install Python
1. Download Python from [python.org](https://www.python.org/downloads/)
2. Choose Python 3.8 or later
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### Step 2: Install ZeroLag Dependencies
```cmd
# Install required packages
pip install PyQt5 pynput pywin32 psutil

# Optional: Install development dependencies
pip install pytest pytest-qt
```

#### Step 3: Download ZeroLag
```cmd
# Clone the repository
git clone https://github.com/imsnokfr/zerolag.git
cd zerolag

# Or download and extract ZIP file
```

#### Step 4: Run ZeroLag
```cmd
python run_gui.py
```

### Method 2: Virtual Environment (Recommended for Development)

#### Step 1: Create Virtual Environment
```cmd
# Create virtual environment
python -m venv zerolag_env

# Activate virtual environment
zerolag_env\Scripts\activate
```

#### Step 2: Install Dependencies
```cmd
# Install packages in virtual environment
pip install PyQt5 pynput pywin32 psutil
```

#### Step 3: Run ZeroLag
```cmd
python run_gui.py
```

### Method 3: Anaconda/Miniconda

#### Step 1: Install Anaconda
Download from [anaconda.com](https://www.anaconda.com/download)

#### Step 2: Create Environment
```cmd
# Create conda environment
conda create -n zerolag python=3.9

# Activate environment
conda activate zerolag
```

#### Step 3: Install Dependencies
```cmd
# Install packages
conda install pyqt
pip install pynput pywin32 psutil
```

## Windows-Specific Configuration

### Administrator Privileges
Some ZeroLag features require administrator privileges:

1. **Right-click** on Command Prompt or PowerShell
2. Select **"Run as administrator"**
3. Navigate to ZeroLag directory
4. Run: `python run_gui.py`

### Windows Defender Configuration
Windows Defender may flag ZeroLag due to input monitoring:

1. Open **Windows Security**
2. Go to **Virus & threat protection**
3. Click **"Manage settings"** under Virus & threat protection settings
4. Click **"Add or remove exclusions"**
5. Add ZeroLag installation folder as an exclusion

### Firewall Configuration
If ZeroLag doesn't work properly:

1. Open **Windows Defender Firewall**
2. Click **"Allow an app or feature through Windows Defender Firewall"**
3. Click **"Change settings"** then **"Allow another app"**
4. Browse to Python executable and add it

## Troubleshooting

### Common Issues

#### "Python is not recognized"
- Ensure Python is added to PATH
- Restart Command Prompt after installation
- Try using `py` instead of `python`

#### "Module not found" errors
```cmd
# Update pip
python -m pip install --upgrade pip

# Reinstall packages
pip install --upgrade PyQt5 pynput pywin32 psutil
```

#### "Permission denied" errors
- Run Command Prompt as administrator
- Check Windows Defender exclusions
- Verify user permissions

#### GUI not displaying
- Check if PyQt5 is properly installed:
  ```cmd
  python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"
  ```
- Try running with different Python version
- Check for missing Visual C++ Redistributables

#### Input not working
- Run as administrator
- Check Windows Defender settings
- Verify input device permissions
- Try different USB ports for input devices

### Performance Issues

#### High CPU usage
- Close unnecessary applications
- Check for background processes
- Update graphics drivers
- Restart Windows

#### Memory issues
- Close other applications
- Check for memory leaks
- Restart ZeroLag
- Restart Windows

## Windows-Specific Features

### System Tray Integration
- ZeroLag minimizes to system tray
- Right-click tray icon for quick access
- Double-click to restore window

### Global Hotkeys
- Works system-wide when enabled
- Requires administrator privileges
- Can be disabled in settings

### DPI Scaling
- Automatic detection of display DPI
- Manual DPI adjustment available
- Supports multiple monitor setups

### Performance Monitoring
- Real-time CPU and memory usage
- Input event statistics
- Latency measurements

## Uninstallation

### Remove Python Packages
```cmd
pip uninstall PyQt5 pynput pywin32 psutil
```

### Remove ZeroLag Files
1. Delete ZeroLag installation folder
2. Remove from Windows Defender exclusions
3. Clear any created profiles (optional)

### Clean Up Registry (Advanced)
1. Open Registry Editor (regedit)
2. Navigate to: `HKEY_CURRENT_USER\Software\ZeroLag`
3. Delete ZeroLag entries (optional)

## Support

### Getting Help
- Check this installation guide
- Review troubleshooting section
- Test with minimal configuration
- Report issues with Windows version details

### System Information
When reporting issues, include:
- Windows version (winver command)
- Python version
- Installed packages list
- Error messages
- System specifications

### Log Files
ZeroLag creates log files in:
- `%APPDATA%\ZeroLag\logs\`
- Check for error messages
- Include relevant log entries when reporting issues

## Advanced Configuration

### Environment Variables
```cmd
# Set Python path (if needed)
set PYTHONPATH=C:\path\to\zerolag\src

# Set log level
set ZEROLAG_LOG_LEVEL=DEBUG
```

### Registry Settings
ZeroLag stores settings in:
- `HKEY_CURRENT_USER\Software\ZeroLag\Settings`
- Can be modified manually (advanced users only)

### Service Installation (Advanced)
For running ZeroLag as a Windows service:
1. Install NSSM (Non-Sucking Service Manager)
2. Create service pointing to Python script
3. Configure auto-start options

## Security Considerations

### Input Monitoring
- ZeroLag monitors keyboard and mouse input
- Data is processed locally, not transmitted
- Can be disabled in settings

### Network Access
- ZeroLag does not require internet connection
- No data is sent to external servers
- All processing is local

### Antivirus Software
- May flag ZeroLag due to input monitoring
- Add to exclusions list
- Whitelist Python executable if needed

## Performance Optimization

### Windows Settings
1. **Power Options**: Set to "High Performance"
2. **Game Mode**: Enable for gaming
3. **Background Apps**: Disable unnecessary apps
4. **Startup Programs**: Disable unused programs

### ZeroLag Settings
1. **Polling Rate**: Adjust based on needs
2. **DPI Settings**: Optimize for display
3. **Profile Management**: Use appropriate profiles
4. **Performance Monitoring**: Monitor resource usage

## Updates

### Checking for Updates
```cmd
# Check current version
python -c "import src; print(src.__version__)"

# Update from repository
git pull origin main
pip install --upgrade -r requirements.txt
```

### Backup Settings
Before updating:
1. Export current profiles
2. Backup configuration files
3. Note current settings
4. Test after update

## Development Setup

### For Developers
```cmd
# Clone repository
git clone https://github.com/imsnokfr/zerolag.git
cd zerolag

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run GUI
python run_gui.py
```

### IDE Configuration
- **VS Code**: Install Python extension
- **PyCharm**: Configure Python interpreter
- **Sublime Text**: Install Python package
- **Vim/Neovim**: Configure Python support

## Conclusion

ZeroLag is designed to work seamlessly on Windows systems. Follow this guide for the best installation experience. If you encounter issues, check the troubleshooting section or report problems with detailed system information.
