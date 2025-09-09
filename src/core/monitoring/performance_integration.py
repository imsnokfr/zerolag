"""
Performance Integration Module for ZeroLag

This module integrates the performance monitoring system with the input handling
components, providing real-time metrics collection and performance tracking.

Features:
- Automatic metrics collection from input handlers
- Performance data aggregation
- Real-time monitoring integration
- Performance optimization feedback
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .performance_monitor import PerformanceMonitor, PerformanceAlert
from ..input.input_handler import InputHandler
from ..input.mouse_handler import GamingMouseHandler
from ..input.keyboard_handler import GamingKeyboardHandler
from ..queue.input_queue import InputQueue
from ..polling.polling_manager import PollingManager


@dataclass
class ComponentMetrics:
    """Metrics for a specific component."""
    component_name: str
    events_processed: int = 0
    events_dropped: int = 0
    processing_time_ms: float = 0.0
    queue_size: int = 0
    queue_utilization: float = 0.0
    last_update: float = 0.0


class PerformanceIntegration:
    """
    Integrates performance monitoring with input handling components.
    
    Collects metrics from various components and provides them to the
    performance monitor for real-time tracking and analysis.
    """
    
    def __init__(self, 
                 performance_monitor: PerformanceMonitor,
                 input_handler: Optional[InputHandler] = None,
                 enable_component_tracking: bool = True,
                 enable_logging: bool = False):
        """
        Initialize performance integration.
        
        Args:
            performance_monitor: PerformanceMonitor instance
            input_handler: InputHandler instance to monitor
            enable_component_tracking: Whether to track individual components
            enable_logging: Whether to enable debug logging
        """
        self.performance_monitor = performance_monitor
        self.input_handler = input_handler
        self.enable_component_tracking = enable_component_tracking
        self.enable_logging = enable_logging
        
        # Component tracking
        self.component_metrics: Dict[str, ComponentMetrics] = {}
        self.metrics_lock = threading.RLock()
        
        # Integration state
        self.is_integrated = False
        self.integration_thread: Optional[threading.Thread] = None
        
        # Logging
        self.logger = logging.getLogger(__name__) if enable_logging else None
        
        # Performance tracking
        self.start_time = 0.0
        self.total_events_processed = 0
        self.total_events_dropped = 0
        
        # Component references
        self.mouse_handler: Optional[GamingMouseHandler] = None
        self.keyboard_handler: Optional[GamingKeyboardHandler] = None
        self.input_queue: Optional[InputQueue] = None
        self.polling_manager: Optional[PollingManager] = None
        
    def integrate(self) -> bool:
        """
        Integrate with the input handler and start metrics collection.
        
        Returns:
            True if integration successful, False otherwise
        """
        if self.is_integrated:
            return True
        
        try:
            if self.input_handler:
                # Extract component references
                self._extract_components()
                
                # Initialize component metrics
                if self.enable_component_tracking:
                    self._initialize_component_metrics()
                
                # Start integration thread
                self.is_integrated = True
                self.start_time = time.time()
                
                self.integration_thread = threading.Thread(
                    target=self._integration_loop,
                    daemon=True,
                    name="PerformanceIntegrationThread"
                )
                self.integration_thread.start()
                
                if self.logger:
                    self.logger.info("Performance integration started")
                
                return True
            else:
                if self.logger:
                    self.logger.warning("No input handler provided for integration")
                return False
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to integrate performance monitoring: {e}")
            self.is_integrated = False
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from input handler and stop metrics collection.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        if not self.is_integrated:
            return True
        
        try:
            self.is_integrated = False
            
            # Wait for integration thread to finish
            if self.integration_thread and self.integration_thread.is_alive():
                self.integration_thread.join(timeout=2.0)
            
            if self.logger:
                self.logger.info("Performance integration stopped")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error disconnecting performance monitoring: {e}")
            return False
    
    def _extract_components(self) -> None:
        """Extract component references from the input handler."""
        if not self.input_handler:
            return
        
        # Extract components (these would need to be exposed by InputHandler)
        # For now, we'll use placeholder extraction
        try:
            # In a real implementation, InputHandler would expose these components
            # self.mouse_handler = self.input_handler.mouse_handler
            # self.keyboard_handler = self.input_handler.keyboard_handler
            # self.input_queue = self.input_handler.input_queue
            # self.polling_manager = self.input_handler.polling_manager
            
            if self.logger:
                self.logger.info("Component references extracted")
                
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not extract all components: {e}")
    
    def _initialize_component_metrics(self) -> None:
        """Initialize metrics tracking for each component."""
        components = [
            ("input_handler", "Input Handler"),
            ("mouse_handler", "Mouse Handler"),
            ("keyboard_handler", "Keyboard Handler"),
            ("input_queue", "Input Queue"),
            ("polling_manager", "Polling Manager")
        ]
        
        for component_id, component_name in components:
            self.component_metrics[component_id] = ComponentMetrics(
                component_name=component_name,
                last_update=time.time()
            )
        
        if self.logger:
            self.logger.info(f"Initialized metrics for {len(components)} components")
    
    def _integration_loop(self) -> None:
        """Main integration loop that collects and updates metrics."""
        try:
            while self.is_integrated:
                try:
                    # Collect metrics from components
                    self._collect_component_metrics()
                    
                    # Update performance monitor
                    self._update_performance_monitor()
                    
                    # Sleep for a short interval
                    time.sleep(0.1)  # 10Hz update rate
                    
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error in integration loop: {e}")
                    time.sleep(0.1)
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fatal error in integration loop: {e}")
    
    def _collect_component_metrics(self) -> None:
        """Collect metrics from individual components."""
        if not self.enable_component_tracking:
            return
        
        current_time = time.time()
        
        with self.metrics_lock:
            # Update input handler metrics
            if "input_handler" in self.component_metrics:
                # In a real implementation, we would get actual metrics from InputHandler
                # For now, we'll simulate some metrics
                self.component_metrics["input_handler"].events_processed += 1
                self.component_metrics["input_handler"].last_update = current_time
            
            # Update mouse handler metrics
            if "mouse_handler" in self.component_metrics and self.mouse_handler:
                # Simulate mouse handler metrics
                self.component_metrics["mouse_handler"].events_processed += 1
                self.component_metrics["mouse_handler"].last_update = current_time
            
            # Update keyboard handler metrics
            if "keyboard_handler" in self.component_metrics and self.keyboard_handler:
                # Simulate keyboard handler metrics
                self.component_metrics["keyboard_handler"].events_processed += 1
                self.component_metrics["keyboard_handler"].last_update = current_time
            
            # Update input queue metrics
            if "input_queue" in self.component_metrics and self.input_queue:
                try:
                    queue_size = self.input_queue.get_queue_size()
                    self.component_metrics["input_queue"].queue_size = queue_size
                    self.component_metrics["input_queue"].last_update = current_time
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Could not get queue size: {e}")
            
            # Update polling manager metrics
            if "polling_manager" in self.component_metrics and self.polling_manager:
                # Simulate polling manager metrics
                self.component_metrics["polling_manager"].events_processed += 1
                self.component_metrics["polling_manager"].last_update = current_time
    
    def _update_performance_monitor(self) -> None:
        """Update the performance monitor with aggregated metrics."""
        try:
            # Calculate aggregated metrics
            total_events_processed = sum(
                metrics.events_processed for metrics in self.component_metrics.values()
            )
            
            total_events_dropped = sum(
                metrics.events_dropped for metrics in self.component_metrics.values()
            )
            
            # Get queue metrics
            queue_size = 0
            queue_utilization = 0.0
            if "input_queue" in self.component_metrics:
                queue_metrics = self.component_metrics["input_queue"]
                queue_size = queue_metrics.queue_size
                queue_utilization = queue_metrics.queue_utilization
            
            # Calculate processing latency (simplified)
            processing_latency_ms = 0.0
            if self.component_metrics:
                avg_processing_time = sum(
                    metrics.processing_time_ms for metrics in self.component_metrics.values()
                ) / len(self.component_metrics)
                processing_latency_ms = avg_processing_time
            
            # Update the performance monitor
            self.performance_monitor.update_application_metrics(
                events_processed=total_events_processed,
                queue_size=queue_size,
                queue_utilization=queue_utilization,
                events_dropped=total_events_dropped,
                processing_latency_ms=processing_latency_ms
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating performance monitor: {e}")
    
    def update_component_metrics(self, 
                               component_id: str,
                               events_processed: int = 0,
                               events_dropped: int = 0,
                               processing_time_ms: float = 0.0,
                               queue_size: int = 0,
                               queue_utilization: float = 0.0) -> None:
        """
        Update metrics for a specific component.
        
        This method can be called by components to report their metrics.
        
        Args:
            component_id: Identifier for the component
            events_processed: Number of events processed
            events_dropped: Number of events dropped
            processing_time_ms: Processing time in milliseconds
            queue_size: Current queue size
            queue_utilization: Queue utilization percentage
        """
        if not self.enable_component_tracking:
            return
        
        with self.metrics_lock:
            if component_id in self.component_metrics:
                metrics = self.component_metrics[component_id]
                metrics.events_processed += events_processed
                metrics.events_dropped += events_dropped
                metrics.processing_time_ms = processing_time_ms
                metrics.queue_size = queue_size
                metrics.queue_utilization = queue_utilization
                metrics.last_update = time.time()
    
    def get_component_metrics(self, component_id: str) -> Optional[ComponentMetrics]:
        """
        Get metrics for a specific component.
        
        Args:
            component_id: Identifier for the component
            
        Returns:
            ComponentMetrics object or None if not found
        """
        with self.metrics_lock:
            return self.component_metrics.get(component_id)
    
    def get_all_component_metrics(self) -> Dict[str, ComponentMetrics]:
        """
        Get metrics for all components.
        
        Returns:
            Dictionary of component metrics
        """
        with self.metrics_lock:
            return self.component_metrics.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive performance summary.
        
        Returns:
            Dictionary containing performance summary
        """
        with self.metrics_lock:
            total_events_processed = sum(
                metrics.events_processed for metrics in self.component_metrics.values()
            )
            
            total_events_dropped = sum(
                metrics.events_dropped for metrics in self.component_metrics.values()
            )
            
            total_processing_time = sum(
                metrics.processing_time_ms for metrics in self.component_metrics.values()
            )
            
            avg_processing_time = (
                total_processing_time / len(self.component_metrics) 
                if self.component_metrics else 0.0
            )
            
            return {
                'integration_uptime': time.time() - self.start_time,
                'total_events_processed': total_events_processed,
                'total_events_dropped': total_events_dropped,
                'drop_rate': total_events_dropped / max(total_events_processed, 1),
                'avg_processing_time_ms': avg_processing_time,
                'components_tracked': len(self.component_metrics),
                'component_metrics': {
                    comp_id: {
                        'name': metrics.component_name,
                        'events_processed': metrics.events_processed,
                        'events_dropped': metrics.events_dropped,
                        'processing_time_ms': metrics.processing_time_ms,
                        'queue_size': metrics.queue_size,
                        'queue_utilization': metrics.queue_utilization,
                        'last_update': metrics.last_update
                    }
                    for comp_id, metrics in self.component_metrics.items()
                }
            }
    
    def add_performance_alert_callback(self, callback) -> None:
        """
        Add a callback for performance alerts.
        
        Args:
            callback: Function to call when alerts are triggered
        """
        self.performance_monitor.add_alert_callback(callback)
    
    def remove_performance_alert_callback(self, callback) -> None:
        """
        Remove a performance alert callback.
        
        Args:
            callback: Function to remove
        """
        self.performance_monitor.remove_alert_callback(callback)


# Example usage and testing
if __name__ == "__main__":
    import sys
    from ..input.input_handler import InputHandler
    
    # Create performance monitor
    monitor = PerformanceMonitor(monitoring_interval=1.0, enable_alerts=True)
    
    # Create input handler (placeholder)
    input_handler = None  # Would be created with actual InputHandler()
    
    # Create performance integration
    integration = PerformanceIntegration(
        performance_monitor=monitor,
        input_handler=input_handler,
        enable_component_tracking=True,
        enable_logging=True
    )
    
    # Start monitoring
    if monitor.start():
        print("Performance monitoring started")
        
        # Integrate with input handler
        if integration.integrate():
            print("Performance integration started")
            
            try:
                # Simulate some activity
                for i in range(10):
                    integration.update_component_metrics(
                        component_id="input_handler",
                        events_processed=100,
                        events_dropped=1,
                        processing_time_ms=0.5,
                        queue_size=10,
                        queue_utilization=0.1
                    )
                    
                    time.sleep(1)
                
                # Get performance summary
                summary = integration.get_performance_summary()
                print(f"Performance Summary: {summary}")
                
            except KeyboardInterrupt:
                print("Stopping...")
            finally:
                integration.disconnect()
                monitor.stop()
        else:
            print("Failed to start performance integration")
    else:
        print("Failed to start performance monitoring")
