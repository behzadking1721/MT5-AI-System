"""
Demo: compute ORB entry/exit from sample bars (no MT5 connection required).
Run:  set PYTHONPATH=. && python scripts/analyze_orb_demo.py
For live MT5 data, feed bars/stats from integrations.mt5_marketdata or mt5_terminal (P1+).
"""
from datetime import datetime, timedelta

from modules.strategy_lab import Bar, DailyStats, ORBConfig, analyze_orb


def main():
    start = datetime(2024, 1, 2, 9, 30)
    # Example 5-min opening range bars (1-min granularity): bullish OR
    bars = [
        Bar(start + timedelta(minutes=0), open=100.00, high=100.80, low=99.90, close=100.20, volume=120000),
        Bar(start + timedelta(minutes=1), open=100.20, high=100.60, low=100.10, close=100.40, volume=90000),
        Bar(start + timedelta(minutes=2), open=100.40, high=100.90, low=100.30, close=100.70, volume=110000),
        Bar(start + timedelta(minutes=3), open=100.70, high=101.00, low=100.50, close=100.80, volume=95000),
        Bar(start + timedelta(minutes=4), open=100.80, high=101.20, low=100.60, close=101.10, volume=85000),
    ]
    stats = DailyStats(atr14=2.50, avg_volume14=2_000_000, prev_or_volumes=[250000] * 14)
    sig = analyze_orb("SAMPLE", bars, start, stats, ORBConfig(opening_minutes=5))

    print("direction:", sig.direction.value)
    print("eligible:", sig.eligible)
    print("OR high/low:", sig.or_high, sig.or_low)
    print("relative_volume:", sig.relative_volume)
    print("entry (breakout):", sig.entry_price)
    print("stop_loss (10% ATR14):", sig.stop_loss)
    print("risk_per_share:", sig.risk_per_share)
    print("take_profit_time (EoD):", sig.take_profit_time)
    print("reasons:", sig.reasons)


if __name__ == "__main__":
    main()
