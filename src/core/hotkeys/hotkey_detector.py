"""
Hotkey Detector for ZeroLag

This module provides global hotkey detection using Windows API.
It handles system-wide hotkey registration and detection even when
the application is minimized or running in the background.

Features:
- Global hotkey registration using RegisterHotKey API
- Thread-safe hotkey event processing
- Support for modifier keys (Ctrl, Alt, Shift, Win)
- Hotkey conflict detection and resolution
- Low-level Windows message handling
- System-wide hotkey hooks
"""

import ctypes
import ctypes.wintypes
import threading
import time
import logging
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum, IntFlag
import queue

logger = logging.getLogger(__name__)

# Windows API constants
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

# Windows message constants
WM_HOTKEY = 0x0312
WM_QUIT = 0x0012

# Virtual key codes
VK_F1 = 0x70
VK_F2 = 0x71
VK_F3 = 0x72
VK_F4 = 0x73
VK_F5 = 0x74
VK_F6 = 0x75
VK_F7 = 0x76
VK_F8 = 0x77
VK_F9 = 0x78
VK_F10 = 0x79
VK_F11 = 0x7A
VK_F12 = 0x7B

VK_0 = 0x30
VK_1 = 0x31
VK_2 = 0x32
VK_3 = 0x33
VK_4 = 0x34
VK_5 = 0x35
VK_6 = 0x36
VK_7 = 0x37
VK_8 = 0x38
VK_9 = 0x39

VK_A = 0x41
VK_B = 0x42
VK_C = 0x43
VK_D = 0x44
VK_E = 0x45
VK_F = 0x46
VK_G = 0x47
VK_H = 0x48
VK_I = 0x49
VK_J = 0x4A
VK_K = 0x4B
VK_L = 0x4C
VK_M = 0x4D
VK_N = 0x4E
VK_O = 0x4F
VK_P = 0x50
VK_Q = 0x51
VK_R = 0x52
VK_S = 0x53
VK_T = 0x54
VK_U = 0x55
VK_V = 0x56
VK_W = 0x57
VK_X = 0x58
VK_Y = 0x59
VK_Z = 0x5A

VK_UP = 0x26
VK_DOWN = 0x28
VK_LEFT = 0x25
VK_RIGHT = 0x27
VK_SPACE = 0x20
VK_ENTER = 0x0D
VK_ESCAPE = 0x1B
VK_DELETE = 0x2E
VK_TAB = 0x09

class HotkeyModifier(IntFlag):
    """Hotkey modifier keys."""
    NONE = 0
    ALT = MOD_ALT
    CTRL = MOD_CONTROL
    SHIFT = MOD_SHIFT
    WIN = MOD_WIN

class HotkeyType(Enum):
    """Types of hotkey events."""
    PRESS = "press"
    RELEASE = "release"
    HOLD = "hold"

class HotkeyState(Enum):
    """Hotkey registration states."""
    REGISTERED = "registered"
    UNREGISTERED = "unregistered"
    CONFLICT = "conflict"
    ERROR = "error"

@dataclass
class HotkeyEvent:
    """Represents a hotkey event."""
    hotkey_id: int
    modifiers: HotkeyModifier
    virtual_key: int
    event_type: HotkeyType
    timestamp: float
    is_repeat: bool = False

class HotkeyDetector:
    """
    Global hotkey detector using Windows API.
    
    This class provides system-wide hotkey detection that works even
    when the application is minimized or running in the background.
    """
    
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Hotkey tracking
        self.registered_hotkeys: Dict[int, tuple] = {}  # id -> (modifiers, vk)
        self.hotkey_callbacks: Dict[int, Callable[[HotkeyEvent], None]] = {}
        self.next_hotkey_id = 1
        
        # Threading
        self.message_thread: Optional[threading.Thread] = None
        self.message_queue = queue.Queue()
        self.running = False
        self.lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'hotkeys_registered': 0,
            'hotkeys_unregistered': 0,
            'events_processed': 0,
            'conflicts_detected': 0,
            'errors_encountered': 0
        }
        
        logger.info("HotkeyDetector initialized")
    
    def start(self) -> bool:
        """Start the hotkey detection system."""
        with self.lock:
            if self.running:
                logger.warning("HotkeyDetector is already running")
                return True
            
            try:
                self.running = True
                self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
                self.message_thread.start()
                logger.info("HotkeyDetector started successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to start HotkeyDetector: {e}")
                self.running = False
                return False
    
    def stop(self) -> bool:
        """Stop the hotkey detection system."""
        with self.lock:
            if not self.running:
                logger.warning("HotkeyDetector is not running")
                return True
            
            try:
                self.running = False
                
                # Unregister all hotkeys
                self.unregister_all_hotkeys()
                
                # Send quit message to message loop
                if self.message_thread and self.message_thread.is_alive():
                    self.user32.PostQuitMessage(0)
                    self.message_thread.join(timeout=2.0)
                
                logger.info("HotkeyDetector stopped successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to stop HotkeyDetector: {e}")
                return False
    
    def register_hotkey(self, modifiers: HotkeyModifier, virtual_key: int, 
                       callback: Callable[[HotkeyEvent], None]) -> Optional[int]:
        """
        Register a global hotkey.
        
        Args:
            modifiers: Modifier keys (Ctrl, Alt, Shift, Win)
            virtual_key: Virtual key code
            callback: Function to call when hotkey is pressed
            
        Returns:
            Hotkey ID if successful, None if failed
        """
        with self.lock:
            try:
                hotkey_id = self.next_hotkey_id
                self.next_hotkey_id += 1
                
                # Check for conflicts
                if self._check_hotkey_conflict(modifiers, virtual_key):
                    logger.warning(f"Hotkey conflict detected: {modifiers} + {virtual_key}")
                    self.stats['conflicts_detected'] += 1
                    return None
                
                # Register with Windows API
                success = self.user32.RegisterHotKey(
                    None,  # Window handle (None for global)
                    hotkey_id,
                    int(modifiers),
                    virtual_key
                )
                
                if success:
                    self.registered_hotkeys[hotkey_id] = (modifiers, virtual_key)
                    self.hotkey_callbacks[hotkey_id] = callback
                    self.stats['hotkeys_registered'] += 1
                    logger.info(f"Registered hotkey {hotkey_id}: {modifiers} + {virtual_key}")
                    return hotkey_id
                else:
                    error_code = self.kernel32.GetLastError()
                    logger.error(f"Failed to register hotkey: Windows error {error_code}")
                    self.stats['errors_encountered'] += 1
                    return None
                    
            except Exception as e:
                logger.error(f"Error registering hotkey: {e}")
                self.stats['errors_encountered'] += 1
                return None
    
    def unregister_hotkey(self, hotkey_id: int) -> bool:
        """
        Unregister a hotkey.
        
        Args:
            hotkey_id: ID of the hotkey to unregister
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            try:
                if hotkey_id not in self.registered_hotkeys:
                    logger.warning(f"Hotkey {hotkey_id} is not registered")
                    return False
                
                success = self.user32.UnregisterHotKey(None, hotkey_id)
                
                if success:
                    del self.registered_hotkeys[hotkey_id]
                    del self.hotkey_callbacks[hotkey_id]
                    self.stats['hotkeys_unregistered'] += 1
                    logger.info(f"Unregistered hotkey {hotkey_id}")
                    return True
                else:
                    error_code = self.kernel32.GetLastError()
                    logger.error(f"Failed to unregister hotkey {hotkey_id}: Windows error {error_code}")
                    self.stats['errors_encountered'] += 1
                    return False
                    
            except Exception as e:
                logger.error(f"Error unregistering hotkey {hotkey_id}: {e}")
                self.stats['errors_encountered'] += 1
                return False
    
    def unregister_all_hotkeys(self) -> int:
        """
        Unregister all hotkeys.
        
        Returns:
            Number of hotkeys unregistered
        """
        with self.lock:
            unregistered_count = 0
            hotkey_ids = list(self.registered_hotkeys.keys())
            
            for hotkey_id in hotkey_ids:
                if self.unregister_hotkey(hotkey_id):
                    unregistered_count += 1
            
            logger.info(f"Unregistered {unregistered_count} hotkeys")
            return unregistered_count
    
    def _check_hotkey_conflict(self, modifiers: HotkeyModifier, virtual_key: int) -> bool:
        """Check if a hotkey combination conflicts with existing registrations."""
        for existing_modifiers, existing_vk in self.registered_hotkeys.values():
            if existing_modifiers == modifiers and existing_vk == virtual_key:
                return True
        return False
    
    def _message_loop(self):
        """Main message loop for processing Windows messages."""
        logger.info("Hotkey message loop started")
        
        while self.running:
            try:
                # Get message from Windows message queue
                msg = ctypes.wintypes.MSG()
                result = self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                
                if result == 0:  # WM_QUIT
                    break
                elif result == -1:  # Error
                    logger.error("GetMessage failed")
                    break
                
                # Process hotkey messages
                if msg.message == WM_HOTKEY:
                    self._process_hotkey_message(msg)
                
                # Translate and dispatch message
                self.user32.TranslateMessage(ctypes.byref(msg))
                self.user32.DispatchMessageW(ctypes.byref(msg))
                
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                self.stats['errors_encountered'] += 1
                time.sleep(0.01)  # Prevent tight error loop
        
        logger.info("Hotkey message loop ended")
    
    def _process_hotkey_message(self, msg: ctypes.wintypes.MSG):
        """Process a hotkey message from Windows."""
        try:
            hotkey_id = msg.wParam
            modifiers = HotkeyModifier(msg.lParam & 0xFFFF)
            virtual_key = (msg.lParam >> 16) & 0xFFFF
            
            if hotkey_id in self.hotkey_callbacks:
                # Create hotkey event
                event = HotkeyEvent(
                    hotkey_id=hotkey_id,
                    modifiers=modifiers,
                    virtual_key=virtual_key,
                    event_type=HotkeyType.PRESS,
                    timestamp=time.time()
                )
                
                # Call callback
                try:
                    self.hotkey_callbacks[hotkey_id](event)
                    self.stats['events_processed'] += 1
                except Exception as e:
                    logger.error(f"Error in hotkey callback {hotkey_id}: {e}")
                    self.stats['errors_encountered'] += 1
            else:
                logger.warning(f"Received hotkey message for unregistered ID: {hotkey_id}")
                
        except Exception as e:
            logger.error(f"Error processing hotkey message: {e}")
            self.stats['errors_encountered'] += 1
    
    def get_stats(self) -> Dict[str, int]:
        """Get hotkey detection statistics."""
        with self.lock:
            return self.stats.copy()
    
    def is_running(self) -> bool:
        """Check if the hotkey detector is running."""
        with self.lock:
            return self.running
    
    def get_registered_hotkeys(self) -> Dict[int, tuple]:
        """Get all registered hotkeys."""
        with self.lock:
            return self.registered_hotkeys.copy()
    
    def get_virtual_key_code(self, key_name: str) -> Optional[int]:
        """
        Get virtual key code for a key name.
        
        Args:
            key_name: Name of the key (e.g., 'F1', 'A', 'UP', 'SPACE')
            
        Returns:
            Virtual key code or None if not found
        """
        key_mapping = {
            # Function keys
            'F1': VK_F1, 'F2': VK_F2, 'F3': VK_F3, 'F4': VK_F4,
            'F5': VK_F5, 'F6': VK_F6, 'F7': VK_F7, 'F8': VK_F8,
            'F9': VK_F9, 'F10': VK_F10, 'F11': VK_F11, 'F12': VK_F12,
            
            # Number keys
            '0': VK_0, '1': VK_1, '2': VK_2, '3': VK_3, '4': VK_4,
            '5': VK_5, '6': VK_6, '7': VK_7, '8': VK_8, '9': VK_9,
            
            # Letter keys
            'A': VK_A, 'B': VK_B, 'C': VK_C, 'D': VK_D, 'E': VK_E,
            'F': VK_F, 'G': VK_G, 'H': VK_H, 'I': VK_I, 'J': VK_J,
            'K': VK_K, 'L': VK_L, 'M': VK_M, 'N': VK_N, 'O': VK_O,
            'P': VK_P, 'Q': VK_Q, 'R': VK_R, 'S': VK_S, 'T': VK_T,
            'U': VK_U, 'V': VK_V, 'W': VK_W, 'X': VK_X, 'Y': VK_Y, 'Z': VK_Z,
            
            # Special keys
            'UP': VK_UP, 'DOWN': VK_DOWN, 'LEFT': VK_LEFT, 'RIGHT': VK_RIGHT,
            'SPACE': VK_SPACE, 'ENTER': VK_ENTER, 'ESCAPE': VK_ESCAPE,
            'DELETE': VK_DELETE, 'TAB': VK_TAB
        }
        
        return key_mapping.get(key_name.upper())
    
    def get_key_name(self, virtual_key: int) -> str:
        """
        Get key name for a virtual key code.
        
        Args:
            virtual_key: Virtual key code
            
        Returns:
            Key name or 'UNKNOWN' if not found
        """
        key_mapping = {
            VK_F1: 'F1', VK_F2: 'F2', VK_F3: 'F3', VK_F4: 'F4',
            VK_F5: 'F5', VK_F6: 'F6', VK_F7: 'F7', VK_F8: 'F8',
            VK_F9: 'F9', VK_F10: 'F10', VK_F11: 'F11', VK_F12: 'F12',
            VK_0: '0', VK_1: '1', VK_2: '2', VK_3: '3', VK_4: '4',
            VK_5: '5', VK_6: '6', VK_7: '7', VK_8: '8', VK_9: '9',
            VK_A: 'A', VK_B: 'B', VK_C: 'C', VK_D: 'D', VK_E: 'E',
            VK_F: 'F', VK_G: 'G', VK_H: 'H', VK_I: 'I', VK_J: 'J',
            VK_K: 'K', VK_L: 'L', VK_M: 'M', VK_N: 'N', VK_O: 'O',
            VK_P: 'P', VK_Q: 'Q', VK_R: 'R', VK_S: 'S', VK_T: 'T',
            VK_U: 'U', VK_V: 'V', VK_W: 'W', VK_X: 'X', VK_Y: 'Y', VK_Z: 'Z',
            VK_UP: 'UP', VK_DOWN: 'DOWN', VK_LEFT: 'LEFT', VK_RIGHT: 'RIGHT',
            VK_SPACE: 'SPACE', VK_ENTER: 'ENTER', VK_ESCAPE: 'ESCAPE',
            VK_DELETE: 'DELETE', VK_TAB: 'TAB'
        }
        
        return key_mapping.get(virtual_key, 'UNKNOWN')
