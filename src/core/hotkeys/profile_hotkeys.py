"""
Profile Switching Hotkeys for ZeroLag

This module provides specialized hotkey functionality for profile switching,
including cycling through profiles, quick preset switching, and visual feedback.

Features:
- Profile cycling hotkeys (Ctrl+Alt+P)
- Specific profile switching (Ctrl+Alt+1, Ctrl+Alt+2, etc.)
- Gaming preset hotkeys (Ctrl+Alt+F for FPS, Ctrl+Alt+M for MOBA, etc.)
- Visual feedback for profile switches
- Integration with existing profile management system
"""

import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field

from .hotkey_actions import HotkeyActionType, ActionContext, ActionResult
from .hotkey_detector import HotkeyModifier
from ..profiles import ProfileManager, Profile, GamingMode

logger = logging.getLogger(__name__)

@dataclass
class ProfileSwitchFeedback:
    """Feedback information for profile switching."""
    profile_name: str
    switch_time: float
    success: bool
    message: str = ""
    visual_feedback: bool = True
    audio_feedback: bool = False

@dataclass
class ProfileHotkeyConfig:
    """Configuration for profile switching hotkeys."""
    enable_profile_cycling: bool = True
    enable_specific_switching: bool = True
    enable_preset_switching: bool = True
    max_profile_hotkeys: int = 9  # 1-9 keys
    visual_feedback_duration: float = 2.0  # seconds
    audio_feedback: bool = False
    cycle_direction: str = "forward"  # "forward", "backward", "alternating"

class ProfileHotkeyManager:
    """
    Manages profile switching hotkeys and provides visual feedback.
    
    This class integrates with the existing profile management system
    to provide hotkey-based profile switching functionality.
    """
    
    def __init__(self, profile_manager: ProfileManager, config: Optional[ProfileHotkeyConfig] = None):
        self.profile_manager = profile_manager
        self.config = config or ProfileHotkeyConfig()
        
        # Profile switching state
        self.current_profile_index = 0
        self.profile_list: List[str] = []
        self.last_switch_time = 0.0
        self.switch_history: List[ProfileSwitchFeedback] = []
        
        # Callbacks for visual feedback
        self.feedback_callbacks: List[Callable[[ProfileSwitchFeedback], None]] = []
        
        # Hotkey mappings
        self.profile_hotkey_mappings: Dict[int, str] = {}  # hotkey_id -> profile_name
        self.preset_hotkey_mappings: Dict[str, str] = {}   # preset_key -> profile_name
        
        # Update profile list
        self._update_profile_list()
        
        logger.info("ProfileHotkeyManager initialized")
    
    def register_profile_hotkeys(self, hotkey_manager) -> Dict[str, int]:
        """
        Register all profile switching hotkeys with the hotkey manager.
        
        Args:
            hotkey_manager: HotkeyManager instance
            
        Returns:
            Dictionary mapping action names to hotkey IDs
        """
        hotkey_ids = {}
        
        try:
            # Profile cycling hotkey
            if self.config.enable_profile_cycling:
                hotkey_id = hotkey_manager.register_hotkey(
                    HotkeyActionType.CYCLE_PROFILE,
                    HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    hotkey_manager.detector.get_virtual_key_code('P'),
                    self._handle_cycle_profile
                )
                if hotkey_id:
                    hotkey_ids['cycle_profile'] = hotkey_id
                    logger.info("Registered profile cycling hotkey: Ctrl+Alt+P")
            
            # Specific profile switching hotkeys (1-9)
            if self.config.enable_specific_switching:
                for i in range(1, min(self.config.max_profile_hotkeys + 1, 10)):
                    virtual_key = ord(str(i))  # Convert number to virtual key
                    hotkey_id = hotkey_manager.register_hotkey(
                        HotkeyActionType.SWITCH_TO_PROFILE,
                        HotkeyModifier.CTRL | HotkeyModifier.ALT,
                        virtual_key,
                        lambda ctx, idx=i-1: self._handle_switch_to_profile(ctx, idx)
                    )
                    if hotkey_id:
                        hotkey_ids[f'switch_to_profile_{i}'] = hotkey_id
                        logger.info(f"Registered profile switch hotkey: Ctrl+Alt+{i}")
            
            # Gaming preset hotkeys
            if self.config.enable_preset_switching:
                preset_hotkeys = {
                    'F': 'FPS',      # Ctrl+Alt+F for FPS preset
                    'M': 'MOBA',     # Ctrl+Alt+M for MOBA preset
                    'R': 'RTS',      # Ctrl+Alt+R for RTS preset
                    'O': 'MMO',      # Ctrl+Alt+O for MMO preset
                }
                
                for key, preset_name in preset_hotkeys.items():
                    virtual_key = ord(key.upper())
                    hotkey_id = hotkey_manager.register_hotkey(
                        HotkeyActionType.SWITCH_TO_PROFILE,
                        HotkeyModifier.CTRL | HotkeyModifier.ALT,
                        virtual_key,
                        lambda ctx, preset=preset_name: self._handle_switch_to_preset(ctx, preset)
                    )
                    if hotkey_id:
                        hotkey_ids[f'switch_to_preset_{preset_name.lower()}'] = hotkey_id
                        self.preset_hotkey_mappings[key] = preset_name
                        logger.info(f"Registered preset hotkey: Ctrl+Alt+{key} -> {preset_name}")
            
            logger.info(f"Registered {len(hotkey_ids)} profile switching hotkeys")
            return hotkey_ids
            
        except Exception as e:
            logger.error(f"Error registering profile hotkeys: {e}")
            return {}
    
    def _handle_cycle_profile(self, context: ActionContext) -> Dict[str, Any]:
        """Handle profile cycling hotkey."""
        try:
            # Update profile list
            self._update_profile_list()
            
            if not self.profile_list:
                return {
                    'success': False,
                    'message': 'No profiles available for switching',
                    'action': 'cycle_profile'
                }
            
            # Determine next profile index
            if self.config.cycle_direction == "forward":
                self.current_profile_index = (self.current_profile_index + 1) % len(self.profile_list)
            elif self.config.cycle_direction == "backward":
                self.current_profile_index = (self.current_profile_index - 1) % len(self.profile_list)
            else:  # alternating
                # Simple alternating logic - could be enhanced
                self.current_profile_index = (self.current_profile_index + 1) % len(self.profile_list)
            
            # Switch to the selected profile
            profile_name = self.profile_list[self.current_profile_index]
            success = self._switch_to_profile(profile_name)
            
            return {
                'success': success,
                'profile_name': profile_name,
                'profile_index': self.current_profile_index,
                'action': 'cycle_profile'
            }
            
        except Exception as e:
            logger.error(f"Error handling cycle profile: {e}")
            return {
                'success': False,
                'message': f'Error cycling profile: {str(e)}',
                'action': 'cycle_profile'
            }
    
    def _handle_switch_to_profile(self, context: ActionContext, profile_index: int) -> Dict[str, Any]:
        """Handle switching to a specific profile by index."""
        try:
            # Update profile list
            self._update_profile_list()
            
            if not self.profile_list:
                return {
                    'success': False,
                    'message': 'No profiles available for switching',
                    'action': 'switch_to_profile'
                }
            
            if profile_index >= len(self.profile_list):
                return {
                    'success': False,
                    'message': f'Profile index {profile_index} out of range',
                    'action': 'switch_to_profile'
                }
            
            profile_name = self.profile_list[profile_index]
            success = self._switch_to_profile(profile_name)
            
            if success:
                self.current_profile_index = profile_index
            
            return {
                'success': success,
                'profile_name': profile_name,
                'profile_index': profile_index,
                'action': 'switch_to_profile'
            }
            
        except Exception as e:
            logger.error(f"Error handling switch to profile: {e}")
            return {
                'success': False,
                'message': f'Error switching to profile: {str(e)}',
                'action': 'switch_to_profile'
            }
    
    def _handle_switch_to_preset(self, context: ActionContext, preset_name: str) -> Dict[str, Any]:
        """Handle switching to a gaming preset."""
        try:
            # Find or create a profile with the specified preset
            profile_name = self._find_or_create_preset_profile(preset_name)
            
            if not profile_name:
                return {
                    'success': False,
                    'message': f'Could not find or create preset profile: {preset_name}',
                    'action': 'switch_to_preset'
                }
            
            success = self._switch_to_profile(profile_name)
            
            return {
                'success': success,
                'profile_name': profile_name,
                'preset_name': preset_name,
                'action': 'switch_to_preset'
            }
            
        except Exception as e:
            logger.error(f"Error handling switch to preset: {e}")
            return {
                'success': False,
                'message': f'Error switching to preset: {str(e)}',
                'action': 'switch_to_preset'
            }
    
    def _switch_to_profile(self, profile_name: str) -> bool:
        """Switch to a specific profile and provide feedback."""
        try:
            start_time = time.time()
            
            # Load the profile
            profile = self.profile_manager.load_profile(profile_name)
            if not profile:
                logger.error(f"Failed to load profile: {profile_name}")
                self._notify_feedback(ProfileSwitchFeedback(
                    profile_name=profile_name,
                    switch_time=time.time() - start_time,
                    success=False,
                    message=f"Failed to load profile: {profile_name}"
                ))
                return False
            
            # Apply the profile settings
            # This would integrate with the main application to apply settings
            # For now, we'll just log the action
            logger.info(f"Switching to profile: {profile_name}")
            
            # Update current profile index
            if profile_name in self.profile_list:
                self.current_profile_index = self.profile_list.index(profile_name)
            
            # Record switch time
            self.last_switch_time = time.time()
            
            # Create feedback
            feedback = ProfileSwitchFeedback(
                profile_name=profile_name,
                switch_time=time.time() - start_time,
                success=True,
                message=f"Switched to profile: {profile_name}",
                visual_feedback=self.config.visual_feedback_duration > 0,
                audio_feedback=self.config.audio_feedback
            )
            
            # Add to history
            self.switch_history.append(feedback)
            if len(self.switch_history) > 100:  # Keep last 100 switches
                self.switch_history.pop(0)
            
            # Notify feedback callbacks
            self._notify_feedback(feedback)
            
            logger.info(f"Successfully switched to profile: {profile_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error switching to profile {profile_name}: {e}")
            self._notify_feedback(ProfileSwitchFeedback(
                profile_name=profile_name,
                switch_time=time.time() - start_time,
                success=False,
                message=f"Error switching to profile: {str(e)}"
            ))
            return False
    
    def _find_or_create_preset_profile(self, preset_name: str) -> Optional[str]:
        """Find an existing profile with the specified preset or create one."""
        try:
            # First, try to find an existing profile with this preset
            for profile_name, profile in self.profile_manager.profiles.items():
                if (hasattr(profile, 'metadata') and 
                    hasattr(profile.metadata, 'gaming_mode') and
                    profile.metadata.gaming_mode.value.upper() == preset_name.upper()):
                    return profile_name
            
            # If not found, create a new profile with the preset
            # This would integrate with the gaming presets system
            logger.info(f"Creating new profile for preset: {preset_name}")
            
            # For now, return None - this would be implemented with actual preset creation
            return None
            
        except Exception as e:
            logger.error(f"Error finding/creating preset profile: {e}")
            return None
    
    def _update_profile_list(self):
        """Update the internal profile list."""
        try:
            self.profile_list = list(self.profile_manager.profiles.keys())
            logger.debug(f"Updated profile list: {self.profile_list}")
        except Exception as e:
            logger.error(f"Error updating profile list: {e}")
            self.profile_list = []
    
    def _notify_feedback(self, feedback: ProfileSwitchFeedback):
        """Notify all feedback callbacks."""
        for callback in self.feedback_callbacks:
            try:
                callback(feedback)
            except Exception as e:
                logger.error(f"Error in feedback callback: {e}")
    
    def add_feedback_callback(self, callback: Callable[[ProfileSwitchFeedback], None]):
        """Add a feedback callback for profile switching."""
        self.feedback_callbacks.append(callback)
        logger.info("Added profile switch feedback callback")
    
    def remove_feedback_callback(self, callback: Callable[[ProfileSwitchFeedback], None]):
        """Remove a feedback callback."""
        if callback in self.feedback_callbacks:
            self.feedback_callbacks.remove(callback)
            logger.info("Removed profile switch feedback callback")
    
    def get_current_profile(self) -> Optional[str]:
        """Get the currently active profile name."""
        if self.profile_list and 0 <= self.current_profile_index < len(self.profile_list):
            return self.profile_list[self.current_profile_index]
        return None
    
    def get_profile_list(self) -> List[str]:
        """Get the list of available profiles."""
        self._update_profile_list()
        return self.profile_list.copy()
    
    def get_switch_history(self, limit: Optional[int] = None) -> List[ProfileSwitchFeedback]:
        """Get the profile switch history."""
        if limit is None:
            return self.switch_history.copy()
        return self.switch_history[-limit:] if limit > 0 else []
    
    def clear_switch_history(self):
        """Clear the profile switch history."""
        self.switch_history.clear()
        logger.info("Cleared profile switch history")
    
    def update_config(self, new_config: ProfileHotkeyConfig):
        """Update the profile hotkey configuration."""
        self.config = new_config
        logger.info("Updated profile hotkey configuration")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get profile switching statistics."""
        total_switches = len(self.switch_history)
        successful_switches = sum(1 for feedback in self.switch_history if feedback.success)
        failed_switches = total_switches - successful_switches
        
        avg_switch_time = 0.0
        if successful_switches > 0:
            avg_switch_time = sum(f.switch_time for f in self.switch_history if f.success) / successful_switches
        
        return {
            'total_switches': total_switches,
            'successful_switches': successful_switches,
            'failed_switches': failed_switches,
            'success_rate': successful_switches / total_switches if total_switches > 0 else 0.0,
            'average_switch_time': avg_switch_time,
            'current_profile': self.get_current_profile(),
            'available_profiles': len(self.get_profile_list()),
            'last_switch_time': self.last_switch_time
        }
