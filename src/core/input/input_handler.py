"""
Core Input Handler for ZeroLag

This module provides a unified interface for handling both mouse and keyboard
input events with high-performance processing and low-latency optimization.
"""

import time
import threading
import queue
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging

from pynput import mouse, keyboard
from pynput.mouse import Button, Listener as MouseListener
from pynput.keyboard import Key, Listener as KeyboardListener
from ..polling.polling_manager import PollingManager, PollingConfig, PollingMode
from ..queue.input_queue import InputQueue, EventPriority, QueueMode


class InputEventType(Enum):
    """Types of input events that can be captured."""
    # Mouse events
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_PRESS = "mouse_press"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_SCROLL = "mouse_scroll"
    
    # Keyboard events
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"


@dataclass
class InputEvent:
    """Represents a unified input event with timing and data."""
    event_type: InputEventType
    timestamp: float
    data: Dict[str, Any]
    processed: bool = False
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class InputHandler:
    """
    Unified input handler for mouse and keyboard events.
    
    Features:
    - High-performance event capture
    - Event queuing and buffering
    - Callback system for event handling
    - Thread-safe operation
    - Performance monitoring
    """
    
    def __init__(self, queue_size: int = 5000, enable_logging: bool = True):
        """
        Initialize the input handler.
        
        Args:
            queue_size: Maximum number of events in the queue
            enable_logging: Enable logging for debugging
        """
        self.queue_size = queue_size
        self.event_queue = queue.Queue(maxsize=queue_size)
        
        # State tracking
        self.is_running = False
        self.mouse_listener = None
        self.keyboard_listener = None
        
        # Event processing
        self.processing_thread = None
        self.event_callbacks: Dict[InputEventType, List[Callable]] = {
            event_type: [] for event_type in InputEventType
        }
        self.raw_event_callback: Optional[Callable] = None
        
        # Performance tracking
        self.events_processed = 0
        self.events_dropped = 0
        self.start_time = 0.0
        
        # Polling rate management
        self.polling_manager = PollingManager(
            config=PollingConfig(mouse_rate=1000, keyboard_rate=1000),
            enable_logging=enable_logging
        )
        self._setup_polling_callbacks()
        
        # High-frequency input queuing
        self.input_queue = InputQueue(
            max_size=queue_size * 2,  # Double the queue size for high-frequency events
            mode=QueueMode.ADAPTIVE,
            enable_logging=enable_logging
        )
        self._setup_queue_handlers()
        
        # Logging
        self.logger = logging.getLogger(__name__) if enable_logging else None
        if self.logger:
            self.logger.setLevel(logging.INFO)
        
        # Thread safety
        self._lock = threading.Lock()
    
    def start(self) -> bool:
        """
        Start the input handler.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            return True
        
        try:
            with self._lock:
                self.is_running = True  # Set this before starting threads
                self.start_time = time.time()
                
                self._start_mouse_listener()
                self._start_keyboard_listener()
                self._start_processing_thread()
                
                # Start polling manager
                if not self.polling_manager.start():
                    if self.logger:
                        self.logger.warning("Failed to start polling manager")
                
                # Start input queue
                if not self.input_queue.start():
                    if self.logger:
                        self.logger.warning("Failed to start input queue")
                
                if self.logger:
                    self.logger.info("Input handler started successfully")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start input handler: {e}")
            else:
                print(f"Failed to start input handler: {e}")
                import traceback
                traceback.print_exc()
            return False
    
    def stop(self) -> None:
        """Stop the input handler."""
        with self._lock:
            self.is_running = False
            
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
                
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=1.0)
            
            # Stop polling manager
            self.polling_manager.stop()
            
            # Stop input queue
            self.input_queue.stop()
            
            if self.logger:
                self.logger.info("Input handler stopped")
    
    def _start_mouse_listener(self) -> None:
        """Start the mouse event listener."""
        def on_move(x, y):
            self._queue_event(InputEventType.MOUSE_MOVE, {
                'x': x, 'y': y, 'dx': 0, 'dy': 0
            })
        
        def on_click(x, y, button, pressed):
            event_type = InputEventType.MOUSE_PRESS if pressed else InputEventType.MOUSE_RELEASE
            self._queue_event(event_type, {
                'x': x, 'y': y, 'button': button.name if hasattr(button, 'name') else str(button)
            })
        
        def on_scroll(x, y, dx, dy):
            self._queue_event(InputEventType.MOUSE_SCROLL, {
                'x': x, 'y': y, 'dx': dx, 'dy': dy
            })
        
        self.mouse_listener = MouseListener(
            on_move=on_move,
            on_click=on_click,
            on_scroll=on_scroll
        )
        self.mouse_listener.start()
    
    def _start_keyboard_listener(self) -> None:
        """Start the keyboard event listener."""
        def on_press(key):
            self._queue_event(InputEventType.KEY_PRESS, {
                'key': self._key_to_string(key),
                'key_code': self._key_to_code(key)
            })
        
        def on_release(key):
            self._queue_event(InputEventType.KEY_RELEASE, {
                'key': self._key_to_string(key),
                'key_code': self._key_to_code(key)
            })
        
        self.keyboard_listener = KeyboardListener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start()
    
    def _start_processing_thread(self) -> None:
        """Start the event processing thread."""
        self.processing_thread = threading.Thread(
            target=self._processing_loop,
            daemon=True,
            name="InputProcessingThread"
        )
        self.processing_thread.start()
        
        # Give the thread a moment to start and initialize
        time.sleep(0.1)
        
        if not self.processing_thread.is_alive():
            raise RuntimeError("Processing thread failed to start")
    
    def _processing_loop(self) -> None:
        """Main event processing loop."""
        try:
            if self.logger:
                self.logger.info("Processing thread started")
            
            while self.is_running:
                try:
                    # Process multiple events per cycle for better performance
                    events_processed_this_cycle = 0
                    max_events_per_cycle = 100  # Process up to 100 events per cycle
                    
                    while events_processed_this_cycle < max_events_per_cycle and self.is_running:
                        try:
                            # Try to get event with very short timeout
                            event = self.event_queue.get(timeout=0.001)
                            self._process_event(event)
                            self.events_processed += 1
                            events_processed_this_cycle += 1
                            
                            if self.logger and events_processed_this_cycle % 10 == 0:
                                self.logger.debug(f"Processed {events_processed_this_cycle} events this cycle")
                                
                        except queue.Empty:
                            break  # No more events, exit inner loop
                    
                    # Small sleep to prevent excessive CPU usage
                    if events_processed_this_cycle == 0:
                        time.sleep(0.001)  # 1ms sleep when no events
                    
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error in processing cycle: {e}")
                    else:
                        print(f"Error in processing cycle: {e}")
                    time.sleep(0.01)  # Small delay before retrying
            
            if self.logger:
                self.logger.info("Processing thread stopped")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fatal error in processing thread: {e}")
            else:
                print(f"Fatal error in processing thread: {e}")
            # Re-raise to see the full traceback
            raise
    
    def _queue_event(self, event_type: InputEventType, data: Dict[str, Any]) -> None:
        """
        Queue an input event for processing.
        
        Args:
            event_type: Type of input event
            data: Event data dictionary
        """
        try:
            event = InputEvent(
                event_type=event_type,
                timestamp=time.time(),
                data=data
            )
            
            # Try to put event in queue (non-blocking)
            self.event_queue.put_nowait(event)
            
        except queue.Full:
            # Queue is full, try to make room by dropping oldest events
            self.events_dropped += 1
            
            # Try to drop a few old events to make room
            try:
                for _ in range(10):  # Drop up to 10 old events
                    self.event_queue.get_nowait()
                    self.events_dropped += 1
                
                # Try to add the new event again
                self.event_queue.put_nowait(event)
                self.events_dropped -= 1  # Don't count this as dropped
                
            except queue.Empty:
                # Still can't add, drop the event
                if self.logger and self.events_dropped % 100 == 0:  # Log every 100th drop
                    self.logger.warning(f"Event queue full, dropped {self.events_dropped} events")
    
    def _process_event(self, event: InputEvent) -> None:
        """
        Process a single input event.
        
        Args:
            event: Input event to process
        """
        if self.logger:
            self.logger.debug(f"Processing event: {event.event_type.value}")
        
        # Call raw event callback if set
        if self.raw_event_callback:
            try:
                self.raw_event_callback(event)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in raw event callback: {e}")
        
        # Call specific event type callbacks
        callbacks = self.event_callbacks.get(event.event_type, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in event callback for {event.event_type}: {e}")
        
        event.processed = True
    
    def _key_to_string(self, key) -> str:
        """Convert a key object to string representation."""
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            else:
                return str(key)
        except:
            return str(key)
    
    def _key_to_code(self, key) -> int:
        """Convert a key object to key code."""
        try:
            if hasattr(key, 'value'):
                return key.value.vk if hasattr(key.value, 'vk') else 0
            return 0
        except:
            return 0
    
    def add_event_callback(self, event_type: InputEventType, callback: Callable) -> None:
        """
        Add a callback for a specific event type.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event occurs
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
        else:
            self.event_callbacks[event_type] = [callback]
    
    def remove_event_callback(self, event_type: InputEventType, callback: Callable) -> None:
        """
        Remove a callback for a specific event type.
        
        Args:
            event_type: Type of event
            callback: Function to remove
        """
        if event_type in self.event_callbacks:
            try:
                self.event_callbacks[event_type].remove(callback)
            except ValueError:
                pass  # Callback not found
    
    def set_raw_event_callback(self, callback: Callable) -> None:
        """
        Set a callback for all raw input events.
        
        Args:
            callback: Function to call for all events
        """
        self.raw_event_callback = callback
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get current performance statistics.
        
        Returns:
            Dictionary containing performance metrics
        """
        current_time = time.time()
        uptime = current_time - self.start_time if self.start_time > 0 else 0
        
        return {
            'is_running': self.is_running,
            'uptime': uptime,
            'events_processed': self.events_processed,
            'events_dropped': self.events_dropped,
            'events_per_second': self.events_processed / uptime if uptime > 0 else 0,
            'queue_size': self.event_queue.qsize(),
            'queue_utilization': self.event_queue.qsize() / self.queue_size,
            'drop_rate': self.events_dropped / (self.events_processed + self.events_dropped) if (self.events_processed + self.events_dropped) > 0 else 0
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.
        
        Returns:
            Dictionary containing queue information
        """
        return {
            'queue_size': self.event_queue.qsize(),
            'max_size': self.queue_size,
            'utilization': self.event_queue.qsize() / self.queue_size,
            'is_running': self.is_running
        }
    
    def clear_queue(self) -> int:
        """
        Clear all events from the queue.
        
        Returns:
            Number of events cleared
        """
        cleared = 0
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
                cleared += 1
            except queue.Empty:
                break
        return cleared
    
    def _setup_polling_callbacks(self):
        """Set up polling manager callbacks."""
        self.polling_manager.set_mouse_poll_callback(self._on_mouse_poll)
        self.polling_manager.set_keyboard_poll_callback(self._on_keyboard_poll)
        self.polling_manager.set_stats_callback(self._on_polling_stats)
    
    def _on_mouse_poll(self, event_data):
        """Handle mouse polling events."""
        # This can be used to trigger high-frequency mouse polling
        pass
    
    def _on_keyboard_poll(self, event_data):
        """Handle keyboard polling events."""
        # This can be used to trigger high-frequency keyboard polling
        pass
    
    def _on_polling_stats(self, stats):
        """Handle polling statistics updates."""
        # This can be used to monitor polling performance
        if self.logger and self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Polling stats: {stats.actual_rate:.1f}Hz actual, "
                            f"{stats.target_rate}Hz target, {stats.latency_avg:.2f}ms latency")
    
    def set_mouse_polling_rate(self, rate: int) -> bool:
        """
        Set the mouse polling rate.
        
        Args:
            rate: Polling rate in Hz (125-8000)
            
        Returns:
            True if successful, False otherwise
        """
        return self.polling_manager.set_mouse_polling_rate(rate)
    
    def set_keyboard_polling_rate(self, rate: int) -> bool:
        """
        Set the keyboard polling rate.
        
        Args:
            rate: Polling rate in Hz (125-8000)
            
        Returns:
            True if successful, False otherwise
        """
        return self.polling_manager.set_keyboard_polling_rate(rate)
    
    def set_polling_mode(self, mode: PollingMode) -> bool:
        """
        Set the polling mode.
        
        Args:
            mode: Polling mode (FIXED, ADAPTIVE, GAMING, POWER_SAVE)
            
        Returns:
            True if successful, False otherwise
        """
        return self.polling_manager.set_polling_mode(mode)
    
    def get_polling_stats(self):
        """Get polling statistics."""
        return self.polling_manager.get_polling_stats()
    
    def get_polling_config(self):
        """Get polling configuration."""
        return self.polling_manager.get_config()
    
    def _setup_queue_handlers(self):
        """Set up input queue event handlers."""
        # Set up event handlers for different event types
        self.input_queue.add_event_handler("mouse_move", self._handle_queued_mouse_move)
        self.input_queue.add_event_handler("mouse_click", self._handle_queued_mouse_click)
        self.input_queue.add_event_handler("mouse_press", self._handle_queued_mouse_press)
        self.input_queue.add_event_handler("mouse_release", self._handle_queued_mouse_release)
        self.input_queue.add_event_handler("mouse_scroll", self._handle_queued_mouse_scroll)
        self.input_queue.add_event_handler("key_press", self._handle_queued_key_press)
        self.input_queue.add_event_handler("key_release", self._handle_queued_key_release)
        
        # Set up batch processing handler
        self.input_queue.add_batch_handler(self._handle_batch_events)
        
        # Set up error handler
        self.input_queue.add_error_handler(self._handle_queue_error)
    
    def _handle_queued_mouse_move(self, queued_event):
        """Handle queued mouse move events."""
        # Convert queued event back to InputEvent and process
        input_event = InputEvent(
            event_type=InputEventType.MOUSE_MOVE,
            data=queued_event.data,
            timestamp=queued_event.timestamp
        )
        self._process_event(input_event)
    
    def _handle_queued_mouse_click(self, queued_event):
        """Handle queued mouse click events."""
        input_event = InputEvent(
            event_type=InputEventType.MOUSE_CLICK,
            data=queued_event.data,
            timestamp=queued_event.timestamp
        )
        self._process_event(input_event)
    
    def _handle_queued_mouse_press(self, queued_event):
        """Handle queued mouse press events."""
        input_event = InputEvent(
            event_type=InputEventType.MOUSE_PRESS,
            data=queued_event.data,
            timestamp=queued_event.timestamp
        )
        self._process_event(input_event)
    
    def _handle_queued_mouse_release(self, queued_event):
        """Handle queued mouse release events."""
        input_event = InputEvent(
            event_type=InputEventType.MOUSE_RELEASE,
            data=queued_event.data,
            timestamp=queued_event.timestamp
        )
        self._process_event(input_event)
    
    def _handle_queued_mouse_scroll(self, queued_event):
        """Handle queued mouse scroll events."""
        input_event = InputEvent(
            event_type=InputEventType.MOUSE_SCROLL,
            data=queued_event.data,
            timestamp=queued_event.timestamp
        )
        self._process_event(input_event)
    
    def _handle_queued_key_press(self, queued_event):
        """Handle queued key press events."""
        input_event = InputEvent(
            event_type=InputEventType.KEY_PRESS,
            data=queued_event.data,
            timestamp=queued_event.timestamp
        )
        self._process_event(input_event)
    
    def _handle_queued_key_release(self, queued_event):
        """Handle queued key release events."""
        input_event = InputEvent(
            event_type=InputEventType.KEY_RELEASE,
            data=queued_event.data,
            timestamp=queued_event.timestamp
        )
        self._process_event(input_event)
    
    def _handle_batch_events(self, batch):
        """Handle batch of events for optimal performance."""
        # Process batch of events together for better performance
        for queued_event in batch:
            # Convert and process each event
            event_type_map = {
                "mouse_move": InputEventType.MOUSE_MOVE,
                "mouse_click": InputEventType.MOUSE_CLICK,
                "mouse_press": InputEventType.MOUSE_PRESS,
                "mouse_release": InputEventType.MOUSE_RELEASE,
                "mouse_scroll": InputEventType.MOUSE_SCROLL,
                "key_press": InputEventType.KEY_PRESS,
                "key_release": InputEventType.KEY_RELEASE
            }
            
            if queued_event.event_type in event_type_map:
                input_event = InputEvent(
                    event_type=event_type_map[queued_event.event_type],
                    data=queued_event.data,
                    timestamp=queued_event.timestamp
                )
                self._process_event(input_event)
    
    def _handle_queue_error(self, error, context):
        """Handle input queue errors."""
        if self.logger:
            self.logger.error(f"Input queue error: {error}, context: {context}")
    
    def enqueue_high_frequency_event(self, event_type: InputEventType, data: Dict[str, Any], priority: EventPriority = EventPriority.NORMAL):
        """
        Enqueue an event for high-frequency processing.
        
        Args:
            event_type: Type of the input event
            data: Event data
            priority: Event priority for processing
        """
        return self.input_queue.enqueue(
            event_type=event_type.value,
            data=data,
            priority=priority,
            source="input_handler"
        )
    
    def get_queue_stats(self):
        """Get input queue statistics."""
        return self.input_queue.get_stats()
    
    def set_queue_mode(self, mode: QueueMode):
        """Set the input queue processing mode."""
        self.input_queue.set_mode(mode)
    
    def set_queue_batch_size(self, size: int):
        """Set the input queue batch size."""
        self.input_queue.set_batch_size(size)


# Example usage and testing
if __name__ == "__main__":
    def on_mouse_move(event: InputEvent):
        data = event.data
        print(f"Mouse moved to ({data['x']}, {data['y']})")
    
    def on_key_press(event: InputEvent):
        data = event.data
        print(f"Key pressed: {data['key']}")
    
    def on_raw_event(event: InputEvent):
        print(f"Raw event: {event.event_type.value} at {event.timestamp}")
    
    # Create and configure input handler
    input_handler = InputHandler(queue_size=100, enable_logging=True)
    
    # Add event callbacks
    input_handler.add_event_callback(InputEventType.MOUSE_MOVE, on_mouse_move)
    input_handler.add_event_callback(InputEventType.KEY_PRESS, on_key_press)
    input_handler.set_raw_event_callback(on_raw_event)
    
    # Start the handler
    if input_handler.start():
        print("Input handler started. Move your mouse and press keys to test.")
        print("Press Ctrl+C to stop.")
        
        try:
            while True:
                time.sleep(1)
                stats = input_handler.get_performance_stats()
                print(f"Performance: {stats['events_per_second']:.1f} events/sec, "
                      f"Queue: {stats['queue_utilization']:.1%}, "
                      f"Dropped: {stats['events_dropped']}")
        except KeyboardInterrupt:
            print("\nStopping input handler...")
            input_handler.stop()
    else:
        print("Failed to start input handler")
