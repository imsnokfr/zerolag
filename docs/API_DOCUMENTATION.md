# ZeroLag API Documentation

## Overview

ZeroLag provides a comprehensive API for developers to integrate input optimization features into their applications. The API is built on Python and provides both high-level and low-level interfaces for input processing, optimization, and monitoring.

## Table of Contents
1. [Core Modules](#core-modules)
2. [Input Processing](#input-processing)
3. [Optimization Algorithms](#optimization-algorithms)
4. [Profile Management](#profile-management)
5. [Benchmarking](#benchmarking)
6. [Community Features](#community-features)
7. [Event System](#event-system)
8. [Configuration](#configuration)
9. [Examples](#examples)

## Core Modules

### Input Handler
The main input processing module that coordinates all input optimization.

```python
from src.core.input.input_handler import InputHandler

# Initialize input handler
handler = InputHandler()

# Start processing
handler.start()

# Stop processing
handler.stop()
```

**Key Methods:**
- `start()`: Begin input processing
- `stop()`: Stop input processing
- `set_smoothing(enabled, factor)`: Configure mouse smoothing
- `set_anti_ghosting(enabled)`: Enable/disable anti-ghosting
- `set_nkro(enabled)`: Enable/disable NKRO support

### Mouse Handler
Specialized handler for mouse input optimization.

```python
from src.core.input.mouse_handler import MouseHandler

# Initialize mouse handler
mouse = MouseHandler()

# Configure smoothing
mouse.set_smoothing(enabled=True, factor=0.5)

# Set DPI emulation
mouse.set_dpi_emulation(enabled=True, target_dpi=800)
```

**Key Methods:**
- `set_smoothing(enabled, factor)`: Configure smoothing
- `set_dpi_emulation(enabled, target_dpi)`: Set DPI emulation
- `set_polling_rate(rate)`: Set USB polling rate
- `get_performance_metrics()`: Get performance statistics

### Keyboard Handler
Specialized handler for keyboard input optimization.

```python
from src.core.input.keyboard_handler import KeyboardHandler

# Initialize keyboard handler
keyboard = KeyboardHandler()

# Configure anti-ghosting
keyboard.set_anti_ghosting(enabled=True)

# Set NKRO support
keyboard.set_nkro(enabled=True)
```

**Key Methods:**
- `set_anti_ghosting(enabled)`: Enable anti-ghosting
- `set_nkro(enabled)`: Enable NKRO support
- `set_debounce_threshold(threshold)`: Set key debounce
- `get_key_state(key)`: Get current key state

## Input Processing

### Event System
ZeroLag uses a comprehensive event system for input processing.

```python
from src.core.input.input_handler import InputHandler
from src.core.input.events import MouseEvent, KeyboardEvent

# Initialize handler
handler = InputHandler()

# Register event callbacks
def on_mouse_move(event: MouseEvent):
    print(f"Mouse moved to ({event.x}, {event.y})")

def on_key_press(event: KeyboardEvent):
    print(f"Key pressed: {event.key}")

# Register callbacks
handler.on_mouse_move = on_mouse_move
handler.on_key_press = on_key_press
```

### Event Types

#### MouseEvent
```python
@dataclass
class MouseEvent:
    x: float
    y: float
    button: Optional[str] = None
    pressed: bool = False
    timestamp: float = 0.0
    delta_x: float = 0.0
    delta_y: float = 0.0
```

#### KeyboardEvent
```dataclass
class KeyboardEvent:
    key: str
    pressed: bool
    timestamp: float = 0.0
    modifiers: List[str] = field(default_factory=list)
```

### Input Filtering
Apply filters to input events for optimization.

```python
from src.core.input.filters import SmoothingFilter, AntiGhostingFilter

# Create filters
smoothing_filter = SmoothingFilter(factor=0.5)
anti_ghosting_filter = AntiGhostingFilter()

# Apply filters to events
filtered_event = smoothing_filter.process(mouse_event)
filtered_event = anti_ghosting_filter.process(keyboard_event)
```

## Optimization Algorithms

### Smoothing Algorithms
Advanced algorithms for mouse movement smoothing.

```python
from src.core.smoothing.smoothing_algorithms import SmoothingAlgorithms

# Initialize smoothing
smoothing = SmoothingAlgorithms()

# Configure algorithm
smoothing.set_algorithm("exponential")
smoothing.set_factor(0.5)
smoothing.set_sensitivity(1.0)

# Process mouse movement
smoothed_x, smoothed_y = smoothing.process_movement(x, y, delta_x, delta_y)
```

**Available Algorithms:**
- `exponential`: Exponential smoothing
- `linear`: Linear interpolation
- `adaptive`: Adaptive smoothing based on movement speed
- `custom`: Custom algorithm implementation

### Anti-Ghosting
Prevent key conflicts during simultaneous key presses.

```python
from src.core.keyboard.anti_ghosting import AntiGhostingManager

# Initialize anti-ghosting
anti_ghosting = AntiGhostingManager()

# Configure key matrix
anti_ghosting.set_key_matrix(key_matrix)
anti_ghosting.set_conflict_resolution("priority")

# Process key events
processed_event = anti_ghosting.process_key_event(key_event)
```

### NKRO Support
Full keyboard rollover support.

```python
from src.core.keyboard.nkro import NKROManager

# Initialize NKRO
nkro = NKROManager()

# Enable NKRO
nkro.enable()

# Check NKRO support
if nkro.is_supported():
    print("NKRO is supported")
```

## Profile Management

### Profile System
Comprehensive profile management for different gaming scenarios.

```python
from src.core.profiles import Profile, ProfileManager

# Initialize profile manager
profile_manager = ProfileManager()

# Create new profile
profile = Profile()
profile.metadata.name = "FPS Gaming"
profile.metadata.description = "Optimized for FPS games"
profile.settings.smoothing.enabled = True
profile.settings.smoothing.factor = 0.3

# Save profile
profile_manager.save_profile(profile)

# Load profile
loaded_profile = profile_manager.load_profile("FPS Gaming")
```

### Profile Settings
Detailed configuration options for profiles.

```python
from src.core.profiles import ProfileSettings

# Create settings
settings = ProfileSettings()

# Configure input settings
settings.smoothing.enabled = True
settings.smoothing.factor = 0.5
settings.keyboard.anti_ghosting_enabled = True
settings.keyboard.nkro_enabled = True

# Configure performance settings
settings.dpi.enabled = True
settings.dpi.target_dpi = 800
settings.polling.mouse_rate = 1000
settings.polling.keyboard_rate = 1000
```

### Profile Export/Import
Share profiles between systems.

```python
from src.core.profiles import ProfileExporter

# Export profile
exporter = ProfileExporter()
exporter.export_profile(profile, "fps_profile.json")

# Import profile
imported_profile = exporter.import_profile("fps_profile.json")
```

## Benchmarking

### Benchmark System
Comprehensive benchmarking tools for performance testing.

```python
from src.core.benchmark import BenchmarkManager, BenchmarkConfig

# Create benchmark configuration
config = BenchmarkConfig(
    test_duration=30.0,
    target_size=50.0,
    target_count=10
)

# Initialize benchmark manager
benchmark = BenchmarkManager(config)

# Start aim accuracy test
benchmark.start_test("aim_accuracy")

# Handle test events
def on_test_finished(result):
    print(f"Test completed with score: {result.overall_score}")

benchmark.test_finished.connect(on_test_finished)
```

### Test Types
Different types of benchmark tests available.

#### Aim Accuracy Test
```python
from src.core.benchmark.aim_test import AimAccuracyTest

# Create aim test
aim_test = AimAccuracyTest({
    'test_duration': 30.0,
    'target_size': 50.0,
    'target_count': 10
})

# Start test
aim_test.start_test(width=800, height=600)

# Handle mouse clicks
aim_test.handle_click(x, y)
```

#### Key Speed Test
```python
from src.core.benchmark.key_speed_test import KeySpeedTest

# Create key speed test
key_test = KeySpeedTest({
    'test_duration': 30.0,
    'key_sequence_length': 4
})

# Start test
key_test.start_test()

# Handle key presses
key_test.handle_key_press('a')
```

#### Reaction Time Test
```python
from src.core.benchmark.reaction_test import ReactionTimeTest

# Create reaction test
reaction_test = ReactionTimeTest({
    'test_duration': 30.0,
    'stimulus_delay_min': 1.0,
    'stimulus_delay_max': 4.0
})

# Start test
reaction_test.start_test()

# Handle responses
reaction_test.handle_response()
```

### Metrics and Scoring
Comprehensive metrics and scoring system.

```python
from src.core.benchmark.metrics import ScoreCalculator, TestMetrics

# Calculate scores
aim_score = ScoreCalculator.calculate_aim_score(accuracy=0.9, speed=0.8, reaction_time=0.5)
key_score = ScoreCalculator.calculate_key_speed_score(keys_per_second=5.0, accuracy=0.95)
reaction_score = ScoreCalculator.calculate_reaction_score(reaction_time=0.3, consistency=0.9)

# Get performance rank
rank = ScoreCalculator.get_performance_rank(score=95.0)
```

## Community Features

### Profile Sharing
Upload and download community profiles.

```python
from src.core.community import ProfileSharingManager, GitHubProfileRepository

# Initialize sharing manager
sharing_manager = ProfileSharingManager()

# Configure GitHub repository
github_config = ProfileRepositoryConfig(
    owner="zerolag-community",
    repo="profiles",
    token="your_github_token"
)

# Set up repository
sharing_manager.set_repository(GitHubProfileRepository(github_config))

# Upload profile
sharing_manager.upload_profile(profile, metadata)

# Download profile
downloaded_profile = sharing_manager.download_profile(profile_id)
```

### Profile Library
Manage local profile library.

```python
from src.core.community import ProfileLibraryManager

# Initialize library manager
library_manager = ProfileLibraryManager(Path("profiles/community"))

# Search profiles
results = library_manager.search_profiles(
    query="FPS",
    category=ProfileCategory.FPS,
    difficulty=ProfileDifficulty.INTERMEDIATE
)

# Get featured profiles
featured = library_manager.get_featured_profiles()
```

### Profile Validation
Validate profiles for compatibility and integrity.

```python
from src.core.community import ProfileValidator, CompatibilityChecker

# Initialize validators
validator = ProfileValidator()
compatibility_checker = CompatibilityChecker()

# Validate profile
validation_result = validator.validate_profile(profile)
if validation_result.is_valid:
    print("Profile is valid")
else:
    print(f"Validation errors: {validation_result.errors}")

# Check compatibility
compatibility = compatibility_checker.check_compatibility(profile, system_info)
```

## Event System

### Signal/Slot System
ZeroLag uses PyQt5's signal/slot system for event handling.

```python
from PyQt5.QtCore import QObject, pyqtSignal

class CustomInputHandler(QObject):
    # Define signals
    mouse_moved = pyqtSignal(float, float)
    key_pressed = pyqtSignal(str)
    test_completed = pyqtSignal(object)
    
    def __init__(self):
        super().__init__()
    
    def handle_mouse_move(self, x, y):
        # Emit signal
        self.mouse_moved.emit(x, y)
    
    def handle_key_press(self, key):
        # Emit signal
        self.key_pressed.emit(key)

# Connect to signals
handler = CustomInputHandler()
handler.mouse_moved.connect(lambda x, y: print(f"Mouse: {x}, {y}"))
handler.key_pressed.connect(lambda key: print(f"Key: {key}"))
```

### Custom Events
Create custom events for specific functionality.

```python
from PyQt5.QtCore import QEvent

class CustomEvent(QEvent):
    def __init__(self, event_type, data):
        super().__init__(QEvent.User)
        self.event_type = event_type
        self.data = data

# Use custom events
def custom_event_handler(event):
    if event.event_type == "profile_changed":
        print(f"Profile changed: {event.data}")

# Post custom event
custom_event = CustomEvent("profile_changed", "FPS Gaming")
QApplication.postEvent(target_object, custom_event)
```

## Configuration

### Configuration Management
Centralized configuration management system.

```python
from src.core.config import ConfigManager

# Initialize config manager
config = ConfigManager()

# Set configuration values
config.set("input.smoothing.enabled", True)
config.set("input.smoothing.factor", 0.5)
config.set("performance.polling_rate", 1000)

# Get configuration values
smoothing_enabled = config.get("input.smoothing.enabled", False)
smoothing_factor = config.get("input.smoothing.factor", 0.3)

# Save configuration
config.save("config.json")

# Load configuration
config.load("config.json")
```

### Environment Variables
Use environment variables for configuration.

```python
import os
from src.core.config import ConfigManager

# Set environment variables
os.environ["ZEROLAG_DEBUG"] = "true"
os.environ["ZEROLAG_LOG_LEVEL"] = "INFO"

# Initialize config with environment
config = ConfigManager()
config.load_from_environment()
```

## Examples

### Basic Input Optimization
```python
from src.core.input.input_handler import InputHandler
from src.core.profiles import ProfileManager

# Initialize components
input_handler = InputHandler()
profile_manager = ProfileManager()

# Load profile
profile = profile_manager.load_profile("FPS Gaming")

# Apply profile settings
input_handler.set_smoothing(
    enabled=profile.settings.smoothing.enabled,
    factor=profile.settings.smoothing.factor
)

# Start processing
input_handler.start()
```

### Custom Benchmark Test
```python
from src.core.benchmark import BenchmarkManager, BenchmarkConfig
from src.core.benchmark.metrics import TestMetrics, TestType

# Create custom test
class CustomTest:
    def __init__(self):
        self.test_active = False
        self.start_time = 0.0
        self.end_time = 0.0
    
    def start_test(self):
        self.test_active = True
        self.start_time = time.time()
    
    def stop_test(self):
        self.test_active = False
        self.end_time = time.time()
    
    def get_metrics(self):
        return TestMetrics(
            test_type=TestType.CUSTOM,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=self.end_time - self.start_time,
            score=85.0,
            accuracy=0.9,
            speed=0.8,
            reaction_time=0.3,
            errors=0,
            total_attempts=10,
            success_rate=0.9
        )

# Use custom test
custom_test = CustomTest()
custom_test.start_test()
# ... perform test ...
custom_test.stop_test()
metrics = custom_test.get_metrics()
```

### Profile Sharing Integration
```python
from src.core.community import ProfileSharingManager, ProfileRepositoryConfig
from src.core.profiles import Profile

# Initialize sharing
sharing_manager = ProfileSharingManager()

# Configure repository
config = ProfileRepositoryConfig(
    owner="your-username",
    repo="zerolag-profiles",
    token="your_github_token"
)

# Set up repository
sharing_manager.set_repository(GitHubProfileRepository(config))

# Create and upload profile
profile = Profile()
profile.metadata.name = "My FPS Profile"
profile.metadata.description = "Custom FPS optimization"
profile.settings.smoothing.factor = 0.3

# Upload with metadata
metadata = {
    "name": "My FPS Profile",
    "description": "Custom FPS optimization",
    "category": "FPS",
    "difficulty": "Intermediate",
    "tags": ["fps", "competitive", "custom"]
}

sharing_manager.upload_profile(profile, metadata)
```

### GUI Integration
```python
from PyQt5.QtWidgets import QApplication, QMainWindow
from src.gui.main_window import ZeroLagMainWindow

# Create application
app = QApplication(sys.argv)

# Create main window
window = ZeroLagMainWindow()

# Show window
window.show()

# Run application
sys.exit(app.exec_())
```

## Error Handling

### Exception Handling
Comprehensive error handling throughout the API.

```python
from src.core.exceptions import ZeroLagError, InputError, ProfileError

try:
    # Initialize input handler
    input_handler = InputHandler()
    input_handler.start()
except InputError as e:
    print(f"Input error: {e}")
except ZeroLagError as e:
    print(f"ZeroLag error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Logging
Built-in logging system for debugging and monitoring.

```python
import logging
from src.core.logging import setup_logging

# Setup logging
setup_logging(level=logging.INFO)

# Get logger
logger = logging.getLogger(__name__)

# Log messages
logger.info("Application started")
logger.warning("Low memory warning")
logger.error("Input device not found")
```

## Performance Considerations

### Memory Management
Efficient memory usage for optimal performance.

```python
from src.core.memory import MemoryManager

# Initialize memory manager
memory_manager = MemoryManager()

# Monitor memory usage
memory_usage = memory_manager.get_memory_usage()
if memory_usage > 0.8:  # 80% memory usage
    memory_manager.cleanup()
```

### Threading
Thread-safe operations for concurrent processing.

```python
from PyQt5.QtCore import QThread, pyqtSignal

class InputProcessingThread(QThread):
    def __init__(self, input_handler):
        super().__init__()
        self.input_handler = input_handler
    
    def run(self):
        self.input_handler.start()
        self.exec_()

# Use thread
thread = InputProcessingThread(input_handler)
thread.start()
```

---

This API documentation provides comprehensive information for developers who want to integrate ZeroLag's functionality into their applications. For additional examples and advanced usage, refer to the source code and test files in the repository.
