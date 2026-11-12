import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from shared.common.audit import make_audit_event
from core.workflow_state.store import WorkflowStateStore


class TestWorkflowAndAudit(unittest.TestCase):
    def test_audit_event_shape(self):
        e = make_audit_event(actor="test", action="x", result="ok", input_summary={"a": 1})
        self.assertEqual(e["contract_version"], "1.0.0")
        self.assertEqual(e["actor"], "test")
        self.assertIn("event_id", e)
        self.assertIn("timestamp", e)

    def test_workflow_store(self):
        with TemporaryDirectory() as d:
            p = Path(d) / "wf.json"
            s = WorkflowStateStore(p)
            rec = s.create("orb_analysis", {"symbol": "X"})
            self.assertEqual(rec.status, "created")
            s.update(rec.workflow_id, "done", event={"k": 1})
            self.assertTrue(p.exists())
            data = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual(data[rec.workflow_id]["status"], "done")
            self.assertEqual(len(data[rec.workflow_id]["events"]), 1)


if __name__ == "__main__":
    unittest.main()
