"""
Benchmark metrics and result classes for ZeroLag.

This module defines data structures for storing and analyzing
benchmark test results and performance metrics.
"""

import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class TestType(Enum):
    """Types of benchmark tests available."""
    AIM_ACCURACY = "aim_accuracy"
    KEY_SPEED = "key_speed"
    REACTION_TIME = "reaction_time"
    COMBINED = "combined"


class DifficultyLevel(Enum):
    """Difficulty levels for benchmark tests."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class TestMetrics:
    """Individual test metrics for a single test run."""
    test_type: TestType
    start_time: float
    end_time: float
    duration: float
    score: float
    accuracy: float
    speed: float
    reaction_time: float
    errors: int
    total_attempts: int
    success_rate: float
    raw_data: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        if self.total_attempts > 0:
            self.success_rate = (self.total_attempts - self.errors) / self.total_attempts
        else:
            self.success_rate = 0.0


@dataclass
class TestResult:
    """Complete result for a benchmark test session."""
    session_id: str
    profile_name: str
    test_type: TestType
    difficulty: DifficultyLevel
    start_time: float
    end_time: float
    total_duration: float
    metrics: List[TestMetrics]
    overall_score: float
    rank: Optional[str] = None
    percentile: Optional[float] = None
    notes: str = ""
    
    def __post_init__(self):
        """Calculate overall score and duration."""
        if self.metrics:
            # Calculate weighted overall score
            total_weight = 0
            weighted_score = 0
            
            for metric in self.metrics:
                weight = self._get_metric_weight(metric.test_type)
                weighted_score += metric.score * weight
                total_weight += weight
            
            self.overall_score = weighted_score / total_weight if total_weight > 0 else 0.0
        else:
            self.overall_score = 0.0
        
        self.total_duration = self.end_time - self.start_time
    
    def _get_metric_weight(self, test_type: TestType) -> float:
        """Get weight for different test types in overall scoring."""
        weights = {
            TestType.AIM_ACCURACY: 0.4,
            TestType.KEY_SPEED: 0.3,
            TestType.REACTION_TIME: 0.3,
            TestType.COMBINED: 1.0
        }
        return weights.get(test_type, 0.5)


@dataclass
class BenchmarkMetrics:
    """Aggregated metrics for benchmark analysis."""
    total_tests: int
    average_score: float
    best_score: float
    worst_score: float
    average_accuracy: float
    average_speed: float
    average_reaction_time: float
    improvement_trend: float
    consistency_score: float
    test_history: List[TestResult] = field(default_factory=list)
    
    def add_result(self, result: TestResult):
        """Add a new test result and update metrics."""
        self.test_history.append(result)
        self._recalculate_metrics()
    
    def _recalculate_metrics(self):
        """Recalculate all aggregated metrics."""
        if not self.test_history:
            return
        
        scores = [r.overall_score for r in self.test_history]
        accuracies = []
        speeds = []
        reaction_times = []
        
        for result in self.test_history:
            for metric in result.metrics:
                accuracies.append(metric.accuracy)
                speeds.append(metric.speed)
                reaction_times.append(metric.reaction_time)
        
        self.total_tests = len(self.test_history)
        self.average_score = sum(scores) / len(scores) if scores else 0.0
        self.best_score = max(scores) if scores else 0.0
        self.worst_score = min(scores) if scores else 0.0
        self.average_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        self.average_speed = sum(speeds) / len(speeds) if speeds else 0.0
        self.average_reaction_time = sum(reaction_times) / len(reaction_times) if reaction_times else 0.0
        
        # Calculate improvement trend (simple linear regression slope)
        if len(scores) > 1:
            x_values = list(range(len(scores)))
            n = len(scores)
            sum_x = sum(x_values)
            sum_y = sum(scores)
            sum_xy = sum(x * y for x, y in zip(x_values, scores))
            sum_x2 = sum(x * x for x in x_values)
            
            self.improvement_trend = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        else:
            self.improvement_trend = 0.0
        
        # Calculate consistency (inverse of standard deviation)
        if len(scores) > 1:
            mean_score = self.average_score
            variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
            std_dev = variance ** 0.5
            self.consistency_score = max(0, 100 - std_dev)  # Higher is more consistent
        else:
            self.consistency_score = 100.0


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests."""
    test_duration: float = 30.0  # seconds
    target_size: float = 50.0  # pixels
    target_count: int = 10
    key_sequence: List[str] = field(default_factory=lambda: ["a", "s", "d", "w"])
    reaction_stimulus_delay: float = 2.0  # seconds
    max_reaction_time: float = 5.0  # seconds
    difficulty_multiplier: float = 1.0
    visual_feedback: bool = True
    sound_feedback: bool = True
    auto_save_results: bool = True


class ScoreCalculator:
    """Utility class for calculating benchmark scores."""
    
    @staticmethod
    def calculate_aim_score(accuracy: float, speed: float, reaction_time: float) -> float:
        """Calculate aim accuracy test score."""
        # Weighted combination: 60% accuracy, 30% speed, 10% reaction time
        accuracy_score = min(100, accuracy * 100)
        speed_score = min(100, speed * 100)
        reaction_score = max(0, 100 - (reaction_time * 20))  # Lower reaction time = higher score
        
        return (accuracy_score * 0.6 + speed_score * 0.3 + reaction_score * 0.1)
    
    @staticmethod
    def calculate_key_speed_score(keys_per_second: float, accuracy: float) -> float:
        """Calculate key speed test score."""
        # Weighted combination: 70% speed, 30% accuracy
        speed_score = min(100, keys_per_second * 10)  # 10 keys/sec = 100 points
        accuracy_score = min(100, accuracy * 100)
        
        return (speed_score * 0.7 + accuracy_score * 0.3)
    
    @staticmethod
    def calculate_reaction_score(reaction_time: float, consistency: float) -> float:
        """Calculate reaction time test score."""
        # Lower reaction time = higher score, consistency bonus
        base_score = max(0, 100 - (reaction_time * 50))  # 2 seconds = 0 points
        consistency_bonus = consistency * 0.2
        
        return min(100, base_score + consistency_bonus)
    
    @staticmethod
    def get_performance_rank(score: float) -> str:
        """Get performance rank based on score."""
        if score >= 95:
            return "S+ (Elite)"
        elif score >= 90:
            return "S (Excellent)"
        elif score >= 80:
            return "A (Very Good)"
        elif score >= 70:
            return "B (Good)"
        elif score >= 60:
            return "C (Average)"
        elif score >= 50:
            return "D (Below Average)"
        else:
            return "F (Needs Improvement)"
    
    @staticmethod
    def calculate_percentile(score: float, all_scores: List[float]) -> float:
        """Calculate percentile rank of a score."""
        if not all_scores:
            return 50.0
        
        sorted_scores = sorted(all_scores)
        count_below = sum(1 for s in sorted_scores if s < score)
        return (count_below / len(sorted_scores)) * 100
