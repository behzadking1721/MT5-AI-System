# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial repository scaffold per `MASTER_PLAN.md` (core, modules, integrations, shared, config, mql5, tests, docs, data, reports, logs).
- Core docs: `README.md`, `.gitignore`, `DECISIONS.md`, `docs/operations/P0_ENV_CHECKLIST.md`.
- Python package scaffold (`pyproject.toml`) with orchestrator/registry/permission gateway, MCP adapter interface and placeholder adapters, shared types.
- Shared contracts (v1.0.0): `RiskDecision`, `TradeProposal`, `AccountSnapshot`, `MarketSnapshot`, `AuditEvent`, `ExecutionRequest`, `ExecutionResult`, `StrategyDefinition`, `BacktestRequest`, `BacktestResult`.
- `RiskManager` safety-first implementation with `RiskLimits`, fixed monetary/fractional sizing (pure), limit checks (per-trade %, daily loss, drawdown, open positions, exposure, consecutive-loss circuit breaker), ATR-adjusted sizing helper, and Fractional Kelly risk% with hard cap.
- `modules/strategy_lab/orb.py`: pure ORB (n-min, default 5m) analysis from paper text — OR direction, breakout entry, SL=`ATR14*fraction`, EoD TP context, universe/relative-volume filters, helpers.
- `modules/strategy_lab/pipeline.py`: `analyze_orb_from_payload` bridge (raw bar payloads → validate/build stats → ORB signal + optional RiskDecision), no MT5/MCP calls.
- `modules/market_data/prepare.py`: bar normalization/validation (OHLC/duplicates/gaps) and `DailyStats` builder for ORB inputs.
- `modules/trade_manager/gateway.py`: simulation-only execution gateway (TradeProposal/Request/Result), enforces RiskDecision approval, human confirmation id, permission gate, and idempotency; `simulate_execute` only.
- `shared/common/audit.py`, `core/workflow_state/store.py`: audit event helper and file-backed workflow state store (no secrets).
- Demo/scripts: `scripts/analyze_orb_demo.py`, `scripts/pipeline_demo.py`, `scripts/analyze_orb_payload.py` (JSON payload → ORB/risk).
- MQL5 read-only template: `mql5/Experts/ORB_Analyzer_Template.mq5` (no order actions).
- Test suite: `tests/safety` + `tests/unit` (43 tests, `unittest`, passing with `PYTHONPATH=.`).

### Notes
- No MT5/MCP connection, compilation, or trading tests performed. P0 environment/security verification items remain pending per `PROJECT_STATE.md`. Live trading disabled by policy. `ssrn-4729284.pdf` present but not parsed (PDF input unsupported).
