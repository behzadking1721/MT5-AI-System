import unittest
from datetime import datetime, timedelta

from modules.risk_manager.manager import RiskInput, RiskLimits
from modules.strategy_lab.pipeline import analyze_orb_from_payload


def make_intraday(start):
    # bullish OR, 5x1m
    prices = [(100.00,100.80,99.90,100.20),(100.20,100.60,100.10,100.40),(100.40,100.90,100.30,100.70),(100.70,101.00,100.50,100.80),(100.80,101.20,100.60,101.10)]
    vols = [120000,90000,110000,95000,85000]
    rows = []
    for i,(o,h,l,c) in enumerate(prices):
        rows.append({"time": (start + timedelta(minutes=i)).isoformat(), "open": o, "high": h, "low": l, "close": c, "tick_volume": vols[i]})
    return rows


def make_daily(base, n=15):
    rows = []
    price = 100.0
    for i in range(n):
        o = price; h = price + 2; l = price - 1; c = price + 1
        rows.append({"time": (base + timedelta(days=i)).isoformat(), "open": o, "high": h, "low": l, "close": c, "volume": 2000000})
        price = c
    return rows


class TestStrategyPipeline(unittest.TestCase):
    def test_analyze_from_payload_with_risk(self):
        start = datetime(2024, 1, 2, 9, 30)
        res = analyze_orb_from_payload(
            symbol="TEST",
            intraday_rows=make_intraday(start),
            daily_rows=make_daily(datetime(2023, 12, 1)),
            prev_or_volumes=[250000]*14,
            session_open=start,
            risk_input=RiskInput(
                proposal_id="p1", symbol="TEST", side="buy", entry_price=None, stop_loss=None,
                account_equity=10000.0, risk_percent=0.5,
                tick_value=1.0, tick_size=0.01, volume_step=0.01, volume_min=0.01, volume_max=100.0,
            ),
            risk_limits=RiskLimits(max_risk_per_trade_pct=0.5),
        )
        self.assertIsNone(res.error)
        self.assertTrue(res.data_report["ok"])
        self.assertTrue(res.signal.eligible)
        self.assertEqual(res.signal.direction.value, "long")
        self.assertIsNotNone(res.risk_decision)
        self.assertTrue(res.risk_decision.approved)
        self.assertGreater(res.risk_decision.volume, 0)

    def test_invalid_data(self):
        start = datetime(2024, 1, 2, 9, 30)
        # missing high -> normalize error
        bad = [{"time": start.isoformat(), "open": 1, "low": 1, "close": 1}]
        res = analyze_orb_from_payload("X", bad, make_daily(datetime(2023,12,1)), [1]*14, start)
        self.assertIsNotNone(res.error)
        self.assertIsNone(res.signal)


if __name__ == "__main__":
    unittest.main()
