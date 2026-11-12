# Decision Log — MT5-AI-MODULAR

Record architectural and process decisions here. Each entry: date, status, context, decision, consequences.

## 2026-11-12 — D001: Adopt master plan and execution state as handoff sources
- **Status:** Accepted
- **Context:** Project must be transferable across AI assistants and sessions.
- **Decision:** `MASTER_PLAN.md` is the strategic reference; `PROJECT_STATE.md` is the live execution ledger. No task is DONE without evidence in state.
- **Consequences:** All future work must update state/changelog and cite evidence.

## 2026-11-12 — D002: Modular architecture with strict boundaries
- **Status:** Accepted
- **Context:** Need independent modules, testability, and future MCP/client portability.
- **Decision:** M00–M09 modules with ownership, independent configs/tests/docs; inter-module communication via versioned contracts in `shared/contracts`; Risk Manager is mandatory gate for any trade path.
- **Consequences:** Adapters isolate MCP/tooling; domain logic must not depend on a specific AI client.

## 2026-11-12 — D003: Safety-first rollout
- **Status:** Accepted
- **Context:** Trading and system access carry financial/security risk.
- **Decision:** Start read-only/experimental, demo before any live consideration, explicit human confirmation for orders, no secrets in repo, live trading disabled by default until P10 gates pass.
- **Consequences:** Early phases prioritize discovery, contracts, and risk controls over execution features.
