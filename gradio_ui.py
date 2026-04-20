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

# === GRADIO INTERFACE ===

def create_gradio_interface():
    """Create a high-contrast, professional Gradio interface for Day 13 Lab"""
    
    # Custom CSS for high contrast and unified theme
    custom_css = """
    .gradio-container { max-width: 1400px !important; background-color: #0b0d11 !important; padding: 10px !important; }
    .main-header { 
        background: linear-gradient(135deg, #111827 0%, #0b0d11 100%); 
        padding: 1rem 1.5rem; border-radius: 12px; margin-bottom: 0.75rem;
        border: 1px solid #1f2937; border-left: 5px solid #5d7cb2;
    }
    .stat-card { background: #111827; padding: 0.75rem; border-radius: 8px; border: 1px solid #1f2937; height: 100%; }
    .dashboard-container { background: #0f172a; border-radius: 12px; padding: 0.5rem; border: 1px solid #1e293b; }
    .console-box { font-family: 'JetBrains Mono', 'Fira Code', monospace; background: #000000 !important; font-size: 0.85rem !important; }
    .gr-button { border-radius: 6px !important; font-weight: 600 !important; }
    footer { display: none !important; }
    .tabs { border: none !important; }
    .tabitem { border: none !important; padding: 1rem 0 !important; }
    """
    
    with gr.Blocks(title="Observability Core | Day 13", css=custom_css, theme=gr.themes.Base()) as demo:
        
        with gr.Group(elem_classes="main-header"):
            with gr.Row():
                with gr.Column(scale=4):
                    gr.HTML(f"""
                        <h1 style='color: #f8fafc; font-size: 2rem; margin: 0; letter-spacing: -0.5px;'>
                            <span style='color: #5d7cb2;'>OBSERVABILITY</span> <span style='color: #b67b88;'>CORE</span> 
                            <small style='color: #4b5563; font-size: 0.9rem; font-weight: 400;'>V2.2 LAB</small>
                        </h1>
                    """)
                with gr.Column(scale=1):
                    with gr.Row():
                        server_status_light = gr.Markdown("## 🔴 **OFL**")
                        refresh_status_btn = gr.Button("🔄 RELOAD", size="sm", variant="secondary")

        with gr.Tabs() as tabs:
            
            # --- TAB 1: EXECUTIVE DASHBOARD ---
            with gr.Tab("📊 DASHBOARD"):
                gr.Markdown("#### 💎 Real-time System Telemetry")
                with gr.Row(variant="compact"):
                    refresh_db_btn = gr.Button("⚡ REFRESH DASHBOARD", variant="primary", scale=2)
                
                with gr.Group(elem_classes="dashboard-container"):
                    main_plot = gr.Plot(show_label=False)
                
                with gr.Accordion("📜 Activity Stream (Logs)", open=False):
                    logs_summary = gr.Markdown()
            
            # --- TAB 2: OPERATOR CONSOLE ---
            with gr.Tab("🛠️ OPERATOR CONSOLE"):
                with gr.Row():
                    with gr.Column(scale=1, elem_classes="stat-card"):
                        gr.Markdown("### ⚙️ SERVICE CONTROL")
                        with gr.Row():
                            start_btn = gr.Button("🚀 BOOT", variant="primary")
                            stop_btn = gr.Button("🛑 HALT", variant="stop")
                        
                        gr.Markdown("---")
                        gr.Markdown("### 🚨 INCIDENT ENGINE")
                        target_incident = gr.Dropdown(
                            label="Select Anomaly Profile",
                            choices=["rag_slow", "llm_error", "memory_leak", "db_connection"],
                            value="rag_slow"
                        )
                        with gr.Row():
                            trigger_btn = gr.Button("🔴 INJECT", variant="stop")
                            recover_btn = gr.Button("🟢 RECOVER", variant="primary")
                            
                    with gr.Column(scale=2, elem_classes="stat-card"):
                        gr.Markdown("### 🧪 STRESS & VALIDATION")
                        with gr.Row():
                            load_concurrency = gr.Slider(1, 20, 5, label="Concurrent Workers", step=1)
                            stress_requests = gr.Slider(1, 100, 20, label="Burst Count", step=1)
                        with gr.Row():
                            run_stress_btn = gr.Button("🔥 RUN STRESS TEST", variant="secondary")
                            validate_sys_btn = gr.Button("✅ VALIDATE SCHEMA", variant="secondary")
                
                gr.Markdown("### 🖥️ SYSTEM CONSOLE")
                console_log = gr.Textbox(show_label=False, lines=8, interactive=False, elem_classes="console-box")

            # --- TAB 3: AGENT SANDBOX ---
            with gr.Tab("💬 AGENT SANDBOX"):
                gr.Markdown("### 🧠 Live LLM Interaction & Tracing")
                with gr.Row():
                    with gr.Column(scale=1):
                        chat_user = gr.Textbox(label="Actor ID", value="operator_01")
                        chat_feature = gr.Dropdown(label="Context Path", choices=["qa", "summary", "analysis"], value="qa")
                        chat_session = gr.Textbox(label="Observation ID", value=f"obs_{int(time.time())}")
                    with gr.Column(scale=3):
                        chat_input = gr.Textbox(label="Inference Payload", placeholder="Test system observability...", lines=2)
                        send_chat_btn = gr.Button("🚀 RUN OBSERVATION", variant="primary")
                
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.Markdown("#### 🤖 Agent Response")
                        chat_output = gr.Textbox(show_label=False, lines=6, interactive=False)
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🧬 Trace Analysis")
                        trace_meta = gr.Markdown()
                        metric_card = gr.Markdown()

        # --- EVENT LOGIC ---
        
        def refresh_all():
            db_builder = DashboardBuilder()
            log_analyzer = LogAnalyzer()
            return (
                db_builder.create_main_dashboard(),
                format_metrics_summary(log_analyzer.get_metrics_summary()),
                check_server_status()
            )

        refresh_db_btn.click(refresh_all, outputs=[main_plot, logs_summary, server_status_light])
        refresh_status_btn.click(check_server_status, outputs=server_status_light)
        
        start_btn.click(start_fastapi_server, outputs=console_log)
        stop_btn.click(stop_fastapi_server, outputs=console_log)
        
        trigger_btn.click(lambda n: toggle_incident(n, True), inputs=target_incident, outputs=console_log)
        recover_btn.click(lambda n: toggle_incident(n, False), inputs=target_incident, outputs=console_log)
        
        run_stress_btn.click(run_load_test, inputs=[load_concurrency, stress_requests], outputs=console_log)
        validate_sys_btn.click(validate_logs, outputs=console_log)
        
        send_chat_btn.click(
            send_chat_message, 
            inputs=[chat_user, chat_session, chat_feature, chat_input],
            outputs=[chat_output, trace_meta, metric_card]
        )
        
        # Initial load
        demo.load(refresh_all, outputs=[main_plot, logs_summary, server_status_light])

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