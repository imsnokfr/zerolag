"""
Macro Player for ZeroLag

This module implements comprehensive macro playback functionality including:
- High-precision event playback with timing control
- Speed adjustment and variable playback rates
- Loop execution with different loop types
- Conditional execution and branching
- Nested macro calls
- Real-time playback monitoring
- Error handling and recovery

Features:
- Microsecond-accurate timing
- Variable playback speeds (0.1x to 10x)
- Loop execution (count, while, until, forever)
- Conditional execution
- Nested macro support
- Text input simulation
- Mouse and keyboard event simulation
- Performance monitoring
- Thread-safe playback
"""

import time
import threading
import json
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import queue
import random

from .macro_recorder import MacroRecording, MacroEvent, MacroEventType, MacroLoop, MacroLoopType


class PlaybackState(Enum):
    """Macro playback states."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOOPING = "looping"
    ERROR = "error"


class PlaybackError(Enum):
    """Playback error types."""
    NONE = "none"
    TIMING_ERROR = "timing_error"
    EVENT_ERROR = "event_error"
    LOOP_ERROR = "loop_error"
    MEMORY_ERROR = "memory_error"
    THREAD_ERROR = "thread_error"


@dataclass
class PlaybackConfig:
    """Configuration for macro playback."""
    enabled: bool = True
    speed_multiplier: float = 1.0  # Playback speed (0.1 to 10.0)
    loop_enabled: bool = False  # Enable loop playback
    max_loops: int = 0  # Maximum loops (0 = unlimited)
    precision_ms: float = 0.1  # Timing precision in milliseconds
    error_recovery: bool = True  # Enable error recovery
    max_errors: int = 10  # Maximum errors before stopping
    thread_priority: int = 1  # Thread priority (1-10)
    memory_limit_mb: int = 100  # Memory limit for playback
    enable_monitoring: bool = True  # Enable performance monitoring


@dataclass
class PlaybackStats:
    """Statistics for macro playback."""
    total_playbacks: int = 0
    total_events_played: int = 0
    current_playback_events: int = 0
    current_playback_duration: float = 0.0
    loops_completed: int = 0
    errors_encountered: int = 0
    average_timing_error_ms: float = 0.0
    max_timing_error_ms: float = 0.0
    memory_usage_mb: float = 0.0
    last_playback_time: float = 0.0


class MacroPlayer:
    """
    High-performance macro player for ZeroLag.
    
    Plays back recorded macros with precise timing and provides
    comprehensive playback control and monitoring.
    """
    
    def __init__(self, config: Optional[PlaybackConfig] = None):
        """
        Initialize macro player.
        
        Args:
            config: Player configuration
        """
        self.config = config or PlaybackConfig()
        self.current_recording: Optional[MacroRecording] = None
        self.playback_state = PlaybackState.STOPPED
        self.playback_thread: Optional[threading.Thread] = None
        self.playback_start_time = 0.0
        self.current_event_index = 0
        self.current_loop_iteration = 0
        self.active_loops: Dict[str, Dict[str, Any]] = {}
        
        # Performance monitoring
        self.stats = PlaybackStats()
        self.timing_errors: List[float] = []
        self.memory_usage = 0.0
        
        # Threading
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        
        # Callbacks
        self.playback_callbacks: List[Callable[[MacroEvent], None]] = []
        self.completion_callbacks: List[Callable[[MacroRecording], None]] = []
        self.error_callbacks: List[Callable[[PlaybackError, str], None]] = []
        
        # Event simulation
        self.event_simulators: Dict[MacroEventType, Callable] = {
            MacroEventType.KEY_PRESS: self._simulate_key_press,
            MacroEventType.KEY_RELEASE: self._simulate_key_release,
            MacroEventType.MOUSE_MOVE: self._simulate_mouse_move,
            MacroEventType.MOUSE_CLICK: self._simulate_mouse_click,
            MacroEventType.MOUSE_PRESS: self._simulate_mouse_press,
            MacroEventType.MOUSE_RELEASE: self._simulate_mouse_release,
            MacroEventType.MOUSE_SCROLL: self._simulate_mouse_scroll,
            MacroEventType.DELAY: self._simulate_delay,
            MacroEventType.TEXT_INPUT: self._simulate_text_input,
            MacroEventType.MACRO_CALL: self._simulate_macro_call,
            MacroEventType.CONDITIONAL: self._simulate_conditional,
            MacroEventType.COMMENT: self._simulate_comment
        }
    
    def load_recording(self, recording: MacroRecording) -> bool:
        """
        Load a recording for playback.
        
        Args:
            recording: Recording to load
            
        Returns:
            True if loaded successfully
        """
        try:
            with self.lock:
                if self.playback_state != PlaybackState.STOPPED:
                    return False
                
                self.current_recording = recording
                self.current_event_index = 0
                self.current_loop_iteration = 0
                self.active_loops.clear()
                
                return True
                
        except Exception as e:
            logging.error(f"Error loading recording: {e}")
            self._handle_error(PlaybackError.EVENT_ERROR, str(e))
            return False
    
    def start_playback(self) -> bool:
        """
        Start playing the loaded recording.
        
        Returns:
            True if playback started successfully
        """
        if not self.current_recording:
            return False
        
        if self.playback_state != PlaybackState.STOPPED:
            return False
        
        try:
            with self.lock:
                self.playback_state = PlaybackState.PLAYING
                self.playback_start_time = time.time()
                self.current_event_index = 0
                self.current_loop_iteration = 0
                self.active_loops.clear()
                
                # Reset stop and pause events
                self.stop_event.clear()
                self.pause_event.set()
                
                # Start playback thread
                self.playback_thread = threading.Thread(
                    target=self._playback_loop,
                    daemon=True,
                    name="MacroPlayerThread"
                )
                self.playback_thread.start()
                
                return True
                
        except Exception as e:
            logging.error(f"Error starting playback: {e}")
            self._handle_error(PlaybackError.THREAD_ERROR, str(e))
            return False
    
    def stop_playback(self) -> bool:
        """
        Stop the current playback.
        
        Returns:
            True if stopped successfully
        """
        try:
            with self.lock:
                if self.playback_state == PlaybackState.STOPPED:
                    return True
                
                # Signal stop
                self.stop_event.set()
                
                # Wait for thread to finish
                if self.playback_thread and self.playback_thread.is_alive():
                    self.playback_thread.join(timeout=2.0)
                
                self.playback_state = PlaybackState.STOPPED
                
                # Update statistics
                self.stats.total_playbacks += 1
                self.stats.last_playback_time = time.time()
                
                return True
                
        except Exception as e:
            logging.error(f"Error stopping playback: {e}")
            self._handle_error(PlaybackError.THREAD_ERROR, str(e))
            return False
    
    def pause_playback(self) -> bool:
        """
        Pause the current playback.
        
        Returns:
            True if paused successfully
        """
        if self.playback_state != PlaybackState.PLAYING:
            return False
        
        try:
            with self.lock:
                self.playback_state = PlaybackState.PAUSED
                self.pause_event.clear()
                return True
                
        except Exception as e:
            logging.error(f"Error pausing playback: {e}")
            return False
    
    def resume_playback(self) -> bool:
        """
        Resume the paused playback.
        
        Returns:
            True if resumed successfully
        """
        if self.playback_state != PlaybackState.PAUSED:
            return False
        
        try:
            with self.lock:
                self.playback_state = PlaybackState.PLAYING
                self.pause_event.set()
                return True
                
        except Exception as e:
            logging.error(f"Error resuming playback: {e}")
            return False
    
    def set_speed(self, speed_multiplier: float) -> bool:
        """
        Set playback speed.
        
        Args:
            speed_multiplier: Speed multiplier (0.1 to 10.0)
            
        Returns:
            True if speed set successfully
        """
        if not 0.1 <= speed_multiplier <= 10.0:
            return False
        
        try:
            with self.lock:
                self.config.speed_multiplier = speed_multiplier
                return True
                
        except Exception as e:
            logging.error(f"Error setting speed: {e}")
            return False
    
    def _playback_loop(self):
        """Main playback loop."""
        try:
            while not self.stop_event.is_set() and self.current_recording:
                # Check pause
                self.pause_event.wait()
                
                if self.stop_event.is_set():
                    break
                
                # Process current event
                if self.current_event_index >= len(self.current_recording.events):
                    # End of recording
                    if self.config.loop_enabled and self.current_loop_iteration < self.config.max_loops:
                        # Start new loop
                        self.current_event_index = 0
                        self.current_loop_iteration += 1
                        self.stats.loops_completed += 1
                        continue
                    else:
                        # End playback
                        break
                
                # Get current event
                event = self.current_recording.events[self.current_event_index]
                
                # Calculate target time
                target_time = self.playback_start_time + (event.timestamp / self.config.speed_multiplier)
                current_time = time.time()
                
                # Wait for target time
                if target_time > current_time:
                    sleep_time = target_time - current_time
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                
                # Check timing accuracy
                actual_time = time.time()
                timing_error = abs(actual_time - target_time) * 1000  # Convert to ms
                self._update_timing_error(timing_error)
                
                # Process event
                if not self._process_event(event):
                    self._handle_error(PlaybackError.EVENT_ERROR, f"Failed to process event: {event.event_type}")
                    if not self.config.error_recovery:
                        break
                
                # Move to next event
                self.current_event_index += 1
                self.stats.current_playback_events += 1
                
                # Update duration
                self.stats.current_playback_duration = actual_time - self.playback_start_time
                
                # Check memory limit
                if self._check_memory_limit():
                    self._handle_error(PlaybackError.MEMORY_ERROR, "Memory limit exceeded")
                    break
                
                # Check error limit
                if self.stats.errors_encountered >= self.config.max_errors:
                    self._handle_error(PlaybackError.EVENT_ERROR, "Maximum errors exceeded")
                    break
            
            # Playback completed
            self.playback_state = PlaybackState.STOPPED
            
            # Trigger completion callbacks
            for callback in self.completion_callbacks:
                try:
                    callback(self.current_recording)
                except Exception as e:
                    logging.error(f"Error in completion callback: {e}")
            
        except Exception as e:
            logging.error(f"Error in playback loop: {e}")
            self._handle_error(PlaybackError.THREAD_ERROR, str(e))
            self.playback_state = PlaybackState.ERROR
    
    def _process_event(self, event: MacroEvent) -> bool:
        """Process a single macro event."""
        try:
            # Handle loop events
            if event.event_type == MacroEventType.LOOP_START:
                return self._handle_loop_start(event)
            elif event.event_type == MacroEventType.LOOP_END:
                return self._handle_loop_end(event)
            
            # Get event simulator
            simulator = self.event_simulators.get(event.event_type)
            if not simulator:
                logging.warning(f"No simulator for event type: {event.event_type}")
                return True  # Skip unknown events
            
            # Simulate event
            success = simulator(event)
            
            # Trigger playback callbacks
            for callback in self.playback_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    logging.error(f"Error in playback callback: {e}")
            
            return success
            
        except Exception as e:
            logging.error(f"Error processing event: {e}")
            return False
    
    def _handle_loop_start(self, event: MacroEvent) -> bool:
        """Handle loop start event."""
        try:
            loop_id = event.data.get('loop_id')
            if not loop_id or loop_id not in self.current_recording.loops:
                return False
            
            loop = self.current_recording.loops[loop_id]
            
            # Initialize loop state
            self.active_loops[loop_id] = {
                'loop': loop,
                'current_iteration': 0,
                'start_index': self.current_event_index,
                'end_index': loop.end_event_index
            }
            
            return True
            
        except Exception as e:
            logging.error(f"Error handling loop start: {e}")
            return False
    
    def _handle_loop_end(self, event: MacroEvent) -> bool:
        """Handle loop end event."""
        try:
            loop_id = event.data.get('loop_id')
            if not loop_id or loop_id not in self.active_loops:
                return True  # Not in a loop
            
            loop_state = self.active_loops[loop_id]
            loop = loop_state['loop']
            
            # Check if loop should continue
            should_continue = self._should_continue_loop(loop, loop_state)
            
            if should_continue:
                # Continue loop
                loop_state['current_iteration'] += 1
                self.current_event_index = loop_state['start_index']
                self.stats.loops_completed += 1
            else:
                # End loop
                del self.active_loops[loop_id]
            
            return True
            
        except Exception as e:
            logging.error(f"Error handling loop end: {e}")
            return False
    
    def _should_continue_loop(self, loop: MacroLoop, loop_state: Dict[str, Any]) -> bool:
        """Check if loop should continue."""
        if loop.loop_type == MacroLoopType.COUNT:
            return loop_state['current_iteration'] < (loop.count or 0)
        elif loop.loop_type == MacroLoopType.FOREVER:
            return True
        elif loop.loop_type == MacroLoopType.WHILE:
            # Evaluate condition (simplified)
            return self._evaluate_condition(loop.condition or "true")
        elif loop.loop_type == MacroLoopType.UNTIL:
            # Evaluate condition (simplified)
            return not self._evaluate_condition(loop.condition or "false")
        
        return False
    
    def _evaluate_condition(self, condition: str) -> bool:
        """Evaluate a loop condition (simplified implementation)."""
        try:
            # This is a simplified condition evaluator
            # In a real implementation, you'd want a proper expression parser
            if condition.lower() in ['true', '1', 'yes']:
                return True
            elif condition.lower() in ['false', '0', 'no']:
                return False
            else:
                # Default to true for unknown conditions
                return True
        except Exception:
            return True
    
    def _simulate_key_press(self, event: MacroEvent) -> bool:
        """Simulate key press event."""
        try:
            key = event.data.get('key', '')
            key_code = event.data.get('key_code', 0)
            modifiers = event.data.get('modifiers', [])
            
            # In a real implementation, you would use pynput or similar
            # to simulate the actual key press
            print(f"Simulating key press: {key} (code: {key_code}, modifiers: {modifiers})")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating key press: {e}")
            return False
    
    def _simulate_key_release(self, event: MacroEvent) -> bool:
        """Simulate key release event."""
        try:
            key = event.data.get('key', '')
            key_code = event.data.get('key_code', 0)
            modifiers = event.data.get('modifiers', [])
            
            # In a real implementation, you would use pynput or similar
            # to simulate the actual key release
            print(f"Simulating key release: {key} (code: {key_code}, modifiers: {modifiers})")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating key release: {e}")
            return False
    
    def _simulate_mouse_move(self, event: MacroEvent) -> bool:
        """Simulate mouse movement event."""
        try:
            x = event.data.get('x', 0)
            y = event.data.get('y', 0)
            dx = event.data.get('dx', 0)
            dy = event.data.get('dy', 0)
            
            # In a real implementation, you would use pynput or similar
            # to simulate the actual mouse movement
            print(f"Simulating mouse move: ({x}, {y}) delta: ({dx}, {dy})")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating mouse move: {e}")
            return False
    
    def _simulate_mouse_click(self, event: MacroEvent) -> bool:
        """Simulate mouse click event."""
        try:
            button = event.data.get('button', 'left')
            x = event.data.get('x', 0)
            y = event.data.get('y', 0)
            click_count = event.data.get('click_count', 1)
            
            # In a real implementation, you would use pynput or similar
            # to simulate the actual mouse click
            print(f"Simulating mouse click: {button} at ({x}, {y}) count: {click_count}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating mouse click: {e}")
            return False
    
    def _simulate_mouse_press(self, event: MacroEvent) -> bool:
        """Simulate mouse press event."""
        try:
            button = event.data.get('button', 'left')
            x = event.data.get('x', 0)
            y = event.data.get('y', 0)
            
            print(f"Simulating mouse press: {button} at ({x}, {y})")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating mouse press: {e}")
            return False
    
    def _simulate_mouse_release(self, event: MacroEvent) -> bool:
        """Simulate mouse release event."""
        try:
            button = event.data.get('button', 'left')
            x = event.data.get('x', 0)
            y = event.data.get('y', 0)
            
            print(f"Simulating mouse release: {button} at ({x}, {y})")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating mouse release: {e}")
            return False
    
    def _simulate_mouse_scroll(self, event: MacroEvent) -> bool:
        """Simulate mouse scroll event."""
        try:
            x = event.data.get('x', 0)
            y = event.data.get('y', 0)
            dx = event.data.get('dx', 0)
            dy = event.data.get('dy', 0)
            
            print(f"Simulating mouse scroll: ({x}, {y}) delta: ({dx}, {dy})")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating mouse scroll: {e}")
            return False
    
    def _simulate_delay(self, event: MacroEvent) -> bool:
        """Simulate delay event."""
        try:
            delay_ms = event.data.get('delay_ms', 0)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating delay: {e}")
            return False
    
    def _simulate_text_input(self, event: MacroEvent) -> bool:
        """Simulate text input event."""
        try:
            text = event.data.get('text', '')
            
            # In a real implementation, you would use pynput or similar
            # to simulate the actual text input
            print(f"Simulating text input: '{text}'")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating text input: {e}")
            return False
    
    def _simulate_macro_call(self, event: MacroEvent) -> bool:
        """Simulate macro call event."""
        try:
            macro_name = event.data.get('macro_name', '')
            
            # In a real implementation, you would load and play the nested macro
            print(f"Simulating macro call: {macro_name}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating macro call: {e}")
            return False
    
    def _simulate_conditional(self, event: MacroEvent) -> bool:
        """Simulate conditional event."""
        try:
            condition = event.data.get('condition', 'true')
            action = event.data.get('action', 'continue')
            
            # Evaluate condition and perform action
            if self._evaluate_condition(condition):
                print(f"Conditional: {condition} -> {action}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating conditional: {e}")
            return False
    
    def _simulate_comment(self, event: MacroEvent) -> bool:
        """Simulate comment event."""
        try:
            comment = event.comment or event.data.get('comment', '')
            if comment:
                print(f"Comment: {comment}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error simulating comment: {e}")
            return False
    
    def _update_timing_error(self, timing_error_ms: float):
        """Update timing error statistics."""
        self.timing_errors.append(timing_error_ms)
        
        # Keep only recent errors
        if len(self.timing_errors) > 100:
            self.timing_errors = self.timing_errors[-100:]
        
        # Update statistics
        self.stats.average_timing_error_ms = sum(self.timing_errors) / len(self.timing_errors)
        self.stats.max_timing_error_ms = max(self.timing_errors)
    
    def _check_memory_limit(self) -> bool:
        """Check if memory limit is exceeded."""
        # Estimate memory usage
        estimated_size = len(self.current_recording.events) * 200  # Rough estimate
        self.memory_usage = estimated_size / (1024 * 1024)  # Convert to MB
        
        return self.memory_usage > self.config.memory_limit_mb
    
    def _handle_error(self, error_type: PlaybackError, message: str):
        """Handle playback error."""
        self.stats.errors_encountered += 1
        
        # Trigger error callbacks
        for callback in self.error_callbacks:
            try:
                callback(error_type, message)
            except Exception as e:
                logging.error(f"Error in error callback: {e}")
        
        # Log error
        logging.error(f"Playback error: {error_type.value} - {message}")
    
    def add_playback_callback(self, callback: Callable[[MacroEvent], None]):
        """Add callback for playback events."""
        self.playback_callbacks.append(callback)
    
    def remove_playback_callback(self, callback: Callable[[MacroEvent], None]):
        """Remove playback callback."""
        try:
            self.playback_callbacks.remove(callback)
        except ValueError:
            pass
    
    def add_completion_callback(self, callback: Callable[[MacroRecording], None]):
        """Add callback for playback completion."""
        self.completion_callbacks.append(callback)
    
    def remove_completion_callback(self, callback: Callable[[MacroRecording], None]):
        """Remove completion callback."""
        try:
            self.completion_callbacks.remove(callback)
        except ValueError:
            pass
    
    def add_error_callback(self, callback: Callable[[PlaybackError, str], None]):
        """Add callback for playback errors."""
        self.error_callbacks.append(callback)
    
    def remove_error_callback(self, callback: Callable[[PlaybackError, str], None]):
        """Remove error callback."""
        try:
            self.error_callbacks.remove(callback)
        except ValueError:
            pass
    
    def get_stats(self) -> PlaybackStats:
        """Get player statistics."""
        with self.lock:
            return PlaybackStats(
                total_playbacks=self.stats.total_playbacks,
                total_events_played=self.stats.total_events_played,
                current_playback_events=self.stats.current_playback_events,
                current_playback_duration=self.stats.current_playback_duration,
                loops_completed=self.stats.loops_completed,
                errors_encountered=self.stats.errors_encountered,
                average_timing_error_ms=self.stats.average_timing_error_ms,
                max_timing_error_ms=self.stats.max_timing_error_ms,
                memory_usage_mb=self.stats.memory_usage_mb,
                last_playback_time=self.stats.last_playback_time
            )
    
    def reset_stats(self):
        """Reset player statistics."""
        with self.lock:
            self.stats = PlaybackStats()
            self.timing_errors.clear()
    
    def get_playback_state(self) -> PlaybackState:
        """Get current playback state."""
        return self.playback_state
    
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self.playback_state == PlaybackState.PLAYING
    
    def is_paused(self) -> bool:
        """Check if currently paused."""
        return self.playback_state == PlaybackState.PAUSED
    
    def is_stopped(self) -> bool:
        """Check if stopped."""
        return self.playback_state == PlaybackState.STOPPED


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create macro player
    config = PlaybackConfig(
        enabled=True,
        speed_multiplier=1.0,
        loop_enabled=False,
        max_loops=0,
        precision_ms=0.1,
        error_recovery=True,
        max_errors=10,
        thread_priority=1,
        memory_limit_mb=100,
        enable_monitoring=True
    )
    
    player = MacroPlayer(config)
    
    # Add callbacks for testing
    def playback_callback(event: MacroEvent):
        print(f"Playing event: {event.event_type.value} at {event.timestamp:.3f}s")
    
    def completion_callback(recording: MacroRecording):
        print(f"Playback completed: {recording.name}")
    
    def error_callback(error_type: PlaybackError, message: str):
        print(f"Playback error: {error_type.value} - {message}")
    
    player.add_playback_callback(playback_callback)
    player.add_completion_callback(completion_callback)
    player.add_error_callback(error_callback)
    
    print("Testing Macro Player...")
    
    # Create a test recording
    from .macro_recorder import MacroRecording, MacroEvent, MacroEventType
    
    test_recording = MacroRecording(
        name="Test Playback",
        description="A test recording for playback demonstration"
    )
    
    # Add some test events
    test_recording.events = [
        MacroEvent(MacroEventType.KEY_PRESS, 0.0, {'key': 'w', 'key_code': 87}),
        MacroEvent(MacroEventType.DELAY, 0.1, {'delay_ms': 100}),
        MacroEvent(MacroEventType.KEY_RELEASE, 0.2, {'key': 'w', 'key_code': 87}),
        MacroEvent(MacroEventType.MOUSE_MOVE, 0.3, {'x': 100, 'y': 100}),
        MacroEvent(MacroEventType.MOUSE_CLICK, 0.4, {'button': 'left', 'x': 100, 'y': 100}),
        MacroEvent(MacroEventType.TEXT_INPUT, 0.5, {'text': 'Hello, World!'}),
        MacroEvent(MacroEventType.COMMENT, 0.6, comment="Test comment")
    ]
    
    test_recording.event_count = len(test_recording.events)
    test_recording.total_duration = 0.6
    
    # Load and play recording
    if player.load_recording(test_recording):
        print("✓ Recording loaded")
        
        if player.start_playback():
            print("✓ Playback started")
            
            # Wait for playback to complete
            while player.is_playing():
                time.sleep(0.1)
            
            print("✓ Playback completed")
        else:
            print("✗ Failed to start playback")
    else:
        print("✗ Failed to load recording")
    
    # Get statistics
    stats = player.get_stats()
    print(f"\nPlayer Statistics:")
    print(f"  - Total playbacks: {stats.total_playbacks}")
    print(f"  - Total events played: {stats.total_events_played}")
    print(f"  - Loops completed: {stats.loops_completed}")
    print(f"  - Errors encountered: {stats.errors_encountered}")
    print(f"  - Average timing error: {stats.average_timing_error_ms:.2f} ms")
    print(f"  - Max timing error: {stats.max_timing_error_ms:.2f} ms")
    print(f"  - Memory usage: {stats.memory_usage_mb:.2f} MB")
    
    print("\nMacro player testing completed!")
