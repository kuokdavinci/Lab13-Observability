# 🚀 QUICKSTART - Day 13 Observability Lab

**Hướng dẫn nhanh để chạy toàn bộ hệ thống observability với Gradio UI**

## ⚡ Chạy nhanh (3 phút)

### Bước 1: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi động hệ thống
```bash
# Cách 1: Dùng launcher (khuyên dùng)
python launch_dashboard.py

# Cách 2: Thủ công
python gradio_ui.py
```

### Bước 3: Truy cập dashboard
- 🎛️ **Gradio Dashboard**: http://localhost:7860
- 🔧 **FastAPI Docs**: http://localhost:8000/docs (sau khi start server)
- 📈 **Langfuse**: http://localhost:3000

## 🎯 Demo Workflow (5 phút)

### 1. Start Services
1. Mở dashboard: http://localhost:7860
2. Vào tab "**🖥️ Server Control**"
3. Click "**🚀 Start Server**"
4. Chờ message "Server started"

### 2. Test Chat Agent
1. Vào tab "**💬 Chat Interface**"
2. Nhập:
   - User ID: `demo_user_01`
   - Session ID: `demo_session_01`
   - Feature: `qa`
   - Message: `What are the benefits of observability?`
3. Click "**📤 Send Message**"
4. Xem response và correlation ID

### 3. Monitor Metrics
1. Vào tab "**📈 Monitoring Dashboard**"
2. Gửi thêm 5-10 messages khác nhau
3. Click "**🔄 Refresh Dashboard**"
4. Quan sát 6 panels dashboard

### 4. Test Incident Management
1. Vào tab "**🚨 Incident Management**"
2. Click "**📋 Get Status**"
3. Chọn incident: `rag_slow`
4. Click "**🔴 Enable Incident**"
5. Gửi messages và xem impact
6. Click "**🟢 Disable Incident**"

### 5. Run Tests
1. Vào tab "**🧪 Testing & Validation**"
2. Set:
   - Concurrency: `5`
   - Requests: `20`
3. Click "**🚀 Run Load Test**"
4. Click "**✅ Validate Logs**"

## 📊 Rubric Demo Points

### Technical Implementation (30 điểm)
- ✅ **JSON Logging**: Xem trong Monitoring Dashboard → Recent Logs
- ✅ **Correlation IDs**: Hiển thị trong Chat Interface responses
- ✅ **10+ Traces**: Gửi messages và check dashboard metrics
- ✅ **6-Panel Dashboard**: Monitor Dashboard hiển thị đầy đủ
- ✅ **PII Scrubbing**: Test với sensitive data
- ✅ **Alert Rules**: Incident Management simulation

### Incident Response (10 điểm)
- 🎯 **Demo Script**:
  1. Enable `rag_slow` incident
  2. Show increased latency trong dashboard
  3. Trace correlation ID để debugging
  4. Explain root cause = simulated slow retrieval

### Live Demo (20 điểm)
- 🎪 **Presentation Flow**:
  1. Healthy system metrics
  2. Chat functionality demo
  3. Incident injection + recovery
  4. Full observability tracing

## 🧪 Test Everything

### Tự động test integration:
```bash
python test_gradio_integration.py
```

### Kiểm tra thủ công:
```bash
# Test API directly
curl http://localhost:8000/health

# Check logs
tail -f data/logs.jsonl

# Validate logs
python scripts/validate_logs.py

# Run load test
python scripts/load_test.py --concurrency 3 --requests 10
```

## 🎯 Key URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Gradio Dashboard** | http://localhost:7860 | Main UI dashboard |
| **FastAPI Server** | http://localhost:8000 | Backend API |
| **API Docs** | http://localhost:8000/docs | Swagger documentation |
| **Health Check** | http://localhost:8000/health | Server health status |
| **Metrics** | http://localhost:8000/metrics | Prometheus metrics |
| **Langfuse** | http://localhost:3000 | Tracing dashboard |

## 🚨 Troubleshooting

### Port conflicts:
```bash
# Kill existing processes
pkill -f "uvicorn"
pkill -f "gradio"

# Check ports
netstat -tlnp | grep -E ":(7860|8000|3000|5432)"
```

### Dependencies issues:
```bash
pip install -r requirements.txt --force-reinstall
```

### Docker issues:
```bash
docker-compose down
docker-compose up -d
```

## 🏆 Success Checklist

- [ ] Gradio dashboard accessible at localhost:7860
- [ ] FastAPI server starts successfully 
- [ ] Chat messages generate responses with correlation IDs
- [ ] Dashboard shows metrics with 6 panels
- [ ] Incidents can be enabled/disabled
- [ ] Load test runs successfully
- [ ] Log validation passes
- [ ] Integration test passes

**🎉 Ready for demo!**