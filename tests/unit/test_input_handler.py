"""
Unit tests for the core InputHandler class.

This module contains comprehensive unit tests for the InputHandler class,
testing event capture, processing, queuing, and performance monitoring.
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


class TestInputHandler:
    """Test cases for the InputHandler class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.input_handler = InputHandler(queue_size=100, enable_logging=False)

    def teardown_method(self):
        """Clean up after each test method."""
        if self.input_handler.is_running:
            self.input_handler.stop()

    def test_initialization(self):
        """Test InputHandler initialization with default parameters."""
        handler = InputHandler()
        assert handler.queue_size == 5000
        assert handler.is_running == False
        assert handler.events_processed == 0
        assert handler.events_dropped == 0

    def test_initialization_with_custom_params(self):
        """Test InputHandler initialization with custom parameters."""
        handler = InputHandler(queue_size=500, enable_logging=False)
        assert handler.queue_size == 500
        assert handler.is_running == False

    def test_start_stop_lifecycle(self):
        """Test starting and stopping the input handler."""
        # Initially not running
        assert not self.input_handler.is_running
        
        # Start the handler
        result = self.input_handler.start()
        assert result == True
        assert self.input_handler.is_running == True
        
        # Stop the handler
        self.input_handler.stop()
        assert self.input_handler.is_running == False

    def test_double_start_handling(self):
        """Test that starting an already running handler returns True."""
        self.input_handler.start()
        assert self.input_handler.is_running == True
        
        # Try to start again
        result = self.input_handler.start()
        assert result == True
        assert self.input_handler.is_running == True

    def test_stop_when_not_running(self):
        """Test that stopping a non-running handler doesn't cause errors."""
        assert not self.input_handler.is_running
        # Should not raise an exception
        self.input_handler.stop()
        assert not self.input_handler.is_running

    def test_event_callback_registration(self):
        """Test registering event callbacks."""
        callback = Mock()
        
        # Register callback for mouse move events
        self.input_handler.add_event_callback(InputEventType.MOUSE_MOVE, callback)
        
        # Check that callback was registered
        assert InputEventType.MOUSE_MOVE in self.input_handler.event_callbacks
        assert callback in self.input_handler.event_callbacks[InputEventType.MOUSE_MOVE]

    def test_multiple_callbacks_for_same_event(self):
        """Test registering multiple callbacks for the same event type."""
        callback1 = Mock()
        callback2 = Mock()
        
        self.input_handler.add_event_callback(InputEventType.KEY_PRESS, callback1)
        self.input_handler.add_event_callback(InputEventType.KEY_PRESS, callback2)
        
        callbacks = self.input_handler.event_callbacks[InputEventType.KEY_PRESS]
        assert len(callbacks) == 2
        assert callback1 in callbacks
        assert callback2 in callbacks

    def test_callback_removal(self):
        """Test removing event callbacks."""
        callback = Mock()
        
        # Register callback
        self.input_handler.add_event_callback(InputEventType.MOUSE_CLICK, callback)
        assert callback in self.input_handler.event_callbacks[InputEventType.MOUSE_CLICK]
        
        # Remove callback
        self.input_handler.remove_event_callback(InputEventType.MOUSE_CLICK, callback)
        assert callback not in self.input_handler.event_callbacks[InputEventType.MOUSE_CLICK]

    def test_event_creation(self):
        """Test creating InputEvent objects."""
        event_data = {"x": 100, "y": 200, "button": "left"}
        event = InputEvent(
            event_type=InputEventType.MOUSE_CLICK,
            timestamp=time.time(),
            data=event_data
        )
        
        assert event.event_type == InputEventType.MOUSE_CLICK
        assert event.data == event_data
        assert isinstance(event.timestamp, float)

    def test_queue_event(self):
        """Test queuing events for processing."""
        self.input_handler.start()
        
        # Create a test event
        event_data = {"key": "a", "key_code": 65}
        self.input_handler._queue_event(InputEventType.KEY_PRESS, event_data)
        
        # Give the processing thread a moment to process
        time.sleep(0.1)
        
        # Check that event was processed
        assert self.input_handler.events_processed > 0

    def test_queue_overflow_handling(self):
        """Test handling of queue overflow."""
        # Create a handler with very small queue
        small_handler = InputHandler(queue_size=2, enable_logging=False)
        small_handler.start()
        
        # Fill the queue beyond capacity
        for i in range(5):
            small_handler._queue_event(InputEventType.MOUSE_MOVE, {"x": i, "y": i})
        
        # Give time for processing
        time.sleep(0.1)
        
        # Should have some dropped events
        assert small_handler.events_dropped > 0
        
        small_handler.stop()

    def test_performance_stats(self):
        """Test performance statistics collection."""
        self.input_handler.start()
        
        # Generate some events
        for i in range(10):
            self.input_handler._queue_event(InputEventType.MOUSE_MOVE, {"x": i, "y": i})
        
        # Give time for processing
        time.sleep(0.1)
        
        stats = self.input_handler.get_performance_stats()
        
        assert "events_processed" in stats
        assert "events_dropped" in stats
        assert "queue_size" in stats
        assert "queue_utilization" in stats
        assert "uptime" in stats
        assert "events_per_second" in stats
        assert "drop_rate" in stats
        
        assert stats["events_processed"] >= 0
        assert stats["events_dropped"] >= 0
        assert stats["uptime"] > 0

    def test_callback_execution(self):
        """Test that registered callbacks are executed when events are processed."""
        callback = Mock()
        self.input_handler.add_event_callback(InputEventType.KEY_PRESS, callback)
        self.input_handler.start()
        
        # Queue an event
        self.input_handler._queue_event(InputEventType.KEY_PRESS, {"key": "a"})
        
        # Give time for processing
        time.sleep(0.1)
        
        # Check that callback was called
        callback.assert_called_once()
        call_args = callback.call_args[0][0]
        assert call_args.event_type == InputEventType.KEY_PRESS
        assert call_args.data["key"] == "a"

    def test_thread_safety(self):
        """Test thread safety of the input handler."""
        self.input_handler.start()
        
        # Create multiple threads that queue events simultaneously
        def queue_events():
            for i in range(10):
                self.input_handler._queue_event(InputEventType.MOUSE_MOVE, {"x": i, "y": i})
        
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=queue_events)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Give time for processing
        time.sleep(0.2)
        
        # Should have processed events without errors
        assert self.input_handler.events_processed > 0

    def test_processing_thread_lifecycle(self):
        """Test that the processing thread starts and stops correctly."""
        # Initially no processing thread
        assert self.input_handler.processing_thread is None
        
        # Start handler
        self.input_handler.start()
        assert self.input_handler.processing_thread is not None
        assert self.input_handler.processing_thread.is_alive()
        
        # Stop handler
        self.input_handler.stop()
        # Give thread time to stop
        time.sleep(0.1)
        assert not self.input_handler.processing_thread.is_alive()

    def test_event_types_enum(self):
        """Test that all expected event types are available."""
        expected_types = [
            "MOUSE_MOVE", "MOUSE_CLICK", "MOUSE_PRESS", "MOUSE_RELEASE",
            "MOUSE_SCROLL", "KEY_PRESS", "KEY_RELEASE"
        ]
        
        for event_type_name in expected_types:
            assert hasattr(InputEventType, event_type_name)

    def test_error_handling_in_processing_loop(self):
        """Test that errors in the processing loop don't crash the handler."""
        # Create a callback that raises an exception
        error_callback = Mock(side_effect=Exception("Test error"))
        self.input_handler.add_event_callback(InputEventType.KEY_PRESS, error_callback)
        self.input_handler.start()
        
        # Queue an event that will cause the callback to fail
        self.input_handler._queue_event(InputEventType.KEY_PRESS, {"key": "a"})
        
        # Give time for processing
        time.sleep(0.1)
        
        # Handler should still be running despite the error
        assert self.input_handler.is_running

    def test_queue_utilization_calculation(self):
        """Test that queue utilization is calculated correctly."""
        # Create handler with known queue size
        handler = InputHandler(queue_size=10, enable_logging=False)
        handler.start()
        
        # Fill queue partially
        for i in range(5):
            handler._queue_event(InputEventType.MOUSE_MOVE, {"x": i, "y": i})
        
        # Give time for some processing
        time.sleep(0.1)
        
        stats = handler.get_performance_stats()
        assert 0 <= stats["queue_utilization"] <= 100
        
        handler.stop()

    def test_uptime_calculation(self):
        """Test that uptime is calculated correctly."""
        self.input_handler.start()
        
        # Wait a bit
        time.sleep(0.1)
        
        stats = self.input_handler.get_performance_stats()
        assert stats["uptime"] >= 0.1  # Should be at least 100ms
        
        # Wait a bit more
        time.sleep(0.1)
        
        stats2 = self.input_handler.get_performance_stats()
        assert stats2["uptime"] > stats["uptime"]  # Should be increasing


if __name__ == "__main__":
    pytest.main([__file__])
