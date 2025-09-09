"""
Macro System for ZeroLag

This module provides comprehensive macro recording, playback, and editing functionality
for ZeroLag gaming input optimization.

Components:
- MacroRecorder: High-precision macro recording with event filtering
- MacroPlayer: Advanced macro playback with timing control and loops
- MacroEditor: Visual timeline-based macro editing with undo/redo
- MacroManager: Centralized macro management with libraries and profiles

Features:
- High-precision timing (microsecond accuracy)
- Event filtering and optimization
- Loop execution and conditional logic
- Visual timeline editing
- Undo/redo functionality
- Macro libraries and profiles
- Search and filtering
- Import/export capabilities
- Version control and backup
- Performance monitoring
- Integration with input handlers

Usage:
    from src.core.macro import MacroManager, MacroRecorder, MacroPlayer, MacroEditor
    
    # Create macro manager
    manager = MacroManager()
    
    # Start recording
    manager.start_recording("My Macro", "A test macro")
    
    # Stop recording and save
    macro = manager.stop_recording("My Macro", "My Library")
    
    # Play macro
    manager.start_playback("My Library", "My Macro")
    
    # Edit macro
    manager.start_editing("My Library", "My Macro")
"""

from .macro_recorder import (
    MacroRecorder,
    MacroRecording,
    MacroEvent,
    MacroEventType,
    MacroLoop,
    MacroLoopType,
    MacroRecorderConfig,
    MacroRecorderStats
)
from .macro_player import (
    MacroPlayer,
    PlaybackState,
    PlaybackError,
    PlaybackConfig,
    PlaybackStats
)
from .macro_editor import (
    MacroEditor,
    EditorMode,
    EventAction,
    EditorConfig,
    EditorState,
    EditorHistory
)
from .macro_manager import (
    MacroManager,
    MacroCategory,
    MacroStatus,
    MacroProfile,
    MacroLibrary,
    MacroManagerConfig,
    MacroManagerStats
)

__all__ = [
    # Core components
    'MacroRecorder',
    'MacroPlayer', 
    'MacroEditor',
    'MacroManager',
    
    # Data structures
    'MacroRecording',
    'MacroEvent',
    'MacroEventType',
    'MacroLoop',
    'MacroLoopType',
    'MacroProfile',
    'MacroLibrary',
    
    # Enums
    'PlaybackState',
    'PlaybackError',
    'EditorMode',
    'EventAction',
    'MacroCategory',
    'MacroStatus',
    
    # Configurations
    'MacroRecorderConfig',
    'PlaybackConfig',
    'EditorConfig',
    'MacroManagerConfig',
    
    # Statistics
    'MacroRecorderStats',
    'PlaybackStats',
    'MacroManagerStats',
    
    # Editor state
    'EditorState',
    'EditorHistory'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Comprehensive macro system for ZeroLag gaming input optimization"
