"""
Hotkey Configuration for ZeroLag

This module provides configuration management for hotkeys, including
saving/loading hotkey bindings, managing hotkey profiles, and handling
configuration validation.

Features:
- Hotkey binding configuration
- Profile-based hotkey management
- Configuration persistence
- Hotkey validation
- Import/export functionality
"""

import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

from .hotkey_detector import HotkeyModifier
from .hotkey_actions import HotkeyActionType

logger = logging.getLogger(__name__)

class HotkeyProfileType(Enum):
    """Types of hotkey profiles."""
    DEFAULT = "default"
    GAMING = "gaming"
    PRODUCTIVITY = "productivity"
    CUSTOM = "custom"

@dataclass
class HotkeyBinding:
    """Represents a single hotkey binding."""
    hotkey_id: int
    action_type: HotkeyActionType
    modifiers: HotkeyModifier
    virtual_key: int
    key_name: str
    description: str = ""
    enabled: bool = True
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    user_data: Optional[Dict[str, Any]] = None

@dataclass
class HotkeyProfile:
    """Represents a hotkey profile with multiple bindings."""
    name: str
    profile_type: HotkeyProfileType
    description: str = ""
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    bindings: Dict[int, HotkeyBinding] = field(default_factory=dict)
    enabled: bool = True
    user_data: Optional[Dict[str, Any]] = None

@dataclass
class HotkeyConfig:
    """Main configuration class for hotkey management."""
    profiles: Dict[str, HotkeyProfile] = field(default_factory=dict)
    active_profile: Optional[str] = None
    global_settings: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    version: str = "1.0.0"

class HotkeyConfigManager:
    """
    Manages hotkey configuration including profiles and bindings.
    
    This class provides functionality to save, load, and manage hotkey
    configurations with support for multiple profiles and validation.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("config/hotkeys.json")
        self.config = HotkeyConfig()
        self.next_hotkey_id = 1
        
        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing configuration
        self.load_config()
        
        logger.info(f"HotkeyConfigManager initialized with config path: {self.config_path}")
    
    def create_profile(self, name: str, profile_type: HotkeyProfileType = HotkeyProfileType.CUSTOM,
                      description: str = "") -> HotkeyProfile:
        """
        Create a new hotkey profile.
        
        Args:
            name: Name of the profile
            profile_type: Type of profile
            description: Description of the profile
            
        Returns:
            Created HotkeyProfile
        """
        if name in self.config.profiles:
            raise ValueError(f"Profile '{name}' already exists")
        
        profile = HotkeyProfile(
            name=name,
            profile_type=profile_type,
            description=description
        )
        
        self.config.profiles[name] = profile
        self.config.modified_at = time.time()
        
        logger.info(f"Created hotkey profile: {name}")
        return profile
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a hotkey profile.
        
        Args:
            name: Name of the profile to delete
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.config.profiles:
            logger.warning(f"Profile '{name}' not found")
            return False
        
        # Don't allow deleting the active profile
        if self.config.active_profile == name:
            logger.warning(f"Cannot delete active profile '{name}'")
            return False
        
        del self.config.profiles[name]
        self.config.modified_at = time.time()
        
        logger.info(f"Deleted hotkey profile: {name}")
        return True
    
    def set_active_profile(self, name: str) -> bool:
        """
        Set the active hotkey profile.
        
        Args:
            name: Name of the profile to activate
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.config.profiles:
            logger.warning(f"Profile '{name}' not found")
            return False
        
        self.config.active_profile = name
        self.config.modified_at = time.time()
        
        logger.info(f"Set active profile: {name}")
        return True
    
    def get_active_profile(self) -> Optional[HotkeyProfile]:
        """Get the currently active profile."""
        if self.config.active_profile and self.config.active_profile in self.config.profiles:
            return self.config.profiles[self.config.active_profile]
        return None
    
    def add_binding(self, profile_name: str, action_type: HotkeyActionType,
                   modifiers: HotkeyModifier, virtual_key: int, key_name: str,
                   description: str = "") -> Optional[HotkeyBinding]:
        """
        Add a hotkey binding to a profile.
        
        Args:
            profile_name: Name of the profile
            action_type: Type of action
            modifiers: Modifier keys
            virtual_key: Virtual key code
            key_name: Human-readable key name
            description: Description of the binding
            
        Returns:
            Created HotkeyBinding if successful, None otherwise
        """
        if profile_name not in self.config.profiles:
            logger.error(f"Profile '{profile_name}' not found")
            return None
        
        # Check for conflicts
        if self._has_conflict(profile_name, modifiers, virtual_key):
            logger.warning(f"Hotkey conflict detected: {modifiers} + {key_name}")
            return None
        
        hotkey_id = self.next_hotkey_id
        self.next_hotkey_id += 1
        
        binding = HotkeyBinding(
            hotkey_id=hotkey_id,
            action_type=action_type,
            modifiers=modifiers,
            virtual_key=virtual_key,
            key_name=key_name,
            description=description
        )
        
        self.config.profiles[profile_name].bindings[hotkey_id] = binding
        self.config.profiles[profile_name].modified_at = time.time()
        self.config.modified_at = time.time()
        
        logger.info(f"Added binding to profile '{profile_name}': {action_type.value} -> {key_name}")
        return binding
    
    def remove_binding(self, profile_name: str, hotkey_id: int) -> bool:
        """
        Remove a hotkey binding from a profile.
        
        Args:
            profile_name: Name of the profile
            hotkey_id: ID of the binding to remove
            
        Returns:
            True if successful, False otherwise
        """
        if profile_name not in self.config.profiles:
            logger.error(f"Profile '{profile_name}' not found")
            return False
        
        if hotkey_id not in self.config.profiles[profile_name].bindings:
            logger.warning(f"Binding {hotkey_id} not found in profile '{profile_name}'")
            return False
        
        del self.config.profiles[profile_name].bindings[hotkey_id]
        self.config.profiles[profile_name].modified_at = time.time()
        self.config.modified_at = time.time()
        
        logger.info(f"Removed binding {hotkey_id} from profile '{profile_name}'")
        return True
    
    def update_binding(self, profile_name: str, hotkey_id: int, **kwargs) -> bool:
        """
        Update a hotkey binding.
        
        Args:
            profile_name: Name of the profile
            hotkey_id: ID of the binding to update
            **kwargs: Fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if profile_name not in self.config.profiles:
            logger.error(f"Profile '{profile_name}' not found")
            return False
        
        if hotkey_id not in self.config.profiles[profile_name].bindings:
            logger.warning(f"Binding {hotkey_id} not found in profile '{profile_name}'")
            return False
        
        binding = self.config.profiles[profile_name].bindings[hotkey_id]
        
        # Update allowed fields
        allowed_fields = ['description', 'enabled', 'user_data']
        for field_name, value in kwargs.items():
            if field_name in allowed_fields and hasattr(binding, field_name):
                setattr(binding, field_name, value)
        
        binding.modified_at = time.time()
        self.config.profiles[profile_name].modified_at = time.time()
        self.config.modified_at = time.time()
        
        logger.info(f"Updated binding {hotkey_id} in profile '{profile_name}'")
        return True
    
    def get_bindings(self, profile_name: Optional[str] = None) -> Dict[int, HotkeyBinding]:
        """
        Get hotkey bindings for a profile or all profiles.
        
        Args:
            profile_name: Name of the profile (None for all profiles)
            
        Returns:
            Dictionary of hotkey bindings
        """
        if profile_name:
            if profile_name in self.config.profiles:
                return self.config.profiles[profile_name].bindings.copy()
            return {}
        
        # Return bindings from all profiles
        all_bindings = {}
        for profile in self.config.profiles.values():
            all_bindings.update(profile.bindings)
        return all_bindings
    
    def get_binding_by_action(self, profile_name: str, action_type: HotkeyActionType) -> Optional[HotkeyBinding]:
        """
        Get a hotkey binding by action type.
        
        Args:
            profile_name: Name of the profile
            action_type: Type of action
            
        Returns:
            HotkeyBinding if found, None otherwise
        """
        if profile_name not in self.config.profiles:
            return None
        
        for binding in self.config.profiles[profile_name].bindings.values():
            if binding.action_type == action_type:
                return binding
        return None
    
    def _has_conflict(self, profile_name: str, modifiers: HotkeyModifier, virtual_key: int) -> bool:
        """Check if a hotkey combination conflicts with existing bindings."""
        if profile_name not in self.config.profiles:
            return False
        
        for binding in self.config.profiles[profile_name].bindings.values():
            if binding.modifiers == modifiers and binding.virtual_key == virtual_key:
                return True
        return False
    
    def load_config(self, config_path: Optional[str] = None) -> bool:
        """
        Load hotkey configuration from file.
        
        Args:
            config_path: Path to configuration file (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if config_path:
            self.config_path = Path(config_path)
        
        try:
            if not self.config_path.exists():
                logger.info(f"Configuration file not found: {self.config_path}")
                self._create_default_config()
                return True
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert loaded data to configuration objects
            self.config = self._dict_to_config(data)
            
            # Update next hotkey_id to avoid conflicts
            max_id = 0
            for profile in self.config.profiles.values():
                for binding in profile.bindings.values():
                    max_id = max(max_id, binding.hotkey_id)
            self.next_hotkey_id = max_id + 1
            
            logger.info(f"Loaded hotkey configuration from {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading hotkey configuration: {e}")
            return False
    
    def save_config(self, config_path: Optional[str] = None) -> bool:
        """
        Save hotkey configuration to file.
        
        Args:
            config_path: Path to configuration file (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if config_path:
            self.config_path = Path(config_path)
        
        try:
            # Convert configuration to dictionary
            data = self._config_to_dict(self.config)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved hotkey configuration to {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving hotkey configuration: {e}")
            return False
    
    def _create_default_config(self):
        """Create default hotkey configuration."""
        # Create default profile
        default_profile = self.create_profile("Default", HotkeyProfileType.DEFAULT, "Default hotkey profile")
        
        # Add some default bindings
        self.add_binding("Default", HotkeyActionType.TOGGLE_ZEROLAG, 
                        HotkeyModifier.CTRL | HotkeyModifier.ALT, 90, "Z", "Toggle ZeroLag")
        self.add_binding("Default", HotkeyActionType.EMERGENCY_STOP, 
                        HotkeyModifier.CTRL | HotkeyModifier.ALT, 46, "Delete", "Emergency Stop")
        
        # Set as active profile
        self.set_active_profile("Default")
        
        # Save the default configuration
        self.save_config()
        
        logger.info("Created default hotkey configuration")
    
    def _config_to_dict(self, config: HotkeyConfig) -> Dict[str, Any]:
        """Convert HotkeyConfig to dictionary for JSON serialization."""
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
        
        data = asdict(config)
        return convert_enum(data)
    
    def _dict_to_config(self, data: Dict[str, Any]) -> HotkeyConfig:
        """Convert dictionary to HotkeyConfig object."""
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
        
        # Convert profiles back to HotkeyProfile objects
        if 'profiles' in data:
            converted_profiles = {}
            for profile_name, profile_data in data['profiles'].items():
                # Convert profile type
                if 'profile_type' in profile_data:
                    profile_data['profile_type'] = convert_enum_back(profile_data['profile_type'], HotkeyProfileType)
                
                # Convert bindings back to HotkeyBinding objects
                if 'bindings' in profile_data:
                    converted_bindings = {}
                    for binding_id, binding_data in profile_data['bindings'].items():
                        # Convert action type and modifiers
                        if 'action_type' in binding_data:
                            binding_data['action_type'] = convert_enum_back(binding_data['action_type'], HotkeyActionType)
                        if 'modifiers' in binding_data:
                            binding_data['modifiers'] = HotkeyModifier(binding_data['modifiers'])
                        
                        # Create HotkeyBinding object
                        converted_bindings[int(binding_id)] = HotkeyBinding(**binding_data)
                    
                    profile_data['bindings'] = converted_bindings
                
                # Create HotkeyProfile object
                converted_profiles[profile_name] = HotkeyProfile(**profile_data)
            
            data['profiles'] = converted_profiles
        
        return HotkeyConfig(**data)
    
    def export_profile(self, profile_name: str, export_path: str) -> bool:
        """
        Export a hotkey profile to a file.
        
        Args:
            profile_name: Name of the profile to export
            export_path: Path to export file
            
        Returns:
            True if successful, False otherwise
        """
        if profile_name not in self.config.profiles:
            logger.error(f"Profile '{profile_name}' not found")
            return False
        
        try:
            profile = self.config.profiles[profile_name]
            data = self._config_to_dict(HotkeyConfig(profiles={profile_name: profile}))
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported profile '{profile_name}' to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting profile: {e}")
            return False
    
    def import_profile(self, import_path: str, profile_name: Optional[str] = None) -> bool:
        """
        Import a hotkey profile from a file.
        
        Args:
            import_path: Path to import file
            profile_name: Name for the imported profile (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_config = self._dict_to_config(data)
            
            # Use the first profile from the imported config
            if not imported_config.profiles:
                logger.error("No profiles found in import file")
                return False
            
            imported_profile_name = list(imported_config.profiles.keys())[0]
            imported_profile = imported_config.profiles[imported_profile_name]
            
            # Use provided name or keep original name
            final_name = profile_name or imported_profile_name
            
            # Check for name conflicts
            if final_name in self.config.profiles:
                logger.warning(f"Profile '{final_name}' already exists, overwriting")
            
            # Update profile name
            imported_profile.name = final_name
            self.config.profiles[final_name] = imported_profile
            self.config.modified_at = time.time()
            
            logger.info(f"Imported profile '{final_name}' from {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing profile: {e}")
            return False
    
    def get_profile_list(self) -> List[str]:
        """Get list of available profile names."""
        return list(self.config.profiles.keys())
    
    def get_profile_info(self, profile_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific profile."""
        if profile_name not in self.config.profiles:
            return None
        
        profile = self.config.profiles[profile_name]
        return {
            'name': profile.name,
            'type': profile.profile_type.value,
            'description': profile.description,
            'enabled': profile.enabled,
            'binding_count': len(profile.bindings),
            'created_at': profile.created_at,
            'modified_at': profile.modified_at
        }
