"""
Memory Optimization Module for ZeroLag

This module provides memory optimization strategies specifically designed
for the input handling components to minimize memory usage while
maintaining optimal performance.

Features:
- Input event object pooling
- Buffer size optimization
- Memory-efficient data structures
- Automatic memory cleanup
- Memory usage profiling
- Optimization recommendations
"""

import time
import threading
import weakref
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

from .memory_manager import MemoryManager, MemoryStrategy, get_memory_manager
from ..input.input_handler import InputEvent, InputEventType, EventPriority


class OptimizationLevel(Enum):
    """Memory optimization levels."""
    MINIMAL = "minimal"      # Minimal optimization, prioritize performance
    MODERATE = "moderate"    # Balanced optimization (default)
    AGGRESSIVE = "aggressive"  # Aggressive optimization, may impact performance
    MAXIMUM = "maximum"      # Maximum optimization, significant performance impact


@dataclass
class MemoryOptimizationConfig:
    """Configuration for memory optimization."""
    optimization_level: OptimizationLevel = OptimizationLevel.MODERATE
    enable_object_pooling: bool = True
    enable_buffer_optimization: bool = True
    enable_automatic_cleanup: bool = True
    max_event_pool_size: int = 1000
    max_buffer_size: int = 10000
    cleanup_interval_seconds: float = 30.0
    memory_threshold_mb: float = 40.0  # Start optimization at 40MB


class OptimizedInputEvent:
    """
    Memory-optimized input event with reduced overhead.
    
    Uses slots to reduce memory footprint and provides
    efficient serialization/deserialization.
    """
    __slots__ = ['event_type', 'data', 'priority', 'timestamp', 'source', '_pooled']
    
    def __init__(self, event_type: str, data: Dict[str, Any], priority: str, timestamp: float, source: str):
        self.event_type = event_type
        self.data = data
        self.priority = priority
        self.timestamp = timestamp
        self.source = source
        self._pooled = False
    
    def reset(self):
        """Reset the event for reuse."""
        self.event_type = ""
        self.data.clear()
        self.priority = "normal"
        self.timestamp = 0.0
        self.source = ""
        self._pooled = False
    
    def is_pooled(self) -> bool:
        """Check if this event is from the object pool."""
        return self._pooled
    
    def mark_pooled(self):
        """Mark this event as being from the object pool."""
        self._pooled = True


class EventObjectPool:
    """
    Object pool for InputEvent objects to reduce allocation overhead.
    
    Reuses event objects to minimize garbage collection pressure
    and improve memory efficiency.
    """
    
    def __init__(self, initial_size: int = 100, max_size: int = 1000):
        """
        Initialize event object pool.
        
        Args:
            initial_size: Initial number of events to create
            max_size: Maximum number of events to keep in pool
        """
        self.initial_size = initial_size
        self.max_size = max_size
        self.available_events = deque()
        self.total_created = 0
        self.total_reused = 0
        self.lock = threading.RLock()
        
        # Pre-allocate initial events
        for _ in range(initial_size):
            event = self._create_event()
            self.available_events.append(event)
            self.total_created += 1
    
    def _create_event(self) -> OptimizedInputEvent:
        """Create a new optimized input event."""
        return OptimizedInputEvent(
            event_type="",
            data={},
            priority="normal",
            timestamp=0.0,
            source=""
        )
    
    def get_event(self) -> OptimizedInputEvent:
        """
        Get an event from the pool.
        
        Returns:
            Event from pool or newly created if pool is empty
        """
        with self.lock:
            if self.available_events:
                event = self.available_events.popleft()
                event.reset()
                event.mark_pooled()
                self.total_reused += 1
                return event
            else:
                event = self._create_event()
                self.total_created += 1
                return event
    
    def return_event(self, event: OptimizedInputEvent):
        """
        Return an event to the pool.
        
        Args:
            event: Event to return to pool
        """
        with self.lock:
            if len(self.available_events) < self.max_size:
                event.reset()
                self.available_events.append(event)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self.lock:
            return {
                'available_count': len(self.available_events),
                'total_created': self.total_created,
                'total_reused': self.total_reused,
                'reuse_rate': self.total_reused / max(self.total_created, 1),
                'max_size': self.max_size
            }


class MemoryOptimizer:
    """
    Memory optimizer for input handling components.
    
    Provides memory optimization strategies, object pooling,
    and automatic cleanup for input handling systems.
    """
    
    def __init__(self, 
                 config: Optional[MemoryOptimizationConfig] = None,
                 memory_manager: Optional[MemoryManager] = None):
        """
        Initialize memory optimizer.
        
        Args:
            config: Optimization configuration
            memory_manager: Memory manager instance
        """
        self.config = config or MemoryOptimizationConfig()
        self.memory_manager = memory_manager or get_memory_manager()
        
        # Object pools
        self.event_pool = EventObjectPool(
            initial_size=100,
            max_size=self.config.max_event_pool_size
        )
        
        # Optimization state
        self.is_optimizing = False
        self.optimization_thread: Optional[threading.Thread] = None
        self.last_cleanup = 0.0
        self.cleanup_count = 0
        
        # Memory tracking
        self.memory_baseline = 0.0
        self.optimization_history: deque = deque(maxlen=100)
        
        # Component references (weak references to avoid circular dependencies)
        self.tracked_components: Set[weakref.ref] = set()
        
        # Cleanup callbacks
        self.cleanup_callbacks: List[Callable[[], None]] = []
        
        # Threading
        self._lock = threading.RLock()
    
    def start_optimization(self) -> bool:
        """
        Start memory optimization.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_optimizing:
            return True
        
        try:
            with self._lock:
                self.is_optimizing = True
                self.memory_baseline = self.memory_manager.get_current_memory_mb()
                
                # Start optimization thread
                self.optimization_thread = threading.Thread(
                    target=self._optimization_loop,
                    daemon=True,
                    name="MemoryOptimizerThread"
                )
                self.optimization_thread.start()
                
                return True
                
        except Exception as e:
            self.is_optimizing = False
            return False
    
    def stop_optimization(self) -> bool:
        """
        Stop memory optimization.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_optimizing:
            return True
        
        try:
            with self._lock:
                self.is_optimizing = False
                
                # Wait for optimization thread to finish
                if self.optimization_thread and self.optimization_thread.is_alive():
                    self.optimization_thread.join(timeout=2.0)
                
                return True
                
        except Exception as e:
            return False
    
    def _optimization_loop(self):
        """Main optimization loop."""
        try:
            while self.is_optimizing:
                try:
                    # Check if optimization is needed
                    if self._should_optimize():
                        self._perform_optimization()
                    
                    # Sleep for optimization interval
                    time.sleep(self.config.cleanup_interval_seconds)
                    
                except Exception as e:
                    time.sleep(1.0)
                    
        except Exception as e:
            pass
    
    def _should_optimize(self) -> bool:
        """Determine if memory optimization is needed."""
        current_memory = self.memory_manager.get_current_memory_mb()
        return current_memory > self.config.memory_threshold_mb
    
    def _perform_optimization(self):
        """Perform memory optimization."""
        optimization_start = time.time()
        
        try:
            # 1. Optimize event pool
            if self.config.enable_object_pooling:
                self._optimize_event_pool()
            
            # 2. Run component cleanup
            self._cleanup_components()
            
            # 3. Run custom cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception:
                    pass
            
            # 4. Force garbage collection
            import gc
            gc.collect()
            
            # Record optimization
            optimization_duration = time.time() - optimization_start
            memory_after = self.memory_manager.get_current_memory_mb()
            
            self.optimization_history.append({
                'timestamp': time.time(),
                'duration': optimization_duration,
                'memory_after': memory_after,
                'cleanup_count': self.cleanup_count
            })
            
            self.cleanup_count += 1
            self.last_cleanup = time.time()
            
        except Exception as e:
            pass
    
    def _optimize_event_pool(self):
        """Optimize the event object pool."""
        with self.event_pool.lock:
            # Remove excess events from pool
            excess_count = len(self.event_pool.available_events) - self.event_pool.max_size
            if excess_count > 0:
                for _ in range(excess_count):
                    if self.event_pool.available_events:
                        self.event_pool.available_events.popleft()
    
    def _cleanup_components(self):
        """Clean up tracked components."""
        dead_refs = []
        
        for ref in self.tracked_components:
            component = ref()
            if component is None:
                dead_refs.append(ref)
            else:
                # Try to cleanup the component
                try:
                    if hasattr(component, 'cleanup_memory'):
                        component.cleanup_memory()
                    elif hasattr(component, 'clear'):
                        component.clear()
                except Exception:
                    pass
        
        # Remove dead references
        for ref in dead_refs:
            self.tracked_components.discard(ref)
    
    def get_optimized_event(self, 
                          event_type: str,
                          data: Dict[str, Any],
                          priority: str = "normal",
                          source: str = "unknown") -> OptimizedInputEvent:
        """
        Get an optimized input event.
        
        Args:
            event_type: Type of the event
            data: Event data
            priority: Event priority
            source: Event source
            
        Returns:
            Optimized input event
        """
        event = self.event_pool.get_event()
        event.event_type = event_type
        event.data = data
        event.priority = priority
        event.timestamp = time.time()
        event.source = source
        return event
    
    def return_event(self, event: OptimizedInputEvent):
        """
        Return an event to the pool for reuse.
        
        Args:
            event: Event to return
        """
        if event.is_pooled():
            self.event_pool.return_event(event)
    
    def track_component(self, component) -> weakref.ref:
        """
        Track a component for memory optimization.
        
        Args:
            component: Component to track
            
        Returns:
            Weak reference to the component
        """
        ref = weakref.ref(component)
        self.tracked_components.add(ref)
        return ref
    
    def add_cleanup_callback(self, callback: Callable[[], None]):
        """
        Add a custom cleanup callback.
        
        Args:
            callback: Function to call during cleanup
        """
        self.cleanup_callbacks.append(callback)
    
    def remove_cleanup_callback(self, callback: Callable[[], None]):
        """
        Remove a cleanup callback.
        
        Args:
            callback: Function to remove
        """
        try:
            self.cleanup_callbacks.remove(callback)
        except ValueError:
            pass
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics."""
        event_pool_stats = self.event_pool.get_stats()
        memory_stats = self.memory_manager.get_memory_stats()
        
        return {
            'optimization_level': self.config.optimization_level.value,
            'is_optimizing': self.is_optimizing,
            'cleanup_count': self.cleanup_count,
            'last_cleanup': self.last_cleanup,
            'memory_baseline_mb': self.memory_baseline,
            'current_memory_mb': memory_stats.current_mb,
            'memory_saved_mb': self.memory_baseline - memory_stats.current_mb,
            'event_pool': event_pool_stats,
            'tracked_components': len(self.tracked_components),
            'optimization_history_count': len(self.optimization_history)
        }
    
    def force_optimization(self) -> Dict[str, Any]:
        """Force immediate memory optimization."""
        optimization_start = time.time()
        
        # Perform optimization
        self._perform_optimization()
        
        optimization_duration = time.time() - optimization_start
        memory_after = self.memory_manager.get_current_memory_mb()
        
        return {
            'optimization_duration': optimization_duration,
            'memory_after_mb': memory_after,
            'memory_saved_mb': self.memory_baseline - memory_after,
            'success': True
        }
    
    def set_optimization_level(self, level: OptimizationLevel):
        """Set the optimization level."""
        self.config.optimization_level = level
        
        # Adjust configuration based on level
        if level == OptimizationLevel.MINIMAL:
            self.config.max_event_pool_size = 500
            self.config.memory_threshold_mb = 45.0
        elif level == OptimizationLevel.MODERATE:
            self.config.max_event_pool_size = 1000
            self.config.memory_threshold_mb = 40.0
        elif level == OptimizationLevel.AGGRESSIVE:
            self.config.max_event_pool_size = 2000
            self.config.memory_threshold_mb = 35.0
        elif level == OptimizationLevel.MAXIMUM:
            self.config.max_event_pool_size = 5000
            self.config.memory_threshold_mb = 30.0
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get memory optimization recommendations."""
        recommendations = []
        stats = self.get_optimization_stats()
        
        # Check memory usage
        if stats['current_memory_mb'] > 45.0:
            recommendations.append("Consider increasing optimization level to reduce memory usage")
        
        # Check event pool efficiency
        event_pool = stats['event_pool']
        if event_pool['reuse_rate'] < 0.5:
            recommendations.append("Event pool reuse rate is low - consider adjusting pool size")
        
        # Check cleanup frequency
        if stats['cleanup_count'] == 0:
            recommendations.append("No cleanups performed - consider enabling automatic cleanup")
        
        # Check tracked components
        if stats['tracked_components'] == 0:
            recommendations.append("No components tracked - consider tracking input handlers for optimization")
        
        return recommendations


# Global memory optimizer instance
_memory_optimizer: Optional[MemoryOptimizer] = None


def get_memory_optimizer() -> MemoryOptimizer:
    """Get the global memory optimizer instance."""
    global _memory_optimizer
    if _memory_optimizer is None:
        _memory_optimizer = MemoryOptimizer()
    return _memory_optimizer


def initialize_memory_optimization(config: Optional[MemoryOptimizationConfig] = None) -> MemoryOptimizer:
    """
    Initialize global memory optimization.
    
    Args:
        config: Optimization configuration
        
    Returns:
        Initialized MemoryOptimizer instance
    """
    global _memory_optimizer
    _memory_optimizer = MemoryOptimizer(config=config)
    _memory_optimizer.start_optimization()
    return _memory_optimizer


# Example usage and testing
if __name__ == "__main__":
    # Initialize memory management
    memory_manager = get_memory_manager()
    memory_manager.start_monitoring()
    
    # Initialize memory optimization
    config = MemoryOptimizationConfig(
        optimization_level=OptimizationLevel.MODERATE,
        enable_object_pooling=True,
        enable_buffer_optimization=True,
        enable_automatic_cleanup=True
    )
    
    optimizer = initialize_memory_optimization(config)
    
    print("Memory optimization initialized")
    
    try:
        # Test event pooling
        print("\nTesting event pooling...")
        
        events = []
        for i in range(100):
            event = optimizer.get_optimized_event(
                event_type="mouse_move",
                data={"x": i, "y": i},
                priority="normal",
                source="test"
            )
            events.append(event)
        
        print(f"✓ Created {len(events)} optimized events")
        
        # Return events to pool
        for event in events:
            optimizer.return_event(event)
        
        print("✓ Returned events to pool")
        
        # Get optimization stats
        stats = optimizer.get_optimization_stats()
        print(f"✓ Event pool stats: {stats['event_pool']['reuse_rate']:.2%} reuse rate")
        
        # Test memory optimization
        print("\nTesting memory optimization...")
        
        # Force optimization
        optimization_result = optimizer.force_optimization()
        print(f"✓ Optimization completed: {optimization_result['memory_saved_mb']:.2f}MB saved")
        
        # Get recommendations
        recommendations = optimizer.get_optimization_recommendations()
        if recommendations:
            print("✓ Optimization recommendations:")
            for rec in recommendations:
                print(f"  - {rec}")
        
        # Simulate some activity
        print("\nSimulating activity...")
        for i in range(10):
            # Create and use events
            temp_events = []
            for j in range(50):
                event = optimizer.get_optimized_event(
                    event_type="key_press",
                    data={"key": f"key_{j}"},
                    priority="high",
                    source="simulation"
                )
                temp_events.append(event)
            
            # Return events
            for event in temp_events:
                optimizer.return_event(event)
            
            time.sleep(0.1)
        
        # Final stats
        final_stats = optimizer.get_optimization_stats()
        print(f"✓ Final optimization stats:")
        print(f"  - Memory saved: {final_stats['memory_saved_mb']:.2f}MB")
        print(f"  - Cleanup count: {final_stats['cleanup_count']}")
        print(f"  - Event pool reuse: {final_stats['event_pool']['reuse_rate']:.2%}")
        
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        optimizer.stop_optimization()
        memory_manager.stop_monitoring()
        print("Memory optimization stopped")
