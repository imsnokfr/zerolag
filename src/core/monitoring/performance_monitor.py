"""
Performance monitoring system for ZeroLag.

This module provides comprehensive performance monitoring capabilities
including system metrics, input lag measurement, and performance alerts.
"""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import logging


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    input_lag_ms: float
    polling_rate_hz: float
    frame_rate_fps: float
    gpu_usage_percent: Optional[float] = None
    disk_io_read_mb: float = 0.0
    disk_io_write_mb: float = 0.0
    network_io_sent_mb: float = 0.0
    network_io_recv_mb: float = 0.0


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    timestamp: float
    metrics: Dict[str, Any]
    threshold: float
    current_value: float


class PerformanceMonitor:
    """Comprehensive performance monitoring system."""
    
    def __init__(self, monitoring_interval: float = 1.0, history_size: int = 300):
        """
        Initialize performance monitor.
        
        Args:
            monitoring_interval: Time between monitoring checks in seconds
            history_size: Number of historical metrics to keep
        """
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_history = deque(maxlen=history_size)
        self.alerts = []
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'input_lag_ms': 16.0,
            'frame_rate_fps': 30.0,
            'gpu_usage_percent': 90.0
        }
        
        # Alert severity levels
        self.severity_levels = {
            'low': 0.7,      # 70% of threshold
            'medium': 0.85,  # 85% of threshold
            'high': 0.95,    # 95% of threshold
            'critical': 1.0  # 100% of threshold
        }
        
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Start performance monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        self.logger.info("Performance monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                self._check_thresholds(metrics)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
            
            time.sleep(self.monitoring_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        timestamp = time.time()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used_mb = memory.used / (1024 * 1024)
        memory_available_mb = memory.available / (1024 * 1024)
        
        # Input lag (simulated - would need actual measurement)
        input_lag_ms = self._measure_input_lag()
        
        # Polling rate (simulated - would need actual measurement)
        polling_rate_hz = self._measure_polling_rate()
        
        # Frame rate (simulated - would need actual measurement)
        frame_rate_fps = self._measure_frame_rate()
        
        # GPU usage (if available)
        gpu_usage_percent = self._get_gpu_usage()
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_io_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0.0
        disk_io_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0.0
        
        # Network I/O
        network_io = psutil.net_io_counters()
        network_io_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0.0
        network_io_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0.0
        
        return PerformanceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used_mb=memory_used_mb,
            memory_available_mb=memory_available_mb,
            input_lag_ms=input_lag_ms,
            polling_rate_hz=polling_rate_hz,
            frame_rate_fps=frame_rate_fps,
            gpu_usage_percent=gpu_usage_percent,
            disk_io_read_mb=disk_io_read_mb,
            disk_io_write_mb=disk_io_write_mb,
            network_io_sent_mb=network_io_sent_mb,
            network_io_recv_mb=network_io_recv_mb
        )
    
    def _measure_input_lag(self) -> float:
        """Measure input lag (simulated)."""
        # In a real implementation, this would measure actual input lag
        # For now, return a simulated value based on system performance
        cpu_percent = psutil.cpu_percent(interval=0.01)
        base_lag = 8.0  # Base input lag in ms
        cpu_factor = cpu_percent / 100.0 * 5.0  # Additional lag based on CPU usage
        return base_lag + cpu_factor
    
    def _measure_polling_rate(self) -> float:
        """Measure polling rate (simulated)."""
        # In a real implementation, this would measure actual polling rate
        # For now, return a simulated value
        return 1000.0  # 1000Hz polling rate
    
    def _measure_frame_rate(self) -> float:
        """Measure frame rate (simulated)."""
        # In a real implementation, this would measure actual frame rate
        # For now, return a simulated value based on system performance
        cpu_percent = psutil.cpu_percent(interval=0.01)
        base_fps = 60.0
        cpu_factor = (100.0 - cpu_percent) / 100.0
        return base_fps * cpu_factor
    
    def _get_gpu_usage(self) -> Optional[float]:
        """Get GPU usage percentage (if available)."""
        try:
            # Try to get GPU usage using nvidia-ml-py or similar
            # For now, return None (not available)
            return None
        except ImportError:
            return None
    
    def _check_thresholds(self, metrics: PerformanceMetrics):
        """Check performance thresholds and generate alerts."""
        for metric_name, threshold in self.thresholds.items():
            current_value = getattr(metrics, metric_name)
            if current_value is None:
                continue
            
            # Check if threshold is exceeded
            if current_value >= threshold:
                # Determine severity
                severity = self._determine_severity(current_value, threshold)
                
                # Create alert
                alert = PerformanceAlert(
                    alert_type=metric_name,
                    severity=severity,
                    message=f"{metric_name} is {current_value:.1f}% (threshold: {threshold:.1f}%)",
                    timestamp=metrics.timestamp,
                    metrics=metrics.__dict__,
                    threshold=threshold,
                    current_value=current_value
                )
                
                self.alerts.append(alert)
                self._notify_alert_callbacks(alert)
                
                self.logger.warning(f"Performance alert: {alert.message}")
    
    def _determine_severity(self, current_value: float, threshold: float) -> str:
        """Determine alert severity based on how much threshold is exceeded."""
        ratio = current_value / threshold
        
        if ratio >= self.severity_levels['critical']:
            return 'critical'
        elif ratio >= self.severity_levels['high']:
            return 'high'
        elif ratio >= self.severity_levels['medium']:
            return 'medium'
        else:
            return 'low'
    
    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Add alert callback function."""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Remove alert callback function."""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def _notify_alert_callbacks(self, alert: PerformanceAlert):
        """Notify all alert callbacks."""
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics."""
        if not self.metrics_history:
            return None
        return self.metrics_history[-1]
    
    def get_metrics_history(self, duration_seconds: Optional[float] = None) -> List[PerformanceMetrics]:
        """Get performance metrics history."""
        if not self.metrics_history:
            return []
        
        if duration_seconds is None:
            return list(self.metrics_history)
        
        current_time = time.time()
        cutoff_time = current_time - duration_seconds
        
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_average_metrics(self, duration_seconds: Optional[float] = None) -> Optional[PerformanceMetrics]:
        """Get average performance metrics over specified duration."""
        metrics_list = self.get_metrics_history(duration_seconds)
        if not metrics_list:
            return None
        
        # Calculate averages
        avg_cpu = sum(m.cpu_percent for m in metrics_list) / len(metrics_list)
        avg_memory = sum(m.memory_percent for m in metrics_list) / len(metrics_list)
        avg_input_lag = sum(m.input_lag_ms for m in metrics_list) / len(metrics_list)
        avg_polling_rate = sum(m.polling_rate_hz for m in metrics_list) / len(metrics_list)
        avg_frame_rate = sum(m.frame_rate_fps for m in metrics_list) / len(metrics_list)
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=avg_cpu,
            memory_percent=avg_memory,
            memory_used_mb=metrics_list[-1].memory_used_mb,
            memory_available_mb=metrics_list[-1].memory_available_mb,
            input_lag_ms=avg_input_lag,
            polling_rate_hz=avg_polling_rate,
            frame_rate_fps=avg_frame_rate,
            gpu_usage_percent=metrics_list[-1].gpu_usage_percent,
            disk_io_read_mb=metrics_list[-1].disk_io_read_mb,
            disk_io_write_mb=metrics_list[-1].disk_io_write_mb,
            network_io_sent_mb=metrics_list[-1].network_io_sent_mb,
            network_io_recv_mb=metrics_list[-1].network_io_recv_mb
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics_history:
            return {"error": "No metrics available"}
        
        current = self.get_current_metrics()
        average = self.get_average_metrics()
        
        # Count alerts by severity
        alert_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for alert in self.alerts:
            alert_counts[alert.severity] += 1
        
        return {
            "current_metrics": current.__dict__ if current else None,
            "average_metrics": average.__dict__ if average else None,
            "total_metrics": len(self.metrics_history),
            "monitoring_duration": (self.metrics_history[-1].timestamp - self.metrics_history[0].timestamp) if len(self.metrics_history) > 1 else 0,
            "alert_counts": alert_counts,
            "total_alerts": len(self.alerts),
            "monitoring_active": self.monitoring
        }
    
    def set_threshold(self, metric_name: str, threshold: float):
        """Set performance threshold for a metric."""
        if metric_name in self.thresholds:
            self.thresholds[metric_name] = threshold
            self.logger.info(f"Threshold set: {metric_name} = {threshold}")
        else:
            self.logger.warning(f"Unknown metric: {metric_name}")
    
    def get_thresholds(self) -> Dict[str, float]:
        """Get current performance thresholds."""
        return self.thresholds.copy()
    
    def clear_alerts(self):
        """Clear all performance alerts."""
        self.alerts.clear()
        self.logger.info("Performance alerts cleared")
    
    def get_recent_alerts(self, count: int = 10) -> List[PerformanceAlert]:
        """Get recent performance alerts."""
        return self.alerts[-count:] if self.alerts else []