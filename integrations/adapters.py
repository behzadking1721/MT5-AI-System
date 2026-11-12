from __future__ import annotations

from typing import List, Optional, Sequence

from shared.common.types import MCPResult, ToolInfo
from shared.interfaces.mcp_adapter import MCPAdapter


class BaseMCPAdapter(MCPAdapter):
    def __init__(self, server_name: str, endpoint: str, tools: Optional[Sequence[ToolInfo]] = None) -> None:
        self.server_name = server_name
        self.endpoint = endpoint
        self._tools: List[ToolInfo] = list(tools or [])
        self.connected: bool = False  # real MCP connection performed only in P1 with user-provided env

    def set_tools(self, tools: Sequence[ToolInfo]) -> None:
        self._tools = list(tools)

    def list_tools(self) -> List[ToolInfo]:
        return list(self._tools)

    def call_tool(self, name: str, arguments: dict | None = None) -> MCPResult:
        if not self.connected:
            return MCPResult(False, error="not connected: configure and connect in P1 (read-only discovery first)", raw={"endpoint": self.endpoint, "tool": name})
        # Real call transport to be implemented after P1 tool inventory/permissions confirmed.
        return MCPResult(False, error="connected transport not implemented", raw={"endpoint": self.endpoint, "tool": name, "arguments": arguments or {}})


class MetaEditorMCPAdapter(BaseMCPAdapter):
    def __init__(self, endpoint: str = "http://127.0.0.1:22345/mcp", tools: Optional[Sequence[ToolInfo]] = None) -> None:
        super().__init__("mt5_metaeditor", endpoint, tools)


class TerminalMCPAdapter(BaseMCPAdapter):
    def __init__(self, endpoint: str = "http://127.0.0.1:22346/mcp", tools: Optional[Sequence[ToolInfo]] = None) -> None:
        super().__init__("mt5_terminal", endpoint, tools)


class MarketDataMCPAdapter(BaseMCPAdapter):
    def __init__(self, endpoint: str = "https://www.metatrader.com/mcp", tools: Optional[Sequence[ToolInfo]] = None) -> None:
        super().__init__("mt5_marketdata", endpoint, tools)

