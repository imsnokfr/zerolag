"""
Hotkey System for ZeroLag

This package provides comprehensive hotkey functionality for ZeroLag,
including global hotkey detection, profile switching, DPI adjustments,
and emergency controls.

Features:
- Global hotkey detection using Windows API
- Thread-safe hotkey processing
- Hotkey conflict detection and resolution
- Profile switching and DPI adjustment hotkeys
- Emergency hotkeys for critical functions
- Customizable hotkey configurations
- System-wide hotkey hooks

Components:
- HotkeyManager: Core hotkey management system
- HotkeyDetector: Windows API hotkey detection
- HotkeyActions: Action handlers for hotkey events
- HotkeyConfig: Configuration management for hotkeys
- HotkeyValidator: Hotkey conflict detection and validation
"""

from .hotkey_manager import (
    HotkeyManager,
    HotkeyManagerConfig,
    HotkeyManagerStats,
    HotkeyManagerState
)
from .hotkey_detector import (
    HotkeyDetector,
    HotkeyEvent,
    HotkeyModifier
)
from .hotkey_actions import (
    HotkeyActions,
    HotkeyActionType,
    ActionContext,
    ActionResult
)
from .hotkey_config import (
    HotkeyConfig,
    HotkeyConfigManager,
    HotkeyBinding,
    HotkeyProfile,
    HotkeyProfileType
)
from .hotkey_validator import (
    HotkeyValidator,
    ValidationResult,
    ValidationError,
    ConflictResolution,
    ConflictInfo
)
from .profile_hotkeys import (
    ProfileHotkeyManager,
    ProfileHotkeyConfig,
    ProfileSwitchFeedback
)
from .profile_feedback import (
    ProfileFeedbackManager,
    FeedbackConfig,
    FeedbackStyle,
    ProfileSwitchNotification,
    ConsoleFeedback,
    get_feedback_manager,
    setup_profile_feedback,
    show_profile_feedback
)
from .emergency_hotkeys import (
    EmergencyHotkeyManager,
    EmergencyConfig,
    EmergencyEvent,
    EmergencyStats,
    EmergencyLevel,
    EmergencyState
)
from .emergency_integration import (
    EmergencyIntegration,
    EmergencyIntegrationConfig
)
from .hotkey_config_gui import (
    HotkeyConfigGUI,
    HotkeyBindingWidget,
    KeyCaptureDialog
)
from .hotkey_presets import (
    HotkeyPresetManager,
    HotkeyPreset,
    GamingGenre,
    PresetComplexity
)

__all__ = [
    # Core hotkey system
    'HotkeyManager',
    'HotkeyManagerConfig', 
    'HotkeyManagerStats',
    'HotkeyManagerState',
    
    # Hotkey detection
    'HotkeyDetector',
    'HotkeyEvent',
    'HotkeyModifier',
    
    # Hotkey actions
    'HotkeyActions',
    'HotkeyActionType',
    'ActionContext',
    'ActionResult',
    
    # Configuration
    'HotkeyConfig',
    'HotkeyConfigManager',
    'HotkeyBinding',
    'HotkeyProfile',
    'HotkeyProfileType',
    
    # Validation
    'HotkeyValidator',
    'ValidationResult',
    'ValidationError',
    'ConflictResolution',
    'ConflictInfo',
    
    # Profile hotkeys
    'ProfileHotkeyManager',
    'ProfileHotkeyConfig',
    'ProfileSwitchFeedback',
    
    # Profile feedback
    'ProfileFeedbackManager',
    'FeedbackConfig',
    'FeedbackStyle',
    'ProfileSwitchNotification',
    'ConsoleFeedback',
    'get_feedback_manager',
    'setup_profile_feedback',
    'show_profile_feedback',
    
    # DPI hotkeys
    'DPIHotkeyManager',
    'DPIHotkeyConfig',
    'DPIStepSize',
    'DPIPreset',
    'DPIStepConfig',
    'DPILimits',
    'DPIFeedback',
    
    # DPI feedback
    'DPIFeedbackManager',
    'DPIFeedbackConfig',
    'FeedbackDisplayMode',
    'FeedbackStyle',
    'DPIFeedbackDisplay',
    
    # Emergency hotkeys
    'EmergencyHotkeyManager',
    'EmergencyConfig',
    'EmergencyEvent',
    'EmergencyStats',
    'EmergencyLevel',
    'EmergencyState',
    
    # Emergency integration
    'EmergencyIntegration',
    'EmergencyIntegrationConfig',
    
    # GUI components
    'HotkeyConfigGUI',
    'HotkeyBindingWidget',
    'KeyCaptureDialog',
    
    # Presets
    'HotkeyPresetManager',
    'HotkeyPreset',
    'GamingGenre',
    'PresetComplexity'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Comprehensive hotkey system for ZeroLag gaming input optimization"
