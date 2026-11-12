"""
Analyze ORB from JSON payload files (bridge for future MT5 MCP data). No MT5 connection.
Usage:
  set PYTHONPATH=. && python scripts/analyze_orb_payload.py --intraday intraday.json --daily daily.json --prev-or prev_or.json --session-open 2024-01-02T09:30:00 --symbol SAMPLE
JSON formats:
  intraday/daily: list of {time, open, high, low, close, volume|tick_volume}
  prev_or: list of numbers (previous 14 opening-range volumes)
Optional: --equity, --risk-pct, --tick-value, --tick-size, --volume-step, --volume-min, --volume-max
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime

from modules.risk_manager.manager import RiskInput, RiskLimits
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

    from modules.strategy_lab import ORBConfig
    cfg = ORBConfig(opening_minutes=args.opening_minutes)
    risk_input = None
    if args.equity and args.risk_pct and args.tick_value and args.tick_size:
        risk_input = RiskInput(
            proposal_id=f"payload-{args.symbol}", symbol=args.symbol, side="buy",
            entry_price=None, stop_loss=None, account_equity=args.equity, risk_percent=args.risk_pct,
            tick_value=args.tick_value, tick_size=args.tick_size,
            volume_step=args.volume_step, volume_min=args.volume_min, volume_max=args.volume_max,
        )
    res = analyze_orb_from_payload(
        args.symbol, intraday, daily, prev_or, session_open, cfg,
        risk_input=risk_input, risk_limits=RiskLimits(),
    )
    out = {
        "error": res.error,
        "data_report": res.data_report,
        "stats_report": res.stats_report,
        "signal": res.signal.to_dict() if res.signal else None,
        "risk_decision": (res.risk_decision.__dict__ if res.risk_decision else None),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
