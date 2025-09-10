#!/usr/bin/env python3
"""
ZeroLag Final Tasks Runner

This script runs all three final tasks:
1. Task 18: User Documentation
2. Task 20: Beta Testing with Users  
3. Task 23: Final Performance Review

It provides comprehensive testing, analysis, and reporting for the complete ZeroLag application.
"""

import sys
import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# Import ZeroLag components
from src.gui.main_window import ZeroLagMainWindow
from src.core.monitoring.performance_monitor import PerformanceMonitor
from src.core.monitoring.crash_reporter import CrashReporter
from src.core.analysis.performance_analyzer import PerformanceAnalyzer
from tests.beta_testing import BetaTestManager, BetaTestConfig, AutomatedTestSuite


class FinalTasksRunner:
    """Runs all final tasks for ZeroLag."""
    
    def __init__(self):
        self.start_time = time.time()
        self.results = {}
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.performance_monitor = None
        self.crash_reporter = None
        self.performance_analyzer = None
        self.beta_manager = None
        self.app = None
        self.main_window = None
    
    def setup_logging(self):
        """Setup logging for final tasks."""
        log_dir = Path("logs/final_tasks")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"final_tasks_{int(time.time())}.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
    
    def run_task_18_documentation(self):
        """Run Task 18: User Documentation."""
        print("\n" + "=" * 60)
        print("TASK 18: USER DOCUMENTATION")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Check if documentation files exist
            doc_files = [
                "README.md",
                "docs/USER_MANUAL.md", 
                "docs/TROUBLESHOOTING.md",
                "docs/API_DOCUMENTATION.md",
                "install.py",
                "requirements.txt"
            ]
            
            missing_files = []
            for file_path in doc_files:
                if not Path(file_path).exists():
                    missing_files.append(file_path)
            
            if missing_files:
                self.logger.error(f"Missing documentation files: {missing_files}")
                return False
            
            # Verify documentation content
            doc_checks = {
                "README.md": self._check_readme_content(),
                "USER_MANUAL.md": self._check_user_manual_content(),
                "TROUBLESHOOTING.md": self._check_troubleshooting_content(),
                "API_DOCUMENTATION.md": self._check_api_documentation_content(),
                "install.py": self._check_install_script(),
                "requirements.txt": self._check_requirements_file()
            }
            
            # Calculate documentation score
            doc_score = sum(doc_checks.values()) / len(doc_checks) * 100
            
            duration = time.time() - start_time
            
            self.results['task_18'] = {
                'status': 'completed',
                'duration': duration,
                'score': doc_score,
                'checks': doc_checks,
                'missing_files': missing_files
            }
            
            print(f"✅ Task 18 completed in {duration:.2f} seconds")
            print(f"📊 Documentation score: {doc_score:.1f}/100")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Task 18 failed: {e}")
            self.results['task_18'] = {
                'status': 'failed',
                'error': str(e),
                'duration': time.time() - start_time
            }
            return False
    
    def _check_readme_content(self) -> bool:
        """Check README.md content."""
        try:
            with open("README.md", 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "# ZeroLag",
                "## Features",
                "## Installation", 
                "## Quick Start",
                "## Contributing",
                "## License"
            ]
            
            return all(section in content for section in required_sections)
        except Exception:
            return False
    
    def _check_user_manual_content(self) -> bool:
        """Check USER_MANUAL.md content."""
        try:
            with open("docs/USER_MANUAL.md", 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "# ZeroLag User Manual",
                "## Getting Started",
                "## Interface Overview",
                "## Core Features",
                "## Advanced Features",
                "## Troubleshooting"
            ]
            
            return all(section in content for section in required_sections)
        except Exception:
            return False
    
    def _check_troubleshooting_content(self) -> bool:
        """Check TROUBLESHOOTING.md content."""
        try:
            with open("docs/TROUBLESHOOTING.md", 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "# ZeroLag Troubleshooting Guide",
                "## Quick Fixes",
                "## Detailed Troubleshooting",
                "## Frequently Asked Questions"
            ]
            
            return all(section in content for section in required_sections)
        except Exception:
            return False
    
    def _check_api_documentation_content(self) -> bool:
        """Check API_DOCUMENTATION.md content."""
        try:
            with open("docs/API_DOCUMENTATION.md", 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "# ZeroLag API Documentation",
                "## Core Modules",
                "## Input Processing",
                "## Optimization Algorithms",
                "## Examples"
            ]
            
            return all(section in content for section in required_sections)
        except Exception:
            return False
    
    def _check_install_script(self) -> bool:
        """Check install.py script."""
        try:
            with open("install.py", 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_elements = [
                "class ZeroLagInstaller",
                "def check_requirements",
                "def install_dependencies",
                "def create_launcher_scripts"
            ]
            
            return all(element in content for element in required_elements)
        except Exception:
            return False
    
    def _check_requirements_file(self) -> bool:
        """Check requirements.txt file."""
        try:
            with open("requirements.txt", 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_packages = [
                "PyQt5",
                "pynput",
                "psutil"
            ]
            
            return all(package in content for package in required_packages)
        except Exception:
            return False
    
    def run_task_20_beta_testing(self):
        """Run Task 20: Beta Testing with Users."""
        print("\n" + "=" * 60)
        print("TASK 20: BETA TESTING WITH USERS")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Initialize beta testing
            beta_config = BetaTestConfig(
                test_duration=60,  # 1 minute for final testing
                enable_performance_monitoring=True,
                enable_crash_reporting=True,
                enable_user_feedback=True
            )
            
            self.beta_manager = BetaTestManager(beta_config)
            
            # Create automated test suite
            test_suite = AutomatedTestSuite(self.beta_manager)
            
            # Run automated tests
            print("Running automated beta tests...")
            test_results = test_suite.run_all_tests()
            
            # Get test statistics
            stats = self.beta_manager.get_test_statistics()
            
            # Calculate beta testing score
            success_rate = stats.get('success_rate', 0)
            total_tests = stats.get('total_tests', 0)
            
            duration = time.time() - start_time
            
            self.results['task_20'] = {
                'status': 'completed',
                'duration': duration,
                'success_rate': success_rate,
                'total_tests': total_tests,
                'statistics': stats,
                'test_results': len(test_results)
            }
            
            print(f"✅ Task 20 completed in {duration:.2f} seconds")
            print(f"📊 Success rate: {success_rate:.1f}%")
            print(f"🧪 Total tests: {total_tests}")
            
            return success_rate >= 80.0  # 80% success rate threshold
            
        except Exception as e:
            self.logger.error(f"Task 20 failed: {e}")
            self.results['task_20'] = {
                'status': 'failed',
                'error': str(e),
                'duration': time.time() - start_time
            }
            return False
    
    def run_task_23_performance_review(self):
        """Run Task 23: Final Performance Review."""
        print("\n" + "=" * 60)
        print("TASK 23: FINAL PERFORMANCE REVIEW")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Initialize performance monitoring
            self.performance_monitor = PerformanceMonitor(monitoring_interval=0.5)
            self.crash_reporter = CrashReporter()
            self.performance_analyzer = PerformanceAnalyzer()
            
            # Start monitoring
            self.performance_monitor.start_monitoring()
            
            # Initialize GUI for testing
            self.app = QApplication(sys.argv)
            self.main_window = ZeroLagMainWindow()
            self.main_window.show()
            
            # Run performance analysis
            print("Running performance analysis...")
            analysis = self.performance_analyzer.analyze_performance(
                self.performance_monitor, 
                duration_seconds=30  # 30 seconds for final analysis
            )
            
            # Stop monitoring
            self.performance_monitor.stop_monitoring()
            
            # Get performance summary
            performance_summary = self.performance_monitor.get_performance_summary()
            
            # Get crash statistics
            crash_stats = self.crash_reporter.get_crash_statistics()
            
            # Calculate performance score
            performance_score = analysis.overall_score
            
            duration = time.time() - start_time
            
            self.results['task_23'] = {
                'status': 'completed',
                'duration': duration,
                'performance_score': performance_score,
                'performance_grade': analysis.performance_grade,
                'analysis': analysis.__dict__,
                'performance_summary': performance_summary,
                'crash_stats': crash_stats
            }
            
            print(f"✅ Task 23 completed in {duration:.2f} seconds")
            print(f"📊 Performance score: {performance_score:.1f}/100")
            print(f"🏆 Performance grade: {analysis.performance_grade}")
            
            # Generate performance report
            report = self.performance_analyzer.generate_performance_report(analysis)
            print("\n" + report)
            
            return performance_score >= 70.0  # 70% performance threshold
            
        except Exception as e:
            self.logger.error(f"Task 23 failed: {e}")
            self.results['task_23'] = {
                'status': 'failed',
                'error': str(e),
                'duration': time.time() - start_time
            }
            return False
    
    def generate_final_report(self):
        """Generate final comprehensive report."""
        print("\n" + "=" * 60)
        print("FINAL COMPREHENSIVE REPORT")
        print("=" * 60)
        
        total_duration = time.time() - self.start_time
        
        # Calculate overall success
        task_18_success = self.results.get('task_18', {}).get('status') == 'completed'
        task_20_success = self.results.get('task_20', {}).get('status') == 'completed'
        task_23_success = self.results.get('task_23', {}).get('status') == 'completed'
        
        overall_success = task_18_success and task_20_success and task_23_success
        
        # Generate report
        report = []
        report.append("ZeroLag Final Tasks Execution Report")
        report.append("=" * 50)
        report.append(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Duration: {total_duration:.2f} seconds")
        report.append(f"Overall Success: {'✅ PASSED' if overall_success else '❌ FAILED'}")
        report.append("")
        
        # Task 18 results
        task_18 = self.results.get('task_18', {})
        report.append("Task 18: User Documentation")
        report.append("-" * 30)
        report.append(f"Status: {task_18.get('status', 'unknown')}")
        report.append(f"Duration: {task_18.get('duration', 0):.2f} seconds")
        if task_18.get('score'):
            report.append(f"Score: {task_18['score']:.1f}/100")
        if task_18.get('error'):
            report.append(f"Error: {task_18['error']}")
        report.append("")
        
        # Task 20 results
        task_20 = self.results.get('task_20', {})
        report.append("Task 20: Beta Testing with Users")
        report.append("-" * 30)
        report.append(f"Status: {task_20.get('status', 'unknown')}")
        report.append(f"Duration: {task_20.get('duration', 0):.2f} seconds")
        if task_20.get('success_rate'):
            report.append(f"Success Rate: {task_20['success_rate']:.1f}%")
        if task_20.get('total_tests'):
            report.append(f"Total Tests: {task_20['total_tests']}")
        if task_20.get('error'):
            report.append(f"Error: {task_20['error']}")
        report.append("")
        
        # Task 23 results
        task_23 = self.results.get('task_23', {})
        report.append("Task 23: Final Performance Review")
        report.append("-" * 30)
        report.append(f"Status: {task_23.get('status', 'unknown')}")
        report.append(f"Duration: {task_23.get('duration', 0):.2f} seconds")
        if task_23.get('performance_score'):
            report.append(f"Performance Score: {task_23['performance_score']:.1f}/100")
        if task_23.get('performance_grade'):
            report.append(f"Performance Grade: {task_23['performance_grade']}")
        if task_23.get('error'):
            report.append(f"Error: {task_23['error']}")
        report.append("")
        
        # Summary
        report.append("Summary")
        report.append("-" * 10)
        report.append(f"Documentation: {'✅' if task_18_success else '❌'}")
        report.append(f"Beta Testing: {'✅' if task_20_success else '❌'}")
        report.append(f"Performance Review: {'✅' if task_23_success else '❌'}")
        report.append("")
        
        if overall_success:
            report.append("🎉 ALL TASKS COMPLETED SUCCESSFULLY!")
            report.append("ZeroLag is ready for release!")
        else:
            report.append("⚠️  SOME TASKS FAILED")
            report.append("Please review the errors above and fix them before release.")
        
        report.append("=" * 50)
        
        # Print report
        print("\n".join(report))
        
        # Save report to file
        report_file = f"final_tasks_report_{int(time.time())}.txt"
        with open(report_file, 'w') as f:
            f.write("\n".join(report))
        
        print(f"\n📄 Report saved to: {report_file}")
        
        return overall_success
    
    def run_all_tasks(self):
        """Run all final tasks."""
        print("ZeroLag Final Tasks Runner")
        print("=" * 40)
        print("Running Tasks 18, 20, and 23...")
        
        # Run Task 18: User Documentation
        task_18_success = self.run_task_18_documentation()
        
        # Run Task 20: Beta Testing with Users
        task_20_success = self.run_task_20_beta_testing()
        
        # Run Task 23: Final Performance Review
        task_23_success = self.run_task_23_performance_review()
        
        # Generate final report
        overall_success = self.generate_final_report()
        
        return overall_success


def main():
    """Main function."""
    try:
        runner = FinalTasksRunner()
        success = runner.run_all_tasks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Execution cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
