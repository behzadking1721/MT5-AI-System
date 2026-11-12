from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional, Sequence

from modules.market_data.prepare import build_daily_stats, normalize_bars, validate_bars
from modules.risk_manager.manager import RiskDecision, RiskInput, RiskLimits, RiskManager
from modules.strategy_lab.orb import DailyStats, ORBConfig, ORBSignal, analyze_orb


@dataclass
class ORBAnalysisResult:
    signal: Optional[ORBSignal]
    data_report: dict
    stats_report: dict
    risk_decision: Optional[RiskDecision]
    error: Optional[str] = None


def analyze_orb_from_payload(
    symbol: str,
    intraday_rows: Sequence[Mapping[str, Any]],
    daily_rows: Sequence[Mapping[str, Any]],
    prev_or_volumes: Sequence[float],
    session_open: datetime,
    config: ORBConfig | None = None,
    risk_input: Optional[RiskInput] = None,
    risk_limits: Optional[RiskLimits] = None,
    intraday_interval_seconds: Optional[int] = 60,
) -> ORBAnalysisResult:
    """End-to-end local analysis from raw bar payloads. No MT5/MCP calls, no trading."""
    cfg = config or ORBConfig()
    try:
        intraday = normalize_bars(intraday_rows)
        daily = normalize_bars(daily_rows)
    except Exception as e:
        return ORBAnalysisResult(None, {"ok": False, "issues": [f"normalize error: {e}"]}, {"ok": False, "issues": []}, None, str(e))

    data_rep = validate_bars(intraday, expected_interval_seconds=intraday_interval_seconds)
    stats, stats_rep = build_daily_stats(daily, prev_or_volumes)
    if not data_rep.ok or stats is None:
        return ORBAnalysisResult(
            signal=None,
            data_report={"ok": data_rep.ok, "issues": data_rep.issues, "warnings": data_rep.warnings, "stats": data_rep.stats},
            stats_report={"ok": stats_rep.ok, "issues": stats_rep.issues, "warnings": stats_rep.warnings, "stats": stats_rep.stats},
            risk_decision=None,
            error="data/stats invalid",
        )

    signal = analyze_orb(symbol, intraday, session_open, stats, cfg)
    risk_decision = None
    if risk_input is not None and signal.eligible:
        rm = RiskManager()
        # ensure proposal linkage and key prices from signal when missing
        ri = RiskInput(
            proposal_id=risk_input.proposal_id,
            symbol=risk_input.symbol or symbol,
            side=risk_input.side or signal.direction.value,
            entry_price=risk_input.entry_price if risk_input.entry_price is not None else signal.entry_price,
            stop_loss=risk_input.stop_loss if risk_input.stop_loss is not None else signal.stop_loss,
            account_equity=risk_input.account_equity,
            risk_amount=risk_input.risk_amount,
            risk_percent=risk_input.risk_percent,
            tick_value=risk_input.tick_value,
            tick_size=risk_input.tick_size,
            volume_step=risk_input.volume_step,
            volume_min=risk_input.volume_min,
            volume_max=risk_input.volume_max,
            daily_loss_pct=risk_input.daily_loss_pct,
            total_drawdown_pct=risk_input.total_drawdown_pct,
            open_positions=risk_input.open_positions,
            symbol_exposure_pct=risk_input.symbol_exposure_pct,
            consecutive_losses=risk_input.consecutive_losses,
        )
        risk_decision = rm.evaluate(ri, risk_limits)

    return ORBAnalysisResult(
        signal=signal,
        data_report={"ok": data_rep.ok, "issues": data_rep.issues, "warnings": data_rep.warnings, "stats": data_rep.stats},
        stats_report={"ok": stats_rep.ok, "issues": stats_rep.issues, "warnings": stats_rep.warnings, "stats": stats_rep.stats},
        risk_decision=risk_decision,
        error=None,
    )
