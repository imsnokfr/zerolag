"""
Gaming Mode Presets for ZeroLag

This module provides predefined gaming mode presets optimized for different
game genres and use cases. Each preset is carefully tuned for specific
gaming scenarios to provide the best possible input experience.

Presets:
- FPS Mode: Optimized for first-person shooters
- MOBA Mode: Balanced settings for MOBA games
- RTS Mode: Precision-focused for real-time strategy
- MMO Mode: Customizable settings for MMO games
- Custom Mode: User-defined settings
- Productivity Mode: General computing and productivity

Features:
- Genre-specific optimizations
- Performance-tuned settings
- Easy profile creation
- Preset customization
- Quick switching between modes
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from .profile import Profile, GamingMode, DPISettings, PollingSettings, KeyboardSettings, SmoothingSettings, MacroSettings, PerformanceSettings, GUISettings, HotkeySettings, ProfileSettings


@dataclass
class GamingModePresets:
    """Container for all gaming mode presets."""
    
    @staticmethod
    def create_fps_profile(name: str = "FPS Mode") -> Profile:
        """Create FPS-optimized profile."""
        profile = Profile()
        profile.metadata.name = name
        profile.metadata.description = "Optimized for first-person shooters - high precision, low latency"
        profile.metadata.gaming_mode = GamingMode.FPS
        profile.metadata.tags = ["fps", "shooter", "precision", "competitive"]
        
        # DPI settings - high DPI for precision
        profile.settings.dpi = DPISettings(
            enabled=True,
            mode="hybrid",
            dpi_value=1600,
            sensitivity_multiplier=0.8,
            acceleration_enabled=False,
            smoothing_enabled=False,  # No smoothing for FPS
            smoothing_algorithm="low_pass",
            smoothing_factor=0.05,
            precision_mode=True
        )
        
        # Polling settings - maximum performance
        profile.settings.polling = PollingSettings(
            mouse_polling_rate=8000,
            keyboard_polling_rate=1000,
            mode="gaming",
            adaptive_threshold=0.9,
            gaming_boost=True,
            real_time_priority=True,
            thread_priority=3
        )
        
        # Keyboard settings - minimal latency
        profile.settings.keyboard = KeyboardSettings(
            nkro_enabled=True,
            nkro_limit=6,
            rapid_trigger_enabled=True,
            rapid_trigger_threshold=0.3,
            debounce_enabled=True,
            debounce_delay=2.0,
            anti_ghosting_enabled=True,
            adaptive_response_enabled=True
        )
        
        # Smoothing settings - disabled for FPS
        profile.settings.smoothing = SmoothingSettings(
            enabled=False,
            algorithm="low_pass",
            factor=0.0,
            performance_mode=True
        )
        
        # Macro settings - basic support
        profile.settings.macro = MacroSettings(
            enabled=True,
            default_library="fps_macros",
            auto_save=True,
            auto_save_interval=60.0,
            max_macros_per_library=50,
            playback_speed=1.0,
            hotkey_enabled=True
        )
        
        # Performance settings - maximum performance
        profile.settings.performance = PerformanceSettings(
            monitoring_enabled=True,
            cpu_monitoring=True,
            memory_monitoring=True,
            input_monitoring=True,
            update_interval=0.5,
            log_performance=False,
            optimization_level=3,
            memory_limit_mb=50.0,
            cpu_limit_percent=90.0
        )
        
        # GUI settings - minimal distraction
        profile.settings.gui = GUISettings(
            theme="dark",
            show_performance_overlay=True,
            performance_overlay_position="top_left",
            compact_mode=True,
            animations_enabled=False
        )
        
        # Hotkey settings - FPS-specific
        profile.settings.hotkeys = HotkeySettings(
            profile_switch_hotkey="ctrl+shift+f",
            macro_record_hotkey="ctrl+shift+r",
            macro_play_hotkey="ctrl+shift+space",
            dpi_cycle_hotkey="ctrl+shift+d",
            polling_cycle_hotkey="ctrl+shift+q",
            emergency_stop_hotkey="ctrl+shift+esc"
        )
        
        return profile
    
    @staticmethod
    def create_moba_profile(name: str = "MOBA Mode") -> Profile:
        """Create MOBA-optimized profile."""
        profile = Profile()
        profile.metadata.name = name
        profile.metadata.description = "Balanced settings for MOBA games - precision with comfort"
        profile.metadata.gaming_mode = GamingMode.MOBA
        profile.metadata.tags = ["moba", "strategy", "balanced", "comfort"]
        
        # DPI settings - balanced
        profile.settings.dpi = DPISettings(
            enabled=True,
            mode="software",
            dpi_value=1200,
            sensitivity_multiplier=1.0,
            acceleration_enabled=False,
            smoothing_enabled=True,
            smoothing_algorithm="ema",
            smoothing_factor=0.15,
            precision_mode=False
        )
        
        # Polling settings - balanced performance
        profile.settings.polling = PollingSettings(
            mouse_polling_rate=2000,
            keyboard_polling_rate=1000,
            mode="adaptive",
            adaptive_threshold=0.7,
            gaming_boost=True,
            real_time_priority=True,
            thread_priority=2
        )
        
        # Keyboard settings - balanced
        profile.settings.keyboard = KeyboardSettings(
            nkro_enabled=True,
            nkro_limit=6,
            rapid_trigger_enabled=False,
            debounce_enabled=True,
            debounce_delay=5.0,
            anti_ghosting_enabled=True,
            snap_tap_enabled=True,
            snap_tap_threshold=0.2,
            adaptive_response_enabled=True
        )
        
        # Smoothing settings - light smoothing
        profile.settings.smoothing = SmoothingSettings(
            enabled=True,
            algorithm="ema",
            factor=0.15,
            window_size=3,
            performance_mode=False
        )
        
        # Macro settings - extensive support
        profile.settings.macro = MacroSettings(
            enabled=True,
            default_library="moba_macros",
            auto_save=True,
            auto_save_interval=30.0,
            max_macros_per_library=100,
            playback_speed=1.0,
            loop_enabled=True,
            hotkey_enabled=True,
            macro_hotkeys={
                "ability_1": "q",
                "ability_2": "w",
                "ability_3": "e",
                "ability_4": "r",
                "item_1": "1",
                "item_2": "2"
            }
        )
        
        # Performance settings - balanced
        profile.settings.performance = PerformanceSettings(
            monitoring_enabled=True,
            cpu_monitoring=True,
            memory_monitoring=True,
            input_monitoring=True,
            update_interval=1.0,
            log_performance=False,
            optimization_level=2,
            memory_limit_mb=75.0,
            cpu_limit_percent=80.0
        )
        
        # GUI settings - comfortable
        profile.settings.gui = GUISettings(
            theme="dark",
            show_performance_overlay=False,
            compact_mode=False,
            animations_enabled=True
        )
        
        return profile
    
    @staticmethod
    def create_rts_profile(name: str = "RTS Mode") -> Profile:
        """Create RTS-optimized profile."""
        profile = Profile()
        profile.metadata.name = name
        profile.metadata.description = "Precision-focused for real-time strategy games"
        profile.metadata.gaming_mode = GamingMode.RTS
        profile.metadata.tags = ["rts", "strategy", "precision", "hotkeys"]
        
        # DPI settings - lower for precision
        profile.settings.dpi = DPISettings(
            enabled=True,
            mode="software",
            dpi_value=800,
            sensitivity_multiplier=1.2,
            acceleration_enabled=False,
            smoothing_enabled=True,
            smoothing_algorithm="low_pass",
            smoothing_factor=0.2,
            precision_mode=True
        )
        
        # Polling settings - standard
        profile.settings.polling = PollingSettings(
            mouse_polling_rate=1000,
            keyboard_polling_rate=1000,
            mode="fixed",
            gaming_boost=False,
            real_time_priority=False,
            thread_priority=1
        )
        
        # Keyboard settings - hotkey focused
        profile.settings.keyboard = KeyboardSettings(
            nkro_enabled=True,
            nkro_limit=10,
            rapid_trigger_enabled=False,
            debounce_enabled=True,
            debounce_delay=8.0,
            anti_ghosting_enabled=True,
            turbo_mode_enabled=True,
            turbo_rate=5.0,
            adaptive_response_enabled=False
        )
        
        # Smoothing settings - moderate smoothing
        profile.settings.smoothing = SmoothingSettings(
            enabled=True,
            algorithm="low_pass",
            factor=0.2,
            window_size=5,
            performance_mode=False
        )
        
        # Macro settings - extensive hotkey support
        profile.settings.macro = MacroSettings(
            enabled=True,
            default_library="rts_macros",
            auto_save=True,
            auto_save_interval=15.0,
            max_macros_per_library=200,
            playback_speed=1.2,
            loop_enabled=True,
            hotkey_enabled=True,
            macro_hotkeys={
                "select_all": "ctrl+a",
                "select_workers": "ctrl+w",
                "select_army": "ctrl+shift+a",
                "build_worker": "ctrl+b",
                "build_army": "ctrl+shift+b"
            }
        )
        
        # Performance settings - standard
        profile.settings.performance = PerformanceSettings(
            monitoring_enabled=True,
            cpu_monitoring=True,
            memory_monitoring=True,
            input_monitoring=False,
            update_interval=2.0,
            log_performance=False,
            optimization_level=1,
            memory_limit_mb=100.0,
            cpu_limit_percent=70.0
        )
        
        # GUI settings - productivity focused
        profile.settings.gui = GUISettings(
            theme="light",
            show_performance_overlay=False,
            compact_mode=False,
            animations_enabled=False
        )
        
        return profile
    
    @staticmethod
    def create_mmo_profile(name: str = "MMO Mode") -> Profile:
        """Create MMO-optimized profile."""
        profile = Profile()
        profile.metadata.name = name
        profile.metadata.description = "Customizable settings for MMO games with extensive macro support"
        profile.metadata.gaming_mode = GamingMode.MMO
        profile.metadata.tags = ["mmo", "rpg", "macros", "customizable"]
        
        # DPI settings - customizable
        profile.settings.dpi = DPISettings(
            enabled=True,
            mode="hybrid",
            dpi_value=1000,
            sensitivity_multiplier=1.0,
            acceleration_enabled=False,
            smoothing_enabled=True,
            smoothing_algorithm="adaptive",
            smoothing_factor=0.1,
            precision_mode=False
        )
        
        # Polling settings - adaptive
        profile.settings.polling = PollingSettings(
            mouse_polling_rate=1000,
            keyboard_polling_rate=1000,
            mode="adaptive",
            adaptive_threshold=0.6,
            gaming_boost=False,
            real_time_priority=False,
            thread_priority=1
        )
        
        # Keyboard settings - macro focused
        profile.settings.keyboard = KeyboardSettings(
            nkro_enabled=True,
            nkro_limit=6,
            rapid_trigger_enabled=False,
            debounce_enabled=True,
            debounce_delay=10.0,
            anti_ghosting_enabled=True,
            turbo_mode_enabled=True,
            turbo_rate=2.0,
            adaptive_response_enabled=False
        )
        
        # Smoothing settings - adaptive
        profile.settings.smoothing = SmoothingSettings(
            enabled=True,
            algorithm="adaptive",
            factor=0.1,
            window_size=7,
            adaptive_threshold=0.5,
            performance_mode=False
        )
        
        # Macro settings - extensive support
        profile.settings.macro = MacroSettings(
            enabled=True,
            default_library="mmo_macros",
            auto_save=True,
            auto_save_interval=10.0,
            max_macros_per_library=500,
            max_events_per_macro=50000,
            playback_speed=1.0,
            loop_enabled=True,
            hotkey_enabled=True,
            macro_hotkeys={
                "rotation_1": "f1",
                "rotation_2": "f2",
                "rotation_3": "f3",
                "buff_sequence": "f4",
                "emergency_heal": "f5"
            }
        )
        
        # Performance settings - monitoring focused
        profile.settings.performance = PerformanceSettings(
            monitoring_enabled=True,
            cpu_monitoring=True,
            memory_monitoring=True,
            input_monitoring=True,
            update_interval=1.0,
            log_performance=True,
            optimization_level=1,
            memory_limit_mb=150.0,
            cpu_limit_percent=60.0
        )
        
        # GUI settings - feature rich
        profile.settings.gui = GUISettings(
            theme="dark",
            show_performance_overlay=True,
            performance_overlay_position="bottom_right",
            compact_mode=False,
            animations_enabled=True
        )
        
        return profile
    
    @staticmethod
    def create_productivity_profile(name: str = "Productivity Mode") -> Profile:
        """Create productivity-optimized profile."""
        profile = Profile()
        profile.metadata.name = name
        profile.metadata.description = "Optimized for general computing and productivity tasks"
        profile.metadata.gaming_mode = GamingMode.PRODUCTIVITY
        profile.metadata.tags = ["productivity", "general", "comfort", "efficiency"]
        
        # DPI settings - comfortable
        profile.settings.dpi = DPISettings(
            enabled=True,
            mode="native",
            dpi_value=800,
            sensitivity_multiplier=1.0,
            acceleration_enabled=True,
            smoothing_enabled=True,
            smoothing_algorithm="gaussian",
            smoothing_factor=0.3,
            precision_mode=False
        )
        
        # Polling settings - power saving
        profile.settings.polling = PollingSettings(
            mouse_polling_rate=500,
            keyboard_polling_rate=500,
            mode="power_saving",
            adaptive_threshold=0.4,
            gaming_boost=False,
            real_time_priority=False,
            thread_priority=0
        )
        
        # Keyboard settings - standard
        profile.settings.keyboard = KeyboardSettings(
            nkro_enabled=False,
            rapid_trigger_enabled=False,
            debounce_enabled=True,
            debounce_delay=15.0,
            anti_ghosting_enabled=False,
            adaptive_response_enabled=False
        )
        
        # Smoothing settings - comfortable
        profile.settings.smoothing = SmoothingSettings(
            enabled=True,
            algorithm="gaussian",
            factor=0.3,
            window_size=9,
            performance_mode=False
        )
        
        # Macro settings - basic
        profile.settings.macro = MacroSettings(
            enabled=True,
            default_library="productivity_macros",
            auto_save=True,
            auto_save_interval=60.0,
            max_macros_per_library=25,
            playback_speed=1.0,
            loop_enabled=False,
            hotkey_enabled=True
        )
        
        # Performance settings - minimal
        profile.settings.performance = PerformanceSettings(
            monitoring_enabled=False,
            cpu_monitoring=False,
            memory_monitoring=False,
            input_monitoring=False,
            update_interval=5.0,
            log_performance=False,
            optimization_level=0,
            memory_limit_mb=200.0,
            cpu_limit_percent=50.0
        )
        
        # GUI settings - clean
        profile.settings.gui = GUISettings(
            theme="light",
            show_performance_overlay=False,
            compact_mode=True,
            animations_enabled=False
        )
        
        return profile
    
    @staticmethod
    def create_custom_profile(name: str = "Custom Mode") -> Profile:
        """Create custom profile with default settings."""
        profile = Profile()
        profile.metadata.name = name
        profile.metadata.description = "Custom user-defined settings"
        profile.metadata.gaming_mode = GamingMode.CUSTOM
        profile.metadata.tags = ["custom", "user-defined"]
        
        # All settings use defaults from Profile class
        # User can customize as needed
        
        return profile
    
    @staticmethod
    def get_all_presets() -> Dict[str, Profile]:
        """Get all available presets."""
        return {
            "FPS Mode": GamingModePresets.create_fps_profile(),
            "MOBA Mode": GamingModePresets.create_moba_profile(),
            "RTS Mode": GamingModePresets.create_rts_profile(),
            "MMO Mode": GamingModePresets.create_mmo_profile(),
            "Productivity Mode": GamingModePresets.create_productivity_profile(),
            "Custom Mode": GamingModePresets.create_custom_profile()
        }
    
    @staticmethod
    def get_preset_by_mode(gaming_mode: GamingMode) -> Optional[Profile]:
        """Get preset profile by gaming mode."""
        presets = GamingModePresets.get_all_presets()
        for profile in presets.values():
            if profile.metadata.gaming_mode == gaming_mode:
                return profile
        return None


# Convenience classes for direct access
class FPSMode:
    """FPS gaming mode preset."""
    @staticmethod
    def create(name: str = "FPS Mode") -> Profile:
        return GamingModePresets.create_fps_profile(name)


class MOBAMode:
    """MOBA gaming mode preset."""
    @staticmethod
    def create(name: str = "MOBA Mode") -> Profile:
        return GamingModePresets.create_moba_profile(name)


class RTSMode:
    """RTS gaming mode preset."""
    @staticmethod
    def create(name: str = "RTS Mode") -> Profile:
        return GamingModePresets.create_rts_profile(name)


class MMMode:
    """MMO gaming mode preset."""
    @staticmethod
    def create(name: str = "MMO Mode") -> Profile:
        return GamingModePresets.create_mmo_profile(name)


class CustomMode:
    """Custom gaming mode preset."""
    @staticmethod
    def create(name: str = "Custom Mode") -> Profile:
        return GamingModePresets.create_custom_profile(name)


# Example usage and testing
if __name__ == "__main__":
    # Create all presets
    presets = GamingModePresets.get_all_presets()
    
    print("Available Gaming Mode Presets:")
    for name, profile in presets.items():
        print(f"- {name}: {profile.metadata.description}")
        print(f"  DPI: {profile.settings.dpi.dpi_value}")
        print(f"  Mouse Polling: {profile.settings.polling.mouse_polling_rate}Hz")
        print(f"  NKRO: {profile.settings.keyboard.nkro_enabled}")
        print(f"  Smoothing: {profile.settings.smoothing.enabled}")
        print()
    
    # Create specific preset
    fps_profile = GamingModePresets.create_fps_profile("My FPS Profile")
    print(f"Created FPS profile: {fps_profile.metadata.name}")
    print(f"DPI: {fps_profile.settings.dpi.dpi_value}")
    print(f"Mouse Polling: {fps_profile.settings.polling.mouse_polling_rate}Hz")
