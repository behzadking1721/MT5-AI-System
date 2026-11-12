from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Iterable, List, Mapping, Optional, Sequence, Tuple

from modules.strategy_lab.orb import Bar, DailyStats, atr, average_volume


@dataclass
class DataQualityReport:
    ok: bool
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def add_issue(self, msg: str) -> None:
        self.issues.append(msg)
        self.ok = False

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


def _to_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        # assume epoch seconds
        return datetime.utcfromtimestamp(value)
    if isinstance(value, str):
        # best-effort ISO parse
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return datetime.fromisoformat(value)
    raise TypeError(f"unsupported time value: {type(value)!r}")


def bar_from_mapping(m: Mapping[str, Any]) -> Bar:
    """Normalize a dict-like bar (e.g. from MT5 MCP/tool output) into Bar.
    Accepted keys: time/timestamp/datetime, open, high, low, close, volume/tick_volume/real_volume."""
    t = m.get("time", m.get("timestamp", m.get("datetime")))
    if t is None:
        raise ValueError("bar missing time")
    vol = m.get("volume", m.get("tick_volume", m.get("real_volume", 0.0)))
    return Bar(
        time=_to_dt(t),
        open=float(m["open"]),
        high=float(m["high"]),
        low=float(m["low"]),
        close=float(m["close"]),
        volume=float(vol or 0.0),
    )


def normalize_bars(rows: Iterable[Mapping[str, Any] | Bar]) -> List[Bar]:
    out: List[Bar] = []
    for r in rows:
        if isinstance(r, Bar):
            out.append(r)
        else:
            out.append(bar_from_mapping(r))
    return sorted(out, key=lambda b: b.time)


def validate_bars(bars: Sequence[Bar], expected_interval_seconds: Optional[int] = None) -> DataQualityReport:
    report = DataQualityReport(ok=True, stats={"count": len(bars)})
    if not bars:
        report.add_issue("no bars")
        return report
    # ordering/duplicates
    times = [b.time for b in bars]
    if times != sorted(times):
        report.add_issue("bars not sorted by time")
    seen = set()
    dups = 0
    for t in times:
        if t in seen:
            dups += 1
        seen.add(t)
    if dups:
        report.add_issue(f"duplicate timestamps: {dups}")
    # OHLC sanity
    bad_ohlc = 0
    for b in bars:
        if b.high < max(b.open, b.close) or b.low > min(b.open, b.close) or b.high < b.low:
            bad_ohlc += 1
        if b.volume < 0:
            report.add_issue("negative volume")
            break
    if bad_ohlc:
        report.add_issue(f"invalid OHLC bars: {bad_ohlc}")
    # gaps (if interval known)
    if expected_interval_seconds and len(bars) > 1:
        gaps = 0
        tol = timedelta(seconds=max(1, expected_interval_seconds // 10))
        for i in range(1, len(bars)):
            delta = bars[i].time - bars[i - 1].time
            if delta > timedelta(seconds=expected_interval_seconds) + tol:
                gaps += 1
        if gaps:
            report.add_warning(f"gaps detected: {gaps}")
        report.stats["gaps"] = gaps
    report.stats["duplicates"] = dups
    return report


def build_daily_stats(daily_bars: Sequence[Bar], prev_or_volumes: Sequence[float], atr_period: int = 14, vol_period: int = 14) -> Tuple[Optional[DailyStats], DataQualityReport]:
    report = DataQualityReport(ok=True, stats={})
    a = atr(daily_bars, period=atr_period)
    av = average_volume(daily_bars, period=vol_period)
    if a is None:
        report.add_issue(f"atr{atr_period} unavailable (need >= {atr_period + 1} daily bars)")
    if av is None:
        report.add_issue(f"avg_volume{vol_period} unavailable (need >= {vol_period} daily bars)")
    if len(prev_or_volumes) < 14:
        report.add_warning(f"prev_or_volumes has {len(prev_or_volumes)} entries (<14)")
    if not report.ok:
        return None, report
    return DailyStats(atr14=float(a), avg_volume14=float(av), prev_or_volumes=list(prev_or_volumes)), report
