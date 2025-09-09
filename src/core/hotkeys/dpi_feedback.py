"""
DPI Adjustment Visual Feedback for ZeroLag

This module provides visual feedback for DPI adjustments, including
overlay displays, console notifications, and status indicators.

Features:
- DPI adjustment overlay display
- Console-based feedback
- Visual DPI indicator
- Adjustment history display
- Customizable feedback styles
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .dpi_hotkeys import DPIFeedback, DPIStepSize

logger = logging.getLogger(__name__)

class FeedbackDisplayMode(Enum):
    """DPI feedback display modes."""
    CONSOLE = "console"
    OVERLAY = "overlay"
    BOTH = "both"
    NONE = "none"

class FeedbackStyle(Enum):
    """DPI feedback visual styles."""
    SIMPLE = "simple"
    DETAILED = "detailed"
    GAMING = "gaming"
    MINIMAL = "minimal"

@dataclass
class DPIFeedbackConfig:
    """Configuration for DPI feedback display."""
    display_mode: FeedbackDisplayMode = FeedbackDisplayMode.CONSOLE
    feedback_style: FeedbackStyle = FeedbackStyle.SIMPLE
    show_duration: float = 2.0
    show_history: bool = True
    max_history_display: int = 5
    console_width: int = 80
    overlay_position: Tuple[int, int] = (10, 10)
    overlay_size: Tuple[int, int] = (300, 150)
    overlay_transparency: float = 0.8
    colors: Dict[str, str] = field(default_factory=lambda: {
        'success': '\033[92m',  # Green
        'error': '\033[91m',    # Red
        'warning': '\033[93m',  # Yellow
        'info': '\033[94m',     # Blue
        'reset': '\033[0m'      # Reset
    })

class DPIFeedbackDisplay:
    """
    Displays visual feedback for DPI adjustments.
    
    This class provides various feedback mechanisms including console
    output, overlay displays, and status indicators.
    """
    
    def __init__(self, config: Optional[DPIFeedbackConfig] = None):
        self.config = config or DPIFeedbackConfig()
        self.feedback_history: List[DPIFeedback] = []
        self.display_active = False
        self.display_thread: Optional[threading.Thread] = None
        self.stop_display = threading.Event()
        
        logger.info("DPIFeedbackDisplay initialized")
    
    def show_feedback(self, feedback: DPIFeedback):
        """
        Display DPI adjustment feedback.
        
        Args:
            feedback: DPI feedback information to display
        """
        try:
            # Add to history
            self.feedback_history.append(feedback)
            if len(self.feedback_history) > 100:  # Keep last 100 feedbacks
                self.feedback_history.pop(0)
            
            # Display based on configuration
            if self.config.display_mode in [FeedbackDisplayMode.CONSOLE, FeedbackDisplayMode.BOTH]:
                self._show_console_feedback(feedback)
            
            if self.config.display_mode in [FeedbackDisplayMode.OVERLAY, FeedbackDisplayMode.BOTH]:
                self._show_overlay_feedback(feedback)
            
            logger.info(f"Displayed DPI feedback: {feedback.message}")
            
        except Exception as e:
            logger.error(f"Error displaying DPI feedback: {e}")
    
    def _show_console_feedback(self, feedback: DPIFeedback):
        """Display console-based feedback."""
        try:
            # Clear line and move cursor to beginning
            print('\r' + ' ' * self.config.console_width + '\r', end='', flush=True)
            
            if self.config.feedback_style == FeedbackStyle.SIMPLE:
                self._show_simple_console_feedback(feedback)
            elif self.config.feedback_style == FeedbackStyle.DETAILED:
                self._show_detailed_console_feedback(feedback)
            elif self.config.feedback_style == FeedbackStyle.GAMING:
                self._show_gaming_console_feedback(feedback)
            elif self.config.feedback_style == FeedbackStyle.MINIMAL:
                self._show_minimal_console_feedback(feedback)
            
            # Show history if enabled
            if self.config.show_history and len(self.feedback_history) > 1:
                self._show_console_history()
            
        except Exception as e:
            logger.error(f"Error showing console feedback: {e}")
    
    def _show_simple_console_feedback(self, feedback: DPIFeedback):
        """Show simple console feedback."""
        color = self.config.colors['success'] if feedback.success else self.config.colors['error']
        reset = self.config.colors['reset']
        
        if feedback.success:
            print(f"{color}DPI: {feedback.old_dpi:.0f} → {feedback.new_dpi:.0f} ({feedback.adjustment:+.0f}){reset}", end='', flush=True)
        else:
            print(f"{color}DPI Error: {feedback.message}{reset}", end='', flush=True)
    
    def _show_detailed_console_feedback(self, feedback: DPIFeedback):
        """Show detailed console feedback."""
        color = self.config.colors['success'] if feedback.success else self.config.colors['error']
        reset = self.config.colors['reset']
        
        print(f"{color}=== DPI Adjustment ===")
        print(f"Old DPI: {feedback.old_dpi:.0f}")
        print(f"New DPI: {feedback.new_dpi:.0f}")
        print(f"Adjustment: {feedback.adjustment:+.0f}")
        print(f"Step Size: {feedback.step_size.value}")
        print(f"Time: {time.strftime('%H:%M:%S', time.localtime(feedback.timestamp))}")
        if not feedback.success:
            print(f"Error: {feedback.message}")
        print(f"===================={reset}")
    
    def _show_gaming_console_feedback(self, feedback: DPIFeedback):
        """Show gaming-style console feedback."""
        color = self.config.colors['success'] if feedback.success else self.config.colors['error']
        reset = self.config.colors['reset']
        
        # Gaming-style display with symbols
        if feedback.success:
            arrow = "↑" if feedback.adjustment > 0 else "↓" if feedback.adjustment < 0 else "="
            print(f"{color}[DPI] {feedback.old_dpi:.0f} {arrow} {feedback.new_dpi:.0f} ({feedback.adjustment:+.0f}){reset}", end='', flush=True)
        else:
            print(f"{color}[DPI] ERROR: {feedback.message}{reset}", end='', flush=True)
    
    def _show_minimal_console_feedback(self, feedback: DPIFeedback):
        """Show minimal console feedback."""
        color = self.config.colors['success'] if feedback.success else self.config.colors['error']
        reset = self.config.colors['reset']
        
        if feedback.success:
            print(f"{color}DPI: {feedback.new_dpi:.0f}{reset}", end='', flush=True)
        else:
            print(f"{color}DPI: ERROR{reset}", end='', flush=True)
    
    def _show_console_history(self):
        """Show recent DPI adjustment history."""
        if len(self.feedback_history) < 2:
            return
        
        recent = self.feedback_history[-self.config.max_history_display:]
        print(f"\n{self.config.colors['info']}Recent DPI adjustments:{self.config.colors['reset']}")
        
        for i, feedback in enumerate(recent[-self.config.max_history_display:], 1):
            if feedback.success:
                arrow = "↑" if feedback.adjustment > 0 else "↓" if feedback.adjustment < 0 else "="
                print(f"  {i}. {feedback.old_dpi:.0f} {arrow} {feedback.new_dpi:.0f} ({feedback.adjustment:+.0f})")
            else:
                print(f"  {i}. ERROR: {feedback.message}")
    
    def _show_overlay_feedback(self, feedback: DPIFeedback):
        """Display overlay feedback (placeholder for future implementation)."""
        # This would implement a GUI overlay in the future
        # For now, we'll just log that overlay feedback was requested
        logger.info(f"Overlay feedback requested: {feedback.message}")
    
    def show_dpi_status(self, current_dpi: float, presets: Dict[int, Any] = None):
        """
        Show current DPI status and available presets.
        
        Args:
            current_dpi: Current DPI value
            presets: Available DPI presets
        """
        try:
            print(f"\n{self.config.colors['info']}=== DPI Status ===")
            print(f"Current DPI: {current_dpi:.0f}")
            
            if presets:
                print("Available Presets:")
                for num, preset in presets.items():
                    marker = " ←" if preset.dpi_value == current_dpi else ""
                    print(f"  {num}. {preset.name}: {preset.dpi_value:.0f}{marker}")
            
            print(f"================{self.config.colors['reset']}")
            
        except Exception as e:
            logger.error(f"Error showing DPI status: {e}")
    
    def show_dpi_help(self):
        """Show DPI hotkey help information."""
        try:
            print(f"\n{self.config.colors['info']}=== DPI Hotkeys ===")
            print("Ctrl+Alt+Up     - Increase DPI")
            print("Ctrl+Alt+Down   - Decrease DPI")
            print("Ctrl+Alt+Home   - Reset DPI")
            print("Ctrl+Alt+1-9    - DPI Presets")
            print("================{self.config.colors['reset']}")
            
        except Exception as e:
            logger.error(f"Error showing DPI help: {e}")
    
    def clear_display(self):
        """Clear the current display."""
        try:
            # Clear console line
            print('\r' + ' ' * self.config.console_width + '\r', end='', flush=True)
        except Exception as e:
            logger.error(f"Error clearing display: {e}")
    
    def get_feedback_history(self, limit: Optional[int] = None) -> List[DPIFeedback]:
        """Get DPI feedback history."""
        if limit is None:
            return self.feedback_history.copy()
        return self.feedback_history[-limit:] if limit > 0 else []
    
    def clear_feedback_history(self):
        """Clear DPI feedback history."""
        self.feedback_history.clear()
        logger.info("Cleared DPI feedback history")
    
    def update_config(self, new_config: DPIFeedbackConfig):
        """Update feedback display configuration."""
        self.config = new_config
        logger.info("Updated DPI feedback configuration")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feedback display statistics."""
        total_feedbacks = len(self.feedback_history)
        successful_feedbacks = sum(1 for f in self.feedback_history if f.success)
        failed_feedbacks = total_feedbacks - successful_feedbacks
        
        return {
            'total_feedbacks': total_feedbacks,
            'successful_feedbacks': successful_feedbacks,
            'failed_feedbacks': failed_feedbacks,
            'success_rate': successful_feedbacks / total_feedbacks if total_feedbacks > 0 else 0.0,
            'display_mode': self.config.display_mode.value,
            'feedback_style': self.config.feedback_style.value,
            'show_duration': self.config.show_duration
        }

class DPIFeedbackManager:
    """
    Manages DPI feedback display and notifications.
    
    This class coordinates between DPI adjustments and feedback display,
    providing a unified interface for DPI feedback management.
    """
    
    def __init__(self, config: Optional[DPIFeedbackConfig] = None):
        self.config = config or DPIFeedbackConfig()
        self.display = DPIFeedbackDisplay(self.config)
        self.feedback_callbacks: List[Callable[[DPIFeedback], None]] = []
        
        logger.info("DPIFeedbackManager initialized")
    
    def show_feedback(self, feedback: DPIFeedback):
        """Show DPI adjustment feedback."""
        self.display.show_feedback(feedback)
        
        # Notify callbacks
        for callback in self.feedback_callbacks:
            try:
                callback(feedback)
            except Exception as e:
                logger.error(f"Error in DPI feedback callback: {e}")
    
    def add_feedback_callback(self, callback: Callable[[DPIFeedback], None]):
        """Add a feedback callback."""
        self.feedback_callbacks.append(callback)
        logger.info("Added DPI feedback callback")
    
    def remove_feedback_callback(self, callback: Callable[[DPIFeedback], None]):
        """Remove a feedback callback."""
        if callback in self.feedback_callbacks:
            self.feedback_callbacks.remove(callback)
            logger.info("Removed DPI feedback callback")
    
    def show_dpi_status(self, current_dpi: float, presets: Dict[int, Any] = None):
        """Show DPI status information."""
        self.display.show_dpi_status(current_dpi, presets)
    
    def show_dpi_help(self):
        """Show DPI hotkey help."""
        self.display.show_dpi_help()
    
    def clear_display(self):
        """Clear the current display."""
        self.display.clear_display()
    
    def get_feedback_history(self, limit: Optional[int] = None) -> List[DPIFeedback]:
        """Get feedback history."""
        return self.display.get_feedback_history(limit)
    
    def clear_feedback_history(self):
        """Clear feedback history."""
        self.display.clear_feedback_history()
    
    def update_config(self, new_config: DPIFeedbackConfig):
        """Update feedback configuration."""
        self.config = new_config
        self.display.update_config(new_config)
        logger.info("Updated DPI feedback manager configuration")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get feedback manager statistics."""
        return self.display.get_stats()
