# ZeroLag - Gaming Input Optimizer

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/imsnokfr/zerolag)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/imsnokfr/zerolag)

**ZeroLag** is a comprehensive gaming input optimization tool designed to eliminate input lag, improve responsiveness, and enhance your gaming performance. Built with Python and PyQt5, it provides real-time input processing, advanced smoothing algorithms, and professional-grade benchmarking tools.

## 🚀 Features

### Core Optimization
- **Anti-Ghosting**: Prevents key conflicts and ensures every keypress is registered
- **NKRO (N-Key Rollover)**: Full keyboard rollover support for complex key combinations
- **Rapid Key Actions**: Optimized key repeat and rapid-fire functionality
- **Input Smoothing**: Advanced algorithms to smooth mouse movement and reduce jitter
- **DPI Emulation**: Custom DPI settings for precise cursor control
- **Polling Rate Optimization**: Maximize USB polling rates for minimal latency

### Advanced Features
- **Macro System**: Record and playback complex key sequences
- **Profile Management**: Save and load different configurations for different games
- **Hotkey System**: Global hotkeys for quick access to features
- **Emergency Hotkeys**: Instant disable/reset for safety
- **System Tray Integration**: Background operation with minimal resource usage
- **Community Profile Sharing**: Upload and download profiles from the community

### Benchmarking Tools
- **Aim Accuracy Test**: Visual target practice with real-time scoring
- **Key Speed Test**: Measure and improve key press speed and accuracy
- **Reaction Time Test**: Test and train your reaction times
- **Performance Analytics**: Detailed statistics and improvement tracking
- **Performance Ranks**: S+ to F grading system for competitive analysis

### Cross-Platform Support
- **Windows**: Full feature support with Windows API integration
- **Linux**: Core functionality with X11/Wayland support
- **macOS**: Basic functionality with Quartz integration

## 📋 Requirements

### System Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 10.15+
- **Python**: 3.8 or higher
- **RAM**: 512MB minimum, 1GB recommended
- **Storage**: 100MB free space
- **Input Devices**: USB keyboard and mouse

### Python Dependencies
- PyQt5 >= 5.15.0
- pynput >= 1.7.6
- psutil >= 5.8.0
- pywin32 >= 227 (Windows only)
- pyobjc >= 8.0 (macOS only)

## 🛠️ Installation

### Quick Install (Recommended)

1. **Clone the repository**:
   ```bash
   git clone https://github.com/imsnokfr/zerolag.git
   cd zerolag
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python run_gui.py
   ```

### Manual Installation

1. **Download the latest release** from the [Releases page](https://github.com/imsnokfr/zerolag/releases)

2. **Extract the archive** to your desired location

3. **Install Python dependencies**:
   ```bash
   pip install PyQt5 pynput psutil
   ```

4. **For Windows users**, install additional dependencies:
   ```bash
   pip install pywin32
   ```

5. **For macOS users**, install additional dependencies:
   ```bash
   pip install pyobjc
   ```

### Development Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/imsnokfr/zerolag.git
   cd zerolag
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

## 🎮 Quick Start Guide

### First Launch
1. **Start ZeroLag** by running `python run_gui.py`
2. **Grant permissions** when prompted (required for input monitoring)
3. **Select your gaming mode** (FPS, MOBA, RTS, MMO, or Custom)
4. **Configure basic settings** in the Settings tab
5. **Test your setup** using the Benchmark tool

### Basic Configuration
1. **Go to Settings tab**
2. **Adjust smoothing settings** for your preference
3. **Enable/disable features** as needed
4. **Set up hotkeys** for quick access
5. **Save your profile** for future use

### Using Profiles
1. **Create a new profile** in the Profiles tab
2. **Configure settings** for your specific game
3. **Save the profile** with a descriptive name
4. **Load profiles** quickly when switching games
5. **Share profiles** with the community

### Benchmarking Your Performance
1. **Go to the Benchmark tab**
2. **Select test type** (Aim, Key Speed, or Reaction Time)
3. **Choose difficulty level** (Beginner to Expert)
4. **Start the test** and follow on-screen instructions
5. **Review your results** and track improvement over time

## 📖 User Manual

### Main Interface

#### Dashboard Tab
- **Real-time Performance**: Live metrics showing input lag, polling rate, and system performance
- **Quick Controls**: Easy access to enable/disable features
- **Status Indicators**: Visual feedback on system status and optimizations

#### Settings Tab
- **Input Settings**: Configure smoothing, anti-ghosting, and NKRO settings
- **Performance Settings**: Adjust polling rates and DPI emulation
- **Hotkey Settings**: Configure global hotkeys for quick access
- **System Settings**: General application preferences

#### Profiles Tab
- **Profile Management**: Create, edit, and delete gaming profiles
- **Quick Switch**: Fast profile switching for different games
- **Import/Export**: Share profiles with other users
- **Community Profiles**: Download and upload profiles from the community

#### Hotkeys Tab
- **Global Hotkeys**: Configure system-wide hotkey combinations
- **Emergency Hotkeys**: Set up instant disable/reset hotkeys
- **Macro Hotkeys**: Assign macros to hotkey combinations
- **Test Hotkeys**: Test your hotkey configurations

#### Community Tab
- **Profile Library**: Browse and download community profiles
- **Upload Profiles**: Share your profiles with the community
- **Search & Filter**: Find profiles by game, difficulty, or tags
- **Rating System**: Rate and review community profiles

#### Benchmark Tab
- **Aim Accuracy Test**: Practice and measure your aiming skills
- **Key Speed Test**: Test your keyboard speed and accuracy
- **Reaction Time Test**: Measure and improve your reaction times
- **Performance Analytics**: Track your improvement over time

### Advanced Features

#### Macro System
1. **Record a macro** by clicking "Record" and performing your actions
2. **Stop recording** and review the recorded sequence
3. **Assign to hotkey** for quick access
4. **Edit macros** to fine-tune timing and actions
5. **Export/import** macros for sharing

#### Profile Sharing
1. **Create a profile** with your preferred settings
2. **Add metadata** (name, description, tags, difficulty)
3. **Upload to community** for others to use
4. **Browse community** profiles and download interesting ones
5. **Rate and review** profiles to help the community

#### Emergency Features
- **Emergency Stop**: Instantly disable all optimizations (Ctrl+Alt+S)
- **Emergency Reset**: Reset to default settings (Ctrl+Alt+R)
- **Emergency Disable**: Disable specific features (Ctrl+Alt+D)

## 🔧 Troubleshooting

### Common Issues

#### Application Won't Start
- **Check Python version**: Ensure Python 3.8+ is installed
- **Install dependencies**: Run `pip install -r requirements.txt`
- **Check permissions**: Ensure you have administrator/root privileges
- **Update drivers**: Update your keyboard and mouse drivers

#### Input Not Being Detected
- **Check device connections**: Ensure keyboard/mouse are properly connected
- **Grant permissions**: Allow ZeroLag to monitor input devices
- **Disable antivirus**: Some antivirus software may block input monitoring
- **Check USB ports**: Try different USB ports or use USB 2.0 ports

#### Performance Issues
- **Close other applications**: Free up system resources
- **Update graphics drivers**: Ensure latest drivers are installed
- **Check system resources**: Monitor CPU and memory usage
- **Adjust settings**: Lower polling rates or disable some features

#### Hotkeys Not Working
- **Check conflicts**: Ensure hotkeys don't conflict with other applications
- **Run as administrator**: Some hotkeys require elevated privileges
- **Test hotkeys**: Use the test buttons in the Hotkeys tab
- **Restart application**: Sometimes a restart is needed for hotkeys to work

### Error Messages

#### "Permission Denied"
- **Run as administrator** (Windows) or with `sudo` (Linux/macOS)
- **Check file permissions** for the ZeroLag directory
- **Disable antivirus** temporarily to test

#### "Device Not Found"
- **Reconnect devices** and restart the application
- **Check device compatibility** in the Settings tab
- **Update device drivers** to the latest version

#### "Profile Load Error"
- **Check file integrity** of the profile file
- **Verify profile format** is correct JSON
- **Create new profile** if the file is corrupted

### Performance Optimization

#### For Low-End Systems
- **Disable visual effects** in Settings
- **Lower polling rates** to reduce CPU usage
- **Disable unnecessary features** like DPI emulation
- **Close other applications** while gaming

#### For High-End Systems
- **Enable all features** for maximum performance
- **Increase polling rates** to 1000Hz or higher
- **Use multiple profiles** for different games
- **Enable advanced smoothing** algorithms

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Reporting Issues
1. **Check existing issues** before creating a new one
2. **Provide detailed information** about your system and the issue
3. **Include logs** and error messages when possible
4. **Test on different systems** if possible

### Suggesting Features
1. **Check existing feature requests** first
2. **Describe the feature** in detail
3. **Explain the use case** and benefits
4. **Consider implementation** complexity

### Code Contributions
1. **Fork the repository** and create a feature branch
2. **Follow coding standards** and add tests
3. **Update documentation** for new features
4. **Submit a pull request** with a clear description

### Community Profiles
1. **Create optimized profiles** for popular games
2. **Add detailed descriptions** and tags
3. **Test thoroughly** before uploading
4. **Respond to feedback** and improve profiles

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PyQt5** for the excellent GUI framework
- **pynput** for cross-platform input monitoring
- **psutil** for system monitoring capabilities
- **The gaming community** for feedback and feature requests
- **Contributors** who have helped improve ZeroLag

## 📞 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/imsnokfr/zerolag/issues)
- **Discussions**: [Community discussions and Q&A](https://github.com/imsnokfr/zerolag/discussions)
- **Email**: [Contact the maintainers](mailto:support@zerolag.app)

## 🔄 Changelog

### Version 1.0.0 (Latest)
- Initial release with full feature set
- Complete GUI implementation
- All core optimization features
- Comprehensive benchmarking tools
- Community profile sharing
- Cross-platform support

---

**ZeroLag** - Eliminate input lag, maximize performance, dominate the competition! 🎮