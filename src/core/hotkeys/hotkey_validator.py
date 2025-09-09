"""
Hotkey Validator for ZeroLag

This module provides validation functionality for hotkey combinations,
conflict detection, and hotkey binding validation.

Features:
- Hotkey combination validation
- Conflict detection and resolution
- Key combination compatibility checking
- Hotkey binding validation
- Reserved key detection
"""

import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field

from .hotkey_detector import HotkeyModifier
from .hotkey_actions import HotkeyActionType
from .hotkey_config import HotkeyBinding

logger = logging.getLogger(__name__)

class ValidationError(Enum):
    """Types of validation errors."""
    INVALID_MODIFIER = "invalid_modifier"
    INVALID_VIRTUAL_KEY = "invalid_virtual_key"
    CONFLICTING_BINDING = "conflicting_binding"
    RESERVED_KEY = "reserved_key"
    INVALID_ACTION = "invalid_action"
    DUPLICATE_BINDING = "duplicate_binding"

class ConflictResolution(Enum):
    """Conflict resolution strategies."""
    WARN = "warn"
    OVERRIDE = "override"
    IGNORE = "ignore"
    REJECT = "reject"

@dataclass
class ValidationResult:
    """Result of hotkey validation."""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    conflict_info: Optional[Dict] = None

@dataclass
class ConflictInfo:
    """Information about a hotkey conflict."""
    existing_binding: HotkeyBinding
    conflicting_binding: HotkeyBinding
    conflict_type: str
    resolution_suggestion: ConflictResolution

class HotkeyValidator:
    """
    Validates hotkey combinations and detects conflicts.
    
    This class provides comprehensive validation for hotkey bindings,
    including conflict detection, reserved key checking, and compatibility
    validation.
    """
    
    def __init__(self):
        # Reserved virtual key codes that should not be used for hotkeys
        self.reserved_keys: Set[int] = {
            0x00,  # VK_LBUTTON
            0x01,  # VK_RBUTTON
            0x02,  # VK_CANCEL
            0x03,  # VK_MBUTTON
            0x04,  # VK_XBUTTON1
            0x05,  # VK_XBUTTON2
            0x06,  # VK_BACK
            0x07,  # VK_TAB
            0x08,  # VK_CLEAR
            0x09,  # VK_RETURN
            0x0A,  # VK_SHIFT
            0x0B,  # VK_CONTROL
            0x0C,  # VK_MENU (Alt)
            0x0D,  # VK_PAUSE
            0x0E,  # VK_CAPITAL
            0x0F,  # VK_KANA
            0x10,  # VK_HANGUL
            0x11,  # VK_JUNJA
            0x12,  # VK_FINAL
            0x13,  # VK_HANJA
            0x14,  # VK_KANJI
            0x15,  # VK_ESCAPE
            0x16,  # VK_CONVERT
            0x17,  # VK_NONCONVERT
            0x18,  # VK_ACCEPT
            0x19,  # VK_MODECHANGE
            0x1A,  # VK_SPACE
            0x1B,  # VK_PRIOR
            0x1C,  # VK_NEXT
            0x1D,  # VK_END
            0x1E,  # VK_HOME
            0x1F,  # VK_LEFT
            0x20,  # VK_UP
            0x21,  # VK_RIGHT
            0x22,  # VK_DOWN
            0x23,  # VK_SELECT
            0x24,  # VK_PRINT
            0x25,  # VK_EXECUTE
            0x26,  # VK_SNAPSHOT
            0x27,  # VK_INSERT
            0x28,  # VK_DELETE
            0x29,  # VK_HELP
        }
        
        # System modifier combinations that should be avoided
        self.system_modifier_combinations: Set[HotkeyModifier] = {
            HotkeyModifier.CTRL | HotkeyModifier.ALT | 46,  # Ctrl+Alt+Del (VK_DELETE)
            HotkeyModifier.CTRL | HotkeyModifier.SHIFT | 27,   # Ctrl+Shift+Esc (VK_ESCAPE)
            HotkeyModifier.ALT | 9,                          # Alt+Tab (VK_TAB)
            HotkeyModifier.ALT | HotkeyModifier.SHIFT | 9,   # Alt+Shift+Tab (VK_TAB)
            HotkeyModifier.CTRL | 27,                         # Ctrl+Esc (VK_ESCAPE)
            HotkeyModifier.ALT | 115,                           # Alt+F4 (VK_F4)
        }
        
        # Minimum and maximum virtual key codes
        self.min_virtual_key = 0x08  # VK_BACK
        self.max_virtual_key = 0xFE  # VK_OEM_CLEAR
        
        logger.info("HotkeyValidator initialized")
    
    def validate_hotkey_combination(self, modifiers: HotkeyModifier, virtual_key: int) -> ValidationResult:
        """
        Validate a hotkey combination.
        
        Args:
            modifiers: Modifier keys
            virtual_key: Virtual key code
            
        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(valid=True)
        
        # Check virtual key validity
        if not self._is_valid_virtual_key(virtual_key):
            result.valid = False
            result.errors.append(ValidationError.INVALID_VIRTUAL_KEY)
            result.warnings.append(f"Invalid virtual key code: {virtual_key}")
        
        # Check for reserved keys
        if virtual_key in self.reserved_keys:
            result.valid = False
            result.errors.append(ValidationError.RESERVED_KEY)
            result.warnings.append(f"Virtual key {virtual_key} is reserved by the system")
        
        # Check modifier validity
        if not self._is_valid_modifier_combination(modifiers):
            result.valid = False
            result.errors.append(ValidationError.INVALID_MODIFIER)
            result.warnings.append(f"Invalid modifier combination: {modifiers}")
        
        # Check for system combinations
        if modifiers in self.system_modifier_combinations:
            result.warnings.append(f"Modifier combination {modifiers} may conflict with system shortcuts")
        
        # Check for empty modifiers (no modifier keys)
        if modifiers == HotkeyModifier.NONE:
            result.warnings.append("No modifier keys specified - hotkey may be too easy to trigger accidentally")
        
        return result
    
    def validate_binding(self, binding: HotkeyBinding, existing_bindings: Dict[int, HotkeyBinding]) -> ValidationResult:
        """
        Validate a hotkey binding against existing bindings.
        
        Args:
            binding: Hotkey binding to validate
            existing_bindings: Dictionary of existing bindings
            
        Returns:
            ValidationResult with validation details
        """
        result = self.validate_hotkey_combination(binding.modifiers, binding.virtual_key)
        
        # Check for conflicts with existing bindings
        conflict = self.check_conflict(binding.modifiers, binding.virtual_key, existing_bindings)
        if conflict:
            result.valid = False
            result.errors.append(ValidationError.CONFLICTING_BINDING)
            result.conflict_info = conflict
            result.warnings.append(f"Hotkey conflicts with existing binding: {conflict['existing_binding'].description}")
        
        # Check for duplicate action types
        for existing_binding in existing_bindings.values():
            if (existing_binding.action_type == binding.action_type and 
                existing_binding.hotkey_id != binding.hotkey_id):
                result.warnings.append(f"Action type {binding.action_type.value} is already bound to another key")
        
        return result
    
    def check_conflict(self, modifiers: HotkeyModifier, virtual_key: int, 
                      existing_bindings: Dict[int, HotkeyBinding]) -> Optional[Dict]:
        """
        Check for conflicts with existing hotkey bindings.
        
        Args:
            modifiers: Modifier keys
            virtual_key: Virtual key code
            existing_bindings: Dictionary of existing bindings
            
        Returns:
            Conflict information if found, None otherwise
        """
        for existing_binding in existing_bindings.values():
            if (existing_binding.modifiers == modifiers and 
                existing_binding.virtual_key == virtual_key):
                return {
                    'existing_binding': existing_binding,
                    'conflict_type': 'exact_match',
                    'resolution_suggestion': ConflictResolution.OVERRIDE
                }
        
        return None
    
    def find_conflicts(self, bindings: Dict[int, HotkeyBinding]) -> List[Dict]:
        """
        Find all conflicts within a set of bindings.
        
        Args:
            bindings: Dictionary of hotkey bindings
            
        Returns:
            List of conflict information dictionaries
        """
        conflicts = []
        binding_list = list(bindings.values())
        
        for i, binding1 in enumerate(binding_list):
            for binding2 in binding_list[i + 1:]:
                if (binding1.modifiers == binding2.modifiers and 
                    binding1.virtual_key == binding2.virtual_key):
                    conflicts.append({
                        'binding1': binding1,
                        'binding2': binding2,
                        'conflict_type': 'duplicate_combination',
                        'resolution_suggestion': ConflictResolution.WARN
                    })
        
        return conflicts
    
    def suggest_alternative(self, modifiers: HotkeyModifier, virtual_key: int, 
                          existing_bindings: Dict[int, HotkeyBinding]) -> List[Tuple[HotkeyModifier, int]]:
        """
        Suggest alternative hotkey combinations for a conflicted binding.
        
        Args:
            modifiers: Original modifier keys
            virtual_key: Original virtual key code
            existing_bindings: Dictionary of existing bindings
            
        Returns:
            List of alternative (modifiers, virtual_key) tuples
        """
        alternatives = []
        
        # Try different modifier combinations
        modifier_variations = [
            HotkeyModifier.CTRL | HotkeyModifier.SHIFT,
            HotkeyModifier.ALT | HotkeyModifier.SHIFT,
            HotkeyModifier.CTRL | HotkeyModifier.ALT | HotkeyModifier.SHIFT,
            HotkeyModifier.WIN | HotkeyModifier.CTRL,
            HotkeyModifier.WIN | HotkeyModifier.ALT,
        ]
        
        for alt_modifiers in modifier_variations:
            if not self.check_conflict(alt_modifiers, virtual_key, existing_bindings):
                alternatives.append((alt_modifiers, virtual_key))
        
        # Try different virtual keys with same modifiers
        key_variations = [
            virtual_key + 1,  # Next key
            virtual_key - 1,  # Previous key
            virtual_key + 10, # Skip some keys
            virtual_key - 10, # Skip some keys
        ]
        
        for alt_virtual_key in key_variations:
            if (self._is_valid_virtual_key(alt_virtual_key) and 
                not self.check_conflict(modifiers, alt_virtual_key, existing_bindings)):
                alternatives.append((modifiers, alt_virtual_key))
        
        return alternatives[:5]  # Return up to 5 alternatives
    
    def _is_valid_virtual_key(self, virtual_key: int) -> bool:
        """Check if a virtual key code is valid."""
        return self.min_virtual_key <= virtual_key <= self.max_virtual_key
    
    def _is_valid_modifier_combination(self, modifiers: HotkeyModifier) -> bool:
        """Check if a modifier combination is valid."""
        # Check for invalid combinations
        if modifiers == HotkeyModifier.NONE:
            return True  # No modifiers is technically valid
        
        # Check for conflicting modifiers (e.g., both left and right shift)
        # This is a simplified check - in practice, you might want more sophisticated validation
        return True
    
    def get_reserved_keys(self) -> Set[int]:
        """Get the set of reserved virtual key codes."""
        return self.reserved_keys.copy()
    
    def add_reserved_key(self, virtual_key: int):
        """Add a virtual key to the reserved list."""
        self.reserved_keys.add(virtual_key)
        logger.info(f"Added reserved key: {virtual_key}")
    
    def remove_reserved_key(self, virtual_key: int):
        """Remove a virtual key from the reserved list."""
        self.reserved_keys.discard(virtual_key)
        logger.info(f"Removed reserved key: {virtual_key}")
    
    def validate_action_type(self, action_type: HotkeyActionType) -> bool:
        """Validate that an action type is valid."""
        try:
            # Check if the action type exists in the enum
            return action_type in HotkeyActionType
        except (ValueError, TypeError):
            return False
    
    def get_compatibility_info(self, modifiers: HotkeyModifier, virtual_key: int) -> Dict[str, Any]:
        """
        Get compatibility information for a hotkey combination.
        
        Args:
            modifiers: Modifier keys
            virtual_key: Virtual key code
            
        Returns:
            Dictionary with compatibility information
        """
        info = {
            'valid': True,
            'warnings': [],
            'recommendations': [],
            'system_conflicts': [],
            'accessibility_notes': []
        }
        
        # Check for system conflicts
        if modifiers in self.system_modifier_combinations:
            info['system_conflicts'].append(f"May conflict with system shortcut: {modifiers}")
        
        # Check for accessibility concerns
        if modifiers == HotkeyModifier.NONE:
            info['accessibility_notes'].append("No modifier keys - may be difficult for users with motor disabilities")
        
        # Check for common gaming conflicts
        if modifiers == HotkeyModifier.CTRL and virtual_key in range(65, 91):  # A-Z
            info['warnings'].append("Ctrl+Letter combinations are commonly used in games")
        
        # Recommendations
        if modifiers == HotkeyModifier.NONE:
            info['recommendations'].append("Consider adding modifier keys for better control")
        
        if virtual_key in self.reserved_keys:
            info['valid'] = False
            info['warnings'].append("This key is reserved by the system")
        
        return info
