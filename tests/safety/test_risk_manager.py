import unittest

from modules.risk_manager.manager import RiskInput, RiskManager


class TestRiskManagerSafety(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager()

    def test_rejects_missing_stop_loss(self):
        d = self.rm.evaluate(RiskInput(proposal_id="p1", symbol="EURUSD", side="buy", entry_price=1.1, stop_loss=None))
        self.assertFalse(d.approved)
        self.assertEqual(d.volume, 0.0)
        self.assertIn("missing stop loss", d.reasons)

    def test_with_stop_loss_is_not_final_sizing(self):
        d = self.rm.evaluate(RiskInput(proposal_id="p2", symbol="EURUSD", side="buy", entry_price=1.1, stop_loss=1.09))
        self.assertTrue(d.approved)
        self.assertEqual(d.volume, 0.0)  # scaffold: no sizing yet


if __name__ == "__main__":
    unittest.main()
