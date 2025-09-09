"""
ZeroLag Input Queuing Package

This package provides high-frequency input queuing and processing capabilities
for gaming peripherals with zero event loss and optimal performance.

Modules:
    - input_queue: High-frequency input event queue with priority processing
"""

from .input_queue import (
    InputQueue, QueuedEvent, QueueStats, 
    EventPriority, QueueMode
)

__all__ = [
    'InputQueue', 'QueuedEvent', 'QueueStats',
    'EventPriority', 'QueueMode'
]
