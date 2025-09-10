"""
Performance Monitoring Module for ZeroLag

This module provides comprehensive performance monitoring capabilities including:
- Real-time performance metrics collection
- Performance dashboard with GUI
- Integration with input handling components
- Performance alerts and notifications
- Historical data tracking and export

Main Components:
- PerformanceMonitor: Core monitoring system
- PerformanceDashboard: GUI dashboard for real-time monitoring
- PerformanceIntegration: Integration with input handling components
"""

from .performance_monitor import (
    PerformanceMonitor,
    PerformanceMetrics,
    PerformanceAlert
)

from .crash_reporter import CrashReporter

__all__ = [
    'PerformanceMonitor',
    'PerformanceMetrics', 
    'PerformanceAlert',
    'CrashReporter'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Real-time performance monitoring for ZeroLag gaming input optimization"
