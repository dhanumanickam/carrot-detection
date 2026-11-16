"""
Central Sorting System Coordinator (Workflow Manager)
=====================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Executes the closed-loop automation workflow:
    1. IR Sensor detects carrot arrival on conveyor.
    2. Raspberry Pi captures camera snapshot of the inspection area.
    3. Image preprocessor normalizes lighting and crops conveyor ROI.
    4. YOLO11 deep learning engine infers carrot quality class & confidence.
    5. Decision engine determines physical sorting destination & travel delay.
    6. Conveyor motor continues transport; Servo sorter diverts into Bin 1, 2, or 3.
    7. Detection metadata and annotated image are committed to SQLite database.
    8. Web dashboard streams real-time updates and logs.
"""

import time
import os
import threading
import logging
import cv2
from pathlib import Path

from camera.camera_stream import CameraStream
from camera.image_processor import ImageProcessor
from training.predict import CarrotPredictor
from hardware.gpio_controller import gpio_controller
from hardware.ir_sensor import IRSensor
from hardware.conveyor_motor import ConveyorMotor
from hardware.servo_sorter import Servo3WaySorter
from sorting.decision_engine import DecisionEngine
from backend.database import db, CAPTURES_DIR

logger = logging.getLogger("Sorting_Manager")


class SortingManager:
    """End-to-End Orchestrator for the Automated Sorting Pipeline."""

    def __init__(self, camera_index=0, model_path=None):
        logger.info("Initializing Automated Carrot Quality Detection & Sorting System...")

        # 1. Camera & Vision Processing
        self.camera = CameraStream(camera_index=camera_index)
        self.processor = ImageProcessor()
        
        # 2. Deep Learning Inference
        self.predictor = CarrotPredictor(model_path=model_path if model_path else "")

        # 3. Hardware Actuators & Sensors
        self.ir_sensor = IRSensor(pin=17, active_low=True, debounce_seconds=1.2)
        self.conveyor = ConveyorMotor(ena_pin=18, in1_pin=27, in2_pin=22)
        self.sorter = Servo3WaySorter(servo_pin=12, hold_time_seconds=1.2)

        # 4. Decision Engine
        self.decision_engine = DecisionEngine(camera_to_diverter_distance_m=0.35, min_confidence=0.50)

        # State tracking
        self.is_system_active = False
        self.last_detection = None
        self.lock = threading.Lock()

        # Connect IR sensor interrupt callback
        self.ir_sensor.register_callback(self._on_ir_trigger)

    def start_system(self):
        """Starts video streaming, conveyor belt, and automation loop."""
        if self.is_system_active:
            return
        
        logger.info("Starting Automated Carrot Sorting System...")
        self.camera.start()
        self.conveyor.start(speed_percent=70.0) # Start conveyor at optimal sorting speed
        self.is_system_active = True
        logger.info("System is ACTIVE. Ready to inspect incoming carrots.")

    def stop_system(self):
        """Stops conveyor, camera, and puts actuators into safety state."""
        logger.info("Stopping sorting system...")
        self.is_system_active = False
        self.conveyor.stop()
        self.sorter.set_angle(self.sorter.ANGLE_REJECT_NEUTRAL)
        logger.info("System halted.")

    def _on_ir_trigger(self):
        """Callback invoked when physical or simulated IR sensor detects a carrot."""
        if not self.is_system_active:
            logger.debug("IR trigger received but system is inactive. Ignoring.")
            return

        logger.info(">>> Carrot detected on conveyor! Initiating inspection cycle...")
        # Run inspection in separate thread to prevent blocking the IR interrupt
        threading.Thread(target=self.process_inspection_cycle, daemon=True).start()

    def process_inspection_cycle(self):
        """Executes full capture -> prediction -> sorting -> database pipeline."""
        with self.lock:
            # 1. Acquire inspection frame
            raw_frame = self.camera.read_frame()
            if raw_frame is None or raw_frame.size == 0:
                logger.error("Failed to capture frame from camera stream.")
                return None

            # 2. Lighting enhancement & preprocessing
            processed_frame = self.processor.enhance_lighting(raw_frame)

            # 3. Deep Learning Prediction (YOLO11)
            prediction = self.predictor.predict_image(processed_frame)

            # 4. Sorting Decision and Delay Calculation
            belt_velocity = self.conveyor.get_velocity_mps()
            decision = self.decision_engine.evaluate(prediction, belt_velocity)

            logger.info(
                f"[Inspection] Class: {decision['class_name']} | "
                f"Conf: {decision['confidence']*100:.1f}% | "
                f"Dest: {decision['target_bin_name']} | "
                f"Travel Delay: {decision['travel_delay_s']}s"
            )

            # 5. Save annotated snapshot to static captures
            filename = f"capture_{int(time.time() * 1000)}.jpg"
            save_path = CAPTURES_DIR / filename
            rel_path = f"/static/captures/{filename}"
            cv2.imwrite(str(save_path), prediction["annotated_image"])

            # 6. Schedule physical servo diverter actuation
            # Delay actuation so the servo diverts when carrot arrives at the diverter gate
            delay = decision["travel_delay_s"]
            target_class_id = decision["class_id"] if decision["decision"].startswith("SORT_") else -1

            def delayed_divert():
                if delay > 0:
                    time.sleep(delay)
                self.sorter.sort_carrot(target_class_id)

            threading.Thread(target=delayed_divert, daemon=True).start()

            # 7. Log detection into SQLite database
            top_bbox = prediction["detections"][0]["bbox"] if prediction["detections"] else []
            db_id = db.log_detection(
                class_id=decision["class_id"],
                class_name=decision["class_name"],
                confidence=decision["confidence"],
                decision=decision["decision"],
                target_bin=decision["target_bin_name"],
                image_path=rel_path,
                bbox=top_bbox,
                status="Diverted" if target_class_id >= 0 else "Rejected"
            )

            # 8. Update in-memory telemetry
            result_payload = {
                "id": db_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "class_id": decision["class_id"],
                "class_name": decision["class_name"],
                "primary_class": decision["class_name"],
                "confidence": decision["confidence"],
                "decision": decision["decision"],
                "target_bin": decision["target_bin_name"],
                "image_path": rel_path,
                "reason": decision["reason"],
                "travel_delay_s": delay
            }
            self.last_detection = result_payload
            return result_payload

    def trigger_manual_inspection(self):
        """Programmatic trigger from Web UI button."""
        logger.info("[Manual Trigger] Triggering inspection cycle from Web Dashboard.")
        return self.process_inspection_cycle()

    def get_system_telemetry(self):
        """Aggregates real-time hardware, camera, model, and sorting states."""
        return {
            "is_system_active": self.is_system_active,
            "camera": {
                "is_running": self.camera.is_running,
                "is_simulation": self.camera.is_simulation,
                "fps": self.camera.fps
            },
            "conveyor": self.conveyor.get_status(),
            "sorter": self.sorter.get_status(),
            "ir_sensor": {
                "pin": self.ir_sensor.pin,
                "is_object_present": self.ir_sensor.is_object_present()
            },
            "last_detection": self.last_detection
        }
