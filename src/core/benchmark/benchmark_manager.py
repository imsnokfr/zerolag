"""
Benchmark Manager for ZeroLag Benchmark Tool.

This module coordinates all benchmark tests and manages results,
providing a unified interface for the benchmark system.
"""

import time
import json
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from .metrics import (
    TestType, TestResult, TestMetrics, BenchmarkMetrics, 
    BenchmarkConfig, DifficultyLevel, ScoreCalculator
)
from .aim_test import AimAccuracyTest
from .key_speed_test import KeySpeedTest
from .reaction_test import ReactionTimeTest
from .visual_feedback import VisualFeedbackManager


class BenchmarkManager(QObject):
    """Main manager for all benchmark tests."""
    
    # Signals
    test_started = pyqtSignal(str)  # test_type
    test_finished = pyqtSignal(object)  # TestResult
    score_updated = pyqtSignal(str, float)  # test_type, score
    progress_updated = pyqtSignal(str, dict)  # test_type, progress
    all_tests_finished = pyqtSignal(object)  # BenchmarkMetrics
    
    def __init__(self, config: BenchmarkConfig = None):
        super().__init__()
        self.config = config or BenchmarkConfig()
        self.results: List[TestResult] = []
        self.current_test: Optional[str] = None
        self.current_session_id = ""
        
        # Initialize test components
        self.aim_test = AimAccuracyTest(self.config.__dict__)
        self.key_speed_test = KeySpeedTest(self.config.__dict__)
        self.reaction_test = ReactionTimeTest(self.config.__dict__)
        
        # Initialize visual feedback (will be set by GUI)
        self.visual_feedback = None
        
        # Connect signals
        self._connect_test_signals()
        
        # Results storage
        self.results_file = Path("benchmark_results.json")
        self._load_results()
    
    def _connect_test_signals(self):
        """Connect signals from all test components."""
        # Aim test signals
        self.aim_test.test_started.connect(lambda: self.test_started.emit("aim_accuracy"))
        self.aim_test.test_finished.connect(self._on_test_finished)
        self.aim_test.score_updated.connect(lambda score: self.score_updated.emit("aim_accuracy", score))
        
        # Key speed test signals
        self.key_speed_test.test_started.connect(lambda: self.test_started.emit("key_speed"))
        self.key_speed_test.test_finished.connect(self._on_test_finished)
        self.key_speed_test.score_updated.connect(lambda score: self.score_updated.emit("key_speed", score))
        
        # Reaction test signals
        self.reaction_test.test_started.connect(lambda: self.test_started.emit("reaction_time"))
        self.reaction_test.test_finished.connect(self._on_test_finished)
        self.reaction_test.score_updated.connect(lambda score: self.score_updated.emit("reaction_time", score))
    
    def start_test(self, test_type: str, profile_name: str = "Default", difficulty: str = "intermediate"):
        """Start a specific benchmark test."""
        if self.current_test:
            return False
        
        self.current_test = test_type
        self.current_session_id = str(uuid.uuid4())
        
        # Update test configurations
        self._update_test_configs(difficulty)
        
        if test_type == "aim_accuracy":
            # Aim test needs widget dimensions
            return True  # Will be started with dimensions
        elif test_type == "key_speed":
            self.key_speed_test.start_test()
        elif test_type == "reaction_time":
            self.reaction_test.start_test()
        else:
            return False
        
        return True
    
    def start_aim_test(self, width: int, height: int):
        """Start the aim accuracy test with dimensions."""
        if self.current_test == "aim_accuracy":
            self.aim_test.start_test(width, height)
    
    def stop_current_test(self):
        """Stop the currently running test."""
        if not self.current_test:
            return
        
        if self.current_test == "aim_accuracy":
            self.aim_test.stop_test()
        elif self.current_test == "key_speed":
            self.key_speed_test.stop_test()
        elif self.current_test == "reaction_time":
            self.reaction_test.stop_test()
        
        self.current_test = None
    
    def handle_mouse_click(self, x: float, y: float) -> bool:
        """Handle mouse click for aim test."""
        if self.current_test == "aim_accuracy":
            return self.aim_test.handle_click(x, y)
        return False
    
    def handle_key_press(self, key: str) -> bool:
        """Handle key press for key speed and reaction tests."""
        if self.current_test == "key_speed":
            return self.key_speed_test.handle_key_press(key)
        elif self.current_test == "reaction_time":
            return self.reaction_test.handle_response()
        return False
    
    def handle_key_release(self, key: str):
        """Handle key release for key speed test."""
        if self.current_test == "key_speed":
            self.key_speed_test.handle_key_release(key)
    
    def get_current_progress(self) -> dict:
        """Get progress of the current test."""
        if not self.current_test:
            return {}
        
        if self.current_test == "aim_accuracy":
            return self.aim_test.get_test_progress()
        elif self.current_test == "key_speed":
            return self.key_speed_test.get_test_progress()
        elif self.current_test == "reaction_time":
            return self.reaction_test.get_test_progress()
        
        return {}
    
    def get_current_sequence(self) -> List[str]:
        """Get current key sequence for key speed test."""
        if self.current_test == "key_speed":
            return self.key_speed_test.get_current_sequence()
        return []
    
    def is_stimulus_visible(self) -> bool:
        """Check if reaction test stimulus is visible."""
        if self.current_test == "reaction_time":
            progress = self.reaction_test.get_test_progress()
            return progress.get('stimulus_visible', False)
        return False
    
    def is_waiting_for_stimulus(self) -> bool:
        """Check if reaction test is waiting for stimulus."""
        if self.current_test == "reaction_time":
            progress = self.reaction_test.get_test_progress()
            return progress.get('waiting_for_stimulus', False)
        return False
    
    def _on_test_finished(self, metrics: TestMetrics):
        """Handle test completion."""
        if not self.current_test or not self.current_session_id:
            return
        
        # Create test result
        result = TestResult(
            session_id=self.current_session_id,
            profile_name=getattr(self, 'current_profile', 'Default'),
            test_type=TestType(self.current_test),
            difficulty=DifficultyLevel(getattr(self, 'current_difficulty', 'intermediate')),
            start_time=metrics.start_time,
            end_time=metrics.end_time,
            total_duration=metrics.duration,
            metrics=[metrics]
        )
        
        # Add to results
        self.results.append(result)
        self._save_results()
        
        # Emit signals
        self.test_finished.emit(result)
        
        # Check if all tests are complete (for combined testing)
        if self._should_run_all_tests():
            self._run_next_test()
        else:
            self.current_test = None
            self._calculate_overall_metrics()
    
    def _should_run_all_tests(self) -> bool:
        """Check if we should run all tests in sequence."""
        return getattr(self, 'run_all_tests', False)
    
    def _run_next_test(self):
        """Run the next test in the sequence."""
        test_sequence = ["aim_accuracy", "key_speed", "reaction_time"]
        current_index = test_sequence.index(self.current_test) if self.current_test in test_sequence else -1
        
        if current_index < len(test_sequence) - 1:
            next_test = test_sequence[current_index + 1]
            self.start_test(next_test, getattr(self, 'current_profile', 'Default'))
        else:
            # All tests complete
            self.current_test = None
            self.run_all_tests = False
            self._calculate_overall_metrics()
    
    def run_all_tests(self, profile_name: str = "Default", difficulty: str = "intermediate"):
        """Run all benchmark tests in sequence."""
        self.run_all_tests = True
        self.current_profile = profile_name
        self.current_difficulty = difficulty
        self.start_test("aim_accuracy", profile_name, difficulty)
    
    def _update_test_configs(self, difficulty: str):
        """Update test configurations based on difficulty."""
        difficulty_multipliers = {
            "beginner": 0.5,
            "intermediate": 1.0,
            "advanced": 1.5,
            "expert": 2.0
        }
        
        multiplier = difficulty_multipliers.get(difficulty, 1.0)
        
        # Update all test configs
        for test in [self.aim_test, self.key_speed_test, self.reaction_test]:
            test.difficulty_multiplier = multiplier
    
    def _calculate_overall_metrics(self):
        """Calculate overall benchmark metrics."""
        if not self.results:
            return
        
        # Get recent results (last 10 sessions)
        recent_results = self.results[-10:]
        
        # Calculate metrics
        metrics = BenchmarkMetrics(total_tests=0)
        for result in recent_results:
            metrics.add_result(result)
        
        self.all_tests_finished.emit(metrics)
    
    def get_test_history(self, limit: int = 50) -> List[TestResult]:
        """Get test history with optional limit."""
        return self.results[-limit:] if limit > 0 else self.results
    
    def get_best_scores(self) -> Dict[str, float]:
        """Get best scores for each test type."""
        best_scores = {}
        
        for test_type in ["aim_accuracy", "key_speed", "reaction_time"]:
            scores = []
            for result in self.results:
                if result.test_type.value == test_type:
                    scores.append(result.overall_score)
            
            if scores:
                best_scores[test_type] = max(scores)
            else:
                best_scores[test_type] = 0.0
        
        return best_scores
    
    def get_average_scores(self) -> Dict[str, float]:
        """Get average scores for each test type."""
        avg_scores = {}
        
        for test_type in ["aim_accuracy", "key_speed", "reaction_time"]:
            scores = []
            for result in self.results:
                if result.test_type.value == test_type:
                    scores.append(result.overall_score)
            
            if scores:
                avg_scores[test_type] = sum(scores) / len(scores)
            else:
                avg_scores[test_type] = 0.0
        
        return avg_scores
    
    def get_improvement_trend(self, test_type: str, days: int = 7) -> float:
        """Get improvement trend for a specific test type."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        recent_results = [
            r for r in self.results 
            if r.test_type.value == test_type and r.start_time >= cutoff_time
        ]
        
        if len(recent_results) < 2:
            return 0.0
        
        scores = [r.overall_score for r in recent_results]
        
        # Simple linear regression
        n = len(scores)
        x_values = list(range(n))
        sum_x = sum(x_values)
        sum_y = sum(scores)
        sum_xy = sum(x * y for x, y in zip(x_values, scores))
        sum_x2 = sum(x * x for x in x_values)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def export_results(self, file_path: str):
        """Export results to a JSON file."""
        export_data = {
            'export_time': time.time(),
            'total_results': len(self.results),
            'results': []
        }
        
        for result in self.results:
            result_data = {
                'session_id': result.session_id,
                'profile_name': result.profile_name,
                'test_type': result.test_type.value,
                'difficulty': result.difficulty.value,
                'start_time': result.start_time,
                'end_time': result.end_time,
                'total_duration': result.total_duration,
                'overall_score': result.overall_score,
                'rank': result.rank,
                'percentile': result.percentile,
                'notes': result.notes,
                'metrics': []
            }
            
            for metric in result.metrics:
                metric_data = {
                    'test_type': metric.test_type.value,
                    'start_time': metric.start_time,
                    'end_time': metric.end_time,
                    'duration': metric.duration,
                    'score': metric.score,
                    'accuracy': metric.accuracy,
                    'speed': metric.speed,
                    'reaction_time': metric.reaction_time,
                    'errors': metric.errors,
                    'total_attempts': metric.total_attempts,
                    'success_rate': metric.success_rate
                }
                result_data['metrics'].append(metric_data)
            
            export_data['results'].append(result_data)
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def _save_results(self):
        """Save results to file."""
        try:
            self.export_results(str(self.results_file))
        except Exception as e:
            print(f"Error saving benchmark results: {e}")
    
    def _load_results(self):
        """Load results from file."""
        try:
            if self.results_file.exists():
                with open(self.results_file, 'r') as f:
                    data = json.load(f)
                
                self.results = []
                for result_data in data.get('results', []):
                    # Reconstruct TestResult from saved data
                    # This is a simplified reconstruction
                    pass  # Would implement full reconstruction here
        except Exception as e:
            print(f"Error loading benchmark results: {e}")
            self.results = []
    
    def clear_history(self):
        """Clear all test history."""
        self.results.clear()
        self._save_results()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive benchmark statistics."""
        if not self.results:
            return {}
        
        total_tests = len(self.results)
        best_scores = self.get_best_scores()
        avg_scores = self.get_average_scores()
        
        # Calculate improvement trends
        trends = {}
        for test_type in ["aim_accuracy", "key_speed", "reaction_time"]:
            trends[test_type] = self.get_improvement_trend(test_type)
        
        return {
            'total_tests': total_tests,
            'best_scores': best_scores,
            'average_scores': avg_scores,
            'improvement_trends': trends,
            'last_test_time': self.results[-1].start_time if self.results else 0,
            'overall_rank': self._calculate_overall_rank()
        }
    
    def _calculate_overall_rank(self) -> str:
        """Calculate overall performance rank."""
        if not self.results:
            return "No Data"
        
        recent_scores = [r.overall_score for r in self.results[-10:]]
        avg_score = sum(recent_scores) / len(recent_scores)
        
        return ScoreCalculator.get_performance_rank(avg_score)
