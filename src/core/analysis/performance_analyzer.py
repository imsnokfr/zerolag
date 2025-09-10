"""
Performance analysis system for ZeroLag.

This module provides comprehensive performance analysis capabilities
including benchmarking, optimization recommendations, and performance reports.
"""

import time
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging

from src.core.monitoring.performance_monitor import PerformanceMonitor, PerformanceMetrics
from src.core.benchmark import BenchmarkManager, BenchmarkConfig


@dataclass
class PerformanceAnalysis:
    """Performance analysis results."""
    analysis_id: str
    timestamp: float
    duration_seconds: float
    overall_score: float
    performance_grade: str  # A+, A, B+, B, C+, C, D, F
    metrics_summary: Dict[str, Any]
    optimization_recommendations: List[Dict[str, Any]]
    stability_assessment: Dict[str, Any]
    bottleneck_analysis: Dict[str, Any]
    improvement_potential: Dict[str, Any]


@dataclass
class OptimizationRecommendation:
    """Optimization recommendation."""
    category: str  # cpu, memory, input, gpu, system
    priority: str  # low, medium, high, critical
    title: str
    description: str
    current_value: float
    target_value: float
    potential_improvement: float
    implementation_effort: str  # low, medium, high
    risk_level: str  # low, medium, high


class PerformanceAnalyzer:
    """Comprehensive performance analysis system."""
    
    def __init__(self, analysis_dir: str = "logs/analysis"):
        """
        Initialize performance analyzer.
        
        Args:
            analysis_dir: Directory to store analysis results
        """
        self.analysis_dir = Path(analysis_dir)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Performance benchmarks
        self.benchmarks = {
            'excellent': {'cpu_percent': 30, 'memory_percent': 50, 'input_lag_ms': 8, 'frame_rate_fps': 60},
            'good': {'cpu_percent': 50, 'memory_percent': 70, 'input_lag_ms': 12, 'frame_rate_fps': 45},
            'average': {'cpu_percent': 70, 'memory_percent': 85, 'input_lag_ms': 16, 'frame_rate_fps': 30},
            'poor': {'cpu_percent': 90, 'memory_percent': 95, 'input_lag_ms': 25, 'frame_rate_fps': 15}
        }
    
    def analyze_performance(self, performance_monitor: PerformanceMonitor, 
                          duration_seconds: int = 300) -> PerformanceAnalysis:
        """
        Perform comprehensive performance analysis.
        
        Args:
            performance_monitor: Performance monitor instance
            duration_seconds: Analysis duration in seconds
            
        Returns:
            PerformanceAnalysis object with results
        """
        analysis_id = f"analysis_{int(time.time())}"
        start_time = time.time()
        
        self.logger.info(f"Starting performance analysis: {analysis_id}")
        
        # Collect performance data
        metrics_history = performance_monitor.get_metrics_history(duration_seconds)
        if not metrics_history:
            raise ValueError("No performance data available for analysis")
        
        # Analyze metrics
        metrics_summary = self._analyze_metrics(metrics_history)
        
        # Generate optimization recommendations
        recommendations = self._generate_recommendations(metrics_summary)
        
        # Assess stability
        stability_assessment = self._assess_stability(metrics_history)
        
        # Analyze bottlenecks
        bottleneck_analysis = self._analyze_bottlenecks(metrics_history)
        
        # Calculate improvement potential
        improvement_potential = self._calculate_improvement_potential(metrics_summary)
        
        # Calculate overall score and grade
        overall_score = self._calculate_overall_score(metrics_summary, stability_assessment)
        performance_grade = self._calculate_performance_grade(overall_score)
        
        # Create analysis result
        analysis = PerformanceAnalysis(
            analysis_id=analysis_id,
            timestamp=start_time,
            duration_seconds=duration_seconds,
            overall_score=overall_score,
            performance_grade=performance_grade,
            metrics_summary=metrics_summary,
            optimization_recommendations=recommendations,
            stability_assessment=stability_assessment,
            bottleneck_analysis=bottleneck_analysis,
            improvement_potential=improvement_potential
        )
        
        # Save analysis
        self._save_analysis(analysis)
        
        self.logger.info(f"Performance analysis completed: {analysis_id} (Score: {overall_score:.1f}, Grade: {performance_grade})")
        
        return analysis
    
    def _analyze_metrics(self, metrics_history: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze performance metrics."""
        if not metrics_history:
            return {}
        
        # Calculate statistics for each metric
        cpu_values = [m.cpu_percent for m in metrics_history]
        memory_values = [m.memory_percent for m in metrics_history]
        input_lag_values = [m.input_lag_ms for m in metrics_history]
        frame_rate_values = [m.frame_rate_fps for m in metrics_history]
        
        return {
            'cpu_percent': {
                'current': cpu_values[-1],
                'average': statistics.mean(cpu_values),
                'min': min(cpu_values),
                'max': max(cpu_values),
                'std_dev': statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0,
                'trend': self._calculate_trend(cpu_values)
            },
            'memory_percent': {
                'current': memory_values[-1],
                'average': statistics.mean(memory_values),
                'min': min(memory_values),
                'max': max(memory_values),
                'std_dev': statistics.stdev(memory_values) if len(memory_values) > 1 else 0,
                'trend': self._calculate_trend(memory_values)
            },
            'input_lag_ms': {
                'current': input_lag_values[-1],
                'average': statistics.mean(input_lag_values),
                'min': min(input_lag_values),
                'max': max(input_lag_values),
                'std_dev': statistics.stdev(input_lag_values) if len(input_lag_values) > 1 else 0,
                'trend': self._calculate_trend(input_lag_values)
            },
            'frame_rate_fps': {
                'current': frame_rate_values[-1],
                'average': statistics.mean(frame_rate_values),
                'min': min(frame_rate_values),
                'max': max(frame_rate_values),
                'std_dev': statistics.stdev(frame_rate_values) if len(frame_rate_values) > 1 else 0,
                'trend': self._calculate_trend(frame_rate_values)
            },
            'data_points': len(metrics_history),
            'analysis_duration': (metrics_history[-1].timestamp - metrics_history[0].timestamp) if len(metrics_history) > 1 else 0
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction."""
        if len(values) < 2:
            return "stable"
        
        # Simple linear trend calculation
        n = len(values)
        x = list(range(n))
        
        # Calculate slope
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return "increasing"
        elif slope < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_recommendations(self, metrics_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # CPU recommendations
        cpu_avg = metrics_summary.get('cpu_percent', {}).get('average', 0)
        if cpu_avg > 70:
            recommendations.append({
                'category': 'cpu',
                'priority': 'high' if cpu_avg > 85 else 'medium',
                'title': 'Optimize CPU Usage',
                'description': f'CPU usage is high at {cpu_avg:.1f}%. Consider closing unnecessary applications or reducing ZeroLag features.',
                'current_value': cpu_avg,
                'target_value': 50.0,
                'potential_improvement': cpu_avg - 50.0,
                'implementation_effort': 'low',
                'risk_level': 'low'
            })
        
        # Memory recommendations
        memory_avg = metrics_summary.get('memory_percent', {}).get('average', 0)
        if memory_avg > 80:
            recommendations.append({
                'category': 'memory',
                'priority': 'high' if memory_avg > 90 else 'medium',
                'title': 'Optimize Memory Usage',
                'description': f'Memory usage is high at {memory_avg:.1f}%. Consider reducing memory-intensive features or closing other applications.',
                'current_value': memory_avg,
                'target_value': 70.0,
                'potential_improvement': memory_avg - 70.0,
                'implementation_effort': 'medium',
                'risk_level': 'low'
            })
        
        # Input lag recommendations
        input_lag_avg = metrics_summary.get('input_lag_ms', {}).get('average', 0)
        if input_lag_avg > 16:
            recommendations.append({
                'category': 'input',
                'priority': 'high' if input_lag_avg > 25 else 'medium',
                'title': 'Reduce Input Lag',
                'description': f'Input lag is high at {input_lag_avg:.1f}ms. Consider optimizing system settings or reducing input processing complexity.',
                'current_value': input_lag_avg,
                'target_value': 12.0,
                'potential_improvement': input_lag_avg - 12.0,
                'implementation_effort': 'high',
                'risk_level': 'medium'
            })
        
        # Frame rate recommendations
        frame_rate_avg = metrics_summary.get('frame_rate_fps', {}).get('average', 0)
        if frame_rate_avg < 30:
            recommendations.append({
                'category': 'gpu',
                'priority': 'high' if frame_rate_avg < 15 else 'medium',
                'title': 'Improve Frame Rate',
                'description': f'Frame rate is low at {frame_rate_avg:.1f} FPS. Consider optimizing graphics settings or updating drivers.',
                'current_value': frame_rate_avg,
                'target_value': 45.0,
                'potential_improvement': 45.0 - frame_rate_avg,
                'implementation_effort': 'medium',
                'risk_level': 'low'
            })
        
        return recommendations
    
    def _assess_stability(self, metrics_history: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Assess system stability."""
        if not metrics_history:
            return {"stability_score": 0, "issues": []}
        
        issues = []
        stability_score = 100.0
        
        # Check for high variance in metrics
        cpu_values = [m.cpu_percent for m in metrics_history]
        memory_values = [m.memory_percent for m in metrics_history]
        
        cpu_std = statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0
        memory_std = statistics.stdev(memory_values) if len(memory_values) > 1 else 0
        
        if cpu_std > 20:
            issues.append("High CPU usage variance")
            stability_score -= 20
        
        if memory_std > 15:
            issues.append("High memory usage variance")
            stability_score -= 15
        
        # Check for extreme values
        cpu_max = max(cpu_values)
        memory_max = max(memory_values)
        
        if cpu_max > 95:
            issues.append("CPU usage reached critical levels")
            stability_score -= 25
        
        if memory_max > 95:
            issues.append("Memory usage reached critical levels")
            stability_score -= 25
        
        # Check for trends
        cpu_trend = self._calculate_trend(cpu_values)
        memory_trend = self._calculate_trend(memory_values)
        
        if cpu_trend == "increasing":
            issues.append("CPU usage is increasing over time")
            stability_score -= 10
        
        if memory_trend == "increasing":
            issues.append("Memory usage is increasing over time")
            stability_score -= 10
        
        return {
            "stability_score": max(0, stability_score),
            "issues": issues,
            "cpu_variance": cpu_std,
            "memory_variance": memory_std,
            "cpu_trend": cpu_trend,
            "memory_trend": memory_trend
        }
    
    def _analyze_bottlenecks(self, metrics_history: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Analyze performance bottlenecks."""
        if not metrics_history:
            return {"bottlenecks": [], "primary_bottleneck": None}
        
        bottlenecks = []
        
        # Analyze each metric for bottlenecks
        cpu_values = [m.cpu_percent for m in metrics_history]
        memory_values = [m.memory_percent for m in metrics_history]
        input_lag_values = [m.input_lag_ms for m in metrics_history]
        frame_rate_values = [m.frame_rate_fps for m in metrics_history]
        
        # CPU bottleneck
        cpu_avg = statistics.mean(cpu_values)
        if cpu_avg > 80:
            bottlenecks.append({
                'type': 'cpu',
                'severity': 'high' if cpu_avg > 90 else 'medium',
                'average_value': cpu_avg,
                'threshold': 80,
                'description': 'CPU is the primary performance bottleneck'
            })
        
        # Memory bottleneck
        memory_avg = statistics.mean(memory_values)
        if memory_avg > 85:
            bottlenecks.append({
                'type': 'memory',
                'severity': 'high' if memory_avg > 95 else 'medium',
                'average_value': memory_avg,
                'threshold': 85,
                'description': 'Memory is a performance bottleneck'
            })
        
        # Input lag bottleneck
        input_lag_avg = statistics.mean(input_lag_values)
        if input_lag_avg > 16:
            bottlenecks.append({
                'type': 'input_lag',
                'severity': 'high' if input_lag_avg > 25 else 'medium',
                'average_value': input_lag_avg,
                'threshold': 16,
                'description': 'Input lag is limiting performance'
            })
        
        # Frame rate bottleneck
        frame_rate_avg = statistics.mean(frame_rate_values)
        if frame_rate_avg < 30:
            bottlenecks.append({
                'type': 'frame_rate',
                'severity': 'high' if frame_rate_avg < 15 else 'medium',
                'average_value': frame_rate_avg,
                'threshold': 30,
                'description': 'Low frame rate is limiting performance'
            })
        
        # Determine primary bottleneck
        primary_bottleneck = None
        if bottlenecks:
            # Sort by severity and impact
            severity_order = {'high': 3, 'medium': 2, 'low': 1}
            bottlenecks.sort(key=lambda x: severity_order.get(x['severity'], 0), reverse=True)
            primary_bottleneck = bottlenecks[0]
        
        return {
            "bottlenecks": bottlenecks,
            "primary_bottleneck": primary_bottleneck,
            "bottleneck_count": len(bottlenecks)
        }
    
    def _calculate_improvement_potential(self, metrics_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate improvement potential for each metric."""
        improvement_potential = {}
        
        # CPU improvement potential
        cpu_avg = metrics_summary.get('cpu_percent', {}).get('average', 0)
        if cpu_avg > 50:
            improvement_potential['cpu'] = {
                'current': cpu_avg,
                'target': 50.0,
                'improvement': cpu_avg - 50.0,
                'improvement_percent': ((cpu_avg - 50.0) / cpu_avg) * 100
            }
        
        # Memory improvement potential
        memory_avg = metrics_summary.get('memory_percent', {}).get('average', 0)
        if memory_avg > 70:
            improvement_potential['memory'] = {
                'current': memory_avg,
                'target': 70.0,
                'improvement': memory_avg - 70.0,
                'improvement_percent': ((memory_avg - 70.0) / memory_avg) * 100
            }
        
        # Input lag improvement potential
        input_lag_avg = metrics_summary.get('input_lag_ms', {}).get('average', 0)
        if input_lag_avg > 12:
            improvement_potential['input_lag'] = {
                'current': input_lag_avg,
                'target': 12.0,
                'improvement': input_lag_avg - 12.0,
                'improvement_percent': ((input_lag_avg - 12.0) / input_lag_avg) * 100
            }
        
        # Frame rate improvement potential
        frame_rate_avg = metrics_summary.get('frame_rate_fps', {}).get('average', 0)
        if frame_rate_avg < 45:
            improvement_potential['frame_rate'] = {
                'current': frame_rate_avg,
                'target': 45.0,
                'improvement': 45.0 - frame_rate_avg,
                'improvement_percent': ((45.0 - frame_rate_avg) / 45.0) * 100
            }
        
        return improvement_potential
    
    def _calculate_overall_score(self, metrics_summary: Dict[str, Any], 
                               stability_assessment: Dict[str, Any]) -> float:
        """Calculate overall performance score."""
        score = 100.0
        
        # CPU score (25% weight)
        cpu_avg = metrics_summary.get('cpu_percent', {}).get('average', 0)
        cpu_score = max(0, 100 - (cpu_avg - 30) * 2)  # 30% = 100, 80% = 0
        score += cpu_score * 0.25
        
        # Memory score (25% weight)
        memory_avg = metrics_summary.get('memory_percent', {}).get('average', 0)
        memory_score = max(0, 100 - (memory_avg - 50) * 2)  # 50% = 100, 100% = 0
        score += memory_score * 0.25
        
        # Input lag score (25% weight)
        input_lag_avg = metrics_summary.get('input_lag_ms', {}).get('average', 0)
        input_lag_score = max(0, 100 - (input_lag_avg - 8) * 5)  # 8ms = 100, 28ms = 0
        score += input_lag_score * 0.25
        
        # Frame rate score (25% weight)
        frame_rate_avg = metrics_summary.get('frame_rate_fps', {}).get('average', 0)
        frame_rate_score = min(100, frame_rate_avg * 1.67)  # 60 FPS = 100
        score += frame_rate_score * 0.25
        
        # Stability penalty
        stability_score = stability_assessment.get('stability_score', 100)
        score = (score + stability_score) / 2
        
        return max(0, min(100, score))
    
    def _calculate_performance_grade(self, score: float) -> str:
        """Calculate performance grade from score."""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _save_analysis(self, analysis: PerformanceAnalysis):
        """Save analysis to file."""
        analysis_file = self.analysis_dir / f"{analysis.analysis_id}.json"
        
        try:
            with open(analysis_file, 'w') as f:
                json.dump(asdict(analysis), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save analysis: {e}")
    
    def get_analysis_history(self) -> List[PerformanceAnalysis]:
        """Get analysis history."""
        analyses = []
        
        for analysis_file in self.analysis_dir.glob("analysis_*.json"):
            try:
                with open(analysis_file, 'r') as f:
                    analysis_data = json.load(f)
                    analysis = PerformanceAnalysis(**analysis_data)
                    analyses.append(analysis)
            except Exception as e:
                self.logger.error(f"Failed to load analysis: {e}")
        
        # Sort by timestamp
        analyses.sort(key=lambda x: x.timestamp)
        
        return analyses
    
    def generate_performance_report(self, analysis: PerformanceAnalysis) -> str:
        """Generate human-readable performance report."""
        report = []
        report.append("=" * 60)
        report.append("ZeroLag Performance Analysis Report")
        report.append("=" * 60)
        report.append(f"Analysis ID: {analysis.analysis_id}")
        report.append(f"Timestamp: {datetime.fromtimestamp(analysis.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Duration: {analysis.duration_seconds} seconds")
        report.append(f"Overall Score: {analysis.overall_score:.1f}/100")
        report.append(f"Performance Grade: {analysis.performance_grade}")
        report.append("")
        
        # Metrics summary
        report.append("Performance Metrics Summary:")
        report.append("-" * 30)
        metrics = analysis.metrics_summary
        
        if 'cpu_percent' in metrics:
            cpu = metrics['cpu_percent']
            report.append(f"CPU Usage: {cpu['current']:.1f}% (avg: {cpu['average']:.1f}%, min: {cpu['min']:.1f}%, max: {cpu['max']:.1f}%)")
        
        if 'memory_percent' in metrics:
            memory = metrics['memory_percent']
            report.append(f"Memory Usage: {memory['current']:.1f}% (avg: {memory['average']:.1f}%, min: {memory['min']:.1f}%, max: {memory['max']:.1f}%)")
        
        if 'input_lag_ms' in metrics:
            input_lag = metrics['input_lag_ms']
            report.append(f"Input Lag: {input_lag['current']:.1f}ms (avg: {input_lag['average']:.1f}ms, min: {input_lag['min']:.1f}ms, max: {input_lag['max']:.1f}ms)")
        
        if 'frame_rate_fps' in metrics:
            frame_rate = metrics['frame_rate_fps']
            report.append(f"Frame Rate: {frame_rate['current']:.1f} FPS (avg: {frame_rate['average']:.1f} FPS, min: {frame_rate['min']:.1f} FPS, max: {frame_rate['max']:.1f} FPS)")
        
        report.append("")
        
        # Optimization recommendations
        if analysis.optimization_recommendations:
            report.append("Optimization Recommendations:")
            report.append("-" * 30)
            for i, rec in enumerate(analysis.optimization_recommendations, 1):
                report.append(f"{i}. {rec['title']} ({rec['priority'].upper()} priority)")
                report.append(f"   {rec['description']}")
                report.append(f"   Current: {rec['current_value']:.1f}, Target: {rec['target_value']:.1f}")
                report.append(f"   Potential Improvement: {rec['potential_improvement']:.1f}")
                report.append("")
        
        # Stability assessment
        stability = analysis.stability_assessment
        report.append("Stability Assessment:")
        report.append("-" * 30)
        report.append(f"Stability Score: {stability.get('stability_score', 0):.1f}/100")
        
        if stability.get('issues'):
            report.append("Issues Identified:")
            for issue in stability['issues']:
                report.append(f"  - {issue}")
        else:
            report.append("No stability issues detected")
        
        report.append("")
        
        # Bottleneck analysis
        bottlenecks = analysis.bottleneck_analysis
        if bottlenecks.get('bottlenecks'):
            report.append("Performance Bottlenecks:")
            report.append("-" * 30)
            for bottleneck in bottlenecks['bottlenecks']:
                report.append(f"- {bottleneck['description']} ({bottleneck['severity'].upper()} severity)")
        else:
            report.append("No significant bottlenecks detected")
        
        report.append("")
        report.append("=" * 60)
        
        return "\n".join(report)
