"""
Memory Management Module for ZeroLag

This module provides comprehensive memory management capabilities including:
- Memory pool management for object reuse
- Memory usage monitoring and optimization
- Automatic cleanup strategies
- Memory leak detection
- Performance-optimized data structures

Main Components:
- MemoryManager: Core memory management system
- MemoryOptimizer: Memory optimization for input handling
- EventObjectPool: Object pooling for input events
- MemoryStrategy: Different memory management strategies
"""

from .memory_manager import (
    MemoryManager,
    MemoryPool,
    MemoryStats,
    MemoryStrategy,
    get_memory_manager,
    initialize_memory_management
)

from .memory_optimizer import (
    MemoryOptimizer,
    EventObjectPool,
    OptimizedInputEvent,
    OptimizationLevel,
    MemoryOptimizationConfig,
    get_memory_optimizer,
    initialize_memory_optimization
)

__all__ = [
    'MemoryManager',
    'MemoryPool',
    'MemoryStats',
    'MemoryStrategy',
    'get_memory_manager',
    'initialize_memory_management',
    'MemoryOptimizer',
    'EventObjectPool',
    'OptimizedInputEvent',
    'OptimizationLevel',
    'MemoryOptimizationConfig',
    'get_memory_optimizer',
    'initialize_memory_optimization'
]

__version__ = "1.0.0"
__author__ = "ZeroLag Team"
__description__ = "Memory management and optimization for ZeroLag gaming input optimization"
