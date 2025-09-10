# ZeroLag User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Interface Overview](#interface-overview)
4. [Core Features](#core-features)
5. [Advanced Features](#advanced-features)
6. [Profiles and Settings](#profiles-and-settings)
7. [Benchmarking](#benchmarking)
8. [Community Features](#community-features)
9. [Troubleshooting](#troubleshooting)
10. [Tips and Tricks](#tips-and-tricks)

## Introduction

ZeroLag is a professional-grade gaming input optimization tool designed to eliminate input lag and enhance your gaming performance. This manual will guide you through all features and help you get the most out of your gaming experience.

### What is Input Lag?
Input lag is the delay between when you perform an action (like clicking or pressing a key) and when that action is registered by the game. Even small amounts of input lag can significantly impact your performance in competitive gaming.

### How ZeroLag Helps
ZeroLag addresses input lag through:
- **Hardware optimization**: Maximizing polling rates and reducing system latency
- **Software smoothing**: Advanced algorithms to smooth input without adding delay
- **System tuning**: Optimizing Windows settings for gaming performance
- **Real-time monitoring**: Continuous feedback on your system's performance

## Getting Started

### First Launch
1. **Run ZeroLag** by executing `python run_gui.py`
2. **Grant permissions** when Windows asks for administrator privileges
3. **Select your primary gaming mode** from the dashboard
4. **Configure basic settings** in the Settings tab
5. **Test your setup** using the Benchmark tool

### Initial Configuration
1. **Go to Settings** tab
2. **Enable core features**:
   - Input Smoothing: ON
   - Anti-Ghosting: ON
   - NKRO: ON
3. **Set polling rate** to 1000Hz (if supported by your mouse)
4. **Configure DPI** to your preferred setting
5. **Save as default profile**

## Interface Overview

### Main Window Layout
The ZeroLag interface is organized into several tabs, each focusing on specific functionality:

#### Dashboard Tab
The main control center showing:
- **Real-time Performance Metrics**: Live display of input lag, polling rate, and system performance
- **Quick Toggle Controls**: Easy access to enable/disable major features
- **System Status**: Visual indicators showing which optimizations are active
- **Performance Graph**: Real-time chart of your system's input performance

#### Settings Tab
Comprehensive configuration options:
- **Input Settings**: Smoothing, anti-ghosting, and NKRO configuration
- **Performance Settings**: Polling rates, DPI emulation, and system optimization
- **Hotkey Settings**: Global hotkey configuration
- **System Settings**: General application preferences and logging

#### Profiles Tab
Profile management system:
- **Profile List**: View and manage all your saved profiles
- **Quick Switch**: Fast profile switching for different games
- **Import/Export**: Share profiles with other users
- **Profile Editor**: Create and modify profile settings

#### Hotkeys Tab
Global hotkey management:
- **Hotkey List**: View all configured hotkeys
- **Add/Edit Hotkeys**: Create new hotkey combinations
- **Test Hotkeys**: Verify hotkey functionality
- **Emergency Hotkeys**: Configure safety hotkeys

#### Community Tab
Community profile sharing:
- **Profile Library**: Browse community-uploaded profiles
- **Search and Filter**: Find profiles by game, difficulty, or tags
- **Upload Profiles**: Share your profiles with the community
- **Rating System**: Rate and review community profiles

#### Benchmark Tab
Performance testing tools:
- **Aim Accuracy Test**: Visual target practice with scoring
- **Key Speed Test**: Measure keyboard speed and accuracy
- **Reaction Time Test**: Test and improve reaction times
- **Performance Analytics**: Track improvement over time

## Core Features

### Input Smoothing
Input smoothing reduces jitter and provides more precise control without adding noticeable delay.

**Configuration:**
- **Smoothing Factor**: 0.1 (minimal) to 1.0 (maximum)
- **Recommended**: 0.3-0.7 for most users
- **Gaming Modes**:
  - FPS: 0.2-0.4 (precision aiming)
  - MOBA: 0.4-0.6 (balanced control)
  - RTS: 0.6-0.8 (smooth unit movement)

**How it works:**
- Analyzes mouse movement patterns
- Applies smoothing algorithms to reduce jitter
- Maintains responsiveness while improving precision

### Anti-Ghosting
Prevents key conflicts when pressing multiple keys simultaneously.

**Configuration:**
- **Enable Anti-Ghosting**: ON (recommended)
- **Key Rollover**: Full NKRO support
- **Conflict Resolution**: Automatic key priority

**Benefits:**
- Every keypress is registered correctly
- No missed inputs during complex combinations
- Improved reliability in fast-paced games

### NKRO (N-Key Rollover)
Full keyboard rollover support for complex key combinations.

**Configuration:**
- **Enable NKRO**: ON (if supported by keyboard)
- **Rollover Mode**: Full (all keys simultaneously)
- **USB Polling**: 1000Hz (if supported)

**Testing:**
- Use the Key Speed Test in Benchmark tab
- Press multiple keys simultaneously
- Verify all keys are registered correctly

### DPI Emulation
Custom DPI settings for precise cursor control.

**Configuration:**
- **Enable DPI Emulation**: ON
- **Target DPI**: 400-1600 (adjust to preference)
- **Sensitivity Scaling**: Automatic or manual

**Gaming Recommendations:**
- **FPS Games**: 400-800 DPI
- **MOBA Games**: 800-1200 DPI
- **RTS Games**: 1000-1600 DPI

### Polling Rate Optimization
Maximizes USB polling rates for minimal latency.

**Configuration:**
- **Mouse Polling**: 1000Hz (if supported)
- **Keyboard Polling**: 1000Hz (if supported)
- **USB Optimization**: Enable

**System Requirements:**
- USB 2.0 or higher
- Compatible mouse/keyboard
- Windows 10/11 recommended

## Advanced Features

### Macro System
Record and playback complex key sequences for automation.

**Creating Macros:**
1. Go to Profiles tab
2. Select "Macros" section
3. Click "Record New Macro"
4. Perform your actions
5. Click "Stop Recording"
6. Assign to hotkey

**Macro Features:**
- **Timing Control**: Adjust delays between actions
- **Loop Support**: Repeat macros automatically
- **Conditional Logic**: Execute based on conditions
- **Hotkey Assignment**: Quick access via hotkeys

**Best Practices:**
- Keep macros simple and focused
- Test thoroughly before using in games
- Avoid macros that give unfair advantages
- Respect game terms of service

### Profile Management
Create and manage different configurations for different games.

**Creating Profiles:**
1. Go to Profiles tab
2. Click "New Profile"
3. Configure settings for your game
4. Add metadata (name, description, tags)
5. Save the profile

**Profile Types:**
- **Game-Specific**: Optimized for particular games
- **Gaming Mode**: FPS, MOBA, RTS, MMO, Custom
- **Difficulty Level**: Beginner, Intermediate, Advanced, Expert
- **Personal**: Your personal preferences

**Sharing Profiles:**
1. Select profile to share
2. Add detailed description
3. Choose appropriate tags
4. Upload to community
5. Respond to feedback

### Hotkey System
Global hotkeys for quick access to features.

**Default Hotkeys:**
- **Ctrl+Alt+S**: Emergency stop (disable all optimizations)
- **Ctrl+Alt+R**: Emergency reset (reset to defaults)
- **Ctrl+Alt+D**: Emergency disable (disable specific features)
- **Ctrl+Alt+P**: Toggle profile switching
- **Ctrl+Alt+B**: Open benchmark tool

**Creating Custom Hotkeys:**
1. Go to Hotkeys tab
2. Click "Add Hotkey"
3. Press desired key combination
4. Select action to perform
5. Save the hotkey

**Hotkey Actions:**
- **Toggle Features**: Enable/disable specific features
- **Switch Profiles**: Change to different profile
- **Run Macros**: Execute recorded macros
- **System Actions**: Minimize, close, restart

### Emergency Features
Safety features for instant control.

**Emergency Stop (Ctrl+Alt+S):**
- Instantly disables all optimizations
- Returns to default Windows behavior
- Use when experiencing issues

**Emergency Reset (Ctrl+Alt+R):**
- Resets all settings to defaults
- Clears any problematic configurations
- Restarts optimization services

**Emergency Disable (Ctrl+Alt+D):**
- Disables specific features
- Allows selective troubleshooting
- Maintains partial optimization

## Profiles and Settings

### Gaming Mode Presets
Pre-configured settings for different gaming types.

**FPS Mode:**
- Smoothing: 0.2-0.4
- Anti-Ghosting: ON
- NKRO: ON
- DPI: 400-800
- Polling: 1000Hz

**MOBA Mode:**
- Smoothing: 0.4-0.6
- Anti-Ghosting: ON
- NKRO: ON
- DPI: 800-1200
- Polling: 1000Hz

**RTS Mode:**
- Smoothing: 0.6-0.8
- Anti-Ghosting: ON
- NKRO: ON
- DPI: 1000-1600
- Polling: 1000Hz

**MMO Mode:**
- Smoothing: 0.5-0.7
- Anti-Ghosting: ON
- NKRO: ON
- DPI: 800-1200
- Polling: 1000Hz

### Custom Profiles
Create profiles tailored to your specific needs.

**Profile Configuration:**
1. **Basic Settings**: Name, description, gaming mode
2. **Input Settings**: Smoothing, anti-ghosting, NKRO
3. **Performance Settings**: Polling rates, DPI, optimization
4. **Hotkey Settings**: Custom hotkey assignments
5. **Advanced Settings**: Expert-level configurations

**Profile Metadata:**
- **Name**: Descriptive profile name
- **Description**: Detailed explanation of settings
- **Tags**: Searchable keywords
- **Difficulty**: Beginner to Expert
- **Game**: Specific game or genre
- **Author**: Profile creator

### Settings Categories

#### Input Settings
- **Smoothing Factor**: 0.1-1.0
- **Anti-Ghosting**: ON/OFF
- **NKRO Support**: ON/OFF
- **Key Repeat**: Rate and delay
- **Mouse Acceleration**: ON/OFF

#### Performance Settings
- **Polling Rate**: 125Hz-1000Hz
- **DPI Emulation**: ON/OFF with target DPI
- **USB Optimization**: ON/OFF
- **System Tuning**: Automatic/Manual
- **Memory Management**: ON/OFF

#### Hotkey Settings
- **Global Hotkeys**: Enable/disable
- **Hotkey Combinations**: Custom assignments
- **Emergency Hotkeys**: Safety hotkeys
- **Macro Hotkeys**: Macro assignments
- **Test Mode**: Hotkey testing

#### System Settings
- **Startup**: Launch with Windows
- **System Tray**: Minimize to tray
- **Logging**: Enable/disable logging
- **Updates**: Automatic update checking
- **Backup**: Automatic profile backup

## Benchmarking

### Aim Accuracy Test
Test and improve your aiming skills with visual targets.

**Test Configuration:**
- **Duration**: 30-120 seconds
- **Target Size**: 25-100 pixels
- **Target Count**: 5-20 targets
- **Difficulty**: Beginner to Expert

**Scoring System:**
- **Accuracy**: Percentage of targets hit
- **Speed**: Time to hit targets
- **Reaction Time**: Average response time
- **Overall Score**: Weighted combination

**Performance Ranks:**
- **S+ (95-100)**: Elite performance
- **S (90-94)**: Excellent performance
- **A (80-89)**: Very good performance
- **B (70-79)**: Good performance
- **C (60-69)**: Average performance
- **D (50-59)**: Below average
- **F (0-49)**: Needs improvement

**Improvement Tips:**
- Practice regularly with different difficulty levels
- Focus on accuracy before speed
- Use consistent mouse settings
- Track your progress over time

### Key Speed Test
Measure and improve your keyboard speed and accuracy.

**Test Configuration:**
- **Duration**: 30-120 seconds
- **Key Sequence**: 3-8 keys
- **Sequence Length**: 2-6 keys
- **Difficulty**: Beginner to Expert

**Scoring System:**
- **Keys Per Second**: Speed measurement
- **Accuracy**: Percentage of correct keys
- **Consistency**: Timing consistency
- **Overall Score**: Weighted combination

**Improvement Tips:**
- Practice with different key combinations
- Focus on accuracy over speed initially
- Use proper finger positioning
- Practice regularly for muscle memory

### Reaction Time Test
Test and improve your reaction times.

**Test Configuration:**
- **Duration**: 30-120 seconds
- **Stimulus Delay**: 1-4 seconds
- **Stimulus Duration**: 0.5-2 seconds
- **Max Reaction Time**: 2-5 seconds

**Scoring System:**
- **Average Reaction Time**: Mean response time
- **Consistency**: Standard deviation
- **False Starts**: Penalty for early responses
- **Overall Score**: Weighted combination

**Improvement Tips:**
- Practice with different stimulus types
- Focus on consistency over speed
- Maintain good posture and focus
- Get adequate sleep and nutrition

### Performance Analytics
Track your improvement over time.

**Metrics Tracked:**
- **Historical Scores**: All test results
- **Improvement Trends**: Progress over time
- **Best Scores**: Personal records
- **Average Performance**: Consistent performance level

**Analysis Features:**
- **Progress Charts**: Visual progress tracking
- **Performance Comparison**: Compare different time periods
- **Weakness Identification**: Areas needing improvement
- **Goal Setting**: Set and track improvement goals

## Community Features

### Profile Library
Browse and download community-uploaded profiles.

**Browsing Profiles:**
1. Go to Community tab
2. Use search and filter options
3. Browse available profiles
4. Read descriptions and ratings
5. Download interesting profiles

**Search and Filter:**
- **Game**: Filter by specific games
- **Difficulty**: Filter by difficulty level
- **Tags**: Search by keywords
- **Rating**: Filter by user ratings
- **Date**: Sort by upload date

**Profile Information:**
- **Name and Description**: Detailed profile information
- **Author**: Profile creator
- **Rating**: Community rating (1-5 stars)
- **Downloads**: Number of downloads
- **Compatibility**: System requirements

### Uploading Profiles
Share your profiles with the community.

**Upload Process:**
1. Create and test your profile
2. Add detailed metadata
3. Choose appropriate tags
4. Upload to community
5. Respond to feedback

**Profile Requirements:**
- **Tested**: Profile must be thoroughly tested
- **Documented**: Clear description and instructions
- **Tagged**: Appropriate tags for discovery
- **Compatible**: Works on standard systems

**Best Practices:**
- Test on multiple systems
- Provide clear instructions
- Respond to user feedback
- Update profiles as needed

### Rating and Reviews
Rate and review community profiles.

**Rating System:**
- **1-5 Stars**: Overall quality rating
- **Categories**: Performance, Ease of Use, Compatibility
- **Comments**: Detailed feedback
- **Helpful Votes**: Community feedback on reviews

**Review Guidelines:**
- Be constructive and helpful
- Test profiles thoroughly before rating
- Provide specific feedback
- Respect other users

## Troubleshooting

### Common Issues

#### Application Won't Start
**Symptoms:**
- Application fails to launch
- Error messages during startup
- Crashes immediately after launch

**Solutions:**
1. **Check Python version**: Ensure Python 3.8+ is installed
2. **Install dependencies**: Run `pip install -r requirements.txt`
3. **Check permissions**: Run as administrator
4. **Update drivers**: Update graphics and input drivers
5. **Check antivirus**: Temporarily disable antivirus software

#### Input Not Being Detected
**Symptoms:**
- Mouse/keyboard input not registered
- Features not working as expected
- No response to input devices

**Solutions:**
1. **Check connections**: Ensure devices are properly connected
2. **Grant permissions**: Allow ZeroLag to monitor input
3. **Update drivers**: Update mouse and keyboard drivers
4. **Check USB ports**: Try different USB ports
5. **Restart application**: Close and restart ZeroLag

#### Performance Issues
**Symptoms:**
- High CPU usage
- Slow response times
- System lag or stuttering

**Solutions:**
1. **Close other applications**: Free up system resources
2. **Adjust settings**: Lower polling rates or disable features
3. **Update drivers**: Ensure latest drivers are installed
4. **Check system resources**: Monitor CPU and memory usage
5. **Restart system**: Reboot to clear memory issues

#### Hotkeys Not Working
**Symptoms:**
- Hotkeys not responding
- Conflicts with other applications
- Hotkeys work intermittently

**Solutions:**
1. **Check conflicts**: Ensure no conflicts with other apps
2. **Run as administrator**: Some hotkeys require elevated privileges
3. **Test hotkeys**: Use test buttons in Hotkeys tab
4. **Restart application**: Sometimes restart is needed
5. **Check permissions**: Ensure hotkey permissions are granted

### Error Messages

#### "Permission Denied"
**Cause:** Insufficient privileges to access system resources
**Solution:** Run ZeroLag as administrator

#### "Device Not Found"
**Cause:** Input devices not detected or not compatible
**Solution:** Reconnect devices and restart application

#### "Profile Load Error"
**Cause:** Corrupted or incompatible profile file
**Solution:** Check file integrity or create new profile

#### "Configuration Error"
**Cause:** Invalid settings or corrupted configuration
**Solution:** Reset to defaults or restore from backup

### Performance Optimization

#### For Low-End Systems
**Recommendations:**
- Disable visual effects
- Lower polling rates
- Disable unnecessary features
- Close other applications
- Use lightweight profiles

#### For High-End Systems
**Recommendations:**
- Enable all features
- Use maximum polling rates
- Enable advanced smoothing
- Use multiple profiles
- Enable system optimization

## Tips and Tricks

### Gaming Performance
1. **Consistent Settings**: Use the same settings across all games
2. **Profile Switching**: Create profiles for different game types
3. **Regular Testing**: Use benchmark tools to track improvement
4. **System Maintenance**: Keep drivers and system updated
5. **Resource Management**: Close unnecessary applications while gaming

### Profile Management
1. **Backup Profiles**: Regularly backup your profiles
2. **Version Control**: Keep track of profile versions
3. **Testing**: Test profiles thoroughly before using
4. **Documentation**: Document your profile settings
5. **Sharing**: Share successful profiles with the community

### Benchmarking
1. **Regular Practice**: Use benchmark tools regularly
2. **Track Progress**: Monitor your improvement over time
3. **Set Goals**: Establish improvement targets
4. **Compare Results**: Compare with community averages
5. **Identify Weaknesses**: Focus on areas needing improvement

### Community Engagement
1. **Share Knowledge**: Help other users with tips and tricks
2. **Provide Feedback**: Rate and review community profiles
3. **Report Issues**: Help improve the application
4. **Suggest Features**: Contribute to development
5. **Stay Updated**: Keep up with new features and updates

---

This manual covers all major features and functionality of ZeroLag. For additional support, visit the [GitHub repository](https://github.com/imsnokfr/zerolag) or contact the development team.
