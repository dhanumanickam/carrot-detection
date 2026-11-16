"""
End-to-End Integration Tests for Detection, Sorting, and Database Pipeline
==========================================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System
"""

import unittest
import numpy as np
import cv2
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from training.predict import CarrotPredictor
from sorting.decision_engine import DecisionEngine
from backend.database import db


class TestPipeline(unittest.TestCase):
    """Integration test suite verifying the complete automated sorting pipeline."""

    def setUp(self):
        self.predictor = CarrotPredictor(conf_threshold=0.30)
        self.engine = DecisionEngine(camera_to_diverter_distance_m=0.35, min_confidence=0.50)
        db.clear_history()

    def test_decision_engine_three_bins(self):
        """Verifies mapping of all 3 quality categories to the 3 physical bins."""
        belt_speed = 0.15 # m/s

        # 1. Good Carrot -> Bin 1
        res_good = {
            "detections": [{"bbox": [10, 10, 100, 100], "confidence": 0.95}],
            "primary_class": "Good_Carrot",
            "primary_class_id": 0,
            "confidence": 0.95
        }
        dec_good = self.engine.evaluate(res_good, belt_speed)
        self.assertEqual(dec_good["target_bin_id"], 1)
        self.assertEqual(dec_good["target_bin_name"], "Bin 1 (Good Carrots)")
        self.assertEqual(dec_good["decision"], "SORT_BIN_1")
        self.assertGreater(dec_good["travel_delay_s"], 0)

        # 2. Damaged Carrot -> Bin 2
        res_damaged = {
            "detections": [{"bbox": [10, 10, 100, 100], "confidence": 0.88}],
            "primary_class": "Damaged_Carrot",
            "primary_class_id": 1,
            "confidence": 0.88
        }
        dec_damaged = self.engine.evaluate(res_damaged, belt_speed)
        self.assertEqual(dec_damaged["target_bin_id"], 2)
        self.assertEqual(dec_damaged["target_bin_name"], "Bin 2 (Damaged Carrots)")
        self.assertEqual(dec_damaged["decision"], "SORT_BIN_2")

        # 3. Rotten Carrot -> Bin 3
        res_rotten = {
            "detections": [{"bbox": [10, 10, 100, 100], "confidence": 0.91}],
            "primary_class": "Rotten_Carrot",
            "primary_class_id": 2,
            "confidence": 0.91
        }
        dec_rotten = self.engine.evaluate(res_rotten, belt_speed)
        self.assertEqual(dec_rotten["target_bin_id"], 3)
        self.assertEqual(dec_rotten["target_bin_name"], "Bin 3 (Rotten Carrots)")
        self.assertEqual(dec_rotten["decision"], "SORT_BIN_3")

        # 4. Low Confidence / Uncertain -> Reject Tray
        res_low_conf = {
            "detections": [{"bbox": [10, 10, 100, 100], "confidence": 0.35}],
            "primary_class": "Good_Carrot",
            "primary_class_id": 0,
            "confidence": 0.35
        }
        dec_reject = self.engine.evaluate(res_low_conf, belt_speed)
        self.assertEqual(dec_reject["target_bin_id"], 0)
        self.assertEqual(dec_reject["target_bin_name"], "Reject / Manual Inspection")

    def test_database_logging_and_kpis(self):
        """Tests SQLite database writes and KPI aggregation."""
        # Log 1 Good, 1 Damaged, 1 Rotten
        db.log_detection(0, "Good_Carrot", 0.94, "SORT_BIN_1", "Bin 1 (Good Carrots)")
        db.log_detection(1, "Damaged_Carrot", 0.85, "SORT_BIN_2", "Bin 2 (Damaged Carrots)")
        db.log_detection(2, "Rotten_Carrot", 0.90, "SORT_BIN_3", "Bin 3 (Rotten Carrots)")

        stats = db.get_statistics()
        self.assertEqual(stats["total_inspected"], 3)
        self.assertEqual(stats["good_count"], 1)
        self.assertEqual(stats["damaged_count"], 1)
        self.assertEqual(stats["rotten_count"], 1)
        self.assertEqual(stats["sorting_efficiency"], 100.0)

        history = db.get_recent_detections(limit=5)
        self.assertEqual(len(history), 3)


if __name__ == "__main__":
    unittest.main()
