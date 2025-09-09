"""
Ultra-Optimized Input Handler for ZeroLag Application

This module provides an ultra-optimized version of the input handler with
aggressive performance optimizations to achieve <1% CPU usage.

Key ultra-optimizations:
- Minimal thread overhead
- Aggressive sleep management
- Event batching with larger batches
- Reduced logging and error handling overhead
- Optimized data structures
- Lazy initialization
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


class UltraOptimizedInputHandler:
    """
    Ultra-optimized input handler with aggressive performance optimizations.
    
    Key ultra-optimizations:
    - Minimal CPU usage through aggressive sleep management
    - Large batch processing for better efficiency
    - Reduced thread overhead
    - Optimized data structures
    - Lazy component initialization
    """
    
    def __init__(self, 
                 queue_size: int = 10000,
                 enable_logging: bool = False,
                 mouse_polling_rate: int = 1000,
                 keyboard_polling_rate: int = 1000):
        """
        Initialize the ultra-optimized input handler.
        
        Args:
            queue_size: Maximum size of the event queue
            enable_logging: Whether to enable debug logging (disabled by default for performance)
            mouse_polling_rate: Mouse polling rate in Hz
            keyboard_polling_rate: Keyboard polling rate in Hz
        """
        self.queue_size = queue_size
        self.is_running = False
        self.start_time = 0.0
        self.events_processed = 0
        self.events_dropped = 0
        
        # Threading - minimal overhead
        self._lock = threading.RLock()
        self.processing_thread: Optional[threading.Thread] = None
        
        # Event handling - optimized data structures
        self.event_queue = queue.Queue(maxsize=queue_size)
        self.event_callbacks: Dict[InputEventType, List[Callable]] = {
            event_type: [] for event_type in InputEventType
        }
        self.raw_event_callback: Optional[Callable] = None
        
        # Components - lazy initialization
        self.input_queue: Optional[InputQueue] = None
        self.polling_manager: Optional[PollingManager] = None
        
        # Listeners
        self.mouse_listener: Optional[MouseListener] = None
        self.keyboard_listener: Optional[KeyboardListener] = None
        
        # Ultra-performance optimization settings
        self._batch_size = 200  # Larger batches for better efficiency
        self._min_sleep = 0.001  # 1ms minimum sleep
        self._max_sleep = 0.01   # 10ms maximum sleep
        self._current_sleep = self._min_sleep
        
        # Aggressive idle management
        self._idle_cycles = 0
        self._max_idle_before_sleep = 50  # Reduce from 1000 to 50
        self._sleep_increment = 0.001  # Increase sleep by 1ms each time
        
        # Logging - minimal overhead
        self.logger = None  # Disabled by default for performance
        
        # Performance tracking - minimal overhead
        self._last_event_time = 0.0
        self._events_since_last_check = 0
        self._last_stats_time = 0.0
        
    def start(self) -> bool:
        """
        Start the input handler with ultra-optimized initialization.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            return True
        
        try:
            with self._lock:
                self.is_running = True
                self.start_time = time.time()
                
                # Start only essential components first
                self._start_mouse_listener()
                self._start_keyboard_listener()
                self._start_processing_thread()
                
                # Lazy initialization of other components
                # (Initialize only when needed)
                
                return True
                
        except Exception as e:
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
                
                # Stop listeners
                if self.mouse_listener:
                    self.mouse_listener.stop()
                if self.keyboard_listener:
                    self.keyboard_listener.stop()
                
                # Stop components if initialized
                if self.polling_manager:
                    self.polling_manager.stop()
                if self.input_queue:
                    self.input_queue.stop()
                
                # Wait for processing thread
                if self.processing_thread and self.processing_thread.is_alive():
                    self.processing_thread.join(timeout=0.5)  # Shorter timeout
                
                return True
                
        except Exception:
            return False
    
    def _start_mouse_listener(self) -> None:
        """Start the mouse listener with minimal overhead."""
        def on_mouse_move(x: int, y: int) -> None:
            if self.is_running:
                self._queue_event_fast(InputEventType.MOUSE_MOVE, {"x": x, "y": y})
        
        def on_mouse_click(x: int, y: int, button: mouse.Button, pressed: bool) -> None:
            if self.is_running:
                event_type = InputEventType.MOUSE_PRESS if pressed else InputEventType.MOUSE_RELEASE
                self._queue_event_fast(event_type, {
                    "x": x, "y": y, "button": button.name
                })
        
        def on_mouse_scroll(x: int, y: int, dx: int, dy: int) -> None:
            if self.is_running:
                self._queue_event_fast(InputEventType.MOUSE_SCROLL, {
                    "x": x, "y": y, "dx": dx, "dy": dy
                })
        
        self.mouse_listener = MouseListener(
            on_move=on_mouse_move,
            on_click=on_mouse_click,
            on_scroll=on_mouse_scroll
        )
        self.mouse_listener.start()
    
    def _start_keyboard_listener(self) -> None:
        """Start the keyboard listener with minimal overhead."""
        def on_key_press(key) -> None:
            if self.is_running:
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    key_code = key.vk if hasattr(key, 'vk') else ord(key_name) if len(key_name) == 1 else 0
                    self._queue_event_fast(InputEventType.KEY_PRESS, {
                        "key": key_name, "key_code": key_code
                    })
                except Exception:
                    pass  # Ignore invalid keys
        
        def on_key_release(key) -> None:
            if self.is_running:
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    key_code = key.vk if hasattr(key, 'vk') else ord(key_name) if len(key_name) == 1 else 0
                    self._queue_event_fast(InputEventType.KEY_RELEASE, {
                        "key": key_name, "key_code": key_code
                    })
                except Exception:
                    pass  # Ignore invalid keys
        
        self.keyboard_listener = KeyboardListener(
            on_press=on_key_press,
            on_release=on_key_release
        )
        self.keyboard_listener.start()
    
    def _start_processing_thread(self) -> None:
        """Start the ultra-optimized event processing thread."""
        self.processing_thread = threading.Thread(
            target=self._ultra_optimized_processing_loop,
            daemon=True,
            name="UltraOptimizedInputProcessingThread"
        )
        self.processing_thread.start()
        
        # Minimal startup delay
        time.sleep(0.005)  # 5ms instead of 10ms
        
        if not self.processing_thread.is_alive():
            raise RuntimeError("Processing thread failed to start")
    
    def _ultra_optimized_processing_loop(self) -> None:
        """
        Ultra-optimized event processing loop with aggressive CPU usage reduction.
        
        Key ultra-optimizations:
        - Large batch processing
        - Aggressive sleep management
        - Minimal logging overhead
        - Optimized idle detection
        """
        try:
            while self.is_running:
                try:
                    events_processed_this_cycle = 0
                    
                    # Process events in large batches for maximum efficiency
                    while events_processed_this_cycle < self._batch_size and self.is_running:
                        try:
                            # Use get_nowait for maximum performance
                            event = self.event_queue.get_nowait()
                            self._process_event_fast(event)
                            self.events_processed += 1
                            events_processed_this_cycle += 1
                            self._last_event_time = time.time()
                            self._idle_cycles = 0
                            
                        except queue.Empty:
                            break  # No more events
                    
                    # Aggressive sleep management for minimal CPU usage
                    if events_processed_this_cycle == 0:
                        self._idle_cycles += 1
                        
                        # Increase sleep duration aggressively during idle periods
                        if self._idle_cycles > self._max_idle_before_sleep:
                            self._current_sleep = min(
                                self._current_sleep + self._sleep_increment,
                                self._max_sleep
                            )
                        
                        # Sleep for the current duration
                        time.sleep(self._current_sleep)
                    else:
                        # Reset sleep duration when active
                        self._current_sleep = self._min_sleep
                        # Only sleep if we processed a full batch
                        if events_processed_this_cycle >= self._batch_size:
                            time.sleep(0.0001)  # Very short sleep
                    
                except Exception:
                    # Minimal error handling for performance
                    time.sleep(0.001)  # Small delay before retrying
                
        except Exception:
            # Minimal error handling for performance
            pass
    
    def _queue_event_fast(self, event_type: InputEventType, data: Dict[str, Any]) -> None:
        """
        Ultra-fast event queuing with minimal overhead.
        
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
            # Drop event silently for maximum performance
            self.events_dropped += 1
    
    def _process_event_fast(self, event: InputEvent) -> None:
        """
        Ultra-fast event processing with minimal overhead.
        
        Args:
            event: Input event to process
        """
        # Call raw event callback if set
        if self.raw_event_callback:
            try:
                self.raw_event_callback(event)
            except Exception:
                pass  # Ignore errors for performance
        
        # Call specific event type callbacks
        callbacks = self.event_callbacks.get(event.event_type, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                pass  # Ignore errors for performance
    
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
        Get current performance statistics with minimal overhead.
        
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
            'idle_cycles': self._idle_cycles,
            'current_sleep': self._current_sleep
        }
    
    def _lazy_init_components(self):
        """Lazy initialization of components when needed."""
        if self.input_queue is None:
            self.input_queue = InputQueue(max_size=self.queue_size)
            self.input_queue.start()
        
        if self.polling_manager is None:
            self.polling_manager = PollingManager()
            self.polling_manager.set_mouse_polling_rate(1000)
            self.polling_manager.set_keyboard_polling_rate(1000)
            self.polling_manager.start()
    
    def enqueue_high_frequency_event(self, event_type: InputEventType, data: Dict[str, Any], priority: EventPriority = EventPriority.NORMAL):
        """
        Enqueue an event for high-frequency processing.
        
        Args:
            event_type: Type of the input event
            data: Event data
            priority: Event priority for processing
        """
        # Lazy initialize components if needed
        self._lazy_init_components()
        
        return self.input_queue.enqueue(
            event_type=event_type.value,
            data=data,
            priority=priority,
            source="input_handler"
        )
    
    def get_queue_stats(self):
        """Get input queue statistics."""
        if self.input_queue is None:
            return None
        return self.input_queue.get_stats()
    
    def set_queue_mode(self, mode: QueueMode):
        """Set the input queue processing mode."""
        if self.input_queue is None:
            self._lazy_init_components()
        self.input_queue.set_mode(mode)
    
    def set_polling_rates(self, mouse_rate: int, keyboard_rate: int):
        """Set polling rates for mouse and keyboard."""
        if self.polling_manager is None:
            self._lazy_init_components()
        self.polling_manager.set_mouse_polling_rate(mouse_rate)
        self.polling_manager.set_keyboard_polling_rate(keyboard_rate)
    
    def get_polling_stats(self):
        """Get polling manager statistics."""
        if self.polling_manager is None:
            return None
        return self.polling_manager.get_polling_stats()


# Example usage and testing
if __name__ == "__main__":
    def on_mouse_move(event):
        print(f"Mouse moved: {event.data}")
    
    def on_key_press(event):
        print(f"Key pressed: {event.data}")
    
    # Create ultra-optimized input handler
    input_handler = UltraOptimizedInputHandler()
    
    # Add event callbacks
    input_handler.add_event_callback(InputEventType.MOUSE_MOVE, on_mouse_move)
    input_handler.add_event_callback(InputEventType.KEY_PRESS, on_key_press)
    
    # Start the handler
    if input_handler.start():
        print("Ultra-optimized input handler started successfully")
        
        try:
            # Run for a while
            time.sleep(10)
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            input_handler.stop()
    else:
        print("Failed to start ultra-optimized input handler")
