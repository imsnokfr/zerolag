"""
Macro Editor for ZeroLag

This module implements a comprehensive macro editor with timeline view including:
- Visual timeline interface for macro editing
- Event manipulation (add, edit, delete, reorder)
- Timing adjustment and precision control
- Loop editing and management
- Conditional logic editing
- Text input editing
- Comment management
- Undo/redo functionality
- Real-time preview

Features:
- Timeline-based visual editing
- Drag-and-drop event reordering
- Precise timing adjustment
- Loop visualization and editing
- Conditional logic builder
- Text input editor
- Comment system
- Undo/redo with history
- Real-time preview
- Export/import functionality
"""

import time
import json
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import copy

from .macro_recorder import MacroRecording, MacroEvent, MacroEventType, MacroLoop, MacroLoopType


class EditorMode(Enum):
    """Macro editor modes."""
    VIEW = "view"
    EDIT = "edit"
    TIMING = "timing"
    LOOP = "loop"
    CONDITIONAL = "conditional"


class EventAction(Enum):
    """Event editing actions."""
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"
    PASTE = "paste"
    DUPLICATE = "duplicate"


@dataclass
class EditorConfig:
    """Configuration for macro editor."""
    enabled: bool = True
    timeline_zoom: float = 1.0  # Timeline zoom level
    timeline_precision_ms: float = 1.0  # Minimum timing precision
    snap_to_grid: bool = True  # Snap events to grid
    grid_size_ms: float = 10.0  # Grid size in milliseconds
    max_undo_levels: int = 50  # Maximum undo levels
    auto_save_interval: float = 30.0  # Auto-save interval
    enable_preview: bool = True  # Enable real-time preview
    enable_validation: bool = True  # Enable event validation


@dataclass
class EditorState:
    """Current editor state."""
    mode: EditorMode = EditorMode.VIEW
    selected_events: List[int] = field(default_factory=list)
    selected_loop: Optional[str] = None
    cursor_position: float = 0.0  # Timeline cursor position
    view_start: float = 0.0  # Timeline view start
    view_end: float = 10.0  # Timeline view end
    zoom_level: float = 1.0
    grid_enabled: bool = True
    snap_enabled: bool = True


@dataclass
class EditorHistory:
    """Editor history for undo/redo."""
    action: EventAction
    timestamp: float
    description: str
    data: Dict[str, Any]  # Action-specific data
    before_state: Optional[MacroRecording] = None
    after_state: Optional[MacroRecording] = None


class MacroEditor:
    """
    Comprehensive macro editor with timeline view.
    
    Provides visual editing capabilities for macro recordings with
    timeline-based interface and advanced editing features.
    """
    
    def __init__(self, config: Optional[EditorConfig] = None):
        """
        Initialize macro editor.
        
        Args:
            config: Editor configuration
        """
        self.config = config or EditorConfig()
        self.current_recording: Optional[MacroRecording] = None
        self.editor_state = EditorState()
        self.history: List[EditorHistory] = []
        self.history_index = -1
        self.auto_save_timer = None
        
        # Callbacks
        self.change_callbacks: List[Callable[[MacroRecording], None]] = []
        self.selection_callbacks: List[Callable[[List[int]], None]] = []
        self.mode_callbacks: List[Callable[[EditorMode], None]] = []
        
        # Validation
        self.validators: Dict[MacroEventType, Callable[[MacroEvent], bool]] = {
            MacroEventType.KEY_PRESS: self._validate_key_event,
            MacroEventType.KEY_RELEASE: self._validate_key_event,
            MacroEventType.MOUSE_MOVE: self._validate_mouse_event,
            MacroEventType.MOUSE_CLICK: self._validate_mouse_event,
            MacroEventType.MOUSE_PRESS: self._validate_mouse_event,
            MacroEventType.MOUSE_RELEASE: self._validate_mouse_event,
            MacroEventType.MOUSE_SCROLL: self._validate_mouse_event,
            MacroEventType.DELAY: self._validate_delay_event,
            MacroEventType.TEXT_INPUT: self._validate_text_event,
            MacroEventType.MACRO_CALL: self._validate_macro_call_event,
            MacroEventType.CONDITIONAL: self._validate_conditional_event,
            MacroEventType.COMMENT: self._validate_comment_event
        }
    
    def load_recording(self, recording: MacroRecording) -> bool:
        """
        Load a recording for editing.
        
        Args:
            recording: Recording to load
            
        Returns:
            True if loaded successfully
        """
        try:
            self.current_recording = copy.deepcopy(recording)
            self.editor_state = EditorState()
            self.history.clear()
            self.history_index = -1
            
            # Start auto-save timer
            if self.config.auto_save_interval > 0:
                self._start_auto_save_timer()
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading recording: {e}")
            return False
    
    def save_recording(self) -> Optional[MacroRecording]:
        """
        Save the current recording.
        
        Returns:
            Current recording or None if error
        """
        if not self.current_recording:
            return None
        
        try:
            # Update metadata
            self.current_recording.modified_at = time.time()
            
            # Validate recording
            if self.config.enable_validation:
                if not self._validate_recording():
                    logging.warning("Recording validation failed")
            
            return copy.deepcopy(self.current_recording)
            
        except Exception as e:
            logging.error(f"Error saving recording: {e}")
            return None
    
    def add_event(self, event: MacroEvent, index: Optional[int] = None) -> bool:
        """
        Add an event to the recording.
        
        Args:
            event: Event to add
            index: Insertion index (None for end)
            
        Returns:
            True if added successfully
        """
        if not self.current_recording:
            return False
        
        try:
            # Validate event
            if self.config.enable_validation:
                if not self._validate_event(event):
                    return False
            
            # Add to history
            self._add_to_history(EventAction.ADD, f"Add {event.event_type.value} event", {
                'event': event,
                'index': index
            })
            
            # Insert event
            if index is None:
                self.current_recording.events.append(event)
            else:
                self.current_recording.events.insert(index, event)
            
            # Update recording metadata
            self._update_recording_metadata()
            
            # Trigger callbacks
            self._trigger_change_callbacks()
            
            return True
            
        except Exception as e:
            logging.error(f"Error adding event: {e}")
            return False
    
    def edit_event(self, index: int, event: MacroEvent) -> bool:
        """
        Edit an event in the recording.
        
        Args:
            index: Event index
            event: New event data
            
        Returns:
            True if edited successfully
        """
        if not self.current_recording or index >= len(self.current_recording.events):
            return False
        
        try:
            # Validate event
            if self.config.enable_validation:
                if not self._validate_event(event):
                    return False
            
            # Add to history
            old_event = self.current_recording.events[index]
            self._add_to_history(EventAction.EDIT, f"Edit {event.event_type.value} event", {
                'index': index,
                'old_event': old_event,
                'new_event': event
            })
            
            # Update event
            self.current_recording.events[index] = event
            
            # Update recording metadata
            self._update_recording_metadata()
            
            # Trigger callbacks
            self._trigger_change_callbacks()
            
            return True
            
        except Exception as e:
            logging.error(f"Error editing event: {e}")
            return False
    
    def delete_event(self, index: int) -> bool:
        """
        Delete an event from the recording.
        
        Args:
            index: Event index to delete
            
        Returns:
            True if deleted successfully
        """
        if not self.current_recording or index >= len(self.current_recording.events):
            return False
        
        try:
            # Add to history
            event = self.current_recording.events[index]
            self._add_to_history(EventAction.DELETE, f"Delete {event.event_type.value} event", {
                'index': index,
                'event': event
            })
            
            # Delete event
            del self.current_recording.events[index]
            
            # Update recording metadata
            self._update_recording_metadata()
            
            # Trigger callbacks
            self._trigger_change_callbacks()
            
            return True
            
        except Exception as e:
            logging.error(f"Error deleting event: {e}")
            return False
    
    def move_event(self, from_index: int, to_index: int) -> bool:
        """
        Move an event to a new position.
        
        Args:
            from_index: Source index
            to_index: Destination index
            
        Returns:
            True if moved successfully
        """
        if not self.current_recording:
            return False
        
        if (from_index >= len(self.current_recording.events) or 
            to_index >= len(self.current_recording.events) or
            from_index == to_index):
            return False
        
        try:
            # Add to history
            event = self.current_recording.events[from_index]
            self._add_to_history(EventAction.MOVE, f"Move {event.event_type.value} event", {
                'from_index': from_index,
                'to_index': to_index,
                'event': event
            })
            
            # Move event
            event = self.current_recording.events.pop(from_index)
            self.current_recording.events.insert(to_index, event)
            
            # Update recording metadata
            self._update_recording_metadata()
            
            # Trigger callbacks
            self._trigger_change_callbacks()
            
            return True
            
        except Exception as e:
            logging.error(f"Error moving event: {e}")
            return False
    
    def duplicate_event(self, index: int) -> bool:
        """
        Duplicate an event.
        
        Args:
            index: Event index to duplicate
            
        Returns:
            True if duplicated successfully
        """
        if not self.current_recording or index >= len(self.current_recording.events):
            return False
        
        try:
            # Get original event
            original_event = self.current_recording.events[index]
            
            # Create duplicate
            duplicate_event = MacroEvent(
                event_type=original_event.event_type,
                timestamp=original_event.timestamp + 0.1,  # Offset slightly
                data=copy.deepcopy(original_event.data),
                duration=original_event.duration,
                loop_id=original_event.loop_id,
                comment=original_event.comment
            )
            
            # Add duplicate
            return self.add_event(duplicate_event, index + 1)
            
        except Exception as e:
            logging.error(f"Error duplicating event: {e}")
            return False
    
    def adjust_timing(self, index: int, new_timestamp: float) -> bool:
        """
        Adjust event timing.
        
        Args:
            index: Event index
            new_timestamp: New timestamp
            
        Returns:
            True if adjusted successfully
        """
        if not self.current_recording or index >= len(self.current_recording.events):
            return False
        
        try:
            # Snap to grid if enabled
            if self.editor_state.snap_enabled:
                new_timestamp = self._snap_to_grid(new_timestamp)
            
            # Get original event
            original_event = self.current_recording.events[index]
            
            # Create updated event
            updated_event = MacroEvent(
                event_type=original_event.event_type,
                timestamp=new_timestamp,
                data=original_event.data,
                duration=original_event.duration,
                loop_id=original_event.loop_id,
                comment=original_event.comment
            )
            
            # Update event
            return self.edit_event(index, updated_event)
            
        except Exception as e:
            logging.error(f"Error adjusting timing: {e}")
            return False
    
    def create_loop(self, start_index: int, end_index: int, loop_type: MacroLoopType, 
                   count: Optional[int] = None, condition: Optional[str] = None) -> bool:
        """
        Create a loop in the recording.
        
        Args:
            start_index: Loop start event index
            end_index: Loop end event index
            loop_type: Type of loop
            count: Loop count (for COUNT loops)
            condition: Loop condition (for WHILE/UNTIL loops)
            
        Returns:
            True if created successfully
        """
        if not self.current_recording:
            return False
        
        if start_index >= end_index or end_index >= len(self.current_recording.events):
            return False
        
        try:
            # Generate loop ID
            loop_id = f"loop_{int(time.time())}"
            
            # Create loop
            loop = MacroLoop(
                loop_id=loop_id,
                loop_type=loop_type,
                count=count,
                condition=condition,
                start_event_index=start_index,
                end_event_index=end_index,
                current_iteration=0,
                max_iterations=count or 0
            )
            
            # Add loop to recording
            self.current_recording.loops[loop_id] = loop
            
            # Add loop start event
            loop_start_event = MacroEvent(
                event_type=MacroEventType.LOOP_START,
                timestamp=self.current_recording.events[start_index].timestamp,
                data={
                    'loop_id': loop_id,
                    'loop_type': loop_type.value,
                    'count': count,
                    'condition': condition
                },
                loop_id=loop_id
            )
            
            # Add loop end event
            loop_end_event = MacroEvent(
                event_type=MacroEventType.LOOP_END,
                timestamp=self.current_recording.events[end_index].timestamp,
                data={'loop_id': loop_id},
                loop_id=loop_id
            )
            
            # Insert loop events
            self.add_event(loop_start_event, start_index)
            self.add_event(loop_end_event, end_index + 1)
            
            return True
            
        except Exception as e:
            logging.error(f"Error creating loop: {e}")
            return False
    
    def delete_loop(self, loop_id: str) -> bool:
        """
        Delete a loop from the recording.
        
        Args:
            loop_id: Loop ID to delete
            
        Returns:
            True if deleted successfully
        """
        if not self.current_recording or loop_id not in self.current_recording.loops:
            return False
        
        try:
            loop = self.current_recording.loops[loop_id]
            
            # Remove loop events
            events_to_remove = []
            for i, event in enumerate(self.current_recording.events):
                if (event.event_type in [MacroEventType.LOOP_START, MacroEventType.LOOP_END] and
                    event.data.get('loop_id') == loop_id):
                    events_to_remove.append(i)
            
            # Remove events in reverse order
            for i in reversed(events_to_remove):
                self.delete_event(i)
            
            # Remove loop
            del self.current_recording.loops[loop_id]
            
            return True
            
        except Exception as e:
            logging.error(f"Error deleting loop: {e}")
            return False
    
    def set_selection(self, event_indices: List[int]):
        """
        Set selected events.
        
        Args:
            event_indices: List of event indices to select
        """
        self.editor_state.selected_events = event_indices
        self._trigger_selection_callbacks()
    
    def set_mode(self, mode: EditorMode):
        """
        Set editor mode.
        
        Args:
            mode: New editor mode
        """
        self.editor_state.mode = mode
        self._trigger_mode_callbacks()
    
    def set_cursor_position(self, position: float):
        """
        Set timeline cursor position.
        
        Args:
            position: Cursor position in seconds
        """
        self.editor_state.cursor_position = position
    
    def set_view_range(self, start: float, end: float):
        """
        Set timeline view range.
        
        Args:
            start: View start time
            end: View end time
        """
        self.editor_state.view_start = start
        self.editor_state.view_end = end
    
    def set_zoom(self, zoom_level: float):
        """
        Set timeline zoom level.
        
        Args:
            zoom_level: Zoom level (0.1 to 10.0)
        """
        self.editor_state.zoom_level = max(0.1, min(10.0, zoom_level))
        self.config.timeline_zoom = self.editor_state.zoom_level
    
    def undo(self) -> bool:
        """
        Undo last action.
        
        Returns:
            True if undo successful
        """
        if self.history_index < 0:
            return False
        
        try:
            history_item = self.history[self.history_index]
            
            # Restore previous state
            if history_item.before_state:
                self.current_recording = copy.deepcopy(history_item.before_state)
            
            # Move history index
            self.history_index -= 1
            
            # Trigger callbacks
            self._trigger_change_callbacks()
            
            return True
            
        except Exception as e:
            logging.error(f"Error undoing action: {e}")
            return False
    
    def redo(self) -> bool:
        """
        Redo last undone action.
        
        Returns:
            True if redo successful
        """
        if self.history_index >= len(self.history) - 1:
            return False
        
        try:
            # Move history index
            self.history_index += 1
            
            history_item = self.history[self.history_index]
            
            # Restore next state
            if history_item.after_state:
                self.current_recording = copy.deepcopy(history_item.after_state)
            
            # Trigger callbacks
            self._trigger_change_callbacks()
            
            return True
            
        except Exception as e:
            logging.error(f"Error redoing action: {e}")
            return False
    
    def _add_to_history(self, action: EventAction, description: str, data: Dict[str, Any]):
        """Add action to history."""
        try:
            # Create history item
            history_item = EditorHistory(
                action=action,
                timestamp=time.time(),
                description=description,
                data=data,
                before_state=copy.deepcopy(self.current_recording) if self.current_recording else None
            )
            
            # Remove future history if we're not at the end
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            
            # Add to history
            self.history.append(history_item)
            self.history_index = len(self.history) - 1
            
            # Limit history size
            if len(self.history) > self.config.max_undo_levels:
                self.history = self.history[-self.config.max_undo_levels:]
                self.history_index = len(self.history) - 1
            
            # Update after state
            if self.history_index >= 0:
                self.history[self.history_index].after_state = copy.deepcopy(self.current_recording)
            
        except Exception as e:
            logging.error(f"Error adding to history: {e}")
    
    def _snap_to_grid(self, timestamp: float) -> float:
        """Snap timestamp to grid."""
        if not self.editor_state.snap_enabled:
            return timestamp
        
        grid_size = self.config.grid_size_ms / 1000.0
        return round(timestamp / grid_size) * grid_size
    
    def _update_recording_metadata(self):
        """Update recording metadata."""
        if not self.current_recording:
            return
        
        # Update event count
        self.current_recording.event_count = len(self.current_recording.events)
        
        # Update total duration
        if self.current_recording.events:
            last_event = self.current_recording.events[-1]
            self.current_recording.total_duration = last_event.timestamp
        else:
            self.current_recording.total_duration = 0.0
        
        # Update modified time
        self.current_recording.modified_at = time.time()
    
    def _validate_recording(self) -> bool:
        """Validate the entire recording."""
        if not self.current_recording:
            return False
        
        try:
            # Check events
            for event in self.current_recording.events:
                if not self._validate_event(event):
                    return False
            
            # Check loops
            for loop in self.current_recording.loops.values():
                if not self._validate_loop(loop):
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating recording: {e}")
            return False
    
    def _validate_event(self, event: MacroEvent) -> bool:
        """Validate a single event."""
        try:
            validator = self.validators.get(event.event_type)
            if validator:
                return validator(event)
            return True
            
        except Exception as e:
            logging.error(f"Error validating event: {e}")
            return False
    
    def _validate_loop(self, loop: MacroLoop) -> bool:
        """Validate a loop."""
        try:
            # Check loop bounds
            if (loop.start_event_index < 0 or 
                loop.end_event_index >= len(self.current_recording.events) or
                loop.start_event_index >= loop.end_event_index):
                return False
            
            # Check loop type specific validation
            if loop.loop_type == MacroLoopType.COUNT and (loop.count is None or loop.count <= 0):
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error validating loop: {e}")
            return False
    
    def _validate_key_event(self, event: MacroEvent) -> bool:
        """Validate key event."""
        return 'key' in event.data and 'key_code' in event.data
    
    def _validate_mouse_event(self, event: MacroEvent) -> bool:
        """Validate mouse event."""
        return 'x' in event.data and 'y' in event.data
    
    def _validate_delay_event(self, event: MacroEvent) -> bool:
        """Validate delay event."""
        delay_ms = event.data.get('delay_ms', 0)
        return isinstance(delay_ms, (int, float)) and delay_ms >= 0
    
    def _validate_text_event(self, event: MacroEvent) -> bool:
        """Validate text input event."""
        return 'text' in event.data and isinstance(event.data['text'], str)
    
    def _validate_macro_call_event(self, event: MacroEvent) -> bool:
        """Validate macro call event."""
        return 'macro_name' in event.data and isinstance(event.data['macro_name'], str)
    
    def _validate_conditional_event(self, event: MacroEvent) -> bool:
        """Validate conditional event."""
        return 'condition' in event.data and 'action' in event.data
    
    def _validate_comment_event(self, event: MacroEvent) -> bool:
        """Validate comment event."""
        return True  # Comments are always valid
    
    def _start_auto_save_timer(self):
        """Start auto-save timer."""
        if self.auto_save_timer:
            self.auto_save_timer.cancel()
        
        self.auto_save_timer = threading.Timer(
            self.config.auto_save_interval,
            self._auto_save
        )
        self.auto_save_timer.start()
    
    def _auto_save(self):
        """Auto-save current recording."""
        if self.current_recording:
            try:
                # Save to temporary file
                filename = f"macro_edit_temp_{self.current_recording.name}_{int(time.time())}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.current_recording.to_dict(), f, indent=2)
                
                # Restart timer
                self._start_auto_save_timer()
                
            except Exception as e:
                logging.error(f"Error in auto-save: {e}")
    
    def _trigger_change_callbacks(self):
        """Trigger change callbacks."""
        for callback in self.change_callbacks:
            try:
                callback(self.current_recording)
            except Exception as e:
                logging.error(f"Error in change callback: {e}")
    
    def _trigger_selection_callbacks(self):
        """Trigger selection callbacks."""
        for callback in self.selection_callbacks:
            try:
                callback(self.editor_state.selected_events)
            except Exception as e:
                logging.error(f"Error in selection callback: {e}")
    
    def _trigger_mode_callbacks(self):
        """Trigger mode callbacks."""
        for callback in self.mode_callbacks:
            try:
                callback(self.editor_state.mode)
            except Exception as e:
                logging.error(f"Error in mode callback: {e}")
    
    def add_change_callback(self, callback: Callable[[MacroRecording], None]):
        """Add callback for recording changes."""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[MacroRecording], None]):
        """Remove change callback."""
        try:
            self.change_callbacks.remove(callback)
        except ValueError:
            pass
    
    def add_selection_callback(self, callback: Callable[[List[int]], None]):
        """Add callback for selection changes."""
        self.selection_callbacks.append(callback)
    
    def remove_selection_callback(self, callback: Callable[[List[int]], None]):
        """Remove selection callback."""
        try:
            self.selection_callbacks.remove(callback)
        except ValueError:
            pass
    
    def add_mode_callback(self, callback: Callable[[EditorMode], None]):
        """Add callback for mode changes."""
        self.mode_callbacks.append(callback)
    
    def remove_mode_callback(self, callback: Callable[[EditorMode], None]):
        """Remove mode callback."""
        try:
            self.mode_callbacks.remove(callback)
        except ValueError:
            pass
    
    def get_current_recording(self) -> Optional[MacroRecording]:
        """Get current recording."""
        return self.current_recording
    
    def get_editor_state(self) -> EditorState:
        """Get current editor state."""
        return self.editor_state
    
    def get_history(self) -> List[EditorHistory]:
        """Get editor history."""
        return self.history.copy()
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return self.history_index >= 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return self.history_index < len(self.history) - 1


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create macro editor
    config = EditorConfig(
        enabled=True,
        timeline_zoom=1.0,
        timeline_precision_ms=1.0,
        snap_to_grid=True,
        grid_size_ms=10.0,
        max_undo_levels=50,
        auto_save_interval=30.0,
        enable_preview=True,
        enable_validation=True
    )
    
    editor = MacroEditor(config)
    
    # Add callbacks for testing
    def change_callback(recording: MacroRecording):
        print(f"Recording changed: {recording.name} ({recording.event_count} events)")
    
    def selection_callback(selected_events: List[int]):
        print(f"Selection changed: {selected_events}")
    
    def mode_callback(mode: EditorMode):
        print(f"Mode changed: {mode.value}")
    
    editor.add_change_callback(change_callback)
    editor.add_selection_callback(selection_callback)
    editor.add_mode_callback(mode_callback)
    
    print("Testing Macro Editor...")
    
    # Create a test recording
    from .macro_recorder import MacroRecording, MacroEvent, MacroEventType
    
    test_recording = MacroRecording(
        name="Test Edit",
        description="A test recording for editing demonstration"
    )
    
    # Add some test events
    test_recording.events = [
        MacroEvent(MacroEventType.KEY_PRESS, 0.0, {'key': 'w', 'key_code': 87}),
        MacroEvent(MacroEventType.DELAY, 0.1, {'delay_ms': 100}),
        MacroEvent(MacroEventType.KEY_RELEASE, 0.2, {'key': 'w', 'key_code': 87}),
        MacroEvent(MacroEventType.MOUSE_MOVE, 0.3, {'x': 100, 'y': 100}),
        MacroEvent(MacroEventType.MOUSE_CLICK, 0.4, {'button': 'left', 'x': 100, 'y': 100}),
        MacroEvent(MacroEventType.TEXT_INPUT, 0.5, {'text': 'Hello, World!'}),
        MacroEvent(MacroEventType.COMMENT, 0.6, comment="Test comment")
    ]
    
    test_recording.event_count = len(test_recording.events)
    test_recording.total_duration = 0.6
    
    # Load recording
    if editor.load_recording(test_recording):
        print("✓ Recording loaded")
        
        # Test editing operations
        print("Testing event editing...")
        
        # Add a new event
        new_event = MacroEvent(MacroEventType.KEY_PRESS, 0.7, {'key': 'space', 'key_code': 32})
        if editor.add_event(new_event):
            print("✓ Event added")
        
        # Edit an event
        edited_event = MacroEvent(MacroEventType.KEY_PRESS, 0.0, {'key': 'a', 'key_code': 65})
        if editor.edit_event(0, edited_event):
            print("✓ Event edited")
        
        # Delete an event
        if editor.delete_event(1):
            print("✓ Event deleted")
        
        # Move an event
        if editor.move_event(0, 2):
            print("✓ Event moved")
        
        # Duplicate an event
        if editor.duplicate_event(0):
            print("✓ Event duplicated")
        
        # Adjust timing
        if editor.adjust_timing(0, 0.5):
            print("✓ Timing adjusted")
        
        # Test selection
        editor.set_selection([0, 1, 2])
        print("✓ Selection set")
        
        # Test mode changes
        editor.set_mode(EditorMode.EDIT)
        editor.set_mode(EditorMode.TIMING)
        editor.set_mode(EditorMode.LOOP)
        print("✓ Modes changed")
        
        # Test undo/redo
        if editor.can_undo():
            if editor.undo():
                print("✓ Undo successful")
        
        if editor.can_redo():
            if editor.redo():
                print("✓ Redo successful")
        
        # Test loop creation
        if editor.create_loop(0, 3, MacroLoopType.COUNT, count=3):
            print("✓ Loop created")
        
        # Test cursor and view
        editor.set_cursor_position(0.5)
        editor.set_view_range(0.0, 1.0)
        editor.set_zoom(2.0)
        print("✓ View settings updated")
        
        # Save recording
        saved_recording = editor.save_recording()
        if saved_recording:
            print(f"✓ Recording saved: {saved_recording.name} ({saved_recording.event_count} events)")
        
        # Get final state
        final_state = editor.get_editor_state()
        print(f"✓ Final state: mode={final_state.mode.value}, selected={len(final_state.selected_events)}")
        
    else:
        print("✗ Failed to load recording")
    
    print("\nMacro editor testing completed!")
