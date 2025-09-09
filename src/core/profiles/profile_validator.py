"""
Profile Validator for ZeroLag

This module provides comprehensive profile validation and compatibility
checking functionality for the ZeroLag profile management system.

Features:
- Profile data validation
- Compatibility checking
- Error reporting and suggestions
- Version migration support
- Performance validation
- Security validation
"""

from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import re
import json
from pathlib import Path

from .profile import (
    Profile, GamingMode, ProfileMetadata, ProfileSettings,
    DPISettings, PollingSettings, KeyboardSettings, SmoothingSettings,
    MacroSettings, PerformanceSettings, GUISettings, HotkeySettings
)


class ValidationErrorType(Enum):
    """Types of validation errors."""
    MISSING_FIELD = "missing_field"
    INVALID_VALUE = "invalid_value"
    OUT_OF_RANGE = "out_of_range"
    INVALID_FORMAT = "invalid_format"
    COMPATIBILITY_ISSUE = "compatibility_issue"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    CORRUPTED_DATA = "corrupted_data"


@dataclass
class ValidationError:
    """Individual validation error."""
    error_type: ValidationErrorType
    field_path: str
    message: str
    current_value: Any = None
    expected_value: Any = None
    severity: str = "error"  # error, warning, info
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result."""
    is_valid: bool
    errors: List[ValidationError] = None
    warnings: List[ValidationError] = None
    info: List[ValidationError] = None
    compatibility_score: float = 1.0
    performance_score: float = 1.0
    security_score: float = 1.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.info is None:
            self.info = []
    
    def add_error(self, error: ValidationError):
        """Add an error to the result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: ValidationError):
        """Add a warning to the result."""
        self.warnings.append(warning)
    
    def add_info(self, info: ValidationError):
        """Add an info message to the result."""
        self.info.append(info)
    
    def get_all_issues(self) -> List[ValidationError]:
        """Get all issues (errors, warnings, info) combined."""
        return self.errors + self.warnings + self.info
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "is_valid": self.is_valid,
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "total_info": len(self.info),
            "compatibility_score": self.compatibility_score,
            "performance_score": self.performance_score,
            "security_score": self.security_score
        }


class ProfileValidator:
    """
    Comprehensive profile validator for ZeroLag.
    
    Validates profile data, checks compatibility, and provides
    suggestions for improvement.
    """
    
    def __init__(self):
        """Initialize profile validator."""
        self.current_version = "1.0.0"
        self.minimum_compatible_version = "1.0.0"
        self.maximum_compatible_version = "2.0.0"
        
        # Validation rules
        self.validation_rules = self._initialize_validation_rules()
    
    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation rules for different fields."""
        return {
            "metadata.name": {
                "required": True,
                "type": str,
                "min_length": 1,
                "max_length": 100,
                "pattern": r"^[a-zA-Z0-9\s\-_]+$",
                "message": "Profile name must contain only letters, numbers, spaces, hyphens, and underscores"
            },
            "metadata.description": {
                "required": False,
                "type": str,
                "max_length": 500,
                "message": "Description must be less than 500 characters"
            },
            "metadata.version": {
                "required": True,
                "type": str,
                "pattern": r"^\d+\.\d+\.\d+$",
                "message": "Version must be in format X.Y.Z"
            },
            "settings.dpi.dpi_value": {
                "required": True,
                "type": int,
                "min_value": 100,
                "max_value": 16000,
                "message": "DPI value must be between 100 and 16000"
            },
            "settings.dpi.sensitivity_multiplier": {
                "required": True,
                "type": float,
                "min_value": 0.1,
                "max_value": 10.0,
                "message": "Sensitivity multiplier must be between 0.1 and 10.0"
            },
            "settings.polling.mouse_polling_rate": {
                "required": True,
                "type": int,
                "min_value": 125,
                "max_value": 8000,
                "message": "Mouse polling rate must be between 125 and 8000 Hz"
            },
            "settings.polling.keyboard_polling_rate": {
                "required": True,
                "type": int,
                "min_value": 125,
                "max_value": 1000,
                "message": "Keyboard polling rate must be between 125 and 1000 Hz"
            },
            "settings.keyboard.nkro_limit": {
                "required": True,
                "type": int,
                "min_value": 1,
                "max_value": 20,
                "message": "NKRO limit must be between 1 and 20"
            },
            "settings.keyboard.debounce_delay": {
                "required": True,
                "type": float,
                "min_value": 0.0,
                "max_value": 100.0,
                "message": "Debounce delay must be between 0.0 and 100.0 ms"
            },
            "settings.smoothing.factor": {
                "required": True,
                "type": float,
                "min_value": 0.0,
                "max_value": 1.0,
                "message": "Smoothing factor must be between 0.0 and 1.0"
            },
            "settings.performance.memory_limit_mb": {
                "required": True,
                "type": float,
                "min_value": 10.0,
                "max_value": 1000.0,
                "message": "Memory limit must be between 10.0 and 1000.0 MB"
            },
            "settings.performance.cpu_limit_percent": {
                "required": True,
                "type": float,
                "min_value": 10.0,
                "max_value": 100.0,
                "message": "CPU limit must be between 10.0 and 100.0 percent"
            }
        }
    
    def validate_profile(self, profile: Profile) -> ValidationResult:
        """
        Validate a complete profile.
        
        Args:
            profile: Profile to validate
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(is_valid=True)
        
        try:
            # Validate metadata
            self._validate_metadata(profile.metadata, result)
            
            # Validate settings
            self._validate_settings(profile.settings, result)
            
            # Check compatibility
            self._validate_compatibility(profile, result)
            
            # Check performance implications
            self._validate_performance(profile, result)
            
            # Check security
            self._validate_security(profile, result)
            
            # Calculate scores
            self._calculate_scores(result)
            
        except Exception as e:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.CORRUPTED_DATA,
                field_path="profile",
                message=f"Profile validation failed: {str(e)}",
                severity="error"
            ))
        
        return result
    
    def validate_profile_file(self, file_path: Union[str, Path]) -> ValidationResult:
        """
        Validate a profile file.
        
        Args:
            file_path: Path to profile file
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(is_valid=True)
        
        try:
            # Check if file exists
            file_path = Path(file_path)
            if not file_path.exists():
                result.add_error(ValidationError(
                    error_type=ValidationErrorType.MISSING_FIELD,
                    field_path="file",
                    message="Profile file does not exist",
                    severity="error"
                ))
                return result
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size == 0:
                result.add_error(ValidationError(
                    error_type=ValidationErrorType.CORRUPTED_DATA,
                    field_path="file",
                    message="Profile file is empty",
                    severity="error"
                ))
                return result
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                result.add_warning(ValidationError(
                    error_type=ValidationErrorType.PERFORMANCE_ISSUE,
                    field_path="file",
                    message="Profile file is very large (>10MB)",
                    current_value=file_size,
                    suggestion="Consider optimizing the profile data"
                ))
            
            # Try to load profile
            profile = Profile.load_from_file(file_path)
            if profile is None:
                result.add_error(ValidationError(
                    error_type=ValidationErrorType.CORRUPTED_DATA,
                    field_path="file",
                    message="Failed to load profile from file",
                    severity="error"
                ))
                return result
            
            # Validate loaded profile
            profile_result = self.validate_profile(profile)
            result.errors.extend(profile_result.errors)
            result.warnings.extend(profile_result.warnings)
            result.info.extend(profile_result.info)
            result.is_valid = profile_result.is_valid
            result.compatibility_score = profile_result.compatibility_score
            result.performance_score = profile_result.performance_score
            result.security_score = profile_result.security_score
            
        except Exception as e:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.CORRUPTED_DATA,
                field_path="file",
                message=f"File validation failed: {str(e)}",
                severity="error"
            ))
        
        return result
    
    def _validate_metadata(self, metadata: ProfileMetadata, result: ValidationResult):
        """Validate profile metadata."""
        # Validate name
        self._validate_field(
            metadata.name, "metadata.name", result,
            required=True, type_check=str, min_length=1, max_length=100,
            pattern=r"^[a-zA-Z0-9\s\-_]+$"
        )
        
        # Validate description
        if metadata.description:
            self._validate_field(
                metadata.description, "metadata.description", result,
                type_check=str, max_length=500
            )
        
        # Validate version
        self._validate_field(
            metadata.version, "metadata.version", result,
            required=True, type_check=str, pattern=r"^\d+\.\d+\.\d+$"
        )
        
        # Validate gaming mode
        if not isinstance(metadata.gaming_mode, GamingMode):
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="metadata.gaming_mode",
                message="Invalid gaming mode",
                current_value=metadata.gaming_mode,
                expected_value="Valid GamingMode enum value"
            ))
        
        # Validate timestamps
        if metadata.created_at <= 0:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="metadata.created_at",
                message="Invalid creation timestamp",
                current_value=metadata.created_at
            ))
        
        if metadata.modified_at <= 0:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="metadata.modified_at",
                message="Invalid modification timestamp",
                current_value=metadata.modified_at
            ))
        
        if metadata.modified_at < metadata.created_at:
            result.add_warning(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="metadata.modified_at",
                message="Modification time is before creation time",
                current_value=metadata.modified_at,
                expected_value=f"> {metadata.created_at}"
            ))
    
    def _validate_settings(self, settings: ProfileSettings, result: ValidationResult):
        """Validate profile settings."""
        # Validate DPI settings
        self._validate_dpi_settings(settings.dpi, result)
        
        # Validate polling settings
        self._validate_polling_settings(settings.polling, result)
        
        # Validate keyboard settings
        self._validate_keyboard_settings(settings.keyboard, result)
        
        # Validate smoothing settings
        self._validate_smoothing_settings(settings.smoothing, result)
        
        # Validate macro settings
        self._validate_macro_settings(settings.macro, result)
        
        # Validate performance settings
        self._validate_performance_settings(settings.performance, result)
        
        # Validate GUI settings
        self._validate_gui_settings(settings.gui, result)
        
        # Validate hotkey settings
        self._validate_hotkey_settings(settings.hotkeys, result)
    
    def _validate_dpi_settings(self, dpi: DPISettings, result: ValidationResult):
        """Validate DPI settings."""
        self._validate_field(
            dpi.dpi_value, "settings.dpi.dpi_value", result,
            required=True, type_check=int, min_value=100, max_value=16000
        )
        
        self._validate_field(
            dpi.sensitivity_multiplier, "settings.dpi.sensitivity_multiplier", result,
            required=True, type_check=float, min_value=0.1, max_value=10.0
        )
        
        if dpi.mode not in ["software", "hybrid", "native"]:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="settings.dpi.mode",
                message="Invalid DPI mode",
                current_value=dpi.mode,
                expected_value="software, hybrid, or native"
            ))
        
        if dpi.smoothing_algorithm not in ["low_pass", "ema", "kalman", "adaptive", "gaussian", "median"]:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="settings.dpi.smoothing_algorithm",
                message="Invalid smoothing algorithm",
                current_value=dpi.smoothing_algorithm,
                expected_value="low_pass, ema, kalman, adaptive, gaussian, or median"
            ))
    
    def _validate_polling_settings(self, polling: PollingSettings, result: ValidationResult):
        """Validate polling settings."""
        self._validate_field(
            polling.mouse_polling_rate, "settings.polling.mouse_polling_rate", result,
            required=True, type_check=int, min_value=125, max_value=8000
        )
        
        self._validate_field(
            polling.keyboard_polling_rate, "settings.polling.keyboard_polling_rate", result,
            required=True, type_check=int, min_value=125, max_value=1000
        )
        
        if polling.mode not in ["fixed", "adaptive", "gaming", "power_saving"]:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="settings.polling.mode",
                message="Invalid polling mode",
                current_value=polling.mode,
                expected_value="fixed, adaptive, gaming, or power_saving"
            ))
        
        if polling.thread_priority < 0 or polling.thread_priority > 5:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.polling.thread_priority",
                message="Thread priority must be between 0 and 5",
                current_value=polling.thread_priority,
                expected_value="0-5"
            ))
    
    def _validate_keyboard_settings(self, keyboard: KeyboardSettings, result: ValidationResult):
        """Validate keyboard settings."""
        self._validate_field(
            keyboard.nkro_limit, "settings.keyboard.nkro_limit", result,
            required=True, type_check=int, min_value=1, max_value=20
        )
        
        self._validate_field(
            keyboard.debounce_delay, "settings.keyboard.debounce_delay", result,
            required=True, type_check=float, min_value=0.0, max_value=100.0
        )
        
        if keyboard.rapid_trigger_threshold < 0.0 or keyboard.rapid_trigger_threshold > 1.0:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.keyboard.rapid_trigger_threshold",
                message="Rapid trigger threshold must be between 0.0 and 1.0",
                current_value=keyboard.rapid_trigger_threshold,
                expected_value="0.0-1.0"
            ))
        
        if keyboard.turbo_rate <= 0.0 or keyboard.turbo_rate > 100.0:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.keyboard.turbo_rate",
                message="Turbo rate must be between 0.0 and 100.0 Hz",
                current_value=keyboard.turbo_rate,
                expected_value="0.0-100.0"
            ))
    
    def _validate_smoothing_settings(self, smoothing: SmoothingSettings, result: ValidationResult):
        """Validate smoothing settings."""
        self._validate_field(
            smoothing.factor, "settings.smoothing.factor", result,
            required=True, type_check=float, min_value=0.0, max_value=1.0
        )
        
        if smoothing.window_size < 1 or smoothing.window_size > 50:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.smoothing.window_size",
                message="Window size must be between 1 and 50",
                current_value=smoothing.window_size,
                expected_value="1-50"
            ))
        
        if smoothing.algorithm not in ["low_pass", "ema", "kalman", "adaptive", "gaussian", "median"]:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="settings.smoothing.algorithm",
                message="Invalid smoothing algorithm",
                current_value=smoothing.algorithm,
                expected_value="low_pass, ema, kalman, adaptive, gaussian, or median"
            ))
    
    def _validate_macro_settings(self, macro: MacroSettings, result: ValidationResult):
        """Validate macro settings."""
        if macro.max_macros_per_library < 1 or macro.max_macros_per_library > 1000:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.macro.max_macros_per_library",
                message="Max macros per library must be between 1 and 1000",
                current_value=macro.max_macros_per_library,
                expected_value="1-1000"
            ))
        
        if macro.max_events_per_macro < 1 or macro.max_events_per_macro > 100000:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.macro.max_events_per_macro",
                message="Max events per macro must be between 1 and 100000",
                current_value=macro.max_events_per_macro,
                expected_value="1-100000"
            ))
        
        if macro.playback_speed <= 0.0 or macro.playback_speed > 10.0:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.macro.playback_speed",
                message="Playback speed must be between 0.0 and 10.0",
                current_value=macro.playback_speed,
                expected_value="0.0-10.0"
            ))
    
    def _validate_performance_settings(self, performance: PerformanceSettings, result: ValidationResult):
        """Validate performance settings."""
        self._validate_field(
            performance.memory_limit_mb, "settings.performance.memory_limit_mb", result,
            required=True, type_check=float, min_value=10.0, max_value=1000.0
        )
        
        self._validate_field(
            performance.cpu_limit_percent, "settings.performance.cpu_limit_percent", result,
            required=True, type_check=float, min_value=10.0, max_value=100.0
        )
        
        if performance.update_interval <= 0.0 or performance.update_interval > 60.0:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.performance.update_interval",
                message="Update interval must be between 0.0 and 60.0 seconds",
                current_value=performance.update_interval,
                expected_value="0.0-60.0"
            ))
        
        if performance.optimization_level < 0 or performance.optimization_level > 3:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.performance.optimization_level",
                message="Optimization level must be between 0 and 3",
                current_value=performance.optimization_level,
                expected_value="0-3"
            ))
    
    def _validate_gui_settings(self, gui: GUISettings, result: ValidationResult):
        """Validate GUI settings."""
        if gui.theme not in ["dark", "light", "auto"]:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path="settings.gui.theme",
                message="Invalid theme",
                current_value=gui.theme,
                expected_value="dark, light, or auto"
            ))
        
        if gui.window_width < 400 or gui.window_width > 4000:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.gui.window_width",
                message="Window width must be between 400 and 4000 pixels",
                current_value=gui.window_width,
                expected_value="400-4000"
            ))
        
        if gui.window_height < 300 or gui.window_height > 3000:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.gui.window_height",
                message="Window height must be between 300 and 3000 pixels",
                current_value=gui.window_height,
                expected_value="300-3000"
            ))
        
        if gui.font_size < 8 or gui.font_size > 24:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path="settings.gui.font_size",
                message="Font size must be between 8 and 24",
                current_value=gui.font_size,
                expected_value="8-24"
            ))
    
    def _validate_hotkey_settings(self, hotkeys: HotkeySettings, result: ValidationResult):
        """Validate hotkey settings."""
        # Validate hotkey format (basic validation)
        hotkey_fields = [
            "profile_switch_hotkey", "macro_record_hotkey", "macro_play_hotkey",
            "dpi_cycle_hotkey", "polling_cycle_hotkey", "emergency_stop_hotkey"
        ]
        
        for field in hotkey_fields:
            hotkey = getattr(hotkeys, field)
            if hotkey and not self._is_valid_hotkey(hotkey):
                result.add_error(ValidationError(
                    error_type=ValidationErrorType.INVALID_FORMAT,
                    field_path=f"settings.hotkeys.{field}",
                    message="Invalid hotkey format",
                    current_value=hotkey,
                    expected_value="Format: ctrl+shift+key or similar"
                ))
    
    def _is_valid_hotkey(self, hotkey: str) -> bool:
        """Check if hotkey format is valid."""
        if not hotkey:
            return True
        
        # Basic hotkey validation
        pattern = r"^[a-zA-Z0-9\s\-\+]+$"
        return bool(re.match(pattern, hotkey))
    
    def _validate_field(self, value: Any, field_path: str, result: ValidationResult,
                       required: bool = False, type_check: type = None,
                       min_value: Any = None, max_value: Any = None,
                       min_length: int = None, max_length: int = None,
                       pattern: str = None, **kwargs):
        """Validate a single field."""
        # Check if required field is present
        if required and value is None:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.MISSING_FIELD,
                field_path=field_path,
                message=f"Required field is missing",
                severity="error"
            ))
            return
        
        if value is None:
            return
        
        # Type check
        if type_check and not isinstance(value, type_check):
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_VALUE,
                field_path=field_path,
                message=f"Expected {type_check.__name__}, got {type(value).__name__}",
                current_value=value,
                expected_value=type_check.__name__,
                severity="error"
            ))
            return
        
        # Range checks
        if min_value is not None and value < min_value:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path=field_path,
                message=f"Value must be >= {min_value}",
                current_value=value,
                expected_value=f">= {min_value}",
                severity="error"
            ))
        
        if max_value is not None and value > max_value:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path=field_path,
                message=f"Value must be <= {max_value}",
                current_value=value,
                expected_value=f"<= {max_value}",
                severity="error"
            ))
        
        # Length checks
        if min_length is not None and len(str(value)) < min_length:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path=field_path,
                message=f"Length must be >= {min_length}",
                current_value=len(str(value)),
                expected_value=f">= {min_length}",
                severity="error"
            ))
        
        if max_length is not None and len(str(value)) > max_length:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.OUT_OF_RANGE,
                field_path=field_path,
                message=f"Length must be <= {max_length}",
                current_value=len(str(value)),
                expected_value=f"<= {max_length}",
                severity="error"
            ))
        
        # Pattern check
        if pattern and not re.match(pattern, str(value)):
            result.add_error(ValidationError(
                error_type=ValidationErrorType.INVALID_FORMAT,
                field_path=field_path,
                message=f"Value does not match required pattern",
                current_value=value,
                expected_value=f"Pattern: {pattern}",
                severity="error"
            ))
    
    def _validate_compatibility(self, profile: Profile, result: ValidationResult):
        """Validate profile compatibility."""
        # Check version compatibility
        if profile.metadata.version < self.minimum_compatible_version:
            result.add_error(ValidationError(
                error_type=ValidationErrorType.COMPATIBILITY_ISSUE,
                field_path="metadata.version",
                message=f"Profile version {profile.metadata.version} is too old",
                current_value=profile.metadata.version,
                expected_value=f">= {self.minimum_compatible_version}",
                suggestion="Consider updating the profile or using a newer version of ZeroLag"
            ))
        
        if profile.metadata.version > self.maximum_compatible_version:
            result.add_warning(ValidationError(
                error_type=ValidationErrorType.COMPATIBILITY_ISSUE,
                field_path="metadata.version",
                message=f"Profile version {profile.metadata.version} is newer than supported",
                current_value=profile.metadata.version,
                expected_value=f"<= {self.maximum_compatible_version}",
                suggestion="Consider using a newer version of ZeroLag or downgrading the profile"
            ))
        
        # Calculate compatibility score
        if result.errors:
            result.compatibility_score = max(0.0, 1.0 - len(result.errors) * 0.1)
        else:
            result.compatibility_score = 1.0
    
    def _validate_performance(self, profile: Profile, result: ValidationResult):
        """Validate performance implications."""
        performance_issues = 0
        
        # Check for high resource usage
        if profile.settings.performance.memory_limit_mb > 500:
            result.add_warning(ValidationError(
                error_type=ValidationErrorType.PERFORMANCE_ISSUE,
                field_path="settings.performance.memory_limit_mb",
                message="High memory limit may impact system performance",
                current_value=profile.settings.performance.memory_limit_mb,
                suggestion="Consider reducing memory limit for better performance"
            ))
            performance_issues += 1
        
        if profile.settings.polling.mouse_polling_rate > 4000:
            result.add_warning(ValidationError(
                error_type=ValidationErrorType.PERFORMANCE_ISSUE,
                field_path="settings.polling.mouse_polling_rate",
                message="Very high mouse polling rate may impact CPU usage",
                current_value=profile.settings.polling.mouse_polling_rate,
                suggestion="Consider using a lower polling rate for better performance"
            ))
            performance_issues += 1
        
        if profile.settings.macro.max_events_per_macro > 50000:
            result.add_warning(ValidationError(
                error_type=ValidationErrorType.PERFORMANCE_ISSUE,
                field_path="settings.macro.max_events_per_macro",
                message="Very large macro may impact performance",
                current_value=profile.settings.macro.max_events_per_macro,
                suggestion="Consider splitting large macros into smaller ones"
            ))
            performance_issues += 1
        
        # Calculate performance score
        result.performance_score = max(0.0, 1.0 - performance_issues * 0.2)
    
    def _validate_security(self, profile: Profile, result: ValidationResult):
        """Validate security implications."""
        security_issues = 0
        
        # Check for potentially dangerous settings
        if profile.settings.performance.cpu_limit_percent > 95:
            result.add_warning(ValidationError(
                error_type=ValidationErrorType.SECURITY_ISSUE,
                field_path="settings.performance.cpu_limit_percent",
                message="Very high CPU limit may impact system stability",
                current_value=profile.settings.performance.cpu_limit_percent,
                suggestion="Consider using a lower CPU limit for system stability"
            ))
            security_issues += 1
        
        # Check for suspicious hotkey combinations
        dangerous_hotkeys = ["ctrl+alt+del", "alt+f4", "ctrl+shift+esc"]
        for hotkey in [profile.settings.hotkeys.profile_switch_hotkey,
                      profile.settings.hotkeys.macro_record_hotkey,
                      profile.settings.hotkeys.macro_play_hotkey]:
            if hotkey and any(dangerous in hotkey.lower() for dangerous in dangerous_hotkeys):
                result.add_warning(ValidationError(
                    error_type=ValidationErrorType.SECURITY_ISSUE,
                    field_path="settings.hotkeys",
                    message=f"Hotkey '{hotkey}' may conflict with system shortcuts",
                    current_value=hotkey,
                    suggestion="Consider using a different hotkey combination"
                ))
                security_issues += 1
        
        # Calculate security score
        result.security_score = max(0.0, 1.0 - security_issues * 0.3)
    
    def _calculate_scores(self, result: ValidationResult):
        """Calculate overall validation scores."""
        # Overall score is the minimum of all component scores
        if result.errors:
            result.is_valid = False
        
        # Update scores if not already calculated
        if result.compatibility_score == 1.0 and not any(
            e.error_type == ValidationErrorType.COMPATIBILITY_ISSUE for e in result.errors
        ):
            result.compatibility_score = 1.0
        
        if result.performance_score == 1.0 and not any(
            e.error_type == ValidationErrorType.PERFORMANCE_ISSUE for e in result.get_all_issues()
        ):
            result.performance_score = 1.0
        
        if result.security_score == 1.0 and not any(
            e.error_type == ValidationErrorType.SECURITY_ISSUE for e in result.get_all_issues()
        ):
            result.security_score = 1.0


# Example usage and testing
if __name__ == "__main__":
    # Create validator
    validator = ProfileValidator()
    
    # Create test profile
    from .profile import Profile, GamingMode
    profile = Profile()
    profile.metadata.name = "Test Profile"
    profile.metadata.gaming_mode = GamingMode.FPS
    
    # Validate profile
    result = validator.validate_profile(profile)
    
    print(f"Profile valid: {result.is_valid}")
    print(f"Errors: {len(result.errors)}")
    print(f"Warnings: {len(result.warnings)}")
    print(f"Compatibility score: {result.compatibility_score:.2f}")
    print(f"Performance score: {result.performance_score:.2f}")
    print(f"Security score: {result.security_score:.2f}")
    
    # Print errors
    for error in result.errors:
        print(f"Error: {error.field_path} - {error.message}")
    
    # Print warnings
    for warning in result.warnings:
        print(f"Warning: {warning.field_path} - {warning.message}")
