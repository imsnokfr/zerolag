"""
Aim Accuracy Test for ZeroLag Benchmark Tool.

This module implements the aim accuracy test with visual targets,
real-time tracking, and performance measurement.
"""

import time
import math
import random
from dataclasses import dataclass
from typing import List, Tuple, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor
from PyQt5.QtWidgets import QWidget

from .metrics import TestType, TestMetrics, ScoreCalculator


@dataclass
class Target:
    """Represents a target in the aim test."""
    x: float
    y: float
    size: float
    created_time: float
    hit_time: Optional[float] = None
    hit: bool = False
    hit_distance: float = 0.0


class AimAccuracyTest(QObject):
    """Aim accuracy test implementation."""
    
    # Signals
    target_created = pyqtSignal(float, float, float)  # x, y, size
    target_hit = pyqtSignal(float, float, float)  # x, y, hit_distance
    test_started = pyqtSignal()
    test_finished = pyqtSignal(object)  # TestMetrics
    score_updated = pyqtSignal(float)  # current_score
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        self.test_active = False
        self.start_time = 0.0
        self.end_time = 0.0
        self.targets: List[Target] = []
        self.current_target_index = 0
        self.hits = 0
        self.misses = 0
        self.total_reaction_time = 0.0
        self.total_distance = 0.0
        
        # Test parameters
        self.test_duration = self.config.get('test_duration', 30.0)
        self.target_size = self.config.get('target_size', 50.0)
        self.target_count = self.config.get('target_count', 10)
        self.difficulty_multiplier = self.config.get('difficulty_multiplier', 1.0)
        
        # Timer for target generation
        self.target_timer = QTimer()
        self.target_timer.timeout.connect(self._create_new_target)
        
        # Timer for test duration
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self._finish_test)
        self.test_timer.setSingleShot(True)
    
    def start_test(self, width: int, height: int):
        """Start the aim accuracy test."""
        if self.test_active:
            return
        
        self.test_active = True
        self.start_time = time.time()
        self.end_time = 0.0
        self.targets.clear()
        self.current_target_index = 0
        self.hits = 0
        self.misses = 0
        self.total_reaction_time = 0.0
        self.total_distance = 0.0
        
        # Store dimensions for target generation
        self.test_width = width
        self.test_height = height
        
        # Start target generation
        self._create_new_target()
        
        # Set up test duration timer
        self.test_timer.start(int(self.test_duration * 1000))
        
        self.test_started.emit()
    
    def stop_test(self):
        """Stop the aim accuracy test."""
        if not self.test_active:
            return
        
        self.test_active = False
        self.end_time = time.time()
        self.target_timer.stop()
        self.test_timer.stop()
        
        # Calculate final metrics
        metrics = self._calculate_metrics()
        self.test_finished.emit(metrics)
    
    def handle_click(self, x: float, y: float) -> bool:
        """Handle mouse click during test. Returns True if target was hit."""
        if not self.test_active or not self.targets:
            return False
        
        # Check if click hit any active target
        for target in self.targets:
            if target.hit:
                continue
            
            distance = math.sqrt((x - target.x) ** 2 + (y - target.y) ** 2)
            if distance <= target.size / 2:
                # Target hit!
                target.hit = True
                target.hit_time = time.time()
                target.hit_distance = distance
                
                self.hits += 1
                self.total_reaction_time += target.hit_time - target.created_time
                self.total_distance += distance
                
                self.target_hit.emit(target.x, target.y, distance)
                
                # Update score
                current_score = self._calculate_current_score()
                self.score_updated.emit(current_score)
                
                return True
        
        # Miss
        self.misses += 1
        return False
    
    def _create_new_target(self):
        """Create a new target at a random position."""
        if not self.test_active:
            return
        
        # Calculate target size based on difficulty
        size = self.target_size / self.difficulty_multiplier
        
        # Generate random position (with margin from edges)
        margin = size
        x = random.uniform(margin, self.test_width - margin)
        y = random.uniform(margin, self.test_height - margin)
        
        # Create target
        target = Target(
            x=x,
            y=y,
            size=size,
            created_time=time.time()
        )
        
        self.targets.append(target)
        self.target_created.emit(x, y, size)
        
        # Set timer for next target (faster for higher difficulty)
        next_delay = max(500, int(2000 / self.difficulty_multiplier))
        self.target_timer.start(next_delay)
    
    def _finish_test(self):
        """Finish the test when duration is reached."""
        self.stop_test()
    
    def _calculate_current_score(self) -> float:
        """Calculate current score during test."""
        if not self.targets:
            return 0.0
        
        total_attempts = self.hits + self.misses
        if total_attempts == 0:
            return 0.0
        
        accuracy = self.hits / total_attempts
        avg_reaction_time = self.total_reaction_time / max(1, self.hits)
        avg_distance = self.total_distance / max(1, self.hits)
        
        # Convert distance to speed (inverse relationship)
        speed = max(0, 1.0 - (avg_distance / (self.target_size / 2)))
        
        return ScoreCalculator.calculate_aim_score(accuracy, speed, avg_reaction_time)
    
    def _calculate_metrics(self) -> TestMetrics:
        """Calculate final test metrics."""
        duration = self.end_time - self.start_time
        total_attempts = self.hits + self.misses
        
        accuracy = self.hits / total_attempts if total_attempts > 0 else 0.0
        avg_reaction_time = self.total_reaction_time / max(1, self.hits)
        avg_distance = self.total_distance / max(1, self.hits)
        speed = max(0, 1.0 - (avg_distance / (self.target_size / 2)))
        
        score = ScoreCalculator.calculate_aim_score(accuracy, speed, avg_reaction_time)
        
        # Collect raw data
        raw_data = []
        for target in self.targets:
            raw_data.append({
                'x': target.x,
                'y': target.y,
                'size': target.size,
                'created_time': target.created_time,
                'hit_time': target.hit_time,
                'hit': target.hit,
                'hit_distance': target.hit_distance
            })
        
        return TestMetrics(
            test_type=TestType.AIM_ACCURACY,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=duration,
            score=score,
            accuracy=accuracy,
            speed=speed,
            reaction_time=avg_reaction_time,
            errors=self.misses,
            total_attempts=total_attempts,
            success_rate=accuracy,
            raw_data=raw_data
        )
    
    def get_active_targets(self) -> List[Target]:
        """Get list of currently active (unhit) targets."""
        return [target for target in self.targets if not target.hit]
    
    def get_test_progress(self) -> dict:
        """Get current test progress information."""
        if not self.test_active:
            return {}
        
        elapsed = time.time() - self.start_time
        remaining = max(0, self.test_duration - elapsed)
        
        return {
            'elapsed_time': elapsed,
            'remaining_time': remaining,
            'progress_percent': (elapsed / self.test_duration) * 100,
            'hits': self.hits,
            'misses': self.misses,
            'total_targets': len(self.targets),
            'current_score': self._calculate_current_score()
        }
