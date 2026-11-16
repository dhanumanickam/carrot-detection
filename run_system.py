#!/usr/bin/env python3
"""
Master Entry Point: Automated Carrot Quality Detection and Sorting System
=========================================================================
Academic M.E. Final-Year Project
Author: M.E. Project Team
Tech Stack: Python, YOLO11, OpenCV, PyTorch, Flask, SQLite, Raspberry Pi GPIO

Usage:
    python run_system.py
    python run_system.py --port 5000 --camera 0
    python run_system.py --sim
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import SERVER_HOST, SERVER_PORT, MODEL_PATH
from backend.app import app, manager


def print_banner():
    banner = r"""
  ======================================================================
     AUTOMATED CARROT QUALITY DETECTION & SORTING SYSTEM
     Master of Engineering (M.E.) Final-Year Technical Project
  ======================================================================
     [AI & CV]   YOLO11 (Ultralytics) + OpenCV + PyTorch
     [Hardware]  Raspberry Pi 40-Pin GPIO + L298N + Servos + IR Sensor
     [Sorting]   3 Physical Bins (Good / Damaged / Rotten) + Reject Chute
     [IoT Web]   Flask REST API + SQLite Analytics Dashboard + MJPEG Stream
  ======================================================================
    """
    print(banner)


def main():
    parser = argparse.ArgumentParser(description="Launch Carrot Quality Detection & Sorting System")
    parser.add_argument("--host", type=str, default=SERVER_HOST, help="Web server host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=SERVER_PORT, help="Web server port (default: 5000)")
    parser.add_argument("--sim", action="store_true", help="Force synthetic conveyor simulation mode")
    parser.add_argument("--model", type=str, default=str(MODEL_PATH), help="Path to YOLO11 weights file")
    args = parser.parse_args()

    print_banner()

    # Diagnostics
    print("[Diagnostics Check]")
    if manager.camera.is_simulation or args.sim:
        print("  * Camera Mode     : Animated Conveyor Simulator (PC Test Mode)")
    else:
        print(f"  * Camera Mode     : Physical Video Device {manager.camera.camera_index}")

    print(f"  * Hardware GPIO   : {'Physical Raspberry Pi' if manager.ir_sensor.pin and hasattr(manager, 'is_rpi') else 'Hardware Mock/Simulation Layer'}")
    print(f"  * Model Weights   : {args.model if os.path.exists(args.model) else 'YOLO11 Base / Heuristic Fallback'}")
    print(f"  * Sorting Bins    : 3 Dedicated Destinations (Bin 1: Good, Bin 2: Damaged, Bin 3: Rotten)")
    print(f"  * Web Dashboard   : http://localhost:{args.port} (or http://{args.host}:{args.port})")
    print("=" * 70)
    print("Starting automated conveyor loop and web monitoring server...")
    print("Press Ctrl+C to safely shut down hardware and exit.\n")

    manager.start_system()

    try:
        app.run(host=args.host, port=args.port, debug=False, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[Shutdown] Caught termination signal. Gracefully stopping actuators...")
        manager.stop_system()
        print("[Shutdown] System halted safely.")


if __name__ == "__main__":
    main()
