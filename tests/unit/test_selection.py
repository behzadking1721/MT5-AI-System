import unittest
from datetime import datetime, timedelta

from modules.strategy_lab import Bar, DailyStats, ORBConfig, analyze_orb, select_stocks_in_play


def bars(open_p, close_p, high_p, low_p, vol, start):
    out = []
    for i in range(5):
        o = open_p if i == 0 else (open_p + close_p) / 2
        c = close_p if i == 4 else (open_p + close_p) / 2
        out.append(Bar(start + timedelta(minutes=i), o, high_p if i == 0 else max(o, c), low_p if i == 0 else min(o, c), c, vol / 5))
    out[0] = Bar(out[0].time, open_p, high_p, low_p, out[0].close, out[0].volume)
    out[-1] = Bar(out[-1].time, out[-1].open, max(out[-1].high, close_p), min(out[-1].low, close_p), close_p, out[-1].volume)
    return out


class TestSelection(unittest.TestCase):
    def test_rank_and_filter(self):
        start = datetime(2024, 1, 2, 9, 30)
        cfg = ORBConfig()
        # A: rv 3.0 eligible, B: rv 1.5 eligible, C: rv 0.5 ineligible by rv, D: doji ineligible
        sA = analyze_orb("A", bars(100, 101, 101.5, 99.8, 750000, start), start, DailyStats(5, 2_000_000, [250000]*14), cfg)
        sB = analyze_orb("B", bars(50, 51, 51.5, 49.8, 375000, start), start, DailyStats(2, 2_000_000, [250000]*14), cfg)
        sC = analyze_orb("C", bars(100, 101, 101.5, 99.8, 125000, start), start, DailyStats(5, 2_000_000, [250000]*14), cfg)
        sD = analyze_orb("D", bars(100, 100, 100.5, 99.5, 750000, start), start, DailyStats(5, 2_000_000, [250000]*14), cfg)
        top = select_stocks_in_play([sC, sB, sD, sA], top_n=20, min_relative_volume=1.0)
        self.assertEqual([s.symbol for s in top], ["A", "B"])
        self.assertAlmostEqual(top[0].relative_volume, 3.0)
        self.assertAlmostEqual(top[1].relative_volume, 1.5)

    def test_top_n(self):
        start = datetime(2024, 1, 2, 9, 30)
        cfg = ORBConfig()
        sigs = []
        for i, sym in enumerate(["X", "Y", "Z"]):
            vol = (i + 2) * 250000  # rv 2,3,4
            sigs.append(analyze_orb(sym, bars(100, 101, 101.5, 99.8, vol, start), start, DailyStats(5, 2_000_000, [250000]*14), cfg))
        top = select_stocks_in_play(sigs, top_n=2)
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0].symbol, "Z")
        self.assertEqual(top[1].symbol, "Y")


if __name__ == "__main__":
    unittest.main()
