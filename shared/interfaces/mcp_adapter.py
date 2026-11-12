from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List

from shared.common.types import MCPResult, ToolInfo


class MCPAdapter(ABC):
    """Base adapter for an MCP server. Implementations must be read-only by default."""

    server_name: str

    @abstractmethod
    def list_tools(self) -> List[ToolInfo]:
        raise NotImplementedError

    @abstractmethod
    def call_tool(self, name: str, arguments: dict | None = None) -> MCPResult:
        raise NotImplementedError

    def capabilities(self) -> Iterable[str]:
        caps = set()
        for t in self.list_tools():
            caps.update(c.value for c in t.capabilities)
        return sorted(caps)
