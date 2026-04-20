import json
import re
from pathlib import Path

def generate_stats():
    log_path = Path("data/logs.jsonl")
    if not log_path.exists():
        return None

    records = []
    for line in log_path.read_text().splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except: continue

    chat_responses = [r for r in records if r.get("event") == "response_sent"]
    total_requests = len(chat_responses)
    total_cost = sum(r.get("cost_usd", 0) for r in chat_responses)
    unique_cids = len(set(r.get("correlation_id") for r in records if r.get("correlation_id")))
    
    # Tìm cache hits (những request có cost = 0 và không phải lỗi)
    cache_hits = len([r for r in chat_responses if r.get("cost_usd") == 0 and r.get("tokens_in") == 0])

    return {
        "total_requests": total_requests,
        "total_cost": total_cost,
        "total_traces": unique_cids,
        "cache_hits": cache_hits
    }

def update_report(stats):
    report_path = Path("docs/blueprint-template.md")
    if not report_path.exists():
        print("Không tìm thấy docs/blueprint-template.md")
        return

    content = report_path.read_text()

    # Cập nhật số lượng Traces
    content = re.sub(r"\[TOTAL_TRACES_COUNT\]: .*", f"[TOTAL_TRACES_COUNT]: {stats['total_traces']}+", content)
    
    # Thêm thông tin vào phần Bonus Cost Optimization
    cost_optimization_text = f"[BONUS_COST_OPTIMIZATION]: Đã triển khai Exact Match Caching. Phát hiện {stats['cache_hits']} yêu cầu lặp lại được phục vụ từ cache với Chi phí = 0$, tiết kiệm tài nguyên LLM."
    content = re.sub(r"\[BONUS_COST_OPTIMIZATION\]: .*", cost_optimization_text, content)

    report_path.write_text(content)
    print(f"✅ Báo cáo đã cập nhật: {stats['total_requests']} requests, {stats['cache_hits']} cache hits, Tổng cost: ${stats['total_cost']:.5f}")

if __name__ == "__main__":
    stats = generate_stats()
    if stats:
        update_report(stats)
    else:
        print("❌ Không tìm thấy log dữ liệu!")
