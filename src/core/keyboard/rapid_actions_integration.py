"""
Rapid Actions Integration for ZeroLag

This module integrates the rapid actions and advanced features with the existing
keyboard handling system to provide seamless gaming optimizations.

Features:
- Integration with GamingKeyboardHandler
- Real-time rapid actions processing
- Advanced keyboard optimizations
- Performance monitoring and statistics
- Gaming-specific feature detection
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .rapid_actions import (
    RapidActionsEngine,
    RapidTriggerConfig,
    SnapTapConfig,
    TurboModeConfig,
    AdaptiveResponseConfig,
    ActuationEmulationConfig,
    RapidActionType,
    RapidActionStats
)
from ..input.keyboard_handler import GamingKeyboardHandler
from ..monitoring.performance_monitor import PerformanceMonitor


@dataclass
class RapidActionsIntegrationConfig:
    """Configuration for rapid actions integration."""
    enable_rapid_trigger: bool = True
    enable_snap_tap: bool = True
    enable_turbo_mode: bool = True
    enable_adaptive_response: bool = True
    enable_actuation_emulation: bool = True
    
    # Rapid Trigger settings
    rapid_trigger_threshold_ms: float = 10.0
    rapid_trigger_reset_delay_ms: float = 5.0
    
    # Snap Tap settings
    snap_tap_neutral_prevention_ms: float = 50.0
    
    # Turbo Mode settings
    turbo_repeat_rate_ms: float = 50.0
    turbo_initial_delay_ms: float = 500.0
    
    # Adaptive Response settings
    adaptive_learning_rate: float = 0.1
    adaptive_history_size: int = 100
    
    # Actuation Emulation settings
    actuation_point: float = 0.5
    actuation_hysteresis: float = 0.1


@dataclass
class RapidActionsIntegrationStats:
    """Statistics for rapid actions integration."""
    total_events_processed: int = 0
    rapid_trigger_events: int = 0
    snap_tap_events: int = 0
    turbo_mode_events: int = 0
    adaptive_response_events: int = 0
    actuation_emulation_events: int = 0
    average_processing_time_ms: float = 0.0
    last_update_time: float = 0.0


class RapidActionsIntegration:
    """
    Integrates rapid actions and advanced features with the keyboard handler.
    
    Provides seamless rapid trigger, snap tap, turbo mode, and other advanced
    keyboard optimizations while maintaining compatibility with the existing system.
    """
    
    def __init__(self, 
                 keyboard_handler: Optional[GamingKeyboardHandler] = None,
                 performance_monitor: Optional[PerformanceMonitor] = None,
                 config: Optional[RapidActionsIntegrationConfig] = None):
        """
        Initialize rapid actions integration.
        
        Args:
            keyboard_handler: GamingKeyboardHandler instance
            performance_monitor: PerformanceMonitor instance
            config: Rapid actions integration configuration
        """
        self.keyboard_handler = keyboard_handler
        self.performance_monitor = performance_monitor
        self.config = config or RapidActionsIntegrationConfig()
        
        # Initialize rapid actions engine
        self.rapid_actions_engine = RapidActionsEngine(
            rapid_trigger_config=RapidTriggerConfig(
                enabled=self.config.enable_rapid_trigger,
                threshold_ms=self.config.rapid_trigger_threshold_ms,
                reset_delay_ms=self.config.rapid_trigger_reset_delay_ms
            ),
            snap_tap_config=SnapTapConfig(
                enabled=self.config.enable_snap_tap,
                neutral_prevention_ms=self.config.snap_tap_neutral_prevention_ms
            ),
            turbo_mode_config=TurboModeConfig(
                enabled=self.config.enable_turbo_mode,
                repeat_rate_ms=self.config.turbo_repeat_rate_ms,
                initial_delay_ms=self.config.turbo_initial_delay_ms
            ),
            adaptive_response_config=AdaptiveResponseConfig(
                enabled=self.config.enable_adaptive_response,
                learning_rate=self.config.adaptive_learning_rate,
                history_size=self.config.adaptive_history_size
            ),
            actuation_emulation_config=ActuationEmulationConfig(
                enabled=self.config.enable_actuation_emulation,
                actuation_point=self.config.actuation_point,
                hysteresis=self.config.actuation_hysteresis
            )
        )
        
        # Integration state
        self.is_integrated = False
        self.integration_thread: Optional[threading.Thread] = None
        
        # Statistics tracking
        self.stats = RapidActionsIntegrationStats()
        self.stats_lock = threading.RLock()
        
        # Callbacks
        self.rapid_actions_callbacks: List[Callable[[str, RapidActionType], None]] = []
        
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
                    name="RapidActionsIntegrationThread"
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
        
        # Store original methods
        if hasattr(self.keyboard_handler, '_handle_key_press'):
            self._original_handle_key_press = self.keyboard_handler._handle_key_press
            
            # Replace with rapid actions version
            self.keyboard_handler._handle_key_press = self._rapid_actions_handle_key_press
        
        if hasattr(self.keyboard_handler, '_handle_key_release'):
            self._original_handle_key_release = self.keyboard_handler._handle_key_release
            
            # Replace with rapid actions version
            self.keyboard_handler._handle_key_release = self._rapid_actions_handle_key_release
    
    def _unhook_keyboard_handler(self):
        """Unhook from keyboard handler's event processing."""
        if not self.keyboard_handler:
            return
        
        # Restore original methods
        if hasattr(self, '_original_handle_key_press'):
            self.keyboard_handler._handle_key_press = self._original_handle_key_press
        
        if hasattr(self, '_original_handle_key_release'):
            self.keyboard_handler._handle_key_release = self._original_handle_key_release
    
    def _rapid_actions_handle_key_press(self, event):
        """
        Rapid actions version of key press handler.
        
        This method intercepts key press events, applies rapid actions,
        and then calls the original handler.
        """
        try:
            # Extract key information from event
            if hasattr(event, 'data') and isinstance(event.data, dict):
                key_name = event.data.get('key', '')
                timestamp = event.timestamp
                pressure = event.data.get('pressure', 0.5)  # Default pressure
                
                # Process through rapid actions engine
                result = self.rapid_actions_engine.process_key_event(
                    key_name, True, timestamp, pressure
                )
                
                # Update statistics
                self._update_stats(result)
                
                # Handle rapid trigger reset delay
                if result['reset_delay_ms']:
                    # Schedule key reset
                    threading.Timer(
                        result['reset_delay_ms'] / 1000.0,
                        self._reset_key_state,
                        args=[key_name]
                    ).start()
                
                # Handle snap tap opposite key release
                if result['opposite_key_to_release']:
                    # Release opposite key first
                    self._release_opposite_key(result['opposite_key_to_release'])
                
                # Create enhanced event with rapid actions data
                enhanced_event = type(event)(
                    event_type=event.event_type,
                    data={
                        **event.data,
                        'rapid_trigger_active': result['rapid_trigger_active'],
                        'snap_tap_active': result['snap_tap_active'],
                        'turbo_mode_active': result['turbo_mode_active'],
                        'adaptive_response_active': result['adaptive_response_active'],
                        'actuation_emulation_active': result['actuation_emulation_active'],
                        'response_multiplier': result['response_multiplier'],
                        'should_actuate': result['should_actuate']
                    },
                    priority=event.priority,
                    timestamp=event.timestamp,
                    source=event.source
                )
                
                # Call original handler with enhanced event
                if hasattr(self, '_original_handle_key_press'):
                    self._original_handle_key_press(enhanced_event)
                
                # Trigger callbacks
                for callback in self.rapid_actions_callbacks:
                    try:
                        if result['rapid_trigger_active']:
                            callback(key_name, RapidActionType.RAPID_TRIGGER)
                        if result['snap_tap_active']:
                            callback(key_name, RapidActionType.SNAP_TAP)
                        if result['turbo_mode_active']:
                            callback(key_name, RapidActionType.TURBO_MODE)
                        if result['adaptive_response_active']:
                            callback(key_name, RapidActionType.ADAPTIVE_RESPONSE)
                        if result['actuation_emulation_active']:
                            callback(key_name, RapidActionType.ACTUATION_EMULATION)
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
    
    def _rapid_actions_handle_key_release(self, event):
        """
        Rapid actions version of key release handler.
        
        This method intercepts key release events, applies rapid actions,
        and then calls the original handler.
        """
        try:
            # Extract key information from event
            if hasattr(event, 'data') and isinstance(event.data, dict):
                key_name = event.data.get('key', '')
                timestamp = event.timestamp
                
                # Process through rapid actions engine
                result = self.rapid_actions_engine.process_key_event(
                    key_name, False, timestamp
                )
                
                # Update statistics
                self._update_stats(result)
                
                # Create enhanced event with rapid actions data
                enhanced_event = type(event)(
                    event_type=event.event_type,
                    data={
                        **event.data,
                        'rapid_trigger_active': result['rapid_trigger_active'],
                        'snap_tap_active': result['snap_tap_active'],
                        'turbo_mode_active': result['turbo_mode_active'],
                        'adaptive_response_active': result['adaptive_response_active'],
                        'actuation_emulation_active': result['actuation_emulation_active'],
                        'response_multiplier': result['response_multiplier'],
                        'should_actuate': result['should_actuate']
                    },
                    priority=event.priority,
                    timestamp=event.timestamp,
                    source=event.source
                )
                
                # Call original handler with enhanced event
                if hasattr(self, '_original_handle_key_release'):
                    self._original_handle_key_release(enhanced_event)
                
                # Trigger callbacks
                for callback in self.rapid_actions_callbacks:
                    try:
                        if result['rapid_trigger_active']:
                            callback(key_name, RapidActionType.RAPID_TRIGGER)
                        if result['snap_tap_active']:
                            callback(key_name, RapidActionType.SNAP_TAP)
                        if result['turbo_mode_active']:
                            callback(key_name, RapidActionType.TURBO_MODE)
                        if result['adaptive_response_active']:
                            callback(key_name, RapidActionType.ADAPTIVE_RESPONSE)
                        if result['actuation_emulation_active']:
                            callback(key_name, RapidActionType.ACTUATION_EMULATION)
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
    
    def _reset_key_state(self, key: str):
        """Reset key state for rapid trigger."""
        self.rapid_actions_engine.rapid_trigger.reset_key_state(key)
    
    def _release_opposite_key(self, opposite_key: str):
        """Release opposite key for snap tap."""
        # This would need to be implemented based on the keyboard handler's API
        # For now, we'll just log it
        print(f"Snap tap: releasing opposite key {opposite_key}")
    
    def _update_stats(self, result: Dict[str, Any]):
        """Update integration statistics."""
        with self.stats_lock:
            self.stats.total_events_processed += 1
            self.stats.last_update_time = time.time()
            
            if result['rapid_trigger_active']:
                self.stats.rapid_trigger_events += 1
            
            if result['snap_tap_active']:
                self.stats.snap_tap_events += 1
            
            if result['turbo_mode_active']:
                self.stats.turbo_mode_events += 1
            
            if result['adaptive_response_active']:
                self.stats.adaptive_response_events += 1
            
            if result['actuation_emulation_active']:
                self.stats.actuation_emulation_events += 1
    
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
        """Update performance monitor with rapid actions metrics."""
        if not self.performance_monitor:
            return
        
        try:
            with self.stats_lock:
                # Update performance monitor with rapid actions-specific metrics
                self.performance_monitor.update_application_metrics(
                    events_processed=self.stats.total_events_processed,
                    queue_size=0,  # Rapid actions doesn't use a queue
                    queue_utilization=0.0,
                    events_dropped=0,  # Rapid actions doesn't drop events
                    processing_latency_ms=self.stats.average_processing_time_ms
                )
        except Exception:
            pass
    
    def update_config(self, config: RapidActionsIntegrationConfig):
        """
        Update rapid actions integration configuration.
        
        Args:
            config: New integration configuration
        """
        with self._lock:
            self.config = config
            
            # Update rapid actions engine configuration
            self.rapid_actions_engine = RapidActionsEngine(
                rapid_trigger_config=RapidTriggerConfig(
                    enabled=config.enable_rapid_trigger,
                    threshold_ms=config.rapid_trigger_threshold_ms,
                    reset_delay_ms=config.rapid_trigger_reset_delay_ms
                ),
                snap_tap_config=SnapTapConfig(
                    enabled=config.enable_snap_tap,
                    neutral_prevention_ms=config.snap_tap_neutral_prevention_ms
                ),
                turbo_mode_config=TurboModeConfig(
                    enabled=config.enable_turbo_mode,
                    repeat_rate_ms=config.turbo_repeat_rate_ms,
                    initial_delay_ms=config.turbo_initial_delay_ms
                ),
                adaptive_response_config=AdaptiveResponseConfig(
                    enabled=config.enable_adaptive_response,
                    learning_rate=config.adaptive_learning_rate,
                    history_size=config.adaptive_history_size
                ),
                actuation_emulation_config=ActuationEmulationConfig(
                    enabled=config.enable_actuation_emulation,
                    actuation_point=config.actuation_point,
                    hysteresis=config.actuation_hysteresis
                )
            )
    
    def get_config(self) -> RapidActionsIntegrationConfig:
        """Get current integration configuration."""
        return self.config
    
    def get_stats(self) -> RapidActionsIntegrationStats:
        """Get integration statistics."""
        with self.stats_lock:
            return RapidActionsIntegrationStats(
                total_events_processed=self.stats.total_events_processed,
                rapid_trigger_events=self.stats.rapid_trigger_events,
                snap_tap_events=self.stats.snap_tap_events,
                turbo_mode_events=self.stats.turbo_mode_events,
                adaptive_response_events=self.stats.adaptive_response_events,
                actuation_emulation_events=self.stats.actuation_emulation_events,
                average_processing_time_ms=self.stats.average_processing_time_ms,
                last_update_time=self.stats.last_update_time
            )
    
    def reset_stats(self):
        """Reset integration statistics."""
        with self.stats_lock:
            self.stats = RapidActionsIntegrationStats()
        
        self.rapid_actions_engine.reset_stats()
    
    def get_active_keys(self) -> List[str]:
        """Get currently active keys."""
        return list(self.rapid_actions_engine.get_active_keys())
    
    def is_turbo_active(self, key: str) -> bool:
        """Check if turbo mode is active for a key."""
        return self.rapid_actions_engine.is_turbo_active(key)
    
    def get_response_multiplier(self, key: str) -> float:
        """Get response multiplier for a key."""
        return self.rapid_actions_engine.get_response_multiplier(key)
    
    def get_actuation_point(self, key: str) -> float:
        """Get actuation point for a key."""
        return self.rapid_actions_engine.get_actuation_point(key)
    
    def add_rapid_actions_callback(self, callback: Callable[[str, RapidActionType], None]):
        """
        Add callback for rapid actions events.
        
        Args:
            callback: Function to call with rapid action events
        """
        self.rapid_actions_callbacks.append(callback)
        self.rapid_actions_engine.add_callback(callback)
    
    def remove_rapid_actions_callback(self, callback: Callable[[str, RapidActionType], None]):
        """
        Remove rapid actions callback.
        
        Args:
            callback: Function to remove
        """
        try:
            self.rapid_actions_callbacks.remove(callback)
        except ValueError:
            pass
        
        self.rapid_actions_engine.remove_callback(callback)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        stats = self.get_stats()
        rapid_actions_stats = self.rapid_actions_engine.get_stats()
        
        return {
            'integration_active': self.is_integrated,
            'rapid_trigger_enabled': self.config.enable_rapid_trigger,
            'snap_tap_enabled': self.config.enable_snap_tap,
            'turbo_mode_enabled': self.config.enable_turbo_mode,
            'adaptive_response_enabled': self.config.enable_adaptive_response,
            'actuation_emulation_enabled': self.config.enable_actuation_emulation,
            'integration_stats': {
                'total_events_processed': stats.total_events_processed,
                'rapid_trigger_events': stats.rapid_trigger_events,
                'snap_tap_events': stats.snap_tap_events,
                'turbo_mode_events': stats.turbo_mode_events,
                'adaptive_response_events': stats.adaptive_response_events,
                'actuation_emulation_events': stats.actuation_emulation_events,
                'average_processing_time_ms': stats.average_processing_time_ms,
                'last_update_time': stats.last_update_time
            },
            'rapid_actions_stats': {
                'total_events_processed': rapid_actions_stats.total_events_processed,
                'rapid_trigger_events': rapid_actions_stats.rapid_trigger_events,
                'snap_tap_events': rapid_actions_stats.snap_tap_events,
                'turbo_mode_events': rapid_actions_stats.turbo_mode_events,
                'adaptive_response_adjustments': rapid_actions_stats.adaptive_response_adjustments,
                'actuation_emulation_events': rapid_actions_stats.actuation_emulation_events,
                'average_processing_time_ms': rapid_actions_stats.average_processing_time_ms
            },
            'callbacks_count': len(self.rapid_actions_callbacks)
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
    
    # Create rapid actions integration
    keyboard_handler = MockKeyboardHandler()
    config = RapidActionsIntegrationConfig(
        enable_rapid_trigger=True,
        enable_snap_tap=True,
        enable_turbo_mode=True,
        enable_adaptive_response=True,
        enable_actuation_emulation=True
    )
    
    integration = RapidActionsIntegration(
        keyboard_handler=keyboard_handler,
        config=config
    )
    
    print("Testing Rapid Actions Integration...")
    
    # Add callback for testing
    def rapid_actions_callback(key: str, action_type: RapidActionType):
        print(f"Rapid action callback: {key} -> {action_type.value}")
    
    integration.add_rapid_actions_callback(rapid_actions_callback)
    
    # Integrate
    if integration.integrate():
        print("✓ Rapid actions integration started")
        
        try:
            # Simulate keyboard events
            test_keys = ['w', 'a', 's', 'd', 'space', 'shift', 'ctrl']
            
            for i in range(30):
                # Create mock event
                class MockEvent:
                    def __init__(self, key, pressed):
                        self.event_type = "key_press" if pressed else "key_release"
                        self.data = {'key': key, 'key_code': hash(key) % 1000, 'pressure': random.uniform(0.3, 0.9)}
                        self.priority = "normal"
                        self.timestamp = time.time()
                        self.source = "test"
                
                key = random.choice(test_keys)
                pressed = random.choice([True, False])
                
                event = MockEvent(key, pressed)
                
                # Process through integration
                if pressed:
                    integration._rapid_actions_handle_key_press(event)
                else:
                    integration._rapid_actions_handle_key_release(event)
                
                time.sleep(0.01)
            
            # Get statistics
            stats = integration.get_stats()
            print(f"✓ Events processed: {stats.total_events_processed}")
            print(f"✓ Rapid trigger events: {stats.rapid_trigger_events}")
            print(f"✓ Snap tap events: {stats.snap_tap_events}")
            print(f"✓ Turbo mode events: {stats.turbo_mode_events}")
            print(f"✓ Adaptive response events: {stats.adaptive_response_events}")
            print(f"✓ Actuation emulation events: {stats.actuation_emulation_events}")
            
            # Test active keys
            active_keys = integration.get_active_keys()
            print(f"✓ Active keys: {active_keys}")
            
            # Test turbo mode
            if active_keys:
                turbo_active = integration.is_turbo_active(active_keys[0])
                print(f"✓ Turbo mode active for {active_keys[0]}: {turbo_active}")
            
            # Test response multiplier
            if active_keys:
                response_multiplier = integration.get_response_multiplier(active_keys[0])
                print(f"✓ Response multiplier for {active_keys[0]}: {response_multiplier:.2f}")
            
            # Test actuation point
            if active_keys:
                actuation_point = integration.get_actuation_point(active_keys[0])
                print(f"✓ Actuation point for {active_keys[0]}: {actuation_point:.2f}")
            
            # Get final stats
            final_stats = integration.get_performance_stats()
            print(f"✓ Final stats: {final_stats}")
            
        except Exception as e:
            print(f"✗ Error during integration test: {e}")
        finally:
            integration.disconnect()
            print("✓ Rapid actions integration stopped")
    else:
        print("✗ Failed to start rapid actions integration")
    
    print("\nRapid actions integration testing completed!")
