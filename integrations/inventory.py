from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

from shared.common.types import Capability, ToolInfo


_CAP_MAP = {
    "read": Capability.READ,
    "write": Capability.WRITE,
    "compile": Capability.COMPILE,
    "backtest": Capability.BACKTEST,
    "trade": Capability.TRADE,
}


def capabilities_from_flags(flags: Mapping[str, Any]) -> tuple[Capability, ...]:
    caps: List[Capability] = []
    for k, cap in _CAP_MAP.items():
        v = flags.get(k)
        if v is True or (isinstance(v, str) and v.lower() in ("yes", "true", "1", "y")):
            caps.append(cap)
    return tuple(caps)


def toolinfo_from_dict(server: str, d: Mapping[str, Any]) -> ToolInfo:
    name = str(d.get("name") or d.get("tool") or "")
    desc = str(d.get("purpose") or d.get("description") or "")
    # flags can be top-level booleans or nested
    flags = d.get("capabilities") if isinstance(d.get("capabilities"), dict) else d
    caps = capabilities_from_flags(flags)
    requires_confirmation = bool(d.get("requires_confirmation", False))
    # heuristic: trade/compile/write should require confirmation by policy
    if any(c in caps for c in (Capability.TRADE, Capability.WRITE, Capability.COMPILE, Capability.BACKTEST)):
        requires_confirmation = True
    return ToolInfo(name=name, server=server, description=desc, capabilities=caps, requires_confirmation=requires_confirmation)


def load_inventory(data: Mapping[str, Any]) -> Dict[str, List[ToolInfo]]:
    """Load tool inventory from a dict structure.
    Expected: {"servers": {"mt5_terminal": {"endpoint":..., "tools":[{name,purpose,read,write,...}, ...]}, ...}}
    Also accepts {"mt5_terminal": [..tools..]} shorthand.
    """
    out: Dict[str, List[ToolInfo]] = {}
    servers = data.get("servers", data)
    if not isinstance(servers, Mapping):
        return out
    for server, payload in servers.items():
        tools_raw: Iterable[Any]
        if isinstance(payload, list):
            tools_raw = payload
        elif isinstance(payload, Mapping):
            tools_raw = payload.get("tools", [])
        else:
            tools_raw = []
        items: List[ToolInfo] = []
        for t in tools_raw:
            if isinstance(t, Mapping):
                ti = toolinfo_from_dict(str(server), t)
                if ti.name:
                    items.append(ti)
        out[str(server)] = items
    return out


def load_inventory_file(path: str | Path) -> Dict[str, List[ToolInfo]]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, Mapping):
        return {}
    return load_inventory(data)
