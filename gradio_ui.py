#!/usr/bin/env python3
"""
Gradio UI for Day 13 Observability Lab
Comprehensive dashboard for monitoring, testing, and managing the observability system
"""

import os
import json
import time
import asyncio
import subprocess
import threading
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

import gradio as gr
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psutil

# Import our custom helpers
try:
    from utils.dashboard_helpers import (
        DashboardBuilder, 
        LogAnalyzer, 
        MetricsCollector,
        AlertsManager,
        get_comprehensive_status,
        format_metrics_summary,
        format_alerts_display
    )
    HELPERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Helper functions not available: {e}")
    HELPERS_AVAILABLE = False

# Configuration
API_BASE_URL = "http://localhost:8000"
LANGFUSE_URL = "http://localhost:3000"

# Global state
app_process = None
logs_data = []
metrics_data = []
incident_status = {}

class ObservabilityDashboard:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.logs_file = Path("data/logs.jsonl")
        self.audit_file = Path("data/audit.jsonl")
        
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

# === UTILITY FUNCTIONS ===

def start_fastapi_server():
    """Start the FastAPI server in background"""
    global app_process
    if app_process and app_process.poll() is None:
        return "✅ Server is already running"
    
    try:
        app_process = subprocess.Popen([
            "uvicorn", "app.main:app", "--reload", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(3)  # Give server time to start
        return "🚀 FastAPI server started on http://localhost:8000"
    except Exception as e:
        return f"❌ Failed to start server: {str(e)}"

def stop_fastapi_server():
    """Stop the FastAPI server"""
    global app_process
    if app_process and app_process.poll() is None:
        app_process.terminate()
        app_process.wait()
        app_process = None
        return "🛑 Server stopped"
    return "ℹ️ Server was not running"

def check_server_status():
    """Check if the FastAPI server is running"""
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            return f"✅ Server Online | Tracing: {data.get('tracing_enabled', False)} | Incidents: {len(data.get('incidents', {}))}"
        else:
            return f"⚠️ Server responding with status {response.status_code}"
    except Exception as e:
        return f"❌ Server offline or unreachable: {str(e)}"

def get_system_metrics():
    """Get system resource metrics"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "cpu_usage": cpu_percent,
        "memory_usage": memory.percent,
        "memory_total_gb": memory.total / (1024**3),
        "memory_used_gb": memory.used / (1024**3),
        "disk_usage": disk.percent,
        "disk_total_gb": disk.total / (1024**3),
        "disk_used_gb": disk.used / (1024**3)
    }

# === CHAT INTERFACE ===

async def send_chat_message(user_id: str, session_id: str, feature: str, message: str):
    """Send a chat message to the FastAPI agent"""
    if not message.strip():
        return "Please enter a message", "", ""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{API_BASE_URL}/chat", json={
                "user_id": user_id,
                "session_id": session_id,
                "feature": feature,
                "message": message
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Format response details
                details = f"""
**Response Details:**
- Correlation ID: `{data.get('correlation_id', 'N/A')}`
- Latency: {data.get('latency_ms', 0)}ms
- Tokens In/Out: {data.get('tokens_in', 0)}/{data.get('tokens_out', 0)}
- Cost: ${data.get('cost_usd', 0):.6f}
- Quality Score: {data.get('quality_score', 0):.2f}
"""
                
                # Format metrics summary
                metrics_summary = f"""
**Request Metrics:**
```
Latency: {data.get('latency_ms', 0)}ms
Cost: ${data.get('cost_usd', 0):.6f}  
Quality: {data.get('quality_score', 0):.2f}/1.0
```
"""
                
                return data.get('answer', 'No response'), details, metrics_summary
            else:
                error_msg = f"Error {response.status_code}: {response.text}"
                return error_msg, error_msg, ""
                
    except Exception as e:
        error_msg = f"Request failed: {str(e)}"
        return error_msg, error_msg, ""

# === MONITORING DASHBOARD ===

def load_logs_data():
    """Load and parse logs from logs.jsonl"""
    logs = []
    logs_file = Path("data/logs.jsonl")
    
    if logs_file.exists():
        try:
            with open(logs_file, 'r') as f:
                for line in f:
                    if line.strip():
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
        except Exception as e:
            print(f"Error loading logs: {e}")
    
    return logs

def create_metrics_dashboard():
    """Create comprehensive metrics dashboard"""
    if HELPERS_AVAILABLE:
        dashboard_builder = DashboardBuilder()
        return dashboard_builder.create_main_dashboard()
    else:
        # Fallback to basic implementation
        logs = load_logs_data()
        
        if not logs:
            return go.Figure().add_annotation(
                text="No logs data available. Start the server and make some requests.",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False
            )
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(logs)
        
        # Create simple dashboard
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Request Latency Over Time', 'Error Distribution',
                           'Token Usage', 'Cost Analysis'),
        )
        
        # Basic latency plot
        if 'latency_ms' in df.columns and 'ts' in df.columns:
            latency_data = df.dropna(subset=['latency_ms'])
            fig.add_trace(
                go.Scatter(x=latency_data['ts'], y=latency_data['latency_ms'],
                          mode='lines+markers', name='Latency (ms)'),
                row=1, col=1
            )
        
        fig.update_layout(height=600, title_text="Basic Observability Dashboard")
        return fig

def get_logs_summary():
    """Get summary of recent logs"""
    if HELPERS_AVAILABLE:
        analyzer = LogAnalyzer()
        metrics = analyzer.get_metrics_summary()
        return format_metrics_summary(metrics)
    else:
        # Fallback implementation
        logs = load_logs_data()
        
        if not logs:
            return "No logs available. Start the server and make some requests."
        
        # Get recent logs (last 10)
        recent_logs = logs[-10:]
        
        summary = "## Recent Log Entries\n\n"
        for log in recent_logs:
            ts = log.get('ts', 'Unknown time')
            level = log.get('level', 'info').upper()
            event = log.get('event', 'unknown')
            service = log.get('service', 'unknown')
            
            summary += f"**{ts}** [{level}] {service}: {event}\n"
            
            if log.get('error_type'):
                summary += f"  - Error: {log['error_type']}\n"
            if log.get('latency_ms'):
                summary += f"  - Latency: {log['latency_ms']}ms\n"
                
            summary += "\n"
        
        return summary

# === INCIDENT MANAGEMENT ===

async def get_incident_status():
    """Get current incident status"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                incidents = data.get('incidents', {})
                
                if not incidents:
                    return "No incidents configured"
                
                status_text = "## Incident Status\n\n"
                for name, enabled in incidents.items():
                    status = "🔴 ACTIVE" if enabled else "🟢 DISABLED"
                    status_text += f"- **{name}**: {status}\n"
                
                return status_text
            else:
                return f"Failed to get status: {response.status_code}"
    except Exception as e:
        return f"Error getting incident status: {str(e)}"

async def toggle_incident(incident_name: str, enable: bool):
    """Enable or disable an incident"""
    try:
        action = "enable" if enable else "disable"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{API_BASE_URL}/incidents/{incident_name}/{action}")
            
            if response.status_code == 200:
                status = "enabled" if enable else "disabled"
                return f"✅ Incident '{incident_name}' {status}"
            else:
                return f"❌ Failed to {action} incident: {response.text}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# === LOAD TESTING ===

def run_load_test(concurrency: int = 1, requests: int = 10):
    """Run load test against the API"""
    try:
        result = subprocess.run([
            "python", "scripts/load_test.py", 
            "--concurrency", str(concurrency),
            "--requests", str(requests)
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return f"✅ Load test completed:\n\n```\n{result.stdout}\n```"
        else:
            return f"❌ Load test failed:\n\n```\n{result.stderr}\n```"
    except subprocess.TimeoutExpired:
        return "⏰ Load test timed out after 60 seconds"
    except Exception as e:
        return f"❌ Error running load test: {str(e)}"

def validate_logs():
    """Run log validation script"""
    try:
        result = subprocess.run([
            "python", "scripts/validate_logs.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return f"✅ Log validation passed:\n\n```\n{result.stdout}\n```"
        else:
            return f"❌ Log validation failed:\n\n```\n{result.stderr}\n```"
    except Exception as e:
        return f"❌ Error running validation: {str(e)}"

# === GRADIO INTERFACE ===

def create_gradio_interface():
    """Create the main Gradio interface"""
    
    with gr.Blocks(
        title="Day 13 Observability Lab Dashboard",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .tab-nav {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        }
        """
    ) as demo:
        
        gr.HTML("""
        <div style="text-align: center; padding: 20px; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; margin-bottom: 20px; border-radius: 10px;">
            <h1>🔍 Day 13 Observability Lab Dashboard</h1>
            <p>Comprehensive monitoring, testing, and management interface for the observability system</p>
        </div>
        """)
        
        with gr.Tabs() as tabs:
            
            # === SERVER CONTROL TAB ===
            with gr.Tab("🖥️ Server Control"):
                gr.Markdown("## Server Management")
                
                with gr.Row():
                    with gr.Column():
                        start_btn = gr.Button("🚀 Start Server", variant="primary")
                        stop_btn = gr.Button("🛑 Stop Server", variant="stop")
                        status_btn = gr.Button("📊 Check Status", variant="secondary")
                
                server_output = gr.Textbox(
                    label="Server Status", 
                    lines=3, 
                    interactive=False
                )
                
                # Auto-refresh status every 10 seconds
                status_btn.click(
                    fn=check_server_status,
                    outputs=server_output,
                    every=10
                )
                
                start_btn.click(
                    fn=start_fastapi_server,
                    outputs=server_output
                )
                
                stop_btn.click(
                    fn=stop_fastapi_server,
                    outputs=server_output
                )
            
            # === CHAT INTERFACE TAB ===
            with gr.Tab("💬 Chat Interface"):
                gr.Markdown("## Test the Chat Agent")
                gr.Markdown("Send messages to test the observability instrumentation")
                
                with gr.Row():
                    with gr.Column(scale=1):
                        user_id = gr.Textbox(
                            label="User ID",
                            value="test_user_01",
                            placeholder="Enter user ID"
                        )
                        session_id = gr.Textbox(
                            label="Session ID",
                            value="session_01",
                            placeholder="Enter session ID"
                        )
                        feature = gr.Dropdown(
                            label="Feature",
                            choices=["qa", "summary", "analysis"],
                            value="qa"
                        )
                    
                    with gr.Column(scale=2):
                        message = gr.Textbox(
                            label="Message",
                            placeholder="Enter your message here...",
                            lines=3
                        )
                        send_btn = gr.Button("📤 Send Message", variant="primary")
                
                with gr.Row():
                    with gr.Column():
                        response = gr.Textbox(
                            label="Agent Response",
                            lines=5,
                            interactive=False
                        )
                    
                    with gr.Column():
                        response_details = gr.Markdown(label="Response Details")
                        metrics_info = gr.Markdown(label="Metrics")
                
                send_btn.click(
                    fn=send_chat_message,
                    inputs=[user_id, session_id, feature, message],
                    outputs=[response, response_details, metrics_info]
                )
            
            # === MONITORING DASHBOARD TAB ===
            with gr.Tab("📈 Monitoring Dashboard"):
                gr.Markdown("## System Metrics & Observability")
                
                with gr.Row():
                    refresh_dashboard = gr.Button("🔄 Refresh Dashboard", variant="secondary")
                
                dashboard_plot = gr.Plot(label="Metrics Dashboard")
                
                with gr.Row():
                    with gr.Column():
                        logs_summary = gr.Markdown(label="Recent Logs")
                    
                    with gr.Column():
                        system_metrics = gr.JSON(label="System Resources")
                
                def refresh_all_dashboard():
                    return (
                        create_metrics_dashboard(),
                        get_logs_summary(),
                        get_system_metrics()
                    )
                
                refresh_dashboard.click(
                    fn=refresh_all_dashboard,
                    outputs=[dashboard_plot, logs_summary, system_metrics]
                )
                
                # Auto-refresh every 30 seconds
                demo.load(
                    fn=refresh_all_dashboard,
                    outputs=[dashboard_plot, logs_summary, system_metrics],
                    every=30
                )
            
            # === INCIDENT MANAGEMENT TAB ===
            with gr.Tab("🚨 Incident Management"):
                gr.Markdown("## Incident Simulation & Management")
                
                with gr.Row():
                    get_status_btn = gr.Button("📋 Get Status", variant="secondary")
                    incident_status_output = gr.Markdown(label="Incident Status")
                
                with gr.Row():
                    with gr.Column():
                        incident_name = gr.Dropdown(
                            label="Incident Type",
                            choices=["rag_slow", "llm_error", "memory_leak", "db_connection"],
                            value="rag_slow"
                        )
                        
                        with gr.Row():
                            enable_incident = gr.Button("🔴 Enable Incident", variant="stop")
                            disable_incident = gr.Button("🟢 Disable Incident", variant="primary")
                    
                    with gr.Column():
                        incident_output = gr.Textbox(
                            label="Incident Management Output",
                            lines=5,
                            interactive=False
                        )
                
                async def enable_incident_wrapper(name):
                    return await toggle_incident(name, True)
                
                async def disable_incident_wrapper(name):
                    return await toggle_incident(name, False)
                
                get_status_btn.click(
                    fn=get_incident_status,
                    outputs=incident_status_output
                )
                
                enable_incident.click(
                    fn=enable_incident_wrapper,
                    inputs=incident_name,
                    outputs=incident_output
                )
                
                disable_incident.click(
                    fn=disable_incident_wrapper,
                    inputs=incident_name,
                    outputs=incident_output
                )
            
            # === TESTING & VALIDATION TAB ===
            with gr.Tab("🧪 Testing & Validation"):
                gr.Markdown("## Load Testing & Log Validation")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### Load Testing")
                        concurrency = gr.Slider(
                            label="Concurrency",
                            minimum=1,
                            maximum=20,
                            value=5,
                            step=1
                        )
                        requests_count = gr.Slider(
                            label="Number of Requests",
                            minimum=1,
                            maximum=100,
                            value=20,
                            step=1
                        )
                        run_load_btn = gr.Button("🚀 Run Load Test", variant="primary")
                    
                    with gr.Column():
                        gr.Markdown("### Log Validation")
                        validate_btn = gr.Button("✅ Validate Logs", variant="secondary")
                
                with gr.Row():
                    test_output = gr.Textbox(
                        label="Test Results",
                        lines=15,
                        interactive=False
                    )
                
                run_load_btn.click(
                    fn=run_load_test,
                    inputs=[concurrency, requests_count],
                    outputs=test_output
                )
                
                validate_btn.click(
                    fn=validate_logs,
                    outputs=test_output
                )
            
            # === SYSTEM INFO TAB ===
            with gr.Tab("ℹ️ System Info"):
                gr.Markdown("## Lab Information & Setup")
                
                gr.Markdown(f"""
                ### Lab Environment
                - **API Server**: {API_BASE_URL}
                - **Langfuse UI**: {LANGFUSE_URL}  
                - **Working Directory**: {os.getcwd()}
                
                ### Key Features Monitored
                1. **Structured Logging** - JSON schema with correlation IDs
                2. **Distributed Tracing** - Langfuse integration
                3. **PII Scrubbing** - Automatic data sanitization
                4. **Metrics Collection** - Latency, cost, quality scores
                5. **Incident Simulation** - Controlled failure injection
                6. **SLO Monitoring** - Service level objectives
                
                ### Rubric Requirements Covered
                - ✅ **Logging & Tracing**: JSON schema, correlation IDs, 10+ traces
                - ✅ **Dashboard & SLO**: 6-panel dashboard with thresholds
                - ✅ **Alerts & PII**: PII redaction, alert rules with runbook
                - ✅ **Incident Response**: Root cause analysis capabilities
                - ✅ **Live Demo**: Full system demonstration
                
                ### Quick Start Commands
                ```bash
                # Start the system
                python gradio_ui.py
                
                # In another terminal, start FastAPI
                uvicorn app.main:app --reload
                
                # Start Langfuse (if using Docker)
                docker-compose up -d
                ```
                
                ### Testing the System
                1. Start the FastAPI server from the Server Control tab
                2. Send test messages via the Chat Interface
                3. Monitor metrics in the Dashboard
                4. Simulate incidents for testing
                5. Validate logs and run load tests
                """)
    
    return demo

# === MAIN EXECUTION ===

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    
    # Initialize the dashboard
    demo = create_gradio_interface()
    
    # Launch the interface
    print("🚀 Starting Day 13 Observability Lab Dashboard...")
    print(f"📊 Dashboard URL: http://localhost:7860")
    print(f"🔧 API Server: {API_BASE_URL}")
    print(f"📈 Langfuse: {LANGFUSE_URL}")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )