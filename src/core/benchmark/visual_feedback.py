"""
Visual Feedback Manager for ZeroLag Benchmark Tool.

This module provides visual feedback, animations, and rendering
for the benchmark tests with real-time updates.
"""

import math
import time
from typing import List, Tuple, Optional, Dict, Any
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics
from PyQt5.QtWidgets import QWidget


class VisualFeedbackManager(QObject):
    """Manages visual feedback for benchmark tests."""
    
    # Signals
    update_required = pyqtSignal()  # Request visual update
    
    def __init__(self, widget: QWidget):
        super().__init__()
        self.widget = widget
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(16)  # ~60 FPS
        
        # Animation state
        self.animations: List[Dict[str, Any]] = []
        self.pulse_phase = 0.0
        self.fade_phase = 0.0
        
        # Visual settings
        self.colors = {
            'target': QColor(255, 100, 100, 200),
            'target_hit': QColor(100, 255, 100, 200),
            'target_miss': QColor(255, 100, 100, 200),
            'background': QColor(30, 30, 30, 255),
            'text': QColor(255, 255, 255, 255),
            'score': QColor(100, 255, 100, 255),
            'progress': QColor(100, 150, 255, 255),
            'stimulus': QColor(255, 255, 100, 255)
        }
        
        # Font settings
        self.fonts = {
            'title': QFont("Arial", 16, QFont.Bold),
            'score': QFont("Arial", 14, QFont.Bold),
            'info': QFont("Arial", 12),
            'small': QFont("Arial", 10)
        }
    
    def render_aim_test(self, painter: QPainter, targets: List, progress: dict):
        """Render the aim accuracy test."""
        self._render_background(painter)
        self._render_targets(painter, targets)
        self._render_aim_ui(painter, progress)
    
    def render_key_speed_test(self, painter: QPainter, sequence: List[str], progress: dict):
        """Render the key speed test."""
        self._render_background(painter)
        self._render_key_sequence(painter, sequence, progress)
        self._render_key_speed_ui(painter, progress)
    
    def render_reaction_test(self, painter: QPainter, stimulus_visible: bool, progress: dict):
        """Render the reaction time test."""
        self._render_background(painter)
        if stimulus_visible:
            self._render_stimulus(painter)
        self._render_reaction_ui(painter, progress)
    
    def _render_background(self, painter: QPainter):
        """Render the background."""
        painter.fillRect(self.widget.rect(), self.colors['background'])
    
    def _render_targets(self, painter: QPainter, targets: List):
        """Render aim test targets."""
        for target in targets:
            if target.hit:
                # Render hit target
                self._render_hit_target(painter, target)
            else:
                # Render active target
                self._render_active_target(painter, target)
    
    def _render_active_target(self, painter: QPainter, target):
        """Render an active (unhit) target."""
        # Pulsing effect
        pulse = 1.0 + 0.2 * math.sin(self.pulse_phase + target.created_time * 5)
        size = target.size * pulse
        
        # Target circle
        pen = QPen(self.colors['target'], 3)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.colors['target']))
        
        x = target.x - size / 2
        y = target.y - size / 2
        painter.drawEllipse(x, y, size, size)
        
        # Target center
        center_size = size * 0.3
        painter.setBrush(QBrush(self.colors['text']))
        painter.drawEllipse(
            target.x - center_size / 2,
            target.y - center_size / 2,
            center_size, center_size
        )
    
    def _render_hit_target(self, painter: QPainter, target):
        """Render a hit target."""
        # Fade out effect
        fade = max(0, 1.0 - (time.time() - target.hit_time) * 2)
        if fade <= 0:
            return
        
        color = QColor(self.colors['target_hit'])
        color.setAlpha(int(200 * fade))
        
        pen = QPen(color, 3)
        painter.setPen(pen)
        painter.setBrush(QBrush(color))
        
        # Expanding circle effect
        expand = 1.0 + (time.time() - target.hit_time) * 3
        size = target.size * expand
        
        x = target.x - size / 2
        y = target.y - size / 2
        painter.drawEllipse(x, y, size, size)
        
        # Check mark
        if fade > 0.5:
            self._render_checkmark(painter, target.x, target.y, size * 0.3)
    
    def _render_checkmark(self, painter: QPainter, x: float, y: float, size: float):
        """Render a checkmark."""
        pen = QPen(self.colors['text'], 3)
        painter.setPen(pen)
        
        # Simple checkmark
        points = [
            (x - size * 0.3, y),
            (x - size * 0.1, y + size * 0.2),
            (x + size * 0.3, y - size * 0.2)
        ]
        
        for i in range(len(points) - 1):
            painter.drawLine(
                int(points[i][0]), int(points[i][1]),
                int(points[i + 1][0]), int(points[i + 1][1])
            )
    
    def _render_key_sequence(self, painter: QPainter, sequence: List[str], progress: dict):
        """Render the key sequence for key speed test."""
        if not sequence:
            return
        
        # Calculate positions
        widget_rect = self.widget.rect()
        center_x = widget_rect.width() // 2
        center_y = widget_rect.height() // 2
        
        key_size = 60
        spacing = 80
        start_x = center_x - (len(sequence) - 1) * spacing // 2
        
        for i, key in enumerate(sequence):
            x = start_x + i * spacing
            y = center_y
            
            # Highlight current key
            if i == progress.get('current_key_index', 0):
                self._render_highlighted_key(painter, x, y, key_size, key)
            else:
                self._render_key(painter, x, y, key_size, key)
    
    def _render_key(self, painter: QPainter, x: float, y: float, size: float, key: str):
        """Render a single key."""
        pen = QPen(self.colors['text'], 2)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.colors['background']))
        
        # Key rectangle
        rect = QRectF(x - size // 2, y - size // 2, size, size)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Key text
        painter.setFont(self.fonts['title'])
        painter.setPen(QPen(self.colors['text']))
        painter.drawText(rect, key.upper(), QPainter.AlignCenter)
    
    def _render_highlighted_key(self, painter: QPainter, x: float, y: float, size: float, key: str):
        """Render a highlighted key."""
        # Pulsing effect
        pulse = 1.0 + 0.3 * math.sin(self.pulse_phase * 2)
        size = size * pulse
        
        pen = QPen(self.colors['score'], 3)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.colors['score']))
        
        # Key rectangle
        rect = QRectF(x - size // 2, y - size // 2, size, size)
        painter.drawRoundedRect(rect, 8, 8)
        
        # Key text
        painter.setFont(self.fonts['title'])
        painter.setPen(QPen(self.colors['background']))
        painter.drawText(rect, key.upper(), QPainter.AlignCenter)
    
    def _render_stimulus(self, painter: QPainter):
        """Render the reaction test stimulus."""
        widget_rect = self.widget.rect()
        center_x = widget_rect.width() // 2
        center_y = widget_rect.height() // 2
        
        # Pulsing circle
        pulse = 1.0 + 0.5 * math.sin(self.pulse_phase * 3)
        size = 100 * pulse
        
        pen = QPen(self.colors['stimulus'], 5)
        painter.setPen(pen)
        painter.setBrush(QBrush(self.colors['stimulus']))
        
        x = center_x - size // 2
        y = center_y - size // 2
        painter.drawEllipse(x, y, size, size)
    
    def _render_aim_ui(self, painter: QPainter, progress: dict):
        """Render aim test UI elements."""
        self._render_progress_bar(painter, progress)
        self._render_score(painter, progress.get('current_score', 0.0))
        self._render_stats(painter, progress, ['hits', 'misses'])
    
    def _render_key_speed_ui(self, painter: QPainter, progress: dict):
        """Render key speed test UI elements."""
        self._render_progress_bar(painter, progress)
        self._render_score(painter, progress.get('current_score', 0.0))
        self._render_stats(painter, progress, ['correct_keys', 'total_keys'])
    
    def _render_reaction_ui(self, painter: QPainter, progress: dict):
        """Render reaction test UI elements."""
        self._render_progress_bar(painter, progress)
        self._render_score(painter, progress.get('current_score', 0.0))
        self._render_stats(painter, progress, ['total_responses', 'false_starts'])
        
        # Show waiting message
        if progress.get('waiting_for_stimulus', False):
            self._render_waiting_message(painter)
    
    def _render_progress_bar(self, painter: QPainter, progress: dict):
        """Render the progress bar."""
        widget_rect = self.widget.rect()
        bar_width = widget_rect.width() - 40
        bar_height = 20
        bar_x = 20
        bar_y = widget_rect.height() - 40
        
        # Background
        painter.setPen(QPen(self.colors['text'], 2))
        painter.setBrush(QBrush(self.colors['background']))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 10, 10)
        
        # Progress
        progress_percent = progress.get('progress_percent', 0.0) / 100.0
        progress_width = int(bar_width * progress_percent)
        
        painter.setBrush(QBrush(self.colors['progress']))
        painter.drawRoundedRect(bar_x, bar_y, progress_width, bar_height, 10, 10)
        
        # Time remaining
        remaining = progress.get('remaining_time', 0.0)
        time_text = f"Time: {remaining:.1f}s"
        painter.setFont(self.fonts['small'])
        painter.setPen(QPen(self.colors['text']))
        painter.drawText(bar_x + bar_width + 10, bar_y + bar_height // 2 + 5, time_text)
    
    def _render_score(self, painter: QPainter, score: float):
        """Render the current score."""
        widget_rect = self.widget.rect()
        x = 20
        y = 50
        
        painter.setFont(self.fonts['score'])
        painter.setPen(QPen(self.colors['score']))
        painter.drawText(x, y, f"Score: {score:.1f}")
    
    def _render_stats(self, painter: QPainter, progress: dict, stat_keys: List[str]):
        """Render statistics."""
        widget_rect = self.widget.rect()
        x = 20
        y = 80
        
        painter.setFont(self.fonts['info'])
        painter.setPen(QPen(self.colors['text']))
        
        for i, key in enumerate(stat_keys):
            value = progress.get(key, 0)
            text = f"{key.replace('_', ' ').title()}: {value}"
            painter.drawText(x, y + i * 20, text)
    
    def _render_waiting_message(self, painter: QPainter):
        """Render waiting message for reaction test."""
        widget_rect = self.widget.rect()
        center_x = widget_rect.width() // 2
        center_y = widget_rect.height() // 2 + 100
        
        painter.setFont(self.fonts['title'])
        painter.setPen(QPen(self.colors['text']))
        
        # Pulsing text
        alpha = int(128 + 127 * math.sin(self.pulse_phase))
        color = QColor(self.colors['text'])
        color.setAlpha(alpha)
        painter.setPen(QPen(color))
        
        painter.drawText(center_x - 100, center_y, "Wait for the stimulus...")
    
    def _update_animations(self):
        """Update animation phases."""
        self.pulse_phase += 0.1
        self.fade_phase += 0.05
        
        # Keep phases in reasonable range
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase -= 2 * math.pi
        if self.fade_phase > 2 * math.pi:
            self.fade_phase -= 2 * math.pi
        
        self.update_required.emit()
    
    def add_animation(self, animation_type: str, duration: float, **kwargs):
        """Add a new animation."""
        animation = {
            'type': animation_type,
            'start_time': time.time(),
            'duration': duration,
            'data': kwargs
        }
        self.animations.append(animation)
    
    def clear_animations(self):
        """Clear all animations."""
        self.animations.clear()
