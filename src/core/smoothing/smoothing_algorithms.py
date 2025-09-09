"""
Smoothing Algorithms for ZeroLag

This module provides various smoothing algorithms to eliminate cursor jitter
and provide smooth, precise mouse movement tracking for gaming applications.

Features:
- Low-pass filters for noise reduction
- Exponential moving averages for smooth tracking
- Kalman filtering for predictive smoothing
- Adaptive smoothing based on movement speed
- Configurable smoothing parameters
- Real-time performance optimization
"""

import math
import time
import threading
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics


class SmoothingType(Enum):
    """Types of smoothing algorithms available."""
    LOW_PASS = "low_pass"
    EXPONENTIAL_MA = "exponential_ma"
    KALMAN = "kalman"
    ADAPTIVE = "adaptive"
    GAUSSIAN = "gaussian"
    MEDIAN = "median"


@dataclass
class SmoothingConfig:
    """Configuration for smoothing algorithms."""
    smoothing_type: SmoothingType = SmoothingType.ADAPTIVE
    enabled: bool = True
    
    # Low-pass filter parameters
    low_pass_cutoff: float = 0.1  # Cutoff frequency (0.0 to 1.0)
    low_pass_order: int = 2       # Filter order
    
    # Exponential moving average parameters
    ema_alpha: float = 0.1        # Smoothing factor (0.0 to 1.0)
    ema_velocity_alpha: float = 0.05  # Velocity smoothing factor
    
    # Kalman filter parameters
    kalman_process_noise: float = 0.01
    kalman_measurement_noise: float = 0.1
    kalman_initial_uncertainty: float = 1.0
    
    # Adaptive smoothing parameters
    adaptive_min_smoothing: float = 0.05
    adaptive_max_smoothing: float = 0.3
    adaptive_velocity_threshold: float = 10.0  # pixels per second
    
    # Gaussian smoothing parameters
    gaussian_sigma: float = 1.0
    gaussian_kernel_size: int = 5
    
    # Median filter parameters
    median_window_size: int = 5
    
    # Performance parameters
    max_history_size: int = 100
    enable_velocity_calculation: bool = True
    enable_acceleration_calculation: bool = False


@dataclass
class SmoothingResult:
    """Result of smoothing operation."""
    smoothed_x: float
    smoothed_y: float
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    acceleration_x: float = 0.0
    acceleration_y: float = 0.0
    smoothing_factor: float = 0.0
    confidence: float = 1.0
    processing_time_ms: float = 0.0


class LowPassFilter:
    """
    Low-pass filter implementation for smoothing mouse movement.
    
    Removes high-frequency noise while preserving the general movement pattern.
    """
    
    def __init__(self, cutoff: float = 0.1, order: int = 2):
        """
        Initialize low-pass filter.
        
        Args:
            cutoff: Cutoff frequency (0.0 to 1.0)
            order: Filter order (1 or 2)
        """
        self.cutoff = max(0.0, min(1.0, cutoff))
        self.order = max(1, min(2, order))
        
        # Filter coefficients
        self.alpha = self.cutoff
        if self.order == 2:
            self.alpha = 1.0 - math.exp(-2.0 * math.pi * self.cutoff)
        
        # Filter state
        self.prev_x = 0.0
        self.prev_y = 0.0
        self.prev2_x = 0.0
        self.prev2_y = 0.0
        
        # Initialize
        self.initialized = False
    
    def filter(self, x: float, y: float) -> Tuple[float, float]:
        """
        Apply low-pass filter to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Filtered (x, y) coordinates
        """
        if not self.initialized:
            self.prev_x = x
            self.prev_y = y
            self.prev2_x = x
            self.prev2_y = y
            self.initialized = True
            return x, y
        
        # First order filter
        filtered_x = self.alpha * x + (1.0 - self.alpha) * self.prev_x
        filtered_y = self.alpha * y + (1.0 - self.alpha) * self.prev_y
        
        # Second order filter
        if self.order == 2:
            filtered_x = self.alpha * filtered_x + (1.0 - self.alpha) * self.prev2_x
            filtered_y = self.alpha * filtered_y + (1.0 - self.alpha) * self.prev2_y
            self.prev2_x = self.prev_x
            self.prev2_y = self.prev_y
        
        # Update state
        self.prev_x = filtered_x
        self.prev_y = filtered_y
        
        return filtered_x, filtered_y
    
    def reset(self):
        """Reset filter state."""
        self.initialized = False


class ExponentialMovingAverage:
    """
    Exponential Moving Average (EMA) for smooth mouse tracking.
    
    Provides smooth tracking with configurable responsiveness.
    """
    
    def __init__(self, alpha: float = 0.1, velocity_alpha: float = 0.05):
        """
        Initialize EMA filter.
        
        Args:
            alpha: Smoothing factor for position (0.0 to 1.0)
            velocity_alpha: Smoothing factor for velocity
        """
        self.alpha = max(0.0, min(1.0, alpha))
        self.velocity_alpha = max(0.0, min(1.0, velocity_alpha))
        
        # State
        self.smoothed_x = 0.0
        self.smoothed_y = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.last_time = 0.0
        
        # Initialize
        self.initialized = False
    
    def update(self, x: float, y: float, timestamp: float) -> Tuple[float, float, float, float]:
        """
        Update EMA with new coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            timestamp: Current timestamp
            
        Returns:
            (smoothed_x, smoothed_y, velocity_x, velocity_y)
        """
        if not self.initialized:
            self.smoothed_x = x
            self.smoothed_y = y
            self.velocity_x = 0.0
            self.velocity_y = 0.0
            self.last_time = timestamp
            self.initialized = True
            return x, y, 0.0, 0.0
        
        # Calculate time delta
        dt = timestamp - self.last_time
        if dt <= 0:
            dt = 0.001  # Minimum time step
        
        # Calculate velocity
        new_velocity_x = (x - self.smoothed_x) / dt
        new_velocity_y = (y - self.smoothed_y) / dt
        
        # Smooth velocity
        self.velocity_x = self.velocity_alpha * new_velocity_x + (1.0 - self.velocity_alpha) * self.velocity_x
        self.velocity_y = self.velocity_alpha * new_velocity_y + (1.0 - self.velocity_alpha) * self.velocity_y
        
        # Smooth position
        self.smoothed_x = self.alpha * x + (1.0 - self.alpha) * self.smoothed_x
        self.smoothed_y = self.alpha * y + (1.0 - self.alpha) * self.smoothed_y
        
        # Update timestamp
        self.last_time = timestamp
        
        return self.smoothed_x, self.smoothed_y, self.velocity_x, self.velocity_y
    
    def reset(self):
        """Reset EMA state."""
        self.initialized = False


class KalmanFilter:
    """
    Kalman filter for predictive mouse smoothing.
    
    Provides optimal smoothing with prediction capabilities.
    """
    
    def __init__(self, 
                 process_noise: float = 0.01,
                 measurement_noise: float = 0.1,
                 initial_uncertainty: float = 1.0):
        """
        Initialize Kalman filter.
        
        Args:
            process_noise: Process noise variance
            measurement_noise: Measurement noise variance
            initial_uncertainty: Initial uncertainty
        """
        self.q = process_noise
        self.r = measurement_noise
        self.p = initial_uncertainty
        
        # State
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.last_time = 0.0
        
        # Initialize
        self.initialized = False
    
    def update(self, x: float, y: float, timestamp: float) -> Tuple[float, float, float, float]:
        """
        Update Kalman filter with new measurement.
        
        Args:
            x: X coordinate measurement
            y: Y coordinate measurement
            timestamp: Current timestamp
            
        Returns:
            (filtered_x, filtered_y, velocity_x, velocity_y)
        """
        if not self.initialized:
            self.x = x
            self.y = y
            self.vx = 0.0
            self.vy = 0.0
            self.last_time = timestamp
            self.initialized = True
            return x, y, 0.0, 0.0
        
        # Calculate time delta
        dt = timestamp - self.last_time
        if dt <= 0:
            dt = 0.001
        
        # Prediction step
        # State transition: x = x + vx*dt, y = y + vy*dt
        predicted_x = self.x + self.vx * dt
        predicted_y = self.y + self.vy * dt
        
        # Update uncertainty
        self.p += self.q * dt
        
        # Update step
        # Kalman gain
        k = self.p / (self.p + self.r)
        
        # Update state
        self.x = predicted_x + k * (x - predicted_x)
        self.y = predicted_y + k * (y - predicted_y)
        
        # Update velocity
        self.vx = (self.x - predicted_x) / dt
        self.vy = (self.y - predicted_y) / dt
        
        # Update uncertainty
        self.p *= (1.0 - k)
        
        # Update timestamp
        self.last_time = timestamp
        
        return self.x, self.y, self.vx, self.vy
    
    def reset(self):
        """Reset Kalman filter state."""
        self.initialized = False


class GaussianSmoother:
    """
    Gaussian smoothing for mouse movement.
    
    Applies Gaussian kernel smoothing to reduce noise.
    """
    
    def __init__(self, sigma: float = 1.0, kernel_size: int = 5):
        """
        Initialize Gaussian smoother.
        
        Args:
            sigma: Gaussian standard deviation
            kernel_size: Size of the smoothing kernel
        """
        self.sigma = max(0.1, sigma)
        self.kernel_size = max(3, kernel_size)
        
        # Generate Gaussian kernel
        self.kernel = self._generate_kernel()
        
        # History buffer
        self.history_x = deque(maxlen=self.kernel_size)
        self.history_y = deque(maxlen=self.kernel_size)
    
    def _generate_kernel(self) -> List[float]:
        """Generate Gaussian kernel."""
        kernel = []
        center = self.kernel_size // 2
        
        for i in range(self.kernel_size):
            x = i - center
            weight = math.exp(-(x * x) / (2 * self.sigma * self.sigma))
            kernel.append(weight)
        
        # Normalize kernel
        total = sum(kernel)
        return [w / total for w in kernel]
    
    def smooth(self, x: float, y: float) -> Tuple[float, float]:
        """
        Apply Gaussian smoothing.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Smoothed (x, y) coordinates
        """
        # Add to history
        self.history_x.append(x)
        self.history_y.append(y)
        
        # Apply kernel if we have enough data
        if len(self.history_x) >= self.kernel_size:
            smoothed_x = sum(self.history_x[i] * self.kernel[i] for i in range(self.kernel_size))
            smoothed_y = sum(self.history_y[i] * self.kernel[i] for i in range(self.kernel_size))
            return smoothed_x, smoothed_y
        else:
            # Not enough data, return current values
            return x, y
    
    def reset(self):
        """Reset smoother state."""
        self.history_x.clear()
        self.history_y.clear()


class MedianFilter:
    """
    Median filter for removing outliers in mouse movement.
    
    Effective for removing sudden jumps or noise spikes.
    """
    
    def __init__(self, window_size: int = 5):
        """
        Initialize median filter.
        
        Args:
            window_size: Size of the median window
        """
        self.window_size = max(3, window_size)
        self.history_x = deque(maxlen=self.window_size)
        self.history_y = deque(maxlen=self.window_size)
    
    def filter(self, x: float, y: float) -> Tuple[float, float]:
        """
        Apply median filter.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Filtered (x, y) coordinates
        """
        # Add to history
        self.history_x.append(x)
        self.history_y.append(y)
        
        # Apply median filter if we have enough data
        if len(self.history_x) >= self.window_size:
            median_x = statistics.median(self.history_x)
            median_y = statistics.median(self.history_y)
            return median_x, median_y
        else:
            # Not enough data, return current values
            return x, y
    
    def reset(self):
        """Reset filter state."""
        self.history_x.clear()
        self.history_y.clear()


class AdaptiveSmoother:
    """
    Adaptive smoothing that adjusts based on movement characteristics.
    
    Provides more smoothing for slow movements and less for fast movements.
    """
    
    def __init__(self, 
                 min_smoothing: float = 0.05,
                 max_smoothing: float = 0.3,
                 velocity_threshold: float = 10.0):
        """
        Initialize adaptive smoother.
        
        Args:
            min_smoothing: Minimum smoothing factor
            max_smoothing: Maximum smoothing factor
            velocity_threshold: Velocity threshold for adaptation
        """
        self.min_smoothing = max(0.0, min(1.0, min_smoothing))
        self.max_smoothing = max(self.min_smoothing, min(1.0, max_smoothing))
        self.velocity_threshold = max(0.1, velocity_threshold)
        
        # Use EMA as the base smoother
        self.ema = ExponentialMovingAverage(alpha=self.max_smoothing)
        
        # Velocity tracking
        self.last_x = 0.0
        self.last_y = 0.0
        self.last_time = 0.0
        self.initialized = False
    
    def smooth(self, x: float, y: float, timestamp: float) -> Tuple[float, float, float, float, float]:
        """
        Apply adaptive smoothing.
        
        Args:
            x: X coordinate
            y: Y coordinate
            timestamp: Current timestamp
            
        Returns:
            (smoothed_x, smoothed_y, velocity_x, velocity_y, smoothing_factor)
        """
        if not self.initialized:
            self.last_x = x
            self.last_y = y
            self.last_time = timestamp
            self.initialized = True
            return x, y, 0.0, 0.0, self.max_smoothing
        
        # Calculate velocity
        dt = timestamp - self.last_time
        if dt <= 0:
            dt = 0.001
        
        velocity_x = (x - self.last_x) / dt
        velocity_y = (y - self.last_y) / dt
        velocity_magnitude = math.sqrt(velocity_x * velocity_x + velocity_y * velocity_y)
        
        # Calculate adaptive smoothing factor
        if velocity_magnitude > self.velocity_threshold:
            # Fast movement - less smoothing
            smoothing_factor = self.min_smoothing
        else:
            # Slow movement - more smoothing
            # Interpolate between min and max based on velocity
            velocity_ratio = velocity_magnitude / self.velocity_threshold
            smoothing_factor = self.max_smoothing - (self.max_smoothing - self.min_smoothing) * velocity_ratio
        
        # Update EMA with adaptive alpha
        self.ema.alpha = smoothing_factor
        smoothed_x, smoothed_y, vel_x, vel_y = self.ema.update(x, y, timestamp)
        
        # Update state
        self.last_x = x
        self.last_y = y
        self.last_time = timestamp
        
        return smoothed_x, smoothed_y, vel_x, vel_y, smoothing_factor
    
    def reset(self):
        """Reset adaptive smoother state."""
        self.ema.reset()
        self.initialized = False


class SmoothingEngine:
    """
    Main smoothing engine that coordinates all smoothing algorithms.
    
    Provides a unified interface for applying various smoothing techniques
    to mouse movement data.
    """
    
    def __init__(self, config: Optional[SmoothingConfig] = None):
        """
        Initialize smoothing engine.
        
        Args:
            config: Smoothing configuration
        """
        self.config = config or SmoothingConfig()
        
        # Initialize smoothing algorithms
        self.low_pass = LowPassFilter(
            cutoff=self.config.low_pass_cutoff,
            order=self.config.low_pass_order
        )
        
        self.ema = ExponentialMovingAverage(
            alpha=self.config.ema_alpha,
            velocity_alpha=self.config.ema_velocity_alpha
        )
        
        self.kalman = KalmanFilter(
            process_noise=self.config.kalman_process_noise,
            measurement_noise=self.config.kalman_measurement_noise,
            initial_uncertainty=self.config.kalman_initial_uncertainty
        )
        
        self.gaussian = GaussianSmoother(
            sigma=self.config.gaussian_sigma,
            kernel_size=self.config.gaussian_kernel_size
        )
        
        self.median = MedianFilter(
            window_size=self.config.median_window_size
        )
        
        self.adaptive = AdaptiveSmoother(
            min_smoothing=self.config.adaptive_min_smoothing,
            max_smoothing=self.config.adaptive_max_smoothing,
            velocity_threshold=self.config.adaptive_velocity_threshold
        )
        
        # Performance tracking
        self.processing_times = deque(maxlen=100)
        self.lock = threading.RLock()
    
    def smooth(self, x: float, y: float, timestamp: Optional[float] = None) -> SmoothingResult:
        """
        Apply smoothing to mouse coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            timestamp: Current timestamp (uses current time if None)
            
        Returns:
            SmoothingResult with smoothed coordinates and metadata
        """
        if not self.config.enabled:
            return SmoothingResult(
                smoothed_x=x,
                smoothed_y=y,
                velocity_x=0.0,
                velocity_y=0.0,
                smoothing_factor=0.0,
                confidence=1.0,
                processing_time_ms=0.0
            )
        
        start_time = time.time()
        if timestamp is None:
            timestamp = start_time
        
        with self.lock:
            try:
                # Apply selected smoothing algorithm
                if self.config.smoothing_type == SmoothingType.LOW_PASS:
                    smoothed_x, smoothed_y = self.low_pass.filter(x, y)
                    velocity_x, velocity_y = 0.0, 0.0
                    smoothing_factor = self.config.low_pass_cutoff
                    confidence = 0.8
                
                elif self.config.smoothing_type == SmoothingType.EXPONENTIAL_MA:
                    smoothed_x, smoothed_y, velocity_x, velocity_y = self.ema.update(x, y, timestamp)
                    smoothing_factor = self.config.ema_alpha
                    confidence = 0.9
                
                elif self.config.smoothing_type == SmoothingType.KALMAN:
                    smoothed_x, smoothed_y, velocity_x, velocity_y = self.kalman.update(x, y, timestamp)
                    smoothing_factor = 0.5  # Kalman doesn't have a simple smoothing factor
                    confidence = 0.95
                
                elif self.config.smoothing_type == SmoothingType.GAUSSIAN:
                    smoothed_x, smoothed_y = self.gaussian.smooth(x, y)
                    velocity_x, velocity_y = 0.0, 0.0
                    smoothing_factor = self.config.gaussian_sigma
                    confidence = 0.7
                
                elif self.config.smoothing_type == SmoothingType.MEDIAN:
                    smoothed_x, smoothed_y = self.median.filter(x, y)
                    velocity_x, velocity_y = 0.0, 0.0
                    smoothing_factor = 0.5
                    confidence = 0.6
                
                elif self.config.smoothing_type == SmoothingType.ADAPTIVE:
                    smoothed_x, smoothed_y, velocity_x, velocity_y, smoothing_factor = self.adaptive.smooth(x, y, timestamp)
                    confidence = 0.85
                
                else:
                    # Default to no smoothing
                    smoothed_x, smoothed_y = x, y
                    velocity_x, velocity_y = 0.0, 0.0
                    smoothing_factor = 0.0
                    confidence = 1.0
                
                # Calculate processing time
                processing_time = (time.time() - start_time) * 1000
                self.processing_times.append(processing_time)
                
                return SmoothingResult(
                    smoothed_x=smoothed_x,
                    smoothed_y=smoothed_y,
                    velocity_x=velocity_x,
                    velocity_y=velocity_y,
                    smoothing_factor=smoothing_factor,
                    confidence=confidence,
                    processing_time_ms=processing_time
                )
                
            except Exception as e:
                # Fallback to no smoothing on error
                processing_time = (time.time() - start_time) * 1000
                return SmoothingResult(
                    smoothed_x=x,
                    smoothed_y=y,
                    velocity_x=0.0,
                    velocity_y=0.0,
                    smoothing_factor=0.0,
                    confidence=0.0,
                    processing_time_ms=processing_time
                )
    
    def update_config(self, config: SmoothingConfig):
        """
        Update smoothing configuration.
        
        Args:
            config: New smoothing configuration
        """
        with self.lock:
            self.config = config
            
            # Reinitialize algorithms with new config
            self.low_pass = LowPassFilter(
                cutoff=config.low_pass_cutoff,
                order=config.low_pass_order
            )
            
            self.ema = ExponentialMovingAverage(
                alpha=config.ema_alpha,
                velocity_alpha=config.ema_velocity_alpha
            )
            
            self.kalman = KalmanFilter(
                process_noise=config.kalman_process_noise,
                measurement_noise=config.kalman_measurement_noise,
                initial_uncertainty=config.kalman_initial_uncertainty
            )
            
            self.gaussian = GaussianSmoother(
                sigma=config.gaussian_sigma,
                kernel_size=config.gaussian_kernel_size
            )
            
            self.median = MedianFilter(
                window_size=config.median_window_size
            )
            
            self.adaptive = AdaptiveSmoother(
                min_smoothing=config.adaptive_min_smoothing,
                max_smoothing=config.adaptive_max_smoothing,
                velocity_threshold=config.adaptive_velocity_threshold
            )
    
    def reset(self):
        """Reset all smoothing algorithms."""
        with self.lock:
            self.low_pass.reset()
            self.ema.reset()
            self.kalman.reset()
            self.gaussian.reset()
            self.median.reset()
            self.adaptive.reset()
            self.processing_times.clear()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self.lock:
            if not self.processing_times:
                return {
                    'avg_processing_time_ms': 0.0,
                    'max_processing_time_ms': 0.0,
                    'min_processing_time_ms': 0.0,
                    'total_samples': 0
                }
            
            return {
                'avg_processing_time_ms': statistics.mean(self.processing_times),
                'max_processing_time_ms': max(self.processing_times),
                'min_processing_time_ms': min(self.processing_times),
                'total_samples': len(self.processing_times)
            }
    
    def get_config(self) -> SmoothingConfig:
        """Get current configuration."""
        return self.config


# Example usage and testing
if __name__ == "__main__":
    import random
    
    # Create smoothing engine
    config = SmoothingConfig(
        smoothing_type=SmoothingType.ADAPTIVE,
        enabled=True,
        adaptive_min_smoothing=0.05,
        adaptive_max_smoothing=0.3,
        adaptive_velocity_threshold=10.0
    )
    
    smoother = SmoothingEngine(config)
    
    print("Testing smoothing algorithms...")
    
    # Simulate noisy mouse movement
    base_x, base_y = 100.0, 100.0
    results = []
    
    for i in range(100):
        # Add some noise to simulate jittery mouse movement
        noise_x = random.gauss(0, 2.0)
        noise_y = random.gauss(0, 2.0)
        
        # Simulate movement
        base_x += random.gauss(0, 1.0)
        base_y += random.gauss(0, 1.0)
        
        noisy_x = base_x + noise_x
        noisy_y = base_y + noise_y
        
        # Apply smoothing
        result = smoother.smooth(noisy_x, noisy_y)
        results.append(result)
        
        if i % 20 == 0:
            print(f"Step {i}: Raw({noisy_x:.1f}, {noisy_y:.1f}) -> "
                  f"Smoothed({result.smoothed_x:.1f}, {result.smoothed_y:.1f}) "
                  f"Velocity({result.velocity_x:.1f}, {result.velocity_y:.1f}) "
                  f"Factor({result.smoothing_factor:.3f})")
    
    # Get performance stats
    stats = smoother.get_performance_stats()
    print(f"\nPerformance Stats:")
    print(f"Average processing time: {stats['avg_processing_time_ms']:.3f}ms")
    print(f"Max processing time: {stats['max_processing_time_ms']:.3f}ms")
    print(f"Total samples: {stats['total_samples']}")
    
    # Test different smoothing types
    print("\nTesting different smoothing types...")
    smoothing_types = [
        SmoothingType.LOW_PASS,
        SmoothingType.EXPONENTIAL_MA,
        SmoothingType.KALMAN,
        SmoothingType.ADAPTIVE
    ]
    
    for smoothing_type in smoothing_types:
        config.smoothing_type = smoothing_type
        smoother.update_config(config)
        smoother.reset()
        
        # Test with a few samples
        test_results = []
        for i in range(10):
            x = 100 + i + random.gauss(0, 1.0)
            y = 100 + i + random.gauss(0, 1.0)
            result = smoother.smooth(x, y)
            test_results.append(result)
        
        avg_processing = statistics.mean([r.processing_time_ms for r in test_results])
        print(f"{smoothing_type.value}: Avg processing time {avg_processing:.3f}ms")
    
    print("\nSmoothing algorithm testing completed!")
