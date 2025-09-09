"""
Core Profile Data Structure for ZeroLag

This module defines the comprehensive profile data structure that stores
all user settings, configurations, and preferences for the ZeroLag
gaming input optimization system.

Features:
- Complete settings storage for all ZeroLag components
- Gaming mode categorization and presets
- Profile metadata and versioning
- Validation and compatibility checking
- Serialization and deserialization
- Performance optimization
"""

import time
import json
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from pathlib import Path


class GamingMode(Enum):
    """Gaming mode categories for profile organization."""
    FPS = "fps"
    MOBA = "moba"
    RTS = "rts"
    MMO = "mmo"
    CUSTOM = "custom"
    PRODUCTIVITY = "productivity"
    GENERAL = "general"


@dataclass
class DPISettings:
    """DPI and mouse sensitivity settings."""
    enabled: bool = True
    mode: str = "software"  # software, hybrid, native
    dpi_value: int = 800
    sensitivity_multiplier: float = 1.0
    acceleration_enabled: bool = False
    smoothing_enabled: bool = True
    smoothing_algorithm: str = "low_pass"  # low_pass, ema, kalman, adaptive
    smoothing_factor: float = 0.1
    precision_mode: bool = False
    custom_scaling: Dict[str, float] = field(default_factory=dict)


@dataclass
class PollingSettings:
    """Polling rate and frequency settings."""
    mouse_polling_rate: int = 1000  # Hz
    keyboard_polling_rate: int = 1000  # Hz
    mode: str = "fixed"  # fixed, adaptive, gaming, power_saving
    adaptive_threshold: float = 0.8
    gaming_boost: bool = True
    power_saving_threshold: float = 0.3
    real_time_priority: bool = True
    thread_priority: int = 2  # 0-5, higher = more priority


@dataclass
class KeyboardSettings:
    """Keyboard optimization settings."""
    nkro_enabled: bool = True
    nkro_limit: int = 6
    rapid_trigger_enabled: bool = False
    rapid_trigger_threshold: float = 0.5
    debounce_enabled: bool = True
    debounce_delay: float = 5.0  # ms
    anti_ghosting_enabled: bool = True
    snap_tap_enabled: bool = False
    snap_tap_threshold: float = 0.1
    turbo_mode_enabled: bool = False
    turbo_rate: float = 10.0  # Hz
    adaptive_response_enabled: bool = True
    actuation_emulation_enabled: bool = False
    actuation_distance: float = 2.0  # mm


@dataclass
class SmoothingSettings:
    """Cursor smoothing and filtering settings."""
    enabled: bool = True
    algorithm: str = "low_pass"  # low_pass, ema, kalman, adaptive, gaussian, median
    factor: float = 0.1
    window_size: int = 5
    adaptive_threshold: float = 0.5
    performance_mode: bool = False
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MacroSettings:
    """Macro system settings and associations."""
    enabled: bool = True
    default_library: str = "default"
    auto_save: bool = True
    auto_save_interval: float = 30.0  # seconds
    max_macros_per_library: int = 100
    max_events_per_macro: int = 10000
    playback_speed: float = 1.0
    loop_enabled: bool = False
    hotkey_enabled: bool = True
    macro_hotkeys: Dict[str, str] = field(default_factory=dict)  # macro_name -> hotkey


@dataclass
class PerformanceSettings:
    """Performance monitoring and optimization settings."""
    monitoring_enabled: bool = True
    cpu_monitoring: bool = True
    memory_monitoring: bool = True
    input_monitoring: bool = True
    update_interval: float = 1.0  # seconds
    log_performance: bool = False
    performance_thresholds: Dict[str, float] = field(default_factory=dict)
    optimization_level: int = 2  # 0-3, higher = more aggressive
    memory_limit_mb: float = 100.0
    cpu_limit_percent: float = 80.0


@dataclass
class GUISettings:
    """GUI appearance and behavior settings."""
    theme: str = "dark"  # dark, light, auto
    window_width: int = 800
    window_height: int = 600
    window_x: int = 100
    window_y: int = 100
    always_on_top: bool = False
    minimize_to_tray: bool = True
    show_performance_overlay: bool = False
    performance_overlay_position: str = "top_right"
    language: str = "en"
    font_size: int = 12
    font_family: str = "Segoe UI"
    animations_enabled: bool = True
    compact_mode: bool = False


@dataclass
class HotkeySettings:
    """Hotkey and shortcut configurations."""
    profile_switch_hotkey: str = "ctrl+shift+p"
    macro_record_hotkey: str = "ctrl+shift+r"
    macro_play_hotkey: str = "ctrl+shift+space"
    dpi_cycle_hotkey: str = "ctrl+shift+d"
    polling_cycle_hotkey: str = "ctrl+shift+q"
    emergency_stop_hotkey: str = "ctrl+shift+esc"
    custom_hotkeys: Dict[str, str] = field(default_factory=dict)


@dataclass
class ProfileSettings:
    """Complete profile settings container."""
    dpi: DPISettings = field(default_factory=DPISettings)
    polling: PollingSettings = field(default_factory=PollingSettings)
    keyboard: KeyboardSettings = field(default_factory=KeyboardSettings)
    smoothing: SmoothingSettings = field(default_factory=SmoothingSettings)
    macro: MacroSettings = field(default_factory=MacroSettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    gui: GUISettings = field(default_factory=GUISettings)
    hotkeys: HotkeySettings = field(default_factory=HotkeySettings)


@dataclass
class ProfileMetadata:
    """Profile metadata and versioning information."""
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Default Profile"
    description: str = ""
    version: str = "1.0.0"
    gaming_mode: GamingMode = GamingMode.GENERAL
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    author: str = "ZeroLag User"
    tags: List[str] = field(default_factory=list)
    is_default: bool = False
    is_readonly: bool = False
    compatibility_version: str = "1.0.0"
    file_size: int = 0
    checksum: str = ""


@dataclass
class Profile:
    """
    Complete profile data structure for ZeroLag.
    
    Contains all user settings, configurations, and preferences
    for the gaming input optimization system.
    """
    metadata: ProfileMetadata = field(default_factory=ProfileMetadata)
    settings: ProfileSettings = field(default_factory=ProfileSettings)
    
    def __post_init__(self):
        """Initialize profile after creation."""
        if not self.metadata.profile_id:
            self.metadata.profile_id = str(uuid.uuid4())
        if not self.metadata.created_at:
            self.metadata.created_at = time.time()
        if not self.metadata.modified_at:
            self.metadata.modified_at = time.time()
    
    def update_modified_time(self):
        """Update the modified timestamp."""
        self.metadata.modified_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for serialization."""
        def convert_enum(obj):
            """Convert enums to their values for JSON serialization."""
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, dict):
                return {k: convert_enum(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enum(item) for item in obj]
            else:
                return obj
        
        metadata_dict = asdict(self.metadata)
        settings_dict = asdict(self.settings)
        
        return {
            'metadata': convert_enum(metadata_dict),
            'settings': convert_enum(settings_dict)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """Create profile from dictionary."""
        def convert_enum_back(obj, enum_class=None):
            """Convert enum values back to enum objects."""
            if enum_class and isinstance(obj, str):
                try:
                    return enum_class(obj)
                except ValueError:
                    return obj
            elif isinstance(obj, dict):
                return {k: convert_enum_back(v, enum_class) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enum_back(item, enum_class) for item in obj]
            else:
                return obj
        
        # Handle metadata
        metadata_data = data.get('metadata', {})
        # Convert gaming_mode back to enum
        if 'gaming_mode' in metadata_data:
            metadata_data['gaming_mode'] = convert_enum_back(metadata_data['gaming_mode'], GamingMode)
        metadata = ProfileMetadata(**metadata_data)
        
        # Handle settings
        settings_data = data.get('settings', {})
        
        # Reconstruct nested dataclasses
        dpi_data = settings_data.get('dpi', {})
        dpi = DPISettings(**dpi_data)
        
        polling_data = settings_data.get('polling', {})
        polling = PollingSettings(**polling_data)
        
        keyboard_data = settings_data.get('keyboard', {})
        keyboard = KeyboardSettings(**keyboard_data)
        
        smoothing_data = settings_data.get('smoothing', {})
        smoothing = SmoothingSettings(**smoothing_data)
        
        macro_data = settings_data.get('macro', {})
        macro = MacroSettings(**macro_data)
        
        performance_data = settings_data.get('performance', {})
        performance = PerformanceSettings(**performance_data)
        
        gui_data = settings_data.get('gui', {})
        gui = GUISettings(**gui_data)
        
        hotkeys_data = settings_data.get('hotkeys', {})
        hotkeys = HotkeySettings(**hotkeys_data)
        
        settings = ProfileSettings(
            dpi=dpi,
            polling=polling,
            keyboard=keyboard,
            smoothing=smoothing,
            macro=macro,
            performance=performance,
            gui=gui,
            hotkeys=hotkeys
        )
        
        return cls(metadata=metadata, settings=settings)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert profile to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Profile':
        """Create profile from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: Union[str, Path]) -> bool:
        """Save profile to JSON file."""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            
            # Update metadata
            self.metadata.file_size = file_path.stat().st_size
            self.metadata.checksum = self._calculate_checksum()
            self.update_modified_time()
            
            return True
        except Exception as e:
            print(f"Error saving profile to {file_path}: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> Optional['Profile']:
        """Load profile from JSON file."""
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = cls.from_dict(data)
            
            # Update metadata
            profile.metadata.file_size = file_path.stat().st_size
            profile.metadata.checksum = profile._calculate_checksum()
            
            return profile
        except Exception as e:
            print(f"Error loading profile from {file_path}: {e}")
            return None
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum for profile validation."""
        import hashlib
        profile_str = self.to_json()
        return hashlib.md5(profile_str.encode('utf-8')).hexdigest()
    
    def validate_checksum(self) -> bool:
        """Validate profile checksum."""
        return self.metadata.checksum == self._calculate_checksum()
    
    def clone(self, new_name: str = None) -> 'Profile':
        """Create a copy of the profile with a new name."""
        new_profile = Profile(
            metadata=ProfileMetadata(
                name=new_name or f"{self.metadata.name} (Copy)",
                description=self.metadata.description,
                gaming_mode=self.metadata.gaming_mode,
                author=self.metadata.author,
                tags=self.metadata.tags.copy()
            ),
            settings=ProfileSettings(
                dpi=DPISettings(**asdict(self.settings.dpi)),
                polling=PollingSettings(**asdict(self.settings.polling)),
                keyboard=KeyboardSettings(**asdict(self.settings.keyboard)),
                smoothing=SmoothingSettings(**asdict(self.settings.smoothing)),
                macro=MacroSettings(**asdict(self.settings.macro)),
                performance=PerformanceSettings(**asdict(self.settings.performance)),
                gui=GUISettings(**asdict(self.settings.gui)),
                hotkeys=HotkeySettings(**asdict(self.settings.hotkeys))
            )
        )
        return new_profile
    
    def apply_to_system(self, input_handler, mouse_handler, keyboard_handler, gui_app=None):
        """Apply profile settings to the ZeroLag system components."""
        try:
            # Apply DPI settings
            if hasattr(mouse_handler, 'set_dpi_mode'):
                mouse_handler.set_dpi_mode(self.settings.dpi.mode)
            if hasattr(mouse_handler, 'set_dpi_value'):
                mouse_handler.set_dpi_value(self.settings.dpi.dpi_value)
            if hasattr(mouse_handler, 'set_sensitivity'):
                mouse_handler.set_sensitivity(self.settings.dpi.sensitivity_multiplier)
            
            # Apply polling settings
            if hasattr(input_handler, 'set_polling_mode'):
                input_handler.set_polling_mode(self.settings.polling.mode)
            if hasattr(input_handler, 'set_mouse_polling_rate'):
                input_handler.set_mouse_polling_rate(self.settings.polling.mouse_polling_rate)
            if hasattr(input_handler, 'set_keyboard_polling_rate'):
                input_handler.set_keyboard_polling_rate(self.settings.polling.keyboard_polling_rate)
            
            # Apply keyboard settings
            if hasattr(keyboard_handler, 'set_nkro_mode'):
                keyboard_handler.set_nkro_mode(self.settings.keyboard.nkro_enabled)
            if hasattr(keyboard_handler, 'set_rapid_trigger'):
                keyboard_handler.set_rapid_trigger(self.settings.keyboard.rapid_trigger_enabled)
            if hasattr(keyboard_handler, 'set_debounce'):
                keyboard_handler.set_debounce(self.settings.keyboard.debounce_enabled)
            
            # Apply GUI settings
            if gui_app and hasattr(gui_app, 'apply_profile_settings'):
                gui_app.apply_profile_settings(self.settings.gui)
            
            return True
        except Exception as e:
            print(f"Error applying profile to system: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the profile settings."""
        return {
            'name': self.metadata.name,
            'gaming_mode': self.metadata.gaming_mode.value,
            'dpi': self.settings.dpi.dpi_value,
            'mouse_polling': self.settings.polling.mouse_polling_rate,
            'keyboard_polling': self.settings.polling.keyboard_polling_rate,
            'nkro_enabled': self.settings.keyboard.nkro_enabled,
            'smoothing_enabled': self.settings.smoothing.enabled,
            'macro_enabled': self.settings.macro.enabled,
            'theme': self.settings.gui.theme,
            'created': time.strftime('%Y-%m-%d %H:%M', time.localtime(self.metadata.created_at)),
            'modified': time.strftime('%Y-%m-%d %H:%M', time.localtime(self.metadata.modified_at))
        }


# Example usage and testing
if __name__ == "__main__":
    # Create a test profile
    profile = Profile()
    profile.metadata.name = "Test Profile"
    profile.metadata.description = "A test profile for development"
    profile.metadata.gaming_mode = GamingMode.FPS
    
    # Modify some settings
    profile.settings.dpi.dpi_value = 1600
    profile.settings.polling.mouse_polling_rate = 8000
    profile.settings.keyboard.nkro_enabled = True
    
    # Save to file
    profile.save_to_file("test_profile.json")
    
    # Load from file
    loaded_profile = Profile.load_from_file("test_profile.json")
    
    if loaded_profile:
        print(f"Loaded profile: {loaded_profile.metadata.name}")
        print(f"DPI: {loaded_profile.settings.dpi.dpi_value}")
        print(f"Mouse polling: {loaded_profile.settings.polling.mouse_polling_rate}Hz")
        print(f"NKRO enabled: {loaded_profile.settings.keyboard.nkro_enabled}")
    
    # Get summary
    summary = profile.get_summary()
    print(f"Profile summary: {summary}")
