"""
Emergency Hotkey Integration for ZeroLag

This module integrates the emergency hotkey system with the main ZeroLag
application, providing seamless emergency functionality across all components.

Features:
- Integration with HotkeyManager
- Component lifecycle management
- Emergency state monitoring
- GUI integration for emergency controls
- Recovery management
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .emergency_hotkeys import EmergencyHotkeyManager, EmergencyConfig, EmergencyState
from .hotkey_manager import HotkeyManager
from .hotkey_detector import HotkeyEvent
from .hotkey_actions import HotkeyActionType, ActionResult

logger = logging.getLogger(__name__)

@dataclass
class EmergencyIntegrationConfig:
    """Configuration for emergency hotkey integration."""
    # Integration settings
    auto_register_emergency_hotkeys: bool = True
    enable_emergency_monitoring: bool = True
    emergency_check_interval: float = 1.0
    
    # Recovery settings
    auto_recovery_enabled: bool = True
    recovery_attempts: int = 3
    recovery_delay: float = 5.0
    
    # Notification settings
    show_emergency_notifications: bool = True
    log_emergency_events: bool = True

class EmergencyIntegration:
    """
    Integrates emergency hotkey functionality with ZeroLag components.
    
    This class manages the integration between emergency hotkeys and the
    main ZeroLag application, providing seamless emergency functionality.
    """
    
    def __init__(self, config: Optional[EmergencyIntegrationConfig] = None):
        self.config = config or EmergencyIntegrationConfig()
        
        # Initialize emergency manager
        emergency_config = EmergencyConfig()
        self.emergency_manager = EmergencyHotkeyManager(emergency_config)
        
        # Component references
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.input_handler = None
        self.dpi_emulator = None
        self.polling_manager = None
        self.keyboard_handler = None
        self.mouse_handler = None
        self.macro_manager = None
        self.profile_manager = None
        
        # Integration state
        self.is_integrated = False
        self.emergency_hotkeys_registered = False
        self.monitoring_active = False
        
        logger.info("EmergencyIntegration initialized")
    
    def integrate_with_hotkey_manager(self, hotkey_manager: HotkeyManager):
        """Integrate with the main hotkey manager."""
        self.hotkey_manager = hotkey_manager
        
        if self.config.auto_register_emergency_hotkeys:
            self._register_emergency_hotkeys()
        
        logger.info("Emergency integration connected to hotkey manager")
    
    def set_components(self, input_handler=None, dpi_emulator=None, 
                      polling_manager=None, keyboard_handler=None,
                      mouse_handler=None, macro_manager=None, profile_manager=None):
        """Set references to ZeroLag components."""
        self.input_handler = input_handler
        self.dpi_emulator = dpi_emulator
        self.polling_manager = polling_manager
        self.keyboard_handler = keyboard_handler
        self.mouse_handler = mouse_handler
        self.macro_manager = macro_manager
        self.profile_manager = profile_manager
        
        # Set components in emergency manager
        self.emergency_manager.set_components(
            input_handler=input_handler,
            dpi_emulator=dpi_emulator,
            polling_manager=polling_manager,
            keyboard_handler=keyboard_handler,
            mouse_handler=mouse_handler,
            macro_manager=macro_manager,
            profile_manager=profile_manager
        )
        
        logger.info("Emergency components set")
    
    def _register_emergency_hotkeys(self):
        """Register emergency hotkeys with the hotkey manager."""
        if not self.hotkey_manager:
            logger.warning("Cannot register emergency hotkeys - no hotkey manager")
            return
        
        try:
            # Register emergency stop hotkey
            self.hotkey_manager.register_hotkey(
                hotkey_id="emergency_stop",
                modifiers=["ctrl", "alt", "shift"],
                virtual_key=27,  # Escape key
                callback=self._handle_emergency_stop
            )
            
            # Register emergency reset hotkey
            self.hotkey_manager.register_hotkey(
                hotkey_id="emergency_reset",
                modifiers=["ctrl", "alt", "shift"],
                virtual_key=82,  # R key
                callback=self._handle_emergency_reset
            )
            
            # Register emergency disable hotkey
            self.hotkey_manager.register_hotkey(
                hotkey_id="emergency_disable",
                modifiers=["ctrl", "alt", "shift"],
                virtual_key=68,  # D key
                callback=self._handle_emergency_disable
            )
            
            self.emergency_hotkeys_registered = True
            logger.info("Emergency hotkeys registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to register emergency hotkeys: {e}")
    
    def _handle_emergency_stop(self, event: HotkeyEvent):
        """Handle emergency stop hotkey."""
        logger.critical("Emergency stop hotkey triggered")
        result = self.emergency_manager.handle_emergency_stop(event)
        self._log_emergency_result("emergency_stop", result)
        return result
    
    def _handle_emergency_reset(self, event: HotkeyEvent):
        """Handle emergency reset hotkey."""
        logger.critical("Emergency reset hotkey triggered")
        result = self.emergency_manager.handle_emergency_reset(event)
        self._log_emergency_result("emergency_reset", result)
        return result
    
    def _handle_emergency_disable(self, event: HotkeyEvent):
        """Handle emergency disable hotkey."""
        logger.critical("Emergency disable hotkey triggered")
        result = self.emergency_manager.handle_emergency_disable_all(event)
        self._log_emergency_result("emergency_disable", result)
        return result
    
    def _log_emergency_result(self, action_type: str, result: ActionResult):
        """Log emergency action result."""
        if self.config.log_emergency_events:
            if result.success:
                logger.critical(f"Emergency {action_type} successful: {result.message}")
            else:
                logger.error(f"Emergency {action_type} failed: {result.message}")
    
    def start_emergency_monitoring(self):
        """Start monitoring for emergency states."""
        if not self.config.enable_emergency_monitoring:
            return
        
        self.monitoring_active = True
        logger.info("Emergency monitoring started")
    
    def stop_emergency_monitoring(self):
        """Stop monitoring for emergency states."""
        self.monitoring_active = False
        logger.info("Emergency monitoring stopped")
    
    def check_emergency_state(self) -> EmergencyState:
        """Check current emergency state."""
        return self.emergency_manager.get_current_state()
    
    def is_emergency_active(self) -> bool:
        """Check if emergency state is active."""
        return self.emergency_manager.is_emergency_state()
    
    def force_recovery(self):
        """Force recovery from emergency state."""
        logger.info("Forcing emergency recovery")
        self.emergency_manager.force_recovery()
    
    def get_emergency_stats(self):
        """Get emergency statistics."""
        return self.emergency_manager.get_emergency_stats()
    
    def get_emergency_history(self, limit: Optional[int] = None):
        """Get emergency action history."""
        return self.emergency_manager.get_emergency_history(limit)
    
    def update_emergency_config(self, new_config: EmergencyConfig):
        """Update emergency configuration."""
        self.emergency_manager.update_config(new_config)
        logger.info("Emergency configuration updated")
    
    def register_emergency_callback(self, event_type: str, callback):
        """Register emergency callback."""
        self.emergency_manager.register_emergency_callback(event_type, callback)
    
    def unregister_emergency_callback(self, event_type: str, callback):
        """Unregister emergency callback."""
        self.emergency_manager.unregister_emergency_callback(event_type, callback)
    
    def create_emergency_profile(self) -> Dict[str, Any]:
        """Create a safe emergency profile."""
        return {
            "name": "Emergency Safe",
            "description": "Safe emergency profile with minimal optimizations",
            "dpi_settings": {
                "enabled": False,
                "dpi": 800,
                "mode": "software",
                "smoothing": False,
                "precision_mode": False
            },
            "polling_settings": {
                "mouse_rate": 125,
                "keyboard_rate": 125,
                "mode": "fixed"
            },
            "keyboard_settings": {
                "nkro_mode": "off",
                "rapid_trigger": "off",
                "debounce_time": 0
            },
            "smoothing_settings": {
                "enabled": False,
                "algorithm": "none",
                "strength": 0.0
            },
            "macro_settings": {
                "enabled": False
            },
            "performance_settings": {
                "monitoring_enabled": False,
                "memory_optimization": False
            }
        }
    
    def get_emergency_status(self) -> Dict[str, Any]:
        """Get comprehensive emergency status."""
        stats = self.get_emergency_stats()
        current_state = self.check_emergency_state()
        
        return {
            "current_state": current_state.value,
            "is_emergency_active": self.is_emergency_active(),
            "total_emergency_actions": stats.total_emergency_actions,
            "emergency_stops": stats.emergency_stops,
            "emergency_resets": stats.emergency_resets,
            "emergency_disables": stats.emergency_disables,
            "successful_recoveries": stats.successful_recoveries,
            "failed_recoveries": stats.failed_recoveries,
            "last_emergency_time": stats.last_emergency_time,
            "monitoring_active": self.monitoring_active,
            "hotkeys_registered": self.emergency_hotkeys_registered
        }
    
    def cleanup(self):
        """Cleanup emergency integration."""
        self.stop_emergency_monitoring()
        
        if self.hotkey_manager and self.emergency_hotkeys_registered:
            try:
                self.hotkey_manager.unregister_hotkey("emergency_stop")
                self.hotkey_manager.unregister_hotkey("emergency_reset")
                self.hotkey_manager.unregister_hotkey("emergency_disable")
                logger.info("Emergency hotkeys unregistered")
            except Exception as e:
                logger.error(f"Error unregistering emergency hotkeys: {e}")
        
        logger.info("Emergency integration cleaned up")
