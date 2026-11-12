from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class WorkflowRecord:
    workflow_id: str
    action: str
    status: str
    created_at: str
    updated_at: str
    details: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)


class WorkflowStateStore:
    """Simple local workflow state store. File-backed for traceability; no secrets."""

    def __init__(self, path: Optional[str | Path] = None) -> None:
        self.path = Path(path) if path else None
        self._records: Dict[str, WorkflowRecord] = {}

    def create(self, action: str, details: Optional[Dict[str, Any]] = None) -> WorkflowRecord:
        now = datetime.now(timezone.utc).isoformat()
        rec = WorkflowRecord(
            workflow_id=str(uuid4()),
            action=action,
            status="created",
            created_at=now,
            updated_at=now,
            details=details or {},
        )
        self._records[rec.workflow_id] = rec
        self._persist()
        return rec

    def update(self, workflow_id: str, status: str, details: Optional[Dict[str, Any]] = None, event: Optional[Dict[str, Any]] = None) -> Optional[WorkflowRecord]:
        rec = self._records.get(workflow_id)
        if not rec:
            return None
        rec.status = status
        rec.updated_at = datetime.now(timezone.utc).isoformat()
        if details:
            rec.details.update(details)
        if event:
            rec.events.append(event)
        self._persist()
        return rec

    def get(self, workflow_id: str) -> Optional[WorkflowRecord]:
        return self._records.get(workflow_id)

    def _persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {wid: {
            "workflow_id": r.workflow_id, "action": r.action, "status": r.status,
            "created_at": r.created_at, "updated_at": r.updated_at,
            "details": r.details, "events": r.events,
        } for wid, r in self._records.items()}
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
