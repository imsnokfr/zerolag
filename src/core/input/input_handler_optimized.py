"""
Optimized Input Handler for ZeroLag Application

This module provides an optimized version of the input handler with improved
performance characteristics, reduced CPU usage, and faster startup times.

Key optimizations:
- Parallel component initialization
- Optimized event processing loop
- Reduced thread overhead
- Better memory management
- Improved error handling
"""

import time
import threading
import queue
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
from pynput import mouse, keyboard
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener

from ..queue.input_queue import InputQueue, EventPriority, QueueMode
from ..polling.polling_manager import PollingManager


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


class OptimizedInputHandler:
    """
    Optimized input handler with improved performance characteristics.
    
    Key improvements:
    - Faster startup through parallel initialization
    - Optimized event processing with batching
    - Reduced CPU usage through better sleep management
    - Improved memory efficiency
    """
    
    def __init__(self, 
                 queue_size: int = 10000,
                 enable_logging: bool = False,
                 mouse_polling_rate: int = 1000,
                 keyboard_polling_rate: int = 1000):
        """
        Initialize the optimized input handler.
        
        Args:
            queue_size: Maximum size of the event queue
            enable_logging: Whether to enable debug logging
            mouse_polling_rate: Mouse polling rate in Hz
            keyboard_polling_rate: Keyboard polling rate in Hz
        """
        self.queue_size = queue_size
        self.is_running = False
        self.start_time = 0.0
        self.events_processed = 0
        self.events_dropped = 0
        
        # Threading
        self._lock = threading.RLock()
        self.processing_thread: Optional[threading.Thread] = None
        
        # Event handling
        self.event_queue = queue.Queue(maxsize=queue_size)
        self.event_callbacks: Dict[InputEventType, List[Callable]] = {
            event_type: [] for event_type in InputEventType
        }
        self.raw_event_callback: Optional[Callable] = None
        
        # Components
        self.input_queue = InputQueue(max_size=queue_size)
        self.polling_manager = PollingManager()
        
        # Listeners
        self.mouse_listener: Optional[MouseListener] = None
        self.keyboard_listener: Optional[KeyboardListener] = None
        
        # Performance optimization
        self._batch_size = 50  # Process events in batches
        self._sleep_duration = 0.0001  # 0.1ms sleep for better CPU usage
        self._max_sleep_duration = 0.001  # 1ms max sleep
        
        # Logging
        self.logger = logging.getLogger(__name__) if enable_logging else None
        
        # Performance tracking
        self._last_event_time = 0.0
        self._idle_cycles = 0
        self._max_idle_cycles = 1000  # After 1000 idle cycles, increase sleep
        
    def start(self) -> bool:
        """
        Start the input handler with optimized parallel initialization.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            return True
        
        try:
            with self._lock:
                self.is_running = True
                self.start_time = time.time()
                
                # Start components in parallel for faster initialization
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    # Submit all initialization tasks
                    mouse_future = executor.submit(self._start_mouse_listener)
                    keyboard_future = executor.submit(self._start_keyboard_listener)
                    polling_future = executor.submit(self._start_polling_manager)
                    queue_future = executor.submit(self._start_input_queue)
                    
                    # Wait for all components to start (with timeout)
                    try:
                        mouse_future.result(timeout=2.0)
                        keyboard_future.result(timeout=2.0)
                        polling_future.result(timeout=2.0)
                        queue_future.result(timeout=2.0)
                    except concurrent.futures.TimeoutError:
                        if self.logger:
                            self.logger.error("Component initialization timeout")
                        return False
                
                # Start processing thread last
                self._start_processing_thread()
                
                if self.logger:
                    self.logger.info("Input handler started successfully")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start input handler: {e}")
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the input handler with optimized cleanup.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_running:
            return True
        
        try:
            with self._lock:
                self.is_running = False
                
                # Stop listeners first
                if self.mouse_listener:
                    self.mouse_listener.stop()
                if self.keyboard_listener:
                    self.keyboard_listener.stop()
                
                # Stop components
                self.polling_manager.stop()
                self.input_queue.stop()
                
                # Wait for processing thread to finish
                if self.processing_thread and self.processing_thread.is_alive():
                    self.processing_thread.join(timeout=1.0)
                
                if self.logger:
                    self.logger.info("Input handler stopped successfully")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error stopping input handler: {e}")
            return False
    
    def _start_mouse_listener(self) -> None:
        """Start the mouse listener with optimized callbacks."""
        def on_mouse_move(x: int, y: int) -> None:
            if self.is_running:
                self._queue_event(InputEventType.MOUSE_MOVE, {"x": x, "y": y})
        
        def on_mouse_click(x: int, y: int, button: mouse.Button, pressed: bool) -> None:
            if self.is_running:
                event_type = InputEventType.MOUSE_PRESS if pressed else InputEventType.MOUSE_RELEASE
                self._queue_event(event_type, {
                    "x": x, "y": y, "button": button.name
                })
        
        def on_mouse_scroll(x: int, y: int, dx: int, dy: int) -> None:
            if self.is_running:
                self._queue_event(InputEventType.MOUSE_SCROLL, {
                    "x": x, "y": y, "dx": dx, "dy": dy
                })
        
        self.mouse_listener = MouseListener(
            on_move=on_mouse_move,
            on_click=on_mouse_click,
            on_scroll=on_mouse_scroll
        )
        self.mouse_listener.start()
    
    def _start_keyboard_listener(self) -> None:
        """Start the keyboard listener with optimized callbacks."""
        def on_key_press(key) -> None:
            if self.is_running:
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    key_code = key.vk if hasattr(key, 'vk') else ord(key_name) if len(key_name) == 1 else 0
                    self._queue_event(InputEventType.KEY_PRESS, {
                        "key": key_name, "key_code": key_code
                    })
                except Exception:
                    pass  # Ignore invalid keys
        
        def on_key_release(key) -> None:
            if self.is_running:
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    key_code = key.vk if hasattr(key, 'vk') else ord(key_name) if len(key_name) == 1 else 0
                    self._queue_event(InputEventType.KEY_RELEASE, {
                        "key": key_name, "key_code": key_code
                    })
                except Exception:
                    pass  # Ignore invalid keys
        
        self.keyboard_listener = KeyboardListener(
            on_press=on_key_press,
            on_release=on_key_release
        )
        self.keyboard_listener.start()
    
    def _start_polling_manager(self) -> None:
        """Start the polling manager."""
        self.polling_manager.set_mouse_polling_rate(1000)
        self.polling_manager.set_keyboard_polling_rate(1000)
        self.polling_manager.start()
    
    def _start_input_queue(self) -> None:
        """Start the input queue."""
        self.input_queue.start()
    
    def _start_processing_thread(self) -> None:
        """Start the optimized event processing thread."""
        self.processing_thread = threading.Thread(
            target=self._optimized_processing_loop,
            daemon=True,
            name="OptimizedInputProcessingThread"
        )
        self.processing_thread.start()
        
        # Reduced startup delay
        time.sleep(0.01)  # 10ms instead of 100ms
        
        if not self.processing_thread.is_alive():
            raise RuntimeError("Processing thread failed to start")
    
    def _optimized_processing_loop(self) -> None:
        """
        Optimized event processing loop with better CPU usage.
        
        Key optimizations:
        - Batch processing of events
        - Adaptive sleep duration
        - Reduced logging overhead
        - Better error handling
        """
        try:
            if self.logger:
                self.logger.info("Optimized processing thread started")
            
            current_sleep = self._sleep_duration
            
            while self.is_running:
                try:
                    events_processed_this_cycle = 0
                    batch_start_time = time.time()
                    
                    # Process events in batches for better performance
                    while events_processed_this_cycle < self._batch_size and self.is_running:
                        try:
                            # Use get_nowait for better performance
                            event = self.event_queue.get_nowait()
                            self._process_event(event)
                            self.events_processed += 1
                            events_processed_this_cycle += 1
                            self._last_event_time = time.time()
                            self._idle_cycles = 0
                            
                        except queue.Empty:
                            break  # No more events
                    
                    # Adaptive sleep based on activity
                    if events_processed_this_cycle == 0:
                        self._idle_cycles += 1
                        # Increase sleep duration during idle periods
                        if self._idle_cycles > self._max_idle_cycles:
                            current_sleep = min(current_sleep * 1.1, self._max_sleep_duration)
                        time.sleep(current_sleep)
                    else:
                        # Reset sleep duration when active
                        current_sleep = self._sleep_duration
                        # Only sleep if we processed a full batch
                        if events_processed_this_cycle >= self._batch_size:
                            time.sleep(0.0001)  # Very short sleep
                    
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error in processing cycle: {e}")
                    time.sleep(0.001)  # Small delay before retrying
            
            if self.logger:
                self.logger.info("Optimized processing thread stopped")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fatal error in processing loop: {e}")
            else:
                print(f"Fatal error in processing loop: {e}")
    
    def _queue_event(self, event_type: InputEventType, data: Dict[str, Any]) -> None:
        """
        Queue an event with optimized error handling.
        
        Args:
            event_type: Type of input event
            data: Event data
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
            # Queue is full, drop event silently for better performance
            self.events_dropped += 1
            
            # Only log every 1000th drop to reduce overhead
            if self.logger and self.events_dropped % 1000 == 0:
                self.logger.warning(f"Dropped {self.events_dropped} events due to full queue")
    
    def _process_event(self, event: InputEvent) -> None:
        """
        Process a single input event with optimized callback handling.
        
        Args:
            event: Input event to process
        """
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
            'drop_rate': self.events_dropped / (self.events_processed + self.events_dropped) if (self.events_processed + self.events_dropped) > 0 else 0,
            'idle_cycles': self._idle_cycles
        }
    
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
    
    def set_polling_rates(self, mouse_rate: int, keyboard_rate: int):
        """Set polling rates for mouse and keyboard."""
        self.polling_manager.set_mouse_polling_rate(mouse_rate)
        self.polling_manager.set_keyboard_polling_rate(keyboard_rate)
    
    def get_polling_stats(self):
        """Get polling manager statistics."""
        return self.polling_manager.get_polling_stats()


# Example usage and testing
if __name__ == "__main__":
    def on_mouse_move(event):
        print(f"Mouse moved: {event.data}")
    
    def on_key_press(event):
        print(f"Key pressed: {event.data}")
    
    # Create optimized input handler
    input_handler = OptimizedInputHandler(enable_logging=True)
    
    # Add event callbacks
    input_handler.add_event_callback(InputEventType.MOUSE_MOVE, on_mouse_move)
    input_handler.add_event_callback(InputEventType.KEY_PRESS, on_key_press)
    
    # Start the handler
    if input_handler.start():
        print("Optimized input handler started successfully")
        
        try:
            # Run for a while
            time.sleep(10)
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            input_handler.stop()
    else:
        print("Failed to start optimized input handler")
