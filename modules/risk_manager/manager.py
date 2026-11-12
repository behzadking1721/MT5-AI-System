from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4


@dataclass
class RiskInput:
    proposal_id: str
    symbol: str
    side: str
    entry_price: Optional[float]
    stop_loss: Optional[float]
    account_equity: Optional[float] = None
    risk_percent: Optional[float] = None


@dataclass
class RiskDecision:
    contract_version: str
    decision_id: str
    proposal_id: str
    approved: bool
    volume: float
    risk_amount: Optional[float]
    risk_percent: Optional[float]
    limits_checked: List[str]
    reasons: List[str]
    timestamp: str


class RiskManager:
    """Safety-first stub. Real sizing/risk math to be implemented in P5 with full tests."""

    def evaluate(self, inp: RiskInput) -> RiskDecision:
        reasons: List[str] = []
        approved = True
        limits = ["stop_loss_required", "no_live_trade_policy"]

        if inp.stop_loss is None:
            approved = False
            reasons.append("missing stop loss")

        if not approved:
            reasons.append("rejected by safety-first policy")
        else:
            reasons.append("preliminary approval only; sizing not computed in scaffold")

        return RiskDecision(
            contract_version="1.0.0",
            decision_id=str(uuid4()),
            proposal_id=inp.proposal_id,
            approved=approved,
            volume=0.0,
            risk_amount=None,
            risk_percent=inp.risk_percent,
            limits_checked=limits,
            reasons=reasons,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def to_contract_dict(decision: RiskDecision) -> dict:
        return asdict(decision)
