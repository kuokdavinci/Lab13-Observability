#!/usr/bin/env python3
"""
Dashboard Helper Functions for Gradio UI
Utility functions to support the observability dashboard
"""

import json
import time
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import httpx
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class LogAnalyzer:
    """Analyze and process log data for dashboard visualization"""
    
    def __init__(self, logs_file: Path = Path("data/logs.jsonl")):
        self.logs_file = logs_file
        self.cache = {}
        self.cache_timestamp = 0
    
    def load_logs(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Load logs with caching support"""
        if not self.logs_file.exists():
            return []
        
        # Check cache validity (refresh every 10 seconds)
        current_time = time.time()
        if (use_cache and 
            current_time - self.cache_timestamp < 10 and 
            'logs' in self.cache):
            return self.cache['logs']
        
        logs = []
        try:
            with open(self.logs_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            log_entry = json.loads(line.strip())
                            logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error loading logs: {e}")
        
        # Update cache
        self.cache['logs'] = logs
        self.cache_timestamp = current_time
        
        return logs
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary metrics from logs"""
        logs = self.load_logs()
        
        if not logs:
            return {
                "total_requests": 0,
                "avg_latency": 0,
                "total_cost": 0,
                "error_rate": 0,
                "avg_quality": 0
            }
        
        df = pd.DataFrame(logs)
        
        # Filter request logs
        request_logs = df[df.get('event') == 'response_sent']
        
        summary = {
            "total_requests": len(request_logs),
            "avg_latency": request_logs['latency_ms'].mean() if 'latency_ms' in request_logs.columns else 0,
            "total_cost": request_logs['cost_usd'].sum() if 'cost_usd' in request_logs.columns else 0,
            "error_rate": len(df[df.get('level') == 'error']) / max(len(df), 1) * 100,
            "avg_quality": request_logs['quality_score'].mean() if 'quality_score' in request_logs.columns else 0
        }
        
        return summary
    
    def get_time_series_data(self, metric: str, window_minutes: int = 60) -> Tuple[List[str], List[float]]:
        """Get time series data for a specific metric"""
        logs = self.load_logs()
        
        if not logs:
            return [], []
        
        df = pd.DataFrame(logs)
        
        # Convert timestamp
        if 'ts' in df.columns:
            df['timestamp'] = pd.to_datetime(df['ts'])
        else:
            return [], []
        
        # Filter recent data
        cutoff = datetime.now(timezone.utc) - pd.Timedelta(minutes=window_minutes)
        recent_df = df[df['timestamp'] > cutoff]
        
        if metric not in recent_df.columns:
            return [], []
        
        # Group by minute and aggregate
        recent_df.set_index('timestamp', inplace=True)
        grouped = recent_df.resample('1min')[metric].mean().dropna()
        
        return grouped.index.strftime('%H:%M:%S').tolist(), grouped.tolist()

class MetricsCollector:
    """Collect and aggregate metrics from various sources"""
    
    def __init__(self, api_base: str = "http://localhost:8000"):
        self.api_base = api_base
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_api_health(self) -> Dict[str, Any]:
        """Get API health status"""
        try:
            response = await self.client.get(f"{self.api_base}/health")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "data": response.json()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }
    
    async def get_prometheus_metrics(self) -> Optional[str]:
        """Get Prometheus metrics from API"""
        try:
            response = await self.client.get(f"{self.api_base}/metrics")
            if response.status_code == 200:
                return response.text
            return None
        except Exception:
            return None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

class DashboardBuilder:
    """Build comprehensive dashboard visualizations"""
    
    def __init__(self):
        self.analyzer = LogAnalyzer()
    
    def create_main_dashboard(self) -> go.Figure:
        """Create the main 6-panel dashboard"""
        logs = self.analyzer.load_logs()
        
        if not logs:
            fig = go.Figure()
            fig.add_annotation(
                text="No data available. Start the server and make some requests.",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        df = pd.DataFrame(logs)
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'Request Latency Over Time',
                'Response Quality Distribution', 
                'Token Usage Analysis',
                'Cost per Request',
                'Error Rate by Service',
                'Request Volume Timeline'
            ],
            specs=[
                [{"secondary_y": True}, {"type": "histogram"}],
                [{"secondary_y": False}, {"type": "scatter"}],
                [{"type": "bar"}, {"secondary_y": True}]
            ]
        )
        
        # Panel 1: Request Latency
        if 'latency_ms' in df.columns and 'ts' in df.columns:
            latency_data = df.dropna(subset=['latency_ms'])
            if not latency_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=latency_data['ts'],
                        y=latency_data['latency_ms'],
                        mode='lines+markers',
                        name='Latency (ms)',
                        line=dict(color='blue')
                    ),
                    row=1, col=1
                )
        
        # Panel 2: Quality Distribution
        if 'quality_score' in df.columns:
            quality_data = df.dropna(subset=['quality_score'])
            if not quality_data.empty:
                fig.add_trace(
                    go.Histogram(
                        x=quality_data['quality_score'],
                        name='Quality Score',
                        nbinsx=20,
                        marker_color='green'
                    ),
                    row=1, col=2
                )
        
        # Panel 3: Token Usage
        if 'tokens_in' in df.columns and 'tokens_out' in df.columns:
            token_data = df.dropna(subset=['tokens_in', 'tokens_out'])
            if not token_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(token_data))),
                        y=token_data['tokens_in'],
                        mode='markers',
                        name='Input Tokens',
                        marker=dict(color='orange')
                    ),
                    row=2, col=1
                )
                fig.add_trace(
                    go.Scatter(
                        x=list(range(len(token_data))),
                        y=token_data['tokens_out'], 
                        mode='markers',
                        name='Output Tokens',
                        marker=dict(color='red')
                    ),
                    row=2, col=1
                )
        
        # Panel 4: Cost Analysis
        if 'cost_usd' in df.columns and 'ts' in df.columns:
            cost_data = df.dropna(subset=['cost_usd'])
            if not cost_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=cost_data['ts'],
                        y=cost_data['cost_usd'],
                        mode='markers',
                        name='Cost per Request',
                        marker=dict(color='purple', size=8)
                    ),
                    row=2, col=2
                )
        
        # Panel 5: Error Rate by Service
        if 'service' in df.columns and 'level' in df.columns:
            error_df = df[df['level'] == 'error']
            if not error_df.empty:
                error_by_service = error_df['service'].value_counts()
                fig.add_trace(
                    go.Bar(
                        x=error_by_service.index,
                        y=error_by_service.values,
                        name='Error Count',
                        marker_color='red'
                    ),
                    row=3, col=1
                )
        
        # Panel 6: Request Volume
        if 'ts' in df.columns:
            df['timestamp'] = pd.to_datetime(df['ts'])
            hourly_requests = df.set_index('timestamp').resample('1H').size()
            if not hourly_requests.empty:
                fig.add_trace(
                    go.Scatter(
                        x=hourly_requests.index,
                        y=hourly_requests.values,
                        mode='lines+markers',
                        name='Requests/Hour',
                        line=dict(color='darkblue')
                    ),
                    row=3, col=2
                )
        
        # Update layout
        fig.update_layout(
            height=900,
            title_text="Day 13 Observability Dashboard - Key Metrics",
            showlegend=True
        )
        
        return fig
    
    def create_real_time_chart(self, metric: str = 'latency_ms') -> go.Figure:
        """Create real-time chart for a specific metric"""
        timestamps, values = self.analyzer.get_time_series_data(metric)
        
        fig = go.Figure()
        
        if timestamps and values:
            fig.add_trace(
                go.Scatter(
                    x=timestamps,
                    y=values,
                    mode='lines+markers',
                    name=metric,
                    line=dict(width=2)
                )
            )
        else:
            fig.add_annotation(
                text=f"No {metric} data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False
            )
        
        fig.update_layout(
            title=f"Real-time {metric}",
            xaxis_title="Time",
            yaxis_title=metric,
            height=400
        )
        
        return fig

class AlertsManager:
    """Manage alerts and notifications"""
    
    def __init__(self):
        self.alert_rules = self._load_alert_rules()
        self.analyzer = LogAnalyzer()
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load alert rules from configuration"""
        rules_file = Path("config/alert_rules.yaml")
        if rules_file.exists():
            try:
                import yaml
                with open(rules_file, 'r') as f:
                    return yaml.safe_load(f)
            except ImportError:
                print("PyYAML not installed, using default rules")
            except Exception as e:
                print(f"Error loading alert rules: {e}")
        
        # Default rules
        return {
            "latency_high": {"threshold": 1000, "metric": "latency_ms"},
            "error_rate_high": {"threshold": 10, "metric": "error_rate"},
            "quality_low": {"threshold": 0.5, "metric": "quality_score"}
        }
    
    def check_alerts(self) -> List[Dict[str, Any]]:
        """Check current metrics against alert rules"""
        alerts = []
        metrics = self.analyzer.get_metrics_summary()
        
        # Check latency alert
        if metrics['avg_latency'] > self.alert_rules['latency_high']['threshold']:
            alerts.append({
                "name": "High Latency",
                "value": metrics['avg_latency'],
                "threshold": self.alert_rules['latency_high']['threshold'],
                "severity": "warning"
            })
        
        # Check error rate alert
        if metrics['error_rate'] > self.alert_rules['error_rate_high']['threshold']:
            alerts.append({
                "name": "High Error Rate",
                "value": metrics['error_rate'],
                "threshold": self.alert_rules['error_rate_high']['threshold'],
                "severity": "critical"
            })
        
        # Check quality alert
        if metrics['avg_quality'] < self.alert_rules['quality_low']['threshold']:
            alerts.append({
                "name": "Low Quality Score",
                "value": metrics['avg_quality'],
                "threshold": self.alert_rules['quality_low']['threshold'],
                "severity": "warning"
            })
        
        return alerts

# Utility functions for the main Gradio app
async def get_comprehensive_status():
    """Get comprehensive system status"""
    async with MetricsCollector() as collector:
        health = await collector.get_api_health()
        
    analyzer = LogAnalyzer()
    metrics = analyzer.get_metrics_summary()
    
    alerts_manager = AlertsManager()
    alerts = alerts_manager.check_alerts()
    
    return {
        "api_health": health,
        "metrics_summary": metrics,
        "active_alerts": alerts,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def format_metrics_summary(metrics: Dict[str, Any]) -> str:
    """Format metrics summary for display"""
    return f"""
## 📊 Metrics Summary

- **Total Requests**: {metrics['total_requests']}
- **Average Latency**: {metrics['avg_latency']:.2f}ms
- **Total Cost**: ${metrics['total_cost']:.6f}
- **Error Rate**: {metrics['error_rate']:.2f}%
- **Average Quality**: {metrics['avg_quality']:.2f}/1.0

*Updated: {datetime.now().strftime('%H:%M:%S')}*
"""

def format_alerts_display(alerts: List[Dict[str, Any]]) -> str:
    """Format alerts for display"""
    if not alerts:
        return "✅ **All systems normal** - No active alerts"
    
    alerts_text = "🚨 **Active Alerts**\n\n"
    for alert in alerts:
        severity_icon = "🔴" if alert['severity'] == 'critical' else "⚠️"
        alerts_text += f"{severity_icon} **{alert['name']}**\n"
        alerts_text += f"  - Current: {alert['value']:.2f}\n"
        alerts_text += f"  - Threshold: {alert['threshold']}\n\n"
    
    return alerts_text