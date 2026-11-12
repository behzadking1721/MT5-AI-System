# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial repository scaffold per `MASTER_PLAN.md` (core, modules, integrations, shared, config, mql5, tests, docs, data, reports, logs).
- Core docs: `README.md`, `.gitignore`, `DECISIONS.md`, `docs/operations/P0_ENV_CHECKLIST.md`.
- Python package scaffold (`pyproject.toml`) with orchestrator/registry/permission gateway, MCP adapter interface and placeholder adapters, shared types.
- Shared contracts (v1.0.0): `RiskDecision`, `TradeProposal`, `AccountSnapshot`, `MarketSnapshot`, `AuditEvent`, `ExecutionRequest`, `ExecutionResult`, `StrategyDefinition`, `BacktestRequest`, `BacktestResult`.
- `RiskManager` safety-first implementation with `RiskLimits`, fixed monetary/fractional sizing (pure), and limit checks (per-trade %, daily loss, drawdown, open positions, exposure, consecutive-loss circuit breaker).
- Test suite: `tests/safety` + `tests/unit` (14 tests, `unittest`, passing with `PYTHONPATH=.`).

### Notes
- No MT5/MCP connection, compilation, or trading tests performed. P0 environment/security verification items remain pending per `PROJECT_STATE.md`. Live trading disabled by policy. PDF `ssrn-4729284.pdf` present in repo but not ingested (model cannot read PDF).
