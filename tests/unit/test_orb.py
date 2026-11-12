import unittest
from datetime import datetime, timedelta

from modules.strategy_lab.orb import Bar, DailyStats, ORBConfig, Direction, analyze_orb, relative_volume


def make_or_bars(open_p, close_p, high_p, low_p, vol, start=None, n=5):
    start = start or datetime(2024, 1, 2, 9, 30)
    bars = []
    # split into 1-min bars roughly
    for i in range(n):
        o = open_p if i == 0 else (open_p + close_p) / 2
        c = close_p if i == n - 1 else (open_p + close_p) / 2
        h = high_p if i == 0 else max(o, c)
        l = low_p if i == 0 else min(o, c)
        bars.append(Bar(time=start + timedelta(minutes=i), open=o, high=h, low=l, close=c, volume=vol / n))
    # ensure extremes present
    bars[0] = Bar(time=bars[0].time, open=open_p, high=high_p, low=low_p, close=bars[0].close, volume=bars[0].volume)
    bars[-1] = Bar(time=bars[-1].time, open=bars[-1].open, high=max(bars[-1].high, close_p), low=min(bars[-1].low, close_p), close=close_p, volume=bars[-1].volume)
    return bars


class TestORB(unittest.TestCase):
    def test_bullish_long_signal(self):
        bars = make_or_bars(100.0, 101.0, 101.5, 99.8, 500000)
        stats = DailyStats(atr14=5.0, avg_volume14=2_000_000, prev_or_volumes=[250000]*14)
        sig = analyze_orb("TEST", bars, bars[0].time, stats, ORBConfig())
        self.assertEqual(sig.direction, Direction.LONG)
        self.assertEqual(sig.entry_price, 101.5)
        self.assertAlmostEqual(sig.risk_per_share, 0.5)
        self.assertAlmostEqual(sig.stop_loss, 101.0)
        self.assertTrue(sig.eligible)
        self.assertAlmostEqual(sig.relative_volume, 2.0)

    def test_bearish_short_signal(self):
        bars = make_or_bars(100.0, 99.0, 100.2, 98.5, 500000)
        stats = DailyStats(atr14=5.0, avg_volume14=2_000_000, prev_or_volumes=[250000]*14)
        sig = analyze_orb("TEST", bars, bars[0].time, stats, ORBConfig())
        self.assertEqual(sig.direction, Direction.SHORT)
        self.assertEqual(sig.entry_price, 98.5)
        self.assertAlmostEqual(sig.stop_loss, 99.0)
        self.assertTrue(sig.eligible)

    def test_doji_ineligible(self):
        bars = make_or_bars(100.0, 100.0, 100.5, 99.5, 500000)
        stats = DailyStats(atr14=5.0, avg_volume14=2_000_000, prev_or_volumes=[250000]*14)
        sig = analyze_orb("TEST", bars, bars[0].time, stats, ORBConfig())
        self.assertEqual(sig.direction, Direction.NONE)
        self.assertFalse(sig.eligible)

    def test_relative_volume_filter(self):
        bars = make_or_bars(100.0, 101.0, 101.5, 99.8, 100000)
        stats = DailyStats(atr14=5.0, avg_volume14=2_000_000, prev_or_volumes=[250000]*14)  # RV 0.4
        sig = analyze_orb("TEST", bars, bars[0].time, stats, ORBConfig())
        self.assertFalse(sig.eligible)
        self.assertTrue(any("relative volume" in r for r in sig.reasons))

    def test_universe_filters(self):
        bars = make_or_bars(4.0, 4.1, 4.2, 3.9, 500000)
        stats = DailyStats(atr14=0.2, avg_volume14=500_000, prev_or_volumes=[250000]*14)
        sig = analyze_orb("PENNY", bars, bars[0].time, stats, ORBConfig())
        self.assertFalse(sig.eligible)
        joined = " ".join(sig.reasons)
        self.assertIn("open price below minimum", joined)
        self.assertIn("avg 14d volume below minimum", joined)
        self.assertIn("atr14 below minimum", joined)

    def test_relative_volume_helper(self):
        self.assertAlmostEqual(relative_volume(200, [100]*14), 2.0)
        self.assertIsNone(relative_volume(200, []))
        self.assertIsNone(relative_volume(200, [0]*14))


if __name__ == "__main__":
    unittest.main()
