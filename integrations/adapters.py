from __future__ import annotations

from typing import List

from shared.common.types import MCPResult, ToolInfo
from shared.interfaces.mcp_adapter import MCPAdapter


class MetaEditorMCPAdapter(MCPAdapter):
    server_name = "mt5_metaeditor"

    def __init__(self, endpoint: str = "http://127.0.0.1:22345/mcp") -> None:
        self.endpoint = endpoint

    def list_tools(self) -> List[ToolInfo]:
        # Placeholder until connected to real MCP endpoint in P1.
        return []

    def call_tool(self, name: str, arguments: dict | None = None) -> MCPResult:
        return MCPResult(False, error="not connected: configure and connect in P1", raw={"endpoint": self.endpoint, "tool": name})


class TerminalMCPAdapter(MCPAdapter):
    server_name = "mt5_terminal"

    def __init__(self, endpoint: str = "http://127.0.0.1:22346/mcp") -> None:
        self.endpoint = endpoint

    def list_tools(self) -> List[ToolInfo]:
        return []

    def call_tool(self, name: str, arguments: dict | None = None) -> MCPResult:
        return MCPResult(False, error="not connected: configure and connect in P1", raw={"endpoint": self.endpoint, "tool": name})


class MarketDataMCPAdapter(MCPAdapter):
    server_name = "mt5_marketdata"

    def __init__(self, endpoint: str = "https://www.metatrader.com/mcp") -> None:
        self.endpoint = endpoint

    def list_tools(self) -> List[ToolInfo]:
        return []

    def call_tool(self, name: str, arguments: dict | None = None) -> MCPResult:
        return MCPResult(False, error="not connected: configure and connect in P1", raw={"endpoint": self.endpoint, "tool": name})
