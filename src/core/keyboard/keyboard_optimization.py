"""
Keyboard Optimization Integration for ZeroLag

This module integrates the anti-ghosting and NKRO simulation with the existing
keyboard handling system to provide seamless gaming optimizations.

Features:
- Integration with GamingKeyboardHandler
- Real-time anti-ghosting processing
- NKRO simulation for unlimited simultaneous keys
- Gaming-specific key combination detection
- Performance monitoring and optimization
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .anti_ghosting import (
    AntiGhostingEngine,
    KeyState,
    KeyInfo,
    KeyCombination,
    AntiGhostingStats
)
from ..input.keyboard_handler import GamingKeyboardHandler
from ..monitoring.performance_monitor import PerformanceMonitor


@dataclass
class KeyboardOptimizationConfig:
    """Configuration for keyboard optimization."""
    enable_nkro: bool = True
    max_simultaneous_keys: int = 0  # 0 = unlimited
    enable_ghosting_prevention: bool = True
    enable_combination_detection: bool = True
    enable_rapid_trigger: bool = True
    enable_debounce: bool = True
    debounce_threshold_ms: float = 50.0
    rapid_trigger_threshold_ms: float = 10.0


@dataclass
class KeyboardOptimizationStats:
    """Statistics for keyboard optimization."""
    total_events_processed: int = 0
    nkro_events_processed: int = 0
    ghosting_events_prevented: int = 0
    key_combinations_detected: int = 0
    rapid_trigger_events: int = 0
    debounced_events: int = 0
    average_processing_time_ms: float = 0.0
    max_simultaneous_keys: int = 0
    last_update_time: float = 0.0


class KeyboardOptimizationIntegration:
    """
    Integrates keyboard optimization features with the existing keyboard handler.
    
    Provides seamless anti-ghosting, NKRO simulation, and gaming optimizations
    while maintaining compatibility with the existing system.
    """
    
    def __init__(self, 
                 keyboard_handler: Optional[GamingKeyboardHandler] = None,
                 performance_monitor: Optional[PerformanceMonitor] = None,
                 config: Optional[KeyboardOptimizationConfig] = None):
        """
        Initialize keyboard optimization integration.
        
        Args:
            keyboard_handler: GamingKeyboardHandler instance
            performance_monitor: PerformanceMonitor instance
            config: Keyboard optimization configuration
        """
        self.keyboard_handler = keyboard_handler
        self.performance_monitor = performance_monitor
        self.config = config or KeyboardOptimizationConfig()
        
        # Initialize anti-ghosting engine
        self.anti_ghosting_engine = AntiGhostingEngine(
            enable_nkro=self.config.enable_nkro,
            max_keys=self.config.max_simultaneous_keys
        )
        
        # Integration state
        self.is_integrated = False
        self.integration_thread: Optional[threading.Thread] = None
        
        # Statistics tracking
        self.stats = KeyboardOptimizationStats()
        self.stats_lock = threading.RLock()
        
        # Callbacks
        self.optimization_callbacks: List[Callable[[str, KeyState], None]] = []
        
        # Threading
        self._lock = threading.RLock()
    
    def integrate(self) -> bool:
        """
        Integrate with the keyboard handler.
        
        Returns:
            True if integration successful, False otherwise
        """
        if self.is_integrated:
            return True
        
        try:
            with self._lock:
                if self.keyboard_handler:
                    # Hook into keyboard handler's event processing
                    self._hook_keyboard_handler()
                
                self.is_integrated = True
                
                # Start integration thread for monitoring
                self.integration_thread = threading.Thread(
                    target=self._integration_loop,
                    daemon=True,
                    name="KeyboardOptimizationThread"
                )
                self.integration_thread.start()
                
                return True
                
        except Exception as e:
            self.is_integrated = False
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from keyboard handler.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        if not self.is_integrated:
            return True
        
        try:
            with self._lock:
                self.is_integrated = False
                
                # Unhook from keyboard handler
                if self.keyboard_handler:
                    self._unhook_keyboard_handler()
                
                # Wait for integration thread to finish
                if self.integration_thread and self.integration_thread.is_alive():
                    self.integration_thread.join(timeout=2.0)
                
                return True
                
        except Exception as e:
            return False
    
    def _hook_keyboard_handler(self):
        """Hook into keyboard handler's event processing."""
        if not self.keyboard_handler:
            return
        
        # Store original method
        if hasattr(self.keyboard_handler, '_handle_key_press'):
            self._original_handle_key_press = self.keyboard_handler._handle_key_press
            
            # Replace with optimized version
            self.keyboard_handler._handle_key_press = self._optimized_handle_key_press
        
        if hasattr(self.keyboard_handler, '_handle_key_release'):
            self._original_handle_key_release = self.keyboard_handler._handle_key_release
            
            # Replace with optimized version
            self.keyboard_handler._handle_key_release = self._optimized_handle_key_release
    
    def _unhook_keyboard_handler(self):
        """Unhook from keyboard handler's event processing."""
        if not self.keyboard_handler:
            return
        
        # Restore original methods
        if hasattr(self, '_original_handle_key_press'):
            self.keyboard_handler._handle_key_press = self._original_handle_key_press
        
        if hasattr(self, '_original_handle_key_release'):
            self.keyboard_handler._handle_key_release = self._original_handle_key_release
    
    def _optimized_handle_key_press(self, event):
        """
        Optimized version of key press handler.
        
        This method intercepts key press events, applies optimizations,
        and then calls the original handler.
        """
        try:
            # Extract key information from event
            if hasattr(event, 'data') and isinstance(event.data, dict):
                key_name = event.data.get('key', '')
                key_code = event.data.get('key_code', 0)
                timestamp = event.timestamp
                
                # Apply anti-ghosting and NKRO processing
                success = self.anti_ghosting_engine.process_key_event(
                    key_name, True, timestamp
                )
                
                if not success:
                    # Key was blocked by anti-ghosting system
                    self._update_stats(ghosting_prevented=True)
                    return
                
                # Update statistics
                self._update_stats(nkro_processed=True)
                
                # Create optimized event with additional data
                optimized_event = type(event)(
                    event_type=event.event_type,
                    data={
                        **event.data,
                        'nkro_processed': True,
                        'ghosting_prevented': False,
                        'simultaneous_keys': len(self.anti_ghosting_engine.get_active_keys())
                    },
                    priority=event.priority,
                    timestamp=event.timestamp,
                    source=event.source
                )
                
                # Call original handler with optimized event
                if hasattr(self, '_original_handle_key_press'):
                    self._original_handle_key_press(optimized_event)
                
                # Trigger callbacks
                for callback in self.optimization_callbacks:
                    try:
                        callback(key_name, KeyState.PRESSED)
                    except Exception:
                        pass
                
            else:
                # Fallback to original handler if event format is unexpected
                if hasattr(self, '_original_handle_key_press'):
                    self._original_handle_key_press(event)
                    
        except Exception as e:
            # Fallback to original handler on error
            if hasattr(self, '_original_handle_key_press'):
                self._original_handle_key_press(event)
    
    def _optimized_handle_key_release(self, event):
        """
        Optimized version of key release handler.
        
        This method intercepts key release events, applies optimizations,
        and then calls the original handler.
        """
        try:
            # Extract key information from event
            if hasattr(event, 'data') and isinstance(event.data, dict):
                key_name = event.data.get('key', '')
                timestamp = event.timestamp
                
                # Apply anti-ghosting and NKRO processing
                success = self.anti_ghosting_engine.process_key_event(
                    key_name, False, timestamp
                )
                
                if not success:
                    # Key release was blocked (shouldn't happen)
                    return
                
                # Update statistics
                self._update_stats()
                
                # Create optimized event with additional data
                optimized_event = type(event)(
                    event_type=event.event_type,
                    data={
                        **event.data,
                        'nkro_processed': True,
                        'ghosting_prevented': False,
                        'simultaneous_keys': len(self.anti_ghosting_engine.get_active_keys())
                    },
                    priority=event.priority,
                    timestamp=event.timestamp,
                    source=event.source
                )
                
                # Call original handler with optimized event
                if hasattr(self, '_original_handle_key_release'):
                    self._original_handle_key_release(optimized_event)
                
                # Trigger callbacks
                for callback in self.optimization_callbacks:
                    try:
                        callback(key_name, KeyState.RELEASED)
                    except Exception:
                        pass
                
            else:
                # Fallback to original handler if event format is unexpected
                if hasattr(self, '_original_handle_key_release'):
                    self._original_handle_key_release(event)
                    
        except Exception as e:
            # Fallback to original handler on error
            if hasattr(self, '_original_handle_key_release'):
                self._original_handle_key_release(event)
    
    def _update_stats(self, nkro_processed: bool = False, ghosting_prevented: bool = False):
        """Update optimization statistics."""
        with self.stats_lock:
            self.stats.total_events_processed += 1
            self.stats.last_update_time = time.time()
            
            if nkro_processed:
                self.stats.nkro_events_processed += 1
            
            if ghosting_prevented:
                self.stats.ghosting_events_prevented += 1
            
            # Update max simultaneous keys
            active_keys = self.anti_ghosting_engine.get_active_keys()
            self.stats.max_simultaneous_keys = max(
                self.stats.max_simultaneous_keys,
                len(active_keys)
            )
            
            # Update key combinations
            combinations = self.anti_ghosting_engine.get_key_combinations()
            self.stats.key_combinations_detected = len(combinations)
    
    def _integration_loop(self):
        """Main integration loop for monitoring and optimization."""
        try:
            while self.is_integrated:
                try:
                    # Update performance monitor if available
                    if self.performance_monitor:
                        self._update_performance_monitor()
                    
                    # Sleep for monitoring interval
                    time.sleep(1.0)
                    
                except Exception:
                    time.sleep(1.0)
                    
        except Exception:
            pass
    
    def _update_performance_monitor(self):
        """Update performance monitor with optimization metrics."""
        if not self.performance_monitor:
            return
        
        try:
            with self.stats_lock:
                # Update performance monitor with keyboard-specific metrics
                self.performance_monitor.update_application_metrics(
                    events_processed=self.stats.total_events_processed,
                    queue_size=0,  # Keyboard optimization doesn't use a queue
                    queue_utilization=0.0,
                    events_dropped=self.stats.ghosting_events_prevented,
                    processing_latency_ms=self.stats.average_processing_time_ms
                )
        except Exception:
            pass
    
    def update_config(self, config: KeyboardOptimizationConfig):
        """
        Update keyboard optimization configuration.
        
        Args:
            config: New optimization configuration
        """
        with self._lock:
            self.config = config
            
            # Update anti-ghosting engine
            self.anti_ghosting_engine = AntiGhostingEngine(
                enable_nkro=config.enable_nkro,
                max_keys=config.max_simultaneous_keys
            )
            
            # Update ghosting prevention
            self.anti_ghosting_engine.enable_ghosting_prevention(config.enable_ghosting_prevention)
            self.anti_ghosting_engine.enable_combination_detection(config.enable_combination_detection)
    
    def get_config(self) -> KeyboardOptimizationConfig:
        """Get current optimization configuration."""
        return self.config
    
    def get_stats(self) -> KeyboardOptimizationStats:
        """Get optimization statistics."""
        with self.stats_lock:
            return KeyboardOptimizationStats(
                total_events_processed=self.stats.total_events_processed,
                nkro_events_processed=self.stats.nkro_events_processed,
                ghosting_events_prevented=self.stats.ghosting_events_prevented,
                key_combinations_detected=self.stats.key_combinations_detected,
                rapid_trigger_events=self.stats.rapid_trigger_events,
                debounced_events=self.stats.debounced_events,
                average_processing_time_ms=self.stats.average_processing_time_ms,
                max_simultaneous_keys=self.stats.max_simultaneous_keys,
                last_update_time=self.stats.last_update_time
            )
    
    def reset_stats(self):
        """Reset optimization statistics."""
        with self.stats_lock:
            self.stats = KeyboardOptimizationStats()
        
        self.anti_ghosting_engine.reset_stats()
    
    def get_active_keys(self) -> List[str]:
        """Get currently active keys."""
        return list(self.anti_ghosting_engine.get_active_keys())
    
    def get_key_combinations(self) -> List[KeyCombination]:
        """Get currently active key combinations."""
        return self.anti_ghosting_engine.get_key_combinations()
    
    def get_key_info(self, key: str) -> Optional[KeyInfo]:
        """Get information about a specific key."""
        return self.anti_ghosting_engine.get_key_info(key)
    
    def add_optimization_callback(self, callback: Callable[[str, KeyState], None]):
        """
        Add callback for optimization events.
        
        Args:
            callback: Function to call with key state changes
        """
        self.optimization_callbacks.append(callback)
        self.anti_ghosting_engine.add_key_callback(callback)
    
    def remove_optimization_callback(self, callback: Callable[[str, KeyState], None]):
        """
        Remove optimization callback.
        
        Args:
            callback: Function to remove
        """
        try:
            self.optimization_callbacks.remove(callback)
        except ValueError:
            pass
        
        self.anti_ghosting_engine.remove_key_callback(callback)
    
    def clear_all_keys(self):
        """Clear all key states (emergency reset)."""
        self.anti_ghosting_engine.clear_all_keys()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = self.get_stats()
        anti_ghosting_stats = self.anti_ghosting_engine.get_stats()
        
        return {
            'integration_active': self.is_integrated,
            'nkro_enabled': self.config.enable_nkro,
            'ghosting_prevention_enabled': self.config.enable_ghosting_prevention,
            'max_simultaneous_keys': self.config.max_simultaneous_keys,
            'optimization_stats': {
                'total_events_processed': stats.total_events_processed,
                'nkro_events_processed': stats.nkro_events_processed,
                'ghosting_events_prevented': stats.ghosting_events_prevented,
                'key_combinations_detected': stats.key_combinations_detected,
                'max_simultaneous_keys': stats.max_simultaneous_keys,
                'last_update_time': stats.last_update_time
            },
            'anti_ghosting_stats': {
                'total_keys_tracked': anti_ghosting_stats.total_keys_tracked,
                'simultaneous_keys_max': anti_ghosting_stats.simultaneous_keys_max,
                'nkro_events_processed': anti_ghosting_stats.nkro_events_processed,
                'processing_time_ms': anti_ghosting_stats.processing_time_ms
            },
            'callbacks_count': len(self.optimization_callbacks)
        }


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create mock keyboard handler
    class MockKeyboardHandler:
        def __init__(self):
            self.events_processed = 0
            self.last_event_data = None
        
        def _handle_key_press(self, event):
            self.events_processed += 1
            self.last_event_data = event.data
            print(f"Key press processed: {event.data}")
        
        def _handle_key_release(self, event):
            self.events_processed += 1
            self.last_event_data = event.data
            print(f"Key release processed: {event.data}")
    
    # Create keyboard optimization integration
    keyboard_handler = MockKeyboardHandler()
    config = KeyboardOptimizationConfig(
        enable_nkro=True,
        max_simultaneous_keys=0,  # Unlimited
        enable_ghosting_prevention=True,
        enable_combination_detection=True
    )
    
    integration = KeyboardOptimizationIntegration(
        keyboard_handler=keyboard_handler,
        config=config
    )
    
    print("Testing Keyboard Optimization Integration...")
    
    # Add callback for testing
    def optimization_callback(key: str, state: KeyState):
        print(f"Optimization callback: {key} -> {state.value}")
    
    integration.add_optimization_callback(optimization_callback)
    
    # Integrate
    if integration.integrate():
        print("✓ Keyboard optimization integration started")
        
        try:
            # Simulate keyboard events
            for i in range(20):
                # Create mock event
                class MockEvent:
                    def __init__(self, key, pressed):
                        self.event_type = "key_press" if pressed else "key_release"
                        self.data = {'key': key, 'key_code': hash(key) % 1000}
                        self.priority = "normal"
                        self.timestamp = time.time()
                        self.source = "test"
                
                # Test various keys
                test_keys = ['w', 'a', 's', 'd', 'space', 'shift', 'ctrl']
                key = random.choice(test_keys)
                pressed = random.choice([True, False])
                
                event = MockEvent(key, pressed)
                
                # Process through integration
                if pressed:
                    integration._optimized_handle_key_press(event)
                else:
                    integration._optimized_handle_key_release(event)
                
                time.sleep(0.05)
            
            # Get statistics
            stats = integration.get_stats()
            print(f"✓ Events processed: {stats.total_events_processed}")
            print(f"✓ NKRO events: {stats.nkro_events_processed}")
            print(f"✓ Ghosting prevented: {stats.ghosting_events_prevented}")
            print(f"✓ Key combinations: {stats.key_combinations_detected}")
            print(f"✓ Max simultaneous keys: {stats.max_simultaneous_keys}")
            
            # Test active keys
            active_keys = integration.get_active_keys()
            print(f"✓ Active keys: {active_keys}")
            
            # Test key combinations
            combinations = integration.get_key_combinations()
            print(f"✓ Key combinations: {len(combinations)}")
            for combo in combinations:
                print(f"  - {combo.name}: {combo.keys}")
            
            # Get final stats
            final_stats = integration.get_performance_stats()
            print(f"✓ Final stats: {final_stats}")
            
        except Exception as e:
            print(f"✗ Error during integration test: {e}")
        finally:
            integration.disconnect()
            print("✓ Keyboard optimization integration stopped")
    else:
        print("✗ Failed to start keyboard optimization integration")
    
    print("\nKeyboard optimization integration testing completed!")
