#!/usr/bin/env python3
"""
Launch script for Day 13 Observability Lab Dashboard
Handles environment setup and service orchestration
"""

import os
import sys
import time
import subprocess
import signal
import threading
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ServiceManager:
    def __init__(self):
        self.processes = {}
        self.running = True
        
    def start_service(self, name: str, command: list, cwd: str = None):
        """Start a service with the given command"""
        try:
            print(f"🚀 Starting {name}...")
            process = subprocess.Popen(
                command,
                cwd=cwd or os.getcwd(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            self.processes[name] = process
            print(f"✅ {name} started (PID: {process.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to start {name}: {e}")
            return False
    
    def stop_service(self, name: str):
        """Stop a service"""
        if name in self.processes:
            process = self.processes[name]
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                process.wait(timeout=5)
                print(f"🛑 {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️  Force killing {name}")
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")
            finally:
                del self.processes[name]
    
    def stop_all(self):
        """Stop all services"""
        self.running = False
        for name in list(self.processes.keys()):
            self.stop_service(name)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🔄 Received shutdown signal, stopping services...")
        self.stop_all()
        sys.exit(0)

def setup_environment():
    """Setup the environment and check dependencies"""
    print("🔧 Setting up environment...")
    
    # Create necessary directories
    directories = ["data", "logs", "config"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # Check if .env exists, create from example if not
    if not Path(".env").exists() and Path(".env.example").exists():
        print("📋 Creating .env from .env.example...")
        subprocess.run(["cp", ".env.example", ".env"])
    
    # Check Python dependencies
    try:
        import gradio
        import fastapi
        import httpx
        import plotly
        import pandas
        import psutil
        print("✅ All Python dependencies are installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Installing dependencies...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        if result.returncode != 0:
            print("❌ Failed to install dependencies. Please run manually:")
            print(f"   {sys.executable} -m pip install -r requirements.txt")
            return False
    
    return True


def get_docker_compose_cmd() -> list[str] | None:
    """Return supported Docker Compose command."""
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    if shutil.which("docker"):
        # We still validate by trying a lightweight subcommand.
        probe = subprocess.run(["docker", "compose", "version"], capture_output=True, text=True)
        if probe.returncode == 0:
            return ["docker", "compose"]
    return None

def check_ports():
    """Check if required ports are available"""
    import socket
    
    ports_to_check = [
        (7860, "Gradio Dashboard"),
        (8000, "FastAPI Server"),
        (3000, "Langfuse"),
        (5432, "PostgreSQL")
    ]
    
    print("🔍 Checking port availability...")
    for port, service in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            print(f"⚠️  Port {port} ({service}) is already in use")
        else:
            print(f"✅ Port {port} ({service}) is available")
        sock.close()

def main():
    """Main function to launch the dashboard"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                Day 13 Observability Lab                     ║
║               🔍 Dashboard Launcher 🚀                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        return 1
    
    # Check ports
    check_ports()
    
    # Initialize service manager
    manager = ServiceManager()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        # Start Docker services (if docker-compose.yml exists)
        if Path("docker-compose.yml").exists():
            print("🐳 Starting Docker services...")
            compose_cmd = get_docker_compose_cmd()
            if compose_cmd is None:
                raise RuntimeError("Docker Compose command not found. Install docker compose plugin.")
            result = subprocess.run(compose_cmd + ["up", "-d"])
            if result.returncode != 0:
                raise RuntimeError("Failed to start docker services.")
            time.sleep(5)  # Wait for services to start
        
        # Start the Gradio dashboard
        print("🎛️  Starting Gradio Dashboard...")
        manager.start_service(
            "gradio-dashboard",
            [sys.executable, "gradio_ui.py"]
        )
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    🎉 Services Started                      ║
╠══════════════════════════════════════════════════════════════╣
║  📊 Dashboard: http://localhost:7860                        ║
║  🔧 API Server: http://localhost:8000                       ║
║  📈 Langfuse: http://localhost:3000                         ║
║  🐘 PostgreSQL: localhost:5432                             ║
╠══════════════════════════════════════════════════════════════╣
║  Instructions:                                               ║
║  1. Open the Dashboard in your browser                      ║
║  2. Use 'Server Control' tab to start FastAPI server       ║
║  3. Test the system via 'Chat Interface' tab               ║
║  4. Monitor metrics in 'Monitoring Dashboard' tab          ║
║  5. Use Ctrl+C to stop all services                        ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Keep the main thread alive
        while manager.running:
            time.sleep(1)
            
            # Check if processes are still running
            for name, process in list(manager.processes.items()):
                if process.poll() is not None:
                    print(f"⚠️  {name} has stopped unexpectedly")
                    del manager.processes[name]
    
    except KeyboardInterrupt:
        print("\n🔄 Shutting down...")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        manager.stop_all()
        print("👋 Goodbye!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())