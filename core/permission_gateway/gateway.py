from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PermissionContext:
    level: str = "L1_read_only"
    trading_enabled: bool = False
    live_trading_enabled: bool = False
    human_confirmed: bool = False


@dataclass(frozen=True)
class PermissionDecision:
    allowed: bool
    reason: str


class PermissionGateway:
    """Minimal gate; extend with config-driven rules. Trade is denied by default."""

    def allow(self, action: str, ctx: PermissionContext) -> PermissionDecision:
        if action == "trade":
            if not ctx.trading_enabled:
                return PermissionDecision(False, "trading disabled")
            if ctx.live_trading_enabled:
                return PermissionDecision(False, "live trading disabled by policy")
            if not ctx.human_confirmed:
                return PermissionDecision(False, "human confirmation required")
        if action in {"write", "compile", "backtest"} and ctx.level in {"L0", "L1_read_only"}:
            return PermissionDecision(False, f"action '{action}' not permitted at level {ctx.level}")
        return PermissionDecision(True, "allowed")
