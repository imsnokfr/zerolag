"""
Real-Time Performance Monitoring System for ZeroLag

This module provides comprehensive performance monitoring capabilities
to track CPU usage, memory consumption, event processing rates, and
other key performance metrics in real-time.

Features:
- Real-time CPU and memory monitoring
- Event processing rate tracking
- Performance trend analysis
- Alert system for performance issues
- Historical performance data
- Export capabilities for analysis
"""

import time
import threading
import psutil
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
import statistics


@dataclass
class PerformanceSnapshot:
    """A snapshot of performance metrics at a specific time."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    events_processed: int
    events_per_second: float
    queue_size: int
    queue_utilization: float
    events_dropped: int
    drop_rate: float
    processing_latency_ms: float
    thread_count: int
    uptime_seconds: float


@dataclass
class PerformanceAlert:
    """A performance alert with severity and details."""
    timestamp: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    metric: str
    value: float
    threshold: float
    message: str


class PerformanceMonitor:
    """
    Real-time performance monitoring system.
    
    Tracks and analyzes performance metrics, provides alerts,
    and maintains historical data for trend analysis.
    """
    
    def __init__(self, 
                 monitoring_interval: float = 1.0,
                 history_size: int = 3600,  # 1 hour of data at 1-second intervals
                 enable_alerts: bool = True,
                 enable_logging: bool = False):
        """
        Initialize the performance monitor.
        
        Args:
            monitoring_interval: How often to collect metrics (seconds)
            history_size: Number of snapshots to keep in memory
            enable_alerts: Whether to enable performance alerts
            enable_logging: Whether to enable debug logging
        """
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size
        self.enable_alerts = enable_alerts
        self.enable_logging = enable_logging
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.start_time = 0.0
        
        # Data storage
        self.performance_history: deque = deque(maxlen=history_size)
        self.alerts: List[PerformanceAlert] = []
        self.current_snapshot: Optional[PerformanceSnapshot] = None
        
        # Process information
        self.process = psutil.Process()
        self.baseline_cpu = 0.0
        self.baseline_memory = 0.0
        
        # Performance targets and thresholds
        self.targets = {
            'cpu_percent': 1.0,      # Target: <1% CPU
            'memory_mb': 50.0,       # Target: <50MB
            'events_per_second': 1000,  # Target: >1000 events/sec
            'drop_rate': 0.01,       # Target: <1% drop rate
            'processing_latency_ms': 5.0  # Target: <5ms latency
        }
        
        self.thresholds = {
            'cpu_percent': {'warning': 2.0, 'critical': 5.0},
            'memory_mb': {'warning': 75.0, 'critical': 100.0},
            'events_per_second': {'warning': 500, 'critical': 100},
            'drop_rate': {'warning': 0.05, 'critical': 0.1},
            'processing_latency_ms': {'warning': 10.0, 'critical': 20.0}
        }
        
        # Callbacks
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # Logging
        self.logger = logging.getLogger(__name__) if enable_logging else None
        
        # Threading
        self._lock = threading.RLock()
        
    def start(self) -> bool:
        """
        Start performance monitoring.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_monitoring:
            return True
        
        try:
            with self._lock:
                self.is_monitoring = True
                self.start_time = time.time()
                
                # Establish baseline metrics
                self._establish_baseline()
                
                # Start monitoring thread
                self.monitoring_thread = threading.Thread(
                    target=self._monitoring_loop,
                    daemon=True,
                    name="PerformanceMonitorThread"
                )
                self.monitoring_thread.start()
                
                if self.logger:
                    self.logger.info("Performance monitoring started")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start performance monitoring: {e}")
            self.is_monitoring = False
            return False
    
    def stop(self) -> bool:
        """
        Stop performance monitoring.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_monitoring:
            return True
        
        try:
            with self._lock:
                self.is_monitoring = False
                
                # Wait for monitoring thread to finish
                if self.monitoring_thread and self.monitoring_thread.is_alive():
                    self.monitoring_thread.join(timeout=2.0)
                
                if self.logger:
                    self.logger.info("Performance monitoring stopped")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error stopping performance monitoring: {e}")
            return False
    
    def _establish_baseline(self) -> None:
        """Establish baseline performance metrics."""
        # Let the system stabilize
        time.sleep(0.5)
        
        # Take multiple samples for a stable baseline
        cpu_samples = []
        memory_samples = []
        
        for _ in range(5):
            cpu_samples.append(self.process.cpu_percent())
            memory_samples.append(self.process.memory_info().rss / 1024 / 1024)
            time.sleep(0.1)
        
        self.baseline_cpu = statistics.mean(cpu_samples)
        self.baseline_memory = statistics.mean(memory_samples)
        
        if self.logger:
            self.logger.info(f"Baseline established: CPU {self.baseline_cpu:.2f}%, Memory {self.baseline_memory:.2f}MB")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop that collects performance metrics."""
        try:
            while self.is_monitoring:
                try:
                    # Collect current metrics
                    snapshot = self._collect_metrics()
                    
                    # Store the snapshot
                    with self._lock:
                        self.performance_history.append(snapshot)
                        self.current_snapshot = snapshot
                    
                    # Check for alerts
                    if self.enable_alerts:
                        self._check_alerts(snapshot)
                    
                    # Sleep until next monitoring interval
                    time.sleep(self.monitoring_interval)
                    
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(self.monitoring_interval)
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fatal error in monitoring loop: {e}")
    
    def _collect_metrics(self) -> PerformanceSnapshot:
        """Collect current performance metrics."""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # System metrics
        cpu_percent = self.process.cpu_percent()
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = self.process.memory_percent()
        thread_count = self.process.num_threads()
        
        # Application-specific metrics (these would be provided by the input handler)
        # For now, we'll use placeholder values
        events_processed = 0
        events_per_second = 0.0
        queue_size = 0
        queue_utilization = 0.0
        events_dropped = 0
        drop_rate = 0.0
        processing_latency_ms = 0.0
        
        # Calculate events per second from recent history
        if len(self.performance_history) > 1:
            recent_snapshots = list(self.performance_history)[-10:]  # Last 10 snapshots
            if len(recent_snapshots) > 1:
                time_diff = recent_snapshots[-1].timestamp - recent_snapshots[0].timestamp
                events_diff = recent_snapshots[-1].events_processed - recent_snapshots[0].events_processed
                if time_diff > 0:
                    events_per_second = events_diff / time_diff
        
        return PerformanceSnapshot(
            timestamp=current_time,
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            events_processed=events_processed,
            events_per_second=events_per_second,
            queue_size=queue_size,
            queue_utilization=queue_utilization,
            events_dropped=events_dropped,
            drop_rate=drop_rate,
            processing_latency_ms=processing_latency_ms,
            thread_count=thread_count,
            uptime_seconds=uptime
        )
    
    def _check_alerts(self, snapshot: PerformanceSnapshot) -> None:
        """Check for performance alerts and trigger callbacks."""
        alerts_triggered = []
        
        # Check each metric against thresholds
        for metric, thresholds in self.thresholds.items():
            value = getattr(snapshot, metric)
            
            # Determine severity
            severity = None
            if value >= thresholds['critical']:
                severity = 'critical'
            elif value >= thresholds['warning']:
                severity = 'warning'
            
            if severity:
                alert = PerformanceAlert(
                    timestamp=snapshot.timestamp,
                    severity=severity,
                    metric=metric,
                    value=value,
                    threshold=thresholds[severity],
                    message=f"{metric} is {value:.2f}, exceeding {severity} threshold of {thresholds[severity]:.2f}"
                )
                alerts_triggered.append(alert)
        
        # Store alerts and trigger callbacks
        for alert in alerts_triggered:
            self.alerts.append(alert)
            
            # Trigger callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error in alert callback: {e}")
    
    def update_application_metrics(self, 
                                 events_processed: int = 0,
                                 queue_size: int = 0,
                                 queue_utilization: float = 0.0,
                                 events_dropped: int = 0,
                                 processing_latency_ms: float = 0.0) -> None:
        """
        Update application-specific metrics.
        
        This method should be called by the input handler to provide
        real-time application metrics.
        
        Args:
            events_processed: Total events processed
            queue_size: Current queue size
            queue_utilization: Queue utilization percentage
            events_dropped: Total events dropped
            processing_latency_ms: Average processing latency
        """
        if self.current_snapshot:
            # Update the current snapshot with application metrics
            self.current_snapshot.events_processed = events_processed
            self.current_snapshot.queue_size = queue_size
            self.current_snapshot.queue_utilization = queue_utilization
            self.current_snapshot.events_dropped = events_dropped
            self.current_snapshot.processing_latency_ms = processing_latency_ms
            
            # Recalculate events per second
            if len(self.performance_history) > 1:
                recent_snapshots = list(self.performance_history)[-10:]
                if len(recent_snapshots) > 1:
                    time_diff = recent_snapshots[-1].timestamp - recent_snapshots[0].timestamp
                    events_diff = recent_snapshots[-1].events_processed - recent_snapshots[0].events_processed
                    if time_diff > 0:
                        self.current_snapshot.events_per_second = events_diff / time_diff
    
    def get_current_metrics(self) -> Optional[PerformanceSnapshot]:
        """
        Get the current performance metrics.
        
        Returns:
            Current performance snapshot or None if not monitoring
        """
        with self._lock:
            return self.current_snapshot
    
    def get_performance_summary(self, duration_minutes: int = 5) -> Dict[str, Any]:
        """
        Get a performance summary for the specified duration.
        
        Args:
            duration_minutes: Duration to analyze in minutes
            
        Returns:
            Dictionary containing performance summary
        """
        with self._lock:
            if not self.performance_history:
                return {}
            
            # Get recent snapshots
            cutoff_time = time.time() - (duration_minutes * 60)
            recent_snapshots = [s for s in self.performance_history if s.timestamp >= cutoff_time]
            
            if not recent_snapshots:
                return {}
            
            # Calculate statistics
            cpu_values = [s.cpu_percent for s in recent_snapshots]
            memory_values = [s.memory_mb for s in recent_snapshots]
            events_per_second_values = [s.events_per_second for s in recent_snapshots]
            
            return {
                'duration_minutes': duration_minutes,
                'snapshots_analyzed': len(recent_snapshots),
                'cpu_percent': {
                    'current': recent_snapshots[-1].cpu_percent,
                    'average': statistics.mean(cpu_values),
                    'min': min(cpu_values),
                    'max': max(cpu_values),
                    'target': self.targets['cpu_percent']
                },
                'memory_mb': {
                    'current': recent_snapshots[-1].memory_mb,
                    'average': statistics.mean(memory_values),
                    'min': min(memory_values),
                    'max': max(memory_values),
                    'target': self.targets['memory_mb']
                },
                'events_per_second': {
                    'current': recent_snapshots[-1].events_per_second,
                    'average': statistics.mean(events_per_second_values),
                    'min': min(events_per_second_values),
                    'max': max(events_per_second_values),
                    'target': self.targets['events_per_second']
                },
                'targets_met': {
                    'cpu': recent_snapshots[-1].cpu_percent < self.targets['cpu_percent'],
                    'memory': recent_snapshots[-1].memory_mb < self.targets['memory_mb'],
                    'events': recent_snapshots[-1].events_per_second > self.targets['events_per_second']
                }
            }
    
    def get_recent_alerts(self, count: int = 10) -> List[PerformanceAlert]:
        """
        Get recent performance alerts.
        
        Args:
            count: Number of recent alerts to return
            
        Returns:
            List of recent alerts
        """
        with self._lock:
            return self.alerts[-count:] if self.alerts else []
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """
        Add a callback function to be called when alerts are triggered.
        
        Args:
            callback: Function to call with PerformanceAlert object
        """
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """
        Remove an alert callback function.
        
        Args:
            callback: Function to remove
        """
        try:
            self.alert_callbacks.remove(callback)
        except ValueError:
            pass
    
    def export_data(self, filepath: str, format: str = 'json') -> bool:
        """
        Export performance data to a file.
        
        Args:
            filepath: Path to export file
            format: Export format ('json' or 'csv')
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            with self._lock:
                if format.lower() == 'json':
                    data = {
                        'export_timestamp': time.time(),
                        'monitoring_interval': self.monitoring_interval,
                        'targets': self.targets,
                        'thresholds': self.thresholds,
                        'performance_history': [asdict(snapshot) for snapshot in self.performance_history],
                        'alerts': [asdict(alert) for alert in self.alerts]
                    }
                    
                    with open(filepath, 'w') as f:
                        json.dump(data, f, indent=2)
                
                elif format.lower() == 'csv':
                    import csv
                    
                    with open(filepath, 'w', newline='') as f:
                        if self.performance_history:
                            writer = csv.DictWriter(f, fieldnames=asdict(self.performance_history[0]).keys())
                            writer.writeheader()
                            for snapshot in self.performance_history:
                                writer.writerow(asdict(snapshot))
                
                else:
                    raise ValueError(f"Unsupported format: {format}")
                
                if self.logger:
                    self.logger.info(f"Performance data exported to {filepath}")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to export performance data: {e}")
            return False
    
    def clear_history(self) -> None:
        """Clear performance history and alerts."""
        with self._lock:
            self.performance_history.clear()
            self.alerts.clear()
            
            if self.logger:
                self.logger.info("Performance history cleared")


# Example usage and testing
if __name__ == "__main__":
    def alert_callback(alert: PerformanceAlert):
        print(f"ALERT [{alert.severity.upper()}]: {alert.message}")
    
    # Create performance monitor
    monitor = PerformanceMonitor(
        monitoring_interval=1.0,
        enable_alerts=True,
        enable_logging=True
    )
    
    # Add alert callback
    monitor.add_alert_callback(alert_callback)
    
    # Start monitoring
    if monitor.start():
        print("Performance monitoring started")
        
        try:
            # Simulate some activity
            for i in range(10):
                monitor.update_application_metrics(
                    events_processed=i * 100,
                    queue_size=i * 10,
                    queue_utilization=i * 0.1,
                    events_dropped=i,
                    processing_latency_ms=i * 0.5
                )
                
                time.sleep(1)
            
            # Get performance summary
            summary = monitor.get_performance_summary(duration_minutes=1)
            print(f"Performance Summary: {summary}")
            
            # Export data
            monitor.export_data("performance_data.json", "json")
            print("Performance data exported")
            
        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            monitor.stop()
    else:
        print("Failed to start performance monitoring")
