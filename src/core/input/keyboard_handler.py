import time
import threading
from collections import deque
from typing import Callable, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from pynput import keyboard

from src.core.input.input_handler import InputHandler, InputEventType, InputEvent
from src.core.queue.input_queue import EventPriority


class NKROMode(Enum):
    """N-Key Rollover modes for keyboard handling."""
    DISABLED = "disabled"
    BASIC = "basic"      # 6-key rollover
    FULL = "full"        # Full NKRO
    GAMING = "gaming"    # Optimized for gaming


class RapidTriggerMode(Enum):
    """Rapid trigger modes for gaming keyboards."""
    DISABLED = "disabled"
    LINEAR = "linear"    # Linear activation
    EXPONENTIAL = "exponential"  # Exponential activation
    CUSTOM = "custom"    # Custom curve


@dataclass
class KeyState:
    """State information for a single key."""
    is_pressed: bool = False
    press_count: int = 0
    last_press_time: float = 0.0
    last_release_time: float = 0.0
    hold_duration: float = 0.0
    debounce_time: float = 0.0
    rapid_trigger_threshold: float = 0.0
    activation_point: float = 0.0  # For rapid trigger


@dataclass
class KeyboardStats:
    """Statistics for keyboard performance monitoring."""
    total_key_events: int = 0
    keys_pressed: int = 0
    keys_released: int = 0
    simultaneous_keys: int = 0
    max_simultaneous_keys: int = 0
    rapid_triggers: int = 0
    debounced_events: int = 0
    events_per_second: float = 0.0
    last_update: float = 0.0


class GamingKeyboardHandler:
    """
    Handles advanced keyboard input features for gaming, building upon the core InputHandler.
    Features include:
    - Enhanced key press/release tracking with timing
    - Key state management for complex gaming inputs
    - Debounce algorithms to prevent key chatter
    - Rapid key repeat detection and handling
    - Performance monitoring specific to keyboard events
    - Anti-ghosting simulation for simultaneous key presses
    """

    def __init__(self, input_handler: InputHandler, debounce_threshold: float = 0.05, enable_logging: bool = True):
        """
        Initialize the GamingKeyboardHandler.

        Args:
            input_handler: The core InputHandler instance
            debounce_threshold: Minimum time between key presses to avoid chatter (seconds)
            enable_logging: Whether to enable debug logging
        """
        self.input_handler = input_handler
        self.debounce_threshold = debounce_threshold
        self.enable_logging = enable_logging

        # Enhanced key state tracking
        self.key_states: Dict[keyboard.Key, KeyState] = {}
        self.last_key_press_time: Dict[keyboard.Key, float] = {}
        self.key_press_count: Dict[keyboard.Key, int] = {}
        
        # Gaming features
        self.nkro_mode = NKROMode.GAMING
        self.rapid_trigger_mode = RapidTriggerMode.DISABLED
        self.max_simultaneous_keys = 6  # Default 6-key rollover
        
        # Performance tracking
        self.stats = KeyboardStats()
        self.total_key_presses = 0
        self.total_key_releases = 0
        self.total_debounced_keys = 0
        self.total_rapid_keys = 0
        self.total_simultaneous_keys = 0
        
        # Currently pressed keys for simultaneous key tracking
        self.currently_pressed_keys: Set[keyboard.Key] = set()
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Rapid key detection
        self.rapid_key_threshold = 0.1  # 100ms for rapid key detection
        self.last_rapid_key_time: Dict[keyboard.Key, float] = {}
        
        # Lock for thread safety
        self._lock = threading.Lock()

        # Logger setup
        self.logger = None
        if enable_logging:
            import logging
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.INFO)

        # Register callbacks with the core input handler
        self.input_handler.add_event_callback(InputEventType.KEY_PRESS, self._on_key_press)
        self.input_handler.add_event_callback(InputEventType.KEY_RELEASE, self._on_key_release)

        if self.logger:
            self.logger.info("GamingKeyboardHandler initialized with debounce threshold: {}s".format(debounce_threshold))

    def _on_key_press(self, event: InputEvent) -> None:
        """
        Handle key press events with gaming optimizations.

        Args:
            event: The key press event from InputHandler
        """
        try:
            key_name = event.data['key']
            key_code = event.data['key_code']
            current_time = time.time()
            
            # Convert key name to pynput Key object
            key = self._get_key_from_name(key_name)
            if key is None:
                if self.logger:
                    self.logger.warning(f"Unknown key: {key_name}")
                return

            # Use high-frequency queuing for critical keyboard events
            if hasattr(self.input_handler, 'input_queue') and self.input_handler.input_queue.is_processing():
                # Enqueue for high-frequency processing with critical priority
                self.input_handler.enqueue_high_frequency_event(
                    InputEventType.KEY_PRESS,
                    event.data,
                    EventPriority.CRITICAL  # Critical priority for key presses
                )
                return
            
            # Fallback to direct processing if queue not available
            self._process_key_press_direct(event)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in key press handler: {e}")
    
    def _process_key_press_direct(self, event: InputEvent) -> None:
        """Process key press event directly (fallback method)."""
        try:
            key_name = event.data['key']
            key_code = event.data['key_code']
            current_time = time.time()
            
            # Convert key name to pynput Key object
            key = self._get_key_from_name(key_name)
            if key is None:
                if self.logger:
                    self.logger.warning(f"Unknown key: {key_name}")
                return

            with self._lock:
                # Check for debouncing
                time_since_last = 0.0
                if key in self.last_key_press_time:
                    time_since_last = current_time - self.last_key_press_time[key]
                    if time_since_last < self.debounce_threshold:
                        self.total_debounced_keys += 1
                        if self.logger:
                            self.logger.debug(f"Debounced key press: {key_name} (time since last: {time_since_last:.3f}s)")
                        return

                # Update key state
                self.key_states[key] = True
                self.last_key_press_time[key] = current_time
                self.key_press_count[key] = self.key_press_count.get(key, 0) + 1
                self.currently_pressed_keys.add(key)
                
                # Track simultaneous keys
                if len(self.currently_pressed_keys) > 1:
                    self.total_simultaneous_keys += 1
                    if self.logger:
                        self.logger.debug(f"Simultaneous keys detected: {len(self.currently_pressed_keys)} keys pressed")
                
                # Check for rapid key presses
                if key in self.last_rapid_key_time:
                    time_since_rapid = current_time - self.last_rapid_key_time[key]
                    if time_since_rapid < self.rapid_key_threshold:
                        self.total_rapid_keys += 1
                        if self.logger:
                            self.logger.debug(f"Rapid key press: {key_name} (time since last: {time_since_rapid:.3f}s)")
                
                self.last_rapid_key_time[key] = current_time
                self.total_key_presses += 1

                # Add gaming-specific data to the event
                event.data['is_simultaneous'] = len(self.currently_pressed_keys) > 1
                event.data['simultaneous_count'] = len(self.currently_pressed_keys)
                event.data['key_press_count'] = self.key_press_count[key]
                event.data['time_since_last_press'] = time_since_last

                if self.logger:
                    self.logger.debug(f"Key pressed: {key_name} (code: {key_code}) - Simultaneous: {len(self.currently_pressed_keys)} keys")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in key press handler: {e}")
            else:
                print(f"Error in key press handler: {e}")

    def _on_key_release(self, event: InputEvent) -> None:
        """
        Handle key release events with gaming optimizations.

        Args:
            event: The key release event from InputHandler
        """
        try:
            key_name = event.data['key']
            key_code = event.data['key_code']
            current_time = time.time()
            
            # Convert key name to pynput Key object
            key = self._get_key_from_name(key_name)
            if key is None:
                if self.logger:
                    self.logger.warning(f"Unknown key: {key_name}")
                return

            with self._lock:
                # Update key state
                self.key_states[key] = False
                self.currently_pressed_keys.discard(key)
                self.total_key_releases += 1

                # Calculate key hold duration
                hold_duration = 0.0
                if key in self.last_key_press_time:
                    hold_duration = current_time - self.last_key_press_time[key]

                # Add gaming-specific data to the event
                event.data['hold_duration'] = hold_duration
                event.data['remaining_pressed_keys'] = len(self.currently_pressed_keys)
                event.data['key_press_count'] = self.key_press_count.get(key, 0)

                if self.logger:
                    self.logger.debug(f"Key released: {key_name} (code: {key_code}) - Hold duration: {hold_duration:.3f}s")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in key release handler: {e}")
            else:
                print(f"Error in key release handler: {e}")

    def _get_key_from_name(self, key_name: str) -> Optional[keyboard.Key]:
        """
        Convert a key name string to a pynput Key object.

        Args:
            key_name: The key name string

        Returns:
            The corresponding Key object or None if not found
        """
        try:
            # Handle special keys
            if hasattr(keyboard.Key, key_name.lower()):
                return getattr(keyboard.Key, key_name.lower())
            
            # Handle regular character keys
            if len(key_name) == 1:
                return keyboard.KeyCode.from_char(key_name)
            
            # Handle function keys
            if key_name.startswith('f') and key_name[1:].isdigit():
                return getattr(keyboard.Key, key_name.lower(), None)
            
            # Handle other special cases
            special_keys = {
                'space': keyboard.Key.space,
                'enter': keyboard.Key.enter,
                'tab': keyboard.Key.tab,
                'backspace': keyboard.Key.backspace,
                'delete': keyboard.Key.delete,
                'shift': keyboard.Key.shift,
                'ctrl': keyboard.Key.ctrl,
                'alt': keyboard.Key.alt,
                'cmd': keyboard.Key.cmd,
                'up': keyboard.Key.up,
                'down': keyboard.Key.down,
                'left': keyboard.Key.left,
                'right': keyboard.Key.right,
            }
            
            return special_keys.get(key_name.lower())
            
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not convert key name '{key_name}' to Key object: {e}")
            return None

    def get_keyboard_stats(self) -> Dict[str, Any]:
        """
        Get current keyboard performance statistics.

        Returns:
            Dictionary containing keyboard performance metrics
        """
        with self._lock:
            return {
                "total_presses": self.total_key_presses,
                "total_releases": self.total_key_releases,
                "total_debounced": self.total_debounced_keys,
                "total_rapid_keys": self.total_rapid_keys,
                "total_simultaneous": self.total_simultaneous_keys,
                "currently_pressed_count": len(self.currently_pressed_keys),
                "currently_pressed_keys": [key.name if hasattr(key, 'name') else str(key) for key in self.currently_pressed_keys],
                "key_states": {key.name if hasattr(key, 'name') else str(key): state for key, state in self.key_states.items()},
                "debounce_threshold": self.debounce_threshold,
                "rapid_key_threshold": self.rapid_key_threshold,
            }

    def get_pressed_keys(self) -> Set[keyboard.Key]:
        """
        Get currently pressed keys.

        Returns:
            Set of currently pressed Key objects
        """
        with self._lock:
            return self.currently_pressed_keys.copy()

    def is_key_pressed(self, key: keyboard.Key) -> bool:
        """
        Check if a specific key is currently pressed.

        Args:
            key: The key to check

        Returns:
            True if the key is pressed, False otherwise
        """
        with self._lock:
            return self.key_states.get(key, False)

    def get_key_press_count(self, key: keyboard.Key) -> int:
        """
        Get the number of times a key has been pressed.

        Args:
            key: The key to check

        Returns:
            Number of times the key has been pressed
        """
        with self._lock:
            return self.key_press_count.get(key, 0)

    def reset_statistics(self) -> None:
        """Reset all keyboard statistics."""
        with self._lock:
            self.total_key_presses = 0
            self.total_key_releases = 0
            self.total_debounced_keys = 0
            self.total_rapid_keys = 0
            self.total_simultaneous_keys = 0
            self.key_press_count.clear()
            self.last_key_press_time.clear()
            self.last_rapid_key_time.clear()

    # Gaming Features Methods
    
    def set_nkro_mode(self, mode: NKROMode) -> None:
        """
        Set the N-Key Rollover mode.
        
        Args:
            mode: NKRO mode (DISABLED, BASIC, FULL, GAMING)
        """
        with self._lock:
            self.nkro_mode = mode
            
            # Set max simultaneous keys based on mode
            if mode == NKROMode.DISABLED:
                self.max_simultaneous_keys = 1
            elif mode == NKROMode.BASIC:
                self.max_simultaneous_keys = 6
            elif mode == NKROMode.FULL:
                self.max_simultaneous_keys = 104  # Full keyboard
            elif mode == NKROMode.GAMING:
                self.max_simultaneous_keys = 20  # Optimized for gaming
            
            if self.logger:
                self.logger.info(f"NKRO mode set to: {mode.value} (max keys: {self.max_simultaneous_keys})")
    
    def set_rapid_trigger_mode(self, mode: RapidTriggerMode) -> None:
        """
        Set the rapid trigger mode.
        
        Args:
            mode: Rapid trigger mode (DISABLED, LINEAR, EXPONENTIAL, CUSTOM)
        """
        with self._lock:
            self.rapid_trigger_mode = mode
            if self.logger:
                self.logger.info(f"Rapid trigger mode set to: {mode.value}")
    
    def set_rapid_trigger_threshold(self, key: keyboard.Key, threshold: float) -> None:
        """
        Set rapid trigger threshold for a specific key.
        
        Args:
            key: The key to set threshold for
            threshold: Activation threshold (0.0 to 1.0)
        """
        with self._lock:
            if key not in self.key_states:
                self.key_states[key] = KeyState()
            self.key_states[key].rapid_trigger_threshold = threshold
            if self.logger:
                self.logger.debug(f"Rapid trigger threshold for {key} set to: {threshold}")
    
    def get_key_state(self, key: keyboard.Key) -> Optional[KeyState]:
        """
        Get the current state of a key.
        
        Args:
            key: The key to get state for
            
        Returns:
            KeyState object or None if key not tracked
        """
        with self._lock:
            return self.key_states.get(key)
    
    def get_simultaneous_keys(self) -> Set[keyboard.Key]:
        """
        Get currently pressed keys.
        
        Returns:
            Set of currently pressed keys
        """
        with self._lock:
            return self.currently_pressed_keys.copy()
    
    def is_nkro_available(self) -> bool:
        """
        Check if NKRO is available for current simultaneous key count.
        
        Returns:
            True if NKRO is available, False otherwise
        """
        with self._lock:
            if self.nkro_mode == NKROMode.DISABLED:
                return len(self.currently_pressed_keys) < 1
            else:
                return len(self.currently_pressed_keys) < self.max_simultaneous_keys
    
    def get_keyboard_stats(self) -> KeyboardStats:
        """
        Get current keyboard statistics.
        
        Returns:
            KeyboardStats object with current performance data
        """
        with self._lock:
            # Update stats
            self.stats.total_key_events = self.total_key_presses + self.total_key_releases
            self.stats.keys_pressed = self.total_key_presses
            self.stats.keys_released = self.total_key_releases
            self.stats.simultaneous_keys = len(self.currently_pressed_keys)
            self.stats.max_simultaneous_keys = max(self.stats.max_simultaneous_keys, len(self.currently_pressed_keys))
            self.stats.rapid_triggers = self.total_rapid_keys
            self.stats.debounced_events = self.total_debounced_keys
            self.stats.last_update = time.time()
            
            return self.stats
    
    def set_debounce_threshold(self, threshold: float) -> None:
        """
        Set the debounce threshold for key presses.

        Args:
            threshold: New debounce threshold in seconds
        """
        with self._lock:
            self.debounce_threshold = threshold
            if self.logger:
                self.logger.info(f"Debounce threshold updated to: {threshold}s")

    def set_rapid_key_threshold(self, threshold: float) -> None:
        """
        Set the rapid key detection threshold.

        Args:
            threshold: New rapid key threshold in seconds
        """
        with self._lock:
            self.rapid_key_threshold = threshold
            if self.logger:
                self.logger.info(f"Rapid key threshold updated to: {threshold}s")

    def start_tracking(self) -> bool:
        """
        Start keyboard tracking by ensuring the underlying InputHandler is running.

        Returns:
            True if started successfully, False otherwise
        """
        if self.input_handler.is_running:
            if self.logger:
                self.logger.info("GamingKeyboardHandler started tracking.")
            return True
        else:
            if self.logger:
                self.logger.warning("InputHandler is not running. Cannot start GamingKeyboardHandler tracking.")
            return False

    def stop_tracking(self) -> None:
        """Stop keyboard tracking."""
        if self.logger:
            self.logger.info("GamingKeyboardHandler stopped tracking.")
