"""
Key Speed Test for ZeroLag Benchmark Tool.

This module implements the key press speed test with sequence tracking,
timing measurement, and performance analysis.
"""

import time
import random
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from .metrics import TestType, TestMetrics, ScoreCalculator


@dataclass
class KeyPress:
    """Represents a single key press event."""
    key: str
    press_time: float
    release_time: Optional[float] = None
    duration: float = 0.0
    correct: bool = False
    expected: bool = False


class KeySpeedTest(QObject):
    """Key speed test implementation."""
    
    # Signals
    key_sequence_updated = pyqtSignal(list)  # current_sequence
    key_pressed = pyqtSignal(str, bool)  # key, correct
    test_started = pyqtSignal()
    test_finished = pyqtSignal(object)  # TestMetrics
    score_updated = pyqtSignal(float)  # current_score
    
    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        self.test_active = False
        self.start_time = 0.0
        self.end_time = 0.0
        self.key_sequence: List[str] = []
        self.current_sequence: List[str] = []
        self.key_presses: List[KeyPress] = []
        self.current_key_index = 0
        self.correct_keys = 0
        self.total_keys = 0
        self.total_press_time = 0.0
        
        # Test parameters
        self.test_duration = self.config.get('test_duration', 30.0)
        self.key_sequence_length = self.config.get('key_sequence_length', 4)
        self.available_keys = self.config.get('available_keys', ['a', 's', 'd', 'w', 'space'])
        self.difficulty_multiplier = self.config.get('difficulty_multiplier', 1.0)
        
        # Timer for test duration
        self.test_timer = QTimer()
        self.test_timer.timeout.connect(self._finish_test)
        self.test_timer.setSingleShot(True)
        
        # Timer for sequence updates
        self.sequence_timer = QTimer()
        self.sequence_timer.timeout.connect(self._update_sequence)
    
    def start_test(self):
        """Start the key speed test."""
        if self.test_active:
            return
        
        self.test_active = True
        self.start_time = time.time()
        self.end_time = 0.0
        self.key_sequence.clear()
        self.current_sequence.clear()
        self.key_presses.clear()
        self.current_key_index = 0
        self.correct_keys = 0
        self.total_keys = 0
        self.total_press_time = 0.0
        
        # Generate initial key sequence
        self._generate_sequence()
        
        # Start test timer
        self.test_timer.start(int(self.test_duration * 1000))
        
        # Start sequence update timer (faster for higher difficulty)
        update_interval = max(1000, int(3000 / self.difficulty_multiplier))
        self.sequence_timer.start(update_interval)
        
        self.test_started.emit()
        self.key_sequence_updated.emit(self.current_sequence.copy())
    
    def stop_test(self):
        """Stop the key speed test."""
        if not self.test_active:
            return
        
        self.test_active = False
        self.end_time = time.time()
        self.test_timer.stop()
        self.sequence_timer.stop()
        
        # Calculate final metrics
        metrics = self._calculate_metrics()
        self.test_finished.emit(metrics)
    
    def handle_key_press(self, key: str) -> bool:
        """Handle key press during test. Returns True if key was correct."""
        if not self.test_active:
            return False
        
        current_time = time.time()
        
        # Check if this is the expected key
        expected_key = self.current_sequence[self.current_key_index] if self.current_key_index < len(self.current_sequence) else None
        is_correct = (key.lower() == expected_key.lower()) if expected_key else False
        
        # Record key press
        key_press = KeyPress(
            key=key.lower(),
            press_time=current_time,
            expected=(expected_key is not None),
            correct=is_correct
        )
        
        self.key_presses.append(key_press)
        self.total_keys += 1
        
        if is_correct:
            self.correct_keys += 1
            self.current_key_index += 1
            
            # Check if sequence is complete
            if self.current_key_index >= len(self.current_sequence):
                self._complete_sequence()
        
        self.key_pressed.emit(key, is_correct)
        
        # Update score
        current_score = self._calculate_current_score()
        self.score_updated.emit(current_score)
        
        return is_correct
    
    def handle_key_release(self, key: str):
        """Handle key release during test."""
        if not self.test_active:
            return
        
        current_time = time.time()
        
        # Find the most recent press of this key
        for key_press in reversed(self.key_presses):
            if key_press.key == key.lower() and key_press.release_time is None:
                key_press.release_time = current_time
                key_press.duration = current_time - key_press.press_time
                self.total_press_time += key_press.duration
                break
    
    def _generate_sequence(self):
        """Generate a new key sequence."""
        sequence_length = min(self.key_sequence_length, len(self.available_keys))
        self.key_sequence = random.sample(self.available_keys, sequence_length)
        self.current_sequence = self.key_sequence.copy()
        self.current_key_index = 0
    
    def _update_sequence(self):
        """Update the key sequence during test."""
        if not self.test_active:
            return
        
        # Generate new sequence
        self._generate_sequence()
        self.key_sequence_updated.emit(self.current_sequence.copy())
    
    def _complete_sequence(self):
        """Handle sequence completion."""
        # Reset for next sequence
        self.current_key_index = 0
        self._generate_sequence()
        self.key_sequence_updated.emit(self.current_sequence.copy())
    
    def _finish_test(self):
        """Finish the test when duration is reached."""
        self.stop_test()
    
    def _calculate_current_score(self) -> float:
        """Calculate current score during test."""
        if self.total_keys == 0:
            return 0.0
        
        accuracy = self.correct_keys / self.total_keys
        
        # Calculate keys per second
        elapsed_time = time.time() - self.start_time
        keys_per_second = self.correct_keys / max(0.1, elapsed_time)
        
        return ScoreCalculator.calculate_key_speed_score(keys_per_second, accuracy)
    
    def _calculate_metrics(self) -> TestMetrics:
        """Calculate final test metrics."""
        duration = self.end_time - self.start_time
        
        accuracy = self.correct_keys / self.total_keys if self.total_keys > 0 else 0.0
        keys_per_second = self.correct_keys / max(0.1, duration)
        avg_press_duration = self.total_press_time / max(1, len([kp for kp in self.key_presses if kp.release_time is not None]))
        
        score = ScoreCalculator.calculate_key_speed_score(keys_per_second, accuracy)
        
        # Calculate reaction time (time between sequence updates and key presses)
        reaction_times = []
        for key_press in self.key_presses:
            if key_press.correct and key_press.expected:
                # Find the sequence update time before this key press
                # This is a simplified calculation
                reaction_times.append(0.1)  # Placeholder
        
        avg_reaction_time = sum(reaction_times) / len(reaction_times) if reaction_times else 0.0
        
        # Collect raw data
        raw_data = []
        for key_press in self.key_presses:
            raw_data.append({
                'key': key_press.key,
                'press_time': key_press.press_time,
                'release_time': key_press.release_time,
                'duration': key_press.duration,
                'correct': key_press.correct,
                'expected': key_press.expected
            })
        
        return TestMetrics(
            test_type=TestType.KEY_SPEED,
            start_time=self.start_time,
            end_time=self.end_time,
            duration=duration,
            score=score,
            accuracy=accuracy,
            speed=keys_per_second,
            reaction_time=avg_reaction_time,
            errors=self.total_keys - self.correct_keys,
            total_attempts=self.total_keys,
            success_rate=accuracy,
            raw_data=raw_data
        )
    
    def get_current_sequence(self) -> List[str]:
        """Get the current key sequence."""
        return self.current_sequence.copy()
    
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
            'correct_keys': self.correct_keys,
            'total_keys': self.total_keys,
            'current_sequence': self.current_sequence.copy(),
            'current_key_index': self.current_key_index,
            'current_score': self._calculate_current_score()
        }
