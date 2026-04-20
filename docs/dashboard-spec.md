# Dashboard Specification: System Health

This document defines the 6-panel "System Health" dashboard for the Day 13 Observability Lab, incorporating SLO thresholds and recovery targets.

## Panel Overview

| # | Panel Name | Metric / Query | Visualization | Thresholds (SLO) |
|---|------------|----------------|---------------|------------------|
| 1 | **Traffic (Throughput)** | `http_requests_total` rate | Time-series | N/A |
| 2 | **Availability (SR)** | `(success / total) * 100` | Gauge / Trend | **SLO: 99.0%** (Yellow: 99.5%) |
| 3 | **Latencies (P50/P95)** | `http_request_duration_seconds` | Dist / Percentile | **SLO P95: 5000ms** |
| 4 | **AI Quality Score** | `quality_score_avg` | Gauge | **SLO: 0.75** (Critical: < 0.6) |
| 5 | **Cost & Budget** | `daily_cost_usd` | Cumulative / Bar | **Limit: $2.50 / day** |
| 6 | **Error Breakdown** | `http_errors_total` by `type` | Donut / Pie | Goal: 0 |

---

## Detailed Panel Specifications

### 1. Throughput (Member A/B)
- **Goal**: Monitor system load and seasonality.
- **Metric**: `rate(http_requests_total[5m])`
- **Visualization**: Area chart, grouped by `feature`.

### 2. Success Rate (Member E)
- **Goal**: High-level indicator of "Are we up?".
- **Metric**: `sum(rate(http_requests_total{status=~"200"}[5m])) / sum(rate(http_requests_total[5m]))`
- **Threshold**: Add a solid green line at **99%**.

### 3. Response Time Distribution (Member B)
- **Goal**: Customer experience tracking.
- **Metric**: `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m]))`
- **Threshold**: Add a red line at **5s** (SLO boundary).

### 4. Generation Quality (Member D)
- **Goal**: Measure "Smartness" vs "Drift".
- **Metric**: `avg(quality_score_avg)`
- **Color Mapping**: 
  - 0.8 - 1.0: Green (Excellent)
  - 0.6 - 0.79: Yellow (Watch)
  - < 0.6: Red (Alert)

### 5. Cloud Cost Consumption (Member C)
- **Goal**: Prevent budget burn.
- **Metric**: `sum(daily_cost_usd)`
- **Visualization**: Stacked bar by `model`.
- **Target**: Max $2.50 / 24h.

### 6. Error Signal (Member A)
- **Goal**: Identify top failure points.
- **Metric**: `sum by (error_type) (http_errors_total)`
- **Action**: Drill down into traces if `LLMTimeout` spikes.
