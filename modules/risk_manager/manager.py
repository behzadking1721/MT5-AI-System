from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import floor
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
    risk_amount: Optional[float] = None
    risk_percent: Optional[float] = None
    # symbol/contract data required for sizing
    tick_value: Optional[float] = None  # account currency value per tick
    tick_size: Optional[float] = None
    volume_step: Optional[float] = None
    volume_min: Optional[float] = None
    volume_max: Optional[float] = None


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


def _floor_to_step(value: float, step: float) -> float:
    if step <= 0:
        return value
    return floor(value / step) * step


class RiskManager:
    """Safety-first risk gate. Pure sizing helpers require explicit symbol/risk inputs."""

    @staticmethod
    def calculate_volume_fixed_monetary(
        entry: float, sl: float, risk_amount: float, tick_value: float, tick_size: float,
        volume_step: float = 0.01, volume_min: float = 0.01, volume_max: float = 100.0,
    ) -> tuple[float, list[str]]:
        reasons: list[str] = []
        if risk_amount <= 0 or tick_value <= 0 or tick_size <= 0:
            return 0.0, ["invalid monetary risk inputs"]
        distance = abs(entry - sl)
        if distance <= 0:
            return 0.0, ["invalid stop distance"]
        ticks = round(distance / tick_size, 10)
        loss_per_lot = ticks * tick_value
        if loss_per_lot <= 0:
            return 0.0, ["invalid loss per lot"]
        raw = risk_amount / loss_per_lot
        vol = _floor_to_step(raw, volume_step)
        if vol < volume_min:
            reasons.append("volume below minimum after risk cap")
            return 0.0, reasons
        if vol > volume_max:
            vol = volume_max
            reasons.append("volume capped at maximum")
        return round(vol, 8), reasons

    @staticmethod
    def calculate_volume_fixed_fractional(equity: float, risk_percent: float, **kwargs) -> tuple[float, list[str]]:
        if equity <= 0 or risk_percent <= 0:
            return 0.0, ["invalid fractional risk inputs"]
        risk_amount = equity * (risk_percent / 100.0)
        return RiskManager.calculate_volume_fixed_monetary(risk_amount=risk_amount, **kwargs)

    def evaluate(self, inp: RiskInput) -> RiskDecision:
        reasons: List[str] = []
        approved = True
        limits = ["stop_loss_required", "no_live_trade_policy", "sizing_inputs_required"]
        volume = 0.0
        risk_amount = inp.risk_amount

        if inp.entry_price is None:
            approved = False
            reasons.append("missing entry price")
        if inp.stop_loss is None:
            approved = False
            reasons.append("missing stop loss")
        elif inp.risk_percent is not None and inp.account_equity is not None:
            can_size = all(v is not None for v in [inp.tick_value, inp.tick_size, inp.volume_step, inp.volume_min, inp.volume_max])
            if can_size:
                volume, msgs = self.calculate_volume_fixed_fractional(
                    equity=inp.account_equity, risk_percent=inp.risk_percent,
                    entry=inp.entry_price, sl=inp.stop_loss,
                    tick_value=inp.tick_value, tick_size=inp.tick_size,
                    volume_step=inp.volume_step, volume_min=inp.volume_min, volume_max=inp.volume_max,
                )
                reasons.extend(msgs)
                if volume <= 0:
                    approved = False
                    reasons.append("sizing produced zero/invalid volume")
            else:
                reasons.append("fractional sizing inputs incomplete; volume not computed")
        elif inp.risk_amount is not None:
            can_size = all(v is not None for v in [inp.tick_value, inp.tick_size, inp.volume_step, inp.volume_min, inp.volume_max])
            if can_size:
                volume, msgs = self.calculate_volume_fixed_monetary(
                    entry=inp.entry_price, sl=inp.stop_loss, risk_amount=inp.risk_amount,
                    tick_value=inp.tick_value, tick_size=inp.tick_size,
                    volume_step=inp.volume_step, volume_min=inp.volume_min, volume_max=inp.volume_max,
                )
                reasons.extend(msgs)
                if volume <= 0:
                    approved = False
                    reasons.append("sizing produced zero/invalid volume")
            else:
                reasons.append("monetary sizing inputs incomplete; volume not computed")
        else:
            reasons.append("no risk amount/percent provided; volume not computed")

        if not approved and not reasons:
            reasons.append("rejected by safety-first policy")
        elif approved and volume == 0.0 and "volume not computed" not in " ".join(reasons):
            reasons.append("approved preliminarily; verify sizing before any execution path")

        return RiskDecision(
            contract_version="1.0.0",
            decision_id=str(uuid4()),
            proposal_id=inp.proposal_id,
            approved=approved,
            volume=volume,
            risk_amount=risk_amount,
            risk_percent=inp.risk_percent,
            limits_checked=limits,
            reasons=reasons,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def to_contract_dict(decision: RiskDecision) -> dict:
        return asdict(decision)

