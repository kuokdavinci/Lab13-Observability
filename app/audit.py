import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_LOG_PATH = Path(os.getenv("AUDIT_LOG_PATH", "data/audit.jsonl"))

def audit_log(event: str, actor: str = "system", payload: dict[str, Any] | None = None) -> None:
    """Write an immutable-style audit record to a dedicated file."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "actor": actor,
        "payload": payload or {},
    }
    
    # Ensure directory exists
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
