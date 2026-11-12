# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Initial repository scaffold: directory structure per `MASTER_PLAN.md` (core, modules, integrations, shared, config, mql5, tests, docs, data, reports, logs).
- `README.md`, `.gitignore`, `DECISIONS.md`, initial module READMEs and contract stubs.
- `docs/operations/P0_ENV_CHECKLIST.md` for P0 environment/safety capture.
- Python package scaffold (`pyproject.toml`, `__init__`s) with core orchestrator, module registry, permission gateway, MCP adapter interface and placeholder adapters (`integrations/adapters.py`), shared types, and safety-first `RiskManager` stub; syntax-checked via `py_compile`.
- Git repository initialized and committed locally (no remote configured).
