# ZeroLag

A lightweight, Python-based desktop application designed to optimize standard mouse and keyboard inputs for competitive gaming, targeting players using generic hardware without proprietary software.

## 🎯 Overview

ZeroLag leverages low-level system APIs, event interception, and advanced algorithms to minimize input latency, maximize responsiveness, and enable rapid, precise actions for genres like FPS, MOBA, RTS, and MMO. It delivers gaming-grade performance with negligible system overhead, ensuring no FPS drops or lag spikes.

## ✨ Key Features

### 🖱️ Mouse Optimization
- **DPI Emulation**: Software-based DPI adjustment from 400 to 26,000 in 50-unit increments
- **High-Frequency Polling**: Up to 8000Hz polling rates with adaptive adjustment
- **Input Queuing**: High-frequency event processing with configurable buffer management
- **Smoothing Algorithms**: Low-pass filters and exponential moving averages for jitter-free cursor tracking
- **Precision Features**: Angle snapping, prediction toggles, and rotation adjustment

### ⌨️ Keyboard Optimization
- **High-Frequency Polling**: Up to 8000Hz keyboard event capture
- **Anti-Ghosting**: NKRO simulation for simultaneous key presses
- **Rapid Key Actions**: Rapid Trigger and Snap Tap emulation
- **Debounce Algorithms**: Configurable thresholds for chatter elimination
- **Turbo Mode**: Rapid key repeat simulation

### 🎮 Advanced Features
- **Macro System**: Recording, editing, and playback with timeline view
- **Profile Management**: Game-specific profiles with auto-switching
- **Button Remapping**: Comprehensive key/button reassignment
- **System Tray Integration**: Background operation with quick access
- **Emergency Hotkey**: Instant optimization disable (Ctrl+Alt+Z)

## 🚀 Performance Targets

- **CPU Usage**: <1% during intensive gaming
- **Memory Usage**: <50MB RAM
- **Latency Overhead**: <5ms for all processing
- **Input Lag Reduction**: 30-50% improvement
- **Speed/Accuracy**: 20-40% improvement

## 🛠️ Technical Stack

- **Core**: Python 3.10+
- **GUI**: PyQt5
- **Input Handling**: pynput, platform-specific APIs
- **Platform Support**: Windows (pywin32), macOS (pyObjC), Linux (python-evdev)
- **Packaging**: PyInstaller

## 📋 Requirements

- Python 3.10 or higher
- Windows 10/11, macOS Ventura+, or Ubuntu/Debian
- Generic USB/PS2 mouse and keyboard

## 🚀 Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/zerolag.git
   cd zerolag
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python src/main.py
   ```

## 📖 Usage

1. **Installation**: Download and run the executable or install from source
2. **Onboarding**: Wizard guides DPI/polling/queue setup with in-app tests
3. **Customization**: Configure profiles, tweak settings via GUI, save presets
4. **Gameplay**: Runs in background; auto-applies game-specific profiles
5. **Community**: Share/import profiles via GitHub integration

## 🎮 Supported Games

- **FPS**: Valorant, CS2, Apex Legends
- **MOBA**: League of Legends, Dota 2
- **RTS**: StarCraft II, Age of Empires
- **MMO**: World of Warcraft, Final Fantasy XIV

## 🔧 Development

### Project Structure
```
zerolag/
├── src/                    # Source code
│   ├── core/              # Core input handling
│   ├── gui/               # PyQt5 interface
│   ├── profiles/          # Profile management
│   └── utils/             # Utilities and helpers
├── tests/                 # Test suite
├── docs/                  # Documentation
├── config/                # Configuration files
└── requirements.txt       # Dependencies
```

### Building from Source
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Build executable
python -m PyInstaller src/main.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

ZeroLag is designed for legitimate gaming optimization. Users are responsible for ensuring compliance with game terms of service and anti-cheat systems. The developers are not responsible for any issues arising from the use of this software.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/zerolag/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/zerolag/discussions)
- **Discord**: [Join our Discord](https://discord.gg/zerolag)

## 🎯 Roadmap

- **v1.0 (MVP)**: Core DPI, polling, smoothing, and input queuing
- **v1.1**: Macro system, remapping, and auto-profile switching
- **v1.2**: Advanced emulations like Rapid Trigger and Snap Tap
- **v2.0**: ML-based auto-tuning and pattern detection

## 📊 Success Metrics

- **Performance**: 30%+ lag reduction in aim trainers
- **Adoption**: 100,000 GitHub downloads in 12 months
- **Stability**: <1% crash rate across supported platforms
- **Community**: 1,000+ shared profiles

---

**Made with ❤️ for the gaming community**
