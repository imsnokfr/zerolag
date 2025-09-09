"""
Power-Saving Input Handler for ZeroLag Application

This module provides a power-saving version of the input handler that
aggressively reduces CPU usage during idle periods to achieve <1% CPU usage.

Key power-saving features:
- Aggressive idle detection and sleep management
- Dynamic polling rate adjustment based on activity
- Power-saving mode that reduces CPU usage to near-zero when idle
- Smart wake-up on input activity
- Minimal overhead during active periods
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


class PowerSavingInputHandler:
    """
    Power-saving input handler with aggressive CPU usage reduction.
    
    Key power-saving features:
    - Aggressive idle detection and sleep management
    - Dynamic polling rate adjustment
    - Power-saving mode for minimal CPU usage
    - Smart wake-up on activity
    """
    
    def __init__(self, 
                 queue_size: int = 10000,
                 enable_logging: bool = False,
                 mouse_polling_rate: int = 1000,
                 keyboard_polling_rate: int = 1000):
        """
        Initialize the power-saving input handler.
        
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
        self.input_queue: Optional[InputQueue] = None
        self.polling_manager: Optional[PollingManager] = None
        
        # Listeners
        self.mouse_listener: Optional[MouseListener] = None
        self.keyboard_listener: Optional[KeyboardListener] = None
        
        # Power-saving settings
        self._batch_size = 100  # Moderate batch size
        self._min_sleep = 0.001  # 1ms minimum sleep
        self._max_sleep = 0.1    # 100ms maximum sleep (aggressive)
        self._current_sleep = self._min_sleep
        
        # Aggressive idle management
        self._idle_cycles = 0
        self._max_idle_before_sleep = 10  # Very aggressive - sleep after 10 idle cycles
        self._sleep_increment = 0.005  # Increase sleep by 5ms each time
        self._power_save_threshold = 20  # Enter power save after 20 idle cycles
        
        # Power-saving mode
        self._power_save_mode = False
        self._power_save_sleep = 0.05  # 50ms sleep in power save mode
        
        # Activity tracking
        self._last_event_time = 0.0
        self._activity_window = 1.0  # 1 second activity window
        self._events_in_window = 0
        self._window_start_time = 0.0
        
        # Logging
        self.logger = None  # Disabled by default for performance
        
    def start(self) -> bool:
        """
        Start the power-saving input handler.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            return True
        
        try:
            with self._lock:
                self.is_running = True
                self.start_time = time.time()
                self._window_start_time = time.time()
                
                # Start components
                self._start_mouse_listener()
                self._start_keyboard_listener()
                self._start_processing_thread()
                
                return True
                
        except Exception as e:
            self.is_running = False
            return False
    
    def stop(self) -> bool:
        """
        Stop the power-saving input handler.
        
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
                
                # Stop components
                if self.polling_manager:
                    self.polling_manager.stop()
                if self.input_queue:
                    self.input_queue.stop()
                
                # Wait for processing thread
                if self.processing_thread and self.processing_thread.is_alive():
                    self.processing_thread.join(timeout=0.5)
                
                return True
                
        except Exception:
            return False
    
    def _start_mouse_listener(self) -> None:
        """Start the mouse listener."""
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
        """Start the keyboard listener."""
        def on_key_press(key) -> None:
            if self.is_running:
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    key_code = key.vk if hasattr(key, 'vk') else ord(key_name) if len(key_name) == 1 else 0
                    self._queue_event_fast(InputEventType.KEY_PRESS, {
                        "key": key_name, "key_code": key_code
                    })
                except Exception:
                    pass
        
        def on_key_release(key) -> None:
            if self.is_running:
                try:
                    key_name = key.char if hasattr(key, 'char') and key.char else str(key)
                    key_code = key.vk if hasattr(key, 'vk') else ord(key_name) if len(key_name) == 1 else 0
                    self._queue_event_fast(InputEventType.KEY_RELEASE, {
                        "key": key_name, "key_code": key_code
                    })
                except Exception:
                    pass
        
        self.keyboard_listener = KeyboardListener(
            on_press=on_key_press,
            on_release=on_key_release
        )
        self.keyboard_listener.start()
    
    def _start_processing_thread(self) -> None:
        """Start the power-saving event processing thread."""
        self.processing_thread = threading.Thread(
            target=self._power_saving_processing_loop,
            daemon=True,
            name="PowerSavingInputProcessingThread"
        )
        self.processing_thread.start()
        
        time.sleep(0.005)  # 5ms startup delay
        
        if not self.processing_thread.is_alive():
            raise RuntimeError("Processing thread failed to start")
    
    def _power_saving_processing_loop(self) -> None:
        """
        Power-saving event processing loop with aggressive CPU usage reduction.
        
        Key power-saving features:
        - Aggressive idle detection
        - Dynamic sleep duration adjustment
        - Power-saving mode for minimal CPU usage
        - Smart wake-up on activity
        """
        try:
            while self.is_running:
                try:
                    events_processed_this_cycle = 0
                    
                    # Process events in batches
                    while events_processed_this_cycle < self._batch_size and self.is_running:
                        try:
                            event = self.event_queue.get_nowait()
                            self._process_event_fast(event)
                            self.events_processed += 1
                            events_processed_this_cycle += 1
                            self._last_event_time = time.time()
                            self._idle_cycles = 0
                            self._events_in_window += 1
                            
                        except queue.Empty:
                            break
                    
                    # Aggressive power-saving logic
                    if events_processed_this_cycle == 0:
                        self._idle_cycles += 1
                        
                        # Check if we should enter power-saving mode
                        if self._idle_cycles > self._power_save_threshold:
                            if not self._power_save_mode:
                                self._power_save_mode = True
                                if self.logger:
                                    self.logger.info("Entering power-saving mode")
                        
                        # Adjust sleep duration based on idle time
                        if self._power_save_mode:
                            # In power-saving mode, use longer sleep
                            time.sleep(self._power_save_sleep)
                        else:
                            # Gradually increase sleep duration
                            if self._idle_cycles > self._max_idle_before_sleep:
                                self._current_sleep = min(
                                    self._current_sleep + self._sleep_increment,
                                    self._max_sleep
                                )
                            time.sleep(self._current_sleep)
                    else:
                        # Reset power-saving state when active
                        if self._power_save_mode:
                            self._power_save_mode = False
                            if self.logger:
                                self.logger.info("Exiting power-saving mode")
                        
                        self._current_sleep = self._min_sleep
                        
                        # Only sleep if we processed a full batch
                        if events_processed_this_cycle >= self._batch_size:
                            time.sleep(0.0001)  # Very short sleep
                    
                    # Update activity window
                    self._update_activity_window()
                    
                except Exception:
                    time.sleep(0.001)  # Small delay before retrying
                
        except Exception:
            pass  # Minimal error handling for performance
    
    def _update_activity_window(self) -> None:
        """Update the activity window for smart power management."""
        current_time = time.time()
        
        # Reset window if it's been more than the window duration
        if current_time - self._window_start_time > self._activity_window:
            self._events_in_window = 0
            self._window_start_time = current_time
    
    def _queue_event_fast(self, event_type: InputEventType, data: Dict[str, Any]) -> None:
        """
        Fast event queuing with minimal overhead.
        
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
            
            self.event_queue.put_nowait(event)
            
        except queue.Full:
            self.events_dropped += 1
    
    def _process_event_fast(self, event: InputEvent) -> None:
        """
        Fast event processing with minimal overhead.
        
        Args:
            event: Input event to process
        """
        # Call raw event callback if set
        if self.raw_event_callback:
            try:
                self.raw_event_callback(event)
            except Exception:
                pass
        
        # Call specific event type callbacks
        callbacks = self.event_callbacks.get(event.event_type, [])
        for callback in callbacks:
            try:
                callback(event)
            except Exception:
                pass
    
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
                pass
    
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
            'idle_cycles': self._idle_cycles,
            'current_sleep': self._current_sleep,
            'power_save_mode': self._power_save_mode,
            'events_in_window': self._events_in_window
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
    
    # Create power-saving input handler
    input_handler = PowerSavingInputHandler()
    
    # Add event callbacks
    input_handler.add_event_callback(InputEventType.MOUSE_MOVE, on_mouse_move)
    input_handler.add_event_callback(InputEventType.KEY_PRESS, on_key_press)
    
    # Start the handler
    if input_handler.start():
        print("Power-saving input handler started successfully")
        
        try:
            # Run for a while
            time.sleep(10)
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            input_handler.stop()
    else:
        print("Failed to start power-saving input handler")
