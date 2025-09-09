"""
Unit tests for the GamingMouseHandler class.

This module contains comprehensive unit tests for the GamingMouseHandler class,
testing mouse event processing, double-click detection, and gaming optimizations.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_dir))

from core.input.input_handler import InputHandler, InputEventType, InputEvent
from core.input.mouse_handler import GamingMouseHandler


class TestGamingMouseHandler:
    """Test cases for the GamingMouseHandler class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.input_handler = InputHandler(queue_size=100, enable_logging=False)
        self.mouse_handler = GamingMouseHandler(
            self.input_handler, 
            enable_logging=False
        )

    def teardown_method(self):
        """Clean up after each test method."""
        if self.input_handler.is_running:
            self.input_handler.stop()

    def test_initialization(self):
        """Test GamingMouseHandler initialization with default parameters."""
        handler = GamingMouseHandler(self.input_handler)
        assert handler.logger is not None
        assert handler.movement_events == 0
        assert handler.click_events == 0
        assert handler.mouse_state.position == (0, 0)

    def test_initialization_with_custom_params(self):
        """Test GamingMouseHandler initialization with custom parameters."""
        handler = GamingMouseHandler(
            self.input_handler,
            enable_logging=False
        )
        assert handler.logger is None

    def test_mouse_move_processing(self):
        """Test processing of mouse movement events."""
        self.input_handler.start()
        
        # Create a mouse move event
        event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            timestamp=time.time(),
            data={"x": 100, "y": 200}
        )
        
        # Process the event
        self.mouse_handler._handle_mouse_move(event)
        
        # Check that position was updated
        assert self.mouse_handler.mouse_position == (100, 200)
        assert self.mouse_handler.total_mouse_moves == 1
        
        # Check that delta was calculated
        assert "dx" in event.data
        assert "dy" in event.data

    def test_mouse_click_processing(self):
        """Test processing of mouse click events."""
        self.input_handler.start()
        
        # Create a mouse press event
        press_event = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        
        # Process the press event
        self.mouse_handler._handle_mouse_click(press_event)
        
        # Check that button state was updated
        from pynput import mouse
        assert self.mouse_handler.button_states[mouse.Button.left] == True
        assert self.mouse_handler.total_mouse_clicks == 1
        
        # Create a mouse release event
        release_event = InputEvent(
            event_type=InputEventType.MOUSE_RELEASE,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        
        # Process the release event
        self.mouse_handler._handle_mouse_click(release_event)
        
        # Check that button state was updated
        assert self.mouse_handler.button_states[mouse.Button.left] == False

    def test_double_click_detection(self):
        """Test double-click detection functionality."""
        self.input_handler.start()
        
        # First click
        first_click = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        self.mouse_handler._handle_mouse_click(first_click)
        
        # Second click within threshold
        second_click = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time() + 0.1,  # Within 300ms threshold
            data={"x": 100, "y": 200, "button": "left"}
        )
        self.mouse_handler._handle_mouse_click(second_click)
        
        # Should detect double-click
        assert self.mouse_handler.total_double_clicks == 1

    def test_double_click_threshold(self):
        """Test that double-click detection respects the threshold."""
        # Set a very short threshold
        handler = GamingMouseHandler(
            self.input_handler,
            double_click_threshold=0.1,
            enable_logging=False
        )
        self.input_handler.start()
        
        # First click
        first_click = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        handler._on_mouse_press(first_click)
        
        # Second click outside threshold
        second_click = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time() + 0.2,  # Outside 100ms threshold
            data={"x": 100, "y": 200, "button": "left"}
        )
        handler._on_mouse_press(second_click)
        
        # Should not detect double-click
        assert handler.total_double_clicks == 0

    def test_double_click_different_positions(self):
        """Test that double-click detection requires same position."""
        self.input_handler.start()
        
        # First click
        first_click = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        self.mouse_handler._handle_mouse_click(first_click)
        
        # Second click at different position
        second_click = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time() + 0.1,
            data={"x": 150, "y": 250, "button": "left"}  # Different position
        )
        self.mouse_handler._handle_mouse_click(second_click)
        
        # Should not detect double-click
        assert self.mouse_handler.total_double_clicks == 0

    def test_mouse_scroll_processing(self):
        """Test processing of mouse scroll events."""
        self.input_handler.start()
        
        # Create a mouse scroll event
        scroll_event = InputEvent(
            event_type=InputEventType.MOUSE_SCROLL,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "dx": 0, "dy": 1}
        )
        
        # Process the event
        self.mouse_handler._handle_mouse_scroll(scroll_event)
        
        # Check that scroll was counted
        assert self.mouse_handler.total_mouse_scrolls == 1

    def test_button_state_tracking(self):
        """Test tracking of mouse button states."""
        self.input_handler.start()
        
        from pynput import mouse
        
        # Test all button states start as False
        for button in [mouse.Button.left, mouse.Button.right, mouse.Button.middle]:
            assert self.mouse_handler.button_states[button] == False
        
        # Press left button
        press_event = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        self.mouse_handler._on_mouse_press(press_event)
        assert self.mouse_handler.button_states[mouse.Button.left] == True
        
        # Release left button
        release_event = InputEvent(
            event_type=InputEventType.MOUSE_RELEASE,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        self.mouse_handler._on_mouse_release(release_event)
        assert self.mouse_handler.button_states[mouse.Button.left] == False

    def test_mouse_stats(self):
        """Test mouse statistics collection."""
        self.input_handler.start()
        
        # Generate some events
        move_event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            timestamp=time.time(),
            data={"x": 100, "y": 200}
        )
        self.mouse_handler._on_mouse_move(move_event)
        
        click_event = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        self.mouse_handler._on_mouse_press(click_event)
        
        scroll_event = InputEvent(
            event_type=InputEventType.MOUSE_SCROLL,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "dx": 0, "dy": 1}
        )
        self.mouse_handler._handle_mouse_scroll(scroll_event)
        
        # Get stats
        stats = self.mouse_handler.get_mouse_stats()
        
        assert "position" in stats
        assert "last_movement_delta" in stats
        assert "button_states" in stats
        assert "total_moves" in stats
        assert "total_clicks" in stats
        assert "total_scrolls" in stats
        assert "total_double_clicks" in stats
        
        assert stats["total_moves"] == 1
        assert stats["total_clicks"] == 1
        assert stats["total_scrolls"] == 1
        assert stats["total_double_clicks"] == 0

    def test_start_tracking(self):
        """Test starting mouse tracking."""
        # Should return False if input handler is not running
        assert not self.mouse_handler.start_tracking()
        
        # Start input handler
        self.input_handler.start()
        
        # Should return True if input handler is running
        assert self.mouse_handler.start_tracking()

    def test_stop_tracking(self):
        """Test stopping mouse tracking."""
        # Should not raise an exception
        self.mouse_handler.stop_tracking()

    def test_delta_calculation(self):
        """Test mouse movement delta calculation."""
        self.input_handler.start()
        
        # First movement
        first_move = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            timestamp=time.time(),
            data={"x": 100, "y": 200}
        )
        self.mouse_handler._on_mouse_move(first_move)
        
        # Second movement
        second_move = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            timestamp=time.time(),
            data={"x": 150, "y": 250}
        )
        self.mouse_handler._on_mouse_move(second_move)
        
        # Check that delta was calculated correctly
        assert second_move.data["dx"] == 50  # 150 - 100
        assert second_move.data["dy"] == 50  # 250 - 200

    def test_multiple_buttons(self):
        """Test handling of multiple mouse buttons."""
        self.input_handler.start()
        
        # Press left button
        left_press = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        self.mouse_handler._on_mouse_press(left_press)
        
        # Press right button
        right_press = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "right"}
        )
        self.mouse_handler._on_mouse_press(right_press)
        
        from pynput import mouse
        assert self.mouse_handler.button_states[mouse.Button.left] == True
        assert self.mouse_handler.button_states[mouse.Button.right] == True
        assert self.mouse_handler.total_mouse_clicks == 2

    def test_unknown_button_handling(self):
        """Test handling of unknown button names."""
        self.input_handler.start()
        
        # Try to process an event with unknown button
        unknown_event = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "unknown_button"}
        )
        
        # Should not raise an exception
        self.mouse_handler._on_mouse_press(unknown_event)
        
        # Should still count the click
        assert self.mouse_handler.total_mouse_clicks == 1

    def test_thread_safety(self):
        """Test thread safety of mouse handler operations."""
        self.input_handler.start()
        
        # Create multiple threads that generate mouse events
        def generate_events():
            for i in range(10):
                event = InputEvent(
                    event_type=InputEventType.MOUSE_MOVE,
                    timestamp=time.time(),
                    data={"x": i, "y": i}
                )
                self.mouse_handler._handle_mouse_move(event)
        
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=generate_events)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should have processed events without errors
        assert self.mouse_handler.total_mouse_moves > 0


if __name__ == "__main__":
    pytest.main([__file__])
