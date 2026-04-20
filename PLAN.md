# 📋 Kế hoạch Triển khai Lab 13 - Observability

## 🛠 Trạng thái Môi trường
- **Python:** 3.12.13 (trong `.venv`)
- **Library:** Langfuse v2.57.0 (đã hạ cấp để tương thích Lab)
- **Status:** Giai đoạn 1, 2, 3 đã hoàn thành ✅

---

## ✅ Giai đoạn 1: Correlation ID (Member A)
- [x] **Middleware:** Hoàn thành `CorrelationIdMiddleware` trong `app/middleware.py`.
- [x] **Header:** Trả về `x-request-id` và `x-response-time-ms`.
- [x] **Context:** Xóa context cũ trước mỗi request và bind ID mới.

## ✅ Giai đoạn 2: Log Enrichment & PII (Member A)
- [x] **Enrichment:** Gắn `user_id_hash`, `session_id`, `feature`, `model`, `env` vào logs.
- [x] **PII Scrubbing:** Đăng ký `scrub_event` trong `app/logging_config.py`.
- [x] **Xác thực:** Chạy `scripts/validate_logs.py` đạt 100/100 điểm.

## ✅ Giai đoạn 3: Distributed Tracing (Member B)
- [x] **Cấu hình:** Điền API Keys vào `.env`.
- [x] **Fix lỗi:** Di chuyển `load_dotenv()` lên đầu `app/main.py` để decorator nhận diện được Key.
- [x] **Traces:** Xác nhận Trace hiện lên trên Langfuse Cloud (Traces: `chat`, `Manual Test Trace`).
- [x] **Tags:** Traces đã có đủ tags (`lab`, `qa/summary`, `model`).

## 📈 Giai đoạn 4: Metrics & SLOs (Member C) - ĐANG THỰC HIỆN 🕒
Mục tiêu: Xuất dữ liệu ra Prometheus định dạng `/metrics`.

- [ ] **Implement Metrics (`app/metrics.py`):**
    - [ ] `request_count` (Counter): Đếm tổng số request.
    - [ ] `error_count` (Counter): Đếm số request bị lỗi (5xx).
    - [ ] `latency_seconds` (Histogram): Đo thời gian xử lý.
- [ ] **SLO Definition:**
    - [ ] **Availability:** 99.9% success rate.
    - [ ] **Latency:** 95% request < 500ms.
- [ ] **Dashboard:** Tạo Dashboard (hoặc Snapshot) hiển thị các chỉ số này.

## 🚨 Giai đoạn 5: Incident Response (Member B & C)
Mục tiêu: Phát hiện và xử lý sự cố.

- [ ] **Simulate Incidents:** Sử dụng `/incident/enable` để tạo lỗi giả (RAG slow, Tool fail).
- [ ] **Detection:** Quan sát sự thay đổi trên Dashboard và Langfuse Traces.
- [ ] **Analysis:** Tìm ra Root Cause (Ví dụ: Model latency tăng, Tool trả về lỗi).
- [ ] **Report:** Viết báo cáo ngắn gọn về sự cố và cách khắc phục.
