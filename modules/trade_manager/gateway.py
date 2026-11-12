from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from core.permission_gateway.gateway import PermissionContext, PermissionGateway
from modules.risk_manager.manager import RiskDecision


@dataclass(frozen=True)
class TradeProposal:
    contract_version: str
    proposal_id: str
    symbol: str
    side: str  # buy/sell
    order_type: str  # market/limit/stop
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    expiration: Optional[str]
    reason: str

    @staticmethod
    def from_orb_signal(signal: Any, order_type: str = "stop") -> "TradeProposal":
        # signal: strategy_lab.orb.ORBSignal-like
        side = getattr(signal.direction, "value", str(signal.direction))
        if side == "long":
            side = "buy"
        elif side == "short":
            side = "sell"
        return TradeProposal(
            contract_version="1.0.0",
            proposal_id=str(uuid4()),
            symbol=getattr(signal, "symbol", ""),
            side=side,
            order_type=order_type,
            entry_price=getattr(signal, "entry_price", None),
            stop_loss=getattr(signal, "stop_loss", None),
            take_profit=None,  # EoD managed separately
            expiration=None,
            reason=f"ORB {getattr(signal, 'opening_minutes', '')}m breakout; EoD exit {getattr(signal, 'take_profit_time', '')}",
        )


@dataclass(frozen=True)
class ExecutionRequest:
    contract_version: str
    request_id: str
    proposal_id: str
    risk_decision_id: str
    human_confirmation_id: str
    expires_at: str
    idempotency_key: str


@dataclass(frozen=True)
class ExecutionResult:
    contract_version: str
    request_id: str
    order_id: Optional[str]
    deal_id: Optional[str]
    status: str
    executed_price: Optional[float]
    slippage: Optional[float]
    server_message: str
    timestamp: str


class ExecutionGateway:
    """Prepares/simulates execution only after valid RiskDecision and human confirmation.
    Never sends real orders; real MT5 execution requires connected adapter + demo policy (P8)."""

    def __init__(self, gateway: PermissionGateway | None = None) -> None:
        self.gateway = gateway or PermissionGateway()
        self._seen_idempotency: set[str] = set()

    def prepare_request(
        self,
        proposal: TradeProposal,
        risk: RiskDecision,
        human_confirmation_id: Optional[str],
        ctx: PermissionContext,
        idempotency_key: Optional[str] = None,
        ttl_seconds: int = 60,
    ) -> tuple[Optional[ExecutionRequest], Optional[ExecutionResult], str]:
        # 1) risk gate - mandatory
        if risk.proposal_id != proposal.proposal_id:
            return None, self._reject(None, "risk decision proposal_id mismatch"), "risk_mismatch"
        if not risk.approved:
            return None, self._reject(None, f"risk rejected: {'; '.join(risk.reasons)}"), "risk_rejected"
        # 2) human confirmation
        if not human_confirmation_id:
            return None, self._reject(None, "human confirmation required"), "no_confirmation"
        ctx = PermissionContext(
            level=ctx.level,
            trading_enabled=ctx.trading_enabled,
            live_trading_enabled=ctx.live_trading_enabled,
            human_confirmed=True,
        )
        perm = self.gateway.allow("trade", ctx)
        if not perm.allowed:
            return None, self._reject(None, f"permission denied: {perm.reason}"), "permission_denied"
        # 3) idempotency
        idem = idempotency_key or f"{proposal.proposal_id}:{risk.decision_id}:{human_confirmation_id}"
        if idem in self._seen_idempotency:
            return None, self._reject(None, "duplicate execution request"), "duplicate"
        self._seen_idempotency.add(idem)
        # 4) build request (simulation-ready; no real send)
        now = datetime.now(timezone.utc)
        req = ExecutionRequest(
            contract_version="1.0.0",
            request_id=str(uuid4()),
            proposal_id=proposal.proposal_id,
            risk_decision_id=risk.decision_id,
            human_confirmation_id=human_confirmation_id,
            expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
            idempotency_key=idem,
        )
        return req, None, "prepared"

    def simulate_execute(self, req: ExecutionRequest, proposal: TradeProposal) -> ExecutionResult:
        # Explicitly simulated - no order sent to MT5.
        return ExecutionResult(
            contract_version="1.0.0",
            request_id=req.request_id,
            order_id=None,
            deal_id=None,
            status="simulated",
            executed_price=proposal.entry_price,
            slippage=None,
            server_message="simulated only; no MT5 connection or live/demo order sent",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _reject(request_id: Optional[str], msg: str) -> ExecutionResult:
        return ExecutionResult(
            contract_version="1.0.0",
            request_id=request_id or "",
            order_id=None,
            deal_id=None,
            status="rejected",
            executed_price=None,
            slippage=None,
            server_message=msg,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def to_dict(obj: Any) -> Dict[str, Any]:
        return asdict(obj)
