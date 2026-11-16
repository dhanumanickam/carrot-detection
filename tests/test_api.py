"""
Unit Tests for Flask REST API Endpoints
=======================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System
"""

import unittest
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import app
from backend.database import db


class TestAPI(unittest.TestCase):
    """Verifies all REST API routes and payloads."""

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_status_endpoint(self):
        """Tests GET /api/status."""
        res = self.app.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("conveyor", data["data"])
        self.assertIn("sorter", data["data"])
        self.assertIn("ir_sensor", data["data"])

    def test_stats_endpoint(self):
        """Tests GET /api/stats."""
        res = self.app.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("total_inspected", data["data"])
        self.assertIn("good_count", data["data"])

    def test_detections_endpoint(self):
        """Tests GET /api/detections."""
        res = self.app.get("/api/detections?limit=5")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIsInstance(data["data"], list)

    def test_conveyor_control_endpoint(self):
        """Tests POST /api/conveyor/control."""
        # Test start
        res = self.app.post("/api/conveyor/control",
                            data=json.dumps({"action": "start", "speed": 60}),
                            content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])

        # Test stop
        res_stop = self.app.post("/api/conveyor/control",
                                 data=json.dumps({"action": "stop"}),
                                 content_type="application/json")
        self.assertEqual(res_stop.status_code, 200)

    def test_servo_test_endpoint(self):
        """Tests POST /api/servo/test."""
        res = self.app.post("/api/servo/test",
                            data=json.dumps({"bin": 1}),
                            content_type="application/json")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["status"]["current_angle"], 30)

    def test_trigger_inspection_endpoint(self):
        """Tests POST /api/trigger."""
        res = self.app.post("/api/trigger")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data["success"])
        self.assertIn("primary_class", data["data"] if "data" in data else {})


if __name__ == "__main__":
    unittest.main()
