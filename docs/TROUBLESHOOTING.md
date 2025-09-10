# ZeroLag Troubleshooting Guide

## Quick Fixes

### Application Won't Start
**Problem:** ZeroLag fails to launch or crashes immediately
**Quick Fix:**
1. Run as Administrator (Right-click → "Run as administrator")
2. Check Python version: `python --version` (should be 3.8+)
3. Install dependencies: `pip install -r requirements.txt`

### Input Not Working
**Problem:** Mouse/keyboard input not being detected
**Quick Fix:**
1. Grant permissions when prompted
2. Reconnect USB devices
3. Restart the application
4. Check device compatibility in Settings

### Performance Issues
**Problem:** High CPU usage or slow response
**Quick Fix:**
1. Close other applications
2. Lower polling rates in Settings
3. Disable unnecessary features
4. Restart the application

## Detailed Troubleshooting

### Installation Issues

#### Python Not Found
**Error:** `'python' is not recognized as an internal or external command`
**Solution:**
1. Install Python 3.8+ from [python.org](https://python.org)
2. Add Python to PATH during installation
3. Restart command prompt/terminal
4. Verify with `python --version`

#### Missing Dependencies
**Error:** `ModuleNotFoundError: No module named 'PyQt5'`
**Solution:**
```bash
pip install PyQt5 pynput psutil
# For Windows:
pip install pywin32
# For macOS:
pip install pyobjc
```

#### Permission Denied
**Error:** `PermissionError: [Errno 13] Permission denied`
**Solution:**
1. Run command prompt as Administrator
2. Use `pip install --user` for user installation
3. Check antivirus software settings
4. Disable Windows Defender real-time protection temporarily

### Runtime Issues

#### Application Crashes on Startup
**Symptoms:**
- Application window appears briefly then closes
- Error messages in console
- System becomes unresponsive

**Diagnosis:**
1. Check Windows Event Viewer for error details
2. Run from command line to see error messages
3. Check system resources (RAM, CPU)
4. Verify all dependencies are installed

**Solutions:**
1. **Update Graphics Drivers:**
   - Download latest drivers from manufacturer
   - Restart system after installation
   - Test application again

2. **Check System Requirements:**
   - Windows 10/11 (64-bit recommended)
   - 4GB RAM minimum
   - 100MB free disk space
   - USB 2.0+ ports

3. **Disable Antivirus Temporarily:**
   - Add ZeroLag to antivirus exclusions
   - Disable real-time protection temporarily
   - Test application launch

4. **Run in Compatibility Mode:**
   - Right-click ZeroLag executable
   - Properties → Compatibility
   - Enable "Run this program in compatibility mode"
   - Select Windows 10

#### Input Devices Not Detected
**Symptoms:**
- Mouse/keyboard input not registered
- Features show as "Not Available"
- No response to input devices

**Diagnosis:**
1. Check device connections
2. Test devices in other applications
3. Check Windows Device Manager
4. Verify USB port functionality

**Solutions:**
1. **Reconnect Devices:**
   - Unplug and reconnect USB devices
   - Try different USB ports
   - Use USB 2.0 ports if available
   - Check for loose connections

2. **Update Device Drivers:**
   - Open Device Manager
   - Find your mouse/keyboard
   - Right-click → Update driver
   - Restart system after update

3. **Check USB Power Management:**
   - Device Manager → Universal Serial Bus controllers
   - Right-click each USB Root Hub
   - Properties → Power Management
   - Uncheck "Allow the computer to turn off this device"

4. **Test Device Compatibility:**
   - Check manufacturer's compatibility list
   - Test with different devices
   - Use basic USB devices for testing

#### Performance Problems
**Symptoms:**
- High CPU usage (>50%)
- Slow response times
- System lag or stuttering
- Application freezes

**Diagnosis:**
1. Monitor Task Manager for resource usage
2. Check for conflicting applications
3. Verify system specifications
4. Test with different settings

**Solutions:**
1. **Close Conflicting Applications:**
   - Close other gaming software
   - Disable unnecessary startup programs
   - End processes using high CPU
   - Restart system if needed

2. **Adjust ZeroLag Settings:**
   - Lower polling rates (500Hz instead of 1000Hz)
   - Disable DPI emulation
   - Reduce smoothing factor
   - Disable visual effects

3. **System Optimization:**
   - Update all drivers
   - Run Windows Update
   - Check for malware
   - Defragment hard drive

4. **Hardware Issues:**
   - Check RAM for errors
   - Monitor CPU temperature
   - Test with different USB devices
   - Consider hardware upgrade

#### Hotkey Conflicts
**Symptoms:**
- Hotkeys not responding
- Unexpected behavior when pressing hotkeys
- Conflicts with other applications
- Hotkeys work intermittently

**Diagnosis:**
1. Test hotkeys in ZeroLag's test mode
2. Check for conflicting applications
3. Verify hotkey assignments
4. Test with different key combinations

**Solutions:**
1. **Check Application Conflicts:**
   - Close other gaming software
   - Disable Discord/TeamSpeak hotkeys
   - Check for macro software conflicts
   - Restart conflicting applications

2. **Change Hotkey Combinations:**
   - Use less common key combinations
   - Avoid system hotkeys (Ctrl+Alt+Del, Alt+Tab)
   - Test different combinations
   - Use function keys (F1-F12)

3. **Run as Administrator:**
   - Some hotkeys require elevated privileges
   - Right-click ZeroLag → "Run as administrator"
   - Grant UAC permissions when prompted

4. **Reset Hotkey Settings:**
   - Go to Hotkeys tab
   - Click "Reset to Defaults"
   - Reconfigure hotkeys
   - Test each hotkey individually

### Profile Issues

#### Profile Won't Load
**Error:** "Profile load error" or "Invalid profile format"
**Solutions:**
1. **Check File Integrity:**
   - Verify profile file exists
   - Check file permissions
   - Ensure file is not corrupted
   - Try opening in text editor

2. **Restore from Backup:**
   - Check backup folder
   - Restore previous version
   - Create new profile
   - Import from community

3. **Profile Format Issues:**
   - Check JSON syntax
   - Validate profile structure
   - Compare with working profiles
   - Recreate profile manually

#### Profile Settings Not Applied
**Symptoms:**
- Profile loads but settings don't change
- Features remain disabled
- Performance doesn't improve

**Solutions:**
1. **Verify Profile Settings:**
   - Check profile configuration
   - Ensure settings are enabled
   - Test with different profiles
   - Compare with working profiles

2. **Apply Settings Manually:**
   - Go to Settings tab
   - Apply settings manually
   - Save profile again
   - Test functionality

3. **Restart Application:**
   - Close ZeroLag completely
   - Restart application
   - Load profile again
   - Test settings

### Benchmark Issues

#### Tests Not Starting
**Error:** "Test failed to start" or "Invalid test configuration"
**Solutions:**
1. **Check Test Configuration:**
   - Verify test parameters
   - Ensure valid duration settings
   - Check difficulty level
   - Reset to defaults

2. **System Requirements:**
   - Ensure sufficient system resources
   - Close other applications
   - Check input device connections
   - Restart application

3. **Permission Issues:**
   - Run as administrator
   - Grant input permissions
   - Check antivirus settings
   - Disable conflicting software

#### Inaccurate Test Results
**Symptoms:**
- Unrealistic scores
- Inconsistent results
- Tests not reflecting actual performance

**Solutions:**
1. **Calibrate Input Devices:**
   - Test mouse sensitivity
   - Check keyboard response
   - Verify device settings
   - Use consistent hardware

2. **System Optimization:**
   - Close background applications
   - Disable unnecessary services
   - Optimize system performance
   - Use dedicated gaming mode

3. **Test Environment:**
   - Use consistent test conditions
   - Ensure stable system performance
   - Test at same time of day
   - Use same physical setup

### Community Features Issues

#### Profile Upload Failed
**Error:** "Upload failed" or "Network error"
**Solutions:**
1. **Check Internet Connection:**
   - Verify internet connectivity
   - Test with other applications
   - Check firewall settings
   - Try different network

2. **Profile Validation:**
   - Ensure profile is complete
   - Check required fields
   - Validate profile format
   - Test profile locally first

3. **Account Issues:**
   - Check GitHub account status
   - Verify authentication
   - Refresh login credentials
   - Contact support if needed

#### Profile Download Failed
**Error:** "Download failed" or "Profile not found"
**Solutions:**
1. **Network Issues:**
   - Check internet connection
   - Try again later
   - Use different network
   - Check firewall settings

2. **Profile Availability:**
   - Verify profile exists
   - Check profile permissions
   - Try different profile
   - Contact profile author

3. **Local Issues:**
   - Check disk space
   - Verify file permissions
   - Clear download cache
   - Restart application

## Frequently Asked Questions

### General Questions

**Q: Is ZeroLag safe to use?**
A: Yes, ZeroLag is completely safe. It only monitors and optimizes input devices without modifying system files or installing malware.

**Q: Will ZeroLag get me banned from games?**
A: No, ZeroLag only optimizes input processing and doesn't modify game files or provide unfair advantages.

**Q: Does ZeroLag work with all games?**
A: ZeroLag works with most games, but some games with anti-cheat systems may block input monitoring. Check game compatibility before use.

**Q: Can I use ZeroLag with multiple monitors?**
A: Yes, ZeroLag works with multi-monitor setups and can optimize input across all displays.

### Performance Questions

**Q: How much does ZeroLag improve performance?**
A: Performance improvements vary by system, but most users see 10-30% reduction in input lag and improved responsiveness.

**Q: Will ZeroLag slow down my computer?**
A: ZeroLag is designed to be lightweight and should not noticeably impact system performance when properly configured.

**Q: Can I use ZeroLag with other gaming software?**
A: Yes, but some software may conflict. Close other input optimization software before using ZeroLag.

**Q: Does ZeroLag work with wireless devices?**
A: Yes, but wired devices typically provide better performance and lower latency.

### Technical Questions

**Q: What programming language is ZeroLag written in?**
A: ZeroLag is written in Python using PyQt5 for the GUI and pynput for input monitoring.

**Q: Can I modify ZeroLag's source code?**
A: Yes, ZeroLag is open source. You can modify and redistribute it according to the MIT license.

**Q: How do I update ZeroLag?**
A: Download the latest version from GitHub and replace the old files, or use `git pull` if you cloned the repository.

**Q: Can I run ZeroLag on Linux/macOS?**
A: Yes, ZeroLag supports Windows, Linux, and macOS, though some features may be limited on non-Windows platforms.

### Troubleshooting Questions

**Q: Why won't ZeroLag start?**
A: Check Python version, install dependencies, run as administrator, and ensure antivirus isn't blocking the application.

**Q: Why aren't my hotkeys working?**
A: Check for conflicts with other applications, run as administrator, and ensure hotkeys are properly configured.

**Q: Why is my mouse not being detected?**
A: Reconnect USB devices, update drivers, check USB ports, and ensure devices are compatible.

**Q: Why are my benchmark scores low?**
A: Practice regularly, ensure consistent settings, close other applications, and use proper input devices.

## Getting Help

### Self-Help Resources
1. **User Manual**: Comprehensive guide to all features
2. **README**: Quick start and installation guide
3. **GitHub Issues**: Search existing issues and solutions
4. **Community Discussions**: Ask questions and share tips

### Contact Support
1. **GitHub Issues**: Report bugs and request features
2. **Email Support**: Contact the development team
3. **Community Forums**: Get help from other users
4. **Discord Server**: Real-time chat support

### Reporting Issues
When reporting issues, include:
1. **System Information**: OS, Python version, hardware specs
2. **Error Messages**: Exact error text and when it occurs
3. **Steps to Reproduce**: Detailed steps to recreate the issue
4. **Log Files**: Application logs and system logs
5. **Screenshots**: Visual evidence of the problem

---

This troubleshooting guide covers the most common issues and solutions. For additional help, visit the [GitHub repository](https://github.com/imsnokfr/zerolag) or contact the support team.
