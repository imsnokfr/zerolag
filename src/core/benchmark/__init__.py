"""
Benchmark Tool Module for ZeroLag

This module provides comprehensive benchmarking functionality for testing
aim accuracy, key press speed, and reaction times with visual feedback.

Features:
- Aim accuracy testing with visual targets
- Key press speed measurement
- Reaction time testing
- Real-time metrics and scoring
- Performance comparison and history
- Visual feedback and animations
"""

from .benchmark_manager import BenchmarkManager
from .aim_test import AimAccuracyTest
from .key_speed_test import KeySpeedTest
from .reaction_test import ReactionTimeTest
from .metrics import BenchmarkMetrics, TestResult, TestMetrics, BenchmarkConfig, TestType, DifficultyLevel, ScoreCalculator
from .visual_feedback import VisualFeedbackManager

__all__ = [
    'BenchmarkManager',
    'AimAccuracyTest',
    'KeySpeedTest', 
    'ReactionTimeTest',
    'BenchmarkMetrics',
    'TestResult',
    'TestMetrics',
    'BenchmarkConfig',
    'TestType',
    'DifficultyLevel',
    'ScoreCalculator',
    'VisualFeedbackManager'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Comprehensive benchmarking tool for gaming input optimization"
