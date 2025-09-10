"""
Reaction Time Test for ZeroLag Benchmark Tool.

This module implements the reaction time test with visual stimuli,
timing measurement, and consistency analysis.
"""

import time
import random
from dataclasses import dataclass
from typing import List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from .metrics import TestType, TestMetrics, ScoreCalculator


@dataclass
class ReactionStimulus:
    """Represents a reaction stimulus event."""
    stimulus_time: float
    response_time: Optional[float] = None
    reaction_time: float = 0.0
    responded: bool = False
    false_start: bool = False


class ReactionTimeTest(QObject):
    """Reaction time test implementation."""
    
    # Signals
    stimulus_appeared = pyqtSignal()  # Visual stimulus appeared
    stimulus_disappeared = pyqtSignal()  # Visual stimulus disappeared
    response_detected = pyqtSignal(float)  # reaction_time
    false_start_detected = pyqtSignal()
    test_started = pyqtSignal()
    test_finished = pyqtSignal(object)  # TestMetrics
    score_updated = pyqtSignal(float)  # current_score
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        self.test_active = False
        self.start_time = 0.0
        self.end_time = 0.0
        self.stimuli: List[ReactionStimulus] = []
        self.current_stimulus: Optional[ReactionStimulus] = None
        self.total_responses = 0
        self.false_starts = 0
        self.reaction_times: List[float] = []
        
        # Test parameters
        self.test_duration = self.config.get('test_duration', 30.0)
        self.stimulus_delay_min = self.config.get('stimulus_delay_min', 1.0)
        self.stimulus_delay_max = self.config.get('stimulus_delay_max', 4.0)
        self.stimulus_duration = self.config.get('stimulus_duration', 0.5)
        self.max_reaction_time = self.config.get('max_reaction_time', 5.0)
        self.difficulty_multiplier = self.config.get('difficulty_multiplier', 1.0)
        
        # Timer for test duration
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self._finish_test)
        self.test_timer.setSingleShot(True)
        
        # Timer for stimulus delay
        self.stimulus_timer = QTimer()
        self.stimulus_timer.timeout.connect(self._show_stimulus)
        self.stimulus_timer.setSingleShot(True)
        
        # Timer for stimulus duration
        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self._hide_stimulus)
        self.duration_timer.setSingleShot(True)
        
        # State tracking
        self.waiting_for_stimulus = False
        self.stimulus_visible = False
    
    def start_test(self):
        """Start the reaction time test."""
        if self.test_active:
            return
        
        self.test_active = True
        self.start_time = time.time()
        self.end_time = 0.0
        self.stimuli.clear()
        self.current_stimulus = None
        self.total_responses = 0
        self.false_starts = 0
        self.reaction_times.clear()
        self.waiting_for_stimulus = False
        self.stimulus_visible = False
        
        # Start test timer
        self.test_timer.start(int(self.test_duration * 1000))
        
        # Start first stimulus delay
        self._schedule_next_stimulus()
        
        self.test_started.emit()
    
    def stop_test(self):
        """Stop the reaction time test."""
        if not self.test_active:
            return
        
        self.test_active = False
        self.end_time = time.time()
        self.test_timer.stop()
        self.stimulus_timer.stop()
        self.duration_timer.stop()
        
        # Calculate final metrics
        metrics = self._calculate_metrics()
        self.test_finished.emit(metrics)
    
    def handle_response(self) -> bool:
        """Handle user response (key press or click). Returns True if valid response."""
        if not self.test_active:
            return False
        
        current_time = time.time()
        
        if self.stimulus_visible and self.current_stimulus and not self.current_stimulus.responded:
            # Valid response to visible stimulus
            self.current_stimulus.response_time = current_time
            self.current_stimulus.reaction_time = current_time - self.current_stimulus.stimulus_time
            self.current_stimulus.responded = True
            
            self.total_responses += 1
            self.reaction_times.append(self.current_stimulus.reaction_time)
            
            self.response_detected.emit(self.current_stimulus.reaction_time)
            
            # Update score
            current_score = self._calculate_current_score()
            self.score_updated.emit(current_score)
            
            # Schedule next stimulus
            self._schedule_next_stimulus()
            
            return True
        
        elif not self.stimulus_visible and self.waiting_for_stimulus:
            # False start - response before stimulus appeared
            self.false_starts += 1
            self.false_start_detected.emit()
            return False
        
        return False
    
    def _schedule_next_stimulus(self):
        """Schedule the next stimulus with random delay."""
        if not self.test_active:
            return
        
        # Calculate delay based on difficulty
        base_delay_min = self.stimulus_delay_min / self.difficulty_multiplier
        base_delay_max = self.stimulus_delay_max / self.difficulty_multiplier
        
        delay = random.uniform(base_delay_min, base_delay_max)
        delay_ms = int(delay * 1000)
        
        self.waiting_for_stimulus = True
        self.stimulus_timer.start(delay_ms)
    
    def _show_stimulus(self):
        """Show the visual stimulus."""
        if not self.test_active:
            return
        
        self.waiting_for_stimulus = False
        self.stimulus_visible = True
        
        # Create new stimulus
        self.current_stimulus = ReactionStimulus(stimulus_time=time.time())
        self.stimuli.append(self.current_stimulus)
        
        self.stimulus_appeared.emit()
        
        # Schedule stimulus to disappear
        duration_ms = int(self.stimulus_duration * 1000)
        self.duration_timer.start(duration_ms)
    
    def _hide_stimulus(self):
        """Hide the visual stimulus."""
        if not self.test_active:
            return
        
        self.stimulus_visible = False
        self.stimulus_disappeared.emit()
        
        # If no response was recorded, mark as missed
        if self.current_stimulus and not self.current_stimulus.responded:
            self.current_stimulus.reaction_time = self.max_reaction_time
        
        # Schedule next stimulus
        self._schedule_next_stimulus()
    
    def _finish_test(self):
        """Finish the test when duration is reached."""
        self.stop_test()
    
    def _calculate_current_score(self) -> float:
        """Calculate current score during test."""
        if not self.reaction_times:
            return 0.0
        
        avg_reaction_time = sum(self.reaction_times) / len(self.reaction_times)
        
        # Calculate consistency (inverse of standard deviation)
        if len(self.reaction_times) > 1:
            mean_time = avg_reaction_time
            variance = sum((rt - mean_time) ** 2 for rt in self.reaction_times) / len(self.reaction_times)
            std_dev = variance ** 0.5
            consistency = max(0, 1.0 - (std_dev / mean_time)) if mean_time > 0 else 0.0
        else:
            consistency = 1.0
        
        return ScoreCalculator.calculate_reaction_score(avg_reaction_time, consistency)
    
    def _calculate_metrics(self) -> TestMetrics:
        """Calculate final test metrics."""
        duration = self.end_time - self.start_time
        
        # Calculate average reaction time from valid responses
        valid_reaction_times = [rt for rt in self.reaction_times if rt < self.max_reaction_time]
        avg_reaction_time = sum(valid_reaction_times) / len(valid_reaction_times) if valid_reaction_times else self.max_reaction_time
        
        # Calculate consistency
        if len(valid_reaction_times) > 1:
            mean_time = avg_reaction_time
            variance = sum((rt - mean_time) ** 2 for rt in valid_reaction_times) / len(valid_reaction_times)
            std_dev = variance ** 0.5
            consistency = max(0, 1.0 - (std_dev / mean_time)) if mean_time > 0 else 0.0
        else:
            consistency = 1.0
        
        # Calculate accuracy (valid responses / total stimuli)
        total_stimuli = len(self.stimuli)
        accuracy = self.total_responses / total_stimuli if total_stimuli > 0 else 0.0
        
        # Calculate speed (responses per second)
        speed = self.total_responses / max(0.1, duration)
        
        score = ScoreCalculator.calculate_reaction_score(avg_reaction_time, consistency)
        
        # Collect raw data
        raw_data = []
        for stimulus in self.stimuli:
            raw_data.append({
                'stimulus_time': stimulus.stimulus_time,
                'response_time': stimulus.response_time,
                'reaction_time': stimulus.reaction_time,
                'responded': stimulus.responded,
                'false_start': stimulus.false_start
            })
        
        return TestMetrics(
            test_type=TestType.REACTION_TIME,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=duration,
            score=score,
            accuracy=accuracy,
            speed=speed,
            reaction_time=avg_reaction_time,
            errors=self.false_starts,
            total_attempts=total_stimuli,
            success_rate=accuracy,
            raw_data=raw_data
        )
    
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
            'total_responses': self.total_responses,
            'false_starts': self.false_starts,
            'avg_reaction_time': sum(self.reaction_times) / len(self.reaction_times) if self.reaction_times else 0.0,
            'stimulus_visible': self.stimulus_visible,
            'waiting_for_stimulus': self.waiting_for_stimulus,
            'current_score': self._calculate_current_score()
        }
