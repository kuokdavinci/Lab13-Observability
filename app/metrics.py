from __future__ import annotations

from prometheus_client import Counter, Histogram, generate_latest
from collections import Counter as CollectionsCounter
from statistics import mean

# Prometheus metrics
request_count = Counter('http_requests_total', 'Total number of HTTP requests', ['method', 'endpoint', 'status'])
error_count = Counter('http_errors_total', 'Total number of HTTP errors', ['error_type'])
latency_seconds = Histogram('http_request_duration_seconds', 'HTTP request duration in seconds', ['endpoint'])

REQUEST_LATENCIES: list[int] = []
REQUEST_COSTS: list[float] = []
REQUEST_TOKENS_IN: list[int] = []
REQUEST_TOKENS_OUT: list[int] = []
ERRORS: CollectionsCounter[str] = CollectionsCounter()
TRAFFIC: int = 0
QUALITY_SCORES: list[float] = []


def record_request(latency_ms: int, cost_usd: float, tokens_in: int, tokens_out: int, quality_score: float, method: str = 'POST', endpoint: str = '/chat', status: str = '200') -> None:
    global TRAFFIC
    TRAFFIC += 1
    REQUEST_LATENCIES.append(latency_ms)
    REQUEST_COSTS.append(cost_usd)
    REQUEST_TOKENS_IN.append(tokens_in)
    REQUEST_TOKENS_OUT.append(tokens_out)
    QUALITY_SCORES.append(quality_score)
    
    # Record Prometheus metrics
    request_count.labels(method=method, endpoint=endpoint, status=status).inc()
    latency_seconds.labels(endpoint=endpoint).observe(latency_ms / 1000.0)


def record_error(error_type: str, method: str = 'POST', endpoint: str = '/chat', status: str = '500') -> None:
    ERRORS[error_type] += 1
    # Record Prometheus metrics
    error_count.labels(error_type=error_type).inc()
    request_count.labels(method=method, endpoint=endpoint, status=status).inc()


def percentile(values: list[int], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def snapshot() -> dict:
    return {
        "traffic": TRAFFIC,
        "latency_p50": percentile(REQUEST_LATENCIES, 50),
        "latency_p95": percentile(REQUEST_LATENCIES, 95),
        "latency_p99": percentile(REQUEST_LATENCIES, 99),
        "avg_cost_usd": round(mean(REQUEST_COSTS), 4) if REQUEST_COSTS else 0.0,
        "total_cost_usd": round(sum(REQUEST_COSTS), 4),
        "tokens_in_total": sum(REQUEST_TOKENS_IN),
        "tokens_out_total": sum(REQUEST_TOKENS_OUT),
        "error_breakdown": dict(ERRORS),
        "quality_avg": round(mean(QUALITY_SCORES), 4) if QUALITY_SCORES else 0.0,
    }


def get_prometheus_metrics() -> str:
    return generate_latest().decode('utf-8')
