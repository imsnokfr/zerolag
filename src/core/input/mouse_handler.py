"""
Enhanced Mouse Handler for ZeroLag

This module provides specialized mouse event handling optimized for gaming,
including high-frequency tracking, click timing, and performance monitoring.
"""

import time
import threading
from typing import Callable, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

from pynput import mouse
from pynput.mouse import Button, Listener as MouseListener
from .input_handler import InputHandler, InputEventType, InputEvent
from ..dpi.dpi_emulator import DPIEmulator, DPIMode
from ..queue.input_queue import EventPriority


class MouseButton(Enum):
    """Mouse button enumeration for easier handling."""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"
    X1 = "x1"
    X2 = "x2"


@dataclass
class MouseState:
    """Current state of the mouse for tracking."""
    x: int = 0
    y: int = 0
    last_x: int = 0
    last_y: int = 0
    dx: int = 0
    dy: int = 0
    buttons_pressed: Dict[MouseButton, bool] = None
    last_click_time: float = 0.0
    click_count: int = 0
    scroll_dx: int = 0
    scroll_dy: int = 0
    
    def __post_init__(self):
        if self.buttons_pressed is None:
            self.buttons_pressed = {button: False for button in MouseButton}


class GamingMouseHandler:
    """
    Enhanced mouse handler optimized for gaming scenarios.
    
    Features:
    - High-frequency mouse tracking with delta calculations
    - Click timing and double-click detection
    - Button state tracking for complex inputs
    - Performance monitoring for gaming optimization
    - Smooth movement interpolation
    """
    
    def __init__(self, input_handler: InputHandler, enable_logging: bool = True):
        """
        Initialize the gaming mouse handler.
        
        Args:
            input_handler: The base InputHandler instance
            enable_logging: Enable logging for debugging
        """
        self.input_handler = input_handler
        self.logger = logging.getLogger(__name__) if enable_logging else None
        if self.logger:
            self.logger.setLevel(logging.INFO)
        
        # Mouse state tracking
        self.mouse_state = MouseState()
        self.is_tracking = False
        
        # Performance monitoring
        self.movement_events = 0
        self.click_events = 0
        self.scroll_events = 0
        self.last_performance_update = time.time()
        
        # Gaming-specific settings
        self.double_click_threshold = 0.5  # seconds
        self.movement_smoothing = True
        self.high_frequency_tracking = True
        
        # DPI emulation
        self.dpi_emulator = DPIEmulator(base_dpi=800, enable_logging=enable_logging)
        self.dpi_emulator.set_movement_callback(self._on_dpi_movement)
        
        # Callbacks for specific mouse events
        self.mouse_move_callback: Optional[Callable] = None
        self.mouse_click_callback: Optional[Callable] = None
        self.mouse_double_click_callback: Optional[Callable] = None
        self.mouse_scroll_callback: Optional[Callable] = None
        self.mouse_drag_callback: Optional[Callable] = None
        
        # Thread safety
        self._lock = threading.Lock()
    
    def start_tracking(self) -> bool:
        """
        Start enhanced mouse tracking.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_tracking:
            return True
        
        try:
            with self._lock:
                # Set up mouse event callbacks
                self._setup_mouse_callbacks()
                
                self.is_tracking = True
                self.last_performance_update = time.time()
                
                if self.logger:
                    self.logger.info("Gaming mouse handler started")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start mouse tracking: {e}")
            return False
    
    def stop_tracking(self) -> None:
        """Stop enhanced mouse tracking."""
        with self._lock:
            self.is_tracking = False
            if self.logger:
                self.logger.info("Gaming mouse handler stopped")
    
    def _setup_mouse_callbacks(self) -> None:
        """Set up mouse event callbacks for enhanced tracking."""
        # Mouse move callback
        def on_mouse_move(event: InputEvent):
            if event.event_type == InputEventType.MOUSE_MOVE:
                self._handle_mouse_move(event)
        
        # Mouse click callbacks
        def on_mouse_click(event: InputEvent):
            if event.event_type in [InputEventType.MOUSE_PRESS, InputEventType.MOUSE_RELEASE]:
                self._handle_mouse_click(event)
        
        # Mouse scroll callback
        def on_mouse_scroll(event: InputEvent):
            if event.event_type == InputEventType.MOUSE_SCROLL:
                self._handle_mouse_scroll(event)
        
        # Register callbacks with the input handler
        self.input_handler.add_event_callback(InputEventType.MOUSE_MOVE, on_mouse_move)
        self.input_handler.add_event_callback(InputEventType.MOUSE_PRESS, on_mouse_click)
        self.input_handler.add_event_callback(InputEventType.MOUSE_RELEASE, on_mouse_click)
        self.input_handler.add_event_callback(InputEventType.MOUSE_SCROLL, on_mouse_scroll)
    
    def _handle_mouse_move(self, event: InputEvent) -> None:
        """Handle mouse movement events with enhanced tracking and DPI emulation."""
        if not self.is_tracking:
            return
        
        data = event.data
        current_time = event.timestamp
        
        # Use high-frequency queuing for mouse movement events
        if hasattr(self, 'input_queue') and self.input_queue.is_processing():
            # Enqueue for high-frequency processing
            self.enqueue_high_frequency_event(
                InputEventType.MOUSE_MOVE,
                data,
                EventPriority.HIGH  # High priority for mouse movement
            )
            return
        
        # Fallback to direct processing if queue not available
        self._process_mouse_move_direct(event)
    
    def _process_mouse_move_direct(self, event: InputEvent) -> None:
        """Process mouse movement event directly (fallback method)."""
        data = event.data
        current_time = event.timestamp
        
        with self._lock:
            # Get raw movement deltas
            raw_dx = data.get('dx', 0)
            raw_dy = data.get('dy', 0)
            
            # Apply DPI emulation
            scaled_dx, scaled_dy = self.dpi_emulator.process_movement(raw_dx, raw_dy)
            
            # Update mouse state with scaled movement
            self.mouse_state.last_x = self.mouse_state.x
            self.mouse_state.last_y = self.mouse_state.y
            self.mouse_state.x = data['x']
            self.mouse_state.y = data['y']
            self.mouse_state.dx = scaled_dx
            self.mouse_state.dy = scaled_dy
            
            self.movement_events += 1
        
        # Call movement callback if set
        if self.mouse_move_callback:
            try:
                self.mouse_move_callback(self.mouse_state, event)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in mouse move callback: {e}")
        
        # Update performance stats
        self._update_performance_stats()
    
    def _handle_mouse_click(self, event: InputEvent) -> None:
        """Handle mouse click events with timing and state tracking."""
        if not self.is_tracking:
            return
        
        data = event.data
        current_time = event.timestamp
        is_press = event.event_type == InputEventType.MOUSE_PRESS
        button_name = data.get('button', 'unknown')
        
        # Use high-frequency queuing for critical mouse events
        if hasattr(self, 'input_queue') and self.input_queue.is_processing():
            # Enqueue for high-frequency processing with critical priority
            self.enqueue_high_frequency_event(
                event.event_type,
                data,
                EventPriority.CRITICAL  # Critical priority for clicks
            )
            return
        
        # Fallback to direct processing if queue not available
        self._process_mouse_click_direct(event)
    
    def _process_mouse_click_direct(self, event: InputEvent) -> None:
        """Process mouse click event directly (fallback method)."""
        data = event.data
        current_time = event.timestamp
        is_press = event.event_type == InputEventType.MOUSE_PRESS
        button_name = data.get('button', 'unknown')
        
        # Convert button name to MouseButton enum
        try:
            button = MouseButton(button_name.lower())
        except ValueError:
            button = MouseButton.LEFT  # Default fallback
        
        with self._lock:
            if is_press:
                # Button pressed
                self.mouse_state.buttons_pressed[button] = True
                self.mouse_state.last_click_time = current_time
                self.mouse_state.click_count += 1
                self.click_events += 1
                
                # Check for double-click
                if self._is_double_click(current_time):
                    if self.mouse_double_click_callback:
                        try:
                            self.mouse_double_click_callback(button, self.mouse_state, event)
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"Error in double-click callback: {e}")
            else:
                # Button released
                self.mouse_state.buttons_pressed[button] = False
                
                # Check for drag end
                if self._was_dragging(button):
                    if self.mouse_drag_callback:
                        try:
                            self.mouse_drag_callback(button, self.mouse_state, event, False)  # drag_end=True
                        except Exception as e:
                            if self.logger:
                                self.logger.error(f"Error in drag callback: {e}")
        
        # Call click callback if set
        if self.mouse_click_callback:
            try:
                self.mouse_click_callback(button, is_press, self.mouse_state, event)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in mouse click callback: {e}")
    
    def _handle_mouse_scroll(self, event: InputEvent) -> None:
        """Handle mouse scroll events."""
        if not self.is_tracking:
            return
        
        data = event.data
        current_time = event.timestamp
        
        with self._lock:
            self.mouse_state.scroll_dx = data.get('dx', 0)
            self.mouse_state.scroll_dy = data.get('dy', 0)
            self.scroll_events += 1
        
        # Call scroll callback if set
        if self.mouse_scroll_callback:
            try:
                self.mouse_scroll_callback(self.mouse_state, event)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in mouse scroll callback: {e}")
    
    def _is_double_click(self, current_time: float) -> bool:
        """Check if this is a double-click based on timing."""
        time_diff = current_time - self.mouse_state.last_click_time
        return time_diff <= self.double_click_threshold
    
    def _was_dragging(self, button: MouseButton) -> bool:
        """Check if the mouse was being dragged."""
        return self.mouse_state.buttons_pressed.get(button, False)
    
    def _update_performance_stats(self) -> None:
        """Update performance statistics."""
        current_time = time.time()
        if current_time - self.last_performance_update >= 1.0:  # Update every second
            if self.logger:
                self.logger.debug(f"Mouse performance: {self.movement_events} moves, "
                                f"{self.click_events} clicks, {self.scroll_events} scrolls")
            
            # Reset counters
            self.movement_events = 0
            self.click_events = 0
            self.scroll_events = 0
            self.last_performance_update = current_time
    
    def get_mouse_state(self) -> MouseState:
        """
        Get current mouse state.
        
        Returns:
            Current mouse state (thread-safe copy)
        """
        with self._lock:
            return MouseState(
                x=self.mouse_state.x,
                y=self.mouse_state.y,
                last_x=self.mouse_state.last_x,
                last_y=self.mouse_state.last_y,
                dx=self.mouse_state.dx,
                dy=self.mouse_state.dy,
                buttons_pressed=self.mouse_state.buttons_pressed.copy(),
                last_click_time=self.mouse_state.last_click_time,
                click_count=self.mouse_state.click_count,
                scroll_dx=self.mouse_state.scroll_dx,
                scroll_dy=self.mouse_state.scroll_dy
            )
    
    def is_button_pressed(self, button: MouseButton) -> bool:
        """
        Check if a specific button is currently pressed.
        
        Args:
            button: Mouse button to check
            
        Returns:
            True if button is pressed, False otherwise
        """
        with self._lock:
            return self.mouse_state.buttons_pressed.get(button, False)
    
    def get_movement_delta(self) -> Tuple[int, int]:
        """
        Get the last movement delta.
        
        Returns:
            Tuple of (dx, dy) movement delta
        """
        with self._lock:
            return (self.mouse_state.dx, self.mouse_state.dy)
    
    def get_click_count(self) -> int:
        """
        Get total click count since tracking started.
        
        Returns:
            Total number of clicks
        """
        with self._lock:
            return self.mouse_state.click_count
    
    def set_double_click_threshold(self, threshold: float) -> None:
        """
        Set the double-click detection threshold.
        
        Args:
            threshold: Time threshold in seconds
        """
        self.double_click_threshold = max(0.1, min(2.0, threshold))
    
    def set_movement_smoothing(self, enabled: bool) -> None:
        """
        Enable or disable movement smoothing.
        
        Args:
            enabled: True to enable smoothing, False to disable
        """
        self.movement_smoothing = enabled
    
    def set_high_frequency_tracking(self, enabled: bool) -> None:
        """
        Enable or disable high-frequency tracking.
        
        Args:
            enabled: True to enable high-frequency tracking
        """
        self.high_frequency_tracking = enabled
    
    # Callback setters
    def set_mouse_move_callback(self, callback: Callable) -> None:
        """Set callback for mouse movement events."""
        self.mouse_move_callback = callback
    
    def set_mouse_click_callback(self, callback: Callable) -> None:
        """Set callback for mouse click events."""
        self.mouse_click_callback = callback
    
    def set_mouse_double_click_callback(self, callback: Callable) -> None:
        """Set callback for double-click events."""
        self.mouse_double_click_callback = callback
    
    def set_mouse_scroll_callback(self, callback: Callable) -> None:
        """Set callback for mouse scroll events."""
        self.mouse_scroll_callback = callback
    
    def set_mouse_drag_callback(self, callback: Callable) -> None:
        """Set callback for mouse drag events."""
        self.mouse_drag_callback = callback
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get mouse-specific performance statistics.
        
        Returns:
            Dictionary containing mouse performance metrics
        """
        current_time = time.time()
        uptime = current_time - self.last_performance_update
        
        return {
            'is_tracking': self.is_tracking,
            'movement_events': self.movement_events,
            'click_events': self.click_events,
            'scroll_events': self.scroll_events,
            'total_clicks': self.mouse_state.click_count,
            'current_position': (self.mouse_state.x, self.mouse_state.y),
            'last_movement': (self.mouse_state.dx, self.mouse_state.dy),
            'buttons_pressed': {k.name: v for k, v in self.mouse_state.buttons_pressed.items() if v},
            'dpi_stats': self.dpi_emulator.get_performance_stats()
        }
    
    def set_dpi(self, dpi: int) -> bool:
        """
        Set the DPI for mouse movement scaling.
        
        Args:
            dpi: Target DPI (400-26000)
            
        Returns:
            True if successful, False otherwise
        """
        success = self.dpi_emulator.set_dpi(dpi)
        if success and self.logger:
            self.logger.info(f"Mouse DPI set to {dpi}")
        return success
    
    def get_current_dpi(self) -> int:
        """Get the current DPI setting."""
        return self.dpi_emulator.get_current_dpi()
    
    def set_dpi_mode(self, mode: DPIMode) -> bool:
        """
        Set the DPI emulation mode.
        
        Args:
            mode: DPI emulation mode (SOFTWARE, HYBRID, NATIVE)
            
        Returns:
            True if successful, False otherwise
        """
        success = self.dpi_emulator.set_mode(mode)
        if success and self.logger:
            self.logger.info(f"DPI mode set to {mode.value}")
        return success
    
    def set_movement_smoothing(self, enabled: bool):
        """Enable or disable movement smoothing."""
        self.movement_smoothing = enabled
        self.dpi_emulator.set_smoothing(enabled)
        if self.logger:
            self.logger.info(f"Movement smoothing {'enabled' if enabled else 'disabled'}")
    
    def set_precision_mode(self, enabled: bool):
        """Enable or disable precision mode for sub-pixel accuracy."""
        self.dpi_emulator.set_precision_mode(enabled)
        if self.logger:
            self.logger.info(f"Precision mode {'enabled' if enabled else 'disabled'}")
    
    def _on_dpi_movement(self, movement):
        """Handle DPI-processed movement events."""
        # This callback is called when the DPI emulator processes a movement
        # We can use this for additional processing or logging
        if self.logger and self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"DPI processed movement: {movement.dx}, {movement.dy} "
                            f"(raw: {movement.raw_dx}, {movement.raw_dy})")


# Example usage and testing
if __name__ == "__main__":
    def on_mouse_move(state: MouseState, event: InputEvent):
        print(f"Mouse moved to ({state.x}, {state.y}) delta: ({state.dx}, {state.dy})")
    
    def on_mouse_click(button: MouseButton, is_press: bool, state: MouseState, event: InputEvent):
        action = "pressed" if is_press else "released"
        print(f"Mouse {button.name} {action} at ({state.x}, {state.y})")
    
    def on_double_click(button: MouseButton, state: MouseState, event: InputEvent):
        print(f"Double-click detected: {button.name} at ({state.x}, {state.y})")
    
    def on_mouse_scroll(state: MouseState, event: InputEvent):
        print(f"Mouse scrolled: dx={state.scroll_dx}, dy={state.scroll_dy}")
    
    # Create input handler and gaming mouse handler
    input_handler = InputHandler(queue_size=1000, enable_logging=False)
    mouse_handler = GamingMouseHandler(input_handler, enable_logging=True)
    
    # Set up callbacks
    mouse_handler.set_mouse_move_callback(on_mouse_move)
    mouse_handler.set_mouse_click_callback(on_mouse_click)
    mouse_handler.set_mouse_double_click_callback(on_double_click)
    mouse_handler.set_mouse_scroll_callback(on_mouse_scroll)
    
    # Start handlers
    if input_handler.start() and mouse_handler.start_tracking():
        print("Gaming mouse handler started. Move your mouse and click to test.")
        print("Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(1)
                stats = mouse_handler.get_performance_stats()
                print(f"Mouse stats: {stats['movement_events']} moves, "
                      f"{stats['click_events']} clicks, "
                      f"{stats['total_clicks']} total clicks")
        except KeyboardInterrupt:
            print("\nStopping handlers...")
            mouse_handler.stop_tracking()
            input_handler.stop()
    else:
        print("Failed to start handlers")