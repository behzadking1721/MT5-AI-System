"""
Human-readable ORB signal report from JSON payloads (no MT5 connection).
Usage:
  set PYTHONPATH=. && python scripts/orb_report.py --symbol SAMPLE ^
    --intraday data/samples/intraday_sample.json ^
    --daily data/samples/daily_sample.json ^
    --prev-or data/samples/prev_or_sample.json ^
    --session-open 2024-01-02T09:30:00 [--equity 10000 --risk-pct 0.5 --tick-value 1 --tick-size 0.01]
Output: entry/exit plan (analysis only). Execution requires Risk Manager + explicit human confirmation; live disabled.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime

from modules.risk_manager.manager import RiskInput, RiskLimits
from modules.strategy_lab import ORBConfig
from modules.strategy_lab.pipeline import analyze_orb_from_payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--intraday", required=True)
    ap.add_argument("--daily", required=True)
    ap.add_argument("--prev-or", required=True)
    ap.add_argument("--session-open", required=True)
    ap.add_argument("--opening-minutes", type=int, default=5)
    ap.add_argument("--equity", type=float)
    ap.add_argument("--risk-pct", type=float)
    ap.add_argument("--tick-value", type=float)
    ap.add_argument("--tick-size", type=float)
    ap.add_argument("--volume-step", type=float, default=0.01)
    ap.add_argument("--volume-min", type=float, default=0.01)
    ap.add_argument("--volume-max", type=float, default=100.0)
    args = ap.parse_args()

    with open(args.intraday, "r", encoding="utf-8") as f:
        intraday = json.load(f)
    with open(args.daily, "r", encoding="utf-8") as f:
        daily = json.load(f)
    with open(args.prev_or, "r", encoding="utf-8") as f:
        prev_or = json.load(f)
    session_open = datetime.fromisoformat(args.session_open)

    cfg = ORBConfig(opening_minutes=args.opening_minutes)
    risk_input = None
    if args.equity and args.risk_pct and args.tick_value and args.tick_size:
        risk_input = RiskInput(
            proposal_id=f"payload-{args.symbol}", symbol=args.symbol, side="buy",
            entry_price=None, stop_loss=None, account_equity=args.equity, risk_percent=args.risk_pct,
            tick_value=args.tick_value, tick_size=args.tick_size,
            volume_step=args.volume_step, volume_min=args.volume_min, volume_max=args.volume_max,
        )
    res = analyze_orb_from_payload(args.symbol, intraday, daily, prev_or, session_open, cfg, risk_input=risk_input, risk_limits=RiskLimits())

    print(f"Symbol: {args.symbol}")
    print(f"Data OK: {res.data_report.get('ok')}  issues={res.data_report.get('issues')} warnings={res.data_report.get('warnings')}")
    print(f"Stats OK: {res.stats_report.get('ok')}  issues={res.stats_report.get('issues')}")
    if res.error or not res.signal:
        print(f"Result: NO SIGNAL ({res.error})")
        return 1

    s = res.signal
    print(f"Eligible: {s.eligible}  Reasons: {s.reasons or 'none'}")
    print(f"OR ({s.opening_minutes}m): open={s.or_open} high={s.or_high} low={s.or_low} close={s.or_close} vol={s.or_volume}")
    print(f"Relative Volume: {s.relative_volume}")
    print(f"Direction: {s.direction.value.upper()}")
    if s.direction.value == "none" or not s.eligible:
        print("Entry/Exit: none (ineligible)")
    else:
        trigger = "stop-buy above OR high" if s.direction.value == "long" else "stop-sell below OR low"
        print(f"Entry (breakout): {s.entry_price} ({trigger})")
        print(f"Stop Loss: {s.stop_loss}  (risk/share={s.risk_per_share}, ATR14={s.atr14}, {cfg.atr_stop_fraction*100:.0f}% ATR)")
        print(f"Take Profit: EoD close ({s.take_profit_time}) if not stopped")
    if res.risk_decision:
        d = res.risk_decision
        print(f"RiskDecision: approved={d.approved} volume={d.volume} risk_amount={d.risk_amount} risk_percent={d.risk_percent}")
        print(f"Risk reasons: {d.reasons}")
    print("Note: analysis only; no order sent. Any execution requires Risk Manager + explicit human confirmation (live disabled).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
