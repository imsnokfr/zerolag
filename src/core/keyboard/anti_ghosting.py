"""
Anti-Ghosting and NKRO (N-Key Rollover) Simulation for ZeroLag

This module implements advanced keyboard optimizations to prevent input drops
during complex gaming combinations and simulate N-Key Rollover functionality.

Features:
- N-Key Rollover simulation for unlimited simultaneous key presses
- Anti-ghosting algorithms to prevent key blocking
- Key combination detection and validation
- Gaming-specific key matrix optimization
- Real-time key state management
- Performance monitoring and statistics
"""

import time
import threading
from typing import Dict, List, Set, Tuple, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import logging


class KeyState(Enum):
    """Key state enumeration."""
    RELEASED = "released"
    PRESSED = "pressed"
    HELD = "held"
    BLOCKED = "blocked"  # Ghosting prevention


class GhostingType(Enum):
    """Types of ghosting that can occur."""
    NONE = "none"
    MATRIX_CONFLICT = "matrix_conflict"
    HARDWARE_LIMITATION = "hardware_limitation"
    USB_LIMITATION = "usb_limitation"
    SOFTWARE_LIMITATION = "software_limitation"


@dataclass
class KeyInfo:
    """Information about a key state."""
    key_code: int
    key_name: str
    state: KeyState
    press_time: float
    release_time: Optional[float] = None
    hold_duration: float = 0.0
    press_count: int = 0
    is_ghosted: bool = False
    ghosting_type: Optional[GhostingType] = None
    last_activity: float = 0.0


@dataclass
class KeyCombination:
    """Represents a combination of keys."""
    keys: Set[str]
    name: str
    priority: int = 0
    is_gaming_combo: bool = False
    max_keys: int = 0  # 0 = unlimited (NKRO)
    created_time: float = 0.0


@dataclass
class AntiGhostingStats:
    """Statistics for anti-ghosting system."""
    total_keys_tracked: int = 0
    simultaneous_keys_max: int = 0
    ghosting_events_prevented: int = 0
    nkro_events_processed: int = 0
    key_combinations_detected: int = 0
    blocked_keys: int = 0
    processing_time_ms: float = 0.0
    last_update_time: float = 0.0


class KeyMatrix:
    """
    Represents the physical key matrix for ghosting detection.
    
    Many keyboards use a matrix layout where certain key combinations
    can cause ghosting due to electrical conflicts.
    """
    
    def __init__(self, rows: int = 6, cols: int = 22):
        """
        Initialize key matrix.
        
        Args:
            rows: Number of matrix rows
            cols: Number of matrix columns
        """
        self.rows = rows
        self.cols = cols
        self.matrix = [[False for _ in range(cols)] for _ in range(rows)]
        self.key_mappings: Dict[str, Tuple[int, int]] = {}
        self.conflict_groups: List[Set[str]] = []
        
        # Initialize common key mappings (simplified)
        self._initialize_key_mappings()
    
    def _initialize_key_mappings(self):
        """Initialize common key to matrix position mappings."""
        # This is a simplified mapping - real keyboards have complex matrices
        common_keys = [
            'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l',
            'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',
            'z', 'x', 'c', 'v', 'b', 'n', 'm',
            'space', 'shift', 'ctrl', 'alt', 'tab', 'enter',
            '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6',
            'f7', 'f8', 'f9', 'f10', 'f11', 'f12'
        ]
        
        for i, key in enumerate(common_keys):
            if i < self.rows * self.cols:
                row = i // self.cols
                col = i % self.cols
                self.key_mappings[key] = (row, col)
    
    def set_key_state(self, key: str, pressed: bool) -> bool:
        """
        Set key state in matrix.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            
        Returns:
            True if state was set, False if key not found
        """
        if key not in self.key_mappings:
            return False
        
        row, col = self.key_mappings[key]
        self.matrix[row][col] = pressed
        return True
    
    def detect_ghosting(self, pressed_keys: Set[str]) -> List[Tuple[str, str, str]]:
        """
        Detect potential ghosting conflicts.
        
        Args:
            pressed_keys: Set of currently pressed keys
            
        Returns:
            List of (key1, key2, key3) tuples that could cause ghosting
        """
        conflicts = []
        
        # Check for 3-key ghosting patterns
        for key1 in pressed_keys:
            for key2 in pressed_keys:
                if key1 >= key2:
                    continue
                for key3 in pressed_keys:
                    if key3 <= key2:
                        continue
                    
                    if self._check_ghosting_pattern(key1, key2, key3):
                        conflicts.append((key1, key2, key3))
        
        return conflicts
    
    def _check_ghosting_pattern(self, key1: str, key2: str, key3: str) -> bool:
        """
        Check if three keys form a ghosting pattern.
        
        Ghosting occurs when three keys form a rectangle in the matrix,
        causing a fourth key to appear pressed even when it's not.
        """
        if not all(k in self.key_mappings for k in [key1, key2, key3]):
            return False
        
        pos1 = self.key_mappings[key1]
        pos2 = self.key_mappings[key2]
        pos3 = self.key_mappings[key3]
        
        # Check if keys form a rectangle (simplified check)
        # In a real implementation, this would check the actual matrix layout
        return (pos1[0] != pos2[0] and pos1[1] != pos2[1] and
                pos2[0] != pos3[0] and pos2[1] != pos3[1] and
                pos1[0] != pos3[0] and pos1[1] != pos3[1])


class NKROSimulator:
    """
    Simulates N-Key Rollover functionality for keyboards that don't support it natively.
    
    NKRO allows unlimited simultaneous key presses without blocking or ghosting.
    """
    
    def __init__(self, max_keys: int = 0):
        """
        Initialize NKRO simulator.
        
        Args:
            max_keys: Maximum simultaneous keys (0 = unlimited)
        """
        self.max_keys = max_keys  # 0 = unlimited NKRO
        self.active_keys: Set[str] = set()
        self.key_states: Dict[str, KeyInfo] = {}
        self.key_combinations: List[KeyCombination] = []
        self.callbacks: List[Callable[[str, KeyState], None]] = []
        
        # Performance tracking
        self.stats = AntiGhostingStats()
        self.processing_times = deque(maxlen=100)
        
        # Threading
        self.lock = threading.RLock()
        
        # Initialize common gaming combinations
        self._initialize_gaming_combinations()
    
    def _initialize_gaming_combinations(self):
        """Initialize common gaming key combinations."""
        gaming_combos = [
            # FPS games
            KeyCombination({'w', 'a'}, "Move Forward+Left", priority=1, is_gaming_combo=True),
            KeyCombination({'w', 'd'}, "Move Forward+Right", priority=1, is_gaming_combo=True),
            KeyCombination({'s', 'a'}, "Move Backward+Left", priority=1, is_gaming_combo=True),
            KeyCombination({'s', 'd'}, "Move Backward+Right", priority=1, is_gaming_combo=True),
            KeyCombination({'w', 'shift'}, "Sprint Forward", priority=2, is_gaming_combo=True),
            KeyCombination({'space', 'ctrl'}, "Jump+Crouch", priority=2, is_gaming_combo=True),
            
            # MOBA games
            KeyCombination({'q', 'w', 'e'}, "QWER Combo", priority=3, is_gaming_combo=True),
            KeyCombination({'a', 's', 'd'}, "ASD Combo", priority=3, is_gaming_combo=True),
            KeyCombination({'1', '2', '3'}, "Item Combo", priority=2, is_gaming_combo=True),
            
            # RTS games
            KeyCombination({'ctrl', 'a'}, "Select All", priority=1, is_gaming_combo=True),
            KeyCombination({'ctrl', 'c'}, "Copy", priority=1, is_gaming_combo=True),
            KeyCombination({'ctrl', 'v'}, "Paste", priority=1, is_gaming_combo=True),
            KeyCombination({'ctrl', 'z'}, "Undo", priority=1, is_gaming_combo=True),
            
            # Fighting games
            KeyCombination({'a', 's', 'd'}, "ASD Combo", priority=3, is_gaming_combo=True),
            KeyCombination({'q', 'w', 'e'}, "QWE Combo", priority=3, is_gaming_combo=True),
        ]
        
        self.key_combinations.extend(gaming_combos)
    
    def add_key_callback(self, callback: Callable[[str, KeyState], None]):
        """
        Add callback for key state changes.
        
        Args:
            callback: Function to call when key state changes
        """
        self.callbacks.append(callback)
    
    def remove_key_callback(self, callback: Callable[[str, KeyState], None]):
        """
        Remove key callback.
        
        Args:
            callback: Function to remove
        """
        try:
            self.callbacks.remove(callback)
        except ValueError:
            pass
    
    def process_key_event(self, key: str, pressed: bool, timestamp: Optional[float] = None) -> bool:
        """
        Process a key press/release event.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            timestamp: Event timestamp (uses current time if None)
            
        Returns:
            True if event was processed, False if blocked
        """
        if timestamp is None:
            timestamp = time.time()
        
        start_time = time.time()
        
        with self.lock:
            try:
                # Check NKRO limits
                if pressed and not self._can_press_key(key):
                    return False
                
                # Update key state
                if pressed:
                    return self._handle_key_press(key, timestamp)
                else:
                    return self._handle_key_release(key, timestamp)
                
            except Exception as e:
                logging.error(f"Error processing key event: {e}")
                return False
            finally:
                # Update processing time
                processing_time = (time.time() - start_time) * 1000
                self.processing_times.append(processing_time)
                self.stats.processing_time_ms = processing_time
                self.stats.last_update_time = timestamp
    
    def _can_press_key(self, key: str) -> bool:
        """
        Check if a key can be pressed (NKRO limits).
        
        Args:
            key: Key name
            
        Returns:
            True if key can be pressed
        """
        # If key is already pressed, allow it
        if key in self.active_keys:
            return True
        
        # Check NKRO limits
        if self.max_keys > 0 and len(self.active_keys) >= self.max_keys:
            return False
        
        return True
    
    def _handle_key_press(self, key: str, timestamp: float) -> bool:
        """
        Handle key press event.
        
        Args:
            key: Key name
            timestamp: Event timestamp
            
        Returns:
            True if event was processed
        """
        # Update key info
        if key in self.key_states:
            key_info = self.key_states[key]
            key_info.press_count += 1
            key_info.last_activity = timestamp
        else:
            key_info = KeyInfo(
                key_code=hash(key) % 1000,  # Simple key code generation
                key_name=key,
                state=KeyState.PRESSED,
                press_time=timestamp,
                press_count=1,
                last_activity=timestamp
            )
            self.key_states[key] = key_info
        
        # Add to active keys
        self.active_keys.add(key)
        key_info.state = KeyState.PRESSED
        
        # Update statistics
        self.stats.total_keys_tracked = len(self.key_states)
        self.stats.simultaneous_keys_max = max(
            self.stats.simultaneous_keys_max,
            len(self.active_keys)
        )
        self.stats.nkro_events_processed += 1
        
        # Check for key combinations
        self._detect_key_combinations()
        
        # Trigger callbacks
        self._trigger_callbacks(key, KeyState.PRESSED)
        
        return True
    
    def _handle_key_release(self, key: str, timestamp: float) -> bool:
        """
        Handle key release event.
        
        Args:
            key: Key name
            timestamp: Event timestamp
            
        Returns:
            True if event was processed
        """
        if key not in self.key_states:
            return False
        
        key_info = self.key_states[key]
        
        # Update key info
        key_info.state = KeyState.RELEASED
        key_info.release_time = timestamp
        key_info.hold_duration = timestamp - key_info.press_time
        key_info.last_activity = timestamp
        
        # Remove from active keys
        self.active_keys.discard(key)
        
        # Update statistics
        self.stats.nkro_events_processed += 1
        
        # Trigger callbacks
        self._trigger_callbacks(key, KeyState.RELEASED)
        
        return True
    
    def _detect_key_combinations(self):
        """Detect active key combinations."""
        if len(self.active_keys) < 2:
            return
        
        for combo in self.key_combinations:
            if combo.keys.issubset(self.active_keys):
                self.stats.key_combinations_detected += 1
                # Could trigger combo-specific callbacks here
    
    def _trigger_callbacks(self, key: str, state: KeyState):
        """Trigger key state change callbacks."""
        for callback in self.callbacks:
            try:
                callback(key, state)
            except Exception as e:
                logging.error(f"Error in key callback: {e}")
    
    def get_active_keys(self) -> Set[str]:
        """Get currently active keys."""
        with self.lock:
            return self.active_keys.copy()
    
    def get_key_info(self, key: str) -> Optional[KeyInfo]:
        """Get information about a specific key."""
        with self.lock:
            return self.key_states.get(key)
    
    def get_key_combinations(self) -> List[KeyCombination]:
        """Get detected key combinations."""
        with self.lock:
            active_combos = []
            for combo in self.key_combinations:
                if combo.keys.issubset(self.active_keys):
                    active_combos.append(combo)
            return active_combos
    
    def get_stats(self) -> AntiGhostingStats:
        """Get anti-ghosting statistics."""
        with self.lock:
            if self.processing_times:
                self.stats.processing_time_ms = sum(self.processing_times) / len(self.processing_times)
            return AntiGhostingStats(
                total_keys_tracked=self.stats.total_keys_tracked,
                simultaneous_keys_max=self.stats.simultaneous_keys_max,
                ghosting_events_prevented=self.stats.ghosting_events_prevented,
                nkro_events_processed=self.stats.nkro_events_processed,
                key_combinations_detected=self.stats.key_combinations_detected,
                blocked_keys=self.stats.blocked_keys,
                processing_time_ms=self.stats.processing_time_ms,
                last_update_time=self.stats.last_update_time
            )
    
    def reset_stats(self):
        """Reset statistics."""
        with self.lock:
            self.stats = AntiGhostingStats()
            self.processing_times.clear()
    
    def clear_all_keys(self):
        """Clear all key states (emergency reset)."""
        with self.lock:
            self.active_keys.clear()
            for key_info in self.key_states.values():
                key_info.state = KeyState.RELEASED
                key_info.release_time = time.time()


class AntiGhostingEngine:
    """
    Main anti-ghosting engine that coordinates NKRO simulation and ghosting prevention.
    
    Provides a unified interface for handling complex keyboard input scenarios
    in gaming applications.
    """
    
    def __init__(self, enable_nkro: bool = True, max_keys: int = 0):
        """
        Initialize anti-ghosting engine.
        
        Args:
            enable_nkro: Enable NKRO simulation
            max_keys: Maximum simultaneous keys (0 = unlimited)
        """
        self.enable_nkro = enable_nkro
        self.max_keys = max_keys
        
        # Initialize components
        self.nkro_simulator = NKROSimulator(max_keys) if enable_nkro else None
        self.key_matrix = KeyMatrix()
        
        # Configuration
        self.ghosting_prevention_enabled = True
        self.combination_detection_enabled = True
        
        # Callbacks
        self.key_callbacks: List[Callable[[str, KeyState], None]] = []
        self.combo_callbacks: List[Callable[[KeyCombination], None]] = []
        
        # Threading
        self.lock = threading.RLock()
    
    def process_key_event(self, key: str, pressed: bool, timestamp: Optional[float] = None) -> bool:
        """
        Process a key event through the anti-ghosting system.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            timestamp: Event timestamp
            
        Returns:
            True if event was processed, False if blocked
        """
        if timestamp is None:
            timestamp = time.time()
        
        with self.lock:
            try:
                # Update key matrix
                self.key_matrix.set_key_state(key, pressed)
                
                # Check for ghosting if prevention is enabled
                if self.ghosting_prevention_enabled and pressed:
                    if not self._check_ghosting_prevention(key):
                        return False
                
                # Process through NKRO simulator if enabled
                if self.nkro_simulator:
                    return self.nkro_simulator.process_key_event(key, pressed, timestamp)
                else:
                    # Basic processing without NKRO
                    return self._basic_key_processing(key, pressed, timestamp)
                
            except Exception as e:
                logging.error(f"Error in anti-ghosting engine: {e}")
                return False
    
    def _check_ghosting_prevention(self, key: str) -> bool:
        """
        Check if key press should be blocked due to ghosting prevention.
        
        Args:
            key: Key name
            
        Returns:
            True if key can be pressed
        """
        # Get currently pressed keys
        active_keys = self.nkro_simulator.get_active_keys() if self.nkro_simulator else set()
        
        # Check for ghosting patterns
        if len(active_keys) >= 3:
            conflicts = self.key_matrix.detect_ghosting(active_keys | {key})
            if conflicts:
                # Block the key to prevent ghosting
                return False
        
        return True
    
    def _basic_key_processing(self, key: str, pressed: bool, timestamp: float) -> bool:
        """
        Basic key processing without NKRO simulation.
        
        Args:
            key: Key name
            pressed: Whether key is pressed
            timestamp: Event timestamp
            
        Returns:
            True if event was processed
        """
        # Trigger callbacks
        state = KeyState.PRESSED if pressed else KeyState.RELEASED
        self._trigger_key_callbacks(key, state)
        
        return True
    
    def _trigger_key_callbacks(self, key: str, state: KeyState):
        """Trigger key state change callbacks."""
        for callback in self.key_callbacks:
            try:
                callback(key, state)
            except Exception as e:
                logging.error(f"Error in key callback: {e}")
    
    def add_key_callback(self, callback: Callable[[str, KeyState], None]):
        """
        Add key state change callback.
        
        Args:
            callback: Function to call on key state changes
        """
        self.key_callbacks.append(callback)
        if self.nkro_simulator:
            self.nkro_simulator.add_key_callback(callback)
    
    def remove_key_callback(self, callback: Callable[[str, KeyState], None]):
        """
        Remove key callback.
        
        Args:
            callback: Function to remove
        """
        try:
            self.key_callbacks.remove(callback)
        except ValueError:
            pass
        
        if self.nkro_simulator:
            self.nkro_simulator.remove_key_callback(callback)
    
    def get_active_keys(self) -> Set[str]:
        """Get currently active keys."""
        if self.nkro_simulator:
            return self.nkro_simulator.get_active_keys()
        return set()
    
    def get_key_info(self, key: str) -> Optional[KeyInfo]:
        """Get information about a specific key."""
        if self.nkro_simulator:
            return self.nkro_simulator.get_key_info(key)
        return None
    
    def get_key_combinations(self) -> List[KeyCombination]:
        """Get currently active key combinations."""
        if self.nkro_simulator:
            return self.nkro_simulator.get_key_combinations()
        return []
    
    def get_stats(self) -> AntiGhostingStats:
        """Get anti-ghosting statistics."""
        if self.nkro_simulator:
            return self.nkro_simulator.get_stats()
        return AntiGhostingStats()
    
    def reset_stats(self):
        """Reset all statistics."""
        if self.nkro_simulator:
            self.nkro_simulator.reset_stats()
    
    def clear_all_keys(self):
        """Clear all key states (emergency reset)."""
        if self.nkro_simulator:
            self.nkro_simulator.clear_all_keys()
    
    def enable_ghosting_prevention(self, enabled: bool):
        """Enable or disable ghosting prevention."""
        self.ghosting_prevention_enabled = enabled
    
    def enable_combination_detection(self, enabled: bool):
        """Enable or disable key combination detection."""
        self.combination_detection_enabled = enabled


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create anti-ghosting engine
    engine = AntiGhostingEngine(enable_nkro=True, max_keys=0)  # Unlimited NKRO
    
    # Add callback for testing
    def key_callback(key: str, state: KeyState):
        print(f"Key {key}: {state.value}")
    
    engine.add_key_callback(key_callback)
    
    print("Testing Anti-Ghosting and NKRO Simulation...")
    
    # Test basic key presses
    print("\n1. Testing basic key presses...")
    test_keys = ['w', 'a', 's', 'd', 'space', 'shift', 'ctrl']
    
    for key in test_keys:
        # Press key
        success = engine.process_key_event(key, True)
        print(f"Press {key}: {'✓' if success else '✗'}")
        
        time.sleep(0.1)
    
    # Test simultaneous keys
    print("\n2. Testing simultaneous key presses...")
    active_keys = engine.get_active_keys()
    print(f"Active keys: {active_keys}")
    
    # Test key combinations
    print("\n3. Testing key combinations...")
    combinations = engine.get_key_combinations()
    print(f"Detected combinations: {len(combinations)}")
    for combo in combinations:
        print(f"  - {combo.name}: {combo.keys}")
    
    # Test key releases
    print("\n4. Testing key releases...")
    for key in test_keys:
        success = engine.process_key_event(key, False)
        print(f"Release {key}: {'✓' if success else '✗'}")
        time.sleep(0.1)
    
    # Test NKRO limits
    print("\n5. Testing NKRO limits...")
    engine_limited = AntiGhostingEngine(enable_nkro=True, max_keys=3)
    
    test_keys_limited = ['q', 'w', 'e', 'r', 't']
    for i, key in enumerate(test_keys_limited):
        success = engine_limited.process_key_event(key, True)
        active = engine_limited.get_active_keys()
        print(f"Press {key} (limit 3): {'✓' if success else '✗'} - Active: {len(active)}")
    
    # Get statistics
    print("\n6. Statistics:")
    stats = engine.get_stats()
    print(f"Total keys tracked: {stats.total_keys_tracked}")
    print(f"Max simultaneous keys: {stats.simultaneous_keys_max}")
    print(f"NKRO events processed: {stats.nkro_events_processed}")
    print(f"Key combinations detected: {stats.key_combinations_detected}")
    print(f"Average processing time: {stats.processing_time_ms:.3f}ms")
    
    print("\nAnti-Ghosting and NKRO testing completed!")
