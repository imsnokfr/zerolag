"""
Smoothing Module for ZeroLag

This module provides comprehensive cursor smoothing capabilities including:
- Multiple smoothing algorithms (low-pass, EMA, Kalman, adaptive)
- Real-time smoothing configuration
- Performance optimization
- Integration with mouse handling system

Main Components:
- SmoothingEngine: Core smoothing engine with multiple algorithms
- SmoothingIntegration: Integration with mouse handling system
- SmoothingConfig: Configuration for smoothing parameters
- Various smoothing algorithms (LowPassFilter, ExponentialMovingAverage, etc.)
"""

from .smoothing_algorithms import (
    SmoothingEngine,
    SmoothingConfig,
    SmoothingType,
    SmoothingResult,
    LowPassFilter,
    ExponentialMovingAverage,
    KalmanFilter,
    GaussianSmoother,
    MedianFilter,
    AdaptiveSmoother
)

from .smoothing_integration import (
    SmoothingIntegration,
    SmoothingMetrics
)

__all__ = [
    'SmoothingEngine',
    'SmoothingConfig',
    'SmoothingType',
    'SmoothingResult',
    'LowPassFilter',
    'ExponentialMovingAverage',
    'KalmanFilter',
    'GaussianSmoother',
    'MedianFilter',
    'AdaptiveSmoother',
    'SmoothingIntegration',
    'SmoothingMetrics'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Cursor smoothing algorithms for ZeroLag gaming input optimization"
