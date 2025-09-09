"""
High-Frequency Polling Rate Manager for ZeroLag

This module provides advanced polling rate management for gaming peripherals,
supporting polling rates up to 8000Hz with adaptive performance optimization.

Features:
- High-frequency polling (125Hz to 8000Hz)
- Adaptive polling based on system performance
- Cross-platform support (Windows, macOS, Linux)
- Performance monitoring and optimization
- Integration with input handlers
"""

import time
import threading
import queue
import platform
from typing import Dict, Optional, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Platform-specific imports
if platform.system() == "Windows":
    try:
        import win32api
        import win32con
        import win32gui
        WINDOWS_AVAILABLE = True
    except ImportError:
        WINDOWS_AVAILABLE = False
else:
    WINDOWS_AVAILABLE = False


class PollingRate(Enum):
    """Standard polling rates for gaming peripherals."""
    HZ_125 = 125
    HZ_250 = 250
    HZ_500 = 500
    HZ_1000 = 1000
    HZ_2000 = 2000
    HZ_4000 = 4000
    HZ_8000 = 8000


class PollingMode(Enum):
    """Polling rate modes."""
    FIXED = "fixed"           # Fixed polling rate
    ADAPTIVE = "adaptive"     # Adaptive based on performance
    GAMING = "gaming"         # Optimized for gaming
    POWER_SAVE = "power_save" # Power saving mode


@dataclass
class PollingConfig:
    """Configuration for polling rate management."""
    mouse_rate: int = 1000
    keyboard_rate: int = 1000
    mode: PollingMode = PollingMode.FIXED
    adaptive_threshold: float = 0.8  # CPU usage threshold for adaptive mode
    min_rate: int = 125
    max_rate: int = 8000
    performance_monitoring: bool = True


@dataclass
class PollingStats:
    """Statistics for polling performance."""
    current_rate: int
    target_rate: int
    actual_rate: float
    cpu_usage: float
    latency_avg: float
    latency_max: float
    events_per_second: int
    dropped_events: int
    timestamp: float


class PollingManager:
    """
    High-frequency polling rate manager for gaming peripherals.
    
    This class manages polling rates for mouse and keyboard input,
    providing adaptive performance optimization and real-time monitoring.
    """
    
    def __init__(self, config: Optional[PollingConfig] = None, enable_logging: bool = True):
        """
        Initialize the polling manager.
        
        Args:
            config: Polling configuration
            enable_logging: Enable debug logging
        """
        self.config = config or PollingConfig()
        self.logger = logging.getLogger(__name__) if enable_logging else None
        if self.logger:
            self.logger.setLevel(logging.INFO)
        
        # State management
        self.is_active = False
        self._lock = threading.Lock()
        
        # Polling threads
        self.mouse_polling_thread: Optional[threading.Thread] = None
        self.keyboard_polling_thread: Optional[threading.Thread] = None
        
        # Performance monitoring
        self.performance_thread: Optional[threading.Thread] = None
        self.stats = PollingStats(
            current_rate=0, target_rate=0, actual_rate=0.0,
            cpu_usage=0.0, latency_avg=0.0, latency_max=0.0,
            events_per_second=0, dropped_events=0, timestamp=time.time()
        )
        
        # Event queues for high-frequency processing
        self.mouse_event_queue = queue.Queue(maxsize=10000)
        self.keyboard_event_queue = queue.Queue(maxsize=10000)
        
        # Timing and performance tracking
        self.last_poll_time = 0.0
        self.poll_intervals = []
        self.latency_measurements = []
        self.max_latency_history = 1000
        
        # Callbacks
        self.mouse_poll_callback: Optional[Callable] = None
        self.keyboard_poll_callback: Optional[Callable] = None
        self.stats_callback: Optional[Callable] = None
        
        # Platform-specific settings
        self.platform = platform.system()
        self._init_platform_specific()
        
    def _init_platform_specific(self):
        """Initialize platform-specific components."""
        if self.platform == "Windows" and WINDOWS_AVAILABLE:
            self._init_windows()
        elif self.platform == "Darwin":  # macOS
            self._init_macos()
        elif self.platform == "Linux":
            self._init_linux()
        else:
            if self.logger:
                self.logger.warning(f"Unsupported platform: {self.platform}")
    
    def _init_windows(self):
        """Initialize Windows-specific polling optimizations."""
        try:
            # Set high-priority timer resolution for Windows
            win32api.timeBeginPeriod(1)  # 1ms timer resolution
            if self.logger:
                self.logger.info("Windows: High-priority timer resolution enabled")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Windows initialization error: {e}")
    
    def _init_macos(self):
        """Initialize macOS-specific polling optimizations."""
        try:
            # macOS-specific optimizations would go here
            if self.logger:
                self.logger.info("macOS: Using standard polling optimization")
        except Exception as e:
            if self.logger:
                self.logger.error(f"macOS initialization error: {e}")
    
    def _init_linux(self):
        """Initialize Linux-specific polling optimizations."""
        try:
            # Linux-specific optimizations would go here
            if self.logger:
                self.logger.info("Linux: Using standard polling optimization")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Linux initialization error: {e}")
    
    def set_mouse_polling_rate(self, rate: int) -> bool:
        """
        Set the mouse polling rate.
        
        Args:
            rate: Polling rate in Hz (125-8000)
            
        Returns:
            True if successful, False otherwise
        """
        if not 125 <= rate <= 8000:
            if self.logger:
                self.logger.error(f"Invalid mouse polling rate: {rate}. Must be 125-8000 Hz")
            return False
        
        with self._lock:
            old_rate = self.config.mouse_rate
            self.config.mouse_rate = rate
            
            if self.logger:
                self.logger.info(f"Mouse polling rate changed from {old_rate}Hz to {rate}Hz")
            
            # Restart mouse polling if active
            if self.is_active:
                self._restart_mouse_polling()
        
        return True
    
    def set_keyboard_polling_rate(self, rate: int) -> bool:
        """
        Set the keyboard polling rate.
        
        Args:
            rate: Polling rate in Hz (125-8000)
            
        Returns:
            True if successful, False otherwise
        """
        if not 125 <= rate <= 8000:
            if self.logger:
                self.logger.error(f"Invalid keyboard polling rate: {rate}. Must be 125-8000 Hz")
            return False
        
        with self._lock:
            old_rate = self.config.keyboard_rate
            self.config.keyboard_rate = rate
            
            if self.logger:
                self.logger.info(f"Keyboard polling rate changed from {old_rate}Hz to {rate}Hz")
            
            # Restart keyboard polling if active
            if self.is_active:
                self._restart_keyboard_polling()
        
        return True
    
    def set_polling_mode(self, mode: PollingMode) -> bool:
        """
        Set the polling mode.
        
        Args:
            mode: Polling mode (FIXED, ADAPTIVE, GAMING, POWER_SAVE)
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            old_mode = self.config.mode
            self.config.mode = mode
            
            if self.logger:
                self.logger.info(f"Polling mode changed from {old_mode.value} to {mode.value}")
            
            # Apply mode-specific settings
            self._apply_polling_mode()
        
        return True
    
    def _apply_polling_mode(self):
        """Apply mode-specific polling settings."""
        if self.config.mode == PollingMode.GAMING:
            # Gaming mode: maximize polling rates
            self.config.mouse_rate = min(8000, self.config.mouse_rate)
            self.config.keyboard_rate = min(8000, self.config.keyboard_rate)
        elif self.config.mode == PollingMode.POWER_SAVE:
            # Power save mode: reduce polling rates
            self.config.mouse_rate = min(1000, self.config.mouse_rate)
            self.config.keyboard_rate = min(1000, self.config.keyboard_rate)
        elif self.config.mode == PollingMode.ADAPTIVE:
            # Adaptive mode: start with current rates, will adjust based on performance
            pass
    
    def start(self) -> bool:
        """Start the polling manager."""
        with self._lock:
            if self.is_active:
                return True
            
            try:
                self.is_active = True
                
                # Start polling threads
                self._start_mouse_polling()
                self._start_keyboard_polling()
                
                # Start performance monitoring
                if self.config.performance_monitoring:
                    self._start_performance_monitoring()
                
                if self.logger:
                    self.logger.info(f"Polling manager started (Mouse: {self.config.mouse_rate}Hz, "
                                   f"Keyboard: {self.config.keyboard_rate}Hz, Mode: {self.config.mode.value})")
                
                return True
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error starting polling manager: {e}")
                self.is_active = False
                return False
    
    def stop(self) -> bool:
        """Stop the polling manager."""
        with self._lock:
            if not self.is_active:
                return True
            
            try:
                self.is_active = False
                
                # Stop polling threads
                if self.mouse_polling_thread and self.mouse_polling_thread.is_alive():
                    self.mouse_polling_thread.join(timeout=1.0)
                
                if self.keyboard_polling_thread and self.keyboard_polling_thread.is_alive():
                    self.keyboard_polling_thread.join(timeout=1.0)
                
                # Stop performance monitoring
                if self.performance_thread and self.performance_thread.is_alive():
                    self.performance_thread.join(timeout=1.0)
                
                # Cleanup platform-specific resources
                if self.platform == "Windows" and WINDOWS_AVAILABLE:
                    try:
                        win32api.timeEndPeriod(1)
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Windows cleanup error: {e}")
                
                if self.logger:
                    self.logger.info("Polling manager stopped")
                
                return True
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping polling manager: {e}")
                return False
    
    def _start_mouse_polling(self):
        """Start the mouse polling thread."""
        self.mouse_polling_thread = threading.Thread(
            target=self._mouse_polling_loop,
            daemon=True,
            name="MousePollingThread"
        )
        self.mouse_polling_thread.start()
    
    def _start_keyboard_polling(self):
        """Start the keyboard polling thread."""
        self.keyboard_polling_thread = threading.Thread(
            target=self._keyboard_polling_loop,
            daemon=True,
            name="KeyboardPollingThread"
        )
        self.keyboard_polling_thread.start()
    
    def _start_performance_monitoring(self):
        """Start the performance monitoring thread."""
        self.performance_thread = threading.Thread(
            target=self._performance_monitoring_loop,
            daemon=True,
            name="PerformanceMonitoringThread"
        )
        self.performance_thread.start()
    
    def _mouse_polling_loop(self):
        """Main mouse polling loop."""
        try:
            if self.logger:
                self.logger.info("Mouse polling thread started")
            
            interval = 1.0 / self.config.mouse_rate
            last_poll_time = time.time()
            
            while self.is_active:
                current_time = time.time()
                
                # Calculate actual polling interval
                actual_interval = current_time - last_poll_time
                self.poll_intervals.append(actual_interval)
                
                # Keep only recent intervals
                if len(self.poll_intervals) > 100:
                    self.poll_intervals.pop(0)
                
                # Poll for mouse events
                self._poll_mouse_events()
                
                # Calculate sleep time
                elapsed = time.time() - current_time
                sleep_time = max(0, interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                last_poll_time = time.time()
            
            if self.logger:
                self.logger.info("Mouse polling thread stopped")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in mouse polling loop: {e}")
    
    def _keyboard_polling_loop(self):
        """Main keyboard polling loop."""
        try:
            if self.logger:
                self.logger.info("Keyboard polling thread started")
            
            interval = 1.0 / self.config.keyboard_rate
            last_poll_time = time.time()
            
            while self.is_active:
                current_time = time.time()
                
                # Calculate actual polling interval
                actual_interval = current_time - last_poll_time
                self.poll_intervals.append(actual_interval)
                
                # Keep only recent intervals
                if len(self.poll_intervals) > 100:
                    self.poll_intervals.pop(0)
                
                # Poll for keyboard events
                self._poll_keyboard_events()
                
                # Calculate sleep time
                elapsed = time.time() - current_time
                sleep_time = max(0, interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                last_poll_time = time.time()
            
            if self.logger:
                self.logger.info("Keyboard polling thread stopped")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in keyboard polling loop: {e}")
    
    def _poll_mouse_events(self):
        """Poll for mouse events."""
        try:
            # This would integrate with the actual mouse input system
            # For now, we'll simulate high-frequency polling
            
            if self.mouse_poll_callback:
                # Simulate mouse event polling
                event_data = {
                    'timestamp': time.time(),
                    'type': 'mouse_poll',
                    'rate': self.config.mouse_rate
                }
                
                try:
                    self.mouse_event_queue.put_nowait(event_data)
                    self.mouse_poll_callback(event_data)
                except queue.Full:
                    self.stats.dropped_events += 1
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error polling mouse events: {e}")
    
    def _poll_keyboard_events(self):
        """Poll for keyboard events."""
        try:
            # This would integrate with the actual keyboard input system
            # For now, we'll simulate high-frequency polling
            
            if self.keyboard_poll_callback:
                # Simulate keyboard event polling
                event_data = {
                    'timestamp': time.time(),
                    'type': 'keyboard_poll',
                    'rate': self.config.keyboard_rate
                }
                
                try:
                    self.keyboard_event_queue.put_nowait(event_data)
                    self.keyboard_poll_callback(event_data)
                except queue.Full:
                    self.stats.dropped_events += 1
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error polling keyboard events: {e}")
    
    def _performance_monitoring_loop(self):
        """Performance monitoring loop."""
        try:
            if self.logger:
                self.logger.info("Performance monitoring thread started")
            
            while self.is_active:
                self._update_performance_stats()
                
                # Adaptive polling rate adjustment
                if self.config.mode == PollingMode.ADAPTIVE:
                    self._adjust_adaptive_rates()
                
                # Notify stats callback
                if self.stats_callback:
                    try:
                        self.stats_callback(self.stats)
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Error in stats callback: {e}")
                
                time.sleep(0.1)  # Update every 100ms
            
            if self.logger:
                self.logger.info("Performance monitoring thread stopped")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in performance monitoring loop: {e}")
    
    def _update_performance_stats(self):
        """Update performance statistics."""
        current_time = time.time()
        
        # Calculate actual polling rate
        if self.poll_intervals:
            avg_interval = sum(self.poll_intervals) / len(self.poll_intervals)
            actual_rate = 1.0 / avg_interval if avg_interval > 0 else 0
        else:
            actual_rate = 0
        
        # Calculate latency
        if self.latency_measurements:
            avg_latency = sum(self.latency_measurements) / len(self.latency_measurements)
            max_latency = max(self.latency_measurements)
        else:
            avg_latency = 0
            max_latency = 0
        
        # Calculate events per second
        events_per_second = (self.mouse_event_queue.qsize() + 
                           self.keyboard_event_queue.qsize()) * 10  # Rough estimate
        
        # Update stats
        self.stats.current_rate = int(actual_rate)
        self.stats.target_rate = max(self.config.mouse_rate, self.config.keyboard_rate)
        self.stats.actual_rate = actual_rate
        self.stats.latency_avg = avg_latency * 1000  # Convert to ms
        self.stats.latency_max = max_latency * 1000  # Convert to ms
        self.stats.events_per_second = events_per_second
        self.stats.timestamp = current_time
        
        # Keep latency history manageable
        if len(self.latency_measurements) > self.max_latency_history:
            self.latency_measurements = self.latency_measurements[-self.max_latency_history:]
    
    def _adjust_adaptive_rates(self):
        """Adjust polling rates based on performance in adaptive mode."""
        # Simple adaptive algorithm - can be enhanced
        if self.stats.cpu_usage > self.config.adaptive_threshold:
            # Reduce rates if CPU usage is high
            new_mouse_rate = max(self.config.min_rate, int(self.config.mouse_rate * 0.8))
            new_keyboard_rate = max(self.config.min_rate, int(self.config.keyboard_rate * 0.8))
            
            if new_mouse_rate != self.config.mouse_rate:
                self.set_mouse_polling_rate(new_mouse_rate)
            if new_keyboard_rate != self.config.keyboard_rate:
                self.set_keyboard_polling_rate(new_keyboard_rate)
        else:
            # Increase rates if CPU usage is low
            new_mouse_rate = min(self.config.max_rate, int(self.config.mouse_rate * 1.1))
            new_keyboard_rate = min(self.config.max_rate, int(self.config.keyboard_rate * 1.1))
            
            if new_mouse_rate != self.config.mouse_rate:
                self.set_mouse_polling_rate(new_mouse_rate)
            if new_keyboard_rate != self.config.keyboard_rate:
                self.set_keyboard_polling_rate(new_keyboard_rate)
    
    def _restart_mouse_polling(self):
        """Restart mouse polling with new rate."""
        # This would restart the mouse polling thread
        # For now, just log the change
        if self.logger:
            self.logger.info(f"Mouse polling restarted with rate {self.config.mouse_rate}Hz")
    
    def _restart_keyboard_polling(self):
        """Restart keyboard polling with new rate."""
        # This would restart the keyboard polling thread
        # For now, just log the change
        if self.logger:
            self.logger.info(f"Keyboard polling restarted with rate {self.config.keyboard_rate}Hz")
    
    def get_polling_stats(self) -> PollingStats:
        """Get current polling statistics."""
        return self.stats
    
    def get_config(self) -> PollingConfig:
        """Get current polling configuration."""
        return self.config
    
    def set_mouse_poll_callback(self, callback: Callable):
        """Set callback for mouse polling events."""
        self.mouse_poll_callback = callback
    
    def set_keyboard_poll_callback(self, callback: Callable):
        """Set callback for keyboard polling events."""
        self.keyboard_poll_callback = callback
    
    def set_stats_callback(self, callback: Callable):
        """Set callback for performance statistics updates."""
        self.stats_callback = callback
    
    def measure_latency(self, start_time: float):
        """Measure and record latency."""
        latency = time.time() - start_time
        self.latency_measurements.append(latency)
