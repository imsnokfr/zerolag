"""
Memory Management System for ZeroLag

This module provides comprehensive memory management capabilities to ensure
the application stays under the 50MB memory target while maintaining
optimal performance.

Features:
- Memory pool management
- Object recycling and reuse
- Memory leak detection
- Garbage collection optimization
- Memory usage monitoring
- Automatic cleanup strategies
"""

import gc
import sys
import time
import threading
import weakref
import psutil
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from collections import deque
from enum import Enum


class MemoryStrategy(Enum):
    """Memory management strategies."""
    AGGRESSIVE = "aggressive"      # Aggressive cleanup, may impact performance
    BALANCED = "balanced"          # Balanced approach (default)
    CONSERVATIVE = "conservative"  # Conservative cleanup, prioritize performance
    CUSTOM = "custom"             # Custom strategy


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    current_mb: float
    peak_mb: float
    target_mb: float
    utilization_percent: float
    objects_count: int
    gc_collections: int
    last_cleanup: float
    cleanup_count: int


class MemoryPool:
    """
    Memory pool for object reuse to reduce allocation overhead.
    
    Maintains pools of commonly used objects to avoid frequent
    allocation and deallocation.
    """
    
    def __init__(self, object_type, initial_size: int = 10, max_size: int = 100):
        """
        Initialize memory pool.
        
        Args:
            object_type: Type of objects to pool
            initial_size: Initial number of objects to create
            max_size: Maximum number of objects to keep in pool
        """
        self.object_type = object_type
        self.initial_size = initial_size
        self.max_size = max_size
        self.available_objects = deque()
        self.total_created = 0
        self.total_reused = 0
        self.lock = threading.RLock()
        
        # Pre-allocate initial objects
        for _ in range(initial_size):
            obj = self._create_object()
            self.available_objects.append(obj)
            self.total_created += 1
    
    def _create_object(self):
        """Create a new object of the pooled type."""
        if hasattr(self.object_type, '__call__'):
            return self.object_type()
        else:
            return self.object_type
    
    def get_object(self):
        """
        Get an object from the pool.
        
        Returns:
            Object from pool or newly created if pool is empty
        """
        with self.lock:
            if self.available_objects:
                obj = self.available_objects.popleft()
                self.total_reused += 1
                return obj
            else:
                obj = self._create_object()
                self.total_created += 1
                return obj
    
    def return_object(self, obj):
        """
        Return an object to the pool.
        
        Args:
            obj: Object to return to pool
        """
        with self.lock:
            if len(self.available_objects) < self.max_size:
                # Reset object state if it has a reset method
                if hasattr(obj, 'reset'):
                    obj.reset()
                elif hasattr(obj, 'clear'):
                    obj.clear()
                
                self.available_objects.append(obj)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self.lock:
            return {
                'object_type': self.object_type.__name__,
                'available_count': len(self.available_objects),
                'total_created': self.total_created,
                'total_reused': self.total_reused,
                'reuse_rate': self.total_reused / max(self.total_created, 1),
                'max_size': self.max_size
            }


class MemoryManager:
    """
    Comprehensive memory management system.
    
    Monitors memory usage, manages object pools, performs cleanup,
    and ensures the application stays within memory targets.
    """
    
    def __init__(self, 
                 target_memory_mb: float = 50.0,
                 strategy: MemoryStrategy = MemoryStrategy.BALANCED,
                 enable_monitoring: bool = True,
                 enable_logging: bool = False):
        """
        Initialize memory manager.
        
        Args:
            target_memory_mb: Target memory usage in MB
            strategy: Memory management strategy
            enable_monitoring: Whether to enable memory monitoring
            enable_logging: Whether to enable debug logging
        """
        self.target_memory_mb = target_memory_mb
        self.strategy = strategy
        self.enable_monitoring = enable_monitoring
        self.enable_logging = enable_logging
        
        # Memory pools
        self.memory_pools: Dict[str, MemoryPool] = {}
        
        # Monitoring
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.memory_history: deque = deque(maxlen=1000)
        self.peak_memory = 0.0
        self.cleanup_count = 0
        self.last_cleanup = 0.0
        
        # Process information
        self.process = psutil.Process()
        
        # Cleanup callbacks
        self.cleanup_callbacks: List[Callable[[], None]] = []
        
        # Weak references for tracking objects
        self.tracked_objects: Set[weakref.ref] = set()
        
        # Logging
        self.logger = logging.getLogger(__name__) if enable_logging else None
        
        # Threading
        self._lock = threading.RLock()
        
        # Initialize memory pools for common types
        self._initialize_memory_pools()
    
    def _initialize_memory_pools(self):
        """Initialize memory pools for commonly used objects."""
        # Pool for dictionaries
        self.memory_pools['dict'] = MemoryPool(dict, initial_size=20, max_size=200)
        
        # Pool for lists
        self.memory_pools['list'] = MemoryPool(list, initial_size=20, max_size=200)
        
        # Pool for sets
        self.memory_pools['set'] = MemoryPool(set, initial_size=10, max_size=100)
        
        # Pool for deques
        self.memory_pools['deque'] = MemoryPool(deque, initial_size=10, max_size=100)
        
        if self.logger:
            self.logger.info(f"Initialized {len(self.memory_pools)} memory pools")
    
    def start_monitoring(self) -> bool:
        """
        Start memory monitoring.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_monitoring:
            return True
        
        try:
            with self._lock:
                self.is_monitoring = True
                
                # Start monitoring thread
                self.monitoring_thread = threading.Thread(
                    target=self._monitoring_loop,
                    daemon=True,
                    name="MemoryManagerThread"
                )
                self.monitoring_thread.start()
                
                if self.logger:
                    self.logger.info("Memory monitoring started")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to start memory monitoring: {e}")
            self.is_monitoring = False
            return False
    
    def stop_monitoring(self) -> bool:
        """
        Stop memory monitoring.
        
        Returns:
            True if stopped successfully, False otherwise
        """
        if not self.is_monitoring:
            return True
        
        try:
            with self._lock:
                self.is_monitoring = False
                
                # Wait for monitoring thread to finish
                if self.monitoring_thread and self.monitoring_thread.is_alive():
                    self.monitoring_thread.join(timeout=2.0)
                
                if self.logger:
                    self.logger.info("Memory monitoring stopped")
                
                return True
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error stopping memory monitoring: {e}")
            return False
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        try:
            while self.is_monitoring:
                try:
                    # Check memory usage
                    current_memory = self.get_current_memory_mb()
                    
                    # Update peak memory
                    if current_memory > self.peak_memory:
                        self.peak_memory = current_memory
                    
                    # Store in history
                    self.memory_history.append({
                        'timestamp': time.time(),
                        'memory_mb': current_memory,
                        'utilization_percent': (current_memory / self.target_memory_mb) * 100
                    })
                    
                    # Check if cleanup is needed
                    if self._should_cleanup(current_memory):
                        self.perform_cleanup()
                    
                    # Sleep for monitoring interval
                    time.sleep(1.0)  # Check every second
                    
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error in memory monitoring loop: {e}")
                    time.sleep(1.0)
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Fatal error in memory monitoring loop: {e}")
    
    def _should_cleanup(self, current_memory: float) -> bool:
        """Determine if memory cleanup is needed."""
        utilization = (current_memory / self.target_memory_mb) * 100
        
        if self.strategy == MemoryStrategy.AGGRESSIVE:
            return utilization > 60  # Cleanup at 60% utilization
        elif self.strategy == MemoryStrategy.BALANCED:
            return utilization > 80  # Cleanup at 80% utilization
        elif self.strategy == MemoryStrategy.CONSERVATIVE:
            return utilization > 95  # Cleanup at 95% utilization
        else:
            return utilization > 90  # Default threshold
    
    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024
        except Exception:
            return 0.0
    
    def get_memory_stats(self) -> MemoryStats:
        """Get comprehensive memory statistics."""
        current_memory = self.get_current_memory_mb()
        utilization = (current_memory / self.target_memory_mb) * 100
        
        # Count objects
        objects_count = len(gc.get_objects())
        
        # Get GC stats
        gc_stats = gc.get_stats()
        total_collections = sum(stat['collections'] for stat in gc_stats)
        
        return MemoryStats(
            current_mb=current_memory,
            peak_mb=self.peak_memory,
            target_mb=self.target_memory_mb,
            utilization_percent=utilization,
            objects_count=objects_count,
            gc_collections=total_collections,
            last_cleanup=self.last_cleanup,
            cleanup_count=self.cleanup_count
        )
    
    def perform_cleanup(self) -> Dict[str, Any]:
        """
        Perform comprehensive memory cleanup.
        
        Returns:
            Dictionary with cleanup results
        """
        cleanup_start = time.time()
        results = {
            'memory_before': self.get_current_memory_mb(),
            'objects_before': len(gc.get_objects()),
            'cleanup_actions': []
        }
        
        try:
            # 1. Run garbage collection
            collected = gc.collect()
            results['cleanup_actions'].append(f"Garbage collection: {collected} objects collected")
            
            # 2. Clean up tracked objects
            self._cleanup_tracked_objects()
            results['cleanup_actions'].append("Cleaned up tracked objects")
            
            # 3. Run custom cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                    results['cleanup_actions'].append(f"Custom cleanup: {callback.__name__}")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Error in cleanup callback {callback.__name__}: {e}")
            
            # 4. Optimize memory pools
            self._optimize_memory_pools()
            results['cleanup_actions'].append("Optimized memory pools")
            
            # 5. Force garbage collection again
            collected2 = gc.collect()
            results['cleanup_actions'].append(f"Final garbage collection: {collected2} objects collected")
            
            # Update statistics
            self.cleanup_count += 1
            self.last_cleanup = time.time()
            
            # Calculate results
            results['memory_after'] = self.get_current_memory_mb()
            results['objects_after'] = len(gc.get_objects())
            results['memory_freed'] = results['memory_before'] - results['memory_after']
            results['objects_freed'] = results['objects_before'] - results['objects_after']
            results['cleanup_duration'] = time.time() - cleanup_start
            
            if self.logger:
                self.logger.info(f"Memory cleanup completed: {results['memory_freed']:.2f}MB freed, "
                               f"{results['objects_freed']} objects freed in {results['cleanup_duration']:.3f}s")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during memory cleanup: {e}")
            results['error'] = str(e)
        
        return results
    
    def _cleanup_tracked_objects(self):
        """Clean up tracked objects that are no longer referenced."""
        dead_refs = []
        
        for ref in self.tracked_objects:
            if ref() is None:  # Object has been garbage collected
                dead_refs.append(ref)
        
        # Remove dead references
        for ref in dead_refs:
            self.tracked_objects.discard(ref)
        
        if self.logger and dead_refs:
            self.logger.debug(f"Cleaned up {len(dead_refs)} dead object references")
    
    def _optimize_memory_pools(self):
        """Optimize memory pools by removing excess objects."""
        for pool_name, pool in self.memory_pools.items():
            with pool.lock:
                # Remove excess objects from pool
                excess_count = len(pool.available_objects) - pool.max_size
                if excess_count > 0:
                    for _ in range(excess_count):
                        if pool.available_objects:
                            pool.available_objects.popleft()
    
    def get_pooled_object(self, object_type: str):
        """
        Get an object from a memory pool.
        
        Args:
            object_type: Type of object to get ('dict', 'list', 'set', 'deque')
            
        Returns:
            Object from pool
        """
        if object_type in self.memory_pools:
            return self.memory_pools[object_type].get_object()
        else:
            # Create new pool for this type
            self.memory_pools[object_type] = MemoryPool(
                type(object_type), initial_size=5, max_size=50
            )
            return self.memory_pools[object_type].get_object()
    
    def return_pooled_object(self, obj, object_type: str):
        """
        Return an object to a memory pool.
        
        Args:
            obj: Object to return
            object_type: Type of object ('dict', 'list', 'set', 'deque')
        """
        if object_type in self.memory_pools:
            self.memory_pools[object_type].return_object(obj)
    
    def track_object(self, obj) -> weakref.ref:
        """
        Track an object for memory management.
        
        Args:
            obj: Object to track
            
        Returns:
            Weak reference to the object
        """
        ref = weakref.ref(obj)
        self.tracked_objects.add(ref)
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
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get statistics for all memory pools."""
        stats = {}
        for name, pool in self.memory_pools.items():
            stats[name] = pool.get_stats()
        return stats
    
    def set_strategy(self, strategy: MemoryStrategy):
        """Set the memory management strategy."""
        self.strategy = strategy
        if self.logger:
            self.logger.info(f"Memory management strategy changed to: {strategy.value}")
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force immediate memory cleanup regardless of current usage."""
        return self.perform_cleanup()
    
    def get_memory_history(self, duration_seconds: int = 60) -> List[Dict[str, Any]]:
        """
        Get memory usage history for the specified duration.
        
        Args:
            duration_seconds: Duration to retrieve history for
            
        Returns:
            List of memory usage records
        """
        cutoff_time = time.time() - duration_seconds
        return [record for record in self.memory_history if record['timestamp'] >= cutoff_time]


# Global memory manager instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager


def initialize_memory_management(target_memory_mb: float = 50.0,
                                strategy: MemoryStrategy = MemoryStrategy.BALANCED,
                                enable_monitoring: bool = True) -> MemoryManager:
    """
    Initialize global memory management.
    
    Args:
        target_memory_mb: Target memory usage in MB
        strategy: Memory management strategy
        enable_monitoring: Whether to enable monitoring
        
    Returns:
        Initialized MemoryManager instance
    """
    global _memory_manager
    _memory_manager = MemoryManager(
        target_memory_mb=target_memory_mb,
        strategy=strategy,
        enable_monitoring=enable_monitoring,
        enable_logging=True
    )
    
    if enable_monitoring:
        _memory_manager.start_monitoring()
    
    return _memory_manager


# Example usage and testing
if __name__ == "__main__":
    # Initialize memory management
    memory_manager = initialize_memory_management(
        target_memory_mb=50.0,
        strategy=MemoryStrategy.BALANCED,
        enable_monitoring=True
    )
    
    print("Memory management initialized")
    
    try:
        # Test memory pools
        print("\nTesting memory pools...")
        
        # Get objects from pools
        test_dict = memory_manager.get_pooled_object('dict')
        test_list = memory_manager.get_pooled_object('list')
        test_set = memory_manager.get_pooled_object('set')
        
        # Use objects
        test_dict['key'] = 'value'
        test_list.append(1)
        test_set.add('item')
        
        # Return objects to pools
        memory_manager.return_pooled_object(test_dict, 'dict')
        memory_manager.return_pooled_object(test_list, 'list')
        memory_manager.return_pooled_object(test_set, 'set')
        
        print("✓ Memory pool test completed")
        
        # Test memory tracking
        print("\nTesting memory tracking...")
        
        # Create some objects and track them
        tracked_objects = []
        for i in range(100):
            obj = {'id': i, 'data': f'data_{i}'}
            ref = memory_manager.track_object(obj)
            tracked_objects.append(ref)
        
        print(f"✓ Tracked {len(tracked_objects)} objects")
        
        # Get memory stats
        stats = memory_manager.get_memory_stats()
        print(f"✓ Current memory: {stats.current_mb:.2f}MB")
        print(f"✓ Memory utilization: {stats.utilization_percent:.1f}%")
        print(f"✓ Objects count: {stats.objects_count}")
        
        # Test cleanup
        print("\nTesting memory cleanup...")
        cleanup_results = memory_manager.perform_cleanup()
        print(f"✓ Cleanup completed: {cleanup_results['memory_freed']:.2f}MB freed")
        
        # Get pool stats
        pool_stats = memory_manager.get_pool_stats()
        print(f"✓ Memory pools: {len(pool_stats)} pools active")
        
        # Simulate some activity
        print("\nSimulating activity...")
        for i in range(10):
            # Create and use objects
            temp_objects = []
            for j in range(100):
                obj = {'iteration': i, 'item': j, 'data': f'data_{i}_{j}'}
                temp_objects.append(obj)
            
            # Let objects go out of scope
            del temp_objects
            
            time.sleep(0.1)
        
        # Final cleanup
        final_cleanup = memory_manager.perform_cleanup()
        print(f"✓ Final cleanup: {final_cleanup['memory_freed']:.2f}MB freed")
        
        # Final stats
        final_stats = memory_manager.get_memory_stats()
        print(f"✓ Final memory: {final_stats.current_mb:.2f}MB")
        print(f"✓ Peak memory: {final_stats.peak_mb:.2f}MB")
        print(f"✓ Total cleanups: {final_stats.cleanup_count}")
        
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        memory_manager.stop_monitoring()
        print("Memory management stopped")
