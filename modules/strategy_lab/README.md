# strategy_lab (M03)

Status: **in progress (local scaffold)**. Pure/testable strategy logic; no MT5 connection/trading.

## Implemented
- `orb.py`: Opening Range Breakout (5/15/30/60m) analysis based on provided ORB paper text.
  - OR direction from first n-min candle (bullish->long, bearish->short, doji->none)
  - Entry at OR high/low breakout, SL = `atr14 * atr_stop_fraction` (default 10%), TP context = session close (EoD)
  - Filters: min price, min avg volume(14d), min ATR(14), Relative Volume = `ORVolume_t / mean(ORVolume_{t-14..t-1})`
  - Helpers: `atr`, `average_volume`, `relative_volume`, `opening_range_bars`

## Integration (future, P1/P4/P6)
- Feed `Bar` series and `DailyStats` from MT5 Market Data/Terminal adapters (`integrations/mt5_*`) once connected read-only.
- Signals are analysis outputs only; any execution path must pass `modules.risk_manager` and require explicit human confirmation (demo/live policy).

## Tests
- `tests/unit/test_orb.py` (`PYTHONPATH=. python -m unittest discover -v -s tests -p "test_*.py"`)

