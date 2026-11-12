# trade_manager / Execution Gateway (M05)

Status: **scaffolded, simulation-only**. No real MT5 orders; no MCP connection.

## Implemented
- `gateway.py`: `TradeProposal`, `ExecutionRequest`, `ExecutionResult`, `ExecutionGateway`
  - `prepare_request`: requires matching approved `RiskDecision`, `human_confirmation_id`, permission gate (`trade` enabled, not live, confirmed), idempotency; returns prepared request or rejection result.
  - `simulate_execute`: returns `status=simulated` only (explicitly no order sent).
  - `from_orb_signal`: builds proposal from strategy ORB signal (entry/SL, EoD context).

## Safety (enforced in code/tests)
- No execution path without valid Risk Manager approval.
- No execution without explicit human confirmation id.
- Live trading denied by policy/gateway; demo/trade flag required.
- Duplicate idempotency keys rejected.

## Future (P8, demo only, after gates)
- Wire to `integrations.mt5_terminal` adapter, enforce symbol/volume allowlists, expiry/price-change checks, server response reconciliation, and full audit events. All subject to PROJECT_STATE evidence and human approval.
