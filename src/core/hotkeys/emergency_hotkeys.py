"""
Emergency Hotkeys for ZeroLag

This module provides emergency hotkey functionality for critical system operations.
It includes emergency stop, reset, and disable all functions with proper
integration to ZeroLag components and safety mechanisms.

Features:
- Emergency stop all input processing
- Emergency reset to safe defaults
- Emergency disable all optimizations
- Safety confirmation mechanisms
- Integration with ZeroLag components
- Emergency logging and notifications
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from .hotkey_detector import HotkeyEvent, HotkeyModifier
from .hotkey_actions import HotkeyActionType, ActionContext, ActionResult

logger = logging.getLogger(__name__)

class EmergencyLevel(Enum):
    """Emergency action severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class EmergencyState(Enum):
    """Current emergency state of the system."""
    NORMAL = "normal"
    EMERGENCY_STOP = "emergency_stop"
    EMERGENCY_RESET = "emergency_reset"
    EMERGENCY_DISABLED = "emergency_disabled"

@dataclass
class EmergencyConfig:
    """Configuration for emergency hotkey system."""
    # Emergency hotkey bindings
    emergency_stop_hotkey: str = "Ctrl+Alt+Shift+Escape"
    emergency_reset_hotkey: str = "Ctrl+Alt+Shift+R"
    emergency_disable_hotkey: str = "Ctrl+Alt+Shift+D"
    
    # Safety settings
    require_confirmation: bool = True
    confirmation_timeout: float = 5.0
    max_emergency_actions: int = 3
    cooldown_period: float = 10.0
    
    # Notification settings
    show_notifications: bool = True
    log_emergency_actions: bool = True
    emergency_sound: bool = True
    
    # Recovery settings
    auto_recovery_enabled: bool = True
    recovery_delay: float = 30.0
    safe_mode_fallback: bool = True

@dataclass
class EmergencyEvent:
    """Record of an emergency action."""
    event_type: str
    timestamp: float
    hotkey: str
    level: EmergencyLevel
    success: bool
    message: str
    recovery_time: Optional[float] = None

@dataclass
class EmergencyStats:
    """Statistics for emergency actions."""
    total_emergency_actions: int = 0
    emergency_stops: int = 0
    emergency_resets: int = 0
    emergency_disables: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    last_emergency_time: Optional[float] = None
    average_recovery_time: float = 0.0

class EmergencyHotkeyManager:
    """
    Manages emergency hotkey functionality for ZeroLag.
    
    This class provides critical emergency operations including stop, reset,
    and disable all functions with proper safety mechanisms and recovery.
    """
    
    def __init__(self, config: Optional[EmergencyConfig] = None):
        self.config = config or EmergencyConfig()
        self.current_state = EmergencyState.NORMAL
        self.emergency_history: List[EmergencyEvent] = []
        self.stats = EmergencyStats()
        self.recovery_timer: Optional[threading.Timer] = None
        self.confirmation_timer: Optional[threading.Timer] = None
        self.pending_action: Optional[str] = None
        
        # Component references (will be set by integration)
        self.input_handler = None
        self.dpi_emulator = None
        self.polling_manager = None
        self.keyboard_handler = None
        self.mouse_handler = None
        self.macro_manager = None
        self.profile_manager = None
        
        # Callbacks for external integration
        self.emergency_callbacks: Dict[str, List[Callable]] = {
            "emergency_stop": [],
            "emergency_reset": [],
            "emergency_disable": [],
            "recovery_start": [],
            "recovery_complete": []
        }
        
        logger.info("EmergencyHotkeyManager initialized")
    
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
        logger.info("Emergency components set")
    
    def register_emergency_callback(self, event_type: str, callback: Callable):
        """Register a callback for emergency events."""
        if event_type in self.emergency_callbacks:
            self.emergency_callbacks[event_type].append(callback)
            logger.info(f"Registered emergency callback for {event_type}")
    
    def unregister_emergency_callback(self, event_type: str, callback: Callable):
        """Unregister an emergency callback."""
        if event_type in self.emergency_callbacks and callback in self.emergency_callbacks[event_type]:
            self.emergency_callbacks[event_type].remove(callback)
            logger.info(f"Unregistered emergency callback for {event_type}")
    
    def handle_emergency_stop(self, event: HotkeyEvent) -> ActionResult:
        """Handle emergency stop action."""
        logger.critical("EMERGENCY STOP triggered")
        
        if self.config.require_confirmation and not self._confirm_emergency_action("EMERGENCY STOP"):
            return ActionResult(
                success=False,
                message="Emergency stop cancelled - confirmation required"
            )
        
        try:
            # Stop all input processing
            if self.input_handler:
                self.input_handler.stop()
            
            # Stop polling
            if self.polling_manager:
                self.polling_manager.stop()
            
            # Stop macro recording/playback
            if self.macro_manager:
                self.macro_manager.stop_all_macros()
            
            # Set emergency state
            self.current_state = EmergencyState.EMERGENCY_STOP
            
            # Record emergency event
            emergency_event = EmergencyEvent(
                event_type="emergency_stop",
                timestamp=time.time(),
                hotkey=self.config.emergency_stop_hotkey,
                level=EmergencyLevel.CRITICAL,
                success=True,
                message="All input processing stopped"
            )
            self._record_emergency_event(emergency_event)
            
            # Notify callbacks
            self._notify_callbacks("emergency_stop", emergency_event)
            
            # Start recovery timer if enabled
            if self.config.auto_recovery_enabled:
                self._start_recovery_timer()
            
            return ActionResult(
                success=True,
                message="Emergency stop executed - all input processing halted",
                data={"state": self.current_state.value}
            )
            
        except Exception as e:
            logger.error(f"Error during emergency stop: {e}")
            return ActionResult(
                success=False,
                message=f"Emergency stop failed: {str(e)}"
            )
    
    def handle_emergency_reset(self, event: HotkeyEvent) -> ActionResult:
        """Handle emergency reset action."""
        logger.critical("EMERGENCY RESET triggered")
        
        if self.config.require_confirmation and not self._confirm_emergency_action("EMERGENCY RESET"):
            return ActionResult(
                success=False,
                message="Emergency reset cancelled - confirmation required"
            )
        
        try:
            # Reset all components to safe defaults
            self._reset_to_safe_defaults()
            
            # Set emergency state
            self.current_state = EmergencyState.EMERGENCY_RESET
            
            # Record emergency event
            emergency_event = EmergencyEvent(
                event_type="emergency_reset",
                timestamp=time.time(),
                hotkey=self.config.emergency_reset_hotkey,
                level=EmergencyLevel.HIGH,
                success=True,
                message="System reset to safe defaults"
            )
            self._record_emergency_event(emergency_event)
            
            # Notify callbacks
            self._notify_callbacks("emergency_reset", emergency_event)
            
            # Start recovery timer if enabled
            if self.config.auto_recovery_enabled:
                self._start_recovery_timer()
            
            return ActionResult(
                success=True,
                message="Emergency reset executed - system restored to safe defaults",
                data={"state": self.current_state.value}
            )
            
        except Exception as e:
            logger.error(f"Error during emergency reset: {e}")
            return ActionResult(
                success=False,
                message=f"Emergency reset failed: {str(e)}"
            )
    
    def handle_emergency_disable_all(self, event: HotkeyEvent) -> ActionResult:
        """Handle emergency disable all action."""
        logger.critical("EMERGENCY DISABLE ALL triggered")
        
        if self.config.require_confirmation and not self._confirm_emergency_action("EMERGENCY DISABLE ALL"):
            return ActionResult(
                success=False,
                message="Emergency disable cancelled - confirmation required"
            )
        
        try:
            # Disable all optimizations
            self._disable_all_optimizations()
            
            # Set emergency state
            self.current_state = EmergencyState.EMERGENCY_DISABLED
            
            # Record emergency event
            emergency_event = EmergencyEvent(
                event_type="emergency_disable",
                timestamp=time.time(),
                hotkey=self.config.emergency_disable_hotkey,
                level=EmergencyLevel.HIGH,
                success=True,
                message="All optimizations disabled"
            )
            self._record_emergency_event(emergency_event)
            
            # Notify callbacks
            self._notify_callbacks("emergency_disable", emergency_event)
            
            # Start recovery timer if enabled
            if self.config.auto_recovery_enabled:
                self._start_recovery_timer()
            
            return ActionResult(
                success=True,
                message="Emergency disable executed - all optimizations turned off",
                data={"state": self.current_state.value}
            )
            
        except Exception as e:
            logger.error(f"Error during emergency disable: {e}")
            return ActionResult(
                success=False,
                message=f"Emergency disable failed: {str(e)}"
            )
    
    def _confirm_emergency_action(self, action_name: str) -> bool:
        """Handle emergency action confirmation."""
        if not self.config.require_confirmation:
            return True
        
        logger.warning(f"Emergency action {action_name} requires confirmation")
        self.pending_action = action_name
        
        # Start confirmation timeout
        self.confirmation_timer = threading.Timer(
            self.config.confirmation_timeout,
            self._confirmation_timeout
        )
        self.confirmation_timer.start()
        
        # In a real implementation, this would show a GUI confirmation dialog
        # For now, we'll simulate confirmation after a short delay
        time.sleep(0.1)  # Simulate user confirmation
        
        if self.confirmation_timer:
            self.confirmation_timer.cancel()
            self.confirmation_timer = None
        
        self.pending_action = None
        return True
    
    def _confirmation_timeout(self):
        """Handle confirmation timeout."""
        logger.warning("Emergency action confirmation timed out")
        self.pending_action = None
        if self.confirmation_timer:
            self.confirmation_timer = None
    
    def _reset_to_safe_defaults(self):
        """Reset all components to safe default values."""
        logger.info("Resetting to safe defaults")
        
        # Reset DPI to safe value
        if self.dpi_emulator:
            self.dpi_emulator.set_dpi(800)  # Safe DPI value
            self.dpi_emulator.set_mode("software")
            self.dpi_emulator.set_smoothing(False)
            self.dpi_emulator.set_precision_mode(False)
        
        # Reset polling rates to safe values
        if self.polling_manager:
            self.polling_manager.set_mouse_polling_rate(125)  # Safe polling rate
            self.polling_manager.set_keyboard_polling_rate(125)
            self.polling_manager.set_polling_mode("adaptive")
        
        # Reset keyboard settings
        if self.keyboard_handler:
            self.keyboard_handler.set_nkro_mode("off")
            self.keyboard_handler.set_rapid_trigger_mode("off")
            self.keyboard_handler.set_debounce_time(0)
        
        # Reset mouse settings
        if self.mouse_handler:
            self.mouse_handler.set_smoothing_enabled(False)
            self.mouse_handler.set_acceleration_enabled(False)
        
        # Stop all macros
        if self.macro_manager:
            self.macro_manager.stop_all_macros()
        
        # Load safe profile if available
        if self.profile_manager:
            safe_profiles = self.profile_manager.get_profiles_by_type("safe")
            if safe_profiles:
                self.profile_manager.load_profile(safe_profiles[0].name)
    
    def _disable_all_optimizations(self):
        """Disable all ZeroLag optimizations."""
        logger.info("Disabling all optimizations")
        
        # Disable DPI emulation
        if self.dpi_emulator:
            self.dpi_emulator.set_enabled(False)
        
        # Disable polling optimizations
        if self.polling_manager:
            self.polling_manager.set_polling_mode("fixed")
            self.polling_manager.set_mouse_polling_rate(125)
            self.polling_manager.set_keyboard_polling_rate(125)
        
        # Disable keyboard optimizations
        if self.keyboard_handler:
            self.keyboard_handler.set_nkro_mode("off")
            self.keyboard_handler.set_rapid_trigger_mode("off")
            self.keyboard_handler.set_debounce_time(0)
        
        # Disable mouse optimizations
        if self.mouse_handler:
            self.mouse_handler.set_smoothing_enabled(False)
            self.mouse_handler.set_acceleration_enabled(False)
        
        # Disable macro system
        if self.macro_manager:
            self.macro_manager.set_enabled(False)
    
    def _start_recovery_timer(self):
        """Start automatic recovery timer."""
        if self.recovery_timer:
            self.recovery_timer.cancel()
        
        self.recovery_timer = threading.Timer(
            self.config.recovery_delay,
            self._attempt_recovery
        )
        self.recovery_timer.start()
        logger.info(f"Recovery timer started - {self.config.recovery_delay}s")
    
    def _attempt_recovery(self):
        """Attempt to recover from emergency state."""
        logger.info("Attempting emergency recovery")
        
        try:
            # Notify recovery start
            self._notify_callbacks("recovery_start", None)
            
            # Restart input processing
            if self.input_handler:
                self.input_handler.start()
            
            # Restart polling
            if self.polling_manager:
                self.polling_manager.start()
            
            # Re-enable optimizations
            if self.dpi_emulator:
                self.dpi_emulator.set_enabled(True)
            
            if self.macro_manager:
                self.macro_manager.set_enabled(True)
            
            # Reset state
            self.current_state = EmergencyState.NORMAL
            
            # Update stats
            self.stats.successful_recoveries += 1
            
            # Notify recovery complete
            self._notify_callbacks("recovery_complete", None)
            
            logger.info("Emergency recovery successful")
            
        except Exception as e:
            logger.error(f"Emergency recovery failed: {e}")
            self.stats.failed_recoveries += 1
    
    def _record_emergency_event(self, event: EmergencyEvent):
        """Record an emergency event."""
        self.emergency_history.append(event)
        
        # Update stats
        self.stats.total_emergency_actions += 1
        self.stats.last_emergency_time = event.timestamp
        
        if event.event_type == "emergency_stop":
            self.stats.emergency_stops += 1
        elif event.event_type == "emergency_reset":
            self.stats.emergency_resets += 1
        elif event.event_type == "emergency_disable":
            self.stats.emergency_disables += 1
        
        # Log emergency action
        if self.config.log_emergency_actions:
            logger.critical(f"Emergency event recorded: {event.event_type} - {event.message}")
    
    def _notify_callbacks(self, event_type: str, data: Any):
        """Notify registered callbacks of emergency events."""
        if event_type in self.emergency_callbacks:
            for callback in self.emergency_callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in emergency callback: {e}")
    
    def get_emergency_stats(self) -> EmergencyStats:
        """Get emergency action statistics."""
        return self.stats
    
    def get_emergency_history(self, limit: Optional[int] = None) -> List[EmergencyEvent]:
        """Get emergency action history."""
        if limit is None:
            return self.emergency_history.copy()
        return self.emergency_history[-limit:] if limit > 0 else []
    
    def clear_emergency_history(self):
        """Clear emergency action history."""
        self.emergency_history.clear()
        logger.info("Emergency history cleared")
    
    def is_emergency_state(self) -> bool:
        """Check if system is in emergency state."""
        return self.current_state != EmergencyState.NORMAL
    
    def get_current_state(self) -> EmergencyState:
        """Get current emergency state."""
        return self.current_state
    
    def force_recovery(self):
        """Force immediate recovery from emergency state."""
        logger.info("Forcing emergency recovery")
        if self.recovery_timer:
            self.recovery_timer.cancel()
            self.recovery_timer = None
        self._attempt_recovery()
    
    def update_config(self, new_config: EmergencyConfig):
        """Update emergency configuration."""
        self.config = new_config
        logger.info("Emergency configuration updated")
