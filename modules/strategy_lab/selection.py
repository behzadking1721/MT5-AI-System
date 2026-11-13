from __future__ import annotations

from typing import Iterable, List

from .orb import ORBSignal


def select_stocks_in_play(
    signals: Iterable[ORBSignal],
    top_n: int = 20,
    min_relative_volume: float = 1.0,
) -> List[ORBSignal]:
    """Filter and rank ORB signals like 'Stocks in Play' selection:
    - eligible signals only
    - relative volume >= min_relative_volume (and available)
    - sorted by relative volume desc, then symbol
    - top_n results (top_n <= 0 means no limit)
    """
    filtered: List[ORBSignal] = []
    for s in signals:
        rv = s.relative_volume
        if not s.eligible:
            continue
        if rv is None or rv < min_relative_volume:
            continue
        filtered.append(s)
    filtered.sort(key=lambda x: (-(x.relative_volume or 0.0), x.symbol))
    if top_n and top_n > 0:
        return filtered[:top_n]
    return filtered
