"""
Benchmark Widget for ZeroLag GUI.

This module provides the GUI interface for the benchmark tool,
including test selection, real-time visualization, and results display.
"""

import time
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QProgressBar,
    QTextEdit, QGroupBox, QFrame, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont

from src.core.benchmark import (
    BenchmarkManager, BenchmarkConfig, TestType, DifficultyLevel
)


class BenchmarkCanvas(QWidget):
    """Canvas widget for rendering benchmark tests."""
    
    # Signals
    mouse_clicked = pyqtSignal(float, float)  # x, y
    key_pressed = pyqtSignal(str)  # key
    key_released = pyqtSignal(str)  # key
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Test state
        self.current_test = None
        self.benchmark_manager = None
        self.visual_feedback = None
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update)
        self.update_timer.start(16)  # ~60 FPS
    
    def set_benchmark_manager(self, manager: BenchmarkManager):
        """Set the benchmark manager."""
        self.benchmark_manager = manager
        if manager:
            self.visual_feedback = manager.visual_feedback
    
    def start_test(self, test_type: str):
        """Start a benchmark test."""
        self.current_test = test_type
        if self.benchmark_manager:
            self.benchmark_manager.start_test(test_type)
            if test_type == "aim_accuracy":
                self.benchmark_manager.start_aim_test(self.width(), self.height())
    
    def stop_test(self):
        """Stop the current test."""
        if self.benchmark_manager and self.current_test:
            self.benchmark_manager.stop_current_test()
        self.current_test = None
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            self.mouse_clicked.emit(event.x(), event.y())
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        key = event.text().lower()
        if key:
            self.key_pressed.emit(key)
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        """Handle key release events."""
        key = event.text().lower()
        if key:
            self.key_released.emit(key)
        super().keyReleaseEvent(event)
    
    def paintEvent(self, event):
        """Paint the benchmark test visualization."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if not self.benchmark_manager or not self.current_test:
            self._paint_idle(painter)
            return
        
        # Get current progress
        progress = self.benchmark_manager.get_current_progress()
        
        if self.current_test == "aim_accuracy":
            self._paint_aim_test(painter, progress)
        elif self.current_test == "key_speed":
            self._paint_key_speed_test(painter, progress)
        elif self.current_test == "reaction_time":
            self._paint_reaction_test(painter, progress)
    
    def _paint_idle(self, painter: QPainter):
        """Paint idle state."""
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        # Draw instructions
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 16))
        painter.drawText(self.rect(), Qt.AlignCenter, "Select a test to begin benchmarking")
    
    def _paint_aim_test(self, painter: QPainter, progress: Dict[str, Any]):
        """Paint aim accuracy test."""
        # Background
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        # Get active targets from aim test
        if hasattr(self.benchmark_manager.aim_test, 'get_active_targets'):
            targets = self.benchmark_manager.aim_test.get_active_targets()
            
            # Draw targets
            for target in targets:
                self._draw_target(painter, target)
        
        # Draw UI overlay
        self._draw_ui_overlay(painter, progress)
    
    def _paint_key_speed_test(self, painter: QPainter, progress: Dict[str, Any]):
        """Paint key speed test."""
        # Background
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        # Get current sequence
        sequence = self.benchmark_manager.get_current_sequence()
        if sequence:
            self._draw_key_sequence(painter, sequence, progress)
        
        # Draw UI overlay
        self._draw_ui_overlay(painter, progress)
    
    def _paint_reaction_test(self, painter: QPainter, progress: Dict[str, Any]):
        """Paint reaction time test."""
        # Background
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        # Draw stimulus if visible
        if self.benchmark_manager.is_stimulus_visible():
            self._draw_stimulus(painter)
        
        # Draw waiting message if waiting
        if self.benchmark_manager.is_waiting_for_stimulus():
            self._draw_waiting_message(painter)
        
        # Draw UI overlay
        self._draw_ui_overlay(painter, progress)
    
    def _draw_target(self, painter: QPainter, target):
        """Draw an aim test target."""
        # Target circle
        pen = QPen(QColor(255, 100, 100), 3)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 100, 100, 100)))
        
        x = target.x - target.size / 2
        y = target.y - target.size / 2
        painter.drawEllipse(x, y, target.size, target.size)
        
        # Target center
        center_size = target.size * 0.3
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawEllipse(
            target.x - center_size / 2,
            target.y - center_size / 2,
            center_size, center_size
        )
    
    def _draw_key_sequence(self, painter: QPainter, sequence: list, progress: Dict[str, Any]):
        """Draw key sequence for key speed test."""
        if not sequence:
            return
        
        # Calculate positions
        center_x = self.width() // 2
        center_y = self.height() // 2
        key_size = 60
        spacing = 80
        start_x = center_x - (len(sequence) - 1) * spacing // 2
        
        current_index = progress.get('current_key_index', 0)
        
        for i, key in enumerate(sequence):
            x = start_x + i * spacing
            y = center_y
            
            # Highlight current key
            if i == current_index:
                self._draw_highlighted_key(painter, x, y, key_size, key)
            else:
                self._draw_key(painter, x, y, key_size, key)
    
    def _draw_key(self, painter: QPainter, x: float, y: float, size: float, key: str):
        """Draw a single key."""
        pen = QPen(QColor(255, 255, 255), 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        
        # Key rectangle
        rect = painter.window()
        painter.drawRoundedRect(x - size // 2, y - size // 2, size, size, 8, 8)
        
        # Key text
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(x - size // 2, y - size // 2, size, size, 
                        Qt.AlignCenter, key.upper())
    
    def _draw_highlighted_key(self, painter: QPainter, x: float, y: float, size: float, key: str):
        """Draw a highlighted key."""
        pen = QPen(QColor(100, 255, 100), 3)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(100, 255, 100, 100)))
        
        # Key rectangle
        painter.drawRoundedRect(x - size // 2, y - size // 2, size, size, 8, 8)
        
        # Key text
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 16, QFont.Bold))
        painter.drawText(x - size // 2, y - size // 2, size, size, 
                        Qt.AlignCenter, key.upper())
    
    def _draw_stimulus(self, painter: QPainter):
        """Draw reaction test stimulus."""
        center_x = self.width() // 2
        center_y = self.height() // 2
        size = 100
        
        pen = QPen(QColor(255, 255, 100), 5)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(255, 255, 100, 150)))
        
        x = center_x - size // 2
        y = center_y - size // 2
        painter.drawEllipse(x, y, size, size)
    
    def _draw_waiting_message(self, painter: QPainter):
        """Draw waiting message for reaction test."""
        center_x = self.width() // 2
        center_y = self.height() // 2 + 100
        
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 18, QFont.Bold))
        painter.drawText(center_x - 150, center_y, "Wait for the stimulus...")
    
    def _draw_ui_overlay(self, painter: QPainter, progress: Dict[str, Any]):
        """Draw UI overlay with progress and stats."""
        # Progress bar
        self._draw_progress_bar(painter, progress)
        
        # Score
        score = progress.get('current_score', 0.0)
        painter.setPen(QPen(QColor(100, 255, 100)))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(20, 30, f"Score: {score:.1f}")
        
        # Stats
        y_offset = 60
        for key, value in progress.items():
            if key in ['hits', 'misses', 'correct_keys', 'total_keys', 'total_responses', 'false_starts']:
                painter.setPen(QPen(QColor(255, 255, 255)))
                painter.setFont(QFont("Arial", 12))
                painter.drawText(20, y_offset, f"{key.replace('_', ' ').title()}: {value}")
                y_offset += 20
    
    def _draw_progress_bar(self, painter: QPainter, progress: Dict[str, Any]):
        """Draw progress bar."""
        bar_width = self.width() - 40
        bar_height = 20
        bar_x = 20
        bar_y = self.height() - 40
        
        # Background
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 10, 10)
        
        # Progress
        progress_percent = progress.get('progress_percent', 0.0) / 100.0
        progress_width = int(bar_width * progress_percent)
        
        painter.setBrush(QBrush(QColor(100, 150, 255)))
        painter.drawRoundedRect(bar_x, bar_y, progress_width, bar_height, 10, 10)
        
        # Time remaining
        remaining = progress.get('remaining_time', 0.0)
        time_text = f"Time: {remaining:.1f}s"
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(bar_x + bar_width + 10, bar_y + bar_height // 2 + 5, time_text)


class BenchmarkWidget(QWidget):
    """Main benchmark widget for the GUI."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.benchmark_manager = None
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_group = QGroupBox("Benchmark Controls")
        control_layout = QHBoxLayout(control_group)
        
        # Test selection
        control_layout.addWidget(QLabel("Test Type:"))
        self.test_combo = QComboBox()
        self.test_combo.addItems(["Aim Accuracy", "Key Speed", "Reaction Time", "All Tests"])
        control_layout.addWidget(self.test_combo)
        
        # Difficulty selection
        control_layout.addWidget(QLabel("Difficulty:"))
        self.difficulty_combo = QComboBox()
        self.difficulty_combo.addItems(["Beginner", "Intermediate", "Advanced", "Expert"])
        self.difficulty_combo.setCurrentText("Intermediate")
        control_layout.addWidget(self.difficulty_combo)
        
        # Profile selection
        control_layout.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Default", "FPS", "MOBA", "RTS", "Custom"])
        control_layout.addWidget(self.profile_combo)
        
        # Control buttons
        self.start_btn = QPushButton("Start Test")
        self.start_btn.clicked.connect(self.start_test)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop Test")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        layout.addWidget(control_group)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Canvas area
        canvas_group = QGroupBox("Test Area")
        canvas_layout = QVBoxLayout(canvas_group)
        
        self.canvas = BenchmarkCanvas()
        canvas_layout.addWidget(self.canvas)
        
        content_splitter.addWidget(canvas_group)
        
        # Results area
        results_group = QGroupBox("Results & Statistics")
        results_layout = QVBoxLayout(results_group)
        
        # Current test info
        self.current_test_label = QLabel("No test running")
        self.current_test_label.setStyleSheet("font-weight: bold; color: #00d4ff;")
        results_layout.addWidget(self.current_test_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        results_layout.addWidget(self.progress_bar)
        
        # Score display
        self.score_label = QLabel("Score: 0.0")
        self.score_label.setStyleSheet("font-size: 14px; color: #00ff00;")
        results_layout.addWidget(self.score_label)
        
        # Statistics
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(150)
        self.stats_text.setReadOnly(True)
        results_layout.addWidget(self.stats_text)
        
        # History
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        results_layout.addWidget(QLabel("Test History:"))
        results_layout.addWidget(self.history_text)
        
        content_splitter.addWidget(results_group)
        content_splitter.setSizes([400, 300])
        
        layout.addWidget(content_splitter)
    
    def setup_connections(self):
        """Set up signal connections."""
        # Canvas signals
        self.canvas.mouse_clicked.connect(self.handle_mouse_click)
        self.canvas.key_pressed.connect(self.handle_key_press)
        self.canvas.key_released.connect(self.handle_key_release)
    
    def set_benchmark_manager(self, manager: BenchmarkManager):
        """Set the benchmark manager."""
        self.benchmark_manager = manager
        self.canvas.set_benchmark_manager(manager)
        
        if manager:
            # Connect manager signals
            manager.test_started.connect(self.on_test_started)
            manager.test_finished.connect(self.on_test_finished)
            manager.score_updated.connect(self.on_score_updated)
            manager.progress_updated.connect(self.on_progress_updated)
            manager.all_tests_finished.connect(self.on_all_tests_finished)
    
    def start_test(self):
        """Start the selected benchmark test."""
        if not self.benchmark_manager:
            return
        
        test_type = self.test_combo.currentText().lower().replace(" ", "_")
        difficulty = self.difficulty_combo.currentText().lower()
        profile = self.profile_combo.currentText()
        
        if test_type == "all_tests":
            self.benchmark_manager.run_all_tests(profile, difficulty)
        else:
            self.benchmark_manager.start_test(test_type, profile, difficulty)
            if test_type == "aim_accuracy":
                self.benchmark_manager.start_aim_test(self.canvas.width(), self.canvas.height())
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.canvas.setFocus()
    
    def stop_test(self):
        """Stop the current test."""
        if self.benchmark_manager:
            self.benchmark_manager.stop_current_test()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.current_test_label.setText("Test stopped")
    
    def handle_mouse_click(self, x: float, y: float):
        """Handle mouse click from canvas."""
        if self.benchmark_manager:
            self.benchmark_manager.handle_mouse_click(x, y)
    
    def handle_key_press(self, key: str):
        """Handle key press from canvas."""
        if self.benchmark_manager:
            self.benchmark_manager.handle_key_press(key)
    
    def handle_key_release(self, key: str):
        """Handle key release from canvas."""
        if self.benchmark_manager:
            self.benchmark_manager.handle_key_release(key)
    
    def on_test_started(self, test_type: str):
        """Handle test started signal."""
        self.current_test_label.setText(f"Running: {test_type.replace('_', ' ').title()}")
        self.progress_bar.setValue(0)
        self.score_label.setText("Score: 0.0")
    
    def on_test_finished(self, result):
        """Handle test finished signal."""
        self.update_history()
        self.update_statistics()
    
    def on_score_updated(self, test_type: str, score: float):
        """Handle score updated signal."""
        self.score_label.setText(f"Score: {score:.1f}")
    
    def on_progress_updated(self, test_type: str, progress: Dict[str, Any]):
        """Handle progress updated signal."""
        progress_percent = progress.get('progress_percent', 0.0)
        self.progress_bar.setValue(int(progress_percent))
        
        # Update stats text
        stats_text = f"Test: {test_type.replace('_', ' ').title()}\n"
        for key, value in progress.items():
            if key not in ['progress_percent', 'elapsed_time', 'remaining_time']:
                stats_text += f"{key.replace('_', ' ').title()}: {value}\n"
        
        self.stats_text.setText(stats_text)
    
    def on_all_tests_finished(self, metrics):
        """Handle all tests finished signal."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.current_test_label.setText("All tests completed!")
        
        # Show final results
        final_score = metrics.overall_score if hasattr(metrics, 'overall_score') else 0.0
        self.score_label.setText(f"Final Score: {final_score:.1f}")
        
        self.update_history()
        self.update_statistics()
    
    def update_history(self):
        """Update test history display."""
        if not self.benchmark_manager:
            return
        
        history = self.benchmark_manager.get_test_history(10)
        history_text = ""
        
        for result in reversed(history):
            history_text += f"{result.test_type.value.replace('_', ' ').title()}: "
            history_text += f"{result.overall_score:.1f} ({result.difficulty.value})\n"
        
        self.history_text.setText(history_text)
    
    def update_statistics(self):
        """Update statistics display."""
        if not self.benchmark_manager:
            return
        
        stats = self.benchmark_manager.get_statistics()
        if not stats:
            return
        
        stats_text = f"Total Tests: {stats.get('total_tests', 0)}\n"
        stats_text += f"Overall Rank: {stats.get('overall_rank', 'No Data')}\n\n"
        
        best_scores = stats.get('best_scores', {})
        stats_text += "Best Scores:\n"
        for test_type, score in best_scores.items():
            stats_text += f"  {test_type.replace('_', ' ').title()}: {score:.1f}\n"
        
        avg_scores = stats.get('average_scores', {})
        stats_text += "\nAverage Scores:\n"
        for test_type, score in avg_scores.items():
            stats_text += f"  {test_type.replace('_', ' ').title()}: {score:.1f}\n"
        
        self.stats_text.setText(stats_text)
