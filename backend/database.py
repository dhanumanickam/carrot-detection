"""
SQLite Database Layer for Detection History and IoT Analytics
=============================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Stores every inspection event, classification result, confidence score,
assigned bin destination, and annotated image path. Provides statistical
aggregation for the web dashboard.
"""

import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DB_PATH = BACKEND_DIR / "carrot_sorting.db"
CAPTURES_DIR = BACKEND_DIR / "static" / "captures"


class Database:
    """Thread-safe SQLite database manager for detection logs and statistics."""

    def __init__(self, db_path=str(DB_PATH)):
        self.db_path = db_path
        CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        """Creates connection with Row factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initializes database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    class_id INTEGER NOT NULL,
                    class_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    decision TEXT NOT NULL,
                    target_bin TEXT NOT NULL,
                    image_path TEXT,
                    bbox TEXT,
                    sorting_status TEXT DEFAULT 'Completed'
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    component TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            conn.commit()

    def log_detection(self, class_id, class_name, confidence, decision, target_bin, image_path="", bbox=None, status="Completed"):
        """Inserts a new carrot detection and sorting event."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bbox_str = json.dumps(bbox) if bbox is not None else "[]"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO detections (
                    timestamp, class_id, class_name, confidence, decision, target_bin, image_path, bbox, sorting_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, class_id, class_name, float(confidence), decision, target_bin, image_path, bbox_str, status))
            conn.commit()
            return cursor.lastrowid

    def get_recent_detections(self, limit=20):
        """Retrieves most recent detections ordered by timestamp descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM detections
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_statistics(self):
        """Computes live KPIs and breakdown for web dashboard charts."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) AS total FROM detections")
            total = cursor.fetchone()["total"]

            # Class breakdown
            cursor.execute("""
                SELECT class_id, class_name, COUNT(*) AS count
                FROM detections
                GROUP BY class_id
            """)
            breakdown_rows = cursor.fetchall()

            counts = {
                "good": 0,
                "damaged": 0,
                "rotten": 0,
                "rejected": 0
            }

            for row in breakdown_rows:
                cid = row["class_id"]
                c_cnt = row["count"]
                if cid == 0:
                    counts["good"] = c_cnt
                elif cid == 1:
                    counts["damaged"] = c_cnt
                elif cid == 2:
                    counts["rotten"] = c_cnt
                else:
                    counts["rejected"] += c_cnt

            # Average confidence
            cursor.execute("SELECT AVG(confidence) AS avg_conf FROM detections WHERE class_id >= 0")
            avg_conf_row = cursor.fetchone()
            avg_conf = avg_conf_row["avg_conf"] if avg_conf_row and avg_conf_row["avg_conf"] is not None else 0.0

            # Sorting Efficiency: Carrots sorted successfully into 3 bins / total
            sorted_count = counts["good"] + counts["damaged"] + counts["rotten"]
            efficiency = (sorted_count / total * 100.0) if total > 0 else 100.0

            # Hourly trend for line chart (last 12 hours)
            cursor.execute("""
                SELECT strftime('%H:00', timestamp) AS hour, COUNT(*) AS hourly_total
                FROM detections
                GROUP BY hour
                ORDER BY hour DESC
                LIMIT 10
            """)
            timeline = [dict(r) for r in cursor.fetchall()]
            timeline.reverse()

            return {
                "total_inspected": total,
                "good_count": counts["good"],
                "damaged_count": counts["damaged"],
                "rotten_count": counts["rotten"],
                "rejected_count": counts["rejected"],
                "good_percent": round((counts["good"] / total * 100) if total > 0 else 0, 1),
                "damaged_percent": round((counts["damaged"] / total * 100) if total > 0 else 0, 1),
                "rotten_percent": round((counts["rotten"] / total * 100) if total > 0 else 0, 1),
                "avg_confidence": round(avg_conf * 100, 1),
                "sorting_efficiency": round(efficiency, 1),
                "timeline": timeline
            }

    def clear_history(self):
        """Clears all records for fresh test runs."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM detections")
            cursor.execute("DELETE FROM system_logs")
            conn.commit()


# Global Singleton instance
db = Database()
