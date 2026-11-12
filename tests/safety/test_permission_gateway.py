import unittest

from core.permission_gateway.gateway import PermissionContext, PermissionGateway


class TestPermissionGateway(unittest.TestCase):
    def setUp(self):
        self.gw = PermissionGateway()

    def test_trade_denied_by_default(self):
        d = self.gw.allow("trade", PermissionContext())
        self.assertFalse(d.allowed)

    def test_trade_requires_confirmation_and_not_live(self):
        d = self.gw.allow("trade", PermissionContext(trading_enabled=True, human_confirmed=True, live_trading_enabled=False))
        self.assertTrue(d.allowed)
        d2 = self.gw.allow("trade", PermissionContext(trading_enabled=True, human_confirmed=True, live_trading_enabled=True))
        self.assertFalse(d2.allowed)

    def test_write_denied_at_read_only(self):
        d = self.gw.allow("write", PermissionContext(level="L1_read_only"))
        self.assertFalse(d.allowed)


if __name__ == "__main__":
    unittest.main()
