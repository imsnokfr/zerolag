"""
Hotkey Presets for ZeroLag

This module provides predefined hotkey configurations for different
gaming genres and use cases, making it easy for users to get started
with optimized hotkey setups.

Features:
- Gaming genre presets (FPS, MOBA, RTS, MMO, etc.)
- Productivity presets
- Custom preset creation
- Preset validation and testing
- Preset sharing and import/export
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from .hotkey_config import HotkeyProfile, HotkeyBinding, HotkeyProfileType
from .hotkey_actions import HotkeyActionType
from .hotkey_detector import HotkeyModifier

logger = logging.getLogger(__name__)

class GamingGenre(Enum):
    """Gaming genres for preset categorization."""
    FPS = "fps"
    MOBA = "moba"
    RTS = "rts"
    MMO = "mmo"
    RPG = "rpg"
    RACING = "racing"
    FIGHTING = "fighting"
    STRATEGY = "strategy"
    SIMULATION = "simulation"
    SPORTS = "sports"

class PresetComplexity(Enum):
    """Complexity levels for presets."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class HotkeyPreset:
    """Represents a hotkey preset configuration."""
    name: str
    genre: GamingGenre
    complexity: PresetComplexity
    description: str
    author: str = "ZeroLag Team"
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)
    bindings: List[Dict[str, Any]] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

class HotkeyPresetManager:
    """
    Manages hotkey presets for different gaming genres and use cases.
    
    This class provides predefined hotkey configurations and allows
    users to create, modify, and share custom presets.
    """
    
    def __init__(self):
        self.presets: Dict[str, HotkeyPreset] = {}
        self.custom_presets: Dict[str, HotkeyPreset] = {}
        
        # Load built-in presets
        self._load_builtin_presets()
        
        logger.info("HotkeyPresetManager initialized")
    
    def _load_builtin_presets(self):
        """Load built-in hotkey presets."""
        # FPS Gaming Preset
        fps_preset = HotkeyPreset(
            name="FPS Gaming",
            genre=GamingGenre.FPS,
            complexity=PresetComplexity.INTERMEDIATE,
            description="Optimized hotkeys for first-person shooter games",
            bindings=[
                {
                    "action": HotkeyActionType.INCREASE_DPI,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 38,  # Up arrow
                    "key_name": "Up",
                    "description": "Increase DPI for precision"
                },
                {
                    "action": HotkeyActionType.DECREASE_DPI,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 40,  # Down arrow
                    "key_name": "Down",
                    "description": "Decrease DPI for wide view"
                },
                {
                    "action": HotkeyActionType.TOGGLE_SMOOTHING,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 83,  # S key
                    "key_name": "S",
                    "description": "Toggle cursor smoothing"
                },
                {
                    "action": HotkeyActionType.EMERGENCY_STOP,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT | HotkeyModifier.SHIFT,
                    "virtual_key": 27,  # Escape
                    "key_name": "Escape",
                    "description": "Emergency stop all optimizations"
                },
                {
                    "action": HotkeyActionType.TOGGLE_ZEROLAG,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 90,  # Z key
                    "key_name": "Z",
                    "description": "Toggle ZeroLag on/off"
                }
            ],
            requirements=["Gaming mouse with DPI adjustment", "Low-latency keyboard"],
            tags=["fps", "gaming", "precision", "aiming"]
        )
        self.presets["fps_gaming"] = fps_preset
        
        # MOBA Gaming Preset
        moba_preset = HotkeyPreset(
            name="MOBA Gaming",
            genre=GamingGenre.MOBA,
            complexity=PresetComplexity.ADVANCED,
            description="Hotkeys optimized for MOBA games like League of Legends, Dota 2",
            bindings=[
                {
                    "action": HotkeyActionType.INCREASE_POLLING_RATE,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 80,  # P key
                    "key_name": "P",
                    "description": "Increase polling rate for responsiveness"
                },
                {
                    "action": HotkeyActionType.DECREASE_POLLING_RATE,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 79,  # O key
                    "key_name": "O",
                    "description": "Decrease polling rate for stability"
                },
                {
                    "action": HotkeyActionType.TOGGLE_NKRO,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 78,  # N key
                    "key_name": "N",
                    "description": "Toggle N-Key Rollover for complex combos"
                },
                {
                    "action": HotkeyActionType.TOGGLE_RAPID_TRIGGER,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 82,  # R key
                    "key_name": "R",
                    "description": "Toggle rapid trigger for quick actions"
                },
                {
                    "action": HotkeyActionType.EMERGENCY_RESET,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT | HotkeyModifier.SHIFT,
                    "virtual_key": 82,  # R key
                    "key_name": "R",
                    "description": "Emergency reset to safe defaults"
                }
            ],
            requirements=["Mechanical keyboard", "Gaming mouse", "Low input lag setup"],
            tags=["moba", "gaming", "mechanical", "responsiveness"]
        )
        self.presets["moba_gaming"] = moba_preset
        
        # RTS Gaming Preset
        rts_preset = HotkeyPreset(
            name="RTS Gaming",
            genre=GamingGenre.RTS,
            complexity=PresetComplexity.EXPERT,
            description="Hotkeys for real-time strategy games like StarCraft, Age of Empires",
            bindings=[
                {
                    "action": HotkeyActionType.INCREASE_DPI,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 38,  # Up arrow
                    "key_name": "Up",
                    "description": "Increase DPI for quick map navigation"
                },
                {
                    "action": HotkeyActionType.DECREASE_DPI,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 40,  # Down arrow
                    "key_name": "Down",
                    "description": "Decrease DPI for precise unit selection"
                },
                {
                    "action": HotkeyActionType.TOGGLE_SMOOTHING,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 83,  # S key
                    "key_name": "S",
                    "description": "Toggle cursor smoothing for smooth scrolling"
                },
                {
                    "action": HotkeyActionType.INCREASE_SMOOTHING,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 187,  # + key
                    "key_name": "+",
                    "description": "Increase smoothing strength"
                },
                {
                    "action": HotkeyActionType.DECREASE_SMOOTHING,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 189,  # - key
                    "key_name": "-",
                    "description": "Decrease smoothing strength"
                },
                {
                    "action": HotkeyActionType.START_MACRO_RECORDING,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 77,  # M key
                    "key_name": "M",
                    "description": "Start recording macro for build orders"
                },
                {
                    "action": HotkeyActionType.STOP_MACRO_RECORDING,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 78,  # N key
                    "key_name": "N",
                    "description": "Stop recording macro"
                }
            ],
            requirements=["High-DPI mouse", "Mechanical keyboard", "Large mousepad"],
            tags=["rts", "gaming", "strategy", "macros", "precision"]
        )
        self.presets["rts_gaming"] = rts_preset
        
        # MMO Gaming Preset
        mmo_preset = HotkeyPreset(
            name="MMO Gaming",
            genre=GamingGenre.MMO,
            complexity=PresetComplexity.ADVANCED,
            description="Hotkeys for MMORPG games like World of Warcraft, Final Fantasy XIV",
            bindings=[
                {
                    "action": HotkeyActionType.TOGGLE_NKRO,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 78,  # N key
                    "key_name": "N",
                    "description": "Toggle N-Key Rollover for complex key combinations"
                },
                {
                    "action": HotkeyActionType.TOGGLE_RAPID_TRIGGER,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 82,  # R key
                    "key_name": "R",
                    "description": "Toggle rapid trigger for quick skill activation"
                },
                {
                    "action": HotkeyActionType.ADJUST_DEBOUNCE_TIME,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 68,  # D key
                    "key_name": "D",
                    "description": "Adjust debounce time for key spam prevention"
                },
                {
                    "action": HotkeyActionType.START_MACRO_RECORDING,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 77,  # M key
                    "key_name": "M",
                    "description": "Start recording macro for skill rotations"
                },
                {
                    "action": HotkeyActionType.PLAY_MACRO,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 80,  # P key
                    "key_name": "P",
                    "description": "Play recorded macro"
                },
                {
                    "action": HotkeyActionType.EMERGENCY_DISABLE_ALL,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT | HotkeyModifier.SHIFT,
                    "virtual_key": 68,  # D key
                    "key_name": "D",
                    "description": "Emergency disable all optimizations"
                }
            ],
            requirements=["Mechanical keyboard with NKRO", "Gaming mouse", "Macro support"],
            tags=["mmo", "gaming", "macros", "nkro", "skills"]
        )
        self.presets["mmo_gaming"] = mmo_preset
        
        # Productivity Preset
        productivity_preset = HotkeyPreset(
            name="Productivity",
            genre=GamingGenre.SIMULATION,  # Using simulation as closest to productivity
            complexity=PresetComplexity.BASIC,
            description="Hotkeys optimized for productivity and general computer use",
            bindings=[
                {
                    "action": HotkeyActionType.TOGGLE_ZEROLAG,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 90,  # Z key
                    "key_name": "Z",
                    "description": "Toggle ZeroLag on/off"
                },
                {
                    "action": HotkeyActionType.SHOW_GUI,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 71,  # G key
                    "key_name": "G",
                    "description": "Show ZeroLag GUI"
                },
                {
                    "action": HotkeyActionType.HIDE_GUI,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 72,  # H key
                    "key_name": "H",
                    "description": "Hide ZeroLag GUI"
                },
                {
                    "action": HotkeyActionType.MINIMIZE_TO_TRAY,
                    "modifiers": HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    "virtual_key": 84,  # T key
                    "key_name": "T",
                    "description": "Minimize to system tray"
                }
            ],
            requirements=["Standard keyboard and mouse"],
            tags=["productivity", "general", "basic", "work"]
        )
        self.presets["productivity"] = productivity_preset
        
        logger.info(f"Loaded {len(self.presets)} built-in presets")
    
    def get_preset(self, preset_id: str) -> Optional[HotkeyPreset]:
        """Get a preset by ID."""
        if preset_id in self.presets:
            return self.presets[preset_id]
        elif preset_id in self.custom_presets:
            return self.custom_presets[preset_id]
        return None
    
    def get_presets_by_genre(self, genre: GamingGenre) -> List[HotkeyPreset]:
        """Get all presets for a specific genre."""
        presets = []
        for preset in self.presets.values():
            if preset.genre == genre:
                presets.append(preset)
        for preset in self.custom_presets.values():
            if preset.genre == genre:
                presets.append(preset)
        return presets
    
    def get_presets_by_complexity(self, complexity: PresetComplexity) -> List[HotkeyPreset]:
        """Get all presets for a specific complexity level."""
        presets = []
        for preset in self.presets.values():
            if preset.complexity == complexity:
                presets.append(preset)
        for preset in self.custom_presets.values():
            if preset.complexity == complexity:
                presets.append(preset)
        return presets
    
    def search_presets(self, query: str) -> List[HotkeyPreset]:
        """Search presets by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for preset in self.presets.values():
            if (query_lower in preset.name.lower() or
                query_lower in preset.description.lower() or
                any(query_lower in tag.lower() for tag in preset.tags)):
                results.append(preset)
        
        for preset in self.custom_presets.values():
            if (query_lower in preset.name.lower() or
                query_lower in preset.description.lower() or
                any(query_lower in tag.lower() for tag in preset.tags)):
                results.append(preset)
        
        return results
    
    def create_custom_preset(self, name: str, genre: GamingGenre, 
                           complexity: PresetComplexity, description: str,
                           bindings: List[Dict[str, Any]], author: str = "User",
                           requirements: List[str] = None, tags: List[str] = None) -> str:
        """
        Create a custom preset.
        
        Args:
            name: Name of the preset
            genre: Gaming genre
            complexity: Complexity level
            description: Description of the preset
            bindings: List of binding configurations
            author: Author of the preset
            requirements: List of requirements
            tags: List of tags
            
        Returns:
            Preset ID if successful, None otherwise
        """
        preset_id = f"custom_{name.lower().replace(' ', '_')}"
        
        if preset_id in self.custom_presets:
            logger.warning(f"Custom preset '{preset_id}' already exists")
            return None
        
        preset = HotkeyPreset(
            name=name,
            genre=genre,
            complexity=complexity,
            description=description,
            author=author,
            bindings=bindings,
            requirements=requirements or [],
            tags=tags or []
        )
        
        self.custom_presets[preset_id] = preset
        logger.info(f"Created custom preset: {preset_id}")
        return preset_id
    
    def delete_custom_preset(self, preset_id: str) -> bool:
        """Delete a custom preset."""
        if preset_id in self.custom_presets:
            del self.custom_presets[preset_id]
            logger.info(f"Deleted custom preset: {preset_id}")
            return True
        return False
    
    def apply_preset_to_profile(self, preset_id: str, profile: HotkeyProfile) -> bool:
        """
        Apply a preset to a profile.
        
        Args:
            preset_id: ID of the preset to apply
            profile: Profile to apply the preset to
            
        Returns:
            True if successful, False otherwise
        """
        preset = self.get_preset(preset_id)
        if not preset:
            logger.error(f"Preset '{preset_id}' not found")
            return False
        
        try:
            # Clear existing bindings
            profile.bindings.clear()
            
            # Add preset bindings
            for binding_config in preset.bindings:
                binding = HotkeyBinding(
                    hotkey_id=len(profile.bindings) + 1,
                    action_type=binding_config["action"],
                    modifiers=binding_config["modifiers"],
                    virtual_key=binding_config["virtual_key"],
                    key_name=binding_config["key_name"],
                    description=binding_config["description"],
                    enabled=True,
                    created_at=time.time(),
                    modified_at=time.time()
                )
                profile.bindings[binding.hotkey_id] = binding
            
            profile.modified_at = time.time()
            logger.info(f"Applied preset '{preset_id}' to profile '{profile.name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error applying preset '{preset_id}': {e}")
            return False
    
    def export_preset(self, preset_id: str, file_path: str) -> bool:
        """Export a preset to a file."""
        preset = self.get_preset(preset_id)
        if not preset:
            return False
        
        try:
            import json
            from dataclasses import asdict
            
            # Convert preset to dictionary
            preset_dict = asdict(preset)
            
            # Convert enums to strings
            def convert_enum(obj):
                if isinstance(obj, Enum):
                    return obj.value
                elif isinstance(obj, dict):
                    return {k: convert_enum(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_enum(item) for item in obj]
                else:
                    return obj
            
            preset_dict = convert_enum(preset_dict)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(preset_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported preset '{preset_id}' to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting preset '{preset_id}': {e}")
            return False
    
    def import_preset(self, file_path: str) -> Optional[str]:
        """Import a preset from a file."""
        try:
            import json
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert string values back to enums
            def convert_enum_back(obj, enum_class=None):
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
            
            # Convert enums
            if 'genre' in data:
                data['genre'] = convert_enum_back(data['genre'], GamingGenre)
            if 'complexity' in data:
                data['complexity'] = convert_enum_back(data['complexity'], PresetComplexity)
            
            # Create preset
            preset = HotkeyPreset(**data)
            preset_id = f"custom_{preset.name.lower().replace(' ', '_')}"
            
            self.custom_presets[preset_id] = preset
            logger.info(f"Imported preset '{preset_id}' from {file_path}")
            return preset_id
            
        except Exception as e:
            logger.error(f"Error importing preset: {e}")
            return None
    
    def get_all_presets(self) -> List[HotkeyPreset]:
        """Get all available presets."""
        return list(self.presets.values()) + list(self.custom_presets.values())
    
    def get_preset_list(self) -> List[Dict[str, Any]]:
        """Get a list of all presets with basic information."""
        preset_list = []
        
        for preset_id, preset in self.presets.items():
            preset_list.append({
                'id': preset_id,
                'name': preset.name,
                'genre': preset.genre.value,
                'complexity': preset.complexity.value,
                'description': preset.description,
                'author': preset.author,
                'is_custom': False,
                'binding_count': len(preset.bindings)
            })
        
        for preset_id, preset in self.custom_presets.items():
            preset_list.append({
                'id': preset_id,
                'name': preset.name,
                'genre': preset.genre.value,
                'complexity': preset.complexity.value,
                'description': preset.description,
                'author': preset.author,
                'is_custom': True,
                'binding_count': len(preset.bindings)
            })
        
        return preset_list
