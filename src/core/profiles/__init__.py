"""
Profile Management System for ZeroLag

This module provides comprehensive profile management functionality for
saving and loading user configurations, gaming mode presets, and settings.

Components:
- Profile: Core profile data structure
- ProfileManager: Centralized profile management
- GamingModePresets: Predefined gaming configurations
- ProfileValidator: Profile validation and compatibility checking
- ProfileExporter: Import/export functionality

Features:
- Complete settings storage and management
- Gaming mode presets (FPS, MOBA, RTS, MMO)
- Profile switching with real-time application
- Import/export capabilities
- Profile validation and error handling
- GUI integration
- Performance optimization
"""

from .profile import (
    Profile,
    ProfileSettings,
    DPISettings,
    PollingSettings,
    KeyboardSettings,
    SmoothingSettings,
    MacroSettings,
    PerformanceSettings,
    GUISettings,
    HotkeySettings,
    GamingMode,
    ProfileMetadata
)
from .profile_manager import (
    ProfileManager,
    ProfileManagerConfig,
    ProfileManagerStats
)
from .gaming_presets import (
    GamingModePresets,
    FPSMode,
    MOBAMode,
    RTSMode,
    MMMode,
    CustomMode
)
from .profile_validator import (
    ProfileValidator,
    ValidationResult,
    ValidationError
)
from .profile_exporter import (
    ProfileExporter,
    ExportFormat,
    ImportResult
)

__all__ = [
    # Core profile components
    'Profile',
    'ProfileSettings',
    'DPISettings',
    'PollingSettings',
    'KeyboardSettings',
    'SmoothingSettings',
    'MacroSettings',
    'PerformanceSettings',
    'GUISettings',
    'HotkeySettings',
    'GamingMode',
    'ProfileMetadata',
    
    # Profile management
    'ProfileManager',
    'ProfileManagerConfig',
    'ProfileManagerStats',
    
    # Gaming presets
    'GamingModePresets',
    'FPSMode',
    'MOBAMode',
    'RTSMode',
    'MMMode',
    'CustomMode',
    
    # Validation and export
    'ProfileValidator',
    'ValidationResult',
    'ValidationError',
    'ProfileExporter',
    'ExportFormat',
    'ImportResult'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Comprehensive profile management system for ZeroLag gaming input optimization"
