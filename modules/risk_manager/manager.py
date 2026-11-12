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
    # portfolio/state context for limit checks (all optional, fail-safe when policy requires)
    daily_loss_pct: Optional[float] = None
    total_drawdown_pct: Optional[float] = None
    open_positions: Optional[int] = None
    symbol_exposure_pct: Optional[float] = None
    consecutive_losses: Optional[int] = None


@dataclass
class RiskLimits:
    max_risk_per_trade_pct: float = 0.5
    max_daily_loss_pct: float = 2.0
    max_total_drawdown_pct: float = 10.0
    max_open_positions: int = 3
    max_symbol_exposure_pct: float = 2.0
    max_consecutive_losses: int = 3
    require_stop_loss: bool = True
    allow_martingale: bool = False
    live_trading_enabled: bool = False


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

    def evaluate(self, inp: RiskInput, limits: RiskLimits | None = None) -> RiskDecision:
        limits = limits or RiskLimits()
        reasons: List[str] = []
        approved = True
        checked = ["stop_loss_required", "no_live_trade_policy", "trade_risk_limit", "daily_loss_limit", "drawdown_limit", "exposure_limit", "circuit_breaker"]
        volume = 0.0
        risk_amount = inp.risk_amount

        if limits.live_trading_enabled:
            approved = False
            reasons.append("live trading disabled by policy")

        if limits.require_stop_loss and inp.stop_loss is None:
            approved = False
            reasons.append("missing stop loss")
        elif inp.stop_loss is None:
            reasons.append("stop loss missing (not required by current policy)")
        if inp.entry_price is None:
            approved = False
            reasons.append("missing entry price")

        # per-trade risk percent limit
        eff_risk_pct = inp.risk_percent
        if eff_risk_pct is None and inp.risk_amount is not None and inp.account_equity:
            eff_risk_pct = (inp.risk_amount / inp.account_equity) * 100.0
        if eff_risk_pct is not None and eff_risk_pct > limits.max_risk_per_trade_pct:
            approved = False
            reasons.append(f"risk percent {eff_risk_pct:.4f} exceeds max {limits.max_risk_per_trade_pct:.4f}")

        # portfolio/state guards (reject if breached or unknown when state provided as breach context)
        if inp.daily_loss_pct is not None and inp.daily_loss_pct >= limits.max_daily_loss_pct:
            approved = False
            reasons.append("daily loss limit breached")
        if inp.total_drawdown_pct is not None and inp.total_drawdown_pct >= limits.max_total_drawdown_pct:
            approved = False
            reasons.append("total drawdown limit breached")
        if inp.open_positions is not None and inp.open_positions >= limits.max_open_positions:
            approved = False
            reasons.append("max open positions reached")
        if inp.symbol_exposure_pct is not None and inp.symbol_exposure_pct >= limits.max_symbol_exposure_pct:
            approved = False
            reasons.append("symbol exposure limit breached")
        if inp.consecutive_losses is not None and inp.consecutive_losses >= limits.max_consecutive_losses:
            approved = False
            reasons.append("consecutive loss circuit breaker active")

        # sizing (only if basic inputs valid)
        can_try_sizing = approved and inp.entry_price is not None and inp.stop_loss is not None
        if can_try_sizing and eff_risk_pct is not None and inp.account_equity is not None:
            can_size = all(v is not None for v in [inp.tick_value, inp.tick_size, inp.volume_step, inp.volume_min, inp.volume_max])
            if can_size:
                volume, msgs = self.calculate_volume_fixed_fractional(
                    equity=inp.account_equity, risk_percent=min(eff_risk_pct, limits.max_risk_per_trade_pct),
                    entry=inp.entry_price, sl=inp.stop_loss,
                    tick_value=inp.tick_value, tick_size=inp.tick_size,
                    volume_step=inp.volume_step, volume_min=inp.volume_min, volume_max=inp.volume_max,
                )
                reasons.extend(msgs)
                if volume <= 0:
                    approved = False
                    reasons.append("sizing produced zero/invalid volume")
                risk_amount = inp.account_equity * (min(eff_risk_pct, limits.max_risk_per_trade_pct) / 100.0)
            else:
                reasons.append("fractional sizing inputs incomplete; volume not computed")
        elif can_try_sizing and inp.risk_amount is not None:
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
        elif can_try_sizing:
            reasons.append("no risk amount/percent provided; volume not computed")

        if not approved and not reasons:
            reasons.append("rejected by safety-first policy")

        return RiskDecision(
            contract_version="1.0.0",
            decision_id=str(uuid4()),
            proposal_id=inp.proposal_id,
            approved=approved,
            volume=volume,
            risk_amount=risk_amount,
            risk_percent=eff_risk_pct if eff_risk_pct is not None else inp.risk_percent,
            limits_checked=checked,
            reasons=reasons,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def to_contract_dict(decision: RiskDecision) -> dict:
        return asdict(decision)

