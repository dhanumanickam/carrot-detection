"""
Sorting Decision Engine and Conveyor Travel Timing Calculator
============================================================
Academic M.E. Project: Automated Carrot Quality Detection and Sorting System

Maps AI detections and confidence values to physical sorting decisions:
- Computes time-of-flight travel delay between Camera and Sorter:
      t_delay = Distance / Belt_Velocity
- Evaluates confidence thresholds to divert unconfident/ambiguous items to Reject
- Selects target bin:
      Class 0 -> Bin 1 (Good)
      Class 1 -> Bin 2 (Damaged)
      Class 2 -> Bin 3 (Rotten)
      Fallback -> Reject / Manual Inspection
"""

import logging

logger = logging.getLogger("Decision_Engine")


class DecisionEngine:
    """Evaluates YOLO predictions and schedules physical bin actuation."""

    def __init__(self, camera_to_diverter_distance_m=0.35, min_confidence=0.50):
        self.distance_m = camera_to_diverter_distance_m
        self.min_confidence = min_confidence

    def calculate_travel_delay(self, conveyor_velocity_mps):
        """
        Calculates travel time in seconds for the carrot to move from
        the camera inspection station to the physical servo diverter.
        """
        if conveyor_velocity_mps <= 0.01:
            # Fallback nominal delay if conveyor telemetry is idle
            return 1.8
        
        delay = self.distance_m / conveyor_velocity_mps
        # Clamp to realistic bounds (0.5s to 5.0s)
        return max(0.5, min(5.0, delay))

    def evaluate(self, prediction_result, conveyor_velocity_mps):
        """
        Processes prediction output and yields sorting decision and actuation timing.
        
        Args:
            prediction_result (dict): Output from CarrotPredictor.predict_image()
            conveyor_velocity_mps (float): Current speed of conveyor belt in m/s
            
        Returns:
            dict: Sorting decision metadata
        """
        detections = prediction_result.get("detections", [])
        primary_class_id = prediction_result.get("primary_class_id", -1)
        confidence = prediction_result.get("confidence", 0.0)

        # 1. Check for absence of carrots or detection failure
        if not detections or primary_class_id < 0:
            return {
                "decision": "NO_OBJECT",
                "class_id": -1,
                "class_name": "No Carrot Detected",
                "target_bin_id": 0,
                "target_bin_name": "Reject / Manual Inspection",
                "confidence": 0.0,
                "travel_delay_s": 0.0,
                "reason": "No object detected within inspection ROI"
            }

        # 2. Check confidence threshold
        if confidence < self.min_confidence:
            return {
                "decision": "REJECT_LOW_CONFIDENCE",
                "class_id": primary_class_id,
                "class_name": prediction_result.get("primary_class", "Uncertain"),
                "target_bin_id": 0,
                "target_bin_name": "Reject / Manual Inspection",
                "confidence": confidence,
                "travel_delay_s": self.calculate_travel_delay(conveyor_velocity_mps),
                "reason": f"Confidence {confidence*100:.1f}% below minimum {self.min_confidence*100:.1f}%"
            }

        # 3. Map validated quality class to physical collection bin
        if primary_class_id == 0:
            target_bin_id = 1
            target_bin_name = "Bin 1 (Good Carrots)"
            decision = "SORT_BIN_1"
        elif primary_class_id == 1:
            target_bin_id = 2
            target_bin_name = "Bin 2 (Damaged Carrots)"
            decision = "SORT_BIN_2"
        elif primary_class_id == 2:
            target_bin_id = 3
            target_bin_name = "Bin 3 (Rotten Carrots)"
            decision = "SORT_BIN_3"
        else:
            target_bin_id = 0
            target_bin_name = "Reject / Manual Inspection"
            decision = "REJECT_UNKNOWN_CLASS"

        delay = self.calculate_travel_delay(conveyor_velocity_mps)

        return {
            "decision": decision,
            "class_id": primary_class_id,
            "class_name": prediction_result.get("primary_class"),
            "target_bin_id": target_bin_id,
            "target_bin_name": target_bin_name,
            "confidence": confidence,
            "travel_delay_s": round(delay, 2),
            "reason": f"Matched quality profile with {confidence*100:.1f}% confidence"
        }
