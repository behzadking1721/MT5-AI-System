from __future__ import annotations

from typing import Dict, Optional

from shared.interfaces.mcp_adapter import MCPAdapter


class ModuleRegistry:
    def __init__(self) -> None:
        self._adapters: Dict[str, MCPAdapter] = {}

    def register_adapter(self, adapter: MCPAdapter) -> None:
        self._adapters[adapter.server_name] = adapter

    def get_adapter(self, server_name: str) -> Optional[MCPAdapter]:
        return self._adapters.get(server_name)

    def list_adapters(self) -> list[str]:
        return sorted(self._adapters.keys())
