import argparse
import concurrent.futures
import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://127.0.0.1:8000"
QUERIES = Path("data/sample_queries.jsonl")


def send_request(client: httpx.Client, payload: dict) -> None:
    try:
        start = time.perf_counter()
        r = client.post(f"{BASE_URL}/chat", json=payload)
        latency = (time.perf_counter() - start) * 1000
        print(f"[{r.status_code}] {r.json().get('correlation_id')} | {payload['feature']} | {latency:.1f}ms")
    except Exception as e:
        print(f"Error: {e}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=1, help="Number of concurrent requests")
    parser.add_argument("--requests", type=int, default=10, help="Total number of requests to send")
    args = parser.parse_args()

    # Load queries and handle empty/limited data
    lines = [line for line in QUERIES.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        print("Error: data/sample_queries.jsonl is empty")
        return
        
    # Repeat or slice queries to match exactly the --requests count
    query_payloads = []
    while len(query_payloads) < args.requests:
        query_payloads.extend([json.loads(l) for l in lines])
    query_payloads = query_payloads[:args.requests]
    
    print(f"🚀 Running load test with {args.concurrency} concurrent workers for {args.requests} total requests...")
    
    with httpx.Client(timeout=30.0) as client:
        if args.concurrency > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as executor:
                futures = [executor.submit(send_request, client, payload) for payload in query_payloads]
                concurrent.futures.wait(futures)
        else:
            for payload in query_payloads:
                send_request(client, payload)


if __name__ == "__main__":
    main()
