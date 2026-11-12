import unittest

from integrations.inventory import load_inventory
from shared.common.types import Capability


class TestInventory(unittest.TestCase):
    def test_load_inventory(self):
        data = {
            "servers": {
                "mt5_terminal": {
                    "endpoint": "http://127.0.0.1:22346/mcp",
                    "tools": [
                        {"name": "get_symbol_info", "purpose": "read symbol", "read": True, "write": False, "trade": False},
                        {"name": "place_order", "purpose": "trade", "read": False, "write": False, "trade": True},
                    ],
                }
            }
        }
        inv = load_inventory(data)
        self.assertIn("mt5_terminal", inv)
        tools = inv["mt5_terminal"]
        self.assertEqual(tools[0].capabilities, (Capability.READ,))
        self.assertIn(Capability.TRADE, tools[1].capabilities)
        self.assertTrue(tools[1].requires_confirmation)

    def test_shorthand(self):
        inv = load_inventory({"mt5_marketdata": [{"name": "bars", "purpose": "x", "read": True}]})
        self.assertEqual(len(inv["mt5_marketdata"]), 1)


if __name__ == "__main__":
    unittest.main()
