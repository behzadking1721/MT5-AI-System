import unittest

from modules.risk_manager.manager import RiskInput, RiskLimits, RiskManager


class TestRiskLimits(unittest.TestCase):
    def setUp(self):
        self.rm = RiskManager()

    def base(self, **kw):
        args = dict(proposal_id="p", symbol="EURUSD", side="buy", entry_price=1.1, stop_loss=1.099, account_equity=10000.0, risk_percent=0.5,
                    tick_value=1.0, tick_size=0.00001, volume_step=0.01, volume_min=0.01, volume_max=100.0)
        args.update(kw)
        return RiskInput(**args)

    def test_rejects_risk_over_trade_limit(self):
        d = self.rm.evaluate(self.base(risk_percent=2.0), RiskLimits(max_risk_per_trade_pct=0.5))
        self.assertFalse(d.approved)
        self.assertTrue(any("exceeds max" in r for r in d.reasons))

    def test_rejects_daily_loss_breach(self):
        d = self.rm.evaluate(self.base(daily_loss_pct=2.0), RiskLimits(max_daily_loss_pct=2.0))
        self.assertFalse(d.approved)

    def test_rejects_drawdown_breach(self):
        d = self.rm.evaluate(self.base(total_drawdown_pct=10.5), RiskLimits(max_total_drawdown_pct=10.0))
        self.assertFalse(d.approved)

    def test_rejects_max_open_positions(self):
        d = self.rm.evaluate(self.base(open_positions=3), RiskLimits(max_open_positions=3))
        self.assertFalse(d.approved)

    def test_rejects_consecutive_losses_circuit_breaker(self):
        d = self.rm.evaluate(self.base(consecutive_losses=3), RiskLimits(max_consecutive_losses=3))
        self.assertFalse(d.approved)

    def test_approves_within_limits(self):
        d = self.rm.evaluate(self.base(), RiskLimits(max_risk_per_trade_pct=0.5))
        self.assertTrue(d.approved)
        self.assertGreater(d.volume, 0.0)


if __name__ == "__main__":
    unittest.main()
