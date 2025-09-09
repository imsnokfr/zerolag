"""
Hotkey Manager for ZeroLag

This module provides the main hotkey management system that coordinates
hotkey detection, action handling, and configuration management.

Features:
- Centralized hotkey management
- Action routing and handling
- Configuration persistence
- Conflict detection and resolution
- Performance monitoring
- Integration with ZeroLag components
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from .hotkey_detector import HotkeyDetector, HotkeyEvent, HotkeyModifier
from .hotkey_actions import HotkeyActions, HotkeyActionType
from .hotkey_config import HotkeyConfig, HotkeyBinding
from .hotkey_validator import HotkeyValidator

logger = logging.getLogger(__name__)

class HotkeyManagerState(Enum):
    """Hotkey manager states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"

@dataclass
class HotkeyManagerConfig:
    """Configuration for the Hotkey Manager."""
    enable_hotkeys: bool = True
    auto_start: bool = True
    conflict_resolution: str = "warn"  # "warn", "override", "ignore"
    log_hotkey_events: bool = False
    performance_monitoring: bool = True
    max_hotkeys: int = 50
    hotkey_timeout: float = 0.1  # seconds

@dataclass
class HotkeyManagerStats:
    """Statistics for the Hotkey Manager."""
    total_hotkeys_registered: int = 0
    total_hotkeys_unregistered: int = 0
    total_events_processed: int = 0
    total_conflicts_detected: int = 0
    total_errors_encountered: int = 0
    uptime_seconds: float = 0.0
    last_event_time: float = 0.0
    average_response_time: float = 0.0
    hotkeys_active: int = 0

class HotkeyManager:
    """
    Main hotkey management system for ZeroLag.
    
    This class coordinates hotkey detection, action handling, and
    configuration management for the entire hotkey system.
    """
    
    def __init__(self, config: Optional[HotkeyManagerConfig] = None):
        self.config = config or HotkeyManagerConfig()
        self.state = HotkeyManagerState.STOPPED
        
        # Core components
        self.detector = HotkeyDetector()
        self.actions = HotkeyActions()
        self.validator = HotkeyValidator()
        self.hotkey_config = HotkeyConfig()
        
        # Hotkey tracking
        self.hotkey_bindings: Dict[int, HotkeyBinding] = {}
        self.hotkey_callbacks: Dict[int, Callable] = {}  # hotkey_id -> callback
        self.action_callbacks: Dict[HotkeyActionType, Callable] = {}
        
        # Threading
        self.lock = threading.RLock()
        self.start_time = 0.0
        
        # Statistics
        self.stats = HotkeyManagerStats()
        
        # Event handlers
        self.event_handlers: List[Callable[[HotkeyEvent], None]] = []
        
        logger.info("HotkeyManager initialized")
    
    def start(self) -> bool:
        """Start the hotkey management system."""
        with self.lock:
            if self.state == HotkeyManagerState.RUNNING:
                logger.warning("HotkeyManager is already running")
                return True
            
            if not self.config.enable_hotkeys:
                logger.info("Hotkeys are disabled in configuration")
                return True
            
            try:
                self.state = HotkeyManagerState.STARTING
                logger.info("Starting HotkeyManager...")
                
                # Start hotkey detector
                if not self.detector.start():
                    logger.error("Failed to start hotkey detector")
                    self.state = HotkeyManagerState.ERROR
                    return False
                
                # Register default hotkeys
                self._register_default_hotkeys()
                
                # Set up action callbacks
                self._setup_action_callbacks()
                
                self.state = HotkeyManagerState.RUNNING
                self.start_time = time.time()
                logger.info("HotkeyManager started successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to start HotkeyManager: {e}")
                self.state = HotkeyManagerState.ERROR
                return False
    
    def stop(self) -> bool:
        """Stop the hotkey management system."""
        with self.lock:
            if self.state == HotkeyManagerState.STOPPED:
                logger.warning("HotkeyManager is already stopped")
                return True
            
            try:
                self.state = HotkeyManagerState.STOPPING
                logger.info("Stopping HotkeyManager...")
                
                # Stop hotkey detector
                if not self.detector.stop():
                    logger.warning("Failed to stop hotkey detector cleanly")
                
                # Clear hotkey bindings
                self.hotkey_bindings.clear()
                
                self.state = HotkeyManagerState.STOPPED
                logger.info("HotkeyManager stopped successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to stop HotkeyManager: {e}")
                self.state = HotkeyManagerState.ERROR
                return False
    
    def register_hotkey(self, action_type: HotkeyActionType, modifiers: HotkeyModifier, 
                       virtual_key: int, callback: Optional[Callable] = None) -> Optional[int]:
        """
        Register a hotkey for a specific action.
        
        Args:
            action_type: Type of action to perform
            modifiers: Modifier keys
            virtual_key: Virtual key code
            callback: Optional custom callback function
            
        Returns:
            Hotkey ID if successful, None if failed
        """
        with self.lock:
            try:
                # Validate hotkey combination
                if not self.validator.validate_hotkey_combination(modifiers, virtual_key):
                    logger.error(f"Invalid hotkey combination: {modifiers} + {virtual_key}")
                    return None
                
                # Check for conflicts
                conflict = self.validator.check_conflict(modifiers, virtual_key, self.hotkey_bindings)
                if conflict:
                    if self.config.conflict_resolution == "warn":
                        logger.warning(f"Hotkey conflict detected: {conflict}")
                        return None
                    elif self.config.conflict_resolution == "override":
                        logger.info(f"Overriding conflicting hotkey: {conflict}")
                        self._unregister_conflicting_hotkey(conflict)
                
                # Register with detector
                hotkey_id = self.detector.register_hotkey(modifiers, virtual_key, self._handle_hotkey_event)
                if hotkey_id is None:
                    logger.error(f"Failed to register hotkey with detector: {modifiers} + {virtual_key}")
                    return None
                
                # Create hotkey binding
                binding = HotkeyBinding(
                    hotkey_id=hotkey_id,
                    action_type=action_type,
                    modifiers=modifiers,
                    virtual_key=virtual_key,
                    key_name=self.detector.get_key_name(virtual_key),
                    description=f"Hotkey for {action_type.value}",
                    created_at=time.time()
                )
                
                self.hotkey_bindings[hotkey_id] = binding
                if callback:
                    self.hotkey_callbacks[hotkey_id] = callback
                self.stats.total_hotkeys_registered += 1
                self.stats.hotkeys_active = len(self.hotkey_bindings)
                
                logger.info(f"Registered hotkey {hotkey_id}: {action_type} -> {modifiers} + {virtual_key}")
                return hotkey_id
                
            except Exception as e:
                logger.error(f"Error registering hotkey: {e}")
                self.stats.total_errors_encountered += 1
                return None
    
    def unregister_hotkey(self, hotkey_id: int) -> bool:
        """
        Unregister a hotkey.
        
        Args:
            hotkey_id: ID of the hotkey to unregister
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            try:
                if hotkey_id not in self.hotkey_bindings:
                    logger.warning(f"Hotkey {hotkey_id} is not registered")
                    return False
                
                # Unregister from detector
                if not self.detector.unregister_hotkey(hotkey_id):
                    logger.warning(f"Failed to unregister hotkey {hotkey_id} from detector")
                
                # Remove from bindings and callbacks
                del self.hotkey_bindings[hotkey_id]
                if hotkey_id in self.hotkey_callbacks:
                    del self.hotkey_callbacks[hotkey_id]
                self.stats.total_hotkeys_unregistered += 1
                self.stats.hotkeys_active = len(self.hotkey_bindings)
                
                logger.info(f"Unregistered hotkey {hotkey_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error unregistering hotkey {hotkey_id}: {e}")
                self.stats.total_errors_encountered += 1
                return False
    
    def unregister_all_hotkeys(self) -> int:
        """
        Unregister all hotkeys.
        
        Returns:
            Number of hotkeys unregistered
        """
        with self.lock:
            unregistered_count = 0
            hotkey_ids = list(self.hotkey_bindings.keys())
            
            for hotkey_id in hotkey_ids:
                if self.unregister_hotkey(hotkey_id):
                    unregistered_count += 1
            
            logger.info(f"Unregistered {unregistered_count} hotkeys")
            return unregistered_count
    
    def _handle_hotkey_event(self, event: HotkeyEvent):
        """Handle a hotkey event from the detector."""
        try:
            start_time = time.time()
            
            if self.config.log_hotkey_events:
                logger.info(f"Hotkey event: {event}")
            
            # Find the binding for this hotkey
            if event.hotkey_id in self.hotkey_bindings:
                binding = self.hotkey_bindings[event.hotkey_id]
                
                # Execute the action
                if event.hotkey_id in self.hotkey_callbacks:
                    # Use custom callback
                    self.hotkey_callbacks[event.hotkey_id](event)
                else:
                    # Use default action handler
                    self.actions.execute_action(binding.action_type, event)
                
                # Update statistics
                self.stats.total_events_processed += 1
                self.stats.last_event_time = time.time()
                
                # Calculate response time
                response_time = time.time() - start_time
                if self.config.performance_monitoring:
                    self._update_average_response_time(response_time)
                
                # Notify event handlers
                for handler in self.event_handlers:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in hotkey event handler: {e}")
            else:
                logger.warning(f"Received event for unregistered hotkey: {event.hotkey_id}")
                
        except Exception as e:
            logger.error(f"Error handling hotkey event: {e}")
            self.stats.total_errors_encountered += 1
    
    def _update_average_response_time(self, response_time: float):
        """Update the average response time statistic."""
        if self.stats.total_events_processed == 1:
            self.stats.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.stats.average_response_time = (
                alpha * response_time + 
                (1 - alpha) * self.stats.average_response_time
            )
    
    def _register_default_hotkeys(self):
        """Register default hotkeys for common actions."""
        try:
            # Profile switching hotkeys
            self.register_hotkey(
                HotkeyActionType.CYCLE_PROFILE,
                HotkeyModifier.CTRL | HotkeyModifier.ALT,
                self.detector.get_virtual_key_code('P')
            )
            
            # DPI adjustment hotkeys
            self.register_hotkey(
                HotkeyActionType.INCREASE_DPI,
                HotkeyModifier.CTRL | HotkeyModifier.ALT,
                self.detector.get_virtual_key_code('UP')
            )
            
            self.register_hotkey(
                HotkeyActionType.DECREASE_DPI,
                HotkeyModifier.CTRL | HotkeyModifier.ALT,
                self.detector.get_virtual_key_code('DOWN')
            )
            
            # Emergency hotkeys
            self.register_hotkey(
                HotkeyActionType.EMERGENCY_STOP,
                HotkeyModifier.CTRL | HotkeyModifier.ALT,
                46  # VK_DELETE
            )
            
            self.register_hotkey(
                HotkeyActionType.TOGGLE_ZEROLAG,
                HotkeyModifier.CTRL | HotkeyModifier.ALT,
                self.detector.get_virtual_key_code('Z')
            )
            
            logger.info("Default hotkeys registered")
            
        except Exception as e:
            logger.error(f"Error registering default hotkeys: {e}")
    
    def _setup_action_callbacks(self):
        """Set up action callbacks for hotkey actions."""
        # This will be implemented when we create the action handlers
        pass
    
    def _unregister_conflicting_hotkey(self, conflict_info):
        """Unregister a conflicting hotkey."""
        # Implementation for conflict resolution
        pass
    
    def add_event_handler(self, handler: Callable[[HotkeyEvent], None]):
        """Add a hotkey event handler."""
        with self.lock:
            self.event_handlers.append(handler)
    
    def remove_event_handler(self, handler: Callable[[HotkeyEvent], None]):
        """Remove a hotkey event handler."""
        with self.lock:
            if handler in self.event_handlers:
                self.event_handlers.remove(handler)
    
    def get_stats(self) -> HotkeyManagerStats:
        """Get hotkey manager statistics."""
        with self.lock:
            # Update uptime
            if self.state == HotkeyManagerState.RUNNING:
                self.stats.uptime_seconds = time.time() - self.start_time
            
            # Merge detector stats
            detector_stats = self.detector.get_stats()
            self.stats.total_conflicts_detected = detector_stats.get('conflicts_detected', 0)
            self.stats.total_errors_encountered += detector_stats.get('errors_encountered', 0)
            
            return self.stats
    
    def is_running(self) -> bool:
        """Check if the hotkey manager is running."""
        with self.lock:
            return self.state == HotkeyManagerState.RUNNING
    
    def get_hotkey_bindings(self) -> Dict[int, HotkeyBinding]:
        """Get all hotkey bindings."""
        with self.lock:
            return self.hotkey_bindings.copy()
    
    def get_hotkey_by_action(self, action_type: HotkeyActionType) -> Optional[HotkeyBinding]:
        """Get hotkey binding for a specific action type."""
        with self.lock:
            for binding in self.hotkey_bindings.values():
                if binding.action_type == action_type:
                    return binding
            return None
    
    def update_config(self, new_config: HotkeyManagerConfig):
        """Update hotkey manager configuration."""
        with self.lock:
            self.config = new_config
            logger.info("HotkeyManager configuration updated")
    
    def load_hotkey_config(self, config_path: str) -> bool:
        """Load hotkey configuration from file."""
        try:
            # This will be implemented when we create the config system
            logger.info(f"Loading hotkey configuration from {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading hotkey configuration: {e}")
            return False
    
    def save_hotkey_config(self, config_path: str) -> bool:
        """Save hotkey configuration to file."""
        try:
            # This will be implemented when we create the config system
            logger.info(f"Saving hotkey configuration to {config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving hotkey configuration: {e}")
            return False
