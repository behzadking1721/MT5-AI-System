import unittest

from core.permission_gateway.gateway import PermissionContext
from modules.risk_manager.manager import RiskDecision
from modules.strategy_lab.orb import Direction, ORBSignal
from modules.trade_manager.gateway import ExecutionGateway, TradeProposal


def approved_risk(proposal_id):
    return RiskDecision(
        contract_version="1.0.0", decision_id="d1", proposal_id=proposal_id,
        approved=True, volume=0.5, risk_amount=50.0, risk_percent=0.5,
        limits_checked=["ok"], reasons=["ok"], timestamp="t",
    )


class TestExecutionGateway(unittest.TestCase):
    def setUp(self):
        self.gw = ExecutionGateway()
        self.proposal = TradeProposal("1.0.0", "p1", "EURUSD", "buy", "stop", 1.1, 1.099, None, None, "test")
        self.ctx_ok = PermissionContext(level="L4", trading_enabled=True, live_trading_enabled=False, human_confirmed=False)

    def test_rejects_unapproved_risk(self):
        risk = RiskDecision("1.0.0", "d2", "p1", False, 0.0, None, None, [], ["no"], "t")
        req, res, reason = self.gw.prepare_request(self.proposal, risk, "human-1", self.ctx_ok)
        self.assertIsNone(req)
        self.assertEqual(res.status, "rejected")
        self.assertEqual(reason, "risk_rejected")

    def test_rejects_mismatch_proposal(self):
        risk = approved_risk("other")
        req, res, reason = self.gw.prepare_request(self.proposal, risk, "human-1", self.ctx_ok)
        self.assertIsNone(req)
        self.assertEqual(reason, "risk_mismatch")

    def test_rejects_without_confirmation(self):
        risk = approved_risk("p1")
        req, res, reason = self.gw.prepare_request(self.proposal, risk, None, self.ctx_ok)
        self.assertEqual(reason, "no_confirmation")

    def test_rejects_when_trading_disabled(self):
        risk = approved_risk("p1")
        ctx = PermissionContext(trading_enabled=False)
        req, res, reason = self.gw.prepare_request(self.proposal, risk, "human-1", ctx)
        self.assertEqual(reason, "permission_denied")

    def test_prepare_and_simulate(self):
        risk = approved_risk("p1")
        req, res, reason = self.gw.prepare_request(self.proposal, risk, "human-1", self.ctx_ok, idempotency_key="k1")
        self.assertIsNone(res)
        self.assertEqual(reason, "prepared")
        self.assertEqual(req.risk_decision_id, "d1")
        sim = self.gw.simulate_execute(req, self.proposal)
        self.assertEqual(sim.status, "simulated")
        self.assertIsNone(sim.order_id)

    def test_rejects_duplicate_idempotency(self):
        risk = approved_risk("p1")
        self.gw.prepare_request(self.proposal, risk, "human-1", self.ctx_ok, idempotency_key="kdup")
        req, res, reason = self.gw.prepare_request(self.proposal, risk, "human-1", self.ctx_ok, idempotency_key="kdup")
        self.assertIsNone(req)
        self.assertEqual(reason, "duplicate")

    def test_from_orb_signal(self):
        sig = ORBSignal(
            symbol="TEST", direction=Direction.LONG, opening_minutes=5,
            or_high=101.2, or_low=99.9, or_open=100.0, or_close=101.1, or_volume=1, relative_volume=2.0,
            entry_price=101.2, stop_loss=100.95, take_profit_time="16:00:00", risk_per_share=0.25,
            atr14=2.5, reasons=[], eligible=True,
        )
        p = TradeProposal.from_orb_signal(sig)
        self.assertEqual(p.side, "buy")
        self.assertEqual(p.entry_price, 101.2)
        self.assertEqual(p.stop_loss, 100.95)
        self.assertEqual(p.order_type, "stop")


if __name__ == "__main__":
    unittest.main()
