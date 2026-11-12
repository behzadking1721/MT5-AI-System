from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from core.permission_gateway.gateway import PermissionContext, PermissionGateway
from core.module_registry.registry import ModuleRegistry


@dataclass
class WorkflowResult:
    workflow_id: str
    status: str
    details: Dict[str, Any]


class Orchestrator:
    def __init__(self, registry: ModuleRegistry | None = None, gateway: PermissionGateway | None = None) -> None:
        self.registry = registry or ModuleRegistry()
        self.gateway = gateway or PermissionGateway()

    def run_read_only(self, action: str, payload: Dict[str, Any] | None = None) -> WorkflowResult:
        ctx = PermissionContext(level="L1_read_only", trading_enabled=False, live_trading_enabled=False)
        decision = self.gateway.allow("read", ctx)
        status = "ok" if decision.allowed else "denied"
        return WorkflowResult(
            workflow_id=str(uuid4()),
            status=status,
            details={
                "action": action,
                "permission": decision.reason,
                "payload_keys": sorted((payload or {}).keys()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
