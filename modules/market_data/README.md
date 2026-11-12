# market_data (M02)

Status: **in progress (local scaffold)**. Pure data preparation/validation helpers; no live MT5/MCP connection.

## Implemented
- `prepare.py`: normalize mapping/epoch/ISO bars to `strategy_lab.Bar`, sort, validate (OHLC sanity, duplicates, negative volume, optional gap detection), and `build_daily_stats` (ATR14, avg volume 14, previous OR volumes) for ORB pipeline.

## Integration (future, P1/P4)
- Fetch bars/symbol info from `integrations/mt5_marketdata` or `mt5_terminal` read-only adapters; pass through normalization/validation before analysis.
- Persist source/timestamp/timezone metadata per `MarketSnapshot` contract; record data limitations. No secrets in artifacts.
