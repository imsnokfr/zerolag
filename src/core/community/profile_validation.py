"""
Profile Validation System

This module provides validation and compatibility checking for community
profiles to ensure they work correctly across different systems.

Features:
- Profile data validation
- Compatibility checking
- Version migration
- Security validation
- Performance validation
"""

import json
import logging
import platform
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from ..profiles.profile import Profile, GamingMode

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation levels for profile checking."""
    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"

class CompatibilityIssue(Enum):
    """Types of compatibility issues."""
    OS_INCOMPATIBLE = "os_incompatible"
    VERSION_MISMATCH = "version_mismatch"
    MISSING_FEATURES = "missing_features"
    INVALID_DATA = "invalid_data"
    SECURITY_RISK = "security_risk"
    PERFORMANCE_ISSUE = "performance_issue"

@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    issue_type: CompatibilityIssue
    severity: str  # "low", "medium", "high", "critical"
    message: str
    field: Optional[str] = None
    suggested_fix: Optional[str] = None

@dataclass
class ProfileValidationResult:
    """Result of profile validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    warnings: List[ValidationIssue]
    compatibility_score: float  # 0.0 to 1.0
    recommended_actions: List[str]
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(issue.severity == "critical" for issue in self.issues)
    
    def has_high_issues(self) -> bool:
        """Check if there are any high severity issues."""
        return any(issue.severity == "high" for issue in self.issues)

class ProfileValidator:
    """Validates community profiles for compatibility and correctness."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_os = platform.system().lower()
        self.supported_os = {"windows", "linux", "darwin"}
    
    def validate_profile(self, profile_data: Dict[str, Any], 
                        validation_level: ValidationLevel = ValidationLevel.STANDARD) -> ProfileValidationResult:
        """
        Validate a community profile.
        
        Args:
            profile_data: The profile data to validate
            validation_level: The level of validation to perform
            
        Returns:
            ProfileValidationResult with validation results
        """
        issues = []
        warnings = []
        recommended_actions = []
        
        try:
            # Basic structure validation
            self._validate_structure(profile_data, issues, warnings)
            
            # Data type validation
            self._validate_data_types(profile_data, issues, warnings)
            
            # Value range validation
            self._validate_value_ranges(profile_data, issues, warnings)
            
            # Compatibility validation
            self._validate_compatibility(profile_data, issues, warnings)
            
            # Security validation
            if validation_level in [ValidationLevel.STANDARD, ValidationLevel.STRICT]:
                self._validate_security(profile_data, issues, warnings)
            
            # Performance validation
            if validation_level == ValidationLevel.STRICT:
                self._validate_performance(profile_data, issues, warnings)
            
            # Generate recommendations
            recommended_actions = self._generate_recommendations(issues, warnings)
            
            # Calculate compatibility score
            compatibility_score = self._calculate_compatibility_score(issues, warnings)
            
            # Determine if profile is valid
            is_valid = not any(issue.severity in ["critical", "high"] for issue in issues)
            
            return ProfileValidationResult(
                is_valid=is_valid,
                issues=issues,
                warnings=warnings,
                compatibility_score=compatibility_score,
                recommended_actions=recommended_actions
            )
            
        except Exception as e:
            self.logger.error(f"Error validating profile: {e}")
            return ProfileValidationResult(
                is_valid=False,
                issues=[ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="critical",
                    message=f"Validation failed: {str(e)}"
                )],
                warnings=[],
                compatibility_score=0.0,
                recommended_actions=["Fix validation errors before using this profile"]
            )
    
    def _validate_structure(self, profile_data: Dict[str, Any], 
                          issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Validate the basic structure of the profile."""
        required_fields = [
            "profile_id", "name", "description", "author", "author_id",
            "category", "difficulty", "tags", "profile_data", "created_at", "updated_at"
        ]
        
        for field in required_fields:
            if field not in profile_data:
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="critical",
                    message=f"Missing required field: {field}",
                    field=field,
                    suggested_fix=f"Add the missing {field} field"
                ))
        
        # Validate profile_data structure
        if "profile_data" in profile_data:
            profile_data_content = profile_data["profile_data"]
            if not isinstance(profile_data_content, dict):
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="critical",
                    message="profile_data must be a dictionary",
                    field="profile_data",
                    suggested_fix="Ensure profile_data is a valid dictionary"
                ))
            else:
                self._validate_profile_data_structure(profile_data_content, issues, warnings)
    
    def _validate_profile_data_structure(self, profile_data: Dict[str, Any], 
                                       issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Validate the structure of the actual profile data."""
        required_profile_fields = ["name", "settings"]
        
        for field in required_profile_fields:
            if field not in profile_data:
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="critical",
                    message=f"Missing required profile field: {field}",
                    field=f"profile_data.{field}",
                    suggested_fix=f"Add the missing {field} field to profile data"
                ))
        
        # Validate settings structure
        if "settings" in profile_data:
            settings = profile_data["settings"]
            if not isinstance(settings, dict):
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="critical",
                    message="settings must be a dictionary",
                    field="profile_data.settings",
                    suggested_fix="Ensure settings is a valid dictionary"
                ))
            else:
                self._validate_settings_structure(settings, issues, warnings)
    
    def _validate_settings_structure(self, settings: Dict[str, Any], 
                                   issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Validate the settings structure."""
        required_settings = ["dpi", "polling", "keyboard", "smoothing", "macro", "performance", "gui", "hotkeys"]
        
        for setting in required_settings:
            if setting not in settings:
                warnings.append(ValidationIssue(
                    issue_type=CompatibilityIssue.MISSING_FEATURES,
                    severity="low",
                    message=f"Missing settings section: {setting}",
                    field=f"profile_data.settings.{setting}",
                    suggested_fix=f"Add {setting} settings section"
                ))
    
    def _validate_data_types(self, profile_data: Dict[str, Any], 
                           issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Validate data types of profile fields."""
        # Validate string fields
        string_fields = ["profile_id", "name", "description", "author", "author_id"]
        for field in string_fields:
            if field in profile_data and not isinstance(profile_data[field], str):
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="high",
                    message=f"{field} must be a string",
                    field=field,
                    suggested_fix=f"Convert {field} to a string"
                ))
        
        # Validate numeric fields
        numeric_fields = ["created_at", "updated_at", "downloads", "rating", "rating_count"]
        for field in numeric_fields:
            if field in profile_data and not isinstance(profile_data[field], (int, float)):
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="high",
                    message=f"{field} must be a number",
                    field=field,
                    suggested_fix=f"Convert {field} to a number"
                ))
        
        # Validate list fields
        list_fields = ["tags", "compatibility"]
        for field in list_fields:
            if field in profile_data and not isinstance(profile_data[field], list):
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="medium",
                    message=f"{field} must be a list",
                    field=field,
                    suggested_fix=f"Convert {field} to a list"
                ))
    
    def _validate_value_ranges(self, profile_data: Dict[str, Any], 
                             issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Validate value ranges for numeric fields."""
        # Validate rating range
        if "rating" in profile_data:
            rating = profile_data["rating"]
            if not (0.0 <= rating <= 5.0):
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="high",
                    message="Rating must be between 0.0 and 5.0",
                    field="rating",
                    suggested_fix="Set rating to a value between 0.0 and 5.0"
                ))
        
        # Validate download count
        if "downloads" in profile_data:
            downloads = profile_data["downloads"]
            if downloads < 0:
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="medium",
                    message="Download count cannot be negative",
                    field="downloads",
                    suggested_fix="Set downloads to a non-negative number"
                ))
        
        # Validate timestamps
        current_time = time.time()
        for field in ["created_at", "updated_at"]:
            if field in profile_data:
                timestamp = profile_data[field]
                if timestamp < 0 or timestamp > current_time + 86400:  # Allow 1 day in future
                    issues.append(ValidationIssue(
                        issue_type=CompatibilityIssue.INVALID_DATA,
                        severity="medium",
                        message=f"{field} must be a valid timestamp",
                        field=field,
                        suggested_fix=f"Set {field} to a valid Unix timestamp"
                    ))
    
    def _validate_compatibility(self, profile_data: Dict[str, Any], 
                              issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Validate OS and feature compatibility."""
        # Check OS compatibility
        if "compatibility" in profile_data:
            compatibility = profile_data["compatibility"]
            if not isinstance(compatibility, list):
                issues.append(ValidationIssue(
                    issue_type=CompatibilityIssue.INVALID_DATA,
                    severity="high",
                    message="compatibility must be a list",
                    field="compatibility",
                    suggested_fix="Convert compatibility to a list of supported OS names"
                ))
            else:
                if self.current_os not in compatibility:
                    warnings.append(ValidationIssue(
                        issue_type=CompatibilityIssue.OS_INCOMPATIBLE,
                        severity="medium",
                        message=f"Profile may not be compatible with {self.current_os}",
                        field="compatibility",
                        suggested_fix=f"Add {self.current_os} to compatibility list"
                    ))
        
        # Check for unsupported features
        if "profile_data" in profile_data and "settings" in profile_data["profile_data"]:
            settings = profile_data["profile_data"]["settings"]
            self._check_feature_compatibility(settings, issues, warnings)
    
    def _check_feature_compatibility(self, settings: Dict[str, Any], 
                                   issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Check compatibility of specific features."""
        # Check DPI settings
        if "dpi" in settings:
            dpi_settings = settings["dpi"]
            if "current_dpi" in dpi_settings:
                dpi = dpi_settings["current_dpi"]
                if not (400 <= dpi <= 26000):
                    warnings.append(ValidationIssue(
                        issue_type=CompatibilityIssue.PERFORMANCE_ISSUE,
                        severity="low",
                        message=f"DPI value {dpi} may cause performance issues",
                        field="profile_data.settings.dpi.current_dpi",
                        suggested_fix="Use DPI values between 400 and 26000"
                    ))
        
        # Check polling rate settings
        if "polling" in settings:
            polling_settings = settings["polling"]
            if "rate" in polling_settings:
                rate = polling_settings["rate"]
                if rate > 8000:
                    warnings.append(ValidationIssue(
                        issue_type=CompatibilityIssue.PERFORMANCE_ISSUE,
                        severity="low",
                        message=f"Polling rate {rate} may cause performance issues",
                        field="profile_data.settings.polling.rate",
                        suggested_fix="Use polling rates up to 8000Hz"
                    ))
    
    def _validate_security(self, profile_data: Dict[str, Any], 
                         issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Validate security aspects of the profile."""
        # Check for potentially dangerous values
        if "profile_data" in profile_data and "settings" in profile_data["profile_data"]:
            settings = profile_data["profile_data"]["settings"]
            
            # Check macro settings for suspicious content
            if "macro" in settings:
                macro_settings = settings["macro"]
                if "enabled" in macro_settings and macro_settings["enabled"]:
                    warnings.append(ValidationIssue(
                        issue_type=CompatibilityIssue.SECURITY_RISK,
                        severity="medium",
                        message="Profile contains macros which may pose security risks",
                        field="profile_data.settings.macro",
                        suggested_fix="Review macro content before using"
                    ))
    
    def _validate_performance(self, profile_data: Dict[str, Any], 
                            issues: List[ValidationIssue], warnings: List[ValidationIssue]):
        """Validate performance aspects of the profile."""
        if "profile_data" in profile_data and "settings" in profile_data["profile_data"]:
            settings = profile_data["profile_data"]["settings"]
            
            # Check for high resource usage settings
            if "performance" in settings:
                perf_settings = settings["performance"]
                if "max_cpu_usage" in perf_settings and perf_settings["max_cpu_usage"] > 5.0:
                    warnings.append(ValidationIssue(
                        issue_type=CompatibilityIssue.PERFORMANCE_ISSUE,
                        severity="low",
                        message="Profile may use high CPU resources",
                        field="profile_data.settings.performance.max_cpu_usage",
                        suggested_fix="Consider reducing CPU usage limit"
                    ))
    
    def _generate_recommendations(self, issues: List[ValidationIssue], 
                                warnings: List[ValidationIssue]) -> List[str]:
        """Generate recommended actions based on validation results."""
        recommendations = []
        
        # Critical issues
        critical_issues = [i for i in issues if i.severity == "critical"]
        if critical_issues:
            recommendations.append("Fix critical issues before using this profile")
        
        # High severity issues
        high_issues = [i for i in issues if i.severity == "high"]
        if high_issues:
            recommendations.append("Address high severity issues for better compatibility")
        
        # OS compatibility
        os_issues = [i for i in warnings if i.issue_type == CompatibilityIssue.OS_INCOMPATIBLE]
        if os_issues:
            recommendations.append("Verify OS compatibility before using this profile")
        
        # Performance issues
        perf_issues = [i for i in warnings if i.issue_type == CompatibilityIssue.PERFORMANCE_ISSUE]
        if perf_issues:
            recommendations.append("Monitor system performance when using this profile")
        
        return recommendations
    
    def _calculate_compatibility_score(self, issues: List[ValidationIssue], 
                                     warnings: List[ValidationIssue]) -> float:
        """Calculate a compatibility score from 0.0 to 1.0."""
        total_issues = len(issues) + len(warnings)
        if total_issues == 0:
            return 1.0
        
        # Weight issues by severity
        weighted_score = 0.0
        for issue in issues:
            if issue.severity == "critical":
                weighted_score += 4
            elif issue.severity == "high":
                weighted_score += 3
            elif issue.severity == "medium":
                weighted_score += 2
            else:
                weighted_score += 1
        
        for warning in warnings:
            if warning.severity == "high":
                weighted_score += 2
            elif warning.severity == "medium":
                weighted_score += 1
            else:
                weighted_score += 0.5
        
        # Calculate score (lower is better)
        max_possible_score = total_issues * 4  # Assume all critical
        if max_possible_score == 0:
            return 1.0
        
        score = 1.0 - (weighted_score / max_possible_score)
        return max(0.0, min(1.0, score))

class CompatibilityChecker:
    """Checks compatibility between profiles and current system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_os = platform.system().lower()
        self.supported_features = self._detect_supported_features()
    
    def check_compatibility(self, profile: 'CommunityProfile') -> Dict[str, Any]:
        """Check compatibility of a profile with the current system."""
        compatibility_info = {
            "is_compatible": True,
            "compatibility_score": 1.0,
            "issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Check OS compatibility
            if self.current_os not in profile.compatibility:
                compatibility_info["is_compatible"] = False
                compatibility_info["issues"].append(f"Profile not compatible with {self.current_os}")
                compatibility_info["compatibility_score"] *= 0.5
            
            # Check feature compatibility
            feature_issues = self._check_feature_compatibility(profile)
            compatibility_info["warnings"].extend(feature_issues)
            
            # Check requirements
            req_issues = self._check_requirements(profile)
            compatibility_info["warnings"].extend(req_issues)
            
            # Generate recommendations
            compatibility_info["recommendations"] = self._generate_compatibility_recommendations(
                compatibility_info["issues"], compatibility_info["warnings"]
            )
            
        except Exception as e:
            self.logger.error(f"Error checking compatibility: {e}")
            compatibility_info["is_compatible"] = False
            compatibility_info["issues"].append(f"Compatibility check failed: {str(e)}")
        
        return compatibility_info
    
    def _detect_supported_features(self) -> Set[str]:
        """Detect features supported by the current system."""
        features = {"basic_input", "dpi_emulation", "polling_rate"}
        
        # Add OS-specific features
        if self.current_os == "windows":
            features.update({"high_frequency_polling", "raw_input", "system_tray"})
        elif self.current_os == "linux":
            features.update({"evdev", "libinput"})
        elif self.current_os == "darwin":
            features.update({"quartz_events"})
        
        return features
    
    def _check_feature_compatibility(self, profile: 'CommunityProfile') -> List[str]:
        """Check if profile uses features supported by current system."""
        warnings = []
        
        # Check profile requirements
        if "requirements" in profile.requirements:
            required_features = profile.requirements.get("features", [])
            for feature in required_features:
                if feature not in self.supported_features:
                    warnings.append(f"Feature '{feature}' not supported on current system")
        
        return warnings
    
    def _check_requirements(self, profile: 'CommunityProfile') -> List[str]:
        """Check if profile requirements are met."""
        warnings = []
        
        # Check system requirements
        if "system" in profile.requirements:
            sys_req = profile.requirements["system"]
            
            # Check minimum OS version
            if "min_os_version" in sys_req:
                # This would need platform-specific implementation
                pass
            
            # Check required hardware
            if "min_ram" in sys_req:
                # This would need system memory detection
                pass
        
        return warnings
    
    def _generate_compatibility_recommendations(self, issues: List[str], warnings: List[str]) -> List[str]:
        """Generate recommendations based on compatibility issues."""
        recommendations = []
        
        if issues:
            recommendations.append("This profile may not work correctly on your system")
        
        if warnings:
            recommendations.append("Some features may not be available or may work differently")
        
        if not issues and not warnings:
            recommendations.append("Profile should work well on your system")
        
        return recommendations
