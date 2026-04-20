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
                "success_rate": 0,
                "avg_quality": 0
            }
        
        df = pd.DataFrame(logs)
        
        # Filter requests - Only count terminal events
        success_logs = df[df.get('event') == 'response_sent']
        failed_logs = df[df.get('event') == 'request_failed']
        
        # total_attempts should only be the sum of completions and failures
        total_attempts = len(success_logs) + len(failed_logs)
        
        # Safe column access (using success_logs)
        def get_stat(col):
            return success_logs[col] if col in success_logs.columns and len(success_logs) > 0 else pd.Series()

        summary = {
            "total_requests": total_attempts,
            "avg_latency": get_stat('latency_ms').mean() if not get_stat('latency_ms').empty else 0,
            "p95_latency": get_stat('latency_ms').quantile(0.95) if not get_stat('latency_ms').empty else 0,
            "total_cost": get_stat('cost_usd').sum() if not get_stat('cost_usd').empty else 0,
            "success_rate": (len(success_logs) / total_attempts * 100) if total_attempts > 0 else 0,
            "avg_quality": get_stat('quality_score').mean() if not get_stat('quality_score').empty else 0
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
    
    def format_metrics_summary(self) -> str:
        """Get summary string for metrics card"""
        stats = self.analyzer.get_metrics_summary()
        return (
            f"### 📊 Session Summary\n"
            f"**Traffic**: {stats['total_requests']} reqs\n"
            f"**P95 Latency**: {stats['avg_latency']:.1f}ms\n"
            f"**Success Rate**: {stats['success_rate']:.1f}%\n"
            f"**Budget Used**: ${stats['total_cost']:.4f}\n"
            f"**Avg AI Quality**: {stats['avg_quality']:.2f}"
        )
    
    def create_main_dashboard(self) -> go.Figure:
        """Professional SRE Dashboard with Time-series Trend Analysis"""
        logs = self.analyzer.load_logs()
        
        # Color Palette - Blue/Pink Elite
        P_BLUE = "#5d7cb2"
        P_PINK = "#b67b88"
        P_GRAY = "#475569"
        
        if not logs:
            fig = go.Figure()
            fig.add_annotation(text="WAITING FOR TELEMETRY DATA...", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color=P_GRAY))
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            return fig
        
        df = pd.DataFrame(logs)
        df['ts_dt'] = pd.to_datetime(df['ts']) if 'ts' in df.columns else None
        resp_df = df[df.get('event') == 'response_sent'].copy() if 'event' in df.columns else df.copy()
        
        # Create subplots with specific types for Indicators
        fig = make_subplots(
            rows=3, cols=2,
            specs=[
                [{"type": "xy"}, {"type": "domain"}],      # Traffic, Availability
                [{"type": "xy"}, {"type": "domain"}],      # Latency, Quality (Number Only)
                [{"type": "xy"}, {"type": "xy"}]           # Cost, Errors
            ],
            subplot_titles=(
                "LLM Traffic (Throughput)", "Availability % (SLA 95%)",
                "P95 Latency (ms) - Response Tail", "AI Quality (AVG Score)",
                "Total Cost Burn ($)", "Error Breakdown (by Type)"
            ),
            vertical_spacing=0.12,
            horizontal_spacing=0.08
        )
        
        # Filter relevant logs
        success_df = df[df.get('event') == 'response_sent'].copy() if 'event' in df.columns else pd.DataFrame()
        
        # 1. Traffic (Throughput) - 5s resolution
        if not success_df.empty:
            traffic = success_df.set_index('ts_dt').resample('5s').size()
            fig.add_trace(go.Scatter(x=traffic.index, y=traffic.values, fill='tozeroy', name='Throughput', line=dict(color=P_BLUE, width=2)), row=1, col=1)

        # 2. Availability (Average Success Rate) - Big Indicator
        if not df.empty:
            # Only consider terminal events for availability
            terminal_df = df[df['event'].isin(['response_sent', 'request_failed'])].copy()
            if not terminal_df.empty:
                terminal_df['is_success'] = (terminal_df['event'] == 'response_sent').astype(int)
                total_avail = terminal_df['is_success'].mean() * 100
            else:
                total_avail = 0
            
            fig.add_trace(go.Indicator(
                mode = "gauge+number",
                value = total_avail,
                number = {'suffix': "%", 'font': {'color': P_BLUE, 'size': 45}},
                gauge = {
                    'axis': {'range': [0, 100]},
                    'bar': {'color': P_BLUE},
                    'steps': [
                        {'range': [0, 95], 'color': "red"},
                        {'range': [95, 99], 'color': "orange"},
                        {'range': [99, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': 95.0
                    }
                },
                title = {'text': "AVAILABILITY % (SLA 95%)", 'font': {'size': 14}}
            ), row=1, col=2)
            
            # Hide axes for indicator cell to avoid overlap/garbage numbers
            fig.update_xaxes(visible=False, row=1, col=2)
            fig.update_yaxes(visible=False, row=1, col=2)
        else:
            fig.add_annotation(text="WAITING FOR DATA", row=1, col=2, showarrow=False)

        # 3. Latency (P95 Trend) - 5s resolution
        if not success_df.empty and 'latency_ms' in success_df.columns:
            lat_trend = success_df.set_index('ts_dt')['latency_ms'].resample('5s').quantile(0.95).fillna(0)
            threshold_ms = 1000 # 1 second as per alert rules
            
            fig.add_trace(go.Scatter(x=lat_trend.index, y=lat_trend.values, name='P95', line=dict(color=P_PINK, width=2)), row=2, col=1)
            
            # SLO Line at 1000ms
            fig.add_shape(type="line", x0=lat_trend.index.min(), x1=lat_trend.index.max(), y0=threshold_ms, y1=threshold_ms, 
                          line=dict(color="red", width=2, dash="dot"), row=2, col=1)
            
            # Fix Y-axis for high resolution (Clean look)
            current_p95 = lat_trend.max()
            fig.update_yaxes(
                range=[0, max(current_p95 * 1.5, 50)], 
                nticks=5, # Fewer marks for cleaner look
                row=2, col=1
            )
            
            fig.add_annotation(
                text=f"SLO: {threshold_ms}ms",
                xref="x3", yref="y3", x=lat_trend.index.min(), y=threshold_ms,
                showarrow=False, yshift=10, font=dict(color="red", size=10)
            )

        # 4. AI Quality Score - Big Number Only (No Plot)
        if not success_df.empty and 'quality_score' in success_df.columns:
            avg_qual = success_df['quality_score'].mean()
            
            fig.add_trace(go.Indicator(
                mode = "number",
                value = avg_qual,
                number = {'font': {'size': 60, 'color': P_PINK}, 'valueformat': ".2f"},
                domain = {'row': 1, 'column': 1}
            ), row=2, col=2)
        else:
            fig.add_annotation(text="WAITING FOR SCORE", row=2, col=2, showarrow=False)

        # 5. Cost Burn (Cumulative)
        if not success_df.empty and 'cost_usd' in success_df.columns:
            cost_series = success_df.sort_values('ts_dt').set_index('ts_dt')['cost_usd'].cumsum()
            
            fig.add_trace(go.Scatter(
                x=cost_series.index, y=cost_series.values, 
                fill='tozeroy', name='Cost', 
                line=dict(color=P_BLUE, width=3)
            ), row=3, col=1)
            
            # Auto-scale Y axis for micro-costs to make it "visible"
            current_max = cost_series.max()
            fig.update_yaxes(range=[0, max(current_max * 1.5, 0.001)], row=3, col=1)
            
            fig.add_annotation(
                text=f"Total: ${current_max:.6f}",
                xref="x5", yref="y5", x=cost_series.index.min(), y=current_max,
                showarrow=False, yshift=15, font=dict(color=P_BLUE, size=11)
            )

        # 6. Error Breakdown
        error_df = df[df.get('level') == 'error']
        if not error_df.empty and 'error_type' in error_df.columns:
            err_counts = error_df['error_type'].value_counts()
            fig.add_trace(go.Bar(x=err_counts.index, y=err_counts.values, name='Errors', marker_color=P_PINK), row=3, col=2)
        else:
            fig.add_annotation(text="NO ERRORS REPORTED", row=3, col=2, showarrow=False, font=dict(color="green"))

        fig.update_layout(
            height=900, template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(15,23,42,0.5)',
            font=dict(family="Inter, sans-serif", size=13),
            margin=dict(t=120, b=50, l=60, r=40), # Increased top margin to prevent title cutoff
            showlegend=False,
            title=dict(text="SYSTEM OBSERVABILITY CORE TELEMETRY", x=0.5, y=0.98, font=dict(size=20, color=P_BLUE))
        )
        # Ensure subplot titles are visible
        for i in fig['layout']['annotations']:
            i['font'] = dict(size=14, color="white", family="Inter, sans-serif")
            
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
        
        # Check success rate alert (SLA 95%)
        if metrics['success_rate'] < 95.0:
            alerts.append({
                "name": "SLA Breach (Success Rate)",
                "value": metrics['success_rate'],
                "threshold": 95.0,
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

- **Total Requests (Terminal)**: {metrics['total_requests']}
- **P95 Latency**: {metrics['p95_latency']:.2f}ms
- **Total Cost**: ${metrics['total_cost']:.6f}
- **Success Rate**: {metrics['success_rate']:.2f}%
- **Avg Quality**: {metrics['avg_quality']:.2f}/1.0

*Note: Data derived from {metrics['total_requests']} completed operations.*
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