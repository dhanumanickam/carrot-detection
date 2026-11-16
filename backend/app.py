"""
Flask Web Application & REST API Server
=======================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Provides:
- Web dashboard presentation (Live camera stream HUD, KPIs, charts, history)
- Hardware manual calibration & test workbench
- Real-time video streaming endpoint (/video_feed)
- Full REST API for IoT monitoring, conveyor speed control, and servo actuation
"""

import os
import sys
import time
import logging
from pathlib import Path
from flask import Flask, render_template, Response, jsonify, request, send_from_directory

# Project paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DASHBOARD_DIR = PROJECT_ROOT / "web_dashboard"

from backend.config import (
    MODEL_PATH, CAMERA_INDEX, SERVER_HOST, SERVER_PORT,
    DEBUG_MODE, CONVEYOR_SPEED_PERCENT
)
from backend.database import db, CAPTURES_DIR
from sorting.sorting_manager import SortingManager

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("Flask_Server")

# Create Flask Application
app = Flask(
    __name__,
    template_folder=str(DASHBOARD_DIR / "templates"),
    static_folder=str(DASHBOARD_DIR / "static")
)

# Instantiate central sorting system
model_file = str(MODEL_PATH) if MODEL_PATH.exists() else None
manager = SortingManager(camera_index=CAMERA_INDEX, model_path=model_file)


# ------------------------------------------------------------------------------
# Frontend Web Routes
# ------------------------------------------------------------------------------

@app.route("/")
def index():
    """Main Real-Time IoT Monitoring & Analytics Dashboard."""
    return render_template("index.html")


@app.route("/manual")
def manual_control():
    """Hardware Calibration & Manual Diagnostics Workbench."""
    return render_template("manual_control.html")


@app.route("/static/captures/<path:filename>")
def serve_capture(filename):
    """Serves annotated carrot inspection images."""
    return send_from_directory(str(CAPTURES_DIR), filename)


@app.route("/video_feed")
def video_feed():
    """MJPEG Live Camera Stream with Inspection HUD."""
    return Response(
        manager.camera.generate_mjpeg_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


# ------------------------------------------------------------------------------
# REST API Endpoints
# ------------------------------------------------------------------------------

@app.route("/api/status", methods=["GET"])
def get_system_status():
    """Returns real-time telemetry from camera, conveyor, sorter, and IR sensor."""
    telemetry = manager.get_system_telemetry()
    return jsonify({"success": True, "data": telemetry})


@app.route("/api/stats", methods=["GET"])
def get_statistics():
    """Returns aggregated classification counts, percentages, and time-series data."""
    stats = db.get_statistics()
    return jsonify({"success": True, "data": stats})


@app.route("/api/detections", methods=["GET"])
def get_detections():
    """Returns recent inspection logs from database."""
    limit = request.args.get("limit", default=20, type=int)
    records = db.get_recent_detections(limit=limit)
    return jsonify({"success": True, "count": len(records), "data": records})


@app.route("/api/trigger", methods=["POST"])
def trigger_inspection():
    """
    Manually triggers an inspection cycle (simulates IR sensor event or manual test).
    """
    result = manager.trigger_manual_inspection()
    if result is not None:
        return jsonify({"success": True, "message": "Inspection executed successfully.", "data": result})
    else:
        return jsonify({"success": False, "message": "Failed to capture or process frame."}), 500


@app.route("/api/conveyor/control", methods=["POST"])
def control_conveyor():
    """Controls conveyor motor: action='start'|'stop'|'reverse', speed=0..100."""
    data = request.get_json() or {}
    action = data.get("action", "start").lower()
    speed = data.get("speed", None)

    if action == "start":
        manager.conveyor.start(speed_percent=speed)
    elif action == "stop":
        manager.conveyor.stop()
    elif action == "reverse":
        manager.conveyor.reverse(speed_percent=speed)
    elif action == "set_speed" and speed is not None:
        manager.conveyor.set_speed(speed)
    else:
        return jsonify({"success": False, "message": f"Unknown action: {action}"}), 400

    return jsonify({
        "success": True,
        "message": f"Conveyor action '{action}' executed.",
        "status": manager.conveyor.get_status()
    })


@app.route("/api/servo/test", methods=["POST"])
def test_servo():
    """Drives sorting servo to specified bin angle for physical calibration."""
    data = request.get_json() or {}
    bin_num = data.get("bin", 0)
    manager.sorter.test_bin_position(bin_num)
    return jsonify({
        "success": True,
        "message": f"Servo moved to position for Bin {bin_num}",
        "status": manager.sorter.get_status()
    })


@app.route("/api/system/start", methods=["POST"])
def start_system():
    """Starts the full automated detection and sorting workflow."""
    manager.start_system()
    return jsonify({"success": True, "message": "Automated sorting system started."})


@app.route("/api/system/stop", methods=["POST"])
def stop_system():
    """Stops the automated sorting workflow."""
    manager.stop_system()
    return jsonify({"success": True, "message": "Automated sorting system stopped."})


@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    """Clears detection logs and resets counters."""
    db.clear_history()
    return jsonify({"success": True, "message": "Inspection database records cleared."})


# ------------------------------------------------------------------------------
# Main Application Launcher
# ------------------------------------------------------------------------------

def start_server(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE):
    """Starts Flask web server and begins camera streaming."""
    logger.info(f"Starting Web Dashboard at http://{host}:{port}")
    manager.start_system()
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)


if __name__ == "__main__":
    start_server()
