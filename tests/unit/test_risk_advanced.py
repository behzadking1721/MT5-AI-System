import unittest

from modules.risk_manager.manager import RiskManager


class TestRiskAdvancedSizing(unittest.TestCase):
    def test_atr_sizing_long(self):
        vol, sl, reasons = RiskManager.calculate_volume_atr(
            entry=1.1000, atr=0.0010, atr_multiplier=1.5, equity=10000.0, risk_percent=0.5,
            tick_value=1.0, tick_size=0.00001, volume_step=0.01, volume_min=0.01, volume_max=100.0,
            side="buy",
        )
        # SL distance 0.0015 => 150 ticks, loss/lot 150, risk $50 => 0.33 lots floored
        self.assertAlmostEqual(sl, 1.0985, places=6)
        self.assertAlmostEqual(vol, 0.33, places=6)
        self.assertEqual(reasons, [])

    def test_atr_sizing_short(self):
        vol, sl, reasons = RiskManager.calculate_volume_atr(
            entry=1.1000, atr=0.0010, atr_multiplier=1.5, equity=10000.0, risk_percent=0.5,
            tick_value=1.0, tick_size=0.00001, volume_step=0.01, volume_min=0.01, volume_max=100.0,
            side="sell",
        )
        self.assertAlmostEqual(sl, 1.1015, places=6)
        self.assertGreater(vol, 0)

    def test_atr_invalid(self):
        vol, sl, reasons = RiskManager.calculate_volume_atr(
            entry=1.1, atr=0.0, atr_multiplier=1.5, equity=10000.0, risk_percent=0.5,
            tick_value=1.0, tick_size=0.00001,
        )
        self.assertEqual(vol, 0.0)
        self.assertIsNone(sl)
        self.assertTrue(reasons)

    def test_fractional_kelly(self):
        # win_rate 0.55, payoff 1.0 => kelly = 0.55 - 0.45 = 0.10; *0.25 cap => 0.025 => 2.5%
        pct, reasons = RiskManager.calculate_fractional_kelly_risk_percent(0.55, 1.0, fraction_cap=0.25, hard_max_pct=5.0)
        self.assertAlmostEqual(pct, 2.5, places=6)
        self.assertTrue(any("kelly=" in r for r in reasons))

    def test_fractional_kelly_hard_capped(self):
        pct, reasons = RiskManager.calculate_fractional_kelly_risk_percent(0.7, 2.0, fraction_cap=0.5, hard_max_pct=0.5)
        self.assertAlmostEqual(pct, 0.5, places=6)
        self.assertTrue(any("hard maximum" in r for r in reasons))

    def test_fractional_kelly_no_edge(self):
        pct, reasons = RiskManager.calculate_fractional_kelly_risk_percent(0.4, 1.0, fraction_cap=0.25)
        self.assertEqual(pct, 0.0)
        self.assertTrue(reasons)

    def test_fractional_kelly_invalid_inputs(self):
        pct, reasons = RiskManager.calculate_fractional_kelly_risk_percent(1.2, 1.0)
        self.assertEqual(pct, 0.0)
        self.assertTrue(reasons)


if __name__ == "__main__":
    unittest.main()
