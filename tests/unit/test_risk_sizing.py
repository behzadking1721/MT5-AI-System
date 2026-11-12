import unittest

from modules.risk_manager.manager import RiskInput, RiskManager


class TestRiskSizing(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager()

    def test_fixed_monetary_sizing(self):
        # distance 0.0010, tick_size 0.00001 => 100 ticks, tick_value $1 => $100/lot, risk $50 => 0.5 lot
        vol, reasons = RiskManager.calculate_volume_fixed_monetary(
            entry=1.1000, sl=1.0990, risk_amount=50.0,
            tick_value=1.0, tick_size=0.00001, volume_step=0.01, volume_min=0.01, volume_max=100.0,
        )
        self.assertAlmostEqual(vol, 0.5, places=6)
        self.assertEqual(reasons, [])

    def test_fixed_fractional_via_evaluate(self):
        d = self.rm.evaluate(RiskInput(
            proposal_id="p3", symbol="EURUSD", side="buy", entry_price=1.1000, stop_loss=1.0990,
            account_equity=10000.0, risk_percent=1.0,
            tick_value=1.0, tick_size=0.00001, volume_step=0.01, volume_min=0.01, volume_max=100.0,
        ))
        self.assertTrue(d.approved)
        self.assertAlmostEqual(d.volume, 1.0, places=6)  # $100 risk => 1.0 lot

    def test_rejects_below_min_volume(self):
        vol, reasons = RiskManager.calculate_volume_fixed_monetary(
            entry=1.1000, sl=1.0900, risk_amount=1.0,  # huge stop, tiny risk
            tick_value=1.0, tick_size=0.00001, volume_step=0.01, volume_min=0.01, volume_max=100.0,
        )
        self.assertEqual(vol, 0.0)
        self.assertTrue(reasons)


if __name__ == "__main__":
    unittest.main()
