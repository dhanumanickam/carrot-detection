# Automated Carrot Quality Detection and Sorting System Using Deep Learning, Computer Vision and IoT

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![YOLO11](https://img.shields.io/badge/Ultralytics-YOLO11-00FFFF.svg)](https://docs.ultralytics.com/)
[![Flask](https://img.shields.io/badge/Backend-Flask-black.svg)](https://flask.palletsprojects.com/)
[![Raspberry Pi](https://img.shields.io/badge/Hardware-Raspberry%20Pi-C51A4A.svg)](https://www.raspberrypi.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An academic Master of Engineering (M.E.) technical project delivering a complete autonomous cyber-physical system for automated post-harvest carrot quality inspection, grading, and physical three-way sorting.

---

## 📌 Project Overview

This system automates the inspection and physical segregation of carrots moving along a conveyor belt into **three separate physical collection bins**, plus an automatic fail-safe reject route:
- 🟢 **Bin 1 (Good Carrots):** Premium grade, uniform shape, free from defects.
- 🟡 **Bin 2 (Damaged Carrots):** Fractured, cut, broken tips, or longitudinal cracks.
- 🔴 **Bin 3 (Rotten Carrots):** Microbial rot, black lesions (*Alternaria*), soft decay.
- ⚪ **Reject Chute:** Low-confidence (< 50%) or unrecognized foreign objects.

---

## 🛠️ Technology Stack

- **Deep Learning:** YOLO11 (Ultralytics), PyTorch, TorchVision
- **Computer Vision:** OpenCV (CLAHE illumination correction, ROI cropping, MJPEG video streaming)
- **Backend & Database:** Python Flask REST API, SQLite Embedded Database
- **Frontend Dashboard:** HTML5, CSS3 (Glassmorphism), JavaScript, Bootstrap 5, Chart.js
- **Embedded Hardware:** Raspberry Pi 4/5, USB Webcam, Optical IR Sensor, DC Geared Motor, L298N Motor Driver, SG90/MG996R 3-Way Servo Diverter

---

## 📂 Project Architecture & Directory Structure

```text
carrot_quality_detection/
│
├── dataset/                        # YOLO11 dataset structure
│   ├── data.yaml                   # Class names & paths configuration
│   ├── train/                      # Training split (70%)
│   ├── val/                        # Validation split (20%)
│   └── test/                       # Unseen evaluation split (10%)
│
├── models/                         # Trained neural network weights
│   ├── yolo11n.pt                  # Base YOLO11 model
│   └── best.pt                     # Best trained checkpoint weights
│
├── training/                       # AI development & evaluation pipeline
│   ├── generate_sample_dataset.py  # Synthetic dataset generator for pipeline verification
│   ├── split_dataset.py            # Stratified dataset splitter
│   ├── train.py                    # YOLO11 model training script
│   ├── validate.py                 # Academic validation script (Confusion matrix, mAP, F1)
│   ├── predict.py                  # Single-image / stream inference script
│   └── evaluate_metrics.py         # Academic metrics & LaTeX/Markdown thesis table generator
│
├── camera/                         # Computer vision & frame acquisition
│   ├── camera_stream.py            # Thread-safe USB / CSI camera & animated conveyor simulation
│   └── image_processor.py          # CLAHE contrast enhancement & letterboxing
│
├── hardware/                       # Embedded hardware abstraction layer
│   ├── gpio_controller.py          # Unified GPIO manager with seamless PC auto-mocking
│   ├── ir_sensor.py                # Optical IR break-beam sensor with debouncing
│   ├── conveyor_motor.py           # L298N DC geared motor controller with PWM velocity math
│   └── servo_sorter.py             # 3-Way physical servo diverter actuator
│
├── sorting/                        # Automation & decision engine
│   ├── decision_engine.py          # Maps predictions to physical bins & conveyor travel delay
│   └── sorting_manager.py          # Closed-loop workflow orchestrator
│
├── backend/                        # Flask backend & database
│   ├── app.py                      # REST API & MJPEG video server
│   ├── database.py                 # SQLite ORM for detection history & analytics
│   └── config.py                   # System configuration & GPIO pinouts
│
├── web_dashboard/                  # Web interface
│   ├── static/
│   │   ├── css/style.css           # Modern dark glassmorphic responsive UI
│   │   └── js/dashboard.js         # Real-time polling & Chart.js graph controllers
│   └── templates/
│       ├── index.html              # Real-time IoT monitoring & analytics dashboard
│       └── manual_control.html     # Hardware calibration & actuator testing workbench
│
├── tests/                          # Automated test suite
│   ├── test_hardware_mock.py       # Unit tests for GPIO, IR sensor, motor, and 3-way diverter
│   ├── test_pipeline.py            # Integration tests for inference, decision engine, and DB
│   └── test_api.py                 # REST API unit tests
│
├── docs/                           # Comprehensive engineering & academic documentation
│   ├── SYSTEM_ARCHITECTURE.md      # Mermaid diagrams, flowcharts, and mathematical formulas
│   ├── HARDWARE_WIRING_GUIDE.md    # Circuit schematic, RPi 40-pin GPIO pinout & BOM
│   ├── DATASET_GUIDE.md            # Image collection, Roboflow labeling & training tutorial
│   └── THESIS_PROJECT_REPORT.md    # Complete academic M.E. Project report / thesis documentation
│
├── run_system.py                   # Master entry point to launch the entire system
└── requirements.txt                # Python package dependencies
```

---

## 🚀 Quick Start Guide

### 1. Installation
Clone this repository and install dependencies:
```bash
cd carrot_quality_detection
pip install -r requirements.txt
```

### 2. Run the Complete System
Launch the automated system with a single command:
```bash
python run_system.py
```
- Open your browser and navigate to: **`http://localhost:5000`**
- If running on a PC without physical Raspberry Pi GPIO or conveyor hardware, the system **automatically enables Simulation Mode** featuring an animated conveyor video feed and virtual GPIO actuators.
- Click **"Simulate IR Trigger"** on the dashboard to test the real-time detection, sorting decision, and database logging cycle.

### 3. Run Automated Tests
Execute the unit and integration test suite:
```bash
python -m unittest discover tests
```
All 12 test cases covering hardware mocking, 3-way diverter angles, decision routing, database operations, and REST APIs will execute.

---

## 🧠 AI Training and Evaluation Pipeline

### Step 1: Generate Verification Dataset (Optional)
To test the pipeline before collecting physical images:
```bash
python training/generate_sample_dataset.py --samples 40
```

### Step 2: Split Your Dataset
Split custom annotated images into train (70%), val (20%), and test (10%):
```bash
python training/split_dataset.py --source /path/to/raw_images --output dataset/
```

### Step 3: Train YOLO11
Train the model on your dataset:
```bash
python training/train.py --epochs 50 --batch 16 --imgsz 640
```
Best model weights are automatically saved to `models/best.pt`.

### Step 4: Validate & Evaluate Metrics
Compute mAP@0.5, Precision, Recall, and Confusion Matrix:
```bash
python training/validate.py --model models/best.pt --split test
```

### Step 5: Run Inference on Single Image
```bash
python training/predict.py --source dataset/test/images/good_carrot_test_0001.jpg
```

---

## ⚡ Hardware Wiring & GPIO Mapping

| Raspberry Pi Pin | BCM GPIO | Component | Function |
| :---: | :---: | :--- | :--- |
| **Pin 11** | **GPIO 17** | IR Proximity Sensor | Digital Input (Active LOW on carrot detection) |
| **Pin 12** | **GPIO 18** | L298N Motor Driver (ENA) | PWM Speed Modulation |
| **Pin 13** | **GPIO 27** | L298N Motor Driver (IN1) | Motor Direction (Forward: HIGH) |
| **Pin 15** | **GPIO 22** | L298N Motor Driver (IN2) | Motor Direction (Reverse: LOW) |
| **Pin 32** | **GPIO 12** | 3-Way Servo Diverter | 50Hz PWM Actuation (Diverter Arm) |
| **Pin 6** | **GND** | Power Supply Common | Shared Ground Reference |

### Diverter Angular Calibration:
- **30° Position:** Diverts to **Bin 1 (Good Carrots)**
- **90° Position:** Diverts to **Bin 2 (Damaged Carrots)**
- **150° Position:** Diverts to **Bin 3 (Rotten Carrots)**
- **0° Position:** Resets to **Neutral / Reject Tray** (Fail-safe route)

---

## 🌐 REST API Reference

| Method | Endpoint | Description |
| :---: | :--- | :--- |
| `GET` | `/` | Web Monitoring & Analytics Dashboard |
| `GET` | `/manual` | Hardware Calibration Workbench |
| `GET` | `/video_feed` | Live MJPEG Camera Stream with Inspection HUD |
| `GET` | `/api/status` | Real-time telemetry (camera, conveyor, servo, sensor) |
| `GET` | `/api/stats` | Aggregated sorting KPIs and hourly throughput |
| `GET` | `/api/detections` | Paginated detection history records |
| `POST`| `/api/trigger` | Triggers immediate camera capture and sorting cycle |
| `POST`| `/api/conveyor/control`| Adjusts conveyor motor speed and state |
| `POST`| `/api/servo/test` | Drives servo diverter to specific bin angle for testing |
| `POST`| `/api/history/clear` | Clears inspection history for fresh batch |

---

## 🎓 Academic Citations & Thesis Deliverables

For complete details on mathematical modeling, system design, circuit schematics, and thesis tables, refer to:
- 📖 [System Architecture Document](docs/SYSTEM_ARCHITECTURE.md)
- 🔌 [Hardware Wiring & Electrical Guide](docs/HARDWARE_WIRING_GUIDE.md)
- 📊 [Dataset Collection & Training Guide](docs/DATASET_GUIDE.md)
- 🎓 [Full M.E. Technical Project Report](docs/THESIS_PROJECT_REPORT.md)
