"""
System Configuration Parameters
===============================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Model & Inference Settings
MODEL_PATH = BASE_DIR / "models" / "best.pt"
FALLBACK_MODEL = "yolo11n.pt"
CONFIDENCE_THRESHOLD = 0.45
IOU_THRESHOLD = 0.45
IMAGE_SIZE = 640

# Camera Settings
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
FORCE_SIMULATION = False  # Set True to force animated conveyor simulation

# Hardware GPIO Pin Mappings (BCM Mode)
PIN_IR_SENSOR = 17       # Optical IR obstacle detection
PIN_MOTOR_ENA = 18       # L298N PWM speed enable
PIN_MOTOR_IN1 = 27       # L298N Direction 1
PIN_MOTOR_IN2 = 22       # L298N Direction 2
PIN_SERVO_SORTER = 12    # 3-Way Diverter Servo (PWM GPIO 12)
PIN_SERVO_SECONDARY = 13 # Optional dual-servo gate (PWM GPIO 13)

# Mechanical & Timing Calibration
CONVEYOR_SPEED_PERCENT = 70.0
MAX_CONVEYOR_VELOCITY_MPS = 0.20 # 20 cm/s
CAMERA_TO_SORTER_DISTANCE_M = 0.35 # 35 cm distance
SERVO_HOLD_TIME_S = 1.2

# Flask Web Server
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
DEBUG_MODE = False
