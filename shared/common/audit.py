from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4


def make_audit_event(
    actor: str,
    action: str,
    result: str,
    workflow_id: Optional[str] = None,
    input_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # Never include secrets, full account numbers, tokens, or raw credentials.
    return {
        "contract_version": "1.0.0",
        "event_id": str(uuid4()),
        "workflow_id": workflow_id,
        "actor": actor,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "input_summary": input_summary or {},
        "result": result,
    }
