"""
Hotkey Actions for ZeroLag

This module defines the actions that can be performed when hotkeys are pressed.
It provides a centralized way to handle hotkey-triggered actions throughout
the ZeroLag application.

Features:
- Action type definitions
- Action execution engine
- Integration with ZeroLag components
- Action logging and monitoring
- Custom action support
"""

import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum

from .hotkey_detector import HotkeyEvent

logger = logging.getLogger(__name__)

class HotkeyActionType(Enum):
    """Types of actions that can be triggered by hotkeys."""
    # Profile Management
    CYCLE_PROFILE = "cycle_profile"
    NEXT_PROFILE = "next_profile"
    PREVIOUS_PROFILE = "previous_profile"
    SWITCH_TO_PROFILE = "switch_to_profile"
    SAVE_CURRENT_PROFILE = "save_current_profile"
    LOAD_PROFILE = "load_profile"
    
    # DPI Management
    INCREASE_DPI = "increase_dpi"
    DECREASE_DPI = "decrease_dpi"
    RESET_DPI = "reset_dpi"
    SET_DPI = "set_dpi"
    TOGGLE_DPI_MODE = "toggle_dpi_mode"
    
    # Polling Rate Management
    INCREASE_POLLING_RATE = "increase_polling_rate"
    DECREASE_POLLING_RATE = "decrease_polling_rate"
    RESET_POLLING_RATE = "reset_polling_rate"
    SET_POLLING_RATE = "set_polling_rate"
    
    # Keyboard Optimizations
    TOGGLE_NKRO = "toggle_nkro"
    TOGGLE_RAPID_TRIGGER = "toggle_rapid_trigger"
    TOGGLE_DEBOUNCE = "toggle_debounce"
    ADJUST_DEBOUNCE_TIME = "adjust_debounce_time"
    
    # Smoothing Controls
    TOGGLE_SMOOTHING = "toggle_smoothing"
    INCREASE_SMOOTHING = "increase_smoothing"
    DECREASE_SMOOTHING = "decrease_smoothing"
    CHANGE_SMOOTHING_ALGORITHM = "change_smoothing_algorithm"
    
    # Macro Controls
    START_MACRO_RECORDING = "start_macro_recording"
    STOP_MACRO_RECORDING = "stop_macro_recording"
    PLAY_MACRO = "play_macro"
    PAUSE_MACRO = "pause_macro"
    STOP_MACRO = "stop_macro"
    
    # Performance Controls
    TOGGLE_PERFORMANCE_MONITORING = "toggle_performance_monitoring"
    TOGGLE_MEMORY_OPTIMIZATION = "toggle_memory_optimization"
    RESET_PERFORMANCE_STATS = "reset_performance_stats"
    
    # Application Controls
    TOGGLE_ZEROLAG = "toggle_zerolag"
    SHOW_GUI = "show_gui"
    HIDE_GUI = "hide_gui"
    MINIMIZE_TO_TRAY = "minimize_to_tray"
    QUIT_APPLICATION = "quit_application"
    
    # Emergency Controls
    EMERGENCY_STOP = "emergency_stop"
    EMERGENCY_RESET = "emergency_reset"
    EMERGENCY_DISABLE_ALL = "emergency_disable_all"
    
    # Custom Actions
    CUSTOM_ACTION = "custom_action"

@dataclass
class ActionContext:
    """Context information for action execution."""
    event: HotkeyEvent
    timestamp: float = field(default_factory=time.time)
    user_data: Optional[Dict[str, Any]] = None
    action_params: Optional[Dict[str, Any]] = None

@dataclass
class ActionResult:
    """Result of an action execution."""
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0

class HotkeyActions:
    """
    Handles execution of hotkey-triggered actions.
    
    This class provides a centralized way to execute actions when hotkeys
    are pressed, with support for custom actions and integration with
    ZeroLag components.
    """
    
    def __init__(self):
        self.action_handlers: Dict[HotkeyActionType, Callable] = {}
        self.custom_actions: Dict[str, Callable] = {}
        self.action_history: List[ActionContext] = []
        self.max_history = 1000
        
        # Initialize default action handlers
        self._setup_default_handlers()
        
        logger.info("HotkeyActions initialized")
    
    def execute_action(self, action_type: HotkeyActionType, event: HotkeyEvent, 
                      context: Optional[ActionContext] = None) -> ActionResult:
        """
        Execute a hotkey action.
        
        Args:
            action_type: Type of action to execute
            event: Hotkey event that triggered the action
            context: Optional context information
            
        Returns:
            ActionResult with execution details
        """
        start_time = time.time()
        
        try:
            # Create action context if not provided
            if context is None:
                context = ActionContext(event=event)
            
            # Add to action history
            self._add_to_history(context)
            
            # Execute the action
            if action_type in self.action_handlers:
                handler = self.action_handlers[action_type]
                result = handler(context)
                
                execution_time = time.time() - start_time
                return ActionResult(
                    success=True,
                    message=f"Action {action_type.value} executed successfully",
                    data=result,
                    execution_time=execution_time
                )
            else:
                execution_time = time.time() - start_time
                return ActionResult(
                    success=False,
                    message=f"No handler found for action {action_type.value}",
                    execution_time=execution_time
                )
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing action {action_type.value}: {e}")
            return ActionResult(
                success=False,
                message=f"Error executing action: {str(e)}",
                execution_time=execution_time
            )
    
    def register_action_handler(self, action_type: HotkeyActionType, handler: Callable):
        """
        Register a handler for a specific action type.
        
        Args:
            action_type: Type of action
            handler: Function to handle the action
        """
        self.action_handlers[action_type] = handler
        logger.info(f"Registered handler for action: {action_type.value}")
    
    def unregister_action_handler(self, action_type: HotkeyActionType):
        """
        Unregister a handler for a specific action type.
        
        Args:
            action_type: Type of action
        """
        if action_type in self.action_handlers:
            del self.action_handlers[action_type]
            logger.info(f"Unregistered handler for action: {action_type.value}")
    
    def register_custom_action(self, action_name: str, handler: Callable):
        """
        Register a custom action handler.
        
        Args:
            action_name: Name of the custom action
            handler: Function to handle the action
        """
        self.custom_actions[action_name] = handler
        logger.info(f"Registered custom action: {action_name}")
    
    def unregister_custom_action(self, action_name: str):
        """
        Unregister a custom action handler.
        
        Args:
            action_name: Name of the custom action
        """
        if action_name in self.custom_actions:
            del self.custom_actions[action_name]
            logger.info(f"Unregistered custom action: {action_name}")
    
    def _setup_default_handlers(self):
        """Set up default action handlers."""
        # Profile Management
        self.action_handlers[HotkeyActionType.CYCLE_PROFILE] = self._handle_cycle_profile
        self.action_handlers[HotkeyActionType.NEXT_PROFILE] = self._handle_next_profile
        self.action_handlers[HotkeyActionType.PREVIOUS_PROFILE] = self._handle_previous_profile
        self.action_handlers[HotkeyActionType.SAVE_CURRENT_PROFILE] = self._handle_save_current_profile
        
        # DPI Management
        self.action_handlers[HotkeyActionType.INCREASE_DPI] = self._handle_increase_dpi
        self.action_handlers[HotkeyActionType.DECREASE_DPI] = self._handle_decrease_dpi
        self.action_handlers[HotkeyActionType.RESET_DPI] = self._handle_reset_dpi
        self.action_handlers[HotkeyActionType.TOGGLE_DPI_MODE] = self._handle_toggle_dpi_mode
        
        # Polling Rate Management
        self.action_handlers[HotkeyActionType.INCREASE_POLLING_RATE] = self._handle_increase_polling_rate
        self.action_handlers[HotkeyActionType.DECREASE_POLLING_RATE] = self._handle_decrease_polling_rate
        self.action_handlers[HotkeyActionType.RESET_POLLING_RATE] = self._handle_reset_polling_rate
        
        # Keyboard Optimizations
        self.action_handlers[HotkeyActionType.TOGGLE_NKRO] = self._handle_toggle_nkro
        self.action_handlers[HotkeyActionType.TOGGLE_RAPID_TRIGGER] = self._handle_toggle_rapid_trigger
        self.action_handlers[HotkeyActionType.TOGGLE_DEBOUNCE] = self._handle_toggle_debounce
        
        # Smoothing Controls
        self.action_handlers[HotkeyActionType.TOGGLE_SMOOTHING] = self._handle_toggle_smoothing
        self.action_handlers[HotkeyActionType.INCREASE_SMOOTHING] = self._handle_increase_smoothing
        self.action_handlers[HotkeyActionType.DECREASE_SMOOTHING] = self._handle_decrease_smoothing
        
        # Macro Controls
        self.action_handlers[HotkeyActionType.START_MACRO_RECORDING] = self._handle_start_macro_recording
        self.action_handlers[HotkeyActionType.STOP_MACRO_RECORDING] = self._handle_stop_macro_recording
        self.action_handlers[HotkeyActionType.PLAY_MACRO] = self._handle_play_macro
        
        # Application Controls
        self.action_handlers[HotkeyActionType.TOGGLE_ZEROLAG] = self._handle_toggle_zerolag
        self.action_handlers[HotkeyActionType.SHOW_GUI] = self._handle_show_gui
        self.action_handlers[HotkeyActionType.HIDE_GUI] = self._handle_hide_gui
        self.action_handlers[HotkeyActionType.QUIT_APPLICATION] = self._handle_quit_application
        
        # Emergency Controls
        self.action_handlers[HotkeyActionType.EMERGENCY_STOP] = self._handle_emergency_stop
        self.action_handlers[HotkeyActionType.EMERGENCY_RESET] = self._handle_emergency_reset
        self.action_handlers[HotkeyActionType.EMERGENCY_DISABLE_ALL] = self._handle_emergency_disable_all
        
        logger.info("Default action handlers registered")
    
    def _add_to_history(self, context: ActionContext):
        """Add action context to history."""
        self.action_history.append(context)
        if len(self.action_history) > self.max_history:
            self.action_history.pop(0)
    
    # Default action handlers (placeholders - will be implemented with actual ZeroLag integration)
    
    def _handle_cycle_profile(self, context: ActionContext) -> Dict[str, Any]:
        """Handle profile cycling action."""
        logger.info("Cycling to next profile")
        return {"action": "cycle_profile", "status": "success"}
    
    def _handle_next_profile(self, context: ActionContext) -> Dict[str, Any]:
        """Handle next profile action."""
        logger.info("Switching to next profile")
        return {"action": "next_profile", "status": "success"}
    
    def _handle_previous_profile(self, context: ActionContext) -> Dict[str, Any]:
        """Handle previous profile action."""
        logger.info("Switching to previous profile")
        return {"action": "previous_profile", "status": "success"}
    
    def _handle_save_current_profile(self, context: ActionContext) -> Dict[str, Any]:
        """Handle save current profile action."""
        logger.info("Saving current profile")
        return {"action": "save_current_profile", "status": "success"}
    
    def _handle_increase_dpi(self, context: ActionContext) -> Dict[str, Any]:
        """Handle increase DPI action."""
        logger.info("Increasing DPI")
        return {"action": "increase_dpi", "status": "success"}
    
    def _handle_decrease_dpi(self, context: ActionContext) -> Dict[str, Any]:
        """Handle decrease DPI action."""
        logger.info("Decreasing DPI")
        return {"action": "decrease_dpi", "status": "success"}
    
    def _handle_reset_dpi(self, context: ActionContext) -> Dict[str, Any]:
        """Handle reset DPI action."""
        logger.info("Resetting DPI")
        return {"action": "reset_dpi", "status": "success"}
    
    def _handle_toggle_dpi_mode(self, context: ActionContext) -> Dict[str, Any]:
        """Handle toggle DPI mode action."""
        logger.info("Toggling DPI mode")
        return {"action": "toggle_dpi_mode", "status": "success"}
    
    def _handle_increase_polling_rate(self, context: ActionContext) -> Dict[str, Any]:
        """Handle increase polling rate action."""
        logger.info("Increasing polling rate")
        return {"action": "increase_polling_rate", "status": "success"}
    
    def _handle_decrease_polling_rate(self, context: ActionContext) -> Dict[str, Any]:
        """Handle decrease polling rate action."""
        logger.info("Decreasing polling rate")
        return {"action": "decrease_polling_rate", "status": "success"}
    
    def _handle_reset_polling_rate(self, context: ActionContext) -> Dict[str, Any]:
        """Handle reset polling rate action."""
        logger.info("Resetting polling rate")
        return {"action": "reset_polling_rate", "status": "success"}
    
    def _handle_toggle_nkro(self, context: ActionContext) -> Dict[str, Any]:
        """Handle toggle NKRO action."""
        logger.info("Toggling NKRO")
        return {"action": "toggle_nkro", "status": "success"}
    
    def _handle_toggle_rapid_trigger(self, context: ActionContext) -> Dict[str, Any]:
        """Handle toggle rapid trigger action."""
        logger.info("Toggling rapid trigger")
        return {"action": "toggle_rapid_trigger", "status": "success"}
    
    def _handle_toggle_debounce(self, context: ActionContext) -> Dict[str, Any]:
        """Handle toggle debounce action."""
        logger.info("Toggling debounce")
        return {"action": "toggle_debounce", "status": "success"}
    
    def _handle_toggle_smoothing(self, context: ActionContext) -> Dict[str, Any]:
        """Handle toggle smoothing action."""
        logger.info("Toggling smoothing")
        return {"action": "toggle_smoothing", "status": "success"}
    
    def _handle_increase_smoothing(self, context: ActionContext) -> Dict[str, Any]:
        """Handle increase smoothing action."""
        logger.info("Increasing smoothing")
        return {"action": "increase_smoothing", "status": "success"}
    
    def _handle_decrease_smoothing(self, context: ActionContext) -> Dict[str, Any]:
        """Handle decrease smoothing action."""
        logger.info("Decreasing smoothing")
        return {"action": "decrease_smoothing", "status": "success"}
    
    def _handle_start_macro_recording(self, context: ActionContext) -> Dict[str, Any]:
        """Handle start macro recording action."""
        logger.info("Starting macro recording")
        return {"action": "start_macro_recording", "status": "success"}
    
    def _handle_stop_macro_recording(self, context: ActionContext) -> Dict[str, Any]:
        """Handle stop macro recording action."""
        logger.info("Stopping macro recording")
        return {"action": "stop_macro_recording", "status": "success"}
    
    def _handle_play_macro(self, context: ActionContext) -> Dict[str, Any]:
        """Handle play macro action."""
        logger.info("Playing macro")
        return {"action": "play_macro", "status": "success"}
    
    def _handle_toggle_zerolag(self, context: ActionContext) -> Dict[str, Any]:
        """Handle toggle ZeroLag action."""
        logger.info("Toggling ZeroLag")
        return {"action": "toggle_zerolag", "status": "success"}
    
    def _handle_show_gui(self, context: ActionContext) -> Dict[str, Any]:
        """Handle show GUI action."""
        logger.info("Showing GUI")
        return {"action": "show_gui", "status": "success"}
    
    def _handle_hide_gui(self, context: ActionContext) -> Dict[str, Any]:
        """Handle hide GUI action."""
        logger.info("Hiding GUI")
        return {"action": "hide_gui", "status": "success"}
    
    def _handle_quit_application(self, context: ActionContext) -> Dict[str, Any]:
        """Handle quit application action."""
        logger.info("Quitting application")
        return {"action": "quit_application", "status": "success"}
    
    def _handle_emergency_stop(self, context: ActionContext) -> Dict[str, Any]:
        """Handle emergency stop action."""
        logger.warning("EMERGENCY STOP triggered")
        return {"action": "emergency_stop", "status": "success"}
    
    def _handle_emergency_reset(self, context: ActionContext) -> Dict[str, Any]:
        """Handle emergency reset action."""
        logger.warning("EMERGENCY RESET triggered")
        return {"action": "emergency_reset", "status": "success"}
    
    def _handle_emergency_disable_all(self, context: ActionContext) -> Dict[str, Any]:
        """Handle emergency disable all action."""
        logger.warning("EMERGENCY DISABLE ALL triggered")
        return {"action": "emergency_disable_all", "status": "success"}
    
    def get_action_history(self, limit: Optional[int] = None) -> List[ActionContext]:
        """Get action execution history."""
        if limit is None:
            return self.action_history.copy()
        return self.action_history[-limit:] if limit > 0 else []
    
    def clear_action_history(self):
        """Clear action execution history."""
        self.action_history.clear()
        logger.info("Action history cleared")
    
    def get_available_actions(self) -> List[HotkeyActionType]:
        """Get list of available action types."""
        return list(HotkeyActionType)
    
    def get_registered_handlers(self) -> List[HotkeyActionType]:
        """Get list of registered action handlers."""
        return list(self.action_handlers.keys())
