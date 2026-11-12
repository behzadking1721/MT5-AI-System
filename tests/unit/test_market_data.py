import unittest
from datetime import datetime, timedelta

from modules.market_data import bar_from_mapping, normalize_bars, validate_bars, build_daily_stats
from modules.strategy_lab import Bar


class TestMarketData(unittest.TestCase):
    def test_bar_from_mapping(self):
        b = bar_from_mapping({"time": "2024-01-02T09:30:00", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "tick_volume": 100})
        self.assertEqual(b.volume, 100.0)
        self.assertEqual(b.high, 2.0)

    def test_validate_detects_duplicates_and_bad_ohlc(self):
        t = datetime(2024, 1, 2, 9, 30)
        bars = [
            Bar(t, 1, 1.2, 0.9, 1.1, 10),
            Bar(t, 1, 1.2, 0.9, 1.1, 10),  # dup
            Bar(t + timedelta(minutes=1), 1, 0.5, 0.9, 1.1, 10),  # bad high < low/open/close
        ]
        rep = validate_bars(bars, expected_interval_seconds=60)
        self.assertFalse(rep.ok)
        joined = " ".join(rep.issues)
        self.assertIn("duplicate", joined)
        self.assertIn("invalid OHLC", joined)

    def test_validate_detects_gaps(self):
        t = datetime(2024, 1, 2, 9, 30)
        bars = [Bar(t, 1, 1, 1, 1, 1), Bar(t + timedelta(minutes=5), 1, 1, 1, 1, 1)]
        rep = validate_bars(bars, expected_interval_seconds=60)
        self.assertTrue(rep.ok)  # gaps are warnings
        self.assertTrue(any("gaps" in w for w in rep.warnings))

    def test_build_daily_stats(self):
        # 15 daily bars with simple range to get ATR and avg vol
        base = datetime(2024, 1, 1)
        daily = []
        price = 100.0
        for i in range(15):
            o = price
            h = price + 2
            l = price - 1
            c = price + 1
            daily.append(Bar(base + timedelta(days=i), o, h, l, c, 1000 + i))
            price = c
        stats, rep = build_daily_stats(daily, [500]*14)
        self.assertIsNotNone(stats)
        self.assertTrue(rep.ok)
        self.assertIsNotNone(stats.atr14)
        self.assertGreater(stats.avg_volume14, 0)

    def test_build_daily_stats_insufficient(self):
        base = datetime(2024, 1, 1)
        daily = [Bar(base + timedelta(days=i), 1, 2, 0.5, 1.5, 100) for i in range(5)]
        stats, rep = build_daily_stats(daily, [1]*14)
        self.assertIsNone(stats)
        self.assertFalse(rep.ok)


if __name__ == "__main__":
    unittest.main()
