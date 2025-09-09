"""
Simple unit tests for the GamingMouseHandler class.

This module contains basic unit tests for the GamingMouseHandler class,
testing core functionality without complex edge cases.
"""

import pytest
import time
from unittest.mock import Mock

import sys
from pathlib import Path

# Add src directory to path
src_dir = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_dir))

from core.input.input_handler import InputHandler, InputEventType, InputEvent
from core.input.mouse_handler import GamingMouseHandler


class TestGamingMouseHandlerSimple:
    """Simple test cases for the GamingMouseHandler class."""

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
        """Test GamingMouseHandler initialization."""
        handler = GamingMouseHandler(self.input_handler)
        assert handler.input_handler == self.input_handler
        assert handler.movement_events == 0
        assert handler.click_events == 0

    def test_start_tracking(self):
        """Test starting mouse tracking."""
        # Start input handler first
        self.input_handler.start()
        
        # Should return True if input handler is running
        assert self.mouse_handler.start_tracking()

    def test_stop_tracking(self):
        """Test stopping mouse tracking."""
        # Should not raise an exception
        self.mouse_handler.stop_tracking()

    def test_mouse_move_processing(self):
        """Test processing of mouse movement events."""
        self.input_handler.start()
        self.mouse_handler.start_tracking()
        
        # Create a mouse move event
        event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            timestamp=time.time(),
            data={"x": 100, "y": 200}
        )
        
        # Process the event
        self.mouse_handler._handle_mouse_move(event)
        
        # Check that movement was counted
        assert self.mouse_handler.movement_events == 1

    def test_mouse_click_processing(self):
        """Test processing of mouse click events."""
        self.input_handler.start()
        self.mouse_handler.start_tracking()
        
        # Create a mouse press event
        press_event = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        
        # Process the event
        self.mouse_handler._handle_mouse_click(press_event)
        
        # Check that click was counted
        assert self.mouse_handler.click_events == 1

    def test_mouse_scroll_processing(self):
        """Test processing of mouse scroll events."""
        self.input_handler.start()
        self.mouse_handler.start_tracking()
        
        # Create a mouse scroll event
        scroll_event = InputEvent(
            event_type=InputEventType.MOUSE_SCROLL,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "dx": 0, "dy": 1}
        )
        
        # Process the event
        self.mouse_handler._handle_mouse_scroll(scroll_event)
        
        # Check that scroll was counted
        assert self.mouse_handler.scroll_events == 1

    def test_performance_stats(self):
        """Test performance statistics collection."""
        self.input_handler.start()
        self.mouse_handler.start_tracking()
        
        # Generate some events
        move_event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            timestamp=time.time(),
            data={"x": 100, "y": 200}
        )
        self.mouse_handler._handle_mouse_move(move_event)
        
        click_event = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            timestamp=time.time(),
            data={"x": 100, "y": 200, "button": "left"}
        )
        self.mouse_handler._handle_mouse_click(click_event)
        
        # Get stats
        stats = self.mouse_handler.get_performance_stats()
        
        assert "movement_events" in stats
        assert "click_events" in stats
        assert "scroll_events" in stats
        assert "is_tracking" in stats
        
        assert stats["movement_events"] == 1
        assert stats["click_events"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
