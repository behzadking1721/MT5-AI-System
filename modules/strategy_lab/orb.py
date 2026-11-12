from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, time
from enum import Enum
from typing import Iterable, List, Optional, Sequence


class Direction(str, Enum):
    LONG = "long"
    SHORT = "short"
    NONE = "none"


@dataclass(frozen=True)
class Bar:
    """Generic OHLCV bar. `time` should be in exchange/server timezone context used consistently."""
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass(frozen=True)
class DailyStats:
    """Precomputed daily context needed by ORB filters/SL sizing."""
    atr14: float
    avg_volume14: float  # average daily volume over previous 14 days
    prev_or_volumes: Sequence[float]  # opening-range volumes for previous 14 sessions (same n-min window)


@dataclass(frozen=True)
class ORBConfig:
    opening_minutes: int = 5
    atr_stop_fraction: float = 0.10  # 10% of ATR
    min_price: float = 5.0
    min_avg_volume14: float = 1_000_000
    min_atr14: float = 0.50
    min_relative_volume: float = 1.0  # 100%
    session_close: time = time(16, 0)  # US equity regular close ET (caller must align)
    allow_doji: bool = False


@dataclass(frozen=True)
class ORBSignal:
    symbol: str
    direction: Direction
    opening_minutes: int
    or_high: float
    or_low: float
    or_open: float
    or_close: float
    or_volume: float
    relative_volume: Optional[float]
    entry_price: float  # breakout/stop trigger level
    stop_loss: float
    take_profit_time: str  # EoD by default
    risk_per_share: float
    atr14: float
    reasons: List[str]
    eligible: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d["direction"] = self.direction.value
        return d


def true_range(high: float, low: float, prev_close: float) -> float:
    return max(high - low, abs(high - prev_close), abs(low - prev_close))


def atr(daily_bars: Sequence[Bar], period: int = 14) -> Optional[float]:
    """Wilder-style ATR over `period` using prior close. Requires at least period+1 bars."""
    if len(daily_bars) < period + 1:
        return None
    trs: List[float] = []
    for i in range(1, len(daily_bars)):
        b = daily_bars[i]
        p = daily_bars[i - 1]
        trs.append(true_range(b.high, b.low, p.close))
    if len(trs) < period:
        return None
    # Wilder smoothing
    val = sum(trs[:period]) / period
    for tr in trs[period:]:
        val = (val * (period - 1) + tr) / period
    return val


def average_volume(daily_bars: Sequence[Bar], period: int = 14) -> Optional[float]:
    if len(daily_bars) < period:
        return None
    window = daily_bars[-period:]
    return sum(b.volume for b in window) / period


def opening_range_bars(intraday_bars: Sequence[Bar], session_open: datetime, opening_minutes: int) -> List[Bar]:
    end_ts = session_open.timestamp() + opening_minutes * 60
    # include bars whose start time is within [open, open+minutes)
    return [b for b in intraday_bars if session_open.timestamp() <= b.time.timestamp() < end_ts]


def compute_opening_range(bars: Sequence[Bar]) -> Optional[dict]:
    if not bars:
        return None
    o = bars[0].open
    c = bars[-1].close
    h = max(b.high for b in bars)
    l = min(b.low for b in bars)
    v = sum(b.volume for b in bars)
    return {"open": o, "close": c, "high": h, "low": l, "volume": v}


def relative_volume(current_or_volume: float, prev_or_volumes: Sequence[float]) -> Optional[float]:
    valid = [v for v in prev_or_volumes if v is not None]
    if len(valid) == 0:
        return None
    avg = sum(valid) / len(valid)
    if avg <= 0:
        return None
    return current_or_volume / avg


def analyze_orb(
    symbol: str,
    intraday_bars: Sequence[Bar],
    session_open: datetime,
    stats: DailyStats,
    config: ORBConfig | None = None,
) -> ORBSignal:
    """Pure ORB analysis: computes direction, entry, SL, EoD target context, and eligibility.
    Expects `intraday_bars` for the session (at least covering opening range) and consistent timezone.
    """
    cfg = config or ORBConfig()
    reasons: List[str] = []
    eligible = True

    or_bars = opening_range_bars(intraday_bars, session_open, cfg.opening_minutes)
    or_data = compute_opening_range(or_bars)
    if not or_data:
        return ORBSignal(symbol, Direction.NONE, cfg.opening_minutes, 0, 0, 0, 0, 0, None, 0, 0, cfg.session_close.isoformat(), 0, stats.atr14, ["missing opening range bars"], False)

    or_open, or_close, or_high, or_low, or_vol = (
        or_data["open"], or_data["close"], or_data["high"], or_data["low"], or_data["volume"],
    )
    rel_vol = relative_volume(or_vol, stats.prev_or_volumes)

    # direction by first n-min candle bias (as per provided strategy text)
    if or_close > or_open:
        direction = Direction.LONG
        entry = or_high
    elif or_close < or_open:
        direction = Direction.SHORT
        entry = or_low
    else:
        direction = Direction.NONE
        entry = 0.0
        reasons.append("doji opening range")
        if not cfg.allow_doji:
            eligible = False

    # filters
    if or_open <= cfg.min_price:
        eligible = False
        reasons.append("open price below minimum")
    if stats.avg_volume14 < cfg.min_avg_volume14:
        eligible = False
        reasons.append("avg 14d volume below minimum")
    if stats.atr14 < cfg.min_atr14:
        eligible = False
        reasons.append("atr14 below minimum")
    if rel_vol is None:
        eligible = False
        reasons.append("relative volume unavailable")
    elif rel_vol < cfg.min_relative_volume:
        eligible = False
        reasons.append("relative volume below minimum")

    risk_per_share = stats.atr14 * cfg.atr_stop_fraction
    if direction == Direction.LONG:
        stop_loss = round(entry - risk_per_share, 10) if entry else 0.0
    elif direction == Direction.SHORT:
        stop_loss = round(entry + risk_per_share, 10) if entry else 0.0
    else:
        stop_loss = 0.0

    if direction == Direction.NONE:
        eligible = False
    if risk_per_share <= 0:
        eligible = False
        reasons.append("invalid risk per share")

    return ORBSignal(
        symbol=symbol,
        direction=direction,
        opening_minutes=cfg.opening_minutes,
        or_high=or_high,
        or_low=or_low,
        or_open=or_open,
        or_close=or_close,
        or_volume=or_vol,
        relative_volume=rel_vol,
        entry_price=entry,
        stop_loss=stop_loss,
        take_profit_time=cfg.session_close.isoformat(),
        risk_per_share=round(risk_per_share, 10),
        atr14=stats.atr14,
        reasons=reasons,
        eligible=eligible,
    )
