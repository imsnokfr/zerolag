"""
Macro Recorder for ZeroLag

This module implements comprehensive macro recording functionality including:
- Key press/release recording with precise timing
- Mouse movement and click recording
- Delay and timing capture
- Loop and conditional recording
- Text input recording
- Nested macro support
- Real-time recording with minimal overhead

Features:
- High-precision timing (microsecond accuracy)
- Event filtering and optimization
- Memory-efficient storage
- Real-time compression
- Thread-safe recording
- Performance monitoring
"""

import time
import threading
import json
import gzip
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import logging
import pickle
import base64


class MacroEventType(Enum):
    """Types of macro events."""
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_PRESS = "mouse_press"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_SCROLL = "mouse_scroll"
    DELAY = "delay"
    LOOP_START = "loop_start"
    LOOP_END = "loop_end"
    TEXT_INPUT = "text_input"
    MACRO_CALL = "macro_call"
    CONDITIONAL = "conditional"
    COMMENT = "comment"


class MacroLoopType(Enum):
    """Types of macro loops."""
    COUNT = "count"  # Repeat N times
    WHILE = "while"  # Repeat while condition is true
    FOREVER = "forever"  # Repeat indefinitely
    UNTIL = "until"  # Repeat until condition is true


@dataclass
class MacroEvent:
    """A single macro event with timing and data."""
    event_type: MacroEventType
    timestamp: float
    data: Dict[str, Any] = field(default_factory=dict)
    duration: Optional[float] = None  # For events with duration
    loop_id: Optional[str] = None  # For loop events
    comment: Optional[str] = None  # For comments
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'data': self.data,
            'duration': self.duration,
            'loop_id': self.loop_id,
            'comment': self.comment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroEvent':
        """Create from dictionary."""
        return cls(
            event_type=MacroEventType(data['event_type']),
            timestamp=data['timestamp'],
            data=data.get('data', {}),
            duration=data.get('duration'),
            loop_id=data.get('loop_id'),
            comment=data.get('comment')
        )


@dataclass
class MacroLoop:
    """Macro loop definition."""
    loop_id: str
    loop_type: MacroLoopType
    count: Optional[int] = None  # For COUNT loops
    condition: Optional[str] = None  # For WHILE/UNTIL loops
    start_event_index: int = 0
    end_event_index: int = 0
    current_iteration: int = 0
    max_iterations: int = 0


@dataclass
class MacroRecording:
    """Complete macro recording with metadata."""
    name: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    version: str = "1.0"
    events: List[MacroEvent] = field(default_factory=list)
    loops: Dict[str, MacroLoop] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_duration: float = 0.0
    event_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'version': self.version,
            'events': [event.to_dict() for event in self.events],
            'loops': {loop_id: {
                'loop_id': loop.loop_id,
                'loop_type': loop.loop_type.value,
                'count': loop.count,
                'condition': loop.condition,
                'start_event_index': loop.start_event_index,
                'end_event_index': loop.end_event_index,
                'current_iteration': loop.current_iteration,
                'max_iterations': loop.max_iterations
            } for loop_id, loop in self.loops.items()},
            'metadata': self.metadata,
            'total_duration': self.total_duration,
            'event_count': self.event_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MacroRecording':
        """Create from dictionary."""
        loops = {}
        for loop_id, loop_data in data.get('loops', {}).items():
            loops[loop_id] = MacroLoop(
                loop_id=loop_data['loop_id'],
                loop_type=MacroLoopType(loop_data['loop_type']),
                count=loop_data.get('count'),
                condition=loop_data.get('condition'),
                start_event_index=loop_data['start_event_index'],
                end_event_index=loop_data['end_event_index'],
                current_iteration=loop_data['current_iteration'],
                max_iterations=loop_data['max_iterations']
            )
        
        return cls(
            name=data['name'],
            description=data.get('description', ''),
            created_at=data.get('created_at', time.time()),
            modified_at=data.get('modified_at', time.time()),
            version=data.get('version', '1.0'),
            events=[MacroEvent.from_dict(event_data) for event_data in data.get('events', [])],
            loops=loops,
            metadata=data.get('metadata', {}),
            total_duration=data.get('total_duration', 0.0),
            event_count=data.get('event_count', 0)
        )


@dataclass
class MacroRecorderConfig:
    """Configuration for macro recorder."""
    enabled: bool = True
    precision_ms: float = 0.1  # Recording precision in milliseconds
    max_events: int = 10000  # Maximum events per recording
    compression_enabled: bool = True
    auto_save_interval: float = 30.0  # Auto-save interval in seconds
    memory_limit_mb: int = 100  # Memory limit in MB
    filter_duplicate_events: bool = True
    min_event_interval_ms: float = 0.1  # Minimum interval between events
    enable_performance_monitoring: bool = True


@dataclass
class MacroRecorderStats:
    """Statistics for macro recorder."""
    total_recordings: int = 0
    total_events_recorded: int = 0
    current_recording_events: int = 0
    current_recording_duration: float = 0.0
    memory_usage_mb: float = 0.0
    compression_ratio: float = 0.0
    average_event_interval_ms: float = 0.0
    last_save_time: float = 0.0
    errors_count: int = 0


class MacroRecorder:
    """
    High-performance macro recorder for ZeroLag.
    
    Records keyboard and mouse events with precise timing and provides
    comprehensive macro management capabilities.
    """
    
    def __init__(self, config: Optional[MacroRecorderConfig] = None):
        """
        Initialize macro recorder.
        
        Args:
            config: Recorder configuration
        """
        self.config = config or MacroRecorderConfig()
        self.current_recording: Optional[MacroRecording] = None
        self.is_recording = False
        self.recording_start_time = 0.0
        self.last_event_time = 0.0
        
        # Event filtering
        self.last_events: deque = deque(maxlen=10)
        self.event_filter_enabled = self.config.filter_duplicate_events
        
        # Performance monitoring
        self.stats = MacroRecorderStats()
        self.performance_monitor = None
        
        # Threading
        self.lock = threading.RLock()
        self.recording_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.recording_callbacks: List[Callable[[MacroEvent], None]] = []
        self.completion_callbacks: List[Callable[[MacroRecording], None]] = []
        
        # Auto-save
        self.auto_save_timer: Optional[threading.Timer] = None
        
        # Memory management
        self.memory_usage = 0.0
        self.compressed_data = None
    
    def start_recording(self, name: str, description: str = "") -> bool:
        """
        Start recording a new macro.
        
        Args:
            name: Macro name
            description: Macro description
            
        Returns:
            True if recording started successfully
        """
        if self.is_recording:
            return False
        
        try:
            with self.lock:
                # Create new recording
                self.current_recording = MacroRecording(
                    name=name,
                    description=description,
                    created_at=time.time(),
                    modified_at=time.time()
                )
                
                self.is_recording = True
                self.recording_start_time = time.time()
                self.last_event_time = self.recording_start_time
                
                # Reset statistics
                self.stats.current_recording_events = 0
                self.stats.current_recording_duration = 0.0
                
                # Start auto-save timer
                if self.config.auto_save_interval > 0:
                    self._start_auto_save_timer()
                
                # Start performance monitoring
                if self.config.enable_performance_monitoring:
                    self._start_performance_monitoring()
                
                return True
                
        except Exception as e:
            logging.error(f"Error starting macro recording: {e}")
            self.stats.errors_count += 1
            return False
    
    def stop_recording(self) -> Optional[MacroRecording]:
        """
        Stop recording and return the completed macro.
        
        Returns:
            Completed macro recording or None if error
        """
        if not self.is_recording or not self.current_recording:
            return None
        
        try:
            with self.lock:
                # Stop auto-save timer
                if self.auto_save_timer:
                    self.auto_save_timer.cancel()
                    self.auto_save_timer = None
                
                # Calculate final duration
                if self.current_recording.events:
                    last_event = self.current_recording.events[-1]
                    self.current_recording.total_duration = last_event.timestamp - self.recording_start_time
                else:
                    self.current_recording.total_duration = time.time() - self.recording_start_time
                
                # Update metadata
                self.current_recording.modified_at = time.time()
                self.current_recording.event_count = len(self.current_recording.events)
                
                # Compress if enabled
                if self.config.compression_enabled:
                    self._compress_recording()
                
                # Update statistics
                self.stats.total_recordings += 1
                self.stats.total_events_recorded += self.stats.current_recording_events
                
                # Get completed recording
                completed_recording = self.current_recording
                
                # Reset state
                self.current_recording = None
                self.is_recording = False
                self.recording_start_time = 0.0
                self.last_event_time = 0.0
                
                # Trigger completion callbacks
                for callback in self.completion_callbacks:
                    try:
                        callback(completed_recording)
                    except Exception as e:
                        logging.error(f"Error in completion callback: {e}")
                
                return completed_recording
                
        except Exception as e:
            logging.error(f"Error stopping macro recording: {e}")
            self.stats.errors_count += 1
            return None
    
    def record_event(self, event_type: MacroEventType, data: Dict[str, Any], 
                    duration: Optional[float] = None, comment: Optional[str] = None) -> bool:
        """
        Record a macro event.
        
        Args:
            event_type: Type of event to record
            data: Event data
            duration: Event duration (for events with duration)
            comment: Optional comment
            
        Returns:
            True if event recorded successfully
        """
        if not self.is_recording or not self.current_recording:
            return False
        
        try:
            current_time = time.time()
            
            # Check event filtering
            if self.event_filter_enabled and self._should_filter_event(event_type, data, current_time):
                return True  # Event filtered but not an error
            
            # Check memory limit
            if self._check_memory_limit():
                logging.warning("Memory limit reached, stopping recording")
                self.stop_recording()
                return False
            
            # Check max events
            if len(self.current_recording.events) >= self.config.max_events:
                logging.warning("Maximum events reached, stopping recording")
                self.stop_recording()
                return False
            
            # Create macro event
            macro_event = MacroEvent(
                event_type=event_type,
                timestamp=current_time - self.recording_start_time,  # Relative timestamp
                data=data,
                duration=duration,
                comment=comment
            )
            
            # Add to recording
            with self.lock:
                self.current_recording.events.append(macro_event)
                self.last_event_time = current_time
                
                # Update statistics
                self.stats.current_recording_events += 1
                self.stats.current_recording_duration = current_time - self.recording_start_time
                
                # Update average event interval
                if self.stats.current_recording_events > 1:
                    interval = current_time - self.last_event_time
                    self.stats.average_event_interval_ms = (
                        (self.stats.average_event_interval_ms * (self.stats.current_recording_events - 1) + interval * 1000) /
                        self.stats.current_recording_events
                    )
            
            # Trigger recording callbacks
            for callback in self.recording_callbacks:
                try:
                    callback(macro_event)
                except Exception as e:
                    logging.error(f"Error in recording callback: {e}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error recording macro event: {e}")
            self.stats.errors_count += 1
            return False
    
    def record_key_press(self, key: str, key_code: int, modifiers: List[str] = None) -> bool:
        """Record a key press event."""
        return self.record_event(
            MacroEventType.KEY_PRESS,
            {
                'key': key,
                'key_code': key_code,
                'modifiers': modifiers or []
            }
        )
    
    def record_key_release(self, key: str, key_code: int, modifiers: List[str] = None) -> bool:
        """Record a key release event."""
        return self.record_event(
            MacroEventType.KEY_RELEASE,
            {
                'key': key,
                'key_code': key_code,
                'modifiers': modifiers or []
            }
        )
    
    def record_mouse_move(self, x: int, y: int, dx: int = 0, dy: int = 0) -> bool:
        """Record a mouse movement event."""
        return self.record_event(
            MacroEventType.MOUSE_MOVE,
            {
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy
            }
        )
    
    def record_mouse_click(self, button: str, x: int, y: int, click_count: int = 1) -> bool:
        """Record a mouse click event."""
        return self.record_event(
            MacroEventType.MOUSE_CLICK,
            {
                'button': button,
                'x': x,
                'y': y,
                'click_count': click_count
            }
        )
    
    def record_mouse_press(self, button: str, x: int, y: int) -> bool:
        """Record a mouse press event."""
        return self.record_event(
            MacroEventType.MOUSE_PRESS,
            {
                'button': button,
                'x': x,
                'y': y
            }
        )
    
    def record_mouse_release(self, button: str, x: int, y: int) -> bool:
        """Record a mouse release event."""
        return self.record_event(
            MacroEventType.MOUSE_RELEASE,
            {
                'button': button,
                'x': x,
                'y': y
            }
        )
    
    def record_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> bool:
        """Record a mouse scroll event."""
        return self.record_event(
            MacroEventType.MOUSE_SCROLL,
            {
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy
            }
        )
    
    def record_delay(self, delay_ms: float) -> bool:
        """Record a delay event."""
        return self.record_event(
            MacroEventType.DELAY,
            {'delay_ms': delay_ms},
            duration=delay_ms / 1000.0
        )
    
    def record_text_input(self, text: str) -> bool:
        """Record a text input event."""
        return self.record_event(
            MacroEventType.TEXT_INPUT,
            {'text': text}
        )
    
    def record_comment(self, comment: str) -> bool:
        """Record a comment event."""
        return self.record_event(
            MacroEventType.COMMENT,
            {},
            comment=comment
        )
    
    def start_loop(self, loop_id: str, loop_type: MacroLoopType, 
                  count: Optional[int] = None, condition: Optional[str] = None) -> bool:
        """Start a loop in the recording."""
        if not self.is_recording or not self.current_recording:
            return False
        
        try:
            with self.lock:
                loop = MacroLoop(
                    loop_id=loop_id,
                    loop_type=loop_type,
                    count=count,
                    condition=condition,
                    start_event_index=len(self.current_recording.events),
                    current_iteration=0,
                    max_iterations=count or 0
                )
                
                self.current_recording.loops[loop_id] = loop
                
                # Record loop start event
                return self.record_event(
                    MacroEventType.LOOP_START,
                    {
                        'loop_id': loop_id,
                        'loop_type': loop_type.value,
                        'count': count,
                        'condition': condition
                    },
                    loop_id=loop_id
                )
                
        except Exception as e:
            logging.error(f"Error starting loop: {e}")
            return False
    
    def end_loop(self, loop_id: str) -> bool:
        """End a loop in the recording."""
        if not self.is_recording or not self.current_recording:
            return False
        
        try:
            with self.lock:
                if loop_id not in self.current_recording.loops:
                    return False
                
                loop = self.current_recording.loops[loop_id]
                loop.end_event_index = len(self.current_recording.events)
                
                # Record loop end event
                return self.record_event(
                    MacroEventType.LOOP_END,
                    {'loop_id': loop_id},
                    loop_id=loop_id
                )
                
        except Exception as e:
            logging.error(f"Error ending loop: {e}")
            return False
    
    def _should_filter_event(self, event_type: MacroEventType, data: Dict[str, Any], 
                           current_time: float) -> bool:
        """Check if event should be filtered out."""
        # Check minimum interval
        if current_time - self.last_event_time < self.config.min_event_interval_ms / 1000.0:
            return True
        
        # Check for duplicate events
        if len(self.last_events) > 0:
            last_event = self.last_events[-1]
            if (last_event['event_type'] == event_type.value and 
                last_event['data'] == data and
                current_time - last_event['timestamp'] < 0.01):  # 10ms threshold
                return True
        
        # Add to last events
        self.last_events.append({
            'event_type': event_type.value,
            'data': data,
            'timestamp': current_time
        })
        
        return False
    
    def _check_memory_limit(self) -> bool:
        """Check if memory limit is exceeded."""
        if not self.current_recording:
            return False
        
        # Estimate memory usage
        estimated_size = len(self.current_recording.events) * 200  # Rough estimate
        self.memory_usage = estimated_size / (1024 * 1024)  # Convert to MB
        
        return self.memory_usage > self.config.memory_limit_mb
    
    def _compress_recording(self):
        """Compress the current recording."""
        if not self.current_recording:
            return
        
        try:
            # Serialize to JSON
            json_data = json.dumps(self.current_recording.to_dict())
            
            # Compress with gzip
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            # Calculate compression ratio
            original_size = len(json_data)
            compressed_size = len(compressed_data)
            self.stats.compression_ratio = compressed_size / original_size if original_size > 0 else 0
            
            # Store compressed data
            self.compressed_data = base64.b64encode(compressed_data).decode('utf-8')
            
        except Exception as e:
            logging.error(f"Error compressing recording: {e}")
    
    def _start_auto_save_timer(self):
        """Start auto-save timer."""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        self.auto_save_timer = threading.Timer(
            self.config.auto_save_interval,
            self._auto_save
        )
        self.auto_save_timer.start()
    
    def _auto_save(self):
        """Auto-save current recording."""
        if self.is_recording and self.current_recording:
            try:
                # Save to temporary file
                filename = f"macro_temp_{self.current_recording.name}_{int(time.time())}.json"
                self.save_recording(self.current_recording, filename)
                self.stats.last_save_time = time.time()
                
                # Restart timer
                self._start_auto_save_timer()
                
            except Exception as e:
                logging.error(f"Error in auto-save: {e}")
    
    def _start_performance_monitoring(self):
        """Start performance monitoring."""
        if self.performance_monitor:
            return
        
        def monitor_performance():
            while self.is_recording:
                try:
                    # Update memory usage
                    self._check_memory_limit()
                    
                    # Update statistics
                    self.stats.memory_usage_mb = self.memory_usage
                    
                    time.sleep(1.0)  # Monitor every second
                    
                except Exception as e:
                    logging.error(f"Error in performance monitoring: {e}")
                    break
        
        self.performance_monitor = threading.Thread(
            target=monitor_performance,
            daemon=True,
            name="MacroRecorderPerformanceMonitor"
        )
        self.performance_monitor.start()
    
    def save_recording(self, recording: MacroRecording, filename: str) -> bool:
        """
        Save a recording to file.
        
        Args:
            recording: Recording to save
            filename: Output filename
            
        Returns:
            True if saved successfully
        """
        try:
            # Convert to dictionary
            data = recording.to_dict()
            
            # Add compressed data if available
            if self.compressed_data:
                data['compressed_data'] = self.compressed_data
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logging.error(f"Error saving recording: {e}")
            self.stats.errors_count += 1
            return False
    
    def load_recording(self, filename: str) -> Optional[MacroRecording]:
        """
        Load a recording from file.
        
        Args:
            filename: Input filename
            
        Returns:
            Loaded recording or None if error
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check for compressed data
            if 'compressed_data' in data:
                compressed_data = base64.b64decode(data['compressed_data'])
                json_data = gzip.decompress(compressed_data).decode('utf-8')
                data = json.loads(json_data)
            
            return MacroRecording.from_dict(data)
            
        except Exception as e:
            logging.error(f"Error loading recording: {e}")
            self.stats.errors_count += 1
            return None
    
    def add_recording_callback(self, callback: Callable[[MacroEvent], None]):
        """Add callback for recording events."""
        self.recording_callbacks.append(callback)
    
    def remove_recording_callback(self, callback: Callable[[MacroEvent], None]):
        """Remove recording callback."""
        try:
            self.recording_callbacks.remove(callback)
        except ValueError:
            pass
    
    def add_completion_callback(self, callback: Callable[[MacroRecording], None]):
        """Add callback for recording completion."""
        self.completion_callbacks.append(callback)
    
    def remove_completion_callback(self, callback: Callable[[MacroRecording], None]):
        """Remove completion callback."""
        try:
            self.completion_callbacks.remove(callback)
        except ValueError:
            pass
    
    def get_stats(self) -> MacroRecorderStats:
        """Get recorder statistics."""
        with self.lock:
            return MacroRecorderStats(
                total_recordings=self.stats.total_recordings,
                total_events_recorded=self.stats.total_events_recorded,
                current_recording_events=self.stats.current_recording_events,
                current_recording_duration=self.stats.current_recording_duration,
                memory_usage_mb=self.stats.memory_usage_mb,
                compression_ratio=self.stats.compression_ratio,
                average_event_interval_ms=self.stats.average_event_interval_ms,
                last_save_time=self.stats.last_save_time,
                errors_count=self.stats.errors_count
            )
    
    def reset_stats(self):
        """Reset recorder statistics."""
        with self.lock:
            self.stats = MacroRecorderStats()
    
    def is_recording_active(self) -> bool:
        """Check if recording is currently active."""
        return self.is_recording
    
    def get_current_recording(self) -> Optional[MacroRecording]:
        """Get current recording if active."""
        return self.current_recording


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create macro recorder
    config = MacroRecorderConfig(
        enabled=True,
        precision_ms=0.1,
        max_events=1000,
        compression_enabled=True,
        auto_save_interval=10.0,
        memory_limit_mb=50,
        filter_duplicate_events=True,
        min_event_interval_ms=1.0,
        enable_performance_monitoring=True
    )
    
    recorder = MacroRecorder(config)
    
    # Add callbacks for testing
    def recording_callback(event: MacroEvent):
        print(f"Recording event: {event.event_type.value} at {event.timestamp:.3f}s")
    
    def completion_callback(recording: MacroRecording):
        print(f"Recording completed: {recording.name} with {recording.event_count} events")
    
    recorder.add_recording_callback(recording_callback)
    recorder.add_completion_callback(completion_callback)
    
    print("Testing Macro Recorder...")
    
    # Test recording
    if recorder.start_recording("Test Macro", "A test macro for demonstration"):
        print("✓ Recording started")
        
        try:
            # Record some events
            print("Recording keyboard events...")
            for i in range(10):
                key = random.choice(['w', 'a', 's', 'd', 'space', 'shift', 'ctrl'])
                recorder.record_key_press(key, hash(key) % 1000, ['ctrl'] if i % 3 == 0 else [])
                time.sleep(0.01)
                recorder.record_key_release(key, hash(key) % 1000, ['ctrl'] if i % 3 == 0 else [])
                time.sleep(0.01)
            
            print("Recording mouse events...")
            for i in range(5):
                x, y = random.randint(0, 1920), random.randint(0, 1080)
                recorder.record_mouse_move(x, y, random.randint(-10, 10), random.randint(-10, 10))
                time.sleep(0.01)
                recorder.record_mouse_click('left', x, y, 1)
                time.sleep(0.01)
            
            print("Recording delays...")
            for i in range(3):
                delay = random.uniform(10, 100)
                recorder.record_delay(delay)
                time.sleep(0.01)
            
            print("Recording text input...")
            recorder.record_text_input("Hello, World!")
            time.sleep(0.01)
            
            print("Recording comments...")
            recorder.record_comment("This is a test macro")
            time.sleep(0.01)
            
            # Test loop recording
            print("Recording loop...")
            recorder.start_loop("test_loop", MacroLoopType.COUNT, count=3)
            recorder.record_key_press('space', 32)
            recorder.record_delay(100)
            recorder.record_key_release('space', 32)
            recorder.end_loop("test_loop")
            
            # Stop recording
            recording = recorder.stop_recording()
            if recording:
                print(f"✓ Recording completed: {recording.name}")
                print(f"  - Events: {recording.event_count}")
                print(f"  - Duration: {recording.total_duration:.3f}s")
                print(f"  - Loops: {len(recording.loops)}")
                
                # Save recording
                if recorder.save_recording(recording, "test_macro.json"):
                    print("✓ Recording saved to test_macro.json")
                
                # Test loading
                loaded_recording = recorder.load_recording("test_macro.json")
                if loaded_recording:
                    print("✓ Recording loaded successfully")
                    print(f"  - Loaded events: {loaded_recording.event_count}")
                    print(f"  - Loaded duration: {loaded_recording.total_duration:.3f}s")
                else:
                    print("✗ Failed to load recording")
            else:
                print("✗ Failed to complete recording")
        
        except Exception as e:
            print(f"✗ Error during recording: {e}")
            recorder.stop_recording()
    
    # Get statistics
    stats = recorder.get_stats()
    print(f"\nRecorder Statistics:")
    print(f"  - Total recordings: {stats.total_recordings}")
    print(f"  - Total events recorded: {stats.total_events_recorded}")
    print(f"  - Memory usage: {stats.memory_usage_mb:.2f} MB")
    print(f"  - Compression ratio: {stats.compression_ratio:.2f}")
    print(f"  - Average event interval: {stats.average_event_interval_ms:.2f} ms")
    print(f"  - Errors: {stats.errors_count}")
    
    print("\nMacro recorder testing completed!")
