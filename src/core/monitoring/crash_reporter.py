"""
Crash reporting system for ZeroLag.

This module provides comprehensive crash reporting capabilities including
exception handling, crash dumps, and automatic reporting.
"""

import sys
import os
import traceback
import json
import time
import threading
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import logging


@dataclass
class CrashReport:
    """Crash report data structure."""
    crash_id: str
    timestamp: float
    exception_type: str
    exception_message: str
    traceback: str
    system_info: Dict[str, Any]
    application_info: Dict[str, Any]
    user_info: Optional[Dict[str, Any]] = None
    context_info: Optional[Dict[str, Any]] = None
    crash_count: int = 1
    severity: str = "medium"  # low, medium, high, critical


@dataclass
class SystemInfo:
    """System information data structure."""
    platform: str
    platform_version: str
    architecture: str
    python_version: str
    cpu_count: int
    memory_total_gb: float
    memory_available_gb: float
    disk_space_gb: float
    gpu_info: Optional[Dict[str, Any]] = None


class CrashReporter:
    """Comprehensive crash reporting system."""
    
    def __init__(self, crash_dir: str = "logs/crashes", max_reports: int = 100):
        """
        Initialize crash reporter.
        
        Args:
            crash_dir: Directory to store crash reports
            max_reports: Maximum number of crash reports to keep
        """
        self.crash_dir = Path(crash_dir)
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        self.max_reports = max_reports
        self.crash_count = 0
        self.crash_reports: List[CrashReport] = []
        self.report_callbacks: List[Callable[[CrashReport], None]] = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Setup exception handlers
        self._setup_exception_handlers()
        
        # Load existing crash reports
        self._load_existing_reports()
    
    def _setup_exception_handlers(self):
        """Setup global exception handlers."""
        # Set up exception hook for uncaught exceptions
        sys.excepthook = self._handle_exception
        
        # Set up thread exception handler
        threading.excepthook = self._handle_thread_exception
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if exc_type is KeyboardInterrupt:
            # Don't report keyboard interrupts
            return
        
        self._create_crash_report(
            exception_type=str(exc_type),
            exception_message=str(exc_value),
            traceback=traceback.format_exception(exc_type, exc_value, exc_traceback)
        )
    
    def _handle_thread_exception(self, args):
        """Handle exceptions in threads."""
        exc_type, exc_value, exc_traceback, thread = args
        
        self._create_crash_report(
            exception_type=str(exc_type),
            exception_message=str(exc_value),
            traceback=traceback.format_exception(exc_type, exc_value, exc_traceback),
            context_info={"thread_name": thread.name if thread else "Unknown"}
        )
    
    def _create_crash_report(self, exception_type: str, exception_message: str, 
                           traceback: List[str], context_info: Optional[Dict[str, Any]] = None):
        """Create a crash report."""
        self.crash_count += 1
        crash_id = f"crash_{self.crash_count}_{int(time.time())}"
        
        # Get system information
        system_info = self._get_system_info()
        
        # Get application information
        application_info = self._get_application_info()
        
        # Create crash report
        crash_report = CrashReport(
            crash_id=crash_id,
            timestamp=time.time(),
            exception_type=exception_type,
            exception_message=exception_message,
            traceback="\n".join(traceback),
            system_info=asdict(system_info),
            application_info=application_info,
            context_info=context_info,
            crash_count=self.crash_count,
            severity=self._determine_severity(exception_type, exception_message)
        )
        
        # Add to reports
        self.crash_reports.append(crash_report)
        
        # Save crash report
        self._save_crash_report(crash_report)
        
        # Notify callbacks
        self._notify_report_callbacks(crash_report)
        
        # Log crash
        self.logger.error(f"Crash reported: {crash_id} - {exception_type}: {exception_message}")
        
        # Clean up old reports
        self._cleanup_old_reports()
    
    def _get_system_info(self) -> SystemInfo:
        """Get system information."""
        import platform
        import psutil
        
        # Get basic system info
        platform_info = platform.platform()
        platform_version = platform.version()
        architecture = platform.architecture()[0]
        python_version = platform.python_version()
        cpu_count = psutil.cpu_count()
        
        # Get memory info
        memory = psutil.virtual_memory()
        memory_total_gb = memory.total / (1024**3)
        memory_available_gb = memory.available / (1024**3)
        
        # Get disk space
        disk_usage = psutil.disk_usage('/')
        disk_space_gb = disk_usage.free / (1024**3)
        
        # Get GPU info (if available)
        gpu_info = self._get_gpu_info()
        
        return SystemInfo(
            platform=platform_info,
            platform_version=platform_version,
            architecture=architecture,
            python_version=python_version,
            cpu_count=cpu_count,
            memory_total_gb=memory_total_gb,
            memory_available_gb=memory_available_gb,
            disk_space_gb=disk_space_gb,
            gpu_info=gpu_info
        )
    
    def _get_gpu_info(self) -> Optional[Dict[str, Any]]:
        """Get GPU information (if available)."""
        try:
            # Try to get GPU info using various methods
            # This is a simplified version - in practice, you'd use
            # libraries like nvidia-ml-py, pynvml, or similar
            return None
        except Exception:
            return None
    
    def _get_application_info(self) -> Dict[str, Any]:
        """Get application information."""
        return {
            "name": "ZeroLag",
            "version": "1.0.0",
            "python_executable": sys.executable,
            "working_directory": os.getcwd(),
            "command_line": sys.argv,
            "environment_variables": dict(os.environ),
            "loaded_modules": list(sys.modules.keys())
        }
    
    def _determine_severity(self, exception_type: str, exception_message: str) -> str:
        """Determine crash severity."""
        # Critical exceptions
        critical_exceptions = [
            "SystemExit", "KeyboardInterrupt", "GeneratorExit",
            "MemoryError", "SystemError", "FatalError"
        ]
        
        if any(exc in exception_type for exc in critical_exceptions):
            return "critical"
        
        # High severity exceptions
        high_exceptions = [
            "ImportError", "ModuleNotFoundError", "AttributeError",
            "NameError", "TypeError", "ValueError"
        ]
        
        if any(exc in exception_type for exc in high_exceptions):
            return "high"
        
        # Medium severity exceptions
        medium_exceptions = [
            "KeyError", "IndexError", "FileNotFoundError",
            "PermissionError", "OSError", "RuntimeError"
        ]
        
        if any(exc in exception_type for exc in medium_exceptions):
            return "medium"
        
        # Default to low severity
        return "low"
    
    def _save_crash_report(self, crash_report: CrashReport):
        """Save crash report to file."""
        report_file = self.crash_dir / f"{crash_report.crash_id}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(asdict(crash_report), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save crash report: {e}")
    
    def _load_existing_reports(self):
        """Load existing crash reports."""
        try:
            for report_file in self.crash_dir.glob("crash_*.json"):
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                    crash_report = CrashReport(**report_data)
                    self.crash_reports.append(crash_report)
            
            # Sort by timestamp
            self.crash_reports.sort(key=lambda x: x.timestamp)
            
            # Update crash count
            if self.crash_reports:
                self.crash_count = max(r.crash_count for r in self.crash_reports)
            
            self.logger.info(f"Loaded {len(self.crash_reports)} existing crash reports")
            
        except Exception as e:
            self.logger.error(f"Failed to load existing crash reports: {e}")
    
    def _cleanup_old_reports(self):
        """Clean up old crash reports."""
        if len(self.crash_reports) <= self.max_reports:
            return
        
        # Remove oldest reports
        reports_to_remove = self.crash_reports[:-self.max_reports]
        
        for report in reports_to_remove:
            report_file = self.crash_dir / f"{report.crash_id}.json"
            if report_file.exists():
                try:
                    report_file.unlink()
                except Exception as e:
                    self.logger.error(f"Failed to remove old crash report: {e}")
        
        # Update reports list
        self.crash_reports = self.crash_reports[-self.max_reports:]
    
    def add_report_callback(self, callback: Callable[[CrashReport], None]):
        """Add crash report callback."""
        self.report_callbacks.append(callback)
    
    def remove_report_callback(self, callback: Callable[[CrashReport], None]):
        """Remove crash report callback."""
        if callback in self.report_callbacks:
            self.report_callbacks.remove(callback)
    
    def _notify_report_callbacks(self, crash_report: CrashReport):
        """Notify all report callbacks."""
        for callback in self.report_callbacks:
            try:
                callback(crash_report)
            except Exception as e:
                self.logger.error(f"Error in crash report callback: {e}")
    
    def get_crash_statistics(self) -> Dict[str, Any]:
        """Get crash statistics."""
        if not self.crash_reports:
            return {"total_crashes": 0}
        
        # Count by severity
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for report in self.crash_reports:
            severity_counts[report.severity] += 1
        
        # Count by exception type
        exception_counts = {}
        for report in self.crash_reports:
            exc_type = report.exception_type
            exception_counts[exc_type] = exception_counts.get(exc_type, 0) + 1
        
        # Get recent crashes
        recent_crashes = self.crash_reports[-10:] if len(self.crash_reports) > 10 else self.crash_reports
        
        return {
            "total_crashes": len(self.crash_reports),
            "crash_count": self.crash_count,
            "severity_counts": severity_counts,
            "exception_counts": exception_counts,
            "recent_crashes": [asdict(r) for r in recent_crashes],
            "crash_rate_per_hour": self._calculate_crash_rate()
        }
    
    def _calculate_crash_rate(self) -> float:
        """Calculate crashes per hour."""
        if not self.crash_reports:
            return 0.0
        
        if len(self.crash_reports) < 2:
            return 0.0
        
        time_span = self.crash_reports[-1].timestamp - self.crash_reports[0].timestamp
        if time_span <= 0:
            return 0.0
        
        hours = time_span / 3600.0
        return len(self.crash_reports) / hours
    
    def get_crash_report(self, crash_id: str) -> Optional[CrashReport]:
        """Get specific crash report by ID."""
        for report in self.crash_reports:
            if report.crash_id == crash_id:
                return report
        return None
    
    def get_recent_crashes(self, count: int = 10) -> List[CrashReport]:
        """Get recent crash reports."""
        return self.crash_reports[-count:] if self.crash_reports else []
    
    def clear_crash_reports(self):
        """Clear all crash reports."""
        # Remove all report files
        for report_file in self.crash_dir.glob("crash_*.json"):
            try:
                report_file.unlink()
            except Exception as e:
                self.logger.error(f"Failed to remove crash report file: {e}")
        
        # Clear reports list
        self.crash_reports.clear()
        self.crash_count = 0
        
        self.logger.info("All crash reports cleared")
    
    def export_crash_reports(self, file_path: str):
        """Export crash reports to file."""
        try:
            with open(file_path, 'w') as f:
                json.dump([asdict(r) for r in self.crash_reports], f, indent=2, default=str)
            self.logger.info(f"Crash reports exported to: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to export crash reports: {e}")
    
    def report_manual_crash(self, exception_type: str, exception_message: str, 
                          traceback: str, context_info: Optional[Dict[str, Any]] = None):
        """Manually report a crash."""
        self._create_crash_report(
            exception_type=exception_type,
            exception_message=exception_message,
            traceback=[traceback],
            context_info=context_info
        )
    
    def test_crash_reporting(self):
        """Test crash reporting system."""
        try:
            # Intentionally cause an exception for testing
            raise ValueError("Test crash for crash reporting system")
        except Exception as e:
            self._create_crash_report(
                exception_type=type(e).__name__,
                exception_message=str(e),
                traceback=traceback.format_exception(type(e), e, e.__traceback__),
                context_info={"test": True}
            )
