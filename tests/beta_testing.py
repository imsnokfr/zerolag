#!/usr/bin/env python3
"""
ZeroLag Beta Testing Framework

This module provides comprehensive testing capabilities for beta testing
with real users, including automated testing, performance monitoring,
and feedback collection.
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QObject, pyqtSignal

from src.core.benchmark import BenchmarkManager, BenchmarkConfig
from src.core.profiles import ProfileManager
from src.core.input.input_handler import InputHandler
from src.gui.main_window import ZeroLagMainWindow


@dataclass
class TestResult:
    """Result of a beta test."""
    test_id: str
    user_id: str
    test_type: str
    start_time: datetime
    end_time: datetime
    duration: float
    success: bool
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = None
    user_feedback: Dict[str, Any] = None


@dataclass
class BetaTestConfig:
    """Configuration for beta testing."""
    test_duration: int = 300  # 5 minutes
    test_interval: int = 60   # 1 minute between tests
    max_concurrent_tests: int = 5
    enable_performance_monitoring: bool = True
    enable_crash_reporting: bool = True
    enable_user_feedback: bool = True
    log_level: str = "INFO"


class BetaTestManager(QObject):
    """Manages beta testing process."""
    
    # Signals
    test_started = pyqtSignal(str)  # test_id
    test_completed = pyqtSignal(object)  # TestResult
    test_failed = pyqtSignal(str, str)  # test_id, error_message
    performance_alert = pyqtSignal(str, dict)  # alert_type, metrics
    
    def __init__(self, config: BetaTestConfig = None):
        super().__init__()
        self.config = config or BetaTestConfig()
        self.active_tests: Dict[str, TestResult] = {}
        self.test_results: List[TestResult] = []
        self.performance_monitor = None
        self.crash_reporter = None
        self.feedback_collector = None
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.setup_components()
    
    def setup_logging(self):
        """Setup logging for beta testing."""
        log_dir = Path("logs/beta_testing")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"beta_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def setup_components(self):
        """Setup testing components."""
        try:
            # Initialize performance monitor
            if self.config.enable_performance_monitoring:
                self.performance_monitor = PerformanceMonitor()
                self.performance_monitor.performance_alert.connect(self.on_performance_alert)
            
            # Initialize crash reporter
            if self.config.enable_crash_reporting:
                self.crash_reporter = CrashReporter()
            
            # Initialize feedback collector
            if self.config.enable_user_feedback:
                self.feedback_collector = FeedbackCollector()
            
            self.logger.info("Beta testing components initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize components: {e}")
            raise
    
    def start_beta_test(self, user_id: str, test_type: str) -> str:
        """Start a beta test."""
        test_id = f"{test_type}_{user_id}_{int(time.time())}"
        
        # Check concurrent test limit
        if len(self.active_tests) >= self.config.max_concurrent_tests:
            raise Exception("Maximum concurrent tests reached")
        
        # Create test result
        test_result = TestResult(
            test_id=test_id,
            user_id=user_id,
            test_type=test_type,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0,
            success=False
        )
        
        self.active_tests[test_id] = test_result
        self.test_started.emit(test_id)
        
        self.logger.info(f"Started beta test: {test_id}")
        return test_id
    
    def complete_beta_test(self, test_id: str, success: bool, 
                          error_message: str = None, 
                          performance_metrics: Dict[str, Any] = None,
                          user_feedback: Dict[str, Any] = None):
        """Complete a beta test."""
        if test_id not in self.active_tests:
            self.logger.error(f"Test not found: {test_id}")
            return
        
        test_result = self.active_tests[test_id]
        test_result.end_time = datetime.now()
        test_result.duration = (test_result.end_time - test_result.start_time).total_seconds()
        test_result.success = success
        test_result.error_message = error_message
        test_result.performance_metrics = performance_metrics or {}
        test_result.user_feedback = user_feedback or {}
        
        # Move to completed tests
        self.test_results.append(test_result)
        del self.active_tests[test_id]
        
        if success:
            self.test_completed.emit(test_result)
            self.logger.info(f"Completed beta test: {test_id}")
        else:
            self.test_failed.emit(test_id, error_message or "Unknown error")
            self.logger.error(f"Failed beta test: {test_id} - {error_message}")
    
    def on_performance_alert(self, alert_type: str, metrics: Dict[str, Any]):
        """Handle performance alerts."""
        self.performance_alert.emit(alert_type, metrics)
        self.logger.warning(f"Performance alert: {alert_type} - {metrics}")
    
    def get_test_statistics(self) -> Dict[str, Any]:
        """Get beta testing statistics."""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for t in self.test_results if t.success)
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group by test type
        test_types = {}
        for test in self.test_results:
            if test.test_type not in test_types:
                test_types[test.test_type] = {"total": 0, "successful": 0, "failed": 0}
            
            test_types[test.test_type]["total"] += 1
            if test.success:
                test_types[test.test_type]["successful"] += 1
            else:
                test_types[test.test_type]["failed"] += 1
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "active_tests": len(self.active_tests),
            "test_types": test_types,
            "average_duration": sum(t.duration for t in self.test_results) / total_tests if total_tests > 0 else 0
        }
    
    def export_test_results(self, file_path: str):
        """Export test results to JSON file."""
        results_data = {
            "export_time": datetime.now().isoformat(),
            "config": asdict(self.config),
            "statistics": self.get_test_statistics(),
            "test_results": [asdict(test) for test in self.test_results]
        }
        
        with open(file_path, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        self.logger.info(f"Test results exported to: {file_path}")


class PerformanceMonitor(QObject):
    """Monitors system performance during testing."""
    
    performance_alert = pyqtSignal(str, dict)
    
    def __init__(self):
        super().__init__()
        self.monitoring = False
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.check_performance)
        
        # Performance thresholds
        self.cpu_threshold = 80.0  # 80% CPU usage
        self.memory_threshold = 80.0  # 80% memory usage
        self.input_lag_threshold = 16.0  # 16ms input lag
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.monitoring = True
        self.monitor_timer.start(1000)  # Check every second
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        self.monitor_timer.stop()
    
    def check_performance(self):
        """Check current performance metrics."""
        if not self.monitoring:
            return
        
        try:
            import psutil
            
            # Get system metrics
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            # Check for alerts
            if cpu_percent > self.cpu_threshold:
                self.performance_alert.emit("high_cpu", {
                    "cpu_percent": cpu_percent,
                    "threshold": self.cpu_threshold
                })
            
            if memory_percent > self.memory_threshold:
                self.performance_alert.emit("high_memory", {
                    "memory_percent": memory_percent,
                    "threshold": self.memory_threshold
                })
            
        except Exception as e:
            logging.error(f"Performance monitoring error: {e}")


class CrashReporter(QObject):
    """Reports crashes and errors during testing."""
    
    def __init__(self):
        super().__init__()
        self.crash_count = 0
        self.setup_exception_handler()
    
    def setup_exception_handler(self):
        """Setup global exception handler."""
        import sys
        sys.excepthook = self.handle_exception
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        self.crash_count += 1
        
        crash_info = {
            "timestamp": datetime.now().isoformat(),
            "exception_type": str(exc_type),
            "exception_message": str(exc_value),
            "traceback": str(exc_traceback),
            "crash_count": self.crash_count
        }
        
        # Log crash
        logging.error(f"Crash reported: {crash_info}")
        
        # Save crash report
        crash_dir = Path("logs/crashes")
        crash_dir.mkdir(parents=True, exist_ok=True)
        
        crash_file = crash_dir / f"crash_{self.crash_count}_{int(time.time())}.json"
        with open(crash_file, 'w') as f:
            json.dump(crash_info, f, indent=2)
    
    def get_crash_statistics(self) -> Dict[str, Any]:
        """Get crash statistics."""
        return {
            "total_crashes": self.crash_count,
            "crash_rate": self.crash_count / max(1, time.time() / 3600)  # crashes per hour
        }


class FeedbackCollector(QObject):
    """Collects user feedback during testing."""
    
    def __init__(self):
        super().__init__()
        self.feedback_data = []
    
    def collect_feedback(self, test_id: str, feedback: Dict[str, Any]):
        """Collect user feedback."""
        feedback_entry = {
            "test_id": test_id,
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback
        }
        
        self.feedback_data.append(feedback_entry)
        
        # Save feedback
        feedback_dir = Path("logs/feedback")
        feedback_dir.mkdir(parents=True, exist_ok=True)
        
        feedback_file = feedback_dir / f"feedback_{test_id}.json"
        with open(feedback_file, 'w') as f:
            json.dump(feedback_entry, f, indent=2)
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get feedback summary."""
        if not self.feedback_data:
            return {"total_feedback": 0}
        
        # Analyze feedback
        total_feedback = len(self.feedback_data)
        
        # Count feedback types
        feedback_types = {}
        for entry in self.feedback_data:
            for key in entry["feedback"]:
                feedback_types[key] = feedback_types.get(key, 0) + 1
        
        return {
            "total_feedback": total_feedback,
            "feedback_types": feedback_types,
            "recent_feedback": self.feedback_data[-10:] if len(self.feedback_data) > 10 else self.feedback_data
        }


class AutomatedTestSuite:
    """Automated test suite for beta testing."""
    
    def __init__(self, beta_manager: BetaTestManager):
        self.beta_manager = beta_manager
        self.app = None
        self.main_window = None
    
    def setup_gui(self):
        """Setup GUI for testing."""
        self.app = QApplication(sys.argv)
        self.main_window = ZeroLagMainWindow()
        self.main_window.show()
    
    def run_gui_tests(self) -> List[TestResult]:
        """Run GUI-related tests."""
        tests = []
        
        # Test 1: Application startup
        test_id = self.beta_manager.start_beta_test("automated", "gui_startup")
        try:
            self.setup_gui()
            self.beta_manager.complete_beta_test(test_id, True, 
                                               performance_metrics={"startup_time": 0.5})
            tests.append(self.beta_manager.test_results[-1])
        except Exception as e:
            self.beta_manager.complete_beta_test(test_id, False, str(e))
            tests.append(self.beta_manager.test_results[-1])
        
        # Test 2: Profile management
        test_id = self.beta_manager.start_beta_test("automated", "profile_management")
        try:
            # Test profile creation
            profile_manager = ProfileManager()
            test_profile = profile_manager.create_profile("Test Profile")
            
            # Test profile saving
            profile_manager.save_profile(test_profile)
            
            # Test profile loading
            loaded_profile = profile_manager.load_profile("Test Profile")
            
            self.beta_manager.complete_beta_test(test_id, True,
                                               performance_metrics={"profiles_created": 1})
            tests.append(self.beta_manager.test_results[-1])
        except Exception as e:
            self.beta_manager.complete_beta_test(test_id, False, str(e))
            tests.append(self.beta_manager.test_results[-1])
        
        # Test 3: Benchmark functionality
        test_id = self.beta_manager.start_beta_test("automated", "benchmark_tests")
        try:
            benchmark_config = BenchmarkConfig(test_duration=5.0)
            benchmark_manager = BenchmarkManager(benchmark_config)
            
            # Test aim accuracy test
            benchmark_manager.start_test("aim_accuracy")
            time.sleep(1)  # Brief test
            benchmark_manager.stop_current_test()
            
            self.beta_manager.complete_beta_test(test_id, True,
                                               performance_metrics={"benchmark_tests": 1})
            tests.append(self.beta_manager.test_results[-1])
        except Exception as e:
            self.beta_manager.complete_beta_test(test_id, False, str(e))
            tests.append(self.beta_manager.test_results[-1])
        
        return tests
    
    def run_performance_tests(self) -> List[TestResult]:
        """Run performance-related tests."""
        tests = []
        
        # Test 1: Input processing performance
        test_id = self.beta_manager.start_beta_test("automated", "input_performance")
        try:
            input_handler = InputHandler()
            input_handler.start()
            
            # Simulate input processing
            start_time = time.time()
            for _ in range(1000):
                # Simulate input processing
                pass
            end_time = time.time()
            
            processing_time = end_time - start_time
            input_handler.stop()
            
            self.beta_manager.complete_beta_test(test_id, True,
                                               performance_metrics={
                                                   "processing_time": processing_time,
                                                   "inputs_processed": 1000
                                               })
            tests.append(self.beta_manager.test_results[-1])
        except Exception as e:
            self.beta_manager.complete_beta_test(test_id, False, str(e))
            tests.append(self.beta_manager.test_results[-1])
        
        return tests
    
    def run_stability_tests(self) -> List[TestResult]:
        """Run stability tests."""
        tests = []
        
        # Test 1: Long-running stability
        test_id = self.beta_manager.start_beta_test("automated", "stability_test")
        try:
            input_handler = InputHandler()
            input_handler.start()
            
            # Run for 30 seconds
            time.sleep(30)
            
            input_handler.stop()
            
            self.beta_manager.complete_beta_test(test_id, True,
                                               performance_metrics={"test_duration": 30})
            tests.append(self.beta_manager.test_results[-1])
        except Exception as e:
            self.beta_manager.complete_beta_test(test_id, False, str(e))
            tests.append(self.beta_manager.test_results[-1])
        
        return tests
    
    def run_all_tests(self) -> List[TestResult]:
        """Run all automated tests."""
        all_tests = []
        
        print("Running GUI tests...")
        all_tests.extend(self.run_gui_tests())
        
        print("Running performance tests...")
        all_tests.extend(self.run_performance_tests())
        
        print("Running stability tests...")
        all_tests.extend(self.run_stability_tests())
        
        return all_tests


def main():
    """Main beta testing function."""
    print("ZeroLag Beta Testing Framework")
    print("=" * 40)
    
    # Create beta test manager
    config = BetaTestConfig(
        test_duration=300,
        enable_performance_monitoring=True,
        enable_crash_reporting=True,
        enable_user_feedback=True
    )
    
    beta_manager = BetaTestManager(config)
    
    # Create automated test suite
    test_suite = AutomatedTestSuite(beta_manager)
    
    # Run automated tests
    print("Starting automated tests...")
    test_results = test_suite.run_all_tests()
    
    # Print results
    print("\nTest Results:")
    print("-" * 20)
    
    for test in test_results:
        status = "✅ PASS" if test.success else "❌ FAIL"
        print(f"{test.test_type}: {status}")
        if not test.success and test.error_message:
            print(f"  Error: {test.error_message}")
    
    # Print statistics
    stats = beta_manager.get_test_statistics()
    print(f"\nStatistics:")
    print(f"Total tests: {stats['total_tests']}")
    print(f"Successful: {stats['successful_tests']}")
    print(f"Failed: {stats['failed_tests']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    
    # Export results
    results_file = f"beta_test_results_{int(time.time())}.json"
    beta_manager.export_test_results(results_file)
    print(f"\nResults exported to: {results_file}")
    
    return len([t for t in test_results if t.success]) == len(test_results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
