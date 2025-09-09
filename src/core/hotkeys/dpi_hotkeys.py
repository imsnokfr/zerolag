"""
DPI Adjustment Hotkeys for ZeroLag

This module provides specialized hotkey functionality for real-time DPI adjustments,
including step adjustments, preset switching, and visual feedback.

Features:
- Real-time DPI adjustment hotkeys
- Step-based DPI changes (small, medium, large)
- Quick DPI presets (Ctrl+Alt+1-9)
- Visual DPI indicator overlay
- DPI adjustment limits and validation
- Integration with existing DPI emulator system
"""

import logging
import time
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .hotkey_actions import HotkeyActionType, ActionContext, ActionResult
from .hotkey_detector import HotkeyModifier
from ..dpi import DPIEmulator

logger = logging.getLogger(__name__)

class DPIStepSize(Enum):
    """DPI adjustment step sizes."""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    CUSTOM = "custom"

@dataclass
class DPIPreset:
    """DPI preset configuration."""
    name: str
    dpi_value: float
    description: str = ""
    hotkey_number: Optional[int] = None

@dataclass
class DPIStepConfig:
    """Configuration for DPI step adjustments."""
    small_step: float = 50.0
    medium_step: float = 100.0
    large_step: float = 200.0
    custom_step: float = 100.0

@dataclass
class DPILimits:
    """DPI adjustment limits."""
    min_dpi: float = 100.0
    max_dpi: float = 16000.0
    default_dpi: float = 800.0

@dataclass
class DPIFeedback:
    """Feedback information for DPI adjustments."""
    old_dpi: float
    new_dpi: float
    adjustment: float
    step_size: DPIStepSize
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    message: str = ""

@dataclass
class DPIHotkeyConfig:
    """Configuration for DPI hotkeys."""
    enable_dpi_adjustment: bool = True
    enable_preset_switching: bool = True
    enable_step_adjustment: bool = True
    visual_feedback_duration: float = 2.0
    step_config: DPIStepConfig = field(default_factory=DPIStepConfig)
    limits: DPILimits = field(default_factory=DPILimits)
    default_presets: List[DPIPreset] = field(default_factory=lambda: [
        DPIPreset("Low", 400.0, "Low DPI for precision", 1),
        DPIPreset("Medium", 800.0, "Medium DPI for balance", 2),
        DPIPreset("High", 1600.0, "High DPI for speed", 3),
        DPIPreset("Ultra", 3200.0, "Ultra high DPI", 4),
        DPIPreset("Max", 6400.0, "Maximum DPI", 5),
    ])

class DPIHotkeyManager:
    """
    Manages DPI adjustment hotkeys and provides visual feedback.
    
    This class integrates with the existing DPI emulator system
    to provide hotkey-based DPI adjustment functionality.
    """
    
    def __init__(self, dpi_emulator: DPIEmulator, config: Optional[DPIHotkeyConfig] = None):
        self.dpi_emulator = dpi_emulator
        self.config = config or DPIHotkeyConfig()
        
        # DPI state
        self.current_dpi = self.config.limits.default_dpi
        self.last_adjustment_time = 0.0
        self.adjustment_history: List[DPIFeedback] = []
        
        # DPI presets
        self.dpi_presets: Dict[int, DPIPreset] = {}
        self._setup_default_presets()
        
        # Callbacks for visual feedback
        self.feedback_callbacks: List[Callable[[DPIFeedback], None]] = []
        
        # Hotkey mappings
        self.dpi_hotkey_mappings: Dict[int, str] = {}  # hotkey_id -> action_name
        
        logger.info("DPIHotkeyManager initialized")
    
    def _setup_default_presets(self):
        """Set up default DPI presets."""
        for preset in self.config.default_presets:
            if preset.hotkey_number:
                self.dpi_presets[preset.hotkey_number] = preset
        logger.info(f"Set up {len(self.dpi_presets)} DPI presets")
    
    def register_dpi_hotkeys(self, hotkey_manager) -> Dict[str, int]:
        """
        Register all DPI adjustment hotkeys with the hotkey manager.
        
        Args:
            hotkey_manager: HotkeyManager instance
            
        Returns:
            Dictionary mapping action names to hotkey IDs
        """
        hotkey_ids = {}
        
        try:
            # DPI step adjustment hotkeys
            if self.config.enable_step_adjustment:
                # Increase DPI (Ctrl+Alt+Up)
                hotkey_id = hotkey_manager.register_hotkey(
                    HotkeyActionType.INCREASE_DPI,
                    HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    38,  # VK_UP
                    self._handle_increase_dpi
                )
                if hotkey_id:
                    hotkey_ids['increase_dpi'] = hotkey_id
                    logger.info("Registered DPI increase hotkey: Ctrl+Alt+Up")
                
                # Decrease DPI (Ctrl+Alt+Down)
                hotkey_id = hotkey_manager.register_hotkey(
                    HotkeyActionType.DECREASE_DPI,
                    HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    40,  # VK_DOWN
                    self._handle_decrease_dpi
                )
                if hotkey_id:
                    hotkey_ids['decrease_dpi'] = hotkey_id
                    logger.info("Registered DPI decrease hotkey: Ctrl+Alt+Down")
                
                # Reset DPI (Ctrl+Alt+Home)
                hotkey_id = hotkey_manager.register_hotkey(
                    HotkeyActionType.RESET_DPI,
                    HotkeyModifier.CTRL | HotkeyModifier.ALT,
                    36,  # VK_HOME
                    self._handle_reset_dpi
                )
                if hotkey_id:
                    hotkey_ids['reset_dpi'] = hotkey_id
                    logger.info("Registered DPI reset hotkey: Ctrl+Alt+Home")
            
            # DPI preset hotkeys (Ctrl+Alt+1-9)
            if self.config.enable_preset_switching:
                for preset_num, preset in self.dpi_presets.items():
                    virtual_key = ord(str(preset_num))
                    hotkey_id = hotkey_manager.register_hotkey(
                        HotkeyActionType.SET_DPI,
                        HotkeyModifier.CTRL | HotkeyModifier.ALT,
                        virtual_key,
                        lambda ctx, pnum=preset_num: self._handle_dpi_preset(ctx, pnum)
                    )
                    if hotkey_id:
                        hotkey_ids[f'dpi_preset_{preset_num}'] = hotkey_id
                        self.dpi_hotkey_mappings[hotkey_id] = f'dpi_preset_{preset_num}'
                        logger.info(f"Registered DPI preset hotkey: Ctrl+Alt+{preset_num} -> {preset.name}")
            
            logger.info(f"Registered {len(hotkey_ids)} DPI adjustment hotkeys")
            return hotkey_ids
            
        except Exception as e:
            logger.error(f"Error registering DPI hotkeys: {e}")
            return {}
    
    def _handle_increase_dpi(self, context: ActionContext) -> Dict[str, Any]:
        """Handle DPI increase hotkey."""
        try:
            # Determine step size based on modifier keys or default to medium
            step_size = DPIStepSize.MEDIUM
            if hasattr(context, 'action_params') and context.action_params:
                step_size = context.action_params.get('step_size', DPIStepSize.MEDIUM)
            
            # Calculate adjustment amount
            adjustment = self._get_step_amount(step_size)
            
            # Apply DPI adjustment
            result = self._adjust_dpi(adjustment, step_size)
            
            return {
                'success': result.success,
                'old_dpi': result.old_dpi,
                'new_dpi': result.new_dpi,
                'adjustment': result.adjustment,
                'step_size': step_size.value,
                'action': 'increase_dpi'
            }
            
        except Exception as e:
            logger.error(f"Error handling increase DPI: {e}")
            return {
                'success': False,
                'message': f'Error increasing DPI: {str(e)}',
                'action': 'increase_dpi'
            }
    
    def _handle_decrease_dpi(self, context: ActionContext) -> Dict[str, Any]:
        """Handle DPI decrease hotkey."""
        try:
            # Determine step size based on modifier keys or default to medium
            step_size = DPIStepSize.MEDIUM
            if hasattr(context, 'action_params') and context.action_params:
                step_size = context.action_params.get('step_size', DPIStepSize.MEDIUM)
            
            # Calculate adjustment amount (negative)
            adjustment = -self._get_step_amount(step_size)
            
            # Apply DPI adjustment
            result = self._adjust_dpi(adjustment, step_size)
            
            return {
                'success': result.success,
                'old_dpi': result.old_dpi,
                'new_dpi': result.new_dpi,
                'adjustment': result.adjustment,
                'step_size': step_size.value,
                'action': 'decrease_dpi'
            }
            
        except Exception as e:
            logger.error(f"Error handling decrease DPI: {e}")
            return {
                'success': False,
                'message': f'Error decreasing DPI: {str(e)}',
                'action': 'decrease_dpi'
            }
    
    def _handle_reset_dpi(self, context: ActionContext) -> Dict[str, Any]:
        """Handle DPI reset hotkey."""
        try:
            # Reset to default DPI
            old_dpi = self.current_dpi
            new_dpi = self.config.limits.default_dpi
            
            # Apply DPI change
            success = self._set_dpi(new_dpi)
            
            # Create feedback
            feedback = DPIFeedback(
                old_dpi=old_dpi,
                new_dpi=new_dpi,
                adjustment=new_dpi - old_dpi,
                step_size=DPIStepSize.CUSTOM,
                success=success,
                message=f"Reset DPI to {new_dpi}"
            )
            
            # Add to history
            self.adjustment_history.append(feedback)
            if len(self.adjustment_history) > 100:  # Keep last 100 adjustments
                self.adjustment_history.pop(0)
            
            # Notify callbacks
            self._notify_feedback(feedback)
            
            return {
                'success': success,
                'old_dpi': old_dpi,
                'new_dpi': new_dpi,
                'adjustment': feedback.adjustment,
                'action': 'reset_dpi'
            }
            
        except Exception as e:
            logger.error(f"Error handling reset DPI: {e}")
            return {
                'success': False,
                'message': f'Error resetting DPI: {str(e)}',
                'action': 'reset_dpi'
            }
    
    def _handle_dpi_preset(self, context: ActionContext, preset_number: int) -> Dict[str, Any]:
        """Handle DPI preset hotkey."""
        try:
            if preset_number not in self.dpi_presets:
                return {
                    'success': False,
                    'message': f'DPI preset {preset_number} not found',
                    'action': 'dpi_preset'
                }
            
            preset = self.dpi_presets[preset_number]
            old_dpi = self.current_dpi
            new_dpi = preset.dpi_value
            
            # Apply DPI preset
            success = self._set_dpi(new_dpi)
            
            # Create feedback
            feedback = DPIFeedback(
                old_dpi=old_dpi,
                new_dpi=new_dpi,
                adjustment=new_dpi - old_dpi,
                step_size=DPIStepSize.CUSTOM,
                success=success,
                message=f"Applied DPI preset: {preset.name} ({new_dpi})"
            )
            
            # Add to history
            self.adjustment_history.append(feedback)
            if len(self.adjustment_history) > 100:  # Keep last 100 adjustments
                self.adjustment_history.pop(0)
            
            # Notify callbacks
            self._notify_feedback(feedback)
            
            return {
                'success': success,
                'old_dpi': old_dpi,
                'new_dpi': new_dpi,
                'preset_name': preset.name,
                'adjustment': feedback.adjustment,
                'action': 'dpi_preset'
            }
            
        except Exception as e:
            logger.error(f"Error handling DPI preset {preset_number}: {e}")
            return {
                'success': False,
                'message': f'Error applying DPI preset: {str(e)}',
                'action': 'dpi_preset'
            }
    
    def _adjust_dpi(self, adjustment: float, step_size: DPIStepSize) -> DPIFeedback:
        """Adjust DPI by the specified amount."""
        old_dpi = self.current_dpi
        new_dpi = old_dpi + adjustment
        
        # Apply limits
        new_dpi = max(self.config.limits.min_dpi, min(new_dpi, self.config.limits.max_dpi))
        
        # Apply DPI change
        success = self._set_dpi(new_dpi)
        
        # Create feedback
        if success:
            message = f"Adjusted DPI by {adjustment:+.0f} to {new_dpi}"
        else:
            message = f"Failed to adjust DPI by {adjustment:+.0f} to {new_dpi}"
        
        feedback = DPIFeedback(
            old_dpi=old_dpi,
            new_dpi=new_dpi if success else old_dpi,  # Keep old DPI if failed
            adjustment=adjustment,
            step_size=step_size,
            success=success,
            message=message
        )
        
        # Add to history
        self.adjustment_history.append(feedback)
        if len(self.adjustment_history) > 100:  # Keep last 100 adjustments
            self.adjustment_history.pop(0)
        
        # Notify callbacks
        self._notify_feedback(feedback)
        
        return feedback
    
    def _set_dpi(self, dpi_value: float) -> bool:
        """Set DPI to the specified value."""
        try:
            # Validate DPI value
            if not (self.config.limits.min_dpi <= dpi_value <= self.config.limits.max_dpi):
                logger.warning(f"DPI value {dpi_value} is outside limits [{self.config.limits.min_dpi}, {self.config.limits.max_dpi}]")
                return False
            
            # Apply DPI change through emulator
            success = self.dpi_emulator.set_dpi(dpi_value)
            if success:
                self.current_dpi = dpi_value
                self.last_adjustment_time = time.time()
            else:
                return False
            
            logger.info(f"Set DPI to {dpi_value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting DPI to {dpi_value}: {e}")
            return False
    
    def _get_step_amount(self, step_size: DPIStepSize) -> float:
        """Get the adjustment amount for a given step size."""
        if step_size == DPIStepSize.SMALL:
            return self.config.step_config.small_step
        elif step_size == DPIStepSize.MEDIUM:
            return self.config.step_config.medium_step
        elif step_size == DPIStepSize.LARGE:
            return self.config.step_config.large_step
        else:  # CUSTOM
            return self.config.step_config.custom_step
    
    def _notify_feedback(self, feedback: DPIFeedback):
        """Notify all feedback callbacks."""
        for callback in self.feedback_callbacks:
            try:
                callback(feedback)
            except Exception as e:
                logger.error(f"Error in DPI feedback callback: {e}")
    
    def add_feedback_callback(self, callback: Callable[[DPIFeedback], None]):
        """Add a feedback callback for DPI adjustments."""
        self.feedback_callbacks.append(callback)
        logger.info("Added DPI adjustment feedback callback")
    
    def remove_feedback_callback(self, callback: Callable[[DPIFeedback], None]):
        """Remove a feedback callback."""
        if callback in self.feedback_callbacks:
            self.feedback_callbacks.remove(callback)
            logger.info("Removed DPI adjustment feedback callback")
    
    def get_current_dpi(self) -> float:
        """Get the current DPI value."""
        return self.current_dpi
    
    def set_dpi(self, dpi_value: float) -> bool:
        """Set DPI to a specific value."""
        return self._set_dpi(dpi_value)
    
    def adjust_dpi(self, adjustment: float, step_size: DPIStepSize = DPIStepSize.MEDIUM) -> DPIFeedback:
        """Adjust DPI by a specific amount."""
        return self._adjust_dpi(adjustment, step_size)
    
    def get_dpi_presets(self) -> Dict[int, DPIPreset]:
        """Get all DPI presets."""
        return self.dpi_presets.copy()
    
    def add_dpi_preset(self, preset_number: int, preset: DPIPreset):
        """Add a new DPI preset."""
        self.dpi_presets[preset_number] = preset
        logger.info(f"Added DPI preset {preset_number}: {preset.name}")
    
    def remove_dpi_preset(self, preset_number: int):
        """Remove a DPI preset."""
        if preset_number in self.dpi_presets:
            del self.dpi_presets[preset_number]
            logger.info(f"Removed DPI preset {preset_number}")
    
    def get_adjustment_history(self, limit: Optional[int] = None) -> List[DPIFeedback]:
        """Get DPI adjustment history."""
        if limit is None:
            return self.adjustment_history.copy()
        return self.adjustment_history[-limit:] if limit > 0 else []
    
    def clear_adjustment_history(self):
        """Clear DPI adjustment history."""
        self.adjustment_history.clear()
        logger.info("Cleared DPI adjustment history")
    
    def update_config(self, new_config: DPIHotkeyConfig):
        """Update DPI hotkey configuration."""
        self.config = new_config
        self._setup_default_presets()
        logger.info("Updated DPI hotkey configuration")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get DPI adjustment statistics."""
        total_adjustments = len(self.adjustment_history)
        successful_adjustments = sum(1 for feedback in self.adjustment_history if feedback.success)
        failed_adjustments = total_adjustments - successful_adjustments
        
        avg_adjustment = 0.0
        if successful_adjustments > 0:
            avg_adjustment = sum(f.adjustment for f in self.adjustment_history if f.success) / successful_adjustments
        
        return {
            'current_dpi': self.current_dpi,
            'total_adjustments': total_adjustments,
            'successful_adjustments': successful_adjustments,
            'failed_adjustments': failed_adjustments,
            'success_rate': successful_adjustments / total_adjustments if total_adjustments > 0 else 0.0,
            'average_adjustment': avg_adjustment,
            'last_adjustment_time': self.last_adjustment_time,
            'available_presets': len(self.dpi_presets),
            'dpi_limits': {
                'min': self.config.limits.min_dpi,
                'max': self.config.limits.max_dpi,
                'default': self.config.limits.default_dpi
            }
        }
