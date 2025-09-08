# ZeroLag Project Structure

This document outlines the complete directory structure and organization of the ZeroLag project.

## 📁 Root Directory

```
zerolag/
├── src/                    # Source code
├── tests/                  # Test suite
├── docs/                   # Documentation
├── config/                 # Configuration files
├── assets/                 # Static assets
├── scripts/                # Build and deployment scripts
├── .taskmaster/            # Task Master project management
├── .cursor/                # Cursor IDE configuration
├── README.md               # Project overview
├── CONTRIBUTING.md         # Contribution guidelines
├── LICENSE                 # MIT license
├── requirements.txt        # Python dependencies
└── PROJECT_STRUCTURE.md    # This file
```

## 🐍 Source Code (`src/`)

### Core Module (`src/core/`)
```
core/
├── __init__.py
├── input/                  # Input handling
│   ├── __init__.py
│   ├── mouse_handler.py    # Mouse input capture
│   ├── keyboard_handler.py # Keyboard input capture
│   └── event_queue.py      # Input event queuing
├── processing/             # Input processing
│   ├── __init__.py
│   ├── smoothing.py        # Cursor smoothing algorithms
│   ├── filtering.py        # Input filtering
│   └── optimization.py     # Performance optimization
└── optimization/           # Optimization algorithms
    ├── __init__.py
    ├── dpi_scaling.py      # DPI emulation
    ├── polling_rate.py     # Polling rate enhancement
    └── performance.py      # Performance monitoring
```

### GUI Module (`src/gui/`)
```
gui/
├── __init__.py
├── main_window.py          # Main application window
├── components/             # Reusable components
│   ├── __init__.py
│   ├── dpi_slider.py       # DPI adjustment slider
│   ├── polling_control.py  # Polling rate controls
│   └── performance_meter.py # Performance monitoring
├── dialogs/                # Dialog windows
│   ├── __init__.py
│   ├── settings_dialog.py  # Settings configuration
│   ├── profile_dialog.py   # Profile management
│   └── about_dialog.py     # About information
└── widgets/                # Custom widgets
    ├── __init__.py
    ├── custom_slider.py    # Custom slider widget
    └── status_indicator.py # Status indicators
```

### Profile Management (`src/profiles/`)
```
profiles/
├── __init__.py
├── management/             # Profile management
│   ├── __init__.py
│   ├── profile_manager.py  # Profile save/load
│   ├── profile_validator.py # Profile validation
│   └── profile_migrator.py # Profile migration
└── community/              # Community features
    ├── __init__.py
    ├── profile_sharing.py  # Profile sharing
    ├── community_client.py # Community API client
    └── profile_importer.py # Profile importing
```

### Utilities (`src/utils/`)
```
utils/
├── __init__.py
├── helpers/                # Helper functions
│   ├── __init__.py
│   ├── platform_utils.py  # Platform detection
│   ├── performance_utils.py # Performance utilities
│   └── file_utils.py       # File operations
└── validators/             # Validation utilities
    ├── __init__.py
    ├── input_validators.py # Input validation
    ├── config_validators.py # Configuration validation
    └── profile_validators.py # Profile validation
```

## 🧪 Test Suite (`tests/`)

```
tests/
├── __init__.py
├── unit/                   # Unit tests
│   ├── __init__.py
│   ├── test_core/          # Core module tests
│   ├── test_gui/           # GUI module tests
│   ├── test_profiles/      # Profile module tests
│   └── test_utils/         # Utility module tests
├── integration/            # Integration tests
│   ├── __init__.py
│   ├── test_input_flow.py  # Input processing flow
│   ├── test_gui_integration.py # GUI integration
│   └── test_profile_management.py # Profile management
└── fixtures/               # Test fixtures
    ├── __init__.py
    ├── sample_profiles.json # Sample profile data
    ├── test_config.json    # Test configuration
    └── mock_data.py        # Mock data generators
```

## 📚 Documentation (`docs/`)

```
docs/
├── README.md               # Documentation overview
├── api/                    # API documentation
│   ├── README.md
│   ├── core_api.md         # Core module API
│   ├── gui_api.md          # GUI module API
│   └── utils_api.md        # Utilities API
├── user/                   # User documentation
│   ├── README.md
│   ├── installation.md     # Installation guide
│   ├── getting_started.md  # Getting started
│   ├── features.md         # Feature documentation
│   └── troubleshooting.md  # Troubleshooting
└── developer/              # Developer documentation
    ├── README.md
    ├── architecture.md     # System architecture
    ├── development.md      # Development setup
    ├── testing.md          # Testing guidelines
    └── deployment.md       # Deployment process
```

## ⚙️ Configuration (`config/`)

```
config/
├── defaults/               # Default configurations
│   ├── settings.json       # Default application settings
│   ├── mouse_defaults.json # Default mouse settings
│   └── keyboard_defaults.json # Default keyboard settings
└── templates/              # Configuration templates
    ├── profile_template.json # Profile template
    ├── game_config_template.json # Game configuration template
    └── macro_template.json  # Macro template
```

## 🎨 Assets (`assets/`)

```
assets/
├── icons/                  # Application icons
│   ├── zerolag.ico         # Windows icon
│   ├── zerolag.png         # Application icon
│   └── tray_icon.png       # System tray icon
├── profiles/               # Default profiles
│   ├── fps_default.json    # FPS game profile
│   ├── moba_default.json   # MOBA game profile
│   └── rts_default.json    # RTS game profile
└── sounds/                 # Sound effects
    ├── notification.wav    # Notification sound
    └── error.wav           # Error sound
```

## 🔧 Scripts (`scripts/`)

```
scripts/
├── build/                  # Build scripts
│   ├── build_windows.py    # Windows build script
│   ├── build_macos.py      # macOS build script
│   ├── build_linux.py      # Linux build script
│   └── build_all.py        # Cross-platform build
└── deploy/                 # Deployment scripts
    ├── package_windows.py  # Windows packaging
    ├── package_macos.py    # macOS packaging
    └── package_linux.py    # Linux packaging
```

## 📋 Key Files

### Root Level
- **`README.md`** - Project overview and quick start
- **`CONTRIBUTING.md`** - Contribution guidelines
- **`LICENSE`** - MIT license
- **`requirements.txt`** - Python dependencies
- **`PROJECT_STRUCTURE.md`** - This file

### Source Code
- **`src/main.py`** - Application entry point
- **`src/__init__.py`** - Package initialization

### Configuration
- **`config/defaults/settings.json`** - Default application settings
- **`config/templates/profile_template.json`** - Profile template

## 🎯 Design Principles

### Modularity
- Each module has a clear, single responsibility
- Modules are loosely coupled and highly cohesive
- Easy to test and maintain individual components

### Scalability
- Structure supports future feature additions
- Clear separation between core functionality and UI
- Extensible plugin architecture for profiles and macros

### Maintainability
- Consistent naming conventions
- Comprehensive documentation
- Clear separation of concerns
- Extensive test coverage

### Performance
- Optimized for low-latency gaming applications
- Efficient resource usage
- Platform-specific optimizations

## 🔄 Development Workflow

1. **Feature Development**: Add new features in appropriate modules
2. **Testing**: Write tests in corresponding test directories
3. **Documentation**: Update relevant documentation
4. **Integration**: Ensure components work together
5. **Build**: Use build scripts for packaging
6. **Deploy**: Use deployment scripts for distribution

This structure provides a solid foundation for the ZeroLag project and supports all planned features while maintaining clean, maintainable code.
