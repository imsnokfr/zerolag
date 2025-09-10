"""
Performance Analysis Module for ZeroLag

This module provides comprehensive performance analysis capabilities including:
- Performance benchmarking and scoring
- Optimization recommendations
- Bottleneck analysis
- Stability assessment
- Performance reporting

Main Components:
- PerformanceAnalyzer: Core analysis system
- PerformanceAnalysis: Analysis results data structure
- OptimizationRecommendation: Optimization recommendations
"""

from .performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceAnalysis,
    OptimizationRecommendation
)

__all__ = [
    'PerformanceAnalyzer',
    'PerformanceAnalysis',
    'OptimizationRecommendation'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Performance analysis and optimization for ZeroLag gaming input optimization"
