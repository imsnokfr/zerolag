"""
Rapid Key Actions and Advanced Features for ZeroLag

This module implements advanced keyboard optimizations including:
- Rapid Trigger emulation for dynamic key state resets
- Snap Tap/Rappy Snappy for handling opposite directions
- Turbo Mode for rapid key repeats
- Adaptive response tuning and actuation emulation
- Gaming-specific key optimizations

Features:
- Rapid Trigger: Dynamic key state resets based on press/release velocity
- Snap Tap: Prevents neutral states in opposite direction inputs (A+D)
- Turbo Mode: Rapid key repeat functionality
- Adaptive Response: Tuning based on user behavior
- Actuation Emulation: Simulate different key actuation points
"""

import time
import threading
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging
import math


class RapidActionType(Enum):
    """Types of rapid key actions."""
    RAPID_TRIGGER = "rapid_trigger"
    SNAP_TAP = "snap_tap"
    TURBO_MODE = "turbo_mode"
    ADAPTIVE_RESPONSE = "adaptive_response"
    ACTUATION_EMULATION = "actuation_emulation"


class KeyDirection(Enum):
    """Key direction for movement keys."""
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"
    FORWARD = "forward"
    BACKWARD = "backward"
    NEUTRAL = "neutral"


@dataclass
class RapidTriggerConfig:
    """Configuration for Rapid Trigger functionality."""
    enabled: bool = True
    threshold_ms: float = 10.0  # Velocity threshold for rapid trigger
    reset_delay_ms: float = 5.0  # Delay before key state reset
    min_press_duration_ms: float = 1.0  # Minimum press duration
    max_press_duration_ms: float = 100.0  # Maximum press duration
    velocity_smoothing: float = 0.1  # Smoothing factor for velocity calculation


@dataclass
class SnapTapConfig:
    """Configuration for Snap Tap functionality."""
    enabled: bool = True
    opposite_pairs: Dict[str, str] = field(default_factory=lambda: {
        'a': 'd', 'd': 'a',  # Left/Right movement
        'w': 's', 's': 'w',  # Forward/Backward movement
        'left': 'right', 'right': 'left',  # Arrow keys
        'up': 'down', 'down': 'up'  # Arrow keys
    })
    neutral_prevention_ms: float = 50.0  # Time to prevent neutral state
    overlap_tolerance_ms: float = 10.0  # Tolerance for key overlap


@dataclass
class TurboModeConfig:
    """Configuration for Turbo Mode functionality."""
    enabled: bool = True
    repeat_rate_ms: float = 50.0  # Repeat interval in milliseconds
    initial_delay_ms: float = 500.0  # Initial delay before first repeat
    max_repeats: int = 0  # Maximum repeats (0 = unlimited)
    acceleration_factor: float = 1.0  # Speed up factor over time


@dataclass
class AdaptiveResponseConfig:
    """Configuration for Adaptive Response functionality."""
    enabled: bool = True
    learning_rate: float = 0.1  # How quickly to adapt
    history_size: int = 100  # Number of events to remember
    adaptation_threshold: float = 0.1  # Threshold for adaptation
    response_tuning_range: Tuple[float, float] = (0.5, 2.0)  # Min/max response multiplier


@dataclass
class ActuationEmulationConfig:
    """Configuration for Actuation Emulation functionality."""
    enabled: bool = True
    actuation_point: float = 0.5  # Actuation point (0.0 to 1.0)
    linear_curve: bool = True  # Use linear or custom curve
    custom_curve: Optional[List[Tuple[float, float]]] = None  # Custom actuation curve
    hysteresis: float = 0.1  # Hysteresis to prevent bouncing


@dataclass
class KeyVelocity:
    """Key press/release velocity information."""
    press_velocity: float = 0.0  # Press velocity (ms)
    release_velocity: float = 0.0  # Release velocity (ms)
    average_velocity: float = 0.0  # Average velocity
    max_velocity: float = 0.0  # Maximum velocity
    min_velocity: float = 0.0  # Minimum velocity
    velocity_trend: float = 0.0  # Velocity trend (positive = increasing)


@dataclass
class RapidActionStats:
    """Statistics for rapid key actions."""
    rapid_trigger_events: int = 0
    snap_tap_events: int = 0
    turbo_mode_events: int = 0
    adaptive_response_adjustments: int = 0
    actuation_emulation_events: int = 0
    total_events_processed: int = 0
    average_processing_time_ms: float = 0.0
    last_update_time: float = 0.0


class RapidTrigger:
    """
    Rapid Trigger implementation for dynamic key state resets.
    
    Rapid Trigger allows keys to reset their state based on press/release velocity,
    enabling faster key repetition for gaming scenarios.
    """
    
    def __init__(self, config: RapidTriggerConfig):
        """
        Initialize Rapid Trigger.
        
        Args:
            config: Rapid Trigger configuration
        """
        self.config = config
        self.key_states: Dict[str, Dict[str, Any]] = {}
        self.velocity_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10))
        self.lock = threading.RLock()
    
    def process_key_event(self, key: str, pressed: bool, timestamp: float) -> Tuple[bool, Optional[float]]:
        """
        Process a key event for rapid trigger.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            timestamp: Event timestamp
            
        Returns:
            (should_process, reset_delay_ms)
        """
        if not self.config.enabled:
            return True, None
        
        with self.lock:
            try:
                if pressed:
                    return self._handle_key_press(key, timestamp)
                else:
                    return self._handle_key_release(key, timestamp)
            except Exception as e:
                logging.error(f"Error in rapid trigger: {e}")
                return True, None
    
    def _handle_key_press(self, key: str, timestamp: float) -> Tuple[bool, Optional[float]]:
        """Handle key press for rapid trigger."""
        if key not in self.key_states:
            self.key_states[key] = {
                'last_press_time': timestamp,
                'last_release_time': None,
                'press_count': 0,
                'velocity_history': deque(maxlen=10)
            }
        
        key_state = self.key_states[key]
        key_state['last_press_time'] = timestamp
        key_state['press_count'] += 1
        
        # Calculate velocity if we have previous data
        velocity = self._calculate_velocity(key, timestamp)
        if velocity is not None:
            key_state['velocity_history'].append(velocity)
            self.velocity_history[key].append(velocity)
        
        # Check if rapid trigger should activate
        if self._should_activate_rapid_trigger(key, velocity):
            # Calculate reset delay based on velocity
            reset_delay = self._calculate_reset_delay(key, velocity)
            return True, reset_delay
        
        return True, None
    
    def _handle_key_release(self, key: str, timestamp: float) -> Tuple[bool, Optional[float]]:
        """Handle key release for rapid trigger."""
        if key not in self.key_states:
            return True, None
        
        key_state = self.key_states[key]
        key_state['last_release_time'] = timestamp
        
        # Calculate release velocity
        if key_state['last_press_time']:
            press_duration = timestamp - key_state['last_press_time']
            release_velocity = 1000.0 / press_duration if press_duration > 0 else 0.0
            key_state['velocity_history'].append(release_velocity)
            self.velocity_history[key].append(release_velocity)
        
        return True, None
    
    def _calculate_velocity(self, key: str, timestamp: float) -> Optional[float]:
        """Calculate key press velocity."""
        if key not in self.key_states:
            return None
        
        key_state = self.key_states[key]
        if key_state['last_release_time'] is None:
            return None
        
        time_since_release = timestamp - key_state['last_release_time']
        if time_since_release <= 0:
            return None
        
        # Velocity in presses per second
        return 1000.0 / time_since_release
    
    def _should_activate_rapid_trigger(self, key: str, velocity: Optional[float]) -> bool:
        """Check if rapid trigger should activate for a key."""
        if velocity is None:
            return False
        
        # Check velocity threshold
        if velocity < (1000.0 / self.config.threshold_ms):
            return False
        
        # Check if we have enough velocity history
        if len(self.velocity_history[key]) < 3:
            return False
        
        # Check velocity trend
        recent_velocities = list(self.velocity_history[key])[-3:]
        if len(recent_velocities) >= 3:
            trend = (recent_velocities[-1] - recent_velocities[0]) / len(recent_velocities)
            if trend < 0:  # Decreasing velocity
                return False
        
        return True
    
    def _calculate_reset_delay(self, key: str, velocity: float) -> float:
        """Calculate reset delay based on velocity."""
        # Base delay
        base_delay = self.config.reset_delay_ms
        
        # Adjust based on velocity (higher velocity = shorter delay)
        velocity_factor = min(2.0, velocity / (1000.0 / self.config.threshold_ms))
        adjusted_delay = base_delay / velocity_factor
        
        # Apply smoothing
        if key in self.key_states and self.key_states[key]['velocity_history']:
            prev_delays = [d for d in self.key_states[key]['velocity_history'] if isinstance(d, float)]
            if prev_delays:
                avg_delay = sum(prev_delays) / len(prev_delays)
                adjusted_delay = (1 - self.config.velocity_smoothing) * adjusted_delay + \
                               self.config.velocity_smoothing * avg_delay
        
        return max(self.config.min_press_duration_ms, 
                  min(adjusted_delay, self.config.max_press_duration_ms))
    
    def get_key_velocity(self, key: str) -> Optional[KeyVelocity]:
        """Get velocity information for a key."""
        if key not in self.key_states or not self.velocity_history[key]:
            return None
        
        velocities = list(self.velocity_history[key])
        if not velocities:
            return None
        
        return KeyVelocity(
            press_velocity=velocities[-1] if velocities else 0.0,
            release_velocity=velocities[-2] if len(velocities) > 1 else 0.0,
            average_velocity=sum(velocities) / len(velocities),
            max_velocity=max(velocities),
            min_velocity=min(velocities),
            velocity_trend=velocities[-1] - velocities[0] if len(velocities) > 1 else 0.0
        )
    
    def reset_key_state(self, key: str):
        """Reset key state for rapid trigger."""
        with self.lock:
            if key in self.key_states:
                self.key_states[key]['last_press_time'] = None
                self.key_states[key]['last_release_time'] = None


class SnapTap:
    """
    Snap Tap implementation for handling opposite direction inputs.
    
    Snap Tap prevents neutral states when pressing opposite direction keys
    (like A+D in FPS games) by managing the timing of key releases.
    """
    
    def __init__(self, config: SnapTapConfig):
        """
        Initialize Snap Tap.
        
        Args:
            config: Snap Tap configuration
        """
        self.config = config
        self.active_keys: Set[str] = set()
        self.opposite_pairs: Dict[str, str] = config.opposite_pairs
        self.key_timings: Dict[str, float] = {}
        self.neutral_prevention: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def process_key_event(self, key: str, pressed: bool, timestamp: float) -> Tuple[bool, Optional[str]]:
        """
        Process a key event for snap tap.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            timestamp: Event timestamp
            
        Returns:
            (should_process, opposite_key_to_release)
        """
        if not self.config.enabled:
            return True, None
        
        with self.lock:
            try:
                if pressed:
                    return self._handle_key_press(key, timestamp)
                else:
                    return self._handle_key_release(key, timestamp)
            except Exception as e:
                logging.error(f"Error in snap tap: {e}")
                return True, None
    
    def _handle_key_press(self, key: str, timestamp: float) -> Tuple[bool, Optional[str]]:
        """Handle key press for snap tap."""
        self.active_keys.add(key)
        self.key_timings[key] = timestamp
        
        # Check for opposite key
        opposite_key = self.opposite_pairs.get(key)
        if opposite_key and opposite_key in self.active_keys:
            # Both opposite keys are active, prevent neutral state
            self.neutral_prevention[key] = timestamp + self.config.neutral_prevention_ms
            self.neutral_prevention[opposite_key] = timestamp + self.config.neutral_prevention_ms
        
        return True, None
    
    def _handle_key_release(self, key: str, timestamp: float) -> Tuple[bool, Optional[str]]:
        """Handle key release for snap tap."""
        if key not in self.active_keys:
            return True, None
        
        # Check if we should prevent neutral state
        if key in self.neutral_prevention and timestamp < self.neutral_prevention[key]:
            # Prevent neutral state by releasing opposite key first
            opposite_key = self.opposite_pairs.get(key)
            if opposite_key and opposite_key in self.active_keys:
                # Release opposite key first
                self.active_keys.discard(opposite_key)
                if opposite_key in self.neutral_prevention:
                    del self.neutral_prevention[opposite_key]
                return True, opposite_key
        
        # Normal release
        self.active_keys.discard(key)
        if key in self.neutral_prevention:
            del self.neutral_prevention[key]
        
        return True, None
    
    def get_active_keys(self) -> Set[str]:
        """Get currently active keys."""
        with self.lock:
            return self.active_keys.copy()
    
    def is_neutral_prevention_active(self, key: str) -> bool:
        """Check if neutral prevention is active for a key."""
        with self.lock:
            return key in self.neutral_prevention


class TurboMode:
    """
    Turbo Mode implementation for rapid key repeats.
    
    Turbo Mode automatically repeats key presses at configurable intervals,
    useful for rapid-fire actions in games.
    """
    
    def __init__(self, config: TurboModeConfig):
        """
        Initialize Turbo Mode.
        
        Args:
            config: Turbo Mode configuration
        """
        self.config = config
        self.turbo_keys: Dict[str, Dict[str, Any]] = {}
        self.turbo_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.RLock()
        self.callbacks: List[Callable[[str], None]] = []
    
    def start_turbo_mode(self, key: str, timestamp: float) -> bool:
        """
        Start turbo mode for a key.
        
        Args:
            key: Key name
            timestamp: Start timestamp
            
        Returns:
            True if turbo mode started successfully
        """
        if not self.config.enabled:
            return False
        
        with self.lock:
            if key in self.turbo_keys:
                return False  # Already in turbo mode
            
            self.turbo_keys[key] = {
                'start_time': timestamp,
                'last_repeat_time': timestamp,
                'repeat_count': 0,
                'next_repeat_time': timestamp + self.config.initial_delay_ms / 1000.0
            }
            
            # Start turbo thread if not running
            if not self.running:
                self.running = True
                self.turbo_thread = threading.Thread(
                    target=self._turbo_loop,
                    daemon=True,
                    name="TurboModeThread"
                )
                self.turbo_thread.start()
            
            return True
    
    def stop_turbo_mode(self, key: str) -> bool:
        """
        Stop turbo mode for a key.
        
        Args:
            key: Key name
            
        Returns:
            True if turbo mode stopped successfully
        """
        with self.lock:
            if key not in self.turbo_keys:
                return False
            
            del self.turbo_keys[key]
            
            # Stop turbo thread if no keys are in turbo mode
            if not self.turbo_keys and self.running:
                self.running = False
                if self.turbo_thread:
                    self.turbo_thread.join(timeout=1.0)
            
            return True
    
    def _turbo_loop(self):
        """Main turbo mode loop."""
        while self.running:
            try:
                current_time = time.time()
                keys_to_repeat = []
                
                with self.lock:
                    for key, turbo_data in self.turbo_keys.items():
                        if current_time >= turbo_data['next_repeat_time']:
                            keys_to_repeat.append(key)
                
                # Process repeats
                for key in keys_to_repeat:
                    self._process_turbo_repeat(key, current_time)
                
                # Sleep for a short time
                time.sleep(0.001)  # 1ms sleep
                
            except Exception as e:
                logging.error(f"Error in turbo loop: {e}")
                time.sleep(0.01)
    
    def _process_turbo_repeat(self, key: str, current_time: float):
        """Process a turbo repeat for a key."""
        with self.lock:
            if key not in self.turbo_keys:
                return
            
            turbo_data = self.turbo_keys[key]
            turbo_data['repeat_count'] += 1
            turbo_data['last_repeat_time'] = current_time
            
            # Check max repeats
            if self.config.max_repeats > 0 and turbo_data['repeat_count'] >= self.config.max_repeats:
                del self.turbo_keys[key]
                return
            
            # Calculate next repeat time with acceleration
            base_interval = self.config.repeat_rate_ms / 1000.0
            acceleration = self.config.acceleration_factor ** turbo_data['repeat_count']
            next_interval = base_interval / acceleration
            
            turbo_data['next_repeat_time'] = current_time + next_interval
            
            # Trigger callback
            for callback in self.callbacks:
                try:
                    callback(key)
                except Exception as e:
                    logging.error(f"Error in turbo callback: {e}")
    
    def add_callback(self, callback: Callable[[str], None]):
        """Add callback for turbo repeats."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str], None]):
        """Remove turbo callback."""
        try:
            self.callbacks.remove(callback)
        except ValueError:
            pass
    
    def is_turbo_active(self, key: str) -> bool:
        """Check if turbo mode is active for a key."""
        with self.lock:
            return key in self.turbo_keys
    
    def get_turbo_stats(self, key: str) -> Optional[Dict[str, Any]]:
        """Get turbo mode statistics for a key."""
        with self.lock:
            if key not in self.turbo_keys:
                return None
            
            turbo_data = self.turbo_keys[key]
            return {
                'start_time': turbo_data['start_time'],
                'repeat_count': turbo_data['repeat_count'],
                'last_repeat_time': turbo_data['last_repeat_time'],
                'next_repeat_time': turbo_data['next_repeat_time']
            }


class AdaptiveResponse:
    """
    Adaptive Response implementation for tuning based on user behavior.
    
    Adaptive Response learns from user input patterns and adjusts
    response times and sensitivities accordingly.
    """
    
    def __init__(self, config: AdaptiveResponseConfig):
        """
        Initialize Adaptive Response.
        
        Args:
            config: Adaptive Response configuration
        """
        self.config = config
        self.key_histories: Dict[str, deque] = defaultdict(lambda: deque(maxlen=config.history_size))
        self.response_multipliers: Dict[str, float] = defaultdict(lambda: 1.0)
        self.adaptation_counts: Dict[str, int] = defaultdict(int)
        self.lock = threading.RLock()
    
    def process_key_event(self, key: str, pressed: bool, timestamp: float) -> float:
        """
        Process a key event for adaptive response.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            timestamp: Event timestamp
            
        Returns:
            Response multiplier for this key
        """
        if not self.config.enabled:
            return 1.0
        
        with self.lock:
            try:
                # Record event
                self.key_histories[key].append({
                    'pressed': pressed,
                    'timestamp': timestamp
                })
                
                # Analyze pattern and adapt
                self._analyze_and_adapt(key)
                
                return self.response_multipliers[key]
                
            except Exception as e:
                logging.error(f"Error in adaptive response: {e}")
                return 1.0
    
    def _analyze_and_adapt(self, key: str):
        """Analyze key pattern and adapt response."""
        history = self.key_histories[key]
        if len(history) < 5:  # Need at least 5 events
            return
        
        # Calculate timing patterns
        press_times = [event['timestamp'] for event in history if event['pressed']]
        release_times = [event['timestamp'] for event in history if not event['pressed']]
        
        if len(press_times) < 2 or len(release_times) < 2:
            return
        
        # Calculate average press interval
        press_intervals = [press_times[i] - press_times[i-1] for i in range(1, len(press_times))]
        avg_press_interval = sum(press_intervals) / len(press_intervals) if press_intervals else 0
        
        # Calculate average hold duration
        hold_durations = []
        for i, event in enumerate(history):
            if event['pressed']:
                # Find next release
                for j in range(i+1, len(history)):
                    if not history[j]['pressed']:
                        hold_durations.append(history[j]['timestamp'] - event['timestamp'])
                        break
        
        avg_hold_duration = sum(hold_durations) / len(hold_durations) if hold_durations else 0
        
        # Adapt based on patterns
        self._adapt_to_pattern(key, avg_press_interval, avg_hold_duration)
    
    def _adapt_to_pattern(self, key: str, avg_press_interval: float, avg_hold_duration: float):
        """Adapt response based on detected patterns."""
        current_multiplier = self.response_multipliers[key]
        
        # Detect rapid tapping (short intervals)
        if avg_press_interval < 0.1:  # Less than 100ms between presses
            # Increase response for rapid tapping
            new_multiplier = min(current_multiplier * 1.1, self.config.response_tuning_range[1])
        # Detect slow tapping (long intervals)
        elif avg_press_interval > 0.5:  # More than 500ms between presses
            # Decrease response for slow tapping
            new_multiplier = max(current_multiplier * 0.9, self.config.response_tuning_range[0])
        # Detect short holds
        elif avg_hold_duration < 0.05:  # Less than 50ms hold
            # Increase response for quick releases
            new_multiplier = min(current_multiplier * 1.05, self.config.response_tuning_range[1])
        # Detect long holds
        elif avg_hold_duration > 1.0:  # More than 1 second hold
            # Decrease response for long holds
            new_multiplier = max(current_multiplier * 0.95, self.config.response_tuning_range[0])
        else:
            # No significant pattern, slight adjustment towards 1.0
            new_multiplier = current_multiplier + (1.0 - current_multiplier) * self.config.learning_rate
        
        # Apply adaptation
        if abs(new_multiplier - current_multiplier) > self.config.adaptation_threshold:
            self.response_multipliers[key] = new_multiplier
            self.adaptation_counts[key] += 1
    
    def get_response_multiplier(self, key: str) -> float:
        """Get current response multiplier for a key."""
        with self.lock:
            return self.response_multipliers[key]
    
    def get_adaptation_stats(self, key: str) -> Dict[str, Any]:
        """Get adaptation statistics for a key."""
        with self.lock:
            history = self.key_histories[key]
            return {
                'event_count': len(history),
                'response_multiplier': self.response_multipliers[key],
                'adaptation_count': self.adaptation_counts[key],
                'last_event_time': history[-1]['timestamp'] if history else 0
            }


class ActuationEmulation:
    """
    Actuation Emulation implementation for simulating different key actuation points.
    
    Actuation Emulation allows keys to trigger at different points in their travel,
    simulating different mechanical switch characteristics.
    """
    
    def __init__(self, config: ActuationEmulationConfig):
        """
        Initialize Actuation Emulation.
        
        Args:
            config: Actuation Emulation configuration
        """
        self.config = config
        self.key_states: Dict[str, Dict[str, Any]] = {}
        self.actuation_curves: Dict[str, List[Tuple[float, float]]] = {}
        self.lock = threading.RLock()
    
    def process_key_event(self, key: str, pressed: bool, timestamp: float, pressure: float = 0.5) -> bool:
        """
        Process a key event for actuation emulation.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            timestamp: Event timestamp
            pressure: Key pressure (0.0 to 1.0)
            
        Returns:
            True if key should actuate
        """
        if not self.config.enabled:
            return pressed
        
        with self.lock:
            try:
                if pressed:
                    return self._handle_key_press(key, timestamp, pressure)
                else:
                    return self._handle_key_release(key, timestamp)
            except Exception as e:
                logging.error(f"Error in actuation emulation: {e}")
                return pressed
    
    def _handle_key_press(self, key: str, timestamp: float, pressure: float) -> bool:
        """Handle key press for actuation emulation."""
        if key not in self.key_states:
            self.key_states[key] = {
                'last_press_time': None,
                'last_release_time': None,
                'actuation_point': self.config.actuation_point,
                'pressure_history': deque(maxlen=10)
            }
        
        key_state = self.key_states[key]
        key_state['last_press_time'] = timestamp
        key_state['pressure_history'].append(pressure)
        
        # Calculate actuation point
        actuation_point = self._calculate_actuation_point(key, pressure)
        
        # Check if key should actuate
        return pressure >= actuation_point
    
    def _handle_key_release(self, key: str, timestamp: float) -> bool:
        """Handle key release for actuation emulation."""
        if key not in self.key_states:
            return True
        
        key_state = self.key_states[key]
        key_state['last_release_time'] = timestamp
        
        # Always allow release
        return True
    
    def _calculate_actuation_point(self, key: str, pressure: float) -> float:
        """Calculate actuation point for a key."""
        if self.config.linear_curve:
            return self.config.actuation_point
        
        # Use custom curve if available
        if key in self.actuation_curves and self.actuation_curves[key]:
            curve = self.actuation_curves[key]
            # Find the appropriate point on the curve
            for i in range(len(curve) - 1):
                if curve[i][0] <= pressure <= curve[i+1][0]:
                    # Linear interpolation
                    t = (pressure - curve[i][0]) / (curve[i+1][0] - curve[i][0])
                    return curve[i][1] + t * (curve[i+1][1] - curve[i][1])
            return curve[-1][1] if curve else self.config.actuation_point
        
        return self.config.actuation_point
    
    def set_custom_curve(self, key: str, curve: List[Tuple[float, float]]):
        """Set custom actuation curve for a key."""
        with self.lock:
            self.actuation_curves[key] = curve
    
    def get_actuation_point(self, key: str) -> float:
        """Get current actuation point for a key."""
        with self.lock:
            if key in self.key_states:
                return self.key_states[key]['actuation_point']
            return self.config.actuation_point


class RapidActionsEngine:
    """
    Main engine for rapid key actions and advanced features.
    
    Coordinates all rapid action components and provides a unified interface
    for advanced keyboard optimizations.
    """
    
    def __init__(self, 
                 rapid_trigger_config: Optional[RapidTriggerConfig] = None,
                 snap_tap_config: Optional[SnapTapConfig] = None,
                 turbo_mode_config: Optional[TurboModeConfig] = None,
                 adaptive_response_config: Optional[AdaptiveResponseConfig] = None,
                 actuation_emulation_config: Optional[ActuationEmulationConfig] = None):
        """
        Initialize Rapid Actions Engine.
        
        Args:
            rapid_trigger_config: Rapid Trigger configuration
            snap_tap_config: Snap Tap configuration
            turbo_mode_config: Turbo Mode configuration
            adaptive_response_config: Adaptive Response configuration
            actuation_emulation_config: Actuation Emulation configuration
        """
        self.rapid_trigger_config = rapid_trigger_config or RapidTriggerConfig()
        self.snap_tap_config = snap_tap_config or SnapTapConfig()
        self.turbo_mode_config = turbo_mode_config or TurboModeConfig()
        self.adaptive_response_config = adaptive_response_config or AdaptiveResponseConfig()
        self.actuation_emulation_config = actuation_emulation_config or ActuationEmulationConfig()
        
        # Initialize components
        self.rapid_trigger = RapidTrigger(self.rapid_trigger_config)
        self.snap_tap = SnapTap(self.snap_tap_config)
        self.turbo_mode = TurboMode(self.turbo_mode_config)
        self.adaptive_response = AdaptiveResponse(self.adaptive_response_config)
        self.actuation_emulation = ActuationEmulation(self.actuation_emulation_config)
        
        # Statistics
        self.stats = RapidActionStats()
        self.lock = threading.RLock()
        
        # Callbacks
        self.callbacks: List[Callable[[str, RapidActionType], None]] = []
    
    def process_key_event(self, key: str, pressed: bool, timestamp: Optional[float] = None, pressure: float = 0.5) -> Dict[str, Any]:
        """
        Process a key event through all rapid action components.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            timestamp: Event timestamp
            pressure: Key pressure (0.0 to 1.0)
            
        Returns:
            Dictionary with processing results
        """
        if timestamp is None:
            timestamp = time.time()
        
        start_time = time.time()
        
        with self.lock:
            try:
                result = {
                    'should_process': True,
                    'reset_delay_ms': None,
                    'opposite_key_to_release': None,
                    'response_multiplier': 1.0,
                    'should_actuate': pressed,
                    'rapid_trigger_active': False,
                    'snap_tap_active': False,
                    'turbo_mode_active': False,
                    'adaptive_response_active': False,
                    'actuation_emulation_active': False
                }
                
                # Process through Rapid Trigger
                if self.rapid_trigger_config.enabled:
                    should_process, reset_delay = self.rapid_trigger.process_key_event(key, pressed, timestamp)
                    result['should_process'] = should_process
                    result['reset_delay_ms'] = reset_delay
                    result['rapid_trigger_active'] = reset_delay is not None
                    if result['rapid_trigger_active']:
                        self.stats.rapid_trigger_events += 1
                
                # Process through Snap Tap
                if self.snap_tap_config.enabled:
                    should_process, opposite_key = self.snap_tap.process_key_event(key, pressed, timestamp)
                    result['should_process'] = should_process
                    result['opposite_key_to_release'] = opposite_key
                    result['snap_tap_active'] = opposite_key is not None
                    if result['snap_tap_active']:
                        self.stats.snap_tap_events += 1
                
                # Process through Adaptive Response
                if self.adaptive_response_config.enabled:
                    response_multiplier = self.adaptive_response.process_key_event(key, pressed, timestamp)
                    result['response_multiplier'] = response_multiplier
                    result['adaptive_response_active'] = abs(response_multiplier - 1.0) > 0.01
                    if result['adaptive_response_active']:
                        self.stats.adaptive_response_adjustments += 1
                
                # Process through Actuation Emulation
                if self.actuation_emulation_config.enabled:
                    should_actuate = self.actuation_emulation.process_key_event(key, pressed, timestamp, pressure)
                    result['should_actuate'] = should_actuate
                    result['actuation_emulation_active'] = not pressed or should_actuate
                    if result['actuation_emulation_active']:
                        self.stats.actuation_emulation_events += 1
                
                # Handle Turbo Mode
                if self.turbo_mode_config.enabled:
                    if pressed:
                        turbo_started = self.turbo_mode.start_turbo_mode(key, timestamp)
                        result['turbo_mode_active'] = turbo_started
                        if turbo_started:
                            self.stats.turbo_mode_events += 1
                    else:
                        self.turbo_mode.stop_turbo_mode(key)
                
                # Update statistics
                self.stats.total_events_processed += 1
                self.stats.last_update_time = timestamp
                
                # Calculate processing time
                processing_time = (time.time() - start_time) * 1000
                self.stats.average_processing_time_ms = (
                    (self.stats.average_processing_time_ms * (self.stats.total_events_processed - 1) + processing_time) /
                    self.stats.total_events_processed
                )
                
                # Trigger callbacks
                for callback in self.callbacks:
                    try:
                        if result['rapid_trigger_active']:
                            callback(key, RapidActionType.RAPID_TRIGGER)
                        if result['snap_tap_active']:
                            callback(key, RapidActionType.SNAP_TAP)
                        if result['turbo_mode_active']:
                            callback(key, RapidActionType.TURBO_MODE)
                        if result['adaptive_response_active']:
                            callback(key, RapidActionType.ADAPTIVE_RESPONSE)
                        if result['actuation_emulation_active']:
                            callback(key, RapidActionType.ACTUATION_EMULATION)
                    except Exception as e:
                        logging.error(f"Error in rapid action callback: {e}")
                
                return result
                
            except Exception as e:
                logging.error(f"Error in rapid actions engine: {e}")
                return {
                    'should_process': True,
                    'reset_delay_ms': None,
                    'opposite_key_to_release': None,
                    'response_multiplier': 1.0,
                    'should_actuate': pressed,
                    'rapid_trigger_active': False,
                    'snap_tap_active': False,
                    'turbo_mode_active': False,
                    'adaptive_response_active': False,
                    'actuation_emulation_active': False
                }
    
    def add_callback(self, callback: Callable[[str, RapidActionType], None]):
        """Add callback for rapid action events."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[str, RapidActionType], None]):
        """Remove rapid action callback."""
        try:
            self.callbacks.remove(callback)
        except ValueError:
            pass
    
    def get_stats(self) -> RapidActionStats:
        """Get rapid action statistics."""
        with self.lock:
            return RapidActionStats(
                rapid_trigger_events=self.stats.rapid_trigger_events,
                snap_tap_events=self.stats.snap_tap_events,
                turbo_mode_events=self.stats.turbo_mode_events,
                adaptive_response_adjustments=self.stats.adaptive_response_adjustments,
                actuation_emulation_events=self.stats.actuation_emulation_events,
                total_events_processed=self.stats.total_events_processed,
                average_processing_time_ms=self.stats.average_processing_time_ms,
                last_update_time=self.stats.last_update_time
            )
    
    def reset_stats(self):
        """Reset all statistics."""
        with self.lock:
            self.stats = RapidActionStats()
    
    def get_key_velocity(self, key: str) -> Optional[KeyVelocity]:
        """Get velocity information for a key."""
        return self.rapid_trigger.get_key_velocity(key)
    
    def get_active_keys(self) -> Set[str]:
        """Get currently active keys."""
        return self.snap_tap.get_active_keys()
    
    def is_turbo_active(self, key: str) -> bool:
        """Check if turbo mode is active for a key."""
        return self.turbo_mode.is_turbo_active(key)
    
    def get_response_multiplier(self, key: str) -> float:
        """Get response multiplier for a key."""
        return self.adaptive_response.get_response_multiplier(key)
    
    def get_actuation_point(self, key: str) -> float:
        """Get actuation point for a key."""
        return self.actuation_emulation.get_actuation_point(key)


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create rapid actions engine
    engine = RapidActionsEngine()
    
    # Add callback for testing
    def rapid_action_callback(key: str, action_type: RapidActionType):
        print(f"Rapid action: {key} -> {action_type.value}")
    
    engine.add_callback(rapid_action_callback)
    
    print("Testing Rapid Key Actions and Advanced Features...")
    
    # Test rapid trigger
    print("\n1. Testing Rapid Trigger...")
    test_keys = ['space', 'shift', 'ctrl']
    
    for i in range(20):
        key = random.choice(test_keys)
        pressed = random.choice([True, False])
        
        result = engine.process_key_event(key, pressed)
        if result['rapid_trigger_active']:
            print(f"Rapid trigger activated for {key}: {result['reset_delay_ms']:.2f}ms")
        
        time.sleep(0.01)
    
    # Test snap tap
    print("\n2. Testing Snap Tap...")
    movement_keys = ['a', 'd', 'w', 's']
    
    for i in range(10):
        key = random.choice(movement_keys)
        pressed = random.choice([True, False])
        
        result = engine.process_key_event(key, pressed)
        if result['snap_tap_active']:
            print(f"Snap tap activated for {key}: release {result['opposite_key_to_release']}")
        
        time.sleep(0.05)
    
    # Test turbo mode
    print("\n3. Testing Turbo Mode...")
    turbo_key = 'space'
    
    # Start turbo mode
    result = engine.process_key_event(turbo_key, True)
    if result['turbo_mode_active']:
        print(f"Turbo mode started for {turbo_key}")
        
        # Let it run for a bit
        time.sleep(2.0)
        
        # Stop turbo mode
        result = engine.process_key_event(turbo_key, False)
        print(f"Turbo mode stopped for {turbo_key}")
    
    # Test adaptive response
    print("\n4. Testing Adaptive Response...")
    adaptive_key = 'w'
    
    for i in range(30):
        pressed = random.choice([True, False])
        result = engine.process_key_event(adaptive_key, pressed)
        
        if result['adaptive_response_active']:
            print(f"Adaptive response for {adaptive_key}: {result['response_multiplier']:.2f}x")
        
        time.sleep(0.02)
    
    # Test actuation emulation
    print("\n5. Testing Actuation Emulation...")
    actuation_key = 'space'
    
    for pressure in [0.3, 0.5, 0.7, 0.9]:
        result = engine.process_key_event(actuation_key, True, pressure=pressure)
        print(f"Actuation emulation for {actuation_key} at {pressure:.1f}: {result['should_actuate']}")
    
    # Get statistics
    print("\n6. Statistics:")
    stats = engine.get_stats()
    print(f"Total events processed: {stats.total_events_processed}")
    print(f"Rapid trigger events: {stats.rapid_trigger_events}")
    print(f"Snap tap events: {stats.snap_tap_events}")
    print(f"Turbo mode events: {stats.turbo_mode_events}")
    print(f"Adaptive response adjustments: {stats.adaptive_response_adjustments}")
    print(f"Actuation emulation events: {stats.actuation_emulation_events}")
    print(f"Average processing time: {stats.average_processing_time_ms:.3f}ms")
    
    print("\nRapid Key Actions testing completed!")
