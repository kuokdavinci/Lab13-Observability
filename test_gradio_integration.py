#!/usr/bin/env python3
"""
Integration Test for Gradio UI with FastAPI Backend
Tests the complete observability system integration
"""

import asyncio
import json
import time
import subprocess
import sys
from pathlib import Path
import httpx
from datetime import datetime

class IntegrationTester:
    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.test_results = []
        self.client = None
    
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    def log_result(self, test_name: str, success: bool, message: str):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
    
    async def test_api_health(self):
        """Test FastAPI health endpoint"""
        try:
            response = await self.client.get(f"{self.api_base}/health")
            if response.status_code == 200:
                data = response.json()
                self.log_result("API Health", True, f"Server healthy, tracing: {data.get('tracing_enabled', False)}")
            else:
                self.log_result("API Health", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("API Health", False, str(e))
    
    async def test_chat_endpoint(self):
        """Test chat endpoint with observability"""
        try:
            test_message = {
                "user_id": "integration_test_user",
                "session_id": "integration_test_session",
                "feature": "qa",
                "message": "What is the meaning of life?"
            }
            
            response = await self.client.post(f"{self.api_base}/chat", json=test_message)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ['answer', 'correlation_id', 'latency_ms', 'tokens_in', 'tokens_out']
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    self.log_result("Chat Endpoint", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_result("Chat Endpoint", True, f"Response received with correlation_id: {data['correlation_id'][:8]}...")
            else:
                self.log_result("Chat Endpoint", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_result("Chat Endpoint", False, str(e))
    
    async def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        try:
            response = await self.client.get(f"{self.api_base}/metrics")
            if response.status_code == 200:
                metrics_text = response.text
                if "requests_total" in metrics_text or "latency" in metrics_text:
                    self.log_result("Metrics Endpoint", True, "Prometheus metrics available")
                else:
                    self.log_result("Metrics Endpoint", False, "No recognizable metrics found")
            else:
                self.log_result("Metrics Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Metrics Endpoint", False, str(e))
    
    async def test_incident_management(self):
        """Test incident management endpoints"""
        try:
            # Test enabling incident
            response = await self.client.post(f"{self.api_base}/incidents/rag_slow/enable")
            if response.status_code == 200:
                # Test disabling incident
                response = await self.client.post(f"{self.api_base}/incidents/rag_slow/disable")
                if response.status_code == 200:
                    self.log_result("Incident Management", True, "Enable/disable incidents working")
                else:
                    self.log_result("Incident Management", False, f"Failed to disable: {response.status_code}")
            else:
                self.log_result("Incident Management", False, f"Failed to enable: {response.status_code}")
        except Exception as e:
            self.log_result("Incident Management", False, str(e))
    
    def test_log_files(self):
        """Test log file generation"""
        logs_file = Path("data/logs.jsonl")
        
        if logs_file.exists():
            try:
                with open(logs_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        # Try to parse last log entry
                        last_line = lines[-1].strip()
                        log_entry = json.loads(last_line)
                        
                        required_fields = ['ts', 'level', 'service', 'event', 'correlation_id']
                        missing_fields = [field for field in required_fields if field not in log_entry]
                        
                        if missing_fields:
                            self.log_result("Log Files", False, f"Missing log fields: {missing_fields}")
                        else:
                            self.log_result("Log Files", True, f"Valid JSON logs found ({len(lines)} entries)")
                    else:
                        self.log_result("Log Files", False, "Log file exists but is empty")
            except Exception as e:
                self.log_result("Log Files", False, f"Error parsing logs: {e}")
        else:
            self.log_result("Log Files", False, "logs.jsonl not found")
    
    def test_gradio_dependencies(self):
        """Test Gradio and related dependencies"""
        try:
            import gradio
            import plotly
            import pandas
            import psutil
            
            self.log_result("Dependencies", True, "All Gradio dependencies installed")
        except ImportError as e:
            self.log_result("Dependencies", False, f"Missing dependency: {e}")
    
    def test_scripts(self):
        """Test utility scripts"""
        scripts_to_test = [
            "scripts/validate_logs.py",
            "scripts/load_test.py"
        ]
        
        for script in scripts_to_test:
            script_path = Path(script)
            if script_path.exists():
                self.log_result(f"Script: {script}", True, "Script file exists")
            else:
                self.log_result(f"Script: {script}", False, "Script file missing")
    
    def run_load_test_sample(self):
        """Run a small load test"""
        try:
            result = subprocess.run([
                sys.executable, "scripts/load_test.py", 
                "--concurrency", "2",
                "--requests", "5"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_result("Load Test", True, "Load test script executed successfully")
            else:
                self.log_result("Load Test", False, f"Load test failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.log_result("Load Test", False, "Load test timed out")
        except Exception as e:
            self.log_result("Load Test", False, str(e))
    
    def run_log_validation(self):
        """Run log validation"""
        try:
            result = subprocess.run([
                sys.executable, "scripts/validate_logs.py"
            ], capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                self.log_result("Log Validation", True, "Log validation passed")
            else:
                self.log_result("Log Validation", False, f"Validation failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.log_result("Log Validation", False, "Validation timed out")
        except Exception as e:
            self.log_result("Log Validation", False, str(e))
    
    def print_summary(self):
        """Print test summary"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n{'='*60}")
        print(f"INTEGRATION TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "No tests run")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        print(f"\n{'='*60}")
        
        # Save detailed results
        results_file = Path("test_results.json")
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        print(f"Detailed results saved to: {results_file}")
        
        return failed_tests == 0

async def main():
    """Run integration tests"""
    print("🚀 Starting Day 13 Observability Integration Tests")
    print(f"Target API: http://localhost:8000")
    print(f"Time: {datetime.now()}")
    print("="*60)
    
    async with IntegrationTester() as tester:
        # Test dependencies first
        tester.test_gradio_dependencies()
        tester.test_scripts()
        
        # Test API endpoints
        await tester.test_api_health()
        await tester.test_chat_endpoint()
        await tester.test_metrics_endpoint()
        await tester.test_incident_management()
        
        # Test observability features
        tester.test_log_files()
        
        # Test utilities (if API is healthy)
        api_healthy = any("API Health" in r["test"] and "✅ PASS" in r["status"] for r in tester.test_results)
        if api_healthy:
            tester.run_load_test_sample()
            time.sleep(2)  # Let logs generate
            tester.run_log_validation()
        
        # Print summary
        success = tester.print_summary()
        
        if success:
            print("\n🎉 All tests passed! The system is ready for demo.")
        else:
            print("\n⚠️  Some tests failed. Check the issues above.")
        
        return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)