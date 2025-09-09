"""
Smoothing Integration Module for ZeroLag

This module integrates the smoothing algorithms with the mouse handling
system to provide seamless cursor smoothing functionality.

Features:
- Integration with GamingMouseHandler
- Real-time smoothing configuration
- Performance monitoring
- Smoothing quality metrics
- Automatic optimization
"""

import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

from .smoothing_algorithms import (
    SmoothingEngine,
    SmoothingConfig,
    SmoothingType,
    SmoothingResult
)
from ..input.mouse_handler import GamingMouseHandler
from ..monitoring.performance_monitor import PerformanceMonitor


@dataclass
class SmoothingMetrics:
    """Metrics for smoothing performance and quality."""
    total_events_processed: int = 0
    total_processing_time_ms: float = 0.0
    average_processing_time_ms: float = 0.0
    smoothing_quality_score: float = 0.0
    jitter_reduction_percent: float = 0.0
    velocity_tracking_accuracy: float = 0.0
    last_update_time: float = 0.0


class SmoothingIntegration:
    """
    Integrates smoothing algorithms with mouse handling system.
    
    Provides seamless cursor smoothing with real-time configuration
    and performance monitoring.
    """
    
    def __init__(self, 
                 mouse_handler: Optional[GamingMouseHandler] = None,
                 performance_monitor: Optional[PerformanceMonitor] = None,
                 config: Optional[SmoothingConfig] = None):
        """
        Initialize smoothing integration.
        
        Args:
            mouse_handler: GamingMouseHandler instance
            performance_monitor: PerformanceMonitor instance
            config: Smoothing configuration
        """
        self.mouse_handler = mouse_handler
        self.performance_monitor = performance_monitor
        self.config = config or SmoothingConfig()
        
        # Initialize smoothing engine
        self.smoothing_engine = SmoothingEngine(self.config)
        
        # Integration state
        self.is_integrated = False
        self.integration_thread: Optional[threading.Thread] = None
        
        # Metrics tracking
        self.metrics = SmoothingMetrics()
        self.metrics_lock = threading.RLock()
        
        # Callbacks
        self.smoothing_callbacks: List[Callable[[SmoothingResult], None]] = []
        
        # Threading
        self._lock = threading.RLock()
    
    def integrate(self) -> bool:
        """
        Integrate with the mouse handler.
        
        Returns:
            True if integration successful, False otherwise
        """
        if self.is_integrated:
            return True
        
        try:
            with self._lock:
                if self.mouse_handler:
                    # Hook into mouse handler's event processing
                    self._hook_mouse_handler()
                
                self.is_integrated = True
                
                # Start integration thread for monitoring
                self.integration_thread = threading.Thread(
                    target=self._integration_loop,
                    daemon=True,
                    name="SmoothingIntegrationThread"
                )
                self.integration_thread.start()
                
                return True
                
        except Exception as e:
            self.is_integrated = False
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from mouse handler.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        if not self.is_integrated:
            return True
        
        try:
            with self._lock:
                self.is_integrated = False
                
                # Unhook from mouse handler
                if self.mouse_handler:
                    self._unhook_mouse_handler()
                
                # Wait for integration thread to finish
                if self.integration_thread and self.integration_thread.is_alive():
                    self.integration_thread.join(timeout=2.0)
                
                return True
                
        except Exception as e:
            return False
    
    def _hook_mouse_handler(self):
        """Hook into mouse handler's event processing."""
        if not self.mouse_handler:
            return
        
        # Store original method
        if hasattr(self.mouse_handler, '_handle_mouse_move'):
            self._original_handle_mouse_move = self.mouse_handler._handle_mouse_move
            
            # Replace with smoothed version
            self.mouse_handler._handle_mouse_move = self._smoothed_handle_mouse_move
    
    def _unhook_mouse_handler(self):
        """Unhook from mouse handler's event processing."""
        if not self.mouse_handler:
            return
        
        # Restore original method
        if hasattr(self, '_original_handle_mouse_move'):
            self.mouse_handler._handle_mouse_move = self._original_handle_mouse_move
    
    def _smoothed_handle_mouse_move(self, event):
        """
        Smoothed version of mouse move handler.
        
        This method intercepts mouse movement events, applies smoothing,
        and then calls the original handler with smoothed coordinates.
        """
        try:
            # Extract coordinates from event
            if hasattr(event, 'data') and isinstance(event.data, dict):
                x = event.data.get('x', 0)
                y = event.data.get('y', 0)
                
                # Apply smoothing
                smoothing_result = self.smoothing_engine.smooth(x, y)
                
                # Update metrics
                self._update_metrics(smoothing_result)
                
                # Create new event with smoothed coordinates
                smoothed_event = type(event)(
                    event_type=event.event_type,
                    data={
                        **event.data,
                        'x': smoothing_result.smoothed_x,
                        'y': smoothing_result.smoothed_y,
                        'velocity_x': smoothing_result.velocity_x,
                        'velocity_y': smoothing_result.velocity_y,
                        'smoothing_factor': smoothing_result.smoothing_factor,
                        'smoothing_confidence': smoothing_result.confidence
                    },
                    priority=event.priority,
                    timestamp=event.timestamp,
                    source=event.source
                )
                
                # Call original handler with smoothed event
                if hasattr(self, '_original_handle_mouse_move'):
                    self._original_handle_mouse_move(smoothed_event)
                
                # Trigger callbacks
                for callback in self.smoothing_callbacks:
                    try:
                        callback(smoothing_result)
                    except Exception:
                        pass
                
            else:
                # Fallback to original handler if event format is unexpected
                if hasattr(self, '_original_handle_mouse_move'):
                    self._original_handle_mouse_move(event)
                    
        except Exception as e:
            # Fallback to original handler on error
            if hasattr(self, '_original_handle_mouse_move'):
                self._original_handle_mouse_move(event)
    
    def _update_metrics(self, result: SmoothingResult):
        """Update smoothing metrics."""
        with self.metrics_lock:
            self.metrics.total_events_processed += 1
            self.metrics.total_processing_time_ms += result.processing_time_ms
            self.metrics.average_processing_time_ms = (
                self.metrics.total_processing_time_ms / self.metrics.total_events_processed
            )
            self.metrics.last_update_time = time.time()
            
            # Calculate smoothing quality score (simplified)
            # Higher confidence and lower processing time = better quality
            self.metrics.smoothing_quality_score = (
                result.confidence * (1.0 - min(result.processing_time_ms / 10.0, 1.0))
            )
    
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
        """Update performance monitor with smoothing metrics."""
        if not self.performance_monitor:
            return
        
        try:
            with self.metrics_lock:
                # Update performance monitor with smoothing-specific metrics
                self.performance_monitor.update_application_metrics(
                    events_processed=self.metrics.total_events_processed,
                    queue_size=0,  # Smoothing doesn't use a queue
                    queue_utilization=0.0,
                    events_dropped=0,  # Smoothing doesn't drop events
                    processing_latency_ms=self.metrics.average_processing_time_ms
                )
        except Exception:
            pass
    
    def update_config(self, config: SmoothingConfig):
        """
        Update smoothing configuration.
        
        Args:
            config: New smoothing configuration
        """
        with self._lock:
            self.config = config
            self.smoothing_engine.update_config(config)
    
    def get_config(self) -> SmoothingConfig:
        """Get current smoothing configuration."""
        return self.config
    
    def get_metrics(self) -> SmoothingMetrics:
        """Get smoothing metrics."""
        with self.metrics_lock:
            return SmoothingMetrics(
                total_events_processed=self.metrics.total_events_processed,
                total_processing_time_ms=self.metrics.total_processing_time_ms,
                average_processing_time_ms=self.metrics.average_processing_time_ms,
                smoothing_quality_score=self.metrics.smoothing_quality_score,
                jitter_reduction_percent=self.metrics.jitter_reduction_percent,
                velocity_tracking_accuracy=self.metrics.velocity_tracking_accuracy,
                last_update_time=self.metrics.last_update_time
            )
    
    def reset_metrics(self):
        """Reset smoothing metrics."""
        with self.metrics_lock:
            self.metrics = SmoothingMetrics()
    
    def reset_smoothing(self):
        """Reset smoothing engine state."""
        self.smoothing_engine.reset()
    
    def add_smoothing_callback(self, callback: Callable[[SmoothingResult], None]):
        """
        Add a callback for smoothing results.
        
        Args:
            callback: Function to call with smoothing results
        """
        self.smoothing_callbacks.append(callback)
    
    def remove_smoothing_callback(self, callback: Callable[[SmoothingResult], None]):
        """
        Remove a smoothing callback.
        
        Args:
            callback: Function to remove
        """
        try:
            self.smoothing_callbacks.remove(callback)
        except ValueError:
            pass
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        metrics = self.get_metrics()
        engine_stats = self.smoothing_engine.get_performance_stats()
        
        return {
            'integration_active': self.is_integrated,
            'smoothing_type': self.config.smoothing_type.value,
            'smoothing_enabled': self.config.enabled,
            'metrics': {
                'total_events_processed': metrics.total_events_processed,
                'average_processing_time_ms': metrics.average_processing_time_ms,
                'smoothing_quality_score': metrics.smoothing_quality_score,
                'last_update_time': metrics.last_update_time
            },
            'engine_stats': engine_stats,
            'callbacks_count': len(self.smoothing_callbacks)
        }
    
    def optimize_for_performance(self) -> Dict[str, Any]:
        """
        Optimize smoothing for performance.
        
        Automatically adjusts configuration for better performance.
        
        Returns:
            Dictionary with optimization results
        """
        optimization_start = time.time()
        
        try:
            # Get current performance
            current_stats = self.get_performance_stats()
            current_avg_time = current_stats['metrics']['average_processing_time_ms']
            
            # Optimize based on current performance
            if current_avg_time > 1.0:  # If processing takes more than 1ms
                # Switch to faster smoothing algorithm
                if self.config.smoothing_type == SmoothingType.KALMAN:
                    self.config.smoothing_type = SmoothingType.EXPONENTIAL_MA
                elif self.config.smoothing_type == SmoothingType.GAUSSIAN:
                    self.config.smoothing_type = SmoothingType.LOW_PASS
                
                # Reduce smoothing intensity
                if self.config.smoothing_type == SmoothingType.EXPONENTIAL_MA:
                    self.config.ema_alpha = min(0.3, self.config.ema_alpha * 1.5)
                elif self.config.smoothing_type == SmoothingType.ADAPTIVE:
                    self.config.adaptive_max_smoothing = min(0.5, self.config.adaptive_max_smoothing * 1.2)
                
                # Update configuration
                self.update_config(self.config)
                
                optimization_result = {
                    'optimization_applied': True,
                    'previous_avg_time_ms': current_avg_time,
                    'new_smoothing_type': self.config.smoothing_type.value,
                    'optimization_duration_ms': (time.time() - optimization_start) * 1000
                }
            else:
                optimization_result = {
                    'optimization_applied': False,
                    'reason': 'Performance already optimal',
                    'current_avg_time_ms': current_avg_time,
                    'optimization_duration_ms': (time.time() - optimization_start) * 1000
                }
            
            return optimization_result
            
        except Exception as e:
            return {
                'optimization_applied': False,
                'error': str(e),
                'optimization_duration_ms': (time.time() - optimization_start) * 1000
            }
    
    def optimize_for_quality(self) -> Dict[str, Any]:
        """
        Optimize smoothing for quality.
        
        Automatically adjusts configuration for better smoothing quality.
        
        Returns:
            Dictionary with optimization results
        """
        optimization_start = time.time()
        
        try:
            # Get current quality
            current_metrics = self.get_metrics()
            current_quality = current_metrics.smoothing_quality_score
            
            # Optimize based on current quality
            if current_quality < 0.7:  # If quality is below threshold
                # Switch to higher quality smoothing algorithm
                if self.config.smoothing_type == SmoothingType.LOW_PASS:
                    self.config.smoothing_type = SmoothingType.EXPONENTIAL_MA
                elif self.config.smoothing_type == SmoothingType.EXPONENTIAL_MA:
                    self.config.smoothing_type = SmoothingType.KALMAN
                
                # Increase smoothing intensity
                if self.config.smoothing_type == SmoothingType.EXPONENTIAL_MA:
                    self.config.ema_alpha = max(0.05, self.config.ema_alpha * 0.8)
                elif self.config.smoothing_type == SmoothingType.ADAPTIVE:
                    self.config.adaptive_max_smoothing = min(0.5, self.config.adaptive_max_smoothing * 1.1)
                
                # Update configuration
                self.update_config(self.config)
                
                optimization_result = {
                    'optimization_applied': True,
                    'previous_quality_score': current_quality,
                    'new_smoothing_type': self.config.smoothing_type.value,
                    'optimization_duration_ms': (time.time() - optimization_start) * 1000
                }
            else:
                optimization_result = {
                    'optimization_applied': False,
                    'reason': 'Quality already optimal',
                    'current_quality_score': current_quality,
                    'optimization_duration_ms': (time.time() - optimization_start) * 1000
                }
            
            return optimization_result
            
        except Exception as e:
            return {
                'optimization_applied': False,
                'error': str(e),
                'optimization_duration_ms': (time.time() - optimization_start) * 1000
            }


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create mock mouse handler
    class MockMouseHandler:
        def __init__(self):
            self.events_processed = 0
        
        def _handle_mouse_move(self, event):
            self.events_processed += 1
            print(f"Mouse move processed: {event.data}")
    
    # Create smoothing integration
    mouse_handler = MockMouseHandler()
    config = SmoothingConfig(
        smoothing_type=SmoothingType.ADAPTIVE,
        enabled=True
    )
    
    integration = SmoothingIntegration(
        mouse_handler=mouse_handler,
        config=config
    )
    
    print("Testing smoothing integration...")
    
    # Integrate
    if integration.integrate():
        print("✓ Smoothing integration started")
        
        try:
            # Simulate mouse movement events
            for i in range(20):
                # Create mock event
                class MockEvent:
                    def __init__(self, x, y):
                        self.event_type = "mouse_move"
                        self.data = {'x': x, 'y': y}
                        self.priority = "normal"
                        self.timestamp = time.time()
                        self.source = "test"
                
                # Add some noise to simulate jittery movement
                base_x = 100 + i * 2
                base_y = 100 + i * 2
                noisy_x = base_x + random.gauss(0, 2.0)
                noisy_y = base_y + random.gauss(0, 2.0)
                
                event = MockEvent(noisy_x, noisy_y)
                
                # Process through integration
                integration._smoothed_handle_mouse_move(event)
                
                time.sleep(0.05)
            
            # Get metrics
            metrics = integration.get_metrics()
            print(f"✓ Events processed: {metrics.total_events_processed}")
            print(f"✓ Average processing time: {metrics.average_processing_time_ms:.3f}ms")
            print(f"✓ Smoothing quality score: {metrics.smoothing_quality_score:.3f}")
            
            # Test optimization
            print("\nTesting optimization...")
            
            # Optimize for performance
            perf_optimization = integration.optimize_for_performance()
            print(f"✓ Performance optimization: {perf_optimization}")
            
            # Optimize for quality
            quality_optimization = integration.optimize_for_quality()
            print(f"✓ Quality optimization: {quality_optimization}")
            
            # Get final stats
            final_stats = integration.get_performance_stats()
            print(f"✓ Final stats: {final_stats}")
            
        except Exception as e:
            print(f"✗ Error during integration test: {e}")
        finally:
            integration.disconnect()
            print("✓ Smoothing integration stopped")
    else:
        print("✗ Failed to start smoothing integration")
    
    print("\nSmoothing integration testing completed!")
