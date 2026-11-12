from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class Capability(str, Enum):
    READ = "read"
    WRITE = "write"
    COMPILE = "compile"
    BACKTEST = "backtest"
    TRADE = "trade"


@dataclass(frozen=True)
class ToolInfo:
    name: str
    server: str
    description: str = ""
    capabilities: tuple[Capability, ...] = ()
    requires_confirmation: bool = False


@dataclass
class MCPResult:
    ok: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)
