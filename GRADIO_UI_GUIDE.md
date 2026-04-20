# 🔍 Day 13 Observability Lab - Gradio UI Guide

Hướng dẫn toàn diện về giao diện Gradio cho Lab Observability Day 13

## 🚀 Quick Start

### 1. Cài đặt Dependencies

```bash
# Cài đặt Python dependencies
pip install -r requirements.txt

# Hoặc sử dụng launcher tự động
python launch_dashboard.py
```

### 2. Khởi động Hệ thống

#### Cách 1: Sử dụng Launcher (Khuyên dùng)
```bash
python launch_dashboard.py
```

#### Cách 2: Khởi động thủ công
```bash
# Bước 1: Khởi động Docker services (Langfuse + PostgreSQL)
docker-compose up -d

# Bước 2: Khởi động Gradio Dashboard
python gradio_ui.py

# Bước 3: (Tùy chọn) Khởi động FastAPI server trong terminal khác
uvicorn app.main:app --reload --port 8000
```

### 3. Truy cập Dashboard

- **📊 Gradio Dashboard**: http://localhost:7860
- **🔧 FastAPI API**: http://localhost:8000
- **📈 Langfuse Tracing**: http://localhost:3000

---

## 🎛️ Giao diện Dashboard

### Tab 1: 🖥️ Server Control
**Mục đích**: Quản lý FastAPI server

**Tính năng**:
- 🚀 **Start Server**: Khởi động FastAPI server
- 🛑 **Stop Server**: Dừng FastAPI server  
- 📊 **Check Status**: Kiểm tra trạng thái server (tự động refresh mỗi 10s)

**Sử dụng**:
1. Click "Start Server" để khởi động API
2. Chờ thông báo "Server started"
3. Sử dụng "Check Status" để kiểm tra health

### Tab 2: 💬 Chat Interface
**Mục đích**: Test chat agent với observability instrumentation

**Tính năng**:
- ✍️ **Message Input**: Gửi tin nhắn test
- 🆔 **User/Session ID**: Cấu hình context
- 🎯 **Feature Selection**: Chọn feature (qa, summary, analysis)
- 📊 **Response Details**: Xem correlation ID, latency, tokens, cost
- 📈 **Metrics Info**: Theo dõi performance metrics

**Sử dụng**:
1. Nhập User ID (vd: `test_user_01`)
2. Nhập Session ID (vd: `session_01`) 
3. Chọn feature từ dropdown
4. Gửi message và xem kết quả
5. Kiểm tra metrics và tracing data

### Tab 3: 📈 Monitoring Dashboard
**Mục đích**: Giám sát metrics và observability data

**Panels Dashboard**:
1. **Request Latency Over Time**: Biểu đồ latency theo thời gian
2. **Error Distribution**: Phân bố lỗi theo loại
3. **Token Usage**: Sử dụng tokens input/output
4. **Cost Analysis**: Phân tích chi phí requests
5. **Quality Scores**: Phân bố quality scores
6. **Service Activity**: Hoạt động các services

**Tính năng**:
- 🔄 **Auto-refresh**: Tự động cập nhật mỗi 30s
- 📋 **Recent Logs**: Hiển thị logs gần đây
- 💻 **System Resources**: CPU, memory, disk usage

**Sử dụng**:
1. Dashboard tự động load khi có data
2. Click "Refresh Dashboard" để update thủ công
3. Phân tích trends và patterns trong metrics

### Tab 4: 🚨 Incident Management
**Mục đích**: Simulation và quản lý incidents

**Incident Types**:
- `rag_slow`: Slow retrieval performance
- `llm_error`: LLM generation errors
- `memory_leak`: Memory leak simulation
- `db_connection`: Database connection issues

**Tính năng**:
- 📋 **Get Status**: Xem trạng thái incidents
- 🔴 **Enable Incident**: Bật incident simulation
- 🟢 **Disable Incident**: Tắt incident simulation

**Sử dụng**:
1. Click "Get Status" để xem incidents hiện tại
2. Chọn incident type từ dropdown
3. Enable/disable để test incident response
4. Kiểm tra impact trong monitoring dashboard

### Tab 5: 🧪 Testing & Validation
**Mục đích**: Load testing và validation

**Load Testing**:
- ⚡ **Concurrency**: Số requests đồng thời (1-20)
- 📊 **Request Count**: Tổng số requests (1-100)
- 🚀 **Run Load Test**: Chạy test và hiển thị kết quả

**Log Validation**:
- ✅ **Validate Logs**: Kiểm tra JSON schema compliance
- 📋 **Validation Report**: Báo cáo chi tiết về logs quality

**Sử dụng**:
1. Cấu hình concurrency và request count
2. Click "Run Load Test" để chạy test
3. Click "Validate Logs" để kiểm tra compliance
4. Xem kết quả và performance metrics

### Tab 6: ℹ️ System Info
**Mục đích**: Thông tin hệ thống và hướng dẫn

**Thông tin**:
- 🌐 **Environment URLs**: Links đến các services
- ✅ **Feature Checklist**: Các tính năng đã implement
- 📋 **Rubric Coverage**: Mapping với yêu cầu chấm điểm
- 🚀 **Quick Commands**: Các lệnh hữu ích

---

## 🎯 Workflow Khuyên Dùng

### 1. Setup & Verification
```bash
# Khởi động dashboard
python launch_dashboard.py

# Truy cập dashboard
# Browser -> http://localhost:7860
```

### 2. Server Management
1. Vào tab "Server Control"
2. Click "Start Server"
3. Chờ status "Server Online"

### 3. Testing Flow
1. **Chat Interface**: Gửi vài test messages
2. **Monitoring**: Kiểm tra metrics dashboard
3. **Incidents**: Simulate failures và observe impact
4. **Validation**: Run log validation và load tests

### 4. Demo Preparation
1. Prepare test scenarios với meaningful messages
2. Enable/disable incidents để demo incident response
3. Show correlation between metrics → traces → logs
4. Demonstrate PII scrubbing và structured logging

---

## 🏆 Rubric Coverage

### Group Score Requirements (60 points)

#### A1. Implementation Quality (30 điểm)
- ✅ **Logging & Tracing (10đ)**: 
  - JSON schema validation qua "Testing & Validation" tab
  - Correlation ID tracking qua chat responses
  - 10+ traces visible qua metrics dashboard
  
- ✅ **Dashboard & SLO (10đ)**:
  - 6-panel dashboard trong "Monitoring Dashboard" tab
  - Clear units và thresholds
  - SLO tracking capabilities
  
- ✅ **Alerts & PII (10đ)**:
  - PII scrubbing demonstrated qua chat interface
  - Incident simulation qua "Incident Management" tab
  - Alert rules configuration

#### A2. Incident Response (10 điểm)
- 🎯 **Root Cause Analysis**: 
  - Use incident simulation để inject failures
  - Follow Metrics → Traces → Logs flow trong dashboard
  - Demonstrate debugging workflow

#### A3. Live Demo (20 điểm)
- 🎪 **Demo Flow**:
  1. Show healthy system metrics
  2. Inject incident và observe impact
  3. Trace root cause using observability data
  4. Demonstrate recovery

### Individual Score Requirements (40 points)

#### B1. Individual Report (20 điểm)
- 📝 **Evidence Collection**: 
  - Screenshot dashboard panels
  - Copy correlation IDs và trace data
  - Document specific contributions

#### B2. Evidence of Work (20 điểm)
- 🔍 **Git Evidence**: 
  - Gradio UI implementation
  - Dashboard customizations
  - Integration work

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Server Won't Start
```bash
# Kiểm tra port conflicts
netstat -tlnp | grep :8000

# Kill existing processes
pkill -f "uvicorn"
```

#### 2. Dashboard No Data
- Đảm bảo FastAPI server đang chạy
- Gửi ít nhất 1-2 test messages qua chat interface
- Check logs.jsonl file được tạo

#### 3. Docker Services Issues
```bash
# Restart Docker services
docker-compose down
docker-compose up -d

# Check service health
docker-compose ps
```

#### 4. Dependencies Issues
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall

# Check versions
pip list | grep -E "(gradio|fastapi|plotly)"
```

### Performance Tips

1. **Memory Usage**: Dashboard auto-refreshes có thể consume memory. Tăng interval nếu cần.

2. **Load Testing**: Start với concurrency thấp (1-3) trước khi scale up.

3. **Log Files**: Monitor kích thước `data/logs.jsonl` - truncate nếu quá lớn.

---

## 📚 Advanced Features

### Custom Metrics
- Extend `create_metrics_dashboard()` để add custom panels
- Modify log parsing để include thêm fields
- Add thêm incident types trong `toggle_incident()`

### Dashboard Customization  
- Customize Gradio theme trong `create_gradio_interface()`
- Add thêm visualization types từ Plotly
- Implement real-time streaming updates

### Integration Extensions
- Connect với external monitoring systems
- Add Slack/Teams notifications
- Implement custom alert rules

---

## 🤝 Support & Resources

### Documentation Links
- **FastAPI Docs**: http://localhost:8000/docs (khi server chạy)
- **Langfuse**: http://localhost:3000 
- **Gradio Docs**: https://gradio.app/docs/

### Lab Resources
- `docs/dashboard-spec.md`: Dashboard requirements
- `docs/blueprint-template.md`: Report template
- `config/alert_rules.yaml`: Alert configurations
- `scripts/`: Utility scripts

### Contact
- Lab instructor để support
- Team members để collaboration
- GitHub issues để bug reports

---

**🎉 Chúc các bạn thành công với Day 13 Observability Lab!**