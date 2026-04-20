# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: Nhóm 10
- [REPO_URL]: https://github.com/KuoKuok1234/Lab13-Observability
- [MEMBERS]:
  - Member A: Lê Trung Anh Quốc | Role: Logging & PII, Tracing & Enrichment
  - Member C: [Name] | Role: SLO & Alerts
  - Member D: [Name] | Role: Load Test & Dashboard
  - Member E: [Name] | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 22+ (verified via load test)
- [PII_LEAKS_FOUND]: 0 (Post-masking implementation)

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
Record : {"service": "api", "payload": {"message_preview": "I need to update my passport [REDACTED_PASSPORT] and my address at [REDACTED_ADD..."}, "event": "request_received", "feature": "qa", "env": "dev", "model": "mock-gpt-4o", "correlation_id": "req-4332e07c", "user_id_hash": "92ec86fa8892", "session_id": "s11", "level": "info", "ts": "2026-04-20T07:53:00.888296Z"}
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: ![alt text](screenshots/orrel-traces.png)
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: ![alt text](screenshots/pii-traces.png)
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: ![alt text](screenshots/waerfall.png)
- [TRACE_WATERFALL_EXPLANATION]: "Biểu đồ Waterfall hiển thị trình tự xử lý của một yêu cầu chat. Chúng tôi đã tối ưu bảo mật bằng cách triển khai PII Masking ngay tại level Tracing (app/agent.py). Giờ đây, các thông tin nhạy cảm như Passport, Số điện thoại đều được [REDACTED] trước khi gửi lên Langfuse UI, giải quyết triệt để vấn đề rò rỉ dữ liệu trong Traces."

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 5000ms | 28d | < 200ms (Load Test) |
| Error Rate | < 2% | 28d | 0% |
| Cost Budget | < $2.5/day | 1d | $0.05 (Estimate) |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [config/alert_rules.yaml](file:///Users/bangtran/Obsidian_notes/Obsidian/Courses/4th%20year/assignments/Lab13-Observability/config/alert_rules.yaml)

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: P95 Latency spike above 5s.
- [ROOT_CAUSE_PROVED_BY]: langfuse trace id: trace-rag-slow-001
- [FIX_ACTION]: Enable incident toggle to disable recursive retrieval.
- [PREVENTIVE_MEASURE]: Added a Quality Regression alert (Bonus) to catch performance drift early.

---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: Logging, PII Recursive Scrubbing, Audit Logs implementation.
- [EVIDENCE_LINK]: app/logging_config.py, app/pii.py, app/audit.py

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: Tracing, PII-Safe Tracing Bonus, Load Testing.
- [EVIDENCE_LINK]: app/agent.py

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: Dynamic token tracking and cost-based alerting logic in config/alert_rules.yaml.
- [BONUS_AUDIT_LOGS]: Separated Audit Logs located in `data/audit.jsonl` tracking immutable control events (incident_enabled/disabled) and user sessions.
- [BONUS_CUSTOM_METRIC]: Implementation of `quality_score_avg` with associated P3 degradation alert.
